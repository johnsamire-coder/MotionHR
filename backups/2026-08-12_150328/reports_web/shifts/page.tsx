"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Clock, Loader2, Search, Users } from "lucide-react";
import { useLangStore } from "@/lib/stores/language";
import { STORAGE_KEYS } from "@/lib/constants/config";

export default function ShiftsReportPage() {
  const lang = useLangStore((s) => s.lang);
  const ar = lang === "ar";
  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authH = token?.startsWith("Token") ? token : `Token ${token}`;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/reports/shifts-report`, { headers: { Authorization: authH } });
      const json = await res.json();
      setData(json);
    } catch {
      toast.error(ar ? "فشل تحميل التقرير" : "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const shifts = useMemo(() => {
    const list = data?.shifts || [];
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter((r: any) => `${r.shift_name || ""} ${r.shift_type || ""}`.toLowerCase().includes(q));
  }, [data, search]);

  const noShift = data?.no_shift_employees || [];

  return (
    <div className="space-y-6 pb-6" dir={ar ? "rtl" : "ltr"}>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{ar ? "تقرير الشيفتات" : "Shifts Report"}</h1>
        <p className="text-muted-foreground mt-1">{ar ? "توزيع الموظفين على الشيفتات والموظفين بدون شيفت" : "Employee distribution across shifts and employees without shift"}</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { l: ar ? "الشيفتات" : "Shifts", v: data?.shifts_count || 0, c: "text-indigo-600" },
          { l: ar ? "الموظفون" : "Employees", v: data?.total_employees || 0, c: "text-emerald-600" },
          { l: ar ? "بدون شيفت" : "No Shift", v: data?.employees_without_shifts || noShift.length || 0, c: "text-amber-600" },
        ].map((x, i) => <div key={i} className="border rounded-xl p-3 bg-white text-center"><p className={`text-xl font-bold ${x.c}`}>{x.v}</p><p className="text-xs text-muted-foreground">{x.l}</p></div>)}
      </div>

      <div className="border rounded-xl p-4 bg-white">
        <div className="relative">
          <Search className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={ar ? "بحث باسم/نوع الشيفت" : "Search by shift name/type"} className="w-full border rounded-lg px-10 py-2" />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
      ) : (
        <>
          {shifts.length === 0 ? (
            <div className="text-center py-16 border rounded-xl bg-white"><Clock className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" /><p className="text-muted-foreground">{ar ? "لا توجد بيانات" : "No data"}</p></div>
          ) : (
            <div className="space-y-4">
              {shifts.map((s: any, i: number) => (
                <div key={i} className="border rounded-xl p-4 bg-white space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold">{s.shift_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {s.shift_type} · {s.start_time} → {s.end_time}
                        {s.shift_mode && <span> · {s.shift_mode}</span>}
                        {s.crosses_midnight && <span> · {ar ? "يمتد لليوم التالي" : "Crosses Midnight"}</span>}
                      </p>
                    </div>
                    <div className="text-end">
                      <p className="text-xs text-muted-foreground">{ar ? "عدد الموظفين" : "Employees"}</p>
                      <p className="text-lg font-bold text-indigo-700">{s.employees_count}</p>
                    </div>
                  </div>
                  {Array.isArray(s.employees) && s.employees.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {s.employees.slice(0, 10).map((e: any, j: number) => (
                        <span key={j} className="text-xs bg-slate-100 rounded-full px-3 py-1">
                          {e.employee_name}
                          {e.department && <span> · {e.department}</span>}
                          {e.source && <span> · {e.source}</span>}
                          {e.employee_id && <span> · #{e.employee_id}</span>}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {noShift.length > 0 && (
            <div className="border rounded-xl p-4 bg-white">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-4 h-4 text-amber-600" />
                <p className="font-semibold">{ar ? "موظفون بدون شيفت" : "Employees Without Shift"}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {noShift.map((e: any, i: number) => (
                  <span key={i} className="text-xs bg-amber-50 text-amber-800 rounded-full px-3 py-1">
                    {e.employee_name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
