"use client";

import type { ScanProfile } from "@autopilot/types";

interface ProfileSelectorProps {
  profiles: ScanProfile[];
  selectedId: string | null;
  onSelect: (profile: ScanProfile) => void;
}

export function ProfileSelector({
  profiles,
  selectedId,
  onSelect,
}: ProfileSelectorProps) {
  if (profiles.length === 0) {
    return (
      <div className="p-4 bg-gray-900 rounded-xl border border-gray-800 text-gray-500 text-center">
        Keine Profile vorhanden
      </div>
    );
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
      {profiles.map((profile) => (
        <button
          key={profile.id}
          onClick={() => onSelect(profile)}
          className={`flex-shrink-0 min-w-[160px] min-h-[80px] p-4 rounded-xl border-2 transition-colors text-left ${
            selectedId === profile.id
              ? "border-blue-500 bg-blue-950"
              : "border-gray-700 bg-gray-900 active:bg-gray-800"
          }`}
        >
          <p className="font-semibold text-sm truncate">{profile.name}</p>
          <p className="text-xs text-gray-400 mt-1">
            {profile.magnification} | {profile.voltage ?? "—"}kV |{" "}
            {profile.ampere ?? "—"}uA
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {profile.rotationDegrees}&deg;
          </p>
        </button>
      ))}
    </div>
  );
}
