from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from employees.models import Employee

from .models import LeaveBalance, LeaveType


def _get_entitlement_days(company, employee, leave_type, year):
    """
    احسب رصيد الإجازة للموظف من السياسة النشطة
    لو مفيش سياسة نشطة، ارجع للقيمة الثابتة في نوع الإجازة
    """
    try:
        from leaves.models import LeavePolicy, LeavePolicyTypeRule

        policy = LeavePolicy._base_manager.filter(
            company=company,
            status="active",
        ).order_by("-effective_from").first()

        if not policy:
            return float(leave_type.days_allowed)

        # احسب مدة خدمة الموظف بالشهور
        hire_date = getattr(employee, "hire_date", None)
        if not hire_date:
            return float(leave_type.days_allowed)

        from dateutil.relativedelta import relativedelta
        from datetime import date
        today = date(year, 1, 1)
        diff = relativedelta(today, hire_date)
        service_months = diff.years * 12 + diff.months

        # جيب الشريحة المناسبة
        tier = policy.tiers.filter(
            from_months__lte=service_months,
        ).filter(
            __import__("django.db.models", fromlist=["Q"]).Q(to_months__isnull=True) |
            __import__("django.db.models", fromlist=["Q"]).Q(to_months__gte=service_months)
        ).order_by("-from_months").first()

        if not tier:
            return float(leave_type.days_allowed)

        # جيب قاعدة نوع الإجازة دي في السياسة
        try:
            rule = LeavePolicyTypeRule.objects.get(
                policy=policy,
                leave_type=leave_type,
                enabled=True,
            )
            if rule.entitlement_mode == "fixed_days":
                return float(rule.fixed_days)
            elif rule.entitlement_mode == "from_service_tier":
                return float(tier.annual_entitlement_days)
            elif rule.entitlement_mode == "subset_of_parent":
                return float(rule.subset_limit_days)
        except LeavePolicyTypeRule.DoesNotExist:
            pass

        return float(tier.annual_entitlement_days)

    except Exception:
        return float(leave_type.days_allowed)


@receiver(post_save, sender=Employee)
def create_employee_leave_balances(sender, instance, created, **kwargs):
    if not created:
        return

    if not getattr(instance, "company_id", None):
        return

    year = timezone.now().year
    leave_types = LeaveType._base_manager.filter(
        company=instance.company,
        is_active=True,
    )

    for leave_type in leave_types:
        days = _get_entitlement_days(instance.company, instance, leave_type, year)
        LeaveBalance._base_manager.get_or_create(
            company=instance.company,
            employee=instance,
            leave_type=leave_type,
            year=year,
            defaults={
                "total_days": days,
                "used_days": 0,
                "pending_days": 0,
            },
        )
