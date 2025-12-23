"""
    Start[用户输入任务] --> Analyst[分析师节点 model: qwen3-max, tools: 搜索/分析]
    Analyst --> Eval{评估节点 规则: 完整性检查（后续引入评估模型）}
    Eval -->|报告合格| Designer[设计师节点 model: kimi/豆包 tools: 原型/文档]
    Eval -->|报告不合格| Analyst
    Designer --> End[输出产品方案]
"""
from typing import Literal

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from pydantic import BaseModel

# 状态
class State(BaseModel):
    user_query:str
    analysis_res:str
    messages:list[BaseMessage]
    eval_count: int

# 分析师
# 分析师model
analyze_model = ChatTongyi(model="qwen-max")
# 分析师节点
def analyst(state:State) -> State:
    prompt = "你是一个商业分析师，你将与公司的设计师合作，你的任务是根据用户的提问给出《市场报告》"
    messages = state.messages
    ai_message = analyze_model.invoke(input=messages, prompt = prompt)
    print(ai_message)
    messages.append(ai_message)
    return state

# 设计师
# 设计师model
design_model = ChatTongyi(model="qwen-max")
# 设计师节点
def designer(state:State) -> State:
    prompt = "你是一个产品设计师，你将与公司的商业分析师合作，你的核心产出是产品需求文档（PRD）、用户流程图、功能规格说明书。这些文档要求极高的逻辑性、结构清晰、格式规范、无歧义"
    messages = state.messages
    ai_message = analyze_model.invoke(input=state.messages, prompt = prompt)
    print(ai_message)
    messages.append(ai_message)
    return state

# 分析报告评估节点
def eval_analysis(state:State) -> State:
    state.eval_count += 1
    is_pass = True
    human_message = HumanMessage(
        content=f"{'通过' if is_pass else '太简短'}"
    )
    state.messages.append(human_message)
    return state

# 构建图
graph = StateGraph(State)
graph.add_node("analyst", analyst)
graph.add_node("designer", designer)
graph.add_node("eval_analysis", eval_analysis)

graph.add_edge(START, "analyst")
graph.add_edge("analyst", "eval_analysis")
def should_continue(state: State) -> Literal["analyst", "designer"]:
    """评估结果判断条件边"""
    messages = state.messages
    last_message = messages[-1]
    if last_message.content == "通过":
        return "designer"
    else:
        return "analyst"
graph.add_conditional_edges("eval_analysis", should_continue, ["analyst", "designer"])
graph.add_edge("designer", END)


agent = graph.compile()
agent.get_graph(xray=True).print_ascii()

if (__name__ == "__main__"):
    query = "为一个面向00后的新社交App生成一份包含市场分析和产品原型的创意提案"
    state = State(
        analysis_res = "",
        eval_count = 0,
        user_query=query,
        messages=[HumanMessage(content=query)],
    )
    state = agent.invoke(state)
    for message in state.get("messages"):
        print(message.content)