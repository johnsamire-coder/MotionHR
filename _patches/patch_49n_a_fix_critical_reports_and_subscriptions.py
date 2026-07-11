"""
Patch 49N-A — Fix Critical Reports + Subscription Dashboard

الهدف:
1) إصلاح تقارير:
   - /reports/late/
   - /reports/leaves/
   - /reports/employees/
2) إصلاح مشكلة زر "الملف الشامل" لما الـ employee يكون None أو variable غلط في templates
3) إصلاح subscriptions:admin_dashboard
   - Decimal + float error
4) إعادة كتابة templates الحرجة بشكل آمن

هذا الباتش يعالج فقط الأولوية A (Critical Bugs)
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")


def backup(rel_path, backup_name):
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup: _patches/_backups/{backup_name}")


print("=" * 70)
print("Patch 49N-A — Fix Critical Reports + Subscription Dashboard")
print("=" * 70)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
for rel_path, backup_name in [
    ("reports/views.py", "reports_views_before_49n_a.py.bak"),
    ("templates/reports/attendance_report.html", "attendance_report_before_49n_a.html.bak"),
    ("templates/reports/late_report.html", "late_report_before_49n_a.html.bak"),
    ("templates/reports/leave_report.html", "leave_report_before_49n_a.html.bak"),
    ("templates/reports/employees_report.html", "employees_report_before_49n_a.html.bak"),
    ("subscriptions/views.py", "subscriptions_views_before_49n_a.py.bak"),
    ("templates/subscriptions/admin_dashboard.html", "subscriptions_admin_dashboard_before_49n_a.html.bak"),
]:
    backup(rel_path, backup_name)

# ────────────────────────────────────────────────────────────
# Step 1: Rewrite reports/views.py safely
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: إعادة كتابة reports/views.py")

reports_views = '''"""
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
'''
write_file("reports/views.py", reports_views)

# ────────────────────────────────────────────────────────────
# Step 2: Rewrite critical report templates safely
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إعادة كتابة templates التقارير الحرجة")

attendance_tpl = """{% extends 'base/dashboard_base.html' %}

{% block title %}تقرير الحضور والغياب{% endblock %}

{% block content %}
<div class="container-fluid">
  {% with report_title="تقرير الحضور والغياب" %}
  {% include 'reports/_report_header.html' %}
  {% endwith %}

  <div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-primary">{{ summary.total|default:0 }}</div><div class="small text-muted">إجمالي السجلات</div></div></div>
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-success">{{ summary.present|default:0 }}</div><div class="small text-muted">حاضر</div></div></div>
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-warning">{{ summary.late|default:0 }}</div><div class="small text-muted">متأخر</div></div></div>
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-danger">{{ summary.absent|default:0 }}</div><div class="small text-muted">غائب</div></div></div>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-2 align-items-end">
        <div class="col-md-3">
          <label class="form-label small">الفترة</label>
          <select name="period" class="form-select">
            <option value="week" {% if period == 'week' %}selected{% endif %}>هذا الأسبوع</option>
            <option value="month" {% if period == 'month' %}selected{% endif %}>هذا الشهر</option>
            <option value="year" {% if period == 'year' %}selected{% endif %}>هذه السنة</option>
            <option value="custom" {% if period == 'custom' %}selected{% endif %}>فترة مخصصة</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label small">من</label>
          <input type="date" name="start_date" value="{{ start_date|date:'Y-m-d' }}" class="form-control">
        </div>
        <div class="col-md-3">
          <label class="form-label small">إلى</label>
          <input type="date" name="end_date" value="{{ end_date|date:'Y-m-d' }}" class="form-control">
        </div>
        <div class="col-md-3 d-flex gap-2">
          <button class="btn btn-primary w-100">عرض</button>
          <a href="?period={{ period }}&start_date={{ start_date|date:'Y-m-d' }}&end_date={{ end_date|date:'Y-m-d' }}&export=excel" class="btn btn-success">Excel</a>
        </div>
      </form>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-header bg-white py-3"><h6 class="mb-0 fw-bold">تفاصيل التقرير</h6></div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>الموظف</th>
              <th>الكود</th>
              <th>حاضر</th>
              <th>غائب</th>
              <th>متأخر</th>
              <th>إجازة</th>
              <th>نسبة الحضور</th>
              <th>التأخير (د)</th>
              <th>ساعات العمل</th>
              <th>الملف</th>
            </tr>
          </thead>
          <tbody>
            {% for d in details %}
            <tr>
              <td>{{ d.employee.full_name_ar|default:"—" }}</td>
              <td>{{ d.employee.employee_code|default:"—" }}</td>
              <td>{{ d.present|default:0 }}</td>
              <td>{{ d.absent|default:0 }}</td>
              <td>{{ d.late|default:0 }}</td>
              <td>{{ d.on_leave|default:0 }}</td>
              <td>{{ d.rate|default:0 }}%</td>
              <td>{{ d.late_mins|default:0 }}</td>
              <td>{{ d.work_hours|default:0 }}</td>
              <td>
                {% if d.employee and d.employee.pk %}
                  <a href="{% url 'employees:comprehensive_profile' d.employee.pk %}" class="btn btn-sm btn-outline-info" title="الملف الشامل">
                    <i class="bi bi-person-lines-fill"></i>
                  </a>
                {% else %}
                  <span class="text-muted">—</span>
                {% endif %}
              </td>
            </tr>
            {% empty %}
            <tr><td colspan="10" class="text-center py-4 text-muted">لا توجد بيانات</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  {% include 'reports/_report_footer.html' %}
</div>
{% endblock %}
"""
write_file("templates/reports/attendance_report.html", attendance_tpl)

late_tpl = """{% extends 'base/dashboard_base.html' %}

{% block title %}تقرير التأخيرات{% endblock %}

{% block content %}
<div class="container-fluid">
  {% with report_title="تقرير التأخيرات" %}
  {% include 'reports/_report_header.html' %}
  {% endwith %}

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-2 align-items-end">
        <div class="col-md-3">
          <label class="form-label small">الفترة</label>
          <select name="period" class="form-select">
            <option value="week" {% if period == 'week' %}selected{% endif %}>هذا الأسبوع</option>
            <option value="month" {% if period == 'month' %}selected{% endif %}>هذا الشهر</option>
            <option value="year" {% if period == 'year' %}selected{% endif %}>هذه السنة</option>
            <option value="custom" {% if period == 'custom' %}selected{% endif %}>فترة مخصصة</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label small">من</label>
          <input type="date" name="start_date" value="{{ start_date|date:'Y-m-d' }}" class="form-control">
        </div>
        <div class="col-md-3">
          <label class="form-label small">إلى</label>
          <input type="date" name="end_date" value="{{ end_date|date:'Y-m-d' }}" class="form-control">
        </div>
        <div class="col-md-3 d-flex gap-2">
          <button class="btn btn-primary w-100">عرض</button>
          <a href="?period={{ period }}&start_date={{ start_date|date:'Y-m-d' }}&end_date={{ end_date|date:'Y-m-d' }}&export=excel" class="btn btn-success">Excel</a>
        </div>
      </form>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-header bg-white py-3"><h6 class="mb-0 fw-bold">تفاصيل التأخيرات</h6></div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>الموظف</th>
              <th>الكود</th>
              <th>التاريخ</th>
              <th>وقت الدخول</th>
              <th>التأخير (دقيقة)</th>
              <th>الوردية</th>
              <th>الملف</th>
            </tr>
          </thead>
          <tbody>
            {% for r in late_records %}
            <tr>
              <td>{{ r.employee.full_name_ar|default:"—" }}</td>
              <td>{{ r.employee.employee_code|default:"—" }}</td>
              <td>{{ r.date|date:"Y/m/d" }}</td>
              <td>{{ r.check_in_time|time:"H:i"|default:"—" }}</td>
              <td class="fw-bold text-danger">{{ r.late_minutes|default:0 }}</td>
              <td>{{ r.shift.name|default:"—" }}</td>
              <td>
                {% if r.employee and r.employee.pk %}
                  <a href="{% url 'employees:comprehensive_profile' r.employee.pk %}" class="btn btn-sm btn-outline-info" title="الملف الشامل">
                    <i class="bi bi-person-lines-fill"></i>
                  </a>
                {% else %}
                  <span class="text-muted">—</span>
                {% endif %}
              </td>
            </tr>
            {% empty %}
            <tr><td colspan="7" class="text-center py-4 text-muted">لا توجد تأخيرات</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  {% include 'reports/_report_footer.html' %}
</div>
{% endblock %}
"""
write_file("templates/reports/late_report.html", late_tpl)

leave_tpl = """{% extends 'base/dashboard_base.html' %}

{% block title %}تقرير الإجازات{% endblock %}

{% block content %}
<div class="container-fluid">
  {% with report_title="تقرير الإجازات" %}
  {% include 'reports/_report_header.html' %}
  {% endwith %}

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-2 align-items-end">
        <div class="col-md-3">
          <label class="form-label small">الفترة</label>
          <select name="period" class="form-select">
            <option value="week" {% if period == 'week' %}selected{% endif %}>هذا الأسبوع</option>
            <option value="month" {% if period == 'month' %}selected{% endif %}>هذا الشهر</option>
            <option value="year" {% if period == 'year' %}selected{% endif %}>هذه السنة</option>
            <option value="custom" {% if period == 'custom' %}selected{% endif %}>فترة مخصصة</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label small">من</label>
          <input type="date" name="start_date" value="{{ start_date|date:'Y-m-d' }}" class="form-control">
        </div>
        <div class="col-md-3">
          <label class="form-label small">إلى</label>
          <input type="date" name="end_date" value="{{ end_date|date:'Y-m-d' }}" class="form-control">
        </div>
        <div class="col-md-3 d-flex gap-2">
          <button class="btn btn-primary w-100">عرض</button>
          <a href="?period={{ period }}&start_date={{ start_date|date:'Y-m-d' }}&end_date={{ end_date|date:'Y-m-d' }}&export=excel" class="btn btn-success">Excel</a>
        </div>
      </form>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-header bg-white py-3"><h6 class="mb-0 fw-bold">تفاصيل الإجازات</h6></div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>الموظف</th>
              <th>الكود</th>
              <th>نوع الإجازة</th>
              <th>من</th>
              <th>إلى</th>
              <th>الحالة</th>
              <th>الملف</th>
            </tr>
          </thead>
          <tbody>
            {% for lr in leave_requests %}
            <tr>
              <td>{{ lr.employee.full_name_ar|default:"—" }}</td>
              <td>{{ lr.employee.employee_code|default:"—" }}</td>
              <td>{{ lr.leave_type.name_ar|default:lr.leave_type.name|default:"—" }}</td>
              <td>{{ lr.start_date|date:"Y/m/d" }}</td>
              <td>{{ lr.end_date|date:"Y/m/d" }}</td>
              <td>{{ lr.get_status_display|default:lr.status }}</td>
              <td>
                {% if lr.employee and lr.employee.pk %}
                  <a href="{% url 'employees:comprehensive_profile' lr.employee.pk %}" class="btn btn-sm btn-outline-info" title="الملف الشامل">
                    <i class="bi bi-person-lines-fill"></i>
                  </a>
                {% else %}
                  <span class="text-muted">—</span>
                {% endif %}
              </td>
            </tr>
            {% empty %}
            <tr><td colspan="7" class="text-center py-4 text-muted">لا توجد طلبات إجازة</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  {% include 'reports/_report_footer.html' %}
</div>
{% endblock %}
"""
write_file("templates/reports/leave_report.html", leave_tpl)

employees_tpl = """{% extends 'base/dashboard_base.html' %}

{% block title %}تقرير الموظفين{% endblock %}

{% block content %}
<div class="container-fluid">
  {% with report_title="تقرير الموظفين" %}
  {% include 'reports/_report_header.html' %}
  {% endwith %}

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-2 align-items-end">
        <div class="col-md-4">
          <label class="form-label small">الحالة</label>
          <select name="status" class="form-select">
            <option value="">الكل</option>
            <option value="active" {% if status_filter == 'active' %}selected{% endif %}>نشط</option>
            <option value="inactive" {% if status_filter == 'inactive' %}selected{% endif %}>غير نشط</option>
            <option value="suspended" {% if status_filter == 'suspended' %}selected{% endif %}>موقوف</option>
            <option value="terminated" {% if status_filter == 'terminated' %}selected{% endif %}>منتهي الخدمة</option>
          </select>
        </div>
        <div class="col-md-8 d-flex gap-2">
          <button class="btn btn-primary">عرض</button>
          <a href="?status={{ status_filter }}&export=excel" class="btn btn-success">Excel</a>
        </div>
      </form>
    </div>
  </div>

  <div class="card border-0 shadow-sm">
    <div class="card-header bg-white py-3"><h6 class="mb-0 fw-bold">قائمة الموظفين</h6></div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>الرقم الوظيفي</th>
              <th>الاسم</th>
              <th>القسم</th>
              <th>الفرع</th>
              <th>المسمى الوظيفي</th>
              <th>المدير المباشر</th>
              <th>تاريخ التعيين</th>
              <th>الحالة</th>
              <th>نوع العقد</th>
              <th>الملف</th>
            </tr>
          </thead>
          <tbody>
            {% for emp in employees %}
            <tr>
              <td>{{ emp.employee_code }}</td>
              <td>{{ emp.full_name_ar }}</td>
              <td>{{ emp.department.name_ar|default:emp.department.name_en|default:"—" }}</td>
              <td>{{ emp.branch.name_ar|default:emp.branch.name_en|default:"—" }}</td>
              <td>{{ emp.job_title.name_ar|default:emp.job_title.name_en|default:"—" }}</td>
              <td>{{ emp.direct_manager.full_name_ar|default:"—" }}</td>
              <td>{{ emp.hire_date|default:"—" }}</td>
              <td>{{ emp.get_status_display|default:emp.status }}</td>
              <td>{{ emp.get_contract_type_display|default:emp.contract_type }}</td>
              <td>
                {% if emp.pk %}
                  <a href="{% url 'employees:comprehensive_profile' emp.pk %}" class="btn btn-sm btn-outline-info" title="الملف الشامل">
                    <i class="bi bi-person-lines-fill"></i>
                  </a>
                {% else %}
                  <span class="text-muted">—</span>
                {% endif %}
              </td>
            </tr>
            {% empty %}
            <tr><td colspan="10" class="text-center py-4 text-muted">لا يوجد موظفون</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  {% include 'reports/_report_footer.html' %}
</div>
{% endblock %}
"""
write_file("templates/reports/employees_report.html", employees_tpl)

# ────────────────────────────────────────────────────────────
# Step 3: Override subscriptions admin dashboard safely
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إصلاح subscriptions admin_dashboard")

subs_views_path = "subscriptions/views.py"
subs_views_content = read_file(subs_views_path)
if subs_views_content is None:
    raise SystemExit("❌ ملف subscriptions/views.py غير موجود")

override_dashboard = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49N-A — Safe Admin Dashboard Override
# ═════════════════════════════════════════════════════════════

@login_required
def admin_dashboard(request):
    from decimal import Decimal
    from datetime import date
    from companies.models import Company
    from .models import CompanySubscription, SubscriptionPlan

    today = date.today()

    subscriptions = CompanySubscription.objects.select_related('company', 'plan').order_by('-id')
    plans = SubscriptionPlan.objects.all().order_by('id')
    companies_count = Company.objects.count()

    def _is_active(sub):
        status = str(getattr(sub, 'status', '') or '').lower()
        if status in ['cancelled', 'expired', 'inactive']:
            return False

        if hasattr(sub, 'is_active'):
            try:
                if sub.is_active is False:
                    return False
            except Exception:
                pass

        end_date = getattr(sub, 'end_date', None)
        if end_date and end_date < today:
            return False

        return True

    active_subscriptions = [s for s in subscriptions if _is_active(s)]
    expired_subscriptions = [s for s in subscriptions if not _is_active(s)]

    total_revenue = Decimal('0.00')
    for s in active_subscriptions:
        price = None
        if getattr(s, 'plan', None) and hasattr(s.plan, 'price'):
            price = s.plan.price
        elif hasattr(s, 'price'):
            price = s.price
        else:
            price = Decimal('0.00')

        try:
            total_revenue += Decimal(str(price))
        except Exception:
            pass

    monthly_revenue = total_revenue

    context = {
        'page_title': 'لوحة الاشتراكات',
        'subscriptions': subscriptions[:10],
        'recent_subscriptions': subscriptions[:10],
        'plans': plans,
        'companies_count': companies_count,
        'active_count': len(active_subscriptions),
        'expired_count': len(expired_subscriptions),
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
    }
    return render(request, 'subscriptions/admin_dashboard.html', context)
'''
if "Patch 49N-A — Safe Admin Dashboard Override" not in subs_views_content:
    subs_views_content = subs_views_content.rstrip() + "\n" + override_dashboard + "\n"
    write_file(subs_views_path, subs_views_content)
else:
    print("ℹ️ admin_dashboard override موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 4: Rewrite admin dashboard template safely
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: إعادة كتابة subscriptions/admin_dashboard.html")

subs_tpl = """{% extends 'base/dashboard_base.html' %}

{% block title %}لوحة الاشتراكات{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold"><i class="bi bi-stars text-primary me-2"></i>لوحة الاشتراكات</h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item active">الاشتراكات</li>
        </ol>
      </nav>
    </div>
  </div>

  <div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-primary">{{ companies_count }}</div><div class="small text-muted">الشركات</div></div></div>
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-success">{{ active_count }}</div><div class="small text-muted">اشتراكات فعالة</div></div></div>
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-danger">{{ expired_count }}</div><div class="small text-muted">منتهية / غير فعالة</div></div></div>
    <div class="col-md-3"><div class="card border-0 shadow-sm text-center py-3"><div class="fs-3 fw-bold text-warning">{{ total_revenue }}</div><div class="small text-muted">إجمالي الإيراد</div></div></div>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-header bg-white py-3"><h6 class="mb-0 fw-bold">أحدث الاشتراكات</h6></div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>الشركة</th>
              <th>الباقة</th>
              <th>البداية</th>
              <th>النهاية</th>
              <th>الحالة</th>
            </tr>
          </thead>
          <tbody>
            {% for sub in recent_subscriptions %}
            <tr>
              <td>{{ sub.company.name_ar|default:sub.company.name_en|default:"—" }}</td>
              <td>{{ sub.plan.name|default:"—" }}</td>
              <td>{{ sub.start_date|default:"—" }}</td>
              <td>{{ sub.end_date|default:"—" }}</td>
              <td>
                {% if sub.is_active %}
                  <span class="badge bg-success-subtle text-success">فعّال</span>
                {% else %}
                  <span class="badge bg-danger-subtle text-danger">غير فعّال</span>
                {% endif %}
              </td>
            </tr>
            {% empty %}
            <tr><td colspan="5" class="text-center py-4 text-muted">لا توجد اشتراكات</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
write_file("templates/subscriptions/admin_dashboard.html", subs_tpl)

print("\n" + "=" * 70)
print("✅ Patch 49N-A اكتمل")
print("=" * 70)
print("""
تم إصلاح:
  ✅ reports:late
  ✅ reports:leaves
  ✅ reports:employees
  ✅ subscriptions:admin_dashboard

شغّل الآن:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000

ثم اختبر:
  /reports/late/
  /reports/leaves/
  /reports/employees/
  /subscriptions/
""")