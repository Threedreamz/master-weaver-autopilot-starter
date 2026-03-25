import { NextResponse } from "next/server";
import type { HealthResponse } from "@autopilot/types";

const startTime = Date.now();

export async function GET() {
  const response: HealthResponse = {
    status: "ok",
    node: "ipad",
    timestamp: new Date().toISOString(),
    uptime: Math.floor((Date.now() - startTime) / 1000),
  };
  return NextResponse.json(response);
}
