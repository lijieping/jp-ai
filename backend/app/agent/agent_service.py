import langsmith as ls
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.agent.knowledge_tool import KnowledgeTool
from app.agent.middlewares import trim_messages
from app.agent.mysql_agent_saver import get_hybrid_checkpoint_saver
from app.conversation.dao.message_dao import MessageStreamChunk, MsgChunkType
from app.infra.settings import get_settings
from app.rag.service.knowledge_service import knowledge_service


class CoreAgentService:
    """应用唯一的核心 Agent 执行层。"""

    def __init__(self):
        self._agent = None

    def init_small_model(self) -> BaseChatModel:
        model_name = "qwen2.5-3b-instruct"
        return ChatTongyi(model=model_name)

    def small_model_service(self, question: str) -> str:
        """执行标题等低成本模型任务。"""
        with ls.tracing_context(enabled=True, project_name="small-model"):
            ai_msg = self.init_small_model().invoke(question)
            return ai_msg.content

    def init_main_model(self) -> BaseChatModel:
        model_name = "qwen-max"
        return ChatTongyi(model=model_name)

    @staticmethod
    def init_sys_prompt() -> str:
        return "你是一个乐于助人的助手。"

    @staticmethod
    def build_tools() -> list[BaseTool]:
        return [
            KnowledgeTool(
                name=kb_space.name,
                description=kb_space.desc,
                vector_collection=kb_space.collection,
            )
            for kb_space in knowledge_service.space_list_all()
        ]

    def init_memory_pattern_middlewares(self) -> list:
        """先汇总，再滑动窗口。"""
        settings = get_settings()
        summarization_middleware = SummarizationMiddleware(
            model=self.init_small_model(),
            max_tokens_before_summary=settings.AGENT_MSG_SUMMARY_MAX_BEFORE,
            messages_to_keep=settings.AGENT_MSG_SUMMARY_TO_KEEP,
        )
        return [summarization_middleware, trim_messages]

    def initialize_agent(
        self,
        model: BaseChatModel | None = None,
        system_prompt: str | None = None,
        tools: list | None = None,
        middlewares: list | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ):
        return create_agent(
            model=model or self.init_main_model(),
            name="core_assistant",
            tools=tools if tools is not None else self.build_tools(),
            middleware=middlewares if middlewares is not None else self.init_memory_pattern_middlewares(),
            system_prompt=system_prompt or self.init_sys_prompt(),
            checkpointer=checkpointer or get_hybrid_checkpoint_saver(),
        )

    def get_agent(self):
        """惰性创建并复用核心 Agent。"""
        if self._agent is None:
            self._agent = self.initialize_agent()
        return self._agent

    def exec(self, question: str, conversation_id: str):
        """按既有流式消息协议执行核心 Agent。"""
        config = RunnableConfig(configurable={"thread_id": conversation_id})
        agent_input = {"messages": [HumanMessage(content=question)]}

        for event in self.get_agent().stream(agent_input, config=config):
            for graph_state in event.values():
                messages = graph_state.get("messages", [])
                if not messages:
                    continue

                message = messages[-1]
                message_type = MsgChunkType.AI if isinstance(message, AIMessage) else MsgChunkType.TOOL
                yield MessageStreamChunk.from_attrs(message_type, message.content, message.id)


core_agent_service = CoreAgentService()
