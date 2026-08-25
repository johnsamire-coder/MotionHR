from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendance.models import Shift, EmployeeShift
from accounts.models import FCMDeviceToken, EmployeeNotification
from firebase_admin import messaging

class Command(BaseCommand):
    help = 'Send push notifications 15 minutes before shift starts'

    def handle(self, *args, **kwargs):
        now = timezone.localtime()
        target_time = (now + timedelta(minutes=15)).time()
        
        upcoming_shifts = Shift.objects.filter(
            start_time__hour=target_time.hour,
            start_time__minute=target_time.minute
        )

        if not upcoming_shifts.exists():
            return

        for shift in upcoming_shifts:
            active_emp_shifts = EmployeeShift.objects.filter(
                shift=shift, start_date__lte=now.date()
            ).exclude(end_date__lt=now.date()).select_related('employee', 'employee__user')

            for emp_shift in active_emp_shifts:
                user = emp_shift.employee.user
                title = "تذكير بموعد الشيفت ⏰"
                body = f"شيفت ({shift.name}) سيبدأ خلال 15 دقيقة. استعد ليوم عمل رائع!"

                EmployeeNotification.objects.create(user=user, title=title, message=body, notification_type='system')

                tokens = FCMDeviceToken.objects.filter(user=user).values_list('token', flat=True)
                if tokens:
                    try:
                        message = messaging.MulticastMessage(
                            notification=messaging.Notification(title=title, body=body),
                            tokens=list(tokens),
                        )
                        messaging.send_multicast(message)
                    except Exception as e:
                        self.stderr.write(f"FCM Error: {e}")

        self.stdout.write(self.style.SUCCESS(f'Notified employees for shifts at {target_time}'))
