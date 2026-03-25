"use client";

import type { TimeTrackingStats } from "@autopilot/types";

interface TimeLogViewProps {
  stats: TimeTrackingStats | null;
}

export function TimeLogView({ stats }: TimeLogViewProps) {
  if (!stats || stats.workerHours.length === 0) {
    return (
      <div className="text-center text-gray-600 py-6 text-sm">
        Heute noch keine Zeiteintr&auml;ge.
      </div>
    );
  }

  const maxHours = Math.max(...stats.workerHours.map((w) => w.hours), 1);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Heute</h2>
        <span className="text-sm text-gray-400">
          Gesamt: {stats.totalHoursToday.toFixed(1)}h
        </span>
      </div>

      {/* Worker hour bars */}
      <div className="space-y-2">
        {stats.workerHours.map((entry) => {
          const pct = Math.min((entry.hours / maxHours) * 100, 100);
          const isActive = stats.activeWorker?.id === entry.workerId;
          const barColor = isActive ? "bg-green-500" : "bg-gray-600";

          return (
            <div key={entry.workerId} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className={isActive ? "text-green-400 font-semibold" : "text-gray-300"}>
                  {entry.workerName}
                </span>
                <span className="text-gray-400">
                  {entry.hours.toFixed(1)}h
                </span>
              </div>
              <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent log entries */}
      {stats.todayLogs.length > 0 && (
        <div className="mt-4 space-y-1">
          <h3 className="text-sm font-semibold text-gray-500 mb-2">Letzte Eintr&auml;ge</h3>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {stats.todayLogs
              .slice()
              .reverse()
              .slice(0, 10)
              .map((log) => {
                const time = new Date(log.timestamp).toLocaleTimeString("de-DE", {
                  hour: "2-digit",
                  minute: "2-digit",
                });
                const actionLabel =
                  log.action === "login"
                    ? "Eingeloggt"
                    : log.action === "logout"
                      ? "Abgemeldet"
                      : "Auto-Abmeldung";
                const actionColor =
                  log.action === "login"
                    ? "text-green-500"
                    : log.action === "auto-logout"
                      ? "text-amber-500"
                      : "text-gray-500";

                return (
                  <div
                    key={log.id}
                    className="flex items-center justify-between text-xs py-1 px-2 rounded bg-gray-900"
                  >
                    <span className="text-gray-400">{time}</span>
                    <span className="text-gray-300 font-medium">{log.workerName}</span>
                    <span className={actionColor}>{actionLabel}</span>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
