"""
Investment Memo Bench — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from state.session_store import SessionStore
from state.user_profile import UserProfile, Position
from routers import webhook, health, tickers, sse, upload, profile, portfolio, history, sessions
from band import Agent
from agents.adapters import PMAgentAdapter, QuantAgentAdapter, BullAgentAdapter, BearAgentAdapter
import asyncio

MOCK_USER_ID = "demo_user"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: connect Redis, etc."""
    # Startup
    store = SessionStore()
    await store.connect()
    app.state.session_store = store
    print(f"[OK] Redis connected at {settings.REDIS_URL}")
    
    # Seed mock user if not exists
    existing = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    if not existing:
        mock_profile = UserProfile(
            user_id=MOCK_USER_ID,
            income=100000.0,
            risk_tolerance="aggressive",
            experience="advanced",
            portfolio={
                "NVDA": Position(buy_price=120.50, shares=150),
                "MOCK": Position(buy_price=100.00, shares=100, threshold="10.00")
            }
        )
        await store._redis.set(f"user_profile:{MOCK_USER_ID}", mock_profile.model_dump_json())
        
        # Seed initial history so the portfolio accurately computes profit/shows bought flags
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        await store._redis.lpush(f"user_history:{MOCK_USER_ID}", json.dumps({
            "type": "transaction", "action": "BUY", "ticker": "NVDA", "shares": 150, "price": 120.50, "timestamp": timestamp
        }))
        await store._redis.lpush(f"user_history:{MOCK_USER_ID}", json.dumps({
            "type": "transaction", "action": "BUY", "ticker": "MOCK", "shares": 100, "price": 100.00, "timestamp": timestamp
        }))
        
        print(f"[OK] Seeded mock user profile: {MOCK_USER_ID}")
    else:
        print(f"[OK] Loaded existing user profile: {MOCK_USER_ID}")
        
    # Seed example sessions
    import os
    if os.path.exists("seed_data.json"):
        import json
        with open("seed_data.json", "r") as f:
            seed_data = json.load(f)
            for sid, data in seed_data.items():
                existing_session = await store._redis.get(f"{store.PREFIX}{sid}")
                if not existing_session:
                    await store._redis.set(f"{store.PREFIX}{sid}", json.dumps(data["session"]))
                    for m in reversed(data["messages"]):
                        await store._redis.lpush(f"{store.PREFIX}{sid}:messages", json.dumps(m))
                    print(f"[OK] Seeded example session: {sid}")
    
    # Start Band Agents
    pm_agent = Agent.create(adapter=PMAgentAdapter(store), agent_id=settings.PM_AGENT_ID, api_key=settings.BAND_PM_BOT_TOKEN)
    quant_agent = Agent.create(adapter=QuantAgentAdapter(store), agent_id=settings.QUANT_AGENT_ID, api_key=settings.BAND_QUANT_BOT_TOKEN)
    bull_agent = Agent.create(adapter=BullAgentAdapter(store), agent_id=settings.BULL_AGENT_ID, api_key=settings.BAND_BULL_BOT_TOKEN)
    bear_agent = Agent.create(adapter=BearAgentAdapter(store), agent_id=settings.BEAR_AGENT_ID, api_key=settings.BAND_BEAR_BOT_TOKEN)

    async def threshold_monitor(session_store):
        import httpx
        from state.user_profile import UserProfile
        from state.session_store import Phase
        import uuid
        
        while True:
            try:
                await asyncio.sleep(30)
                data = await session_store._redis.get(f"user_profile:{MOCK_USER_ID}")
                if not data: continue
                
                profile = UserProfile.model_validate_json(data)
                
                tickers_to_check = [t for t, p in profile.portfolio.items() if p.shares > 0 and p.threshold]
                if not tickers_to_check: continue
                
                async with httpx.AsyncClient() as client:
                    for t in tickers_to_check:
                        if t == "MOCK":
                            import time
                            cycle = 420  # 7 minutes
                            elapsed = time.time() % cycle
                            if elapsed < 210:
                                current_price = 70.0 + (50.0 * (elapsed / 210.0))
                            else:
                                current_price = 120.0 - (50.0 * ((elapsed - 210) / 210.0))
                            current_price = round(current_price, 2)
                            print(f"[DEBUG] MOCK Price: {current_price:.2f}")
                        else:
                            res = await client.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{t}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10.0)
                            if res.status_code == 200:
                                chart = res.json()
                                current_price = chart["chart"]["result"][0]["meta"]["regularMarketPrice"]
                            else:
                                continue
                                
                        # Check if there is already an active session
                        active = await session_store._redis.get("current_session_id")
                        if active: continue
                                
                        if t in profile.portfolio:
                            pos = profile.portfolio[t]
                            threshold_str = pos.threshold
                            buy_price = pos.buy_price
                            shares = pos.shares
                        elif t == "MOCK":
                            # Fallback if MOCK was accidentally removed from user's portfolio
                            threshold_str = "10.00"
                            buy_price = 100.00
                            shares = 100
                        else:
                            continue
                        
                        threshold_str = threshold_str.replace("$", "").replace("±", "").replace("+", "").replace("-", "").strip()
                        try:
                            deviation = float(threshold_str)
                        except:
                            print(f"[DEBUG] Failed to parse threshold for {t}: {threshold_str}")
                            continue
                                
                        trigger = False
                        upper_threshold = buy_price + deviation
                        lower_threshold = buy_price - deviation
                        
                        if current_price >= upper_threshold:
                            trigger = True
                        elif current_price <= lower_threshold:
                            trigger = True
                            
                        if trigger:
                            import datetime
                            from band_api.client import get_pm_client
                            from config import settings
                            from state.session_store import Phase
                            
                            print(f"[ALERT] Threshold crossed for {t}! Triggering emergency chat.")
                            new_session_id = str(uuid.uuid4())
                            session = await session_store.create_session(new_session_id, t)
                            
                            pm_client = get_pm_client()
                            try:
                                chat_resp = await pm_client.create_chat_room()
                                chat_id = chat_resp.get("data", {}).get("id") or chat_resp.get("id")
                                session.main_room_id = chat_id
                                session.phase = Phase.ROLL_CALL
                                session.is_emergency = True
                                await session_store.update_session(session)
                                
                                await session_store._redis.set("current_session_id", new_session_id)
                                
                                # Add agents
                                await pm_client.add_participant(chat_id, settings.QUANT_AGENT_ID)
                                await pm_client.add_participant(chat_id, settings.BULL_AGENT_ID)
                                await pm_client.add_participant(chat_id, settings.BEAR_AGENT_ID)
                                
                                await asyncio.sleep(2)
                                
                                msg_content = f"[EMERGENCY ALERT] The threshold deviation of ±${deviation} for {t} has been crossed. The current price is ${current_price}. Please analyze immediately and recommend whether to SELL or HOLD."
                                
                                await pm_client.send_message(
                                    chat_id=chat_id,
                                    content=f"@{settings.QUANT_AGENT_NAME} @{settings.BULL_AGENT_NAME} @{settings.BEAR_AGENT_NAME} {msg_content}",
                                    mentions=[
                                        {"id": settings.QUANT_AGENT_ID, "handle": settings.QUANT_AGENT_NAME},
                                        {"id": settings.BULL_AGENT_ID, "handle": settings.BULL_AGENT_NAME},
                                        {"id": settings.BEAR_AGENT_ID, "handle": settings.BEAR_AGENT_NAME},
                                    ]
                                )
                                
                                # Also push a system message for UI
                                msg = {
                                    "id": str(uuid.uuid4()),
                                    "role": "SYSTEM",
                                    "content": msg_content,
                                    "timestamp": datetime.datetime.now().isoformat()
                                }
                                await session_store.add_message(new_session_id, msg)
                                
                                import json
                                await session_store._redis.lpush(
                                    f"user_history:{MOCK_USER_ID}", 
                                    json.dumps({
                                        "type": "transaction", 
                                        "action": "ALERT", 
                                        "ticker": t,
                                        "shares": shares,
                                        "price": current_price,
                                        "timestamp": datetime.datetime.now().isoformat()
                                    })
                                )
                            finally:
                                await pm_client.close()
                                
                            break # Only trigger one at a time
            except Exception as e:
                print(f"[Monitor Error] {e}")

    async def safe_run_agent(agent_obj, name):
        try:
            await agent_obj.run()
        except Exception as e:
            print(f"[FATAL] {name} Agent WebSocket crashed: {e}")

    app.state.agent_tasks = [
        asyncio.create_task(safe_run_agent(pm_agent, "PM")),
        asyncio.create_task(safe_run_agent(quant_agent, "Quant")),
        asyncio.create_task(safe_run_agent(bull_agent, "Bull")),
        asyncio.create_task(safe_run_agent(bear_agent, "Bear")),
        asyncio.create_task(threshold_monitor(store))
    ]
    print("[OK] Band SDK Agents started (WebSocket connections established)")

    yield

    # Shutdown
    print("[OFF] Cancelling Agent tasks...")
    for task in app.state.agent_tasks:
        task.cancel()

    await store.disconnect()
    print("[OFF] Redis disconnected. Shutting down.")


app = FastAPI(
    title="The Delphi Crucible",
    description="Multi-agent investment analysis powered by Band.ai",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://delphicrucible-n8qs2svrv-klein-moretti.vercel.app"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(webhook.router, tags=["Band Webhook"])
app.include_router(health.router, tags=["Health"])
app.include_router(tickers.router, tags=["Tickers"])
app.include_router(sse.router, tags=["SSE"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(profile.router, tags=["Profile"])
app.include_router(portfolio.router, tags=["Portfolio"])
app.include_router(history.router, tags=["History"])
app.include_router(sessions.router, tags=["Sessions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
