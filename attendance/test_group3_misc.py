"""
اختبارات باقي الدفعة التالتة:
- 4: شاشات المدير في المهمات مقفولة على الموظف العادي
- 19 و35 و20: الموظف يشوف جزاءاته ومكافآته وسلفه هو بس
- 104 و18 و39: رفض موقع العمل بيرفض فعلاً

التشغيل:
  python manage.py test attendance.test_group3_misc --settings=motionhr.settings_test
"""
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from attendance.test_action_scope import ScopeBase


class ManagerMissionScreensTests(ScopeBase):
    def test_employee_cannot_create_or_list_manager_missions(self):
        from attendance.missions_models import Mission
        c = self.api(self.other_a)
        self.assertEqual(c.get('/attendance/api/mobile/manager/missions/').status_code, 403)
        now = timezone.now()
        r = c.post('/attendance/api/mobile/manager/missions/create/', {
            'title': 'لنفسي', 'planned_start_time': (now + timedelta(days=1)).isoformat(),
            'planned_end_time': (now + timedelta(days=1, hours=2)).isoformat(),
            'employee_ids': [self.other_a.id],
        }, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Mission._base_manager.filter(title='لنفسي').exists())

    def test_manager_still_lists(self):
        self.assertEqual(self.api(self.mgr_a).get('/attendance/api/mobile/manager/missions/').status_code, 200)


class ManualEntriesVisibilityTests(ScopeBase):
    def penalty(self, emp, amount):
        from attendance.company_policy_models import ManualPenalty
        today = date.today()
        return ManualPenalty._base_manager.create(
            company=emp.company, employee=emp, requested_by=self.hr_a.user, amount_type='fixed',
            amount_value=Decimal(amount), reason='ت', target_year=today.year, target_month=today.month,
        )

    def installment(self, emp, total):
        from attendance.payroll_pro_models import PayrollInstallment
        today = date.today()
        return PayrollInstallment._base_manager.create(
            company=emp.company, employee=emp, description='سلفة', total_amount=Decimal(total), monthly_amount=Decimal('100'),
            start_month=today.month, start_year=today.year,
        )

    def ids(self, r):
        return sorted(x['id'] for x in r.json()['results'])

    def test_employee_sees_only_own_penalties(self):
        mine = self.penalty(self.other_a, 50)
        theirs = self.penalty(self.team_a, 70)
        c = self.api(self.other_a)
        r = c.get('/attendance/api/mobile/manager/entries/penalty/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.ids(r), [mine.id])
        self.assertEqual(c.get(f'/attendance/api/mobile/manager/entries/penalty/{theirs.id}/').status_code, 404)
        self.assertEqual(c.get(f'/attendance/api/mobile/manager/entries/penalty/{mine.id}/').status_code, 200)

    def test_manager_sees_team_hr_sees_all(self):
        a = self.penalty(self.other_a, 50)
        b = self.penalty(self.team_a, 70)
        self.assertEqual(self.ids(self.api(self.mgr_a).get('/attendance/api/mobile/manager/entries/penalty/')), [b.id])
        self.assertEqual(self.ids(self.api(self.hr_a).get('/attendance/api/mobile/manager/entries/penalty/')), sorted([a.id, b.id]))

    def test_employee_sees_only_own_advances(self):
        mine = self.installment(self.other_a, 1000)
        self.installment(self.team_a, 3000)
        r = self.api(self.other_a).get('/attendance/api/mobile/manager/entries/installment/')
        self.assertEqual(self.ids(r), [mine.id])
        self.assertEqual(len(self.api(self.hr_a).get('/attendance/api/mobile/manager/entries/installment/').json()['results']), 2)


class RejectWorkLocationTests(ScopeBase):
    def location(self, emp):
        from attendance.models import EmployeeWorkLocation
        return EmployeeWorkLocation._base_manager.create(
            company=emp.company, employee=emp, name='موقع', latitude=Decimal('30.0'), longitude=Decimal('31.0'),
            status='pending_hr',
        )

    def test_reject_really_rejects(self):
        loc = self.location(self.other_a)
        url = f'/attendance/api/mobile/manager/work-locations/{loc.id}/reject/'
        c = self.api(self.hr_a)
        self.assertEqual(c.post(url, {'reason': ''}, format='json').status_code, 400)
        r = c.post(url, {'reason': 'بعيد'}, format='json')
        self.assertEqual(r.status_code, 200)
        loc.refresh_from_db()
        self.assertEqual(loc.status, 'rejected')
        self.assertEqual(loc.rejection_reason, 'بعيد')

    def test_reject_other_company_not_found(self):
        loc = self.location(self.emp_b)
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/work-locations/{loc.id}/reject/', {'reason': 'x'}, format='json')
        self.assertEqual(r.status_code, 404)
