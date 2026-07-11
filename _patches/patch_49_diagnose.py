"""
Patch 49 - Diagnose: يقرأ كل الملفات الموجودة ويطبع تقرير كامل
شغّله أول حاجة قبل أي تعديل
"""

import os
import sys

# إضافة مسار المشروع
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def check_file(path, label=""):
    full = os.path.join(BASE_DIR, path)
    exists = os.path.exists(full)
    size = os.path.getsize(full) if exists else 0
    status = "✅" if exists else "❌"
    print(f"  {status} {label or path} {'(' + str(size) + ' bytes)' if exists else '(مش موجود)'}")
    return exists

def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if os.path.exists(full):
        with open(full, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def scan_dir(path, ext=None):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        print(f"  ❌ المجلد مش موجود: {path}")
        return []
    files = []
    for root, dirs, filenames in os.walk(full):
        # تجاهل __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in filenames:
            if ext is None or f.endswith(ext):
                rel = os.path.relpath(os.path.join(root, f), BASE_DIR)
                files.append(rel)
    return sorted(files)

print("=" * 70)
print("  PATCH 49 — تشخيص كامل للمشروع")
print("=" * 70)

# ─────────────────────────────────────────────
print("\n📁 هيكل المشروع الكامل:")
print("-" * 50)

apps = [
    'motionhr',
    'core',
    'accounts',
    'companies',
    'employees',
    'attendance',
    'leaves',
    'requests_app',
    'subscriptions',
    'reports',
    'landing',
]

for app in apps:
    app_path = os.path.join(BASE_DIR, app)
    if os.path.exists(app_path):
        print(f"\n  📦 {app}/")
        py_files = scan_dir(app, '.py')
        for f in py_files:
            print(f"    ├── {f}")
    else:
        print(f"\n  ❌ {app}/ — مش موجود")

# ─────────────────────────────────────────────
print("\n\n📁 Templates:")
print("-" * 50)
templates = scan_dir('templates', '.html')
for t in templates:
    print(f"  ├── {t}")

# ─────────────────────────────────────────────
print("\n\n📁 Static Files:")
print("-" * 50)
statics = scan_dir('static')
for s in statics:
    print(f"  ├── {s}")

# ─────────────────────────────────────────────
print("\n\n🔍 فحص الملفات المهمة للـ Patches:")
print("-" * 50)

critical_files = [
    # Models
    ('employees/models.py', 'Employee Model'),
    ('attendance/models.py', 'Attendance Model'),
    ('companies/models.py', 'Companies Model'),
    ('accounts/models.py', 'Accounts Model'),
    ('reports/models.py', 'Reports Model'),
    ('leaves/models.py', 'Leaves Model'),

    # Views
    ('employees/views.py', 'Employee Views'),
    ('attendance/views.py', 'Attendance Views'),
    ('companies/views.py', 'Companies Views'),
    ('reports/views.py', 'Reports Views'),
    ('leaves/views.py', 'Leaves Views'),

    # URLs
    ('employees/urls.py', 'Employee URLs'),
    ('attendance/urls.py', 'Attendance URLs'),
    ('companies/urls.py', 'Companies URLs'),
    ('reports/urls.py', 'Reports URLs'),

    # Templates المهمة
    ('templates/employees/list.html', 'Employee List Template'),
    ('templates/employees/add.html', 'Employee Add Template'),
    ('templates/attendance/list.html', 'Attendance List Template'),
    ('templates/attendance/live_map.html', 'Live Map Template'),
    ('templates/attendance/visits.html', 'Visits Template'),
    ('templates/attendance/visits_add.html', 'Visit Add Template'),
    ('templates/attendance/schedule.html', 'Schedule Template'),
    ('templates/attendance/stealth_manage.html', 'Stealth Template'),
    ('templates/companies/departments.html', 'Departments Template'),
    ('templates/companies/charter.html', 'Charter Template'),
    ('templates/reports/attendance_report.html', 'Attendance Report Template'),
    ('templates/reports/late_report.html', 'Late Report Template'),
    ('templates/reports/employee_report.html', 'Employee Report Template'),
    ('templates/reports/leave_report.html', 'Leave Report Template'),
    ('templates/base.html', 'Base Template'),
    ('templates/sidebar.html', 'Sidebar Template'),

    # Static
    ('static/css/style.css', 'Main CSS'),
    ('static/js/app.js', 'Main JS'),

    # Settings
    ('motionhr/settings.py', 'Settings'),
    ('motionhr/urls.py', 'Main URLs'),

    # Requirements
    ('requirements.txt', 'Requirements'),
]

for path, label in critical_files:
    check_file(path, label)

# ─────────────────────────────────────────────
print("\n\n🔍 قراءة محتوى الملفات المهمة:")
print("-" * 50)

# attendance/urls.py — علشان نشوف مشكلة override
print("\n📄 attendance/urls.py:")
content = read_file('attendance/urls.py')
if content:
    print(content)
else:
    print("  ❌ مش موجود")

# attendance/views.py — نشوف إيه اللي موجود
print("\n📄 attendance/views.py (أول 100 سطر):")
content = read_file('attendance/views.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines[:100], 1):
        print(f"  {i:3}: {line}")
    if len(lines) > 100:
        print(f"  ... ({len(lines) - 100} سطر تاني)")
else:
    print("  ❌ مش موجود")

# employees/views.py — نشوف إيه موجود
print("\n📄 employees/views.py (أول 80 سطر):")
content = read_file('employees/views.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines[:80], 1):
        print(f"  {i:3}: {line}")
    if len(lines) > 80:
        print(f"  ... ({len(lines) - 80} سطر تاني)")
else:
    print("  ❌ مش موجود")

# reports/views.py
print("\n📄 reports/views.py (أول 80 سطر):")
content = read_file('reports/views.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines[:80], 1):
        print(f"  {i:3}: {line}")
    if len(lines) > 80:
        print(f"  ... ({len(lines) - 80} سطر تاني)")
else:
    print("  ❌ مش موجود")

# companies/models.py — نشوف CompanyPolicy و stealth
print("\n📄 companies/models.py (نبحث عن stealth و policy):")
content = read_file('companies/models.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if any(kw in line.lower() for kw in ['stealth', 'policy', 'charter', 'tracking']):
            print(f"  {i:3}: {line}")
else:
    print("  ❌ مش موجود")

# employees/models.py — نشوف attendance_mode و stealth
print("\n📄 employees/models.py (نبحث عن stealth و mode):")
content = read_file('employees/models.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if any(kw in line.lower() for kw in ['stealth', 'mode', 'manager', 'role', 'supervisor']):
            print(f"  {i:3}: {line}")
else:
    print("  ❌ مش موجود")

# attendance/models.py — نشوف DailyAssignment
print("\n📄 attendance/models.py (نبحث عن DailyAssignment و work_mode):")
content = read_file('attendance/models.py')
if content:
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if any(kw in line.lower() for kw in ['dailyassignment', 'work_mode', 'day_type', 'override']):
            print(f"  {i:3}: {line}")
else:
    print("  ❌ مش موجود")

# requirements.txt
print("\n📄 requirements.txt:")
content = read_file('requirements.txt')
if content:
    print(content)
else:
    print("  ❌ مش موجود — هنحتاج ننشئه")

# ─────────────────────────────────────────────
print("\n\n🔍 فحص الـ Installed Apps في settings.py:")
print("-" * 50)
content = read_file('motionhr/settings.py')
if content:
    lines = content.split('\n')
    in_apps = False
    for line in lines:
        if 'INSTALLED_APPS' in line:
            in_apps = True
        if in_apps:
            print(f"  {line}")
        if in_apps and ']' in line:
            break
else:
    print("  ❌ مش موجود")

# ─────────────────────────────────────────────
print("\n\n🔍 فحص الـ Main URLs:")
print("-" * 50)
content = read_file('motionhr/urls.py')
if content:
    print(content)
else:
    print("  ❌ مش موجود")

# ─────────────────────────────────────────────
print("\n\n📊 ملخص نهائي:")
print("=" * 70)
print("""
بعد شغّل الملف ده:
1. انسخ الـ output كامل
2. ابعته هنا
3. وأنا هبني الـ Patches على أساس الملفات الفعلية الموجودة عندك
""")

print("=" * 70)
print("  خلص التشخيص ✅")
print("=" * 70)