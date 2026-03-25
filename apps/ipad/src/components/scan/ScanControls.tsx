"use client";

import { ScanState } from "@autopilot/types";

interface ScanControlsProps {
  state: ScanState;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
}

export function ScanControls({
  state,
  onStart,
  onStop,
  disabled = false,
}: ScanControlsProps) {
  const isActive =
    state === ScanState.SCANNING ||
    state === ScanState.TUBE_ON ||
    state === ScanState.ROTATE_PREVIEW ||
    state === ScanState.GREEN_BOX ||
    state === ScanState.ERROR_CORRECT ||
    state === ScanState.WAIT_COMPLETE ||
    state === ScanState.EXPORT_STL;

  const canStart =
    state === ScanState.IDLE || state === ScanState.PROFILE_SELECT;

  return (
    <div className="flex gap-4">
      {/* START SCAN */}
      <button
        onClick={onStart}
        disabled={disabled || !canStart}
        className={`flex-1 min-h-[72px] rounded-2xl text-xl font-bold transition-colors ${
          canStart && !disabled
            ? "bg-green-600 text-white active:bg-green-700"
            : "bg-gray-800 text-gray-600 cursor-not-allowed"
        }`}
      >
        SCAN STARTEN
      </button>

      {/* EMERGENCY STOP */}
      <button
        onClick={onStop}
        disabled={!isActive}
        className={`min-w-[72px] min-h-[72px] rounded-2xl text-lg font-bold transition-colors ${
          isActive
            ? "bg-red-600 text-white active:bg-red-700 ring-2 ring-red-400"
            : "bg-gray-800 text-gray-600 cursor-not-allowed"
        }`}
      >
        STOP
      </button>
    </div>
  );
}
