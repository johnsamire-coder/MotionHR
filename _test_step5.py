import os, django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from companies.models import Company, Branch, Department
from employees.models import Employee, JobTitle
from leaves.models import LeavePolicy, LeavePolicyTier, LeaveType
from leaves.services_leave_accrual import calculate_employee_leave_entitlement, refresh_employee_leave_balances

# 1. إعداد الشركة والفرع والقسم
company = Company._base_manager.first()
if not company:
    company = Company._base_manager.create(name_ar="شركة تجريبية", is_active=True)

branch, _ = Branch._base_manager.get_or_create(company=company, name_ar="الفرع الرئيسي", defaults={"is_active": True})
dept, _ = Department._base_manager.get_or_create(company=company, branch=branch, name_ar="قسم الموارد البشرية", defaults={"is_active": True})
job_title, _ = JobTitle._base_manager.get_or_create(company=company, department=dept, name_ar="أخصائي HR", defaults={"is_active": True})

# 2. إعداد نوع إجازة سنوية
leave_type, _ = LeaveType._base_manager.get_or_create(
    company=company,
    name="إجازة سنوية",
    defaults={"category": "annual", "days_allowed": 21}
)

# 3. إعداد سياسة الإجازات المتدرجة للعميل
policy, _ = LeavePolicy._base_manager.get_or_create(
    company=company,
    name="سياسة الإجازات المتدرجة (نظام التعيين)",
    defaults={
        "effective_from": date(2026, 1, 1),
        "status": "active"
    }
)
policy.status = "active"
policy.save()

# تنظيف وتكوين الشرائح (0-3 شهور: 0 / 4-6 شهور: 6 / 7+ شهور: 21)
LeavePolicyTier._base_manager.filter(policy=policy).delete()

tier1 = LeavePolicyTier._base_manager.create(
    policy=policy,
    from_months=0,
    to_months=3,
    annual_entitlement_days=Decimal('0.0'),
    description="فترة الاختبار (أول 3 شهور)"
)

tier2 = LeavePolicyTier._base_manager.create(
    policy=policy,
    from_months=4,
    to_months=6,
    annual_entitlement_days=Decimal('6.0'),
    description="من الشهر 4 إلى 6"
)

tier3 = LeavePolicyTier._base_manager.create(
    policy=policy,
    from_months=7,
    to_months=None,  # بلا حد أقصى
    annual_entitlement_days=Decimal('21.0'),
    description="بعد 6 شهور (الرصيد السنوي الكامل)"
)

print(f"Leave Policy Configured with 3 Tiers (0-3m: 0d / 4-6m: 6d / 7m+: 21d)")

# إنشاء موظف معين في 2026-01-01
emp, _ = Employee._base_manager.get_or_create(
    company=company,
    employee_code="EMP_LEAVE_TIER",
    defaults={
        "first_name_ar": "سارة",
        "last_name_ar": "محمد",
        "national_id": "29803101234567",
        "branch": branch,
        "department": dept,
        "job_title": job_title,
        "birth_date": date(1998, 3, 10),
        "hire_date": date(2026, 1, 1),
        "status": "active"
    }
)
emp.hire_date = date(2026, 1, 1)
emp.save()

# TEST 1: فحص الرصيد في شهر فبراير 2026 (مدة الخدمة = 1 شهر -> شريحة 0-3 شهور = 0 يوم)
date_test_1 = date(2026, 2, 15)
bal1 = calculate_employee_leave_entitlement(emp, leave_type, as_of_date=date_test_1)
print(f"\nTEST 1 (Service Tenure = 1 Month): Entitlement = {bal1} Days (Expected 0.0)")
assert bal1 == Decimal('0.0'), f"Expected 0.0, got {bal1}"
print("[PASS] 0 days entitlement in probation tier.")

# TEST 2: فحص الرصيد في شهر مايو 2026 (مدة الخدمة = 4 شهور -> شريحة 4-6 شهور = 6 أيام)
date_test_2 = date(2026, 5, 15)
bal2 = calculate_employee_leave_entitlement(emp, leave_type, as_of_date=date_test_2)
print(f"\nTEST 2 (Service Tenure = 4 Months): Entitlement = {bal2} Days (Expected 6.0)")
assert bal2 == Decimal('6.0'), f"Expected 6.0, got {bal2}"
print("[PASS] 6 days entitlement in 4-6 months tier.")

# TEST 3: فحص الرصيد في شهر أغسطس 2026 (مدة الخدمة = 7 شهور -> بعد 6 شهور = 21 يوم)
date_test_3 = date(2026, 8, 15)
bal3 = calculate_employee_leave_entitlement(emp, leave_type, as_of_date=date_test_3)
print(f"\nTEST 3 (Service Tenure = 7 Months): Entitlement = {bal3} Days (Expected 21.0)")
assert bal3 == Decimal('21.0'), f"Expected 21.0, got {bal3}"
print("[PASS] Full 21 days entitlement after 6 months.")

# TEST 4: تحديث جدول LeaveBalance الفعلي للموظف
refreshed = refresh_employee_leave_balances(emp, as_of_date=date_test_3)
print(f"\nTEST 4 (LeaveBalance Table Auto-Sync): {refreshed}")
assert refreshed.get('إجازة سنوية') == 21.0, "LeaveBalance sync failed"
print("[PASS] LeaveBalance table refreshed successfully.")

print("\n" + "="*50)
print(">>> STEP 5 COMPLETED & TESTED 100% <<<")
print("="*50)
