"""
Quick test script for LLMClient (Gemini API)
References: AGENTS.md, Agent_Building_Guidlines
"""

import os
from dotenv import load_dotenv
load_dotenv()
from src.services.llm_client import LLMClient

def main():
    client = LLMClient()

    prompt = "Say hello and tell me the current year."
    try:
        print("Testing generate_content_with_grounding (Exa web search):")
        result = client.generate_content_with_grounding(
            prompt=prompt,
            search_query="current year"
        )
        print("Response:", result)
    except Exception as e:
        print("Error in generate_content_with_grounding:", e)

if __name__ == "__main__":
    main()
