import pathlib, re

BASE = pathlib.Path('.')

def extract_model_fields(filepath, classname):
    fp = BASE / filepath
    if not fp.exists():
        print(f"\n[!] {filepath} NOT FOUND")
        return
    content = fp.read_text(encoding='utf-8')
    # Find class definition
    pattern = rf'class {classname}\b[^\n]*\n(.*?)(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"\n[!] Class {classname} not found")
        return
    body = match.group(1)
    # Extract field definitions
    fields = []
    for line in body.splitlines():
        stripped = line.strip()
        if '=' in stripped and 'models.' in stripped and not stripped.startswith('#'):
            field_name = stripped.split('=')[0].strip()
            field_type = stripped.split('models.')[1].split('(')[0] if 'models.' in stripped else '?'
            fields.append(f"  {field_name}: {field_type}")
        if stripped.startswith('class Meta') or stripped.startswith('def '):
            break
    print(f"\n--- {classname} ({len(fields)} fields) ---")
    for f in fields:
        print(f)

print("=" * 60)
print("LEAVES MODELS - ALL FIELDS")
print("=" * 60)
extract_model_fields('leaves/models.py', 'LeaveType')
extract_model_fields('leaves/models.py', 'LeavePolicy')
extract_model_fields('leaves/models.py', 'LeavePolicyTier')
extract_model_fields('leaves/models.py', 'LeaveBalance')
extract_model_fields('leaves/models.py', 'LeaveRequest')

print("\n" + "=" * 60)
print("ATTENDANCE MODELS - ALL FIELDS")
print("=" * 60)
extract_model_fields('attendance/models.py', 'Shift')
extract_model_fields('attendance/models.py', 'Attendance')
extract_model_fields('attendance/models.py', 'AttendancePolicy')
extract_model_fields('attendance/models.py', 'AbsenceRule')
extract_model_fields('attendance/models.py', 'DailyAttendanceSummary')

