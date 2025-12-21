
from langchain_community.vectorstores import FAISS

from app.infra import embd
from app.infra.log import logger
from app.infra.settings import SETTINGS
from app.infra.vecstore import get_chroma

class RagService:
    def __init__(self, embedding_func=None, settings=None, chroma_func=None):
        self._embedding_func = embedding_func or embd.embed
        self._settings = settings or SETTINGS
        self._chroma_func = chroma_func or get_chroma

    def query_lite_mode(self, collection_name: str, question, k: int = 15):
        # 懒加载磁盘，节省内存
        if self._settings.VECTOR_STORE_MODE == "faiss":
            try:
                vector_store = FAISS.load_local(
                    folder_path=self._settings.FAISS_STORE_PATH,
                    embeddings=self._embedding_func,
                    index_name=collection_name, # todo faiss空间中没有文件时会报错
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                logger.warning(e)
                raise Exception(f"加载知识库空间[{collection_name}]报错")
        else:
            vector_store = self._chroma_func(embedding_function=self._embedding_func, collection_name=collection_name)

        res_docs = vector_store.similarity_search(query=question, k=k)
        logger.info("similarity search question=%s, k=%d, result=%s", question, k, [res_doc.model_dump_json() for res_doc in res_docs])

        return res_docs

# 创建全局实例
rag_service = RagService()
