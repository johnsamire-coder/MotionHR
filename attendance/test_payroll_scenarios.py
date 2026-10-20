"""
اختبارات سيناريوهات المرتبات ومركز السياسات.

كل اختبار بيبني شركة تجريبية من الصفر، وموظف مرتبه 9000 جنيه، وشهر سبتمبر 2026
(30 يوم، الجمعة والسبت إجازة = 22 يوم عمل)، وبيقارن الأرقام اللي طالعة من
calculate_effective_payroll بأرقام محسوبة يدوي.

المرتب اليومي = 9000 / 30 = 300 جنيه، أجر الساعة = 300 / 8 = 37.5 جنيه.

التشغيل:
    python manage.py test attendance.test_payroll_scenarios --settings=motionhr.settings_test
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import TestCase

from accounts.models import User
from companies.models import Company, Branch, Department
from employees.models import Employee, JobTitle
from attendance.models import (
    Shift, ShiftAssignment, Attendance, AttendancePolicy, AttendancePolicyAssignment,
    LateRule, AbsenceRule, OvertimeRule, NightShiftRule, WeekendWorkRule,
    PermissionLedger,
)
from attendance.company_policy_models import (
    CompanyWorkPolicy, PenaltyRule, BonusRule, AllowanceRule,
    CompanyInsurancePolicy, TaxPolicy, CompanyAllowancePolicy, CompanyDeductionPolicy,
    EndOfServicePolicy,
)
from attendance.payroll_settings_model import PayrollSettings
from attendance.payroll_rules import calculate_effective_payroll

CAIRO = ZoneInfo('Africa/Cairo')
YEAR, MONTH = 2026, 9
SEPT_WORKDAYS = [
    date(2026, 9, d) for d in range(1, 31)
    if date(2026, 9, d).weekday() not in (4, 5)  # الجمعة والسبت
]
DAILY = 300.0
HOURLY = 37.5


def dt(d, hh, mm=0):
    return datetime.combine(d, time(hh, mm)).replace(tzinfo=CAIRO)


class PayrollScenarioBase(TestCase):
    salary = 9000
    shift_grace = 0

    def setUp(self):
        self.company = Company.objects.create(name_ar='شركة تجريبية', name_en='Test Co')
        self.branch = Branch.objects.create(company=self.company, name_ar='الفرع الرئيسي', name_en='Main')
        self.branch2 = Branch.objects.create(company=self.company, name_ar='فرع 2', name_en='B2')
        self.dept = Department.objects.create(company=self.company, name_ar='المبيعات', name_en='Sales')
        CompanyWorkPolicy._base_manager.create(company=self.company)  # الأحد-الخميس
        self.shift = Shift._base_manager.create(
            company=self.company, name='صباحي', start_time=time(9), end_time=time(17),
            grace_period=self.shift_grace, break_duration=0,
        )
        ShiftAssignment._base_manager.create(
            company=self.company, shift=self.shift, assignment_type='company',
            start_date=date(2020, 1, 1), is_active=True,
        )
        self.job = JobTitle._base_manager.create(company=self.company, name_ar='موظف', name_en='Staff')
        self.emp = self.make_employee()

    _seq = 0

    def make_employee(self, salary=None, **kw):
        PayrollScenarioBase._seq += 1
        n = PayrollScenarioBase._seq
        user = User.objects.create_user(
            username=f'emp{n}', password='x', company=self.company, role='employee',
        )
        defaults = dict(
            user=user, company=self.company, employee_code=f'E{n}',
            first_name_ar='موظف', last_name_ar=str(n), first_name_en='Emp', last_name_en=str(n),
            national_id=f'{n:014d}', hire_date=date(2020, 1, 1), birth_date=date(1990, 1, 1), gender='male',
            basic_salary=Decimal(str(salary or self.salary)), branch=self.branch,
            department=self.dept, job_title=self.job, phone=f'010{n:08d}',
        )
        defaults.update(kw)
        return Employee._base_manager.create(**defaults)

    # ── حضور ──
    def attend(self, d, in_hm=(9, 0), out_hm=(17, 0), emp=None, **kw):
        emp = emp or self.emp
        check_in = dt(d, *in_hm) if in_hm else None
        check_out = dt(d, *out_hm) if out_hm else None
        if check_in and check_out and check_out <= check_in:
            check_out += timedelta(days=1)
        hours = round((check_out - check_in).total_seconds() / 3600, 2) if check_in and check_out else 0
        return Attendance._base_manager.create(
            company=self.company, employee=emp, date=d, check_in_time=check_in,
            check_out_time=check_out, work_hours=hours, status='present', **kw,
        )

    def attend_all(self, except_days=(), emp=None, overrides=None):
        overrides = overrides or {}
        for d in SEPT_WORKDAYS:
            if d.day in except_days:
                continue
            self.attend(d, emp=emp, **overrides.get(d.day, {}))

    # True = نحسب الملخصات اليومية الأول (زي كرون السيرفر) والمرتب يقرا منها
    with_summaries = False

    def payroll(self, emp=None, settings=None):
        emp = emp or self.emp
        if self.with_summaries:
            from attendance.models import DailyAttendanceSummary
            for day in range(1, 31):
                DailyAttendanceSummary.compute_for_day(emp, D(day))
        return calculate_effective_payroll(emp, YEAR, MONTH, settings=settings)

    # ── سياسات ──
    def penalty_rule(self, penalty_type, tiers, grace=0, **kw):
        return PenaltyRule._base_manager.create(
            company=self.company, name=f'قاعدة {penalty_type}', penalty_type=penalty_type,
            grace_amount=grace, tiers=tiers, start_date=date(2026, 1, 1), **kw,
        )

    def bonus_rule(self, bonus_type, tiers, company=None, **kw):
        return BonusRule._base_manager.create(
            company=company or self.company, name=f'قاعدة {bonus_type}', bonus_type=bonus_type,
            tiers=tiers, start_date=date(2026, 1, 1), **kw,
        )

    def attendance_policy(self, status='active', assign='company', **kw):
        pol = AttendancePolicy._base_manager.create(
            company=self.company, name='سياسة الحضور', effective_from=date(2026, 1, 1),
            status=status, **kw,
        )
        if assign:
            AttendancePolicyAssignment._base_manager.create(
                company=self.company, policy=pol, assignment_type=assign,
                branch=self.branch if assign == 'branch' else None,
                department=self.dept if assign == 'department' else None,
                priority={'department': 1, 'branch': 2, 'company': 3}[assign],
            )
        return pol

    def settings_row(self, **kw):
        return PayrollSettings._base_manager.create(company=self.company, **kw)

    def assertMoney(self, actual, expected, msg=None):
        self.assertAlmostEqual(float(actual), float(expected), places=2, msg=msg)


# ═══════════════════════════════════════════════════════════════
# 1) الأساس: حضور كامل
# ═══════════════════════════════════════════════════════════════
class BaselineTests(PayrollScenarioBase):
    def test_full_attendance_no_deductions(self):
        self.attend_all()
        p = self.payroll()
        self.assertEqual(p['total_working_days'], 22)
        self.assertEqual(p['present_days'], 22)
        self.assertEqual(p['absent_days'], 0)
        self.assertMoney(p['late_deduction'], 0)
        self.assertMoney(p['absence_deduction'], 0)
        self.assertMoney(p['weekend_allowance'], 0)
        self.assertMoney(p['net_salary'], 9000)


def _leave_type(company, paid=True, name='اعتيادي'):
    from leaves.models import LeaveType
    return LeaveType._base_manager.create(company=company, name=name, is_paid=paid, category='annual')


def _leave(emp, leave_type, start, end=None, days=1, half='', hours=None):
    from leaves.models import LeaveRequest
    return LeaveRequest._base_manager.create(
        company=emp.company, employee=emp, leave_type=leave_type, start_date=start,
        end_date=end or start, days_count=Decimal(str(days)), half_day_type=half,
        leave_hours=hours, reason='اختبار', status='approved',
    )


def _permission_request(emp, d, hours, kind='late_arrival'):
    from requests_app.models import RequestCategory, RequestType, EmployeeRequest
    cat = RequestCategory._base_manager.create(company=emp.company, name='أذونات')
    rt = RequestType._base_manager.create(company=emp.company, category=cat, name='إذن', permission_kind=kind)
    return EmployeeRequest._base_manager.create(
        company=emp.company, employee=emp, request_type=rt, subject='إذن', start_date=d,
        end_date=d, duration_hours=Decimal(str(hours)), status='approved',
    )


D = lambda day: date(2026, 9, day)  # noqa: E731


# ═══════════════════════════════════════════════════════════════
# 2) التأخير
# ═══════════════════════════════════════════════════════════════
class LateDefaultTests(PayrollScenarioBase):
    """مفيش أي سياسة → الافتراضي جنيه لكل دقيقة بعد سماحية الشيفت"""

    def test_default_per_minute(self):
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        p = self.payroll()
        self.assertEqual(p['late_days'], 1)
        self.assertMoney(p['late_deduction'], 20)
        self.assertMoney(p['net_salary'], 8980)

    def test_settings_rate(self):
        self.settings_row(late_deduction_per_minute=Decimal('2'))
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 40)


class LateShiftGraceTests(PayrollScenarioBase):
    shift_grace = 10

    def test_within_grace_not_late(self):
        self.attend_all(overrides={1: {'in_hm': (9, 10)}})
        p = self.payroll()
        self.assertEqual(p['late_days'], 0)
        self.assertMoney(p['late_deduction'], 0)

    def test_after_grace_only_extra_minutes(self):
        self.attend_all(overrides={1: {'in_hm': (9, 25)}})
        self.assertMoney(self.payroll()['late_deduction'], 15)

    def test_rule_grace_bigger_than_shift_grace_applied_once(self):
        # سماح الشيفت 10 وسماح اللائحة 15 → السماح 15 مرة واحدة
        self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'fixed_per_unit', 'value': 2}], grace=15)
        self.attend_all(overrides={1: {'in_hm': (9, 20)}, 2: {'in_hm': (9, 30)}, 3: {'in_hm': (9, 14)}})
        p = self.payroll()
        # يوم1: 20-15=5 → 10 ، يوم2: 30-15=15 → 30 ، يوم3: 14 أقل من السماح → 0
        self.assertMoney(p['late_deduction'], 40)

    def test_rule_grace_smaller_than_shift_grace(self):
        self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'fixed_per_unit', 'value': 1}], grace=5)
        self.attend_all(overrides={1: {'in_hm': (9, 30)}})
        # السماح الأكبر = 10 → 20 دقيقة
        self.assertMoney(self.payroll()['late_deduction'], 20)


class LatePenaltyRuleTests(PayrollScenarioBase):
    TIERS = [
        {'from': 1, 'to': 15, 'deduction_type': 'fixed_per_unit', 'value': 2},
        {'from': 16, 'to': 60, 'deduction_type': 'quarter_day'},
        {'from': 61, 'to': None, 'deduction_type': 'half_day'},
    ]

    def test_tiers_per_day_no_attendance_policy(self):
        self.penalty_rule('late_arrival', self.TIERS)
        self.attend_all(overrides={1: {'in_hm': (9, 10)}, 2: {'in_hm': (9, 30)}, 3: {'in_hm': (10, 30)}})
        p = self.payroll()
        # 10د → 20 ، 30د → ربع يوم 75 ، 90د → نص يوم 150
        self.assertMoney(p['late_deduction'], 245)
        self.assertEqual(p['late_days'], 3)

    def test_tiers_per_day_with_attendance_policy(self):
        self.attendance_policy()
        self.penalty_rule('late_arrival', self.TIERS)
        self.attend_all(overrides={1: {'in_hm': (9, 10)}, 2: {'in_hm': (9, 30)}, 3: {'in_hm': (10, 30)}})
        self.assertMoney(self.payroll()['late_deduction'], 245)

    def test_rule_for_other_branch_not_applied(self):
        self.penalty_rule('late_arrival', self.TIERS, scope='branch', branch=self.branch2)
        self.attend_all(overrides={2: {'in_hm': (9, 30)}})
        # مش بتاعته → الافتراضي 1 جنيه/دقيقة
        self.assertMoney(self.payroll()['late_deduction'], 30)

    def test_rule_for_other_branch_not_applied_with_policy(self):
        self.attendance_policy()
        self.penalty_rule('late_arrival', self.TIERS, scope='branch', branch=self.branch2)
        self.attend_all(overrides={2: {'in_hm': (9, 30)}})
        # سياسة حضور بدون قواعد تأخير → الافتراضي 1 جنيه/دقيقة
        self.assertMoney(self.payroll()['late_deduction'], 30)

    def test_rule_for_own_department(self):
        self.penalty_rule('late_arrival', self.TIERS, scope='department', department=self.dept)
        self.attend_all(overrides={2: {'in_hm': (9, 30)}})
        self.assertMoney(self.payroll()['late_deduction'], 75)

    def test_rule_for_specific_employee(self):
        r = self.penalty_rule('late_arrival', self.TIERS, scope='employees')
        other = self.make_employee()
        r.specific_employees.add(other)
        self.attend_all(overrides={2: {'in_hm': (9, 30)}})
        self.attend_all(emp=other, overrides={2: {'in_hm': (9, 30)}})
        self.assertMoney(self.payroll()['late_deduction'], 30)
        self.assertMoney(self.payroll(other)['late_deduction'], 75)

    def test_rule_not_started_yet(self):
        r = self.penalty_rule('late_arrival', self.TIERS)
        r.start_date = date(2026, 10, 1)
        r.save()
        self.attend_all(overrides={2: {'in_hm': (9, 30)}})
        self.assertMoney(self.payroll()['late_deduction'], 30)

    def test_rule_ending_mid_month_applies_until_end(self):
        r = self.penalty_rule('late_arrival', self.TIERS)
        r.end_date = date(2026, 9, 15)
        r.save()
        self.attend_all(overrides={2: {'in_hm': (9, 30)}, 22: {'in_hm': (9, 30)}})
        # يوم 2 بالقاعدة 75 ، يوم 22 بعد انتهائها → 30
        self.assertMoney(self.payroll()['late_deduction'], 105)

    def test_full_day_tier(self):
        self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'full_day'}])
        self.attend_all(overrides={1: {'in_hm': (9, 5)}, 2: {'in_hm': (9, 5)}})
        self.assertMoney(self.payroll()['late_deduction'], 600)


class LateAttendancePolicyTests(PayrollScenarioBase):
    def _rules(self, pol):
        LateRule.objects.create(policy=pol, from_minutes=1, to_minutes=30, deduction_type='fixed_amount', deduction_value=Decimal('50'))
        LateRule.objects.create(policy=pol, from_minutes=31, to_minutes=999, deduction_type='day_fraction', deduction_value=Decimal('0.5'))

    def test_active_assigned_policy(self):
        self._rules(self.attendance_policy())
        self.attend_all(overrides={1: {'in_hm': (9, 20)}, 2: {'in_hm': (10, 0)}})
        self.assertMoney(self.payroll()['late_deduction'], 200)

    def test_draft_policy_not_applied(self):
        self._rules(self.attendance_policy(status='draft'))
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 20)

    def test_active_policy_without_assignment_applies_company_wide(self):
        self._rules(self.attendance_policy(assign=None))
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 50)

    def test_department_policy_beats_company_policy(self):
        self._rules(self.attendance_policy(assign='company'))
        pol2 = self.attendance_policy(assign='department')
        LateRule.objects.create(policy=pol2, from_minutes=1, to_minutes=999, deduction_type='fixed_amount', deduction_value=Decimal('10'))
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 10)

    def test_penalty_rule_beats_policy_late_rules(self):
        self._rules(self.attendance_policy())
        self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'fixed_total', 'value': 7}])
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 7)

    def test_policy_late_beyond_last_rule_uses_default_per_minute(self):
        # زي جاكي ستور: قاعدة واحدة 0-15 لا خصم
        pol = self.attendance_policy()
        LateRule.objects.create(policy=pol, from_minutes=0, to_minutes=15, deduction_type='none', deduction_value=0)
        self.attend_all(overrides={1: {'in_hm': (9, 10)}, 2: {'in_hm': (9, 40)}})
        # يوم 1: 0 ، يوم 2: 40 دقيقة → 25 دقيقة زيادة × 1
        self.assertMoney(self.payroll()['late_deduction'], 25)

    def test_jacky_escalating_rules(self):
        pol = self.attendance_policy()
        LateRule.objects.create(policy=pol, from_minutes=0, to_minutes=15, deduction_type='none', deduction_value=0)
        LateRule.objects.create(policy=pol, from_minutes=16, to_minutes=30, deduction_type='day_fraction', deduction_value=Decimal('0.25'))
        LateRule.objects.create(policy=pol, from_minutes=31, to_minutes=60, deduction_type='day_fraction', deduction_value=Decimal('0.5'))
        LateRule.objects.create(policy=pol, from_minutes=61, to_minutes=1440, deduction_type='day_fraction', deduction_value=Decimal('1'))
        self.attend_all(overrides={1: {'in_hm': (9, 15)}, 2: {'in_hm': (9, 16)}, 3: {'in_hm': (9, 45)}, 6: {'in_hm': (11, 0)}})
        # 0 + ربع يوم 75 + نص يوم 150 + يوم 300
        self.assertMoney(self.payroll()['late_deduction'], 525)

    def test_policy_late_rule_none_type(self):
        pol = self.attendance_policy()
        LateRule.objects.create(policy=pol, from_minutes=1, to_minutes=15, deduction_type='none', deduction_value=0)
        LateRule.objects.create(policy=pol, from_minutes=16, to_minutes=999, deduction_type='per_minute', deduction_value=Decimal('3'))
        self.attend_all(overrides={1: {'in_hm': (9, 10)}, 2: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 60)


class LatePermissionTests(PayrollScenarioBase):
    def test_permission_balance_converts_late_and_is_idempotent(self):
        self.attendance_policy(
            permission_enabled=True, permission_monthly_hours=Decimal('2'), permission_monthly_count=2,
            permission_max_hours_per_request=Decimal('1'),
        )
        self.attend_all(overrides={1: {'in_hm': (9, 30)}, 2: {'in_hm': (9, 45)}, 3: {'in_hm': (9, 20)}})
        p1 = self.payroll()
        p2 = self.payroll()
        # يوم 1 و 2 اتحولوا لإذن، يوم 3 الرصيد (عدد المرات) خلص → 20 جنيه
        self.assertMoney(p1['late_deduction'], 20)
        self.assertMoney(p2['late_deduction'], 20)
        self.assertEqual(PermissionLedger._base_manager.filter(employee=self.emp).count(), 2)

    def test_partial_permission(self):
        self.attendance_policy(
            permission_enabled=True, permission_monthly_hours=Decimal('0.5'), permission_monthly_count=5,
            permission_max_hours_per_request=Decimal('1'),
        )
        self.attend_all(overrides={1: {'in_hm': (9, 45)}})
        # 30 دقيقة إذن، 15 خصم
        self.assertMoney(self.payroll()['late_deduction'], 15)

    def test_approved_late_permission_request_cancels_deduction(self):
        self.attend_all(overrides={1: {'in_hm': (9, 30)}, 2: {'in_hm': (9, 30)}})
        _permission_request(self.emp, D(1), 0.5)
        # يوم 1 عليه إذن معتمد نص ساعة → يوم 2 بس
        self.assertMoney(self.payroll()['late_deduction'], 30)

    def test_approved_early_leave_request(self):
        self.attend_all(overrides={1: {'out_hm': (16, 0), 'early_leave_minutes': 60}})
        _permission_request(self.emp, D(1), 1, kind='early_leave')
        self.assertMoney(self.payroll()['early_leave_deduction'], 0)


# ═══════════════════════════════════════════════════════════════
# 3) الانصراف المبكر وعدم تسجيل الخروج
# ═══════════════════════════════════════════════════════════════
class EarlyLeaveTests(PayrollScenarioBase):
    def test_default_uses_late_rate(self):
        self.attend_all(overrides={1: {'out_hm': (16, 30), 'early_leave_minutes': 30}})
        self.assertMoney(self.payroll()['early_leave_deduction'], 30)

    def test_penalty_rule_early_leave(self):
        self.penalty_rule('early_leave', [{'from': 1, 'to': None, 'deduction_type': 'fixed_per_unit', 'value': 0.5}], grace=5)
        self.attend_all(overrides={1: {'out_hm': (16, 30), 'early_leave_minutes': 30}})
        self.assertMoney(self.payroll()['early_leave_deduction'], 12.5)

    def test_missing_checkout_rule(self):
        self.penalty_rule('missing_checkout', [{'from': 1, 'to': None, 'deduction_type': 'fixed_per_unit', 'value': 50}])
        self.attend_all(overrides={1: {'out_hm': None}, 2: {'out_hm': None}})
        p = self.payroll()
        self.assertEqual(p['missing_checkout_days_count'], 2)
        self.assertMoney(p['missing_checkout_deduction'], 100)


# ═══════════════════════════════════════════════════════════════
# 4) الغياب
# ═══════════════════════════════════════════════════════════════
class AbsenceTests(PayrollScenarioBase):
    def test_default_absence_is_day_wage(self):
        self.attend_all(except_days=(1, 2))
        p = self.payroll()
        self.assertEqual(p['absent_days'], 2)
        self.assertMoney(p['absence_deduction'], 600)
        self.assertMoney(p['net_salary'], 8400)

    def test_settings_fixed_absence_amount(self):
        self.settings_row(absence_deduction_per_day=Decimal('250'))
        self.attend_all(except_days=(1, 2))
        self.assertMoney(self.payroll()['absence_deduction'], 500)

    def test_settings_zero_absence_means_day_wage(self):
        self.settings_row(absence_deduction_per_day=Decimal('0'))
        self.attend_all(except_days=(1,))
        self.assertMoney(self.payroll()['absence_deduction'], 300)

    def test_penalty_rule_progressive(self):
        self.penalty_rule('absence', [
            {'from': 1, 'to': 1, 'deduction_type': 'full_day'},
            {'from': 2, 'to': None, 'deduction_type': 'two_days'},
        ])
        self.attend_all(except_days=(1, 2, 3))
        # يوم + يومين + يومين = 5 أيام
        self.assertMoney(self.payroll()['absence_deduction'], 1500)

    def test_penalty_rule_with_grace_days(self):
        self.penalty_rule('absence', [
            {'from': 1, 'to': 1, 'deduction_type': 'full_day'},
            {'from': 2, 'to': None, 'deduction_type': 'two_days'},
        ], grace=1)
        self.attend_all(except_days=(1, 2, 3))
        # أول يوم سماح، التاني يوم، التالت يومين
        self.assertMoney(self.payroll()['absence_deduction'], 900)

    def test_penalty_rule_single_full_day_tier(self):
        self.penalty_rule('absence', [{'from': 1, 'to': None, 'deduction_type': 'full_day'}])
        self.attend_all(except_days=(1, 2, 3, 6))
        self.assertMoney(self.payroll()['absence_deduction'], 1200)

    def test_penalty_rule_with_attendance_policy(self):
        self.attendance_policy()
        self.penalty_rule('absence', [{'from': 1, 'to': None, 'deduction_type': 'full_day'}])
        self.attend_all(except_days=(1, 2))
        self.assertMoney(self.payroll()['absence_deduction'], 600)

    def test_policy_absence_rule_day_fraction(self):
        pol = self.attendance_policy()
        AbsenceRule.objects.create(policy=pol, absence_type='unexcused', deduction_type='day_fraction', deduction_value=Decimal('1.5'))
        self.attend_all(except_days=(1, 2))
        self.assertMoney(self.payroll()['absence_deduction'], 900)

    def test_policy_absence_rule_warning_only(self):
        pol = self.attendance_policy()
        AbsenceRule.objects.create(policy=pol, absence_type='unexcused', deduction_type='warning', deduction_value=0)
        self.attend_all(except_days=(1,))
        self.assertMoney(self.payroll()['absence_deduction'], 0)

    def test_policy_without_absence_rule_deducts_day(self):
        self.attendance_policy()
        self.attend_all(except_days=(1,))
        self.assertMoney(self.payroll()['absence_deduction'], 300)

    def test_full_day_leave_not_absent(self):
        lt = _leave_type(self.company)
        _leave(self.emp, lt, D(1), D(2), days=2)
        self.attend_all(except_days=(1, 2))
        p = self.payroll()
        self.assertEqual(p['absent_days'], 0)
        self.assertEqual(p['on_leave_days'], 2)
        self.assertMoney(p['net_salary'], 9000)

    def test_unpaid_leave_deducted_once(self):
        lt = _leave_type(self.company, paid=False, name='بدون أجر')
        _leave(self.emp, lt, D(1), D(1), days=1)
        self.attend_all(except_days=(1,))
        p = self.payroll()
        self.assertMoney(p['unpaid_leave_deduction'], 300)
        self.assertMoney(p['absence_deduction'], 0)
        self.assertMoney(p['net_salary'], 8700)

    def test_half_day_leave_attended_other_half(self):
        lt = _leave_type(self.company)
        _leave(self.emp, lt, D(1), days=0.5, half='morning', hours=4)
        self.attend_all(overrides={1: {'in_hm': (13, 0)}})
        p = self.payroll()
        # إجازة الصبح مدفوعة وجه الضهر → مفيش تأخير ولا خصم
        self.assertMoney(p['late_deduction'], 0)
        self.assertMoney(p['absence_deduction'], 0)
        self.assertMoney(p['net_salary'], 9000)

    def test_half_day_leave_not_attended(self):
        lt = _leave_type(self.company)
        _leave(self.emp, lt, D(1), days=0.5, half='morning', hours=4)
        self.attend_all(except_days=(1,))
        p = self.payroll()
        # نص يوم إجازة مدفوعة + نص يوم غياب
        self.assertMoney(p['absence_deduction'], 150)

    def test_official_holiday_without_rule_is_paid(self):
        from leaves.official_holiday_models import OfficialHoliday
        OfficialHoliday._base_manager.create(company=self.company, name='عيد', start_date=D(1), end_date=D(2))
        self.attend_all(except_days=(1, 2))
        p = self.payroll()
        self.assertEqual(p['absent_days'], 0)
        self.assertMoney(p['net_salary'], 9000)

    def test_zero_engagement_gets_nothing(self):
        p = self.payroll()
        self.assertEqual(p['absent_days'], 22)
        self.assertMoney(p['net_salary'], 0)


class AbsenceTodayTests(PayrollScenarioBase):
    def test_admin_exempt(self):
        self.emp.user.role = 'company_admin'
        self.emp.user.save()
        p = self.payroll()
        self.assertMoney(p['absence_deduction'], 0)
        self.assertMoney(p['net_salary'], 9000)


# ═══════════════════════════════════════════════════════════════
# 5) التعيين وانتهاء الخدمة في نص الشهر
# ═══════════════════════════════════════════════════════════════
class EmploymentPeriodTests(PayrollScenarioBase):
    def test_hired_mid_month(self):
        self.emp.hire_date = D(16)
        self.emp.save()
        self.attend_all(except_days=range(1, 16))
        p = self.payroll()
        # 15 يوم قبل التعيين مش مستحقة
        self.assertEqual(p['absent_days'], 0)
        self.assertMoney(p['not_employed_deduction'], 4500)
        self.assertMoney(p['net_salary'], 4500)

    def test_terminated_mid_month(self):
        self.emp.termination_date = D(15)
        self.emp.save()
        self.attend_all(except_days=range(16, 31))
        p = self.payroll()
        self.assertEqual(p['absent_days'], 0)
        self.assertMoney(p['net_salary'], 4500)


# ═══════════════════════════════════════════════════════════════
# 6) أيام الراحة والويك إند
# ═══════════════════════════════════════════════════════════════
class WeekendTests(PayrollScenarioBase):
    def test_shift_rest_day_not_paid_as_weekend_work(self):
        # شيفت الموظف إجازته الأحد والاثنين وبيشتغل الجمعة والسبت
        sh = Shift._base_manager.create(
            company=self.company, name='ويك إند', start_time=time(9), end_time=time(17), break_duration=0,
            work_sunday=False, work_monday=False, work_friday=True, work_saturday=True,
        )
        ShiftAssignment._base_manager.create(
            company=self.company, shift=sh, assignment_type='employee', employee=self.emp,
            start_date=date(2020, 1, 1), is_active=True,
        )
        self.attendance_policy()
        for day in range(1, 31):
            d = D(day)
            if sh.is_work_day(d):
                self.attend(d)
        p = self.payroll()
        self.assertMoney(p['weekend_allowance'], 0)
        self.assertEqual(p['absent_days'], 0)

    def test_work_on_rest_day_with_policy_rule(self):
        pol = self.attendance_policy()
        WeekendWorkRule.objects.create(policy=pol, compensation_type='overtime_multiplier', multiplier=Decimal('1'))
        self.attend_all()
        self.attend(D(4))  # جمعة
        p = self.payroll()
        self.assertEqual(p['weekend_work_days'], 1)
        self.assertMoney(p['weekend_allowance'], 300)

    def test_weekend_bonus_rule(self):
        self.bonus_rule('weekend_work', [{'from': 1, 'to': None, 'value_type': 'multiplier', 'value': 2}])
        self.attend_all()
        self.attend(D(4))
        self.assertMoney(self.payroll()['weekend_allowance'], 600)


# ═══════════════════════════════════════════════════════════════
# 7) الأوفر تايم
# ═══════════════════════════════════════════════════════════════
class OvertimeTests(PayrollScenarioBase):
    def test_settings_rate(self):
        self.settings_row(overtime_rate_per_hour=Decimal('50'))
        self.attend_all(overrides={1: {'out_hm': (19, 0)}})
        p = self.payroll()
        self.assertAlmostEqual(p['overtime_hours'], 2, places=2)
        self.assertMoney(p['overtime_bonus'], 100)

    def test_no_rate_no_rule_no_overtime(self):
        self.attend_all(overrides={1: {'out_hm': (19, 0)}})
        self.assertMoney(self.payroll()['overtime_bonus'], 0)

    def test_bonus_rule_works_even_if_settings_rate_zero(self):
        self.settings_row(overtime_rate_per_hour=Decimal('0'))
        self.bonus_rule('overtime', [{'from': 0, 'to': None, 'value_type': 'multiplier', 'value': 1.5}])
        self.attend_all(overrides={1: {'out_hm': (19, 0)}})
        # 2 ساعة × 37.5 × 1.5
        self.assertMoney(self.payroll()['overtime_bonus'], 112.5)

    def test_bonus_rule_with_attendance_policy(self):
        self.attendance_policy()
        self.bonus_rule('overtime', [{'from': 0, 'to': None, 'value_type': 'fixed_per_unit', 'value': 60}])
        self.attend_all(overrides={1: {'out_hm': (19, 0)}})
        self.assertMoney(self.payroll()['overtime_bonus'], 120)

    def test_other_company_bonus_rule_ignored(self):
        other_co = Company.objects.create(name_ar='شركة تانية', name_en='Other')
        self.bonus_rule('overtime', [{'from': 0, 'to': None, 'value_type': 'multiplier', 'value': 5}], company=other_co)
        pol = self.attendance_policy()
        OvertimeRule.objects.create(policy=pol, overtime_type='after_shift', multiplier=Decimal('2'), min_minutes=0)
        self.attend_all(overrides={1: {'out_hm': (19, 0)}})
        # 2 × 37.5 × 2
        self.assertMoney(self.payroll()['overtime_bonus'], 150)

    def test_policy_overtime_min_minutes_per_day(self):
        # أقل مدة 10 دقايق: الأيام اللي فيها 5 دقايق بس مش بتتحسب حتى لو مجموعها كبير
        pol = self.attendance_policy()
        OvertimeRule.objects.create(policy=pol, overtime_type='after_shift', multiplier=Decimal('1.5'), min_minutes=10)
        overrides = {d.day: {'out_hm': (17, 5)} for d in SEPT_WORKDAYS}
        overrides[1] = {'out_hm': (19, 0)}
        self.attend_all(overrides=overrides)
        # يوم 1 بس: 2 ساعة × 37.5 × 1.5
        self.assertMoney(self.payroll()['overtime_bonus'], 112.5)

    def test_policy_overtime_max_per_day(self):
        pol = self.attendance_policy()
        OvertimeRule.objects.create(policy=pol, overtime_type='after_shift', multiplier=Decimal('1'), min_minutes=0, max_hours_per_day=1)
        self.attend_all(overrides={1: {'out_hm': (20, 0)}})
        self.assertMoney(self.payroll()['overtime_bonus'], 37.5)

    def test_policy_overtime_min_minutes(self):
        pol = self.attendance_policy()
        OvertimeRule.objects.create(policy=pol, overtime_type='after_shift', multiplier=Decimal('1.5'), min_minutes=180)
        self.attend_all(overrides={1: {'out_hm': (19, 0)}})
        self.assertMoney(self.payroll()['overtime_bonus'], 0)


class NightShiftTests(PayrollScenarioBase):
    def test_night_rule_percentage(self):
        night = Shift._base_manager.create(
            company=self.company, name='ليلي', start_time=time(22), end_time=time(6), break_duration=0,
            crosses_midnight=True, shift_type='night',
        )
        ShiftAssignment._base_manager.create(
            company=self.company, shift=night, assignment_type='employee', employee=self.emp,
            start_date=date(2020, 1, 1), is_active=True,
        )
        pol = self.attendance_policy()
        NightShiftRule.objects.create(policy=pol, allowance_type='percentage', percentage=Decimal('25'))
        for d in SEPT_WORKDAYS:
            self.attend(d, in_hm=(22, 0), out_hm=(6, 0))
        p = self.payroll()
        self.assertEqual(p['night_shift_days'], 22)
        self.assertMoney(p['night_allowance'], 22 * 75)
        self.assertMoney(p['late_deduction'], 0)


# ═══════════════════════════════════════════════════════════════
# 8) البدلات والتأمينات والضرايب
# ═══════════════════════════════════════════════════════════════
class AllowanceRuleTests(PayrollScenarioBase):
    def _rule(self, allowance_type, calc, amount, **kw):
        return AllowanceRule._base_manager.create(
            company=self.company, name=allowance_type, allowance_type=allowance_type,
            calculation_type=calc, fixed_amount=Decimal(str(amount)), start_date=date(2026, 1, 1), **kw,
        )

    def test_housing_fixed_monthly(self):
        self._rule('housing', 'fixed_monthly', 1000)
        self.attend_all()
        p = self.payroll()
        self.assertMoney(p['rule_allowances_total'], 1000)
        self.assertMoney(p['net_salary'], 10000)

    def test_transport_per_day(self):
        self._rule('transport', 'per_day', 20)
        self.attend_all(except_days=(1,))
        p = self.payroll()
        # 21 يوم حضور × 20
        self.assertMoney(p['rule_allowances_total'], 420)

    def test_per_day_min_hours(self):
        self._rule('meals', 'per_day', 30, min_work_hours_per_day=8)
        self.attend_all(overrides={1: {'out_hm': (15, 0)}, 2: {'out_hm': (15, 0)}})
        # 20 يوم كاملين × 30
        self.assertMoney(self.payroll()['rule_allowances_total'], 600)

    def test_field_work_only_for_field_workers(self):
        self._rule('field_work', 'fixed_monthly', 500)
        self.attend_all()
        self.assertMoney(self.payroll()['rule_allowances_total'], 0)

    def test_multiple_rule_types(self):
        self._rule('housing', 'fixed_monthly', 1000)
        self._rule('phone', 'fixed_monthly', 200)
        self.attend_all()
        self.assertMoney(self.payroll()['rule_allowances_total'], 1200)


class InsuranceTaxTests(PayrollScenarioBase):
    def test_insurance_policy_percent(self):
        CompanyInsurancePolicy._base_manager.create(
            company=self.company, insurance_type='social', name_ar='تأمينات',
            company_share_type='percent', company_share_value=Decimal('18.75'),
            employee_share_type='percent', employee_share_value=Decimal('11'),
            start_date=date(2026, 1, 1),
        )
        self.attend_all()
        p = self.payroll()
        self.assertMoney(p['insurance_deduction'], 990)
        self.assertMoney(p['social_insurance_company'], 1687.5)

    def test_insurance_not_double_with_settings(self):
        self.settings_row(insurance_mode='percent', insurance_percent=Decimal('11'))
        self.emp.has_insurance = True
        self.emp.save()
        CompanyInsurancePolicy._base_manager.create(
            company=self.company, insurance_type='social', name_ar='تأمينات',
            company_share_type='percent', company_share_value=Decimal('18.75'),
            employee_share_type='percent', employee_share_value=Decimal('11'),
            start_date=date(2026, 1, 1),
        )
        self.attend_all()
        # سياسة التأمينات بتكسب، والإعداد القديم مش بيتجمع عليها
        self.assertMoney(self.payroll()['insurance_deduction'], 990)

    def test_tax_on_earned_salary(self):
        tp = TaxPolicy._base_manager.create(
            company=self.company, start_date=date(2026, 1, 1), personal_exemption_single=Decimal('0'),
            tax_brackets=[{'from': 0, 'to': None, 'rate': 10}],
        )
        self.assertIsNotNone(tp)
        self._rule = AllowanceRule._base_manager.create(
            company=self.company, name='سكن', allowance_type='housing', calculation_type='fixed_monthly',
            fixed_amount=Decimal('1000'), start_date=date(2026, 1, 1),
        )
        self.attend_all()
        p = self.payroll()
        # الوعاء = 10000 شهري × 12 = 120000 × 10% / 12 = 1000
        self.assertMoney(p['tax_deduction'], 1000)


# ═══════════════════════════════════════════════════════════════
# 9) نهاية الخدمة
# ═══════════════════════════════════════════════════════════════
class EndOfServiceTests(PayrollScenarioBase):
    def test_tiers_with_web_keys(self):
        pol = EndOfServicePolicy._base_manager.create(
            company=self.company, name='نهاية خدمة', min_service_months=12, start_date=date(2026, 1, 1),
            service_tiers=[
                {'from_year': 0, 'to_year': 5, 'months_per_year': 0.5},
                {'from_year': 5, 'to_year': None, 'months_per_year': 1},
            ],
        )
        r = pol.calculate_eos(8, 10000, 'termination')
        # 5 سنين × نص شهر + 3 سنين × شهر = 5.5 شهر
        self.assertAlmostEqual(r['total_months'], 5.5)


    def test_tiers_old_keys(self):
        pol = EndOfServicePolicy._base_manager.create(
            company=self.company, name='نهاية خدمة', min_service_months=12, start_date=date(2026, 1, 1),
            service_tiers=[{'from_years': 0, 'to_years': None, 'months_per_year': 1}],
        )
        self.assertAlmostEqual(pol.calculate_eos(4, 10000, 'termination')['total_months'], 4)


# ═══════════════════════════════════════════════════════════════
# 10) شاشات مركز السياسات (API)
# ═══════════════════════════════════════════════════════════════
class PolicyApiTests(PayrollScenarioBase):
    BASE = '/attendance/api/mobile/manager/'

    def setUp(self):
        super().setUp()
        from rest_framework.test import APIClient
        self.admin = User.objects.create_user(username='owner', password='x', company=self.company, role='company_admin')
        self.client_api = APIClient()
        self.client_api.force_authenticate(self.admin)

    def _create_policy(self, **extra):
        payload = {'name': 'سياسة', 'effective_from': '2026-01-01', 'late_rules': [
            {'from_minutes': 1, 'to_minutes': 999, 'deduction_type': 'fixed_amount', 'deduction_value': 50},
        ]}
        payload.update(extra)
        r = self.client_api.post(self.BASE + 'attendance-policy/', payload, format='json')
        self.assertIn(r.status_code, (200, 201), r.content)
        return r.json()['policy']['id']

    def test_web_created_policy_with_scope_applies_after_approval(self):
        pid = self._create_policy(assignment_type='branch', branch_id=self.branch.id)
        self.assertEqual(AttendancePolicyAssignment._base_manager.filter(policy_id=pid, branch=self.branch).count(), 1)
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 20)  # لسه مسودة
        r = self.client_api.post(self.BASE + f'attendance-policy/{pid}/approve/', {}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertMoney(self.payroll()['late_deduction'], 50)

    def test_approving_second_policy_keeps_first(self):
        p1 = self._create_policy(assignment_type='branch', branch_id=self.branch.id)
        self.client_api.post(self.BASE + f'attendance-policy/{p1}/approve/', {}, format='json')
        p2 = self._create_policy(name='سياسة فرع 2', assignment_type='branch', branch_id=self.branch2.id)
        self.client_api.post(self.BASE + f'attendance-policy/{p2}/approve/', {}, format='json')
        self.assertEqual(AttendancePolicy._base_manager.get(id=p1).status, 'active')
        self.assertEqual(AttendancePolicy._base_manager.get(id=p2).status, 'active')
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 50)

    def test_new_policy_same_scope_replaces_old(self):
        p1 = self._create_policy(assignment_type='company')
        self.client_api.post(self.BASE + f'attendance-policy/{p1}/approve/', {}, format='json')
        p2 = self._create_policy(name='جديدة', assignment_type='company', late_rules=[
            {'from_minutes': 1, 'to_minutes': 999, 'deduction_type': 'fixed_amount', 'deduction_value': 10},
        ])
        self.client_api.post(self.BASE + f'attendance-policy/{p2}/approve/', {}, format='json')
        self.attend_all(overrides={1: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 10)

    def test_leave_policy_saves_type_days(self):
        from leaves.models import LeaveType, LeavePolicyTypeRule
        LeaveType._base_manager.create(company=self.company, name='سنوي', category='annual', days_allowed=21)
        sick = LeaveType._base_manager.create(company=self.company, name='مرضي', category='sick', days_allowed=0)
        r = self.client_api.post(self.BASE + 'leave-policy/', {
            'name': 'إجازات', 'effective_from': '2026-01-01', 'annual_days': 21, 'sick_days': 14,
            'casual_days': 7, 'maternity_days': 90, 'paternity_days': 3, 'unpaid_allowed': True,
            'carry_forward_enabled': True, 'max_carry_forward_days': 5,
            'tiers': [{'from_months': 0, 'to_months': None, 'annual_entitlement_days': 21}],
        }, format='json')
        self.assertIn(r.status_code, (200, 201), r.content)
        pol = r.json()['policy']
        self.assertEqual(pol['sick_days'], 14)
        self.assertTrue(pol['carry_forward_enabled'])
        rule = LeavePolicyTypeRule._base_manager.get(policy_id=pol['id'], leave_type=sick)
        self.assertEqual(float(rule.fixed_days), 14)

    def test_leave_entitlement_per_type(self):
        from leaves.models import LeaveType, LeavePolicy, LeavePolicyTier
        from leaves.services_leave_accrual import calculate_employee_leave_entitlement
        annual = LeaveType._base_manager.create(company=self.company, name='سنوي', category='annual', days_allowed=15)
        maternity = LeaveType._base_manager.create(company=self.company, name='وضع', category='maternity', days_allowed=90)
        pol = LeavePolicy._base_manager.create(company=self.company, name='x', effective_from=date(2026, 1, 1), status='active')
        LeavePolicyTier._base_manager.create(policy=pol, from_months=0, to_months=None, annual_entitlement_days=21)
        self.assertEqual(float(calculate_employee_leave_entitlement(self.emp, annual)), 21)
        self.assertEqual(float(calculate_employee_leave_entitlement(self.emp, maternity)), 90)

    def test_eos_calculator_web_payload(self):
        r = self.client_api.post(self.BASE + 'eos/calculate/', {
            'years_of_service': 8, 'monthly_salary': 10000, 'termination_reason': 'resignation',
            'service_tiers': [
                {'from_year': 0, 'to_year': 5, 'months_per_year': 0.5},
                {'from_year': 5, 'to_year': None, 'months_per_year': 1},
            ],
            'termination_adjustments': {'resignation': 50, 'termination': 100},
            'min_service_months': 12,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        d = r.json()
        self.assertAlmostEqual(d['total_months_earned'], 5.5)
        self.assertAlmostEqual(d['gross_benefit'], 55000)
        self.assertAlmostEqual(d['final_benefit'], 27500)

    def test_eos_policy_saves_reason_percents(self):
        r = self.client_api.post(self.BASE + 'eos/policies/', {
            'name': 'نهاية خدمة', 'service_tiers': [{'from_year': 0, 'to_year': None, 'months_per_year': 1}],
            'termination_adjustments': {'resignation': 40, 'death': 100},
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        pol = EndOfServicePolicy._base_manager.get(id=r.json()['policy']['id'])
        self.assertEqual(float(pol.percent_on_resignation), 40)


# ═══════════════════════════════════════════════════════════════
# 11) سيناريوهات مركبة ودورات مختلفة
# ═══════════════════════════════════════════════════════════════
class CutoffCycleTests(PayrollScenarioBase):
    """دورة مرتب من 21 الشهر اللي فات لـ 20 الشهر ده"""

    def setUp(self):
        super().setUp()
        self.company.payroll_cycle_type = 'cutoff_day'
        self.company.payroll_cutoff_day = 20
        self.company.save()
        self.emp.company = self.company

    def _period_workdays(self):
        d, out = date(2026, 8, 21), []
        while d <= date(2026, 9, 20):
            if d.weekday() not in (4, 5):
                out.append(d)
            d += timedelta(days=1)
        return out

    def test_period_and_absence(self):
        days = self._period_workdays()
        self.assertEqual(len(days), 21)
        for d in days:
            if d != date(2026, 8, 24):
                self.attend(d, in_hm=(9, 15) if d == date(2026, 9, 2) else (9, 0))
        p = self.payroll()
        self.assertEqual(p['total_working_days'], 21)
        self.assertEqual(p['absent_days'], 1)
        self.assertMoney(p['absence_deduction'], 300)
        self.assertMoney(p['late_deduction'], 15)
        self.assertMoney(p['net_salary'], 9000 - 315)


class MissionTests(PayrollScenarioBase):
    def test_mission_day_without_attendance_not_absent(self):
        from attendance.models import DailyAssignment
        DailyAssignment._base_manager.create(company=self.company, employee=self.emp, date=D(1), day_type='mission_day')
        self.attend_all(except_days=(1,))
        p = self.payroll()
        self.assertEqual(p['absent_days'], 0)
        self.assertEqual(p['mission_days'], 1)
        self.assertMoney(p['net_salary'], 9000)

    def test_mission_day_late_not_deducted(self):
        from attendance.models import DailyAssignment
        DailyAssignment._base_manager.create(company=self.company, employee=self.emp, date=D(1), day_type='mission_day')
        self.attend_all(overrides={1: {'in_hm': (11, 0)}})
        self.assertMoney(self.payroll()['late_deduction'], 0)


class MoreRuleShapesTests(PayrollScenarioBase):
    def test_late_percent_basic_tier(self):
        self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'percent_basic', 'value': 1}])
        self.attend_all(overrides={1: {'in_hm': (9, 5)}, 2: {'in_hm': (9, 50)}})
        self.assertMoney(self.payroll()['late_deduction'], 180)

    def test_late_minute_beyond_last_tier(self):
        # شرائح من 1 لـ 30 بس، والتأخير 45 → آخر شريحة (25) + 15 دقيقة × 1 جنيه
        self.penalty_rule('late_arrival', [{'from': 1, 'to': 30, 'deduction_type': 'fixed_total', 'value': 25}])
        self.attend_all(overrides={1: {'in_hm': (9, 45)}, 2: {'in_hm': (9, 10)}})
        self.assertMoney(self.payroll()['late_deduction'], 25 + 40)

    def test_overtime_fixed_total(self):
        self.bonus_rule('overtime', [{'from': 0, 'to': None, 'value_type': 'fixed_total', 'value': 200}])
        self.attend_all(overrides={1: {'out_hm': (18, 0)}, 2: {'out_hm': (18, 0)}})
        self.assertMoney(self.payroll()['overtime_bonus'], 200)

    def test_overtime_tier_by_monthly_hours(self):
        self.bonus_rule('overtime', [
            {'from': 0, 'to': 5, 'value_type': 'multiplier', 'value': 1.5},
            {'from': 5.01, 'to': None, 'value_type': 'multiplier', 'value': 2},
        ])
        self.attend_all(overrides={1: {'out_hm': (20, 0)}, 2: {'out_hm': (20, 0)}})
        # 6 ساعات في الشهر → شريحة ×2 → 6 × 37.5 × 2
        self.assertMoney(self.payroll()['overtime_bonus'], 450)

    def test_night_bonus_rule_hours(self):
        night = Shift._base_manager.create(
            company=self.company, name='ليلي', start_time=time(22), end_time=time(6), break_duration=0,
            crosses_midnight=True, shift_type='night',
        )
        ShiftAssignment._base_manager.create(
            company=self.company, shift=night, assignment_type='employee', employee=self.emp,
            start_date=date(2020, 1, 1), is_active=True,
        )
        self.bonus_rule('night_shift', [{'from': 0, 'to': None, 'value_type': 'multiplier', 'value': 0.25}])
        for d in SEPT_WORKDAYS:
            self.attend(d, in_hm=(22, 0), out_hm=(6, 0))
        # 22 يوم × 8 ساعات × 37.5 × 0.25
        self.assertMoney(self.payroll()['night_allowance'], 1650)

    def test_penalty_rule_versions_by_date(self):
        old = self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'fixed_total', 'value': 10}])
        old.end_date = D(15)
        old.is_superseded = True
        old.save()
        new = self.penalty_rule('late_arrival', [{'from': 1, 'to': None, 'deduction_type': 'fixed_total', 'value': 40}])
        new.start_date = D(16)
        new.version_number = 2
        new.previous_version = old
        new.save()
        self.attend_all(overrides={2: {'in_hm': (9, 20)}, 22: {'in_hm': (9, 20)}})
        self.assertMoney(self.payroll()['late_deduction'], 50)

    def test_permission_request_bigger_than_late(self):
        self.attend_all(overrides={1: {'in_hm': (9, 30)}})
        _permission_request(self.emp, D(1), 1)
        p = self.payroll()
        self.assertMoney(p['late_deduction'], 0)
        self.assertEqual(p['approved_late_minutes'], 30)

    def test_hr_manager_exempt(self):
        self.emp.user.role = 'hr_manager'
        self.emp.user.save()
        self.attend_all(except_days=(1, 2), overrides={3: {'in_hm': (11, 0)}})
        p = self.payroll()
        self.assertMoney(p['total_deductions'], 0)
        self.assertMoney(p['net_salary'], 9000)


class RealisticMonthTests(PayrollScenarioBase):
    """شهر فيه كل حاجة مع بعض — الرقم النهائي محسوب يدوي"""

    def test_full_month(self):
        self.penalty_rule('late_arrival', LatePenaltyRuleTests.TIERS)
        self.penalty_rule('absence', [{'from': 1, 'to': None, 'deduction_type': 'full_day'}])
        self.bonus_rule('overtime', [{'from': 0, 'to': None, 'value_type': 'multiplier', 'value': 1.5}])
        AllowanceRule._base_manager.create(
            company=self.company, name='مواصلات', allowance_type='transport', calculation_type='per_day',
            fixed_amount=Decimal('20'), start_date=date(2026, 1, 1),
        )
        CompanyInsurancePolicy._base_manager.create(
            company=self.company, insurance_type='social', name_ar='تأمينات',
            company_share_type='percent', company_share_value=Decimal('18.75'),
            employee_share_type='percent', employee_share_value=Decimal('11'),
            start_date=date(2026, 1, 1),
        )
        TaxPolicy._base_manager.create(
            company=self.company, start_date=date(2026, 1, 1), personal_exemption_single=Decimal('0'),
            tax_brackets=[{'from': 0, 'to': None, 'rate': 10}],
        )
        self.attend_all(except_days=(6,), overrides={
            1: {'in_hm': (9, 10)},       # 20
            2: {'in_hm': (9, 30)},       # 75
            3: {'out_hm': (19, 0)},      # أوفر تايم ساعتين
        })
        p = self.payroll()
        self.assertMoney(p['late_deduction'], 95)
        self.assertMoney(p['absence_deduction'], 300)
        self.assertMoney(p['overtime_bonus'], 112.5)
        self.assertMoney(p['transport_allowance'], 420)
        self.assertMoney(p['gross_salary'], 9532.5)
        self.assertMoney(p['insurance_deduction'], 990)
        # (9532.5 - 395 - 990) × 12 × 10% ÷ 12
        self.assertMoney(p['tax_deduction'], 814.75)
        self.assertMoney(p['net_salary'], 7332.75)


class ScreensConsistencyTests(PayrollScenarioBase):
    """نفس الموظف لازم يطلع نفس الصافي في شاشة المرتبات وتفاصيل الموظف"""

    def test_summary_and_detail_match(self):
        from rest_framework.test import APIClient
        owner = User.objects.create_user(username='own2', password='x', company=self.company, role='company_admin')
        api = APIClient()
        api.force_authenticate(owner)
        self.penalty_rule('late_arrival', LatePenaltyRuleTests.TIERS)
        self.attend_all(except_days=(6,), overrides={2: {'in_hm': (9, 30)}})
        expected = self.payroll()['net_salary']
        r1 = api.get('/attendance/api/mobile/manager/payroll/summary/', {'year': YEAR, 'month': MONTH})
        self.assertEqual(r1.status_code, 200, r1.content)
        row = next(e for e in r1.json()['employees'] if e['employee_id'] == self.emp.id)
        r2 = api.get('/attendance/api/mobile/manager/payroll/employee/', {'year': YEAR, 'month': MONTH, 'employee_id': self.emp.id})
        self.assertEqual(r2.status_code, 200, r2.content)
        self.assertMoney(row['net_salary'], expected)
        self.assertMoney(r2.json().get('net_salary', r2.json().get('payroll', {}).get('net_salary')), expected)
        self.assertMoney(expected, 9000 - 75 - 300)


# ═══════════════════════════════════════════════════════════════
# نفس كل السيناريوهات تاني بس المرتب بيقرا من الملخصات اليومية
# (السيرفر بيحسبها بالليل لكل يوم فات)
# ═══════════════════════════════════════════════════════════════
def _summary_variants():
    out = {}
    for name, obj in list(globals().items()):
        if (isinstance(obj, type) and issubclass(obj, PayrollScenarioBase)
                and obj is not PayrollScenarioBase and not name.endswith('ViaSummaries')):
            variant = type(name + 'ViaSummaries', (obj,), {'with_summaries': True, '__module__': __name__})
            out[variant.__name__] = variant
    return out


globals().update(_summary_variants())


class SummaryPathSanityTests(PayrollScenarioBase):
    with_summaries = True

    def test_summaries_are_really_created_and_used(self):
        from attendance.models import DailyAttendanceSummary
        self.attend_all(except_days=(1,), overrides={2: {'in_hm': (9, 20)}})
        p = self.payroll()
        self.assertGreaterEqual(DailyAttendanceSummary._base_manager.filter(employee=self.emp).count(), 22)
        self.assertEqual(DailyAttendanceSummary._base_manager.get(employee=self.emp, date=D(1)).status, 'absent')
        self.assertEqual(DailyAttendanceSummary._base_manager.get(employee=self.emp, date=D(2)).late_minutes, 20)
        self.assertMoney(p['absence_deduction'], 300)
        self.assertMoney(p['late_deduction'], 20)

    def test_stale_absent_summary_with_real_attendance(self):
        from attendance.models import DailyAttendanceSummary
        self.attend_all(except_days=(1,))
        DailyAttendanceSummary.compute_for_day(self.emp, D(1))  # غياب
        self.attend(D(1))  # HR سجل الحضور بعدين
        self.with_summaries = False
        p = self.payroll()
        self.assertEqual(p['absent_days'], 0)
        self.assertMoney(p['net_salary'], 9000)
