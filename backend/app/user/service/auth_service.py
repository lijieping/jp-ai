import traceback
import re
import jwt
from jwt import ExpiredSignatureError, DecodeError
from starlette.responses import JSONResponse
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.user.dao.user_dao import UserRole
from app.infra import logger
from app.infra.settings import get_settings

# 定义白名单
SESSION_WHITE_LIST = re.compile(r"^(POST /user/session)$")
GUEST_WHITE_LIST = re.compile(r"^GET /.+|" r"^[A-Z]+ /conversation(?:/.*)?$")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1、解析token中用户信息
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            logger.debug("authorization格式非法:%s", authorization)
        else:
            token = authorization[7:]
            try:
                settings = get_settings()
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
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
            settings = get_settings()
            request.state.user_id = settings.GUEST_USER_ID
            request.state.user_role = UserRole.GUEST.value
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "登录已过期，请重新登陆" if hasattr(request.state, 'user_token') else "此功能需要登录体验"}
        )

