import asyncio
import random
from typing import Any, Iterator, Sequence

from langchain.agents.middleware import SummarizationMiddleware, before_model
from langchain_community.chat_models import ChatTongyi
from langchain_community.tools.asknews.tool import SearchInput
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import RemoveMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple, Checkpoint, CheckpointMetadata, \
    ChannelVersions
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from langchain.agents import create_agent, AgentState
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime
import langsmith as ls
from pydantic import BaseModel

from app.infra.agent_memory import get_agent_memory
from app.infra.log import logger
from app.infra.mysql import engine
from app.infra.settings import SETTINGS
from app.service import rag_service
from app.service import knowledge_service

def init_small_model() -> BaseChatModel:
    model_name = "qwen2.5-3b-instruct"
    # 创建千问model对象，要确保已设置api_key到系统变量DASHSCOPE_API_KEY
    return ChatTongyi(model=model_name)


def small_model_service(question: str) -> str:
    model = init_small_model()
    """轻量模型服务，为系统做一些简单的工作"""
    with ls.tracing_context(enabled=True, project_name="small-model"):
        ai_msg = model.invoke(question)
        return ai_msg.content


def token_generator(question: str, conversation_id: str):
    # 配置对话id，用于记忆对话上下文
    config = RunnableConfig(configurable={"thread_id": conversation_id})
    agent = initialize_agent()
    with ls.tracing_context(enabled=True, project_name="jp-ai"):
        for token, metadata in agent.stream(
                {"messages": [HumanMessage(content=question)]},
                config=config,
                stream_mode="messages"  # messages模式，最细粒度，逐字
        ):
            """token:消息块； metadata：元数据，不暴露给业务"""
            #print(f"=========conv_id:%s, chunk:%s", conversation_id, token)
            yield token


class HybridCheckpointSaver(BaseCheckpointSaver):
    def __init__(self) -> None:
        super().__init__()
        self._cache_saver = get_agent_memory()
        self._db_saver = PyMySQLSaver(conn=engine.pool.connect())
        self._db_saver.setup()

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        tup = self._cache_saver.get_tuple(config)
        if tup is None:
            tup = self._db_saver.get_tuple(config)
            if tup is None:
                return None
            self._cache_saver.put(tup.config, tup.checkpoint, tup.metadata, {})
        return tup

    def list(
            self,
            config: RunnableConfig | None,
            *,
            filter: dict[str, Any] | None = None,
            before: RunnableConfig | None = None,
            limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:

        return self._db_saver.list(config, filter=filter, before=before, limit=limit)

    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        self._db_saver.put(config, checkpoint, metadata, new_versions)
        return self._cache_saver.put(config, checkpoint, metadata, new_versions)

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:

        self._db_saver.put_writes(config, writes, task_id, task_path)
        return self._cache_saver.put_writes(config, writes, task_id, task_path)

    def delete_thread(
            self,
            thread_id: str,
    ) -> None:
        self._db_saver.delete_thread(thread_id)
        self._cache_saver.delete_thread(thread_id)
        raise NotImplementedError

    def get_next_version(self, current: str | None, channel: None) -> str:
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(current.split(".")[0])
        next_v = current_v + 1
        next_h = random.random()
        return f"{next_v:032}.{next_h:016}"


def init_main_model() -> BaseChatModel:
    model_name = "qwen-max"
    # 创建千问model对象，要确保已设置api_key到系统变量DASHSCOPE_API_KEY
    return ChatTongyi(model=model_name, streaming=True) # 模型也要设置streaming=True，不然agent.stream()不生效


def init_sys_prompt() -> str:
    return "你是一个乐于助人的助手。"


class KnowledgeTool(BaseTool):
    name: str
    description: str
    args_schema: type[BaseModel] = SearchInput
    vector_collection: str

    def _run(self, query: str, *args: Any, **kwargs: Any) -> str:
        logger.debug("开始在知识空间[%s]内检索，query：[%s]", self.name, query)
        return rag_service.query_lite_mode(self.vector_collection, question=query)


async def build_tools() -> list:
    tools: list[BaseTool] = []
    # rag tools
    kb_spaces = knowledge_service.space_list_all()
    for kb_space in kb_spaces:
        kb_tool = KnowledgeTool(name=kb_space.name, description=kb_space.desc,
                                vector_collection=kb_space.collection)
        tools.append(kb_tool)
    # mcp tools
    # async with MultiServerMCPClient(
    #     # {
    #     #     "fetch": {
    #     #         "command": "uvx",
    #     #         "args": ["mcp-server-fetch"],
    #     #         "transport": "stdio"
    #     #     }
    #     # }
    # ) as client:
    #     await client.initialize()  # 必须，先握手
    #     async for tool in client.get_tools():
    #         tools.append(tool)
    # 其他 tools ...
    return tools

@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]
    to_keep = SETTINGS.AGENT_MSG_TRIM_TO_KEEP
    if len(messages) <= to_keep:
        return None  # No changes needed
    first_msg = messages[0]
    recent_messages = messages[-to_keep:] if len(messages) % 2 == 0 else messages[-to_keep+1:]
    new_messages = [first_msg] + recent_messages
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

def init_memory_pattern_middlewares() -> list:
    """先汇总，再滑动窗口"""
    summarization_middleware = SummarizationMiddleware(
        model=init_small_model(),
        max_tokens_before_summary=SETTINGS.AGENT_MSG_SUMMARY_MAX_BEFORE,
        messages_to_keep=SETTINGS.AGENT_MSG_SUMMARY_TO_KEEP,
    )

    return [summarization_middleware, trim_messages]


def initialize_agent(
        model: BaseChatModel = None,
        system_prompt:str = None,
        tools:list = None,
        middlewares:list = None,
        checkpointer:BaseCheckpointSaver = None
):
    if model is None:
        model = init_main_model()
    if system_prompt is None:
        system_prompt:str = init_sys_prompt()
    if tools is None:
        tools = asyncio.run(build_tools())
    if middlewares is None:
        middlewares = init_memory_pattern_middlewares()
    if checkpointer is None:
        checkpointer = HybridCheckpointSaver()
    # LangChain 1.0 中构建智能体的标准方式
    _agent_instance = create_agent(
        model=model,
        tools=tools,
        middleware=middlewares,
        system_prompt=system_prompt,
        checkpointer=checkpointer, # 每次新建一个，防止mysql连接丢失
    )

    _agent_instance.get_graph(xray=True).print_ascii()

    return _agent_instance
