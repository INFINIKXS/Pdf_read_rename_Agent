"""
Base Handler Interface for Document Intelligence Agent
Defines the common interface for all file handlers (TXT, PDF, DOCX, etc.).
References: AGENTS.md, Agent_Building_Guidlines, copilot-instructions.md
"""
from abc import ABC, abstractmethod
from typing import Any

# Context sources checked: MCP Context7 (no relevant handler interface library found), Exa web search (best practices confirm use of abc.ABC and @abstractmethod for Python handler interfaces; see e.g. langchain, semchunk, semantic-text-splitter). Standard Python abstract base class pattern used; no additional context found via MCP Context7 or Exa.
# See copilot-instructions.md for compliance details.

class BaseHandler(ABC):
    """
    Abstract base class for all document/file handlers.
    All handlers must implement the extract_text method.
    """

    @abstractmethod
    def extract_text(self, file_path: str, **kwargs) -> str:
        """
        Extract text content from the given file.
        Args:
            file_path (str): Path to the file to extract text from.
            **kwargs: Additional handler-specific options.
        Returns:
            str: Extracted text content.
        """
        pass

    def preprocess(self, content: str, **kwargs) -> Any:
        """
        Optional: Preprocess extracted text (e.g., cleaning, normalization).
        Args:
            content (str): Raw extracted text.
            **kwargs: Additional options.
        Returns:
            Any: Preprocessed content (default: returns input).
        """
        return content
