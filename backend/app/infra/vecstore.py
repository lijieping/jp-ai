import uuid
from typing import Any, Iterable, List, Optional, Callable, Dict, Union

import numpy as np
from langchain_chroma import Chroma
from langchain_community.docstore import InMemoryDocstore
from langchain_community.docstore.base import AddableMixin, Docstore
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.faiss import dependable_faiss_import, _len_check_if_sized
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.infra.settings import get_settings


class _CUSTOM_FAISS(FAISS):
    """自己写FAISS类，继承社区版类，支持saveDocs"""

    def __init__(self,
                 embedding_function: Union[
                     Callable[[str], List[float]],
                     Embeddings,
                 ],
                 index: Any,
                 docstore: Docstore,
                 index_to_docstore_id: Dict[int, str],
                 index_name: str):
        super().__init__(embedding_function, index, docstore, index_to_docstore_id)
        self.index_name = index_name

    def add_documents(self, documents: list[Document], **kwargs: Any) -> list[str]:
        """Add or update documents in the `VectorStore`.

        Args:
            documents: Documents to add to the `VectorStore`.
            **kwargs: Additional keyword arguments.

                If kwargs contains IDs and documents contain ids, the IDs in the kwargs
                will receive precedence.

        Returns:
            List of IDs of the added texts.
        """
        # texts, metadatas = map(list, zip(*[(doc.page_content, doc.metadata) for doc in documents]))

        texts, metadatas = [], []
        for doc in documents:
            texts.append(doc.page_content)
            metadatas.append(doc.metadata)
        embeddings: Iterable[List[float]] = self.embedding_function.embed_documents(texts)
        ids: Optional[List[str]] = kwargs.pop("ids", None)
        dim = len(embeddings[0])

        from faiss import IndexFlatL2 # 此处import 防止chroma模式还要load faiss的IndexFlatL2
        self.index = IndexFlatL2(dim)

        faiss = dependable_faiss_import()
        if not isinstance(self.docstore, AddableMixin):
            raise ValueError(
                "If trying to add texts, the underlying docstore should support "
                f"adding items, which {self.docstore} does not"
            )

        _len_check_if_sized(texts, metadatas, "texts", "metadatas")

        ids = ids or [str(uuid.uuid4()) for _ in texts]
        _len_check_if_sized(texts, ids, "texts", "ids")

        _metadatas = metadatas or ({} for _ in texts)
        documents = [
            Document(id=id_, page_content=t, metadata=m)
            for id_, t, m in zip(ids, texts, _metadatas)
        ]

        _len_check_if_sized(documents, embeddings, "documents", "embeddings")

        if ids and len(ids) != len(set(ids)):
            raise ValueError("Duplicate ids found in the ids list.")
        # Add to the index.
        vector = np.array(embeddings, dtype=np.float32)
        if self._normalize_L2:
            faiss.normalize_L2(vector)
        self.index.add(vector)

        # Add information to docstore and index.
        self.docstore.add({id_: doc for id_, doc in zip(ids, documents)})
        starting_len = len(self.index_to_docstore_id)
        index_to_id = {starting_len + j: id_ for j, id_ in enumerate(ids)}
        self.index_to_docstore_id.update(index_to_id)

        settings = get_settings()
        self.save_local(folder_path=settings.FAISS_STORE_PATH, index_name=self.index_name)  # 此处为新加
        return ids


def get_faiss(embedding_function: Embeddings, collection_name: str) -> FAISS:
    settings = get_settings()
    if settings.VECTOR_STORE_MODE == "faiss":
        return _CUSTOM_FAISS(
            embedding_function=embedding_function,
            docstore=InMemoryDocstore(),  # langchain外挂kv内存， key：chunk_id，value：文档
            index_to_docstore_id={},  # langchain外挂索引， key：从小到大的序号，value：chunk_id
            index_name=collection_name,
            index=None
        )
    raise ValueError(f"非法的VECTOR_STORE_MODE={settings.VECTOR_STORE_MODE}")


def get_chroma(embedding_function: Embeddings, collection_name: str) -> Chroma:
    settings = get_settings()
    if settings.VECTOR_STORE_MODE == "chroma":
        return Chroma(collection_name=collection_name, embedding_function=embedding_function, host=settings.CHROMA_HOST,
                      port=settings.CHROMA_PORT)
    raise ValueError(f"非法的VECTOR_STORE_MODE={settings.VECTOR_STORE_MODE}")
