from dotenv import load_dotenv
from typing import List, TypedDict, Annotated, Optional, cast, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display
from langchain_tavily import TavilySearch
import json
import os
from PIL import Image as PILImage
from io import BytesIO
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
from langgraph.prebuilt import InjectedState

class AgentState(TypedDict):
    input_file: str
    messages: Annotated[list[AnyMessage], add_messages]

def extract_text(path: str) -> str:
    """
    Extracts the full textual content and tabular data from a PDF file.

    Args:
        path: path to the bank statement

    Returns:
        str: extracted text from the bank statement
    """

    print(f"[extract_text] extracting text from {path}...")
    
    all_text = """
    bank statement
    account name: Nivantha Mandawala
    opening balance: $2000
    closing balance: $4000
    start: 01/04/2025
    end: 30/04/2025
    transactions:
        01/04/2025  Tango Energy    $45
        02/04/2025  Uber Eats       $34
    """

    return all_text

def parse_statement_text(text: str) -> str:
    """
    Parses raw bank statement text into structured account and transaction data.

    Extracted fields include:
        - account name: Name or label of the account.
        - start: Statement start date (string format).
        - end: Statement end date (string format).
        - opening_balance: Opening balance at start of period.
        - closing_balance: Closing balance at end of period.
        - transactions: List of transactions, each with:
            - date: Transaction date (string).
            - transaction_details: Merchant or description.
            - amount: Transaction amount (positive or negative).

    Args:
        text: plain text from the bank statement

    Returns:
        str: valid json string
    """

    print(f"[parse_statement_text] parsing extracted text...")

    statement_json = """
    {
        "bank_statement": {
            "account_name": "Nivantha Mandawala",
            "opening_balance": 2000,
            "closing_balance": 4000,
            "start_date": "2025-04-01",
            "end_date": "2025-04-30",
            "transactions": [
            {
                "date": "2025-04-01",
                "description": "Tango Energy",
                "amount": 45
            },
            {
                "date": "2025-04-02",
                "description": "Uber Eats",
                "amount": 34
            }
            ]
        }
    }
    """

    return statement_json

def write_statement_to_db(statement_json: str) -> bool:
    """
    Writes structured bank statement data and transactions into database.
    
    Args:
        statement_json: A valid JSON string.

    Returns:
        bool: True or False indicating DB write was successful or not.
    """

    print(f"[write_statement_to_db] saving to database...")

    return True

def read_statement_from_db() -> str:
    """
    Reads statement from database

    Returns:
        str: JSON data of the bank statement
    """

    print(f"[read_statement_from_db] saving to database...")

    statement_json = """
    {
        "bank_statement": {
            "account_name": "Nivantha Mandawala",
            "opening_balance": 2000,
            "closing_balance": 4000,
            "start_date": "2025-04-01",
            "end_date": "2025-04-30",
            "transactions": [
            {
                "date": "2025-04-01",
                "description": "Tango Energy",
                "amount": 45
            },
            {
                "date": "2025-04-02",
                "description": "Uber Eats",
                "amount": 34
            }
            ]
        }
    }
    """

    return statement_json


def update_transaction_classification(category: str) -> bool:
    """
    Updates statement category in database
    
    Args:
        category: Category of the transaction in plain text

    Returns:
        bool: True or False indicating DB write was successful or not.
    """

    print(f"[update_transaction_classification] updating transaction category...")


    return True

def search_web(query: str) -> dict:
    """
    Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.

    Args:
        query: query string for the search engine

    Returns:
        dict: search results
    """

    print(f"[search_web] searching web...")

    client = TavilySearch(max_results=3)
    result = client.invoke({"query": query})

    return cast(dict[str, Any], result)

def agent(state: AgentState):
    sys_msg = SystemMessage(content=f"""
        You are a helpful agent named Finnie.
        You can analyse bank statements and run computations with provided tools.
        Current statement file is {state["input_file"]}
    """)
    return {
        "messages": [llm_with_tools.invoke([sys_msg] + state["messages"])],
    }

if __name__ == "__main__":
    load_dotenv()
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        base_url=os.getenv("OPENAI_BASE_URL", None),
        api_key=os.getenv("OPENAI_API_KEY", None),
        temperature=0
    )
    tools = [
        extract_text,
        parse_statement_text,
        write_statement_to_db,
        read_statement_from_db,
        update_transaction_classification,
        search_web
    ]
    llm_with_tools = llm.bind_tools(tools)

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        # If the latest message requires a tool, route to tools
        # Otherwise, provide a direct response
        tools_condition,
    )
    builder.add_edge("tools", "agent")

    finnie = builder.compile()

    messages = [HumanMessage(content="""
        Go through all the available bank statements and classify the transactions.
        The output should be saved to database.
        You must do a web search to get more details about the transaction decription before attempting to classify.
        Following are the categories, only use these categories.
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

    # from langchain_core.utils.function_calling import convert_to_openai_function
    # result = convert_to_openai_function(search_web)
    # print(result)