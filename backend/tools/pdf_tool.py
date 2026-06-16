"""
PDF Tool — Fast text extractor for 10-K / annual report PDFs.
Strategy for large PDFs (130+ pages):
  - Run pdfplumber in a ThreadPoolExecutor (non-blocking for asyncio)
  - For very large PDFs, use smart page sampling instead of reading every page
  - Prioritise pages with key financial keywords
  - Hard cap on total characters sent to LLM (60k)
"""

import pdfplumber
import io
import concurrent.futures
from typing import Tuple

# ── Tuning constants ───────────────────────────────────────────────────
MAX_CHARS = 55_000          # chars sent to LLM (covers ~40+ dense pages)
MAX_PAGES_FULL = 60         # below this → read every page
SAMPLE_INTERVAL = 2         # above MAX_PAGES_FULL → read every Nth page
MAX_CHARS_PER_PAGE = 3_000  # prevent a single huge page from eating the budget
_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)

PRIORITY_KEYWORDS = [
    "selected financial data",
    "consolidated balance sheet",
    "consolidated statements",
    "income from operations",
    "cash and cash equivalents",
    "total revenue",
    "net revenues",
    "earnings per share",
    "management's discussion",
    "results of operations",
    "liquidity and capital",
    "total assets",
    "total liabilities",
    "stockholders' equity",
    "free cash flow",
    "operating income",
]


def _extract_sync(pdf_bytes: bytes) -> Tuple[str, int]:
    """
    Synchronous core — called inside a thread pool so it doesn't block asyncio.
    Uses smart page sampling for PDFs > MAX_PAGES_FULL pages.
    """
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)

        # Decide which pages to read
        if total_pages <= MAX_PAGES_FULL:
            page_indices = list(range(total_pages))
        else:
            # Sample every Nth page + always include first 10 and last 20
            # (10-Ks have cover/overview at start; financials near end)
            sampled = set(range(0, total_pages, SAMPLE_INTERVAL))
            sampled.update(range(min(10, total_pages)))               # first 10
            sampled.update(range(max(0, total_pages - 25), total_pages))  # last 25
            page_indices = sorted(sampled)

        # Extract text per page and score by financial keyword density
        scored_pages: list[tuple[int, str]] = []
        for i in page_indices:
            try:
                text = pdf.pages[i].extract_text(x_tolerance=2, y_tolerance=2) or ""
            except Exception:
                continue
            text = text.strip()
            if len(text) < 80:          # skip near-empty pages
                continue
            text = text[:MAX_CHARS_PER_PAGE]
            text_lower = text.lower()
            score = sum(1 for kw in PRIORITY_KEYWORDS if kw in text_lower)
            scored_pages.append((score, text))

        # High-priority pages first, then fill remaining budget
        scored_pages.sort(key=lambda x: x[0], reverse=True)

        parts: list[str] = []
        chars_used = 0
        for _, page_text in scored_pages:
            remaining = MAX_CHARS - chars_used
            if remaining <= 0:
                break
            chunk = page_text[:remaining]
            parts.append(chunk)
            chars_used += len(chunk)

        full_text = "\n\n---\n\n".join(parts)
        return full_text, total_pages


async def extract_pdf_text(pdf_bytes: bytes) -> Tuple[str, int]:
    """
    Async wrapper — runs pdfplumber in a thread so FastAPI stays non-blocking.
    Returns (extracted_text, page_count).
    """
    import asyncio
    return await asyncio.to_thread(_extract_sync, pdf_bytes)


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """Extract basic PDF metadata for display. Fast — only reads metadata, not pages."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            meta = pdf.metadata or {}
            return {
                "pages": len(pdf.pages),
                "title": meta.get("Title", ""),
                "author": meta.get("Author", ""),
            }
    except Exception:
        return {"pages": 0, "title": "", "author": ""}
