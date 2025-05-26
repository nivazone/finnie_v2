from abc import ABC, abstractmethod
from typing import Any
from langchain_tavily import TavilySearch
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper


class SearchProvider(ABC):
    @abstractmethod
    async def ainvoke(self, input: dict) -> dict:
        pass

class TavilySearchClient(SearchProvider):
    def __init__(self, max_results: int = 3):
        self.client = TavilySearch(max_results=max_results)

    async def ainvoke(self, input: dict) -> dict:
        return await self.client.ainvoke(input)
    
class SerperSearchClient(SearchProvider):
    def __init__(self, max_results: int = 3):
        self.client = GoogleSerperAPIWrapper()
        self.max_results = max_results

    async def ainvoke(self, input: dict) -> dict:
        results = self.client.results(input["query"])
        items = results.get("organic", [])[:self.max_results]
        return {
            "results": [
                {
                    "title": r.get("title", ""),
                    "content": r.get("snippet", ""),
                    "url": r.get("link", "")
                } for r in items
            ]
        }

