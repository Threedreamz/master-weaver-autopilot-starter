"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";

interface Worker {
  id: string;
  name: string;
  active: boolean;
  lastLogin?: string;
  lastLogout?: string;
  createdAt: string;
}

type TimeLogAction = "login" | "logout" | "auto-logout";

interface TimeLog {
  id: string;
  workerId: string;
  workerName: string;
  action: TimeLogAction;
  timestamp: string;
  scanId?: string;
}

interface WorkerHours {
  workerId: string;
  workerName: string;
  hours: number;
  autoLoggedOut?: boolean;
}

interface TimeTrackingStats {
  totalHoursToday: number;
  activeWorker: Worker | null;
  todayLogs: TimeLog[];
  workerHours: WorkerHours[];
}

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString("de-DE", { hour: "2-digit", minute: "2-digit" });
}

function formatDurationSince(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins} Min.`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h ${m}m`;
}

function formatHours(h: number): string {
  return h.toFixed(1);
}

const actionLabels: Record<TimeLogAction, string> = {
  login: "Login",
  logout: "Logout",
  "auto-logout": "Auto-Logout",
};

const actionColors: Record<TimeLogAction, string> = {
  login: "var(--accent-green)",
  logout: "var(--accent-red)",
  "auto-logout": "var(--accent-yellow)",
};

export default function TeamPage() {
  const [stats, setStats] = useState<TimeTrackingStats | null>(null);
  const [logs, setLogs] = useState<TimeLog[]>([]);
  const [refreshCountdown, setRefreshCountdown] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, logsRes] = await Promise.all([
        fetch("/api/team"),
        fetch("/api/team/logs"),
      ]);

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
        setError(null);
      } else {
        setError("CT-PC API nicht erreichbar");
      }

      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(Array.isArray(data) ? data : data.logs ?? []);
      }
    } catch {
      setError("Verbindung fehlgeschlagen");
    }
    setRefreshCountdown(5);
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const timer = setInterval(() => {
      setRefreshCountdown((c) => (c > 0 ? c - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Auto-scroll log list
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleExport = async () => {
    try {
      const res = await fetch("/api/team/export");
      if (!res.ok) throw new Error("Export fehlgeschlagen");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const today = new Date().toISOString().split("T")[0];
      a.href = url;
      a.download = `zeiterfassung-${today}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("CSV Export fehlgeschlagen");
    }
  };

  const maxHours = Math.max(
    8,
    ...(stats?.workerHours?.map((w) => w.hours) ?? [0])
  );

  // Determine if a worker was auto-logged-out today
  const autoLoggedOutWorkers = new Set(
    logs
      .filter((l) => l.action === "auto-logout")
      .map((l) => l.workerId)
  );

  return (
    <div>
      {/* Back navigation */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs mb-4 transition-colors"
        style={{ color: "var(--text-muted)" }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = "var(--text-secondary)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = "var(--text-muted)";
        }}
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15.75 19.5L8.25 12l7.5-7.5"
          />
        </svg>
        Zurueck zur Uebersicht
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Zeiterfassung
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Mitarbeiter-Anwesenheit und Arbeitszeiten
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExport}
            className="px-3 py-1.5 text-xs rounded-md transition-colors"
            style={{
              backgroundColor: "var(--bg-secondary)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-color)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--accent-blue)";
              e.currentTarget.style.color = "var(--accent-blue)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-color)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            <span className="flex items-center gap-1.5">
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                />
              </svg>
              CSV Export
            </span>
          </button>
          <div className="flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full status-dot-green"
              style={{ backgroundColor: "var(--accent-green)" }}
            />
            <span
              className="text-xs font-mono"
              style={{ color: "var(--text-muted)" }}
            >
              Auto-Refresh in {refreshCountdown}s
            </span>
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div
          className="rounded-lg border px-4 py-3 mb-6 text-sm"
          style={{
            backgroundColor: "rgba(239,68,68,0.1)",
            borderColor: "var(--accent-red)",
            color: "var(--accent-red)",
          }}
        >
          {error}
        </div>
      )}

      {/* Active worker card */}
      {stats?.activeWorker && (
        <div
          className="rounded-xl border-2 p-5 mb-6"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--accent-green)",
          }}
        >
          <div className="flex items-center gap-3 mb-2">
            <span
              className="w-3 h-3 rounded-full status-dot-green"
              style={{ backgroundColor: "var(--accent-green)" }}
            />
            <h2
              className="text-sm font-semibold uppercase tracking-wider"
              style={{ color: "var(--accent-green)" }}
            >
              Aktiver Mitarbeiter
            </h2>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <span
                className="text-xl font-bold font-mono"
                style={{ color: "var(--text-primary)" }}
              >
                {stats.activeWorker.name}
              </span>
              {stats.activeWorker.lastLogin && (
                <span
                  className="text-sm ml-3"
                  style={{ color: "var(--text-muted)" }}
                >
                  seit {formatTime(stats.activeWorker.lastLogin)} (
                  {formatDurationSince(stats.activeWorker.lastLogin)})
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
                style={{ color: "var(--accent-green)" }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                />
              </svg>
            </div>
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div
          className="rounded-lg border p-3"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <span
            className="text-xs block mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Total Stunden heute
          </span>
          <span
            className="text-lg font-mono font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            {stats ? formatHours(stats.totalHoursToday) : "---"}h
          </span>
        </div>
        <div
          className="rounded-lg border p-3"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <span
            className="text-xs block mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Mitarbeiter aktiv
          </span>
          <span
            className="text-lg font-mono font-bold"
            style={{
              color: stats?.activeWorker
                ? "var(--accent-green)"
                : "var(--text-muted)",
            }}
          >
            {stats?.activeWorker ? "1" : "0"}
          </span>
        </div>
        <div
          className="rounded-lg border p-3"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <span
            className="text-xs block mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Eintraege heute
          </span>
          <span
            className="text-lg font-mono font-bold"
            style={{ color: "var(--accent-blue)" }}
          >
            {stats?.todayLogs?.length ?? logs.length}
          </span>
        </div>
      </div>

      {/* Daily hours bar chart */}
      {stats?.workerHours && stats.workerHours.length > 0 && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border-color)",
          }}
        >
          <h2
            className="text-sm font-semibold mb-4 uppercase tracking-wider"
            style={{ color: "var(--text-secondary)" }}
          >
            Arbeitsstunden heute
          </h2>
          <div className="space-y-3">
            {stats.workerHours.map((w) => {
              const isAutoLoggedOut = autoLoggedOutWorkers.has(w.workerId);
              const barColor = isAutoLoggedOut
                ? "var(--accent-yellow)"
                : "var(--accent-green)";
              const pct = Math.min((w.hours / maxHours) * 100, 100);

              return (
                <div key={w.workerId} className="flex items-center gap-3">
                  <span
                    className="text-xs font-mono w-28 shrink-0 truncate"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {w.workerName}
                  </span>
                  <div
                    className="flex-1 h-6 rounded overflow-hidden"
                    style={{ backgroundColor: "var(--bg-secondary)" }}
                  >
                    <div
                      className="h-full rounded transition-all duration-500"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: barColor,
                        minWidth: w.hours > 0 ? "4px" : "0",
                      }}
                    />
                  </div>
                  <span
                    className="text-xs font-mono w-12 text-right shrink-0"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {formatHours(w.hours)}h
                  </span>
                  {isAutoLoggedOut && (
                    <span
                      className="text-xs px-1.5 py-0.5 rounded"
                      style={{
                        backgroundColor: "rgba(245,158,11,0.1)",
                        color: "var(--accent-yellow)",
                      }}
                    >
                      Auto
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Live log */}
      <div
        className="rounded-xl border p-5"
        style={{
          backgroundColor: "var(--bg-card)",
          borderColor: "var(--border-color)",
        }}
      >
        <h2
          className="text-sm font-semibold mb-4 uppercase tracking-wider"
          style={{ color: "var(--text-secondary)" }}
        >
          Heutige Eintraege
        </h2>

        {(stats?.todayLogs ?? logs).length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              Noch keine Eintraege heute
            </p>
          </div>
        ) : (
          <div className="space-y-0 max-h-96 overflow-y-auto">
            {(stats?.todayLogs ?? logs).map((log) => (
              <div
                key={log.id}
                className="flex items-center gap-4 py-2.5 border-b last:border-b-0"
                style={{ borderColor: "var(--border-color)" }}
              >
                {/* Action dot */}
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{
                    backgroundColor: actionColors[log.action],
                  }}
                />

                {/* Time */}
                <span
                  className="text-xs font-mono w-12 shrink-0"
                  style={{ color: "var(--text-muted)" }}
                >
                  {formatTime(log.timestamp)}
                </span>

                {/* Name */}
                <span
                  className="text-xs font-mono flex-1 truncate"
                  style={{ color: "var(--text-primary)" }}
                >
                  {log.workerName}
                </span>

                {/* Action badge */}
                <span
                  className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0"
                  style={{
                    backgroundColor: `color-mix(in srgb, ${actionColors[log.action]} 15%, transparent)`,
                    color: actionColors[log.action],
                  }}
                >
                  {actionLabels[log.action]}
                </span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
