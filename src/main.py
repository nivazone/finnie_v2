from dotenv import load_dotenv
import asyncio
import logging
from langchain_core.messages import HumanMessage
from config import get_settings
from dependencies import get_llm, init_db_pool, close_db_pool
from logger import log
from langsmith import traceable
from agents import get_graph
from langchain_core.runnables.graph import MermaidDrawMethod
from PIL import Image as PILImage
from io import BytesIO

@traceable(name="finnie")
async def begin(input_path: str):
    llm = get_llm()
    finnie_graph = get_graph(llm)

    # messages = [
    #     HumanMessage(content="""
    #     Process all available bank statement using the following workflow.
    #         1. get plain text version for each statement in the folder.
    #         2. parse each plain text version so that you can get a JSON version.
    #         3. save each statement JSON to database for future use.
    #         4. wait for each statement to finish parsing and saving to database before proceeding further
    #         5. once all statements are parsed and saved to database, get all transactions from the database for each statement and classify them using classify transactions tool.
    #         6. update the transaction classification in database.
    #     """)
    # ]

    messages = [
        HumanMessage(content="""
        what is a transaction?
        """)
    ]

    return await finnie_graph.ainvoke({
        "messages": messages,
        "input_folder": input_path,
        "fatal_err": False,
    })

async def main():
    try:
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        load_dotenv()
        s = get_settings()
        
        await init_db_pool()
        
        response = await begin(s.INPUT_FOLDER)
        log.info(response["messages"][-1].content)

    finally:
        await close_db_pool()

def draw_graph() -> None:
    llm = get_llm()
    graph = get_graph(llm)

    png_bytes = graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.PYPPETEER
    )
    PILImage.open(BytesIO(png_bytes)).show()

if __name__ == "__main__":
    # draw_graph()

    asyncio.run(main())
