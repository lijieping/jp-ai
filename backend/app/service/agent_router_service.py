import json
import os
from types import FunctionType
from typing import Any

from langchain_community.chat_models import ChatTongyi

from app.service import agent_service_v2, agent_service

# 定义Agent模式注册表
agent_modes_registry:dict[str, Any] = {
    "personal_assistant": {
        "name": "日常管家",
        "description": "处理生活琐事和简单问答的个人助理",
        "trigger_conditions": [
            "- 生活信息咨询（天气、交通、定义、科普）",
            "- 简单内容生成（润色邮件、写个简短祝福、翻译）",
            "- 即时性问答（'谁'、'是什么'、'什么时候'）",
            "- 闲聊与情感陪伴"
        ],
        "example": """
用户：“明天上海天气怎么样？”
你：{"decision": "personal_assistant", "reason_and_mode": "这是一个简单的天气信息查询，属于日常事务范畴。我将转发给日常管家来处理......", "user_query_for_next": "明天上海天气怎么样？"}
        """,
        "exec_func": agent_service.exec
    },
    "company_affairs": {
        "name": "公司管家",
        "description": "处理商业项目、分析和创作的公司级任务",
        "trigger_conditions": [
            "- 包含明确的项目目标（'做个...'、'开发一个...'、'分析一下...市场'）",
            "- 需要多步骤协作（'先...然后...再...'）",
            "- 涉及专业领域深度分析（市场、产品、技术、策略）",
            "- 要求交付结构化成果（报告、方案、计划书、原型）",
            "- 上下文涉及商业、创业、盈利、竞争等关键词"
        ],
        "example": """
用户：“我想做一款针对00后的社交APP，帮我分析下市场并出个初步方案。”
你：{"decision": "company_affairs", "reason_and_mode": "这是一个涉及市场分析、产品设计的复杂商业项目，需要多部门专家协作。我将转发给公司管家来处理......", "user_query_for_next": “我想做一款针对00后的社交APP，帮我分析下市场并出个初步方案。”}
        """,
        "exec_func": agent_service_v2.exec
    }
}


def build_routing_prompt(registry, user_input: str):
    prompt = """
你是一位顶尖的“智能助理总监”，负责为我管理所有AI助理资源。你的核心能力是精准判断任务类型，并启动相应的处理流程
# 你的角色与原则
1.  **身份**：你是我的第一接触点，代表整个AI助理团队的门面。
2.  **目标**：以最高效、最专业的方式满足我的需求。
3.  **流程**：先判断，再路由，不越俎代庖执行具体任务。

# 路由判断标准
请根据以下标准严格判断用户请求：
"""

    for mode_id, mode_info in registry.items():
        prompt += f"""**启动【{mode_info["name"]}】模式（模式名为【{mode_info["name"]}】，id为{mode_id}），{mode_info["description"]},如果请求满足以下任一条件：**\n"""
        for condition in mode_info["trigger_conditions"]:
            prompt += condition + "\n"

    prompt += """
# 你的输出格式
**请只输出一个纯JSON对象，格式如下：**
{
  "decision": "你选择的模式的id",
  "reason_and_mode": "一句话解释你的判断理由，并说出你将转发给的模式名，并加省略号提示用户等待下一步回答，体现你的专业性",
  "user_query_for_next": "原样转发或精炼后的用户请求，用于下一步处理"
}
"""

    prompt += """# 示例\n"""

    for mode_id, mode_info in registry.items():
        prompt += mode_info["example"]

    prompt += "\n用户提问：" + user_input
    return prompt


# 意图分类模型
_router_model = ChatTongyi(model="qwen1.5-32b-chat", api_key=os.getenv("DASHSCOPE_API_KEY"))


def route_with_llm(user_input: str) -> tuple[FunctionType, dict]:
    prompt = build_routing_prompt(agent_modes_registry, user_input)
    response = _router_model.invoke(prompt).content.strip().lower()
    rsp_json:dict = json.loads(response)
    exec_func:FunctionType = agent_modes_registry[rsp_json['decision']]['exec_func']
    return exec_func, rsp_json