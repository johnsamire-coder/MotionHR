"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { FileText, Loader2, Search } from "lucide-react";
import { useLangStore } from "@/lib/stores/language";
import { STORAGE_KEYS } from "@/lib/constants/config";

export default function RequestsReportPage() {
  const lang = useLangStore((s) => s.lang);
  const ar = lang === "ar";
  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authH = token?.startsWith("Token") ? token : `Token ${token}`;
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [status, setStatus] = useState("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const q = new URLSearchParams({ year: String(year), month: String(month) });
      if (status) q.set("status", status);
      const res = await fetch(`/api/reports/requests-report?${q.toString()}`, { headers: { Authorization: authH } });
      const json = await res.json();
      setData(json);
    } catch {
      toast.error(ar ? "فشل تحميل التقرير" : "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [year, month, status]);

  const rows = useMemo(() => {
    const list = data?.details || [];
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter((r: any) => `${r.employee_name || ""} ${r.request_type || ""} ${r.subject || ""}`.toLowerCase().includes(q));
  }, [data, search]);

  return (
    <div className="space-y-6 pb-6" dir={ar ? "rtl" : "ltr"}>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{ar ? "تقرير الطلبات" : "Requests Report"}</h1>
        <p className="text-muted-foreground mt-1">{ar ? "ملخص حالات الطلبات وتفاصيلها" : "Summary and details of requests by status"}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { l: ar ? "الإجمالي" : "Total", v: data?.total_requests || 0, c: "text-slate-700" },
          { l: ar ? "موافق" : "Approved", v: data?.approved || 0, c: "text-emerald-600" },
          { l: ar ? "معلق" : "Pending", v: data?.pending || 0, c: "text-amber-600" },
          { l: ar ? "مرفوض" : "Rejected", v: data?.rejected || 0, c: "text-red-600" },
        ].map((x, i) => <div key={i} className="border rounded-xl p-3 bg-white text-center"><p className={`text-xl font-bold ${x.c}`}>{x.v}</p><p className="text-xs text-muted-foreground">{x.l}</p></div>)}
      </div>

      <div className="border rounded-xl p-4 bg-white flex flex-wrap gap-3 items-center">
        <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || now.getFullYear())} className="border rounded-lg px-3 py-2 w-28" />
        <input type="number" min="1" max="12" value={month} onChange={(e) => setMonth(Number(e.target.value) || 1)} className="border rounded-lg px-3 py-2 w-24" />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="border rounded-lg px-3 py-2 bg-white">
          <option value="">{ar ? "كل الحالات" : "All statuses"}</option>
          <option value="approved">{ar ? "موافق" : "Approved"}</option>
          <option value="pending">{ar ? "معلق" : "Pending"}</option>
          <option value="rejected">{ar ? "مرفوض" : "Rejected"}</option>
        </select>
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={ar ? "بحث بالاسم / النوع / الموضوع" : "Search by name / type / subject"} className="w-full border rounded-lg px-10 py-2" />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 border rounded-xl bg-white"><FileText className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" /><p className="text-muted-foreground">{ar ? "لا توجد بيانات" : "No data"}</p></div>
      ) : (
        <div className="space-y-3">
          {rows.map((r: any, i: number) => (
            <div key={i} className="border rounded-xl p-4 bg-white">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold">{r.employee_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {r.request_type}
                    {r.employee_id && <span> · #{r.employee_id}</span>}
                    {r.id && <span> · Req#{r.id}</span>}
                  </p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{r.status}</span>
              </div>
              <p className="text-sm mt-2">{r.subject || "—"}</p>
              <p className="text-xs text-muted-foreground mt-1">{r.created_at || ""}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
