from langchain_core.tools import tool
from dependencies import get_search_client
from logger import log
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event

@tool
async def search_web(query: str, config: RunnableConfig) -> dict:
    """
    Search the web for information about a given query.

    Args:
        query: The search query string

    Returns:
        dict: {
            "search_results": [
                {
                    "title": str,
                    "snippet": str,
                    "link": str
                },
                ...
            ],
            "fatal_err": False
        }
        or
        {
            "fatal_err": True,
            "err_details": str
        } on failure
    """

    log.info(f"[search_web] Searching web for {query}")

    await adispatch_custom_event("on_search_web", {"friendly_msg": "Searching web...\n"}, config=config)

    try:
        search_client = get_search_client()
        results = await search_client.ainvoke({"query": query})
        
        # Convert results to expected format
        search_results = []
        for r in results.get("results", []):
            search_results.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "link": r.get("url", "")
            })
        
        return {
            "search_results": search_results,
            "fatal_err": False
        }
    except Exception as e:
        log.error(f"[search_web] Failed to search web: {e}")
        return {
            "fatal_err": True,
            "err_details": str(e)
        } 