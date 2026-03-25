import type {
  ScanProfile,
  ScanResult,
  ScanJobRequest,
  SystemStatus,
  Worker,
  TimeLog,
  TimeTrackingStats,
} from "@autopilot/types";

const CT_PC_BASE =
  process.env.NEXT_PUBLIC_CT_PC_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:4802`
    : "http://localhost:4802");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${CT_PC_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

/** Get current system status from CT-PC */
export function getStatus(): Promise<SystemStatus> {
  return request("/api/status");
}

/** List all scan profiles */
export function getProfiles(): Promise<ScanProfile[]> {
  return request("/api/profiles");
}

/** Get a single profile */
export function getProfile(id: string): Promise<ScanProfile> {
  return request(`/api/profiles/${id}`);
}

/** Create a new scan profile */
export function createProfile(
  profile: Omit<ScanProfile, "id" | "createdAt" | "updatedAt">
): Promise<ScanProfile> {
  return request("/api/profiles", {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

/** Update an existing profile */
export function updateProfile(
  id: string,
  profile: Partial<ScanProfile>
): Promise<ScanProfile> {
  return request(`/api/profiles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(profile),
  });
}

/** Delete a profile */
export function deleteProfile(id: string): Promise<void> {
  return request(`/api/profiles/${id}`, { method: "DELETE" });
}

/** Select a profile on the CT-PC */
export function selectProfile(id: string): Promise<{ ok: boolean }> {
  return request("/api/scan/select-profile", {
    method: "POST",
    body: JSON.stringify({ profileId: id }),
  });
}

/** Start a new scan job */
export function startScan(job: ScanJobRequest): Promise<ScanResult> {
  return request("/api/scan/start", {
    method: "POST",
    body: JSON.stringify(job),
  });
}

/** Emergency stop the current scan */
export function stopScan(): Promise<{ ok: boolean }> {
  return request("/api/scan/stop", { method: "POST" });
}

/** Export STL from the latest scan */
export function exportStl(jobId: string): Promise<{ stlPath: string }> {
  return request(`/api/scan/${jobId}/export-stl`, { method: "POST" });
}

/** Get scan history */
export function getScans(): Promise<ScanResult[]> {
  return request("/api/scans");
}

/** Get a single scan result */
export function getScan(jobId: string): Promise<ScanResult> {
  return request(`/api/scans/${jobId}`);
}

/** Upload reference STL for Soll-Ist comparison */
export async function uploadReferenceStl(file: File): Promise<{ path: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${CT_PC_BASE}/api/analysis/upload-reference`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

/** Run Soll-Ist analysis */
export function runAnalysis(
  scanJobId: string,
  referenceStlPath: string,
  toleranceMm: number
): Promise<ScanResult> {
  return request("/api/analysis/compare", {
    method: "POST",
    body: JSON.stringify({ scanJobId, referenceStlPath, toleranceMm }),
  });
}

// ─── Time Tracking (Zeiterfassung) ───

/** List all workers */
export function getWorkers(): Promise<Worker[]> {
  return request("/api/workers");
}

/** Add a new worker */
export function addWorker(name: string): Promise<Worker> {
  return request("/api/workers", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

/** Remove a worker */
export function removeWorker(id: string): Promise<void> {
  return request(`/api/workers/${id}`, { method: "DELETE" });
}

/** Login a worker (auto-logouts any currently active worker) */
export function loginWorker(id: string): Promise<TimeLog> {
  return request(`/api/workers/${id}/login`, { method: "POST" });
}

/** Logout a worker */
export function logoutWorker(id: string): Promise<TimeLog> {
  return request(`/api/workers/${id}/logout`, { method: "POST" });
}

/** Get the currently active worker (or null) */
export function getActiveWorker(): Promise<Worker | null> {
  return request("/api/workers/active");
}

/** Get time logs, optionally filtered by date and/or workerId */
export function getTimeLogs(date?: string, workerId?: string): Promise<TimeLog[]> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  if (workerId) params.set("workerId", workerId);
  const qs = params.toString();
  return request(`/api/timelogs${qs ? `?${qs}` : ""}`);
}

/** Get today's time tracking statistics */
export function getTimeStats(): Promise<TimeTrackingStats> {
  return request("/api/timelogs/stats");
}
