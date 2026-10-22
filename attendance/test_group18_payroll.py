"""
مجموعة 18: المرتبات والسياسات (أرقام محسوبة يدوي).
مرتب 9000 في سبتمبر 2026 (30 يوم، 22 يوم عمل، 8 أيام جمعة وسبت) → اليوم = 300.
  python manage.py test attendance.test_group18_payroll --settings=motionhr.settings_test
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.utils import timezone

from attendance.company_policy_models import (
    AllowanceRule, CompanyAllowancePolicy, CompanyInsurancePolicy, PenaltyRule,
)
from attendance.models import AbsenceRule, Attendance, LateRule
from attendance.payroll_pro_models import PayrollLine, PayrollRun
from attendance.payroll_rules import get_payroll_period_bounds
from attendance.test_group17_money import MoneyBase
from attendance.test_payroll_scenarios import CAIRO, PayrollScenarioBase, dt


class PeriodAndWeekendTests(PayrollScenarioBase):
    def test_cutoff_day_28_in_march_of_a_normal_year(self):
        self.company.payroll_cycle_type = 'cutoff_day'
        self.company.payroll_cutoff_day = 28
        self.company.save()
        # فبراير 2027 فيه 28 يوم: مارس من 1 لـ 28، وأبريل من 29 مارس (من غير أيام متكررة)
        self.assertEqual(get_payroll_period_bounds(self.company, 2027, 3), (date(2027, 3, 1), date(2027, 3, 28)))
        self.assertEqual(get_payroll_period_bounds(self.company, 2027, 4), (date(2027, 3, 29), date(2027, 4, 28)))
        self.assertEqual(get_payroll_period_bounds(self.company, 2028, 3), (date(2028, 2, 29), date(2028, 3, 28)))

    def test_no_show_weekend_follows_warning_only_absence_rule(self):
        pol = self.attendance_policy()
        AbsenceRule.objects.create(policy=pol, absence_type='unexcused', deduction_type='warning', deduction_value=0)
        p = self.payroll()              # ولا يوم حضور
        self.assertMoney(p['absence_deduction'], 0)          # قبل كده: الجمعة والسبت 8 × 300 = 2400

    def test_no_show_full_day_rule_unchanged(self):
        p = self.payroll()
        self.assertMoney(p['absence_deduction'], 9000)       # 22 + 8 أيام × 300 (زي ما كان)


class LegacyRuleTypesTests(PayrollScenarioBase):
    def test_web_fixed_late_rule_deducts_its_amount(self):
        pol = self.attendance_policy()
        LateRule.objects.create(policy=pol, from_minutes=1, to_minutes=60, deduction_type='fixed', deduction_value=50)
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 50)   # قبل كده صفر

    def test_web_half_day_absence_rule(self):
        pol = self.attendance_policy()
        AbsenceRule.objects.create(policy=pol, absence_type='unexcused', deduction_type='half_day', deduction_value=0)
        self.attend_all(except_days=(1,))
        self.assertMoney(self.payroll()['absence_deduction'], 150)

    def test_only_consecutive_rule_is_used(self):
        pol = self.attendance_policy()
        AbsenceRule.objects.create(policy=pol, absence_type='consecutive', deduction_type='day_fraction',
                                   deduction_value=Decimal('2'))
        self.attend_all(except_days=(1,))
        self.assertMoney(self.payroll()['absence_deduction'], 600)   # قبل كده كان يوم كامل بس (القاعدة متجاهلة)


class OneTimeItemsTests(PayrollScenarioBase):
    def allowance(self, start, monthly):
        return CompanyAllowancePolicy._base_manager.create(
            company=self.company, allowance_type='housing', name_ar='بدل', amount=Decimal('500'),
            is_monthly=monthly, scope='company', start_date=start)

    def test_one_time_allowance_only_in_its_month(self):
        self.attend_all()
        self.allowance(date(2026, 8, 10), monthly=False)             # اتصرف في أغسطس
        self.assertMoney(self.payroll()['allowances_total'], 0)
        self.allowance(date(2026, 9, 5), monthly=False)              # بتاع سبتمبر
        self.allowance(date(2026, 7, 1), monthly=True)               # شهري من يوليو
        self.assertMoney(self.payroll()['allowances_total'], 1000)

    def test_disciplinary_half_day_without_amount(self):
        from attendance.models import DisciplinaryAction
        self.attend_all()
        DisciplinaryAction._base_manager.create(
            company=self.company, employee=self.emp, action_type='half_day_deduction', reason='تأخير متكرر',
            status='approved', payroll_month='2026-09')
        self.assertMoney(self.payroll()['penalties_total'], 150)


class InsuranceTests(PayrollScenarioBase):
    def policy(self, pct, **kw):
        return CompanyInsurancePolicy._base_manager.create(
            company=self.company, insurance_type='social', name_ar='تأمينات',
            company_share_type='percent', company_share_value=Decimal('18.75'),
            employee_share_type='percent', employee_share_value=Decimal(pct), start_date=date(2026, 1, 1), **kw)

    def test_social_insurance_only_for_insured(self):
        self.policy('11')
        self.attend_all()
        self.assertMoney(self.payroll()['insurance_deduction'], 0)
        self.emp.has_insurance = True
        self.emp.save()
        self.assertMoney(self.payroll()['insurance_deduction'], 990)

    def test_overlapping_policies_not_summed(self):
        self.emp.has_insurance = True
        self.emp.save()
        self.policy('11')
        self.policy('10', scope='branch', branch=self.branch)     # الأخص (الفرع) هو اللي بيتطبق
        self.attend_all()
        self.assertMoney(self.payroll()['insurance_deduction'], 900)   # قبل كده 990 + 900


class VisitsAllowanceTests(PayrollScenarioBase):
    def visit(self, day, start, minutes, lat='30.0444', lng='31.2357', status='completed', name='عميل'):
        from attendance.models import LocationCheckIn
        arr = dt(date(2026, 9, day), *start)
        return LocationCheckIn._base_manager.create(
            company=self.company, employee=self.emp, visit_type='client', location_name=name,
            arrival_time=arr, arrival_latitude=Decimal(lat), arrival_longitude=Decimal(lng),
            departure_time=arr + timedelta(minutes=minutes) if minutes is not None else None, status=status)

    def test_only_real_distinct_visits_count(self):
        AllowanceRule._base_manager.create(
            company=self.company, name='زيارات', allowance_type='field_work', calculation_type='per_visit',
            fixed_amount=Decimal('50'), start_date=date(2026, 1, 1))
        self.emp.worker_type = 'field_free'
        self.emp.save()
        self.attend_all()
        self.visit(1, (10, 0), 30)
        self.visit(1, (11, 0), 30)                                  # نفس المكان ونفس اليوم = مرة
        self.visit(1, (12, 0), 30, lat='30.1000', lng='31.3000')     # مكان تاني = مرة
        self.visit(2, (10, 0), 2)                                   # دقيقتين = لا
        self.visit(2, (11, 0), 40, status='cancelled')              # ملغية = لا
        self.visit(3, (10, 0), None, status='arrived')              # لسه مفتوحة = لا
        self.assertMoney(self.payroll()['field_allowance'], 100)


class RunAndPayslipTests(MoneyBase):
    def test_payslip_shows_approved_run(self):
        run = self.run_month(2026, 9)
        line = self.line(run, self.team_a)
        self.assertEqual(self.approve(run).status_code, 200)
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(basic_salary=Decimal('99999'))   # اتغير بعد الاعتماد
        r = self.api(self.team_a).get('/attendance/api/mobile/employee/payslip/?year=2026&month=9')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['is_final'])
        self.assertEqual(r.data['net_salary'], float(line.net_salary))
        self.assertIn('other_deductions', r.data)
        d = r.data
        shown = sum(d[k] for k in ('late_deduction', 'absence_deduction', 'insurance_deduction', 'installments_total',
                                   'penalties_total', 'extra_deductions_total', 'tax_deduction', 'other_deductions'))
        self.assertAlmostEqual(shown, d['total_deductions'], places=1)

    def test_run_includes_on_leave_and_mid_month_leavers(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(status='on_leave')
        left = self.emp(self.a)
        Employee._base_manager.filter(pk=left.pk).update(status='resigned', termination_date=date(2026, 9, 15))
        gone = self.emp(self.a)
        Employee._base_manager.filter(pk=gone.pk).update(status='terminated', termination_date=date(2026, 8, 20))
        run = self.run_month(2026, 9)
        ids = set(PayrollLine._base_manager.filter(payroll_run=run).values_list('employee_id', flat=True))
        self.assertIn(self.other_a.id, ids)
        self.assertIn(left.id, ids)
        self.assertNotIn(gone.id, ids)

    def test_approve_blocked_when_employee_missing(self):
        run = self.run_month(2026, 9)
        PayrollLine._base_manager.filter(payroll_run=run, employee=self.team_a).delete()
        r = self.approve(run)
        self.assertEqual(r.status_code, 400)
        self.assertIn('ماتحسبش', r.data['error'])
        PayrollLine._base_manager.filter(payroll_run=run).delete()
        self.assertEqual(self.approve(run).status_code, 400)        # فاضي

    def test_runs_list_filters_month_and_shows_total(self):
        r9 = self.run_month(2026, 9)
        self.run_month(2026, 8)
        r = self.api(self.owner_a).get('/attendance/api/mobile/manager/payroll/runs/?year=2026&month=9')
        self.assertEqual([x['id'] for x in r.data['runs']], [r9.id])
        total = sum(float(l.net_salary) for l in PayrollLine._base_manager.filter(payroll_run=r9))
        self.assertAlmostEqual(r.data['runs'][0]['grand_net'], round(total, 2), places=2)
        self.assertEqual(len(self.api(self.owner_a).get('/attendance/api/mobile/manager/payroll/runs/').data['runs']), 2)

    def test_terminate_without_date_sets_today(self):
        from employees.models import Employee
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/offboarding/{self.other_a.id}/',
                                     {'status': 'resigned', 'reason': 'ظروف'}, format='json')
        self.assertIn(r.status_code, (200, 201), getattr(r, 'data', None))
        self.assertEqual(Employee._base_manager.get(pk=self.other_a.pk).termination_date, timezone.localdate())


class RulesLifecycleTests(MoneyBase):
    URL = '/attendance/api/mobile/manager/rules/penalty/'

    def rule(self, start=date(2026, 1, 1), **kw):
        return PenaltyRule._base_manager.create(
            company=self.a, name='تأخير', penalty_type='late_arrival', start_date=start,
            tiers=[{'from': 1, 'to': None, 'deduction_type': 'fixed_total', 'value': 50}], **kw)

    def put(self, rule, body, who=None):
        return self.api(who or self.hr_a).put(f'{self.URL}{rule.id}/', body, format='json')

    def test_deactivate_stops_rule_without_new_version(self):
        r = self.rule()
        body = {'name': r.name, 'penalty_type': 'late_arrival', 'tiers': r.tiers, 'scope': 'company', 'is_active': False}
        resp = self.put(r, body)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(PenaltyRule._base_manager.filter(company=self.a).count(), 1)
        r.refresh_from_db()
        today = timezone.localdate()
        self.assertEqual(r.end_date.month, today.month)

    def test_resending_same_values_is_not_a_new_version(self):
        r = self.rule()
        body = {'name': 'تأخير الصبح', 'penalty_type': 'late_arrival', 'scope': 'company', 'grace_amount': 0,
                'tiers': [{'from': 1, 'to': None, 'deduction_type': 'fixed_total', 'value': 50.0}],
                'warnings_enabled': True, 'first_warning_after': 2}
        self.assertEqual(self.put(r, body).status_code, 200)
        self.assertEqual(PenaltyRule._base_manager.filter(company=self.a).count(), 1)
        r.refresh_from_db()
        self.assertEqual((r.name, r.warnings_enabled, r.first_warning_after), ('تأخير الصبح', True, 2))
        body['tiers'][0]['value'] = 70                                # تغيير حقيقي = نسخة جديدة
        self.assertEqual(self.put(r, body).status_code, 200)
        self.assertEqual(PenaltyRule._base_manager.filter(company=self.a).count(), 2)
        r.refresh_from_db()
        self.assertEqual(self.put(r, body).status_code, 400)          # النسخة القديمة مينفعش تتعدل

    def test_delete_used_rule_is_closed_not_erased(self):
        used = self.rule()
        fresh = self.rule(start=timezone.localdate().replace(day=1))
        self.assertEqual(self.api(self.hr_a).delete(f'{self.URL}{used.id}/').status_code, 200)
        self.assertEqual(self.api(self.hr_a).delete(f'{self.URL}{fresh.id}/').status_code, 200)
        used.refresh_from_db()
        self.assertLess(used.end_date, timezone.localdate().replace(day=1))
        self.assertFalse(PenaltyRule._base_manager.filter(pk=fresh.pk).exists())

    def test_late_warning_levels(self):
        from attendance.payroll_rules import get_late_warning_info
        self.rule(warnings_enabled=True, first_warning_after=2, second_warning_after=3, termination_after=5)
        d = date(2026, 9, 10)
        Attendance._base_manager.create(company=self.a, employee=self.team_a, date=date(2026, 9, 8), status='late',
                                        late_minutes=15)
        info = get_late_warning_info(self.team_a, d, 10)
        self.assertEqual((info['incident_number'], info['warning_level'], info['reached_now'], info['should_deduct']),
                         (2, 1, True, False))
        self.assertIn('إنذار أول', info['message_ar'])
        PenaltyRule._base_manager.filter(company=self.a).update(warnings_enabled=False)
        self.assertIsNone(get_late_warning_info(self.team_a, d, 10))

    def test_only_owner_changes_approval_settings(self):
        url = '/attendance/api/mobile/manager/entries/approval-settings/'
        body = {'settings': [{'entry_type': 'bonus', 'category': 'performance', 'requires_approval': False}]}
        self.assertEqual(self.api(self.hr_a).post(url, body, format='json').status_code, 403)
        r = self.api(self.owner_a).post(url, body, format='json')
        self.assertEqual(r.status_code, 200, r.content)


class AttendanceCorrectionTests(MoneyBase):
    def correction(self, form):
        from requests_app.models import EmployeeRequest, RequestCategory, RequestType
        cat = RequestCategory._base_manager.create(company=self.a, name='حضور', name_en='Attendance')
        rt = RequestType._base_manager.create(company=self.a, category=cat, name='تعديل سجل حضور', name_en='Attendance Correction')
        return EmployeeRequest._base_manager.create(company=self.a, employee=self.team_a, request_type=rt,
                                                    subject='نسيت أبصم', status='pending', form_data=form)

    def test_approval_fixes_existing_and_missing_attendance(self):
        att = Attendance._base_manager.create(company=self.a, employee=self.team_a, date=date(2026, 10, 5), status='present',
                                              check_in_time=timezone.make_aware(datetime(2026, 10, 5, 11, 0), CAIRO))
        req = self.correction({'attendance_date': '2026-10-05', 'correction_type': 'check_in', 'correct_check_in': '09:00'})
        self.assertEqual(self.act(self.mgr_a, 'request', req).status_code, 200)
        att.refresh_from_db()
        self.assertEqual(timezone.localtime(att.check_in_time).time(), time(9, 0))
        # يوم مفيهوش سجل خالص (غايب)
        req2 = self.correction({'attendance_date': '2026-10-06', 'correction_type': 'both',
                                'correct_check_in': '09:00', 'correct_check_out': '17:00'})
        self.assertEqual(self.act(self.mgr_a, 'request', req2).status_code, 200)
        a2 = Attendance._base_manager.get(employee=self.team_a, date=date(2026, 10, 6))
        self.assertEqual(timezone.localtime(a2.check_out_time).time(), time(17, 0))
