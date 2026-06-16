"""
Ticker search + price lookup endpoints.
"""

import json
import pathlib
from fastapi import APIRouter
import yfinance as yf

router = APIRouter()

# Load curated ticker list at startup
_TICKERS_FILE = pathlib.Path(__file__).parent.parent / "data" / "tickers.json"
TICKERS: list[dict] = []
if _TICKERS_FILE.exists():
    TICKERS = json.loads(_TICKERS_FILE.read_text(encoding="utf-8"))


@router.get("/api/tickers/search")
def search_tickers(q: str = "", limit: int = 10) -> list[dict]:
    """
    Fuzzy-searches the curated ticker list by symbol or company name.
    Returns up to `limit` results sorted by relevance score.
    """
    if not q or len(q) < 1:
        return TICKERS[:limit]

    q_upper = q.upper().strip()
    q_lower = q.lower().strip()

    results = []
    for t in TICKERS:
        score = 0
        ticker = t["ticker"]
        name = t["name"].lower()

        if ticker == q_upper:
            score = 100
        elif ticker.startswith(q_upper):
            score = 80
        elif name.startswith(q_lower):
            score = 60
        elif q_lower in name:
            score = 40
        elif q_upper in ticker:
            score = 30

        if score > 0:
            results.append({**t, "_score": score})

    results.sort(key=lambda x: -x["_score"])
    return [{k: v for k, v in r.items() if k != "_score"} for r in results[:limit]]


@router.get("/api/tickers/{symbol}/price")
def get_ticker_price(symbol: str) -> dict:
    """
    Fetch current price for a ticker via yfinance.
    Fast — uses fast_info for minimal API calls.
    """
    try:
        stock = yf.Ticker(symbol.upper())
        info = stock.info
        return {
            "ticker": symbol.upper(),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "change_pct": round((info.get("regularMarketChangePercent") or 0), 2),
            "market_cap_B": round((info.get("marketCap") or 0) / 1e9, 2),
            "name": info.get("longName", symbol.upper()),
        }
    except Exception as e:
        return {"ticker": symbol.upper(), "error": str(e)}
