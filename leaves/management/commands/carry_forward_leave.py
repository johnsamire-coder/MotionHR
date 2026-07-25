from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "ترحيل رصيد الإجازات للسنة الجديدة"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="السنة المصدر (الافتراضي: السنة الحالية - 1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="معاينة فقط بدون حفظ",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        today = timezone.localdate()

        from_year = options["year"] or (today.year - 1)
        to_year = from_year + 1

        self.stdout.write(
            f"[MotionHR] Carry Forward: {from_year} → {to_year} | dry_run={dry_run}"
        )

        from leaves.models import LeaveType, LeaveBalance
        from employees.models import Employee

        types_with_carry = LeaveType._base_manager.filter(
            carry_forward=True,
            is_active=True,
        ).select_related('company')

        total_processed = 0
        total_created = 0
        total_skipped = 0

        for lt in types_with_carry:
            company = lt.company
            max_carry = Decimal(str(lt.max_carry_days or 0))
            days_allowed = Decimal(str(lt.days_allowed or 0))

            balances = LeaveBalance._base_manager.filter(
                company=company,
                leave_type=lt,
                year=from_year,
            ).select_related('employee')

            for bal in balances:
                total_processed += 1
                employee = bal.employee

                remaining = bal.remaining_days
                if remaining <= 0:
                    total_skipped += 1
                    continue

                carry_days = min(remaining, max_carry) if max_carry > 0 else remaining
                if carry_days <= 0:
                    total_skipped += 1
                    continue

                new_total = days_allowed + carry_days

                self.stdout.write(
                    f"  [{employee}] {lt.name}: "
                    f"remaining={remaining} carry={carry_days} "
                    f"new_total={new_total}"
                )

                if not dry_run:
                    new_bal, created = LeaveBalance._base_manager.get_or_create(
                        company=company,
                        employee=employee,
                        leave_type=lt,
                        year=to_year,
                        defaults={
                            'total_days': new_total,
                            'used_days': Decimal('0'),
                            'pending_days': Decimal('0'),
                        }
                    )
                    if not created:
                        new_bal.total_days = max(new_bal.total_days, new_total)
                        new_bal.save(update_fields=['total_days'])
                    total_created += 1
                else:
                    total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"[MotionHR] Done | processed={total_processed} | "
                f"carried={total_created} | skipped={total_skipped} | dry_run={dry_run}"
            )
        )
