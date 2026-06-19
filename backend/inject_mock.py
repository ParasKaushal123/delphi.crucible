import asyncio
import json
import datetime
from state.user_profile import UserProfile, Position
from redis.asyncio import Redis

MOCK_USER_ID = "demo_user"

async def main():
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    
    # 1 month ago
    past_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    # Inject into user_profile
    data = await redis.get(f"user_profile:{MOCK_USER_ID}")
    if data:
        profile = UserProfile.model_validate_json(data)
    else:
        profile = UserProfile(user_id=MOCK_USER_ID)
        
    profile.portfolio["TSLA"] = Position(
        buy_price=175.0,
        shares=10,
        threshold=""
    )
    
    profile.portfolio["MOCK"] = Position(
        buy_price=100.0,
        shares=10,
        threshold="115.0"
    )
    
    await redis.set(f"user_profile:{MOCK_USER_ID}", profile.model_dump_json())
    
    # Inject history entry
    await redis.lpush(
        f"user_history:{MOCK_USER_ID}", 
        json.dumps({
            "type": "transaction", 
            "action": "BUY", 
            "ticker": "TSLA",
            "shares": 10,
            "price": 175.0,
            "timestamp": past_date.isoformat()
        })
    )
    
    await redis.lpush(
        f"user_history:{MOCK_USER_ID}", 
        json.dumps({
            "type": "transaction", 
            "action": "BUY", 
            "ticker": "MOCK",
            "shares": 10,
            "price": 100.0,
            "timestamp": past_date.isoformat()
        })
    )
    print("Injected TSLA and MOCK stock from 30 days ago.")

if __name__ == "__main__":
    asyncio.run(main())
