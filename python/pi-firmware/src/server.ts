import Fastify from "fastify";
import cors from "@fastify/cors";
import websocket from "@fastify/websocket";
import { registerHealthRoute } from "./health.js";
import { registerCameraRoutes } from "./camera/routes.js";
import { CameraManager } from "./camera/capture.js";
import { MdnsService } from "./discovery/mdns.js";
import type { WebSocket } from "ws";

const PORT = Number(process.env.PORT) || 4801;
const HOST = process.env.HOST || "0.0.0.0";
// In AP mode, the Pi's static IP is 192.168.4.1 — used for logging and discovery
const AP_IP = process.env.AP_IP || "192.168.4.1";

const fastify = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || "info",
  },
});

// Track connected WebSocket clients for event broadcasting
const wsClients = new Set<WebSocket>();

export function broadcastEvent(event: string, data: unknown): void {
  const message = JSON.stringify({ event, data, timestamp: new Date().toISOString() });
  for (const client of wsClients) {
    if (client.readyState === 1) {
      client.send(message);
    }
  }
}

async function main(): Promise<void> {
  // Register plugins
  await fastify.register(cors, { origin: true });
  await fastify.register(websocket);

  // Initialize camera manager
  const cameraManager = new CameraManager();
  await cameraManager.init();

  // Decorate fastify with camera manager
  fastify.decorate("cameraManager", cameraManager);

  // WebSocket endpoint for events
  fastify.get("/ws", { websocket: true }, (socket) => {
    wsClients.add(socket);
    fastify.log.info("WebSocket client connected");

    socket.on("close", () => {
      wsClients.delete(socket);
      fastify.log.info("WebSocket client disconnected");
    });

    socket.send(
      JSON.stringify({
        event: "connected",
        data: { cameras: cameraManager.getCameraCount() },
        timestamp: new Date().toISOString(),
      })
    );
  });

  // Register routes
  registerHealthRoute(fastify, cameraManager);
  registerCameraRoutes(fastify, cameraManager);

  // Start mDNS service
  const mdns = new MdnsService(PORT, cameraManager.getCameraCount());

  // Start server — bind to 0.0.0.0 so it's reachable from WiFi AP clients
  await fastify.listen({ port: PORT, host: HOST });
  fastify.log.info(`Camera server running on http://${HOST}:${PORT}`);
  fastify.log.info(`AP network address: http://${AP_IP}:${PORT}`);

  mdns.publish();
  fastify.log.info("mDNS service published: _autopilot-pi._tcp");

  // Graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    fastify.log.info(`Received ${signal}, shutting down...`);
    mdns.unpublish();
    await cameraManager.shutdown();
    for (const client of wsClients) {
      client.close(1001, "Server shutting down");
    }
    wsClients.clear();
    await fastify.close();
    process.exit(0);
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

main().catch((err) => {
  console.error("Failed to start server:", err);
  process.exit(1);
});

// Type augmentation for Fastify
declare module "fastify" {
  interface FastifyInstance {
    cameraManager: CameraManager;
  }
}
