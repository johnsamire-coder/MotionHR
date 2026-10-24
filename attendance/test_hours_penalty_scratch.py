"""
اختبار نوع خصم "ساعات" في جزاءات التأخير/الغياب — التأكد إنه بيأثر في المرتب.

الأساس من test_payroll_scenarios: مرتب 9000، يوم = 300، شيفت 8 ساعات → ساعة = 37.5

التشغيل:
    python manage.py test attendance.test_hours_penalty_scratch --settings=motionhr.settings_scratch --keepdb
"""
from datetime import date

from .test_payroll_scenarios import PayrollScenarioBase


class HoursPenaltyTests(PayrollScenarioBase):

    def test_late_hours_tier_deducts_hourly_times_value(self):
        # ساعتين عن كل يوم تأخير = 75 جنيه
        self.penalty_rule('late_arrival', [
            {'from': 1, 'to': None, 'deduction_type': 'hours', 'value': 2},
        ])
        self.attend_all(overrides={1: {'in_hm': (9, 10)}, 2: {'in_hm': (9, 30)}})
        p = self.payroll()
        self.assertMoney(p['late_deduction'], 150)  # 75 + 75
        self.assertMoney(p['net_salary'], 9000 - 150)

    def test_late_hours_fractional_value(self):
        # نص ساعة = 18.75 جنيه
        self.penalty_rule('late_arrival', [
            {'from': 1, 'to': None, 'deduction_type': 'hours', 'value': 0.5},
        ])
        self.attend_all(overrides={3: {'in_hm': (9, 5)}})
        self.assertMoney(self.payroll()['late_deduction'], 18.75)

    def test_hours_tier_per_tier_ranges(self):
        # 1-15 دقيقة → ساعة (37.5) ، 16-60 → ساعتين (75) ، أكبر → 4 ساعات (150)
        self.penalty_rule('late_arrival', [
            {'from': 1, 'to': 15, 'deduction_type': 'hours', 'value': 1},
            {'from': 16, 'to': 60, 'deduction_type': 'hours', 'value': 2},
            {'from': 61, 'to': None, 'deduction_type': 'hours', 'value': 4},
        ])
        self.attend_all(overrides={
            1: {'in_hm': (9, 10)},    # 10د → 37.5
            2: {'in_hm': (9, 30)},    # 30د → 75
            3: {'in_hm': (10, 30)},   # 90د → 150
        })
        self.assertMoney(self.payroll()['late_deduction'], 37.5 + 75 + 150)

    def test_absence_hours_tier(self):
        # يوم الغياب = خصم 8 ساعات = 300 جنيه (يوم كامل)
        self.penalty_rule('absence', [
            {'from': 1, 'to': None, 'deduction_type': 'hours', 'value': 8},
        ])
        self.attend_all(except_days=(1,))
        p = self.payroll()
        self.assertMoney(p['absence_deduction'], 300)

    def test_early_leave_hours_tier(self):
        self.penalty_rule('early_leave', [
            {'from': 1, 'to': None, 'deduction_type': 'hours', 'value': 1},
        ])
        self.attend_all(overrides={1: {'out_hm': (16, 20), 'early_leave_minutes': 40}})
        p = self.payroll()
        self.assertMoney(p['early_leave_deduction'], 37.5)
