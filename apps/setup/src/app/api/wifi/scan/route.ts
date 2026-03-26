import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

interface WifiNetwork {
  ssid: string;
  signal: number;
  security: string;
  secured: boolean;
}

const MOCK_NETWORKS: WifiNetwork[] = [
  { ssid: "Werkstatt-WLAN", signal: 85, security: "WPA2", secured: true },
  { ssid: "Büro-5GHz", signal: 72, security: "WPA3", secured: true },
  { ssid: "Gast-Netzwerk", signal: 45, security: "Open", secured: false },
  { ssid: "CT-Lab-Intern", signal: 90, security: "WPA2-Enterprise", secured: true },
];

export async function GET() {
  const isLinux = process.platform === "linux";

  if (!isLinux) {
    // Development fallback: return mock data
    return NextResponse.json(MOCK_NETWORKS);
  }

  try {
    const { stdout } = await execAsync(
      "nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list --rescan yes"
    );

    const seen = new Set<string>();
    const networks: WifiNetwork[] = [];

    for (const line of stdout.trim().split("\n")) {
      if (!line) continue;
      const [ssid, signalStr, security] = line.split(":");
      if (!ssid || seen.has(ssid)) continue;
      seen.add(ssid);

      networks.push({
        ssid,
        signal: parseInt(signalStr, 10) || 0,
        security: security || "Open",
        secured: !!security && security !== "--",
      });
    }

    // Sort by signal strength descending
    networks.sort((a, b) => b.signal - a.signal);

    return NextResponse.json(networks);
  } catch (err) {
    console.error("WiFi scan failed:", err);
    return NextResponse.json(
      { error: "WLAN-Scan fehlgeschlagen" },
      { status: 500 }
    );
  }
}
