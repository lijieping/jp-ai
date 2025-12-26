import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Annotated, List

from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import add_messages
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import BaseModel

from app.conversation.dao.message_dao import MsgChunkType, MessageStreamChunk
from app.agent.mysql_agent_saver import get_hybrid_checkpoint_saver


@dataclass
class AgentInfo:
    id: str
    name: str
    description: str
    trigger_conditions: list[str]
    example: str
    agent: CompiledStateGraph


class BaseSubAgent(ABC):
    """子 Agent 基类，所有子 agent 必须继承此类并实现类方法注册"""
    
    @classmethod
    @abstractmethod
    def register_to_router(cls, registry: 'RouterRegistry'):
        """子类必须实现此类方法，用于向 RouterRegistry 注册自己
        
        Args:
            registry: RouterRegistry 类，用于注册
        """
        pass


class RouterRegistry:
    """子agent路由注册器，支持基于继承的自动注册"""
    _routers: dict[str, AgentInfo] = {}

    @classmethod
    def register(cls,
                 id: str,
                 name: str,
                 description: str,
                 trigger_conditions: list[str],
                 example: str,
                 agent: CompiledStateGraph):
        """注册子 agent"""
        agent_info = AgentInfo(id, name, description, trigger_conditions, example, agent)
        cls._routers[agent_info.id] = agent_info
        return agent_info

    @classmethod
    def get_all_subclasses(cls, base_class):
        """递归获取所有子类（包括子类的子类）"""
        subclasses = set(base_class.__subclasses__())
        for subclass in list(subclasses):
            subclasses.update(cls.get_all_subclasses(subclass))
        return subclasses

    @classmethod
    def auto_register_all_sub_agents(cls):
        """自动注册所有 BaseSubAgent 的子类
        
        工作流程：
        1. 导入 sub_agent 包（包的 __init__.py 会自动导入所有子模块）
        2. 通过 BaseSubAgent.__subclasses__() 获取所有子类
        3. 调用每个子类的 register_to_router 类方法
        """
        # 导入 sub_agent 包，包的 __init__.py 会自动导入所有子模块
        import app.agent.sub_agent  # noqa: F401
        
        # 获取所有 BaseSubAgent 的子类（包括递归子类）
        sub_agent_classes = cls.get_all_subclasses(BaseSubAgent)
        
        # 调用每个子类的注册类方法
        registered_count = 0
        for sub_agent_class in sub_agent_classes:
            try:
                sub_agent_class.register_to_router(cls)
                registered_count += 1
                print(f"Registered sub-agent: {sub_agent_class.__name__}")
            except Exception as e:
                print(f"Warning: Failed to register {sub_agent_class.__name__}: {e}")
        
        return registered_count

    @classmethod
    def list(cls) -> tuple[list[CompiledStateGraph], list[str], list[str]]:
        agents: list[CompiledStateGraph] = []
        trigger_condition_prompts: list[str] = []
        example_prompts: list[str] = []
        for agent_id, agent_info in cls._routers.items():
            agents.append(agent_info.agent)
            condition_prompt = f"""**启动【{agent_info.name}】模式（模式名为【{agent_info.name}】，id为{agent_info.id}），{agent_info.description},如果请求满足以下任一条件：**\n"""
            for condition in agent_info.trigger_conditions:
                condition_prompt += condition + "\n"
            trigger_condition_prompts.append(condition_prompt)
            example_prompts.append(agent_info.example)

        return agents, trigger_condition_prompts, example_prompts

    @classmethod
    def all(cls) -> dict[str, AgentInfo]:
        return cls._routers.copy()

class RouterState(BaseModel):
    router_ai_message:Optional[AIMessage] = None
    user_question:Optional[str] = None
    route_agent_id: Optional[str] = None
    reason_and_mode: Optional[str] = None
    messages: Annotated[List[AnyMessage], add_messages] = []
    thread_id:str = None

class RouterService:
    def build_routing_prompt(self, trigger_condition_prompts: list[str], example_prompts: list[str]):
        prompt = """
    你是一位顶尖的"智能助理总监"，负责为我管理所有AI助理资源。你的核心能力是精准判断任务类型，并启动相应的处理流程
    # 你的角色与原则
    1.  **身份**：你是我的第一接触点，代表整个AI助理团队的门面。
    2.  **目标**：以最高效、最专业的方式满足我的需求。
    3.  **流程**：先判断，再路由，不越俎代庖执行具体任务。
    
    # 路由判断标准
    请根据以下标准严格判断用户请求：
    """
        prompt += "\n".join(trigger_condition_prompts)
        prompt += """
    # 你的输出格式
    **请只输出一个纯JSON对象，格式如下：**
    {
      "route_agent_id": "你选择的模式的id",
      "reason_and_mode": "一句话解释你的判断理由，并说出你将转发给的模式名，并加省略号提示用户等待下一步回答，体现你的专业性"
    }
    """
        prompt += """# 示例\n"""
        prompt += "\n".join(example_prompts)
        prompt += "# 用户提问：\n"
        return prompt

    ROUTE_NODE:str = "route_node"
    ROUTE_AGENT_ID:str = "route_agent_id"

    def create_router(self):

        agents, trigger_condition_prompts, example_prompts = RouterRegistry.list()
        router_prompt = self.build_routing_prompt(trigger_condition_prompts, example_prompts)

        router_model = ChatOpenAI(openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                                  model="qwen1.5-32b-chat",
                                  api_key=os.getenv("DASHSCOPE_API_KEY"))

        def route_node(state: RouterState):
            ai_message:AIMessage = router_model.invoke(input=router_prompt + state.user_question)
            return {"router_ai_message":ai_message}

        router_graph = StateGraph(RouterState)
        router_graph.add_edge(START, self.ROUTE_NODE)
        router_graph.add_node(self.ROUTE_NODE, route_node)
        route_path_map = {}
        for agent_id, agent_info in RouterRegistry.all().items():
            # 直接添加子agent作为节点
            # 当子graph作为节点被调用时，LangGraph会自动传递config
            # 如果子graph有checkpointer，LangGraph会自动从checkpointer加载历史状态
            # 但是，由于router_graph没有checkpointer，LangGraph可能不会为子graph加载历史状态
            # 所以我们需要直接添加子agent，让LangGraph自动处理
            router_graph.add_node(agent_id, agent_info.agent)
            router_graph.add_edge(agent_id, END)
            route_path_map[agent_id] = agent_id
        def route_conditional_edge(state: RouterState):
            return json.loads(state.router_ai_message.content).get(self.ROUTE_AGENT_ID)
        router_graph.add_conditional_edges(self.ROUTE_NODE, route_conditional_edge, route_path_map)
        # 为router_graph添加checkpointer，确保子agent能够从checkpointer加载历史状态
        # 虽然router_graph本身不需要保存状态，但是有了checkpointer后，LangGraph会为子graph加载历史状态
        # 使用全局单例，与子agent共享同一个checkpointer实例
        router_checkpointer = get_hybrid_checkpoint_saver()
        router_agent = router_graph.compile(checkpointer=router_checkpointer)
        router_agent.get_graph(xray=True).print_ascii()
        return router_agent

    def exec(self, question: str, conversation_id: str):
        # 配置对话id，用于记忆对话上下文
        config = RunnableConfig(configurable={"thread_id": conversation_id})

        router_state = RouterState(
            user_question=question,
            route_agent_id=None,
            reason_and_mode=None,
            messages=[HumanMessage(content=question)],
            thread_id=conversation_id
        )
        for event in router_graph_manager.get_router().stream(router_state, config=config):
            #print(f"=========event:{event}")
            for graph_node, graph_state in event.items():
                if graph_node == self.ROUTE_NODE:
                    message = graph_state['router_ai_message']
                    type = MsgChunkType.ROUTER
                else:
                    message = graph_state['messages'][-1]
                    type = MsgChunkType.AI if isinstance(message, AIMessage) else MsgChunkType.TOOL

                main_message_chunk = MessageStreamChunk.from_attrs(type, message.content, message.id)
                yield main_message_chunk

class RouterGraphManager:
    """Router Graph 管理器，支持显式初始化和延迟初始化"""
    
    def __init__(self):
        self._router_graph: Optional[CompiledStateGraph] = None
        self._initialized = False
        self._router_service = RouterService()
    
    def initialize(self):
        """显式初始化 router_graph，会自动扫描并注册所有子 agent"""
        if self._initialized:
            return
        
        # 自动扫描并注册所有 BaseSubAgent 的子类
        registered_count = RouterRegistry.auto_register_all_sub_agents()
        
        if registered_count == 0:
            raise RuntimeError("No sub-agents registered. Please ensure at least one sub-agent inherits from BaseSubAgent.")
        
        self._router_graph = self._router_service.create_router()
        self._initialized = True
    
    def get_router(self) -> CompiledStateGraph:
        """获取 router_graph，如果未初始化则自动初始化（延迟初始化）"""
        if not self._initialized:
            self.initialize()
        return self._router_graph
    
    @property
    def router_service(self) -> RouterService:
        """获取 RouterService 实例"""
        return self._router_service


# 全局 RouterGraph 管理器实例
router_graph_manager = RouterGraphManager()

# RouterService 实例（被 conversation_service 使用）
agent_router_service = router_graph_manager.router_service

