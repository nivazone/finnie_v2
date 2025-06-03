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
from .fallback import get_graph as get_fallback_graph
from logger import log
from dependencies import get_llm

MEMBERS = ["Scribe", "Sage", "Fallback"]
OPTIONS = ["FINISH"] + MEMBERS

SYSTEM_PROMPT = """
Your name is Finnie.
You are a personal assistant for a user.
You have access to user's personal financial information such as bank statements etc.
You are a supervisor managing the following agents: {MEMBERS}.
Routing rule:
  - Financial documents processing and persisting related requests, send to Scribe
  - Questions about personal financial information such as bank statements, send to Sage
  - Everything else, send to Fallback
  
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

async def supervisor(state: AgentState):
    llm = get_llm(streaming=False)
    log.info("Came to Supervisor")

    if state.get("next") == "FINISH":
        return {"next": "FINISH"}
    
    return await (SUPERVISOR_PROMPT | llm.with_structured_output(Routes)).ainvoke(state)

def get_graph():
    wf = StateGraph(AgentState)
    wf.add_node("Supervisor", supervisor)
    wf.add_node("Scribe", get_scribe_graph())
    wf.add_node("Sage", get_sage_graph())
    wf.add_node("Fallback", get_fallback_graph())

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
