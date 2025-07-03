"""
LLM Client Service for Gemini API (Google Generative AI)
References: see AGENTS.md and Agent_Building_Guidlines for agent protocols and best practices.
"""
import os
from typing import Optional, Dict, Any
from google import genai
from promptl_ai import Promptl, PromptlError
from .web_search_service import WebSearchService

class LLMClient:
    def chunk_text(self, text: str, max_tokens: int = 1000, overlap: int = 100) -> list:
        """
        Split a large text into overlapping chunks for LLM processing.
        Args:
            text (str): The input text to split.
            max_tokens (int): Maximum tokens (approx. words) per chunk.
            overlap (int): Number of words to overlap between chunks.
        Returns:
            list: List of text chunks.
        """
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + max_tokens, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            if end == len(words):
                break
            start = end - overlap
        return chunks
    """Handles all Gemini API interactions via google-generativeai SDK, with prompt templating support."""
    # Default prompt templates for major tasks
    PROMPT_TEMPLATES = {
        "rename": (
            "You are an expert document intelligence agent. Given the following extracted text, generate a concise, descriptive filename for the document.\n"
            "Text: {{text}}\n"
            "Rules: Only return the filename, no extra text."
        ),
        "research": (
            "You are a research assistant. Given the following document text, answer the user's research question.\n"
            "Text: {{text}}\n"
            "Question: {{question}}\n"
            "Rules: Be concise and cite relevant sections if possible."
        ),
    }

    def __init__(self, api_key: Optional[str] = None, exa_api_key: Optional[str] = None):
        """
        Initialize the LLMClient for Gemini API.
        References: AGENTS.md, Agent_Building_Guidlines for agent protocols and best practices.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for LLMClient.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "models/gemini-2.5-pro"
        # Ensure exa_api_key is str, not None
        exa_key: str = exa_api_key or os.getenv("EXA_API_KEY") or ""
        if not exa_key:
            raise ValueError("EXA_API_KEY is required for WebSearchService.")
        self.web_search = WebSearchService(api_key=exa_key)
        self.promptl = Promptl()

    def get_prompt_template(self, name: str) -> str:
        """
        Retrieve a named prompt template for a given task.
        Args:
            name (str): The template name ('rename', 'research', etc.)
        Returns:
            str: The template string.
        Raises:
            KeyError: If the template is not found.
        """
        if name not in self.PROMPT_TEMPLATES:
            raise KeyError(f"Prompt template '{name}' not found.")
        return self.PROMPT_TEMPLATES[name]

    def render_named_prompt(self, name: str, parameters: Dict[str, Any]) -> str:
        """
        Render a named prompt template with parameters.
        Args:
            name (str): The template name ('rename', 'research', etc.)
            parameters (dict): Parameters to fill into the template.
        Returns:
            str: The rendered prompt string.
        """
        template = self.get_prompt_template(name)
        return self.render_prompt(template, parameters)
        """
        Initialize the LLMClient for Gemini API.
        References: AGENTS.md, Agent_Building_Guidlines for agent protocols and best practices.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for LLMClient.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "models/gemini-2.5-pro"
        # Ensure exa_api_key is str, not None
        exa_key: str = exa_api_key or os.getenv("EXA_API_KEY") or ""
        if not exa_key:
            raise ValueError("EXA_API_KEY is required for WebSearchService.")
        self.web_search = WebSearchService(api_key=exa_key)
        self.promptl = Promptl()

    def render_prompt(self, template: str, parameters: Dict[str, Any]) -> str:
        """
        Render a prompt using PromptL templating engine.
        Args:
            template (str): The PromptL template string.
            parameters (dict): Parameters to fill into the template.
        Returns:
            str: The rendered prompt string (user message content).
        References: promptl-py docs, AGENTS.md
        """
        try:
            result = self.promptl.prompts.render(prompt=template, parameters=parameters)
            # Only join string contents, skip non-string or nested content
            contents = []
            for msg in result.messages:
                content = getattr(msg, "content", None)
                if isinstance(content, str):
                    contents.append(content)
            return "\n".join(contents)
        except PromptlError as e:
            raise RuntimeError(f"PromptL rendering failed: {e.cause.message}")

    def generate_content(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Generate content from the Gemini LLM for a given prompt.
        Args:
            prompt (str): The prompt to send to the LLM.
            model (Optional[str]): Optional model name override.
            **kwargs: Additional parameters for the LLM API.
        Returns:
            str: The generated text response.
        Raises:
            RuntimeError: If the LLM API call fails.
        References: AGENTS.md, Agent_Building_Guidlines
        """
        model_name = model or self.model_name
        try:
            response = self.client.models.generate_content(model=model_name, contents=prompt, **kwargs)
            return response.text or ""
        except Exception as e:
            # Log or handle error as per agent protocols
            raise RuntimeError(f"LLMClient.generate_content failed: {e}")

    def generate_content_stream(self, prompt: str, model: Optional[str] = None, **kwargs):
        """
        Stream content from the Gemini LLM for a given prompt using the latest SDK best practices.
        Args:
            prompt (str): The prompt to send to the LLM.
            model (Optional[str]): Optional model name override.
            **kwargs: Additional parameters for the LLM API.
        Yields:
            str: Chunks of generated text as they are produced.
        Raises:
            RuntimeError: If the LLM API call fails.
        References: AGENTS.md, Agent_Building_Guidlines, MCP Context7, Google GenAI SDK docs
        """
        try:
            for chunk in self.client.models.generate_content_stream(
                model=model or self.model_name,
                contents=prompt,
                **kwargs
            ):
                yield chunk.text
        except Exception as e:
            # Log or handle error as per agent protocols
            raise RuntimeError(f"LLMClient.generate_content_stream failed: {e}")

    def generate_content_with_grounding(self, prompt: str, search_query: Optional[str] = None, model: Optional[str] = None, **kwargs) -> str:
        """
        Generate content from the Gemini LLM, grounded with Exa web search results if a search_query is provided.
        Args:
            prompt (str): The prompt to send to the LLM.
            search_query (str): If provided, run this query with Exa and prepend results to the prompt.
            model (Optional[str]): Optional model name override.
            **kwargs: Additional parameters for the LLM API.
        Returns:
            str: The generated text response.
        References: AGENTS.md, Agent_Building_Guidlines, Exa docs
        """
        if search_query:
            search_results = self.web_search.search(search_query)
            context = self._format_exa_results(search_results)
            # Explicit, instruction-driven prompt for year extraction
            full_prompt = (
                f"[Web Search Results]\n{context}\n\n[User Prompt]\n{prompt}\n\n"
                "Instructions: Based only on the web search results above, extract the year mentioned. "
                "If no year is present, respond with 'Unknown'. Do not guess or use prior knowledge."
            )
        else:
            full_prompt = prompt
        return self.generate_content(full_prompt, model=model, **kwargs)

    def _format_exa_results(self, results) -> str:
        """
        Format Exa search results for LLM context.
        Accepts Exa SearchResponse object or dict.
        """
        # Handle Exa SearchResponse object
        if hasattr(results, 'results') and isinstance(results.results, list):
            result_list = results.results
        elif isinstance(results, dict) and 'results' in results:
            result_list = results['results']
        else:
            return "No web results found."
        formatted = []
        for r in result_list[:3]:
            # Exa SearchResult objects have .title, .url, .text attributes
            title = getattr(r, 'title', '') if hasattr(r, 'title') else r.get('title', '')
            url = getattr(r, 'url', '') if hasattr(r, 'url') else r.get('url', '')
            snippet = getattr(r, 'text', '') if hasattr(r, 'text') else r.get('text', '')
            formatted.append(f"- {title}\n  {snippet}\n  Source: {url}")
        return '\n'.join(formatted)
