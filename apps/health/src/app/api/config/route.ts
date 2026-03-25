import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/**
 * GET /api/config
 *
 * Returns the current deployment configuration for the admin dashboard.
 * Factory equipment URLs are configured via env vars — when running on
 * Railway these will be unreachable (factory network is offline from
 * Railway's perspective), so the dashboard shows last-known state.
 */
export async function GET() {
  const ctpcUrl = process.env.CTPC_URL ?? null;
  const piUrl = process.env.PI_URL ?? null;
  const ipadUrl = process.env.IPAD_URL ?? null;
  const webhookSecret = process.env.WEBHOOK_SECRET ? true : false;

  // Determine factory network reachability
  let factoryReachable = false;
  if (ctpcUrl) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const res = await fetch(`${ctpcUrl}/api/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      factoryReachable = res.ok;
    } catch {
      factoryReachable = false;
    }
  }

  return NextResponse.json({
    environment: process.env.RAILWAY_ENVIRONMENT ?? process.env.NODE_ENV ?? "development",
    factoryNetwork: {
      reachable: factoryReachable,
      lastChecked: new Date().toISOString(),
      ctpcUrl: ctpcUrl ? "(configured)" : null,
      piUrl: piUrl ? "(configured)" : null,
      ipadUrl: ipadUrl ? "(configured)" : null,
    },
    webhookEnabled: webhookSecret,
    port: Number(process.env.PORT) || 4803,
    railwayService: process.env.RAILWAY_SERVICE_NAME ?? null,
    railwayUrl: process.env.RAILWAY_PUBLIC_DOMAIN
      ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
      : null,
  });
}
