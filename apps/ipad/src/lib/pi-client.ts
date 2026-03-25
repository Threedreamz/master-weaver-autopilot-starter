/** Raspberry Pi camera endpoints */

const PI_BASE =
  process.env.NEXT_PUBLIC_PI_URL ||
  (typeof window !== "undefined"
    ? `http://${window.location.hostname}:4801`
    : "http://192.168.4.1:4801");

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
