
from langchain_community.vectorstores import FAISS

from app.infra import embd
from app.infra.log import logger
from app.infra.settings import SETTINGS
from app.infra.vecstore import get_chroma

chroma_client_instance = None





# def get_chroma_client():
#     global chroma_client_instance
#     if (chroma_client_instance is None):
#         chroma_client_instance = chromadb.HttpClient(host='117.72.39.0', port=18000)
#     return chroma_client_instance
#
#
# def query(collection_name: str, question, n_results: int = 15):
#     chroma_client = get_chroma_client()
#     collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=ollama_embd_function)
#     results = collection.query(
#         query_texts=question,
#         n_results=n_results
#     )
#     return results

def query_lite_mode(collection_name: str, question, k: int = 15):
    # 懒加载磁盘，节省内存
    if SETTINGS.VECTOR_STORE_MODE == "faiss":
        try:
            vector_store = FAISS.load_local(
                folder_path=SETTINGS.FAISS_STORE_PATH,
                embeddings=embd.embed,
                index_name=collection_name, # todo faiss空间中没有文件时会报错
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            logger.warning(e)
            raise Exception(f"加载知识库空间[{collection_name}]报错")
    else:
        vector_store = get_chroma(embedding_function=embd.embed, collection_name=collection_name)

    return vector_store.similarity_search(query=question, k=k)
