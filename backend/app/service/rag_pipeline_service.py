from __future__ import annotations

import os
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional, Final

import langchain_text_splitters
from langchain_core.documents import Document
from langchain_excel_loader import StructuredExcelLoader

from app.dao.rag_pipeline_record import rag_pipeline_record_dao, RagPipelineRecordDAO
from app.infra import embd
from app.infra.log import logger
from app.infra.ocr import ocr_parse
from app.infra.vecstore import get_faiss, get_chroma
from app.infra.settings import get_settings
from pathlib import Path
from typing import List

from langchain_community.document_loaders import ( Docx2txtLoader, TextLoader, PyPDFLoader)


# 上下文对象（在整个链里传递）
@dataclass
class Context:
    file_url: str               # 文件地址，流水线自行查询
    collection_name : str       # 调用方指定所属的向量库集合，流水线自行查询
    record_id:int = 0
    file_name:str = None # 文件名带扩展名，流水线自行计算
    ext:str = None # 文件扩展名，流水线自行计算
    # version: int
    pages:List[Document] = None # 清洗产物 #todo用完销毁，节省内存
    chunks: List[Document] = None # 分块产物 #todo用完销毁，节省内存
    success: bool = True
    message: str = None

# 抽象处理者
class Handler(ABC):
    _next: Optional["Handler"] = None
    _rag_pipeline_record_dao: rag_pipeline_record_dao.__class__

    def __init__(self):
        self._rag_pipeline_record_dao = rag_pipeline_record_dao

    def set_next(self, handler: "Handler") -> "Handler":
        self._next = handler
        return handler

    def handle(self, ctx: Context) -> None:
        logger.info("[%s] begin", self.__class__.__name__)
        try:
            self.process(ctx)
        except Exception as e:
            ctx.success = False
            error_trace = traceback.format_exc()
            ctx.message = error_trace
        finally:
            logger.info("[%s] end, success:%s, message:%s", self.__class__.__name__, ctx.success, ctx.message)

        if ctx.success and self._next:
            self._next.handle(ctx)
        else:
            # 更新状态记录
            status = 2 if ctx.success else 3
            self._rag_pipeline_record_dao.update(record_id=ctx.record_id, status=status, msg=ctx.message)

    @abstractmethod
    def process(self, ctx: Context) -> None:
        raise NotImplementedError

# 具体处理者
class FileParseHandler(Handler):
    """todo 版式还原、跨页表格合并、代码语法树解析：
        Unstructured质量更高，且自带版面还原，页脚去除等，但需要安装各种模型，比较重
    """

    _support_exts = {
        "text": {"name": "文本类",
                 "exts": {".txt", ".md", ".html", ".xml", ".json", ".py", ".java", ".c", ".cpp", ".csv"}},
        "excel": {"name": "excel表格", "exts": {".xlsx"}},
        "word": {"name": "word文档", "exts": {".docx"}},
        "pdf": {"name": "pdf", "exts": {".pdf"}},
        "img": {"name": "图片", "exts": {".png", ".jpg", ".jpeg", ".bmp"}}
    }

    def process(self, ctx: Context) -> None:
        path = Path(ctx.file_url)
        # 获取文件名（带扩展名）
        ctx.file_name = os.path.basename(path)
        # 获取扩展名
        ctx.ext = path.suffix
        if ctx.ext in self._support_exts["text"]["exts"]:
            ctx.pages = TextLoader(ctx.file_url).load()
        elif ctx.ext in self._support_exts["excel"]["exts"]:
            ctx.pages = StructuredExcelLoader(ctx.file_url).load()
        elif ctx.ext in self._support_exts["word"]["exts"]:
            # ctx.docs = UnstructuredWordDocumentLoader(ctx.file_url).load()
            ctx.pages = Docx2txtLoader(ctx.file_url).load()
        elif ctx.ext in self._support_exts["pdf"]["exts"]:
            # 文字部分
            ctx.pages = PyPDFLoader(ctx.file_url).load()
        # 3. 纯图片格式
        elif ctx.ext in self._support_exts["img"]["exts"]:
            texts = ocr_parse(ctx.file_url)
            ctx.pages = [Document(page_content=text) for text in texts]
        # 4. 其他 → 抛异常 or 按需扩展
        else:
            raise ValueError(f"unsupported ext: {ctx.ext}")

class ChunkHandler(Handler):
    """ todo 语意分块 """
    _text_splitter = langchain_text_splitters.RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " ", ""],
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )
    def process(self, ctx: Context) -> None:
        ctx.chunks = ChunkHandler._text_splitter.split_documents(ctx.pages)


class EmbedAStoreHandler(Handler):
    def process(self, ctx: Context) -> None:
        embedding_func = embd.embed
        texts = [doc.page_content for doc in ctx.chunks]
        if get_settings().VECTOR_STORE_MODE == "faiss":
            vector_store = get_faiss(embedding_func, collection_name=ctx.collection_name)
            vector_store.add_documents(documents=ctx.chunks)
        else:
            vector_store = get_chroma(embedding_func, collection_name=ctx.collection_name)
            vector_store.add_texts(texts)

class RagPipelineService:
    def __init__(self, rag_pipeline_record_dao: RagPipelineRecordDAO):
        self._rag_pipeline_record_dao = rag_pipeline_record_dao
        # 模块级单例
        self._chain_head: Final[Handler] = FileParseHandler()
        self._chain_head.set_next(ChunkHandler()).set_next(EmbedAStoreHandler())
        # 线程池
        self._executor: Final[ThreadPoolExecutor] = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="RAG-Chain"
        )

    def submit(self, file_url: str, collection_name:str) -> None:
        """非阻塞提交：把整条链当成一个 Task 扔进线程池"""
        record_id = self._rag_pipeline_record_dao.create(file_url, 1, 1, None)
        ctx = Context(file_url=file_url, collection_name=collection_name, record_id=record_id)
        self._executor.submit(self._chain_head.handle, ctx)

    def get_support_exts(self) -> dict:
        return FileParseHandler._support_exts.copy()

    def get_support_ext_set(self) -> set:
        return set().union(*(v['exts'] for v in FileParseHandler._support_exts.values()))

# 创建全局实例
rag_pipeline_service = RagPipelineService(rag_pipeline_record_dao)





