from dotenv import load_dotenv
import logging
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage, HumanMessage
from typing import TypedDict, Optional, List, Dict
from tools.pdf_extractor import pdf_extractor
from tools.statement_parser import statement_parser
from tools.postgres_writer import postgres_writer
from langchain_tavily import TavilySearch
from shared.dependencies import get_llm
from datetime import datetime
from langgraph.prebuilt import create_react_agent
import uuid
from PIL import Image as PILImage
from io import BytesIO
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod

class AgentState(TypedDict):
    messages: List[AnyMessage]
    pdf_path: Optional[str]
    extracted_text: Optional[str]
    parsed_data: Optional[Dict]
    db_write_result: Optional[str]
    job_id: Optional[str]
    start_timestamp: Optional[str]
    end_timestamp: Optional[str]

def preprocess(state):
    print("[Preprocess] Validating inputs...")
    if "messages" not in state or not state["messages"]:
        raise ValueError("messages[] cannot be empty.")
    if "pdf_path" not in state or not state["pdf_path"]:
        raise ValueError("pdf_path must be provided.")
    state["job_id"] = str(uuid.uuid4())
    state["start_timestamp"] = datetime.utcnow().isoformat()
    print(f"[Preprocess] Job ID: {state['job_id']}")
    return state

def postprocess(state):
    print("[Postprocess] Finalizing job...")
    state["end_timestamp"] = datetime.utcnow().isoformat()
    print(f"[Postprocess] Job {state['job_id']} complete.")
    print(f"Started: {state['start_timestamp']}")
    print(f"Ended: {state['end_timestamp']}")
    return state

def build_agent():
    llm = get_llm()
    search_tool = TavilySearch(max_results=3)
    tools = [
        pdf_extractor,
        statement_parser,
        postgres_writer,
        search_tool
    ]
    
    return create_react_agent(llm, tools)

if __name__ == "__main__":
    load_dotenv()
    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    graph = StateGraph(AgentState)
    graph.add_node("preprocess", preprocess)
    graph.add_node("agent", build_agent())
    graph.add_node("postprocess", postprocess)
    graph.add_edge(START, "preprocess")
    graph.add_edge("preprocess", "agent")
    graph.add_edge("agent", "postprocess")
    graph.add_edge("postprocess", END)

    pipeline = graph.compile()

    prompt = """
        You are an AI agent named Finnie who can extract and parse bank statements.
        The statement can be located using pdf_path in AgentState.
        """
    result = pipeline.invoke({
        "messages": [HumanMessage(content=prompt)],
        "pdf_path": "statements/april-2025.pdf"
    })

    print("Agent execution complete, result:", result)

    # png_bytes = pipeline.get_graph(xray=True).draw_mermaid_png(
    #     draw_method=MermaidDrawMethod.PYPPETEER
    # )
    # PILImage.open(BytesIO(png_bytes)).show()
