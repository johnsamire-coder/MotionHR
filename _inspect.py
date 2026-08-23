import os, sys, pathlib

BASE = pathlib.Path('.')
print("=" * 60)
print("PYTHON PATH:", sys.executable)
print("CURRENT DIR:", BASE.resolve())
print("=" * 60)

# 1) فحص الموديلات
models_to_check = [
    ('leaves/models.py', ['LeaveType', 'LeavePolicyTier', 'LeavePolicy', 'LeaveBalance', 'LeaveRequest']),
    ('attendance/models.py', ['Shift', 'Attendance', 'AttendancePolicy', 'AbsenceRule', 'DailyAttendanceSummary']),
]

for file_path, classes in models_to_check:
    fp = BASE / file_path
    print(f"\n--- FILE: {file_path} ---")
    if not fp.exists():
        print(f"  [X] NOT FOUND")
        continue
    content = fp.read_text(encoding='utf-8')
    print(f"  [OK] Exists ({len(content.splitlines())} lines)")
    for cls in classes:
        found = f"class {cls}" in content
        print(f"  Class {cls}: {'FOUND' if found else 'MISSING'}")

# 2) فحص Django Settings و Apps
print("\n--- DJANGO SETUP & APPS ---")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    import django
    django.setup()
    from django.apps import apps
    
    for app in apps.get_app_configs():
        if any(k in app.name for k in ['leave', 'attend', 'employee', 'account', 'company', 'request']):
            print(f"  App: {app.name} ({app.label})")
            for model in app.get_models():
                fields = [f.name for f in model._meta.get_fields()]
                print(f"    - Model: {model.__name__} (Fields: {len(fields)})")
except Exception as e:
    print(f"  Django Setup Error: {e}")

# 3) فحص ملفات الـ Payroll و Services والـ URLs
print("\n--- FILES EXISTENCE CHECK ---")
check_files = [
    'attendance/views.py',
    'attendance/urls.py',
    'attendance/serializers.py',
    'attendance/payroll_engine.py',
    'attendance/services.py',
    'leaves/serializers.py',
    'leaves/urls.py',
    'leaves/views.py',
    'leaves/services.py',
]

for cf in check_files:
    p = BASE / cf
    print(f"  {cf}: {'EXISTS' if p.exists() else 'NOT FOUND'}")

print("\n" + "=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)
