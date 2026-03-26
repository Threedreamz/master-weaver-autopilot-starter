"use client";

import { useEffect, useState, useCallback } from "react";
import { ScanState } from "@autopilot/types";
import type { ScanProfile, SystemStatus } from "@autopilot/types";
import { StatusIndicator } from "@/components/scan/StatusIndicator";
import { ScanControls } from "@/components/scan/ScanControls";
import { CameraFeed } from "@/components/scan/CameraFeed";
import { ProfileSelector } from "@/components/scan/ProfileSelector";
import { ErrorDisplay } from "@/components/scan/ErrorDisplay";
import { useWSEvents, type ConnectionState } from "@/lib/ws-client";
import * as api from "@/lib/api-client";

function ConnectionBadge({ state }: { state: ConnectionState }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-3 h-3 rounded-full ${
          state === "connected"
            ? "bg-green-500"
            : state === "connecting"
              ? "bg-yellow-500 animate-pulse"
              : "bg-red-500"
        }`}
      />
      <span className="text-xs text-gray-400">
        {state === "connected"
          ? "Verbunden"
          : state === "connecting"
            ? "Verbinde..."
            : "Offline"}
      </span>
    </div>
  );
}

export default function HomePage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [profiles, setProfiles] = useState<ScanProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<ScanProfile | null>(null);
  const [scanState, setScanState] = useState<ScanState>(ScanState.IDLE);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { connectionState, lastEvent } = useWSEvents();

  // Load initial data
  useEffect(() => {
    api.getStatus().then(setStatus).catch(() => {});
    api.getProfiles().then(setProfiles).catch(() => {});
  }, []);

  // Process WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    switch (lastEvent.type) {
      case "scan.state_change":
        setScanState((lastEvent.data as { state: ScanState }).state);
        break;
      case "system.status":
        setStatus(lastEvent.data as SystemStatus);
        setScanState((lastEvent.data as SystemStatus).currentScanState);
        break;
      case "scan.error":
      case "system.error":
        setError((lastEvent.data as { message: string }).message);
        break;
    }
  }, [lastEvent]);

  // Sync scan state from status
  useEffect(() => {
    if (status) setScanState(status.currentScanState);
  }, [status]);

  const handleStart = useCallback(async () => {
    if (!selectedProfile) {
      setError("Bitte zuerst ein Profil wählen");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await api.selectProfile(selectedProfile.name);
      await api.startScan({
        profileId: selectedProfile.id,
        partId: `scan-${Date.now()}`,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }, [selectedProfile]);

  const handleStop = useCallback(async () => {
    setLoading(true);
    try {
      await api.stopScan();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">CT Scanner</h1>
        <ConnectionBadge state={connectionState} />
      </div>

      {/* Offline banner */}
      {connectionState === "disconnected" && (
        <div className="p-3 bg-red-950 border border-red-800 rounded-xl text-center text-red-300 text-sm font-semibold">
          Verbindung zum CT-PC verloren
        </div>
      )}

      {/* Status indicator */}
      <StatusIndicator state={scanState} className="w-full" />

      {/* Error display */}
      <ErrorDisplay
        errorBoxes={status?.errorBoxes}
        errorMessage={error ?? undefined}
      />

      {/* Profile selector */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 mb-2">
          Scan-Profil
        </h2>
        <ProfileSelector
          profiles={profiles}
          selectedId={selectedProfile?.id ?? null}
          onSelect={setSelectedProfile}
        />
      </div>

      {/* Scan controls */}
      <ScanControls
        state={scanState}
        onStart={handleStart}
        onStop={handleStop}
        disabled={loading || connectionState !== "connected"}
      />

      {/* Camera feeds */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 mb-2">Kameras</h2>
        <div className="grid grid-cols-2 gap-3">
          <CameraFeed cameraId={0} compact />
          <CameraFeed cameraId={1} compact />
        </div>
      </div>

      {/* System status bar */}
      {status && (
        <div className="flex items-center gap-4 text-xs text-gray-500 px-2">
          <span>
            Röhre:{" "}
            <span
              className={
                status.tubeStatus.on ? "text-yellow-400" : "text-gray-600"
              }
            >
              {status.tubeStatus.on ? "AN" : "AUS"}
            </span>
          </span>
          <span>
            Bereit:{" "}
            <span
              className={
                status.tubeStatus.ready ? "text-green-400" : "text-gray-600"
              }
            >
              {status.tubeStatus.ready ? "Ja" : "Nein"}
            </span>
          </span>
          <span>
            Profil-Button:{" "}
            <span
              className={
                status.profileButtonActive ? "text-green-400" : "text-gray-600"
              }
            >
              {status.profileButtonActive ? "Aktiv" : "Inaktiv"}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
