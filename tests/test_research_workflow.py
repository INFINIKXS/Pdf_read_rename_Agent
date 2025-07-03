
import os
import tempfile
import pytest
from unittest.mock import MagicMock
from src.agent_core.research_workflow import ResearchWorkflow

class DummyPDFHandler:
    def extract_text(self, file_path, **kwargs):
        return "Dummy PDF content"

class DummyLLM:
    def generate_content(self, prompt, **kwargs):
        return "0.9"

def test_filter_pdfs():
    workflow = ResearchWorkflow(llm_client=DummyLLM(), pdf_handler=DummyPDFHandler())
    with tempfile.NamedTemporaryFile('w', suffix='.pdf', delete=False) as f:
        f.write("irrelevant")
        f.flush()
        path = f.name
    try:
        result = workflow.filter_pdfs([path], score_threshold=0.5)
        assert path in result
    finally:
        os.remove(path)

def test_copy_relevant_pdfs():
    workflow = ResearchWorkflow(llm_client=DummyLLM(), pdf_handler=DummyPDFHandler())
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        file_path = os.path.join(src_dir, "file.pdf")
        with open(file_path, "w") as f:
            f.write("irrelevant")
        copied = workflow.copy_relevant_pdfs(src_dir, dest_dir, score_threshold=0.5, verbose=False)
        assert any(os.path.basename(file_path) in c for c in copied)
