"""
Sessions router — fetch old chat sessions and their messages.
"""

from fastapi import APIRouter, Request, HTTPException
import json

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

@router.get("")
async def get_all_sessions(request: Request):
    """List all analysis sessions."""
    store = request.app.state.session_store
    
    sessions = []
    async for key in store._redis.scan_iter(match=f"{store.PREFIX}*"):
        if not key.endswith(":messages"):
            raw = await store._redis.get(key)
            if raw:
                try:
                    data = json.loads(raw)
                    sessions.append(data)
                except Exception:
                    pass
                
    # Sort by created_at descending
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {"sessions": sessions}

@router.get("/{session_id}/messages")
async def get_session_messages(session_id: str, request: Request):
    """Get all saved chat messages for a specific session."""
    store = request.app.state.session_store
    
    # Check if session exists
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    raw_msgs = await store._redis.lrange(f"{store.PREFIX}{session_id}:messages", 0, -1)
    
    messages = []
    for m in raw_msgs:
        try:
            messages.append(json.loads(m))
        except Exception:
            pass
            
    return {"session": session.to_dict(), "messages": messages}
