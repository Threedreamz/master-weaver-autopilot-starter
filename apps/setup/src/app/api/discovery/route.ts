import { NextRequest, NextResponse } from "next/server";
import { readFile, writeFile, mkdir } from "fs/promises";
import { join } from "path";

const CONFIG_DIR = "/opt/autopilot/config";
const CTPC_PATH = join(CONFIG_DIR, "ctpc.json");

interface CtpcRegistration {
  ip: string;
  port: number;
  version: string;
  hostname: string;
  registeredAt: string;
}

async function readCtpc(): Promise<CtpcRegistration | null> {
  try {
    const data = await readFile(CTPC_PATH, "utf-8");
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export async function GET() {
  const ctpc = await readCtpc();

  if (ctpc) {
    return NextResponse.json({
      registered: true,
      ...ctpc,
    });
  }

  return NextResponse.json({ registered: false });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { ip, port, version, hostname } = body as {
    ip: string;
    port: number;
    version: string;
    hostname: string;
  };

  if (!ip || !port) {
    return NextResponse.json(
      { error: "IP und Port erforderlich" },
      { status: 400 }
    );
  }

  const registration: CtpcRegistration = {
    ip,
    port,
    version: version ?? "unknown",
    hostname: hostname ?? "unknown",
    registeredAt: new Date().toISOString(),
  };

  try {
    await mkdir(CONFIG_DIR, { recursive: true });
    await writeFile(CTPC_PATH, JSON.stringify(registration, null, 2));
    return NextResponse.json({ success: true, ...registration });
  } catch (err) {
    console.error("Failed to save CT-PC registration:", err);
    return NextResponse.json(
      { error: "Registrierung fehlgeschlagen" },
      { status: 500 }
    );
  }
}
