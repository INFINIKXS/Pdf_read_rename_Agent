import pytest
from unittest.mock import MagicMock
import os
import pytest
from src.services.llm_client import LLMClient

@pytest.fixture
def llm_client():
    api_key = os.getenv("GEMINI_API_KEY", "test-key")
    return LLMClient(api_key=api_key)


def test_render_named_prompt(llm_client):
    llm_client.promptl = MagicMock()
    llm_client.promptl.prompts.render.return_value.messages = [type('msg', (), {"content": "Rendered!"})()]
    result = llm_client.render_named_prompt('rename', {'text': 'foo'})
    assert "Rendered!" in result

def test_chunk_text(llm_client):
    text = "word " * 1050
    chunks = llm_client.chunk_text(text, max_tokens=1000, overlap=100)
    assert len(chunks) == 2
