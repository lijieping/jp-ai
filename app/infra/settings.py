import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

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
    # EasyOCR模型存放目录
    EASYOCR_MODULE_PATH: str

    ############################################## 登录鉴权相关
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    GUEST_USER_ID:int
    GUEST_CHAT_ALLOW_PROBABILITY:float

    # 项目模式：lite、std
    PROJECT_MODE: str = "lite"
    ############################################## lite模式组件及配置
    # （向量存储）faiss文件存放目录
    FAISS_STORE_PATH: str
    # （embedding）fastembed + bge-small-en-v1.5，模型存放位置
    MODEL_BGE_SMALL_EN_V15_STORE_PATH: str

    ############################################## std模式组件及配置
    # （向量存储）chromadb/milvus，TODO
    # （embedding）BGE-M3配置，TODO
    # （对话记忆）redis url
    REDIS_URL: str

    # Pydantic配置
    model_config = SettingsConfigDict(
        env_file=(
            f".env.{ENVIRONMENT}"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

# 创建配置实例的工厂函数，使用缓存避免重复读取文件
@lru_cache
def get_settings() -> _Settings:
    return _Settings()

SETTINGS : _Settings = get_settings()

def init_settings():
    # 三方sdk所需环境变量，通过env设置到环境变量
    os.environ.setdefault("DASHSCOPE_API_KEY", SETTINGS.DASHSCOPE_API_KEY)
    os.environ.setdefault("EASYOCR_MODULE_PATH", SETTINGS.EASYOCR_MODULE_PATH)
