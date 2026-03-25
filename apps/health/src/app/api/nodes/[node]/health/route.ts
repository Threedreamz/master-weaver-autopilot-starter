import { NextRequest, NextResponse } from "next/server";

const NODE_TARGETS: Record<string, string> = {
  ipad: "http://localhost:4800/api/health",
  pi: "http://localhost:4801/api/health",
  ctpc: "http://localhost:4802/health",
  pipeline: "http://localhost:4802/queue/stats",
};

export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ node: string }> }
) {
  const { node } = await params;
  const target = NODE_TARGETS[node];

  if (!target) {
    return NextResponse.json(
      { online: false, error: `Unknown node: ${node}` },
      { status: 404 }
    );
  }

  try {
    const res = await fetch(target, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Normalize response per node type
    if (node === "ipad") {
      const hasRealClients = (data.connectedClients ?? 0) > 0;
      return NextResponse.json({
        online: hasRealClients,
        serverRunning: true,
        connectedClients: data.connectedClients ?? 0,
        clientIps: data.clientIps ?? [],
        timestamp: data.timestamp,
        lastActivity: hasRealClients ? new Date().toISOString() : null,
      });
    }

    if (node === "pi") {
      return NextResponse.json({
        online: true,
        timestamp: data.timestamp,
        cameras: data.cameras ?? [false, false],
        cpuTemp: data.cpuTemp ?? 0,
        memoryUsedPct: data.memoryUsedPct ?? 0,
        fps: data.fps ?? 0,
      });
    }

    if (node === "ctpc") {
      return NextResponse.json({
        online: true,
        timestamp: data.timestamp,
        winwerthConnected: data.winwerth_connected ?? false,
        scanState: data.scan_state ?? "IDLE",
        errors: data.errors ?? 0,
        tubeOk: data.tube_ok ?? false,
      });
    }

    if (node === "pipeline") {
      return NextResponse.json({
        online: true,
        timestamp: new Date().toISOString(),
        activeScans: data.active ?? 0,
        queueLength: data.queued ?? 0,
        lastCompleted: data.last_completed ?? null,
        successRate: data.success_rate ?? 0,
      });
    }

    return NextResponse.json({ online: true, ...data });
  } catch {
    return NextResponse.json(
      {
        online: false,
        timestamp: new Date().toISOString(),
      },
      { status: 200 } // Return 200 with online:false so poller doesn't error
    );
  }
}
