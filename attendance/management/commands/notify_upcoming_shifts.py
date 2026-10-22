from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendance.models import Shift, EmployeeShift, DailyAssignment, ShiftOverride
from leaves.models import LeaveRequest
from accounts.fcm_service import send_notification_to_user

class Command(BaseCommand):
    help = 'Send push notifications 15 minutes before shift starts'

    def handle(self, *args, **kwargs):
        now = timezone.localtime()
        target_time = (now + timedelta(minutes=15)).time()

        upcoming_shifts = Shift._base_manager.filter(
            is_active=True,
            start_time__hour=target_time.hour,
            start_time__minute=target_time.minute
        )

        if not upcoming_shifts.exists():
            return

        for shift in upcoming_shifts:
            active_emp_shifts = EmployeeShift._base_manager.filter(
                shift=shift, is_active=True, start_date__lte=now.date()
            ).exclude(end_date__lt=now.date()).select_related('employee', 'employee__user')

            for emp_shift in active_emp_shifts:
                employee = emp_shift.employee
                daily = DailyAssignment._base_manager.filter(
                    employee=employee, date=now.date()
                ).first()
                override = ShiftOverride._base_manager.filter(
                    employee=employee, override_date=now.date()
                ).first()

                if daily and not daily.is_working_day:
                    continue
                if override:
                    if override.shift_id != shift.id:
                        continue
                elif daily:
                    if daily.shift_id and daily.shift_id != shift.id:
                        continue
                    if daily.start_time and daily.start_time != shift.start_time:
                        continue
                elif not shift.is_work_day(now.date()):
                    from attendance.api_shifts import get_effective_shift
                    effective, source = get_effective_shift(employee, now.date())
                    rotation_today = (
                        effective and effective.id == shift.id
                        and source and source.startswith("rotation_")
                    )
                    if not rotation_today:
                        continue

                approved_leave = LeaveRequest._base_manager.filter(
                    employee=employee,
                    status="approved",
                    start_date__lte=now.date(),
                    end_date__gte=now.date(),
                ).exists()
                if approved_leave:
                    continue

                user = getattr(employee, 'user', None)
                if not user:
                    continue
                title_ar = 'تذكير بموعد الشيفت ⏰'
                body_ar = f'شيفت ({shift.name}) سيبدأ خلال 15 دقيقة. استعد ليوم عمل رائع!'
                title_en = 'Shift Reminder ⏰'
                body_en = f'Shift ({shift.name}) starts in 15 minutes. Have a great work day!'

                send_notification_to_user(
                    user=user,
                    title=title_ar,
                    body=body_ar,
                    title_en=title_en,
                    body_en=body_en,
                    data={'type': 'reminder_shift', 'shift_id': str(shift.id)}
                )

        self.stdout.write(self.style.SUCCESS(f'Notified employees for shifts at {target_time}'))
