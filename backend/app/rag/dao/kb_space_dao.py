from sqlalchemy import func, Column, String, DateTime, SmallInteger, BigInteger, Text
from app.infra.mysql import mysql_manager as global_mysql_manager

class KbSpace(global_mysql_manager.Base):
    __tablename__ = "rag_kb_space"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    vector_db_collection = Column(String(128), nullable=False)
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())

class KbSpaceDAO:
    def __init__(self, mysql_manager=None):
        self._mysql_manager = mysql_manager or global_mysql_manager

    def create(self, name:str, description:str, vector_db_collection:str) -> int:
        with self._mysql_manager.DbSession() as db:
            # 创建KbSpace对象
            kb_space = KbSpace(name=name, description=description, vector_db_collection=vector_db_collection)
            db.add(kb_space)
            db.commit()
            # 刷新以确保获取自增的id值
            db.refresh(kb_space)
        return kb_space.id
    
    def list_all(self):
        """获取所有知识库空间"""
        with self._mysql_manager.DbSession() as db:
            return db.query(KbSpace).filter(KbSpace.status==1).all()
    
    def get_by_id(self, id: int) -> KbSpace:
        """根据ID获取知识库空间"""
        with self._mysql_manager.DbSession() as db:
            return db.query(KbSpace).filter(KbSpace.id == id).first()
    
    def update(self, id: int, **kwargs):
        """更新知识库空间信息"""
        with self._mysql_manager.DbSession() as db:
            # 查找要更新的记录
            kb_space = db.query(KbSpace).filter(KbSpace.id == id).first()
            if not kb_space:
                return False
            
            # 更新提供的字段
            for key, value in kwargs.items():
                if hasattr(kb_space, key):
                    setattr(kb_space, key, value)
            
            db.commit()
        return True

    def delete(self, id: int):
        with self._mysql_manager.DbSession() as db:
            kb_space = db.query(KbSpace).filter(KbSpace.id == id).first()
            if not kb_space:
                return False
            kb_space.status = 0
            db.commit()
        return True

# 创建全局实例
kb_space_dao = KbSpaceDAO(global_mysql_manager)

