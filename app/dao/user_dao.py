from typing import Optional

from app.infra.mysql import Base, DbSession
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, SmallInteger, BigInteger, func, select

class User(Base):
    __tablename__ = "user"
    user_id    = Column(BigInteger, primary_key=True)
    username   = Column(String(50), nullable=False)
    password   = Column(String(255), nullable=False)
    role = Column(
        SQLEnum('admin', 'user', name='role'),  # 与数据库 ENUM 完全一致
        nullable=False,
        default='user',
        server_default='user'  # 让 MySQL 也走默认值
    )
    status     = Column(SmallInteger, default=1)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())

class UserDAO:

    @staticmethod
    def get_by_name(user_name: str) -> Optional[User]:
        """
        根据用户名查询有效用户（status=1）
        """
        with DbSession() as session:
            stmt = (
                select(User)
                .where(
                    User.username == user_name,
                    User.status == 1
                )
                .limit(1)
            )
            return session.execute(stmt).scalars().first()

    @staticmethod
    def list_by_ids(ids: list[int]) -> dict[int, User]:
        if not ids:
            return {}
            
        with DbSession() as session:
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
