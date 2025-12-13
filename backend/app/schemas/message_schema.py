from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, field_serializer


class StepType(Enum):
    AI_CONTENT = "ai_content"
    TOOL_CALL = "tool_call"

class MsgContentStep(BaseModel):
    id:str = None
    type:str = None
    tool_calls_dict:dict = {} # key:id  value:  toolcall字典
    ai_answer:str = ''

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'tool_calls_dict': self.tool_calls_dict,
            "ai_answer": self.ai_answer
        }

class MsgCreate(BaseModel):
    role: str
    content: str
    conv_id: str

class MsgOut(MsgCreate):
    msg_id: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_dt(self, value: datetime) -> str:
        # 1. 先转 UTC（如果原来是本地时间）
        utc = value.astimezone(timezone.utc)
        # 2. 格式化成 ISO-8601
        return utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    model_config = {"from_attributes": True}