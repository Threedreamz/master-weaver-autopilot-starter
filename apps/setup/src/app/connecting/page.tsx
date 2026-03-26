"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface WifiStatus {
  connected: boolean;
  ssid: string;
  ip: string;
  mode: "ap" | "station";
}

export default function ConnectingPage() {
  const [status, setStatus] = useState<WifiStatus | null>(null);
  const [error, setError] = useState(false);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/wifi/status");
        const data: WifiStatus = await res.json();
        setAttempts((a) => a + 1);

        if (data.connected && data.mode === "station") {
          setStatus(data);
          clearInterval(interval);
        } else if (attempts > 30) {
          setError(true);
          clearInterval(interval);
        }
      } catch {
        // Server may be restarting during network switch
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [attempts]);

  if (error) {
    return (
      <div className="flex min-h-[80dvh] flex-col items-center justify-center gap-6 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-red-900/40">
          <svg
            className="h-10 w-10 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold">Verbindung fehlgeschlagen</h1>
        <p className="text-gray-400">
          Die WLAN-Verbindung konnte nicht hergestellt werden.
        </p>
        <Link
          href="/wifi"
          className="inline-flex h-14 items-center justify-center rounded-xl bg-gray-800 px-8 text-lg font-medium active:bg-gray-700"
        >
          Erneut versuchen
        </Link>
      </div>
    );
  }

  if (status) {
    return (
      <div className="flex min-h-[80dvh] flex-col items-center justify-center gap-6 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-green-900/40">
          <svg
            className="h-10 w-10 text-green-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>

        <div>
          <p className="text-sm font-medium text-green-400">Schritt 2/3</p>
          <h1 className="mt-1 text-2xl font-bold">Verbunden!</h1>
        </div>

        <div className="w-full rounded-xl bg-gray-900 p-6 text-left">
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Netzwerk</span>
              <span className="font-mono font-medium">{status.ssid}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">IP-Adresse</span>
              <span className="font-mono font-medium">{status.ip}</span>
            </div>
          </div>
        </div>

        <div className="w-full rounded-xl bg-blue-900/30 p-6 text-left">
          <p className="text-sm text-blue-300">
            Verbinde dein iPad jetzt mit{" "}
            <strong className="text-blue-200">{status.ssid}</strong> und
            navigiere zu:
          </p>
          <p className="mt-3 text-center font-mono text-xl font-bold text-blue-200">
            http://autopilot.local
          </p>
        </div>

        <Link
          href="/download"
          className="inline-flex h-14 w-full items-center justify-center rounded-xl bg-blue-600 text-lg font-semibold text-white active:bg-blue-700"
        >
          Schritt 3/3: Windows-PC einrichten
        </Link>

        <Link
          href="/status"
          className="text-sm text-gray-500 underline hover:text-gray-300"
        >
          Zum Systemstatus
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-[80dvh] flex-col items-center justify-center gap-6 text-center">
      <div>
        <p className="text-sm font-medium text-blue-400">Schritt 2/3</p>
        <h1 className="mt-1 text-2xl font-bold">Verbinde mit WLAN...</h1>
      </div>

      <div className="flex h-20 w-20 items-center justify-center">
        <span className="inline-block h-16 w-16 animate-spin rounded-full border-4 border-gray-700 border-t-blue-500" />
      </div>

      <p className="text-gray-400">
        Dies kann bis zu 30 Sekunden dauern. Bitte warten...
      </p>

      <p className="text-xs text-gray-600">
        Versuch {attempts} / 30
      </p>
    </div>
  );
}
