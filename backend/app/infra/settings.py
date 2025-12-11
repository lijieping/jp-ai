import os
from functools import lru_cache

from pydantic_settings import BaseSettings

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
_env_file_path_str = f".env.{ENVIRONMENT}"

class _Settings(BaseSettings):
    ############################################## 通用配置
    # 日志级别
    LOG_LEVEL: str = "INFO"
    # mysql url
    MYSQL_URL: str
    # 本地文件存储
    FILE_STORE_PATH: str
    # 三方sdk所需环境变量，通过env设置到环境变量
    # 百炼api-key
    DASHSCOPE_API_KEY: str

    ############################################## 登录鉴权相关
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    GUEST_USER_ID:int
    GUEST_CHAT_ALLOW_PROBABILITY:float

    # agent checkpoint缓存选项
    AGENT_MEM_MODE:str="memory" # memory/redis
    REDIS_URL: str
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
    # EasyOCR模型存放目录
    EASYOCR_MODULE_PATH: str
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

SETTINGS : _Settings

def init_settings():
    global SETTINGS
    SETTINGS = get_settings()
