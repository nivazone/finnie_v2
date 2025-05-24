from dotenv import load_dotenv
import asyncio
import logging
from langchain_core.messages import HumanMessage
from IPython.display import Image, display
from PIL import Image as PILImage
# from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
from agent import get_graph
from dependencies import get_llm, init_db_pool

async def main():
    try:
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        load_dotenv()
        
        await init_db_pool()
        llm = get_llm()
        finnie = get_graph(llm)

        messages = [HumanMessage(content="""
            Process all available bank statement using the following workflow.
                1. get plain text version of the statement.
                2. parse the plain text so that you can get JSON version.
                3. save statement JSON to database for future use.
                4. get all transactions from the database for the statement and classify them using classify transactions tool.
                5. update the transaction classification in database.
                                
            """
        )]
        
        response = await finnie.ainvoke({
            "messages": messages,
            "input_file": "statements/april-2025.pdf",
            "fatal_err": False,
        })

        print(print(response['messages'][-1].content))

        # png_bytes = finnie.get_graph(xray=True).draw_mermaid_png(
        #     draw_method=MermaidDrawMethod.PYPPETEER
        # )
        # PILImage.open(BytesIO(png_bytes)).show()

    finally:
        await init_db_pool()

if __name__ == "__main__":
    asyncio.run(main())