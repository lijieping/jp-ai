from typing import Any, List, Literal, Optional, Sequence, cast, Tuple, ClassVar

import numpy as np
from pydantic import BaseModel, ConfigDict

from app.infra.settings import SETTINGS

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

    model: Any =  fastembed.TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            max_length=512,
            threads=4,
            providers=None,
            specific_model_path=SETTINGS.MODEL_BGE_SMALL_EN_V15_STORE_PATH
        )

    model_config = ConfigDict(extra="allow", protected_namespaces=())

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


def _init_embed() -> Embeddings:
    #if SETTINGS.PROJECT_MODE == "lite":
        return FastEmbedBgeSmallEnV15()

embed = _init_embed()
