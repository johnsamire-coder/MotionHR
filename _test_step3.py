import os, django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from companies.models import Company
from attendance.models import AttendancePolicy, AbsenceRule
from attendance.payroll_rules import _apply_absence_rule

# 1. إعداد الشركة والسياسة
company = Company._base_manager.first()
if not company:
    company = Company._base_manager.create(name_ar="شركة تجريبية", is_active=True)

policy, _ = AttendancePolicy._base_manager.get_or_create(
    company=company,
    name="سياسة الحضور الرئيسية",
    defaults={
        "effective_from": date(2026, 1, 1),
        "status": "active"
    }
)

# حذف القواعد القديمة للتجربة النظيفة
AbsenceRule._base_manager.filter(policy=policy).delete()

daily_salary = 200.0  # الراتب اليومي للموظف 200 جنيه

print("="*50)
print("RUNNING ABSENCE RULES DEDUCTION TESTS")
print("="*50)

# TEST 1: قاعدة خصم مضاعف (يوم الغياب بخصم 2 يوم عمل = 2.0x)
rule1 = AbsenceRule._base_manager.create(
    policy=policy,
    absence_type='unexcused',
    deduction_type='day_fraction',
    deduction_value=Decimal('2.0'),  # يومين خصم
    display_order=1
)

amount1, days1 = _apply_absence_rule(policy, absent_days=1, daily_salary=daily_salary)
print(f"\nTEST 1 (1 Day Absent with 2.0x Rule):")
print(f"  Deduction Amount: {amount1} EGP (Expected 400.0)")
print(f"  Deducted Days: {days1} Days (Expected 2.0)")
assert amount1 == 400.0, f"Expected 400.0, got {amount1}"
assert days1 == 2.0, f"Expected 2.0 days, got {days1}"
print("[PASS] Double day deduction applied successfully.")

# TEST 2: غياب يومين بخصم 1.5 يوم لكل غياب (إجمالي 3 أيام خصم)
rule1.deduction_value = Decimal('1.5')
rule1.save()

amount2, days2 = _apply_absence_rule(policy, absent_days=2, daily_salary=daily_salary)
print(f"\nTEST 2 (2 Days Absent with 1.5x Rule):")
print(f"  Deduction Amount: {amount2} EGP (Expected 600.0)")
print(f"  Deducted Days: {days2} Days (Expected 3.0)")
assert amount2 == 600.0, f"Expected 600.0, got {amount2}"
assert days2 == 3.0, f"Expected 3.0 days, got {days2}"
print("[PASS] 1.5x deduction applied successfully.")

# TEST 3: قاعدة غياب متتالي (لو غاب 3 أيام متتالية الخصم يكون 3.0x لكل يوم)
rule_consecutive = AbsenceRule._base_manager.create(
    policy=policy,
    absence_type='consecutive',
    consecutive_days=3,
    deduction_type='day_fraction',
    deduction_value=Decimal('3.0'),  # 3 أيام خصم لكل غياب
    display_order=0
)

amount3, days3 = _apply_absence_rule(policy, absent_days=3, daily_salary=daily_salary, consecutive_days=3)
print(f"\nTEST 3 (Consecutive Absence with 3.0x Rule):")
print(f"  Deduction Amount: {amount3} EGP (Expected 1800.0)")
print(f"  Deducted Days: {days3} Days (Expected 9.0)")
assert amount3 == 1800.0, f"Expected 1800.0, got {amount3}"
assert days3 == 9.0, f"Expected 9.0 days, got {days3}"
print("[PASS] Consecutive absence rule prioritized and applied successfully.")

print("\n" + "="*50)
print(">>> STEP 3 COMPLETED & TESTED 100% <<<")
print("="*50)
