"use client";

export interface ScanEvent {
  id: string;
  state: "queued" | "preparing" | "scanning" | "reconstructing" | "completed" | "failed";
  timestamp: string;
  partName?: string;
  duration?: number;
}

const stateColors: Record<ScanEvent["state"], string> = {
  queued: "var(--accent-gray)",
  preparing: "var(--accent-blue)",
  scanning: "var(--accent-yellow)",
  reconstructing: "var(--accent-blue)",
  completed: "var(--accent-green)",
  failed: "var(--accent-red)",
};

interface ScanStateTimelineProps {
  events: ScanEvent[];
}

export default function ScanStateTimeline({ events }: ScanStateTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        No scan events recorded
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {events.map((event, idx) => (
        <div key={event.id} className="flex items-start gap-3">
          {/* Timeline connector */}
          <div className="flex flex-col items-center">
            <span
              className="w-2.5 h-2.5 rounded-full mt-1.5 shrink-0"
              style={{ backgroundColor: stateColors[event.state] }}
            />
            {idx < events.length - 1 && (
              <div className="w-px flex-1 min-h-[20px]" style={{ backgroundColor: "var(--border-color)" }} />
            )}
          </div>

          {/* Event content */}
          <div className="pb-3">
            <div className="flex items-center gap-2">
              <span
                className="text-xs font-mono px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor: `color-mix(in srgb, ${stateColors[event.state]} 15%, transparent)`,
                  color: stateColors[event.state],
                }}
              >
                {event.state}
              </span>
              {event.partName && (
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  {event.partName}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
              {event.duration != null && (
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {event.duration}s
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
