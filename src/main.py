from dotenv import load_dotenv
import logging
import asyncio, signal, sys, readline
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
from dependencies import get_llm, init_db_pool, close_db_pool
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout

def draw_graph():
    llm = get_llm()
    graph = get_graph(llm)

    png_bytes = graph.get_graph(xray=True).draw_mermaid_png(
        draw_method=MermaidDrawMethod.PYPPETEER
    )
    PILImage.open(BytesIO(png_bytes)).show()

@traceable(name="Finnie")
async def chat():
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    load_dotenv()
    settings = get_settings()

    console  = Console()
    session  = PromptSession()

    try:
        await init_db_pool()
        graph = get_graph()

        messages: list = []
        console.print("[cyan bold]Finnie:[/] Hi, how can I help you today?")

        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

        while True:
            # asynchronous, non-erasable prompt
            with patch_stdout():     # NEW – lets background prints show safely
                user_input = (await session.prompt_async(
                    HTML("<b><ansigreen>You:</ansigreen></b> ")
                )).strip()

            if user_input.lower() in {"exit", "quit"}:
                break

            messages.append(HumanMessage(content=user_input))

            state = await graph.ainvoke(
                {
                    "messages":    messages,
                    "input_folder": settings.INPUT_FOLDER,
                    "fatal_err":   False,
                    "err_details": None,
                }
            )
            messages = state["messages"]
            console.print()          # newline after streamed reply

    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(chat())
    # draw_graph()