"use client";

import { useEffect, useState } from "react";
import StatusPanel, { type StatusLevel } from "@/components/StatusPanel";
import MetricBar from "@/components/MetricBar";
import { pollNode, type NodeHealth } from "@/lib/node-poller";

interface NodeState {
  health: NodeHealth | null;
  status: StatusLevel;
  lastUpdated: string | null;
}

const defaultState: NodeState = { health: null, status: "unknown", lastUpdated: null };

function deriveStatus(h: NodeHealth | null): StatusLevel {
  if (!h) return "unknown";
  if (!h.online) return "offline";
  if (h.degraded) return "degraded";
  return "online";
}

function formatAge(ts: string | null): string | null {
  if (!ts) return null;
  const diff = Date.now() - new Date(ts).getTime();
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`;
  return `${Math.round(diff / 3_600_000)}h ago`;
}

export default function OverviewPage() {
  const [ipad, setIpad] = useState<NodeState>(defaultState);
  const [pi, setPi] = useState<NodeState>(defaultState);
  const [ctpc, setCtpc] = useState<NodeState>(defaultState);
  const [pipeline, setPipeline] = useState<NodeState>(defaultState);

  useEffect(() => {
    const nodes = [
      { id: "ipad", setter: setIpad },
      { id: "pi", setter: setPi },
      { id: "ctpc", setter: setCtpc },
      { id: "pipeline", setter: setPipeline },
    ];

    const intervals = nodes.map(({ id, setter }) => {
      const poll = async () => {
        const h = await pollNode(id);
        setter({
          health: h,
          status: deriveStatus(h),
          lastUpdated: h?.timestamp ?? null,
        });
      };
      poll();
      return setInterval(poll, 5000);
    });

    return () => intervals.forEach(clearInterval);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>
        System Overview
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* iPad Panel */}
        <StatusPanel title="iPad" href="/nodes/ipad" status={ipad.status} lastUpdated={formatAge(ipad.lastUpdated)}>
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Connection</span>
            <span className="text-xs font-mono" style={{ color: ipad.health?.online ? "var(--accent-green)" : "var(--accent-red)" }}>
              {ipad.health?.online ? "Connected" : "Disconnected"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Last Activity</span>
            <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
              {ipad.health?.lastActivity ?? "---"}
            </span>
          </div>
        </StatusPanel>

        {/* Pi Panel */}
        <StatusPanel title="Raspberry Pi" href="/nodes/pi" status={pi.status} lastUpdated={formatAge(pi.lastUpdated)}>
          <div className="flex gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full" style={{
                backgroundColor: pi.health?.cameras?.[0] ? "var(--accent-green)" : "var(--accent-red)"
              }} />
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Cam 0</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full" style={{
                backgroundColor: pi.health?.cameras?.[1] ? "var(--accent-green)" : "var(--accent-red)"
              }} />
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Cam 1</span>
            </div>
            {pi.health?.fps != null && (
              <span className="text-xs font-mono ml-auto" style={{ color: "var(--text-secondary)" }}>
                {pi.health.fps} FPS
              </span>
            )}
          </div>
          <MetricBar
            label="CPU Temp"
            value={pi.health?.cpuTemp ?? 0}
            max={100}
            unit="C"
            thresholds={{ warn: 60, critical: 75 }}
          />
          <MetricBar
            label="Memory"
            value={pi.health?.memoryUsedPct ?? 0}
            max={100}
            thresholds={{ warn: 75, critical: 90 }}
          />
        </StatusPanel>

        {/* CT-PC Panel */}
        <StatusPanel title="CT-PC" href="/nodes/ctpc" status={ctpc.status} lastUpdated={formatAge(ctpc.lastUpdated)}>
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>WinWerth</span>
            <span className="text-xs font-mono" style={{
              color: ctpc.health?.winwerthConnected ? "var(--accent-green)" : "var(--accent-red)"
            }}>
              {ctpc.health?.winwerthConnected ? "Connected" : "Disconnected"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Scan State</span>
            <span
              className="text-xs font-mono px-1.5 py-0.5 rounded"
              style={{
                backgroundColor: "var(--bg-secondary)",
                color: ctpc.health?.scanState === "scanning" ? "var(--accent-yellow)"
                  : ctpc.health?.scanState === "idle" ? "var(--accent-green)"
                  : "var(--text-muted)",
              }}
            >
              {ctpc.health?.scanState ?? "---"}
            </span>
          </div>
          {(ctpc.health?.errors ?? 0) > 0 && (
            <div className="text-xs px-2 py-1 rounded" style={{ backgroundColor: "rgba(239,68,68,0.1)", color: "var(--accent-red)" }}>
              {ctpc.health?.errors} error(s) in last hour
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Tube</span>
            <span className="text-xs font-mono" style={{
              color: ctpc.health?.tubeOk ? "var(--accent-green)" : "var(--accent-red)"
            }}>
              {ctpc.health?.tubeOk ? "OK" : "Warning"}
            </span>
          </div>
        </StatusPanel>

        {/* Pipeline Panel */}
        <StatusPanel title="Pipeline" href="/scans" status={pipeline.status} lastUpdated={formatAge(pipeline.lastUpdated)}>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Active</span>
              <span className="text-lg font-mono font-bold" style={{ color: "var(--text-primary)" }}>
                {pipeline.health?.activeScans ?? 0}
              </span>
            </div>
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Queued</span>
              <span className="text-lg font-mono font-bold" style={{ color: "var(--text-primary)" }}>
                {pipeline.health?.queueLength ?? 0}
              </span>
            </div>
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Last Completed</span>
              <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
                {pipeline.health?.lastCompleted ?? "---"}
              </span>
            </div>
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Success Rate</span>
              <span className="text-lg font-mono font-bold" style={{
                color: (pipeline.health?.successRate ?? 100) >= 90 ? "var(--accent-green)"
                  : (pipeline.health?.successRate ?? 100) >= 70 ? "var(--accent-yellow)"
                  : "var(--accent-red)"
              }}>
                {pipeline.health?.successRate ?? 0}%
              </span>
            </div>
          </div>
        </StatusPanel>
      </div>
    </div>
  );
}
