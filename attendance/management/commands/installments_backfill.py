"""
السلف اللي اتخصمت في مسيرات اتعتمدت قبل تصليح الأقساط: المدفوع فيها ماكانش بيتسجل،
فالقسط كان هيفضل يتخصم للأبد. الأمر ده بيحسب المدفوع الحقيقي من المسيرات المعتمدة.

  python manage.py installments_backfill            → عرض بس (مابيغيرش حاجة)
  python manage.py installments_backfill --apply    → يسجل المدفوع ويقفل السلف اللي خلصت
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Backfill paid amounts of payroll installments from approved payroll runs'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **opts):
        from attendance.api_payroll import INSTALLMENTS_MARK
        from attendance.payroll_pro_models import PayrollInstallment, PayrollLine
        rows = []
        for inst in PayrollInstallment._base_manager.filter(status='active').select_related('employee').order_by('id'):
            months = sorted(set(
                PayrollLine._base_manager.filter(
                    employee_id=inst.employee_id, payroll_run__status__in=('approved', 'locked'),
                ).exclude(payroll_run__notes__contains=INSTALLMENTS_MARK)   # اللي اتسجل وقت اعتماده
                .values_list('payroll_run__year', 'payroll_run__month')
            ))
            months = [m for m in months if m >= (inst.start_year, inst.start_month)]
            if not months:
                continue
            p0 = inst.paid_amount or Decimal('0')
            per_month = max(min(inst.monthly_amount or 0, (inst.total_amount or 0) - p0), Decimal('0'))
            deducted = per_month * len(months)                 # اللي اتخصم فعلاً من الموظف في المسيرات دي
            paid = min(inst.total_amount, p0 + deducted)
            extra = p0 + deducted - inst.total_amount if p0 + deducted > inst.total_amount else Decimal('0')
            rows.append((inst, len(months), paid, extra))

        if not rows:
            self.stdout.write('مفيش سلف محتاجة تصحيح')
            return
        emp = lambda e: f'{e.employee_code} {e.first_name_ar or ""} {e.last_name_ar or ""}'.strip()
        total_extra = Decimal('0')
        for inst, n, paid, extra in rows:
            total_extra += extra
            done = ' ← خلصت' if paid >= inst.total_amount else ''
            more = f' | اتخصم زيادة {extra}' if extra > 0 else ''
            self.stdout.write(f'سلفة #{inst.id} {emp(inst.employee)}: إجمالي {inst.total_amount}، قسط {inst.monthly_amount}، '
                              f'اتخصمت في {n} مسير معتمد → المدفوع {inst.paid_amount} ← {paid}{done}{more}')
        self.stdout.write(f'عدد السلف: {len(rows)} | إجمالي اللي اتخصم زيادة عن السلف: {total_extra}')
        if not opts['apply']:
            self.stdout.write('(عرض بس — ماتغيرش حاجة. للتطبيق: --apply)')
            return
        from attendance.payroll_pro_models import PayrollRun
        with transaction.atomic():
            # المسيرات القديمة دي اتحسبت أقساطها خلاص — علامة عشان الأمر مايحسبهاش تاني لو اتشغل مرة كمان
            for run in PayrollRun._base_manager.filter(status__in=('approved', 'locked')).exclude(
                    notes__contains=INSTALLMENTS_MARK):
                run.notes = f'{run.notes or ""}\n{INSTALLMENTS_MARK}'.strip()
                run.save(update_fields=['notes'])
            for inst, n, paid, extra in rows:
                inst.paid_amount = paid
                if inst.total_amount - paid <= Decimal('0.009'):
                    inst.status = 'completed'
                inst.save(update_fields=['paid_amount', 'status'])
        self.stdout.write('اتسجل ✔')
