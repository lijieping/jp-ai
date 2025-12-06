from sqlalchemy import func, Column, String, DateTime, SmallInteger, BigInteger, Text
from app.infra.mysql import Base, DbSession


class KbSpace(Base):
    __tablename__ = "rag_kb_space"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    vector_db_collection = Column(String(128), nullable=False)
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())

class KbSpaceDAO:
    @staticmethod
    def create(name:str, description:str, vector_db_collection:str) -> int:
        with DbSession() as db:
            # 创建KbSpace对象
            kb_space = KbSpace(name=name, description=description, vector_db_collection=vector_db_collection)
            db.add(kb_space)
            db.commit()
            # 刷新以确保获取自增的id值
            db.refresh(kb_space)
        return kb_space.id
    
    @staticmethod
    def list_all():
        """获取所有知识库空间"""
        with DbSession() as db:
            return db.query(KbSpace).all()
    
    @staticmethod
    def get_by_id(id: str):
        """根据ID获取知识库空间"""
        with DbSession() as db:
            return db.query(KbSpace).filter(KbSpace.id == id).first()
    
    @staticmethod
    def update(id: str, **kwargs):
        """更新知识库空间信息"""
        with DbSession() as db:
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
