from fastapi import APIRouter, Request
import json

router = APIRouter(prefix="/api/history", tags=["History"])
MOCK_USER_ID = "demo_user"

@router.get("")
async def get_history(request: Request):
    store = request.app.state.session_store
    
    # Fetch from list
    raw_history = await store._redis.lrange(f"user_history:{MOCK_USER_ID}", 0, -1)
    
    history_items = []
    for item in raw_history:
        try:
            history_items.append(json.loads(item))
        except:
            pass
            
    return {"history": history_items}

@router.post("/clear")
async def clear_history(request: Request):
    store = request.app.state.session_store
    await store._redis.delete(f"user_history:{MOCK_USER_ID}")
    return {"status": "success"}
