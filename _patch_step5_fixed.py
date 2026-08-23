import pathlib, re, textwrap

BASE = pathlib.Path('.')

# 1) إنشاء leaves/services_leave_accrual.py
service_code = textwrap.dedent("""
from django.utils import timezone
from django.db.models import Q
from dateutil.relativedelta import relativedelta
from datetime import date
from decimal import Decimal

from leaves.models import LeavePolicy, LeavePolicyTier, LeavePolicyTypeRule, LeaveBalance, LeaveType


def calculate_employee_leave_entitlement(employee, leave_type, as_of_date=None):
    \"\"\"
    حساب رصيد الإجازات المتدرج حسب مدة الخدمة الفعلية بالأشهر
    \"\"\"
    if not employee or not getattr(employee, 'company', None):
        return Decimal(str(getattr(leave_type, 'days_allowed', 0) or 0))

    if not getattr(employee, 'hire_date', None):
        return Decimal(str(getattr(leave_type, 'days_allowed', 0) or 0))

    target_date = as_of_date or timezone.localdate()
    hire_date = employee.hire_date

    # حساب مدة الخدمة بالأشهر حتى التاريخ المطلوب
    diff = relativedelta(target_date, hire_date)
    service_months = max(0, diff.years * 12 + diff.months)

    policy = LeavePolicy._base_manager.filter(
        company=employee.company,
        status="active"
    ).order_by("-effective_from").first()

    if not policy:
        return Decimal(str(getattr(leave_type, 'days_allowed', 0) or 0))

    # البحث عن الشريحة المتوافقة مع مدة الخدمة
    tier = policy.tiers.filter(
        from_months__lte=service_months
    ).filter(
        Q(to_months__isnull=True) | Q(to_months__gte=service_months)
    ).order_by("-from_months").first()

    if not tier:
        return Decimal(str(getattr(leave_type, 'days_allowed', 0) or 0))

    # فحص نوع الإجازة
    rule = LeavePolicyTypeRule._base_manager.filter(
        policy=policy,
        leave_type=leave_type,
        enabled=True
    ).first()

    if rule:
        if rule.entitlement_mode == "fixed_days":
            return Decimal(str(rule.fixed_days or 0))
        elif rule.entitlement_mode == "from_service_tier":
            return Decimal(str(tier.annual_entitlement_days or 0))
        elif rule.entitlement_mode == "subset_of_parent":
            return Decimal(str(rule.subset_limit_days or 0))

    return Decimal(str(tier.annual_entitlement_days or 0))


def refresh_employee_leave_balances(employee, as_of_date=None):
    \"\"\"
    تحديث رصيد الإجازات في جدول LeaveBalance لكل أنواع الإجازات النشطة للموظف
    مع الحفاظ على الأيام المستخدمة والمعلقة
    \"\"\"
    target_date = as_of_date or timezone.localdate()
    year = target_date.year

    leave_types = LeaveType._base_manager.filter(
        company=employee.company,
        is_active=True
    )

    results = {}
    for lt in leave_types:
        entitlement = calculate_employee_leave_entitlement(employee, lt, as_of_date=target_date)
        
        balance, created = LeaveBalance._base_manager.get_or_create(
            company=employee.company,
            employee=employee,
            leave_type=lt,
            year=year,
            defaults={
                "total_days": entitlement,
                "used_days": Decimal("0.0"),
                "pending_days": Decimal("0.0"),
            }
        )
        if not created:
            balance.total_days = entitlement
            balance.save()
        
        results[lt.name] = float(balance.total_days)

    return results
""").strip()

(BASE / 'leaves' / 'services_leave_accrual.py').write_text(service_code, encoding='utf-8')
print("[OK] Created leaves/services_leave_accrual.py")

# 2) تحديث leaves/signals.py
signals_path = BASE / 'leaves' / 'signals.py'
signals_content = signals_path.read_text(encoding='utf-8')

new_signal_func = """def _get_entitlement_days(company, employee, leave_type, year):
    \"\"\"احسب رصيد الإجازة للموظف من السياسة المتدرجة النشطة\"\"\"
    try:
        from leaves.services_leave_accrual import calculate_employee_leave_entitlement
        from datetime import date
        as_of = date(year, 1, 1) if year != timezone.localdate().year else timezone.localdate()
        return float(calculate_employee_leave_entitlement(employee, leave_type, as_of_date=as_of))
    except Exception:
        return float(getattr(leave_type, 'days_allowed', 0) or 0)
"""

pattern = r'def _get_entitlement_days\(.*?\):.*?(?=\n@receiver|\Z)'
signals_content = re.sub(pattern, new_signal_func + '\n\n', signals_content, count=1, flags=re.DOTALL)
signals_path.write_text(signals_content, encoding='utf-8')
print("[OK] Updated leaves/signals.py with pro-rated accrual engine.")

