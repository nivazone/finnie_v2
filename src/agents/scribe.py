from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from functools import partial
from langchain_core.tools import tool
from typing import Any, Callable, List
from state import AgentState
from helpers import needs_tool
from logger import log
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
]

async def scribe(state: AgentState, llm: ChatOpenAI):
    log.info("came to scribe")

    llm_with_tools = llm.bind_tools(TOOLS)
    sys_msgs = [SystemMessage(content=f"""
        Process all available bank statements using the following workflow.
            1. get plain text version for each statement in the folder.
            2. parse each plain text version so that you can get a JSON version.
            3. save each statement JSON to database for future use.
        Statements are located at {state["input_folder"]}.
        """
    )]
    last = state["messages"][-1]

    # ── 2nd+ passes: we already have a ToolMessage result ────────────
    if isinstance(last, ToolMessage):
        reply = await llm_with_tools.ainvoke(sys_msgs + state["messages"])
        more_tools_needed = bool(getattr(reply, "tool_calls", []))
        
        return {
            "messages": [reply],
            "next": None if more_tools_needed else "FINISH",
        }

    # ── 1st pass: ask for a tool ─────────────────────────────────────
    first = await llm_with_tools.ainvoke(sys_msgs + state["messages"])
    return {"messages": [first], "next": None}

def get_graph(llm: ChatOpenAI):
    """
    Return a runnable graph whose entry node is Scribe and whose
    terminal node sets next='FINISH'.
    """
    
    wf = StateGraph(AgentState)

    wf.add_node("Scribe", partial(scribe, llm=llm))
    wf.add_node("ScribeTools", ToolNode(TOOLS))

    wf.add_edge(START, "Scribe")
    wf.add_conditional_edges(
        "Scribe",
        lambda s: "ScribeTools" if needs_tool(s) else END,
            {
                "ScribeTools": "ScribeTools",
                END: END
            },
    )
    wf.add_edge("ScribeTools", "Scribe")

    return wf.compile()