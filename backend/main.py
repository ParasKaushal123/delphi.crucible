"""
Investment Memo Bench — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from state.session_store import SessionStore
from state.user_profile import UserProfile, Position
from routers import webhook, health, tickers, sse, upload
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
    
    # Seed mock user
    mock_profile = UserProfile(
        user_id=MOCK_USER_ID,
        capital=100000.0,
        risk_tolerance="aggressive",
        portfolio={
            "NVDA": Position(buy_price=120.50, shares=150)
        }
    )
    await store._redis.set(f"user_profile:{MOCK_USER_ID}", mock_profile.model_dump_json())
    print(f"[OK] Seeded mock user profile: {MOCK_USER_ID}")
    
    # Start Band Agents
    pm_agent = Agent.create(adapter=PMAgentAdapter(store), agent_id=settings.PM_AGENT_ID, api_key=settings.BAND_PM_BOT_TOKEN)
    quant_agent = Agent.create(adapter=QuantAgentAdapter(store), agent_id=settings.QUANT_AGENT_ID, api_key=settings.BAND_QUANT_BOT_TOKEN)
    bull_agent = Agent.create(adapter=BullAgentAdapter(store), agent_id=settings.BULL_AGENT_ID, api_key=settings.BAND_BULL_BOT_TOKEN)
    bear_agent = Agent.create(adapter=BearAgentAdapter(store), agent_id=settings.BEAR_AGENT_ID, api_key=settings.BAND_BEAR_BOT_TOKEN)

    app.state.agent_tasks = [
        asyncio.create_task(pm_agent.run()),
        asyncio.create_task(quant_agent.run()),
        asyncio.create_task(bull_agent.run()),
        asyncio.create_task(bear_agent.run())
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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
