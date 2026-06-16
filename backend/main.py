"""
Investment Memo Bench — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from state.session_store import SessionStore
from routers import webhook, health, tickers, sse, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: connect Redis, etc."""
    # Startup
    store = SessionStore()
    await store.connect()
    app.state.session_store = store
    print(f"[OK] Redis connected at {settings.REDIS_URL}")
    print(f"[OK] The Delphi Crucible backend running on {settings.HOST}:{settings.PORT}")
    yield
    # Shutdown
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
