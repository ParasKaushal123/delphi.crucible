# The Delphi Crucible — Comprehensive Documentation

This document serves as the single source of truth for **The Delphi Crucible**. It synthesizes the project's architecture, AI agent orchestration, frontend design system, and the Band.ai SDK integration concepts. All previous fragmented documentation files have been consolidated here.

---

## 1. Project Overview

**The Delphi Crucible** is a multi-agent AI investment analysis platform originally built for the LabLab Hackathon (June 2026). It orchestrates a debate between specialized AI agents to produce institutional-grade investment memos. 

Users provide a stock ticker (e.g., `NVDA`) or upload a 10-K PDF. The system orchestrates 4 AI agents via **Band.ai** that analyze the data, debate in real-time (Bull vs. Bear), and synthesize a final memo. Users can then seamlessly **Paper Trade** based on the AI's recommendations, tracking their portfolio and 30-day historical charts in a dedicated dashboard.

### State Machine (Phases)
The orchestration flows through the following phases:
```
IDLE → DATA_CAVE_OPEN → DATA_CAVE_COMPLETE → DEBATE_RING_OPEN → DEBATE_COMPLETE → MEMO_DELIVERED
```

---

## 2. System Architecture

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11 + FastAPI + Uvicorn + pdfplumber + httpx |
| **Frontend** | Next.js 16.2.9 + TypeScript + React + Tailwind CSS v4 + Framer Motion |
| **Agent Orchestration** | Band.ai SDK (`thenvoi_rest`, `band` packages) |
| **AI/ML (PM, Bull, Bear)** | AI/ML API (`api.aimlapi.com/v1`) — GPT-4o |
| **AI/ML (Quant)** | Featherless AI (`api.featherless.ai/v1`) — Qwen2.5-72B |
| **State Management** | Global `WorkspaceContext` (React) + Native Redis (Windows install, port 6379) |
| **Styling** | Custom "Mesh Dark Editorial" design system via vanilla CSS + Tailwind |

### Core Execution Flow
1. User posts a ticker to `/api/analyze` or a PDF via FormData to `/api/analyze/upload`.
2. The **PM Agent** creates a Band.ai chat room and pings all agents.
3. The **Quant Agent** pulls financials via Featherless AI or processes the PDF via `pdfplumber`.
4. The **Bull** and **Bear** agents argue in parallel using GPT-4o.
5. The **PM Agent** synthesizes the arguments and delivers the final investment memo.
6. The Next.js frontend receives all messages and events in real-time via Server-Sent Events (SSE).

### Infrastructure Setup
The project runs natively on Windows PowerShell via local scripts:
- **Redis**: Runs on port `6379`.
- **Backend**: `python -m uvicorn main:app --port 8000` (Port `8000`).
- **Frontend**: `npm run dev` (Port `3000`).
- **Startup Script**: `.\start.ps1` handles spinning up the stack.
- **Shutdown Script**: `.\stop.ps1` handles process cleanup.

---

## 3. Agent Definitions

| Agent | Role | AI Provider | Band Handle |
|-------|------|-------------|-------------|
| **PM (Manager)** | Orchestrator, creates rooms, synthesizes final memo | AI/ML API (GPT-4o) | `@paras.kaushal.work/manager` |
| **Quant** | Financial data extraction / PDF document processing | Featherless AI (Qwen2.5-72B) | `@paras.kaushal.work/quant` |
| **Bull** | Formulates the bullish investment case | AI/ML API (GPT-4o) | `@paras.kaushal.work/bull` |
| **Bear** | Formulates the bearish investment case | AI/ML API (GPT-4o) | `@paras.kaushal.work/bear` |

---

## 4. Frontend Design System (Mesh Dark Editorial)

The frontend uses a highly stylized single-page "glass window" app structure. It relies on vanilla CSS logic combined with Tailwind `@layer`s.

### Layout Structure
- **Left Panel**: "Analysis Input" (Ticker / PDF drag-and-drop) and a wide "PM Agent Feed" that expands dynamically.
- **Center Panel**: The "Debate Ring" natively mapping `bullMessages` and `bearMessages` into separated agent bubbles.
- **Right Panel**: The "Data Cave" and "Quant Feed" displaying `dataCaveMessages`.
- **Background**: An animated WebGL-style glowing orbital canvas (`AnimatedBackground.tsx`).

### Design Rules
- **Color Palette**: 
  - Obsidian Canvas (`#0f0f10`)
  - Graphite Layer (`#1d1d1f`)
  - Bone White (`#fefef7`)
  - Bronze Glow (`#f2b98b`)
- **Typography**: 
  - Google Fonts: *Hanken Grotesk* (Headers), *Source Serif 4* (Memos), *Material Symbols*.
  - Use uppercase labels with wide letter-spacing (`tracking-widest`).
- **Constraints**: 
  - Do NOT introduce additional chromatic colors.
  - Do reserve `#f2b98b` for outlined actions and decorative accents—never as a fill.
  - Dark mode is forced globally (`class="dark"`).
- **Markdown Handling**: Uses `@tailwindcss/typography` combined with `<ReactMarkdown>` wrapped in standard `<div>` elements to prevent hydration crashes.

---

## 5. Band.ai Platform Integration Guide

The project relies heavily on Band.ai for agent orchestration. This section synthesizes the core SDK concepts needed to maintain the platform.

### Remote Agents vs Platform Agents
The Delphi Crucible uses **Remote Agents**. These agents run in our local backend environment and connect to the Band API via the Python SDK. We control the execution loop, the LLM, and the tools, while Band handles message routing and room participation.

### Two-Channel Architecture
1. **REST API**: Used to send commands to the platform (create chats, send messages, manage participants). Base URL: `https://app.band.ai/api/v1/agent`.
2. **WebSockets**: Used to receive real-time events (incoming messages, room changes).
*Note: An agent must use both. Sending messages via REST does not automatically subscribe the agent to replies.*

### Chat Rooms & @Mention Routing
Band uses a targeted routing system to prevent context overload:
- Agents **only** receive and process messages where they are explicitly `@mentioned`.
- Non-mentioned agents in a room see nothing.
- Humans see all messages.
- Multiple agents can be mentioned in one message to trigger parallel execution (e.g., `@Bull @Bear Analyze this data`).

### Message Types
- `text`: Regular chat messages (routed via mentions).
- `tool_call` & `tool_result`: Agent invoking a tool and receiving results.
- `thought`: Internal agent reasoning.
- `error`: Failure notifications.
- `task`: Status updates.
*Note: Events do not require mentions. They are visible to humans and stored in the chat history but do not route to other agents.*

### Contacts & Visibility
Handles are structured as `@username/agent-slug`.
- **Sibling Agents**: Agents owned by the same user (like our 4 agents) are automatically visible to each other and require no explicit contact requests.
- **Cross-Boundary Contacts**: If interacting with agents from other organizations, a bilateral contact request (`PENDING` → `APPROVED`) is required before adding them to a chat room.

### State Recovery (Crash Resilience)
If the backend crashes during processing, messages remain in a `processing` state. Upon restart:
1. The SDK drains the backlog via `GET /messages/next`.
2. The agent resumes work, calling `POST /messages/{id}/processing` to create a new attempt.
3. Once the backlog returns `204 No Content`, the agent switches back to real-time WebSockets.

---

## 6. Recent Platform Updates (Performance & UX)

The platform was significantly upgraded to improve load times, user experience, and stability against third-party API restrictions.

1. **Persistent Global State (`WorkspaceContext`)**
   - The React component-level `useState` was abstracted into a global `WorkspaceContext`. 
   - Users can now click out to the Portfolio or History pages while the agents are generating a memo, and seamlessly return to the Workspace without losing their chat history or phase state.

2. **Yahoo Finance 429 Bypass (`requests` & `httpx` proxying)**
   - The `yfinance` Python library was completely stripped from the frontend-facing UI APIs due to aggressive IP rate-limiting blocks (429 Too Many Requests) by Yahoo.
   - Live prices and historical charts are now fetched via direct, custom-headers `requests.get()` and `httpx.AsyncClient.get()` calls to Yahoo's `query2.finance.yahoo.com` endpoint, perfectly mimicking browser behavior and bypassing the block entirely.

3. **Parallel Asynchronous Loading (`asyncio.gather`)**
   - The Portfolio page load times were slashed from 10+ seconds to <1 second. The backend now fires all historical chart and price HTTP requests simultaneously via `httpx` and `asyncio.gather` instead of resolving them sequentially.

4. **Interactive Sub-Charts & Framer Motion**
   - The entire Next.js application is wrapped in a `template.tsx` file utilizing `framer-motion` `<AnimatePresence>`, delivering premium, glassy slide-and-fade transitions across page navigations.
   - The Portfolio UI features expandable table rows—clicking any held stock instantly fires an asynchronous request to render an individual 30-day glowing area chart via `recharts`.

---
*End of Documentation.*
