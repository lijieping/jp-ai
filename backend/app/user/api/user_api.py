from fastapi import APIRouter, HTTPException

from app.common.api import R
from app.user.service import user_service
from app.user.schemas import LoginResp, LoginReq

router = APIRouter(tags=["user"], prefix="/user")

@router.post("/session")
def login(body: LoginReq):
    """登录并返回 JWT"""
    userInfo = user_service.authenticate(body.username, body.password)
    if not userInfo:
        raise HTTPException(
            status_code=401,
            detail="账号或密码错误",
        )
    token = user_service.create_jwt(userInfo)
    return R.ok(LoginResp(token=token, userInfo=userInfo))

