"""
Band Agent REST API client — wrapper for room management, messaging, and event handling.
"""

from typing import Optional, List, Dict
from config import settings
from band.client.rest import AsyncRestClient, ChatRoomRequest, ParticipantRequest, ChatMessageRequest, ChatMessageRequestMentionsItem

class BandClient:
    """
    Wraps the AI Band Platform Agent API using the official SDK's AsyncRestClient.
    """

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or settings.BAND_API_KEY
        self._rest = AsyncRestClient(
            base_url="https://app.band.ai",
            api_key=self.access_token
        )

    async def close(self):
        """AsyncRestClient doesn't require explicit close in all versions."""
        pass

    async def create_chat_room(self, task_id: Optional[str] = None) -> dict:
        req = ChatRoomRequest(task_id=task_id) if task_id else ChatRoomRequest()
        resp = await self._rest.agent_api_chats.create_agent_chat(chat=req)
        return {"data": {"id": resp.data.id}}

    async def add_participant(self, chat_id: str, participant_id: str) -> dict:
        resp = await self._rest.agent_api_participants.add_agent_chat_participant(
            chat_id=chat_id,
            participant=ParticipantRequest(participant_id=participant_id, role="member")
        )
        return {"data": {"id": getattr(resp.data, "id", None)}}

    async def send_message(self, chat_id: str, content: str, mentions: Optional[List[Dict]] = None) -> dict:
        mention_items = []
        if mentions:
            mention_items = [
                ChatMessageRequestMentionsItem(id=m["id"], handle=m["handle"])
                for m in mentions
            ]
        
        req = ChatMessageRequest(content=content, mentions=mention_items)
        resp = await self._rest.agent_api_messages.create_agent_chat_message(
            chat_id=chat_id,
            message=req
        )
        return {"data": {"id": getattr(resp.data, "id", None)}}

    async def send_event(self, chat_id: str, content: str, message_type: str = "tool_call", metadata: dict = None) -> dict:
        from band.client.rest import ChatEventRequest
        req = ChatEventRequest(content=content, message_type=message_type, metadata=metadata or {})
        resp = await self._rest.agent_api_events.create_agent_chat_event(
            chat_id=chat_id,
            event=req
        )
        return {"data": {"id": getattr(resp.data, "id", None)}}

# ─── Agent-specific clients ──────────────────────────────────

def get_pm_client() -> BandClient:
    return BandClient(access_token=settings.BAND_PM_BOT_TOKEN)

def get_quant_client() -> BandClient:
    return BandClient(access_token=settings.BAND_QUANT_BOT_TOKEN)

def get_bull_client() -> BandClient:
    return BandClient(access_token=settings.BAND_BULL_BOT_TOKEN)

def get_bear_client() -> BandClient:
    return BandClient(access_token=settings.BAND_BEAR_BOT_TOKEN)
