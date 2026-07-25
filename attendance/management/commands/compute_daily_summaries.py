from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from employees.models import Employee
from attendance.models import DailyAttendanceSummary
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "تحديث ملخصات الحضور اليومية لفترة زمنية (عامل المراجعة)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="عدد الأيام اللي هنراجعها لورا (الافتراضي 30)",
        )
        parser.add_argument(
            "--employee-id",
            type=int,
            help="تحديث موظف واحد فقط (اختياري)",
        )

    def handle(self, *args, **options):
        days_to_sync = options["days"]
        emp_id = options.get("employee_id")

        if days_to_sync <= 0:
            self.stdout.write(self.style.ERROR("[MotionHR] --days لازم يكون أكبر من صفر"))
            return

        today = timezone.localdate()
        end_date = today - timedelta(days=1)  # لحد امبارح فقط
        start_date = today - timedelta(days=days_to_sync)

        self.stdout.write(f"[MotionHR] Starting sync from {start_date} to {end_date}...")

        # نجيب الموظفين
        if emp_id:
            employees = Employee._base_manager.filter(id=emp_id)
        else:
            employees = Employee._base_manager.filter(status='active')

        total_count = employees.count()
        processed = 0

        for emp in employees:
            processed += 1
            if processed % 10 == 0 or processed == total_count:
                self.stdout.write(f"Processing employee {processed}/{total_count}: {emp}")
            
            current_date = start_date
            while current_date <= end_date:
                try:
                    # نستخدم الميثود اللي عملناها في الموديل
                    DailyAttendanceSummary.compute_for_day(emp, current_date)
                except Exception as e:
                    logger.error(f"Error computing summary for {emp} on {current_date}: {e}")
                
                current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"[MotionHR] Successfully synced {total_count} employees for {days_to_sync} days."))
