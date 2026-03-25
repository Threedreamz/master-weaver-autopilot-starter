"use client";

import { useEffect, useState, useCallback } from "react";
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

function stateBgColor(state: ScanState): string {
  switch (state) {
    case ScanState.DONE:
      return "bg-green-900/50 border-green-800";
    case ScanState.ERROR:
      return "bg-red-900/50 border-red-800";
    case ScanState.SCANNING:
    case ScanState.WAIT_COMPLETE:
    case ScanState.EXPORT_STL:
      return "bg-blue-900/50 border-blue-800";
    default:
      return "bg-gray-800/50 border-gray-700";
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
    case ScanState.WAIT_COMPLETE:
      return "Warten";
    case ScanState.EXPORT_STL:
      return "Export";
    case ScanState.IDLE:
      return "Bereit";
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

function formatDuration(startedAt: string, completedAt?: string): string {
  if (!completedAt) return "—";
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  if (ms < 0) return "—";
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  if (min > 0) return `${min}m ${sec}s`;
  return `${sec}s`;
}

type FilterState = "all" | "done" | "error" | "running";
type FilterResult = "all" | "io" | "nio";

const CT_PC_BASE =
  process.env.NEXT_PUBLIC_CT_PC_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:4802`
    : "http://localhost:4802");

export default function HistoryPage() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [filterState, setFilterState] = useState<FilterState>("all");
  const [filterResult, setFilterResult] = useState<FilterResult>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const loadScans = useCallback(async () => {
    try {
      const data = await api.getScans();
      setScans(data);
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadScans().finally(() => setLoading(false));
  }, [loadScans]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadScans();
    setRefreshing(false);
  };

  const handleDownloadStl = (e: React.MouseEvent, scan: ScanResult) => {
    e.preventDefault();
    e.stopPropagation();
    if (scan.stlPath) {
      window.open(`${CT_PC_BASE}/api/scan/${scan.jobId}/export-stl`, "_blank");
    }
  };

  // Apply filters
  const filtered = scans.filter((scan) => {
    // State filter
    if (filterState === "done" && scan.state !== ScanState.DONE) return false;
    if (filterState === "error" && scan.state !== ScanState.ERROR) return false;
    if (
      filterState === "running" &&
      scan.state !== ScanState.SCANNING &&
      scan.state !== ScanState.WAIT_COMPLETE &&
      scan.state !== ScanState.EXPORT_STL
    )
      return false;

    // Result filter (IO/NIO)
    if (filterResult === "io") {
      if (!scan.deviationReport?.withinTolerance) return false;
    }
    if (filterResult === "nio") {
      if (!scan.deviationReport || scan.deviationReport.withinTolerance)
        return false;
    }

    // Date range filter
    if (dateFrom) {
      const from = new Date(dateFrom);
      if (new Date(scan.startedAt) < from) return false;
    }
    if (dateTo) {
      const to = new Date(dateTo);
      to.setHours(23, 59, 59, 999);
      if (new Date(scan.startedAt) > to) return false;
    }

    return true;
  });

  const activeFilterCount =
    (filterState !== "all" ? 1 : 0) +
    (filterResult !== "all" ? 1 : 0) +
    (dateFrom ? 1 : 0) +
    (dateTo ? 1 : 0);

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Verlauf</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`min-h-[48px] px-4 rounded-xl font-semibold flex items-center gap-2 ${
              showFilters || activeFilterCount > 0
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 border border-gray-700"
            } active:opacity-80`}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className="w-5 h-5"
            >
              <path d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filter
            {activeFilterCount > 0 && (
              <span className="w-5 h-5 bg-white text-blue-600 text-xs font-bold rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="min-h-[48px] min-w-[48px] flex items-center justify-center rounded-xl bg-gray-800 border border-gray-700 text-gray-300 active:bg-gray-700"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className={`w-5 h-5 ${refreshing ? "animate-spin" : ""}`}
            >
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-4">
          {/* State filter */}
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Status</label>
            <div className="flex gap-2 flex-wrap">
              {(
                [
                  { key: "all", label: "Alle" },
                  { key: "done", label: "Fertig" },
                  { key: "error", label: "Fehler" },
                  { key: "running", label: "Läuft" },
                ] as const
              ).map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setFilterState(key)}
                  className={`min-h-[48px] px-4 rounded-xl font-semibold ${
                    filterState === key
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-400 border border-gray-700"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Result filter */}
          <div>
            <label className="text-sm text-gray-400 mb-2 block">
              Ergebnis
            </label>
            <div className="flex gap-2">
              {(
                [
                  { key: "all", label: "Alle" },
                  { key: "io", label: "IO" },
                  { key: "nio", label: "NIO" },
                ] as const
              ).map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setFilterResult(key)}
                  className={`min-h-[48px] px-4 rounded-xl font-semibold ${
                    filterResult === key
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-400 border border-gray-700"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Date range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Von</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Bis</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100"
              />
            </div>
          </div>

          {/* Clear filters */}
          {activeFilterCount > 0 && (
            <button
              onClick={() => {
                setFilterState("all");
                setFilterResult("all");
                setDateFrom("");
                setDateTo("");
              }}
              className="min-h-[48px] px-4 text-red-400 font-semibold active:opacity-70"
            >
              Filter zurücksetzen
            </button>
          )}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <p className="text-gray-500 text-center py-12">Laden...</p>
      )}

      {/* Empty state */}
      {!loading && scans.length === 0 && (
        <p className="text-gray-500 text-center py-12">
          Noch keine Scans durchgeführt.
        </p>
      )}

      {/* Filtered empty state */}
      {!loading && scans.length > 0 && filtered.length === 0 && (
        <p className="text-gray-500 text-center py-12">
          Keine Scans für diese Filter gefunden.
        </p>
      )}

      {/* Result count */}
      {!loading && filtered.length > 0 && (
        <p className="text-xs text-gray-500">
          {filtered.length} von {scans.length} Scans
        </p>
      )}

      {/* Scan list */}
      <div className="space-y-3">
        {filtered.map((scan) => (
          <Link
            key={scan.jobId}
            href={`/scan/${scan.jobId}`}
            className="block p-4 bg-gray-900 border border-gray-800 rounded-xl active:bg-gray-800"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">{scan.partId}</p>
                <div className="flex items-center gap-3 text-sm text-gray-500 mt-0.5">
                  <span>{formatDate(scan.startedAt)}</span>
                  <span className="text-gray-700">|</span>
                  <span>
                    Dauer: {formatDuration(scan.startedAt, scan.completedAt)}
                  </span>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-3">
                {/* State badge */}
                <span
                  className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${stateBgColor(scan.state)} ${stateColor(scan.state)}`}
                >
                  {stateLabel(scan.state)}
                </span>

                {/* IO/NIO indicator */}
                {scan.deviationReport && (
                  <p className="text-xs mt-1.5">
                    <span
                      className={`inline-block px-2 py-0.5 rounded font-bold ${
                        scan.deviationReport.withinTolerance
                          ? "bg-green-900/50 text-green-400"
                          : "bg-red-900/50 text-red-400"
                      }`}
                    >
                      {scan.deviationReport.withinTolerance ? "IO" : "NIO"}
                    </span>{" "}
                    <span className="text-gray-500">
                      +/-{scan.deviationReport.avgDeviation.toFixed(3)}mm
                    </span>
                  </p>
                )}
              </div>
            </div>

            {/* STL download */}
            {scan.stlPath && (
              <div className="mt-3 flex items-center gap-2">
                <button
                  onClick={(e) => handleDownloadStl(e, scan)}
                  className="min-h-[48px] px-4 flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-xl text-sm text-gray-300 active:bg-gray-700"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    className="w-4 h-4"
                  >
                    <path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                  </svg>
                  STL herunterladen
                </button>
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
