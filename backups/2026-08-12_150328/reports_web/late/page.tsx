"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  ArrowLeft, ArrowRight, Calendar, Timer, Users, Clock,
  Search, Loader2, Download, Building2, AlertCircle,
  ChevronDown, ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow,
} from "@/components/ui/table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useDict, useLangStore } from "@/lib/stores/language";
import { STORAGE_KEYS } from "@/lib/constants/config";
import { exportToExcel, exportToPDF, type ExportColumn } from "@/lib/utils/export-report";

interface LateEmployee {
  employee_id: number;
  employee_name: string;
  employee_code?: string;
  username?: string;
  department?: string;
  total_late_days: number;
  total_late_minutes: number;
  avg_late_minutes?: number;
  late_dates?: Array<{ date: string; minutes: number }>;
}

interface LateData {
  year: number;
  month: number;
  total_employees_with_late: number;
  employees: LateEmployee[];
}

interface DeptLookup { id: number; name_ar: string; name_en: string; }

function StatCard({
  icon: Icon, label, value, subtitle, color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  subtitle?: string;
  color: string;
}) {
  return (
    <Card className="border-border/50 hover:shadow-md transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          </div>
          <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center flex-shrink-0`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LateReportPage() {
  const router = useRouter();
  const d = useDict();
  const lang = useLangStore((s) => s.lang);

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<LateData | null>(null);
  const [deptMap, setDeptMap] = useState<Record<string, DeptLookup>>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [deptFilter, setDeptFilter] = useState("all");
  const [expandedEmp, setExpandedEmp] = useState<number | null>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authHeader = token?.startsWith("Token") ? token : `Token ${token}`;

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    Promise.all([
      fetch(`/api/reports/late?year=${year}&month=${month}`, { headers: { Authorization: authHeader } }).then(r => r.json()),
      fetch("/api/departments", { headers: { Authorization: authHeader } }).then(r => r.json()),
    ]).then(([lateData, deptData]) => {
      setData(lateData);
      const depts = Array.isArray(deptData) ? deptData : deptData.departments || [];
      const dm: Record<string, DeptLookup> = {};
      depts.forEach((dp: DeptLookup) => { dm[dp.name_ar] = dp; });
      setDeptMap(dm);
    })
      .catch(() => toast.error(d.failedLoad))
      .finally(() => setLoading(false));
  }, [year, month]);

  const getDeptName = (name?: string) => {
    if (!name) return "—";
    const item = deptMap[name];
    if (!item) return name;
    return lang === "en" && item.name_en ? item.name_en : item.name_ar;
  };

  const monthNames = [
    d.January, d.February, d.March, d.April, d.May, d.June,
    d.July, d.August, d.September, d.October, d.November, d.December,
  ];

  const years = Array.from({ length: 5 }, (_, i) => now.getFullYear() - i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  const employees = data?.employees || [];
  const departments = [...new Set(employees.map(e => e.department).filter((v): v is string => Boolean(v)))].sort();

  const filtered = employees.filter(emp => {
    const matchSearch = !search ||
      emp.employee_name.toLowerCase().includes(search.toLowerCase()) ||
      (emp.employee_code || "").toLowerCase().includes(search.toLowerCase());
    const matchDept = deptFilter === "all" || emp.department === deptFilter;
    return matchSearch && matchDept;
  });

  const totalLateDays = employees.reduce((sum, e) => sum + (e.total_late_days || 0), 0);
  const totalLateMinutes = employees.reduce((sum, e) => sum + (e.total_late_minutes || 0), 0);
  const avgLate = employees.length > 0
    ? Math.round(totalLateMinutes / employees.length)
    : 0;

  const getSeverityColor = (minutes: number) => {
    if (minutes >= 120) return "bg-red-500/10 text-red-700 border-red-500/20";
    if (minutes >= 60) return "bg-amber-500/10 text-amber-700 border-amber-500/20";
    return "bg-emerald-500/10 text-emerald-700 border-emerald-500/20";
  };

  const getSeverityLabel = (minutes: number) => {
    if (minutes >= 120) return d.lateSeverityHigh;
    if (minutes >= 60) return d.lateSeverityMedium;
    return d.lateSeverityLow;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(lang === "ar" ? "ar-EG" : "en-US", {
      day: "numeric", month: "short",
    });
  };


  const handleExport = (format: "pdf" | "excel") => {
    const columns: ExportColumn[] = [
      { key: "employee_name", header: d.colEmployee, width: 30 },
      { key: "employee_code", header: d.empCode, width: 15 },
      {
        key: "department",
        header: d.colDept,
        width: 25,
        formatter: (val) => getDeptName(String(val || "")),
      },
      { key: "total_late_days", header: d.colLateDays, width: 15 },
      { key: "total_late_minutes", header: d.colLateMinutes, width: 18 },
      {
        key: "total_late_minutes",
        header: d.colAvgLate,
        width: 18,
        formatter: (val, row) => {
          const days = Number(row.total_late_days) || 0;
          const mins = Number(val) || 0;
          return days > 0 ? String(Math.round(mins / days)) : "0";
        },
      },
    ];

    const config = {
      title: d.lateReportTitle,
      subtitle: d.lateReportDesc,
      companyName: lang === "ar" ? "شركة الإنشاء والمقاولات" : "Construction & Contracting Co.",
      period: `${monthNames[month - 1]} ${year}`,
      columns,
      data: filtered as unknown as Record<string, unknown>[],
      fileName: `late_${year}_${month}`,
      lang,
      summaryStats: [
        { label: d.totalEmployeesWithLate, value: data?.total_employees_with_late || 0 },
        { label: d.totalLateDays, value: totalLateDays },
        { label: d.avgLateMinutes, value: avgLate },
      ],
    };

    if (format === "pdf") {
      exportToPDF(config);
    } else {
      exportToExcel(config);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/hr/reports")} className="gap-2">
            {lang === "ar" ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            {d.backToReports}
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{d.lateReportTitle}</h1>
            <p className="text-muted-foreground mt-1 text-sm">{d.lateReportDesc}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex items-center gap-2 bg-muted/50 rounded-lg p-1">
            <Calendar className="w-4 h-4 text-muted-foreground mx-2" />
            <Select value={String(month)} onValueChange={v => setMonth(Number(v))}>
              <SelectTrigger className="border-0 bg-transparent w-[110px] focus:ring-0"><SelectValue /></SelectTrigger>
              <SelectContent>
                {months.map(m => <SelectItem key={m} value={String(m)}>{monthNames[m - 1]}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={String(year)} onValueChange={v => setYear(Number(v))}>
              <SelectTrigger className="border-0 bg-transparent w-[90px] focus:ring-0"><SelectValue /></SelectTrigger>
              <SelectContent>
                {years.map(y => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <Button variant="outline" className="gap-2" onClick={() => handleExport("excel")}>
            <Download className="w-4 h-4" />
            {d.exportExcel}
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => handleExport("pdf")}>
            <Download className="w-4 h-4" />
            {d.exportPDF}
          </Button>
        </div>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <Card key={i}><CardContent className="p-5"><div className="h-20 bg-muted animate-pulse rounded" /></CardContent></Card>)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            icon={Users}
            label={d.totalEmployeesWithLate}
            value={data?.total_employees_with_late || 0}
            subtitle={lang === "ar" ? "موظف" : "employees"}
            color="bg-amber-500/10 text-amber-600"
          />
          <StatCard
            icon={Timer}
            label={d.totalLateDays}
            value={totalLateDays}
            subtitle={lang === "ar" ? "يوم" : "days"}
            color="bg-orange-500/10 text-orange-600"
          />
          <StatCard
            icon={Clock}
            label={d.avgLateMinutes}
            value={avgLate}
            subtitle={d.minutes}
            color="bg-red-500/10 text-red-600"
          />
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[250px]">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder={d.searchEmployees} value={search} onChange={e => setSearch(e.target.value)} className="pr-10" />
            </div>
            <Select value={deptFilter} onValueChange={setDeptFilter}>
              <SelectTrigger className="w-[200px]">
                <Building2 className="w-4 h-4 ml-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{d.allDepts}</SelectItem>
                {departments.map(dep => <SelectItem key={dep} value={dep}>{getDeptName(dep)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="border-border/50">
        <div className="p-4 border-b border-border">
          <div className="text-sm text-muted-foreground">
            {d.showingOf} <span className="font-semibold text-foreground">{filtered.length}</span> {d.of}{" "}
            <span className="font-semibold text-foreground">{employees.length}</span> {d.employee_count}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Timer className="w-8 h-8 text-muted-foreground/50" />
            </div>
            <p className="font-medium">{d.noLateData}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colEmployee}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colDept}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colLateDays}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colLateMinutes}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colAvgLate}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colLateDates}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map(emp => {
                const avgPerDay = emp.total_late_days > 0
                  ? Math.round(emp.total_late_minutes / emp.total_late_days)
                  : 0;
                const isExpanded = expandedEmp === emp.employee_id;
                return (
                  <React.Fragment key={emp.employee_id}>
                    <TableRow className="hover:bg-muted/30">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-9 h-9">
                            <AvatarFallback className="bg-brand-primary/10 text-brand-primary text-sm font-semibold">
                              {emp.employee_name?.[0]}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{emp.employee_name}</div>
                            {emp.employee_code && <div className="text-xs text-muted-foreground">{emp.employee_code}</div>}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">{getDeptName(emp.department)}</span>
                      </TableCell>
                      <TableCell className="font-mono">{emp.total_late_days}</TableCell>
                      <TableCell className="font-mono text-amber-600 font-semibold">
                        {emp.total_late_minutes} {d.minutes}
                      </TableCell>
                      <TableCell>
                        <Badge className={`${getSeverityColor(avgPerDay)} border font-medium gap-1`}>
                          <AlertCircle className="w-3 h-3" />
                          {avgPerDay} {d.minutes} - {getSeverityLabel(avgPerDay)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {emp.late_dates && emp.late_dates.length > 0 ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setExpandedEmp(isExpanded ? null : emp.employee_id)}
                            className="gap-1 h-8"
                          >
                            {emp.late_dates.length} {d.daysUnit}
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </Button>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                    </TableRow>

                    {isExpanded && emp.late_dates && emp.late_dates.length > 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="bg-muted/30">
                          <div className="flex flex-wrap gap-2 py-2">
                            <span className="text-sm font-semibold ml-2">{d.colLateDates}:</span>
                            {emp.late_dates.map((item, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className={getSeverityColor(item.minutes)}
                                dir="ltr"
                              >
                                {formatDate(item.date)} — {item.minutes} {d.minutes}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
