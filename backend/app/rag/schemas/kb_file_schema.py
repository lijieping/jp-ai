from pydantic import BaseModel
from typing import Optional, Any

class KbFileOut(BaseModel):
    id: Optional[int] = None  # 可选字段，对应前端的id?
    file_name: str  # 文件名
    file_type: str  # 文件类型
    file_size: int  # 文件大小
    file_url: str  # 文件URL
    created_at: str  # 创建时间
    user_id: int  # 用户ID
    user_name: str  # 用户名
    space_id: int  # 空间ID
    space_name: str  # 空间名称
    collection: str  # 集合名称
    description: Optional[str] = None  # 文件描述
    status: int = 1  # 文件状态

class KbFileWithPipelineRecordOut(KbFileOut):
    rag_status: int = 0  # RAG处理状态，0-待执行 1-成功 2-失败
    msg: Optional[Any] = None  # RAG处理消息