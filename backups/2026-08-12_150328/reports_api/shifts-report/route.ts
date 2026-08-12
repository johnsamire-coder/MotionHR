import { NextRequest, NextResponse } from "next/server";
const BACKEND = process.env.NEXT_PUBLIC_API_BASE || "https://jssolutions-eg.com";

export async function GET(req: NextRequest) {
  const auth = req.headers.get("authorization") || "";
  const { searchParams } = new URL(req.url);
  const query = searchParams.toString();
  const res = await fetch(
    `${BACKEND}/attendance/api/mobile/manager/reports/shifts/${query ? "?" + query : ""}`,
    { headers: { Authorization: auth, "Accept-Language": "ar" } }
  );
  return NextResponse.json(await res.json());
}
