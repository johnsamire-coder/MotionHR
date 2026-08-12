"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import {FileBarChart, Clock, UserX, Calendar, FileText, Timer,
  DollarSign, ShieldCheck, Users, Download, Sparkles,
  ChevronLeft, ChevronRight, TrendingUp, Zap,
  UserCheck, Activity, Wallet, MapPin } from "lucide-react";
import { STORAGE_KEYS } from "@/lib/constants/config";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDict, useLangStore } from "@/lib/stores/language";

interface ReportItem {
  key: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  href?: string;
  status: "ready" | "coming_soon";
}

function ReportCard({
  report, lang,
}: {
  report: ReportItem;
  lang: string;
}) {
  const router = useRouter();
  const Icon = report.icon;
  const isReady = report.status === "ready";

  return (
    <Card
      className={`group border-border/50 transition-all cursor-pointer ${
        isReady
          ? "hover:shadow-lg hover:-translate-y-0.5"
          : "opacity-70 cursor-not-allowed"
      }`}
      onClick={() => isReady && report.href && router.push(report.href)}
    >
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className={`w-12 h-12 rounded-xl ${report.bgColor} ${report.color} flex items-center justify-center flex-shrink-0`}>
            <Icon className="w-6 h-6" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-base group-hover:text-brand-primary transition">
                {report.title}
              </h3>
              {!isReady && (
                <Badge className="bg-amber-500/10 text-amber-700 border-0 text-[10px]">
                  Soon
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {report.description}
            </p>
          </div>

          {isReady && (
            <div className="text-muted-foreground group-hover:text-brand-primary transition">
              {lang === "ar" ? (
                <ChevronLeft className="w-5 h-5" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface HubStats {
  effective_date: string;
  is_today: boolean;
  total_employees: number;
  present_today: number;
  absent_today: number;
  late_today: number;
  on_leave_today: number;
  weekend_today: number;
  total_leaves_month: number;
  pending_requests: number;
  total_payroll_net: number;
}

export default function ReportsHubPage() {
  const d = useDict();
  const lang = useLangStore((s) => s.lang);
  const [stats, setStats] = useState<HubStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
    if (!token) return;
    const authHeader = token.startsWith("Token") ? token : `Token ${token}`;

    fetch("/api/reports/hub-stats", { headers: { Authorization: authHeader } })
      .then(r => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const formatNum = (val: number) => {
    return new Intl.NumberFormat(lang === "ar" ? "ar-EG" : "en-US").format(val);
  };

  // Attendance Reports (4)
  const attendanceReports: ReportItem[] = [
    {
      key: "daily-attendance",
      title: d.reportDailyAttendance,
      description: d.reportDailyAttendanceDesc,
      icon: Clock,
      color: "text-blue-600",
      bgColor: "bg-blue-500/10",
      href: "/hr/reports/daily-attendance",
      status: "ready",
    },
    {
      key: "monthly-attendance",
      title: d.reportMonthlyAttendance,
      description: d.reportMonthlyAttendanceDesc,
      icon: Calendar,
      color: "text-indigo-600",
      bgColor: "bg-indigo-500/10",
      href: "/hr/reports/monthly-attendance",
      status: "ready",
    },
    {
      key: "late",
      title: d.reportLate,
      description: d.reportLateDesc,
      icon: Timer,
      color: "text-amber-600",
      bgColor: "bg-amber-500/10",
      href: "/hr/reports/late",
      status: "ready",
    },
    {
      key: "absence",
      title: d.reportAbsence,
      description: d.reportAbsenceDesc,
      icon: UserX,
      color: "text-red-600",
      bgColor: "bg-red-500/10",
      href: "/hr/reports/absence",
      status: "ready",
    },
  ];

  // Leaves & Requests Reports (4)
  const leavesReports: ReportItem[] = [
    {
      key: "leaves-enhanced",
      title: d.reportLeavesEnhanced,
      description: d.reportLeavesEnhancedDesc,
      icon: Sparkles,
      color: "text-emerald-600",
      bgColor: "bg-emerald-500/10",
      href: "/hr/reports/leaves-enhanced",
      status: "ready",
    },
    {
      key: "leaves-basic",
      title: d.reportLeaves,
      description: d.reportLeavesDesc,
      icon: Calendar,
      color: "text-cyan-600",
      bgColor: "bg-cyan-500/10",
      href: "/hr/reports/leaves-basic",
      status: "ready",
    },
    {
      key: "requests",
      title: d.reportRequests,
      description: d.reportRequestsDesc,
      icon: FileText,
      color: "text-purple-600",
      bgColor: "bg-purple-500/10",
      href: "/hr/reports/requests",
      status: "ready",
    },
    {
      key: "permissions",
      title: d.reportPermissions,
      description: d.reportPermissionsDesc,
      icon: ShieldCheck,
      color: "text-teal-600",
      bgColor: "bg-teal-500/10",
      href: "/hr/reports/permissions",
      status: "ready",
    },
  ];

  // Payroll & Others (4)
  const locationReports: ReportItem[] = [
    {
      key: "location-tracking",
      title: lang === "ar" ? "تقرير المواقع الحية" : "Live Location Tracking",
      description: lang === "ar" ? "تتبع مواقع الموظفين ومراجعة خطوط السير" : "Track employee locations and review routes",
      icon: MapPin,
      color: "text-rose-600",
      bgColor: "bg-rose-500/10",
      href: "/hr/reports/location-tracking",
      status: "ready",
    },
    {
      key: "missions",
      title: lang === "ar" ? "تقرير المهمات" : "Missions Report",
      description: lang === "ar" ? "ملخص المهمات وحالاتها والفيدباك" : "Missions summary, statuses and feedback",
      icon: Zap,
      color: "text-violet-600",
      bgColor: "bg-violet-500/10",
      href: "/hr/missions",
      status: "ready",
    },
  ];

  const payrollReports: ReportItem[] = [
    {
      key: "payroll",
      title: d.reportPayrollAll,
      description: d.reportPayrollAllDesc,
      icon: DollarSign,
      color: "text-emerald-600",
      bgColor: "bg-emerald-500/10",
      href: "/hr/reports/payroll",
      status: "ready",
    },
    {
      key: "work-hours",
      title: d.reportWorkHours,
      description: d.reportWorkHoursDesc,
      icon: TrendingUp,
      color: "text-orange-600",
      bgColor: "bg-orange-500/10",
      href: "/hr/reports/shifts",
      status: "ready",
    },
    {
      key: "shifts",
      title: d.reportShifts,
      description: d.reportShiftsDesc,
      icon: Users,
      color: "text-pink-600",
      bgColor: "bg-pink-500/10",
      href: "/hr/reports/work-hours",
      status: "ready",
    },
    {
      key: "executive-dashboard",
      title: lang === "ar" ? "التقرير التنفيذي" : "Executive Dashboard",
      description: lang === "ar" ? "نظرة عامة شاملة على أداء الشركة" : "Complete overview of company performance",
      icon: TrendingUp,
      color: "text-purple-600",
      bgColor: "bg-purple-500/10",
      href: "/hr/reports/executive-dashboard",
      status: "ready",
    },
    {
      key: "turnover",
      title: lang === "ar" ? "معدل دوران الموظفين" : "Employee Turnover",
      description: lang === "ar" ? "تحليل معدلات التعيين والاستقالة" : "Hiring and termination analysis",
      icon: Activity,
      color: "text-pink-600",
      bgColor: "bg-pink-500/10",
      href: "/hr/reports/turnover",
      status: "ready",
    },
    {
      key: "branch-comparison",
      title: lang === "ar" ? "مقارنة الفروع" : "Branch Comparison",
      description: lang === "ar" ? "مقارنة تكاليف الفروع والأقسام" : "Compare branches and departments costs",
      icon: FileBarChart,
      color: "text-indigo-600",
      bgColor: "bg-indigo-500/10",
      href: "/hr/reports/branch-comparison",
      status: "ready",
    },
    {
      key: "bank-transfer",
      title: lang === "ar" ? "كشف تحويلات البنك" : "Bank Transfer Sheet",
      description: lang === "ar" ? "قائمة التحويلات البنكية للمرتبات" : "Bank transfers for salaries",
      icon: Wallet,
      color: "text-emerald-600",
      bgColor: "bg-emerald-500/10",
      href: "/hr/reports/bank-transfer",
      status: "ready",
    },
    {
      key: "insurance",
      title: lang === "ar" ? "تقرير التأمينات" : "Insurance Report",
      description: lang === "ar" ? "التأمينات الاجتماعية للموظفين" : "Social insurance contributions",
      icon: ShieldCheck,
      color: "text-blue-600",
      bgColor: "bg-blue-500/10",
      href: "/hr/reports/insurance",
      status: "ready",
    },
    {
      key: "tax",
      title: lang === "ar" ? "تقرير الضرائب" : "Tax Report",
      description: lang === "ar" ? "الضرائب المستقطعة" : "Tax deductions report",
      icon: DollarSign,
      color: "text-red-600",
      bgColor: "bg-red-500/10",
      href: "/hr/reports/tax",
      status: "ready",
    },
    {
      key: "loans-advances",
      title: lang === "ar" ? "السلف والقروض" : "Loans & Advances",
      description: lang === "ar" ? "السلف والقروض القائمة" : "Active loans and advances",
      icon: Wallet,
      color: "text-orange-600",
      bgColor: "bg-orange-500/10",
      href: "/hr/reports/loans-advances",
      status: "ready",
    },
    {
      key: "eos",
      title: lang === "ar" ? "مكافأة نهاية الخدمة" : "End of Service Report",
      description: lang === "ar" ? "المكافآت المستحقة للموظفين" : "EOS entitlements",
      icon: FileText,
      color: "text-teal-600",
      bgColor: "bg-teal-500/10",
      href: "/hr/reports/eos",
      status: "ready",
    },
    {
      key: "reimbursements",
      title: lang === "ar" ? "رد المصروفات" : "Reimbursements",
      description: lang === "ar" ? "طلبات رد المصروفات" : "Expense reimbursement requests",
      icon: DollarSign,
      color: "text-cyan-600",
      bgColor: "bg-cyan-500/10",
      href: "/hr/reports/reimbursements",
      status: "ready",
    },
    {
      key: "contracts-expiry",
      title: lang === "ar" ? "العقود المنتهية" : "Contract Expiry",
      description: lang === "ar" ? "العقود المنتهية أو قريبة الانتهاء" : "Expired or expiring contracts",
      icon: Calendar,
      color: "text-rose-600",
      bgColor: "bg-rose-500/10",
      href: "/hr/reports/contracts-expiry",
      status: "ready",
    },
    {
      key: "missions-performance",
      title: lang === "ar" ? "أداء المهام" : "Missions Performance",
      description: lang === "ar" ? "معدلات إنجاز المهام" : "Mission completion rates",
      icon: Zap,
      color: "text-yellow-600",
      bgColor: "bg-yellow-500/10",
      href: "/hr/reports/missions-performance",
      status: "ready",
    },
        {
      key: "exports",
      title: d.reportExports,
      description: d.reportExportsDesc,
      icon: Download,
      color: "text-gray-600",
      bgColor: "bg-gray-500/10",
      status: "coming_soon",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{d.reportsTitle}</h1>
          <p className="text-muted-foreground mt-1">{d.reportsDesc}</p>
        </div>

        <div className="flex items-center gap-2 bg-brand-primary/10 rounded-lg px-4 py-2">
          <FileBarChart className="w-5 h-5 text-brand-primary" />
          <div>
            <div className="text-xs text-muted-foreground">
              {lang === "ar" ? "إجمالي التقارير" : "Total Reports"}
            </div>
            <div className="text-lg font-bold text-brand-primary">10</div>
          </div>
        </div>
      </div>

      {/* Live Stats */}
      <div>
        <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-semibold">
              {lang === "ar" ? "لمحة سريعة" : "Quick Overview"}
            </h2>
          </div>

          {stats?.effective_date && (
            <div className="flex items-center gap-2 bg-muted/50 rounded-lg px-3 py-1.5 text-xs">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="text-muted-foreground">
                {stats.is_today
                  ? (lang === "ar" ? "بيانات اليوم" : "Today's data")
                  : (lang === "ar" ? "آخر يوم بيانات:" : "Last data:")}
              </span>
              <span className="font-semibold">
                {new Date(stats.effective_date).toLocaleDateString(lang === "ar" ? "ar-EG" : "en-US", {
                  weekday: "long",
                  day: "numeric",
                  month: "short",
                })}
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card className="border-0 bg-gradient-to-br from-blue-500/10 to-blue-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-blue-600" />
                <p className="text-xs text-muted-foreground">
                  {lang === "ar" ? "إجمالي الموظفين" : "Total Employees"}
                </p>
              </div>
              <p className="text-xl font-bold text-blue-700">
                {loading ? "..." : formatNum(stats?.total_employees || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <UserCheck className="w-4 h-4 text-emerald-600" />
                <p className="text-xs text-muted-foreground">
                  {lang === "ar" ? "حاضر اليوم" : "Present Today"}
                </p>
              </div>
              <p className="text-xl font-bold text-emerald-700">
                {loading ? "..." : formatNum(stats?.present_today || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 bg-gradient-to-br from-red-500/10 to-red-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <UserX className="w-4 h-4 text-red-600" />
                <p className="text-xs text-muted-foreground">
                  {lang === "ar" ? "غائب اليوم" : "Absent Today"}
                </p>
              </div>
              <p className="text-xl font-bold text-red-700">
                {loading ? "..." : formatNum(stats?.absent_today || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 bg-gradient-to-br from-cyan-500/10 to-cyan-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-cyan-600" />
                <p className="text-xs text-muted-foreground">
                  {lang === "ar" ? "إجازات الشهر" : "Leaves (Month)"}
                </p>
              </div>
              <p className="text-xl font-bold text-cyan-700">
                {loading ? "..." : formatNum(stats?.total_leaves_month || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 bg-gradient-to-br from-amber-500/10 to-amber-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-amber-600" />
                <p className="text-xs text-muted-foreground">
                  {lang === "ar" ? "طلبات معلقة" : "Pending Requests"}
                </p>
              </div>
              <p className="text-xl font-bold text-amber-700">
                {loading ? "..." : formatNum(stats?.pending_requests || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 bg-gradient-to-br from-brand-primary/10 to-brand-primary/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="w-4 h-4 text-brand-primary" />
                <p className="text-xs text-muted-foreground">
                  {lang === "ar" ? "صافي الرواتب" : "Net Payroll"}
                </p>
              </div>
              <p className="text-xl font-bold text-brand-primary">
                {loading ? "..." : formatNum(stats?.total_payroll_net || 0)}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Attendance Reports */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold">{d.reportsCategoryAttendance}</h2>
          <Badge variant="outline" className="text-xs">4</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {attendanceReports.map(report => (
            <ReportCard key={report.key} report={report} lang={lang} />
          ))}
        </div>
      </div>

      {/* Leaves & Requests Reports */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-emerald-600" />
          <h2 className="text-lg font-semibold">{d.reportsCategoryLeaves}</h2>
          <Badge variant="outline" className="text-xs">4</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {leavesReports.map(report => (
            <ReportCard key={report.key} report={report} lang={lang} />
          ))}
        </div>
      </div>

      {/* Location & Missions */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="w-5 h-5 text-rose-600" />
          <h2 className="text-lg font-semibold">
            {lang === "ar" ? "المواقع والمهمات" : "Location & Missions"}
          </h2>
          <Badge variant="outline" className="text-xs">{locationReports.length}</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {locationReports.map(report => (
            <ReportCard key={report.key} report={report} lang={lang} />
          ))}
        </div>
      </div>

      {/* Payroll & Others */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-5 h-5 text-emerald-600" />
          <h2 className="text-lg font-semibold">{d.reportsCategoryPayroll}</h2>
          <Badge variant="outline" className="text-xs">4</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {payrollReports.map(report => (
            <ReportCard key={report.key} report={report} lang={lang} />
          ))}
        </div>
      </div>
    </div>
  );
}
