from typing import Any, List, Literal, Optional, Sequence, cast, ClassVar

import numpy as np
from pydantic import BaseModel, ConfigDict

from app.infra.settings import get_settings

MIN_VERSION = "0.2.0"

import fastembed
from langchain_core.embeddings import Embeddings

"""自己写FastEmbedEmbeddings，指定模型存储路径"""
class FastEmbedBgeSmallEnV15(BaseModel, Embeddings):
    """Qdrant FastEmbedding models.

    FastEmbed is a lightweight, fast, Python library built for embedding generation.
    See more documentation at:
    * https://github.com/qdrant/fastembed/
    * https://qdrant.github.io/fastembed/

    To use this class, you must install the `fastembed` Python package.

    `pip install fastembed`
    Example:
        from langchain_community.embeddings import FastEmbedEmbeddings
        fastembed = FastEmbedEmbeddings()
    """

    model_name: str = "BAAI/bge-small-en-v1.5"
    """Name of the FastEmbedding model to use
    Defaults to "BAAI/bge-small-en-v1.5"
    Find the list of supported models at
    https://qdrant.github.io/fastembed/examples/Supported_Models/
    """

    max_length: int = 512
    """The maximum number of tokens. Defaults to 512.
    Unknown behavior for values > 512.
    """

    cache_dir: Optional[str] = None
    """The path to the cache directory.
    Defaults to `local_cache` in the parent directory
    """

    threads: Optional[int] = None
    """The number of threads single onnxruntime session can use.
    Defaults to None
    """

    doc_embed_type: Literal["default", "passage"] = "default"
    """Type of embedding to use for documents
    The available options are: "default" and "passage"
    """

    batch_size: int = 256
    """Batch size for encoding. Higher values will use more memory, but be faster.
    Defaults to 256.
    """

    parallel: Optional[int] = None
    """If `>1`, parallel encoding is used, recommended for encoding of large datasets.
    If `0`, use all available cores.
    If `None`, don't use data-parallel processing, use default onnxruntime threading.
    Defaults to `None`.
    """

    providers: Optional[Sequence[Any]] = None
    """List of ONNX execution providers. Use `["CUDAExecutionProvider"]` to enable the
    use of GPU when generating embeddings. This requires to install `fastembed-gpu`
    instead of `fastembed`. See https://qdrant.github.io/fastembed/examples/FastEmbed_GPU
    for more details.
    Defaults to `None`.
    """

    dim: ClassVar[int] = 384

    _model: Any = None
    """模型实例，懒加载"""

    model_config = ConfigDict(extra="allow", protected_namespaces=())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 延迟初始化模型
        self._model = None

    @property
    def model(self):
        """懒加载模型实例，确保线程安全"""
        if self._model is None:
            # 懒加载模型
            self._model = fastembed.TextEmbedding(
                model_name=self.model_name,
                max_length=self.max_length,
                threads=self.threads or 4,
                providers=self.providers,
                specific_model_path=get_settings().MODEL_BGE_SMALL_EN_V15_STORE_PATH
            )
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents using FastEmbed.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        embeddings: List[np.ndarray]
        if self.doc_embed_type == "passage":
            embeddings = self.model.passage_embed(
                texts, batch_size=self.batch_size, parallel=self.parallel
            )
        else:
            embeddings = self.model.embed(
                texts, batch_size=self.batch_size, parallel=self.parallel
            )
        return [cast(List[float], e.tolist()) for e in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """Generate query embeddings using FastEmbed.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        query_embeddings: np.ndarray = next(
            self.model.query_embed(
                text, batch_size=self.batch_size, parallel=self.parallel
            )
        )
        return cast(List[float], query_embeddings.tolist())


# 单实例模式，使用模块级别的缓存
_embed_instance = None

def _init_embed() -> Embeddings:
    """初始化嵌入模型实例，确保只创建一个实例"""
    global _embed_instance
    if _embed_instance is None:
        _embed_instance = FastEmbedBgeSmallEnV15()
    return _embed_instance

# 创建全局单实例
embed = _init_embed()
