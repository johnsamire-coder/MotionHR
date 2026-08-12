import { NextResponse } from "next/server";

const BACKEND = "https://jssolutions-eg.com";

interface DailyStats {
  present: number;
  late: number;
  absent: number;
  on_leave: number;
  weekend: number;
  mission: number;
  no_data: number;
}

interface DailyResponse {
  date?: string;
  total_employees?: number;
  stats?: DailyStats;
}

async function fetchDaily(date: string, headers: HeadersInit): Promise<DailyResponse | null> {
  try {
    const res = await fetch(
      `${BACKEND}/attendance/api/mobile/manager/reports/daily-attendance/?date=${date}`,
      { headers, cache: "no-store" }
    );
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function isMeaningful(data: DailyResponse | null): boolean {
  if (!data?.stats) return false;
  const s = data.stats;
  // يعتبر يوم فيه بيانات لو مش كله no_data
  const total = s.present + s.late + s.absent + s.on_leave + s.weekend + s.mission;
  return total > 0;
}

export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const headers = {
    Authorization: authHeader,
    "Accept-Language": "ar",
  };

  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;

  try {
    // نبحث عن آخر يوم فيه بيانات (نرجع لحد 7 أيام)
    let effectiveDate = "";
    let effectiveData: DailyResponse | null = null;

    for (let i = 0; i < 7; i++) {
      const check = new Date();
      check.setDate(check.getDate() - i);
      const dateStr = check.toISOString().split("T")[0];

      const data = await fetchDaily(dateStr, headers);
      if (isMeaningful(data)) {
        effectiveDate = dateStr;
        effectiveData = data;
        break;
      }
    }

    // لو ملقاش، ناخد اليوم
    if (!effectiveData) {
      effectiveDate = now.toISOString().split("T")[0];
      effectiveData = await fetchDaily(effectiveDate, headers);
    }

    // باقي الـ APIs
    const [leaves, pending, payroll] = await Promise.all([
      fetch(`${BACKEND}/attendance/api/mobile/manager/reports/leaves-enhanced/?year=${year}&month=${month}`,
        { headers, cache: "no-store" }).then(r => r.json()).catch(() => null),
      fetch(`${BACKEND}/attendance/api/mobile/manager/pending/`,
        { headers, cache: "no-store" }).then(r => r.json()).catch(() => null),
      fetch(`${BACKEND}/attendance/api/mobile/manager/payroll/summary/?year=${year}&month=${month}`,
        { headers, cache: "no-store" }).then(r => r.json()).catch(() => null),
    ]);

    let totalLeaves = 0;
    if (leaves?.employees) {
      leaves.employees.forEach((emp: { leaves?: unknown[] }) => {
        totalLeaves += emp.leaves?.length || 0;
      });
    }

    const isToday = effectiveDate === now.toISOString().split("T")[0];

    return NextResponse.json({
      effective_date: effectiveDate,
      is_today: isToday,
      total_employees: effectiveData?.total_employees || 0,
      present_today: effectiveData?.stats?.present || 0,
      absent_today: effectiveData?.stats?.absent || 0,
      late_today: effectiveData?.stats?.late || 0,
      on_leave_today: effectiveData?.stats?.on_leave || 0,
      weekend_today: effectiveData?.stats?.weekend || 0,
      total_leaves_month: totalLeaves,
      pending_requests: pending?.total_pending || 0,
      total_payroll_net: payroll?.grand_total_net || 0,
    });
  } catch {
    return NextResponse.json({ error: "Network error" }, { status: 500 });
  }
}
