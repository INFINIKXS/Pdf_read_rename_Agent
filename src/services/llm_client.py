
"""
LLM Client Service for Gemini API (Google Generative AI)
References: see AGENTS.md and Agent_Building_Guidlines for agent protocols and best practices.
"""
import os
from typing import Optional
from google import genai

class LLMClient:
    """Handles all Gemini API interactions via google-generativeai SDK."""
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLMClient for Gemini API.
        References: AGENTS.md, Agent_Building_Guidlines for agent protocols and best practices.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for LLMClient.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "models/gemini-2.5-pro"

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
            return response.text
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
