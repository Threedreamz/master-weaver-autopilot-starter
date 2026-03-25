"use client";

import { useEffect, useState, useRef } from "react";
import type { ScanResult, DeviationReport } from "@autopilot/types";
import { ScanState } from "@autopilot/types";
import * as api from "@/lib/api-client";

export default function AnalysisPage() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanResult | null>(null);
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [referencePath, setReferencePath] = useState<string | null>(null);
  const [tolerance, setTolerance] = useState("0.1");
  const [report, setReport] = useState<DeviationReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api
      .getScans()
      .then((s) => setScans(s.filter((x) => x.state === ScanState.DONE)))
      .catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!referenceFile) return;
    try {
      const result = await api.uploadReferenceStl(referenceFile);
      setReferencePath(result.path);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    }
  };

  const handleAnalyze = async () => {
    if (!selectedScan || !referencePath) return;
    setRunning(true);
    setError(null);
    try {
      const result = await api.runAnalysis(
        selectedScan.jobId,
        referencePath,
        Number(tolerance) || 0.1
      );
      setReport(result.deviationReport ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analyse fehlgeschlagen");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Soll-Ist Analyse</h1>

      {/* Step 1: Upload reference STL */}
      <section className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-3">
        <h2 className="font-semibold text-lg">1. Referenz-STL (Soll)</h2>
        <input
          ref={fileInputRef}
          type="file"
          accept=".stl"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              setReferenceFile(file);
              setReferencePath(null);
              setReport(null);
            }
          }}
        />
        <div className="flex gap-3 items-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="min-h-[48px] px-6 bg-gray-800 border border-gray-700 rounded-xl text-gray-300 active:bg-gray-700"
          >
            {referenceFile ? referenceFile.name : "STL-Datei wählen..."}
          </button>
          {referenceFile && !referencePath && (
            <button
              onClick={handleUpload}
              className="min-h-[48px] px-6 bg-blue-600 text-white font-semibold rounded-xl active:bg-blue-700"
            >
              Hochladen
            </button>
          )}
          {referencePath && (
            <span className="text-green-400 text-sm">Hochgeladen</span>
          )}
        </div>
      </section>

      {/* Step 2: Select scan */}
      <section className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-3">
        <h2 className="font-semibold text-lg">2. Scan wählen (Ist)</h2>
        {scans.length === 0 ? (
          <p className="text-gray-500">Keine abgeschlossenen Scans vorhanden.</p>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2">
            {scans.map((scan) => (
              <button
                key={scan.jobId}
                onClick={() => {
                  setSelectedScan(scan);
                  setReport(null);
                }}
                className={`flex-shrink-0 min-w-[160px] min-h-[64px] p-3 rounded-xl border-2 text-left ${
                  selectedScan?.jobId === scan.jobId
                    ? "border-blue-500 bg-blue-950"
                    : "border-gray-700 bg-gray-800 active:bg-gray-700"
                }`}
              >
                <p className="font-semibold text-sm">{scan.partId}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {new Date(scan.startedAt).toLocaleDateString("de-DE")}
                </p>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Step 3: Tolerance + Run */}
      <section className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-3">
        <h2 className="font-semibold text-lg">3. Toleranz & Analyse</h2>
        <div className="flex gap-3 items-center">
          <label className="text-sm text-gray-400">Toleranz (mm):</label>
          <input
            type="number"
            step="0.01"
            value={tolerance}
            onChange={(e) => setTolerance(e.target.value)}
            className="min-h-[48px] w-24 px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100"
          />
          <button
            onClick={handleAnalyze}
            disabled={!selectedScan || !referencePath || running}
            className={`flex-1 min-h-[56px] font-bold text-lg rounded-xl ${
              selectedScan && referencePath && !running
                ? "bg-blue-600 text-white active:bg-blue-700"
                : "bg-gray-800 text-gray-600 cursor-not-allowed"
            }`}
          >
            {running ? "Analysiere..." : "ANALYSE STARTEN"}
          </button>
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-950 border border-red-800 rounded-xl text-red-300">
          {error}
        </div>
      )}

      {/* Results */}
      {report && (
        <section
          className={`p-6 rounded-xl border-2 ${
            report.withinTolerance
              ? "bg-green-950 border-green-700"
              : "bg-red-950 border-red-700"
          }`}
        >
          <div className="text-center mb-4">
            <span
              className={`text-4xl font-bold ${
                report.withinTolerance ? "text-green-400" : "text-red-400"
              }`}
            >
              {report.withinTolerance ? "IO" : "NIO"}
            </span>
            <p className="text-sm text-gray-400 mt-1">
              {report.withinTolerance
                ? "Innerhalb der Toleranz"
                : "Ausserhalb der Toleranz"}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="p-3 bg-black/30 rounded-xl">
              <p className="text-xs text-gray-400">Min Abweichung</p>
              <p className="text-xl font-mono font-bold">
                {report.minDeviation.toFixed(4)} mm
              </p>
            </div>
            <div className="p-3 bg-black/30 rounded-xl">
              <p className="text-xs text-gray-400">Max Abweichung</p>
              <p className="text-xl font-mono font-bold">
                {report.maxDeviation.toFixed(4)} mm
              </p>
            </div>
            <div className="p-3 bg-black/30 rounded-xl">
              <p className="text-xs text-gray-400">Durchschnitt</p>
              <p className="text-xl font-mono font-bold">
                {report.avgDeviation.toFixed(4)} mm
              </p>
            </div>
            <div className="p-3 bg-black/30 rounded-xl">
              <p className="text-xs text-gray-400">Standardabw.</p>
              <p className="text-xl font-mono font-bold">
                {report.stdDeviation.toFixed(4)} mm
              </p>
            </div>
          </div>

          <div className="mt-4 text-center text-sm text-gray-400">
            Toleranz: +/- {report.toleranceMm} mm
          </div>
        </section>
      )}
    </div>
  );
}
