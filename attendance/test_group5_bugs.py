"""
اختبارات دفعة 5 (أعطال مالهاش علاقة بالمرتبات):
71 التذكيرات، 97 الرقم الوظيفي المكرر، 110/177 الأقسام، 149/150/186 إنهاء الخدمة،
152/174 نقل الموظف، 141 الاستدعاء من الإجازة، 48 اعتماد المهمة، 47 نوع إجازة جديد

التشغيل:
  python manage.py test attendance.test_group5_bugs --settings=motionhr.settings_test
"""
from datetime import date, timedelta
from decimal import Decimal

from attendance.test_action_scope import ScopeBase
from companies.models import Branch, Department

M = '/attendance/api/mobile/manager/'


class RemindersTests(ScopeBase):
    def test_reminders_module_runs(self):
        from attendance.reminders import run_all_reminders
        run_all_reminders('checkin')   # قبل كده الملف نفسه كان مابيتحملش (خطأ في الكود)
        run_all_reminders('all')


class EmployeeCodeTests(ScopeBase):
    def test_new_code_skips_used_ones(self):
        from employees.models import Employee
        e1 = self.emp(self.a)
        Employee._base_manager.filter(pk=e1.pk).update(employee_code='EMP00001')
        self.emp(self.a)   # آخر موظف كوده مش EMP (S..)
        e3 = self.emp(self.a)
        Employee._base_manager.filter(pk=e3.pk).update(employee_code='')
        e3.refresh_from_db()
        e3.employee_code = ''
        e3.save()
        self.assertEqual(e3.employee_code, 'EMP00002')


class DepartmentsTests(ScopeBase):
    def test_hr_can_list_departments(self):
        r = self.api(self.hr_a).get(f'{M}departments/list/')
        self.assertEqual(r.status_code, 200)

    def test_manager_without_permission_gets_403_not_500(self):
        r = self.api(self.mgr_a).get(f'{M}departments/list/')
        self.assertEqual(r.status_code, 403)


class OffboardingTests(ScopeBase):
    def test_web_payload_saves_type_date_and_reason(self):
        r = self.api(self.hr_a).post(f'{M}offboarding/{self.other_a.id}/', {
            'termination_type': 'terminated', 'termination_reason': 'غياب متكرر', 'termination_date': '2026-10-15',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.other_a.refresh_from_db()
        self.assertEqual(self.other_a.status, 'terminated')
        self.assertEqual(self.other_a.termination_date, date(2026, 10, 15))
        self.assertEqual(self.other_a.termination_reason, 'غياب متكرر')

    def test_bad_date_message(self):
        r = self.api(self.hr_a).post(f'{M}offboarding/{self.other_a.id}/', {
            'termination_type': 'terminated', 'termination_date': '15-10-2026',
        }, format='json')
        self.assertEqual(r.status_code, 400)


class TransferTests(ScopeBase):
    def test_department_and_branch_change_applied(self):
        d2 = Department.objects.create(company=self.a, name_ar='الحسابات', name_en='Acc')
        b2 = Branch.objects.create(company=self.a, name_ar='فرع 2', name_en='B2')
        r = self.api(self.hr_a).post(f'{M}employees/{self.other_a.id}/transfer/', {
            'new_department_id': d2.id, 'new_branch_id': b2.id, 'reason': 'نقل',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.other_a.refresh_from_db()
        self.assertEqual(self.other_a.department_id, d2.id)
        self.assertEqual(self.other_a.branch_id, b2.id)


class LeaveRecallTests(ScopeBase):
    def test_hr_creates_recall(self):
        from leaves.models import LeaveRecallRequest
        lv = self.leave(self.other_a, 'approved')
        r = self.api(self.hr_a).post('/attendance/api/mobile/leave-recall/create/', {
            'employee_id': self.other_a.id, 'recall_date': str(lv.start_date), 'reason': 'شغل ضروري',
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(LeaveRecallRequest._base_manager.filter(employee=self.other_a).exists())

    def test_manager_cannot_recall_outside_team(self):
        lv = self.leave(self.other_a, 'approved')
        r = self.api(self.mgr_a).post('/attendance/api/mobile/leave-recall/create/', {
            'employee_id': self.other_a.id, 'recall_date': str(lv.start_date), 'reason': 'x',
        }, format='json')
        self.assertEqual(r.status_code, 404)


class MissionApprovalTests(ScopeBase):
    def test_approved_status_and_request_record(self):
        from attendance.missions_models import MissionRequest
        m, _ = self.mission(self.team_a)
        MissionRequest._base_manager.create(mission=m, requested_by=self.team_a, manager=self.mgr_a.user)
        r = self.act(self.mgr_a, 'mission', m)
        self.assertEqual(r.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.status, 'approved')
        mr = MissionRequest._base_manager.get(mission=m)
        self.assertEqual(mr.manager_approval, 'approved')
        self.assertEqual(mr.final_status, 'approved')


class NewLeaveTypeTests(ScopeBase):
    def test_existing_employees_get_balance(self):
        from leaves.models import LeaveBalance, LeaveType
        lt = LeaveType._base_manager.create(company=self.a, name='عارضة', category='casual', days_allowed=7)
        bal = LeaveBalance._base_manager.filter(employee=self.other_a, leave_type=lt, year=date.today().year).first()
        self.assertIsNotNone(bal)
        self.assertEqual(bal.total_days, Decimal('7'))
        # شركة تانية مالهاش دعوة
        self.assertFalse(LeaveBalance._base_manager.filter(employee=self.emp_b, leave_type=lt).exists())
