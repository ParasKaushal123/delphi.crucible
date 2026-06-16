# 🏛️ The Delphi Crucible

> Multi-agent investment analysis — AI agents debate so you don't have to.

**The Delphi Crucible** pits AI analysts against each other to produce rigorous investment memos. A Quant crunches the numbers, a Bull makes the buy case, a Bear tears it apart, and a Portfolio Manager writes the final verdict.

## How It Works

```
📈 Ticker or 📄 10-K PDF
        │
        ▼
  ⚗️ Data Cave ──→ Quant Agent extracts financials
        │
        ▼
  ⚔️ Debate Ring ──→ Bull + Bear argue in parallel
        │
        ▼
  📄 Investment Memo ──→ PM synthesizes the final call
```

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (Python) |
| Frontend | Next.js 16 (TypeScript) |
| State | Redis (pub/sub + session store) |
| LLMs | AI/ML API (gpt-4o) + Featherless (Qwen3-32B) |
| Chat | Band.ai integration |
| Real-time | Server-Sent Events (SSE) |

## Quick Start

```bash
# 1. Start Redis
docker-compose up -d

# 2. Backend
cd backend
cp .env.example .env   # ← fill in your API keys
pip install -r requirements.txt
pip install pdfplumber
python main.py

# 3. Frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** and search for a ticker or upload a 10-K PDF.

## Documentation

See [HANDOFF.md](./HANDOFF.md) for:
- Full architecture walkthrough
- API endpoint reference
- Known issues & gotchas
- Feature roadmap

## API Keys Needed

| Key | Provider | Purpose |
|-----|----------|---------|
| `AIML_API_KEY` | [aimlapi.com](https://aimlapi.com) | PM, Bull, Bear agents |
| `FEATHERLESS_API_KEY` | [featherless.ai](https://featherless.ai) | Quant agent |
| Band tokens | [developers.band.us](https://developers.band.us) | Optional chat integration |

## License

MIT

---

*Built for the LabLab Hackathon · June 2026*
