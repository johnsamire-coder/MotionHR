"""
مجموعة 17: الفلوس الخطيرة — كشف البنك بالصافي، أقساط السلف بتقف لما تخلص، موافقة تسويات الشيفت المرن.
  python manage.py test attendance.test_group17_money --settings=motionhr.settings_test
"""
import io
from datetime import date
from decimal import Decimal

from django.core.management import call_command

from attendance.payroll_pro_models import PayrollInstallment, PayrollLine, PayrollRun
from attendance.test_action_scope import ScopeBase

RUNS = '/attendance/api/mobile/manager/payroll/'


class MoneyBase(ScopeBase):
    def run_month(self, year, month, who=None):
        r = self.api(who or self.owner_a).post(f'{RUNS}run/create/', {'year': year, 'month': month}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        return PayrollRun._base_manager.get(company=self.a, year=year, month=month)

    def approve(self, run, who=None):
        return self.api(who or self.owner_a).post(f'{RUNS}runs/{run.id}/approve/', format='json')

    def line(self, run, emp):
        return PayrollLine._base_manager.get(payroll_run=run, employee=emp)

    def loan(self, emp, total, monthly, start=(2026, 6), paid=0):
        return PayrollInstallment._base_manager.create(
            company=emp.company, employee=emp, description='سلفة', total_amount=Decimal(total),
            monthly_amount=Decimal(monthly), paid_amount=Decimal(paid), start_year=start[0], start_month=start[1])


class InstallmentTests(MoneyBase):
    def test_loan_stops_after_it_is_paid(self):
        # سلفة 250 والقسط 100: يوليو 100، أغسطس 100، سبتمبر 50 (الباقي)، أكتوبر صفر
        inst = self.loan(self.team_a, 250, 100, start=(2026, 7))
        expected = {(2026, 7): (100, 100, 'active'), (2026, 8): (100, 200, 'active'),
                    (2026, 9): (50, 250, 'completed')}
        for (y, m), (deducted, paid, st) in expected.items():
            run = self.run_month(y, m)
            self.assertEqual(float(self.line(run, self.team_a).installments_total), deducted, (y, m))
            self.assertEqual(self.approve(run).status_code, 200)
            inst.refresh_from_db()
            self.assertEqual((float(inst.paid_amount), inst.status), (paid, st), (y, m))
        run = self.run_month(2026, 10)
        self.assertEqual(float(self.line(run, self.team_a).installments_total), 0)

    def test_approving_twice_does_not_pay_twice(self):
        inst = self.loan(self.team_a, 1000, 100, start=(2026, 7))
        run = self.run_month(2026, 7)
        self.assertEqual(self.approve(run).status_code, 200)
        self.assertEqual(self.approve(run).status_code, 400)
        inst.refresh_from_db()
        self.assertEqual(float(inst.paid_amount), 100)

    def test_loan_starting_later_is_not_paid_early(self):
        inst = self.loan(self.team_a, 500, 100, start=(2026, 9))
        self.approve(self.run_month(2026, 8))
        inst.refresh_from_db()
        self.assertEqual(float(inst.paid_amount), 0)

    def test_backfill_from_old_approved_runs(self):
        # قبل التصليح: 4 مسيرات اتعتمدت (يونيو-سبتمبر) والقسط 100 اتخصم في كل واحد، والسلفة 300 بس
        inst = self.loan(self.team_a, 300, 100, start=(2026, 6))
        other = self.loan(self.other_a, 1000, 200, start=(2026, 8), paid=100)   # كان مدفوع منها 100 قبل السيستم
        for m in (6, 7, 8, 9):
            PayrollRun._base_manager.filter(pk=self.run_month(2026, m).pk).update(status='approved')
        out = io.StringIO()
        call_command('installments_backfill', stdout=out)
        self.assertIn('اتخصم زيادة 100', out.getvalue())
        inst.refresh_from_db()
        self.assertEqual(float(inst.paid_amount), 0)          # العرض مابيغيرش حاجة

        call_command('installments_backfill', '--apply', stdout=io.StringIO())
        inst.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual((float(inst.paid_amount), inst.status), (300, 'completed'))
        self.assertEqual((float(other.paid_amount), other.status), (500, 'active'))    # 100 + أغسطس وسبتمبر 200×2
        # تشغيله تاني مايحسبش نفس المسيرات مرتين
        out = io.StringIO()
        call_command('installments_backfill', '--apply', stdout=out)
        self.assertIn('مفيش سلف محتاجة تصحيح', out.getvalue())
        other.refresh_from_db()
        self.assertEqual(float(other.paid_amount), 500)
        # والمسير الجديد بيكمّل عادي
        self.approve(self.run_month(2026, 10))
        other.refresh_from_db()
        self.assertEqual(float(other.paid_amount), 700)


class BankTransferTests(MoneyBase):
    def setUp(self):
        super().setUp()
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(
            salary_payment_method='bank', bank_name='CIB', bank_account='1000200030004000', basic_salary=Decimal('5000'))
        self.team_a.refresh_from_db()

    def rows(self, y, m):
        r = self.api(self.owner_a).get(f'/attendance/api/mobile/manager/reports/bank-transfer/?year={y}&month={m}')
        self.assertEqual(r.status_code, 200, r.data)
        return {x['employee_code']: x for x in r.data['results']}

    def test_amount_is_net_from_payroll_run(self):
        self.loan(self.team_a, 1000, 300, start=(2026, 9))
        run = self.run_month(2026, 9)
        net = float(self.line(run, self.team_a).net_salary)
        row = self.rows(2026, 9)[self.team_a.employee_code]
        self.assertEqual(row['amount'], round(max(net, 0), 2))
        self.assertNotEqual(row['amount'], 5000.0)             # مش الأساسي
        self.assertIn('المسير', row['source'])
        # الموظفين اللي مش بنك مابيظهروش
        self.assertNotIn(self.other_a.employee_code, self.rows(2026, 9))

    def test_without_run_uses_payroll_calculation(self):
        from attendance.payroll_rules import calculate_effective_payroll
        self.loan(self.team_a, 1000, 300, start=(2026, 8))
        expected = calculate_effective_payroll(self.team_a, 2026, 8)['net_salary']
        row = self.rows(2026, 8)[self.team_a.employee_code]
        self.assertEqual(row['amount'], round(max(float(expected), 0), 2))
        self.assertIn('محسوب', row['source'])

    def test_excel_export_has_month(self):
        r = self.api(self.owner_a).get('/attendance/api/mobile/manager/reports/bank-transfer/export/?year=2026&month=9')
        self.assertEqual(r.status_code, 200)


class FlexReviewTests(MoneyBase):
    def adjustment(self):
        from attendance.models import FlexDayAdjustment
        return FlexDayAdjustment._base_manager.create(
            company=self.a, employee=self.team_a, date=date(2026, 10, 5), required_hours=Decimal('8'),
            actual_hours=Decimal('10'), delta_hours=Decimal('2'), adjustment_type='overtime')

    def test_hr_can_approve_and_reject(self):
        adj = self.adjustment()
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/flex-adjustments/{adj.id}/review/',
                                     {'action': 'approve'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        adj.refresh_from_db()
        self.assertEqual(adj.status, 'approved')
        self.assertIsNotNone(adj.reviewed_at)
        adj2 = self.adjustment()
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/flex-adjustments/{adj2.id}/review/',
                                     {'action': 'reject', 'notes': 'مش مظبوط'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        adj2.refresh_from_db()
        self.assertEqual(adj2.status, 'rejected')


class RerunDraftTests(MoneyBase):
    def test_rerunning_a_draft_month_replaces_lines(self):
        run = self.run_month(2026, 9)
        n = PayrollLine._base_manager.filter(payroll_run=run).count()
        self.assertGreater(n, 0)
        self.loan(self.team_a, 1000, 150, start=(2026, 9))     # اتضافت سلفة بعد أول تشغيل
        run = self.run_month(2026, 9)
        self.assertEqual(PayrollLine._base_manager.filter(payroll_run=run).count(), n)
        self.assertEqual(float(self.line(run, self.team_a).installments_total), 150)
