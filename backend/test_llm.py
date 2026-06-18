import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.llm_client import call_llm

async def test():
    print("Testing featherless LLM...")
    try:
        resp = await call_llm(
            system_prompt="You are a test bot.",
            user_prompt="Say hello.",
            provider="featherless",
            temperature=0.2,
            max_tokens=50
        )
        print("Response:", resp)
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(test())
