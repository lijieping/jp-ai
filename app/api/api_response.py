from typing import Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum

T = TypeVar("T")

class R(BaseModel, Generic[T]):
    """统一响应包装"""
    code: int = Field(..., description="业务错误码；200=成功")
    msg: str = Field(..., description="人类可读信息")
    data: T

    # ---- 工厂方法 ----
    @staticmethod
    def ok(data: T = None, msg: str = "success") -> "R[T]":
        return R(code=200000, msg=msg, data=data)

    @staticmethod
    def fail(code: int = 500000, msg: str = "system error", data: T = None) -> "R[T]":
        return R(code=code, msg=msg, data=data)

class Code(Enum):
    SUCCESS = 200000
    PARAM_ERR = 400000
    NOT_FOUND = 404000
    FREQUENT = 429000
    SERVER_ERR = 500000