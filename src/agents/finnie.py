from langgraph.graph import StateGraph, END
from state import AgentState
from functools import partial
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from .scribe import get_graph as get_scribe_graph
from .sage import get_graph as get_sage_graph
from langchain_core.runnables import Runnable
from logger import log

async def finnie(state: AgentState, llm: ChatOpenAI):
    sys_msg = SystemMessage(content=f"""
        You are Finnie, a helpful agent that can manage other agents.
        Route the message based on its intent.

        If it's about bank statements, parsing PDFs, or classifying transactions, choose: scribe
        If it's about financial questions or insights from past data, choose: sage

        Respond with only: scribe or sage.
        
        Message:
    """)

    llm_with_tools = llm
    response = await llm_with_tools.ainvoke([sys_msg] + state["messages"])

    log.info(f"[finnie] routed to {response.content}")

    
    return {
        "messages": [response],
        "active_agent": str(response.content).strip().lower()
    }

def get_graph(llm: ChatOpenAI) -> Runnable:
    finnie_node = partial(finnie, llm=llm)

    scribe_graph = get_scribe_graph(llm)
    sage_graph = get_sage_graph(llm)

    builder = StateGraph(AgentState)
    builder.set_entry_point("finnie")

    builder.add_node("finnie", finnie_node)
    builder.add_node("scribe", scribe_graph)
    builder.add_node("sage", sage_graph)

    builder.add_conditional_edges(
        "finnie",
        lambda state: state["active_agent"],
        {
            "scribe": "scribe",
            "sage": "sage"
        }
    )

    builder.add_edge("scribe", "finnie")
    builder.add_edge("sage", "finnie")

    return builder.compile()
