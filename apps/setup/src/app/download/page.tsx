"use client";

import Link from "next/link";

export default function DownloadPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-medium text-blue-400">Schritt 3/3</p>
        <h1 className="mt-1 text-2xl font-bold">WerthAutopilot für Windows</h1>
        <p className="mt-2 text-gray-400">
          Lade die Windows-Software herunter, um den CT-Scanner mit deinem PC zu
          verbinden.
        </p>
      </div>

      <a
        href="/api/download/WerthAutopilot.exe"
        className="flex h-16 w-full items-center justify-center rounded-2xl bg-blue-600 text-xl font-semibold text-white transition-colors active:bg-blue-700"
      >
        Download starten
      </a>

      <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
        <span>WerthAutopilot.exe</span>
        <span>~25 MB</span>
        <span>v0.1.0</span>
      </div>

      <div className="rounded-xl bg-gray-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Installationsanleitung</h2>
        <ol className="space-y-4 text-gray-300">
          <li className="flex gap-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-900 text-sm font-bold text-blue-300">
              1
            </span>
            <div>
              <p className="font-medium">Herunterladen</p>
              <p className="text-sm text-gray-500">
                Klicke oben auf &quot;Download starten&quot;
              </p>
            </div>
          </li>
          <li className="flex gap-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-900 text-sm font-bold text-blue-300">
              2
            </span>
            <div>
              <p className="font-medium">Doppelklick auf WerthAutopilot.exe</p>
              <p className="text-sm text-gray-500">
                Windows SmartScreen: &quot;Trotzdem ausführen&quot; klicken
              </p>
            </div>
          </li>
          <li className="flex gap-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-900 text-sm font-bold text-blue-300">
              3
            </span>
            <div>
              <p className="font-medium">Windows Firewall: Port 4802 erlauben</p>
              <p className="text-sm text-gray-500">
                Die Firewall-Abfrage mit &quot;Zugriff erlauben&quot; bestätigen
              </p>
            </div>
          </li>
          <li className="flex gap-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-900 text-sm font-bold text-blue-300">
              4
            </span>
            <div>
              <p className="font-medium">
                Programm verbindet sich automatisch
              </p>
              <p className="text-sm text-gray-500">
                Die Software sucht den AutoPilot im Netzwerk und verbindet sich
              </p>
            </div>
          </li>
        </ol>
      </div>

      <div className="rounded-xl bg-gray-900 p-6">
        <h2 className="mb-3 text-base font-semibold text-gray-200">
          Systemanforderungen
        </h2>
        <ul className="space-y-2 text-sm text-gray-400">
          <li className="flex justify-between">
            <span>Betriebssystem</span>
            <span className="text-gray-300">Windows 10/11 (64-Bit)</span>
          </li>
          <li className="flex justify-between">
            <span>Netzwerk</span>
            <span className="text-gray-300">Gleiches WLAN wie AutoPilot</span>
          </li>
          <li className="flex justify-between">
            <span>Port</span>
            <span className="font-mono text-gray-300">4802 (TCP)</span>
          </li>
        </ul>
      </div>

      <Link
        href="/"
        className="inline-flex h-12 items-center text-sm text-gray-500 underline hover:text-gray-300"
      >
        Zurück zur Übersicht
      </Link>
    </div>
  );
}
