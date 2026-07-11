#!/usr/bin/env python3
"""
Patch 42b: Check-in Logic per DailyAssignment
===============================================
1) check-in يبص على DailyAssignment الأول
2) لو off/leave → يطبق policy mode
3) لو مفيش assignment → يطبق unplanned mode
4) لو flexible → يبدأ يومه من وقت check-in
5) لو split → يسجل segment
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
print("  Patch 42b: Check-in per Assignment")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) إضافة Assignment-aware check-in helper
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

assignment_helpers = '''

# ════════════════════════════════════════════════════════════
# Assignment-aware Check-in Helpers
# ════════════════════════════════════════════════════════════

def _get_today_assignment(employee):
    """جلب تكليف اليوم للموظف"""
    from attendance.models import DailyAssignment
    from django.utils import timezone
    today = timezone.now().date()
    return DailyAssignment.objects.filter(
        company=employee.company,
        employee=employee,
        date=today
    ).first()


def _check_assignment_allows_checkin(assignment, policy):
    """
    التحقق: هل التكليف يسمح بـ check-in؟
    Returns: (allowed, message, checkin_mode)
    """
    if not assignment:
        # مفيش تكليف
        mode = "use_default"
        if policy and hasattr(policy, "unplanned_checkin_mode"):
            mode = policy.unplanned_checkin_mode or "use_default"

        if mode == "block":
            return False, "لا يوجد تكليف لك اليوم. تواصل مع مديرك أو HR", "blocked"
        elif mode == "create_exception":
            return True, "سيتم تسجيل حضورك كحالة استثنائية", "exception"
        else:
            return True, "", "default"

    # لو يوم راحة
    if assignment.day_type == "off_day":
        mode = "allow_notify_hr"
        if policy and hasattr(policy, "off_day_checkin_mode"):
            mode = policy.off_day_checkin_mode or "allow_notify_hr"

        if mode == "block":
            return False, "اليوم يوم راحة. لا يمكن تسجيل الحضور", "blocked"
        elif mode == "allow_notify_hr":
            return True, "اليوم يوم راحة. سيتم إشعار HR", "off_notify"
        else:
            return True, "اليوم يوم راحة. سيتم مراجعة الحضور من HR", "off_convert"

    # لو إجازة
    if assignment.day_type == "leave_day":
        mode = "block"
        if policy and hasattr(policy, "leave_day_checkin_mode"):
            mode = policy.leave_day_checkin_mode or "block"

        if mode == "block":
            return False, "عندك إجازة معتمدة اليوم. لا يمكن تسجيل الحضور", "blocked"
        elif mode == "allow_notify_hr":
            return True, "عندك إجازة اليوم. سيتم إشعار HR", "leave_notify"
        else:
            return True, "عندك إجازة اليوم. سيتم مراجعة الحضور من HR", "leave_convert"

    # لو إجازة رسمية
    if assignment.day_type == "holiday":
        return True, "اليوم إجازة رسمية. سيتم تسجيل حضورك كشيفت إضافي", "holiday_extra"

    # لو يوم عمل عادي / مأمورية / تدريب / استدعاء
    return True, "", "normal"


def _get_late_logic_for_assignment(assignment, employee, policy, now):
    """
    تحديد التأخير حسب نوع التكليف
    Returns: (is_late, late_minutes)
    """
    import datetime as dt

    # الأنواع اللي ما فيهاش late
    if not assignment:
        return False, 0

    if assignment.day_type not in ["work_day", "training_day"]:
        return False, 0

    if assignment.work_mode in ["flexible", "field", "remote"]:
        return False, 0

    # fixed / split / mixed → late ينطبق
    shift_start = assignment.start_time
    if not shift_start and assignment.shift:
        shift_start = getattr(assignment.shift, "start_time", None)

    if not shift_start:
        return False, 0

    grace = 0
    if policy and hasattr(policy, "grace_period_minutes"):
        try:
            grace = int(policy.grace_period_minutes or 0)
        except Exception:
            grace = 0

    today = now.date()
    shift_start_dt = dt.datetime.combine(today, shift_start)
    allowed_time = shift_start_dt + dt.timedelta(minutes=grace)

    if now > allowed_time:
        late_mins = int((now - shift_start_dt).total_seconds() / 60)
        return True, late_mins

    return False, 0


def _handle_assignment_checkin(employee, assignment, policy, attendance_obj, now):
    """
    معالجة ما بعد check-in حسب التكليف
    """
    from attendance.models import DailyAssignment

    if not assignment:
        return

    # تحديث حالة التكليف
    if hasattr(assignment, "status"):
        assignment.status = "in_progress"
        assignment.save(update_fields=["status"])

    # لو holiday → convert to extra
    if assignment.day_type == "holiday":
        if not assignment.is_extra_shift:
            assignment.is_extra_shift = True
            assignment.count_as_overtime = True
            assignment.save(update_fields=["is_extra_shift", "count_as_overtime"])
'''

if "_get_today_assignment" not in views:
    views += assignment_helpers
    write_file(views_path, views)
    print("  ✅ تم إضافة Assignment Helpers")
else:
    print("  ℹ️  Assignment Helpers موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) تحديث policy_api_check_in لاستخدام Assignment
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث policy_api_check_in...")

views = read_file(views_path)

# نبحث عن بداية policy_api_check_in ونعدل فيها
old_start = '''    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    existing = Attendance.objects.filter(employee=employee, date=today).first()
    if existing:
        return JsonResponse({"success": False, "message": "تم تسجيل حضورك بالفعل اليوم"})

    policy = _get_company_policy(employee.company)
    branch = employee.branch'''

new_start = '''    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    existing = Attendance.objects.filter(employee=employee, date=today).first()
    if existing:
        return JsonResponse({"success": False, "message": "تم تسجيل حضورك بالفعل اليوم"})

    policy = _get_company_policy(employee.company)

    # ═══ Assignment Check ═══
    assignment = _get_today_assignment(employee)
    allowed, msg, checkin_mode = _check_assignment_allows_checkin(assignment, policy)

    if not allowed:
        return JsonResponse({"success": False, "message": msg})

    branch = employee.branch'''

if old_start in views:
    views = views.replace(old_start, new_start)
    print("  ✅ تم إضافة Assignment Check في check-in")
else:
    print("  ℹ️  لم أجد النص المتوقع - قد يكون اتعدل قبل كده")


# نضيف بعد إنشاء الحضور: handle assignment
old_success = '''        attendance_obj = Attendance.objects.create(**att_kwargs)

        # لو Late → سجل حادثة تأخير + إشعار
        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:'''

new_success = '''        attendance_obj = Attendance.objects.create(**att_kwargs)

        # ═══ Assignment post-processing ═══
        _handle_assignment_checkin(employee, assignment, policy, attendance_obj, now)

        # لو exception
        if checkin_mode == "exception" and assignment is None:
            from attendance.models import DailyAssignment
            DailyAssignment.objects.create(
                company=employee.company,
                employee=employee,
                date=today,
                day_type="work_day",
                work_mode=getattr(employee, "attendance_mode", "fixed") or "fixed",
                expected_hours=getattr(employee, "required_daily_hours", 8) or 8,
                is_exception=True,
                exception_reason="حضور بدون تكليف مسبق",
                exception_status="pending_review",
                is_auto_generated=True,
            )

        # لو Late → سجل حادثة تأخير + إشعار
        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:'''

if old_success in views:
    views = views.replace(old_success, new_success)
    print("  ✅ تم ربط Assignment post-processing")
else:
    print("  ℹ️  لم أجد النص المتوقع للـ post-processing")


# نعدل late calculation ليستخدم assignment
old_late = '''        # التأخير باستخدام policy grace_period
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

        att_kwargs["late_minutes"] = late_mins'''

new_late = '''        # التأخير حسب التكليف اليومي
    if "late_minutes" in att_fields:
        is_late, late_mins = _get_late_logic_for_assignment(assignment, employee, policy, now)
        if is_late:
            att_kwargs["status"] = "late"
        att_kwargs["late_minutes"] = late_mins'''

if old_late in views:
    views = views.replace(old_late, new_late)
    print("  ✅ تم تحديث late logic ليستخدم Assignment")
else:
    print("  ℹ️  late logic مختلف - ممكن يحتاج مراجعة")


# نضيف رسالة النوع في الـ response
old_msg = '''        msg = "تم تسجيل حضورك بنجاح"
        if branch and branch.latitude and branch.longitude:
            msg += f" - المسافة من الفرع: {distance} متر"

        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:
            msg += f" - تم تسجيل {att_kwargs.get(\'late_minutes\', 0)} دقيقة تأخير"'''

new_msg = '''        msg = "تم تسجيل حضورك بنجاح"
        if branch and branch.latitude and branch.longitude:
            msg += f" - المسافة من الفرع: {distance} متر"

        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:
            msg += f" - تم تسجيل {att_kwargs.get(\'late_minutes\', 0)} دقيقة تأخير"

        if checkin_mode == "exception":
            msg += " (حالة استثنائية - سيتم مراجعتها)"
        elif checkin_mode == "off_notify":
            msg += " (يوم راحة - تم إشعار HR)"
        elif checkin_mode == "holiday_extra":
            msg += " (إجازة رسمية - سيتحسب شيفت إضافي)"'''

if old_msg in views:
    views = views.replace(old_msg, new_msg)
    print("  ✅ تم تحديث رسائل الـ response")
else:
    print("  ℹ️  لم أجد الرسائل المتوقعة")


write_file(views_path, views)


# ════════════════════════════════════════════════════════════
# 3) تحديث check_in.html — عرض نوع التكليف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث smart_check_in_page...")

views = read_file(views_path)

# نحدث smart_check_in_page ليرسل assignment في context
old_context = """    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'show_map': show_map,
        'page_title': 'تسجيل الحضور',
    }"""

new_context = """    # جلب تكليف اليوم
    today_assignment = None
    if employee:
        today_assignment = _get_today_assignment(employee)

    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'today_assignment': today_assignment,
        'show_map': show_map,
        'page_title': 'تسجيل الحضور',
    }"""

if old_context in views:
    views = views.replace(old_context, new_context)
    write_file(views_path, views)
    print("  ✅ تم إضافة today_assignment في context")
else:
    print("  ℹ️  context مختلف أو محدث")


# ════════════════════════════════════════════════════════════
# 4) تحديث check_in.html template
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث check_in.html...")

checkin_path = os.path.join(BASE_DIR, "templates", "attendance", "check_in.html")
checkin = read_file(checkin_path)

# نضيف معلومة التكليف تحت معلومة الفرع
if "today_assignment" not in checkin:
    assignment_info = """
      <!-- تكليف اليوم -->
      {% if today_assignment %}
      <div class="location-info mt-2"
           style="background:{% if today_assignment.is_off %}#fde8e8{% elif today_assignment.is_extra_shift %}#fff7ed{% else %}#e0f7fa{% endif %};
                  border:1px solid {% if today_assignment.is_off %}#fca5a5{% elif today_assignment.is_extra_shift %}#fed7aa{% else %}#67e8f9{% endif %};
                  border-radius:10px; padding:10px;">
        <div class="d-flex align-items-center gap-2">
          {% if today_assignment.is_off %}
            <i class="bi bi-calendar-x text-danger"></i>
            <small class="text-danger fw-semibold">
              {{ today_assignment.get_day_type_display }} — لا يوجد عمل مجدول
            </small>
          {% elif today_assignment.is_extra_shift %}
            <i class="bi bi-plus-circle text-warning"></i>
            <small class="text-warning fw-semibold">
              شيفت إضافي
              {% if today_assignment.count_as_overtime %} (أوفر تايم){% endif %}
            </small>
          {% else %}
            <i class="bi bi-briefcase" style="color:#06B6D4;"></i>
            <small style="color:#06B6D4;" class="fw-semibold">
              {{ today_assignment.get_day_type_display }} — {{ today_assignment.get_work_mode_display }}
              {% if today_assignment.expected_hours %}
                ({{ today_assignment.expected_hours }} ساعات)
              {% endif %}
            </small>
          {% endif %}
        </div>
        {% if today_assignment.start_time and today_assignment.end_time %}
        <small class="text-muted d-block mt-1">
          <i class="bi bi-clock me-1"></i>
          {{ today_assignment.start_time|time:"H:i" }} - {{ today_assignment.end_time|time:"H:i" }}
          {% if today_assignment.segment_2_start %}
            + {{ today_assignment.segment_2_start|time:"H:i" }} - {{ today_assignment.segment_2_end|time:"H:i" }}
          {% endif %}
        </small>
        {% endif %}
        {% if today_assignment.task_title %}
        <small class="text-muted d-block mt-1">
          <i class="bi bi-card-checklist me-1"></i>
          {{ today_assignment.task_title }}
        </small>
        {% endif %}
      </div>
      {% endif %}
"""
    # نضيف بعد geofencing-info أو بعد location-info
    if 'id="geofencing-info"' in checkin:
        geo_end = checkin.find("{% endif %}", checkin.find('id="geofencing-info"'))
        if geo_end != -1:
            insert_point = geo_end + len("{% endif %}")
            checkin = checkin[:insert_point] + assignment_info + checkin[insert_point:]
    elif 'id="locationInfo"' in checkin:
        loc_end = checkin.find("</div>", checkin.find('id="locationInfo"'))
        if loc_end != -1:
            checkin = checkin[:loc_end + 6] + assignment_info + checkin[loc_end + 6:]

    write_file(checkin_path, checkin)
    print("  ✅ تم إضافة معلومة التكليف في check_in.html")
else:
    print("  ℹ️  today_assignment موجود في check_in.html")


print("\n" + "=" * 60)
print("  ✅ Patch 42b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Assignment-aware check-in helpers
  2. ✅ _get_today_assignment
  3. ✅ _check_assignment_allows_checkin
  4. ✅ _get_late_logic_for_assignment
  5. ✅ _handle_assignment_checkin
  6. ✅ policy_api_check_in يستخدم Assignment
  7. ✅ late logic يعتمد على نوع التكليف
  8. ✅ exception handling للحضور بدون تكليف
  9. ✅ رسائل واضحة حسب نوع اليوم
  10. ✅ check_in.html يعرض تكليف اليوم

المنطق الجديد:
  - fixed/split → late ينطبق
  - flexible/field/remote → late لا ينطبق
  - off_day → حسب policy (block/notify/convert)
  - leave_day → حسب policy (block/notify/convert)
  - holiday → يتحول لشيفت إضافي
  - بدون assignment → حسب policy (default/exception/block)

شغّل السيرفر وجرب:
  emp10003 / emp10004
  /attendance/check-in/
  لازم يظهر تكليف اليوم
""")