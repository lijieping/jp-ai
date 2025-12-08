import traceback
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from jwt import ExpiredSignatureError, DecodeError
from starlette.responses import JSONResponse

from app.dao.user_dao import UserDAO, UserRole
from app.infra.log import logger
from app.schemas.user_schema import UserInfo
from app.infra.settings import SETTINGS
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import re

# 定义白名单
SESSION_WHITE_LIST = re.compile(r"^(POST /user/session)$")
GUEST_WHITE_LIST = re.compile(r"^GET /.+|" r"^[A-Z]+ /conversation(?:/.*)?$")

def authenticate(username: str, password: str) -> UserInfo:
    user = UserDAO.get_by_name(username)

    if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
        return None
    return UserInfo(
        userId=user.user_id,
        username=user.username,
        role=user.role
    )

def create_jwt(user_info: UserInfo) -> str:
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=SETTINGS.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    # 根据jwt规范，把user_id转成str格式
    payload = {"user_id": str(user_info.userId), "user_role": user_info.role, "iat": now, "exp": expire}
    return jwt.encode(payload, SETTINGS.JWT_SECRET, algorithm=SETTINGS.JWT_ALGORITHM)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1、解析token中用户信息
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            logger.debug("authorization格式非法:%s", authorization)
        else:
            token = authorization[7:]
            try:
                payload = jwt.decode(token, SETTINGS.JWT_SECRET, algorithms=[SETTINGS.JWT_ALGORITHM])
                # 塞user信息
                request.state.user_id = int(payload["user_id"])
                request.state.user_role = payload["user_role"]
                request.state.user_token = token
            except DecodeError as e:
                # token格式不对
                logger.debug("token格式非法:%s", token)
            except ExpiredSignatureError as e:
                # token 过期
                request.state.user_token = token
            except Exception as e:
                logger.error(traceback.format_exc())
                raise e

        # 2、权限判断
        # 有user_id，直接放行
        if hasattr(request.state, 'user_id') and request.state.user_id > 0:
            return await call_next(request)

        method_path = f"{request.method} {request.url.path}"
        # 登录注册白名单api，直接放行
        if SESSION_WHITE_LIST.match(method_path):
            return await call_next(request)
        # 访客模式，塞访客信息再放行
        if GUEST_WHITE_LIST.match(method_path):
            request.state.user_id = SETTINGS.GUEST_USER_ID
            request.state.user_role = UserRole.GUEST.value
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "登录已过期，请重新登陆" if hasattr(request.state, 'user_token') else "此功能需要登录体验"}
        )