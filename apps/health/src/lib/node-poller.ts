/**
 * Node health poller — polls each node's /health endpoint every 5 seconds.
 * Maintains a ring buffer of the last 100 health snapshots per node.
 * Detects online/offline transitions.
 */

export interface NodeHealth {
  online: boolean;
  degraded?: boolean;
  timestamp: string;
  uptime?: number;
  // iPad fields
  lastActivity?: string;
  // Pi fields
  cameras?: [boolean, boolean];
  cpuTemp?: number;
  memoryUsedPct?: number;
  fps?: number;
  // CT-PC fields
  winwerthConnected?: boolean;
  scanState?: string;
  errors?: number;
  tubeOk?: boolean;
  // Pipeline fields
  activeScans?: number;
  queueLength?: number;
  lastCompleted?: string;
  successRate?: number;
  // Catch-all for raw data
  [key: string]: unknown;
}

const BUFFER_SIZE = 100;
const NODE_URLS: Record<string, string> = {
  ipad: `${typeof window !== "undefined" ? window.location.origin : ""}/api/nodes/ipad/health`,
  pi: `${typeof window !== "undefined" ? window.location.origin : ""}/api/nodes/pi/health`,
  ctpc: `${typeof window !== "undefined" ? window.location.origin : ""}/api/nodes/ctpc/health`,
  pipeline: `${typeof window !== "undefined" ? window.location.origin : ""}/api/nodes/pipeline/health`,
};

// Ring buffers per node
const historyBuffers: Record<string, NodeHealth[]> = {};

function pushToBuffer(nodeId: string, entry: NodeHealth) {
  if (!historyBuffers[nodeId]) historyBuffers[nodeId] = [];
  const buf = historyBuffers[nodeId];
  buf.push(entry);
  if (buf.length > BUFFER_SIZE) buf.shift();
}

/**
 * Poll a node's health endpoint. Returns a NodeHealth object.
 * If the node is unreachable, returns an offline health record.
 */
export async function pollNode(nodeId: string): Promise<NodeHealth> {
  const url = NODE_URLS[nodeId];
  if (!url) {
    const offlineEntry: NodeHealth = { online: false, timestamp: new Date().toISOString() };
    pushToBuffer(nodeId, offlineEntry);
    return offlineEntry;
  }

  try {
    const res = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const entry: NodeHealth = {
      ...data,
      online: true,
      timestamp: data.timestamp ?? new Date().toISOString(),
    };

    // Detect degraded state
    if (nodeId === "pi" && entry.cpuTemp != null && entry.cpuTemp >= 75) {
      entry.degraded = true;
    }
    if (nodeId === "ctpc" && (entry.errors ?? 0) > 0) {
      entry.degraded = true;
    }

    // Detect transition
    const prev = getLastEntry(nodeId);
    if (prev && prev.online !== entry.online) {
      console.log(`[node-poller] ${nodeId}: ${prev.online ? "online" : "offline"} -> ${entry.online ? "online" : "offline"}`);
    }

    pushToBuffer(nodeId, entry);
    return entry;
  } catch {
    const offlineEntry: NodeHealth = {
      online: false,
      timestamp: new Date().toISOString(),
    };

    const prev = getLastEntry(nodeId);
    if (prev && prev.online) {
      console.log(`[node-poller] ${nodeId}: online -> offline (unreachable)`);
    }

    pushToBuffer(nodeId, offlineEntry);
    return offlineEntry;
  }
}

function getLastEntry(nodeId: string): NodeHealth | null {
  const buf = historyBuffers[nodeId];
  if (!buf || buf.length === 0) return null;
  return buf[buf.length - 1];
}

/**
 * Get the full health history ring buffer for a node.
 */
export function getHistory(nodeId: string): NodeHealth[] {
  return historyBuffers[nodeId] ?? [];
}
