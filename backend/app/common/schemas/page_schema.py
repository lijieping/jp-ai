from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    """分页数据包装类"""
    total: int = Field(..., description="总数")
    cur_page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    list: List[T] = Field(..., description="数据列表")

