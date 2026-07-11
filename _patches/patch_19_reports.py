#!/usr/bin/env python3
"""
Patch 19: التقارير الكاملة
============================
- تقارير الحضور والغياب
- تقارير التأخيرات
- تقارير الإجازات
- تقارير الميدانيين والزيارات
- Export Excel
- Dashboard أرقام حقيقية
"""

import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def append_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

print("=" * 60)
print("  Patch 19: Reports")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إنشاء reports app
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء reports app...")

reports_dir = os.path.join(BASE_DIR, 'reports')
os.makedirs(reports_dir, exist_ok=True)

create_file(os.path.join(reports_dir, '__init__.py'), '')
create_file(os.path.join(reports_dir, 'apps.py'), '''from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reports"
    verbose_name = "التقارير"
''')
create_file(os.path.join(reports_dir, 'tests.py'), '')


# ════════════════════════════════════════════════════════════
# 2. reports/utils.py — أدوات التقارير
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء reports/utils.py...")

create_file(os.path.join(reports_dir, 'utils.py'), '''"""
reports/utils.py
أدوات وحسابات التقارير
"""

from datetime import date, timedelta
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone


def get_date_range(period, custom_start=None, custom_end=None):
    """
    إرجاع نطاق التاريخ حسب الفترة
    period: today, week, month, quarter, year, custom
    """
    today = date.today()

    if period == "today":
        return today, today

    elif period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today

    elif period == "month":
        start = today.replace(day=1)
        return start, today

    elif period == "last_month":
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        start = last_month_end.replace(day=1)
        return start, last_month_end

    elif period == "quarter":
        q_month = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=q_month, day=1)
        return start, today

    elif period == "year":
        start = today.replace(month=1, day=1)
        return start, today

    elif period == "custom" and custom_start and custom_end:
        return custom_start, custom_end

    # افتراضي: الشهر الحالي
    return today.replace(day=1), today


def get_attendance_summary(company, start_date, end_date, employee=None):
    """ملخص الحضور في فترة معينة"""
    from attendance.models import Attendance

    qs = Attendance.objects.filter(
        company=company,
        date__range=[start_date, end_date]
    )
    if employee:
        qs = qs.filter(employee=employee)

    total     = qs.count()
    present   = qs.filter(status="present").count()
    absent    = qs.filter(status="absent").count()
    late      = qs.filter(status="late").count()
    on_leave  = qs.filter(status="on_leave").count()
    holiday   = qs.filter(status__in=["holiday", "weekend"]).count()

    late_minutes_avg = qs.filter(
        late_minutes__gt=0
    ).aggregate(avg=Avg("late_minutes"))["avg"] or 0

    work_hours_total = qs.aggregate(
        total=Sum("work_hours")
    )["total"] or 0

    return {
        "total":            total,
        "present":          present,
        "absent":           absent,
        "late":             late,
        "on_leave":         on_leave,
        "holiday":          holiday,
        "attendance_rate":  round(present / total * 100, 1) if total else 0,
        "late_rate":        round(late / total * 100, 1) if total else 0,
        "late_minutes_avg": round(late_minutes_avg, 0),
        "work_hours_total": round(float(work_hours_total), 1),
    }


def get_employee_attendance_details(company, start_date, end_date):
    """تفاصيل الحضور لكل موظف"""
    from attendance.models import Attendance
    from employees.models import Employee

    employees = Employee.objects.filter(
        company=company, status="active"
    ).order_by("first_name_ar")

    result = []
    for emp in employees:
        qs = Attendance.objects.filter(
            company=company,
            employee=emp,
            date__range=[start_date, end_date]
        )
        present  = qs.filter(status="present").count()
        absent   = qs.filter(status="absent").count()
        late     = qs.filter(status="late").count()
        on_leave = qs.filter(status="on_leave").count()
        total    = qs.count()

        late_mins = qs.aggregate(
            total=Sum("late_minutes")
        )["total"] or 0

        work_hrs = qs.aggregate(
            total=Sum("work_hours")
        )["total"] or 0

        result.append({
            "employee":    emp,
            "present":     present,
            "absent":      absent,
            "late":        late,
            "on_leave":    on_leave,
            "total":       total,
            "late_mins":   late_mins,
            "work_hours":  round(float(work_hrs), 1),
            "rate":        round(present / total * 100, 1) if total else 0,
        })

    return result


def get_field_tracking_summary(company, start_date, end_date):
    """ملخص التتبع الميداني"""
    from attendance.models import LocationLog, LocationCheckIn
    from employees.models import Employee

    field_employees = Employee.objects.filter(
        company=company,
        status="active",
        is_field_worker=True
    )

    result = []
    for emp in field_employees:
        logs = LocationLog.objects.filter(
            company=company,
            employee=emp,
            timestamp__date__range=[start_date, end_date]
        )
        visits = LocationCheckIn.objects.filter(
            company=company,
            employee=emp,
            arrival_time__date__range=[start_date, end_date]
        )

        result.append({
            "employee":      emp,
            "total_logs":    logs.count(),
            "total_visits":  visits.count(),
            "completed":     visits.filter(status="completed").count(),
        })

    return result


def export_to_excel(headers, rows, sheet_name="تقرير"):
    """
    تصدير بيانات إلى Excel
    يستخدم csv كبديل بسيط لو openpyxl مش موجود
    """
    import io
    import csv
    from django.http import HttpResponse

    response = HttpResponse(
        content_type="text/csv; charset=utf-8-sig"
    )
    response["Content-Disposition"] = (
        f\'attachment; filename="{sheet_name}.csv"\' 
    )

    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    return response
''')


# ════════════════════════════════════════════════════════════
# 3. reports/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء reports/views.py...")

create_file(os.path.join(reports_dir, 'views.py'), '''"""
reports/views.py
"""

from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone

from .utils import (
    get_date_range,
    get_attendance_summary,
    get_employee_attendance_details,
    get_field_tracking_summary,
    export_to_excel,
)


# ════════════════════════════════════════════════════════════
# صفحة التقارير الرئيسية
# ════════════════════════════════════════════════════════════

@login_required
def reports_home(request):
    """الصفحة الرئيسية للتقارير"""
    context = {
        "page_title": "التقارير",
    }
    return render(request, "reports/home.html", context)


# ════════════════════════════════════════════════════════════
# تقرير الحضور والغياب
# ════════════════════════════════════════════════════════════

@login_required
def attendance_report(request):
    """تقرير الحضور والغياب"""
    company = request.user.company
    period  = request.GET.get("period", "month")

    custom_start = None
    custom_end   = None
    if period == "custom":
        try:
            custom_start = date.fromisoformat(request.GET.get("start_date", ""))
            custom_end   = date.fromisoformat(request.GET.get("end_date", ""))
        except Exception:
            period = "month"

    start_date, end_date = get_date_range(period, custom_start, custom_end)

    summary  = get_attendance_summary(company, start_date, end_date)
    details  = get_employee_attendance_details(company, start_date, end_date)

    # Export
    if request.GET.get("export") == "excel":
        headers = [
            "الموظف", "الرقم الوظيفي", "الحاضر", "الغائب",
            "المتأخر", "إجازة", "الإجمالي", "نسبة الحضور%",
            "إجمالي التأخير (دقيقة)", "ساعات العمل"
        ]
        rows = [
            [
                d["employee"].full_name_ar,
                d["employee"].employee_code,
                d["present"],
                d["absent"],
                d["late"],
                d["on_leave"],
                d["total"],
                d["rate"],
                d["late_mins"],
                d["work_hours"],
            ]
            for d in details
        ]
        return export_to_excel(
            headers, rows,
            f"تقرير_الحضور_{start_date}_{end_date}"
        )

    context = {
        "summary":    summary,
        "details":    details,
        "start_date": start_date,
        "end_date":   end_date,
        "period":     period,
        "page_title": "تقرير الحضور والغياب",
    }
    return render(request, "reports/attendance_report.html", context)


# ════════════════════════════════════════════════════════════
# تقرير التأخيرات
# ════════════════════════════════════════════════════════════

@login_required
def late_report(request):
    """تقرير التأخيرات"""
    from attendance.models import Attendance
    from django.db.models import Sum, Count, Avg

    company    = request.user.company
    period     = request.GET.get("period", "month")
    start_date, end_date = get_date_range(period)

    late_records = Attendance.objects.filter(
        company=company,
        date__range=[start_date, end_date],
        late_minutes__gt=0,
    ).select_related("employee").order_by("-late_minutes")

    # تجميع حسب الموظف
    from django.db.models import Sum, Count
    employee_late = Attendance.objects.filter(
        company=company,
        date__range=[start_date, end_date],
        late_minutes__gt=0,
    ).values(
        "employee__first_name_ar",
        "employee__last_name_ar",
        "employee__employee_code",
    ).annotate(
        total_late_minutes=Sum("late_minutes"),
        late_days=Count("id"),
    ).order_by("-total_late_minutes")

    # Export
    if request.GET.get("export") == "excel":
        headers = ["الموظف", "الرقم الوظيفي", "أيام التأخير", "إجمالي الدقائق"]
        rows = [
            [
                f\'{r["employee__first_name_ar"]} {r["employee__last_name_ar"]}\',
                r["employee__employee_code"],
                r["late_days"],
                r["total_late_minutes"],
            ]
            for r in employee_late
        ]
        return export_to_excel(headers, rows, "تقرير_التأخيرات")

    context = {
        "late_records":  late_records[:50],
        "employee_late": employee_late,
        "start_date":    start_date,
        "end_date":      end_date,
        "period":        period,
        "page_title":    "تقرير التأخيرات",
    }
    return render(request, "reports/late_report.html", context)


# ════════════════════════════════════════════════════════════
# تقرير الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_report(request):
    """تقرير الإجازات"""
    from leaves.models import LeaveRequest, LeaveType

    company    = request.user.company
    period     = request.GET.get("period", "month")
    start_date, end_date = get_date_range(period)

    requests = LeaveRequest.objects.filter(
        company=company,
        start_date__range=[start_date, end_date],
    ).select_related("employee", "leave_type").order_by("-start_date")

    # إحصائيات
    from django.db.models import Sum, Count
    by_type = LeaveRequest.objects.filter(
        company=company,
        start_date__range=[start_date, end_date],
        status="approved",
    ).values("leave_type__name").annotate(
        count=Count("id"),
        total_days=Sum("days_count"),
    ).order_by("-total_days")

    by_status = {
        "pending":   requests.filter(status="pending").count(),
        "approved":  requests.filter(status="approved").count(),
        "rejected":  requests.filter(status="rejected").count(),
        "cancelled": requests.filter(status="cancelled").count(),
    }

    # Export
    if request.GET.get("export") == "excel":
        headers = [
            "الموظف", "نوع الإجازة", "من", "إلى",
            "الأيام", "الحالة", "السبب"
        ]
        rows = [
            [
                lr.employee.full_name_ar,
                lr.leave_type.name,
                lr.start_date.strftime("%d/%m/%Y"),
                lr.end_date.strftime("%d/%m/%Y"),
                lr.days_count,
                lr.get_status_display(),
                lr.reason[:50],
            ]
            for lr in requests
        ]
        return export_to_excel(headers, rows, "تقرير_الإجازات")

    context = {
        "requests":   requests,
        "by_type":    by_type,
        "by_status":  by_status,
        "start_date": start_date,
        "end_date":   end_date,
        "period":     period,
        "page_title": "تقرير الإجازات",
    }
    return render(request, "reports/leave_report.html", context)


# ════════════════════════════════════════════════════════════
# تقرير الميدانيين
# ════════════════════════════════════════════════════════════

@login_required
def field_report(request):
    """تقرير الموظفين الميدانيين"""
    company    = request.user.company
    period     = request.GET.get("period", "month")
    start_date, end_date = get_date_range(period)

    field_summary = get_field_tracking_summary(company, start_date, end_date)

    from attendance.models import LocationCheckIn
    from django.db.models import Count

    visits_by_type = LocationCheckIn.objects.filter(
        company=company,
        arrival_time__date__range=[start_date, end_date],
    ).values("visit_type").annotate(
        count=Count("id")
    ).order_by("-count")

    recent_visits = LocationCheckIn.objects.filter(
        company=company,
        arrival_time__date__range=[start_date, end_date],
    ).select_related("employee").order_by("-arrival_time")[:20]

    # Export
    if request.GET.get("export") == "excel":
        headers = ["الموظف", "نقاط تتبع", "زيارات", "مكتملة"]
        rows = [
            [
                r["employee"].full_name_ar,
                r["total_logs"],
                r["total_visits"],
                r["completed"],
            ]
            for r in field_summary
        ]
        return export_to_excel(headers, rows, "تقرير_الميدانيين")

    context = {
        "field_summary":  field_summary,
        "visits_by_type": visits_by_type,
        "recent_visits":  recent_visits,
        "start_date":     start_date,
        "end_date":       end_date,
        "period":         period,
        "page_title":     "تقرير الميدانيين",
    }
    return render(request, "reports/field_report.html", context)


# ════════════════════════════════════════════════════════════
# تقرير الموظفين
# ════════════════════════════════════════════════════════════

@login_required
def employees_report(request):
    """تقرير الموظفين"""
    from employees.models import Employee
    from django.db.models import Count

    company   = request.user.company
    employees = Employee.objects.filter(
        company=company
    ).select_related(
        "department", "branch", "job_title"
    ).order_by("first_name_ar")

    # إحصائيات
    by_status = {}
    for status, label in Employee._meta.get_field("status").choices:
        by_status[label] = employees.filter(status=status).count()

    by_department = employees.filter(
        status="active"
    ).values(
        "department__name_ar"
    ).annotate(count=Count("id")).order_by("-count")

    by_contract = employees.filter(
        status="active"
    ).values("contract_type").annotate(
        count=Count("id")
    ).order_by("-count")

    # Export
    if request.GET.get("export") == "excel":
        headers = [
            "الرقم الوظيفي", "الاسم", "القسم",
            "المسمى الوظيفي", "الفرع", "تاريخ التعيين",
            "الراتب الأساسي", "الحالة"
        ]
        rows = [
            [
                emp.employee_code,
                emp.full_name_ar,
                emp.department.name_ar if emp.department else "",
                emp.job_title.name_ar if emp.job_title else "",
                emp.branch.name_ar if emp.branch else "",
                emp.hire_date.strftime("%d/%m/%Y") if emp.hire_date else "",
                emp.basic_salary,
                emp.get_status_display(),
            ]
            for emp in employees
        ]
        return export_to_excel(headers, rows, "تقرير_الموظفين")

    context = {
        "employees":     employees,
        "by_status":     by_status,
        "by_department": by_department,
        "by_contract":   by_contract,
        "page_title":    "تقرير الموظفين",
    }
    return render(request, "reports/employees_report.html", context)
''')


# ════════════════════════════════════════════════════════════
# 4. reports/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء reports/urls.py...")

create_file(os.path.join(reports_dir, 'urls.py'), '''from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("",           views.reports_home,      name="home"),
    path("attendance/",views.attendance_report,  name="attendance"),
    path("late/",      views.late_report,        name="late"),
    path("leaves/",    views.leave_report,       name="leaves"),
    path("field/",     views.field_report,       name="field"),
    path("employees/", views.employees_report,   name="employees"),
]
''')


# ════════════════════════════════════════════════════════════
# 5. إضافة reports في settings + urls
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings.py و urls.py...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')
settings_content = read_file(settings_path)

if "'reports'" not in settings_content:
    settings_content = settings_content.replace(
        "'leaves',",
        "'leaves',\n    'reports',"
    )
    write_file(settings_path, settings_content)

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

if "reports.urls" not in main_urls_content:
    main_urls_content = main_urls_content.replace(
        "path('leaves/',",
        "path('reports/',      include('reports.urls',      namespace='reports')),\n    path('leaves/',",
    )
    write_file(main_urls_path, main_urls_content)


# ════════════════════════════════════════════════════════════
# 6. Templates
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء Templates...")

# ── reports/home.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'reports', 'home.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}التقارير{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-bar-chart me-2" style="color:#06B6D4;"></i>
      التقارير
    </h4>
    <p class="text-muted">اختر نوع التقرير المطلوب</p>
  </div>

  <div class="row g-4">

    <div class="col-md-6 col-lg-4">
      <a href="{% url 'reports:attendance' %}"
         class="card border-0 shadow-sm text-decoration-none h-100"
         style="transition:transform 0.2s;"
         onmouseover="this.style.transform='translateY(-4px)'"
         onmouseout="this.style.transform='translateY(0)'">
        <div class="card-body p-4 text-center">
          <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
               style="width:64px;height:64px;background:#e0f7fa;">
            <i class="bi bi-calendar-check-fill"
               style="font-size:1.8rem;color:#06B6D4;"></i>
          </div>
          <h5 class="fw-bold text-dark">الحضور والغياب</h5>
          <p class="text-muted small mb-0">
            إجمالي الحضور، الغياب، الإجازات لكل موظف
          </p>
        </div>
      </a>
    </div>

    <div class="col-md-6 col-lg-4">
      <a href="{% url 'reports:late' %}"
         class="card border-0 shadow-sm text-decoration-none h-100"
         style="transition:transform 0.2s;"
         onmouseover="this.style.transform='translateY(-4px)'"
         onmouseout="this.style.transform='translateY(0)'">
        <div class="card-body p-4 text-center">
          <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
               style="width:64px;height:64px;background:#fff3e0;">
            <i class="bi bi-clock-history"
               style="font-size:1.8rem;color:#f59e0b;"></i>
          </div>
          <h5 class="fw-bold text-dark">التأخيرات</h5>
          <p class="text-muted small mb-0">
            تقرير تفصيلي بالتأخيرات ودقائقها لكل موظف
          </p>
        </div>
      </a>
    </div>

    <div class="col-md-6 col-lg-4">
      <a href="{% url 'reports:leaves' %}"
         class="card border-0 shadow-sm text-decoration-none h-100"
         style="transition:transform 0.2s;"
         onmouseover="this.style.transform='translateY(-4px)'"
         onmouseout="this.style.transform='translateY(0)'">
        <div class="card-body p-4 text-center">
          <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
               style="width:64px;height:64px;background:#fce4ec;">
            <i class="bi bi-calendar2-week-fill"
               style="font-size:1.8rem;color:#e91e63;"></i>
          </div>
          <h5 class="fw-bold text-dark">الإجازات</h5>
          <p class="text-muted small mb-0">
            طلبات الإجازات والأرصدة والموافقات
          </p>
        </div>
      </a>
    </div>

    <div class="col-md-6 col-lg-4">
      <a href="{% url 'reports:field' %}"
         class="card border-0 shadow-sm text-decoration-none h-100"
         style="transition:transform 0.2s;"
         onmouseover="this.style.transform='translateY(-4px)'"
         onmouseout="this.style.transform='translateY(0)'">
        <div class="card-body p-4 text-center">
          <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
               style="width:64px;height:64px;background:#e8f5e9;">
            <i class="bi bi-geo-alt-fill"
               style="font-size:1.8rem;color:#4caf50;"></i>
          </div>
          <h5 class="fw-bold text-dark">الميدانيون</h5>
          <p class="text-muted small mb-0">
            تقرير الزيارات والتتبع للموظفين الميدانيين
          </p>
        </div>
      </a>
    </div>

    <div class="col-md-6 col-lg-4">
      <a href="{% url 'reports:employees' %}"
         class="card border-0 shadow-sm text-decoration-none h-100"
         style="transition:transform 0.2s;"
         onmouseover="this.style.transform='translateY(-4px)'"
         onmouseout="this.style.transform='translateY(0)'">
        <div class="card-body p-4 text-center">
          <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
               style="width:64px;height:64px;background:#ede7f6;">
            <i class="bi bi-people-fill"
               style="font-size:1.8rem;color:#7c3aed;"></i>
          </div>
          <h5 class="fw-bold text-dark">الموظفون</h5>
          <p class="text-muted small mb-0">
            قائمة الموظفين مع بياناتهم الكاملة
          </p>
        </div>
      </a>
    </div>

  </div>
</div>
{% endblock %}
"""
)

# ── attendance_report.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'reports', 'attendance_report.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تقرير الحضور{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <!-- Header -->
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-calendar-check me-2" style="color:#06B6D4;"></i>
        تقرير الحضور والغياب
      </h4>
      <p class="text-muted mb-0">
        {{ start_date|date:"d/m/Y" }} ← {{ end_date|date:"d/m/Y" }}
      </p>
    </div>
    <div class="d-flex gap-2">
      <a href="?period={{ period }}&export=excel"
         class="btn btn-success btn-sm">
        <i class="bi bi-file-earmark-excel me-1"></i>Excel
      </a>
    </div>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" class="d-flex gap-3 align-items-center flex-wrap">
        <select name="period" class="form-select" style="max-width:180px;"
                onchange="this.form.submit()">
          <option value="today"      {% if period=='today'      %}selected{% endif %}>اليوم</option>
          <option value="week"       {% if period=='week'       %}selected{% endif %}>هذا الأسبوع</option>
          <option value="month"      {% if period=='month'      %}selected{% endif %}>هذا الشهر</option>
          <option value="last_month" {% if period=='last_month' %}selected{% endif %}>الشهر الماضي</option>
          <option value="quarter"    {% if period=='quarter'    %}selected{% endif %}>هذا الربع</option>
          <option value="year"       {% if period=='year'       %}selected{% endif %}>هذا العام</option>
          <option value="custom"     {% if period=='custom'     %}selected{% endif %}>مخصص</option>
        </select>
        {% if period == 'custom' %}
        <input type="date" name="start_date" class="form-control"
               style="max-width:160px;"
               value="{{ start_date|date:'Y-m-d' }}">
        <input type="date" name="end_date" class="form-control"
               style="max-width:160px;"
               value="{{ end_date|date:'Y-m-d' }}">
        <button type="submit" class="btn btn-primary btn-sm">عرض</button>
        {% endif %}
      </form>
    </div>
  </div>

  <!-- ملخص -->
  <div class="row g-3 mb-4">
    <div class="col-6 col-md-3 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold" style="color:#06B6D4;">{{ summary.present }}</div>
        <small class="text-muted">حاضر</small>
      </div>
    </div>
    <div class="col-6 col-md-3 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold text-danger">{{ summary.absent }}</div>
        <small class="text-muted">غائب</small>
      </div>
    </div>
    <div class="col-6 col-md-3 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold text-warning">{{ summary.late }}</div>
        <small class="text-muted">متأخر</small>
      </div>
    </div>
    <div class="col-6 col-md-3 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold text-info">{{ summary.on_leave }}</div>
        <small class="text-muted">إجازة</small>
      </div>
    </div>
    <div class="col-6 col-md-3 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold text-success">{{ summary.attendance_rate }}%</div>
        <small class="text-muted">نسبة الحضور</small>
      </div>
    </div>
    <div class="col-6 col-md-3 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold text-dark">{{ summary.work_hours_total }}</div>
        <small class="text-muted">ساعات عمل</small>
      </div>
    </div>
  </div>

  <!-- جدول التفاصيل -->
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th class="text-center">حاضر</th>
            <th class="text-center">غائب</th>
            <th class="text-center">متأخر</th>
            <th class="text-center">إجازة</th>
            <th class="text-center">نسبة الحضور</th>
            <th class="text-center">دقائق التأخير</th>
            <th class="text-center">ساعات العمل</th>
          </tr>
        </thead>
        <tbody>
          {% for d in details %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold">{{ d.employee.full_name_ar }}</div>
              <small class="text-muted">{{ d.employee.employee_code }}</small>
            </td>
            <td class="text-center text-success fw-bold">{{ d.present }}</td>
            <td class="text-center text-danger fw-bold">{{ d.absent }}</td>
            <td class="text-center text-warning fw-bold">{{ d.late }}</td>
            <td class="text-center text-info fw-bold">{{ d.on_leave }}</td>
            <td class="text-center">
              <div class="d-flex align-items-center justify-content-center gap-2">
                <div class="progress" style="width:60px;height:6px;">
                  <div class="progress-bar
                    {% if d.rate >= 90 %}bg-success
                    {% elif d.rate >= 70 %}bg-warning
                    {% else %}bg-danger{% endif %}"
                       style="width:{{ d.rate }}%"></div>
                </div>
                <small class="fw-bold">{{ d.rate }}%</small>
              </div>
            </td>
            <td class="text-center
              {% if d.late_mins > 120 %}text-danger fw-bold
              {% elif d.late_mins > 30 %}text-warning fw-bold
              {% else %}text-muted{% endif %}">
              {{ d.late_mins }}
            </td>
            <td class="text-center fw-bold">{{ d.work_hours }}</td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="8" class="text-center py-5 text-muted">
              لا يوجد بيانات حضور في هذه الفترة
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

</div>
{% endblock %}
"""
)

# ── late_report.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'reports', 'late_report.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تقرير التأخيرات{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-clock-history me-2" style="color:#f59e0b;"></i>
        تقرير التأخيرات
      </h4>
      <p class="text-muted mb-0">
        {{ start_date|date:"d/m/Y" }} ← {{ end_date|date:"d/m/Y" }}
      </p>
    </div>
    <a href="?period={{ period }}&export=excel"
       class="btn btn-success btn-sm">
      <i class="bi bi-file-earmark-excel me-1"></i>Excel
    </a>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get">
        <select name="period" class="form-select" style="max-width:180px;"
                onchange="this.form.submit()">
          <option value="today"      {% if period=='today'      %}selected{% endif %}>اليوم</option>
          <option value="week"       {% if period=='week'       %}selected{% endif %}>هذا الأسبوع</option>
          <option value="month"      {% if period=='month'      %}selected{% endif %}>هذا الشهر</option>
          <option value="last_month" {% if period=='last_month' %}selected{% endif %}>الشهر الماضي</option>
          <option value="year"       {% if period=='year'       %}selected{% endif %}>هذا العام</option>
        </select>
      </form>
    </div>
  </div>

  <div class="row g-4">

    <!-- تجميع حسب الموظف -->
    <div class="col-lg-5">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">إجمالي حسب الموظف</h5>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead style="background:#f8fafc;">
                <tr>
                  <th class="px-4 py-3">الموظف</th>
                  <th class="text-center">أيام</th>
                  <th class="text-center">دقائق</th>
                </tr>
              </thead>
              <tbody>
                {% for r in employee_late %}
                <tr>
                  <td class="px-4">
                    <div class="fw-semibold">
                      {{ r.employee__first_name_ar }}
                      {{ r.employee__last_name_ar }}
                    </div>
                    <small class="text-muted">
                      {{ r.employee__employee_code }}
                    </small>
                  </td>
                  <td class="text-center fw-bold text-warning">
                    {{ r.late_days }}
                  </td>
                  <td class="text-center fw-bold text-danger">
                    {{ r.total_late_minutes }}
                  </td>
                </tr>
                {% empty %}
                <tr>
                  <td colspan="3" class="text-center py-4 text-muted">
                    لا يوجد تأخيرات
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- سجلات التأخير التفصيلية -->
    <div class="col-lg-7">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">سجلات التأخير</h5>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead style="background:#f8fafc;">
                <tr>
                  <th class="px-4 py-3">الموظف</th>
                  <th>التاريخ</th>
                  <th class="text-center">دقائق التأخير</th>
                  <th>وقت الحضور</th>
                </tr>
              </thead>
              <tbody>
                {% for rec in late_records %}
                <tr>
                  <td class="px-4 fw-semibold">
                    {{ rec.employee.full_name_ar }}
                  </td>
                  <td>{{ rec.date|date:"d/m/Y" }}</td>
                  <td class="text-center">
                    <span class="badge
                      {% if rec.late_minutes > 60 %}bg-danger
                      {% elif rec.late_minutes > 30 %}bg-warning text-dark
                      {% else %}bg-secondary{% endif %}">
                      {{ rec.late_minutes }} د
                    </span>
                  </td>
                  <td class="text-muted">
                    {{ rec.check_in_time|time:"H:i"|default:"—" }}
                  </td>
                </tr>
                {% empty %}
                <tr>
                  <td colspan="4" class="text-center py-4 text-muted">
                    لا يوجد تأخيرات
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)

# ── leave_report.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'reports', 'leave_report.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تقرير الإجازات{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-calendar2-week me-2" style="color:#e91e63;"></i>
        تقرير الإجازات
      </h4>
    </div>
    <a href="?period={{ period }}&export=excel"
       class="btn btn-success btn-sm">
      <i class="bi bi-file-earmark-excel me-1"></i>Excel
    </a>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get">
        <select name="period" class="form-select" style="max-width:180px;"
                onchange="this.form.submit()">
          <option value="month"      {% if period=='month'      %}selected{% endif %}>هذا الشهر</option>
          <option value="last_month" {% if period=='last_month' %}selected{% endif %}>الشهر الماضي</option>
          <option value="quarter"    {% if period=='quarter'    %}selected{% endif %}>هذا الربع</option>
          <option value="year"       {% if period=='year'       %}selected{% endif %}>هذا العام</option>
        </select>
      </form>
    </div>
  </div>

  <!-- ملخص الحالات -->
  <div class="row g-3 mb-4">
    {% for status, count in by_status.items %}
    <div class="col-6 col-md-3">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold
          {% if status == 'موافق عليه' %}text-success
          {% elif status == 'مرفوض' %}text-danger
          {% elif status == 'قيد الانتظار' %}text-warning
          {% else %}text-secondary{% endif %}">
          {{ count }}
        </div>
        <small class="text-muted">{{ status }}</small>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="row g-4">

    <!-- حسب النوع -->
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">حسب نوع الإجازة</h5>
        </div>
        <div class="card-body">
          {% for bt in by_type %}
          <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
            <span>{{ bt.leave_type__name }}</span>
            <div class="text-end">
              <span class="badge bg-light text-dark">{{ bt.count }} طلب</span>
              <span class="badge ms-1" style="background:#06B6D4;">
                {{ bt.total_days }} يوم
              </span>
            </div>
          </div>
          {% empty %}
          <div class="text-center text-muted py-3">لا يوجد بيانات</div>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- الطلبات -->
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead style="background:#f8fafc;">
              <tr>
                <th class="px-4 py-3">الموظف</th>
                <th>النوع</th>
                <th>من</th>
                <th>إلى</th>
                <th class="text-center">أيام</th>
                <th>الحالة</th>
              </tr>
            </thead>
            <tbody>
              {% for lr in requests %}
              <tr>
                <td class="px-4 fw-semibold">{{ lr.employee.full_name_ar }}</td>
                <td>{{ lr.leave_type.name }}</td>
                <td>{{ lr.start_date|date:"d/m/Y" }}</td>
                <td>{{ lr.end_date|date:"d/m/Y" }}</td>
                <td class="text-center fw-bold">{{ lr.days_count }}</td>
                <td>
                  <span class="badge bg-{{ lr.status_color }}">
                    {{ lr.get_status_display }}
                  </span>
                </td>
              </tr>
              {% empty %}
              <tr>
                <td colspan="6" class="text-center py-5 text-muted">
                  لا يوجد طلبات إجازات
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
)

# ── field_report.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'reports', 'field_report.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تقرير الميدانيين{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-geo-alt me-2" style="color:#4caf50;"></i>
        تقرير الموظفين الميدانيين
      </h4>
    </div>
    <a href="?period={{ period }}&export=excel"
       class="btn btn-success btn-sm">
      <i class="bi bi-file-earmark-excel me-1"></i>Excel
    </a>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get">
        <select name="period" class="form-select" style="max-width:180px;"
                onchange="this.form.submit()">
          <option value="today"  {% if period=='today'  %}selected{% endif %}>اليوم</option>
          <option value="week"   {% if period=='week'   %}selected{% endif %}>هذا الأسبوع</option>
          <option value="month"  {% if period=='month'  %}selected{% endif %}>هذا الشهر</option>
          <option value="year"   {% if period=='year'   %}selected{% endif %}>هذا العام</option>
        </select>
      </form>
    </div>
  </div>

  <div class="row g-4">

    <!-- ملخص الموظفين -->
    <div class="col-lg-5">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">الموظفون الميدانيون</h5>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead style="background:#f8fafc;">
                <tr>
                  <th class="px-4 py-3">الموظف</th>
                  <th class="text-center">نقاط التتبع</th>
                  <th class="text-center">الزيارات</th>
                  <th class="text-center">مكتملة</th>
                </tr>
              </thead>
              <tbody>
                {% for r in field_summary %}
                <tr>
                  <td class="px-4 fw-semibold">
                    {{ r.employee.full_name_ar }}
                  </td>
                  <td class="text-center">{{ r.total_logs }}</td>
                  <td class="text-center fw-bold" style="color:#06B6D4;">
                    {{ r.total_visits }}
                  </td>
                  <td class="text-center text-success fw-bold">
                    {{ r.completed }}
                  </td>
                </tr>
                {% empty %}
                <tr>
                  <td colspan="4" class="text-center py-4 text-muted">
                    لا يوجد موظفون ميدانيون
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- الزيارات الأخيرة -->
    <div class="col-lg-7">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">الزيارات الأخيرة</h5>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead style="background:#f8fafc;">
                <tr>
                  <th class="px-4 py-3">الموظف</th>
                  <th>الموقع</th>
                  <th>التاريخ</th>
                  <th>الحالة</th>
                </tr>
              </thead>
              <tbody>
                {% for v in recent_visits %}
                <tr>
                  <td class="px-4 fw-semibold">
                    {{ v.employee.full_name_ar }}
                  </td>
                  <td class="text-muted small">
                    {{ v.location_name|default:"—" }}
                  </td>
                  <td class="text-muted small">
                    {{ v.arrival_time|date:"d/m H:i" }}
                  </td>
                  <td>
                    <span class="badge
                      {% if v.status == 'completed' %}bg-success
                      {% elif v.status == 'in_progress' %}bg-primary
                      {% else %}bg-secondary{% endif %}">
                      {{ v.get_status_display }}
                    </span>
                  </td>
                </tr>
                {% empty %}
                <tr>
                  <td colspan="4" class="text-center py-4 text-muted">
                    لا يوجد زيارات
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)

# ── employees_report.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'reports', 'employees_report.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تقرير الموظفين{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-people me-2" style="color:#7c3aed;"></i>
        تقرير الموظفين
      </h4>
      <p class="text-muted mb-0">إجمالي: {{ employees.count }} موظف</p>
    </div>
    <a href="?export=excel" class="btn btn-success btn-sm">
      <i class="bi bi-file-earmark-excel me-1"></i>Excel
    </a>
  </div>

  <!-- ملخص -->
  <div class="row g-3 mb-4">
    {% for status, count in by_status.items %}
    {% if count > 0 %}
    <div class="col-6 col-md-4 col-lg-2">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold" style="color:#06B6D4;">{{ count }}</div>
        <small class="text-muted">{{ status }}</small>
      </div>
    </div>
    {% endif %}
    {% endfor %}
  </div>

  <!-- جدول الموظفين -->
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th>القسم</th>
            <th>المسمى</th>
            <th>الفرع</th>
            <th>تاريخ التعيين</th>
            <th>الراتب</th>
            <th>الحالة</th>
          </tr>
        </thead>
        <tbody>
          {% for emp in employees %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold">{{ emp.full_name_ar }}</div>
              <small class="text-muted">{{ emp.employee_code }}</small>
            </td>
            <td class="text-muted small">
              {{ emp.department.name_ar|default:"—" }}
            </td>
            <td class="text-muted small">
              {{ emp.job_title.name_ar|default:"—" }}
            </td>
            <td class="text-muted small">
              {{ emp.branch.name_ar|default:"—" }}
            </td>
            <td class="text-muted small">
              {{ emp.hire_date|date:"d/m/Y"|default:"—" }}
            </td>
            <td class="fw-bold">
              {{ emp.basic_salary|default:"—" }}
            </td>
            <td>
              <span class="badge
                {% if emp.status == 'active' %}bg-success
                {% elif emp.status == 'on_leave' %}bg-info
                {% elif emp.status == 'suspended' %}bg-warning text-dark
                {% else %}bg-danger{% endif %}">
                {{ emp.get_status_display }}
              </span>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="7" class="text-center py-5 text-muted">
              لا يوجد موظفون
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 7. تحديث Dashboard بأرقام حقيقية
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Dashboard view بأرقام حقيقية...")

accounts_views_path = os.path.join(BASE_DIR, 'accounts', 'views.py')
accounts_views = read_file(accounts_views_path)

real_dashboard = '''

# ════════════════════════════════════════════════════════════
# Dashboard محدث بأرقام حقيقية
# ════════════════════════════════════════════════════════════
from django.contrib.auth.decorators import login_required
from django.utils import timezone as tz


@login_required
def dashboard(request):
    """لوحة التحكم الرئيسية"""
    from datetime import date

    company = request.user.company
    today   = date.today()
    context = {"page_title": "لوحة التحكم"}

    if not company:
        return render(request, "dashboard/index.html", context)

    try:
        from employees.models import Employee
        total_employees  = Employee.objects.filter(
            company=company, status="active").count()
        new_this_month   = Employee.objects.filter(
            company=company,
            hire_date__year=today.year,
            hire_date__month=today.month,
        ).count()
    except Exception:
        total_employees = new_this_month = 0

    try:
        from attendance.models import Attendance
        today_att    = Attendance.objects.filter(company=company, date=today)
        present_today = today_att.filter(
            status__in=["present", "late"]).count()
        absent_today  = today_att.filter(status="absent").count()
        late_today    = today_att.filter(status="late").count()
    except Exception:
        present_today = absent_today = late_today = 0

    try:
        from leaves.models import LeaveRequest
        pending_leaves = LeaveRequest.objects.filter(
            company=company, status="pending").count()
    except Exception:
        pending_leaves = 0

    try:
        from attendance.models import LocationLog
        from datetime import timedelta
        cutoff = tz.now() - timedelta(minutes=5)
        live_field = LocationLog.objects.filter(
            company=company,
            timestamp__gte=cutoff,
        ).values("employee").distinct().count()
    except Exception:
        live_field = 0

    try:
        from employees.models import Employee as Emp
        recent_employees = Emp.objects.filter(
            company=company
        ).select_related(
            "job_title", "department"
        ).order_by("-hire_date")[:5]
    except Exception:
        recent_employees = []

    try:
        from attendance.models import Attendance as Att
        recent_attendance = Att.objects.filter(
            company=company, date=today
        ).select_related("employee").order_by("-check_in_time")[:8]
    except Exception:
        recent_attendance = []

    context.update({
        "total_employees":  total_employees,
        "new_this_month":   new_this_month,
        "present_today":    present_today,
        "absent_today":     absent_today,
        "late_today":       late_today,
        "pending_leaves":   pending_leaves,
        "live_field":       live_field,
        "recent_employees": recent_employees,
        "recent_attendance":recent_attendance,
        "today":            today,
    })

    return render(request, "dashboard/index.html", context)
'''

if 'def dashboard(request)' not in accounts_views:
    append_file(accounts_views_path, real_dashboard)
    print("  ✅ تم إضافة dashboard view")
else:
    print("  ℹ️  dashboard view موجود - سنحدثه")
    # استبدال الـ dashboard القديم
    import re
    new_content = re.sub(
        r'@login_required\s*\ndef dashboard\(request\):.*?return render\(request,\s*["\']dashboard/index\.html["\'],\s*context\)',
        real_dashboard.strip(),
        accounts_views,
        flags=re.DOTALL
    )
    if new_content != accounts_views:
        write_file(accounts_views_path, new_content)


# ════════════════════════════════════════════════════════════
# 8. تحديث dashboard/index.html
# ════════════════════════════════════════════════════════════
print("\n📄 تحديث dashboard/index.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'dashboard', 'index.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}لوحة التحكم{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <!-- ترحيب -->
  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋
    </h4>
    <p class="text-muted mb-0">
      {{ today|date:"l، d MMMM Y" }} |
      {{ request.user.company.name_ar|default:"" }}
    </p>
  </div>

  <!-- بطاقات الإحصائيات -->
  <div class="row g-3 mb-4">

    <!-- إجمالي الموظفين -->
    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">إجمالي الموظفين</p>
              <h3 class="fw-black mb-0" style="color:#06B6D4;">
                {{ total_employees }}
              </h3>
              {% if new_this_month > 0 %}
              <small class="text-success">
                +{{ new_this_month }} هذا الشهر
              </small>
              {% endif %}
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#e0f7fa;">
              <i class="bi bi-people-fill fs-4" style="color:#06B6D4;"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- حاضر اليوم -->
    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">حاضر اليوم</p>
              <h3 class="fw-black mb-0 text-success">{{ present_today }}</h3>
              {% if late_today > 0 %}
              <small class="text-warning">{{ late_today }} متأخر</small>
              {% endif %}
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#e8f5e9;">
              <i class="bi bi-person-check-fill fs-4 text-success"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- غائب اليوم -->
    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">غائب اليوم</p>
              <h3 class="fw-black mb-0 text-danger">{{ absent_today }}</h3>
              {% if pending_leaves > 0 %}
              <small class="text-warning">{{ pending_leaves }} إجازة معلقة</small>
              {% endif %}
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#fde8e8;">
              <i class="bi bi-person-x-fill fs-4 text-danger"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ميدانيون نشطون -->
    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">ميدانيون نشطون</p>
              <h3 class="fw-black mb-0" style="color:#7c3aed;">{{ live_field }}</h3>
              <small class="text-muted">آخر 5 دقائق</small>
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#ede7f6;">
              <i class="bi bi-geo-alt-fill fs-4" style="color:#7c3aed;"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- روابط سريعة -->
  <div class="row g-3 mb-4">
    <div class="col-12">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-3">
          <div class="d-flex flex-wrap gap-2">
            <a href="{% url 'attendance:check_in_page' %}"
               class="btn btn-sm text-white"
               style="background:#06B6D4;">
              <i class="bi bi-qr-code-scan me-1"></i>تسجيل حضور
            </a>
            <a href="{% url 'employees:employee_list' %}"
               class="btn btn-sm btn-outline-secondary">
              <i class="bi bi-people me-1"></i>الموظفون
            </a>
            <a href="{% url 'leaves:leave_requests_list' %}"
               class="btn btn-sm btn-outline-secondary">
              <i class="bi bi-calendar2-week me-1"></i>الإجازات
            </a>
            <a href="{% url 'attendance:live_map' %}"
               class="btn btn-sm btn-outline-secondary">
              <i class="bi bi-map me-1"></i>الخريطة
            </a>
            <a href="{% url 'reports:home' %}"
               class="btn btn-sm btn-outline-secondary">
              <i class="bi bi-bar-chart me-1"></i>التقارير
            </a>
            <a href="{% url 'employees:employee_add' %}"
               class="btn btn-sm btn-outline-primary">
              <i class="bi bi-person-plus me-1"></i>موظف جديد
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="row g-4">

    <!-- حضور اليوم -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">حضور اليوم</h5>
          <a href="{% url 'attendance:attendance_list' %}"
             class="btn btn-sm btn-outline-primary">عرض الكل</a>
        </div>
        <div class="card-body p-0">
          {% if recent_attendance %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for att in recent_attendance %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">
                      {{ att.employee.full_name_ar }}
                    </div>
                  </td>
                  <td class="text-muted small">
                    {{ att.check_in_time|time:"H:i"|default:"—" }}
                  </td>
                  <td>
                    <span class="badge
                      {% if att.status == 'present' %}bg-success
                      {% elif att.status == 'late' %}bg-warning text-dark
                      {% elif att.status == 'absent' %}bg-danger
                      {% else %}bg-secondary{% endif %} rounded-pill">
                      {{ att.get_status_display }}
                    </span>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-calendar-x fs-1"></i>
            <p class="mt-2 small">لا يوجد سجلات حضور اليوم</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- آخر الموظفين -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">آخر الموظفين</h5>
          <a href="{% url 'employees:employee_list' %}"
             class="btn btn-sm btn-outline-primary">عرض الكل</a>
        </div>
        <div class="card-body p-0">
          {% if recent_employees %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for emp in recent_employees %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ emp.full_name_ar }}</div>
                    <small class="text-muted">{{ emp.employee_code }}</small>
                  </td>
                  <td class="text-muted small">
                    {{ emp.job_title.name_ar|default:"—" }}
                  </td>
                  <td class="text-muted small">
                    {{ emp.hire_date|date:"d/m/Y"|default:"—" }}
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-people fs-1"></i>
            <p class="mt-2 small">لا يوجد موظفون بعد</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 9. تحديث الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
sidebar_content = read_file(sidebar_path)

if 'reports:home' not in sidebar_content:
    reports_link = """
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'reports:home' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-bar-chart"></i>
                    <span>التقارير</span>
                  </a>
                </li>"""

    # نضيف قبل الإجازات
    if 'leaves:leave_requests_list' in sidebar_content:
        leave_idx = sidebar_content.find("{% url 'leaves:leave_requests_list' %}")
        section_start = sidebar_content.rfind('<!-- ══', 0, leave_idx)
        if section_start == -1:
            section_start = sidebar_content.rfind('<li', 0, leave_idx)
        sidebar_content = (
            sidebar_content[:section_start] +
            reports_link + '\n' +
            sidebar_content[section_start:]
        )
        write_file(sidebar_path, sidebar_content)
        print("  ✅ تم إضافة رابط التقارير")
    else:
        print("  ⚠️  مش لاقي مكان مناسب")
else:
    print("  ℹ️  رابط التقارير موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 19 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ reports app كامل
  2.  ✅ reports/utils.py - أدوات الحسابات
  3.  ✅ reports/views.py - 5 تقارير
  4.  ✅ reports/urls.py
  5.  ✅ 6 صفحات HTML (home + 5 تقارير)
  6.  ✅ Export Excel (CSV) لكل تقرير
  7.  ✅ Dashboard محدث بأرقام حقيقية
  8.  ✅ dashboard/index.html جديد
  9.  ✅ Sidebar محدث

🔗 URLs الجديدة:
  /reports/             ← الصفحة الرئيسية
  /reports/attendance/  ← الحضور والغياب
  /reports/late/        ← التأخيرات
  /reports/leaves/      ← الإجازات
  /reports/field/       ← الميدانيون
  /reports/employees/   ← الموظفون

🚀 الخطوة الجاية: Patch 20 - PWA
""")