import { NextRequest, NextResponse } from "next/server";
import { readFile, stat } from "fs/promises";
import { join } from "path";

const RELEASES_DIR = "/opt/autopilot/releases";
const DEV_DIST_DIR = join(process.cwd(), "..", "..", "python", "ctpc-api", "dist");

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const filename = path.join("/");

  const isLinux = process.platform === "linux";

  // Try release directory first, then dev fallback
  const candidates = isLinux
    ? [join(RELEASES_DIR, filename), join(DEV_DIST_DIR, filename)]
    : [join(DEV_DIST_DIR, filename)];

  for (const filePath of candidates) {
    try {
      const fileStat = await stat(filePath);
      if (!fileStat.isFile()) continue;

      const fileBuffer = await readFile(filePath);

      return new NextResponse(fileBuffer, {
        headers: {
          "Content-Type": "application/octet-stream",
          "Content-Disposition": `attachment; filename="${filename.split("/").pop()}"`,
          "Content-Length": String(fileStat.size),
        },
      });
    } catch {
      continue;
    }
  }

  return NextResponse.json(
    {
      error: `Datei nicht gefunden: ${filename}`,
      hint: isLinux
        ? `Datei wird in ${RELEASES_DIR}/ oder ${DEV_DIST_DIR}/ gesucht`
        : "Download nur auf dem Raspberry Pi verfügbar",
    },
    { status: 404 }
  );
}
