import asyncio
import json
from typing import List

from app.agent.sub_agent.daily_agent import daily_angent_service
from app.infra import logger
from app.infra import is_empty_string
from app.common.schemas import Page

from pydantic import TypeAdapter

from app.conversation.dao.conversation_dao import conv_dao, ConvDAO
from app.conversation.dao.message_dao import msg_dao, MsgRole, MsgDAO, MessageStreamChunk, MsgChunkType
from app.agent.router_agent import agent_router_service
from app.conversation.schemas import ConvOut, MsgCreate, MsgOut


class ConversationService:
    def __init__(self, conv_dao: ConvDAO, msg_dao: MsgDAO):
        self.conv_dao = conv_dao
        self.msg_dao = msg_dao

    def message_create(self, msg_create: MsgCreate):
        # 回答积攒
        messages_store = []
        # 吐节点工作信息
        for message_chunk in agent_router_service.exec(msg_create.content, msg_create.conv_id):
            messages_store.append(message_chunk)
            message_4_web = self._convert_agent_msg(message_chunk)
            yield message_4_web
        # 入库
        with self.conv_dao._mysql_manager.DbSession() as db:
            self.msg_dao.add(conv_id=msg_create.conv_id, role= MsgRole.USER, content= msg_create.content, db = db)
            self.msg_dao.add(conv_id=msg_create.conv_id, role= MsgRole.AI, content= json.dumps([obj.dict() for obj in messages_store], ensure_ascii=False), db = db)
            db.commit()

    def _convert_agent_msg(self, message_chunk:MessageStreamChunk) -> str:
        """转换成吐给前端的格式"""
        message_chunk = message_chunk.model_copy()
        if message_chunk.type == MsgChunkType.ROUTER.value:
            message_chunk.content = json.loads(message_chunk.content)['reason_and_mode']
        return json.dumps(message_chunk.model_dump(), ensure_ascii=False)

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
        title = daily_angent_service.small_model_service(question)
        asyncio.run(self.conversation_async_update(conv_id, conv.user_id, title))
        return title

# 创建全局实例
conv_service = ConversationService(conv_dao, msg_dao)



