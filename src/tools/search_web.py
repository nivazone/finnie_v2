from langchain_tavily import TavilySearch
from typing import cast, Any

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