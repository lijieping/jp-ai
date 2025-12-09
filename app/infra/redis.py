from typing import Optional
import redis
from app.infra.log import logger
from app.infra.settings import SETTINGS
import threading

_redis_client: Optional[redis.Redis] = None
_client_lock = threading.Lock()

def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    with _client_lock:
        if _redis_client is None:
            redis_url = SETTINGS.REDIS_URL
            tmp = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
            # 关键：在锁内赋值，保证对其他线程可见
            _redis_client = tmp
    logger.debug("init redis client %s", _redis_client)
    return _redis_client