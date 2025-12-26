from langchain.agents.middleware import SummarizationMiddleware
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain.agents import create_agent
import langsmith as ls

from app.agent.knowledge_tool import KnowledgeTool
from app.agent.middlewares import trim_messages
from app.agent.mysql_agent_saver import get_hybrid_checkpoint_saver
from app.infra.settings import get_settings
from app.agent.router_agent import RouterRegistry, BaseSubAgent
from app.rag.service.knowledge_service import knowledge_service


class DailyAgentService:

    def init_small_model(self) -> BaseChatModel:
        model_name = "qwen2.5-3b-instruct"
        # 创建千问model对象，要确保已设置api_key到系统变量DASHSCOPE_API_KEY
        return ChatTongyi(model=model_name)

    def small_model_service(self, question: str) -> str:
        model = self.init_small_model()
        """轻量模型服务，为系统做一些简单的工作"""
        with ls.tracing_context(enabled=True, project_name="small-model"):
            ai_msg = model.invoke(question)
            return ai_msg.content

    def init_main_model(self) -> BaseChatModel:
        # 用OpenAPI的方式调用通义千问， 目前langchain-community的Tongyi类在存在多个tool时会触发bug：
        # https://github.com/langchain-ai/langchain-community/issues/475
        model_name = "qwen-max"
        # 创建千问model对象，要确保已设置api_key到系统变量DASHSCOPE_API_KEY
        return ChatTongyi(model=model_name)  # 模型也要设置streaming=True，不然agent.stream()不生效
        #     return ChatOpenAI(model=model_name,
        #                       base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        #                       api_key=os.getenv("DASHSCOPE_API_KEY"))

    def init_sys_prompt(self) -> str:
        # todo 赋予性格和职责说明
        return "你是一个乐于助人的助手。"

    def build_tools(self) -> list:
        tools: list[BaseTool] = []
        # rag tools
        kb_spaces = knowledge_service.space_list_all()
        for kb_space in kb_spaces:
            kb_tool = KnowledgeTool(name=kb_space.name, description=kb_space.desc,
                                    vector_collection=kb_space.collection)
            tools.append(kb_tool)
        return tools

    def init_memory_pattern_middlewares(self) -> list:
        """先汇总，再滑动窗口"""
        settings = get_settings()
        summarization_middleware = SummarizationMiddleware(
            model=self.init_small_model(),
            max_tokens_before_summary=settings.AGENT_MSG_SUMMARY_MAX_BEFORE,
            messages_to_keep=settings.AGENT_MSG_SUMMARY_TO_KEEP,
        )

        return [summarization_middleware, trim_messages]

    def initialize_agent(self,
                         model: BaseChatModel = None,
                         system_prompt: str = None,
                         tools: list = None,
                         middlewares: list = None,
                         checkpointer: BaseCheckpointSaver = None
                         ):
        if model is None:
            model = self.init_main_model()
        if system_prompt is None:
            system_prompt: str = self.init_sys_prompt()
        if tools is None:
            tools = self.build_tools()
        if middlewares is None:
            middlewares = self.init_memory_pattern_middlewares()
        if checkpointer is None:
            checkpointer = get_hybrid_checkpoint_saver()
        # LangChain 1.0 中构建智能体的标准方式
        _agent_instance = create_agent(
            model=model,
            name="daily_assistant",
            tools=tools,
            middleware=middlewares,
            system_prompt=system_prompt,
            checkpointer=checkpointer,  # 每次新建一个，防止mysql连接丢失
        )

        return _agent_instance


class DailySubAgent(BaseSubAgent):
    """日常管家子 Agent，继承 BaseSubAgent 实现自动注册"""
    
    @classmethod
    def register_to_router(cls, registry: RouterRegistry):
        """实现基类的注册类方法"""
        service = DailyAgentService()
        agent = service.initialize_agent()
        registry.register(
            id="daily_assistant",
            name="日常管家",
            description="处理生活琐事和简单问答的个人助理",
            trigger_conditions=[
                "- 生活信息咨询（天气、交通、定义、科普）",
                "- 简单内容生成（润色邮件、写个简短祝福、翻译）",
                "- 即时性问答（'谁'、'是什么'、'什么时候'）",
                "- 闲聊与情感陪伴"
            ],
            example="用户：'明天上海天气怎么样？', 你：{'route_agent_id': 'daily_assistant', 'reason_and_mode': '这是一个简单的天气信息查询，属于日常事务范畴。我将转发给日常管家来处理......'}",
            agent=agent
        )


# DailyAgentService 实例（被 conversation_service 使用）
daily_angent_service = DailyAgentService()

