"""
اختبارات دفعة 9 (صلاحيات وحماية مالهاش علاقة بالمرتبات):
107/108 المهمات، 293 حالة المهمة، 294/295 تقييم الزيارة، 299 مسح الإعلانات، 301/302 اللائحة،
303 التذكيرات، 305 الصلاحيات السيادية، 380 حساب من غير شركة، 388 خط السير، 390 الإجازة مرتين،
138 تعديل الطلب، 397 سجل المرتب، 398 حالة الإجازة، 400/401 الهيكل وملف الموظف، 405 شجرة المديرين، 87 الدخول

التشغيل:
  python manage.py test attendance.test_group9_scope --settings=motionhr.settings_test
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/'


class MissionTests(ScopeBase):
    def started(self, *emps):
        from attendance.missions_models import Mission, MissionAssignment
        now = timezone.now()
        m = Mission._base_manager.create(company=self.a, title='زيارة', planned_start_time=now,
                                         planned_end_time=now + timedelta(hours=2), created_by=self.mgr_a.user,
                                         status='in_progress')
        return m, [MissionAssignment._base_manager.create(company=self.a, mission=m, employee=e, status='in_progress')
                   for e in emps]

    def test_first_finisher_does_not_close_for_all(self):
        m, (a1, a2) = self.started(self.team_a, self.other_a)
        r = self.api(self.team_a).post(f'{M}employee/missions/assignments/{a1.id}/end/', {}, format='json')
        self.assertEqual(r.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.status, 'in_progress')      # لسه فيه موظف تاني شغال
        self.api(self.other_a).post(f'{M}employee/missions/assignments/{a2.id}/end/', {}, format='json')
        m.refresh_from_db()
        self.assertEqual(m.status, 'completed')

    def test_force_cancel_stops_assignments(self):
        m, (a1,) = self.started(self.team_a)
        m.status = 'approved'
        m.save()
        r = self.api(self.hr_a).post(f'{M}manager/missions/{m.id}/force-cancel/', {'reason': 'اتلغت'}, format='json')
        self.assertEqual(r.data['affected_assignments'], 1)
        a1.refresh_from_db()
        self.assertEqual(a1.status, 'rejected')
        self.assertIsNotNone(a1.ended_at)

    def test_update_cannot_set_unknown_status(self):
        m, _ = self.mission(self.team_a)
        c = self.api(self.hr_a)
        self.assertEqual(c.patch(f'{M}manager/missions/{m.id}/update/', {'status': 'xyz'}, format='json').status_code, 400)
        self.assertEqual(c.patch(f'{M}manager/missions/{m.id}/update/', {'status': 'completed'}, format='json').status_code, 400)
        self.assertEqual(c.patch(f'{M}manager/missions/{m.id}/update/', {'status': 'approved'}, format='json').status_code, 200)

    def test_feedback_hidden_from_unrelated_employee(self):
        from attendance.missions_models import MissionFeedback
        m, _ = self.mission(self.team_a)
        MissionFeedback._base_manager.create(mission=m, written_by=self.team_a, internal_notes='سري')
        self.assertEqual(self.api(self.other_a).get(f'{M}missions/{m.id}/feedback/').status_code, 404)
        self.assertEqual(self.api(self.team_a).get(f'{M}missions/{m.id}/feedback/').status_code, 200)
        self.assertEqual(self.api(self.mgr_a).get(f'{M}missions/{m.id}/feedback/').status_code, 200)
        self.assertEqual(self.api(self.hr_a).get(f'{M}missions/{m.id}/feedback/').status_code, 200)

    def test_followup_owner_from_other_company_ignored(self):
        from attendance.missions_models import MissionFeedback
        m, a = self.mission(self.team_a)
        a.is_lead, a.status = True, 'completed'
        a.save()
        self.api(self.team_a).post(f'{M}missions/{m.id}/feedback/submit/',
                                   {'interest_rating': 3, 'followup_owner_id': self.emp_b.id}, format='json')
        fb = MissionFeedback._base_manager.get(mission=m)
        self.assertIsNone(fb.followup_owner_id)


class AnnouncementDeleteTests(ScopeBase):
    def test_manager_cannot_delete_hr_announcement(self):
        from accounts.company_announcements import CompanyAnnouncement
        ann = CompanyAnnouncement._base_manager.create(company=self.a, title='t', message='m', created_by=self.hr_a.user)
        r = self.api(self.mgr_a).delete(f'{M}manager/announcements/{ann.id}/delete/', {'send_deletion_notice': False}, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(CompanyAnnouncement._base_manager.filter(id=ann.id).exists())


class CharterTests(ScopeBase):
    def charter(self):
        from companies.models import CharterAcceptance, WorkCharter
        ch = WorkCharter._base_manager.create(company=self.a, title='لائحة', content='نص 1', is_active=True)
        CharterAcceptance._base_manager.create(employee=self.team_a, charter=ch)
        return ch

    def test_manager_cannot_delete_and_hr_delete_keeps_signatures(self):
        from companies.models import CharterAcceptance, WorkCharter
        ch = self.charter()
        self.assertEqual(self.api(self.mgr_a).delete(f'{M}manager/charters/{ch.id}/delete/').status_code, 403)
        self.assertEqual(self.api(self.hr_a).delete(f'{M}manager/charters/{ch.id}/delete/').status_code, 200)
        ch = WorkCharter._base_manager.get(id=ch.id)
        self.assertFalse(ch.is_active)
        self.assertEqual(CharterAcceptance._base_manager.filter(charter=ch).count(), 1)

    def test_editing_text_asks_for_new_signatures(self):
        from companies.models import CharterAcceptance
        ch = self.charter()
        r = self.api(self.hr_a).put(f'{M}manager/charters/{ch.id}/update/', {'content': 'نص 2'}, format='multipart')
        self.assertEqual(r.status_code, 200)
        ch.refresh_from_db()
        self.assertEqual(ch.version, 2)
        self.assertFalse(CharterAcceptance._base_manager.filter(charter=ch).exists())

    def test_settings_only_change_keeps_signatures(self):
        from companies.models import CharterAcceptance
        ch = self.charter()
        self.api(self.hr_a).put(f'{M}manager/charters/{ch.id}/update/', {'is_mandatory': 'true'}, format='multipart')
        ch.refresh_from_db()
        self.assertEqual(ch.version, 1)
        self.assertTrue(CharterAcceptance._base_manager.filter(charter=ch).exists())


class SmallGuardsTests(ScopeBase):
    def test_reminder_trigger_is_super_admin_only(self):
        r = self.api(self.owner_a).post(f'{M}manager/reminders/trigger/', {'type': 'checkin'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_bulk_override_cannot_grant_sovereign(self):
        from accounts.permissions_models import UserPermissionOverride
        r = self.api(self.owner_a).post(f'{M}manager/permissions/override/bulk/', {
            'target_type': 'department', 'target_id': self.team_a.department_id,
            'permissions': [{'code': 'roles.manage', 'scope': 'company', 'is_granted': True}],
        }, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(UserPermissionOverride._base_manager.filter(permission='roles.manage').exists())

    def test_user_without_company_sees_no_employees(self):
        from accounts.models import User
        from attendance.api_reports import _get_company_employees
        u = User.objects.create_user(username='nocomp', password='x', role='hr_manager')
        self.assertEqual(_get_company_employees(u).count(), 0)

    def test_manager_route_only_for_team(self):
        c = self.api(self.mgr_a)
        self.assertEqual(c.get(f'{M}manager/route/?employee_id={self.other_a.id}').status_code, 404)
        self.assertEqual(c.get(f'{M}manager/route/?employee_id={self.team_a.id}').status_code, 200)

    def test_on_leave_status_keeps_account_active(self):
        r = self.api(self.hr_a).post(f'{M}manager/employees/{self.team_a.id}/toggle-status/', {'status': 'on_leave'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.team_a.user.refresh_from_db()
        self.assertTrue(self.team_a.user.is_active)
        self.api(self.hr_a).post(f'{M}manager/employees/{self.team_a.id}/toggle-status/', {'status': 'suspended'}, format='json')
        self.team_a.user.refresh_from_db()
        self.assertFalse(self.team_a.user.is_active)


class LeaveDoubleSubmitTests(ScopeBase):
    def test_same_leave_twice_makes_one_request(self):
        from leaves.models import LeaveBalance, LeaveRequest, LeaveType
        lt = LeaveType._base_manager.create(company=self.a, name='سنوي', category='annual', days_allowed=21)
        d = date.today() + timedelta(days=20)
        LeaveBalance._base_manager.update_or_create(company=self.a, employee=self.team_a, leave_type=lt, year=d.year,
                                                    defaults={'total_days': 21})
        body = {'leave_type_id': lt.id, 'start_date': d.isoformat(), 'end_date': d.isoformat(), 'reason': 'سفر'}
        c = self.api(self.team_a)
        self.assertEqual(c.post(f'{M}leave-request/', body, format='json').status_code, 200)
        self.assertEqual(c.post(f'{M}leave-request/', body, format='json').status_code, 400)
        self.assertEqual(LeaveRequest._base_manager.filter(employee=self.team_a).count(), 1)
        bal = LeaveBalance._base_manager.get(employee=self.team_a, leave_type=lt, year=d.year)
        self.assertEqual(bal.pending_days, Decimal('1'))


class EditRequestTests(ScopeBase):
    def test_amount_cannot_change_after_submit(self):
        rq = self.req(self.team_a)
        rq.amount = Decimal('1000')
        rq.save()
        c = self.api(self.team_a)
        self.assertEqual(c.patch(f'{M}my-requests/{rq.id}/edit/', {'amount': '50000'}, format='json').status_code, 400)
        self.assertEqual(c.patch(f'{M}my-requests/{rq.id}/edit/', {'amount': '1000.00', 'subject': 'سلفة'}, format='json').status_code, 200)
        rq.refresh_from_db()
        self.assertEqual((rq.amount, rq.subject), (Decimal('1000'), 'سلفة'))


class EmployeeManagementTests(ScopeBase):
    def test_manager_cannot_create_branch_but_can_list(self):
        c = self.api(self.mgr_a)
        self.assertEqual(c.post(f'{M}manager/branches/', {'name_ar': 'فرع جديد'}, format='json').status_code, 403)
        self.assertEqual(c.get(f'{M}manager/branches/').status_code, 200)

    def test_manager_sees_only_team_profiles(self):
        c = self.api(self.mgr_a)
        self.assertEqual(c.get(f'{M}manager/employees/{self.other_a.id}/').status_code, 404)
        self.assertEqual(c.get(f'{M}manager/employees/{self.team_a.id}/').status_code, 200)

    def test_hierarchy_tree_survives_cycle(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.mgr_a.pk).update(direct_manager=self.team_a)
        r = self.api(self.owner_a).get(f'{M}manager/hierarchy-tree/')
        self.assertEqual(r.status_code, 200)
        names = str(r.data['root'])
        self.assertIn(f"'id': {self.mgr_a.id}", names)
        self.assertIn(f"'id': {self.team_a.id}", names)
        self.assertIn("'job_title_ar': 'م'", names)


class LoginLockTests(ScopeBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.other_a.user.set_password('Pass12345')
        self.other_a.user.save()

    def test_locks_after_ten_wrong_passwords(self):
        c = APIClient()
        u = self.other_a.user.username
        for _ in range(10):
            self.assertEqual(c.post(f'{M}login/', {'username': u, 'password': 'wrong'}, format='json').status_code, 401)
        r = c.post(f'{M}login/', {'username': u, 'password': 'Pass12345'}, format='json')
        self.assertEqual(r.status_code, 429)
        cache.clear()
        self.assertEqual(c.post(f'{M}login/', {'username': u, 'password': 'Pass12345'}, format='json').status_code, 200)
