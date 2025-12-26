from typing import Any

from langchain.agents import AgentState
from langchain.agents.middleware import before_model
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from app.infra.settings import get_settings


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    settings = get_settings()
    messages = state["messages"]
    to_keep = settings.AGENT_MSG_TRIM_TO_KEEP
    if len(messages) <= to_keep:
        return None  # No changes needed
    first_msg = messages[0]
    recent_messages = messages[-to_keep:] if len(messages) % 2 == 0 else messages[-to_keep + 1:]
    new_messages = [first_msg] + recent_messages
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }