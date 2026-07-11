#!/usr/bin/env python3
"""
Patch 41b: Late Engine Logic
============================
1) توليد LateIncident عند التأخير
2) توليد LateNotification
3) اقتراح الإجراء حسب CompanyPolicy
4) ربطه بـ check-in
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 41b: Late Engine Logic")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) attendance/views.py — إضافة helper logic
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

late_engine_helpers = '''

# ════════════════════════════════════════════════════════════
# Late Engine Helpers
# ════════════════════════════════════════════════════════════
def _get_late_stage(policy, incident_count):
    """
    تحديد المرحلة الحالية حسب عدد مرات التأخير
    """
    if not policy:
        return None, None

    if incident_count >= getattr(policy, "late_full_day_deduction_after_count", 999):
        return "full_day_deduction", "خصم يوم كامل"
    elif incident_count >= getattr(policy, "late_half_day_deduction_after_count", 999):
        return "half_day_deduction", "خصم نصف يوم"
    elif incident_count >= getattr(policy, "late_quarter_day_deduction_after_count", 999):
        return "quarter_day_deduction", "خصم ربع يوم"
    elif incident_count >= getattr(policy, "late_second_warning_after_count", 999):
        return "written_warning", "إنذار كتابي"
    elif incident_count >= getattr(policy, "late_first_warning_after_count", 999):
        return "verbal_warning", "إنذار شفهي"

    return None, None


def _build_late_details(employee, month, year):
    """
    بناء تفاصيل كل مرات التأخير في الشهر
    """
    try:
        from attendance.models import LateIncident
        incidents = LateIncident.objects.filter(
            company=employee.company,
            employee=employee,
            month=month,
            year=year
        ).order_by("date")

        lines = []
        for inc in incidents:
            lines.append(
                f"• {inc.date.strftime('%d/%m/%Y')} — "
                f"{inc.actual_checkin_time.strftime('%H:%M') if inc.actual_checkin_time else '—'} — "
                f"{inc.late_minutes} دقيقة"
            )
        return "\\n".join(lines)
    except Exception:
        return ""


def _create_late_notification(employee, incident, policy):
    """
    إنشاء إشعار HR عن التأخير
    """
    try:
        from attendance.models import LateNotification

        stage_key, stage_label = _get_late_stage(policy, incident.incident_number_in_month)

        # عادي
        if not stage_key:
            title = "تنبيه تأخير"
            message = (
                f"الموظف {employee.full_name_ar} تأخر اليوم "
                f"{incident.late_minutes} دقيقة"
            )
            details = (
                f"التاريخ: {incident.date.strftime('%d/%m/%Y')}\\n"
                f"وقت الحضور: {incident.actual_checkin_time.strftime('%H:%M') if incident.actual_checkin_time else '—'}\\n"
                f"عدد مرات التأخير هذا الشهر: {incident.incident_number_in_month}"
            )
            suggested_action = ""
            notif_type = "single_late"
        else:
            # وصل للحد
            title = "تكرار تأخير - يتطلب إجراء"
            details_text = _build_late_details(employee, incident.month, incident.year)
            message = (
                f"الموظف {employee.full_name_ar} تأخر "
                f"{incident.incident_number_in_month} مرات هذا الشهر."
            )
            details = (
                f"عدد مرات التأخير هذا الشهر: {incident.incident_number_in_month}\\n\\n"
                f"{details_text}"
            )
            suggested_action = stage_label
            notif_type = "threshold_reached"

        LateNotification.objects.create(
            company=employee.company,
            employee=employee,
            notification_type=notif_type,
            title=title,
            message=message,
            details=details,
            suggested_action=suggested_action or "",
            incident_count=incident.incident_number_in_month,
            month=incident.month,
            year=incident.year,
        )

        return True
    except Exception:
        return False


def _record_late_incident(employee, attendance_obj, late_minutes):
    """
    تسجيل حادثة التأخير وإنشاء الإشعار
    """
    try:
        from attendance.models import LateIncident
        from django.utils import timezone
        today = timezone.now().date()
        policy = _get_company_policy(employee.company)

        # لو العداد بيتصفر شهريًا
        month = today.month
        year = today.year

        count = LateIncident.objects.filter(
            company=employee.company,
            employee=employee,
            month=month,
            year=year
        ).count() + 1

        incident = LateIncident.objects.create(
            company=employee.company,
            employee=employee,
            attendance=attendance_obj,
            date=today,
            late_minutes=int(late_minutes or 0),
            shift_start_time=getattr(getattr(attendance_obj, "shift", None), "start_time", None),
            actual_checkin_time=getattr(attendance_obj, "check_in_time", None),
            grace_period_used=_get_grace_period_minutes(employee, policy),
            month=month,
            year=year,
            incident_number_in_month=count,
            is_excused=False,
            excuse_reason="",
        )

        _create_late_notification(employee, incident, policy)
        return incident
    except Exception:
        return None
'''

if "_record_late_incident" not in views:
    views += late_engine_helpers
    write_file(views_path, views)
    print("  ✅ تم إضافة Late Engine Helpers")
else:
    print("  ℹ️  Late Engine Helpers موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) ربط Late Engine بـ policy_api_check_in
# ════════════════════════════════════════════════════════════
print("\n🔧 ربط Late Engine بـ policy_api_check_in...")

views = read_file(views_path)

old_snippet = """    try:
        Attendance.objects.create(**att_kwargs)
        msg = "تم تسجيل حضورك بنجاح"
        if branch and branch.latitude and branch.longitude:
            msg += f" - المسافة من الفرع: {distance} متر"
        return JsonResponse({"success": True, "status": "success", "message": msg})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})"""

new_snippet = """    try:
        attendance_obj = Attendance.objects.create(**att_kwargs)

        # لو Late → سجل حادثة تأخير + إشعار
        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:
            _record_late_incident(
                employee=employee,
                attendance_obj=attendance_obj,
                late_minutes=att_kwargs.get("late_minutes", 0)
            )

        msg = "تم تسجيل حضورك بنجاح"
        if branch and branch.latitude and branch.longitude:
            msg += f" - المسافة من الفرع: {distance} متر"

        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:
            msg += f" - تم تسجيل {att_kwargs.get('late_minutes', 0)} دقيقة تأخير"

        return JsonResponse({"success": True, "status": "success", "message": msg})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})"""

if old_snippet in views:
    views = views.replace(old_snippet, new_snippet)
    write_file(views_path, views)
    print("  ✅ تم ربط Late Engine بـ check-in")
else:
    print("  ℹ️  لم أجد الـ snippet المتوقع - قد يكون اتغير شكلها")


# ════════════════════════════════════════════════════════════
# 3) تحديث policies.html لإظهار mode الجديد
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/policies.html...")

policies_path = os.path.join(BASE_DIR, "templates", "companies", "policies.html")
policies = read_file(policies_path)

if "late_handling_mode" not in policies:
    insert_block = """
            <div class="mb-3">
              <label class="form-label fw-semibold small">طريقة التعامل مع التأخير</label>
              <select name="late_handling_mode" class="form-select">
                <option value="monitor_only" {% if policy.late_handling_mode == 'monitor_only' %}selected{% endif %}>
                  مراقبة فقط
                </option>
                <option value="recommendation_only" {% if policy.late_handling_mode == 'recommendation_only' %}selected{% endif %}>
                  توصية + قرار HR
                </option>
                <option value="auto_warn_manual_deduct" {% if policy.late_handling_mode == 'auto_warn_manual_deduct' %}selected{% endif %}>
                  إنذارات تلقائية + خصومات بموافقة
                </option>
                <option value="fully_automatic" {% if policy.late_handling_mode == 'fully_automatic' %}selected{% endif %}>
                  تلقائي كامل
                </option>
              </select>
              <small class="text-muted">
                الشركة تحدد هل النظام يراقب فقط، أو يقترح، أو ينفذ تلقائيًا
              </small>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="employee_can_view_late_count" id="viewLateCount"
                     {% if policy.employee_can_view_late_count %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="viewLateCount">
                الموظف يشوف عدد مرات تأخيره
              </label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="employee_can_view_warnings" id="viewWarnings"
                     {% if policy.employee_can_view_warnings %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="viewWarnings">
                الموظف يشوف إنذاراته
              </label>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="hr_override_reason_required" id="hrReason"
                     {% if policy.hr_override_reason_required %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="hrReason">
                سبب إجباري لو HR تجاهل الإجراء المقترح
              </label>
            </div>
"""

    # نحطها بعد سماحية التأخير مباشرة
    target = """            <div class="mb-3">
              <label class="form-label fw-semibold small">سماحية التأخير (دقيقة)</label>"""
    if target in policies:
        idx = policies.find(target)
        # نضيف البلوك بعد select السماحية
        # نبحث عن أول </div> بعد select block
        first_close = policies.find("</div>", idx)
        second_close = policies.find("</div>", first_close + 1)
        if second_close != -1:
            policies = policies[:second_close + 6] + insert_block + policies[second_close + 6:]
            write_file(policies_path, policies)
            print("  ✅ تم إضافة late_handling_mode في صفحة السياسات")
    else:
        print("  ℹ️  مكان الإدراج مختلف")
else:
    print("  ℹ️  late_handling_mode موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 4) تحديث companies/views.py لحفظ الحقول الجديدة
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/views.py...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

if "late_handling_mode" not in comp_views:
    old_part = """        # التأخير
        policy.grace_period_minutes = int(request.POST.get("grace_period_minutes", 15) or 15)
        policy.reset_late_counter_monthly = "reset_late_counter_monthly" in request.POST"""
    new_part = """        # التأخير
        policy.grace_period_minutes = int(request.POST.get("grace_period_minutes", 15) or 15)
        policy.late_handling_mode = request.POST.get("late_handling_mode", "recommendation_only")
        policy.employee_can_view_late_count = "employee_can_view_late_count" in request.POST
        policy.employee_can_view_warnings = "employee_can_view_warnings" in request.POST
        policy.hr_override_reason_required = "hr_override_reason_required" in request.POST
        policy.reset_late_counter_monthly = "reset_late_counter_monthly" in request.POST"""
    if old_part in comp_views:
        comp_views = comp_views.replace(old_part, new_part)
        write_file(comp_views_path, comp_views)
        print("  ✅ تم ربط حفظ الحقول الجديدة")
    else:
        print("  ℹ️  النص مختلف - محتاج مراجعة")
else:
    print("  ℹ️  الحقول مربوطة بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 41b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Late Engine Helpers
  2. ✅ _record_late_incident
  3. ✅ _create_late_notification
  4. ✅ ربط التأخير بـ check-in
  5. ✅ late_handling_mode في صفحة السياسات
  6. ✅ employee visibility settings
  7. ✅ حفظ الإعدادات الجديدة

معنى ده:
  - كل مرة الموظف يتأخر → LateIncident
  - كل مرة يتبعت إشعار لـ HR
  - لو وصل حد معين → إشعار مفصل مع suggested_action

الجاي:
  Patch 41c → صفحة HR لاتخاذ الإجراء
""")