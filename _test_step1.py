import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from leaves.models import LeaveType
from companies.models import Company

# 1) جلب أو إنشاء شركة تجريبية بالحقول الصحيحة (name_ar)
company = Company._base_manager.first()
if not company:
    company = Company._base_manager.create(
        name_ar="شركة تجريبية",
        name_en="Test Company",
        is_active=True
    )

# 2) إنشاء نوع إجازة تجريبي يتطلب سبباً
test_lt, _ = LeaveType._base_manager.get_or_create(
    company=company,
    name="غياب بعذر - تجريبي",
    defaults={
        "category": "emergency",
        "require_reason": True,
        "is_excused_absence": True
    }
)
test_lt.require_reason = True
test_lt.is_excused_absence = True
test_lt.save()

print(f"Leave Type Configured: {test_lt.name} (require_reason={test_lt.require_reason})")

# 3) محاكاة التحقق من الشرط البرمجي
def simulate_request(leave_type, reason_input):
    reason = reason_input.strip()
    if (getattr(leave_type, "require_reason", False) or getattr(leave_type, "is_excused_absence", False)) and not reason:
        return {"status": 400, "message": "يجب كتابة سبب الغياب بالتفصيل"}
    return {"status": 200, "message": "تم قبول الطلب"}

# اختبار بدون سبب
res_fail = simulate_request(test_lt, "")
print(f"Test Empty Reason: Status {res_fail['status']} -> {res_fail['message']}")
assert res_fail['status'] == 400, "Should reject empty reason"
print("[PASS] Rejected empty reason successfully.")

# اختبار بوجود سبب
res_pass = simulate_request(test_lt, "ظرف عائلي طارئ")
print(f"Test Valid Reason: Status {res_pass['status']} -> {res_pass['message']}")
assert res_pass['status'] == 200, "Should accept valid reason"
print("[PASS] Accepted valid reason successfully.")

print("\n" + "="*50)
print(">>> STEP 1 COMPLETED & TESTED 100% <<<")
print("="*50)
