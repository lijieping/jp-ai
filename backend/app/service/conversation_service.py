import asyncio
import json
from typing import List

from _cffi_backend import typeof
from langchain_core.messages import AIMessageChunk, ToolMessage

from app.infra.log import logger
from app.infra.tool import is_empty_string
from app.schemas.page_schema import Page

from pydantic import TypeAdapter

from app.dao.conversation_dao import conv_dao, ConvDAO
from app.dao.message_dao import msg_dao, MsgRole, MsgDAO
from app.service import agent_service
from app.schemas.conversation_schema import ConvOut
from app.schemas.message_schema import MsgCreate, MsgOut, MsgContentStep, StepType

class ConversationService:
    def __init__(self, conv_dao: ConvDAO, msg_dao: MsgDAO):
        self.conv_dao = conv_dao
        self.msg_dao = msg_dao

    def message_create(self, msg_create: MsgCreate):
        conv_id = msg_create.conv_id
        user_content = msg_create.content
        step_chain:list[MsgContentStep] = []
        lc_id_step_index = {}
        for langchain_msg_chunk in agent_service.token_generator(user_content, conv_id):
            if isinstance(langchain_msg_chunk, AIMessageChunk):
                """AI类型消息，包含tool调用和AI正式回答两种"""
                # 获取当前步骤
                step_index = lc_id_step_index.get(langchain_msg_chunk.id)
                if step_index is None:
                    # 外层，新步骤初始化
                    lc_id_step_index[langchain_msg_chunk.id] = len(step_chain)
                    step = MsgContentStep(id = langchain_msg_chunk.id)
                    step_chain.append(step)
                else:
                    step = step_chain[step_index]

                # 处理流式块
                if langchain_msg_chunk.chunk_position == "last":
                    # 步骤结束chunk，不处理
                    continue
                elif langchain_msg_chunk.tool_call_chunks:
                    # tool_call_chunks有值 -> 是工具调用 -> 填充step的tool_calls属性
                    step.type = StepType.TOOL_CALL.value
                    lc_tool_call_chunks = langchain_msg_chunk.tool_call_chunks
                    for lc_tool_call_chunk in lc_tool_call_chunks:
                        if not isinstance(lc_tool_call_chunk, dict) or not lc_tool_call_chunk.get("type") == "tool_call_chunk":
                            logger.error("未识别的tool_call_chunk:%s", lc_tool_call_chunk)
                            continue

                        tool_call_in_step = step.tool_calls_dict.get(lc_tool_call_chunk["id"])
                        if tool_call_in_step is None:
                            # step中没有 -> 首次出现的工具调用 -> 初始化
                            tool_call_in_step = lc_tool_call_chunk
                            step.tool_calls_dict[lc_tool_call_chunk.get('id')] = tool_call_in_step

                            yield json.dumps(lc_tool_call_chunk)  # 给前端
                        else:
                            # step中有 -> 在上面追加内容
                            tool_call_in_step['args'] += lc_tool_call_chunk['args']
                elif not is_empty_string(langchain_msg_chunk.content):
                    # content有值 -> 是AI回答 -> 填充message的content属性
                    step.type = StepType.AI_CONTENT.value
                    step.ai_answer += langchain_msg_chunk.content
                    yield json.dumps(langchain_msg_chunk.model_dump()) # 给前端
                else:
                    logger.error("未识别的chunk:%s,%s", type(langchain_msg_chunk), langchain_msg_chunk)
                    continue
            elif isinstance(langchain_msg_chunk, ToolMessage):
                """Tool类型消息"""
                # 目前是整块，直接追加到step.toolcall.result
                tool_content = langchain_msg_chunk.content
                for step in step_chain:
                    tool_call_in_step = step.tool_calls_dict.get(langchain_msg_chunk.tool_call_id)
                    if tool_call_in_step:
                        if 'result' not in tool_call_in_step:
                            tool_call_in_step['result'] = ''
                        tool_call_in_step['result'] += tool_content
                        break
            else:
                logger.error("未识别的chunk:%s,%s", typeof(langchain_msg_chunk), langchain_msg_chunk)
                continue

        # 入库
        with self.conv_dao._mysql_manager.DbSession() as db:
            self.msg_dao.add(conv_id=conv_id, role= MsgRole.USER, content= msg_create.content, db = db)
            self.msg_dao.add(conv_id=conv_id, role= MsgRole.AI, content= json.dumps([step.to_dict() for step in step_chain]), db = db)
            db.commit()

    def message_list(self, conv_id: str):
        items = self.msg_dao.list_by_conv_id(conv_id)
        # 一次性转整个列表（推荐，更快）
        dto_list = TypeAdapter(List[MsgOut]).validate_python(items)
        return dto_list

    def conversation_create(self, user_id:int):
        conv_id = self.conv_dao.create(user_id=user_id, meta={})
        return conv_id

    async def conversation_async_update(self, conv_id: str, user_id: int, title: str) -> None:
        await self.conv_dao.async_update(conv_id=conv_id, user_id=user_id, title=title)

    def conversation_page(self, user_id:int, cur_page: int = 1, page_size: int = 5) -> Page[ConvOut]:
        offset = (cur_page - 1) * page_size
        items = self.conv_dao.list_by_user(user_id=user_id, offset=offset, limit=page_size)
        # 一次性转整个列表（推荐，更快）
        dto_list = TypeAdapter(List[ConvOut]).validate_python(items)
        total = self.conv_dao.count_by_user(user_id=user_id)
        return Page(total=total, cur_page=cur_page, page_size=page_size, list=dto_list)

    def conversation_get(self, conv_id:str):
        conv = self.conv_dao.get_by_id(conv_id)
        dto = TypeAdapter(ConvOut).validate_python(conv)
        return dto

    def conversation_delete(self, conv_ids:List[str]):
        self.conv_dao.delete(conv_ids)

    def conversation_generate_title(self, conv_id: str) -> str:
        conv = self.conv_dao.get_by_id(conv_id)
        if not is_empty_string(conv.title):
            return conv.title
        items = self.msg_dao.list_by_conv_id(conv_id)
        latest_user_msg = max(
            (item for item in items if item.role == 'user'),
            key=lambda x: x.created_at,
            default=None
        )
        if not latest_user_msg:
            logger.error("未找到对话{%s}的消息", conv_id)
            return "无标题会话"
        question = "请根据以下提问内容生成一个不超过十个字的提问标题：" + latest_user_msg.content
        title = agent_service.small_model_service(question)
        asyncio.run(self.conversation_async_update(conv_id, conv.user_id, title))
        return title

# 创建全局实例
conv_service = ConversationService(conv_dao, msg_dao)



