/**
 * Scan tracker — subscribes to CT-PC WebSocket for scan state updates.
 * Maintains a chronological scan history in memory.
 * Falls back to polling if WebSocket is unavailable.
 */

import type { ScanEvent } from "@/components/ScanStateTimeline";

const MAX_HISTORY = 500;
let scanHistory: ScanEvent[] = [];
let wsConnection: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Initialize the scan tracker WebSocket connection.
 * Call this once from a client component's useEffect.
 */
export function initScanTracker(wsUrl?: string) {
  if (typeof window === "undefined") return;
  if (wsConnection?.readyState === WebSocket.OPEN) return;

  const url = wsUrl ?? `ws://${window.location.hostname}:4802/ws/scans`;

  try {
    wsConnection = new WebSocket(url);

    wsConnection.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const scanEvent: ScanEvent = {
          id: data.id ?? `scan-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          state: data.state ?? "queued",
          timestamp: data.timestamp ?? new Date().toISOString(),
          partName: data.partName,
          duration: data.duration,
        };
        pushScanEvent(scanEvent);
      } catch {
        console.warn("[scan-tracker] Failed to parse WebSocket message");
      }
    };

    wsConnection.onclose = () => {
      wsConnection = null;
      // Reconnect after 5 seconds
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          initScanTracker(wsUrl);
        }, 5000);
      }
    };

    wsConnection.onerror = () => {
      wsConnection?.close();
    };
  } catch {
    console.warn("[scan-tracker] WebSocket connection failed, will retry");
  }
}

function pushScanEvent(event: ScanEvent) {
  scanHistory.push(event);
  if (scanHistory.length > MAX_HISTORY) {
    scanHistory = scanHistory.slice(-MAX_HISTORY);
  }
}

/**
 * Get the full scan history, newest last.
 */
export function getScanHistory(): ScanEvent[] {
  return [...scanHistory];
}

/**
 * Add a mock scan event (useful for development/testing).
 */
export function addMockScanEvent(event: Partial<ScanEvent>) {
  pushScanEvent({
    id: event.id ?? `mock-${Date.now()}`,
    state: event.state ?? "completed",
    timestamp: event.timestamp ?? new Date().toISOString(),
    partName: event.partName,
    duration: event.duration,
  });
}

/**
 * Disconnect the WebSocket and clear reconnect timers.
 */
export function disconnectScanTracker() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }
}
