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
        print("Testing generate_content:")
        result = client.generate_content(prompt)
        print("Response:", result)
    except Exception as e:
        print("Error in generate_content:", e)

    print("\nTesting generate_content_stream:")
    try:
        for chunk in client.generate_content_stream(prompt):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print("Error in generate_content_stream:", e)

if __name__ == "__main__":
    main()
