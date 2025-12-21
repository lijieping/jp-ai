from unittest.mock import patch, Mock
from contextlib import contextmanager

from app.infra.settings import _Settings


# Shared mock settings object that can be used across all test files
mock_settings = Mock(spec=_Settings)
mock_settings.LOG_LEVEL = "INFO"
mock_settings.MYSQL_URL = "mysql://test:test@localhost/test"
mock_settings.FILE_STORE_PATH = "/tmp/test"
mock_settings.DASHSCOPE_API_KEY = "test_api_key"
mock_settings.JWT_SECRET = "test_secret"
mock_settings.JWT_ALGORITHM = "HS256"
mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
mock_settings.GUEST_USER_ID = 999
mock_settings.GUEST_CHAT_ALLOW_PROBABILITY = 0.5
mock_settings.AGENT_MEM_MODE = "memory"
mock_settings.REDIS_URL = "redis://localhost:6379/0"
mock_settings.VECTOR_STORE_MODE = "faiss"
mock_settings.FAISS_STORE_PATH = "/tmp/faiss"
mock_settings.CHROMA_HOST = "localhost"
mock_settings.CHROMA_PORT = 8000
mock_settings.OCR_MODE = "buyan"  # 可以根据测试需要修改
mock_settings.EASYOCR_MODULE_PATH = "/tmp/easyocr"
mock_settings.MODEL_BGE_SMALL_EN_V15_STORE_PATH = "/tmp/bge"


@contextmanager
def patch_settings():
    """Context manager to patch settings in all necessary places.
    
    This ensures that all modules that import get_settings
    will receive the mock settings object.
    
    Usage:
        with patch_settings():
            # Your code here that uses settings
    """
    # Patch get_settings in both the original module and all modules that import it
    with (
        patch('app.infra.mysql.mysql_manager') as mock_mysql_manager,
        patch('app.infra.settings.get_settings') as mock_get_settings1,
        patch('app.infra.ocr.get_settings') as mock_get_settings2
    ):
        # Configure the mocks
        mock_mysql_manager.return_value = Mock()
        mock_get_settings1.return_value = mock_settings
        mock_get_settings2.return_value = mock_settings
        
        yield
