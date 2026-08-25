import os, sys

# 1. Patch api_mobile.py
api_path = os.path.join(r'C:\MotionHR\Backend', 'attendance', 'api_mobile.py')
with open(api_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix early checkin minutes logic
old_early = "early_minutes = int(getattr(active_shift, 'early_checkin_minutes', 30) or 30)"
new_early = """early_val = getattr(active_shift, 'early_checkin_minutes', None)
            early_minutes = int(early_val) if early_val is not None else 30"""

if old_early in content:
    content = content.replace(old_early, new_early)

# Add late checkout enforcement logic
old_checkout_anchor = "# ── تحقق من وقت الشيفت (للحضور فقط) ──"
new_checkout_logic = """# ── تحقق من وقت الشيفت (للانصراف) ──
    if action == 'check_out' and active_shift:
        attendance_mode = getattr(employee, 'attendance_mode', 'fixed_shift')
        shift_mode = getattr(active_shift, 'shift_mode', 'fixed') or 'fixed'
        skip_out_check = (
            attendance_mode in ('flexible_hours', 'field_worker')
            or shift_mode in ('flex_fixed', 'flex_split')
        )
        if not skip_out_check and shift_end:
            from datetime import timedelta
            late_checkout_allowed = getattr(active_shift, 'late_checkout_allowed', False)
            late_checkout_mins = getattr(active_shift, 'late_checkout_minutes', None)
            
            if late_checkout_allowed or (late_checkout_mins is not None and late_checkout_mins > 0):
                late_mins = int(late_checkout_mins or 0)
                max_checkout_time = shift_end + timedelta(minutes=late_mins)
                if now > max_checkout_time:
                    shift_end_str = shift_end.strftime('%I:%M %p')
                    return Response({
                        'success': False,
                        **bilingual_message(
                            employee,
                            f'انتهت المهلة المحددة لتسجيل الانصراف لهذا الشيفت (الموعد: {shift_end_str} + سماحية {late_mins} دقيقة).',
                            f'Check-out time window for this shift has expired (Shift end: {shift_end_str} + {late_mins} min grace).'
                        ),
                        'late_checkout_expired': True,
                    }, status=400)

    """ + old_checkout_anchor

if old_checkout_anchor in content and "late_checkout_expired" not in content:
    content = content.replace(old_checkout_anchor, new_checkout_logic)

with open(api_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ [1/3] تم تحديث api_mobile.py بنجاح!")

# 2. Patch reminders.py
reminders_path = os.path.join(r'C:\MotionHR\Backend', 'attendance', 'reminders.py')
with open(reminders_path, 'r', encoding='utf-8') as f:
    r_content = f.read()

new_reminder_func = """
# ═══════════════════════════════════════════════════════
# 7.8  تذكير بداية الشيفت قبل 15 دقيقة
# ═══════════════════════════════════════════════════════
def remind_shift_starting_soon():
    \"\"\"
    يفحص الموظفين النشطين الذين يبدأ شيفتهم خلال 15 دقيقة ولم يسجلوا حضوراً بعد.
    \"\"\"
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Attendance, Employee
        from attendance.api_mobile import get_active_shift, get_shift_bounds

        User = get_user_model()
        now = timezone.now()
        today = timezone.localdate()

        employees = Employee._base_manager.filter(
            status='active'
        ).select_related('user', 'company')

        for employee in employees:
            if not employee.user:
                continue

            has_attendance = Attendance._base_manager.filter(
                employee=employee,
                date=today,
                check_in_time__isnull=False
            ).exists()

            if has_attendance:
                continue

            shift = get_active_shift(employee, today)
            if not shift:
                continue

            shift_start, shift_end = get_shift_bounds(shift, today)
            if not shift_start:
                continue

            diff_mins = (shift_start - now).total_seconds() / 60.0

            if 13 <= diff_mins <= 17:
                shift_name = getattr(shift, 'name', 'الشيفت')
                shift_start_str = shift_start.strftime('%I:%M %p')
                _send_to_users(
                    User.objects.filter(pk=employee.user.pk),
                    title="⏰ تذكير — ميعاد الشيفت قريب",
                    body=f"شيفت {shift_name} يبدأ خلال 15 دقيقة (الساعة {shift_start_str}). يرجى تسجيل الحضور.",
                    title_en="⏰ Shift Starting Soon",
                    body_en=f"Your shift ({shift_name}) starts in 15 minutes at {shift_start_str}. Please check in.",
                    data={"type": "reminder_shift_starting", "shift_id": str(shift.id)},
                )
                logger.info(f"remind_shift_starting_soon: Sent to {employee.user.username}")

    except Exception as e:
        logger.error(f"remind_shift_starting_soon error: {e}")
"""

if "def remind_shift_starting_soon" not in r_content:
    dispatch_pos = r_content.find("dispatch = {")
    if dispatch_pos != -1:
        r_content = r_content[:dispatch_pos] + new_reminder_func + "\n\n" + r_content[dispatch_pos:]
        r_content = r_content.replace(
            '"shift_coverage": remind_shift_coverage_gaps,',
            '"shift_coverage": remind_shift_coverage_gaps,\n        "shift_starting_soon": remind_shift_starting_soon,'
        )

with open(reminders_path, 'w', encoding='utf-8') as f:
    f.write(r_content)
print("✅ [2/3] تم تحديث reminders.py بنجاح!")

# 3. Patch send_reminders.py command
command_path = os.path.join(r'C:\MotionHR\Backend', 'attendance', 'management', 'commands', 'send_reminders.py')
with open(command_path, 'r', encoding='utf-8') as f:
    c_content = f.read()

if "shift_starting_soon" not in c_content:
    c_content = c_content.replace(
        '"shift_coverage"',
        '"shift_coverage", "shift_starting_soon"'
    )
    with open(command_path, 'w', encoding='utf-8') as f:
        f.write(c_content)
print("✅ [3/3] تم تحديث send_reminders.py بنجاح!")
