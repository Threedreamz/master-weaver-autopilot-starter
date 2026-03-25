"use client";

import { useState, useEffect, useRef } from "react";
import type { Worker } from "@autopilot/types";

function formatTimeSince(isoDate: string): string {
  const start = new Date(isoDate).getTime();
  const now = Date.now();
  const diff = Math.max(0, now - start);
  const hours = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  return `${hours.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}`;
}

function LiveTimer({ since }: { since: string }) {
  const [display, setDisplay] = useState(() => formatTimeSince(since));

  useEffect(() => {
    const id = setInterval(() => setDisplay(formatTimeSince(since)), 10000);
    return () => clearInterval(id);
  }, [since]);

  return <span>{display}</span>;
}

interface WorkerListProps {
  workers: Worker[];
  onLogin: (id: string) => void;
  onLogout: (id: string) => void;
  onDelete: (worker: Worker) => void;
}

export function WorkerList({ workers, onLogin, onLogout, onDelete }: WorkerListProps) {
  const [longPressTarget, setLongPressTarget] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleTouchStart = (worker: Worker) => {
    timerRef.current = setTimeout(() => {
      setLongPressTarget(worker.id);
    }, 600);
  };

  const handleTouchEnd = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const handleTap = (worker: Worker) => {
    if (longPressTarget) return;
    if (worker.active) {
      onLogout(worker.id);
    } else {
      onLogin(worker.id);
    }
  };

  const colors = [
    "bg-blue-600",
    "bg-purple-600",
    "bg-teal-600",
    "bg-orange-600",
    "bg-pink-600",
    "bg-indigo-600",
    "bg-cyan-600",
    "bg-rose-600",
  ];

  return (
    <>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-4">
        {workers.map((worker, idx) => {
          const initial = worker.name.charAt(0).toUpperCase();
          const colorClass = colors[idx % colors.length];
          const isActive = worker.active;

          return (
            <button
              key={worker.id}
              onClick={() => handleTap(worker)}
              onTouchStart={() => handleTouchStart(worker)}
              onTouchEnd={handleTouchEnd}
              onTouchCancel={handleTouchEnd}
              className="flex flex-col items-center gap-2 no-select"
            >
              {/* Avatar */}
              <div
                className={`relative w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold text-white ${
                  isActive ? colorClass : "bg-gray-700"
                } ${isActive ? "ring-4 ring-green-500" : ""}`}
              >
                {isActive && (
                  <div className="absolute inset-0 rounded-full ring-4 ring-green-500 animate-pulse" />
                )}
                {initial}
              </div>
              {/* Name */}
              <span className={`text-sm font-medium truncate max-w-[80px] ${isActive ? "text-green-400" : "text-gray-400"}`}>
                {worker.name}
              </span>
              {/* Status */}
              {isActive && worker.lastLogin && (
                <span className="text-xs text-green-500">
                  Eingeloggt seit <LiveTimer since={worker.lastLogin} />
                </span>
              )}
              {!isActive && (
                <span className="text-xs text-gray-600">Abgemeldet</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Long-press delete confirmation */}
      {longPressTarget && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-gray-900 rounded-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold">Mitarbeiter entfernen?</h2>
            <p className="text-gray-400">
              Soll{" "}
              <span className="text-gray-100 font-semibold">
                &quot;{workers.find((w) => w.id === longPressTarget)?.name}&quot;
              </span>{" "}
              wirklich entfernt werden?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setLongPressTarget(null)}
                className="flex-1 min-h-[56px] bg-gray-800 text-gray-300 font-semibold rounded-xl active:bg-gray-700"
              >
                Abbrechen
              </button>
              <button
                onClick={() => {
                  const w = workers.find((w) => w.id === longPressTarget);
                  if (w) onDelete(w);
                  setLongPressTarget(null);
                }}
                className="flex-1 min-h-[56px] bg-red-600 text-white font-semibold rounded-xl active:bg-red-700"
              >
                Entfernen
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
