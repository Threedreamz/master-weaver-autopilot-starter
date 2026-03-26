"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface SystemInfo {
  hostname: string;
  ip: string;
  version: string;
}

export default function WelcomePage() {
  const [info, setInfo] = useState<SystemInfo>({
    hostname: "autopilot",
    ip: "wird ermittelt...",
    version: "0.1.0",
  });

  useEffect(() => {
    fetch("/api/wifi/status")
      .then((r) => r.json())
      .then((data) => {
        setInfo((prev) => ({
          ...prev,
          hostname: data.hostname ?? prev.hostname,
          ip: data.ip ?? prev.ip,
        }));
      })
      .catch(() => {});
  }, []);

  return (
    <div className="flex min-h-[80dvh] flex-col items-center justify-center gap-8 text-center">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          AutoPilot CT-Scanner Setup
        </h1>
        <p className="mt-3 text-lg text-gray-400">
          Willkommen! Folge den Schritten, um deinen Scanner einzurichten.
        </p>
      </div>

      <Link
        href="/wifi"
        className="inline-flex h-16 items-center justify-center rounded-2xl bg-blue-600 px-10 text-xl font-semibold text-white transition-colors active:bg-blue-700"
      >
        Einrichtung starten
      </Link>

      <div className="mt-8 w-full rounded-xl bg-gray-900 p-6 text-left text-sm text-gray-400">
        <h2 className="mb-3 text-base font-medium text-gray-200">
          System-Info
        </h2>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Hostname</span>
            <span className="font-mono text-gray-300">{info.hostname}</span>
          </div>
          <div className="flex justify-between">
            <span>IP-Adresse</span>
            <span className="font-mono text-gray-300">{info.ip}</span>
          </div>
          <div className="flex justify-between">
            <span>Version</span>
            <span className="font-mono text-gray-300">{info.version}</span>
          </div>
        </div>
      </div>

      <div className="flex gap-4 text-sm text-gray-500">
        <Link href="/status" className="underline hover:text-gray-300">
          Systemstatus
        </Link>
        <Link href="/download" className="underline hover:text-gray-300">
          Windows-Software
        </Link>
      </div>
    </div>
  );
}
