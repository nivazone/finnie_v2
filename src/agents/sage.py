from langgraph.graph import StateGraph, END
from state import AgentState
from langchain_openai import ChatOpenAI
from functools import partial
from langchain_core.messages import SystemMessage
from langchain_core.runnables import Runnable

async def sage(state: AgentState, llm: ChatOpenAI):
    sys_msg = SystemMessage(content="You are Sage, a helpful financial assistant. Answer user questions concisely and clearly.")
    response = await llm.ainvoke([sys_msg] + state["messages"])
    
    return {
        "messages": state["messages"] + [response]
    }

def get_graph(llm: ChatOpenAI) -> Runnable:
    sage_node = partial(sage, llm=llm)
    
    builder = StateGraph(AgentState)
    builder.add_node("sage", sage_node)
    
    builder.set_entry_point("sage")
    
    builder.add_edge("sage", END)

    return builder.compile()


