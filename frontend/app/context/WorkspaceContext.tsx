"use client";

import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from "react";

export type Phase =
  | "IDLE"
  | "DATA_CAVE_OPEN"
  | "DATA_CAVE_COMPLETE"
  | "DEBATE_RING_OPEN"
  | "DEBATE_COMPLETE"
  | "MEMO_DELIVERED"
  | "ERROR";

export interface UnifiedMessage {
  id?: string;
  agent: string;
  room?: string;
  content: string;
  timestamp: string;
}

export interface Session {
  session_id: string;
  ticker: string;
  company_name: string;
  created_at: string;
  phase: Phase;
}

interface WorkspaceContextType {
  sessions: Session[];
  activeSessionId: string | null;
  setActiveSessionId: React.Dispatch<React.SetStateAction<string | null>>;
  messages: UnifiedMessage[];
  setMessages: React.Dispatch<React.SetStateAction<UnifiedMessage[]>>;
  phase: Phase;
  setPhase: React.Dispatch<React.SetStateAction<Phase>>;
  fetchSessions: () => Promise<void>;
  loadSession: (id: string) => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  
  const [phase, setPhase] = useState<Phase>("IDLE");
  const [messages, setMessages] = useState<UnifiedMessage[]>([]);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (e) {
      console.error("Failed to fetch sessions", e);
    }
  }, []);

  const loadSession = useCallback(async (id: string) => {
    try {
      setActiveSessionId(id);
      const res = await fetch(`${API_BASE}/api/sessions/${id}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
        setPhase(data.session.phase || "IDLE");
      }
    } catch (e) {
      console.error("Failed to load session", e);
    }
  }, []);

  // Fetch sessions on initial load
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return (
    <WorkspaceContext.Provider
      value={{
        sessions,
        activeSessionId,
        setActiveSessionId,
        messages,
        setMessages,
        phase,
        setPhase,
        fetchSessions,
        loadSession
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
