import os, sys, pathlib, re

BASE = pathlib.Path('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    print("[OK] Django initialized successfully.")
except Exception as e:
    print(f"[!] Django Setup Note: {e}")

print("\n" + "="*50)
print("FILES IN leaves/")
print("="*50)
leaves_dir = BASE / 'leaves'
if leaves_dir.exists():
    for f in leaves_dir.glob('**/*.py'):
        print(f"  - {f.relative_to(BASE)}")

print("\n" + "="*50)
print("FILES IN attendance/")
print("="*50)
att_dir = BASE / 'attendance'
if att_dir.exists():
    for f in att_dir.glob('**/*.py'):
        print(f"  - {f.relative_to(BASE)}")

def print_model_definition(file_path, class_name):
    fp = BASE / file_path
    if not fp.exists():
        return
    content = fp.read_text(encoding='utf-8')
    pattern = rf'(class {class_name}\b.*?)(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        snippet = match.group(1).strip()
        lines = snippet.splitlines()[:35]  # أول 35 سطر من الموديل
        print(f"\n--- {class_name} in {file_path} (First 35 lines) ---")
        print("\n".join(lines))
    else:
        print(f"\n[!] Class {class_name} not found in {file_path}")

print("\n" + "="*50)
print("CURRENT MODEL DEFINITIONS")
print("="*50)
print_model_definition('leaves/models.py', 'LeaveType')
print_model_definition('leaves/models.py', 'LeavePolicyTier')
print_model_definition('attendance/models.py', 'Shift')
print_model_definition('attendance/models.py', 'Attendance')
print_model_definition('attendance/models.py', 'AttendancePolicy')
print_model_definition('attendance/models.py', 'AbsenceRule')

