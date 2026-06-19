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
    import asyncio
    from tools.yfinance_tool import fetch_financial_data

    raw_data = await asyncio.to_thread(fetch_financial_data, ticker)
    raw_json = json.dumps(raw_data, indent=2, default=str)

    # Bypass the slow LLM formatting step and render the Markdown tables natively!
    formatted_report = f"## 📊 Financial Data for ${ticker.upper()}\n\n"
    
    for section, data in raw_data.items():
        if not data: continue
        formatted_report += f"### {section.replace('_', ' ').title()}\n"
        
        # If it's nested (like income statement years)
        if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
            years = list(data.keys())
            metrics = list(next(iter(data.values())).keys())
            formatted_report += f"| Metric | {' | '.join(years)} |\n"
            formatted_report += f"|---|" + "|---" * len(years) + "|\n"
            for metric in metrics:
                row = [f"**{metric.replace('_', ' ').title()}**"]
                for year in years:
                    val = data[year].get(metric)
                    row.append(str(val) if val is not None else "N/A")
                formatted_report += f"| {' | '.join(row)} |\n"
        
        # Standard flat dictionary
        elif isinstance(data, dict):
            formatted_report += "| Metric | Value |\n|---|---|\n"
            for k, v in data.items():
                if k != "description":
                    formatted_report += f"| **{k.replace('_', ' ').title()}** | {v if v is not None else 'N/A'} |\n"
            if "description" in data:
                formatted_report += f"\n> {data['description']}\n"
                
        formatted_report += "\n"

    return {
        "raw_data": raw_json,
        "formatted_report": formatted_report,
    }
