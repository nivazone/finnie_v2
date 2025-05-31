from pydantic import BaseModel
from typing import Literal
from functools import partial
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langgraph.graph import START, END, StateGraph
from .scribe import get_graph as get_scribe_graph
from .sage import get_graph as get_sage_graph
from .fallback import fallback
from logger import log

MEMBERS = ["Scribe", "Sage", "Fallback"]
OPTIONS = ["FINISH"] + MEMBERS

SYSTEM_PROMPT = """
You are a supervisor managing the following agents: {MEMBERS}.
Routing rule:
  - Financial documents processing and persisting related requests → Scribe
  - Insights about persisted financial docuements                  → Sage
  - Everything else                                                → Fallback
  
When an agent sets {{"next": "FINISH"}}, reply FINISH.
""".strip()

SUPERVISOR_PROMPT = (
    ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("messages"),
            ("system", "Who acts next (or FINISH)? Choose from {OPTIONS}."),
        ]
    )
    .partial(OPTIONS=str(OPTIONS), MEMBERS=", ".join(MEMBERS))
)

class Routes(BaseModel):
    next: Literal["FINISH", "Scribe", "Sage", "Fallback"]

async def supervisor(state: AgentState, llm: ChatOpenAI):
    log.info("came to supervisor")

    if state.get("next") == "FINISH":
        return {"next": "FINISH"}
    
    return await (SUPERVISOR_PROMPT | llm.with_structured_output(Routes)).ainvoke(state)

def get_graph(llm: ChatOpenAI):
    wf = StateGraph(AgentState)

    wf.add_node("Supervisor", partial(supervisor, llm=llm))
    wf.add_node("Scribe", get_scribe_graph(llm))
    wf.add_node("Sage", get_sage_graph(llm))
    wf.add_node("Fallback", partial(
        lambda st: {
            "messages": fallback(st, llm)["messages"],
            "next": "FINISH"
        }))

    wf.add_edge(START, "Supervisor")
    wf.add_conditional_edges(
        "Supervisor",
        lambda s: s["next"],
            {
                "Scribe": "Scribe",
                "Sage": "Sage",
                "Fallback": "Fallback",
                "FINISH": END
            },
    )
    
    return wf.compile()
