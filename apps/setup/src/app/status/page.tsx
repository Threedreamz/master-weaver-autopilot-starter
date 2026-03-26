"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface PiStatus {
  cameras: number;
  cpuPercent: number;
  ramPercent: number;
  temperature: number;
  hostname: string;
}

interface CtpcStatus {
  connected: boolean;
  ip: string;
  version: string;
  hostname: string;
}

interface StatusData {
  pi: PiStatus;
  ctpc: CtpcStatus;
  clients: number;
  wifiSsid: string;
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

export default function StatusPage() {
  const [data, setData] = useState<StatusData | null>(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [wifiRes, ctpcRes] = await Promise.all([
          fetch("/api/wifi/status"),
          fetch("/api/discovery"),
        ]);
        const wifi = await wifiRes.json();
        const ctpc = await ctpcRes.json();

        setData({
          pi: {
            cameras: 2,
            cpuPercent: 0,
            ramPercent: 0,
            temperature: 0,
            hostname: wifi.hostname ?? "autopilot",
          },
          ctpc: ctpc.registered
            ? {
                connected: true,
                ip: ctpc.ip,
                version: ctpc.version,
                hostname: ctpc.hostname,
              }
            : { connected: false, ip: "", version: "", hostname: "" },
          clients: 0,
          wifiSsid: wifi.ssid ?? "—",
        });
      } catch {
        // Status fetch failed
      }
    }

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Systemstatus</h1>
        <p className="mt-1 text-sm text-gray-400">
          Aktualisiert alle 5 Sekunden
        </p>
      </div>

      <div className="space-y-4">
        <StatusCard
          title="Raspberry Pi"
          status={data ? "ok" : "warning"}
        >
          <div className="flex justify-between">
            <span>Kameras</span>
            <span className="text-gray-300">
              {data?.pi.cameras ?? "—"} erkannt
            </span>
          </div>
          <div className="flex justify-between">
            <span>CPU</span>
            <span className="text-gray-300">
              {data?.pi.cpuPercent ?? "—"}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>RAM</span>
            <span className="text-gray-300">
              {data?.pi.ramPercent ?? "—"}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>WLAN</span>
            <span className="text-gray-300">{data?.wifiSsid ?? "—"}</span>
          </div>
        </StatusCard>

        <StatusCard
          title="CT-PC (Windows)"
          status={data?.ctpc.connected ? "ok" : "error"}
        >
          <div className="flex justify-between">
            <span>Status</span>
            <span
              className={
                data?.ctpc.connected ? "text-green-400" : "text-red-400"
              }
            >
              {data?.ctpc.connected ? "Verbunden" : "Nicht verbunden"}
            </span>
          </div>
          {data?.ctpc.connected && (
            <>
              <div className="flex justify-between">
                <span>IP</span>
                <span className="font-mono text-gray-300">
                  {data.ctpc.ip}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Version</span>
                <span className="text-gray-300">{data.ctpc.version}</span>
              </div>
            </>
          )}
        </StatusCard>

        <StatusCard
          title="iPad Clients"
          status={data && data.clients > 0 ? "ok" : "warning"}
        >
          <div className="flex justify-between">
            <span>Verbundene iPads</span>
            <span className="text-gray-300">{data?.clients ?? 0}</span>
          </div>
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
