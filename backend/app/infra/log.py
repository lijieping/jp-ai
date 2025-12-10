import logging
from logging.config import dictConfig

from app.infra.settings import get_settings

_LOG_CONFIG = None

def init_logger():
    global _LOG_CONFIG
    settings = get_settings()

    # 动态构建配置字典
    _LOG_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout',
                'level': settings.LOG_LEVEL.upper(),
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': settings.LOG_LEVEL.upper(),
            },
        },
    }

    dictConfig(_LOG_CONFIG)
    return logging.getLogger(__name__)

logger = logging.getLogger(__name__)