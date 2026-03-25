"use client";

import { useEffect } from "react";

const HEARTBEAT_INTERVAL = 10_000; // 10 seconds

export function Heartbeat() {
  useEffect(() => {
    const send = () => {
      fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
    };

    // Send immediately on mount
    send();
    const id = setInterval(send, HEARTBEAT_INTERVAL);
    return () => clearInterval(id);
  }, []);

  return null; // invisible component
}
