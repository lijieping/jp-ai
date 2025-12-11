from fastapi import APIRouter, Request, HTTPException
from sse_starlette import EventSourceResponse

from app.api.api_response import R
from app.infra.settings import SETTINGS
from app.service import conversation_service
from app.schemas.conversation_schema import ConvIn
from app.schemas.message_schema import MsgCreate
import random

router = APIRouter(prefix="/conversation", tags=["conversation"])

@router.post("/{conv_id}/message")
def message_post(request: Request, body: MsgCreate):
    #简单控制访客的请求量
    if request.state.user_id == SETTINGS.GUEST_USER_ID:
        if random.random() > SETTINGS.GUEST_CHAT_ALLOW_PROBABILITY:
            raise HTTPException(status_code=403, detail="您的聊天次数超限，请登录或稍后再试")
    def generate():
        for delta in conversation_service.message_create(body):
            # print(delta, end="", flush=True)
            yield f"{delta}\n\n"
        yield "[DONE]\n\n"
    return EventSourceResponse(generate(), media_type="text/event-stream")

@router.get("/{conv_id}/message/list")
def message_list(conv_id:str):
    msg_list = conversation_service.message_list(conv_id)
    return R.ok(msg_list)

@router.post("", summary="创建对话")
def conversation_create(request:Request):
    conversation_id = conversation_service.conversation_create(request.state.user_id)
    return R.ok(conversation_id)

@router.put("/{conv_id}", summary="修改对话")
async def conversation_update(body:ConvIn):
    await conversation_service.conversation_async_update(body.conv_id, body.user_id, body.title)
    return R.ok("success")

@router.get("/page", summary="查询对话列表")
def conversation_page(request:Request, cur_page: int = 1, page_size: int = 5, ):
    user_id = request.state.user_id
    page = conversation_service.conversation_page(user_id, cur_page, page_size)
    return R.ok(page)

@router.get("/{conv_id}", summary="查询单个对话")
def conversation_get(conv_id:str):
    conv = conversation_service.conversation_get(conv_id)
    return R.ok(conv)

@router.delete("/{conv_ids}", summary="删除对话")
def conversation_delete(conv_ids:str):
    if conv_ids.strip():
        id_list = [s.strip() for s in conv_ids.split(",") if s.strip()]
        if id_list:
            conversation_service.conversation_delete(id_list)
    return R.ok("success")

@router.post("/{conv_id}/title", summary="生成对话标题")
def conversation_generate_title(conv_id: str):
    title = conversation_service.conversation_generate_title(conv_id)
    return R.ok(title if title else "未知标题")
