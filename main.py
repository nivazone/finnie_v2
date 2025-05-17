# from dotenv import load_dotenv
# import logging
# from langgraph.graph import StateGraph, START, END
# from langchain_core.messages import HumanMessage
# from tools.pdf_extractor import pdf_extractor
# from tools.statement_parser import statement_parser
# from tools.postgres_writer import postgres_writer
# from tools.transaction_classifier import transaction_classifier
# from tools.web_searcher import web_searcher
# from shared.agent_state import AgentState
# from shared.dependencies import get_llm
# from datetime import datetime
# from langgraph.prebuilt import create_react_agent
# import uuid
# from PIL import Image as PILImage
# from io import BytesIO
# from langchain_core.runnables.graph_mermaid import MermaidDrawMethod

# def preprocess(state):
#     print("[preprocess] Validating inputs...")
    
#     if "messages" not in state or not state["messages"]:
#         raise ValueError("messages[] cannot be empty.")
    
#     if "pdf_path" not in state or not state["pdf_path"]:
#         raise ValueError("pdf_path cannot be empty.")
    
#     state["job_id"] = str(uuid.uuid4())
#     state["start_timestamp"] = datetime.utcnow().isoformat()
    
#     print(f"[preprocess] Job ID: {state['job_id']}")
#     return state

# def postprocess(state):
#     print("[postprocess] Finalizing job...")
#     state["end_timestamp"] = datetime.utcnow().isoformat()
#     print(f"[postprocess] Job {state['job_id']} complete.")
#     print(f"started: {state['start_timestamp']}")
#     print(f"ended: {state['end_timestamp']}")
#     return state

# def build_agent():
#     llm = get_llm()
#     tools = [
#         pdf_extractor,
#         statement_parser,
#         postgres_writer,
#         transaction_classifier,
#         web_searcher
#     ]
    
#     return create_react_agent(llm, tools)

# if __name__ == "__main__":
#     load_dotenv()
#     logging.getLogger("pdfminer").setLevel(logging.ERROR)

#     graph = StateGraph(AgentState)
#     graph.add_node("preprocess", preprocess)
#     graph.add_node("agent", build_agent())
#     graph.add_node("postprocess", postprocess)
#     graph.add_edge(START, "preprocess")
#     graph.add_edge("preprocess", "agent")
#     graph.add_edge("agent", "postprocess")
#     graph.add_edge("postprocess", END)

#     pipeline = graph.compile()

#     prompt = """
#         You are an AI agent named Finnie who can extract, parse bank statements and classify transactions.
#         You have all the tools required to complete the job.
#         The path to the statement is statements/april-2025.pdf.
#         Process the statement and save it to the database.
#         And then assign a category for each transaction and save it to the database.
#         If you encounter an error or an exception, do not retry, end the processing.
#         """
#     result = pipeline.invoke({
#         "messages": [HumanMessage(content=prompt)],
#         "pdf_path": "statements/april-2025.pdf",
#     })

#     print("Agent execution complete, result:")

#     # png_bytes = pipeline.get_graph(xray=True).draw_mermaid_png(
#     #     draw_method=MermaidDrawMethod.PYPPETEER
#     # )
#     # PILImage.open(BytesIO(png_bytes)).show()
