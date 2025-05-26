from typing import Annotated
from typing_extensions import TypedDict, Optional
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    input_folder: str
    active_agent: Optional[str]
    fatal_err: bool | None
    messages: Annotated[list[AnyMessage], add_messages]