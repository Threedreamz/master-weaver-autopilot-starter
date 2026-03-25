import sharp from "sharp";
import type { Camera } from "./capture.js";

interface SnapshotOptions {
  width?: number;
  height?: number;
  quality?: number;
}

/**
 * Capture a single frame from a camera, optionally resized.
 * Returns a JPEG buffer.
 */
export async function captureSnapshot(camera: Camera, options?: SnapshotOptions): Promise<Buffer> {
  if (!camera.isAvailable()) {
    throw new SnapshotError("Camera unavailable", 503);
  }

  const quality = options?.quality ?? 90;

  // Capture at native resolution
  const frame = await camera.capture({ quality });

  // Resize if dimensions specified
  if (options?.width || options?.height) {
    return sharp(frame)
      .resize(options.width, options.height, {
        fit: "inside",
        withoutEnlargement: true,
      })
      .jpeg({ quality })
      .toBuffer();
  }

  return frame;
}

export class SnapshotError extends Error {
  public statusCode: number;

  constructor(message: string, statusCode = 500) {
    super(message);
    this.name = "SnapshotError";
    this.statusCode = statusCode;
  }
}
