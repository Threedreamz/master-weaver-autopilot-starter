import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    app: "autopilot-health",
    port: 4803,
    timestamp: new Date().toISOString(),
  });
}
