from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from employees.models import Employee
from attendance.models import Attendance, AttendanceSession, DailyAttendanceSummary
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "إغلاق سجلات الحضور المفتوحة تلقائيًا (Auto Check-out) للأيام السابقة"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="عدد الأيام اللي نراجعها لورا (الافتراضي 7)",
        )
        parser.add_argument(
            "--employee-id",
            type=int,
            help="معالجة موظف واحد فقط (اختياري)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="معاينة فقط بدون حفظ أي تغييرات",
        )

    def _resolve_shift(self, attendance):
        """
        يجيب الشيفت الفعلي لليوم:
        1) attendance.shift لو متسجل
        2) get_effective_shift(employee, date)
        """
        if getattr(attendance, "shift", None):
            return attendance.shift

        try:
            from attendance.api_shifts import get_effective_shift
            shift, _source = get_effective_shift(attendance.employee, attendance.date)
            return shift
        except Exception as e:
            logger.warning(f"resolve shift failed for attendance #{attendance.id}: {e}")
            return None

    def _build_checkout_dt(self, attendance, shift):
        """
        يبني وقت الانصراف التلقائي:
        - من نهاية الشيفت لو موجود
        - وإلا fallback = check_in + عدد ساعات الشيفت / الموظف / 8 ساعات
        """
        tz = timezone.get_current_timezone()
        check_in = attendance.check_in_time

        if not check_in:
            return None

        # لو فيه شيفت وله end_time
        if shift and getattr(shift, "end_time", None):
            end_dt = datetime.combine(attendance.date, shift.end_time)

            shift_start = getattr(shift, "start_time", None)
            if getattr(shift, "crosses_midnight", False) or (
                shift_start and shift.end_time <= shift_start
            ):
                end_dt += timedelta(days=1)

            checkout_dt = timezone.make_aware(end_dt, tz)

            # حماية: لو نهاية الشيفت طلعت قبل/عند الحضور لأي سبب
            if checkout_dt <= check_in:
                fallback_hours = float(
                    getattr(shift, "work_hours", 0)
                    or getattr(attendance.employee, "required_daily_hours", 0)
                    or 8
                )
                return check_in + timedelta(hours=fallback_hours)

            return checkout_dt

        # fallback لو مفيش شيفت
        fallback_hours = float(
            getattr(attendance.employee, "required_daily_hours", 0) or 8
        )
        return check_in + timedelta(hours=fallback_hours)

    def handle(self, *args, **options):
        days_to_sync = options["days"]
        emp_id = options.get("employee_id")
        dry_run = options.get("dry_run", False)

        if days_to_sync <= 0:
            self.stdout.write(self.style.ERROR("[MotionHR] --days لازم يكون أكبر من صفر"))
            return

        today = timezone.localdate()
        start_date = today - timedelta(days=days_to_sync)
        end_date = today - timedelta(days=1)

        self.stdout.write(
            f"[MotionHR] Auto check-out scan from {start_date} to {end_date} | dry_run={dry_run}"
        )

        attendances = Attendance._base_manager.filter(
            check_in_time__isnull=False,
            check_out_time__isnull=True,
            date__gte=start_date,
            date__lte=end_date,
        ).select_related("employee", "shift", "employee__branch", "employee__department")

        if emp_id:
            attendances = attendances.filter(employee_id=emp_id)

        total = attendances.count()
        updated = 0
        skipped = 0

        for idx, attendance in enumerate(attendances, start=1):
            employee = attendance.employee
            shift = self._resolve_shift(attendance)
            checkout_dt = self._build_checkout_dt(attendance, shift)

            if not checkout_dt:
                skipped += 1
                logger.warning(f"Skipping attendance #{attendance.id}: no checkout_dt")
                continue

            auto_note = "auto checkout - الموظف لم يسجل انصراف"

            self.stdout.write(
                f"[{idx}/{total}] attendance #{attendance.id} | emp={employee.id} | date={attendance.date} | checkout={checkout_dt}"
            )

            if dry_run:
                updated += 1
                continue

            try:
                with transaction.atomic():
                    # اقفل أي session مفتوحة
                    open_sessions = AttendanceSession._base_manager.filter(
                        attendance=attendance,
                        employee=employee,
                        check_out_time__isnull=True,
                    ).order_by("session_number")

                    open_count = open_sessions.count()

                    if open_count:
                        for s in open_sessions:
                            s.check_out_time = checkout_dt
                            s.notes = ((s.notes or "").strip() + " | " + auto_note).strip(" |")
                            s.calculate_worked_minutes()
                            s.save(update_fields=["check_out_time", "notes", "worked_minutes"])
                    else:
                        # fallback session لو السجل قديم ومفيهوش sessions
                        fallback_session = AttendanceSession._base_manager.create(
                            company=attendance.company,
                            attendance=attendance,
                            employee=employee,
                            session_number=1,
                            check_in_time=attendance.check_in_time,
                            check_out_time=checkout_dt,
                            check_in_latitude=attendance.check_in_latitude,
                            check_in_longitude=attendance.check_in_longitude,
                            check_out_latitude=attendance.check_out_latitude,
                            check_out_longitude=attendance.check_out_longitude,
                            is_partial=False,
                            notes=auto_note,
                        )
                        fallback_session.calculate_worked_minutes()
                        fallback_session.save(update_fields=["worked_minutes"])

                    attendance.check_out_time = checkout_dt
                    attendance.check_out_notes = (
                        ((attendance.check_out_notes or "").strip() + " | " + auto_note).strip(" |")
                    )
                    attendance.calculate_work_hours()
                    attendance.save(update_fields=["check_out_time", "check_out_notes", "work_hours"])

                    # حدث الملخص اليومي
                    DailyAttendanceSummary.compute_for_day(employee, attendance.date)

                updated += 1

            except Exception as e:
                skipped += 1
                logger.exception(f"auto_checkout failed for attendance #{attendance.id}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"[MotionHR] Done | total={total} | updated={updated} | skipped={skipped} | dry_run={dry_run}"
            )
        )
