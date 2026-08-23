import pathlib, re

BASE = pathlib.Path('.')

print("=== 1. Checking AbsenceRule Model in attendance/models.py ===")
models_content = (BASE / 'attendance' / 'models.py').read_text(encoding='utf-8')
match = re.search(r'class AbsenceRule\(.*?\):.*?(?=\nclass |\Z)', models_content, re.DOTALL)
if match:
    print(match.group(0))
else:
    print("AbsenceRule not found in attendance/models.py")

print("\n=== 2. Checking Absence APIs in attendance/ ===")
for f in ['attendance/api_rules.py', 'attendance/api_attendance_policy.py', 'attendance/api_general_policies.py', 'attendance/api_payroll.py', 'attendance/payroll_rules.py']:
    p = BASE / f
    if p.exists():
        text = p.read_text(encoding='utf-8')
        if 'AbsenceRule' in text or 'absence' in text.lower():
            matches = [line.strip() for line in text.splitlines() if 'absence' in line.lower() or 'deduction' in line.lower()][:10]
            print(f"--- File: {f} ---")
            print('\n'.join(matches))

print("\n=== 3. Checking Payroll Absence Deduction Calculation ===")
payroll_files = list(BASE.glob('attendance/*payroll*.py')) + list(BASE.glob('attendance/*rule*.py'))
for pf in payroll_files:
    content = pf.read_text(encoding='utf-8')
    if 'absence' in content.lower():
        print(f"\nFound 'absence' in {pf.name}:")
        for line in content.splitlines():
            if 'def ' in line and ('absence' in line.lower() or 'deduct' in line.lower() or 'calc' in line.lower()):
                print(f"  - {line.strip()}")

