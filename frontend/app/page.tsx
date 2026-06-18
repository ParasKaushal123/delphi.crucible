"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import TickerSearch from "./components/TickerSearch";
import RoomPanel from "./components/RoomPanel";
import DebateRing from "./components/DebateRing";
import MemoPanel from "./components/MemoPanel";
import UploadZone from "./components/UploadZone";
import { useSSE } from "./hooks/useSSE";
import { toast, Toaster } from "react-hot-toast";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Ticker {
  ticker: string;
  name: string;
  exchange: string;
  sector: string;
}

interface ChatMessage {
  agent: string;
  content: string;
}

type Phase =
  | "IDLE"
  | "DATA_CAVE_OPEN"
  | "DATA_CAVE_COMPLETE"
  | "DEBATE_RING_OPEN"
  | "DEBATE_COMPLETE"
  | "MEMO_DELIVERED"
  | "ERROR";

export default function HomePage() {
  const [selectedTicker, setSelectedTicker] = useState<Ticker | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [phase, setPhase] = useState<Phase>("IDLE");
  const [memo, setMemo] = useState("");
  const [inputMode, setInputMode] = useState<"ticker" | "pdf">("ticker");

  // Messages for each room
  const [mainMessages, setMainMessages] = useState<ChatMessage[]>([]);
  const [dataCaveMessages, setDataCaveMessages] = useState<ChatMessage[]>([]);
  const [bullMessages, setBullMessages] = useState<ChatMessage[]>([]);
  const [bearMessages, setBearMessages] = useState<ChatMessage[]>([]);

  // Auto-scroll refs
  const mainScrollRef = useRef<HTMLDivElement>(null);
  const dataCaveScrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll rooms on new messages
  useEffect(() => {
    const mainEl = document.getElementById("room-main-room");
    if (mainEl) mainEl.scrollTop = mainEl.scrollHeight;
  }, [mainMessages]);

  useEffect(() => {
    const dcEl = document.getElementById("room-data-cave");
    if (dcEl) dcEl.scrollTop = dcEl.scrollHeight;
  }, [dataCaveMessages]);

  useEffect(() => {
    const bullEl = document.getElementById("room-debate-bull");
    if (bullEl) bullEl.scrollTop = bullEl.scrollHeight;
  }, [bullMessages]);

  useEffect(() => {
    const bearEl = document.getElementById("room-debate-bear");
    if (bearEl) bearEl.scrollTop = bearEl.scrollHeight;
  }, [bearMessages]);

  // SSE event handler
  const handleSSEEvent = useCallback(
    (event: { session_id: string; type: string; data: Record<string, unknown> }) => {
      const { type, data } = event;

      switch (type) {
        case "room_message": {
          const room = data.room as string;
          const msg: ChatMessage = {
            agent: data.agent as string,
            content: data.content as string,
          };

          if (room === "main") {
            setMainMessages((prev) => [...prev, msg]);
          } else if (room === "data-cave") {
            setDataCaveMessages((prev) => [...prev, msg]);
          } else if (room === "debate-ring") {
            // Route to bull or bear based on agent
            if (msg.agent === "bull-agent") {
              setBullMessages((prev) => [...prev, msg]);
            } else if (msg.agent === "bear-agent") {
              setBearMessages((prev) => [...prev, msg]);
            } else {
              // PM messages go to both
              setBullMessages((prev) => [...prev, msg]);
              setBearMessages((prev) => [...prev, msg]);
            }
          }
          break;
        }

        case "phase_change": {
          const newPhase = data.phase as Phase;
          setPhase(newPhase);
          if (newPhase === "MEMO_DELIVERED" || newPhase === "ERROR") {
            setIsRunning(false);
          }
          if (newPhase === "MEMO_DELIVERED" && data.is_emergency) {
            toast.error("⚠️ AUTONOMOUS ALERT: NVDA position changed. Click to view.", {
              duration: 8000,
              style: {
                background: '#ff4b4b',
                color: '#fff',
                fontWeight: 'bold',
              },
            });
          }
          break;
        }

        case "memo_update": {
          setMemo(data.memo as string);
          break;
        }
      }
    },
    []
  );

  const { connected } = useSSE(handleSSEEvent);

  // Trigger analysis — Ticker mode
  const handleGenerate = async () => {
    if (!selectedTicker || isRunning) return;

    // Reset state
    setIsRunning(true);
    setPhase("IDLE");
    setMemo("");
    setMainMessages([]);
    setDataCaveMessages([]);
    setBullMessages([]);
    setBearMessages([]);

    try {
      const resp = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: selectedTicker.ticker }),
      });

      if (!resp.ok) {
        throw new Error("Failed to start analysis");
      }
    } catch (e) {
      setIsRunning(false);
      setMainMessages([
        {
          agent: "pm-agent",
          content: `Error: Failed to start analysis pipeline. Make sure the backend is running.`,
        },
      ]);
    }
  };

  const handleSimulateCrash = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setPhase("IDLE");
    setMemo("");
    setMainMessages([]);
    setDataCaveMessages([]);
    setBullMessages([]);
    setBearMessages([]);
    try {
      const resp = await fetch(`${API_BASE}/api/simulate-market-tick`, {
        method: "POST",
      });
      if (!resp.ok) throw new Error("Failed to simulate crash");
    } catch (e) {
      setIsRunning(false);
      toast.error("Failed to trigger simulation");
    }
  };

  // Trigger analysis — PDF mode (called by UploadZone after successful upload)
  const handleUploadStart = (companyName: string) => {
    setIsRunning(true);
    setPhase("IDLE");
    setMemo("");
    setMainMessages([]);
    setDataCaveMessages([]);
    setBullMessages([]);
    setBearMessages([]);
    setMainMessages([
      {
        agent: "pm-agent",
        content: `PDF uploaded. Analyzing **${companyName}** — watch the Data Cave for live updates.`,
      },
    ]);
  };

  // Room status helpers
  const getMainStatus = (): { status: "idle" | "active" | "complete"; text: string } => {
    if (phase === "MEMO_DELIVERED") return { status: "complete", text: "Memo Delivered" };
    if (phase !== "IDLE") return { status: "active", text: "Pipeline Active" };
    return { status: "idle", text: "Ready" };
  };

  const getDataCaveStatus = (): {
    status: "idle" | "active" | "complete" | "waiting";
    text: string;
  } => {
    if (phase === "DATA_CAVE_COMPLETE" || phase === "DEBATE_RING_OPEN" || phase === "DEBATE_COMPLETE" || phase === "MEMO_DELIVERED")
      return { status: "complete", text: "Data Extracted" };
    if (phase === "DATA_CAVE_OPEN") return { status: "active", text: "Quant Analyzing..." };
    return { status: "idle", text: "Standby" };
  };

  const getDebateStatus = (): {
    status: "idle" | "active" | "complete" | "waiting";
    text: string;
  } => {
    if (phase === "DEBATE_COMPLETE" || phase === "MEMO_DELIVERED")
      return { status: "complete", text: "Debate Concluded" };
    if (phase === "DEBATE_RING_OPEN") return { status: "active", text: "Agents Debating..." };
    return { status: "idle", text: "Standby" };
  };

  const mainStatus = getMainStatus();
  const dataCaveStatus = getDataCaveStatus();
  const debateStatus = getDebateStatus();

  // Phase progress for header
  const getPhaseLabel = (): string => {
    switch (phase) {
      case "DATA_CAVE_OPEN":
        return "Phase 2: Data Cave";
      case "DATA_CAVE_COMPLETE":
        return "Data Synthesized";
      case "DEBATE_RING_OPEN":
        return "Phase 3: Debate Ring";
      case "DEBATE_COMPLETE":
        return "Writing Memo...";
      case "MEMO_DELIVERED":
        return "Memo Complete ✓";
      default:
        return isRunning ? "Starting..." : "Ready";
    }
  };

  return (
    <div className="app-container">
      {/* ─── Header ─── */}
      <Toaster position="top-right" />
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">TDC</div>
          <div>
            <div className="header-title">The Delphi Crucible</div>
            <div className="header-subtitle">Multi-Agent Investment Analysis · Band.ai</div>
          </div>
        </div>

        <div className="header-status">
          <div className="agent-indicators" style={{ display: 'flex', gap: '12px', marginRight: '24px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: '#fff', fontWeight: 500 }}>PM {connected ? '🟢' : '⚪'}</span>
            <span style={{ fontSize: '12px', color: '#fff', fontWeight: 500 }}>Quant {connected ? '🟢' : '⚪'}</span>
            <span style={{ fontSize: '12px', color: '#fff', fontWeight: 500 }}>Bull {connected ? '🟢' : '⚪'}</span>
            <span style={{ fontSize: '12px', color: '#fff', fontWeight: 500 }}>Bear {connected ? '🟢' : '⚪'}</span>
          </div>
          <button 
            className="simulate-crash-btn" 
            onClick={handleSimulateCrash}
            disabled={isRunning}
            style={{ backgroundColor: '#ff4b4b', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '16px', fontWeight: 'bold' }}
          >
            🚨 Simulate Market Crash
          </button>
          <div className="status-badge">
            <span
              className={`status-dot ${
                phase === "MEMO_DELIVERED"
                  ? ""
                  : phase === "IDLE"
                  ? "idle"
                  : ""
              }`}
            />
            {getPhaseLabel()}
          </div>
          <div className="status-badge">
            <span
              className={`status-dot ${connected ? "" : "error"}`}
              style={connected ? {} : { animation: "none" }}
            />
            {connected ? "SSE Connected" : "Connecting..."}
          </div>
        </div>
      </header>

      {/* ─── Ticker Bar ─── */}
      <div className="ticker-bar">
        {/* Mode toggle */}
        <div className="input-mode-tabs">
          <button
            className={`input-mode-tab ${inputMode === "ticker" ? "active" : ""}`}
            onClick={() => setInputMode("ticker")}
            disabled={isRunning}
            id="tab-ticker"
          >
            📈 Ticker
          </button>
          <button
            className={`input-mode-tab ${inputMode === "pdf" ? "active" : ""}`}
            onClick={() => setInputMode("pdf")}
            disabled={isRunning}
            id="tab-pdf"
          >
            📄 10-K PDF
          </button>
        </div>

        {/* Conditional input */}
        {inputMode === "ticker" ? (
          <>
            <TickerSearch
              onSelect={setSelectedTicker}
              onClear={() => setSelectedTicker(null)}
              selectedTicker={selectedTicker}
              disabled={isRunning}
            />
            <button
              className={`generate-btn ${isRunning ? "running" : ""}`}
              onClick={handleGenerate}
              disabled={!selectedTicker || isRunning}
              id="generate-memo-btn"
            >
              {isRunning ? (
                <>
                  <span className="upload-spinner" style={{ width: 14, height: 14, borderTopColor: "white" }} />
                  Analyzing...
                </>
              ) : (
                <>🚀 Generate Memo</>
              )}
            </button>
          </>
        ) : (
          <UploadZone
            onUploadStart={handleUploadStart}
            disabled={isRunning}
          />
        )}
      </div>

      {/* ─── War Room (3-column) ─── */}
      <div className="war-room">
        {/* Column 1: Main Room */}
        <RoomPanel
          roomName="Main Room"
          roomIcon="🏛️"
          roomClass="main-room"
          messages={mainMessages}
          status={mainStatus.status}
          statusText={mainStatus.text}
        />

        {/* Column 2: Data Cave */}
        <RoomPanel
          roomName="Data Cave"
          roomIcon="⚗️"
          roomClass="data-cave"
          messages={dataCaveMessages}
          status={dataCaveStatus.status}
          statusText={dataCaveStatus.text}
        />

        {/* Column 3: Debate Ring (split Bull/Bear) */}
        <DebateRing
          bullMessages={bullMessages}
          bearMessages={bearMessages}
          status={debateStatus.status}
          statusText={debateStatus.text}
        />
      </div>

      {/* ─── Memo Strip (bottom) ─── */}
      <MemoPanel memo={memo} isVisible={phase === "MEMO_DELIVERED"} />
    </div>
  );
}
