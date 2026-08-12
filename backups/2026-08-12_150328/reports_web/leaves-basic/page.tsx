"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  ArrowLeft, ArrowRight, Calendar, Activity, CheckCircle2, Clock, XCircle,
  Search, Filter, Loader2, Download, Building2,
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

interface LeaveDetail {
  id: number;
  employee_id?: number;
  employee_name?: string;
  department?: string;
  leave_type?: string;
  leave_type_en?: string;
  start_date?: string;
  end_date?: string;
  days_count?: number;
  status?: string;
}

interface LeavesBasicData {
  year: number;
  month: number;
  total_leaves: number;
  approved: number;
  rejected: number;
  pending: number;
  employees: LeaveDetail[];
}

function StatCard({
  icon: Icon, label, value, color, active, onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  color: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <Card
      className={`border transition-all cursor-pointer hover:shadow-md ${
        active ? "border-brand-primary shadow-md" : "border-border/50"
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-xl font-bold">{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LeavesBasicReportPage() {
  const router = useRouter();
  const d = useDict();
  const lang = useLangStore((s) => s.lang);

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<LeavesBasicData | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authHeader = token?.startsWith("Token") ? token : `Token ${token}`;

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetch(`/api/reports/leaves-basic?year=${year}&month=${month}&status=${statusFilter}`, {
      headers: { Authorization: authHeader },
    })
      .then(r => r.json())
      .then(setData)
      .catch(() => toast.error(d.failedLoad))
      .finally(() => setLoading(false));
  }, [year, month, statusFilter]);

  const monthNames = [
    d.January, d.February, d.March, d.April, d.May, d.June,
    d.July, d.August, d.September, d.October, d.November, d.December,
  ];

  const years = Array.from({ length: 5 }, (_, i) => now.getFullYear() - i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  const leaves = data?.employees || [];

  const filtered = leaves.filter(lv => {
    const matchSearch = !search ||
      (lv.employee_name || "").toLowerCase().includes(search.toLowerCase());
    return matchSearch;
  });

  const getStatusBadge = (status?: string) => {
    const map: Record<string, { label: string; color: string; icon: React.ComponentType<{ className?: string }> }> = {
      approved: { label: d.leaveApproved, color: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20", icon: CheckCircle2 },
      pending: { label: d.leavePending, color: "bg-amber-500/10 text-amber-700 border-amber-500/20", icon: Clock },
      rejected: { label: d.leaveRejected, color: "bg-red-500/10 text-red-700 border-red-500/20", icon: XCircle },
    };
    const info = map[status || ""] || map.pending;
    const Icon = info.icon;
    return (
      <Badge className={`${info.color} border font-medium gap-1`}>
        <Icon className="w-3 h-3" />
        {info.label}
      </Badge>
    );
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString(lang === "ar" ? "ar-EG" : "en-US", {
      day: "numeric", month: "short", year: "numeric",
    });
  };

  const getLeaveTypeName = (lv: LeaveDetail) => {
    return lang === "en" && lv.leave_type_en ? lv.leave_type_en : (lv.leave_type || "—");
  };


  const handleExport = (format: "pdf" | "excel") => {
    const columns: ExportColumn[] = [
      { key: "employee_name", header: d.colEmployee, width: 30 },
      { key: "department", header: d.colDept, width: 25 },
      {
        key: "leave_type",
        header: d.colLeaveType,
        width: 20,
        formatter: (val, row) => {
          if (lang === "en" && row.leave_type_en) return String(row.leave_type_en);
          return String(val || "—");
        },
      },
      { key: "start_date", header: d.colStartDate, width: 15 },
      { key: "end_date", header: d.colEndDate, width: 15 },
      { key: "days_count", header: d.colDaysCount, width: 12 },
      { key: "status", header: d.colLeaveStatus, width: 15 },
    ];

    const config = {
      title: d.leavesBasicTitle,
      subtitle: d.leavesBasicDesc,
      companyName: lang === "ar" ? "شركة الإنشاء والمقاولات" : "Construction & Contracting Co.",
      period: `${monthNames[month - 1]} ${year}`,
      columns,
      data: filtered as unknown as Record<string, unknown>[],
      fileName: `leaves_${year}_${month}`,
      lang,
      summaryStats: [
        { label: d.totalLeaves, value: data?.total_leaves || 0 },
        { label: d.approvedLeaves, value: data?.approved || 0 },
        { label: d.pendingLeaves, value: data?.pending || 0 },
        { label: d.rejectedLeaves, value: data?.rejected || 0 },
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
            <h1 className="text-3xl font-bold tracking-tight">{d.leavesBasicTitle}</h1>
            <p className="text-muted-foreground mt-1 text-sm">{d.leavesBasicDesc}</p>
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => <Card key={i}><CardContent className="p-4"><div className="h-16 bg-muted animate-pulse rounded" /></CardContent></Card>)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard
            icon={Activity}
            label={d.totalLeaves}
            value={data?.total_leaves || 0}
            color="bg-blue-500/10 text-blue-600"
            active={statusFilter === "all"}
            onClick={() => setStatusFilter("all")}
          />
          <StatCard
            icon={CheckCircle2}
            label={d.approvedLeaves}
            value={data?.approved || 0}
            color="bg-emerald-500/10 text-emerald-600"
            active={statusFilter === "approved"}
            onClick={() => setStatusFilter(statusFilter === "approved" ? "all" : "approved")}
          />
          <StatCard
            icon={Clock}
            label={d.pendingLeaves}
            value={data?.pending || 0}
            color="bg-amber-500/10 text-amber-600"
            active={statusFilter === "pending"}
            onClick={() => setStatusFilter(statusFilter === "pending" ? "all" : "pending")}
          />
          <StatCard
            icon={XCircle}
            label={d.rejectedLeaves}
            value={data?.rejected || 0}
            color="bg-red-500/10 text-red-600"
            active={statusFilter === "rejected"}
            onClick={() => setStatusFilter(statusFilter === "rejected" ? "all" : "rejected")}
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
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="w-4 h-4 ml-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{d.filterAll}</SelectItem>
                <SelectItem value="approved">{d.leaveApproved}</SelectItem>
                <SelectItem value="pending">{d.leavePending}</SelectItem>
                <SelectItem value="rejected">{d.leaveRejected}</SelectItem>
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
            <span className="font-semibold text-foreground">{leaves.length}</span>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Calendar className="w-8 h-8 text-muted-foreground/50" />
            </div>
            <p className="font-medium">{d.noLeavesData}</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colEmployee}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colLeaveType}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colStartDate}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colEndDate}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colDaysCount}</TableHead>
                <TableHead className={lang === "ar" ? "text-right" : "text-left"}>{d.colLeaveStatus}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map(lv => (
                <TableRow key={lv.id} className="hover:bg-muted/30">
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="w-9 h-9">
                        <AvatarFallback className="bg-brand-primary/10 text-brand-primary text-sm font-semibold">
                          {lv.employee_name?.[0] || "?"}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium">{lv.employee_name || "—"}</div>
                        {lv.department && (
                          <div className="text-xs text-muted-foreground">{lv.department}</div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-brand-primary/10 text-brand-primary border-0">
                      {getLeaveTypeName(lv)}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs" dir="ltr">{formatDate(lv.start_date)}</TableCell>
                  <TableCell className="font-mono text-xs" dir="ltr">{formatDate(lv.end_date)}</TableCell>
                  <TableCell className="font-mono font-semibold">
                    {lv.days_count || 0} {d.daysUnit}
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(lv.status)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
