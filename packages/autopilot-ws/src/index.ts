import type { WSEvent, WSEventType } from "@autopilot/types";

/** Create a typed WebSocket event */
export function createEvent<T>(type: WSEventType, data: T): WSEvent<T> {
  return {
    type,
    timestamp: new Date().toISOString(),
    data,
  };
}

/** Parse a raw WebSocket message into a typed event */
export function parseEvent(raw: string): WSEvent {
  return JSON.parse(raw) as WSEvent;
}

/** WebSocket connection config */
export interface WSConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * Resolve the WebSocket URL for the CT-PC.
 *
 * The iPad app runs on the Pi. The CT-PC is a separate machine whose address
 * is discovered via the Pi's /api/discovery endpoint, an env var override, or
 * a fallback to localhost.
 */
export async function resolveWsUrl(): Promise<string> {
  // 1. Explicit env var override
  if (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_CT_PC_URL) {
    return process.env.NEXT_PUBLIC_CT_PC_URL.replace(/^http/, "ws") + "/ws/events";
  }

  // 2. Auto-discover via Pi's discovery API
  if (typeof window !== "undefined") {
    try {
      const res = await fetch(`${window.location.origin}/api/discovery`);
      const data = await res.json();
      if (data.ctpc?.ip) {
        const port = data.ctpc.port || 4802;
        return `ws://${data.ctpc.ip}:${port}/ws/events`;
      }
    } catch {
      // Discovery unavailable — fall through
    }
  }

  // 3. Fallback
  return typeof window !== "undefined"
    ? `ws://${window.location.hostname}:4802/ws/events`
    : "ws://localhost:4802/ws/events";
}

export const DEFAULT_WS_CONFIG: WSConfig = {
  // Static fallback — consumers should prefer resolveWsUrl() for dynamic discovery
  url:
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_CT_PC_URL
      ? process.env.NEXT_PUBLIC_CT_PC_URL.replace(/^http/, "ws") + "/ws/events"
      : undefined) ||
    (typeof window !== "undefined"
      ? `ws://${window.location.hostname}:4802/ws/events`
      : "ws://localhost:4802/ws/events"),
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
};
