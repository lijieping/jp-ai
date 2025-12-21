from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.infra.settings import get_settings


class MySQLManager:
    """MySQL数据库管理器，支持延迟初始化"""

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._base = None
        self._initialized = False

    def initialize(self):
        """延迟初始化数据库连接"""
        if self._initialized:
            return

        mysql_url = get_settings().MYSQL_URL
        self._engine = create_engine(mysql_url, pool_recycle=300)
        self._session_factory = sessionmaker(bind=self._engine, autoflush=True, expire_on_commit=True)
        self._base = declarative_base()
        self._base.metadata.create_all(bind=self._engine)
        self._initialized = True

    @property
    def engine(self):
        """获取数据库引擎"""
        if not self._initialized:
            self.initialize()
        return self._engine

    @property
    def DbSession(self):
        """获取数据库会话"""
        if not self._initialized:
            self.initialize()
        return self._session_factory

    @property
    def Base(self):
        """获取数据库基类"""
        if not self._initialized:
            self.initialize()
        return self._base


# 全局MySQL管理器实例
mysql_manager = MySQLManager()