import random
import threading
from typing import Any, Iterator, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple, Checkpoint, CheckpointMetadata, \
    ChannelVersions
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

from app.infra.agent_memory import get_agent_memory
from app.infra.mysql import mysql_manager


class HybridCheckpointSaver(BaseCheckpointSaver):
    def __init__(self) -> None:
        super().__init__()
        self._cache_saver = get_agent_memory()
        # 初始化时执行一次setup，确保表已创建
        _db_saver = PyMySQLSaver(conn=mysql_manager.engine.pool.connect())
        _db_saver.setup()

    def get_db_saver(self) -> PyMySQLSaver:
        # 每次调用都从连接池获取新连接，确保线程安全
        return PyMySQLSaver(conn=mysql_manager.engine.pool.connect())

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        tup = self._cache_saver.get_tuple(config)
        if tup is None:
            tup = self.get_db_saver().get_tuple(config)
            if tup is None:
                return None
            self._cache_saver.put(tup.config, tup.checkpoint, tup.metadata, {})
        return tup

    def list(
            self,
            config: RunnableConfig | None,
            *,
            filter: dict[str, Any] | None = None,
            before: RunnableConfig | None = None,
            limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:

        return self.get_db_saver().list(config, filter=filter, before=before, limit=limit)

    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        self.get_db_saver().put(config, checkpoint, metadata, new_versions)
        return self._cache_saver.put(config, checkpoint, metadata, new_versions)

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:

        self.get_db_saver().put_writes(config, writes, task_id, task_path)
        return self._cache_saver.put_writes(config, writes, task_id, task_path)

    def delete_thread(
            self,
            thread_id: str,
    ) -> None:
        self.get_db_saver().delete_thread(thread_id)
        self._cache_saver.delete_thread(thread_id)
        raise NotImplementedError

    def get_next_version(self, current: str | None, channel: None) -> str:
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(current.split(".")[0])
        next_v = current_v + 1
        next_h = random.random()
        return f"{next_v:032}.{next_h:016}"


# 全局单例实例
_hybrid_checkpoint_saver: HybridCheckpointSaver | None = None
_hybrid_checkpoint_saver_lock = threading.Lock()


def get_hybrid_checkpoint_saver() -> HybridCheckpointSaver:
    global _hybrid_checkpoint_saver
    
    if _hybrid_checkpoint_saver is not None:
        return _hybrid_checkpoint_saver
    
    with _hybrid_checkpoint_saver_lock:
        if _hybrid_checkpoint_saver is None:
            _hybrid_checkpoint_saver = HybridCheckpointSaver()
        return _hybrid_checkpoint_saver

