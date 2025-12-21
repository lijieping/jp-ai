from typing import List, Optional
from pathlib import Path

from fastapi import UploadFile

from app.infra.files import local_file_save, local_file_delete
from app.infra.log import logger
from app.schemas.page_schema import Page

from app.dao.kb_space_dao import kb_space_dao, KbSpaceDAO
from app.dao.kb_file_dao import kb_file_dao, KbFileDAO
from app.dao.user_dao import user_dao, UserDAO
from app.schemas.kb_space_schema import KbSpaceOut, KbSpaceIn
from app.schemas.kb_file_schema import KbFileWithPipelineRecordOut, KbFileOut

from app.service.rag_pipeline_service import rag_pipeline_service

class KnowledgeService:
    def __init__(self, kb_space_dao: KbSpaceDAO, kb_file_dao: KbFileDAO, user_dao: UserDAO):
        self._kb_space_dao = kb_space_dao
        self._kb_file_dao = kb_file_dao
        self._user_dao = user_dao

    def space_create(self, name:str, desc:str, vector_db_collection:str):
        id = self._kb_space_dao.create(name=name, description=desc, vector_db_collection=vector_db_collection)
        return id

    def space_list_all(self) -> List[KbSpaceOut]:
        """获取所有知识库空间列表，返回KbSpaceOut对象列表"""
        kb_spaces = self._kb_space_dao.list_all()
        # 转换为KbSpaceOut对象列表
        return [
            KbSpaceOut(
                id=space.id,
                name=space.name,
                desc=space.description,
                collection=space.vector_db_collection
            )
            for space in kb_spaces
        ]

    def space_get_by_id(self, id: str) -> Optional[KbSpaceOut]:
        """根据ID获取知识库空间，返回KbSpaceOut对象"""
        space = self._kb_space_dao.get_by_id(id)
        if space:
            return KbSpaceOut(
                id=space.id,
                name=space.name,
                desc=space.description,
                collection=space.vector_db_collection
            )
        return None

    def space_delete(self, space_id: int) -> bool:
        """删除知识库空间"""
        # 检查空间是否存在
        space = self._kb_space_dao.get_by_id(space_id)
        if not space:
            raise ValueError(f"知识库空间ID {space_id} 不存在")
        
        # 删除空间下所有文件
        self.file_delete_by_space_id(space_id)   
        # 删除空间（DAO层会处理关联文件的级联删除）
        return self._kb_space_dao.delete(space_id)

    def space_update(self, id: int, kb_space_in: KbSpaceIn) -> bool:
        """更新知识库空间信息，接受KbSpaceIn对象"""
        # 将KbSpaceIn对象转换为字典，注意字段映射
        update_data = {
            'name': kb_space_in.name,
            'description': kb_space_in.desc,
            'vector_db_collection': kb_space_in.collection
        }
        return self._kb_space_dao.update(id, **update_data)

    def file_upload(self, space_id: int, file_datas:List[UploadFile], user_id: int, description: str = ""):
        # 验证知识库空间是否存在
        space = self._kb_space_dao.get_by_id(space_id)
        if not space:
            raise ValueError(f"知识库空间ID {space_id} 不存在")

        support_exts = rag_pipeline_service.get_support_ext_set()
        invalid_exts = set()
        for file_data in file_datas:
            # 检查文件扩展名是否被支持
            file_extension = Path(file_data.filename).suffix.lower()
            if file_extension not in support_exts:
                invalid_exts.add(file_extension)
        if len(invalid_exts) > 0:
            raise ValueError(f"rag不支持的文件类型：: {invalid_exts}")

        for file_data in file_datas:
            # 提取文件信息
            file_name = file_data.filename
            file_extension = Path(file_name).suffix.lower()
            title = Path(file_name).stem
            # 存储本地
            file_url,file_size,file_hash = local_file_save(file_data.file, "kb/" + str(space_id), file_name)
            # 文件信息入库
            doc_id = self._kb_file_dao.create(
                space_id=space_id,
                title=title,
                file_name=file_name,
                description=description or "",  # 使用传入的描述，如果为空则使用空字符串
                file_type=file_extension,
                file_size=file_size,
                file_hash=file_hash,
                user_id=user_id,
                file_url=file_url
            )

            rag_pipeline_service.submit(file_url, space.vector_db_collection)

    def file_get_by_id(self, id: int) -> Optional[KbFileOut]:
        doc = self._kb_file_dao.get_by_id(id)
        if not doc:
            return None

        # 获取空间信息
        space = self._kb_space_dao.get_by_id(doc.space_id)
        space_name = space.name if space else "未知空间"

        return KbFileOut(
            id=doc.id,
            file_name=doc.file_name,
            file_type=doc.file_type,
            file_size=doc.file_size,
            file_url=doc.file_url or "",
            created_at=doc.created_at.isoformat() if doc.created_at else "",
            user_id=doc.user_id,
            user_name="未知用户",
            space_id=doc.space_id,
            space_name=space_name,
            collection=space.vector_db_collection if space else "",
            description=doc.description or "",
            status=doc.status
        )

    def file_delete(self, id: int) -> Optional[bool]:
        file = self._kb_file_dao.get_by_id(id)
        local_file_delete(file.file_url)
        return self._kb_file_dao.delete(id)

    def file_delete_by_space_id(self, space_id: int) -> bool:
        files = self._kb_file_dao.list_by_space_id(space_id, None)
        if not files:
            return True 
        for file in files:
            if file.file_url:
                try:
                    local_file_delete(file.file_url)
                except Exception as e:
                    logger.warning("删除文件失败: %s, 错误: %s", file.file_url, e)
                    pass
        return self._kb_file_dao.delete_by_space_id(space_id) > 0

    def file_with_rag_info_list(self, space_id: int = 0, page_size: int = 10, cur_page: int = 1) -> Page[KbFileWithPipelineRecordOut]:
        # 参数验证
        if page_size <= 0 or cur_page <= 0:
            raise ValueError("page_size和cur_page必须大于0")
        
        # 非零space_id需要验证空间是否存在
        if space_id != 0:
            space = self._kb_space_dao.get_by_id(space_id)
            if not space:
                raise ValueError(f"知识库空间ID {space_id} 不存在")
        
        # 计算偏移量
        offset = (cur_page - 1) * page_size

        paginated_files_with_rag = self._kb_file_dao.list_by_query_with_rag_status(space_id=space_id, offset=offset, limit=page_size)
        total_count = self._kb_file_dao.count(space_id)
        
        # 收集所有用户ID
        user_ids = {file.user_id for file, _ in paginated_files_with_rag if file.user_id}
        
        # 获取用户信息字典
        user_dict = self._user_dao.list_by_ids(list(user_ids))
        
        # 转换为KbFileOut对象列表
        files = []
        for file, rag_record in paginated_files_with_rag:
            # 获取空间信息（用于space_name）
            space = self._kb_space_dao.get_by_id(file.space_id)
            space_name = space.name if space else "未知空间"
            
            # 获取RAG状态和消息，如果没有RAG记录则使用默认值
            rag_status = rag_record.status if rag_record else 0
            rag_msg = rag_record.msg if rag_record else None
            
            # 获取用户名
            user_name = user_dict[file.user_id].username if file.user_id and file.user_id in user_dict else "未知用户"
            
            # 创建KbFileOut对象
            kb_file = KbFileWithPipelineRecordOut(
                id=file.id,
                file_name=file.file_name,
                file_type=file.file_type,
                file_size=file.file_size,
                file_url=file.file_url or "",  # 确保不为None
                created_at=file.created_at.isoformat() if file.created_at else "",
                user_id=file.user_id,
                user_name=user_name,
                space_id=file.space_id,
                space_name=space_name,
                collection=space.vector_db_collection if space else "",
                description=file.description or "",  # 使用description字段
                status=file.status,  # 文件状态
                rag_status=rag_status,  # RAG pipeline状态
                msg=rag_msg  # 添加RAG消息
            )
            files.append(kb_file)
        
        # 返回Page包装对象
        return Page(total=total_count, page_size=page_size, cur_page=cur_page, list=files)

# 创建全局实例
knowledge_service = KnowledgeService(kb_space_dao, kb_file_dao, user_dao)

