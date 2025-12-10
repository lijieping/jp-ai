from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer


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