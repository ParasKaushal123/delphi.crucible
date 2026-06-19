import asyncio
import json
from state.session_store import SessionStore

async def dump():
    store = SessionStore()
    await store.connect()
    keys = await store._redis.keys('imb:session:*')
    
    print(f"Found {len(keys)} keys matching prefix.")
    for k in keys:
        try:
            data = await store._redis.get(k)
            if data:
                s = json.loads(data)
                if isinstance(s, dict) and 'session_id' in s:
                    print(f"Session ID: {s.get('session_id')}, Ticker: {s.get('ticker')}")
        except Exception as e:
            # Probably a list or hash
            pass
            
if __name__ == '__main__':
    asyncio.run(dump())
