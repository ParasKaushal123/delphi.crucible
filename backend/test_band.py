import asyncio
from band_api.client import get_pm_client

async def test():
    client = get_pm_client()
    resp = await client.create_chat_room()
    print("RESPONSE:", resp)
    chat_id = resp.get("data", {}).get("id") or resp.get("id")
    print("EXTRACTED CHAT ID:", chat_id)

asyncio.run(test())
