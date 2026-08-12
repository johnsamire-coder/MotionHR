"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { DollarSign, Loader2, Search } from "lucide-react";
import { useLangStore } from "@/lib/stores/language";
import { STORAGE_KEYS } from "@/lib/constants/config";

export default function PayrollReportPage() {
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
      const res = await fetch(`/api/reports/payroll?year=${year}&month=${month}`, {
        headers: { Authorization: authH },
      });
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
    return list.filter((r: any) =>
      `${r.employee_name || ""} ${r.department || ""} ${r.branch || ""}`.toLowerCase().includes(q)
    );
  }, [data, search]);

  const totals = data?.totals || {};

  return (
    <div className="space-y-6 pb-6" dir={ar ? "rtl" : "ltr"}>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{ar ? "تقرير الرواتب الشهري" : "Monthly Payroll Report"}</h1>
        <p className="text-muted-foreground mt-1">{ar ? "ملخص رواتب كل الموظفين بالتفصيل" : "Detailed payroll summary for all employees"}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: ar ? "عدد الموظفين" : "Employees", value: data?.employees?.length || 0, color: "text-blue-600" },
          { label: ar ? "إجمالي الرواتب" : "Gross Total", value: totals.gross_salary || 0, color: "text-emerald-600" },
          { label: ar ? "إجمالي الخصومات" : "Deductions", value: totals.total_deductions || 0, color: "text-red-600" },
          { label: ar ? "إجمالي الصافي" : "Net Total", value: totals.net_salary || 0, color: "text-purple-600" },
        ].map((c, i) => (
          <div key={i} className="border rounded-xl p-4 bg-white">
            <p className="text-xs text-muted-foreground">{c.label}</p>
            <p className={`text-2xl font-bold mt-1 ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      <div className="border rounded-xl p-4 bg-white flex flex-wrap gap-3 items-center">
        <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || now.getFullYear())} className="border rounded-lg px-3 py-2 w-28" />
        <input type="number" min="1" max="12" value={month} onChange={(e) => setMonth(Number(e.target.value) || 1)} className="border rounded-lg px-3 py-2 w-24" />
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={ar ? "بحث بالاسم / القسم / الفرع" : "Search by name / dept / branch"} className="w-full border rounded-lg px-10 py-2" />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 border rounded-xl bg-white">
          <DollarSign className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" />
          <p className="text-muted-foreground">{ar ? "لا توجد بيانات" : "No data"}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {rows.map((r: any, i: number) => (
            <div key={i} className="border rounded-xl p-4 bg-white space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold">{r.employee_name}</p>
                  <p className="text-xs text-muted-foreground">{r.employee_code} · {r.department} · {r.branch}</p>
                </div>
                <div className="text-end">
                  <p className="text-xs text-muted-foreground">{ar ? "الصافي" : "Net"}</p>
                  <p className="text-lg font-bold text-purple-700">{r.net_salary}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "أساسي" : "Basic"}</p><p className="font-semibold">{r.basic_salary}</p></div>
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "إجمالي" : "Gross"}</p><p className="font-semibold">{r.gross_salary}</p></div>
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "خصومات" : "Deductions"}</p><p className="font-semibold text-red-700">{r.total_deductions}</p></div>
                <div className="bg-slate-50 rounded-lg p-2"><p className="text-xs text-muted-foreground">{ar ? "ضريبة" : "Tax"}</p><p className="font-semibold">{r.tax_deduction || 0}</p></div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-xs text-muted-foreground">
                <div>{ar ? "المسمى" : "Job Title"}: {r.job_title || "—"}</div>
                <div>{ar ? "العملة" : "Currency"}: {r.currency || "EGP"}</div>
                <div>{ar ? "بدلات" : "Allowances"}: {r.allowances_total}</div>
                <div>{ar ? "أوفرتايم" : "Overtime"}: {r.overtime_bonus}</div>
                <div>{ar ? "بدل ليلي" : "Night"}: {r.night_allowance || 0}</div>
                <div>{ar ? "بدل ويكند" : "Weekend"}: {r.weekend_allowance || 0}</div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-xs text-muted-foreground">
                <div>{ar ? "تأمين" : "Insurance"}: {r.insurance_deduction}</div>
                <div>{ar ? "تأخير" : "Late"}: {r.late_deduction}</div>
                <div>{ar ? "غياب" : "Absence"}: {r.absence_deduction}</div>
                <div>{ar ? "انصراف مبكر" : "Early Leave"}: {r.early_leave_deduction || 0}</div>
                <div>{ar ? "بدون راتب" : "Unpaid"}: {r.unpaid_leave_deduction || 0}</div>
                <div>{ar ? "نقص مرن" : "Flex Shortage"}: {r.flex_shortage_deduction || 0}</div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs text-muted-foreground">
                <div>{ar ? "أقساط" : "Installments"}: {r.installments_total || 0}</div>
                <div>{ar ? "جزاءات" : "Penalties"}: {r.penalties_total || 0}</div>
                <div>{ar ? "أيام الحضور" : "Attended Days"}: {r.attended_days || 0}</div>
                <div>{ar ? "أيام التأخير" : "Late Days"}: {r.late_days || 0}</div>
                <div>{ar ? "أيام إجازة" : "Leave Days"}: {r.on_leave_days || 0}</div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs text-muted-foreground">
                <div>{ar ? "إجمالي دقائق التأخير" : "Late Minutes"}: {r.total_late_minutes || 0}</div>
                <div>{ar ? "أيام الغياب" : "Absent Days"}: {r.absent_days || 0}</div>
                <div>{ar ? "السياسة" : "Policy"}: {r.policy_name || "—"}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
