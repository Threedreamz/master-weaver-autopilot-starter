import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    app: "autopilot-setup",
    port: 4804,
    timestamp: new Date().toISOString(),
  });
}
