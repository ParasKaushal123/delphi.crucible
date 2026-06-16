"""
Bear Agent — Argues the sell/avoid thesis using AI/ML API.
"""

from agents.llm_client import call_llm
from prompts.agent_prompts import bear_system_prompt, bear_argue_prompt


async def run_bear_analysis(ticker: str, quant_summary: str) -> str:
    """
    Generate the bear (sell/avoid) case for a ticker.

    Args:
        ticker: Stock ticker symbol
        quant_summary: Clean 5-bullet data summary from PM

    Returns:
        Bear case argument text
    """
    return await call_llm(
        system_prompt=bear_system_prompt(),
        user_prompt=bear_argue_prompt(ticker, quant_summary),
        provider="aiml",
        temperature=0.7,
        max_tokens=1500,
    )
