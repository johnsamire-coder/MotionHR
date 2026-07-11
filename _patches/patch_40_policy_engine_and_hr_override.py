#!/usr/bin/env python3
"""
Patch 40: Policy Engine + HR Attendance Override
================================================
1. CompanyPolicy فعليًا يطبّق على check-in/check-out
2. HR Attendance Override
3. Attendance Action Log
4. Template للتعديل اليدوي
5. أزرار في قائمة الحضور
"""

import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command


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
print("  Patch 40: Policy Engine + HR Attendance Override")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) AttendanceActionLog model
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/models.py...")

models_path = os.path.join(BASE_DIR, "attendance", "models.py")
models_content = read_file(models_path)

action_log_model = '''

class AttendanceActionLog(TenantModel):
    """سجل تعديلات الحضور والانصراف"""

    ACTION_CHOICES = [
        ("edit", "تعديل"),
        ("cancel_checkin", "إلغاء حضور"),
        ("cancel_checkout", "إلغاء انصراف"),
        ("delete", "حذف سجل"),
    ]

    attendance = models.ForeignKey(
        "Attendance",
        on_delete=models.CASCADE,
        related_name="action_logs",
        verbose_name="سجل الحضور"
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="نوع الإجراء"
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_actions",
        verbose_name="تم بواسطة"
    )
    reason = models.TextField(
        verbose_name="سبب التعديل"
    )
    old_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="البيانات قبل التعديل"
    )
    new_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="البيانات بعد التعديل"
    )
    action_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإجراء"
    )

    class Meta:
        verbose_name = "سجل تعديل حضور"
        verbose_name_plural = "سجلات تعديلات الحضور"
        ordering = ["-action_at"]

    def __str__(self):
        return f"{self.attendance} - {self.get_action_type_display()}"
'''

if "class AttendanceActionLog" not in models_content:
    models_content += action_log_model
    write_file(models_path, models_content)
    print("  ✅ تم إضافة AttendanceActionLog")
else:
    print("  ℹ️  AttendanceActionLog موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) Admin registration
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/admin.py...")

admin_path = os.path.join(BASE_DIR, "attendance", "admin.py")
admin_content = read_file(admin_path)

if "AttendanceActionLog" not in admin_content:
    admin_content += '''

from .models import AttendanceActionLog

@admin.register(AttendanceActionLog)
class AttendanceActionLogAdmin(admin.ModelAdmin):
    list_display = ["attendance", "action_type", "performed_by", "action_at"]
    list_filter = ["action_type", "action_at"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل AttendanceActionLog في Admin")
else:
    print("  ℹ️  AttendanceActionLog مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 3) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

call_command("makemigrations", "attendance")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 4) attendance/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

policy_helpers = '''

# ════════════════════════════════════════════════════════════
# Policy Helpers
# ════════════════════════════════════════════════════════════
def _get_company_policy(company):
    try:
        from companies.models import CompanyPolicy
        return CompanyPolicy.get_for_company(company)
    except Exception:
        return None


def _get_checkin_radius(branch, policy):
    """النطاق الفعلي = branch radius أو default policy + tolerance"""
    radius = 100
    tolerance = 0

    if policy:
        try:
            radius = int(policy.default_checkin_radius or 100)
        except Exception:
            radius = 100
        try:
            tolerance = int(policy.distance_tolerance_meters or 0)
        except Exception:
            tolerance = 0

    if branch and getattr(branch, "check_in_radius", None):
        try:
            radius = int(branch.check_in_radius or radius)
        except Exception:
            pass

    return radius + tolerance


def _get_grace_period_minutes(employee, policy):
    """سماحية التأخير من سياسة الشركة، ولو مش موجودة من الشيفت"""
    if policy and getattr(policy, "grace_period_minutes", None) is not None:
        try:
            return int(policy.grace_period_minutes or 0)
        except Exception:
            pass

    try:
        from attendance.models import EmployeeShift
        emp_shift = EmployeeShift.objects.filter(
            employee=employee, is_active=True
        ).select_related("shift").first()
        if emp_shift and emp_shift.shift:
            return int(getattr(emp_shift.shift, "grace_period", 0) or 0)
    except Exception:
        pass

    return 0


def _can_hr_manage_attendance(user, company):
    """هل المستخدم له صلاحية تعديل/إلغاء الحضور؟"""
    role = getattr(user, "role", "")
    if role == "super_admin":
        return True

    if role not in ["hr_manager", "company_admin"]:
        return False

    policy = _get_company_policy(company)
    if not policy:
        return role in ["hr_manager", "company_admin"]

    return bool(
        getattr(policy, "hr_can_edit_attendance", False) or
        getattr(policy, "hr_can_cancel_attendance", False)
    )


def _attendance_snapshot(attendance):
    """لقطة من السجل قبل/بعد التعديل"""
    data = {}
    for field_name in [
        "status",
        "check_in_time",
        "check_out_time",
        "late_minutes",
        "work_hours",
        "check_in_address",
        "check_out_address",
    ]:
        if hasattr(attendance, field_name):
            val = getattr(attendance, field_name)
            data[field_name] = str(val) if val is not None else None
    return data
'''

if "_can_hr_manage_attendance" not in views:
    views += policy_helpers
    write_file(views_path, views)
    print("  ✅ تم إضافة Policy Helpers")
else:
    print("  ℹ️  Policy Helpers موجودة")


# ── API جديدة تعتمد على CompanyPolicy ─────────────────────
policy_api_code = '''

# ════════════════════════════════════════════════════════════
# Policy-based Check-in API
# ════════════════════════════════════════════════════════════
@login_required
def policy_api_check_in(request):
    import json
    from datetime import date as dt_date, datetime as dt_datetime
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    lat = body.get("latitude")
    lng = body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"success": False, "message": "لم يتم تحديد الموقع"})

    lat = float(lat)
    lng = float(lng)

    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    existing = Attendance.objects.filter(employee=employee, date=today).first()
    if existing:
        return JsonResponse({"success": False, "message": "تم تسجيل حضورك بالفعل اليوم"})

    policy = _get_company_policy(employee.company)
    branch = employee.branch

    within_range = True
    distance = 0
    radius = _get_checkin_radius(branch, policy)

    # هل الحضور لازم داخل النطاق؟
    requires_range = True
    if policy and hasattr(policy, "checkin_requires_branch_range"):
        requires_range = bool(policy.checkin_requires_branch_range)

    if branch and branch.latitude and branch.longitude:
        distance = round(calculate_distance(lat, lng, float(branch.latitude), float(branch.longitude)))
        if requires_range and distance > radius:
            return JsonResponse({
                "success": False,
                "message": f"أنت خارج نطاق الفرع. المسافة: {distance} متر (المسموح: {radius} متر)"
            })
        within_range = distance <= radius
    else:
        within_range = True

    now = dt_datetime.now()

    att_kwargs = {
        "company": employee.company,
        "employee": employee,
        "date": today,
        "status": "present",
    }

    att_fields = {f.name for f in Attendance._meta.fields}

    if "check_in_time" in att_fields:
        att_kwargs["check_in_time"] = now.time()
    if "check_in_latitude" in att_fields:
        att_kwargs["check_in_latitude"] = Decimal(str(lat))
    if "check_in_longitude" in att_fields:
        att_kwargs["check_in_longitude"] = Decimal(str(lng))
    if "check_in_address" in att_fields:
        att_kwargs["check_in_address"] = address
    if "within_range" in att_fields:
        att_kwargs["within_range"] = within_range
    if "check_in_within_range" in att_fields:
        att_kwargs["check_in_within_range"] = within_range

    # الشيفت
    if "shift" in att_fields:
        try:
            from attendance.models import EmployeeShift
            emp_shift = EmployeeShift.objects.filter(
                employee=employee, is_active=True
            ).select_related("shift").first()
            if emp_shift:
                att_kwargs["shift"] = emp_shift.shift
        except Exception:
            pass

    # التأخير باستخدام policy grace_period
    if "late_minutes" in att_fields:
        late_mins = 0
        try:
            from attendance.models import EmployeeShift
            emp_shift = EmployeeShift.objects.filter(
                employee=employee, is_active=True
            ).select_related("shift").first()

            if emp_shift and emp_shift.shift:
                shift = emp_shift.shift
                grace = _get_grace_period_minutes(employee, policy)
                shift_start = dt_datetime.combine(today, shift.start_time)
                allowed_time = shift_start + __import__("datetime").timedelta(minutes=grace)

                if now > allowed_time:
                    late_mins = int((now - shift_start).total_seconds() / 60)
                    att_kwargs["status"] = "late"
        except Exception:
            pass

        att_kwargs["late_minutes"] = late_mins

    try:
        Attendance.objects.create(**att_kwargs)
        msg = "تم تسجيل حضورك بنجاح"
        if branch and branch.latitude and branch.longitude:
            msg += f" - المسافة من الفرع: {distance} متر"
        return JsonResponse({"success": True, "status": "success", "message": msg})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})


# ════════════════════════════════════════════════════════════
# Policy-based Check-out API
# ════════════════════════════════════════════════════════════
@login_required
def policy_api_check_out(request):
    import json
    from datetime import date as dt_date, datetime as dt_datetime
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    lat = body.get("latitude")
    lng = body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"success": False, "message": "لم يتم تحديد الموقع"})

    lat = float(lat)
    lng = float(lng)

    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    attendance = Attendance.objects.filter(employee=employee, date=today).first()

    if not attendance:
        return JsonResponse({"success": False, "message": "لم تسجل حضور اليوم بعد"})

    att_fields = {f.name for f in Attendance._meta.fields}
    if "check_out_time" in att_fields and getattr(attendance, "check_out_time", None):
        return JsonResponse({"success": False, "message": "تم تسجيل انصرافك بالفعل"})

    policy = _get_company_policy(employee.company)
    allow_anywhere = True
    if policy and hasattr(policy, "checkout_from_anywhere"):
        allow_anywhere = bool(policy.checkout_from_anywhere)

    # لو مش مسموح من أي مكان → نتحقق من النطاق
    if not allow_anywhere:
        branch = employee.branch
        if branch and branch.latitude and branch.longitude:
            distance = round(calculate_distance(lat, lng, float(branch.latitude), float(branch.longitude)))
            radius = _get_checkin_radius(branch, policy)
            if distance > radius:
                return JsonResponse({
                    "success": False,
                    "message": f"الانصراف خارج النطاق غير مسموح. المسافة: {distance} متر"
                })

    now = dt_datetime.now()

    if "check_out_time" in att_fields:
        attendance.check_out_time = now.time()
    if "check_out_latitude" in att_fields:
        attendance.check_out_latitude = Decimal(str(lat))
    if "check_out_longitude" in att_fields:
        attendance.check_out_longitude = Decimal(str(lng))
    if "check_out_address" in att_fields:
        attendance.check_out_address = address

    # حساب ساعات العمل
    if "work_hours" in att_fields and hasattr(attendance, "check_in_time") and attendance.check_in_time:
        try:
            check_in_dt = dt_datetime.combine(today, attendance.check_in_time)
            diff = now - check_in_dt
            hours = round(diff.total_seconds() / 3600, 1)
            attendance.work_hours = Decimal(str(hours))
        except Exception:
            pass

    try:
        attendance.save()
        return JsonResponse({
            "success": True,
            "status": "success",
            "message": "تم تسجيل انصرافك بنجاح"
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})


# ════════════════════════════════════════════════════════════
# HR Attendance Override
# ════════════════════════════════════════════════════════════
@login_required
def attendance_override(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    from attendance.models import Attendance, AttendanceActionLog

    attendance = get_object_or_404(
        Attendance.all_objects if hasattr(Attendance, "all_objects") else Attendance.objects,
        pk=pk
    )

    if not _can_hr_manage_attendance(request.user, attendance.company):
        messages.error(request, "ليس لديك صلاحية تعديل/إلغاء الحضور")
        return redirect("attendance:list")

    policy = _get_company_policy(attendance.company)

    if request.method == "POST":
        action = request.POST.get("action")
        reason = request.POST.get("reason", "").strip()

        require_reason = True
        if policy and hasattr(policy, "attendance_edit_reason_required"):
            require_reason = bool(policy.attendance_edit_reason_required)

        if require_reason and not reason:
            messages.error(request, "سبب التعديل / الإلغاء إجباري")
            return redirect("attendance:override", pk=attendance.pk)

        old_data = _attendance_snapshot(attendance)

        if action == "edit":
            if hasattr(attendance, "check_in_time") and request.POST.get("check_in_time"):
                attendance.check_in_time = request.POST.get("check_in_time")
            if hasattr(attendance, "check_out_time") and request.POST.get("check_out_time"):
                attendance.check_out_time = request.POST.get("check_out_time")
            if hasattr(attendance, "status") and request.POST.get("status"):
                attendance.status = request.POST.get("status")
            if hasattr(attendance, "admin_notes"):
                attendance.admin_notes = reason
            if hasattr(attendance, "is_manually_edited"):
                attendance.is_manually_edited = True
            attendance.save()

            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="edit",
                performed_by=request.user,
                reason=reason or "تعديل يدوي",
                old_data=old_data,
                new_data=_attendance_snapshot(attendance),
            )
            messages.success(request, "تم تعديل سجل الحضور بنجاح")

        elif action == "cancel_checkin":
            if hasattr(attendance, "check_in_time"):
                attendance.check_in_time = None
            if hasattr(attendance, "check_in_latitude"):
                attendance.check_in_latitude = None
            if hasattr(attendance, "check_in_longitude"):
                attendance.check_in_longitude = None
            if hasattr(attendance, "check_in_address"):
                attendance.check_in_address = ""
            if hasattr(attendance, "admin_notes"):
                attendance.admin_notes = reason
            if hasattr(attendance, "is_manually_edited"):
                attendance.is_manually_edited = True
            attendance.save()

            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="cancel_checkin",
                performed_by=request.user,
                reason=reason or "إلغاء حضور",
                old_data=old_data,
                new_data=_attendance_snapshot(attendance),
            )
            messages.success(request, "تم إلغاء تسجيل الحضور")

        elif action == "cancel_checkout":
            if hasattr(attendance, "check_out_time"):
                attendance.check_out_time = None
            if hasattr(attendance, "check_out_latitude"):
                attendance.check_out_latitude = None
            if hasattr(attendance, "check_out_longitude"):
                attendance.check_out_longitude = None
            if hasattr(attendance, "check_out_address"):
                attendance.check_out_address = ""
            if hasattr(attendance, "admin_notes"):
                attendance.admin_notes = reason
            if hasattr(attendance, "is_manually_edited"):
                attendance.is_manually_edited = True
            attendance.save()

            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="cancel_checkout",
                performed_by=request.user,
                reason=reason or "إلغاء انصراف",
                old_data=old_data,
                new_data=_attendance_snapshot(attendance),
            )
            messages.success(request, "تم إلغاء تسجيل الانصراف")

        elif action == "delete":
            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="delete",
                performed_by=request.user,
                reason=reason or "حذف السجل",
                old_data=old_data,
                new_data={},
            )
            attendance.delete()
            messages.success(request, "تم حذف سجل الحضور")
            return redirect("attendance:list")

        return redirect("attendance:override", pk=pk)

    context = {
        "attendance_obj": attendance,
        "page_title": "تعديل / إلغاء الحضور",
    }
    return render(request, "attendance/override_form.html", context)
'''

if "def policy_api_check_in" not in views:
    views += policy_api_code
    write_file(views_path, views)
    print("  ✅ تم إضافة Policy APIs + Override view")
else:
    print("  ℹ️  Policy APIs موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 5) update attendance/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls_content = read_file(urls_path)

# استبدال الـ APIs
urls_content = urls_content.replace(
    "path('api/check-in/', views.smart_api_check_in, name='api_check_in'),",
    "path('api/check-in/', views.policy_api_check_in, name='api_check_in'),"
)
urls_content = urls_content.replace(
    "path('api/check-out/', views.smart_api_check_out, name='api_check_out'),",
    "path('api/check-out/', views.policy_api_check_out, name='api_check_out'),"
)

if "name='override'" not in urls_content:
    if "path('monitor/'" in urls_content:
        urls_content = urls_content.replace(
            "path('monitor/', views.monitor, name='monitor'),",
            "path('monitor/', views.monitor, name='monitor'),\n    path('<int:pk>/override/', views.attendance_override, name='override'),"
        )
    else:
        urls_content = urls_content.rstrip()
        if urls_content.endswith("]"):
            urls_content = urls_content[:-1] + "\n    path('<int:pk>/override/', views.attendance_override, name='override'),\n]\n"

write_file(urls_path, urls_content)
print("  ✅ تم تحديث URLs")


# ════════════════════════════════════════════════════════════
# 6) override_form template
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء attendance/override_form.html...")

override_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تعديل / إلغاء الحضور{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="row justify-content-center">
    <div class="col-lg-8">

      <div class="d-flex align-items-center mb-4">
        <a href="{% url 'attendance:list' %}" class="btn btn-outline-secondary btn-sm me-3">
          <i class="bi bi-arrow-right"></i>
        </a>
        <h4 class="fw-bold mb-0">تعديل / إلغاء الحضور</h4>
      </div>

      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="text-muted small">الموظف</label>
              <div class="fw-bold">{{ attendance_obj.employee.full_name_ar }}</div>
              <small class="text-muted">{{ attendance_obj.employee.employee_code }}</small>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">التاريخ</label>
              <div class="fw-bold">{{ attendance_obj.date|date:"d/m/Y" }}</div>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">الحضور الحالي</label>
              <div class="fw-bold">{{ attendance_obj.check_in_time|default:"—" }}</div>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">الانصراف الحالي</label>
              <div class="fw-bold">{{ attendance_obj.check_out_time|default:"—" }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- تعديل -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">تعديل السجل</h5>
        </div>
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <input type="hidden" name="action" value="edit">

            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label small">وقت الحضور</label>
                <input type="time" name="check_in_time" class="form-control"
                       value="{{ attendance_obj.check_in_time|time:'H:i'|default:'' }}">
              </div>
              <div class="col-md-4">
                <label class="form-label small">وقت الانصراف</label>
                <input type="time" name="check_out_time" class="form-control"
                       value="{{ attendance_obj.check_out_time|time:'H:i'|default:'' }}">
              </div>
              <div class="col-md-4">
                <label class="form-label small">الحالة</label>
                <select name="status" class="form-select">
                  <option value="present" {% if attendance_obj.status == 'present' %}selected{% endif %}>حاضر</option>
                  <option value="late" {% if attendance_obj.status == 'late' %}selected{% endif %}>متأخر</option>
                  <option value="absent" {% if attendance_obj.status == 'absent' %}selected{% endif %}>غائب</option>
                  <option value="on_leave" {% if attendance_obj.status == 'on_leave' %}selected{% endif %}>إجازة</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label small">سبب التعديل <span class="text-danger">*</span></label>
                <textarea name="reason" class="form-control" rows="2" required
                          placeholder="اكتب سبب التعديل..."></textarea>
              </div>
            </div>

            <div class="mt-3">
              <button type="submit" class="btn text-white" style="background:#06B6D4;">
                <i class="bi bi-check-lg me-1"></i>حفظ التعديل
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- إجراءات سريعة -->
      <div class="row g-3">
        <div class="col-md-4">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-body p-4">
              <h6 class="fw-bold text-warning">إلغاء الحضور</h6>
              <form method="post">
                {% csrf_token %}
                <input type="hidden" name="action" value="cancel_checkin">
                <textarea name="reason" class="form-control form-control-sm mb-3" rows="2" required
                          placeholder="سبب إلغاء الحضور..."></textarea>
                <button type="submit" class="btn btn-outline-warning w-100"
                        onclick="return confirm('إلغاء تسجيل الحضور؟')">
                  إلغاء الحضور
                </button>
              </form>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-body p-4">
              <h6 class="fw-bold text-danger">إلغاء الانصراف</h6>
              <form method="post">
                {% csrf_token %}
                <input type="hidden" name="action" value="cancel_checkout">
                <textarea name="reason" class="form-control form-control-sm mb-3" rows="2" required
                          placeholder="سبب إلغاء الانصراف..."></textarea>
                <button type="submit" class="btn btn-outline-danger w-100"
                        onclick="return confirm('إلغاء تسجيل الانصراف؟')">
                  إلغاء الانصراف
                </button>
              </form>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-body p-4">
              <h6 class="fw-bold text-dark">حذف السجل</h6>
              <form method="post">
                {% csrf_token %}
                <input type="hidden" name="action" value="delete">
                <textarea name="reason" class="form-control form-control-sm mb-3" rows="2" required
                          placeholder="سبب حذف السجل..."></textarea>
                <button type="submit" class="btn btn-outline-dark w-100"
                        onclick="return confirm('حذف سجل الحضور نهائيًا؟')">
                  حذف السجل
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>
{% endblock %}
"""
create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "override_form.html"),
    override_template
)

# ════════════════════════════════════════════════════════════
# 7) update attendance/list.html add override button
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث templates/attendance/list.html...")

list_path = os.path.join(BASE_DIR, "templates", "attendance", "list.html")
if os.path.exists(list_path):
    list_html = read_file(list_path)

    if "attendance:override" not in list_html:
        # نضيف زر override جوه أي عمود إجراءات موجود
        if "</td>" in list_html and "btn btn-sm btn-outline" in list_html:
            list_html = list_html.replace(
                "</td>",
                """{% if request.user.role in 'super_admin,company_admin,hr_manager' %}
                    <a href="{% url 'attendance:override' record.pk %}"
                       class="btn btn-sm btn-outline-warning ms-1">
                      <i class="bi bi-pencil-square"></i>
                    </a>
                    {% endif %}
                  </td>""",
                1
            )
            write_file(list_path, list_html)
            print("  ✅ تم إضافة زر التعديل/الإلغاء")
        else:
            print("  ℹ️  attendance/list.html شكله مختلف")
    else:
        print("  ℹ️  زر override موجود بالفعل")
else:
    print("  ℹ️  attendance/list.html غير موجود - تخطيناه")


print("\n" + "=" * 60)
print("  ✅ Patch 40 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ AttendanceActionLog model
  2. ✅ Policy-based Check-in API
     - check-in بالنطاق + السماحية
  3. ✅ Policy-based Check-out API
     - check-out من أي مكان حسب السياسة
  4. ✅ HR Attendance Override view
  5. ✅ Override Form
  6. ✅ Attendance Action Log في Admin
  7. ✅ زر تعديل/إلغاء في قائمة الحضور (لو القالب يدعمه)

جرب:
  - demo_admin / hr_manager
  - /companies/policies/
  - /attendance/
  - تعديل / إلغاء حضور موظف
""")