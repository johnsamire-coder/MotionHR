import pathlib, re

BASE = pathlib.Path('.')

print("=== 1. Checking Attendance Model in attendance/models.py ===")
models_content = (BASE / 'attendance' / 'models.py').read_text(encoding='utf-8')
match = re.search(r'class Attendance\(TenantModel\):.*?(?=\nclass |\Z)', models_content, re.DOTALL)
if match:
    snippet = match.group(0).splitlines()[:55]
    print("\n".join(snippet))

print("\n=== 2. Checking EmployeeMovement in employees/models.py ===")
emp_models = (BASE / 'employees' / 'models.py').read_text(encoding='utf-8')
print("EmployeeMovement exists:", "class EmployeeMovement" in emp_models)

print("\n=== 3. Checking existing Attendance Adjustment endpoints ===")
urls_content = (BASE / 'attendance' / 'urls.py').read_text(encoding='utf-8')
print("adjust endpoints in urls.py:", [l for l in urls_content.splitlines() if 'adjust' in l or 'override' in l])

