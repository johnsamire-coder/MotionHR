"""
reports/views.py — Patch 49N-A
إعادة كتابة آمنة لمنع:
- Reverse errors في profile buttons
- employees_report returning None
"""

from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .utils import (
    get_date_range,
    get_attendance_summary,
    get_employee_attendance_details,
    get_field_tracking_summary,
    export_to_excel,
)


def _get_report_company(request):
    company = getattr(request.user, 'company', None)
    if not company:
        try:
            company = request.user.employee.company
        except Exception:
            company = None
    return company


@login_required
def reports_home(request):
    company = _get_report_company(request)
    return render(request, "reports/home.html", {
        "page_title": "التقارير",
        "company": company,
    })


@login_required
def attendance_report(request):
    company = _get_report_company(request)
    period = request.GET.get("period", "month")

    custom_start = custom_end = None
    if period == "custom":
        try:
            custom_start = date.fromisoformat(request.GET.get("start_date", ""))
            custom_end   = date.fromisoformat(request.GET.get("end_date", ""))
        except Exception:
            period = "month"

    start_date, end_date = get_date_range(period, custom_start, custom_end)
    summary = get_attendance_summary(company, start_date, end_date)
    details = get_employee_attendance_details(company, start_date, end_date)

    if request.GET.get("export") == "excel":
        headers = [
            "الموظف", "الرقم الوظيفي", "الحاضر", "الغائب",
            "المتأخر", "إجازة", "الإجمالي", "نسبة الحضور%",
            "إجمالي التأخير (دقيقة)", "ساعات العمل"
        ]
        rows = [[
            d["employee"].full_name_ar if d.get("employee") else "—",
            d["employee"].employee_code if d.get("employee") else "—",
            d.get("present", 0), d.get("absent", 0), d.get("late", 0),
            d.get("on_leave", 0), d.get("total", 0), d.get("rate", 0),
            d.get("late_mins", 0), d.get("work_hours", 0),
        ] for d in details]
        return export_to_excel(
            headers, rows,
            filename=f"attendance_{start_date}_{end_date}",
            company=company,
            report_title=f"تقرير الحضور والغياب — {start_date} إلى {end_date}"
        )

    context = {
        "page_title": "تقرير الحضور والغياب",
        "report_title": "تقرير الحضور والغياب",
        "summary": summary,
        "details": details,
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "company": company,
    }
    return render(request, "reports/attendance_report.html", context)


@login_required
def late_report(request):
    from attendance.models import Attendance

    company = _get_report_company(request)
    period = request.GET.get("period", "month")

    custom_start = custom_end = None
    if period == "custom":
        try:
            custom_start = date.fromisoformat(request.GET.get("start_date", ""))
            custom_end   = date.fromisoformat(request.GET.get("end_date", ""))
        except Exception:
            period = "month"

    start_date, end_date = get_date_range(period, custom_start, custom_end)

    late_records = Attendance.objects.filter(
        company=company,
        date__range=(start_date, end_date),
        status="late"
    ).select_related("employee", "shift").order_by("-date")

    if request.GET.get("export") == "excel":
        headers = ["الموظف", "الرقم الوظيفي", "التاريخ", "وقت الدخول", "التأخير (دقيقة)", "الوردية"]
        rows = []
        for r in late_records:
            rows.append([
                r.employee.full_name_ar if getattr(r, 'employee', None) else "—",
                r.employee.employee_code if getattr(r, 'employee', None) else "—",
                str(r.date),
                str(r.check_in_time) if getattr(r, 'check_in_time', None) else "—",
                getattr(r, 'late_minutes', 0) or 0,
                getattr(getattr(r, 'shift', None), 'name', None) or "—",
            ])
        return export_to_excel(
            headers, rows,
            filename=f"late_{start_date}_{end_date}",
            company=company,
            report_title=f"تقرير التأخيرات — {start_date} إلى {end_date}"
        )

    context = {
        "page_title": "تقرير التأخيرات",
        "report_title": "تقرير التأخيرات",
        "late_records": late_records,
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "company": company,
    }
    return render(request, "reports/late_report.html", context)


@login_required
def leave_report(request):
    from leaves.models import LeaveRequest

    company = _get_report_company(request)
    period = request.GET.get("period", "month")

    custom_start = custom_end = None
    if period == "custom":
        try:
            custom_start = date.fromisoformat(request.GET.get("start_date", ""))
            custom_end   = date.fromisoformat(request.GET.get("end_date", ""))
        except Exception:
            period = "month"

    start_date, end_date = get_date_range(period, custom_start, custom_end)

    leave_requests = LeaveRequest.objects.filter(
        employee__company=company,
        start_date__range=(start_date, end_date)
    ).select_related("employee", "leave_type").order_by("-start_date")

    if request.GET.get("export") == "excel":
        headers = ["الموظف", "الرقم الوظيفي", "نوع الإجازة", "من", "إلى", "الأيام", "الحالة"]
        rows = []
        for r in leave_requests:
            try:
                days = (r.end_date - r.start_date).days + 1
            except Exception:
                days = "—"

            leave_type_name = "—"
            if getattr(r, 'leave_type', None):
                leave_type_name = (
                    getattr(r.leave_type, 'name_ar', None)
                    or getattr(r.leave_type, 'name', None)
                    or "—"
                )

            rows.append([
                r.employee.full_name_ar if getattr(r, 'employee', None) else "—",
                r.employee.employee_code if getattr(r, 'employee', None) else "—",
                leave_type_name,
                str(r.start_date),
                str(r.end_date),
                days,
                r.get_status_display() if hasattr(r, 'get_status_display') else getattr(r, 'status', '—'),
            ])

        return export_to_excel(
            headers, rows,
            filename=f"leave_{start_date}_{end_date}",
            company=company,
            report_title=f"تقرير الإجازات — {start_date} إلى {end_date}"
        )

    context = {
        "page_title": "تقرير الإجازات",
        "report_title": "تقرير الإجازات",
        "leave_requests": leave_requests,
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "company": company,
    }
    return render(request, "reports/leave_report.html", context)


@login_required
def employees_report(request):
    from employees.models import Employee

    company = _get_report_company(request)
    employees = Employee.objects.filter(
        company=company
    ).select_related("branch", "department", "job_title", "direct_manager").order_by("employee_code")

    status_filter = request.GET.get("status", "")
    if status_filter:
        employees = employees.filter(status=status_filter)

    if request.GET.get("export") == "excel":
        headers = [
            "الرقم الوظيفي", "الاسم", "القسم", "الفرع",
            "المسمى الوظيفي", "المدير المباشر", "تاريخ التعيين", "الحالة", "نوع العقد"
        ]
        rows = []
        for emp in employees:
            dept_name = "—"
            if getattr(emp, 'department', None):
                dept_name = (
                    getattr(emp.department, 'name_ar', None)
                    or getattr(emp.department, 'name_en', None)
                    or "—"
                )
            branch_name = "—"
            if getattr(emp, 'branch', None):
                branch_name = (
                    getattr(emp.branch, 'name_ar', None)
                    or getattr(emp.branch, 'name_en', None)
                    or getattr(emp.branch, 'name', None)
                    or "—"
                )
            job_name = "—"
            if getattr(emp, 'job_title', None):
                job_name = (
                    getattr(emp.job_title, 'name_ar', None)
                    or getattr(emp.job_title, 'name_en', None)
                    or "—"
                )
            manager_name = "—"
            if getattr(emp, 'direct_manager', None):
                manager_name = getattr(emp.direct_manager, 'full_name_ar', None) or "—"

            rows.append([
                emp.employee_code,
                emp.full_name_ar,
                dept_name,
                branch_name,
                job_name,
                manager_name,
                str(emp.hire_date) if getattr(emp, 'hire_date', None) else "—",
                emp.get_status_display() if hasattr(emp, 'get_status_display') else getattr(emp, 'status', "—"),
                emp.get_contract_type_display() if hasattr(emp, 'get_contract_type_display') else getattr(emp, 'contract_type', "—"),
            ])

        return export_to_excel(
            headers, rows,
            filename=f"employees_{date.today()}",
            company=company,
            report_title="تقرير الموظفين"
        )

    context = {
        "page_title": "تقرير الموظفين",
        "report_title": "تقرير الموظفين",
        "employees": employees,
        "status_filter": status_filter,
        "company": company,
    }
    return render(request, "reports/employees_report.html", context)


@login_required
def field_report(request):
    company = _get_report_company(request)
    period = request.GET.get("period", "month")

    custom_start = custom_end = None
    if period == "custom":
        try:
            custom_start = date.fromisoformat(request.GET.get("start_date", ""))
            custom_end   = date.fromisoformat(request.GET.get("end_date", ""))
        except Exception:
            period = "month"

    start_date, end_date = get_date_range(period, custom_start, custom_end)
    tracking_data = get_field_tracking_summary(company, start_date, end_date)

    context = {
        "page_title": "تقرير الموظفين الميدانيين",
        "report_title": "تقرير الموظفين الميدانيين",
        "tracking_data": tracking_data,
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "company": company,
    }
    return render(request, "reports/field_report.html", context)
