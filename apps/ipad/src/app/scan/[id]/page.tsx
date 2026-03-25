"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ScanState } from "@autopilot/types";
import type { ScanResult } from "@autopilot/types";
import { StatusIndicator } from "@/components/scan/StatusIndicator";
import { StateTimeline } from "@/components/scan/StateTimeline";
import { CameraFeed } from "@/components/scan/CameraFeed";
import { ErrorDisplay } from "@/components/scan/ErrorDisplay";
import { useWSEvents } from "@/lib/ws-client";
import * as api from "@/lib/api-client";

export default function ActiveScanPage() {
  const params = useParams();
  const router = useRouter();
  const scanId = params.id as string;

  const [scan, setScan] = useState<ScanResult | null>(null);
  const [scanState, setScanState] = useState<ScanState>(ScanState.SCANNING);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const { lastEvent, connectionState } = useWSEvents({
    filter: ["scan.state_change", "scan.progress", "scan.error", "scan.complete"],
  });

  // Load scan data
  useEffect(() => {
    api
      .getScan(scanId)
      .then((s) => {
        setScan(s);
        setScanState(s.state);
      })
      .catch(() => {});
  }, [scanId]);

  // Process WS events
  useEffect(() => {
    if (!lastEvent) return;
    switch (lastEvent.type) {
      case "scan.state_change":
        setScanState((lastEvent.data as { state: ScanState }).state);
        break;
      case "scan.error":
        setScanState(ScanState.ERROR);
        setErrorMsg((lastEvent.data as { message: string }).message);
        break;
      case "scan.complete":
        setScanState(ScanState.DONE);
        break;
    }
  }, [lastEvent]);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await api.stopScan();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Abbruch fehlgeschlagen");
    } finally {
      setCancelling(false);
    }
  };

  const isDone = scanState === ScanState.DONE;
  const isError = scanState === ScanState.ERROR;
  const isActive = !isDone && !isError;

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Aktiver Scan</h1>
          <p className="text-sm text-gray-500">ID: {scanId}</p>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              connectionState === "connected"
                ? "bg-green-500"
                : "bg-red-500"
            }`}
          />
        </div>
      </div>

      {/* Status */}
      <StatusIndicator state={scanState} className="w-full" />

      {/* Timeline */}
      <StateTimeline currentState={scanState} />

      {/* Camera feed - full width during scan */}
      <CameraFeed cameraId={0} />

      {/* Error */}
      {errorMsg && <ErrorDisplay errorMessage={errorMsg} />}

      {/* Actions */}
      <div className="flex gap-4">
        {isActive && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="flex-1 min-h-[64px] bg-red-600 text-white text-xl font-bold rounded-2xl active:bg-red-700"
          >
            {cancelling ? "Abbrechen..." : "SCAN ABBRECHEN"}
          </button>
        )}
        {(isDone || isError) && (
          <button
            onClick={() => router.push("/")}
            className="flex-1 min-h-[64px] bg-gray-800 text-gray-200 text-xl font-bold rounded-2xl active:bg-gray-700"
          >
            Zurück
          </button>
        )}
        {isDone && scan?.stlPath && (
          <button
            onClick={() => {
              // trigger STL download
              window.open(
                `${window.location.protocol}//${window.location.hostname}:4692/api/scans/${scanId}/download-stl`,
                "_blank"
              );
            }}
            className="flex-1 min-h-[64px] bg-green-600 text-white text-xl font-bold rounded-2xl active:bg-green-700"
          >
            STL LADEN
          </button>
        )}
      </div>
    </div>
  );
}
