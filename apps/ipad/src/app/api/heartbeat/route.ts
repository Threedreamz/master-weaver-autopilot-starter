import { NextRequest, NextResponse } from "next/server";
import { registerClient } from "../health/route";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const forwarded = req.headers.get("x-forwarded-for");
  const ip = forwarded?.split(",")[0]?.trim() ?? req.headers.get("x-real-ip") ?? "unknown";

  if (ip !== "unknown") {
    registerClient(ip);
  }

  return NextResponse.json({ ok: true, ip });
}
