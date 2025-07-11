from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    input_folder: str
    fatal_err: bool | None
    err_details: str | None
    messages: Annotated[list[AnyMessage], add_messages]
    next: Optional[str]