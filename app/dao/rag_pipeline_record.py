from sqlalchemy import func, Column, String, DateTime, SmallInteger, BigInteger, Index, Text
from app.infra.mysql import Base, DbSession
from typing import Optional


class RagPipelineRecord(Base):
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
    
    @staticmethod
    def create(
        file_url: str,
        file_version: int = 1,
        status: int = 0,
        msg: str = None
    ) -> int:
        with DbSession() as db:
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

    @staticmethod
    def update(
        record_id: int,
        status: Optional[int] = None,
        msg: str = None
    ) -> bool:
        with DbSession() as db:
            record = db.query(RagPipelineRecord).filter_by(id=record_id).first()
            if not record:
                return False
                
            if status is not None:
                record.status = status
            if msg is not None:
                record.msg = msg
                
            db.commit()
        return True
