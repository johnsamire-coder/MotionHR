import os, pathlib, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from leaves.models import LeaveType

fields = [f.name for f in LeaveType._meta.get_fields()]
print("=== LeaveType Fields in DB ===")
print(f"require_reason: {'[OK] Exists' if 'require_reason' in fields else '[X] Missing'}")
print(f"is_excused_absence: {'[OK] Exists' if 'is_excused_absence' in fields else '[X] Missing'}")

api_content = pathlib.Path('attendance/api_mobile_requests.py').read_text(encoding='utf-8')
print("\n=== API Code Check ===")
print(f"Validation Code: {'[OK] Present' if 'يجب كتابة سبب الغياب بالتفصيل' in api_content else '[X] Missing'}")
print(f"API Response Fields: {'[OK] Present' if 'require_reason' in api_content else '[X] Missing'}")
