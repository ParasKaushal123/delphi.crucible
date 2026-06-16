# The Delphi Crucible — Handoff Document

> **Last Updated:** June 16, 2026
> **Status:** MVP functional — both Ticker mode and PDF upload working
> **Stack:** FastAPI (Python) + Next.js 16 (TypeScript) + Redis + Band.ai

---

## What This Project Does

**The Delphi Crucible** is a multi-agent investment analysis tool built for the LabLab hackathon. It uses AI agents that collaborate in "rooms" to analyze stocks or 10-K filings and produce a professional investment memo.

### The Pipeline (4 Phases)

```
User Input (ticker or PDF)
    │
    ▼
┌─────────────────────────────────────────────┐
│  PHASE 1: Session Created                   │
│  PM Agent receives the request              │
└────────────────┬────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────┐
│  PHASE 2: Data Cave                         │
│  Quant Agent fetches financial data:        │
│    • Ticker mode → Yahoo Finance API        │
│    • PDF mode → pdfplumber text extraction   │
│  PM summarizes into 5-bullet summary        │
└────────────────┬────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────┐
│  PHASE 3: Debate Ring                       │
│  Bull + Bear agents run IN PARALLEL:        │
│    • Bull: builds best buy case             │
│    • Bear: builds best sell/avoid case       │
│  Both cite data from the quant summary      │
└────────────────┬────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────┐
│  PHASE 4: Memo Delivered                    │
│  PM synthesizes debate into final memo:     │
│    • Recommendation (STRONG BUY → STRONG SELL) │
│    • Bull/Bear cases + PM Dissent section   │
│    • Key metrics table + price target       │
└─────────────────────────────────────────────┘
```

### Two Input Modes

1. **Ticker Mode** — Type a stock ticker (e.g. AAPL), data is fetched from Yahoo Finance
2. **PDF Mode** — Upload a 10-K annual report PDF, text is extracted and analyzed

---

## Project Structure

```
the-delphi-crucible/
├── docker-compose.yml          # Redis container (required)
│
├── backend/                    # FastAPI (Python 3.11+)
│   ├── main.py                 # App entry point, lifespan, CORS, router mounts
│   ├── config.py               # Settings class, loads from .env
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # YOUR API keys (DO NOT commit)
│   ├── .env.example            # Template for .env
│   │
│   ├── agents/                 # AI agent logic
│   │   ├── llm_client.py       # Unified LLM caller (OpenAI-compatible API)
│   │   ├── pm_agent.py         # Pipeline orchestrator (run_full_pipeline)
│   │   ├── quant_agent.py      # Data fetcher (yfinance or PDF mode)
│   │   ├── bull_agent.py       # Bullish analyst
│   │   └── bear_agent.py       # Bearish analyst
│   │
│   ├── band/                   # Band.ai REST API client
│   │   └── client.py           # BandClient wrapper + agent factory functions
│   │
│   ├── prompts/                # All LLM prompt templates
│   │   └── agent_prompts.py    # System + user prompts for all 4 agents
│   │
│   ├── routers/                # FastAPI route handlers
│   │   ├── webhook.py          # POST /webhook/band + POST /api/analyze
│   │   ├── upload.py           # POST /api/analyze/upload (PDF mode)
│   │   ├── sse.py              # GET /api/sse/events (real-time streaming)
│   │   ├── tickers.py          # GET /api/tickers/search (autocomplete)
│   │   └── health.py           # GET /api/health
│   │
│   ├── state/                  # Session management
│   │   └── session_store.py    # Redis-backed store + SSE event publishing
│   │
│   ├── tools/                  # Data extraction tools
│   │   ├── pdf_tool.py         # pdfplumber PDF text extractor (async)
│   │   └── yfinance_tool.py    # Yahoo Finance data fetcher
│   │
│   └── data/
│       └── tickers.json        # Pre-loaded ticker list for autocomplete
│
└── frontend/                   # Next.js 16 (TypeScript)
    ├── .env.local              # NEXT_PUBLIC_API_URL=http://localhost:8000
    ├── package.json            # Dependencies (react, next, react-markdown)
    │
    └── app/
        ├── page.tsx            # Main page — state management + layout
        ├── layout.tsx          # Root layout
        ├── globals.css         # All styles (single CSS file)
        │
        ├── components/
        │   ├── TickerSearch.tsx # Autocomplete ticker search bar
        │   ├── UploadZone.tsx  # PDF drag-and-drop upload
        │   ├── RoomPanel.tsx   # Generic chat room component
        │   ├── DebateRing.tsx  # Split Bull/Bear debate view
        │   └── MemoPanel.tsx   # Final memo renderer (react-markdown)
        │
        └── hooks/
            └── useSSE.ts       # SSE client hook (auto-reconnect)
```

---

## How It Works (Technical)

### Real-Time Communication

```
Backend (FastAPI)                    Frontend (Next.js)
     │                                     │
     │  Redis Pub/Sub                      │
     │  channel: "imb:events"              │
     │                                     │
     ├──publish_room_message()──→ Redis ──→ SSE ──→ useSSE hook
     ├──publish_phase_change()──→ Redis ──→ SSE ──→ setPhase()
     └──publish_memo_update()───→ Redis ──→ SSE ──→ setMemo()
```

- Backend agents publish events to Redis pub/sub channel `imb:events`
- The SSE endpoint (`/api/sse/events`) subscribes to Redis and streams events to the browser
- Frontend `useSSE` hook listens and routes events to the correct room panel

### LLM Providers

| Agent | Provider | Model | Purpose |
|-------|----------|-------|---------|
| Quant | Featherless AI | Qwen/Qwen3-32B | Data formatting (cheaper, open-source) |
| PM | AI/ML API | gpt-4o | Summarization + final memo |
| Bull | AI/ML API | gpt-4o | Bull case argumentation |
| Bear | AI/ML API | gpt-4o | Bear case argumentation |

Both providers use **OpenAI-compatible** `/chat/completions` endpoints, so switching models is trivial — just change the env vars.

### Session State (Redis)

Each analysis creates a `SessionState` object stored in Redis with key `imb:session:{id}`:
- Tracks current phase, raw data, summaries, arguments, and final memo
- Phase enum: `IDLE → DATA_CAVE_OPEN → DATA_CAVE_COMPLETE → DEBATE_RING_OPEN → DEBATE_COMPLETE → MEMO_DELIVERED`

---

## Getting Started (Setup)

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker** (for Redis)
- API keys for [AI/ML API](https://aimlapi.com) and [Featherless](https://featherless.ai)
- (Optional) [Band.ai](https://developers.band.us) bot tokens for chat integration

### 1. Start Redis

```bash
docker-compose up -d
```

### 2. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys (see .env.example for guidance)

pip install -r requirements.txt
# Also install pdfplumber for PDF mode:
pip install pdfplumber

python main.py
# → Runs on http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# → Runs on http://localhost:3000
```

### 4. Open the App

Go to `http://localhost:3000` — you should see:
- Header with "IMB" logo, phase indicator, and SSE connection status
- Ticker/PDF mode toggle
- 3-column War Room (Main Room, Data Cave, Debate Ring)
- Memo panel appears at the bottom when analysis completes

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Start ticker analysis `{ "ticker": "AAPL" }` |
| `POST` | `/api/analyze/upload` | Upload 10-K PDF (multipart form) |
| `GET`  | `/api/sse/events` | SSE stream of all session events |
| `GET`  | `/api/tickers/search?q=app&limit=8` | Ticker autocomplete search |
| `GET`  | `/api/session` | Get active session state |
| `GET`  | `/api/session/{id}` | Get specific session |
| `GET`  | `/api/health` | Health check |
| `POST` | `/webhook/band` | Band.ai incoming webhook |

---

## Known Issues & Gotchas

1. **Gated Models on Featherless:** Llama models require HuggingFace OAuth. Use ungated models like `Qwen/Qwen3-32B` or connect HuggingFace at the Featherless model page.

2. **PDF Text Extraction:** Uses `pdfplumber` — works well for text-based PDFs but fails on scanned image PDFs. Smart page sampling prioritizes financial keywords for large docs (130+ pages).

3. **ASGI callable returned without completing response:** This warning appears in logs when the server reloads while an SSE connection is open. It's harmless — the frontend auto-reconnects.

4. **dotenv Caching:** If you edit `.env`, make sure to **save the file** and restart the backend. The `python-dotenv` library reads the file at import time, not on every request.

5. **Background Task Lifecycle:** `asyncio.create_task()` is used in the upload route. If the server restarts mid-analysis, the task is lost. Consider moving to a task queue (Celery/ARQ) for production.

---

## What Needs Work (Feature Ideas)

### Frontend Improvements 🎨
- [ ] **Better visual design** — the current CSS is functional but basic. Needs glassmorphism, gradients, animations, dark mode polish
- [ ] **Loading skeleton states** — show skeleton UI while agents are working
- [ ] **Typing indicator** — animate "agent is typing..." in room panels
- [ ] **Memo export** — add "Download as PDF" or "Copy to clipboard" buttons
- [ ] **History page** — show past analysis sessions from Redis
- [ ] **Mobile responsive** — currently desktop-only layout
- [ ] **Agent avatars** — use actual avatar images instead of emoji
- [ ] **Progress bar** — visual pipeline progress (Data → Debate → Memo)
- [ ] **Error handling UI** — show inline errors with retry buttons
- [ ] **Comparison mode** — analyze two tickers side-by-side

### Backend Improvements 🔧
- [ ] **Scoring/Benchmarking** — compare AI memo quality against human analyst memos
- [ ] **Confidence calibration** — track prediction accuracy over time
- [ ] **Multi-round debate** — let Bull and Bear respond to each other (2-3 rounds)
- [ ] **Web search agent** — add a 5th agent that searches for recent news/filings
- [ ] **RAG pipeline** — chunk PDFs and use vector search for better context retrieval
- [ ] **Rate limiting** — protect API endpoints from abuse
- [ ] **Authentication** — add user accounts
- [ ] **WebSocket upgrade** — replace SSE with WebSocket for bidirectional communication
- [ ] **Caching layer** — cache yfinance data to avoid repeated API calls

### Band.ai Integration 🤖
- [ ] **Full Band integration** — all 4 agents post to actual Band rooms
- [ ] **Webhook processing** — parse @mentions and auto-trigger analysis from Band chat
- [ ] **Room creation** — dynamically create Data Cave and Debate Ring rooms in Band

---

## Environment Variables Quick Reference

| Variable | Required | Where to Get It |
|----------|----------|-----------------|
| `AIML_API_KEY` | ✅ Yes | [aimlapi.com](https://aimlapi.com) |
| `FEATHERLESS_API_KEY` | ✅ Yes | [featherless.ai](https://featherless.ai) |
| `REDIS_URL` | ✅ Yes | `docker-compose up` gives you `redis://localhost:6379/0` |
| `BAND_API_KEY` | ❌ Optional | [developers.band.us](https://developers.band.us) |
| `BAND_*_BOT_TOKEN` | ❌ Optional | Create bots in Band developer portal |
| `WEBHOOK_BASE_URL` | ❌ Optional | Your ngrok/tunnel URL for Band webhooks |

---

## Key Files to Read First

If you're new to the codebase, read these files in this order:

1. **`backend/agents/pm_agent.py`** — the main pipeline orchestrator. This is the "brain" of the app.
2. **`backend/prompts/agent_prompts.py`** — all LLM prompts. Editing these changes agent behavior.
3. **`backend/state/session_store.py`** — how state is tracked and events are published.
4. **`frontend/app/page.tsx`** — main frontend page with all state management.
5. **`frontend/app/globals.css`** — all styles in one file.

---

*The Delphi Crucible — Built for the LabLab Hackathon · June 2026*
