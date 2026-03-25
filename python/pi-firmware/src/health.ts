import type { FastifyInstance } from "fastify";
import type { CameraManager } from "./camera/capture.js";
import { getStreamStats } from "./camera/stream.js";
import { getCpuTemperature, getMemoryInfo } from "./system.js";

interface HealthResponse {
  status: "ok" | "degraded" | "error";
  app: string;
  timestamp: string;
  uptime: number;
  cameras: {
    total: number;
    available: number;
    list: Array<{ id: string; type: string; available: boolean }>;
  };
  streams: {
    active: number;
    totalViewers: number;
  };
  system: {
    cpuTemp: number | null;
    memory: {
      totalMB: number;
      usedMB: number;
      usedPercent: number;
    };
  };
}

export function registerHealthRoute(fastify: FastifyInstance, cameraManager: CameraManager): void {
  fastify.get("/health", async (): Promise<HealthResponse> => {
    const cameras = cameraManager.listCameras();
    const availableCameras = cameras.filter((c) => c.available);
    const streams = getStreamStats();
    const activeStreams = streams.filter((s) => s.running);
    const totalViewers = activeStreams.reduce((sum, s) => sum + s.viewers, 0);

    const cpuTemp = await getCpuTemperature();
    const memory = await getMemoryInfo();

    // Determine overall status
    let status: "ok" | "degraded" | "error" = "ok";
    if (availableCameras.length === 0) {
      status = "error";
    } else if (availableCameras.length < cameras.length) {
      status = "degraded";
    }
    if (cpuTemp !== null && cpuTemp > 80) {
      status = "degraded";
    }
    if (memory.usedPercent > 90) {
      status = "degraded";
    }

    return {
      status,
      app: "autopilot-pi-camera",
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      cameras: {
        total: cameras.length,
        available: availableCameras.length,
        list: cameras.map((c) => ({ id: c.id, type: c.type, available: c.available })),
      },
      streams: {
        active: activeStreams.length,
        totalViewers,
      },
      system: {
        cpuTemp,
        memory: {
          totalMB: memory.totalMB,
          usedMB: memory.usedMB,
          usedPercent: memory.usedPercent,
        },
      },
    };
  });
}
