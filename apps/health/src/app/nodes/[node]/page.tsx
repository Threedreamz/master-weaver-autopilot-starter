"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import MetricBar from "@/components/MetricBar";
import { pollNode, getHistory, type NodeHealth } from "@/lib/node-poller";
import type { StatusLevel } from "@/components/StatusPanel";

const nodeLabels: Record<string, string> = {
  ipad: "iPad",
  pi: "Raspberry Pi",
  ctpc: "CT-PC",
  pipeline: "Pipeline",
};

function deriveStatus(h: NodeHealth | null): StatusLevel {
  if (!h) return "unknown";
  if (!h.online) return "offline";
  if (h.degraded) return "degraded";
  return "online";
}

const statusColors: Record<StatusLevel, string> = {
  online: "var(--accent-green)",
  degraded: "var(--accent-yellow)",
  offline: "var(--accent-red)",
  unknown: "var(--accent-gray)",
};

const statusLabels: Record<StatusLevel, string> = {
  online: "Online",
  degraded: "Beeintraechtigt",
  offline: "Offline",
  unknown: "Unbekannt",
};

/** Tiny inline sparkline drawn on a <canvas>-like SVG */
function Sparkline({ data, color, height = 32 }: { data: number[]; color: string; height?: number }) {
  if (data.length < 2) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const w = 300;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${height}`} className="w-full" style={{ height }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div
      className="rounded-lg border p-4"
      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
    >
      <span className="text-xs block mb-1" style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-sm font-mono font-bold" style={{ color: color ?? "var(--text-primary)" }}>
        {value}
      </span>
    </div>
  );
}

export default function NodeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const nodeId = params.node as string;
  const label = nodeLabels[nodeId] ?? nodeId;

  const [health, setHealth] = useState<NodeHealth | null>(null);
  const [history, setHistory] = useState<NodeHealth[]>([]);

  useEffect(() => {
    const poll = async () => {
      const h = await pollNode(nodeId);
      setHealth(h);
      setHistory(getHistory(nodeId));
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, [nodeId]);

  const status = deriveStatus(health);

  const uptime = health?.uptime != null
    ? `${Math.floor(health.uptime / 3600)}h ${Math.floor((health.uptime % 3600) / 60)}m ${health.uptime % 60}s`
    : "---";

  // Derive sparkline data from history
  const responseTimeSeries = useMemo(() => {
    return history.map((_, idx) => {
      // Approximate response time from timestamp gaps
      if (idx === 0) return 0;
      const prev = new Date(history[idx - 1].timestamp).getTime();
      const curr = new Date(history[idx].timestamp).getTime();
      return Math.max(curr - prev - 5000, 0); // deviation from 5s polling
    });
  }, [history]);

  const onlineSeries = useMemo(() => {
    return history.map((h) => (h.online ? 1 : 0));
  }, [history]);

  // Pi-specific series
  const tempSeries = useMemo(() => history.map((h) => h.cpuTemp ?? 0), [history]);
  const memorySeries = useMemo(() => history.map((h) => h.memoryUsedPct ?? 0), [history]);

  // CT-PC-specific series
  const errorSeries = useMemo(() => history.map((h) => h.errors ?? 0), [history]);

  const needsRestart = status === "degraded" || status === "offline";

  return (
    <div>
      {/* Back navigation */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs mb-4 transition-colors"
        style={{ color: "var(--text-muted)" }}
        onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-secondary)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)"; }}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Zurueck zur Uebersicht
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            {label}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Node-Detailansicht
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-mono" style={{ color: statusColors[status] }}>
            {statusLabels[status]}
          </span>
          <span
            className={`inline-block w-3 h-3 rounded-full ${
              status === "online" ? "status-dot-green"
                : status === "degraded" ? "status-dot-yellow"
                : status === "offline" ? "status-dot-red"
                : ""
            }`}
            style={{ backgroundColor: statusColors[status] }}
          />
        </div>
      </div>

      {/* Restart suggestion */}
      {needsRestart && (
        <div
          className="rounded-lg border p-4 mb-6 flex items-center gap-3"
          style={{
            backgroundColor: status === "offline" ? "rgba(239,68,68,0.08)" : "rgba(234,179,8,0.08)",
            borderColor: status === "offline" ? "rgba(239,68,68,0.3)" : "rgba(234,179,8,0.3)",
          }}
        >
          <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
            style={{ color: status === "offline" ? "var(--accent-red)" : "var(--accent-yellow)" }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          <div>
            <p className="text-sm font-semibold" style={{ color: status === "offline" ? "var(--accent-red)" : "var(--accent-yellow)" }}>
              {status === "offline" ? "Node nicht erreichbar" : "Node beeintraechtigt"}
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
              {status === "offline"
                ? "Neustart empfohlen. Pruefe Netzwerkverbindung und Stromversorgung."
                : "Performance-Probleme erkannt. Neustart koennte helfen."}
            </p>
          </div>
        </div>
      )}

      {/* Status overview cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Status"
          value={statusLabels[status]}
          color={statusColors[status]}
        />
        <StatCard label="Betriebszeit" value={uptime} />
        <StatCard
          label="Zuletzt gesehen"
          value={health?.timestamp ? new Date(health.timestamp).toLocaleTimeString("de-DE") : "---"}
        />
        <StatCard
          label="Checks"
          value={`${history.length} / 100`}
          color="var(--text-secondary)"
        />
      </div>

      {/* Node-specific metrics */}
      {nodeId === "pi" && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Raspberry Pi Metriken
          </h2>

          {/* Cameras */}
          <div className="flex gap-6 mb-4">
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: health?.cameras?.[0] ? "var(--accent-green)" : "var(--accent-red)" }}
              />
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                Kamera 0 - {health?.cameras?.[0] ? "Aktiv" : "Inaktiv"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: health?.cameras?.[1] ? "var(--accent-green)" : "var(--accent-red)" }}
              />
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                Kamera 1 - {health?.cameras?.[1] ? "Aktiv" : "Inaktiv"}
              </span>
            </div>
            {health?.fps != null && (
              <div className="ml-auto flex items-center gap-1.5">
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>Stream:</span>
                <span className="text-sm font-mono font-bold" style={{
                  color: health.fps >= 20 ? "var(--accent-green)" : health.fps >= 10 ? "var(--accent-yellow)" : "var(--accent-red)"
                }}>
                  {health.fps} FPS
                </span>
              </div>
            )}
          </div>

          {/* Metric bars */}
          <div className="space-y-3">
            <MetricBar
              label="CPU Temperatur"
              value={health?.cpuTemp ?? 0}
              max={100}
              unit="°C"
              thresholds={{ warn: 60, critical: 75 }}
            />
            <MetricBar
              label="Speicher"
              value={health?.memoryUsedPct ?? 0}
              max={100}
              thresholds={{ warn: 75, critical: 90 }}
            />
          </div>

          {/* Sparklines */}
          {history.length >= 2 && (
            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t" style={{ borderColor: "var(--border-color)" }}>
              <div>
                <span className="text-xs block mb-2" style={{ color: "var(--text-muted)" }}>
                  Temperaturverlauf (letzte {history.length} Checks)
                </span>
                <Sparkline
                  data={tempSeries}
                  color={(health?.cpuTemp ?? 0) >= 75 ? "var(--accent-red)" : (health?.cpuTemp ?? 0) >= 60 ? "var(--accent-yellow)" : "var(--accent-green)"}
                />
              </div>
              <div>
                <span className="text-xs block mb-2" style={{ color: "var(--text-muted)" }}>
                  Speicherverlauf (letzte {history.length} Checks)
                </span>
                <Sparkline
                  data={memorySeries}
                  color={(health?.memoryUsedPct ?? 0) >= 90 ? "var(--accent-red)" : (health?.memoryUsedPct ?? 0) >= 75 ? "var(--accent-yellow)" : "var(--accent-green)"}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {nodeId === "ctpc" && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            CT-PC Metriken
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* WinWerth status */}
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>WinWerth Fenster</span>
              <span className="text-xs font-mono" style={{
                color: health?.winwerthConnected ? "var(--accent-green)" : "var(--accent-red)"
              }}>
                {health?.winwerthConnected ? "Verbunden" : "Getrennt"}
              </span>
            </div>

            {/* Tube status */}
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Roehre</span>
              <span className="text-xs font-mono" style={{
                color: health?.tubeOk ? "var(--accent-green)" : "var(--accent-red)"
              }}>
                {health?.tubeOk ? "OK" : "Warnung"}
              </span>
            </div>

            {/* Scan state */}
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Scan-Zustand</span>
              <span
                className="text-xs font-mono px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  color: health?.scanState === "scanning" ? "var(--accent-yellow)"
                    : health?.scanState === "idle" ? "var(--accent-green)"
                    : "var(--text-muted)",
                }}
              >
                {health?.scanState ?? "---"}
              </span>
            </div>

            {/* Active profile */}
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Aktives Profil</span>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {(health as Record<string, unknown>)?.activeProfile as string ?? "---"}
              </span>
            </div>
          </div>

          {/* Error boxes */}
          {(health?.errors ?? 0) > 0 && (
            <div
              className="rounded-lg px-3 py-2 mb-4"
              style={{ backgroundColor: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}
            >
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
                  style={{ color: "var(--accent-red)" }}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <span className="text-xs font-semibold" style={{ color: "var(--accent-red)" }}>
                  {health?.errors} Fehler in der letzten Stunde
                </span>
              </div>
            </div>
          )}

          {/* Error sparkline */}
          {history.length >= 2 && (
            <div className="pt-4 border-t" style={{ borderColor: "var(--border-color)" }}>
              <span className="text-xs block mb-2" style={{ color: "var(--text-muted)" }}>
                Fehlerverlauf (letzte {history.length} Checks)
              </span>
              <Sparkline
                data={errorSeries}
                color="var(--accent-red)"
              />
            </div>
          )}
        </div>
      )}

      {nodeId === "ipad" && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            iPad Details
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Verbindung</span>
              <span className="text-xs font-mono" style={{
                color: health?.online ? "var(--accent-green)" : "var(--accent-red)"
              }}>
                {health?.online ? "Verbunden" : "Getrennt"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Letzte Aktivitaet</span>
              <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                {health?.lastActivity ?? "---"}
              </span>
            </div>
          </div>
        </div>
      )}

      {nodeId === "pipeline" && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Pipeline Details
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Aktive Scans</span>
              <span className="text-lg font-mono font-bold" style={{ color: "var(--text-primary)" }}>
                {health?.activeScans ?? 0}
              </span>
            </div>
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Warteschlange</span>
              <span className="text-lg font-mono font-bold" style={{ color: "var(--text-primary)" }}>
                {health?.queueLength ?? 0}
              </span>
            </div>
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Letzter Abschluss</span>
              <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
                {health?.lastCompleted ?? "---"}
              </span>
            </div>
            <div>
              <span className="text-xs block" style={{ color: "var(--text-muted)" }}>Erfolgsrate</span>
              <span className="text-lg font-mono font-bold" style={{
                color: (health?.successRate ?? 100) >= 90 ? "var(--accent-green)"
                  : (health?.successRate ?? 100) >= 70 ? "var(--accent-yellow)"
                  : "var(--accent-red)"
              }}>
                {health?.successRate ?? 0}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Availability sparkline */}
      <div
        className="rounded-xl border p-5 mb-6"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
      >
        <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
          Verfuegbarkeit (letzte {history.length} Checks)
        </h2>
        {history.length >= 2 ? (
          <>
            <div className="flex gap-0.5 mb-3">
              {history.map((h, idx) => (
                <div
                  key={idx}
                  className="flex-1 h-6 rounded-sm"
                  style={{
                    backgroundColor: !h.online
                      ? "var(--accent-red)"
                      : h.degraded
                        ? "var(--accent-yellow)"
                        : "var(--accent-green)",
                    opacity: 0.7,
                  }}
                  title={`${new Date(h.timestamp).toLocaleTimeString("de-DE")} - ${h.online ? (h.degraded ? "Beeintraechtigt" : "Online") : "Offline"}`}
                />
              ))}
            </div>
            <div className="flex justify-between text-xs" style={{ color: "var(--text-muted)" }}>
              <span>Aelter</span>
              <span>
                {Math.round((history.filter((h) => h.online).length / history.length) * 100)}% Verfuegbarkeit
              </span>
              <span>Aktuell</span>
            </div>
          </>
        ) : (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Noch keine Historie vorhanden</p>
        )}
      </div>

      {/* Response time sparkline */}
      {history.length >= 2 && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Antwortzeit-Abweichung (letzte {history.length} Checks)
          </h2>
          <Sparkline data={responseTimeSeries} color="var(--accent-blue)" height={40} />
          <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
            Abweichung vom 5-Sekunden-Polling-Intervall in ms (niedriger = besser)
          </p>
        </div>
      )}

      {/* Recent health snapshots */}
      <div
        className="rounded-xl border p-5"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
      >
        <h2 className="text-sm font-semibold mb-3 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
          Letzte Health-Checks ({history.length})
        </h2>
        {history.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Noch keine Historie vorhanden</p>
        ) : (
          <div className="space-y-0 max-h-96 overflow-auto">
            {history.slice(-20).reverse().map((entry, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 text-xs py-2 border-b last:border-b-0"
                style={{ borderColor: "var(--border-color)" }}
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{
                    backgroundColor: !entry.online
                      ? "var(--accent-red)"
                      : entry.degraded
                        ? "var(--accent-yellow)"
                        : "var(--accent-green)",
                  }}
                />
                <span className="font-mono" style={{ color: "var(--text-muted)" }}>
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString("de-DE") : "---"}
                </span>
                <span style={{
                  color: !entry.online
                    ? "var(--accent-red)"
                    : entry.degraded
                      ? "var(--accent-yellow)"
                      : "var(--accent-green)",
                }}>
                  {!entry.online ? "offline" : entry.degraded ? "beeintraechtigt" : "online"}
                </span>

                {/* Node-specific inline details */}
                {nodeId === "pi" && entry.cpuTemp != null && (
                  <span className="ml-auto font-mono" style={{ color: "var(--text-muted)" }}>
                    {entry.cpuTemp}°C | {entry.memoryUsedPct ?? 0}% RAM
                    {entry.fps != null && ` | ${entry.fps} FPS`}
                  </span>
                )}
                {nodeId === "ctpc" && (
                  <span className="ml-auto font-mono" style={{ color: "var(--text-muted)" }}>
                    {entry.scanState ?? "---"}
                    {(entry.errors ?? 0) > 0 && (
                      <span style={{ color: "var(--accent-red)" }}> | {entry.errors} err</span>
                    )}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
