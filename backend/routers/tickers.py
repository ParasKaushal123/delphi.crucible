"""
Ticker search + price lookup endpoints.
"""

import json
import pathlib
import requests
from fastapi import APIRouter

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
    Fetch current price for a ticker via Yahoo API directly.
    """
    try:
        res = requests.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol.upper()}", headers={'User-Agent': 'Mozilla/5.0'})
        if res.status_code != 200:
            raise ValueError("Rate limited or not found")
        data = res.json()["chart"]["result"][0]["meta"]
        return {
            "ticker": symbol.upper(),
            "price": data.get("regularMarketPrice"),
            "change_pct": 0.0, # Not easily available in basic chart meta without previous close
            "market_cap_B": 0.0, # Not in basic chart meta
            "name": symbol.upper(),
        }
    except Exception as e:
        return {"ticker": symbol.upper(), "error": str(e)}
