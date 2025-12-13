from enum import Enum

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, func, select, and_, JSON
import ulid

from app.infra.mysql import Base, DbSession

class MsgRole(Enum):
    AI = "assistant"
    USER = "user"

class Message(Base):
    __tablename__ = "message"
    msg_id = Column(String(100), primary_key=True) # 适应langchain的msg_id长度
    conv_id = Column(String(26), nullable=False, index=True)
    role = Column(SQLEnum(MsgRole.AI.value,
                          MsgRole.USER.value, name = "role"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(), server_default=func.now())

class MsgDAO:

    @staticmethod
    def add(conv_id: str, role: MsgRole, content: str, db) -> str:
        mid = str(ulid.ULID())
        db.add(Message(msg_id=mid, conv_id=conv_id, role=role.value, content=content))
        db.flush()
        return mid

    @staticmethod
    def list_by_conv_id(conv_id: str):
        with DbSession() as db:
            stmt = select(Message).where(
                and_(Message.conv_id == conv_id)
            ).order_by(Message.created_at)
            return db.execute(stmt).scalars().all()