import { NextResponse } from "next/server";

const CT_PC_BASE = process.env.CT_PC_URL ?? "http://localhost:4802";

export async function GET() {
  try {
    const today = new Date().toISOString().split("T")[0];
    const res = await fetch(`${CT_PC_BASE}/timelogs/export?date=${today}`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: "CSV Export fehlgeschlagen", status: res.status },
        { status: res.status }
      );
    }

    const csvText = await res.text();

    return new NextResponse(csvText, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="zeiterfassung-${today}.csv"`,
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Verbindung zum CT-PC fehlgeschlagen" },
      { status: 502 }
    );
  }
}
