import json
import asyncio
from band import Agent
from band.core.simple_adapter import SimpleAdapter
from band.core.protocols import AgentToolsProtocol
from band.core.types import PlatformMessage

from state.session_store import SessionStore, Phase
from agents.quant_agent import run_quant_analysis
from agents.bull_agent import run_bull_analysis
from agents.bear_agent import run_bear_analysis
from agents.llm_client import call_llm
from prompts.agent_prompts import pm_system_prompt, pm_final_memo_prompt
from band_api.client import get_pm_client, get_quant_client, get_bull_client, get_bear_client
from config import settings
import time
from datetime import datetime, timezone

processed_msg_ids = set()

def is_message_fresh(msg: PlatformMessage, adapter_name: str) -> bool:
    if not hasattr(msg, "id"): return False
    key = f"{adapter_name}:{msg.id}"
    if key in processed_msg_ids:
        return False
    processed_msg_ids.add(key)
    
    ts = getattr(msg, "created_at", getattr(msg, "timestamp", None))
    if not ts:
        return True
        
    if isinstance(ts, datetime):
        now = datetime.now(timezone.utc) if ts.tzinfo else datetime.utcnow()
        return (now - ts).total_seconds() < 60
        
    if isinstance(ts, (int, float)):
        if ts > 1e11:
            ts = ts / 1000.0
        return (time.time() - ts) < 60
        
    return True


class BaseBenchAdapter(SimpleAdapter[list]):
    def __init__(self, session_store: SessionStore):
        super().__init__(history_converter=None)
        self.store = session_store

    async def get_session(self, room_id: str):
        return await self.store.find_session_by_room(room_id)


class PMAgentAdapter(BaseBenchAdapter):
    async def on_message(self, msg: PlatformMessage, tools: AgentToolsProtocol, history, participants_msg, contacts_msg, *, is_session_bootstrap: bool, room_id: str) -> None:
        print(f"[PM Agent] Received message: {msg.content} (bootstrap={is_session_bootstrap})")
        if not is_message_fresh(msg, "PM"):
            return

        session = await self.get_session(room_id)
        if not session:
            return

        content = msg.content.lower()

        # ─── Handshake / System Online Intercept ───
        if "system online" in content or "acknowledged. standing by" in content:
            agent_type = None
            sender = getattr(msg, "creator_id", getattr(msg, "sender_id", ""))
            
            if sender == settings.QUANT_AGENT_ID or "quant" in content:
                agent_type = "quant"
            elif sender == settings.BULL_AGENT_ID or "bull" in content:
                agent_type = "bull"
            elif sender == settings.BEAR_AGENT_ID or "bear" in content:
                agent_type = "bear"

            if agent_type and agent_type not in session.agents_ready:
                session.agents_ready.append(agent_type)
                await self.store.update_session(session)
                
                # Check if all 3 agents are ready
                if len(session.agents_ready) == 3:
                    session.phase = Phase.DATA_CAVE_OPEN
                    await self.store.update_session(session)
                    
                    if session.ticker == "PDF":
                        await tools.send_message(
                            content=f"@{settings.QUANT_AGENT_NAME} Please pull financial data for $PDF from the provided 10-K text.",
                            mentions=[{"id": settings.QUANT_AGENT_ID, "handle": settings.QUANT_AGENT_NAME}]
                        )
                    else:
                        await tools.send_message(
                            content=f"@{settings.QUANT_AGENT_NAME} Please pull financial data for ${session.ticker}",
                            mentions=[{"id": settings.QUANT_AGENT_ID, "handle": settings.QUANT_AGENT_NAME}]
                        )
            return

        # 1. Start Analysis (Triggered from Frontend via REST)
        if "here is my bull case" in content or "here is my bear case" in content:
            # We are in the Debate Ring, wait for both to finish
            if session.bull_argument and session.bear_argument and session.phase != Phase.MEMO_DELIVERED:
                session.phase = Phase.MEMO_DELIVERED
                await self.store.update_session(session)
                
                await self.store.publish_room_message(session.session_id, "main", "pm-agent", "⚔️ Debate complete. Both Bull and Bear have presented. Writing final memo...")
                
                # Fetch profile
                raw_profile = await self.store._redis.get("user_profile:demo_user")
                user_profile_data = json.loads(raw_profile) if raw_profile else None
                
                try:
                    final_memo = await call_llm(
                        system_prompt=pm_system_prompt(),
                        user_prompt=pm_final_memo_prompt(session.ticker, session.quant_summary, session.bull_argument, session.bear_argument, user_profile=user_profile_data),
                        provider="aiml",
                        temperature=0.5,
                        max_tokens=3000,
                    )
                except Exception as e:
                    print(f"[PM Agent] LLM Error: {e}")
                    final_memo = f"[System]: Acknowledged. Standing by. (Error: {e})"
                
                session.final_memo = final_memo
                await self.store.update_session(session)
                
                await self.store.publish_memo_update(session.session_id, final_memo)
                await self.store.publish_phase_change(session.session_id, Phase.MEMO_DELIVERED.value, "Investment Memo delivered.", is_emergency=session.is_emergency)
                
                await self.store.publish_room_message(session.session_id, "main", "pm-agent", f"📄 **Investment Memo Delivered.**\n\n{final_memo}")
                
                # Post preview to Main Room
                await tools.send_message(f"Final Memo Delivered:\n{final_memo[:1000]}...")


class QuantAgentAdapter(BaseBenchAdapter):
    async def on_message(self, msg: PlatformMessage, tools: AgentToolsProtocol, history, participants_msg, contacts_msg, *, is_session_bootstrap: bool, room_id: str) -> None:
        print(f"[Quant Agent] Received message: {msg.content} (bootstrap={is_session_bootstrap})")
        if not is_message_fresh(msg, "Quant"):
            return

        session = await self.get_session(room_id)
        if not session:
            return

        # ─── Explicit Mention Check ───
        mentions = getattr(msg, "mentions", []) or []
        is_mentioned = any(
            (m.get("id") if isinstance(m, dict) else str(m)) == settings.QUANT_AGENT_ID 
            for m in mentions
        ) or (f"@[[{settings.QUANT_AGENT_ID}]]" in msg.content)

        if not is_mentioned:
            return

        if session.phase == Phase.ROLL_CALL:
            await tools.send_message(
                content=f"@{settings.PM_AGENT_NAME} [System]: Acknowledged. Standing by.",
                mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
            )
            return
            
        if session.phase != Phase.DATA_CAVE_OPEN:
            return

        await self.store.publish_room_message(session.session_id, "data-cave", "quant-agent", f"Fetching financial data for **${session.ticker}**...")

        try:
            quant_result = await run_quant_analysis(
                ticker=session.ticker,
                extracted_text=session.extracted_text,
                company_name=session.company_name
            )
            session.raw_financial_data = quant_result["raw_data"]
            session.quant_summary = quant_result["formatted_report"][:2000] # Simplification
            session.phase = Phase.DATA_CAVE_COMPLETE
            await self.store.update_session(session)

            await self.store.publish_room_message(session.session_id, "data-cave", "quant-agent", f"📊 **Data Extracted.**")
            await self.store.publish_phase_change(session.session_id, Phase.DATA_CAVE_COMPLETE.value, "Data extracted")

            # Create Debate Ring
            quant_client = get_quant_client()
            debate_resp = await quant_client.create_chat_room()
            debate_id = debate_resp.get("data", {}).get("id") or debate_resp.get("id")
            
            session.debate_ring_id = debate_id
            session.phase = Phase.DEBATE_RING_OPEN
            await self.store.update_session(session)
            await self.store.publish_phase_change(session.session_id, Phase.DEBATE_RING_OPEN.value, "Opening Debate Ring")

            # Add Bull, Bear, and PM to the room
            await quant_client.add_participant(debate_id, settings.BULL_AGENT_ID)
            await quant_client.add_participant(debate_id, settings.BEAR_AGENT_ID)
            await quant_client.add_participant(debate_id, settings.PM_AGENT_ID)

            # Mention Bull and Bear
            await quant_client.send_message(
                chat_id=debate_id,
                content=f"@{settings.BULL_AGENT_NAME} @{settings.BEAR_AGENT_NAME} Here is the data for ${session.ticker}:\n{session.quant_summary}",
                mentions=[
                    {"id": settings.BULL_AGENT_ID, "handle": settings.BULL_AGENT_NAME},
                    {"id": settings.BEAR_AGENT_ID, "handle": settings.BEAR_AGENT_NAME}
                ]
            )
            await quant_client.close()
            
            # Send back a response to the PM in the original room so the Band Execution completes
            await tools.send_message(
                content=f"@{settings.PM_AGENT_NAME} Data extraction complete. I have created the Debate Ring and invited the Bull and Bear agents.",
                mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
            )

        except Exception as e:
            print(f"[Quant Agent] Error: {e}")
            await self.store.publish_room_message(session.session_id, "data-cave", "quant-agent", f"Error: {e}")
            await tools.send_message(
                content=f"@{settings.PM_AGENT_NAME} [System]: Acknowledged. Standing by. (Error: {e})",
                mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
            )


class BullAgentAdapter(BaseBenchAdapter):
    async def on_message(self, msg: PlatformMessage, tools: AgentToolsProtocol, history, participants_msg, contacts_msg, *, is_session_bootstrap: bool, room_id: str) -> None:
        print(f"[Bull Agent] Received message: {msg.content} (bootstrap={is_session_bootstrap})")
        if not is_message_fresh(msg, "Bull"):
            return

        session = await self.get_session(room_id)
        if not session:
            return

        # ─── Explicit Mention Check ───
        mentions = getattr(msg, "mentions", []) or []
        is_mentioned = any(
            (m.get("id") if isinstance(m, dict) else str(m)) == settings.BULL_AGENT_ID 
            for m in mentions
        ) or (f"@[[{settings.BULL_AGENT_ID}]]" in msg.content)

        if not is_mentioned:
            return

        if session.phase == Phase.ROLL_CALL:
            await tools.send_message(
                content=f"@{settings.PM_AGENT_NAME} [System]: Acknowledged. Standing by.",
                mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
            )
            return
            
        if session.phase != Phase.DEBATE_RING_OPEN:
            return

        await self.store.publish_room_message(session.session_id, "debate-ring", "bull-agent", "🟢 Analyzing data for buy thesis...")
        
        try:
            bull_arg = await run_bull_analysis(session.ticker, session.quant_summary)
        except Exception as e:
            print(f"[Bull Agent] Error: {e}")
            bull_arg = f"[System]: Acknowledged. Standing by. (Error: {e})"
            
        # Re-fetch session to avoid race condition overwrites
        session = await self.get_session(room_id)
        if not session: return

        session.bull_argument = bull_arg
        await self.store.update_session(session)

        await self.store.publish_room_message(session.session_id, "debate-ring", "bull-agent", f"🟢 **Bull Case:**\n{bull_arg}")
        
        # Send back to PM
        await tools.send_message(
            content=f"@{settings.PM_AGENT_NAME} Here is my bull case:\n{bull_arg}",
            mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
        )


class BearAgentAdapter(BaseBenchAdapter):
    async def on_message(self, msg: PlatformMessage, tools: AgentToolsProtocol, history, participants_msg, contacts_msg, *, is_session_bootstrap: bool, room_id: str) -> None:
        print(f"[Bear Agent] Received message: {msg.content} (bootstrap={is_session_bootstrap})")
        if not is_message_fresh(msg, "Bear"):
            return

        session = await self.get_session(room_id)
        if not session:
            return

        # ─── Explicit Mention Check ───
        mentions = getattr(msg, "mentions", []) or []
        is_mentioned = any(
            (m.get("id") if isinstance(m, dict) else str(m)) == settings.BEAR_AGENT_ID 
            for m in mentions
        ) or (f"@[[{settings.BEAR_AGENT_ID}]]" in msg.content)

        if not is_mentioned:
            return

        if session.phase == Phase.ROLL_CALL:
            await tools.send_message(
                content=f"@{settings.PM_AGENT_NAME} [System]: Acknowledged. Standing by.",
                mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
            )
            return
            
        if session.phase != Phase.DEBATE_RING_OPEN:
            return

        await self.store.publish_room_message(session.session_id, "debate-ring", "bear-agent", "🔴 Analyzing data for sell thesis...")
        
        try:
            bear_arg = await run_bear_analysis(session.ticker, session.quant_summary)
        except Exception as e:
            print(f"[Bear Agent] Error: {e}")
            bear_arg = f"[System]: Acknowledged. Standing by. (Error: {e})"
            
        # Re-fetch session to avoid race condition overwrites
        session = await self.get_session(room_id)
        if not session: return

        session.bear_argument = bear_arg
        await self.store.update_session(session)

        await self.store.publish_room_message(session.session_id, "debate-ring", "bear-agent", f"🔴 **Bear Case:**\n{bear_arg}")
        
        # Send back to PM
        await tools.send_message(
            content=f"@{settings.PM_AGENT_NAME} Here is my bear case:\n{bear_arg}",
            mentions=[{"id": settings.PM_AGENT_ID, "handle": settings.PM_AGENT_NAME}]
        )
