from pydantic import BaseModel


class ChatResponse(BaseModel):
    conv_id: str
    created_at: str