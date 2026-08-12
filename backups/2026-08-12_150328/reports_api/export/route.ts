import { NextResponse } from "next/server";
const BACKEND = "https://jssolutions-eg.com";

export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const { searchParams } = new URL(request.url);
    const qs = searchParams.toString();
    const url = `${BACKEND}/attendance/api/mobile/manager/reports/unified-export/?${qs}`;

    const res = await fetch(url, {
      headers: { Authorization: authHeader, "Host": "jssolutions-eg.com" },
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Export failed" }, { status: res.status });
    }

    const blob = await res.blob();
    const contentType = res.headers.get("content-type") || "application/octet-stream";
    const contentDisposition = res.headers.get("content-disposition") || "attachment";

    return new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": contentDisposition,
      },
    });
  } catch {
    return NextResponse.json({ error: "Network error" }, { status: 500 });
  }
}
