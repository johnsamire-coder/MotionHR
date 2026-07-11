#!/usr/bin/env python3
"""
Patch 28b: Add Missing Feature Aliases
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
helpers_path = os.path.join(BASE_DIR, "subscriptions", "helpers.py")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 28b: Feature Aliases")
print("=" * 60)

content = read_file(helpers_path)

# 1) زوّد DEMO_FEATURES بالمفاتيح الفعلية كمان
old_demo = """DEMO_FEATURES = {
    'employee_management',
    'attendance_tracking',
    'gps_attendance',
    'field_tracking',
    'live_map',
    'location_visits',
    'reports_basic',
    'reports_advanced',
    'excel_export',
    'pdf_export',
    'login_by_employee_code',
    'login_by_phone',
    'leave_management',
    'multi_branch',
    'payroll_basic',
}"""

new_demo = """DEMO_FEATURES = {
    'employee_management',
    'employees_management',

    'attendance_tracking',
    'attendance_records',
    'gps_attendance',
    'attendance_gps',

    'field_tracking',
    'continuous_tracking',
    'live_map',
    'location_visits',

    'reports_basic',
    'reports_advanced',
    'excel_export',
    'pdf_export',

    'login_by_employee_code',
    'login_by_phone',

    'leave_management',
    'multi_branch',
    'payroll_basic',
}"""

if old_demo in content:
    content = content.replace(old_demo, new_demo)
    print("  ✅ تم تحديث DEMO_FEATURES")
else:
    print("  ℹ️  DEMO_FEATURES شكلها مختلف - هنكمل aliases")

# 2) زوّد FEATURE_ALIASES
replacements = {
    "'employees_management': 'employee_management',": """'employees_management': 'employee_management',
    'attendance_records': 'attendance_tracking',
    'attendance_gps': 'gps_attendance',
    'continuous_tracking': 'field_tracking',""",
}

for old, new in replacements.items():
    if old in content and new not in content:
        content = content.replace(old, new)
        print("  ✅ تم إضافة aliases الجديدة")

write_file(helpers_path, content)

print("\n" + "=" * 60)
print("  ✅ Patch 28b اكتمل!")
print("=" * 60)
print("""
جرب دلوقتي:
- تسجيل الحضور
- سجلات الحضور
- الزيارات
- التتبع

ولو اشتغلوا يبقى اتقفل جزء كبير من المرحلة 1
""")