from enum import Enum

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, func, select, and_, JSON
import ulid

from app.infra.mysql import mysql_manager as global_mysql_manager

class MsgRole(Enum):
    AI = "assistant"
    USER = "user"

class Message(global_mysql_manager.Base):
    __tablename__ = "message"
    msg_id = Column(String(100), primary_key=True) # 适应langchain的msg_id长度
    conv_id = Column(String(26), nullable=False, index=True)
    role = Column(SQLEnum(MsgRole.AI.value,
                          MsgRole.USER.value, name = "role"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(), server_default=func.now())

class MsgDAO:
    def __init__(self, mysql_manager=None):
        self._mysql_manager = mysql_manager or global_mysql_manager

    def add(self, conv_id: str, role: MsgRole, content: str, db) -> str:
        mid = str(ulid.ULID())
        db.add(Message(msg_id=mid, conv_id=conv_id, role=role.value, content=content))
        db.flush()
        return mid

    def list_by_conv_id(self, conv_id: str):
        with self._mysql_manager.DbSession() as db:
            stmt = select(Message).where(
                and_(Message.conv_id == conv_id)
            ).order_by(Message.created_at)
            return db.execute(stmt).scalars().all()

# 创建全局实例
msg_dao = MsgDAO(global_mysql_manager)