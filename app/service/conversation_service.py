import asyncio
from typing import List

from app.infra.tool import is_empty_string
from app.schemas.page_schema import Page

import ulid
from pydantic import TypeAdapter

from app.infra.mysql import DbSession
from app.dao.conversation_dao import ConvDAO
from app.dao.message_dao import Message, MsgDAO
from app.service import agent_service
from app.schemas.conversation_schema import ConvOut
from app.schemas.message_schema import MsgCreate, MsgOut


async def message_create(msg_create:MsgCreate):
    conv_id = msg_create.conv_id
    user_content = msg_create.content

    with DbSession() as db:
        # 先写 user 消息（非流式）
        user_msg = Message(msg_id=str(ulid.ULID),conv_id=conv_id,role="user",content=user_content)
        db.add(user_msg)
        # 流式生成助手消息
        assistant_content = ""
        async for delta in agent_service.token_generator(user_content, conv_id):
            assistant_content += delta
            yield delta  # SSE 用

        # 流结束， 写助手消息
        assistant_msg = Message(msg_id=str(ulid.ULID()), conv_id=conv_id, role="assistant", content=assistant_content)
        db.add(assistant_msg)
        db.commit()
        db.close()

def message_list(conv_id: str):
    items = MsgDAO.list_by_conv_id(conv_id)
    # 一次性转整个列表（推荐，更快）
    dto_list = TypeAdapter(List[MsgOut]).validate_python(items)
    return dto_list

def conversation_create(user_id:int):
    conv_id = ConvDAO.create(user_id=user_id, meta={})
    return conv_id

async def conversation_async_update(conv_id: str, user_id: int, title: str) -> None:
    await ConvDAO.async_update(conv_id=conv_id, user_id=user_id, title=title)

def conversation_page(user_id:int, cur_page: int = 1, page_size: int = 5) -> Page[ConvOut]:
    offset = (cur_page - 1) * page_size
    items = ConvDAO.list_by_user(user_id=user_id, offset=offset, limit=page_size)
    # 一次性转整个列表（推荐，更快）
    dto_list = TypeAdapter(List[ConvOut]).validate_python(items)
    total = ConvDAO.count_by_user(user_id=user_id)
    return Page(total=total, cur_page=cur_page, page_size=page_size, list=dto_list)

def conversation_get(conv_id:str):
    conv = ConvDAO.get_by_id(conv_id)
    dto = TypeAdapter(ConvOut).validate_python(conv)
    return dto

def conversation_delete(conv_ids:List[str]):
    ConvDAO.delete(conv_ids)

def conversation_generate_title(conv_id: str) -> str:
    conv = ConvDAO.get_by_id(conv_id)
    if (is_empty_string(conv.title)):
        items = MsgDAO.list_by_conv_id(conv_id)
        latest_user_msg = max(
            (item for item in items if item.role == 'user'),
            key=lambda x: x.created_at,
            default=None
        )
        content = latest_user_msg.content if latest_user_msg else None
        question = "请根据以下提问内容生成一个不超过十个字的提问标题：" + content
        title = agent_service.small_model_service(question)
        asyncio.run(conversation_async_update(conv_id, conv.user_id, title))
        return title
    return conv.title



