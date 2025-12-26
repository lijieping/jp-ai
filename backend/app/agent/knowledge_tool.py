from typing import Any

from langchain_community.tools.asknews.tool import SearchInput
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.rag.service import rag_service


class KnowledgeTool(BaseTool):
    name: str
    description: str
    args_schema: type[BaseModel] = SearchInput
    vector_collection: str

    def _run(self, query: str, *args: Any, **kwargs: Any) -> str:
        return rag_service.query_lite_mode(self.vector_collection, question=query)