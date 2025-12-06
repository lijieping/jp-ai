from pydantic import BaseModel


class RagPipelineRequest(BaseModel):
    """
    RAG管道执行请求体
    
    Attributes:
        file_id: 文件ID，指定要执行RAG处理的文件
    """
    file_id: int
