from dotenv import load_dotenv
import asyncio
import logging
from langchain_core.messages import HumanMessage
from IPython.display import Image, display
from PIL import Image as PILImage
# from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
from agent import get_graph
from dependencies import get_llm, init_db_pool
from logger import log
from config import get_settings, Settings
from langsmith import traceable

@traceable(name="finnie")
async def begin(s: Settings):
    llm = get_llm()
    finnie = get_graph(llm)

    messages = [HumanMessage(content="""
        Process all available bank statement using the following workflow.
            1. get plain text version for each statement in the folder.
            2. parse each plain text version so that you can get a JSON version.
            3. save each statement JSON to database for future use.
            4. wait for each statement to finish parsing and saving to database before proceeding further
            5. once all statements are parsed and saved to database, get all transactions from the database for each statement and classify them using classify transactions tool.
            5. update the transaction classification in database.
                            
        """
    )]
    
    return await finnie.ainvoke({
        "messages": messages,
        "input_folder": s.INPUT_FOLDER,
        "fatal_err": False,
    })

async def main():
    try:
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        load_dotenv()
        s = get_settings()
        
        await init_db_pool()
        
        response = await begin(s)

        log.info(response['messages'][-1].content)

        # png_bytes = finnie.get_graph(xray=True).draw_mermaid_png(
        #     draw_method=MermaidDrawMethod.PYPPETEER
        # )
        # PILImage.open(BytesIO(png_bytes)).show()

    finally:
        await init_db_pool()

if __name__ == "__main__":
    asyncio.run(main())