"""
Management command لتشغيل التذكيرات.
الاستخدام:
  python manage.py send_reminders --type checkin
  python manage.py send_reminders --type checkout
  python manage.py send_reminders --type pending
  python manage.py send_reminders --type charter
  python manage.py send_reminders --type all
"""
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send automated reminders via FCM"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            default="all",
            choices=["all", "checkin", "checkout", "pending", "charter", "documents"],
            help="Type of reminder to send",
        )

    def handle(self, *args, **options):
        reminder_type = options["type"]
        self.stdout.write(f"[MotionHR] Running reminders: type={reminder_type}")

        try:
            from attendance.reminders import run_all_reminders
            run_all_reminders(reminder_type=reminder_type)
            self.stdout.write(self.style.SUCCESS(f"[MotionHR] Reminders done: {reminder_type}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"[MotionHR] Error: {e}"))
            logger.error(f"send_reminders command error: {e}")
            raise
