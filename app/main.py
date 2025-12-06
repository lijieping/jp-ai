
"""显式控制所有初始化顺序"""
# 1.初始化所有配置和环境变量
from app.infra.settings import init_settings
init_settings()

# 2.初始化日志
from app.infra.log import *
init_logger()

# 3.基础组件
from fastapi import FastAPI
app = FastAPI()

# 4.基础功能
# api鉴权
from app.service.user_service import AuthMiddleware
app.add_middleware(AuthMiddleware)

# 5.业务router
from app.api import conversation_api, user_api, knowledge_api
app.include_router(conversation_api.router)
app.include_router(user_api.router)
app.include_router(knowledge_api.router)
