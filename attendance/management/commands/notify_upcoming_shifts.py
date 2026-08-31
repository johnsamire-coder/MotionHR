from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendance.models import Shift, EmployeeShift
from accounts.fcm_service import send_notification_to_user

class Command(BaseCommand):
    help = 'Send push notifications 15 minutes before shift starts'

    def handle(self, *args, **kwargs):
        now = timezone.localtime()
        target_time = (now + timedelta(minutes=15)).time()

        upcoming_shifts = Shift._base_manager.filter(
            start_time__hour=target_time.hour,
            start_time__minute=target_time.minute
        )

        if not upcoming_shifts.exists():
            return

        for shift in upcoming_shifts:
            active_emp_shifts = EmployeeShift._base_manager.filter(
                shift=shift, start_date__lte=now.date()
            ).exclude(end_date__lt=now.date()).select_related('employee', 'employee__user')

            for emp_shift in active_emp_shifts:
                user = getattr(emp_shift.employee, 'user', None)
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
