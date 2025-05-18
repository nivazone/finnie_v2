from langchain_tavily import TavilySearch
from typing import cast, Any
from dependencies import get_search_client

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

    print(f"[search_web] searching web, {query=}")

    try:     
        client = get_search_client()
        result = client.invoke({"query": query})

        return cast(dict[str, Any], result)
    except Exception as e:
        print(f"--- [ERROR] Unknown error: {e}")
        return False