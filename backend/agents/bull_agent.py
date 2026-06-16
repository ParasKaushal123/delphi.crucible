"""
Bull Agent — Argues the buy thesis using AI/ML API.
"""

from agents.llm_client import call_llm
from prompts.agent_prompts import bull_system_prompt, bull_argue_prompt


async def run_bull_analysis(ticker: str, quant_summary: str) -> str:
    """
    Generate the bull (buy) case for a ticker.

    Args:
        ticker: Stock ticker symbol
        quant_summary: Clean 5-bullet data summary from PM

    Returns:
        Bull case argument text
    """
    return await call_llm(
        system_prompt=bull_system_prompt(),
        user_prompt=bull_argue_prompt(ticker, quant_summary),
        provider="aiml",
        temperature=0.7,
        max_tokens=1500,
    )
