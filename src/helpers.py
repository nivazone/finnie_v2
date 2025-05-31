from langchain_core.messages import AIMessage, ToolMessage
import json
from state import AgentState

def needs_tool(state: AgentState) -> bool:
    """True if the last message contains tool_calls."""
    last = state["messages"][-1]
    return isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", []))

def update_state(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    if isinstance(last, ToolMessage):
        try:
            result = json.loads(last.content)
            if isinstance(result, dict):
                state.update(result)
        except Exception:
            pass

    return state