import os
import pytest
from src.services.llm_client import LLMClient

@pytest.fixture
def llm_client():
    api_key = os.getenv("GEMINI_API_KEY", "test-key")
    return LLMClient(api_key=api_key)

def test_generate_content(monkeypatch, llm_client):
    class DummyResponse:
        text = "Hello, world!"
    class DummyModels:
        def generate_content(self, model, contents, **kwargs):
            return DummyResponse()
    class DummyClient:
        models = DummyModels()
    monkeypatch.setattr(llm_client, "client", DummyClient())
    result = llm_client.generate_content("Say hello")
    assert result == "Hello, world!"
