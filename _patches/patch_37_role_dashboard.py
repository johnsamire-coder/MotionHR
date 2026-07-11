#!/usr/bin/env python3
"""
Patch 37: Role-based Dashboard
==============================
1) Dashboard مختلف حسب الدور
2) Dashboard للموظف
3) Dashboard للمدير
4) Dashboard للإدارة / HR / صاحب الشركة
5) HR يشوف ملخص موافقات ميثاق العمل
6) تجهيز direct_manager لبيانات الديمو
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.utils import timezone


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 37: Role-based Dashboard")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) تجهيز direct_manager لبيانات الديمو
# ════════════════════════════════════════════════════════════
print("\n🔧 تجهيز بيانات المدير والفريق...")

try:
    from employees.models import Employee

    mgr_emp = Employee.all_objects.filter(user__username="manager1").first()
    if mgr_emp and hasattr(mgr_emp, "pk"):
        for code in ["EMP10003", "EMP10004"]:
            emp = Employee.all_objects.filter(employee_code=code).first()
            if emp and hasattr(emp, "direct_manager") and emp.direct_manager_id != mgr_emp.id:
                emp.direct_manager = mgr_emp
                emp.save(update_fields=["direct_manager"])
                print(f"  ✅ تم ربط {code} بالمدير manager1")
    else:
        print("  ℹ️  manager1 غير مربوط بموظف أو direct_manager غير متاح")
except Exception as e:
    print(f"  ⚠️  تعذر تجهيز direct_manager: {e}")


# ════════════════════════════════════════════════════════════
# 2) تحديث accounts/views.py
# إضافة dashboard جديد في آخر الملف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/views.py...")

views_path = os.path.join(BASE_DIR, "accounts", "views.py")
views = read_file(views_path)

role_dashboard_code = '''

# ════════════════════════════════════════════════════════════
# Dashboard حسب الدور
# ════════════════════════════════════════════════════════════
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone as dj_timezone


@login_required
def dashboard(request):
    """لوحة تحكم حسب الدور"""
    today = dj_timezone.now().date()
    role = getattr(request.user, "role", "") or ""
    company = getattr(request.user, "company", None)

    context = {
        "page_title": "لوحة التحكم",
        "today": today,
        "dashboard_mode": "guest",
        "role": role,
        "current_employee": getattr(request, "current_employee", None),
    }

    # لو مفيش شركة
    if not company and role != "super_admin":
        return render(request, "dashboard/index.html", context)

    # استيرادات آمنة
    try:
        from employees.models import Employee, Deduction
    except Exception:
        Employee = None
        Deduction = None

    try:
        from attendance.models import Attendance, LocationLog
    except Exception:
        Attendance = None
        LocationLog = None

    try:
        from requests_app.models import EmployeeRequest
    except Exception:
        EmployeeRequest = None

    try:
        from leaves.models import LeaveBalance, LeaveRequest
    except Exception:
        LeaveBalance = None
        LeaveRequest = None

    try:
        from companies.models import WorkCharter, CharterAcceptance
    except Exception:
        WorkCharter = None
        CharterAcceptance = None

    # current employee
    current_employee = getattr(request, "current_employee", None)
    if not current_employee and Employee:
        current_employee = Employee.all_objects.filter(user=request.user).first()

    context["current_employee"] = current_employee

    # ═══════════════════════════════════════
    # Employee Dashboard
    # ═══════════════════════════════════════
    if role == "employee":
        context["dashboard_mode"] = "employee"

        today_attendance = None
        if Attendance and current_employee:
            today_attendance = Attendance.objects.filter(
                employee=current_employee,
                date=today
            ).first()

        attendance_text = "لم تسجل حضور اليوم"
        attendance_color = "secondary"
        if today_attendance:
            if getattr(today_attendance, "check_out_time", None):
                attendance_text = "تم تسجيل الحضور والانصراف"
                attendance_color = "success"
            elif getattr(today_attendance, "check_in_time", None):
                attendance_text = "أنت في العمل الآن"
                attendance_color = "warning"

        # رصيد الإجازات
        leave_balances = []
        leave_remaining_total = 0
        if LeaveBalance and current_employee:
            leave_balances = LeaveBalance.objects.filter(
                company=company,
                employee=current_employee,
                year=today.year
            ).select_related("leave_type")
            try:
                leave_remaining_total = sum(
                    max(float(getattr(b, "remaining_days", 0) or 0), 0)
                    for b in leave_balances
                )
            except Exception:
                leave_remaining_total = 0

        # طلباتي
        pending_requests_count = 0
        recent_requests = []
        if EmployeeRequest and current_employee:
            pending_requests_count = EmployeeRequest.objects.filter(
                company=company,
                employee=current_employee,
                status="pending"
            ).count()
            recent_requests = EmployeeRequest.objects.filter(
                company=company,
                employee=current_employee
            ).select_related("request_type").order_by("-created_at")[:5]

        # خصوماتي
        recent_deductions = []
        deductions_month_total = 0
        if Deduction and current_employee:
            current_month_deductions = Deduction.objects.filter(
                company=company,
                employee=current_employee,
                month=today.month,
                year=today.year,
                is_visible_to_employee=True
            )
            recent_deductions = current_month_deductions.order_by("-date")[:5]
            try:
                deductions_month_total = current_month_deductions.aggregate(
                    total=Sum("amount")
                )["total"] or 0
            except Exception:
                deductions_month_total = 0

        # الميثاق
        charter_accepted = True
        if WorkCharter and CharterAcceptance and current_employee:
            charter = WorkCharter.objects.filter(
                company=company,
                is_active=True
            ).first()
            if charter:
                charter_accepted = CharterAcceptance.objects.filter(
                    employee=current_employee,
                    charter=charter
                ).exists()

        context.update({
            "today_attendance": today_attendance,
            "attendance_text": attendance_text,
            "attendance_color": attendance_color,
            "leave_balances": leave_balances,
            "leave_remaining_total": leave_remaining_total,
            "pending_requests_count": pending_requests_count,
            "recent_requests": recent_requests,
            "recent_deductions": recent_deductions,
            "deductions_month_total": deductions_month_total,
            "charter_accepted": charter_accepted,
        })

        return render(request, "dashboard/index.html", context)

    # ═══════════════════════════════════════
    # Manager Dashboard
    # ═══════════════════════════════════════
    if role == "manager":
        context["dashboard_mode"] = "manager"

        team_members = []
        team_count = 0
        team_present_today = 0
        team_pending_requests = 0
        team_pending_leaves = 0
        recent_team_requests = []

        if Employee:
            manager_emp = current_employee or Employee.all_objects.filter(user=request.user).first()
            if manager_emp and hasattr(manager_emp, "pk") and hasattr(manager_emp, "direct_reports"):
                try:
                    team_qs = Employee.all_objects.filter(
                        company=company,
                        direct_manager=manager_emp,
                        status="active"
                    ).select_related("department", "job_title")
                except Exception:
                    team_qs = Employee.all_objects.none()
            else:
                try:
                    team_qs = Employee.all_objects.filter(
                        company=company,
                        direct_manager=manager_emp
                    ).select_related("department", "job_title")
                except Exception:
                    team_qs = Employee.all_objects.none()

            team_members = list(team_qs[:8])
            team_count = team_qs.count()
            team_ids = list(team_qs.values_list("id", flat=True))

            if Attendance and team_ids:
                team_present_today = Attendance.objects.filter(
                    company=company,
                    employee_id__in=team_ids,
                    date=today,
                    status__in=["present", "late"]
                ).count()

            if EmployeeRequest and team_ids:
                team_pending_requests = EmployeeRequest.objects.filter(
                    company=company,
                    employee_id__in=team_ids,
                    status="pending"
                ).count()

                recent_team_requests = EmployeeRequest.objects.filter(
                    company=company,
                    employee_id__in=team_ids
                ).select_related("employee", "request_type").order_by("-created_at")[:5]

            if LeaveRequest and team_ids:
                team_pending_leaves = LeaveRequest.objects.filter(
                    company=company,
                    employee_id__in=team_ids,
                    status="pending"
                ).count()

        context.update({
            "team_members": team_members,
            "team_count": team_count,
            "team_present_today": team_present_today,
            "team_pending_requests": team_pending_requests,
            "team_pending_leaves": team_pending_leaves,
            "recent_team_requests": recent_team_requests,
        })

        return render(request, "dashboard/index.html", context)

    # ═══════════════════════════════════════
    # HR / Company Admin / Super Admin Dashboard
    # ═══════════════════════════════════════
    context["dashboard_mode"] = "admin"

    total_employees = 0
    present_today = 0
    absent_today = 0
    late_today = 0
    live_field = 0
    pending_requests = 0
    pending_leaves = 0
    recent_employees = []
    recent_attendance = []
    recent_requests = []
    charter_accepted_count = 0
    charter_not_accepted_count = 0
    charter_not_accepted_employees = []

    if Employee:
        try:
            total_employees = Employee.all_objects.filter(
                company=company,
                status="active"
            ).count()
            recent_employees = Employee.all_objects.filter(
                company=company
            ).select_related("job_title", "department").order_by("-hire_date")[:6]
        except Exception:
            pass

    if Attendance:
        try:
            present_today = Attendance.objects.filter(
                company=company,
                date=today,
                status__in=["present", "late"]
            ).count()

            absent_today = Attendance.objects.filter(
                company=company,
                date=today,
                status="absent"
            ).count()

            late_today = Attendance.objects.filter(
                company=company,
                date=today,
                status="late"
            ).count()

            recent_attendance = Attendance.objects.filter(
                company=company,
                date=today
            ).select_related("employee").order_by("-id")[:8]
        except Exception:
            pass

    if LocationLog:
        try:
            cutoff = dj_timezone.now() - __import__("datetime").timedelta(minutes=10)
            live_field = LocationLog.objects.filter(
                company=company,
                timestamp__gte=cutoff
            ).values("employee").distinct().count()
        except Exception:
            pass

    if EmployeeRequest:
        try:
            pending_requests = EmployeeRequest.objects.filter(
                company=company,
                status="pending"
            ).count()

            recent_requests = EmployeeRequest.objects.filter(
                company=company
            ).select_related("employee", "request_type").order_by("-created_at")[:6]
        except Exception:
            pass

    if LeaveRequest:
        try:
            pending_leaves = LeaveRequest.objects.filter(
                company=company,
                status="pending"
            ).count()
        except Exception:
            pass

    # الميثاق - مهم لـ HR / الإدارة
    if WorkCharter and CharterAcceptance and Employee:
        try:
            charter = WorkCharter.objects.filter(
                company=company,
                is_active=True
            ).first()

            if charter:
                charter_accepted_count = CharterAcceptance.objects.filter(
                    charter=charter
                ).count()

                active_employees_qs = Employee.all_objects.filter(
                    company=company,
                    status="active"
                )
                active_count = active_employees_qs.count()
                charter_not_accepted_count = max(active_count - charter_accepted_count, 0)

                accepted_ids = CharterAcceptance.objects.filter(
                    charter=charter
                ).values_list("employee_id", flat=True)

                charter_not_accepted_employees = active_employees_qs.exclude(
                    id__in=accepted_ids
                )[:5]
        except Exception:
            pass

    context.update({
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "late_today": late_today,
        "live_field": live_field,
        "pending_requests": pending_requests,
        "pending_leaves": pending_leaves,
        "recent_employees": recent_employees,
        "recent_attendance": recent_attendance,
        "recent_requests": recent_requests,
        "charter_accepted_count": charter_accepted_count,
        "charter_not_accepted_count": charter_not_accepted_count,
        "charter_not_accepted_employees": charter_not_accepted_employees,
    })

    return render(request, "dashboard/index.html", context)
'''

# نضيف/نستبدل dashboard الموجود بطريقة آمنة
if "Dashboard حسب الدور" not in views:
    views += role_dashboard_code
    write_file(views_path, views)
    print("  ✅ تم إضافة dashboard حسب الدور")
else:
    print("  ℹ️  dashboard حسب الدور موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3) تحديث template dashboard/index.html
# ════════════════════════════════════════════════════════════
print("\n📄 تحديث templates/dashboard/index.html...")

dashboard_template = r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}لوحة التحكم{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <!-- Header -->
  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋
    </h4>
    <p class="text-muted mb-0">
      {{ today|date:"d/m/Y" }}
      {% if request.user.company %}| {{ request.user.company.name_ar }}{% endif %}
    </p>
  </div>

  {% if dashboard_mode == 'employee' %}
  <!-- ═════════ Employee Dashboard ═════════ -->
  <div class="row g-3 mb-4">

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-{{ attendance_color }}">{{ attendance_text }}</div>
          <small class="text-muted">حالة اليوم</small>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold" style="color:#06B6D4;">
            {{ leave_remaining_total }}
          </div>
          <small class="text-muted">رصيد الإجازات</small>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-warning">{{ pending_requests_count }}</div>
          <small class="text-muted">طلبات معلقة</small>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-danger">{{ deductions_month_total }}</div>
          <small class="text-muted">خصومات الشهر</small>
        </div>
      </div>
    </div>

  </div>

  <!-- Quick Links -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <div class="d-flex flex-wrap gap-2">
        {% if request.current_employee %}
        <a href="{% url 'attendance:check_in' %}" class="btn btn-sm text-white" style="background:#06B6D4;">
          <i class="bi bi-qr-code-scan me-1"></i>تسجيل حضور
        </a>
        {% endif %}
        <a href="{% url 'requests_app:add' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-plus-circle me-1"></i>طلب جديد
        </a>
        <a href="{% url 'employees:my_balance' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-wallet2 me-1"></i>رصيد الإجازات
        </a>
        <a href="{% url 'employees:my_deductions' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-receipt-cutoff me-1"></i>خصوماتي
        </a>
        <a href="{% url 'companies:charter' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-file-earmark-text me-1"></i>الميثاق
        </a>
      </div>
    </div>
  </div>

  <div class="row g-4">

    <!-- طلباتي -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">آخر طلباتي</h5>
          <a href="{% url 'requests_app:list' %}" class="btn btn-sm btn-outline-primary">عرض الكل</a>
        </div>
        <div class="card-body p-0">
          {% if recent_requests %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for req in recent_requests %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ req.subject }}</div>
                    <small class="text-muted">{{ req.request_type.name }}</small>
                  </td>
                  <td class="text-end pe-4">
                    <span class="badge bg-{{ req.status_color }}">
                      {{ req.get_status_display }}
                    </span>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-inbox fs-1"></i>
            <p class="mt-2 small">لا توجد طلبات بعد</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- خصوماتي -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">آخر الخصومات</h5>
          <a href="{% url 'employees:my_deductions' %}" class="btn btn-sm btn-outline-primary">عرض الكل</a>
        </div>
        <div class="card-body p-0">
          {% if recent_deductions %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for ded in recent_deductions %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ ded.get_deduction_type_display }}</div>
                    <small class="text-muted">{{ ded.reason|truncatechars:40 }}</small>
                  </td>
                  <td class="text-end pe-4 text-danger fw-bold">
                    {{ ded.amount }}
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-emoji-smile fs-1"></i>
            <p class="mt-2 small">لا توجد خصومات</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

  </div>

  {% elif dashboard_mode == 'manager' %}
  <!-- ═════════ Manager Dashboard ═════════ -->
  <div class="row g-3 mb-4">

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold" style="color:#06B6D4;">{{ team_count }}</div>
          <small class="text-muted">أعضاء فريقي</small>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-success">{{ team_present_today }}</div>
          <small class="text-muted">حاضر اليوم</small>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-warning">{{ team_pending_requests }}</div>
          <small class="text-muted">طلبات الفريق</small>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-info">{{ team_pending_leaves }}</div>
          <small class="text-muted">إجازات معلقة</small>
        </div>
      </div>
    </div>

  </div>

  <div class="row g-4">

    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">فريقي</h5>
        </div>
        <div class="card-body p-0">
          {% if team_members %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for emp in team_members %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ emp.full_name_ar }}</div>
                    <small class="text-muted">
                      {{ emp.job_title.name_ar|default:"" }}
                    </small>
                  </td>
                  <td class="text-end pe-4 text-muted small">
                    {{ emp.employee_code }}
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-people fs-1"></i>
            <p class="mt-2 small">لا يوجد فريق مربوط بك حاليًا</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">آخر طلبات الفريق</h5>
        </div>
        <div class="card-body p-0">
          {% if recent_team_requests %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for req in recent_team_requests %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ req.employee.full_name_ar }}</div>
                    <small class="text-muted">{{ req.request_type.name }}</small>
                  </td>
                  <td class="text-end pe-4">
                    <span class="badge bg-{{ req.status_color }}">
                      {{ req.get_status_display }}
                    </span>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-inbox fs-1"></i>
            <p class="mt-2 small">لا توجد طلبات لفريقك</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

  </div>

  {% else %}
  <!-- ═════════ Admin / HR / Company Admin Dashboard ═════════ -->
  <div class="row g-3 mb-4">

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">إجمالي الموظفين</p>
              <h3 class="fw-black mb-0" style="color:#06B6D4;">{{ total_employees }}</h3>
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#e0f7fa;">
              <i class="bi bi-people-fill fs-4" style="color:#06B6D4;"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

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

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">طلبات معلقة</p>
              <h3 class="fw-black mb-0 text-warning">{{ pending_requests }}</h3>
              {% if pending_leaves > 0 %}
              <small class="text-info">{{ pending_leaves }} إجازة معلقة</small>
              {% endif %}
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#fff7ed;">
              <i class="bi bi-inbox-fill fs-4 text-warning"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="text-muted small mb-1">الميثاق</p>
              <h3 class="fw-black mb-0" style="color:#7c3aed;">{{ charter_not_accepted_count }}</h3>
              <small class="text-muted">لم يوافقوا بعد</small>
            </div>
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:52px;height:52px;background:#ede7f6;">
              <i class="bi bi-file-earmark-text-fill fs-4" style="color:#7c3aed;"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Quick Links -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <div class="d-flex flex-wrap gap-2">
        <a href="{% url 'employees:employee_list' %}" class="btn btn-sm text-white" style="background:#06B6D4;">
          <i class="bi bi-people me-1"></i>الموظفون
        </a>
        <a href="{% url 'requests_app:list' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-inbox me-1"></i>الطلبات
        </a>
        <a href="{% url 'reports:home' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-bar-chart me-1"></i>التقارير
        </a>
        <a href="{% url 'companies:charter_manage' %}" class="btn btn-sm btn-outline-secondary">
          <i class="bi bi-file-earmark-text me-1"></i>الميثاق
        </a>
      </div>
    </div>
  </div>

  <div class="row g-4">

    <!-- آخر الحضور -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">حضور اليوم</h5>
          <a href="{% url 'attendance:list' %}" class="btn btn-sm btn-outline-primary">عرض الكل</a>
        </div>
        <div class="card-body p-0">
          {% if recent_attendance %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for att in recent_attendance %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ att.employee.full_name_ar }}</div>
                  </td>
                  <td class="text-muted small">{{ att.check_in_time|time:"H:i"|default:"—" }}</td>
                  <td class="text-end pe-4">
                    <span class="badge
                      {% if att.status == 'present' %}bg-success
                      {% elif att.status == 'late' %}bg-warning text-dark
                      {% elif att.status == 'absent' %}bg-danger
                      {% else %}bg-secondary{% endif %}">
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
            <p class="mt-2 small">لا توجد سجلات حضور اليوم</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- آخر الطلبات -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">آخر الطلبات</h5>
          <a href="{% url 'requests_app:list' %}" class="btn btn-sm btn-outline-primary">عرض الكل</a>
        </div>
        <div class="card-body p-0">
          {% if recent_requests %}
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <tbody>
                {% for req in recent_requests %}
                <tr>
                  <td class="px-4 py-3">
                    <div class="fw-semibold small">{{ req.employee.full_name_ar }}</div>
                    <small class="text-muted">{{ req.request_type.name }}</small>
                  </td>
                  <td class="text-end pe-4">
                    <span class="badge bg-{{ req.status_color }}">
                      {{ req.get_status_display }}
                    </span>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-5 text-muted">
            <i class="bi bi-inbox fs-1"></i>
            <p class="mt-2 small">لا توجد طلبات</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- الميثاق -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">حالة الميثاق</h5>
          <a href="{% url 'companies:charter_manage' %}" class="btn btn-sm btn-outline-primary">إدارة</a>
        </div>
        <div class="card-body">
          <div class="row g-3 text-center mb-3">
            <div class="col-6">
              <div class="p-3 rounded" style="background:#e8f5e9;">
                <div class="fs-3 fw-black text-success">{{ charter_accepted_count }}</div>
                <small class="text-muted">وافقوا</small>
              </div>
            </div>
            <div class="col-6">
              <div class="p-3 rounded" style="background:#fde8e8;">
                <div class="fs-3 fw-black text-danger">{{ charter_not_accepted_count }}</div>
                <small class="text-muted">لم يوافقوا</small>
              </div>
            </div>
          </div>

          {% if charter_not_accepted_employees %}
          <div class="small text-muted mb-2">أمثلة للموظفين الذين لم يوافقوا:</div>
          <ul class="mb-0">
            {% for emp in charter_not_accepted_employees %}
            <li class="small mb-1">{{ emp.full_name_ar }} - {{ emp.employee_code }}</li>
            {% endfor %}
          </ul>
          {% else %}
          <div class="text-center text-success small fw-semibold">
            الجميع وافق على الميثاق 🎉
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- آخر الموظفين -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4 d-flex justify-content-between">
          <h5 class="fw-bold mb-0">آخر الموظفين</h5>
          <a href="{% url 'employees:employee_list' %}" class="btn btn-sm btn-outline-primary">عرض الكل</a>
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
                  <td class="text-muted small">{{ emp.job_title.name_ar|default:"—" }}</td>
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

  {% endif %}
</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, "templates", "dashboard", "index.html"),
    dashboard_template
)

print("\n" + "=" * 60)
print("  ✅ Patch 37 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Dashboard للموظف
     - حالة اليوم
     - رصيد الإجازات
     - الطلبات
     - الخصومات
     - روابط سريعة

  2. ✅ Dashboard للمدير
     - أعضاء الفريق
     - الحضور اليوم
     - طلبات الفريق
     - إجازات الفريق

  3. ✅ Dashboard للإدارة / HR / صاحب الشركة
     - موظفين
     - حضور اليوم
     - طلبات معلقة
     - حالة الميثاق
     - آخر الموظفين
     - آخر الطلبات

  4. ✅ HR / الإدارة يشوفوا مين وافق ومين ما وافقش على الميثاق
  5. ✅ تجهيز بيانات direct_manager للديمو

جرب الآن:
  - emp10003
  - manager1
  - hr_manager
  - demo_admin
على /dashboard/
""")