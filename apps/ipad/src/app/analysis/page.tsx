"use client";

import { useEffect, useState, useRef } from "react";
import type { ScanResult, DeviationReport } from "@autopilot/types";
import { ScanState } from "@autopilot/types";
import * as api from "@/lib/api-client";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("de-DE", {
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

export default function AnalysisPage() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanResult | null>(null);
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [referencePath, setReferencePath] = useState<string | null>(null);
  const [tolerance, setTolerance] = useState(0.1);
  const [report, setReport] = useState<DeviationReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api
      .getScans()
      .then((s) => setScans(s.filter((x) => x.state === ScanState.DONE)))
      .catch(() => {});
  }, []);

  const handleFileChange = (file: File) => {
    setReferenceFile(file);
    setReferencePath(null);
    setReport(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!referenceFile) return;
    setUploading(true);
    setError(null);
    try {
      const result = await api.uploadReferenceStl(referenceFile);
      setReferencePath(result.path);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    } finally {
      setUploading(false);
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
        tolerance
      );
      setReport(result.deviationReport ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analyse fehlgeschlagen");
    } finally {
      setRunning(false);
    }
  };

  // Step completion indicators
  const step1Done = !!referencePath;
  const step2Done = !!selectedScan;
  const step3Ready = step1Done && step2Done;

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Analyse</h1>

      {/* Progress indicator */}
      <div className="flex items-center gap-2">
        {[1, 2, 3, 4].map((step) => {
          const done =
            step === 1
              ? step1Done
              : step === 2
                ? step2Done
                : step === 3
                  ? step3Ready
                  : !!report;
          return (
            <div key={step} className="flex items-center gap-2 flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  done
                    ? "bg-green-600 text-white"
                    : "bg-gray-700 text-gray-500"
                }`}
              >
                {done ? "\u2713" : step}
              </div>
              {step < 4 && (
                <div
                  className={`flex-1 h-0.5 ${
                    done ? "bg-green-600" : "bg-gray-700"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Step 1: Upload reference STL */}
      <section className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-3">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-lg">1. Referenz-STL (Soll)</h2>
          {step1Done && (
            <span className="text-green-400 text-sm font-semibold">
              Hochgeladen
            </span>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".stl"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileChange(file);
          }}
        />
        <div className="flex gap-3 items-center flex-wrap">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="min-h-[48px] px-6 bg-gray-800 border border-gray-700 rounded-xl text-gray-300 active:bg-gray-700"
          >
            {referenceFile ? referenceFile.name : "STL-Datei wählen..."}
          </button>
          {referenceFile && !referencePath && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className={`min-h-[48px] px-6 font-semibold rounded-xl ${
                uploading
                  ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                  : "bg-blue-600 text-white active:bg-blue-700"
              }`}
            >
              {uploading ? "Hochladen..." : "Hochladen"}
            </button>
          )}
        </div>
      </section>

      {/* Step 2: Select scan */}
      <section className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-3">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-lg">2. Scan wählen (Ist)</h2>
          {step2Done && (
            <span className="text-green-400 text-sm font-semibold">
              {selectedScan.partId}
            </span>
          )}
        </div>
        {scans.length === 0 ? (
          <p className="text-gray-500">
            Keine abgeschlossenen Scans vorhanden.
          </p>
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
                  {formatDate(scan.startedAt)}
                </p>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Step 3: Tolerance slider + Run */}
      <section className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-4">
        <h2 className="font-semibold text-lg">3. Toleranz & Analyse</h2>

        {/* Tolerance slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm text-gray-400">Toleranz</label>
            <span className="text-lg font-mono font-bold text-gray-100">
              {tolerance.toFixed(2)} mm
            </span>
          </div>
          <input
            type="range"
            min="0.01"
            max="1.0"
            step="0.01"
            value={tolerance}
            onChange={(e) => setTolerance(Number(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-full appearance-none cursor-pointer accent-blue-500"
            style={{ minHeight: "48px" }}
          />
          <div className="flex justify-between text-xs text-gray-600">
            <span>0.01 mm</span>
            <span>0.50 mm</span>
            <span>1.00 mm</span>
          </div>
        </div>

        {/* Analyze button */}
        <button
          onClick={handleAnalyze}
          disabled={!step3Ready || running}
          className={`w-full min-h-[56px] font-bold text-lg rounded-xl ${
            step3Ready && !running
              ? "bg-blue-600 text-white active:bg-blue-700"
              : "bg-gray-800 text-gray-600 cursor-not-allowed"
          }`}
        >
          {running ? "Analysiere..." : "ANALYSE STARTEN"}
        </button>

        {!step3Ready && (
          <p className="text-xs text-gray-500 text-center">
            {!step1Done && !step2Done
              ? "Bitte zuerst eine Referenz-STL hochladen und einen Scan wählen."
              : !step1Done
                ? "Bitte zuerst eine Referenz-STL hochladen."
                : "Bitte zuerst einen Scan wählen."}
          </p>
        )}
      </section>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-950 border border-red-800 rounded-xl text-red-300">
          {error}
        </div>
      )}

      {/* Step 4: Results */}
      {report && (
        <section
          className={`p-6 rounded-xl border-2 ${
            report.withinTolerance
              ? "bg-green-950 border-green-700"
              : "bg-red-950 border-red-700"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-semibold text-lg">4. Ergebnis</h2>
          </div>

          {/* IO/NIO verdict */}
          <div className="text-center mb-4">
            <span
              className={`text-5xl font-bold ${
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

          {/* Deviation metrics */}
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
