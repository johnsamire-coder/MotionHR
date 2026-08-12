"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Calendar, Loader2, Search } from "lucide-react";
import { useLangStore } from "@/lib/stores/language";
import { STORAGE_KEYS } from "@/lib/constants/config";

export default function LeavesEnhancedReportPage() {
  const lang = useLangStore((s) => s.lang);
  const ar = lang === "ar";
  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authH = token?.startsWith("Token") ? token : `Token ${token}`;
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/reports/leaves-enhanced?year=${year}&month=${month}`, { headers: { Authorization: authH } });
      const json = await res.json();
      setData(json);
    } catch {
      toast.error(ar ? "فشل تحميل التقرير" : "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [year, month]);

  const rows = useMemo(() => {
    const list = data?.employees || [];
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter((r: any) => `${r.employee_name || ""} ${r.department || ""}`.toLowerCase().includes(q));
  }, [data, search]);

  return (
    <div className="space-y-6 pb-6" dir={ar ? "rtl" : "ltr"}>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{ar ? "تقرير الإجازات المتقدم" : "Enhanced Leaves Report"}</h1>
        <p className="text-muted-foreground mt-1">{ar ? "الرصيد + الاستخدام + تفاصيل الإجازات" : "Balances, usage and leave details"}</p>
      </div>

      <div className="border rounded-xl p-4 bg-white flex flex-wrap gap-3 items-center">
        <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || now.getFullYear())} className="border rounded-lg px-3 py-2 w-28" />
        <input type="number" min="1" max="12" value={month} onChange={(e) => setMonth(Number(e.target.value) || 1)} className="border rounded-lg px-3 py-2 w-24" />
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={ar ? "بحث بالاسم / القسم" : "Search by name / dept"} className="w-full border rounded-lg px-10 py-2" />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 border rounded-xl bg-white"><Calendar className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" /><p className="text-muted-foreground">{ar ? "لا توجد بيانات" : "No data"}</p></div>
      ) : (
        <div className="space-y-4">
          {rows.map((r: any, i: number) => (
            <div key={i} className="border rounded-xl p-4 bg-white space-y-3">
              <div>
                <p className="font-bold">{r.employee_name}</p>
                <p className="text-xs text-muted-foreground">{r.department}</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "أيام معتمدة" : "Approved Days"}</p><p className="font-semibold">{r.total_approved_days}</p></div>
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "بدون راتب" : "Unpaid"}</p><p className="font-semibold">{r.unpaid_days}</p></div>
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "أنصاف أيام" : "Half Days"}</p><p className="font-semibold">{r.half_day_count}</p></div>
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "عدد الطلبات" : "Leaves Count"}</p><p className="font-semibold">{r.leaves_count}</p></div>
              </div>

              {Array.isArray(r.balances) && r.balances.length > 0 && (
                <div>
                  <p className="text-sm font-semibold mb-2">{ar ? "الأرصدة" : "Balances"}</p>
                  <div className="space-y-2">
                    {r.balances.map((b: any, j: number) => (
                      <div key={j} className="text-xs bg-slate-50 rounded px-3 py-2 flex flex-wrap gap-4">
                        <span className="font-semibold">{b.leave_type}</span>
                        <span>{ar ? "إجمالي" : "Total"}: {b.total_days}</span>
                        <span>{ar ? "مستخدم" : "Used"}: {b.used_days}</span>
                        <span>{ar ? "معلق" : "Pending"}: {b.pending_days || 0}</span>
                        <span className="text-emerald-700">{ar ? "متبقي" : "Remaining"}: {b.remaining_days}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {Array.isArray(r.leaves) && r.leaves.length > 0 && (
                <div>
                  <p className="text-sm font-semibold mb-2">{ar ? "الإجازات" : "Leaves"}</p>
                  <div className="space-y-2">
                    {r.leaves.slice(0, 5).map((lv: any, j: number) => (
                      <div key={j} className="text-xs bg-teal-50 rounded px-3 py-2 flex flex-wrap gap-4">
                        <span className="font-semibold">{lv.leave_type}</span>
                        <span>{lv.start_date} → {lv.end_date}</span>
                        <span>{lv.days_count} {ar ? "يوم" : "days"}</span>
                        <span>{ar ? "الحالة" : "Status"}: {lv.status}</span>
                        <span>{ar ? "مدفوعة" : "Paid"}: {lv.is_paid ? (ar ? "نعم" : "Yes") : (ar ? "لا" : "No")}</span>
                        <span>{ar ? "نصف يوم" : "Half Day"}: {lv.is_half_day ? (ar ? "نعم" : "Yes") : (ar ? "لا" : "No")}</span>
                        {lv.half_day_type && <span>{ar ? "نوع النصف" : "Half Type"}: {lv.half_day_type}</span>}
                        {lv.reason && <span>{ar ? "السبب" : "Reason"}: {lv.reason}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
