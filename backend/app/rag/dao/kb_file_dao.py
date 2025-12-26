from sqlalchemy import func, Column, String, DateTime, SmallInteger, BigInteger, Text, Index, CHAR
from app.infra.mysql import mysql_manager as global_mysql_manager
from typing import List, Optional, Tuple
from app.rag.dao.rag_pipeline_record import RagPipelineRecord

class KbFile(global_mysql_manager.Base):
    __tablename__ = "kb_file"

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 外键关联
    space_id = Column(BigInteger, nullable=False, comment='空间ID')

    # 文档基本信息
    title = Column(String(255), nullable=False, comment='文档标题')

    # 文件信息
    file_name = Column(String(255), nullable=False, comment='原始文件名')
    description = Column(Text, nullable=True, default=None, comment='文档描述')
    file_type = Column(String(64), nullable=False, comment='扩展名 pdf/md/txt...')
    file_size = Column(BigInteger, nullable=False, comment='字节数')
    file_url = Column(String(500), nullable=True, comment='对象存储地址')
    file_hash = Column(CHAR(64), nullable=False, comment='SHA256 去重/秒传')

    # 状态和用户信息
    status = Column(SmallInteger, nullable=False, default=1, comment='0-失效 1-有效')
    user_id = Column(BigInteger, nullable=False, comment='上传人用户ID')

    # 时间戳
    created_at = Column(DateTime(), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(), onupdate=func.now(), server_default=func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        Index('idx_space', 'space_id'),
        Index('idx_hash', 'file_hash'),
        Index('idx_status', 'status'),
    )

class KbFileDAO:
    """知识库文档数据访问对象"""
    def __init__(self, mysql_manager=None):
        self._mysql_manager = mysql_manager or global_mysql_manager

    def create(
            self,
            space_id: int,
            title: str,
            file_name: str,
            file_type: str,
            file_size: int,
            file_hash: str,
            user_id: int,
            file_url: Optional[str] = None,
            description: Optional[str] = None
    ) -> int:
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            kb_file = KbFile(
                space_id=space_id,
                title=title,
                file_name=file_name,
                description=description,
                file_type=file_type,
                file_size=file_size,
                file_url=file_url,
                file_hash=file_hash,
                user_id=user_id
            )
            db.add(kb_file)
            db.commit()
            db.refresh(kb_file)
        return kb_file.id

    def get_by_id(self, id: int) -> Optional[KbFile]:
        with self._mysql_manager.DbSession() as db:
            return db.query(KbFile).filter(KbFile.id == id).first()

    def list_by_query_with_rag_status(self, space_id: int, offset: int, limit: int, status: Optional[int] = 1) -> List[
        Tuple[KbFile, Optional[RagPipelineRecord]]]:
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            # 子查询：获取每个文件最新的pipeline记录
            latest_pipeline_subq = (
                db.query(
                    RagPipelineRecord.file_url.label('file_url'),
                    func.max(RagPipelineRecord.created_at).label('latest_created_at')
                )
                .filter(RagPipelineRecord.file_url.isnot(None))
                .group_by(RagPipelineRecord.file_url)
                .subquery()
            )
            # 主查询
            query = (
                db.query(
                    KbFile,
                    RagPipelineRecord
                )
                .outerjoin(
                    latest_pipeline_subq,
                    KbFile.file_url == latest_pipeline_subq.c.file_url
                )
                .outerjoin(
                    RagPipelineRecord,
                    (RagPipelineRecord.file_url == KbFile.file_url) &
                    (RagPipelineRecord.created_at == latest_pipeline_subq.c.latest_created_at)
                )
                .order_by(KbFile.created_at.desc())
            )
            if space_id > 0:
                query = query.filter(KbFile.space_id == space_id)
            if status is not None:
                query = query.filter(KbFile.status == status)
            return query.order_by(KbFile.created_at.desc()).offset(offset).limit(limit).all()

    def count(self, space_id: int, status: Optional[int] = 1) -> int:
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            query = db.query(KbFile)

            if space_id > 0:
                query = query.filter(KbFile.space_id == space_id)
            if status is not None:
                query = query.filter(KbFile.status == status)

            # 简单的count
            return query.count()

    def update(self, id: int, **kwargs) -> bool:
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            kb_file = db.query(KbFile).filter(KbFile.id == id).first()
            if not kb_file:
                return False

            # 更新提供的字段
            for key, value in kwargs.items():
                if hasattr(kb_file, key):
                    setattr(kb_file, key, value)

            db.commit()
        return True

    def delete(self, id: int) -> bool:
        return self.update(id, status=0)

    def list_by_space_id(self, space_id: int, status: Optional[int] = None) -> List[KbFile]:
        """根据 space_id 查询文件列表"""
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            query = db.query(KbFile).filter(KbFile.space_id == space_id)
            if status is not None:
                query = query.filter(KbFile.status == status)
            return query.order_by(KbFile.created_at.desc()).all()

    def delete_by_space_id(self, space_id: int) -> int:
        with self._mysql_manager.DbSession() as db:
            # 确保表已创建
            self._mysql_manager.Base.metadata.create_all(bind=self._mysql_manager.engine)

            updated_rows = (
                db.query(KbFile)
                .filter(KbFile.space_id == space_id, KbFile.status == 1)
                .update({"status": 0}, synchronize_session=False)
            )
            db.commit()
        return updated_rows

# 创建全局实例
kb_file_dao = KbFileDAO(global_mysql_manager)

