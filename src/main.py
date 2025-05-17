from dotenv import load_dotenv
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage


from IPython.display import Image, display

from PIL import Image as PILImage
from io import BytesIO
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
from config import get_settings
from agent import get_graph

if __name__ == "__main__":
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    load_dotenv()
    
    s = get_settings()

    llm = ChatOpenAI(
        model=s.MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )

    finnie = get_graph(llm)

    messages = [HumanMessage(content="""
        Process all available bank statement using the following workflow.
            1. get plain text version of the statement.
            2. parse the plain text so that you can get JSON version.
            3. save statement JSON to database for future use.
            4. get transactions from the database and classify the transactions.
            5. save the transaction classification to database.
        
        Important:
        - You must do a web search to get more details about the transaction decription before attempting to classify.
        - Following are the categories, only use these categories for classifying transactions.
            - Groceries
            - Transport
            - Utilities 
            - Insurance
            - Entertainment
            - Subscriptions
            - Healthcare
            - Dining
            - Vet
            - Unknown
        """
    )]
    
    response = finnie.invoke({
        "messages": messages,
        "input_file": "statements/april-2025.pdf"
    })

    print(print(response['messages'][-1].content))

    # png_bytes = finnie.get_graph(xray=True).draw_mermaid_png(
    #     draw_method=MermaidDrawMethod.PYPPETEER
    # )
    # PILImage.open(BytesIO(png_bytes)).show()