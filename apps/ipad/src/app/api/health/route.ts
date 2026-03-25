import { NextRequest, NextResponse } from "next/server";
import type { HealthResponse } from "@autopilot/types";

const startTime = Date.now();

// Track unique client IPs that accessed the iPad UI (not just health checks)
const activeClients = new Map<string, number>(); // ip -> last seen timestamp
const CLIENT_TIMEOUT_MS = 30_000; // 30s without activity = disconnected

/** Called by the client heartbeat endpoint to register activity */
export function registerClient(ip: string) {
  activeClients.set(ip, Date.now());
}

function getConnectedClients(): number {
  const now = Date.now();
  // Prune stale clients
  for (const [ip, lastSeen] of activeClients) {
    if (now - lastSeen > CLIENT_TIMEOUT_MS) activeClients.delete(ip);
  }
  return activeClients.size;
}

export async function GET(req: NextRequest) {
  // If request comes from a non-localhost IP, register it as a connected client
  const forwarded = req.headers.get("x-forwarded-for");
  const ip = forwarded?.split(",")[0]?.trim() ?? req.headers.get("x-real-ip") ?? "unknown";

  // Don't count localhost/health-check polling as a "connected iPad"
  const isLocalhost = ip === "127.0.0.1" || ip === "::1" || ip === "localhost";
  if (!isLocalhost && ip !== "unknown") {
    registerClient(ip);
  }

  const connectedClients = getConnectedClients();

  const response: HealthResponse & { connectedClients: number; clientIps: string[] } = {
    status: "ok",
    node: "ipad",
    timestamp: new Date().toISOString(),
    uptime: Math.floor((Date.now() - startTime) / 1000),
    connectedClients,
    clientIps: [...activeClients.keys()],
  };
  return NextResponse.json(response);
}
