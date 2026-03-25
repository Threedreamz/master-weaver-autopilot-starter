/** Raspberry Pi camera endpoints */

const PI_BASE =
  typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:4691`
    : "http://localhost:4691";

/** MJPEG stream URL for a given camera */
export function streamUrl(cameraId: number = 0): string {
  return `${PI_BASE}/api/camera/${cameraId}/stream`;
}

/** Single snapshot URL */
export function snapshotUrl(cameraId: number = 0): string {
  return `${PI_BASE}/api/camera/${cameraId}/snapshot`;
}

/** Check Pi health */
export async function getPiHealth() {
  const res = await fetch(`${PI_BASE}/api/health`);
  if (!res.ok) throw new Error(`Pi health ${res.status}`);
  return res.json();
}
