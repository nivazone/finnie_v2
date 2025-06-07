from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from state import AgentState
from dependencies import get_llm
from tools import search_web
from typing import Any, Callable, List
from logger import log
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from helpers import needs_tool, update_state
from langchain_core.runnables import RunnableConfig

TOOLS: List[Callable[..., Any]] = [
    search_web
]

async def fallback(state: AgentState, config: RunnableConfig):
    log.info(f"Came to Fallback, fatal_err={state.get('fatal_err', False)}")
    llm = get_llm(streaming=True)
    llm_with_tools = llm.bind_tools(TOOLS)

    is_fatal = state.get('fatal_err', False)

    sys_msgs = [SystemMessage(
        content="""
            The request doesn't match any other agents capabilities.
            You're the last resort agent.
            Let the user know that you are not best equiped to answer.
            You are equipped with a search tool to get latest information.
        """
    )]

    if is_fatal:
        log.fatal("[Fallback] Fatal error detected. Ending further processing.")
        err_details = state.get("err_details", "No details provided.")
        sys_msg = SystemMessage(content=f"""
            A fatal error occurred during processing.
            Retrying is not possible.
            Explain the error briefly and end the conversation.
            Explain the error briefly and end the conversation.
            Error details: {err_details}
        """)
        reply = await llm_with_tools.ainvoke([sys_msg] + state["messages"], config=config)
        return {"messages": [reply], "next": "FINISH"}

    last = state["messages"][-1]

    # 2nd pass (tool result already present) -----------------------------
    if isinstance(last, ToolMessage):
        reply = await llm_with_tools.ainvoke(sys_msgs + state["messages"], config=config)
        more_tools_needed = bool(getattr(reply, "tool_calls", []))
        
        return {
            "messages": [reply],
            "next": None if more_tools_needed else "FINISH",
        }

    # 1st pass (no tool result yet) --------------------------------------
    first = await llm_with_tools.ainvoke(sys_msgs + state["messages"], config=config)
    return {"messages": [first], "next": None}    

def get_graph():
    wf = StateGraph(AgentState)

    wf.add_node("Fallback", fallback)
    wf.add_node("FallbackTools", ToolNode(TOOLS))
    wf.add_node("UpdateState", update_state)
    
    wf.add_edge(START, "Fallback")
    wf.add_conditional_edges(
        "Fallback",
        lambda s: "FallbackTools" if needs_tool(s) else END,
            {
                "FallbackTools": "FallbackTools",
                END: END
            },
    )
    wf.add_edge("FallbackTools", "UpdateState")
    wf.add_edge("UpdateState", "Fallback")

    return wf.compile()