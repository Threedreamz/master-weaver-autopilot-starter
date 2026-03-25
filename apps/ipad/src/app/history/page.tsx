"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ScanState } from "@autopilot/types";
import type { ScanResult } from "@autopilot/types";
import * as api from "@/lib/api-client";

function stateColor(state: ScanState): string {
  switch (state) {
    case ScanState.DONE:
      return "text-green-400";
    case ScanState.ERROR:
      return "text-red-400";
    case ScanState.SCANNING:
    case ScanState.WAIT_COMPLETE:
    case ScanState.EXPORT_STL:
      return "text-blue-400";
    default:
      return "text-gray-400";
  }
}

function stateLabel(state: ScanState): string {
  switch (state) {
    case ScanState.DONE:
      return "Fertig";
    case ScanState.ERROR:
      return "Fehler";
    case ScanState.SCANNING:
      return "Läuft";
    default:
      return state;
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function HistoryPage() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getScans()
      .then(setScans)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Scan-Historie</h1>

      {loading && (
        <p className="text-gray-500 text-center py-12">Laden...</p>
      )}

      {!loading && scans.length === 0 && (
        <p className="text-gray-500 text-center py-12">
          Noch keine Scans durchgeführt.
        </p>
      )}

      <div className="space-y-3">
        {scans.map((scan) => (
          <Link
            key={scan.jobId}
            href={`/scan/${scan.jobId}`}
            className="block p-4 bg-gray-900 border border-gray-800 rounded-xl active:bg-gray-800"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">{scan.partId}</p>
                <p className="text-sm text-gray-500 mt-0.5">
                  {formatDate(scan.startedAt)}
                  {scan.completedAt && ` — ${formatDate(scan.completedAt)}`}
                </p>
              </div>
              <div className="text-right">
                <span className={`font-semibold ${stateColor(scan.state)}`}>
                  {stateLabel(scan.state)}
                </span>
                {scan.deviationReport && (
                  <p className="text-xs mt-1">
                    <span
                      className={
                        scan.deviationReport.withinTolerance
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {scan.deviationReport.withinTolerance ? "IO" : "NIO"}
                    </span>
                    {" "}
                    <span className="text-gray-500">
                      +/-{scan.deviationReport.avgDeviation.toFixed(3)}mm
                    </span>
                  </p>
                )}
              </div>
            </div>

            {scan.stlPath && (
              <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
                  <path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                </svg>
                STL verfügbar
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
