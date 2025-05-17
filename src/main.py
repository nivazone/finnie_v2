from dotenv import load_dotenv
from typing import List, TypedDict, Annotated, Optional, cast, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages


from IPython.display import Image, display

import json
import os
from PIL import Image as PILImage
from io import BytesIO
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
from langgraph.prebuilt import InjectedState
from config import get_settings
from agent import get_graph

if __name__ == "__main__":
    load_dotenv()
    s = get_settings()

    llm = ChatOpenAI(
        model=s.MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )

    # tools = [
    #     extract_text,
    #     parse_statement_text,
    #     write_statement_to_db,
    #     read_statement_from_db,
    #     update_transaction_classification,
    #     search_web
    # ]
    # llm_with_tools = llm.bind_tools(tools)

    # builder = StateGraph(AgentState)
    # builder.add_node("agent", agent)
    # builder.add_node("tools", ToolNode(tools))

    # builder.add_edge(START, "agent")
    # builder.add_conditional_edges(
    #     "agent",
    #     # If the latest message requires a tool, route to tools
    #     # Otherwise, provide a direct response
    #     tools_condition,
    # )
    # builder.add_edge("tools", "agent")

    # finnie = builder.compile()

    finnie = get_graph(llm)

    messages = [HumanMessage(content="""
        Process all available bank statement using the following workflow.
            1. get plain text version of the statement.
            2. parsethe plain text so that you can get JSON version.
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