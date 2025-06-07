from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from typing import Any, Callable, List
from state import AgentState
from helpers import needs_tool, update_state
from logger import log
from dependencies import get_llm
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
    read_transactions,
    update_transaction_classification,
    classify_transactions,
]

async def scribe(state: AgentState, config: RunnableConfig):
    log.info(f"Came to Scribe, fatal_err={state.get('fatal_err', False)}")

    llm: ChatOpenAI = get_llm(streaming=True)
    llm_with_tools = llm.bind_tools(TOOLS)
    sys_msgs = [SystemMessage(content=f"""
        Process all available bank statements using the following workflow.
            1. get plain text version for each statement in the folder.
            2. parse each plain text version so that you can get a JSON version.
            3. save each statement JSON to database for future use.
            4. wait for each statement to finish parsing and saving to database before proceeding further
            5. once all statements are parsed and saved, get all transactions from the database for each statement and classify them using classify-transactions tool.
            6. update the transaction classification in database.
        
        **Progress reporting**
        - Before you invoke *any* tool, output a single line that starts with `EVENT: starting <tool_name>` (no extra text).  
        - After the tool finishes (you receive the tool result), output `EVENT: finished <tool_name>` on its own line.  
        - Do **not** reveal private reasoning or chain of thought.
        - Normal conversational replies should follow the event lines.
        
        Statements are located at {state["input_folder"]}.
        """
    )]

    is_fatal = state.get('fatal_err', False)

    if is_fatal:
        log.fatal("[Scribe] Fatal error detected. Ending further processing.")
        err_details = state.get("err_details", "No details provided.")
        sys_msg = SystemMessage(content=f"""
            A fatal error occurred during processing.
            Retrying is not possible.
            Explain the error briefly and end the conversation.
            Error details: {err_details}
        """)
        reply = await llm_with_tools.ainvoke([sys_msg] + state["messages"], config=config)
        return {"messages": [reply], "next": "FINISH"}

    last = state["messages"][-1]

    # ── 2nd+ passes: we already have a ToolMessage result ────────────
    if isinstance(last, ToolMessage):
        reply = await llm_with_tools.ainvoke(sys_msgs + state["messages"], config=config)
        more_tools_needed = bool(getattr(reply, "tool_calls", []))
        
        return {
            "messages": [reply],
            "next": None if more_tools_needed else "FINISH",
        }

    # ── 1st pass: ask for a tool ─────────────────────────────────────
    first = await llm_with_tools.ainvoke(sys_msgs + state["messages"], config=config)
    return {"messages": [first], "next": None}

def get_graph():
    """
    Return a runnable graph whose entry node is Scribe and whose
    terminal node sets next='FINISH'.
    """
    
    wf = StateGraph(AgentState)

    wf.add_node("Scribe", scribe)
    wf.add_node("ScribeTools", ToolNode(TOOLS))
    wf.add_node("UpdateState", update_state)

    wf.add_edge(START, "Scribe")
    wf.add_conditional_edges(
        "Scribe",
        lambda s: "ScribeTools" if needs_tool(s) else END,
            {
                "ScribeTools": "ScribeTools",
                END: END
            },
    )
    wf.add_edge("ScribeTools", "UpdateState")
    wf.add_edge("UpdateState", "Scribe")

    return wf.compile()