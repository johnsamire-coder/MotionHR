from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from employees.models import Employee

from .models import LeaveBalance, LeaveType


def _get_entitlement_days(company, employee, leave_type, year):
    """احسب رصيد الإجازة للموظف من السياسة المتدرجة النشطة"""
    try:
        from leaves.services_leave_accrual import calculate_employee_leave_entitlement
        from datetime import date
        as_of = date(year, 1, 1) if year != timezone.localdate().year else timezone.localdate()
        return float(calculate_employee_leave_entitlement(employee, leave_type, as_of_date=as_of))
    except Exception:
        return float(getattr(leave_type, 'days_allowed', 0) or 0)



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
