from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from app.dao.user_dao import UserDAO
from app.schemas.user_schema import UserInfo
from app.infra.settings import SETTINGS
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import re

# 定义白名单
WHITE_LIST = re.compile(r"^(POST /user/session)$")

def authenticate(username: str, password: str) -> UserInfo:
    user = UserDAO.get_by_name(username)

    if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
        return None
    return UserInfo(
        userId=user.user_id,
        username=user.username
    )

def create_jwt(user_id: int) -> str:
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=SETTINGS.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    # 根据jwt规范，把user_id转成str格式
    payload = {"sub": str(user_id), "iat": now, "exp": expire}
    return jwt.encode(payload, SETTINGS.JWT_SECRET, algorithm=SETTINGS.JWT_ALGORITHM)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method_path = f"{request.method} {request.url.path}"
        if WHITE_LIST.match(method_path):
            return await call_next(request)   # 白名单直接放行

        # 非白名单才验签
        auth = request.headers.get("authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="请求头authorization异常",
            )
        token = auth[7:]
        try:
            # 如果 token 过期，这里会直接抛 jwt.ExpiredSignatureError
            payload = jwt.decode(token, SETTINGS.JWT_SECRET, algorithms=[SETTINGS.JWT_ALGORITHM])
            # 塞user_id
            request.state.user_id = int(payload["sub"])
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="非法token",
            )

        return await call_next(request)