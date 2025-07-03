import os
from typing import List, Callable

from src.handlers.pdf_handler import PdfHandler
from src.services.llm_client import LLMClient


import shutil

class ResearchWorkflow:
    """
    Workflow for filtering and copying relevant PDFs using LLM-based scoring.
    """
    def __init__(self, llm_client=None, pdf_handler=None):
        """
        Initialize the ResearchWorkflow.
        Args:
            llm_client: Optional LLMClient instance. If None, a new one is created.
            pdf_handler: Optional PdfHandler instance. If None, a new one is created.
        """
        self.llm_client = llm_client or LLMClient()
        self.pdf_handler = pdf_handler or PdfHandler()

    def filter_pdfs(self, pdf_paths: List[str], score_threshold: float = 0.5, query: str = "Is this document relevant? Reply with a score from 0 to 1.") -> List[str]:
        """
        Filter a list of PDF files by LLM-generated relevance score.
        Args:
            pdf_paths (List[str]): List of PDF file paths to process.
            score_threshold (float): Minimum score to consider a file relevant.
            query (str): The prompt/question to send to the LLM for scoring.
        Returns:
            List[str]: List of file paths deemed relevant.
        """
        """
        Orchestrate research filtering: extract text, score with LLM, and return relevant files.
        Args:
            pdf_paths: List of PDF file paths to process.
            score_threshold: Minimum score to consider a file relevant.
            query: The prompt/question to send to the LLM for scoring.
        Returns:
            List of file paths deemed relevant.
        """
        relevant_files = []
        for path in pdf_paths:
            try:
                text = self.pdf_handler.extract_text(path)
                prompt = f"{query}\n\n{text[:3000]}"
                response = self.llm_client.generate_content(prompt)
                try:
                    score = float(next(s for s in response.split() if self._is_float(s) and 0 <= float(s) <= 1))
                except Exception:
                    score = 0.0
                if score >= score_threshold:
                    relevant_files.append(path)
            except Exception as e:
                print(f"[WARN] Skipping {path}: {e}")
        return relevant_files

    def copy_relevant_pdfs(self, source_dir: str, dest_dir: str, score_threshold: float = 0.5, query: str = "Is this document relevant? Reply with a score from 0 to 1.", verbose: bool = True) -> List[str]:
        """
        Scan for PDFs in source_dir, filter relevant ones, and copy them to dest_dir.
        Args:
            source_dir (str): Directory to scan for PDF files.
            dest_dir (str): Directory to copy relevant PDFs to.
            score_threshold (float): Minimum score to consider a file relevant.
            query (str): The prompt/question to send to the LLM for scoring.
            verbose (bool): If True, print progress and errors.
        Returns:
            List[str]: List of copied file paths.
        """
        """
        Scan for PDFs in source_dir, filter relevant ones, and copy them to dest_dir.
        Returns list of copied file paths.
        """
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        pdfs = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
        relevant = self.filter_pdfs(pdfs, score_threshold=score_threshold, query=query)
        copied = []
        for src in relevant:
            fname = os.path.basename(src)
            dest = os.path.join(dest_dir, fname)
            try:
                shutil.copy2(src, dest)
                if verbose:
                    print(f"Copied: {src} -> {dest}")
                copied.append(dest)
            except Exception as e:
                if verbose:
                    print(f"Failed to copy {src} -> {dest}: {e}")
        return copied

    @staticmethod
    def _is_float(s):
        """
        Check if a string can be converted to a float.
        Args:
            s: Input string.
        Returns:
            bool: True if s is a float, False otherwise.
        """
        try:
            float(s)
            return True
        except Exception:
            return False



# CLI entry point for research filter mode
def research_filter_mode(
    source_dir: str = "./pdfs",
    dest_dir: str = "./relevant_pdfs",
    score_threshold: float = 0.5,
    query: str = "Is this document relevant? Reply with a score from 0 to 1.",
    verbose: bool = True
) -> None:
    """
    CLI entry point for research filter mode. Scans source_dir for PDFs, filters relevant ones, and copies them to dest_dir.
    Args:
        source_dir (str): Directory to scan for PDF files.
        dest_dir (str): Directory to copy relevant PDFs to.
        score_threshold (float): Minimum score to consider a file relevant.
        query (str): The prompt/question to send to the LLM for scoring.
        verbose (bool): If True, print progress and errors.
    Returns:
        None
    """
    workflow = ResearchWorkflow()
    copied = workflow.copy_relevant_pdfs(
        source_dir=source_dir,
        dest_dir=dest_dir,
        score_threshold=score_threshold,
        query=query,
        verbose=verbose
    )
    print("Copied relevant PDFs:", copied)
