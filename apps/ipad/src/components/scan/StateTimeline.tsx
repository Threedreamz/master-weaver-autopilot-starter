"use client";

import { ScanState } from "@autopilot/types";

/** Ordered workflow states for the timeline */
const TIMELINE_STATES: { state: ScanState; short: string }[] = [
  { state: ScanState.IDLE, short: "Bereit" },
  { state: ScanState.PROFILE_SELECT, short: "Profil" },
  { state: ScanState.TUBE_ON, short: "Röhre" },
  { state: ScanState.ROTATE_PREVIEW, short: "Vorschau" },
  { state: ScanState.GREEN_BOX, short: "Grün" },
  { state: ScanState.ERROR_CORRECT, short: "Korrektur" },
  { state: ScanState.SCANNING, short: "Scan" },
  { state: ScanState.WAIT_COMPLETE, short: "Warten" },
  { state: ScanState.EXPORT_STL, short: "Export" },
  { state: ScanState.DONE, short: "Fertig" },
];

interface StateTimelineProps {
  currentState: ScanState;
  className?: string;
}

export function StateTimeline({ currentState, className = "" }: StateTimelineProps) {
  const currentIdx = TIMELINE_STATES.findIndex(
    (s) => s.state === currentState
  );
  const isError = currentState === ScanState.ERROR;

  return (
    <div className={`w-full overflow-x-auto ${className}`}>
      <div className="flex items-center gap-1 min-w-[700px] px-2">
        {TIMELINE_STATES.map((step, idx) => {
          const isPast = idx < currentIdx;
          const isCurrent = idx === currentIdx && !isError;
          const isFuture = idx > currentIdx || isError;

          return (
            <div key={step.state} className="flex items-center flex-1">
              {/* Step dot + label */}
              <div className="flex flex-col items-center gap-1 min-w-[56px]">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    isPast
                      ? "bg-green-600 text-white"
                      : isCurrent
                        ? "bg-blue-500 text-white ring-2 ring-blue-300"
                        : "bg-gray-700 text-gray-500"
                  }`}
                >
                  {isPast ? "\u2713" : idx + 1}
                </div>
                <span
                  className={`text-[10px] leading-tight text-center ${
                    isCurrent
                      ? "text-blue-400 font-semibold"
                      : isPast
                        ? "text-green-400"
                        : "text-gray-600"
                  }`}
                >
                  {step.short}
                </span>
              </div>

              {/* Connector line */}
              {idx < TIMELINE_STATES.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-1 ${
                    isPast ? "bg-green-600" : "bg-gray-700"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {isError && (
        <div className="mt-3 px-2 py-2 bg-red-900/50 border border-red-800 rounded-xl text-center">
          <span className="text-red-300 font-semibold text-sm">
            Fehler aufgetreten
          </span>
        </div>
      )}
    </div>
  );
}
