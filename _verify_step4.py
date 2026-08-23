import os, pathlib, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from attendance.models import Shift

shift_fields = [f.name for f in Shift._meta.get_fields()]
print("=== Shift Model Fields in DB ===")
print(f"early_checkout_allowed: {'[OK] Exists' if 'early_checkout_allowed' in shift_fields else '[X] Missing'}")
print(f"early_checkout_minutes: {'[OK] Exists' if 'early_checkout_minutes' in shift_fields else '[X] Missing'}")
print(f"late_checkout_allowed:  {'[OK] Exists' if 'late_checkout_allowed' in shift_fields else '[X] Missing'}")
print(f"late_checkout_minutes:  {'[OK] Exists' if 'late_checkout_minutes' in shift_fields else '[X] Missing'}")

api_content = pathlib.Path('attendance/api_mobile.py').read_text(encoding='utf-8')
print("\n=== API Logic Check ===")
print(f"Flex Logic Present: {'[OK]' if 'raw_early <= allowed_early_grace' in api_content else '[X]'}")
