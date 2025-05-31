from dotenv import load_dotenv
import logging
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langsmith import traceable
from PIL import Image as PILImage
from langchain_core.runnables.graph import MermaidDrawMethod
from io import BytesIO
from agents.supervisor import get_graph
from config import get_settings
from logger import log
from dependencies import get_llm, init_db_pool

@traceable(name="finnie")
async def process(input_path: str):
    llm = get_llm()
    graph = get_graph(llm)

    # ---------------------------------------------------------------------
    #  Test run 1
    # ---------------------------------------------------------------------

    messages = [
        HumanMessage(content="process these new bank statements."),
    ]
    result = graph.invoke(
        {
            "messages": messages,
            "input_folder": input_path,
            "fatal_err": False,
        }
    )

    print("\n\nFinal result:\n", result['messages'][-1].content)

    # ---------------------------------------------------------------------
    #  Test run 2
    # ---------------------------------------------------------------------

    messages = [
        HumanMessage(content="Give me insights on last month's spending."),
    ]
    result = result = graph.invoke(
        {
            "messages": messages,
            "input_folder": input_path,
            "fatal_err": False,
        }
    )

    print("\n\nFinal result:\n", result['messages'][-1].content)

    # ---------------------------------------------------------------------
    #  Test run 3
    # ---------------------------------------------------------------------

    messages = [
        HumanMessage(content="what's the capital of Mars?"),
    ]
    result = result = graph.invoke(
        {
            "messages": messages,
            "input_folder": input_path,
            "fatal_err": False,
        }
    )

    print("\n\nFinal result:\n", result['messages'][-1].content)

def draw_graph():
    llm = get_llm()
    graph = get_graph(llm)

    png_bytes = graph.get_graph(xray=True).draw_mermaid_png(
        draw_method=MermaidDrawMethod.PYPPETEER
    )
    PILImage.open(BytesIO(png_bytes)).show()

async def main():
    try:
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        load_dotenv()
        s = get_settings()
        
        await init_db_pool()
        
        await process(s.INPUT_FOLDER)    

    finally:
        await init_db_pool()

if __name__ == "__main__":
    asyncio.run(main())
    # draw_graph()