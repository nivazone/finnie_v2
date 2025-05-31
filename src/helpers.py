from langchain_core.messages import AIMessage
from state import AgentState

def needs_tool(state: AgentState) -> bool:
    """True if the last message contains tool_calls."""
    last = state["messages"][-1]
    return isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", []))