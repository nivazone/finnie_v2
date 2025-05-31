from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from functools import partial
from langchain_core.tools import tool
from typing import Any, Callable, List
from state import AgentState
from helpers import needs_tool

@tool
def document_processor_tool() -> str:
    """Simulated document processor tool."""
    print("came to document processor tool...")
    return "All done."

TOOLS: List[Callable[..., Any]] = [
    document_processor_tool
]

def scribe(state: AgentState, llm: ChatOpenAI):
    print("came to scribe")

    last = state["messages"][-1]

    # 2nd pass (tool result already present) -----------------------------
    if isinstance(last, ToolMessage):
        sys = SystemMessage(content="Using the provided tools, process user's request.")
        final = llm.invoke([sys] + state["messages"])
        return {"messages": [final], "next": "FINISH"}

    # 1st pass (no tool result yet) --------------------------------------
    sys = SystemMessage(content="Use provided tools to process user's request, then stop.")
    first = llm.bind_tools(TOOLS).invoke([sys] + state["messages"])
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