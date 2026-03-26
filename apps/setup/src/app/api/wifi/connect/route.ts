import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";

const execAsync = promisify(exec);

const CONFIG_DIR = "/opt/autopilot/config";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { ssid, password } = body as { ssid: string; password: string };

  if (!ssid || !password) {
    return NextResponse.json(
      { success: false, error: "SSID und Passwort erforderlich" },
      { status: 400 }
    );
  }

  const isLinux = process.platform === "linux";

  if (!isLinux) {
    // Development fallback: simulate connection
    return NextResponse.json({
      success: true,
      ip: "192.168.1.100",
      ssid,
    });
  }

  try {
    // Connect to the WiFi network
    const { stdout, stderr } = await execAsync(
      `nmcli dev wifi connect "${ssid.replace(/"/g, '\\"')}" password "${password.replace(/"/g, '\\"')}" ifname wlan0`
    );

    if (stderr && stderr.includes("Error")) {
      return NextResponse.json(
        { success: false, error: stderr.trim() },
        { status: 400 }
      );
    }

    // Get the new IP address
    let ip = "";
    try {
      const { stdout: ipOut } = await execAsync("hostname -I");
      ip = ipOut.trim().split(" ")[0] || "";
    } catch {
      ip = "unbekannt";
    }

    // Mark WiFi as configured
    try {
      await mkdir(CONFIG_DIR, { recursive: true });
      await writeFile(
        join(CONFIG_DIR, "wifi-configured"),
        JSON.stringify({ ssid, ip, configuredAt: new Date().toISOString() })
      );
    } catch (err) {
      console.error("Failed to write wifi-configured marker:", err);
    }

    return NextResponse.json({
      success: true,
      ip,
      ssid,
      message: stdout.trim(),
    });
  } catch (err) {
    console.error("WiFi connect failed:", err);
    return NextResponse.json(
      {
        success: false,
        error: "Verbindung fehlgeschlagen. Passwort korrekt?",
      },
      { status: 500 }
    );
  }
}
