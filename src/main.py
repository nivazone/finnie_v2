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
    s = get_settings()

    try:
        # 1. initialise DB + streaming LLM + graph
        await init_db_pool()
        graph = get_graph()

        # 2. keep the whole running chat history
        messages: list = []
        print("Agent: Hi, how can I help you today?")

        # 3. ctrl-C exits
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in {"exit", "quit"}:
                break

            messages.append(HumanMessage(content=user_input))

            # 4. run the supervisor graph.  
            reply = await graph.ainvoke({
                "messages": messages,
                "input_folder": s.INPUT_FOLDER,
                "fatal_err": False,
                "err_details": None,
            })

            # 5. persist the returned message list so the next turn has context
            messages = reply["messages"]

            # 6. new line after the last streamed token
            print()

    finally:
        await close_db_pool()

if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(chat())
    # draw_graph()