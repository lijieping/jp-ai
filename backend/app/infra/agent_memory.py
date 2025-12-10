import threading
import time

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import RedisSaver

from app.infra.log import logger
from app.infra.redis import get_redis_client
from app.infra.settings import SETTINGS

_agent_memory = None


def get_agent_memory() -> BaseCheckpointSaver:
    global _agent_memory
    if _agent_memory is None:
        if SETTINGS.AGENT_MEM_MODE == "memory":
            _agent_memory = InMemorySaver()

            # 定期清理内存
            def cleaner():
                while True:
                    time.sleep(60 * 60)
                    logger.info('本地记忆清理')
                    _agent_memory.storage.clear()

            threading.Thread(target=cleaner, daemon=True).start()
        elif SETTINGS.AGENT_MEM_MODE == "redis":
            _agent_memory = RedisSaver(redis_client=get_redis_client(),
                                       ttl={"default_ttl": 120, "refresh_on_read": True})
            _agent_memory.setup()  # 首次运行建表
        else:
            raise ValueError(f"非法的SETTINGS.AGENT_MEM_MODE={SETTINGS.AGENT_MEM_MODE}")
    return _agent_memory
