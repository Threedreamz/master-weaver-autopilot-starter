"use client";

import Link from "next/link";

export type StatusLevel = "online" | "degraded" | "offline" | "unknown";

interface StatusPanelProps {
  title: string;
  href: string;
  status: StatusLevel;
  lastUpdated: string | null;
  children: React.ReactNode;
}

const statusConfig: Record<StatusLevel, { color: string; label: string; dotClass: string }> = {
  online: { color: "var(--accent-green)", label: "Online", dotClass: "status-dot-green" },
  degraded: { color: "var(--accent-yellow)", label: "Degraded", dotClass: "status-dot-yellow" },
  offline: { color: "var(--accent-red)", label: "Offline", dotClass: "status-dot-red" },
  unknown: { color: "var(--accent-gray)", label: "Unknown", dotClass: "" },
};

export default function StatusPanel({ title, href, status, lastUpdated, children }: StatusPanelProps) {
  const cfg = statusConfig[status];

  return (
    <Link
      href={href}
      className="block rounded-xl border p-5 transition-colors"
      style={{
        backgroundColor: "var(--bg-card)",
        borderColor: "var(--border-color)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--bg-card-hover)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "var(--bg-card)";
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
          {title}
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: cfg.color }}>{cfg.label}</span>
          <span
            className={`inline-block w-2.5 h-2.5 rounded-full ${cfg.dotClass}`}
            style={{ backgroundColor: cfg.color }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {children}
      </div>

      {/* Footer */}
      {lastUpdated && (
        <p className="text-xs mt-4 pt-3 border-t" style={{ color: "var(--text-muted)", borderColor: "var(--border-color)" }}>
          Updated {lastUpdated}
        </p>
      )}
    </Link>
  );
}
