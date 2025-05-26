from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from state import AgentState
from functools import partial
from langgraph.prebuilt import ToolNode
from typing import Any, Callable, List
from logger import log
import json
from langchain_openai import ChatOpenAI
from tools import (
    extract_all_texts,
    parse_all_statements,
    read_transactions,
    update_transaction_classification,
    classify_transactions,
    write_all_statements
)

TOOLS: List[Callable[..., Any]] = [
    extract_all_texts,
    parse_all_statements,
    write_all_statements,
    read_transactions,
    update_transaction_classification,
    classify_transactions
]

def route_tools(state: AgentState):
    """
    Use in the conditional_edge to route to the ToolNode.
    Check if there are fatal errors, if yes, route to END.
    If not, check if the last message has tool calls.
    Otherwise, route to the end.
    """
    
    if state.get("fatal_err") is True:
        log.fatal("[route_tools] fatal error detected. Ending execution.")
        return END
    
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    if isinstance(ai_message, AIMessage) and getattr(ai_message, "tool_calls", None):
        return "tools"
    
    return END

async def scribe(state: AgentState, llm: ChatOpenAI):
    sys_msg = SystemMessage(content=f"""
        You are a helpful agent named Finnie.
        You can analyse bank statements and run computations with provided tools.
        Statements are located at {state["input_folder"]}.
    """)
    llm_with_tools = llm.bind_tools(TOOLS)
    response = await llm_with_tools.ainvoke([sys_msg] + state["messages"])
    
    return {
        "messages": [response]
    }

def merge_tool_output(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    if isinstance(last, ToolMessage):
        try:
            result = json.loads(last.content)
            if isinstance(result, dict):
                state.update(result)
        except Exception:
            pass

    return state

def get_graph(llm) -> Runnable:
    scribe_node = partial(scribe, llm=llm)

    builder = StateGraph(AgentState)
    builder.add_node("scribe", scribe_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_node("merge_output", merge_tool_output)

    builder.set_entry_point("scribe")

    builder.add_conditional_edges("scribe", route_tools)
    builder.add_edge("tools", "merge_output")
    builder.add_edge("merge_output", "scribe")
    builder.add_edge("scribe", END)

    return builder.compile()
