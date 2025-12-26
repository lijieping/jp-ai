from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

from app.user.dao.user_dao import user_dao, UserDAO
from app.user.schemas import UserInfo
from app.infra.settings import get_settings

class UserService:
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao

    def authenticate(self, username: str, password: str) -> UserInfo:
        user = self.user_dao.get_by_name(username)

        if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
            return None
        return UserInfo(
            userId=user.user_id,
            username=user.username,
            role=user.role
        )

    def create_jwt(self, user_info: UserInfo) -> str:
        settings = get_settings()
        now = datetime.now(tz=timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        # 根据jwt规范，把user_id转成str格式
        payload = {"user_id": str(user_info.userId), "user_role": user_info.role, "iat": now, "exp": expire}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

# 创建全局实例
user_service = UserService(user_dao)

