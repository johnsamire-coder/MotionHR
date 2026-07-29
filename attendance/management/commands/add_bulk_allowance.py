"""
Management Command: add_bulk_allowance
الاستخدام:
    python manage.py add_bulk_allowance \
        --company_id=1 \
        --allowance_type=transport \
        --name_ar="بدل مواصلات" \
        --amount=500 \
        [--name_en="Transport Allowance"] \
        [--start_date=2026-01-01]
"""

from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'إضافة بدل لكل موظفي شركة دفعة واحدة'

    def add_arguments(self, parser):
        parser.add_argument('--company_id', type=int, required=True)
        parser.add_argument('--allowance_type', type=str, required=True,
            choices=['transport', 'housing', 'phone', 'meal', 'performance', 'other'])
        parser.add_argument('--name_ar', type=str, required=True)
        parser.add_argument('--name_en', type=str, default='')
        parser.add_argument('--amount', type=float, required=True)
        parser.add_argument('--start_date', type=str, default=None)
        parser.add_argument('--is_monthly', type=bool, default=True)
        parser.add_argument('--dry_run', action='store_true',
            help='اطبع الموظفين بس من غير ما تحفظ')

    def handle(self, *args, **options):
        from employees.models import Employee
        from attendance.company_policy_models import PayrollAllowance

        company_id    = options['company_id']
        allowance_type= options['allowance_type']
        name_ar       = options['name_ar']
        name_en       = options['name_en']
        amount        = options['amount']
        is_monthly    = options['is_monthly']
        dry_run       = options['dry_run']

        start_date = date.today()
        if options['start_date']:
            try:
                start_date = date.fromisoformat(options['start_date'])
            except ValueError:
                raise CommandError('start_date لازم يكون بالصيغة YYYY-MM-DD')

        employees = Employee._base_manager.filter(
            company_id=company_id,
            is_active=True,
        )

        if not employees.exists():
            raise CommandError(f'مفيش موظفين نشطين في شركة {company_id}')

        self.stdout.write(f'موظفين: {employees.count()}')

        if dry_run:
            for emp in employees:
                self.stdout.write(f'  [DRY] {emp.employee_id} - {emp.full_name}')
            self.stdout.write(self.style.WARNING('DRY RUN — مفيش حاجة اتحفظت'))
            return

        created = 0
        skipped = 0
        with transaction.atomic():
            for emp in employees:
                already = PayrollAllowance._base_manager.filter(
                    employee=emp,
                    allowance_type=allowance_type,
                    is_active=True,
                ).exists()
                if already:
                    skipped += 1
                    continue
                PayrollAllowance._base_manager.create(
                    company=emp.company,
                    employee=emp,
                    allowance_type=allowance_type,
                    name_ar=name_ar,
                    name_en=name_en,
                    amount=amount,
                    is_monthly=is_monthly,
                    is_active=True,
                    start_date=start_date,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ تم إنشاء {created} بدل | تجاهل {skipped} موظف (عنده بدل بالفعل)'
        ))
