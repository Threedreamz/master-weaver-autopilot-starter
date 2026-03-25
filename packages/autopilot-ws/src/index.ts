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

export const DEFAULT_WS_CONFIG: WSConfig = {
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
