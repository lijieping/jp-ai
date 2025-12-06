from sqlalchemy import Column, String, DateTime, Enum, Text, func, select, and_
import ulid
from app.infra.mysql import Base, DbSession


class Message(Base):
    __tablename__ = "message"
    msg_id = Column(String(26), primary_key=True)
    conv_id = Column(String(26), nullable=False, index=True)
    role = Column(Enum("user", "assistant"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(), server_default=func.now())

class MsgDAO:

    @staticmethod
    async def add(conv_id: str, role: str, content: str, db) -> str:
        mid = str(ulid.new())
        db.add(Message(msg_id=mid, conv_id=conv_id, role=role, content=content))
        await db.flush()
        return mid

    @staticmethod
    def list_by_conv_id(conv_id: str):
        with DbSession() as db:
            stmt = select(Message).where(
                and_(Message.conv_id == conv_id)
            ).order_by(Message.created_at)
            return db.execute(stmt).scalars().all()