import pathlib, re

BASE = pathlib.Path('.')

print("=== 1. Checking Shift Model in attendance/models.py ===")
models_content = (BASE / 'attendance' / 'models.py').read_text(encoding='utf-8')
match = re.search(r'class Shift\(TenantModel\):.*?(?=\nclass |\Z)', models_content, re.DOTALL)
if match:
    snippet = match.group(0).splitlines()[:55]
    print('\n'.join(snippet))

print("\n=== 2. Checking Early Leave Calculation in attendance/api_mobile.py ===")
mobile_content = (BASE / 'attendance' / 'api_mobile.py').read_text(encoding='utf-8')
for line_no, line in enumerate(mobile_content.splitlines()):
    if 'early_leave' in line or 'grace_early_leave' in line:
        print(f"  Line {line_no+1}: {line.strip()[:100]}")

print("\n=== 3. Checking Shift APIs in attendance/api_shifts.py ===")
shifts_api = BASE / 'attendance' / 'api_shifts.py'
if shifts_api.exists():
    text = shifts_api.read_text(encoding='utf-8')
    print("api_shifts.py exists with", len(text.splitlines()), "lines")
else:
    print("attendance/api_shifts.py NOT FOUND")

