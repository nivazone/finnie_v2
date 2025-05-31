from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Any, Callable, List
from state import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from functools import partial
import json
from helpers import needs_tool, update_state
from logger import log

@tool
def insights_tool() -> str:
    """Simulated insights tool."""
    log.info("came to insights tool...")
    return "No insights at this stage."

TOOLS: List[Callable[..., Any]] = [
    insights_tool
]

async def sage(state: AgentState, llm: ChatOpenAI):
    log.info("came to sage")

    llm_with_tools = llm.bind_tools(TOOLS)
    sys_msgs = [SystemMessage(content=f"""
        Using the provided tools, process user's request.
        """
    )]

    is_fatal = state.get('fatal_err', False)

    if is_fatal:
        log.fatal("[Sage] fatal error detected. Ending further processing.")
        sys_msg = SystemMessage(content="""
            A fatal error occurred during processing.
            Retrying is not possible.
            Explain the error briefly and end the conversation.
        """)
        reply = await llm_with_tools.ainvoke([sys_msg] + state["messages"])
        return {"messages": [reply], "next": "FINISH"}

    last = state["messages"][-1]

    # 2nd pass (tool result already present) -----------------------------
    if isinstance(last, ToolMessage):
        reply = await llm_with_tools.ainvoke(sys_msgs + state["messages"])
        more_tools_needed = bool(getattr(reply, "tool_calls", []))
        
        return {
            "messages": [reply],
            "next": None if more_tools_needed else "FINISH",
        }

    # 1st pass (no tool result yet) --------------------------------------
    first = await llm_with_tools.ainvoke(sys_msgs + state["messages"])
    return {"messages": [first], "next": None}

def get_graph(llm: ChatOpenAI):
    """
    Return a runnable graph whose entry node is Sage and whose
    terminal node sets next='FINISH'.
    """

    wf = StateGraph(AgentState)

    wf.add_node("Sage", partial(sage, llm=llm))
    wf.add_node("SageTools", ToolNode(TOOLS))
    wf.add_node("UpdateState", update_state)
    
    wf.add_edge(START, "Sage")
    wf.add_conditional_edges(
        "Sage",
        lambda s: "SageTools" if needs_tool(s) else END,
            {
                "SageTools": "SageTools",
                END: END
            },
    )
    wf.add_edge("SageTools", "UpdateState")
    wf.add_edge("UpdateState", "Sage")

    return wf.compile()