// AutoPilot shared types

/** Scan workflow states */
export enum ScanState {
  IDLE = "IDLE",
  PROFILE_SELECT = "PROFILE_SELECT",
  TUBE_ON = "TUBE_ON",
  ROTATE_PREVIEW = "ROTATE_PREVIEW",
  GREEN_BOX = "GREEN_BOX",
  ERROR_CORRECT = "ERROR_CORRECT",
  SCANNING = "SCANNING",
  WAIT_COMPLETE = "WAIT_COMPLETE",
  EXPORT_STL = "EXPORT_STL",
  ANALYSE = "ANALYSE",
  DONE = "DONE",
  ERROR = "ERROR",
}

/** Scan profile configuration */
export interface ScanProfile {
  id: string;
  name: string;
  magnification: "125L" | "100L" | "50L";
  voltage?: number;
  ampere?: number;
  rotationDegrees: number;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

/** WebSocket event types */
export type WSEventType =
  | "scan.state_change"
  | "scan.progress"
  | "scan.error"
  | "scan.complete"
  | "system.status"
  | "system.error"
  | "camera.frame"
  | "health.update"
  | "worker.login"
  | "worker.logout"
  | "worker.auto-logout";

/** WebSocket event envelope */
export interface WSEvent<T = unknown> {
  type: WSEventType;
  timestamp: string;
  data: T;
}

/** System status from CT-PC */
export interface SystemStatus {
  timestamp: string;
  profileButtonActive: boolean;
  sidebarActive: boolean;
  errorBoxes: { left: [number, number, number]; right: [number, number, number] };
  tubeStatus: { on: boolean; ready: boolean };
  currentScanState: ScanState;
  mousePosition: [number, number];
}

/** Health endpoint response */
export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  node: "ipad" | "pi" | "ctpc" | "health";
  timestamp: string;
  uptime: number;
  details?: Record<string, unknown>;
}

/** Raspberry Pi health details */
export interface PiHealthDetails {
  cameras: { id: number; active: boolean; resolution: string }[];
  cpuTemp: number;
  memoryFree: number;
  memoryTotal: number;
  streamFps: number;
}

/** Scan job request from iPad */
export interface ScanJobRequest {
  profileId: string;
  partId: string;
  referenceStlPath?: string;
  notes?: string;
}

/** Scan result */
export interface ScanResult {
  jobId: string;
  partId: string;
  profileId: string;
  stlPath?: string;
  startedAt: string;
  completedAt?: string;
  state: ScanState;
  deviationReport?: DeviationReport;
}

// ─── Time Tracking (Zeiterfassung) ───

/** Worker / Mitarbeiter */
export interface Worker {
  id: string;
  name: string;
  active: boolean;
  lastLogin?: string;
  lastLogout?: string;
  createdAt: string;
}

/** Time tracking action types */
export type TimeLogAction = "login" | "logout" | "auto-logout";

/** Single time log entry */
export interface TimeLog {
  id: string;
  workerId: string;
  workerName: string;
  action: TimeLogAction;
  timestamp: string;
  scanId?: string;
}

/** Daily time tracking statistics */
export interface TimeTrackingStats {
  totalHoursToday: number;
  activeWorker: Worker | null;
  todayLogs: TimeLog[];
  workerHours: { workerId: string; workerName: string; hours: number }[];
}

/** WebSocket event types for time tracking */
export type WSTimeEventType =
  | "worker.login"
  | "worker.logout"
  | "worker.auto-logout";

/** Soll-Ist deviation report */
export interface DeviationReport {
  referenceStlPath: string;
  scanStlPath: string;
  minDeviation: number;
  maxDeviation: number;
  avgDeviation: number;
  stdDeviation: number;
  withinTolerance: boolean;
  toleranceMm: number;
  heatmapData?: number[];
}
