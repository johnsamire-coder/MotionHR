import { NextResponse } from "next/server";
const BACKEND = "https://jssolutions-eg.com";

export async function GET(request: Request) {
  const auth = request.headers.get("authorization");
  if (!auth) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const url = new URL(request.url);
  const date = url.searchParams.get("date") || new Date().toISOString().split("T")[0];
  try {
    const res = await fetch(`${BACKEND}/attendance/api/mobile/manager/reports/location-tracking/?date=${date}`, {
      headers: { Authorization: auth },
      cache: "no-store",
    });
    const text = await res.text();
    try { return NextResponse.json(JSON.parse(text), { status: res.status }); }
    catch { return NextResponse.json({ error: "Backend error" }, { status: 500 }); }
  } catch {
    return NextResponse.json({ error: "Network error" }, { status: 500 });
  }
}
