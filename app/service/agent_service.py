import asyncio
from typing import Any

from langchain.agents.middleware import SummarizationMiddleware, before_model
from langchain_community.chat_models import ChatTongyi
from langchain.tools import tool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import RemoveMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent, AgentState
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime

from app.infra.log import logger
from app.infra.settings import is_lite_mode
from app.infra.redis import get_redis_client
from app.service import rag_service



def small_model_service(question: str) -> str:
    """轻量模型服务，为系统做一些简单的工作"""
    model_name = "qwen2.5-3b-instruct"
    # 创建千问model对象，要确保已设置api_key到系统变量DASHSCOPE_API_KEY
    model = ChatTongyi(model=model_name)
    ai_msg = model.invoke(question)
    return ai_msg.content

_agent_instance:CompiledStateGraph = None

async def token_generator(question: str, conversation_id:str):
    # 配置对话id，用于记忆对话上下文
    config = {"configurable": {"thread_id": conversation_id}}
    async for chunk in _agent_instance.astream(
            {"messages": [HumanMessage(content=question)]},
        config=config
    ):
        logger.info(f"=========conv_id:%s, chunk:%s", conversation_id, chunk)
        # chunk 结构如 {'model': {'messages': [AIMessageChunk(content="abc")]}}
        if "model" in chunk and chunk["model"]["messages"]:
            token = chunk["model"]["messages"][-1].content
            if token:  # 避免空事件
                yield token

def init_checkpointer() -> BaseCheckpointSaver:
    if (is_lite_mode()):
        # 本地内存记忆
        checkpointer = InMemorySaver()
    else:
        # redis记忆
        redis_client = get_redis_client()
        checkpointer = AsyncRedisSaver(redis_client=redis_client)
        asyncio.run(checkpointer.setup())  # 首次运行建表
    return checkpointer

def init_main_model() -> BaseChatModel:
    model_name = "qwen-max"
    # 创建千问model对象，要确保已设置api_key到系统变量DASHSCOPE_API_KEY
    return ChatTongyi(model=model_name)

def init_sys_prompt() -> str:
    return "你是一个乐于助人的助手。"

async def init_mcp_tools() -> list:
    # mcp infra
    mcp_client = MultiServerMCPClient(
        # {
        #     "fetch": {
        #         "command": "uvx",
        #         "args": ["mcp-server-fetch"],
        #         "transport": "stdio"
        #     }
        # }
    )
    tools = await mcp_client.get_tools()
    return tools

def init_rag_tools() -> list:
    @tool(description="从知识库获取创业方法论")
    def retrieve_entrepreneurship_guide():
        return rag_service.query(collection_name="demo_doc_4_pdf",
                                 question="副业创业者的实战指南：将热点流量转化为可持续收入的方法有哪些")
    return [retrieve_entrepreneurship_guide]

def init_memory_pattern_middlewares(summary_model:BaseChatModel) -> list:
    """前汇总，再滑动窗口"""
    summarization_middleware = SummarizationMiddleware(
        model=summary_model,
        max_tokens_before_summary=4000,
        messages_to_keep=10,
    )

    @before_model
    def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """Keep only the last few messages to fit context window."""
        messages = state["messages"]

        if len(messages) <= 10:
            return None  # No changes needed

        first_msg = messages[0]
        recent_messages = messages[-10:] if len(messages) % 2 == 0 else messages[-11:]
        new_messages = [first_msg] + recent_messages

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages
            ]
        }
    return [summarization_middleware, trim_messages]

def initialize_agent():
    global _agent_instance
    main_model = init_main_model()
    system_prompt = init_sys_prompt()
    # TODO 结构化输出

    middleware = []
    middleware.extend(init_memory_pattern_middlewares(main_model))

    tools = []
    tools.extend(init_rag_tools())
    #tools.extend(init_mcp_tools())

    checkpointer = init_checkpointer()
    # LangChain 1.0 中构建智能体的标准方式
    _agent_instance = create_agent(
        model=main_model,
        tools=tools,
        middleware=middleware,
        system_prompt=system_prompt,
        checkpointer=checkpointer
    )

initialize_agent()