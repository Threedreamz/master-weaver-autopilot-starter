import type {
  ScanProfile,
  ScanResult,
  ScanJobRequest,
  SystemStatus,
  Worker,
  TimeLog,
  TimeTrackingStats,
} from "@autopilot/types";

// ---------------------------------------------------------------------------
// CT-PC URL discovery
// ---------------------------------------------------------------------------
// The iPad app now runs ON the Pi. The CT-PC is a separate machine discovered
// via the Pi's /api/discovery endpoint or an environment variable override.
// ---------------------------------------------------------------------------

let _ctpcUrl: string | null = null;

async function getCtpcUrl(): Promise<string> {
  if (_ctpcUrl) return _ctpcUrl;

  // 1. Explicit environment variable override
  if (process.env.NEXT_PUBLIC_CT_PC_URL) {
    _ctpcUrl = process.env.NEXT_PUBLIC_CT_PC_URL;
    return _ctpcUrl;
  }

  // 2. Auto-discover via Pi's discovery API (same origin since app runs on Pi)
  try {
    const origin =
      typeof window !== "undefined" ? window.location.origin : "http://localhost";
    const res = await fetch(`${origin}/api/discovery`);
    const data = await res.json();
    if (data.ctpc?.ip) {
      _ctpcUrl = `http://${data.ctpc.ip}:${data.ctpc.port || 4802}`;
      return _ctpcUrl;
    }
  } catch {
    // Discovery unavailable — fall through to fallback
  }

  // 3. Fallback
  _ctpcUrl = "http://localhost:4802";
  return _ctpcUrl;
}

/** Reset the cached CT-PC URL (e.g. after network change) */
export function resetCtpcUrl(): void {
  _ctpcUrl = null;
}

async function request<T = any>(path: string, options?: RequestInit): Promise<T> {
  const base = await getCtpcUrl();
  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// snake_case → camelCase conversion for Python API responses
// ---------------------------------------------------------------------------
function snakeToCamel(obj: any): any {
  if (Array.isArray(obj)) return obj.map(snakeToCamel);
  if (obj !== null && typeof obj === "object") {
    return Object.fromEntries(
      Object.entries(obj).map(([k, v]) => [
        k.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase()),
        snakeToCamel(v),
      ])
    );
  }
  return obj;
}

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

/** Get current system status from CT-PC */
export async function getStatus(): Promise<SystemStatus> {
  return request<SystemStatus>("/api/status");
}

// ---------------------------------------------------------------------------
// Profiles
// ---------------------------------------------------------------------------

/** List all scan profiles */
export async function getProfiles(): Promise<ScanProfile[]> {
  const res = await request<{ profiles: ScanProfile[] }>("/api/profiles");
  return res.profiles;
}

/** Get a single profile (returned unwrapped by Python) */
export async function getProfile(id: string): Promise<ScanProfile> {
  return request<ScanProfile>(`/api/profiles/${id}`);
}

/** Create a new scan profile (returned unwrapped by Python) */
export async function createProfile(
  profile: Omit<ScanProfile, "id" | "createdAt" | "updatedAt">
): Promise<ScanProfile> {
  return request<ScanProfile>("/api/profiles", {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

/** Update an existing profile (returned unwrapped by Python) */
export async function updateProfile(
  id: string,
  profile: Partial<ScanProfile>
): Promise<ScanProfile> {
  return request<ScanProfile>(`/api/profiles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(profile),
  });
}

/** Delete a profile */
export async function deleteProfile(id: string): Promise<{ deleted: string }> {
  return request<{ deleted: string }>(`/api/profiles/${id}`, { method: "DELETE" });
}

/** Select a profile on the CT-PC */
export async function selectProfile(name: string): Promise<{ selected: string; success: boolean }> {
  return request<{ selected: string; success: boolean }>(`/api/profiles/${name}/select`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Scans
// ---------------------------------------------------------------------------

/** Start a new scan job */
export async function startScan(job: ScanJobRequest): Promise<ScanResult> {
  const res = await request<{ scan: ScanResult }>("/api/scan/start", {
    method: "POST",
    body: JSON.stringify(job),
  });
  return res.scan;
}

/** Emergency stop the current scan */
export async function stopScan(): Promise<{ stopped: string[]; count: number }> {
  return request<{ stopped: string[]; count: number }>("/api/scan/stop", { method: "POST" });
}

/** Export STL via the controller save sequence */
export async function exportStl(): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>("/api/stl/export", { method: "POST" });
}

/** Get scan history */
export async function getScans(): Promise<ScanResult[]> {
  const res = await request<{ scans: ScanResult[]; total: number }>("/api/scans");
  return res.scans;
}

/** Get a single scan result */
export async function getScan(jobId: string): Promise<ScanResult> {
  const res = await request<{ scan: ScanResult }>(`/api/scans/${jobId}`);
  return res.scan;
}

// ---------------------------------------------------------------------------
// Analysis / Soll-Ist
// ---------------------------------------------------------------------------

/** Upload reference STL for Soll-Ist comparison */
export async function uploadReferenceStl(file: File): Promise<{ path: string; filename: string; size: number }> {
  const base = await getCtpcUrl();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${base}/api/analysis/upload-reference`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

/** Run Soll-Ist analysis */
export async function runAnalysis(
  scanStlPath: string,
  referenceStlPath: string,
  toleranceMm: number
): Promise<Record<string, any>> {
  const res = await request<{ report: Record<string, any> }>("/api/analysis/compare", {
    method: "POST",
    body: JSON.stringify({ scanStlPath, referenceStlPath, toleranceMm }),
  });
  return res.report;
}

// ---------------------------------------------------------------------------
// Time Tracking (Zeiterfassung) — Workers
// ---------------------------------------------------------------------------

/** List all workers */
export async function getWorkers(): Promise<Worker[]> {
  const res = await request<{ workers: any[]; count: number }>("/api/workers");
  return res.workers.map(snakeToCamel) as Worker[];
}

/** Add a new worker */
export async function addWorker(name: string): Promise<Worker> {
  const res = await request<{ worker: any }>("/api/workers", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return snakeToCamel(res.worker) as Worker;
}

/** Remove a worker */
export async function removeWorker(id: string): Promise<{ deleted: string }> {
  return request<{ deleted: string }>(`/api/workers/${id}`, { method: "DELETE" });
}

/** Login a worker (auto-logouts any currently active worker) */
export async function loginWorker(id: string): Promise<TimeLog> {
  const res = await request<{ log: any }>(`/api/workers/${id}/login`, { method: "POST" });
  return snakeToCamel(res.log) as TimeLog;
}

/** Logout a worker */
export async function logoutWorker(id: string): Promise<TimeLog> {
  const res = await request<{ log: any }>(`/api/workers/${id}/logout`, { method: "POST" });
  return snakeToCamel(res.log) as TimeLog;
}

/** Get the currently active worker (or null) */
export async function getActiveWorker(): Promise<Worker | null> {
  const res = await request<{ worker: any | null }>("/api/workers/active");
  return res.worker ? (snakeToCamel(res.worker) as Worker) : null;
}

// ---------------------------------------------------------------------------
// Time Tracking — Logs & Stats
// ---------------------------------------------------------------------------

/** Get time logs, optionally filtered by date and/or workerId */
export async function getTimeLogs(date?: string, workerId?: string): Promise<TimeLog[]> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  if (workerId) params.set("worker_id", workerId);
  const qs = params.toString();
  const res = await request<{ logs: any[]; count: number }>(`/api/timelogs${qs ? `?${qs}` : ""}`);
  return res.logs.map(snakeToCamel) as TimeLog[];
}

/** Get today's time tracking statistics */
export async function getTimeStats(): Promise<TimeTrackingStats> {
  const res = await request<{ stats: any }>("/api/timelogs/stats");
  return snakeToCamel(res.stats) as TimeTrackingStats;
}
