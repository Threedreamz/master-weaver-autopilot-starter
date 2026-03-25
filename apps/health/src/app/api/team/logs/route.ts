import { NextResponse } from "next/server";

const CT_PC_BASE = process.env.CT_PC_URL ?? "http://localhost:4802";

export async function GET() {
  try {
    const today = new Date().toISOString().split("T")[0];
    const res = await fetch(`${CT_PC_BASE}/timelogs?date=${today}`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: "CT-PC API nicht erreichbar", status: res.status },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "Verbindung zum CT-PC fehlgeschlagen" },
      { status: 502 }
    );
  }
}
