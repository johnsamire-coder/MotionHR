import os

filePath = r'attendance/api_mobile.py'
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. إعادة حساب shift_bounds باستخدام attendance.date عند check_out
target_checkout = "# ── تحقق من وقت الشيفت (للانصراف) ──"

patch_checkout = """# ── إعاده حساب حدود الشيفت بناءً على تاريخ الحضور الأصلي ──
    if action == 'check_out' and attendance and getattr(attendance, 'date', None) and active_shift:
        shift_start, shift_end = get_shift_bounds(active_shift, attendance.date)

    # ── تحقق من وقت الشيفت (للانصراف) ──"""

if target_checkout in content and "إعاده حساب حدود الشيفت بناءً على تاريخ الحضور الأصلي" not in content:
    content = content.replace(target_checkout, patch_checkout)

with open(filePath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ تم تطبيق الإصلاح الهندسي بنجاح!")
