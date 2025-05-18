from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    input_file: str
    fatal_err: str | None
    messages: Annotated[list[AnyMessage], add_messages]