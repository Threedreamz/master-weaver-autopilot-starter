"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Network {
  ssid: string;
  signal: number;
  security: string;
  secured: boolean;
}

function SignalBars({ signal }: { signal: number }) {
  const bars = signal >= 75 ? 4 : signal >= 50 ? 3 : signal >= 25 ? 2 : 1;
  return (
    <div className="flex items-end gap-0.5">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={`w-1.5 rounded-sm ${
            i <= bars ? "bg-green-400" : "bg-gray-700"
          }`}
          style={{ height: `${i * 5 + 4}px` }}
        />
      ))}
    </div>
  );
}

export default function WifiPage() {
  const router = useRouter();
  const [networks, setNetworks] = useState<Network[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scanNetworks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/wifi/scan");
      const data = await res.json();
      setNetworks(data);
    } catch {
      setError("WLAN-Scan fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    scanNetworks();
  }, [scanNetworks]);

  async function handleConnect() {
    if (!selected || !password) return;
    setConnecting(true);
    setError(null);
    try {
      const res = await fetch("/api/wifi/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ssid: selected, password }),
      });
      const data = await res.json();
      if (data.success) {
        router.push("/connecting");
      } else {
        setError(data.error ?? "Verbindung fehlgeschlagen");
        setConnecting(false);
      }
    } catch {
      setError("Verbindung fehlgeschlagen");
      setConnecting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-blue-400">Schritt 1/3</p>
        <h1 className="mt-1 text-2xl font-bold">WLAN verbinden</h1>
        <p className="mt-2 text-gray-400">
          Wähle dein Netzwerk aus und gib das Passwort ein.
        </p>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Verfügbare Netzwerke</h2>
        <button
          onClick={scanNetworks}
          disabled={loading}
          className="flex h-12 items-center gap-2 rounded-xl bg-gray-800 px-4 text-sm text-gray-300 active:bg-gray-700"
        >
          {loading ? (
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-500 border-t-gray-200" />
          ) : (
            "Aktualisieren"
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-red-900/40 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {loading && networks.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            <span className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-gray-300" />
            <p className="mt-3">Suche nach Netzwerken...</p>
          </div>
        ) : (
          networks.map((net) => (
            <button
              key={net.ssid}
              onClick={() => {
                setSelected(net.ssid);
                setPassword("");
                setError(null);
              }}
              className={`flex w-full items-center justify-between rounded-xl p-5 text-left transition-colors ${
                selected === net.ssid
                  ? "bg-blue-900/40 ring-2 ring-blue-500"
                  : "bg-gray-900 active:bg-gray-800"
              }`}
            >
              <div className="flex items-center gap-3">
                {net.secured && (
                  <svg
                    className="h-5 w-5 text-gray-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                <div>
                  <p className="text-base font-medium">{net.ssid}</p>
                  <p className="text-xs text-gray-500">{net.security}</p>
                </div>
              </div>
              <SignalBars signal={net.signal} />
            </button>
          ))
        )}
      </div>

      {selected && (
        <div className="space-y-4 rounded-xl bg-gray-900 p-5">
          <label className="block text-sm font-medium text-gray-300">
            Passwort für &quot;{selected}&quot;
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="WLAN-Passwort eingeben"
            className="h-12 w-full rounded-xl bg-gray-800 px-4 text-base text-gray-100 placeholder-gray-500 outline-none ring-1 ring-gray-700 focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
          <button
            onClick={handleConnect}
            disabled={!password || connecting}
            className="flex h-14 w-full items-center justify-center rounded-xl bg-blue-600 text-lg font-semibold text-white transition-colors active:bg-blue-700 disabled:opacity-50"
          >
            {connecting ? (
              <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              "Verbinden"
            )}
          </button>
        </div>
      )}
    </div>
  );
}
