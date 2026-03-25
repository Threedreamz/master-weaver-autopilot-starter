"use client";

import { useEffect, useState, useCallback } from "react";
import type { Worker, TimeTrackingStats } from "@autopilot/types";
import { WorkerList } from "@/components/team/WorkerList";
import { TimeLogView } from "@/components/team/TimeLogView";
import { useWSEvents } from "@/lib/ws-client";
import * as api from "@/lib/api-client";

export default function TeamPage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [stats, setStats] = useState<TimeTrackingStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);
  const [logoutTarget, setLogoutTarget] = useState<string | null>(null);

  const { lastEvent } = useWSEvents({
    filter: ["worker.login", "worker.logout", "worker.auto-logout"],
  });

  const loadData = useCallback(() => {
    api.getWorkers().then(setWorkers).catch(() => {});
    api.getTimeStats().then(setStats).catch(() => {});
  }, []);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const id = setInterval(loadData, 5000);
    return () => clearInterval(id);
  }, [loadData]);

  // React to WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    if (
      lastEvent.type === "worker.login" ||
      lastEvent.type === "worker.logout" ||
      lastEvent.type === "worker.auto-logout"
    ) {
      loadData();
    }
  }, [lastEvent, loadData]);

  const handleLogin = async (id: string) => {
    setError(null);
    try {
      await api.loginWorker(id);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login fehlgeschlagen");
    }
  };

  const handleLogoutRequest = (id: string) => {
    setLogoutTarget(id);
  };

  const confirmLogout = async () => {
    if (!logoutTarget) return;
    setError(null);
    try {
      await api.logoutWorker(logoutTarget);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Abmeldung fehlgeschlagen");
    } finally {
      setLogoutTarget(null);
    }
  };

  const handleAdd = async () => {
    if (!newName.trim()) return;
    setAdding(true);
    setError(null);
    try {
      await api.addWorker(newName.trim());
      setNewName("");
      setShowAddModal(false);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hinzufügen fehlgeschlagen");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (worker: Worker) => {
    setError(null);
    try {
      await api.removeWorker(worker.id);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Entfernen fehlgeschlagen");
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Team</h1>
        <span className="text-sm text-gray-500">Zeiterfassung</span>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-3 bg-red-950 border border-red-800 rounded-xl text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Worker grid */}
      {workers.length === 0 ? (
        <p className="text-center text-gray-500 py-12">
          Noch keine Mitarbeiter. Tippe auf + um einen hinzuzuf&uuml;gen.
        </p>
      ) : (
        <WorkerList
          workers={workers}
          onLogin={handleLogin}
          onLogout={handleLogoutRequest}
          onDelete={handleDelete}
        />
      )}

      {/* Divider */}
      <div className="border-t border-gray-800" />

      {/* Today's summary */}
      <TimeLogView stats={stats} />

      {/* Floating add button */}
      <button
        onClick={() => {
          setNewName("");
          setShowAddModal(true);
        }}
        className="fixed bottom-[calc(var(--nav-height)+24px)] right-6 w-16 h-16 bg-blue-600 text-white text-3xl font-bold rounded-full shadow-lg shadow-blue-600/30 flex items-center justify-center active:bg-blue-700 z-40"
      >
        +
      </button>

      {/* Add worker modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end justify-center">
          <div className="w-full max-w-lg bg-gray-900 rounded-t-2xl p-6 space-y-4 safe-bottom">
            <h2 className="text-xl font-bold">Neuer Mitarbeiter</h2>
            <input
              type="text"
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
              className="w-full min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 min-h-[56px] bg-gray-800 text-gray-300 font-semibold rounded-xl active:bg-gray-700"
              >
                Abbrechen
              </button>
              <button
                onClick={handleAdd}
                disabled={!newName.trim() || adding}
                className={`flex-1 min-h-[56px] font-semibold rounded-xl ${
                  newName.trim() && !adding
                    ? "bg-blue-600 text-white active:bg-blue-700"
                    : "bg-gray-800 text-gray-600 cursor-not-allowed"
                }`}
              >
                {adding ? "Wird hinzugefügt..." : "Hinzufügen"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Logout confirmation modal */}
      {logoutTarget && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-gray-900 rounded-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold">Abmelden?</h2>
            <p className="text-gray-400">
              Soll{" "}
              <span className="text-gray-100 font-semibold">
                &quot;{workers.find((w) => w.id === logoutTarget)?.name}&quot;
              </span>{" "}
              wirklich abgemeldet werden?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setLogoutTarget(null)}
                className="flex-1 min-h-[56px] bg-gray-800 text-gray-300 font-semibold rounded-xl active:bg-gray-700"
              >
                Abbrechen
              </button>
              <button
                onClick={confirmLogout}
                className="flex-1 min-h-[56px] bg-amber-600 text-white font-semibold rounded-xl active:bg-amber-700"
              >
                Abmelden
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
