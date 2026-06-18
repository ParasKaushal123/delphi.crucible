import asyncio
from band_api.client import get_pm_client
from config import settings
import httpx

async def test():
    client = get_pm_client()
    resp = await client.create_chat_room()
    chat_id = resp.get("data", {}).get("id") or resp.get("id")
    print("CHAT ID:", chat_id)
    
    try:
        msg_resp = await client.send_message(
            chat_id=chat_id,
            content=f"@{settings.QUANT_AGENT_NAME} please analyze AAPL",
            mentions=[{"id": settings.QUANT_AGENT_ID, "handle": settings.QUANT_AGENT_NAME}]
        )
        print("MESSAGE RESPONSE:", msg_resp)
    except httpx.HTTPStatusError as e:
        print("SEND ERROR:", e.response.text)

asyncio.run(test())
