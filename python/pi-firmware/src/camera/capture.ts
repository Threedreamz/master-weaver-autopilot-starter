import { execFile } from "node:child_process";
import { readdir } from "node:fs/promises";
import { promisify } from "node:util";
import sharp from "sharp";
import { broadcastEvent } from "../server.js";

const execFileAsync = promisify(execFile);

const PLATFORM = process.platform;
const IS_PI = PLATFORM === "linux";

export interface CameraInfo {
  id: string;
  index: number;
  type: "csi" | "usb" | "mock";
  device: string;
  resolution: { width: number; height: number };
  available: boolean;
}

interface CaptureOptions {
  width?: number;
  height?: number;
  quality?: number;
}

const DEFAULT_WIDTH = 3840;
const DEFAULT_HEIGHT = 2160;
const FALLBACK_WIDTH = 1920;
const FALLBACK_HEIGHT = 1080;
const DEFAULT_QUALITY = 85;

export class Camera {
  public info: CameraInfo;
  private available = false;
  private use4K = true;

  constructor(info: CameraInfo) {
    this.info = info;
    this.available = info.available;
  }

  async init(): Promise<void> {
    if (this.info.type === "mock") {
      this.available = true;
      this.info.available = true;
      return;
    }

    // Test if camera is responsive
    try {
      await this.capture({ width: 320, height: 240, quality: 50 });
      this.available = true;
      this.info.available = true;
    } catch {
      // Try fallback resolution
      this.use4K = false;
      this.info.resolution = { width: FALLBACK_WIDTH, height: FALLBACK_HEIGHT };
      try {
        await this.capture({ width: 320, height: 240, quality: 50 });
        this.available = true;
        this.info.available = true;
      } catch {
        this.available = false;
        this.info.available = false;
      }
    }
  }

  async capture(options?: CaptureOptions): Promise<Buffer> {
    const width = options?.width ?? this.info.resolution.width;
    const height = options?.height ?? this.info.resolution.height;
    const quality = options?.quality ?? DEFAULT_QUALITY;

    if (this.info.type === "mock") {
      return this.generateMockFrame(width, height, quality);
    }

    return this.captureReal(width, height, quality);
  }

  private async captureReal(width: number, height: number, quality: number): Promise<Buffer> {
    if (this.info.type === "csi") {
      return this.captureCSI(width, height, quality);
    }
    return this.captureUSB(width, height, quality);
  }

  private async captureCSI(width: number, height: number, quality: number): Promise<Buffer> {
    const tmpPath = `/tmp/autopilot-cam${this.info.index}.jpg`;
    await execFileAsync("libcamera-still", [
      "--camera",
      String(this.info.index),
      "--width",
      String(width),
      "--height",
      String(height),
      "--quality",
      String(quality),
      "--nopreview",
      "--immediate",
      "-o",
      tmpPath,
    ]);

    const { data } = await sharp(tmpPath).jpeg({ quality }).toBuffer({ resolveWithObject: true });
    return data;
  }

  private async captureUSB(width: number, height: number, quality: number): Promise<Buffer> {
    const tmpPath = `/tmp/autopilot-cam${this.info.index}.jpg`;

    // Set resolution
    await execFileAsync("v4l2-ctl", [
      "--device",
      this.info.device,
      "--set-fmt-video",
      `width=${width},height=${height},pixelformat=MJPG`,
    ]);

    // Capture single frame
    await execFileAsync("v4l2-ctl", [
      "--device",
      this.info.device,
      "--stream-mmap",
      "--stream-count=1",
      `--stream-to=${tmpPath}`,
    ]);

    const { data } = await sharp(tmpPath).jpeg({ quality }).toBuffer({ resolveWithObject: true });
    return data;
  }

  private async generateMockFrame(width: number, height: number, quality: number): Promise<Buffer> {
    // Generate a colored gradient test frame with timestamp
    const time = Date.now();
    const hueShift = (time / 50) % 360;

    // Create gradient using raw pixel data for a small tile, then resize
    const tileW = Math.min(width, 64);
    const tileH = Math.min(height, 64);
    const pixels = Buffer.alloc(tileW * tileH * 3);

    for (let y = 0; y < tileH; y++) {
      for (let x = 0; x < tileW; x++) {
        const idx = (y * tileW + x) * 3;
        const hue = ((x / tileW) * 360 + hueShift) % 360;
        const sat = 0.8;
        const lum = 0.3 + (y / tileH) * 0.5;
        const [r, g, b] = hslToRgb(hue, sat, lum);
        pixels[idx] = r;
        pixels[idx + 1] = g;
        pixels[idx + 2] = b;
      }
    }

    // Create image from raw pixels, resize to target, overlay camera info
    const label = `CAM ${this.info.index} | ${width}x${height} | MOCK`;
    const svgOverlay = `
      <svg width="${width}" height="${height}">
        <rect x="${width / 2 - 220}" y="${height / 2 - 30}" width="440" height="60" rx="8" fill="rgba(0,0,0,0.7)"/>
        <text x="${width / 2}" y="${height / 2 + 8}" font-family="monospace" font-size="24" fill="white" text-anchor="middle">${label}</text>
        <text x="${width / 2}" y="${height - 40}" font-family="monospace" font-size="16" fill="rgba(255,255,255,0.6)" text-anchor="middle">${new Date().toISOString()}</text>
      </svg>`;

    return sharp(pixels, { raw: { width: tileW, height: tileH, channels: 3 } })
      .resize(width, height, { kernel: "cubic" })
      .composite([{ input: Buffer.from(svgOverlay), gravity: "center" }])
      .jpeg({ quality })
      .toBuffer();
  }

  isAvailable(): boolean {
    return this.available;
  }

  getInfo(): CameraInfo {
    return { ...this.info };
  }
}

export class CameraManager {
  private cameras: Map<string, Camera> = new Map();

  async init(): Promise<void> {
    const detected = IS_PI ? await this.detectRealCameras() : [];

    if (detected.length === 0) {
      // Mock mode: create 2 virtual cameras
      console.log("No real cameras detected, using mock cameras");
      for (let i = 0; i < 2; i++) {
        const info: CameraInfo = {
          id: `mock-${i}`,
          index: i,
          type: "mock",
          device: `mock-${i}`,
          resolution: { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT },
          available: true,
        };
        const camera = new Camera(info);
        await camera.init();
        this.cameras.set(info.id, camera);
      }
    } else {
      for (const info of detected) {
        const camera = new Camera(info);
        await camera.init();
        this.cameras.set(info.id, camera);
      }
    }

    broadcastEvent("cameras:ready", {
      count: this.cameras.size,
      cameras: this.listCameras(),
    });
  }

  private async detectRealCameras(): Promise<CameraInfo[]> {
    const cameras: CameraInfo[] = [];

    try {
      // Detect CSI cameras via libcamera
      const { stdout } = await execFileAsync("libcamera-hello", ["--list-cameras"]);
      const csiMatches = stdout.matchAll(/\((\d+)\)\s*:\s*(\S+)/g);
      for (const match of csiMatches) {
        const index = parseInt(match[1], 10);
        cameras.push({
          id: `csi-${index}`,
          index,
          type: "csi",
          device: `/dev/video${index}`,
          resolution: { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT },
          available: true,
        });
      }
    } catch {
      // libcamera not available
    }

    try {
      // Detect USB cameras via /dev/video*
      const entries = await readdir("/dev");
      const videoDevices = entries.filter((e) => /^video\d+$/.test(e)).sort();
      for (const dev of videoDevices) {
        const index = parseInt(dev.replace("video", ""), 10);
        // Skip devices already found as CSI
        if (cameras.some((c) => c.index === index)) continue;
        cameras.push({
          id: `usb-${index}`,
          index,
          type: "usb",
          device: `/dev/${dev}`,
          resolution: { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT },
          available: true,
        });
      }
    } catch {
      // /dev enumeration failed
    }

    return cameras.slice(0, 2); // Max 2 cameras
  }

  getCamera(id: string): Camera | undefined {
    return this.cameras.get(id);
  }

  getCameraByIndex(index: number): Camera | undefined {
    for (const camera of this.cameras.values()) {
      if (camera.info.index === index) return camera;
    }
    return undefined;
  }

  listCameras(): CameraInfo[] {
    return Array.from(this.cameras.values()).map((c) => c.getInfo());
  }

  getCameraCount(): number {
    return this.cameras.size;
  }

  async shutdown(): Promise<void> {
    broadcastEvent("cameras:shutdown", { count: this.cameras.size });
    this.cameras.clear();
  }
}

// HSL to RGB conversion helper
function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;

  let r = 0,
    g = 0,
    b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];

  return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
}
