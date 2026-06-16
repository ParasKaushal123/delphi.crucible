"""
Server-Sent Events (SSE) endpoint — streams real-time events to the frontend.
Subscribes to Redis pub/sub channel for session events.
"""

import asyncio
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis

from state.session_store import SessionStore
from config import settings

router = APIRouter()


async def event_generator(request: Request):
    """
    Generator that yields SSE events from the Redis pub/sub channel.
    Each event is a JSON object with: session_id, type, data, timestamp.
    """
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(SessionStore.SSE_CHANNEL)

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message["type"] == "message":
                yield {
                    "event": "update",
                    "data": message["data"],
                }

            await asyncio.sleep(0.1)
    finally:
        await pubsub.unsubscribe(SessionStore.SSE_CHANNEL)
        await redis_client.close()


@router.get("/api/sse/events")
async def sse_events(request: Request):
    """
    SSE endpoint that streams all session events to the frontend.
    The frontend subscribes to this and routes events to the correct panel.
    """
    return EventSourceResponse(event_generator(request))
