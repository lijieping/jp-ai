from typing import Optional

from sqlalchemy import func, Column, String, DateTime, SmallInteger, BigInteger, Index, Text
from app.infra.mysql import mysql_manager as global_mysql_manager

class RagPipelineRecord(global_mysql_manager.Base):
    __tablename__ = "rag_pipeline_record"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_url = Column(String(500), nullable=True, comment='对象存储地址')
    file_version = Column(BigInteger, nullable=False, default=1, comment='文件版本')
    status = Column(SmallInteger, nullable=False, default=0, comment='0=未执行 1=执行中 2=执行成功 3执行失败')
    msg = Column(Text, nullable=True)
    created_at = Column(DateTime(), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(), onupdate=func.now(), server_default=func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        Index('uk_file_version', 'file_url', 'file_version', unique=True),
        Index('idx_status_updated', 'status', 'updated_at'),
    )

class RagPipelineRecordDAO:
    """RAG流水线记录数据访问对象，支持延迟初始化"""
    def __init__(self, mysql_manager=None):
        self._mysql_manager = mysql_manager or global_mysql_manager

    def create(
        self,
        file_url: str,
        file_version: int = 1,
        status: int = 0,
        msg: str = None
    ) -> int:
        """创建RAG流水线记录"""
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            record = RagPipelineRecord(
                file_url=file_url,
                file_version=file_version,
                status=status,
                msg=msg
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        return record.id

    def update(
        self,
        record_id: int,
        status: Optional[int] = None,
        msg: str = None
    ) -> bool:
        """更新RAG流水线记录"""
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            record = db.query(RagPipelineRecord).filter_by(id=record_id).first()
            if not record:
                return False

            if status is not None:
                record.status = status
            if msg is not None:
                record.msg = msg

            db.commit()
        return True

# 创建全局实例
rag_pipeline_record_dao = RagPipelineRecordDAO(global_mysql_manager)

