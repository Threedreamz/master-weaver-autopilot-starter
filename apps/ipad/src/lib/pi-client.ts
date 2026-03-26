/** Raspberry Pi camera endpoints
 *
 * The iPad app runs ON the Pi. Camera streams are served via Nginx reverse
 * proxy on the same origin at /camera/ (proxied to :4801).
 */

const PI_BASE =
  process.env.NEXT_PUBLIC_PI_URL ||
  (typeof window !== "undefined"
    ? `${window.location.origin}/camera`
    : "http://localhost:4801");

/** MJPEG stream URL for a given camera */
export function streamUrl(cameraId: number = 0): string {
  return `${PI_BASE}/${cameraId}/stream`;
}

/** Single snapshot URL */
export function snapshotUrl(cameraId: number = 0): string {
  return `${PI_BASE}/${cameraId}/snapshot`;
}

/** Check Pi health (camera service) */
export async function getPiHealth() {
  const res = await fetch(`${PI_BASE}/health`);
  if (!res.ok) throw new Error(`Pi camera health ${res.status}`);
  return res.json();
}
