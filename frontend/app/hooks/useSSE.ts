"use client";

import { useEffect, useRef, useCallback, useState } from "react";

interface SSEEvent {
  session_id: string;
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

type SSECallback = (event: SSEEvent) => void;

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useSSE(onEvent: SSECallback) {
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const callbackRef = useRef<SSECallback>(onEvent);

  // Keep callback ref up to date
  useEffect(() => {
    callbackRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const connect = () => {
      const es = new EventSource(`${API_BASE}/api/sse/events`);

      es.onopen = () => {
        setConnected(true);
      };

      es.addEventListener("update", (event) => {
        try {
          const parsed: SSEEvent = JSON.parse(event.data);
          callbackRef.current(parsed);
        } catch (e) {
          console.error("Failed to parse SSE event:", e);
        }
      });

      es.onerror = () => {
        setConnected(false);
        es.close();
        // Reconnect after 3 seconds
        setTimeout(connect, 3000);
      };

      eventSourceRef.current = es;
    };

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return { connected };
}
