"use client";

import { useEffect, useRef, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";

interface SSEEvent {
  session_id: string;
  type: string;
  data: any;
  timestamp: string;
}

type SSECallback = (event: SSEEvent) => void;

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useSSE(onEvent: SSECallback) {
  const [connected, setConnected] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const callbackRef = useRef<SSECallback>(onEvent);

  useEffect(() => {
    callbackRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    controllerRef.current = new AbortController();

    const connect = async () => {
      try {
        await fetchEventSource(`${API_BASE}/api/sse/events`, {
          method: 'GET',
          headers: {
            'Accept': 'text/event-stream',
            'ngrok-skip-browser-warning': '69420'
          },
          signal: controllerRef.current?.signal,
          onopen: async (res) => {
            if (res.ok && res.status === 200) {
              setConnected(true);
            } else {
              setConnected(false);
            }
          },
          onmessage: (event) => {
            if (event.event === "update" || event.data) {
              try {
                const parsed: SSEEvent = JSON.parse(event.data);
                callbackRef.current(parsed);
              } catch (e) {
                console.error("Failed to parse SSE event:", e);
              }
            }
          },
          onclose: () => {
            setConnected(false);
            throw new Error("Connection closed by server"); // forces retry
          },
          onerror: (err) => {
            setConnected(false);
            console.error("SSE Error:", err);
            return 3000; // retry after 3 seconds
          }
        });
      } catch (err) {
        setConnected(false);
      }
    };

    connect();

    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
    };
  }, []);

  return { connected };
}
