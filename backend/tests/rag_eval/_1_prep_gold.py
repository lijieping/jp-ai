import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.infra.embd import embed

""" 把黄金数据灌库（一次即可） """

def run_prep_gold():
    current_dir = Path(__file__).parent.absolute()
    faiss_file = current_dir / f"gold_chunk_vectors.faiss"
    if faiss_file.exists():
        print("FAISS 黄金索引已存在，跳过初始化。")
        return

    with open(current_dir / "gold_chunks.json", encoding="utf-8-sig") as f:
        gold_chunks = json.load(f)
    docs = [
        Document(
            page_content=gold_chunk["text"],
            metadata=gold_chunk["meta"],
            uid=gold_chunk["chunk_id"]
        ) for gold_chunk in gold_chunks
    ]

    # embedding算法必须和主业务一致，这里直接复用保证一致
    embeddings = embed

    # 持久化到磁盘，黄金数据不变不用重新embedding，这里用faiss
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(folder_path=str(current_dir), index_name="gold_chunk_vectors")

run_prep_gold()
