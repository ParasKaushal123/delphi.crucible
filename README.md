# The Delphi Crucible

**An Agentic Investment Accountant Team**

The Delphi Crucible is a multi-agent financial simulation application that leverages the Band Protocol SDK to simulate an entire investment committee debating the viability of a given stock ticker or 10-K financial document.

The project spins up a suite of specialized AI Agents who analyze real-time financial data, debate the fundamentals, and arrive at a synchronized portfolio decision. It features a gorgeous, immersive Next.js frontend, and a robust FastAPI backend with live Server-Sent Events (SSE).

## 🚀 The Multi-Agent Team

1. **Quant Agent:** Crunches the hard numbers, evaluating P/E ratios, revenue growth, cash flow, margins, and historical trends. Provides the mathematical bedrock for the debate.
2. **Bull Agent:** Takes the optimistic stance. Focuses on growth catalysts, market expansion, analyst upgrades, and bullish technical indicators.
3. **Bear Agent:** Takes the pessimistic stance. Identifies macroeconomic risks, fundamental weaknesses, debt liabilities, and overvaluation concerns.
4. **Portfolio Manager (PM) Agent:** The executive decision-maker. Listens to the Quant, Bull, and Bear, synthesizes their arguments against the user's risk profile, and delivers a final executive memo with a strict `[DECISION: INVEST | AMOUNT: $... | THRESHOLD: ...]` outcome.

## 🛠️ Technology Stack

- **Frontend:** Next.js 14, React, TailwindCSS, Recharts.
- **Backend:** Python FastAPI, Uvicorn, HTTPX.
- **AI Agent Orchestration:** Band SDK (`band-sdk`).
- **Database / State:** Redis (used for session persistence, portfolio tracking, and real-time messaging between agents).
- **Live Streaming:** Server-Sent Events (SSE) from FastAPI to React.

## ⚙️ Prerequisites

- Node.js (v18+)
- Python (3.9+)
- Redis Server (must be running on `localhost:6379`)

## 🔑 Setup & Environment

1. Clone the repository.
2. Make sure you have a `.env` file in the `backend/` directory (or the root if specified by your setup) containing your API keys for the Band Agents.
   
Example `.env` (Backend):
```env
REDIS_URL="redis://localhost:6379"

# Agent IDs
QUANT_AGENT_ID="your_quant_id"
BULL_AGENT_ID="your_bull_id"
BEAR_AGENT_ID="your_bear_id"
PM_AGENT_ID="your_pm_id"

# API Keys
BAND_QUANT_BOT_TOKEN="your_quant_token"
BAND_BULL_BOT_TOKEN="your_bull_token"
BAND_BEAR_BOT_TOKEN="your_bear_token"
BAND_PM_BOT_TOKEN="your_pm_token"
```

## 🚀 How to Run

### 1. Start Redis
Ensure your Redis instance is running. You can run it via Docker or natively:
```bash
docker-compose up -d
# or natively start your local redis server
```

### 2. Start the Backend
Navigate to the `backend/` directory, install the dependencies, and start the FastAPI server:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
The backend will run on `http://localhost:8000`.

### 3. Start the Frontend
Navigate to the `frontend/` directory, install the dependencies, and start the Next.js app:
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on `http://localhost:3000`.

## 📈 Features

- **Live Multi-Agent Debate:** Watch in real-time as agents argue over the stock.
- **PDF 10-K Ingestion:** Upload any company's 10-K PDF and the agents will ingest and extract its financial context.
- **Dynamic Portfolio Tracker:** Keep track of your investments, see live-ticking total profit, and monitor algorithmic "Threshold Deviations".
- **Real-Time Data Extraction:** Uses Yahoo Finance integrations to automatically pull real-time fundamentals.

## ⚖️ License
MIT License
