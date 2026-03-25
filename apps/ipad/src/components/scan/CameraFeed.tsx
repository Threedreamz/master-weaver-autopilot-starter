"use client";

import { useState } from "react";
import { streamUrl } from "@/lib/pi-client";

interface CameraFeedProps {
  cameraId?: number;
  className?: string;
  compact?: boolean;
}

export function CameraFeed({
  cameraId = 0,
  className = "",
  compact = false,
}: CameraFeedProps) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div
        className={`flex items-center justify-center bg-gray-900 rounded-xl border border-gray-800 ${
          compact ? "h-32" : "h-64"
        } ${className}`}
      >
        <div className="text-center text-gray-500">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-8 h-8 mx-auto mb-2">
            <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p className="text-sm">Kamera {cameraId} offline</p>
          <button
            onClick={() => setError(false)}
            className="mt-2 text-xs text-blue-400 underline min-h-[48px]"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`relative overflow-hidden bg-gray-900 rounded-xl border border-gray-800 ${
        compact ? "h-32" : "h-64"
      } ${className}`}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={streamUrl(cameraId)}
        alt={`Kamera ${cameraId}`}
        className="w-full h-full object-contain"
        onError={() => setError(true)}
      />
      <div className="absolute top-2 left-2 bg-black/60 text-xs text-gray-300 px-2 py-1 rounded">
        CAM {cameraId}
      </div>
    </div>
  );
}
