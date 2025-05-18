from langchain_core.runnables import Runnable
from langgraph.graph import START, StateGraph
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from functools import partial
from typing import Any, Callable, List
from state import AgentState
from tools import (
    extract_text,
    parse_statement_text,
    write_statement_to_db,
    read_statement_from_db,
    update_transaction_classification,
    search_web
)

TOOLS: List[Callable[..., Any]] = [
    extract_text,
    parse_statement_text,
    write_statement_to_db,
    read_statement_from_db,
    update_transaction_classification,
    search_web]

def agent(state: AgentState, llm: ChatOpenAI):
    sys_msg = SystemMessage(content=f"""
        You are a helpful agent named Finnie.
        You can analyse bank statements and run computations with provided tools.
        Current statement file is {state["input_file"]}.
    """)
    llm_with_tools = llm.bind_tools(TOOLS)
    
    return {
        "messages": [llm_with_tools.invoke([sys_msg] + state["messages"])],
    }

def get_graph(llm: ChatOpenAI) -> Runnable:
    agent_node = partial(agent, llm=llm)

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        # If the latest message requires a tool, route to tools
        # Otherwise, provide a direct response
        tools_condition,
    )
    builder.add_edge("tools", "agent")

    return builder.compile()