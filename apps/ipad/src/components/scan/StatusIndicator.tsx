"use client";

import { ScanState } from "@autopilot/types";

const stateConfig: Record<
  ScanState,
  { label: string; color: string; bg: string }
> = {
  [ScanState.IDLE]: { label: "Bereit", color: "text-gray-300", bg: "bg-gray-700" },
  [ScanState.PROFILE_SELECT]: { label: "Profil wählen", color: "text-blue-300", bg: "bg-blue-900" },
  [ScanState.TUBE_ON]: { label: "Röhre aktiv", color: "text-yellow-300", bg: "bg-yellow-900" },
  [ScanState.ROTATE_PREVIEW]: { label: "Vorschau", color: "text-blue-300", bg: "bg-blue-900" },
  [ScanState.GREEN_BOX]: { label: "Grüner Bereich", color: "text-green-300", bg: "bg-green-900" },
  [ScanState.ERROR_CORRECT]: { label: "Fehlerkorrektur", color: "text-yellow-300", bg: "bg-yellow-900" },
  [ScanState.SCANNING]: { label: "Scan läuft", color: "text-blue-300", bg: "bg-blue-900" },
  [ScanState.WAIT_COMPLETE]: { label: "Warte...", color: "text-blue-300", bg: "bg-blue-900" },
  [ScanState.EXPORT_STL]: { label: "STL Export", color: "text-blue-300", bg: "bg-blue-900" },
  [ScanState.ANALYSE]: { label: "Analyse", color: "text-blue-300", bg: "bg-blue-900" },
  [ScanState.DONE]: { label: "Fertig", color: "text-green-300", bg: "bg-green-900" },
  [ScanState.ERROR]: { label: "Fehler", color: "text-red-300", bg: "bg-red-900" },
};

interface StatusIndicatorProps {
  state: ScanState;
  className?: string;
}

export function StatusIndicator({ state, className = "" }: StatusIndicatorProps) {
  const config = stateConfig[state] ?? stateConfig[ScanState.IDLE];

  return (
    <div
      className={`flex items-center justify-center rounded-2xl px-8 py-6 ${config.bg} ${className}`}
    >
      <div className="flex items-center gap-4">
        <div
          className={`w-5 h-5 rounded-full animate-pulse ${
            state === ScanState.SCANNING
              ? "bg-blue-400"
              : state === ScanState.ERROR
                ? "bg-red-400"
                : state === ScanState.DONE
                  ? "bg-green-400"
                  : "bg-gray-400"
          }`}
        />
        <span className={`text-2xl font-bold ${config.color}`}>
          {config.label}
        </span>
      </div>
    </div>
  );
}
