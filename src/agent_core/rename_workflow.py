import os
import re
from typing import List, Optional, Dict, Type
from src.services.llm_client import LLMClient
from src.handlers.pdf_handler import PdfHandler
from src.handlers.txt_handler import TxtHandler
from src.handlers.docx_handler import DocxHandler


HANDLER_MAP: Dict[str, Type] = {
    '.pdf': PdfHandler,
    '.txt': TxtHandler,
    '.docx': DocxHandler,
}

"""
Module: rename_workflow.py
Implements the Rename Mode workflow for the Document Intelligence Agent.
Scans for supported files, extracts text, generates new filenames using LLM, and renames files.
"""

def scan_files(directory: str, exts: Optional[List[str]] = None) -> List[str]:
    """
    Recursively scan for files with given extensions in a directory.
    Args:
        directory (str): Directory to scan.
        exts (Optional[List[str]]): List of file extensions to include (e.g., ['.pdf', '.txt']). If None, all files are included.
    Returns:
        List[str]: List of file paths matching the extensions.
    """
    matches = []
    for root, _, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if exts is None or ext in exts:
                matches.append(os.path.join(root, f))
    return matches

def sanitize_filename(name: str, ext: str) -> str:
    """
    Sanitize filename by removing invalid characters, trimming, and ensuring the correct extension.
    Args:
        name (str): Proposed filename (without extension).
        ext (str): File extension (e.g., '.pdf').
    Returns:
        str: Sanitized filename with extension.
    """
    name = re.sub(r'[^\w\- ]+', '', name).strip().replace(' ', '_')
    if not name.lower().endswith(ext):
        name += ext
    return name

def resolve_collision(directory: str, filename: str) -> str:
    """
    Resolve filename collisions by appending a counter if the file already exists in the directory.
    Args:
        directory (str): Directory to check for existing files.
        filename (str): Proposed filename.
    Returns:
        str: Unique filename that does not collide with existing files.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    candidate = filename
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{base}_{counter}{ext}"
        counter += 1
    return candidate

def rename_mode(
    target_dir: str = '.',
    exts: Optional[List[str]] = None,
    dry_run: bool = False,
    llm_client: Optional[LLMClient] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    verbose: bool = True
) -> List[tuple]:
    """
    Orchestrate the renaming process: scan files, extract text, generate new names, sanitize, and rename.
    Args:
        target_dir (str): Directory to scan for files to rename.
        exts (Optional[List[str]]): List of file extensions to include. If None, all supported types are included.
        dry_run (bool): If True, do not actually rename files (just print actions).
        llm_client (Optional[LLMClient]): LLM client instance to use. If None, a new one is created.
        chunk_size (int): Max tokens per chunk for LLM input.
        chunk_overlap (int): Overlap between chunks.
        verbose (bool): If True, print progress and errors.
    Returns:
        List[tuple]: List of (old_path, new_path) tuples for renamed files.
    """
    if exts is None:
        exts = list(HANDLER_MAP.keys())
    files = scan_files(target_dir, exts)
    if not files:
        if verbose:
            print(f"No files found in {target_dir} with extensions: {exts}")
        return []
    if llm_client is None:
        llm_client = LLMClient()
    results = []
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        handler_cls = HANDLER_MAP.get(ext)
        if not handler_cls:
            if verbose:
                print(f"No handler for {file_path}")
            continue
        handler = handler_cls()
        try:
            text = handler.extract_text(file_path)
        except Exception as e:
            if verbose:
                print(f"Failed to extract text from {file_path}: {e}")
            continue
        # Chunk if needed
        chunks = llm_client.chunk_text(text, max_tokens=chunk_size, overlap=chunk_overlap)
        # Use first chunk for naming (or join if short)
        chunk_for_prompt = chunks[0] if chunks else ''
        prompt = llm_client.render_named_prompt('rename', {'text': chunk_for_prompt})
        try:
            new_name = llm_client.generate_content(prompt).strip()
        except Exception as e:
            if verbose:
                print(f"LLM failed for {file_path}: {e}")
            continue
        new_name = sanitize_filename(new_name, ext)
        dir_ = os.path.dirname(file_path)
        new_name = resolve_collision(dir_, new_name)
        new_path = os.path.join(dir_, new_name)
        if not dry_run:
            try:
                os.rename(file_path, new_path)
            except Exception as e:
                if verbose:
                    print(f"Rename failed {file_path} -> {new_path}: {e}")
                continue
        if verbose:
            print(f"{file_path} -> {new_path}")
        results.append((file_path, new_path))
    return results
