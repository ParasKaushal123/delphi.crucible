"""
PM Agent (Portfolio Manager) — The Coordinator.
Orchestrates the full multi-room workflow via Band.
"""

import asyncio
import uuid
import json
from datetime import datetime

from agents.llm_client import call_llm
from agents.quant_agent import run_quant_analysis
from agents.bull_agent import run_bull_analysis
from agents.bear_agent import run_bear_analysis
from band_api.client import get_pm_client, get_quant_client
from state.session_store import SessionStore, SessionState, Phase
from prompts.agent_prompts import (
    pm_system_prompt,
    pm_summarize_data_prompt,
    pm_final_memo_prompt,
)


async def run_full_pipeline(
    ticker: str,
    session_store: SessionStore,
    band_key: str = "",
    extracted_text: str | None = None,
    company_name: str | None = None,
    is_emergency: bool = False,
) -> str:
    """
    Execute the full Investment Memo pipeline.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL"), or a label like "PDF" in PDF mode
        session_store: Redis session store instance
        band_key: Band room key (optional)
        extracted_text: Pre-extracted PDF text — if set, skips yfinance entirely
        company_name: Human-readable company name for PDF mode

    Returns:
        Final investment memo as markdown string
    """
    label = company_name or f"${ticker.upper()}"   # display name in messages
    session_id = str(uuid.uuid4())[:8]
    pm_client = get_pm_client() if band_key else None
    pdf_mode = bool(extracted_text)

    # ═══════════════════════════════════════════════════════════
    # PHASE 1: Create Session
    # ═══════════════════════════════════════════════════════════
    session = await session_store.create_session(
        session_id=session_id,
        ticker=ticker.upper(),
        main_room_id=band_key,
    )
    session.is_emergency = is_emergency
    await session_store.update_session(session)

    await session_store.publish_room_message(
        session_id, "main", "pm-agent",
        f"Received request to analyze **{label}**. Initiating multi-agent workflow..."
    )

    # ═══════════════════════════════════════════════════════════
    # PHASE 2: Data Cave — Quant Agent fetches data (Skipped if Emergency)
    # ═══════════════════════════════════════════════════════════
    if is_emergency:
        session.phase = Phase.DATA_CAVE_COMPLETE
        quant_summary = f"🚨 EMERGENCY ALERT: {label} price has dropped more than 5%! Immediate Re-evaluation Required: Hold vs. Sell."
        session.quant_summary = quant_summary
        await session_store.update_session(session)
        await session_store.publish_phase_change(session_id, Phase.DATA_CAVE_COMPLETE.value,
                                                 "Emergency mode: Bypassing Data Cave.")
        await session_store.publish_room_message(
            session_id, "main", "pm-agent",
            f"🚨 **EMERGENCY DETECTED for {label}.** Bypassing Data Cave. Spinning up Debate Ring immediately!"
        )
    else:
        session.phase = Phase.DATA_CAVE_OPEN
        session.data_cave_id = f"data-cave-{session_id}"
        await session_store.update_session(session)
        await session_store.publish_phase_change(session_id, Phase.DATA_CAVE_OPEN.value,
                                                 f"Opening Data Cave for ${ticker.upper()}")
    
        await session_store.publish_room_message(
            session_id, "main", "pm-agent",
            f"Creating **Data Cave** room and dispatching @quant-agent..."
        )
        await session_store.publish_room_message(
            session_id, "data-cave", "pm-agent",
            f"@quant-agent Pull comprehensive financial data for **{label}**."
            + (" (Source: 10-K PDF upload)" if pdf_mode else " (Source: Yahoo Finance)")
        )
    
        # Send to Band if connected
        if pm_client and band_key:
            await pm_client.send_as_agent(
                band_key, "pm-agent",
                f"🏗️ Creating Data Cave for ${ticker.upper()}. Dispatching @quant-agent for data pull..."
            )
    
        # Run quant analysis
        await session_store.publish_room_message(
            session_id, "data-cave", "quant-agent",
            f"Fetching financial data for **{label}** from "
            + ("uploaded PDF..." if pdf_mode else "Yahoo Finance...")
        )
    
        try:
            quant_result = await run_quant_analysis(
                ticker,
                extracted_text=extracted_text,
                company_name=company_name,
            )
        except Exception as e:
            err_str = str(e)
            session.phase = Phase.ERROR
            session.error = f"Quant agent failed: {err_str}"
            await session_store.update_session(session)
            await session_store.publish_room_message(
                session_id, "data-cave", "quant-agent",
                f"Error fetching data: {err_str}\n\nTip: Yahoo Finance sometimes rate-limits. Click Generate again to retry."
            )
            await session_store.publish_phase_change(
                session_id, Phase.ERROR.value,
                f"Pipeline error — {err_str}"
            )
            return f"Error: Quant agent failed — {err_str}"
    
        session.raw_financial_data = quant_result["raw_data"]
        await session_store.update_session(session)
    
        # Publish raw data dump to Data Cave
        raw_preview = quant_result["raw_data"][:2000] + "\n... [truncated for display]"
        await session_store.publish_room_message(
            session_id, "data-cave", "quant-agent",
            f"📊 **Raw Financial Data (JSON):**\n```json\n{raw_preview}\n```"
        )
        await session_store.publish_room_message(
            session_id, "data-cave", "quant-agent",
            f"📋 **Formatted Report:**\n{quant_result['formatted_report']}"
        )
    
        # PM summarizes into 5 bullets
        await session_store.publish_room_message(
            session_id, "data-cave", "pm-agent",
            "🧠 Synthesizing data into a clean 5-bullet summary..."
        )
    
        quant_summary = await call_llm(
            system_prompt=pm_system_prompt(),
            user_prompt=pm_summarize_data_prompt(ticker, quant_result["formatted_report"]),
            provider="aiml",
            temperature=0.3,
            max_tokens=1000,
        )
    
        session.quant_summary = quant_summary
        session.phase = Phase.DATA_CAVE_COMPLETE
        await session_store.update_session(session)
        await session_store.publish_phase_change(session_id, Phase.DATA_CAVE_COMPLETE.value,
                                                 "Data synthesized. Closing Data Cave.")
    
        await session_store.publish_room_message(
            session_id, "data-cave", "pm-agent",
            f"✅ **Summary Complete:**\n{quant_summary}\n\n🚪 *Leaving Data Cave.*"
        )
        await session_store.publish_room_message(
            session_id, "main", "pm-agent",
            "✅ Data Cave complete. 5-bullet summary extracted. Opening Debate Ring..."
        )
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 3: Debate Ring — Bull + Bear argue in parallel
    # ═══════════════════════════════════════════════════════════
    session.phase = Phase.DEBATE_RING_OPEN
    session.debate_ring_id = f"debate-ring-{session_id}"
    await session_store.update_session(session)
    await session_store.publish_phase_change(session_id, Phase.DEBATE_RING_OPEN.value,
                                             "Opening Debate Ring for Bull vs Bear")

    await session_store.publish_room_message(
        session_id, "debate-ring", "pm-agent",
        f"Debate Ring — **{label}**\n\n"
        f"@bull-agent @bear-agent Based on this data, give me your best arguments:\n\n{quant_summary}"
    )

    if pm_client and band_key:
        await pm_client.send_as_agent(
            band_key, "pm-agent",
            f"⚔️ Opening Debate Ring. Bull and Bear agents are analyzing ${ticker.upper()} in parallel..."
        )

    # Run Bull + Bear in parallel
    await session_store.publish_room_message(
        session_id, "debate-ring", "bull-agent",
        "🟢 Analyzing data for buy thesis..."
    )
    await session_store.publish_room_message(
        session_id, "debate-ring", "bear-agent",
        "🔴 Analyzing data for sell thesis..."
    )

    bull_task = asyncio.create_task(run_bull_analysis(ticker, quant_summary))
    bear_task = asyncio.create_task(run_bear_analysis(ticker, quant_summary))

    bull_arg, bear_arg = await asyncio.gather(bull_task, bear_task)

    session.bull_argument = bull_arg
    session.bear_argument = bear_arg
    session.phase = Phase.DEBATE_COMPLETE
    await session_store.update_session(session)

    await session_store.publish_room_message(
        session_id, "debate-ring", "bull-agent",
        f"🟢 **Bull Case:**\n{bull_arg}"
    )
    await session_store.publish_room_message(
        session_id, "debate-ring", "bear-agent",
        f"🔴 **Bear Case:**\n{bear_arg}"
    )
    await session_store.publish_phase_change(session_id, Phase.DEBATE_COMPLETE.value,
                                             "Both sides have argued. PM is deliberating.")

    await session_store.publish_room_message(
        session_id, "main", "pm-agent",
        "⚔️ Debate complete. Both Bull and Bear have presented. Writing final memo..."
    )

    # ═══════════════════════════════════════════════════════════
    # PHASE 4: Resolution — PM writes final memo
    # ═══════════════════════════════════════════════════════════
    await session_store.publish_room_message(
        session_id, "main", "pm-agent",
        "📝 Synthesizing debate and writing final Investment Memo..."
    )

    # Fetch mock user profile
    raw_profile = await session_store._redis.get("user_profile:demo_user")
    user_profile_data = json.loads(raw_profile) if raw_profile else None

    final_memo = await call_llm(
        system_prompt=pm_system_prompt(),
        user_prompt=pm_final_memo_prompt(ticker, quant_summary, bull_arg, bear_arg, user_profile=user_profile_data),
        provider="aiml",
        temperature=0.5,
        max_tokens=3000,
    )

    session.final_memo = final_memo
    session.phase = Phase.MEMO_DELIVERED
    await session_store.update_session(session)

    await session_store.publish_memo_update(session_id, final_memo)
    await session_store.publish_phase_change(session_id, Phase.MEMO_DELIVERED.value,
                                             "Investment Memo delivered.", is_emergency=is_emergency)

    await session_store.publish_room_message(
        session_id, "main", "pm-agent",
        f"📄 **Investment Memo Delivered.**\n\n{final_memo}"
    )

    # Post to Band
    if pm_client and band_key:
        # Band has message length limits, so truncate if needed
        memo_preview = final_memo[:3000]
        await pm_client.send_as_agent(band_key, "pm-agent", memo_preview)
        await pm_client.close()

    return final_memo
