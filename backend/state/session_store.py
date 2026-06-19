"""
Redis-backed session store for tracking multi-room workflow state.
Each session = one ticker analysis request flowing through the pipeline.
"""

import json
import asyncio
from typing import Optional
from datetime import datetime
from enum import Enum

import redis.asyncio as aioredis

from config import settings


class Phase(str, Enum):
    IDLE = "IDLE"
    ROLL_CALL = "ROLL_CALL"
    DATA_CAVE_OPEN = "DATA_CAVE_OPEN"
    DATA_CAVE_COMPLETE = "DATA_CAVE_COMPLETE"
    DEBATE_RING_OPEN = "DEBATE_RING_OPEN"
    DEBATE_COMPLETE = "DEBATE_COMPLETE"
    MEMO_DELIVERED = "MEMO_DELIVERED"
    ERROR = "ERROR"


class SessionState:
    """Represents a single analysis workflow session."""

    def __init__(
        self,
        session_id: str,
        ticker: str,
        phase: Phase = Phase.IDLE,
        main_room_id: str = "",
        data_cave_id: str = "",
        debate_ring_id: str = "",
        raw_financial_data: str = "",
        quant_summary: str = "",
        bull_argument: str = "",
        bear_argument: str = "",
        final_memo: str = "",
        created_at: str = "",
        updated_at: str = "",
        error: str = "",
        is_emergency: bool = False,
        extracted_text: str = "",
        company_name: str = "",
        agents_ready: list = None,
    ):
        self.session_id = session_id
        self.ticker = ticker
        self.phase = phase
        self.main_room_id = main_room_id
        self.data_cave_id = data_cave_id
        self.debate_ring_id = debate_ring_id
        self.raw_financial_data = raw_financial_data
        self.quant_summary = quant_summary
        self.bull_argument = bull_argument
        self.bear_argument = bear_argument
        self.final_memo = final_memo
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()
        self.error = error
        self.is_emergency = is_emergency
        self.extracted_text = extracted_text
        self.company_name = company_name
        self.agents_ready = agents_ready or []

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "ticker": self.ticker,
            "phase": self.phase.value if isinstance(self.phase, Phase) else self.phase,
            "main_room_id": self.main_room_id,
            "data_cave_id": self.data_cave_id,
            "debate_ring_id": self.debate_ring_id,
            "raw_financial_data": self.raw_financial_data,
            "quant_summary": self.quant_summary,
            "bull_argument": self.bull_argument,
            "bear_argument": self.bear_argument,
            "final_memo": self.final_memo,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "is_emergency": self.is_emergency,
            "extracted_text": self.extracted_text,
            "company_name": self.company_name,
            "agents_ready": self.agents_ready,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        data["phase"] = Phase(data.get("phase", "IDLE"))
        return cls(**data)


class SessionStore:
    """Async Redis-backed store for session state."""

    PREFIX = "imb:session:"
    SSE_CHANNEL = "imb:events"

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        # Test the connection
        await self._redis.ping()

    async def disconnect(self):
        if self._redis:
            await self._redis.close()

    def _key(self, session_id: str) -> str:
        return f"{self.PREFIX}{session_id}"

    async def create_session(self, session_id: str, ticker: str, main_room_id: str = "") -> SessionState:
        session = SessionState(
            session_id=session_id,
            ticker=ticker,
            main_room_id=main_room_id,
        )
        await self._redis.set(
            self._key(session_id),
            json.dumps(session.to_dict()),
        )
        await self._publish_event(session_id, "session_created", {
            "ticker": ticker,
            "phase": Phase.IDLE.value,
        })
        return session

    async def get_session(self, session_id: str) -> Optional[SessionState]:
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            return None
        return SessionState.from_dict(json.loads(raw))

    async def update_session(self, session: SessionState) -> SessionState:
        session.updated_at = datetime.utcnow().isoformat()
        await self._redis.set(
            self._key(session.session_id),
            json.dumps(session.to_dict()),
        )
        await self._publish_event(session.session_id, "session_updated", {
            "phase": session.phase.value if isinstance(session.phase, Phase) else session.phase,
            "ticker": session.ticker,
        })
        return session

    async def find_session_by_room(self, room_id: str) -> Optional[SessionState]:
        """Find a session that contains the given room_id (main, data_cave, or debate_ring)."""
        async for key in self._redis.scan_iter(match=f"{self.PREFIX}*"):
            if key.endswith(":messages"):
                continue
            raw = await self._redis.get(key)
            if raw:
                data = json.loads(raw)
                if room_id in (data.get("main_room_id"), data.get("data_cave_id"), data.get("debate_ring_id")):
                    return SessionState.from_dict(data)
        return None

    async def get_active_session(self) -> Optional[SessionState]:
        """Get the most recent non-delivered session (for the frontend)."""
        latest = None
        async for key in self._redis.scan_iter(match=f"{self.PREFIX}*"):
            if key.endswith(":messages"):
                continue
            raw = await self._redis.get(key)
            if raw:
                data = json.loads(raw)
                session = SessionState.from_dict(data)
                if latest is None or session.created_at > latest.created_at:
                    latest = session
        return latest

    # ─── SSE Event Publishing ─────────────────────────────

    async def _publish_event(self, session_id: str, event_type: str, data: dict):
        """Publish an event to the SSE Redis channel for the frontend."""
        event = json.dumps({
            "session_id": session_id,
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        await self._redis.publish(self.SSE_CHANNEL, event)

    async def publish_room_message(self, session_id: str, room_name: str, agent: str, content: str):
        """Publish a chat message event for the frontend room panels, and save it for history."""
        msg_obj = {
            "room": room_name,
            "agent": agent,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to Redis list
        await self._redis.rpush(f"{self.PREFIX}{session_id}:messages", json.dumps(msg_obj))
        
        await self._publish_event(session_id, "room_message", {
            "room": room_name,
            "agent": agent,
            "content": content,
        })

    async def publish_memo_update(self, session_id: str, memo_content: str):
        """Publish a memo update event for the frontend memo panel."""
        await self._publish_event(session_id, "memo_update", {
            "memo": memo_content,
        })

    async def publish_phase_change(self, session_id: str, phase: str, detail: str = "", is_emergency: bool = False):
        """Publish phase change event for the frontend status indicators."""
        await self._publish_event(session_id, "phase_change", {
            "phase": phase,
            "detail": detail,
            "is_emergency": is_emergency,
        })
