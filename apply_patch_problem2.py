import os

api_path = 'attendance/api_mobile.py'
with open(api_path, 'r', encoding='utf-8') as f:
    content = f.read()

# البلوك الخاطئ الحالي
old_code = '''        today = timezone.localdate()
        shift = get_active_shift(employee, today)

        if shift and shift.start_time and shift.end_time:
            start_dt = datetime.combine(today, shift.start_time)
            end_dt = datetime.combine(today, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            mode = getattr(employee, 'attendance_mode', 'fixed_shift')
            if mode == 'flexible_hours' and attendance and attendance.check_in_time:
                check_in_local = timezone.localtime(attendance.check_in_time)
                shift_duration = (end_dt - start_dt).total_seconds()
                end_time_aware = check_in_local + timedelta(seconds=shift_duration)
            else:
                end_time_aware = timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt'''

# البلوك المصحح المحترف
new_code = '''        att_date = attendance.date if (attendance and attendance.date) else timezone.localdate()
        shift = get_active_shift(employee, att_date)

        if shift:
            shift_start, shift_end = get_shift_bounds(shift, att_date)
            mode = getattr(employee, 'attendance_mode', 'fixed_shift')
            
            if mode == 'flexible_hours' and attendance and attendance.check_in_time:
                check_in_local = timezone.localtime(attendance.check_in_time)
                if shift_start and shift_end:
                    shift_duration = (shift_end - shift_start).total_seconds()
                    end_time_aware = check_in_local + timedelta(seconds=shift_duration)
                else:
                    end_time_aware = check_in_local + timedelta(hours=8)
            else:
                end_time_aware = shift_end'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ تم تحديث كود الانصراف بنجاح وتوحيد استخدام get_shift_bounds!")
else:
    print("⚠️ لم يتم العثور على البلوك الدقيق بالنص الحرفي، جاري تطبيق التحديث المرن...")
    # تطبيق مرن
    target_start = "today = timezone.localdate()\n        shift = get_active_shift(employee, today)"
    if target_start in content:
        content = content.replace(target_start, "att_date = attendance.date if (attendance and attendance.date) else timezone.localdate()\n        shift = get_active_shift(employee, att_date)")
    
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ تم التطبيق المرن بنجاح!")
