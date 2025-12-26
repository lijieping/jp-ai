from typing import Optional
import redis
from app.infra.log import logger
from app.infra.settings import get_settings
import threading

_redis_client: Optional[redis.Redis] = None
_client_lock = threading.Lock()

def get_redis_client() -> Optional[redis.Redis]:
    """
    获取 Redis 客户端。
    
    在轻量模式下返回 None，在标准模式下返回 Redis 客户端实例。
    
    Returns:
        Optional[redis.Redis]: Redis 客户端实例，轻量模式下为 None
        
    Raises:
        ValueError: 轻量模式下尝试获取 Redis 客户端
        ValueError: 标准模式下 REDIS_URL 未配置
    """
    global _redis_client
    
    settings = get_settings()
    # 轻量模式下不允许使用 Redis
    if settings.MODE == "lite":
        raise ValueError("轻量模式（MODE=lite）下不支持 Redis，请使用标准模式（MODE=std）")
    
    # 标准模式下必须提供 REDIS_URL
    if not settings.REDIS_URL:
        raise ValueError("标准模式（MODE=std）下必须提供 REDIS_URL 环境变量")
    
    if _redis_client is not None:
        return _redis_client

    with _client_lock:
        if _redis_client is None:
            redis_url = settings.REDIS_URL
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