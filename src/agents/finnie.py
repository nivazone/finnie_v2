from langgraph.graph import StateGraph, END
from state import AgentState
from functools import partial
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from .scribe import get_graph as get_scribe_graph
from .sage import get_graph as get_sage_graph
from langchain_core.runnables import Runnable
from logger import log

async def supervisor(state: AgentState, llm: ChatOpenAI):
    sys_msg = SystemMessage(content="""
        You are Finnie, the master agent responsible for orchestrating specialist agents.

        Decide which agent to invoke next:
        - Choose 'scribe' for statement processing, classification, and parsing.
        - Choose 'sage' for querying insights, analytics, or summaries from transactions.

        Return ONLY the name of the agent: 'scribe', 'sage', or 'end'.
    """)

    response = await llm.ainvoke([sys_msg] + state["messages"])
    decision = str(response.content).strip().lower()
    
    log.info(f"[supervisor] routed to: {decision}")
    
    return {"messages": [response], "next": decision}

async def end_convo(state: AgentState):
    log.info("[supervisor] Conversation ended.")
    return {"messages": state["messages"], "final": True}

def get_graph(llm: ChatOpenAI) -> Runnable:
    supervisor_node = partial(supervisor, llm=llm)
    scribe_graph = get_scribe_graph(llm)
    sage_graph = get_sage_graph(llm)

    builder = StateGraph(AgentState)
    builder.set_entry_point("supervisor")

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("scribe", scribe_graph)
    builder.add_node("sage", sage_graph)
    builder.add_node("finish", end_convo)

    builder.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next"),
        {
            "scribe": "scribe",
            "sage": "sage",
            "end": "finish"
        }
    )

    # Loop back to supervisor for multi-turn convo
    builder.add_edge("scribe", "supervisor")
    builder.add_edge("sage", "supervisor")

    return builder.compile()
