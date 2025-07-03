
import os
import tempfile
import pytest
from unittest.mock import MagicMock
from src.agent_core import rename_workflow

class DummyLLM:
    def chunk_text(self, text, max_tokens=1000, overlap=100):
        return [text]
    def render_named_prompt(self, name, params):
        return f"Prompt: {params['text']}"
    def generate_content(self, prompt):
        return "Renamed_Document"

def test_rename_mode(monkeypatch):
    # Create a dummy txt file
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Test content for rename workflow.")
        # Patch handler map to only txt
        monkeypatch.setattr(rename_workflow, "HANDLER_MAP", {".txt": rename_workflow.TxtHandler})
        # Patch TxtHandler to avoid actual file reading
        monkeypatch.setattr(rename_workflow.TxtHandler, "extract_text", lambda self, fp, **kw: "Dummy text")
        # Run rename_mode with DummyLLM
        results = rename_workflow.rename_mode(target_dir=tmpdir, exts=[".txt"], dry_run=True, llm_client=DummyLLM(), verbose=False)
        assert len(results) == 1
        old_path, new_path = results[0]
        assert old_path == file_path
        assert new_path.endswith("Renamed_Document.txt")
