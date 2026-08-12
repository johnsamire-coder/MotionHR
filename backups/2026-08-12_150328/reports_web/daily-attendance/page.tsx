"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Clock, Loader2, Search } from "lucide-react";
import { useLangStore } from "@/lib/stores/language";
import { STORAGE_KEYS } from "@/lib/constants/config";

export default function DailyAttendanceReportPage() {
  const lang = useLangStore((s) => s.lang);
  const ar = lang === "ar";
  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authH = token?.startsWith("Token") ? token : `Token ${token}`;

  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [status, setStatus] = useState("all");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/reports/daily-attendance?date=${date}`, { headers: { Authorization: authH } });
      const json = await res.json();
      setData(json);
    } catch {
      toast.error(ar ? "فشل تحميل التقرير" : "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [date]);

  const rows = useMemo(() => {
    let list = data?.employees || [];
    if (status !== "all") list = list.filter((r: any) => r.status === status);
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter((r: any) => `${r.employee_name || ""} ${r.department || ""} ${r.branch || ""}`.toLowerCase().includes(q));
  }, [data, search, status]);

  const stats = data?.stats || {};

  return (
    <div className="space-y-6 pb-6" dir={ar ? "rtl" : "ltr"}>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{ar ? "تقرير الحضور اليومي" : "Daily Attendance Report"}</h1>
        <p className="text-muted-foreground mt-1">{ar ? "حالة كل موظف في يوم محدد" : "Attendance status for all employees on a specific day"}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {[
          { l: ar ? "حاضر" : "Present", v: stats.present || 0, c: "text-emerald-600" },
          { l: ar ? "متأخر" : "Late", v: stats.late || 0, c: "text-amber-600" },
          { l: ar ? "غائب" : "Absent", v: stats.absent || 0, c: "text-red-600" },
          { l: ar ? "إجازة" : "Leave", v: stats.on_leave || 0, c: "text-blue-600" },
          { l: ar ? "ويكند" : "Weekend", v: stats.weekend || 0, c: "text-purple-600" },
          { l: ar ? "مهمة" : "Mission", v: stats.mission || 0, c: "text-teal-600" },
        ].map((x, i) => <div key={i} className="border rounded-xl p-3 bg-white text-center"><p className={`text-xl font-bold ${x.c}`}>{x.v}</p><p className="text-xs text-muted-foreground">{x.l}</p></div>)}
      </div>

      <div className="border rounded-xl p-4 bg-white flex flex-wrap gap-3 items-center">
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="border rounded-lg px-3 py-2" />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="border rounded-lg px-3 py-2 bg-white">
          <option value="all">{ar ? "الكل" : "All"}</option>
          <option value="present">{ar ? "حاضر" : "Present"}</option>
          <option value="late">{ar ? "متأخر" : "Late"}</option>
          <option value="absent">{ar ? "غائب" : "Absent"}</option>
          <option value="on_leave">{ar ? "إجازة" : "On Leave"}</option>
          <option value="weekend">{ar ? "ويكند" : "Weekend"}</option>
          <option value="mission">{ar ? "مهمة" : "Mission"}</option>
          <option value="no_data">{ar ? "لا بيانات" : "No Data"}</option>
        </select>
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={ar ? "بحث بالاسم / القسم / الفرع" : "Search by name / dept / branch"} className="w-full border rounded-lg px-10 py-2" />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 border rounded-xl bg-white"><Clock className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" /><p className="text-muted-foreground">{ar ? "لا توجد بيانات" : "No data"}</p></div>
      ) : (
        <div className="space-y-3">
          {rows.map((r: any, i: number) => (
            <div key={i} className="border rounded-xl p-4 bg-white">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold">{r.employee_name}</p>
                  <p className="text-xs text-muted-foreground">{r.department} · {r.branch}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{r.status}</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mt-3 text-sm">
                <div>IN: {r.check_in || "—"}</div>
                <div>OUT: {r.check_out || "—"}</div>
                <div>{ar ? "الشيفت" : "Shift"}: {r.shift_name || "—"}</div>
                <div>{ar ? "ساعات العمل" : "Work Hours"}: {r.work_hours}</div>
                <div>{ar ? "التأخير" : "Late"}: {r.late_minutes}</div>
                <div>{ar ? "الانصراف المبكر" : "Early Leave"}: {r.early_leave_minutes}</div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-2 text-sm">
                <div>{ar ? "الأوفرتايم" : "OT"}: {r.overtime_hours}</div>
                <div>{ar ? "ليلي" : "Night Shift"}: {r.is_night_shift ? (ar ? "نعم" : "Yes") : (ar ? "لا" : "No")}</div>
                <div>{ar ? "عمل ويكند" : "Weekend Work"}: {r.is_weekend_work ? (ar ? "نعم" : "Yes") : (ar ? "لا" : "No")}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
