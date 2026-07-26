from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from employees.models import Employee

from .models import LeaveBalance, LeaveType


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
        LeaveBalance._base_manager.get_or_create(
            company=instance.company,
            employee=instance,
            leave_type=leave_type,
            year=year,
            defaults={
                "total_days": leave_type.days_allowed,
                "used_days": 0,
                "pending_days": 0,
            },
        )
