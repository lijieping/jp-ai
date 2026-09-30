
"""显式控制所有初始化顺序"""

# 1.初始化所有配置和环境变量
from app.infra import init_settings
init_settings()

# 2.初始化日志
from app.infra import init_logger
init_logger()

# 3.基础组件
from app.infra import mysql_manager
mysql_manager.initialize()

# 4.初始化核心主 Agent
from app.agent.agent_service import core_agent_service
core_agent_service.get_agent()

from fastapi import FastAPI
app = FastAPI()

# 4.基础功能
# api鉴权
from app.user.service import AuthMiddleware
app.add_middleware(AuthMiddleware)

# 5.业务router
from app.user.api import router as user_router
from app.conversation.api import router as conversation_router
from app.rag.api import router as rag_router
app.include_router(user_router)
app.include_router(conversation_router)
app.include_router(rag_router)
