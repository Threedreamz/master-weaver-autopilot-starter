"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface DeviceInfo {
  ip: string;
  port: number;
  hostname: string;
  version?: string;
  lastSeen: string;
  meta?: Record<string, unknown>;
}

interface StatusData {
  /** Haupt-Pi self-status */
  hauptPi: {
    cpuPercent: number;
    ramPercent: number;
    temperature: number;
    uptime: string;
    hostname: string;
  };
  /** Kamera-Pi from discovery */
  cameraPi: DeviceInfo | null;
  /** Windows CT-PC from discovery */
  ctpc: DeviceInfo | null;
  /** iPad heartbeat count */
  clients: number;
  wifiSsid: string;
}

function timeSince(iso: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(iso).getTime()) / 1000
  );
  if (seconds < 60) return `vor ${seconds}s`;
  if (seconds < 3600) return `vor ${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `vor ${Math.floor(seconds / 3600)}h`;
  return `vor ${Math.floor(seconds / 86400)}d`;
}

function StatusCard({
  title,
  status,
  children,
}: {
  title: string;
  status: "ok" | "warning" | "error";
  children: React.ReactNode;
}) {
  const ring =
    status === "ok"
      ? "ring-green-800"
      : status === "warning"
        ? "ring-yellow-800"
        : "ring-red-800";
  const dot =
    status === "ok"
      ? "bg-green-400"
      : status === "warning"
        ? "bg-yellow-400"
        : "bg-red-400";

  return (
    <div className={`rounded-xl bg-gray-900 p-5 ring-1 ${ring}`}>
      <div className="mb-3 flex items-center gap-2">
        <span className={`inline-block h-3 w-3 rounded-full ${dot}`} />
        <h2 className="text-base font-semibold">{title}</h2>
      </div>
      <div className="space-y-2 text-sm text-gray-400">{children}</div>
    </div>
  );
}

function Row({ label, value, className }: { label: string; value: React.ReactNode; className?: string }) {
  return (
    <div className="flex justify-between">
      <span>{label}</span>
      <span className={className ?? "text-gray-300"}>{value}</span>
    </div>
  );
}

/** Is a device considered online? (seen within last 60 seconds) */
function isOnline(device: DeviceInfo | null): boolean {
  if (!device) return false;
  const age = Date.now() - new Date(device.lastSeen).getTime();
  return age < 60_000;
}

export default function StatusPage() {
  const [data, setData] = useState<StatusData | null>(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [wifiRes, discoveryRes] = await Promise.all([
          fetch("/api/wifi/status"),
          fetch("/api/discovery"),
        ]);
        const wifi = await wifiRes.json();
        const discovery = await discoveryRes.json();

        const devices = discovery.devices ?? {};

        setData({
          hauptPi: {
            cpuPercent: 0,
            ramPercent: 0,
            temperature: 0,
            uptime: "",
            hostname: wifi.hostname ?? "autopilot",
          },
          cameraPi: devices.camera ?? null,
          ctpc: devices.ctpc ?? null,
          clients: 0,
          wifiSsid: wifi.ssid ?? "\u2014",
        });
      } catch {
        // Status fetch failed
      }
    }

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const cameraPiOnline = isOnline(data?.cameraPi ?? null);
  const ctpcOnline = isOnline(data?.ctpc ?? null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Systemstatus</h1>
        <p className="mt-1 text-sm text-gray-400">
          4 Geräte &middot; Aktualisiert alle 5 Sekunden
        </p>
      </div>

      <div className="space-y-4">
        {/* --- Haupt-Pi (self) --- */}
        <StatusCard title="Haupt-Pi" status={data ? "ok" : "warning"}>
          <Row label="Hostname" value={data?.hauptPi.hostname ?? "\u2014"} />
          <Row label="CPU" value={`${data?.hauptPi.cpuPercent ?? "\u2014"}%`} />
          <Row label="RAM" value={`${data?.hauptPi.ramPercent ?? "\u2014"}%`} />
          <Row label="WLAN" value={data?.wifiSsid ?? "\u2014"} />
          <Row label="Status" value="Immer online" className="text-green-400" />
        </StatusCard>

        {/* --- Kamera-Pi --- */}
        <StatusCard
          title="Kamera-Pi"
          status={cameraPiOnline ? "ok" : data?.cameraPi ? "warning" : "error"}
        >
          <Row
            label="Status"
            value={cameraPiOnline ? "Online" : "Nicht verbunden"}
            className={cameraPiOnline ? "text-green-400" : "text-red-400"}
          />
          {data?.cameraPi && (
            <>
              <Row
                label="IP"
                value={data.cameraPi.ip}
                className="font-mono text-gray-300"
              />
              <Row label="Port" value={data.cameraPi.port} />
              <Row label="Hostname" value={data.cameraPi.hostname} />
              {data.cameraPi.meta?.cameraCount != null && (
                <Row
                  label="Kameras"
                  value={`${data.cameraPi.meta.cameraCount} erkannt`}
                />
              )}
              <Row
                label="Zuletzt gesehen"
                value={timeSince(data.cameraPi.lastSeen)}
              />
            </>
          )}
        </StatusCard>

        {/* --- Windows CT-PC --- */}
        <StatusCard
          title="Windows CT-PC"
          status={ctpcOnline ? "ok" : data?.ctpc ? "warning" : "error"}
        >
          <Row
            label="Status"
            value={ctpcOnline ? "Verbunden" : "Nicht verbunden"}
            className={ctpcOnline ? "text-green-400" : "text-red-400"}
          />
          {data?.ctpc && (
            <>
              <Row
                label="IP"
                value={data.ctpc.ip}
                className="font-mono text-gray-300"
              />
              <Row label="Hostname" value={data.ctpc.hostname} />
              {data.ctpc.version && (
                <Row label="WinWerth Version" value={data.ctpc.version} />
              )}
              <Row
                label="Zuletzt gesehen"
                value={timeSince(data.ctpc.lastSeen)}
              />
            </>
          )}
        </StatusCard>

        {/* --- iPad Clients --- */}
        <StatusCard
          title="iPad Clients"
          status={data && data.clients > 0 ? "ok" : "warning"}
        >
          <Row label="Verbundene iPads" value={data?.clients ?? 0} />
        </StatusCard>
      </div>

      <div className="flex flex-col gap-3 pt-4">
        <button
          onClick={async () => {
            if (
              confirm("Setup wirklich zurücksetzen? Der Pi wechselt zurück in den AP-Modus.")
            ) {
              // TODO: POST /api/wifi/reset
            }
          }}
          className="flex h-14 w-full items-center justify-center rounded-xl bg-red-900/40 text-base font-medium text-red-300 ring-1 ring-red-800 active:bg-red-900/60"
        >
          Setup zurücksetzen
        </button>

        <a
          href="http://autopilot.local:4800"
          target="_blank"
          rel="noopener noreferrer"
          className="flex h-14 w-full items-center justify-center rounded-xl bg-gray-800 text-base font-medium text-blue-400 active:bg-gray-700"
        >
          Zur Scanner-App &rarr;
        </a>

        <Link
          href="/"
          className="inline-flex h-12 items-center text-sm text-gray-500 underline hover:text-gray-300"
        >
          Zurück zur Übersicht
        </Link>
      </div>
    </div>
  );
}
