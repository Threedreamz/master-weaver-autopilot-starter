"use client";

interface MetricBarProps {
  label: string;
  value: number;
  max: number;
  unit?: string;
  thresholds?: { warn: number; critical: number };
}

export default function MetricBar({ label, value, max, unit = "%", thresholds }: MetricBarProps) {
  const pct = Math.min((value / max) * 100, 100);

  let color = "var(--accent-green)";
  if (thresholds) {
    if (value >= thresholds.critical) color = "var(--accent-red)";
    else if (value >= thresholds.warn) color = "var(--accent-yellow)";
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{label}</span>
        <span className="text-xs font-mono" style={{ color }}>
          {value}{unit}
        </span>
      </div>
      <div className="h-1.5 rounded-full" style={{ backgroundColor: "var(--border-color)" }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
