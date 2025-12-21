from typing import Any, List
from sqlalchemy import select, func, update, Column, String, DateTime, SmallInteger, BigInteger, JSON
import ulid
from app.infra.mysql import mysql_manager as global_mysql_manager

class Conversation(global_mysql_manager.Base):
    __tablename__ = "conversation"
    conv_id    = Column(String(26), primary_key=True)
    user_id    = Column(BigInteger, nullable=False)
    title      = Column(String(255), nullable=False)
    status     = Column(SmallInteger, default=1)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())
    meta       = Column(JSON, default=dict)

class ConvDAO:
    def __init__(self, mysql_manager=None):
        self._mysql_manager = mysql_manager or global_mysql_manager

    def create(self, user_id: int, meta: dict) -> str:
        with self._mysql_manager.DbSession() as db:
            cid = str(ulid.ULID())
            db.add(Conversation(conv_id=cid, user_id=user_id, meta=meta))
            db.commit()
            db.close()
        return cid

    async def async_update(self, conv_id: str, user_id:int, title:str):
        with self._mysql_manager.DbSession() as db:
            stmt = (
                update(Conversation)
                .where(Conversation.conv_id == conv_id)
                .values(conv_id=conv_id, user_id=user_id, title=title)
                .execution_options(synchronize_session="fetch")  # 防止缓存不一致
            )
            result_proxy = db.execute(stmt)
            updated_rows = result_proxy.rowcount
            db.commit()
            db.close()
        return updated_rows

    def list_by_user(self, user_id: int, offset: int, limit : int):
        with self._mysql_manager.DbSession() as db:
            # 分页数据
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id, Conversation.status == 1)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = db.execute(stmt).scalars().all()
        return rows

    def count_by_user(self, user_id: int) -> Any:
        with self._mysql_manager.DbSession() as db:
            # 总条数
            total = db.scalar(
                select(func.count(Conversation.conv_id))
                .where(Conversation.user_id == user_id, Conversation.status == 1)
            )
        return total

    def delete(self, conv_ids:List[str]):
        with self._mysql_manager.DbSession() as db:
            stmt = (
                update(Conversation)
                .where(Conversation.conv_id.in_(conv_ids))
                .values(status=0)
                .execution_options(synchronize_session="fetch")  # 防止缓存不一致
            )
            db.execute(stmt)
            db.commit()

    def get_by_id(self, conv_id: str):
        with self._mysql_manager.DbSession() as db:
            stmt = select(Conversation).where(Conversation.conv_id == conv_id).limit(1)
        return db.execute(stmt).scalars().first()

# 创建全局实例
conv_dao = ConvDAO(global_mysql_manager)

