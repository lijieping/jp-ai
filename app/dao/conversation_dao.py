from typing import Any, List
from sqlalchemy import select, func, update, Column, String, DateTime, SmallInteger, BigInteger, JSON
import ulid
from app.infra.mysql import Base, DbSession

class Conversation(Base):
    __tablename__ = "conversation"
    conv_id    = Column(String(26), primary_key=True)
    user_id    = Column(BigInteger, nullable=False)
    title      = Column(String(255), nullable=False)
    status     = Column(SmallInteger, default=1)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())
    meta       = Column(JSON, default=dict)

class ConvDAO:
    @staticmethod
    def create(user_id: int, meta: dict) -> str:
        with DbSession() as db:
            cid = str(ulid.new())
            db.add(Conversation(conv_id=cid, user_id=user_id, meta=meta))
            db.commit()
            db.close()
        return cid

    @staticmethod
    async def async_update(conv_id: str, user_id:int, title:str):
        with DbSession() as db:
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

    @staticmethod
    def list_by_user(user_id: int, offset: int, limit : int):
        with DbSession() as db:
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

    @staticmethod
    def count_by_user(user_id: int) -> Any:
        with DbSession() as db:
            # 总条数
            total = db.scalar(
                select(func.count(Conversation.conv_id))
                .where(Conversation.user_id == user_id, Conversation.status == 1)
            )
        return total

    @staticmethod
    def delete(conv_ids:List[str]):
        with DbSession() as db:
            stmt = (
                update(Conversation)
                .where(Conversation.conv_id.in_(conv_ids))
                .values(status=0)
                .execution_options(synchronize_session="fetch")  # 防止缓存不一致
            )
            db.execute(stmt)
            db.commit()

    @staticmethod
    def get_by_id(conv_id: str):
        with DbSession() as db:
            stmt = select(Conversation).where(Conversation.conv_id == conv_id).limit(1)
        return db.execute(stmt).scalars().first()

