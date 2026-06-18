"""
Band Webhook endpoint + Pipeline trigger via REST.
"""

import asyncio
import re
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import json

from band_api.client import BandClient

from agents.pm_agent import run_full_pipeline
from config import settings
from state.session_store import Phase


router = APIRouter()


class BandWebhookPayload(BaseModel):
    """Incoming webhook payload from Band."""
    # Note: Band typically uses WebSockets, but if a webhook proxy is used, it wraps the event.
    message: dict = {}
    chat_id: str = ""
    event_type: str = ""


class AnalysisRequest(BaseModel):
    """REST trigger for the pipeline (from our frontend)."""
    ticker: str
    band_key: Optional[str] = ""


# Note: The /webhook/band endpoint was removed.
# Agents now run natively via band-sdk WebSockets (see agents/adapters.py).

@router.post("/api/analyze")
async def trigger_analysis(req: AnalysisRequest, request: Request):
    """
    REST endpoint for the frontend to trigger analysis directly.
    Creates the Band Room and sends the first message to the PM Agent.
    """
    import uuid
    from band_api.client import get_pm_client
    
    store = request.app.state.session_store
    session_id = str(uuid.uuid4())
    ticker = req.ticker.upper()
    
    # 1. Create session in Redis
    session = await store.create_session(
        session_id=session_id,
        ticker=ticker,
        main_room_id="",
    )
    
    # 2. Create Band Chat Room
    pm_client = get_pm_client()
    try:
        chat_resp = await pm_client.create_chat_room()
        print("CHAT_RESP_WEBHOOK:", chat_resp)
        chat_id = chat_resp.get("data", {}).get("id") or chat_resp.get("id")
        print("EXTRACTED_CHAT_ID:", chat_id)
        
        session.main_room_id = chat_id
        session.phase = Phase.ROLL_CALL
        await store.update_session(session)

        # Add all agents to the main room for roll call
        await pm_client.add_participant(chat_id, settings.QUANT_AGENT_ID)
        await pm_client.add_participant(chat_id, settings.BULL_AGENT_ID)
        await pm_client.add_participant(chat_id, settings.BEAR_AGENT_ID)

        # Wait for agents to sync history so this arrives as a live message
        import asyncio
        await asyncio.sleep(2)

        # Trigger Roll Call
        await pm_client.send_message(
            chat_id=chat_id,
            content=f"@{settings.QUANT_AGENT_NAME} @{settings.BULL_AGENT_NAME} @{settings.BEAR_AGENT_NAME} Roll call! Please confirm your systems are online.",
            mentions=[
                {"id": settings.QUANT_AGENT_ID, "handle": settings.QUANT_AGENT_NAME},
                {"id": settings.BULL_AGENT_ID, "handle": settings.BULL_AGENT_NAME},
                {"id": settings.BEAR_AGENT_ID, "handle": settings.BEAR_AGENT_NAME},
            ]
        )
    finally:
        await pm_client.close()
        
    return {
        "status": "accepted",
        "ticker": ticker,
        "session_id": session_id,
        "message": f"Analysis pipeline started for ${ticker}",
    }


@router.post("/api/simulate-market-tick")
async def simulate_market_tick(request: Request, background_tasks: BackgroundTasks):
    """
    Simulates a Watcher Agent detecting a >5% drop in NVDA from the user's portfolio.
    Bypasses Band and directly triggers the emergency pipeline.
    """
    store = request.app.state.session_store
    
    # 1. Fetch NVDA from mock profile
    raw_profile = await store._redis.get("user_profile:demo_user")
    if not raw_profile:
        return {"error": "Mock user not seeded"}
        
    profile = json.loads(raw_profile)
    nvda_position = profile.get("portfolio", {}).get("NVDA")
    if not nvda_position:
        return {"error": "NVDA not found in mock portfolio"}
        
    old_price = nvda_position["buy_price"]
    new_price = old_price * 0.92  # -8% drop
    
    # 2. Trigger emergency pipeline locally
    background_tasks.add_task(
        run_full_pipeline,
        ticker="NVDA",
        session_store=store,
        band_key="",
        extracted_text=None,
        company_name=None,
        is_emergency=True
    )
    
    return {
        "status": "accepted",
        "message": f"Simulated -8% drop for NVDA (from ${old_price} to ${new_price:.2f}). Emergency pipeline started.",
        "is_emergency": True
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
