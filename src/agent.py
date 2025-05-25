from langchain_core.runnables import Runnable
from langgraph.graph import START, END, StateGraph
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from functools import partial
from typing import Any, Callable, List
from state import AgentState
from tools import (
    extract_all_texts,
    parse_all_statements,
    read_statement_from_db,
    update_transaction_classification,
    classify_transactions,
    write_all_statements
)
import json
from logger import log

TOOLS: List[Callable[..., Any]] = [
    extract_all_texts,
    parse_all_statements,
    write_all_statements,
    read_statement_from_db,
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
        log.info("[route_tools] fatal error detected. Ending execution.")
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

async def agent(state: AgentState, llm: ChatOpenAI):
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

def get_graph(llm: ChatOpenAI) -> Runnable:
    agent_node = partial(agent, llm=llm)

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_node("merge_output", merge_tool_output)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_tools)

    builder.add_edge("tools", "merge_output")
    builder.add_edge("merge_output", "agent")

    return builder.compile()