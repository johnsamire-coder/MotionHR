"""
اختبارات دفعة 13 (السيرفر مع تصليحات الويب):
525/536 بيانات قايمة الموظفين، 540 الطلبات المعلقة من كل الشهور، 549 شيل موظف من موقع العمل،
562 قايمة البديل في الإجازة المرضية، 722 المهمة اللي نهايتها قبل بدايتها

التشغيل:
  python manage.py test attendance.test_group13_web --settings=motionhr.settings_test
"""
from datetime import timedelta

from django.utils import timezone

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/'


class EmployeeListFieldsTests(ScopeBase):
    def test_list_has_manager_and_user_ids(self):
        r = self.api(self.hr_a).get(f'{M}manager/employees/')
        self.assertEqual(r.status_code, 200)
        rows = {e['id']: e for e in (r.data.get('employees') or r.data.get('results'))}
        self.assertEqual(rows[self.team_a.id]['direct_manager_id'], self.mgr_a.id)
        self.assertEqual(rows[self.team_a.id]['user_id'], self.team_a.user_id)


class PendingAllMonthsTests(ScopeBase):
    def test_old_pending_request_shown_with_all_months(self):
        from requests_app.models import EmployeeRequest
        rq = self.req(self.other_a)
        EmployeeRequest._base_manager.filter(pk=rq.pk).update(created_at=timezone.now() - timedelta(days=70))
        today = timezone.localdate()
        base = f'{M}manager/reports/requests/?year={today.year}&month={today.month}&status=pending'
        c = self.api(self.hr_a)
        ids = lambda r: [d.get('id') for d in r.data.get('details', [])]
        self.assertNotIn(rq.id, ids(c.get(base)))
        self.assertIn(rq.id, ids(c.get(base + '&all_months=1')))


class WorkLocationAssignTests(ScopeBase):
    def loc(self, status='approved'):
        from attendance.models import EmployeeWorkLocation
        return EmployeeWorkLocation._base_manager.create(company=self.a, employee=self.team_a, name='موقع',
                                                         status=status, latitude=30, longitude=31)

    def assigned(self, loc):
        rel = loc.assigned_employees
        return set(rel.through._default_manager.filter(**{rel.source_field_name: loc.id})
                   .values_list(f'{rel.target_field_name}_id', flat=True))

    def test_unchecked_employee_removed(self):
        loc = self.loc()
        url = f'{M}manager/work-locations/{loc.id}/assign-employees/'
        c = self.api(self.hr_a)
        self.assertEqual(c.post(url, {'scope': 'employees', 'employee_ids': [self.team_a.id, self.other_a.id]},
                                format='json').status_code, 200)
        self.assertEqual(self.assigned(loc), {self.team_a.id, self.other_a.id})
        c.post(url, {'scope': 'employees', 'employee_ids': [self.team_a.id]}, format='json')
        self.assertEqual(self.assigned(loc), {self.team_a.id})

    def test_pending_location_refused(self):
        loc = self.loc('pending_hr')
        r = self.api(self.hr_a).post(f'{M}manager/work-locations/{loc.id}/assign-employees/',
                                     {'scope': 'employees', 'employee_ids': [self.team_a.id]}, format='json')
        self.assertEqual(r.status_code, 400)


class SubstituteListTests(ScopeBase):
    def test_manager_gets_substitutes_for_the_employee(self):
        r = self.api(self.mgr_a).get(f'{M}leave-substitutes/?exclude_employee_id={self.team_a.id}')
        self.assertEqual(r.status_code, 200)
        ids = [s['id'] for s in r.data['substitutes']]
        self.assertIn(self.other_a.id, ids)        # موظف عادي زي صاحب الإجازة
        self.assertNotIn(self.team_a.id, ids)      # صاحب الإجازة نفسه
        self.assertNotIn(self.emp_b.id, ids)       # شركة تانية


class MissionTimesTests(ScopeBase):
    def test_end_before_start_refused(self):
        now = timezone.now()
        r = self.api(self.hr_a).post(f'{M}manager/missions/create/', {
            'title': 'زيارة', 'planned_start_time': (now + timedelta(hours=3)).isoformat(),
            'planned_end_time': (now + timedelta(hours=1)).isoformat(), 'employee_ids': [self.team_a.id],
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('النهاية', str(r.data))
