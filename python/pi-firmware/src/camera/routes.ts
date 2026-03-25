import type { FastifyInstance } from "fastify";
import type { CameraManager } from "./capture.js";
import { getOrCreateStream, getStreamStats } from "./stream.js";
import { captureSnapshot, SnapshotError } from "./snapshot.js";

export function registerCameraRoutes(fastify: FastifyInstance, cameraManager: CameraManager): void {
  // List all cameras
  fastify.get("/cameras", async () => {
    const cameras = cameraManager.listCameras();
    const streams = getStreamStats();
    return {
      cameras,
      streams,
      count: cameras.length,
    };
  });

  // MJPEG stream for a specific camera
  fastify.get<{ Params: { id: string }; Querystring: { fps?: string } }>(
    "/camera/:id/stream",
    async (request, reply) => {
      const cameraIndex = parseInt(request.params.id, 10);
      const camera = cameraManager.getCameraByIndex(cameraIndex);

      if (!camera) {
        return reply.code(404).send({ error: "Camera not found", id: request.params.id });
      }

      if (!camera.isAvailable()) {
        return reply.code(503).send({ error: "Camera unavailable", id: request.params.id });
      }

      const fps = request.query.fps ? parseInt(request.query.fps, 10) : undefined;
      const stream = getOrCreateStream(camera, fps);
      await stream.addViewer(reply);

      // Don't return — the response is handled by the stream
      return reply;
    }
  );

  // Single snapshot from a specific camera
  fastify.get<{
    Params: { id: string };
    Querystring: { width?: string; height?: string; quality?: string };
  }>("/camera/:id/snapshot", async (request, reply) => {
    const cameraIndex = parseInt(request.params.id, 10);
    const camera = cameraManager.getCameraByIndex(cameraIndex);

    if (!camera) {
      return reply.code(404).send({ error: "Camera not found", id: request.params.id });
    }

    try {
      const options = {
        width: request.query.width ? parseInt(request.query.width, 10) : undefined,
        height: request.query.height ? parseInt(request.query.height, 10) : undefined,
        quality: request.query.quality ? parseInt(request.query.quality, 10) : undefined,
      };

      const jpeg = await captureSnapshot(camera, options);

      return reply
        .code(200)
        .header("Content-Type", "image/jpeg")
        .header("Content-Length", jpeg.length)
        .header("Cache-Control", "no-cache")
        .send(jpeg);
    } catch (err) {
      if (err instanceof SnapshotError) {
        return reply.code(err.statusCode).send({ error: err.message });
      }
      return reply.code(500).send({ error: "Capture failed" });
    }
  });
}
