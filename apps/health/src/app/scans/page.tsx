"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import ScanStateTimeline, { type ScanEvent } from "@/components/ScanStateTimeline";
import { initScanTracker, getScanHistory, disconnectScanTracker } from "@/lib/scan-tracker";

type FilterStatus = "all" | ScanEvent["state"];

const statusLabels: Record<FilterStatus, string> = {
  all: "Alle",
  queued: "Warteschlange",
  preparing: "Vorbereitung",
  scanning: "Scannen",
  reconstructing: "Rekonstruktion",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
};

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

function ScanCard({ scan, isActive }: { scan: ScanEvent; isActive: boolean }) {
  const stateColors: Record<ScanEvent["state"], string> = {
    queued: "var(--accent-gray)",
    preparing: "var(--accent-blue)",
    scanning: "var(--accent-yellow)",
    reconstructing: "var(--accent-blue)",
    completed: "var(--accent-green)",
    failed: "var(--accent-red)",
  };

  const color = stateColors[scan.state];

  return (
    <div
      className="rounded-lg border p-4 transition-colors"
      style={{
        backgroundColor: isActive ? "var(--bg-card-hover)" : "var(--bg-card)",
        borderColor: isActive ? color : "var(--border-color)",
        borderLeftWidth: isActive ? "3px" : "1px",
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isActive && (
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                scan.state === "scanning" ? "status-dot-yellow"
                  : scan.state === "preparing" ? "status-dot-green"
                  : ""
              }`}
              style={{ backgroundColor: color }}
            />
          )}
          <span className="text-sm font-mono font-semibold" style={{ color: "var(--text-primary)" }}>
            {scan.partName ?? scan.id}
          </span>
        </div>
        <span
          className="text-xs font-mono px-2 py-0.5 rounded"
          style={{
            backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
            color,
          }}
        >
          {statusLabels[scan.state] ?? scan.state}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
        <span className="font-mono">
          {new Date(scan.timestamp).toLocaleString("de-DE", {
            day: "2-digit",
            month: "2-digit",
            year: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })}
        </span>
        {scan.duration != null && (
          <span className="font-mono">
            Dauer: {formatDuration(scan.duration)}
          </span>
        )}
      </div>
    </div>
  );
}

export default function ScansPage() {
  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [dateFilter, setDateFilter] = useState<string>("");
  const [refreshCountdown, setRefreshCountdown] = useState(5);

  // Initialize WebSocket tracker and poll for history
  useEffect(() => {
    initScanTracker();

    const load = () => {
      setEvents(getScanHistory());
      setRefreshCountdown(5);
    };
    load();
    const interval = setInterval(load, 5000);

    return () => {
      clearInterval(interval);
      disconnectScanTracker();
    };
  }, []);

  // Countdown timer for visual feedback
  useEffect(() => {
    const timer = setInterval(() => {
      setRefreshCountdown((c) => (c > 0 ? c - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Separate events by category
  const activeScans = useMemo(
    () => events.filter((e) => e.state === "scanning" || e.state === "preparing" || e.state === "reconstructing"),
    [events]
  );

  const queuedScans = useMemo(
    () => events.filter((e) => e.state === "queued"),
    [events]
  );

  const completedScans = useMemo(
    () => events.filter((e) => e.state === "completed" || e.state === "failed"),
    [events]
  );

  // Filtered events for the timeline/history
  const filtered = useMemo(() => {
    return events.filter((e) => {
      if (filter !== "all" && e.state !== filter) return false;
      if (dateFilter) {
        const eventDate = new Date(e.timestamp).toISOString().split("T")[0];
        if (eventDate !== dateFilter) return false;
      }
      return true;
    });
  }, [events, filter, dateFilter]);

  const statuses: FilterStatus[] = ["all", "queued", "preparing", "scanning", "reconstructing", "completed", "failed"];

  // Stats
  const totalCompleted = events.filter((e) => e.state === "completed").length;
  const totalFailed = events.filter((e) => e.state === "failed").length;
  const avgDuration = useMemo(() => {
    const withDuration = completedScans.filter((e) => e.duration != null);
    if (withDuration.length === 0) return null;
    const sum = withDuration.reduce((acc, e) => acc + (e.duration ?? 0), 0);
    return Math.round(sum / withDuration.length);
  }, [completedScans]);

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
            Scan-Warteschlange & Historie
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Echtzeit-Uebersicht aller Scan-Vorgaenge
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full status-dot-green"
            style={{ backgroundColor: "var(--accent-green)" }}
          />
          <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
            Auto-Refresh in {refreshCountdown}s
          </span>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="rounded-lg border p-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}>
          <span className="text-xs block mb-1" style={{ color: "var(--text-muted)" }}>Gesamt</span>
          <span className="text-lg font-mono font-bold" style={{ color: "var(--text-primary)" }}>
            {events.length}
          </span>
        </div>
        <div className="rounded-lg border p-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}>
          <span className="text-xs block mb-1" style={{ color: "var(--text-muted)" }}>Aktiv</span>
          <span className="text-lg font-mono font-bold" style={{ color: "var(--accent-yellow)" }}>
            {activeScans.length}
          </span>
        </div>
        <div className="rounded-lg border p-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}>
          <span className="text-xs block mb-1" style={{ color: "var(--text-muted)" }}>Warteschlange</span>
          <span className="text-lg font-mono font-bold" style={{ color: "var(--accent-blue)" }}>
            {queuedScans.length}
          </span>
        </div>
        <div className="rounded-lg border p-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}>
          <span className="text-xs block mb-1" style={{ color: "var(--text-muted)" }}>Abgeschlossen</span>
          <span className="text-lg font-mono font-bold" style={{ color: "var(--accent-green)" }}>
            {totalCompleted}
          </span>
        </div>
        <div className="rounded-lg border p-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}>
          <span className="text-xs block mb-1" style={{ color: "var(--text-muted)" }}>Fehlgeschlagen</span>
          <span className="text-lg font-mono font-bold" style={{ color: "var(--accent-red)" }}>
            {totalFailed}
          </span>
        </div>
      </div>

      {/* Active scan with real-time timeline */}
      {activeScans.length > 0 && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--accent-yellow)",
            borderWidth: "1px",
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <span
              className="w-2.5 h-2.5 rounded-full status-dot-yellow"
              style={{ backgroundColor: "var(--accent-yellow)" }}
            />
            <h2 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent-yellow)" }}>
              Aktive Scans ({activeScans.length})
            </h2>
          </div>

          <div className="space-y-3 mb-4">
            {activeScans.map((scan) => (
              <ScanCard key={scan.id} scan={scan} isActive={true} />
            ))}
          </div>

          {/* Real-time state timeline for active scans */}
          <div className="pt-4 border-t" style={{ borderColor: "var(--border-color)" }}>
            <h3 className="text-xs font-semibold mb-3 uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Echtzeit-Zustandsverlauf
            </h3>
            <ScanStateTimeline events={activeScans} />
          </div>
        </div>
      )}

      {/* Queued scans */}
      {queuedScans.length > 0 && (
        <div
          className="rounded-xl border p-5 mb-6"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
            Warteschlange ({queuedScans.length})
          </h2>
          <div className="space-y-2">
            {queuedScans.map((scan) => (
              <ScanCard key={scan.id} scan={scan} isActive={false} />
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div
        className="rounded-xl border p-5 mb-6"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-color)" }}
      >
        <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
          Scan-Historie
        </h2>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <div className="flex gap-1 flex-wrap">
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className="px-2.5 py-1 text-xs rounded-md transition-colors"
                style={{
                  backgroundColor: filter === s ? "var(--accent-blue)" : "var(--bg-secondary)",
                  color: filter === s ? "#fff" : "var(--text-secondary)",
                  border: `1px solid ${filter === s ? "var(--accent-blue)" : "var(--border-color)"}`,
                }}
              >
                {statusLabels[s]}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="px-2.5 py-1 text-xs rounded-md"
              style={{
                backgroundColor: "var(--bg-secondary)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-color)",
                colorScheme: "dark",
              }}
            />
            {dateFilter && (
              <button
                onClick={() => setDateFilter("")}
                className="px-2 py-1 text-xs rounded-md transition-colors"
                style={{ color: "var(--accent-red)" }}
              >
                Datum loeschen
              </button>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-6 mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Angezeigt: {filtered.length}</span>
          {avgDuration != null && (
            <span>Durchschn. Dauer: {formatDuration(avgDuration)}</span>
          )}
          <span style={{ color: "var(--accent-green)" }}>
            IO: {totalCompleted}
          </span>
          <span style={{ color: "var(--accent-red)" }}>
            NIO: {totalFailed}
          </span>
        </div>

        {/* History list */}
        {filtered.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              {events.length === 0
                ? "Noch keine Scan-Ereignisse vorhanden"
                : "Keine Ergebnisse fuer den gewaehlten Filter"}
            </p>
          </div>
        ) : (
          <div className="space-y-0">
            {filtered
              .slice()
              .reverse()
              .map((scan) => {
                const isIO = scan.state === "completed";
                const isNIO = scan.state === "failed";

                return (
                  <div
                    key={scan.id}
                    className="flex items-center gap-4 py-3 border-b last:border-b-0"
                    style={{ borderColor: "var(--border-color)" }}
                  >
                    {/* Status dot */}
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{
                        backgroundColor:
                          scan.state === "completed" ? "var(--accent-green)"
                            : scan.state === "failed" ? "var(--accent-red)"
                            : scan.state === "scanning" ? "var(--accent-yellow)"
                            : scan.state === "queued" ? "var(--accent-gray)"
                            : "var(--accent-blue)",
                      }}
                    />

                    {/* Name */}
                    <span className="text-xs font-mono flex-1 truncate" style={{ color: "var(--text-primary)" }}>
                      {scan.partName ?? scan.id}
                    </span>

                    {/* State badge */}
                    <span
                      className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0"
                      style={{
                        backgroundColor:
                          scan.state === "completed" ? "rgba(34,197,94,0.1)"
                            : scan.state === "failed" ? "rgba(239,68,68,0.1)"
                            : "var(--bg-secondary)",
                        color:
                          scan.state === "completed" ? "var(--accent-green)"
                            : scan.state === "failed" ? "var(--accent-red)"
                            : "var(--text-muted)",
                      }}
                    >
                      {isIO ? "IO" : isNIO ? "NIO" : statusLabels[scan.state] ?? scan.state}
                    </span>

                    {/* Duration */}
                    <span className="text-xs font-mono w-16 text-right shrink-0" style={{ color: "var(--text-muted)" }}>
                      {scan.duration != null ? formatDuration(scan.duration) : "---"}
                    </span>

                    {/* Timestamp */}
                    <span className="text-xs font-mono shrink-0" style={{ color: "var(--text-muted)" }}>
                      {new Date(scan.timestamp).toLocaleString("de-DE", {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
}
