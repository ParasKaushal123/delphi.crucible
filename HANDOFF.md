# Investment Memo Bench - V2 Handoff Document

Welcome to the **Investment Memo Bench**! This document serves as a comprehensive handoff for the next agent/developer taking over the project to build **v2**.

## 🏗️ System Architecture & Tech Stack

This project is a multi-agent debate platform built on the **Band SDK** network.
- **Backend:** Python (FastAPI, Uvicorn)
- **Frontend:** Next.js / React (runs on port 3000)
- **State Store:** Redis (runs via docker-compose)
- **Agents:** 4 distinct agents running locally via `band-sdk` WebSockets:
  1. **Portfolio Manager (PM)**
  2. **Quantitative Agent (Quant)**
  3. **Bullish Analyst (Bull)**
  4. **Bearish Agent (Bear)**

## 🤖 LLM Integrations
- The **Quant Agent** uses **Featherless AI** (currently configured to use the ungated `Qwen/Qwen2.5-72B-Instruct` model to bypass HuggingFace OAuth gating issues).
- The **PM, Bull, and Bear Agents** use the **AI/ML API** (currently configured to use `gpt-4o`).

## 🔄 The Multi-Agent State Machine

The agents communicate by sending text messages in Band network chat rooms. To prevent LLM hallucinations and race conditions, the system strictly enforces a **Redis-backed Phase State Machine**:

1. **`ROLL_CALL`**: PM Agent opens the "Main Room" and pings all agents. Agents reply `[System]: Acknowledged. Standing by.`
2. **`DATA_CAVE_OPEN`**: PM Agent commands the Quant Agent to extract financial data from the provided PDF/ticker.
3. **`DEBATE_RING_OPEN`**: Quant Agent finishes data extraction, creates a new room called the "Debate Ring", invites the PM, Bull, and Bear, and drops the data in. The Bull and Bear agents trigger simultaneously in parallel to write their cases.
4. **`MEMO_DELIVERED`**: The PM Agent intercepts the Bull and Bear replies in the Debate Ring. Once BOTH cases are stored in Redis, the PM generates the final Investment Memo and drops it in the Main Room.

## 🐛 Critical V1 Bug Fixes to Keep in Mind (DO NOT REVERT)

The following deeply complex edge cases were solved in V1. If you modify `backend/agents/adapters.py`, **do not break these fixes**:

1. **Explicit Mentions Array:** When using `tools.send_message` in the Band SDK, you **must** include the `mentions` array with the target's UUID. String mentions in the text alone (e.g. `@Portfolio Manager`) will NOT trigger the target agent's `on_message` hook!
2. **Cache Deduplication (`is_message_fresh`) namespaces:** The 4 adapters run in the same Python process and share the `processed_msg_ids` cache. Because the Quant Agent pings both Bull and Bear in a single message, they receive the exact same `msg.id`. The cache key is namespaced as `f"{adapter_name}:{msg.id}"` so they don't incorrectly discard each other's prompts.
3. **Redis Race Conditions:** The Bull and Bear agents run in parallel and take ~10 seconds to generate their cases. To prevent them from overwriting each other's Redis state, they **must** re-fetch the `Session` object from Redis immediately before saving their results.
4. **WebSocket History (`is_session_bootstrap`):** When the backend restarts, the Band WebSocket redelivers the recent chat history. We use a 60-second timestamp filter to ignore old messages.

## 🚀 Suggestions for V2 Development

Here are a few recommended paths for expanding this project in V2:
- **Expanded Agent Capabilities:** Give the Quant Agent tools to search the live web for breaking news using Tavily or Google Search APIs if no PDF is provided.
- **Interactive PM:** Allow the human user to jump into the Debate Ring and ask the Bull and Bear follow-up questions before the PM writes the final memo.
- **Memory & Persistence:** Connect the user profile JSON stored in Redis to a real database (PostgreSQL/Supabase) so users can save their historical memos.

*Good luck building V2!*
