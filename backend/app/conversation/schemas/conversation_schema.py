from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_serializer

from app.infra import is_empty_string

class ConvIn(BaseModel):
    user_id: int
    title:str | None = None
    conv_id: str

    @field_serializer("title")
    def _title(self, value: str | None) -> str:
        return "无标题对话" if is_empty_string(value) else value

    model_config = {"from_attributes": True}

class ConvOut(ConvIn):
    meta: dict = Field(default_factory=dict)
    created_at: datetime  # 先按 datetime 接收

    @field_serializer("title")
    def _title(self, value: str | None) -> str:
        return "无标题对话" if is_empty_string(value) else value

    @field_serializer("created_at")
    def serialize_dt(self, value: datetime) -> str:
        # 1. 先转 UTC（如果原来是本地时间）
        utc = value.astimezone(timezone.utc)
        # 2. 格式化成 ISO-8601
        return utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    model_config = {"from_attributes": True}