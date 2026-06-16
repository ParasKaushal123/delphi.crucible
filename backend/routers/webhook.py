"""
Band Webhook endpoint + Pipeline trigger via REST.
"""

import asyncio
import re
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from agents.pm_agent import run_full_pipeline
from config import settings


router = APIRouter()


class BandWebhookPayload(BaseModel):
    """Incoming webhook payload from Band."""
    content: str = ""
    band_key: str = ""
    post_key: str = ""
    author: dict = {}
    # Band sends various fields; we only need content + band_key


class AnalysisRequest(BaseModel):
    """REST trigger for the pipeline (from our frontend)."""
    ticker: str
    band_key: Optional[str] = ""


@router.post("/webhook/band")
async def band_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives ALL Band webhook events.
    Parses @mentions and dispatches to the PM agent pipeline.
    """
    body = await request.json()
    content = body.get("content", "")
    band_key = body.get("band_key", "")

    # Check if the message mentions the PM agent and contains a ticker
    if settings.PM_AGENT_NAME in content.lower() or "pm-agent" in content.lower():
        # Extract ticker from $TICKER pattern
        ticker_match = re.search(r'\$([A-Z]{1,5})', content.upper())
        if ticker_match:
            ticker = ticker_match.group(1)
            store = request.app.state.session_store
            background_tasks.add_task(
                run_full_pipeline, ticker, store, band_key
            )
            return {"status": "accepted", "ticker": ticker, "message": "Pipeline started"}

    return {"status": "ignored", "message": "No actionable @mention found"}


@router.post("/api/analyze")
async def trigger_analysis(req: AnalysisRequest, request: Request, background_tasks: BackgroundTasks):
    """
    REST endpoint for the frontend to trigger analysis directly.
    This bypasses Band and runs the pipeline locally.
    """
    store = request.app.state.session_store
    background_tasks.add_task(
        run_full_pipeline, req.ticker, store, req.band_key or ""
    )
    return {
        "status": "accepted",
        "ticker": req.ticker.upper(),
        "message": f"Analysis pipeline started for ${req.ticker.upper()}",
    }


@router.get("/api/session")
async def get_active_session(request: Request):
    """Get the most recent active session state."""
    store = request.app.state.session_store
    session = await store.get_active_session()
    if session is None:
        return {"session": None}
    return {"session": session.to_dict()}


@router.get("/api/session/{session_id}")
async def get_session(session_id: str, request: Request):
    """Get a specific session by ID."""
    store = request.app.state.session_store
    session = await store.get_session(session_id)
    if session is None:
        return {"error": "Session not found"}, 404
    return {"session": session.to_dict()}
