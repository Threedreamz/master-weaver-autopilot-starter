import { NextRequest, NextResponse } from "next/server";
import { readFile, writeFile, mkdir } from "fs/promises";
import { join } from "path";

const CONFIG_DIR = "/opt/autopilot/config";
const DEVICES_PATH = join(CONFIG_DIR, "devices.json");
const CAMERA_IP_PATH = join(CONFIG_DIR, "camera-pi-ip");

/** Valid device types in the 4-device architecture */
type DeviceType = "ctpc" | "camera";

interface DeviceRegistration {
  ip: string;
  port: number;
  version?: string;
  hostname: string;
  lastSeen: string;
  /** Extra metadata per device type */
  meta?: Record<string, unknown>;
}

type DevicesMap = Partial<Record<DeviceType, DeviceRegistration>>;

async function readDevices(): Promise<DevicesMap> {
  try {
    const data = await readFile(DEVICES_PATH, "utf-8");
    return JSON.parse(data);
  } catch {
    // Migrate from legacy ctpc.json if it exists
    try {
      const legacy = await readFile(join(CONFIG_DIR, "ctpc.json"), "utf-8");
      const old = JSON.parse(legacy);
      const migrated: DevicesMap = {
        ctpc: {
          ip: old.ip,
          port: old.port,
          hostname: old.hostname ?? "unknown",
          version: old.version,
          lastSeen: old.registeredAt ?? new Date().toISOString(),
        },
      };
      await writeDevices(migrated);
      return migrated;
    } catch {
      return {};
    }
  }
}

async function writeDevices(devices: DevicesMap): Promise<void> {
  await mkdir(CONFIG_DIR, { recursive: true });
  await writeFile(DEVICES_PATH, JSON.stringify(devices, null, 2));
}

/**
 * GET /api/discovery
 * Returns all registered devices + Haupt-Pi self-status.
 */
export async function GET() {
  const devices = await readDevices();

  return NextResponse.json({
    devices,
    deviceCount: Object.keys(devices).length,
  });
}

/**
 * POST /api/discovery
 * Register or update a device.
 * Body: { type: "ctpc" | "camera", ip, port, hostname?, version?, meta? }
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { type, ip, port, hostname, version, meta } = body as {
    type: DeviceType;
    ip: string;
    port: number;
    hostname?: string;
    version?: string;
    meta?: Record<string, unknown>;
  };

  if (!type || !ip || !port) {
    return NextResponse.json(
      { error: "type, ip und port erforderlich" },
      { status: 400 }
    );
  }

  const validTypes: DeviceType[] = ["ctpc", "camera"];
  if (!validTypes.includes(type)) {
    return NextResponse.json(
      { error: `Unbekannter Gerätetyp: ${type}. Erlaubt: ${validTypes.join(", ")}` },
      { status: 400 }
    );
  }

  const registration: DeviceRegistration = {
    ip,
    port,
    hostname: hostname ?? "unknown",
    version: version ?? undefined,
    lastSeen: new Date().toISOString(),
    meta: meta ?? undefined,
  };

  try {
    const devices = await readDevices();
    devices[type] = registration;
    await writeDevices(devices);

    // Write camera-pi IP to plain text file for nginx to read
    if (type === "camera") {
      await writeFile(CAMERA_IP_PATH, ip, "utf-8");
    }

    return NextResponse.json({ success: true, type, ...registration });
  } catch (err) {
    console.error(`Failed to register device '${type}':`, err);
    return NextResponse.json(
      { error: "Registrierung fehlgeschlagen" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/discovery
 * Unregister a device by type.
 * Body: { type: "ctpc" | "camera" }
 */
export async function DELETE(request: NextRequest) {
  const body = await request.json();
  const { type } = body as { type: DeviceType };

  if (!type) {
    return NextResponse.json(
      { error: "type erforderlich" },
      { status: 400 }
    );
  }

  try {
    const devices = await readDevices();
    if (!devices[type]) {
      return NextResponse.json(
        { error: `Gerät '${type}' nicht registriert` },
        { status: 404 }
      );
    }

    delete devices[type];
    await writeDevices(devices);

    return NextResponse.json({ success: true, removed: type });
  } catch (err) {
    console.error(`Failed to unregister device '${type}':`, err);
    return NextResponse.json(
      { error: "Abmeldung fehlgeschlagen" },
      { status: 500 }
    );
  }
}
