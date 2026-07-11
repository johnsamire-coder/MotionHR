"""
Patch 49a - قراءة محتوى الملفات المهمة اللي محتاجينها للإصلاح
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_file(path, encoding='utf-8'):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    try:
        with open(full, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(full, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except:
            return f"[تعذرت القراءة]"

def print_file(path, label=None, max_lines=None):
    print(f"\n{'='*60}")
    print(f"📄 {label or path}")
    print(f"{'='*60}")
    content = read_file(path)
    if content is None:
        print("  ❌ مش موجود")
        return
    lines = content.split('\n')
    if max_lines:
        for i, line in enumerate(lines[:max_lines], 1):
            print(f"{i:4}: {line}")
        if len(lines) > max_lines:
            print(f"\n  ... ({len(lines) - max_lines} سطر باقي)")
    else:
        print(content)

# ─────────────────────────────────────────────
print("\n" + "="*60)
print("  PATCH 49a — قراءة الملفات المهمة")
print("="*60)

# 1. attendance/list.html — علشان نشوف مشكلة override pk
print_file('templates/attendance/list.html', 'Attendance List Template')

# 2. employees/list.html — علشان نشوف البحث والـ export
print_file('templates/employees/list.html', 'Employee List Template')

# 3. employees/form.html — علشان نشوف الـ multi-step form
print_file('templates/employees/form.html', 'Employee Form Template')

# 4. attendance/live_map.html — علشان نشوف مشكلة الخريطة
print_file('templates/attendance/live_map.html', 'Live Map Template')

# 5. attendance/visit_form.html — مش موجود؟
print_file('templates/attendance/visit_form.html', 'Visit Form Template')

# 6. attendance/schedule_week.html — مش موجود؟
print_file('templates/attendance/schedule_week.html', 'Schedule Week Template')

# 7. companies/departments_list.html
print_file('templates/companies/departments_list.html', 'Departments List Template')

# 8. companies/charter_manage.html
print_file('templates/companies/charter_manage.html', 'Charter Manage Template')

# 9. attendance/assignment_form.html
print_file('templates/attendance/assignment_form.html', 'Assignment Form Template')

# 10. reports/employees_report.html
print_file('templates/reports/employees_report.html', 'Employees Report Template')

# 11. reports/attendance_report.html
print_file('templates/reports/attendance_report.html', 'Attendance Report Template')

# 12. reports/late_report.html
print_file('templates/reports/late_report.html', 'Late Report Template')

# 13. reports/leave_report.html
print_file('templates/reports/leave_report.html', 'Leave Report Template')

# 14. base/base.html أو base/dashboard_base.html
print_file('templates/base/base.html', 'Base Template')
print_file('templates/base/dashboard_base.html', 'Dashboard Base Template')

# 15. employees/views.py كامل
print_file('employees/views.py', 'Employee Views - كامل')

# 16. reports/views.py كامل
print_file('reports/views.py', 'Reports Views - كامل')

# 17. reports/utils.py كامل
print_file('reports/utils.py', 'Reports Utils - كامل')

# 18. companies/views.py — أول 150 سطر + نبحث عن departments و charter
print(f"\n{'='*60}")
print("📄 companies/views.py — أول 150 سطر")
print(f"{'='*60}")
content = read_file('companies/views.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines[:150], 1):
        print(f"{i:4}: {line}")
    print(f"\n  ... ({len(lines) - 150} سطر باقي)")

# 19. attendance/views.py — نبحث عن override و stealth
print(f"\n{'='*60}")
print("📄 attendance/views.py — بحث عن override, stealth, schedule, visit")
print(f"{'='*60}")
content = read_file('attendance/views.py')
if content:
    lines = content.split('\n')
    keywords = ['override', 'stealth', 'schedule', 'visit', 'assignment', 'live_map', 'api_live']
    for i, line in enumerate(lines, 1):
        if any(kw in line.lower() for kw in keywords):
            print(f"{i:4}: {line}")

# 20. companies/models.py كامل
print_file('companies/models.py', 'Companies Models - كامل')

# 21. employees/models.py — نشوف direct_manager و role
print(f"\n{'='*60}")
print("📄 employees/models.py — direct_manager و الـ roles")
print(f"{'='*60}")
content = read_file('employees/models.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if any(kw in line.lower() for kw in ['direct_manager', 'role', 'manager', 'supervisor', 'user_type']):
            print(f"{i:4}: {line}")

# 22. accounts/models.py كامل
print_file('accounts/models.py', 'Accounts Models - كامل')

# 23. motionhr/urls.py كامل
print_file('motionhr/urls.py', 'Main URLs - كامل')

# 24. motionhr/settings.py كامل
print_file('motionhr/settings.py', 'Settings - كامل')

# 25. companies/urls.py
print_file('companies/urls.py', 'Companies URLs')

# 26. employees/urls.py
print_file('employees/urls.py', 'Employee URLs')

# 27. reports/urls.py
print_file('reports/urls.py', 'Reports URLs')

# 28. attendance/stealth_manage.html
print_file('templates/attendance/stealth_manage.html', 'Stealth Manage Template')

# 29. attendance/visits.html
print_file('templates/attendance/visits.html', 'Visits Template')

# 30. companies/policies.html
print_file('templates/companies/policies.html', 'Policies Template')

print("\n" + "="*60)
print("  خلص 49a ✅")
print("="*60)