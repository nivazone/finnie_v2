from dotenv import load_dotenv
import logging
import asyncio, signal, sys, readline
from datetime import datetime
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
from cli import FinnieStream
from langchain_core.runnables.config import RunnableConfig

def draw_graph():
    graph = get_graph()

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
    callback_handler = FinnieStream()
    config = RunnableConfig(
        callbacks=[callback_handler],
        tags=["Finnie"]
    )

    try:
        await init_db_pool()
        graph = get_graph()

        messages: list = []
        console.print("[cyan bold]Finnie:[/] Hi, how can I help you today?")

        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

        while True:
            # ── Read user input ────────────────────────────────────────────────
            with patch_stdout():
                user_input = (await session.prompt_async(
                    HTML("<b><ansigreen>You:</ansigreen></b> ")
                )).strip()

            if user_input.lower() in {"exit", "quit"}:
                break

            messages.append(HumanMessage(content=user_input))

            # ── NEW: run the graph with incremental streaming ─────────────────
            bootstrap_state = {
                "messages":     messages,
                "input_folder": settings.INPUT_FOLDER,
                "fatal_err":    False,
                "err_details":  None,
            }

            final_state = {}     # will accumulate the newest values we care about

            async for ns, delta in graph.astream(
                bootstrap_state,
                stream_mode="values",
                subgraphs=True,
                config=config
            ):
                # Preserve updated messages so we can continue the conversation
                if "messages" in delta:
                    final_state["messages"] = delta["messages"]

            # ── After the graph finishes for this turn ────────────────────────
            messages = final_state.get("messages", messages)
            console.print()

    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(chat())
    # draw_graph()
