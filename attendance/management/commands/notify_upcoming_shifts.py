from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.fcm_service import send_notification_to_user

class Command(BaseCommand):
    help = 'Send push notifications 15 minutes before shift starts'

    def handle(self, *args, **kwargs):
        from attendance.models import Employee
        from attendance.api_mobile import get_shift_periods
        from attendance.api_shifts import get_effective_shift
        from attendance.reminders import (
            _employee_has_approved_leave,
            _shift_reminder_is_workday,
        )

        now = timezone.localtime()
        target_time = (now + timedelta(minutes=15)).replace(second=0, microsecond=0)
        today = now.date()
        employees = Employee._base_manager.filter(
            status='active'
        ).select_related('user', 'company')
        notified = 0

        for employee in employees:
            user = getattr(employee, 'user', None)
            if not user:
                continue

            shift, shift_source = get_effective_shift(employee, today)
            if not _shift_reminder_is_workday(shift, shift_source, today):
                continue
            if _employee_has_approved_leave(employee, today):
                continue

            periods = get_shift_periods(shift, today)
            shift_start = periods[0].get('start') if periods else None
            if not shift_start:
                continue
            if shift_start.replace(second=0, microsecond=0) != target_time:
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
                data={'type': 'reminder_shift', 'shift_id': str(shift.id)},
            )
            notified += 1

        self.stdout.write(
            self.style.SUCCESS(f'Notified {notified} employees for shifts at {target_time}')
        )
