from langchain.tools import tool
from shared.dependencies import get_web_search_provider

@tool
def web_searcher(query: str) -> str:
    """
    Perform a web search using the provided query.

    This tool wraps a production web search provider (e.g. TavilySearch) 
    and logs the query for auditing purposes. It is designed to be called 
    autonomously by agents to look up external information.

    Args:
        query (str): The text query to search for.

    Returns:
        str: A plain text summary or snippet of the top search results.
    """

    print(f"[web_searcher] performing search for {query=}")

    search_tool = get_web_search_provider()
    result = search_tool.invoke({"query": query})

    print(f"[web_searcher] result: '{result=}'")
    return result