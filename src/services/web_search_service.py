"""
WebSearchService for Exa API integration
References: AGENTS.md, Agent_Building_Guidlines, https://docs.exa.ai/examples/exa-researcher-python
"""
import os
from exa_py import Exa


class WebSearchService:
    def __init__(self, api_key: str | None = None):
        key: str = api_key or os.getenv("EXA_API_KEY") or ""
        if not key:
            raise ValueError("EXA_API_KEY is required for WebSearchService.")
        self.api_key = key
        self.client = Exa(self.api_key)

    def search(self, query: str, type_: str = "auto", highlights: bool = True, **kwargs):
        """
        Perform a web search using Exa and return results with content highlights.
        Args:
            query (str): The search query.
            type_ (str): 'auto', 'neural', or 'keyword'.
            highlights (bool): Whether to include highlights in the results.
        Returns:
            dict: Search results from Exa.
        References: AGENTS.md, Exa docs
        """
        # Exa expects highlights to be True or a HighlightsContentsOptions dict, not a generic bool
        # See: https://docs.exa.ai/reference/python-api#exa.search_and_contents
        return self.client.search_and_contents(query=query, type=type_, highlights=True, **kwargs)
