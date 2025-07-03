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

    def filter_pdfs(self, pdf_paths: List[str], score_threshold: float = 0.5, query: str = "Is this document relevant? Reply with a score from 0 to 1.", verbose: bool = True) -> List[str]:
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
        error_files = []
        paper_reasons = []
        for path in pdf_paths:
            score = 0.0
            error_occurred = False
            llm_output = ""
            try:
                text = self.pdf_handler.extract_text(path)
            except Exception as e:
                print(f"[WARN] Could not extract text from {path}: {e}")
                text = ""
                error_occurred = True
            prompt = f"{query}\n\n{text[:3000]}"
            if verbose:
                print(f"\n[AGENT] Processing file: {path}")
                print(f"[AGENT] Sending prompt to LLM:\n{prompt[:1000]}{'...' if len(prompt) > 1000 else ''}")
            try:
                response = self.llm_client.generate_content(prompt)
                llm_output = response
                if verbose:
                    print(f"[LLM OUTPUT] {response}")
                try:
                    score = float(next(s for s in response.split() if self._is_float(s) and 0 <= float(s) <= 1))
                except Exception:
                    score = 0.0
                if verbose:
                    print(f"[AGENT] Score parsed: {score}")
            except Exception as e:
                print(f"[WARN] LLM failed for {path}: {e}")
                score = 0.0
                error_occurred = True
            # Record reason for paper selection
            paper_reasons.append({
                'file': path,
                'score': score,
                'llm_output': llm_output,
                'selected': score >= score_threshold and not error_occurred,
                'error': error_occurred
            })
            if score >= score_threshold and not error_occurred:
                relevant_files.append(path)
            elif error_occurred:
                error_files.append(path)
        self._error_files = error_files
        # Write reasons to .md file
        with open('reason_for_paper_selection.md', 'w', encoding='utf-8') as f:
            f.write('# Reason for Paper Selection\n\n')
            for reason in paper_reasons:
                f.write(f"## File: {os.path.basename(reason['file'])}\n")
                f.write(f"**Selected:** {'Yes' if reason['selected'] else 'No'}  ")
                f.write(f"**Score:** {reason['score']}  ")
                if reason['error']:
                    f.write('**Error occurred during processing**\n')
                f.write('\n')
                if reason['llm_output']:
                    f.write(f"### LLM Output/Justification:\n{reason['llm_output']}\n\n")
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
        relevant = self.filter_pdfs(pdfs, score_threshold=score_threshold, query=query, verbose=verbose)
        copied = []
        # Copy relevant files
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
        # Copy error files to Error folder
        error_files = getattr(self, '_error_files', [])
        if error_files:
            error_dir = os.path.join(dest_dir, 'Error')
            if not os.path.exists(error_dir):
                os.makedirs(error_dir)
            for src in error_files:
                fname = os.path.basename(src)
                dest = os.path.join(error_dir, fname)
                try:
                    shutil.copy2(src, dest)
                    if verbose:
                        print(f"Copied error file: {src} -> {dest}")
                except Exception as e:
                    if verbose:
                        print(f"Failed to copy error file {src} -> {dest}: {e}")
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
from typing import Optional

def research_filter_mode(
    source_dir: Optional[str] = None,
    dest_dir: Optional[str] = None,
    score_threshold: float = 0.5,
    query: Optional[str] = None,
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
    if source_dir is None:
        source_dir = input("Enter the source folder to scan for PDFs: ").strip()
        if not source_dir:
            if verbose:
                print("No source folder provided. Aborting.")
            return
    if dest_dir is None:
        dest_dir = input("Enter the destination folder to copy relevant PDFs: ").strip()
        if not dest_dir:
            if verbose:
                print("No destination folder provided. Aborting.")
            return
    if not query:
        query = "Is this document relevant? Reply with a score from 0 to 1."
    workflow = ResearchWorkflow()
    copied = workflow.copy_relevant_pdfs(
        source_dir=source_dir,
        dest_dir=dest_dir,
        score_threshold=score_threshold,
        query=query,
        verbose=verbose
    )
    print("Copied relevant PDFs:", copied)
