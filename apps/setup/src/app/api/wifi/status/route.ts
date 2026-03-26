import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import { access } from "fs/promises";

const execAsync = promisify(exec);

const WIFI_CONFIGURED_PATH = "/opt/autopilot/config/wifi-configured";

export async function GET() {
  const isLinux = process.platform === "linux";

  if (!isLinux) {
    // Development fallback
    return NextResponse.json({
      connected: true,
      ssid: "Dev-Network",
      ip: "127.0.0.1",
      mode: "station" as const,
      hostname: "autopilot-dev",
    });
  }

  try {
    // Check active connections
    const { stdout: conOut } = await execAsync(
      "nmcli -t -f NAME,DEVICE,STATE con show --active"
    );

    let connected = false;
    let ssid = "";
    let mode: "ap" | "station" = "ap";

    for (const line of conOut.trim().split("\n")) {
      const [name, device, state] = line.split(":");
      if (device === "wlan0" && state === "activated") {
        connected = true;
        ssid = name;
        // If the SSID starts with "AutoPilot-" it's AP mode
        mode = name.startsWith("AutoPilot-") ? "ap" : "station";
        break;
      }
    }

    // Get current IP
    let ip = "";
    try {
      const { stdout: ipOut } = await execAsync("hostname -I");
      ip = ipOut.trim().split(" ")[0] || "";
    } catch {
      ip = "";
    }

    // Get hostname
    let hostname = "autopilot";
    try {
      const { stdout: hostOut } = await execAsync("hostname");
      hostname = hostOut.trim();
    } catch {
      // fallback
    }

    // Check if wifi was previously configured
    let configured = false;
    try {
      await access(WIFI_CONFIGURED_PATH);
      configured = true;
    } catch {
      configured = false;
    }

    return NextResponse.json({
      connected,
      ssid,
      ip,
      mode,
      hostname,
      configured,
    });
  } catch (err) {
    console.error("WiFi status check failed:", err);
    return NextResponse.json(
      { connected: false, ssid: "", ip: "", mode: "ap", hostname: "autopilot" },
      { status: 200 }
    );
  }
}
