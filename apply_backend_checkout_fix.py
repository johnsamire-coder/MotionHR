import os

filePath = r'attendance/api_mobile.py'
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. إصلاح دالة mobile_attendance_action (عند الانصراف)
target1 = '''        today = timezone.localdate()
        shift = get_active_shift(employee, today)'''

replacement1 = '''        att_date = attendance.date if (attendance and attendance.date) else timezone.localdate()
        shift = get_active_shift(employee, att_date)'''

if target1 in content:
    content = content.replace(target1, replacement1)

# 2. إصلاح دالة mobile_attendance_status (العداد المباشر في الموبايل)
target2 = '''            elif shift.start_time and shift.end_time:
                start_dt = datetime.combine(today, shift.start_time)
                end_dt = datetime.combine(today, shift.end_time)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                tz = timezone.get_current_timezone()
                effective_start_dt = timezone.make_aware(start_dt, tz) if timezone.is_naive(start_dt) else start_dt
                effective_end_dt = timezone.make_aware(end_dt, tz) if timezone.is_naive(end_dt) else end_dt

                shift_start_str = shift.start_time.strftime('%I:%M %p')
                shift_end_str = shift.end_time.strftime('%I:%M %p')'''

replacement2 = '''            elif shift.start_time and shift.end_time:
                effective_start_dt, effective_end_dt = get_shift_bounds(shift, att_date)
                shift_start_str = shift.start_time.strftime('%I:%M %p') if shift.start_time else ''
                shift_end_str = shift.end_time.strftime('%I:%M %p') if shift.end_time else '' '''

if target2 in content:
    content = content.replace(target2, replacement2)

with open(filePath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ تم تحديث api_mobile.py بنجاح!")
