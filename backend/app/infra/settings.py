import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
_env_file_path_str = f".env.{ENVIRONMENT}"

class _Settings(BaseSettings):
    ############################################## 通用配置
    # 部署模式：std（标准模式）或 lite（轻量模式）
    MODE: str = "lite"
    # 日志级别
    LOG_LEVEL: str = "INFO"
    # mysql url
    MYSQL_URL: str
    # 本地文件存储
    FILE_STORE_PATH: str
    # 三方sdk所需环境变量，通过env设置到环境变量
    # 百炼api-key
    DASHSCOPE_API_KEY: str

    ##############################################AGENT配置
    # 上下文汇总token数上限
    AGENT_MSG_SUMMARY_MAX_BEFORE: int = 4000
    # 汇总保留消息数
    AGENT_MSG_SUMMARY_TO_KEEP:int = 15
    # 修剪保留消息数
    AGENT_MSG_TRIM_TO_KEEP:int = 15

    ############################################## 登录鉴权相关
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    GUEST_USER_ID:int
    GUEST_CHAT_ALLOW_PROBABILITY:float

    # agent checkpoint缓存选项
    AGENT_MEM_MODE:str="memory" # memory/redis
    # Redis URL，在轻量模式下可选
    REDIS_URL: Optional[str] = None
    # 向量数据库选项
    VECTOR_STORE_MODE:str="faiss" # faiss/chroma
    FAISS_STORE_PATH: str
    CHROMA_HOST: str
    CHROMA_PORT: int
    chroma_http_keepalive_secs: float = 30.0
    chroma_http_max_connections: int = 10
    chroma_http_max_keepalive_connections: int = 5
    # ocr选项
    OCR_MODE:str="buyan" # buyan/easyocr
    # embedding选项
    MODEL_BGE_SMALL_EN_V15_STORE_PATH: str

    ############################################## std模式组件及配置
    # （向量存储）chromadb/milvus，TODO
    # （embedding）BGE-M3配置，TODO
    # （对话记忆）redis url

# 创建配置实例的工厂函数，使用缓存避免重复读取文件
@lru_cache
def get_settings() -> _Settings:
    return _Settings()

# 私有变量，业务通过 get_settings() 获取
_SETTINGS: Optional[_Settings] = None

def init_settings():
    global _SETTINGS
    _SETTINGS = get_settings()
    settings = _SETTINGS
    # 配置验证：标准模式下必须提供 REDIS_URL
    if settings.MODE == "std" and not settings.REDIS_URL:
        raise ValueError("标准模式（MODE=std）下必须提供 REDIS_URL 环境变量")
    # 配置验证：轻量模式下不允许使用 Redis 模式
    if settings.MODE == "lite" and settings.AGENT_MEM_MODE == "redis":
        raise ValueError("轻量模式（MODE=lite）下不允许使用 Redis 记忆模式（AGENT_MEM_MODE=redis）")
