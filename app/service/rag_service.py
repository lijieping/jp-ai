import os
from pathlib import Path

from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from langchain_community.vectorstores import FAISS

from app.infra import vecstore, embd
from app.infra.settings import SETTINGS

chroma_client_instance = None
ollama_embd_function = OllamaEmbeddingFunction(model_name="bge-m3")





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
    vector_store = FAISS.load_local(
        folder_path=SETTINGS.FAISS_STORE_PATH,
        embeddings=embd.embed_dimension[0],
        index_name=collection_name,
        allow_dangerous_deserialization=True
    )
    return vector_store.similarity_search(query=question, k=k)
