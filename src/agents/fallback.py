from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from state import AgentState

def fallback(state: AgentState, llm: ChatOpenAI):
    sys = SystemMessage(
        content="""
            The request doesn’t match any available agents capabilities.
            Let the user know that you are not best equiped to answer.
            Also provide an answer and let them know the answer is based on LLM's knowledge and not from the agents.
        """
    )
    reply = llm.invoke([sys] + state["messages"])
    return {"messages": [reply], "next": "FINISH"}