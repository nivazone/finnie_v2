from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    input_file: str
    fatal_err: bool | None
    messages: Annotated[list[AnyMessage], add_messages]