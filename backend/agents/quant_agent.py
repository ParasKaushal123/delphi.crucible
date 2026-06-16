"""
Quant Agent — Data fetcher.
Supports two modes:
  1. Ticker mode: fetch data via yfinance (default)
  2. PDF mode: use pre-extracted text from a 10-K upload
"""

import json
from agents.llm_client import call_llm
from prompts.agent_prompts import (
    quant_system_prompt,
    quant_format_data_prompt,
    quant_pdf_prompt,
)


async def run_quant_analysis(
    ticker: str,
    extracted_text: str | None = None,
    company_name: str | None = None,
) -> dict:
    """
    Execute the quant agent's full workflow.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL"), or a label like "PDF Upload"
        extracted_text: If provided, skip yfinance and use this PDF text instead
        company_name: Human-readable company name (used in PDF mode)

    Returns:
        dict with "raw_data" (str) and "formatted_report" (LLM output)
    """

    # ── PDF MODE ──────────────────────────────────────────────
    if extracted_text:
        name = company_name or ticker
        raw_json = json.dumps(
            {"source": "10-K PDF upload", "company": name, "text_length": len(extracted_text)},
            indent=2,
        )

        formatted_report = await call_llm(
            system_prompt=quant_system_prompt(),
            user_prompt=quant_pdf_prompt(name, extracted_text),
            provider="featherless",
            temperature=0.2,
            max_tokens=3000,
        )

        return {
            "raw_data": raw_json,
            "formatted_report": formatted_report,
        }

    # ── TICKER MODE (yfinance) ─────────────────────────────────
    from tools.yfinance_tool import fetch_financial_data  # lazy import — avoids slow startup

    raw_data = fetch_financial_data(ticker)
    raw_json = json.dumps(raw_data, indent=2, default=str)

    formatted_report = await call_llm(
        system_prompt=quant_system_prompt(),
        user_prompt=quant_format_data_prompt(ticker, raw_json),
        provider="featherless",
        temperature=0.2,
        max_tokens=2500,
    )

    return {
        "raw_data": raw_json,
        "formatted_report": formatted_report,
    }
