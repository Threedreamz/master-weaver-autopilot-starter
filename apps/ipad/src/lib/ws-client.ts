"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { WSEvent, WSEventType } from "@autopilot/types";
import { parseEvent, DEFAULT_WS_CONFIG, resolveWsUrl } from "@autopilot/ws";

export type ConnectionState = "connecting" | "connected" | "disconnected";

interface UseWSEventsOptions {
  /** WebSocket URL override — when omitted, auto-discovers CT-PC via Pi */
  url?: string;
  /** Filter to specific event types */
  filter?: WSEventType[];
  /** Auto-reconnect interval in ms (default 3000) */
  reconnectInterval?: number;
}

/**
 * React hook for real-time WebSocket events from CT-PC.
 * Auto-discovers the CT-PC WebSocket URL via the Pi's discovery API.
 * Auto-reconnects on disconnect.
 */
export function useWSEvents(options: UseWSEventsOptions = {}) {
  const {
    url: urlOverride,
    filter,
    reconnectInterval = DEFAULT_WS_CONFIG.reconnectInterval ?? 3000,
  } = options;

  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptCount = useRef(0);
  const resolvedUrl = useRef<string | null>(urlOverride ?? null);

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // Resolve CT-PC WebSocket URL on first connect (or use override)
    if (!resolvedUrl.current) {
      try {
        resolvedUrl.current = await resolveWsUrl();
      } catch {
        resolvedUrl.current = DEFAULT_WS_CONFIG.url;
      }
    }

    setConnectionState("connecting");
    const ws = new WebSocket(resolvedUrl.current);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState("connected");
      attemptCount.current = 0;
    };

    ws.onmessage = (msg) => {
      try {
        const event = parseEvent(msg.data);
        if (!filter || filter.includes(event.type)) {
          setLastEvent(event);
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnectionState("disconnected");
      wsRef.current = null;
      if (attemptCount.current < (DEFAULT_WS_CONFIG.maxReconnectAttempts ?? 10)) {
        attemptCount.current++;
        reconnectTimer.current = setTimeout(connect, reconnectInterval);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [urlOverride, filter, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    attemptCount.current = Infinity; // prevent reconnect
    wsRef.current?.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { connectionState, lastEvent, disconnect, reconnect: connect };
}
