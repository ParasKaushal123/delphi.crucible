"""
yFinance Data Tool for @quant-agent
Fetches comprehensive financial data for a given ticker.
Returns a structured dict ready for LLM summarization.
Retries every 15 seconds on Yahoo Finance rate limit errors.
"""

import yfinance as yf
import pandas as pd
from typing import Optional
import json
import sys
import time

MAX_RETRIES = 5
RETRY_WAIT_SECONDS = 15  # flat 15-second wait on every rate limit hit


def fetch_financial_data(ticker: str) -> dict:
    """
    Fetches a comprehensive financial dataset for a given stock ticker.
    Retries every 15 seconds on Yahoo Finance rate limit (429) errors.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")

    Returns:
        dict with 9 sections: profile, valuation, income_statement,
        margins, balance_sheet, cash_flow, growth, analyst, dividends
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _fetch(ticker)
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            is_rate_limit = (
                "too many requests" in err_str
                or "rate limit" in err_str
                or "429" in err_str
            )
            if is_rate_limit and attempt < MAX_RETRIES:
                print(
                    f"[RETRY {attempt}/{MAX_RETRIES}] Yahoo Finance rate limited for "
                    f"{ticker}. Waiting {RETRY_WAIT_SECONDS}s before retry..."
                )
                time.sleep(RETRY_WAIT_SECONDS)
            else:
                raise  # Non-rate-limit error or final attempt — bubble up

    raise Exception(
        f"Failed to fetch data for {ticker} after {MAX_RETRIES} attempts: {last_error}"
    )


def _fetch(ticker: str) -> dict:
    """Single fetch attempt — called by fetch_financial_data with retry wrapper."""
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
                "52w_high": 150.0,
                "52w_low": 80.0,
                "current_price": 115.0,
            },
            "income_statement": {
                "2023": {"revenue_B": 100.0, "gross_profit_B": 60.0, "ebit_B": 30.0, "net_income_B": 25.0},
                "2022": {"revenue_B": 85.0, "gross_profit_B": 50.0, "ebit_B": 24.0, "net_income_B": 20.0},
                "2021": {"revenue_B": 70.0, "gross_profit_B": 40.0, "ebit_B": 18.0, "net_income_B": 15.0},
            },
            "margins": {
                "gross_margin_pct": 60.0,
                "operating_margin_pct": 30.0,
                "net_margin_pct": 25.0,
                "ebitda_margin_pct": 35.0,
                "return_on_equity_pct": 40.0,
                "return_on_assets_pct": 20.0,
            },
            "balance_sheet": {
                "total_debt_B": 10.0,
                "cash_B": 40.0,
                "net_cash_B": 30.0,
            },
            "cash_flow": {
                "operating_cash_flow_B": 35.0,
                "free_cash_flow_B": 30.0,
            },
            "growth": {
                "revenue_growth_pct": 17.6,
                "earnings_growth_pct": 25.0,
            },
            "analyst": {
                "recommendation": "buy",
                "target_mean_price": 140.0,
            },
            "dividends": {
                "dividend_yield_pct": 1.2,
                "payout_ratio_pct": 30.5,
            }
        }

    stock = yf.Ticker(ticker)
    info = stock.info

    # --- 1. Company Profile ---
    profile = {
        "ticker": ticker.upper(),
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap_B": round(info.get("marketCap", 0) / 1e9, 2),
        "employees": info.get("fullTimeEmployees", "N/A"),
        "description": info.get("longBusinessSummary", "")[:500],
    }

    # --- 2. Valuation Multiples ---
    valuation = {
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_sales_ttm": info.get("priceToSalesTrailing12Months"),
        "price_to_book": info.get("priceToBook"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "ev_to_revenue": info.get("enterpriseToRevenue"),
        "peg_ratio": info.get("pegRatio"),
        "beta": info.get("beta"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "current_price": info.get("currentPrice"),
    }

    # --- 3. Income Statement (Annual, last 3 years) ---
    income_stmt_raw = stock.financials
    income_data = {}
    if income_stmt_raw is not None and not income_stmt_raw.empty:
        for col in income_stmt_raw.columns[:3]:
            year_label = str(col.year)
            income_data[year_label] = {
                "revenue_B": _to_billions(_safe_get(income_stmt_raw, "Total Revenue", col)),
                "gross_profit_B": _to_billions(_safe_get(income_stmt_raw, "Gross Profit", col)),
                "ebit_B": _to_billions(_safe_get(income_stmt_raw, "EBIT", col)),
                "net_income_B": _to_billions(_safe_get(income_stmt_raw, "Net Income", col)),
            }

    # --- 4. Margins (TTM) ---
    margins = {
        "gross_margin_pct": _to_pct(info.get("grossMargins")),
        "operating_margin_pct": _to_pct(info.get("operatingMargins")),
        "net_margin_pct": _to_pct(info.get("profitMargins")),
        "ebitda_margin_pct": _to_pct(info.get("ebitdaMargins")),
        "return_on_equity_pct": _to_pct(info.get("returnOnEquity")),
        "return_on_assets_pct": _to_pct(info.get("returnOnAssets")),
    }

    # --- 5. Balance Sheet (Most Recent) ---
    balance_raw = stock.balance_sheet
    balance = {}
    if balance_raw is not None and not balance_raw.empty:
        latest = balance_raw.columns[0]
        total_debt = _safe_get(balance_raw, "Total Debt", latest)
        cash = _safe_get(balance_raw, "Cash And Cash Equivalents", latest)
        balance = {
            "total_debt_B": _to_billions(total_debt),
            "cash_B": _to_billions(cash),
            "net_debt_B": _to_billions(
                total_debt - cash if total_debt is not None and cash is not None else None
            ),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
        }

    # --- 6. Cash Flow (3 years) ---
    cf_raw = stock.cashflow
    cash_flow = {}
    if cf_raw is not None and not cf_raw.empty:
        for col in cf_raw.columns[:3]:
            year_label = str(col.year)
            op_cf = _safe_get(cf_raw, "Operating Cash Flow", col)
            capex = _safe_get(cf_raw, "Capital Expenditure", col)
            fcf = (op_cf + capex) if (op_cf is not None and capex is not None) else None
            cash_flow[year_label] = {
                "operating_cf_B": _to_billions(op_cf),
                "capex_B": _to_billions(capex),
                "free_cash_flow_B": _to_billions(fcf),
            }

    # --- 7. Growth Rates ---
    growth = {
        "revenue_growth_yoy_pct": _to_pct(info.get("revenueGrowth")),
        "earnings_growth_yoy_pct": _to_pct(info.get("earningsGrowth")),
        "earnings_quarterly_growth_yoy_pct": _to_pct(info.get("earningsQuarterlyGrowth")),
        "forward_eps": info.get("forwardEps"),
        "trailing_eps": info.get("trailingEps"),
    }

    # --- 8. Analyst Consensus ---
    analyst = {
        "recommendation": info.get("recommendationKey", "N/A").upper(),
        "mean_target_price": info.get("targetMeanPrice"),
        "high_target_price": info.get("targetHighPrice"),
        "low_target_price": info.get("targetLowPrice"),
        "num_analyst_opinions": info.get("numberOfAnalystOpinions"),
        "implied_upside_pct": _calc_upside(
            info.get("currentPrice"), info.get("targetMeanPrice")
        ),
    }

    # --- 9. Dividends ---
    dividends = {
        "dividend_yield_pct": _to_pct(info.get("dividendYield")),
        "payout_ratio_pct": _to_pct(info.get("payoutRatio")),
        "ex_dividend_date": str(info.get("exDividendDate", "N/A")),
    }

    return {
        "profile": profile,
        "valuation": valuation,
        "income_statement_by_year": income_data,
        "margins": margins,
        "balance_sheet": balance,
        "cash_flow_by_year": cash_flow,
        "growth": growth,
        "analyst_consensus": analyst,
        "dividends": dividends,
        "data_source": "Yahoo Finance via yfinance",
        "fetch_timestamp": pd.Timestamp.utcnow().isoformat(),
    }


# ─── Helpers ───────────────────────────────────────────────

def _to_billions(value) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return round(float(value) / 1e9, 2)


def _to_pct(value) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return round(float(value) * 100, 2)


def _safe_get(df: pd.DataFrame, row_label: str, col):
    try:
        val = df.loc[row_label, col]
        return None if pd.isna(val) else float(val)
    except (KeyError, TypeError):
        return None


def _calc_upside(current_price, target_price) -> Optional[float]:
    if current_price and target_price and current_price > 0:
        return round(((target_price - current_price) / current_price) * 100, 2)
    return None


# ─── CLI Test ──────────────────────────────────────────────

if __name__ == "__main__":
    tickers = ["AAPL"]
    if len(sys.argv) > 1 and "--tickers" in sys.argv[1]:
        tickers = sys.argv[1].split("=")[1].split(",") if "=" in sys.argv[1] else sys.argv[2].split(",")
    elif len(sys.argv) > 2 and sys.argv[1] == "--tickers":
        tickers = sys.argv[2].split(",")

    for t in tickers:
        print(f"\n{'='*60}")
        print(f"  Fetching data for: {t.upper()}")
        print(f"{'='*60}")
        data = fetch_financial_data(t.strip())
        print(json.dumps(data, indent=2, default=str))
