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

from app.dao.rag_pipeline_record import RagPipelineRecordDAO
from app.infra import embd
from app.infra.log import logger
from app.infra.vecstore import get_faiss, get_chroma
from app.infra.settings import SETTINGS
from pathlib import Path
from typing import List

import easyocr
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
            RagPipelineRecordDAO.update(record_id=ctx.record_id, status=status, msg=ctx.message)

    @abstractmethod
    def process(self, ctx: Context) -> None:
        raise NotImplementedError


# 具体处理者
class _DataCleanHandler(Handler):
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

    _easyocr_reader = easyocr.Reader(["ch_sim"], False) # langlist里的语言如果本地没有对应模型，会触发下载

    def process(self, ctx: Context) -> None:
        path = Path(ctx.file_url)
        # 获取文件名（带扩展名）
        ctx.file_name = os.path.basename(path)
        # 获取扩展名
        ctx.ext = path.suffix
        if ctx.ext in self._support_exts["text"]["exts"]:
            ctx.pages = TextLoader(ctx.file_url).load()
        # elif ctx.ext == ".csv":
        #     ctx.docs = UnstructuredCSVLoader(ctx.file_url).load()
        elif ctx.ext in self._support_exts["excel"]["exts"]:
            ctx.pages = StructuredExcelLoader(ctx.file_url).load()
        elif ctx.ext in self._support_exts["word"]["exts"]:
            # ctx.docs = UnstructuredWordDocumentLoader(ctx.file_url).load()
            ctx.pages = Docx2txtLoader(ctx.file_url).load()
        # elif ctx.ext == ".pptx":
        #     ctx.docs = UnstructuredPowerPointLoader(ctx.file_url).load()
        elif ctx.ext in self._support_exts["pdf"]["exts"]:
            # 文字部分
            ctx.pages = PyPDFLoader(ctx.file_url).load()
            # todo 图片部分， 拿到图的位置并ocr，把ocr结果按位置插入到文字中， 或者直接上unstructure
        # 3. 纯图片格式
        elif ctx.ext in self._support_exts["img"]["exts"]:
            texts = self._easyocr_reader.readtext(ctx.file_url, detail=0)
            ctx.pages = [Document(page_content=text) for text in texts]
        # 4. 其他 → 抛异常 or 按需扩展
        else:
            raise ValueError(f"unsupported ext: {ctx.ext}")

class _ChunkHandler(Handler):
    """ todo 语意分块 """
    _text_splitter = langchain_text_splitters.RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " ", ""],
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )
    def process(self, ctx: Context) -> None:
        ctx.chunks = _ChunkHandler._text_splitter.split_documents(ctx.pages)


class _EmbedAStoreHandler(Handler):
    def process(self, ctx: Context) -> None:
        embedding_func = embd.embed
        texts = [doc.page_content for doc in ctx.chunks]
        if SETTINGS.VECTOR_STORE_MODE == "faiss":
            vector_store = get_faiss(embedding_func, collection_name=ctx.collection_name)
            vector_store.add_documents(documents=ctx.chunks)
        else:
            vector_store = get_chroma(embedding_func, collection_name=ctx.collection_name)
            vector_store.add_texts(texts)

# 模块级单例
_chain_head : Final[Handler] = _DataCleanHandler()
_chain_head.set_next(_ChunkHandler()).set_next(_EmbedAStoreHandler())

# 线程池
_executor: Final[ThreadPoolExecutor] = ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="RAG-Chain"
)

# 对外部暴露的接口
# 1、流水线开始处理文件
def submit(file_url: str, collection_name:str) -> None:
    """非阻塞提交：把整条链当成一个 Task 扔进线程池"""
    record_id = RagPipelineRecordDAO.create(file_url, 1, 1, None)
    ctx = Context(file_url=file_url, collection_name=collection_name, record_id=record_id)
    _executor.submit(_chain_head.handle, ctx)

# 2、查询支持的文件类型
def get_support_exts() -> dict:
    return _DataCleanHandler._support_exts.copy()





