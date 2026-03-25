import { readFile } from "node:fs/promises";
import si from "systeminformation";
import { networkInterfaces } from "node:os";

/**
 * Get CPU temperature.
 * Tries /sys/class/thermal first (Linux/Pi), falls back to systeminformation.
 */
export async function getCpuTemperature(): Promise<number | null> {
  // Try Linux thermal zone (fastest on Pi)
  try {
    const raw = await readFile("/sys/class/thermal/thermal_zone0/temp", "utf-8");
    const millidegrees = parseInt(raw.trim(), 10);
    if (!isNaN(millidegrees)) {
      return millidegrees / 1000;
    }
  } catch {
    // Not Linux or no thermal zone
  }

  // Fall back to systeminformation
  try {
    const temp = await si.cpuTemperature();
    return temp.main ?? null;
  } catch {
    return null;
  }
}

/**
 * Get memory usage info.
 */
export async function getMemoryInfo(): Promise<{
  totalMB: number;
  usedMB: number;
  freeMB: number;
  usedPercent: number;
}> {
  try {
    const mem = await si.mem();
    const totalMB = Math.round(mem.total / 1024 / 1024);
    const usedMB = Math.round(mem.used / 1024 / 1024);
    const freeMB = Math.round(mem.free / 1024 / 1024);
    const usedPercent = Math.round((mem.used / mem.total) * 100);
    return { totalMB, usedMB, freeMB, usedPercent };
  } catch {
    // Fallback using process.memoryUsage
    const usage = process.memoryUsage();
    return {
      totalMB: 0,
      usedMB: Math.round(usage.rss / 1024 / 1024),
      freeMB: 0,
      usedPercent: 0,
    };
  }
}

/**
 * Get disk usage info for the root partition.
 */
export async function getDiskInfo(): Promise<{
  totalGB: number;
  usedGB: number;
  freeGB: number;
  usedPercent: number;
}> {
  try {
    const disks = await si.fsSize();
    const root = disks.find((d) => d.mount === "/") ?? disks[0];
    if (!root) {
      return { totalGB: 0, usedGB: 0, freeGB: 0, usedPercent: 0 };
    }
    return {
      totalGB: Math.round((root.size / 1024 / 1024 / 1024) * 10) / 10,
      usedGB: Math.round((root.used / 1024 / 1024 / 1024) * 10) / 10,
      freeGB: Math.round(((root.size - root.used) / 1024 / 1024 / 1024) * 10) / 10,
      usedPercent: Math.round(root.use),
    };
  } catch {
    return { totalGB: 0, usedGB: 0, freeGB: 0, usedPercent: 0 };
  }
}

/**
 * Get network interface info (IP addresses).
 */
export function getNetworkInfo(): Array<{ iface: string; ip4: string; ip6: string; mac: string }> {
  const ifaces = networkInterfaces();
  const result: Array<{ iface: string; ip4: string; ip6: string; mac: string }> = [];

  for (const [name, addrs] of Object.entries(ifaces)) {
    if (!addrs || name === "lo") continue;

    const ip4 = addrs.find((a) => a.family === "IPv4" && !a.internal);
    const ip6 = addrs.find((a) => a.family === "IPv6" && !a.internal);

    if (ip4 || ip6) {
      result.push({
        iface: name,
        ip4: ip4?.address ?? "",
        ip6: ip6?.address ?? "",
        mac: ip4?.mac ?? ip6?.mac ?? "",
      });
    }
  }

  return result;
}
