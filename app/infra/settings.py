import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

class _Settings(BaseSettings):
    # 基础配置
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    #项目模式：lite、std
    PROJECT_MODE: str = "lite"

    # db
    REDIS_URL: str
    MYSQL_URL: str

    # 登录相关
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # FAISS相关
    FAISS_STORE_PATH: str

    # 模型相关
    EASYOCR_MODULE_PATH: str
    MODEL_BGE_SMALL_EN_V15_STORE_PATH: str

    # 本地文件存储
    FILE_STORE_PATH: str

    # 三方sdk所需环境变量，通过env设置到环境变量
    # 百炼api-key
    DASHSCOPE_API_KEY: str
    # EasyOCR模型存放目录
    EASYOCR_MODULE_PATH: str

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

def is_lite_mode():
    is_lite_mode = SETTINGS.PROJECT_MODE == "lite"
    return is_lite_mode
