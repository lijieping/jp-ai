from enum import Enum
from typing import Optional

from sqlalchemy import Column, BigInteger, String, SmallInteger, DateTime, func, Enum as SQLEnum, select

from app.infra.mysql import mysql_manager as global_mysql_manager

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(global_mysql_manager.Base):
    __tablename__ = "user"
    user_id    = Column(BigInteger, primary_key=True)
    username   = Column(String(50), nullable=False)
    password   = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole.ADMIN.value, UserRole.USER.value,UserRole.GUEST.value, name='role'),  # 与数据库 ENUM 完全一致
        nullable=False,
        default=UserRole.ADMIN.value,
        server_default=UserRole.ADMIN.value
    )
    status     = Column(SmallInteger, default=1)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())

class UserDAO:
    def __init__(self, mysql_manager=None):
        self._mysql_manager = mysql_manager or global_mysql_manager

    def get_by_name(self, user_name: str) -> Optional[User]:
        """
        根据用户名查询有效用户（status=1）
        """
        with self._mysql_manager.DbSession() as session:
            stmt = (
                select(User)
                .where(
                    User.username == user_name,
                    User.status == 1
                )
                .limit(1)
            )
            return session.execute(stmt).scalars().first()

    def list_by_ids(self, ids: list[int]) -> dict[int, User]:
        if not ids:
            return {}
            
        with self._mysql_manager.DbSession() as session:
            stmt = (
                select(User)
                .where(
                    User.user_id.in_(ids),
                    User.status == 1
                )
            )
            users = session.execute(stmt).scalars().all()
            
            # 转换为字典，以user_id为键
            return {user.user_id: user for user in users}

# 创建全局实例
user_dao = UserDAO(global_mysql_manager)
