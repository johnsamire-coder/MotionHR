"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ArrowLeft, FileText, Users, DollarSign, Download } from "lucide-react";
import { STORAGE_KEYS } from "@/lib/constants/config";
import { useLangStore } from "@/lib/stores/language";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface EosEmployee {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  department: string;
  branch: string;
  hire_date: string;
  years_of_service: number;
  basic_salary: number;
  eos_amount: number;
}

interface EosSummary {
  employees_count: number;
  total_eos_amount: number;
}

interface EosData {
  as_of_date: string;
  summary: EosSummary;
  results: EosEmployee[];
}

export default function EosReportPage() {
  const lang = useLangStore((s) => s.lang);
  const ar = lang === "ar";
  const router = useRouter();

  const [data, setData] = useState<EosData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [asOfDate, setAsOfDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [exporting, setExporting] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);

  const handleExportPdf = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
    if (!token) return;
    const authHeader = token.startsWith("Token") ? token : `Token ${token}`;
    setExportingPdf(true);
    try {
      const res = await fetch(`/api/reports/eos/export/pdf?as_of_date=${asOfDate}`, {
        headers: { Authorization: authHeader },
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `eos_report_${asOfDate}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert(ar ? "فشل التصدير" : "Export failed");
    } finally {
      setExportingPdf(false);
    }
  };

  const handleExport = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
    if (!token) return;
    const authHeader = token.startsWith("Token") ? token : `Token ${token}`;
    setExporting(true);
    try {
      const res = await fetch(`/api/reports/eos/export?as_of_date=${asOfDate}`, {
        headers: { Authorization: authHeader },
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `eos_report_${asOfDate}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert(ar ? "فشل التصدير" : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  const formatMoney = (val: number) =>
    new Intl.NumberFormat(ar ? "ar-EG" : "en-US", { minimumFractionDigits: 2 }).format(val);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
    if (!token) return;
    const authHeader = token.startsWith("Token") ? token : `Token ${token}`;

    setLoading(true);
    setError("");

    fetch(`/api/reports/eos?as_of_date=${asOfDate}`, {
      headers: { Authorization: authHeader },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) setError(d.error);
        else setData(d);
      })
      .catch(() => setError(ar ? "فشل تحميل البيانات" : "Failed to load data"))
      .finally(() => setLoading(false));
  }, [asOfDate]);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push("/hr/reports")}
          className="p-2 rounded-lg hover:bg-muted transition"
        >
          {ar ? <ArrowRight className="w-5 h-5" /> : <ArrowLeft className="w-5 h-5" />}
        </button>
        <div>
          <h1 className="text-2xl font-bold">
            {ar ? "تقرير مكافأة نهاية الخدمة" : "End of Service Report"}
          </h1>
          <p className="text-muted-foreground text-sm">
            {ar ? "المكافآت المستحقة للموظفين حتى تاريخ معين" : "EOS entitlements up to a specific date"}
          </p>
        </div>
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="p-4 flex items-center gap-4">
          <label className="text-sm font-medium">
            {ar ? "احتساب حتى تاريخ:" : "Calculate as of:"}
          </label>
          <input
            type="date"
            value={asOfDate}
            onChange={(e) => setAsOfDate(e.target.value)}
            className="border rounded-lg px-3 py-1.5 text-sm"
          />
          <button
            onClick={handleExport}
            disabled={exporting || !data}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition disabled:opacity-50 text-sm font-medium"
          >
            <Download className="w-4 h-4" />
            {exporting ? (ar ? "جاري التصدير..." : "Exporting...") : (ar ? "تصدير Excel" : "Export Excel")}
          </button>
          <button
            onClick={handleExportPdf}
            disabled={exportingPdf || !data}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50 text-sm font-medium"
          >
            <Download className="w-4 h-4" />
            {exportingPdf ? (ar ? "جاري التصدير..." : "Exporting...") : (ar ? "تصدير PDF" : "Export PDF")}
          </button>
        </CardContent>
      </Card>

      {/* Loading / Error */}
      {loading && (
        <div className="text-center py-20 text-muted-foreground">
          {ar ? "جاري التحميل..." : "Loading..."}
        </div>
      )}
      {error && (
        <div className="text-center py-10 text-red-500">{error}</div>
      )}

      {/* Summary Cards */}
      {data && !loading && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-600 flex items-center justify-center">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{ar ? "عدد الموظفين" : "Employees"}</p>
                  <p className="text-2xl font-bold">{data.summary.employees_count}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                  <DollarSign className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{ar ? "إجمالي المكافآت" : "Total EOS"}</p>
                  <p className="text-2xl font-bold">{formatMoney(data.summary.total_eos_amount)}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{ar ? "تاريخ الاحتساب" : "As of Date"}</p>
                  <p className="text-lg font-bold">{data.as_of_date}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {ar ? "تفاصيل الموظفين" : "Employee Details"}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="px-4 py-3 text-start font-medium">{ar ? "الموظف" : "Employee"}</th>
                      <th className="px-4 py-3 text-start font-medium">{ar ? "القسم" : "Department"}</th>
                      <th className="px-4 py-3 text-start font-medium">{ar ? "الفرع" : "Branch"}</th>
                      <th className="px-4 py-3 text-start font-medium">{ar ? "تاريخ التعيين" : "Hire Date"}</th>
                      <th className="px-4 py-3 text-start font-medium">{ar ? "سنوات الخدمة" : "Years"}</th>
                      <th className="px-4 py-3 text-start font-medium">{ar ? "الراتب الأساسي" : "Basic Salary"}</th>
                      <th className="px-4 py-3 text-start font-medium text-teal-700">{ar ? "المكافأة" : "EOS Amount"}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {data.results.map((emp) => (
                      <tr key={emp.employee_id} className="hover:bg-muted/30 transition">
                        <td className="px-4 py-3">
                          <div className="font-medium">{emp.employee_name}</div>
                          <div className="text-xs text-muted-foreground">{emp.employee_code}</div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{emp.department || "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground">{emp.branch || "—"}</td>
                        <td className="px-4 py-3">{emp.hire_date}</td>
                        <td className="px-4 py-3">{emp.years_of_service}</td>
                        <td className="px-4 py-3">{formatMoney(emp.basic_salary)}</td>
                        <td className="px-4 py-3 font-bold text-teal-700">{formatMoney(emp.eos_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
