import type { FastifyReply, FastifyRequest } from "fastify";
import type { Camera } from "./capture.js";

const BOUNDARY = "frame";
const MAX_BUFFER_SIZE = 3;
const DEFAULT_FPS = 15;

interface StreamOptions {
  fps?: number;
}

/**
 * MJPEG stream manager for a single camera.
 * Supports multiple concurrent viewers with a shared frame buffer.
 */
export class MjpegStream {
  private camera: Camera;
  private fps: number;
  private running = false;
  private frameBuffer: Buffer[] = [];
  private viewers = new Set<FastifyReply>();
  private captureTimer: ReturnType<typeof setInterval> | null = null;

  constructor(camera: Camera, options?: StreamOptions) {
    this.camera = camera;
    this.fps = options?.fps ?? DEFAULT_FPS;
  }

  /**
   * Add a viewer and start streaming if not already running.
   */
  async addViewer(reply: FastifyReply): Promise<void> {
    // Set MJPEG response headers
    reply.raw.writeHead(200, {
      "Content-Type": `multipart/x-mixed-replace; boundary=${BOUNDARY}`,
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Pragma": "no-cache",
      "Connection": "keep-alive",
    });

    this.viewers.add(reply);

    // Clean up on disconnect
    reply.raw.on("close", () => {
      this.viewers.delete(reply);
      if (this.viewers.size === 0) {
        this.stop();
      }
    });

    // Send the latest frame immediately if available
    if (this.frameBuffer.length > 0) {
      const latestFrame = this.frameBuffer[this.frameBuffer.length - 1];
      this.sendFrame(reply, latestFrame);
    }

    // Start capture loop if not running
    if (!this.running) {
      this.start();
    }
  }

  private start(): void {
    if (this.running) return;
    this.running = true;

    const interval = Math.floor(1000 / this.fps);

    this.captureTimer = setInterval(async () => {
      if (this.viewers.size === 0) {
        this.stop();
        return;
      }

      try {
        const frame = await this.camera.capture();

        // Buffer management: keep max N frames
        this.frameBuffer.push(frame);
        while (this.frameBuffer.length > MAX_BUFFER_SIZE) {
          this.frameBuffer.shift();
        }

        // Send to all viewers
        for (const viewer of this.viewers) {
          this.sendFrame(viewer, frame);
        }
      } catch (err) {
        // Camera error - don't crash the stream, skip this frame
        console.error(`Frame capture error for camera ${this.camera.info.id}:`, err);
      }
    }, interval);
  }

  private sendFrame(reply: FastifyReply, frame: Buffer): void {
    try {
      const header = `--${BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: ${frame.length}\r\n\r\n`;
      reply.raw.write(header);
      reply.raw.write(frame);
      reply.raw.write("\r\n");
    } catch {
      // Client disconnected
      this.viewers.delete(reply);
    }
  }

  stop(): void {
    this.running = false;
    if (this.captureTimer) {
      clearInterval(this.captureTimer);
      this.captureTimer = null;
    }
    this.frameBuffer = [];
  }

  getViewerCount(): number {
    return this.viewers.size;
  }

  isRunning(): boolean {
    return this.running;
  }

  getFps(): number {
    return this.fps;
  }
}

/** Registry of active streams, one per camera */
const activeStreams = new Map<string, MjpegStream>();

export function getOrCreateStream(camera: Camera, fps?: number): MjpegStream {
  let stream = activeStreams.get(camera.info.id);
  if (!stream) {
    stream = new MjpegStream(camera, { fps });
    activeStreams.set(camera.info.id, stream);
  }
  return stream;
}

export function getStreamStats(): Array<{ cameraId: string; viewers: number; fps: number; running: boolean }> {
  return Array.from(activeStreams.entries()).map(([cameraId, stream]) => ({
    cameraId,
    viewers: stream.getViewerCount(),
    fps: stream.getFps(),
    running: stream.isRunning(),
  }));
}
