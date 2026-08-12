"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { MapPin, Users, Activity, Clock, Calendar, Search, Loader2, ChevronLeft, ChevronRight, Navigation, LogIn, LogOut, Download, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useLangStore } from "@/lib/stores/language";
import { exportToExcel, exportToPDF, type ExportColumn } from "@/lib/utils/export-report";
import { STORAGE_KEYS } from "@/lib/constants/config";

interface LogPoint {
  timestamp: string;
  lat: number;
  lng: number;
  address: string;
  accuracy: number;
}

interface EmployeeTracking {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  department: string;
  branch: string;
  worker_type: string;
  checkin_time: string;
  checkout_time: string;
  has_attendance: boolean;
  total_logs: number;
  first_location: LogPoint | null;
  last_location: LogPoint | null;
  logs: LogPoint[];
}

interface TrackingData {
  success: boolean;
  date: string;
  stats: {
    total_employees: number;
    with_attendance: number;
    tracked: number;
    not_tracked: number;
  };
  employees: EmployeeTracking[];
}

function StatCard({ icon: Icon, label, value, color }: { icon: React.ComponentType<{ className?: string }>; label: string; value: number; color: string }) {
  return (
    <Card className="border-border/50 hover:shadow-md transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
          <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center flex-shrink-0`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LocationTrackingPage() {
  const router = useRouter();
  const lang = useLangStore((s) => s.lang);
  const ar = lang === "ar";

  const today = new Date().toISOString().split("T")[0];
  const [date, setDate] = useState(today);
  const [data, setData] = useState<TrackingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<EmployeeTracking | null>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEYS.token) : null;
  const authH = token?.startsWith("Token") ? token : `Token ${token}`;

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetch(`/api/reports/location-tracking?date=${date}`, { headers: { Authorization: authH } })
      .then(r => r.json())
      .then(setData)
      .catch(() => toast.error(ar ? "فشل تحميل البيانات" : "Failed to load"))
      .finally(() => setLoading(false));
  }, [date]);

  const navigateDate = (offset: number) => {
    const d = new Date(date);
    d.setDate(d.getDate() + offset);
    setDate(d.toISOString().split("T")[0]);
  };

  const employees = data?.employees || [];
  const filtered = employees.filter(e => !search || e.employee_name.toLowerCase().includes(search.toLowerCase()) || e.employee_code.includes(search));
  const stats = data?.stats;

  const formatDate = (s: string) => new Date(s).toLocaleDateString(ar ? "ar-EG" : "en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

  const handleExport = (format: "pdf" | "excel") => {
    if (!filtered.length) {
      toast.error(ar ? "لا توجد بيانات للتصدير" : "No data to export");
      return;
    }

    const columns: ExportColumn[] = [
      { key: "employee_code", header: ar ? "كود الموظف" : "Employee Code", width: 15 },
      { key: "employee_name", header: ar ? "اسم الموظف" : "Employee Name", width: 25 },
      { key: "department", header: ar ? "القسم" : "Department", width: 20 },
      { key: "branch", header: ar ? "الفرع" : "Branch", width: 20 },
      { key: "checkin_time", header: ar ? "الحضور" : "Check In", width: 15 },
      { key: "checkout_time", header: ar ? "الانصراف" : "Check Out", width: 15 },
      { key: "total_logs", header: ar ? "نقاط التتبع" : "Track Points", width: 15 },
      { key: "last_address", header: ar ? "آخر موقع" : "Last Location", width: 35 },
      { key: "status_label", header: ar ? "الحالة" : "Status", width: 15 },
    ];

    const exportData = filtered.map(emp => ({
      employee_code: emp.employee_code || "—",
      employee_name: emp.employee_name || "—",
      department: emp.department || "—",
      branch: emp.branch || "—",
      checkin_time: emp.checkin_time || "—",
      checkout_time: emp.checkout_time || "—",
      total_logs: emp.total_logs || 0,
      last_address: emp.last_location?.address || "—",
      status_label: !emp.has_attendance
        ? (ar ? "لم يحضر" : "Absent")
        : emp.total_logs > 0
          ? (ar ? "متتبع" : "Tracked")
          : (ar ? "بدون تتبع" : "No tracking"),
    }));

    const config = {
      title: ar ? "تقرير تتبع المواقع" : "Location Tracking Report",
      period: date,
      columns,
      data: exportData,
      fileName: `location_tracking_${date}`,
      lang: (ar ? "ar" : "en") as "ar" | "en",
      summaryStats: [
        { label: ar ? "إجمالي الموظفين" : "Total", value: stats?.total_employees ?? 0 },
        { label: ar ? "لديهم حضور" : "With Attendance", value: stats?.with_attendance ?? 0 },
        { label: ar ? "متتبعين" : "Tracked", value: stats?.tracked ?? 0 },
        { label: ar ? "غير متتبع" : "Not Tracked", value: stats?.not_tracked ?? 0 },
      ],
    };

    if (format === "pdf") {
      exportToPDF(config);
    } else {
      exportToExcel(config);
    }
  };

  return (
    <div className="space-y-6" dir={ar ? "rtl" : "ltr"}>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{ar ? "تتبع مواقع الموظفين" : "Location Tracking"}</h1>
          <p className="text-muted-foreground mt-1">{ar ? "تقرير يومي بمواقع كل موظف من الحضور حتى الانصراف" : "Daily tracking report from check-in to check-out"}</p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => router.push("/hr/reports")}>
            {ar ? "رجوع للتقارير" : "Back to Reports"}
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => handleExport("excel")}>
            <Download className="w-4 h-4" />
            {ar ? "تصدير Excel" : "Export Excel"}
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => handleExport("pdf")}>
            <Printer className="w-4 h-4" />
            {ar ? "تصدير PDF" : "Export PDF"}
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigateDate(-1)}>
              {ar ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
            </Button>
            <div className="flex-1 flex items-center justify-center gap-4">
              <Calendar className="w-5 h-5 text-brand-primary" />
              <div className="text-center">
                <div className="text-sm text-muted-foreground">{ar ? "اختر التاريخ" : "Select Date"}</div>
                <div className="text-lg font-bold">{formatDate(date)}</div>
              </div>
              <Input type="date" value={date} onChange={e => setDate(e.target.value)} className="w-40" />
            </div>
            <Button variant="ghost" size="icon" onClick={() => navigateDate(1)}>
              {ar ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-24"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={Users} label={ar ? "إجمالي الموظفين" : "Total"} value={stats?.total_employees ?? 0} color="bg-brand-primary/10 text-brand-primary" />
            <StatCard icon={LogIn} label={ar ? "لديهم حضور" : "With Attendance"} value={stats?.with_attendance ?? 0} color="bg-emerald-500/10 text-emerald-600" />
            <StatCard icon={Navigation} label={ar ? "متتبعين" : "Tracked"} value={stats?.tracked ?? 0} color="bg-blue-500/10 text-blue-600" />
            <StatCard icon={MapPin} label={ar ? "غير متتبع" : "Not Tracked"} value={stats?.not_tracked ?? 0} color="bg-slate-500/10 text-slate-600" />
          </div>

          <Card>
            <CardContent className="p-4">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input placeholder={ar ? "بحث بالاسم أو الكود..." : "Search..."} value={search} onChange={e => setSearch(e.target.value)} className="pr-10" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="border-b bg-muted/30">
                    <TableHead className="text-start">{ar ? "الموظف" : "Employee"}</TableHead>
                    <TableHead className="text-start">{ar ? "القسم" : "Department"}</TableHead>
                    <TableHead className="text-start">{ar ? "الحضور" : "Check In"}</TableHead>
                    <TableHead className="text-start">{ar ? "الانصراف" : "Check Out"}</TableHead>
                    <TableHead className="text-start">{ar ? "نقاط التتبع" : "Track Points"}</TableHead>
                    <TableHead className="text-start">{ar ? "آخر موقع" : "Last Location"}</TableHead>
                    <TableHead className="text-start">{ar ? "الحالة" : "Status"}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map(emp => (
                    <TableRow key={emp.employee_id} className="hover:bg-muted/40 cursor-pointer" onClick={() => setSelected(emp)}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-9 h-9">
                            <AvatarFallback className="bg-brand-primary/10 text-brand-primary text-sm font-semibold">{emp.employee_name?.[0]}</AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium text-sm">{emp.employee_name}</div>
                            <div className="text-xs text-muted-foreground font-mono">{emp.employee_code}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell><span className="text-sm">{emp.department || "—"}</span></TableCell>
                      <TableCell><span className="text-sm font-mono">{emp.checkin_time || "—"}</span></TableCell>
                      <TableCell><span className="text-sm font-mono">{emp.checkout_time || "—"}</span></TableCell>
                      <TableCell>
                        {emp.total_logs > 0 ? (
                          <Badge className="bg-blue-100 text-blue-700 border-0">{emp.total_logs} {ar ? "نقطة" : "points"}</Badge>
                        ) : (<span className="text-xs text-muted-foreground">—</span>)}
                      </TableCell>
                      <TableCell>
                        <div className="text-xs text-muted-foreground max-w-[200px] truncate" title={emp.last_location?.address}>
                          {emp.last_location?.address || "—"}
                        </div>
                      </TableCell>
                      <TableCell>
                        {emp.has_attendance ? (
                          emp.total_logs > 0 ? (<Badge className="bg-emerald-100 text-emerald-700 border-0">{ar ? "متتبع" : "Tracked"}</Badge>)
                          : (<Badge className="bg-amber-100 text-amber-700 border-0">{ar ? "بدون تتبع" : "No tracking"}</Badge>)
                        ) : (<Badge className="bg-slate-100 text-slate-600 border-0">{ar ? "لم يحضر" : "Absent"}</Badge>)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      {selected && (
        <Dialog open={!!selected} onOpenChange={v => !v && setSelected(null)}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{ar ? "تفاصيل تتبع" : "Tracking Details"}: {selected.employee_name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 pt-2">
              <div className="grid grid-cols-2 gap-3 p-3 bg-muted/30 rounded">
                <div><span className="text-xs text-muted-foreground">{ar ? "الحضور" : "Check In"}:</span> <span className="font-mono">{selected.checkin_time || "—"}</span></div>
                <div><span className="text-xs text-muted-foreground">{ar ? "الانصراف" : "Check Out"}:</span> <span className="font-mono">{selected.checkout_time || "—"}</span></div>
                <div><span className="text-xs text-muted-foreground">{ar ? "القسم" : "Department"}:</span> <span>{selected.department || "—"}</span></div>
                <div><span className="text-xs text-muted-foreground">{ar ? "الفرع" : "Branch"}:</span> <span>{selected.branch || "—"}</span></div>
              </div>

              <h3 className="font-semibold mt-4">{ar ? "سجل التحركات" : "Movement Log"} ({selected.logs.length})</h3>
              {selected.logs.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">{ar ? "لا توجد نقاط تتبع" : "No tracking points"}</p>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {selected.logs.map((log, i) => (
                    <div key={i} className="border rounded p-3 flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-primary/10 text-brand-primary flex items-center justify-center flex-shrink-0 font-mono text-xs">{i + 1}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Clock className="w-3 h-3 text-muted-foreground" />
                          <span className="text-sm font-mono">{log.timestamp}</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <MapPin className="w-3 h-3 text-muted-foreground mt-1 flex-shrink-0" />
                          <span className="text-sm">{log.address || `${log.lat.toFixed(6)}, ${log.lng.toFixed(6)}`}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

