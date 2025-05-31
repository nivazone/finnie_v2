from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Any, Callable, List
from state import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from functools import partial
from helpers import needs_tool

@tool
def insights_tool() -> str:
    """Simulated insights tool."""
    print("came to insights tool...")
    return "No insights at this stage."

TOOLS: List[Callable[..., Any]] = [
    insights_tool
]

def sage(state: AgentState, llm: ChatOpenAI):
    print("came to sage")

    last = state["messages"][-1]

    # 2nd pass (tool result already present) -----------------------------
    if isinstance(last, ToolMessage):
        sys = SystemMessage(content="Using the provided tools, process user's request.")
        final = llm.invoke([sys] + state["messages"])
        return {"messages": [final], "next": "FINISH"}

    # 1st pass (no tool result yet) --------------------------------------
    sys = SystemMessage(content="Using the provided tools, process user's request.")
    first = llm.bind_tools(TOOLS).invoke([sys] + state["messages"])
    return {"messages": [first], "next": None}

def get_graph(llm: ChatOpenAI):
    """
    Return a runnable graph whose entry node is Sage and whose
    terminal node sets next='FINISH'.
    """

    wf = StateGraph(AgentState)

    wf.add_node("Sage", partial(sage, llm=llm))
    wf.add_node("SageTools", ToolNode(TOOLS))
    
    wf.add_edge(START, "Sage")
    wf.add_conditional_edges(
        "Sage",
        lambda s: "SageTools" if needs_tool(s) else END,
            {
                "SageTools": "SageTools",
                END: END
            },
    )
    wf.add_edge("SageTools", "Sage")

    return wf.compile()