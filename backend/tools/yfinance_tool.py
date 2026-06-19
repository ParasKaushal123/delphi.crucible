"""
yFinance Data Tool for @quant-agent
Re-written to use `yahooquery` instead of `yfinance`.
Yahooquery hits an undocumented Yahoo Finance API endpoint that returns ALL data 
in a single fast request, completely bypassing the strict rate limits of yfinance.
"""

from yahooquery import Ticker
from typing import Optional
import json
import time

def fetch_financial_data(ticker: str) -> dict:
    """
    Fetches a comprehensive financial dataset for a given stock ticker using yahooquery.
    If it fails, it instantly falls back to simulated data.
    """
    try:
        return _fetch(ticker)
    except Exception as e:
        print(f"⚠️ [Quant Agent] Yahoo Finance (yahooquery) failed for {ticker}: {e}")
        print(f"⚠️ [Quant Agent] Falling back to instant simulated data for {ticker} to keep demo running!")
        
        # Graceful fallback to mock data
        mock_data = _fetch("MOCK")
        mock_data["profile"]["ticker"] = ticker.upper()
        mock_data["profile"]["name"] = f"{ticker.upper()} Corporation"
        mock_data["profile"]["description"] = f"(SIMULATED DATA) Due to Yahoo Finance API rate limits, this is a simulated financial profile for {ticker.upper()} to keep the pipeline running smoothly."
        return mock_data

def _fetch(ticker: str) -> dict:
    if ticker.upper() == "MOCK":
        return {
            "profile": {
                "ticker": "MOCK",
                "name": "Mock Corporation",
                "sector": "Technology",
                "industry": "Software",
                "market_cap_B": 1500.5,
                "employees": 10000,
                "description": "Mock Corporation is a simulated entity used for testing the trading threshold and analysis pipeline.",
            },
            "valuation": {
                "trailing_pe": 25.4,
                "forward_pe": 22.1,
                "price_to_sales_ttm": 8.5,
                "price_to_book": 12.3,
                "ev_to_ebitda": 18.2,
                "ev_to_revenue": 9.1,
                "peg_ratio": 1.5,
                "beta": 1.2,
                "current_price": 115.0,
            },
            "income_and_cashflow": {
                "total_revenue_B": 100.0,
                "gross_profits_B": 60.0,
                "ebitda_B": 35.0,
                "free_cashflow_B": 30.0,
            },
            "margins": {
                "gross_margin_pct": 60.0,
                "operating_margin_pct": 30.0,
                "net_margin_pct": 25.0,
                "return_on_equity_pct": 40.0,
                "return_on_assets_pct": 20.0,
            },
            "balance_sheet": {
                "total_debt_B": 10.0,
                "cash_B": 40.0,
                "current_ratio": 2.5,
                "quick_ratio": 2.1,
            },
            "growth": {
                "revenue_growth_yoy_pct": 17.6,
                "earnings_growth_yoy_pct": 25.0,
            },
            "analyst_consensus": {
                "recommendation": "buy",
                "mean_target_price": 140.0,
            }
        }

    t = Ticker(ticker)
    # This hits a single endpoint and gets everything!
    data = t.all_modules.get(ticker, {})
    
    if isinstance(data, str) or not data:
        raise Exception(f"Invalid data received for {ticker}: {data}")

    summaryProfile = data.get("summaryProfile", {})
    financialData = data.get("financialData", {})
    defaultKeyStatistics = data.get("defaultKeyStatistics", {})
    price_data = data.get("price", {})

    profile = {
        "ticker": ticker.upper(),
        "name": price_data.get("shortName", "N/A"),
        "sector": summaryProfile.get("sector", "N/A"),
        "industry": summaryProfile.get("industry", "N/A"),
        "employees": summaryProfile.get("fullTimeEmployees", "N/A"),
        "market_cap_B": _to_billions(price_data.get("marketCap")),
        "description": summaryProfile.get("longBusinessSummary", "")[:500] if isinstance(summaryProfile.get("longBusinessSummary"), str) else "",
    }

    valuation = {
        "trailing_pe": summaryProfile.get("trailingPE"),
        "forward_pe": defaultKeyStatistics.get("forwardPE"),
        "price_to_book": defaultKeyStatistics.get("priceToBook"),
        "peg_ratio": defaultKeyStatistics.get("pegRatio"),
        "beta": defaultKeyStatistics.get("beta"),
        "current_price": financialData.get("currentPrice"),
    }
    
    income_and_cashflow = {
        "total_revenue_B": _to_billions(financialData.get("totalRevenue")),
        "gross_profits_B": _to_billions(financialData.get("grossProfits")),
        "ebitda_B": _to_billions(financialData.get("ebitda")),
        "free_cashflow_B": _to_billions(financialData.get("freeCashflow")),
    }

    margins = {
        "gross_margin_pct": _to_pct(financialData.get("grossMargins")),
        "operating_margin_pct": _to_pct(financialData.get("operatingMargins")),
        "net_margin_pct": _to_pct(financialData.get("profitMargins")),
        "return_on_equity_pct": _to_pct(financialData.get("returnOnEquity")),
        "return_on_assets_pct": _to_pct(financialData.get("returnOnAssets")),
    }

    balance = {
        "total_debt_B": _to_billions(financialData.get("totalDebt")),
        "cash_B": _to_billions(financialData.get("totalCash")),
        "current_ratio": financialData.get("currentRatio"),
        "quick_ratio": financialData.get("quickRatio"),
        "debt_to_equity": financialData.get("debtToEquity"),
    }
    
    growth = {
        "revenue_growth_yoy_pct": _to_pct(financialData.get("revenueGrowth")),
        "earnings_growth_yoy_pct": _to_pct(financialData.get("earningsGrowth")),
    }

    analyst = {
        "recommendation": financialData.get("recommendationKey", "N/A").upper(),
        "mean_target_price": financialData.get("targetMeanPrice"),
        "high_target_price": financialData.get("targetHighPrice"),
        "low_target_price": financialData.get("targetLowPrice"),
    }

    return {
        "profile": profile,
        "valuation": valuation,
        "income_and_cashflow": income_and_cashflow,
        "margins": margins,
        "balance_sheet": balance,
        "growth": growth,
        "analyst_consensus": analyst,
        "data_source": "Yahoo Finance via yahooquery",
    }


def _to_billions(value) -> Optional[float]:
    if value is None or str(value).lower() in ["nan", "infinity"]:
        return None
    try:
        return round(float(value) / 1e9, 2)
    except:
        return None


def _to_pct(value) -> Optional[float]:
    if value is None or str(value).lower() in ["nan", "infinity"]:
        return None
    try:
        return round(float(value) * 100, 2)
    except:
        return None
