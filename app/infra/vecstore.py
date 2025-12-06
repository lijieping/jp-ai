import uuid
from typing import Any, Iterable, List, Optional

import faiss
import numpy as np
from langchain_community.docstore import InMemoryDocstore
from langchain_community.docstore.base import AddableMixin
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.faiss import dependable_faiss_import, _len_check_if_sized
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


class _CUSTOM_FAISS(FAISS):
    """自己写FAISS类，继承社区版类，支持saveDocs"""

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
        return ids


def get_vecstore(embedding_function: Embeddings, dimension: int):
    # todo 模式切换chroma、milvus
    index = faiss.IndexFlatL2(dimension)
    return _CUSTOM_FAISS(
        embedding_function=embedding_function,
        index=index,  # faiss原生index
        docstore=InMemoryDocstore(),  # langchain外挂kv内存， key：chunk_id，value：文档
        index_to_docstore_id={}  # langchain外挂索引， key：从小到大的序号，value：chunk_id
    )
