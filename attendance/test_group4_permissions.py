"""
اختبارات دفعة 4 (الصلاحيات):
151 إعادة باسورد صاحب الشركة، 154 إيقاف/إنهاء خدمة صاحب الشركة، 153 الحذف النهائي، 158 إضافة موظفين،
163 أيام العمل، 167 اللائحة، 95 موقع الشركة، 105 اعتماد الموقع لنفسه، 93 بند لنفسه، 106 السلف،
84 تقرير المواقع، 137/202 مدير مالوش ملف، 156/157 تقارير المدير ومسير الرواتب، 176/205/121 الإعلانات، 109 بدء مأمورية ملغية

التشغيل:
  python manage.py test attendance.test_group4_permissions --settings=motionhr.settings_test
"""
import json
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import User
from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/manager/'


class AccountActionTests(ScopeBase):
    def test_hr_cannot_reset_owner_password(self):
        old_hash = self.owner_a.user.password
        r = self.api(self.hr_a).post(f'{M}employees/{self.owner_a.id}/reset-password/', {}, format='json')
        self.assertEqual(r.status_code, 403)
        self.owner_a.user.refresh_from_db()
        self.assertEqual(self.owner_a.user.password, old_hash)

    def test_hr_resets_employee_password(self):
        r = self.api(self.hr_a).post(f'{M}employees/{self.other_a.id}/reset-password/', {}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_owner_resets_hr_password(self):
        self.assertEqual(self.api(self.owner_a).post(f'{M}employees/{self.hr_a.id}/reset-password/', {}, format='json').status_code, 200)

    def test_hr_cannot_suspend_or_offboard_owner_or_self(self):
        c = self.api(self.hr_a)
        for who in (self.owner_a, self.hr_a):
            self.assertEqual(c.post(f'{M}employees/{who.id}/toggle-status/', {'status': 'suspended'}, format='json').status_code, 403)
            self.assertEqual(c.post(f'{M}offboarding/{who.id}/web/', {'termination_type': 'terminated', 'reason': 'x'}, format='json').status_code, 403)
            who.refresh_from_db()
            who.user.refresh_from_db()
            self.assertEqual(who.status, 'active')
            self.assertTrue(who.user.is_active)

    def test_hr_suspends_employee(self):
        r = self.api(self.hr_a).post(f'{M}employees/{self.other_a.id}/toggle-status/', {'status': 'suspended'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_hr_cannot_edit_owner_salary(self):
        r = self.api(self.hr_a).patch(f'{M}employees/{self.owner_a.id}/update/', {'basic_salary': 1}, format='json')
        self.assertEqual(r.status_code, 403)
        self.owner_a.refresh_from_db()
        self.assertEqual(self.owner_a.basic_salary, Decimal('5000'))

    def test_delete_keeps_employee_with_history(self):
        from leaves.models import LeaveRequest
        self.leave(self.other_a, 'approved')
        r = self.api(self.owner_a).post(f'{M}employees/{self.other_a.id}/delete/', {}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(LeaveRequest._base_manager.filter(employee=self.other_a).exists())
        new = self.emp(self.a)
        self.assertEqual(self.api(self.owner_a).post(f'{M}employees/{new.id}/delete/', {}, format='json').status_code, 200)

    def test_manager_cannot_create_employee(self):
        r = self.api(self.mgr_a).post(f'{M}employees/create/', {'first_name_ar': 'جديد'}, format='json')
        self.assertEqual(r.status_code, 403)


class CompanySettingsTests(ScopeBase):
    def test_manager_cannot_change_company_wide_settings(self):
        c = self.api(self.mgr_a)
        self.assertEqual(c.post(f'{M}work-policy/save/', {'work_days': [0]}, format='json').status_code, 403)
        self.assertEqual(c.post(f'{M}charter/update/', {'title': 'x'}, format='json').status_code, 403)
        self.assertEqual(c.post(f'{M}geofence/set/', {'latitude': 1, 'longitude': 1}, format='json').status_code, 403)
        self.a.refresh_from_db()
        self.assertIsNone(self.a.office_latitude)

    def test_hr_can_set_company_location(self):
        r = self.api(self.hr_a).post(f'{M}geofence/set/', {'latitude': 30.1, 'longitude': 31.2, 'radius': 150}, format='json')
        self.assertEqual(r.status_code, 200)


class SelfApprovalTests(ScopeBase):
    def test_manager_cannot_approve_own_work_location(self):
        from attendance.models import EmployeeWorkLocation
        loc = EmployeeWorkLocation._base_manager.create(
            company=self.a, employee=self.mgr_a, name='بيتي', latitude=Decimal('30'), longitude=Decimal('31'), status='pending_manager',
        )
        r = self.api(self.mgr_a).post(f'{M}work-locations/{loc.id}/approve/', {}, format='json')
        self.assertEqual(r.status_code, 403)
        loc.refresh_from_db()
        self.assertEqual(loc.status, 'pending_manager')
        team_loc = EmployeeWorkLocation._base_manager.create(
            company=self.a, employee=self.team_a, name='موقع', latitude=Decimal('30'), longitude=Decimal('31'), status='pending_manager',
        )
        self.assertEqual(self.api(self.mgr_a).post(f'{M}work-locations/{team_loc.id}/approve/', {}, format='json').status_code, 200)

    def test_hr_cannot_add_bonus_to_self(self):
        from attendance.company_policy_models import ManualBonus
        today = date.today()
        body = {'employee_id': self.hr_a.id, 'amount_type': 'fixed', 'amount_value': 5000, 'reason': 'لنفسي',
                'target_year': today.year, 'target_month': today.month, 'category': 'performance'}
        r = self.api(self.hr_a).post(f'{M}entries/bonus/', json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertFalse(ManualBonus._base_manager.filter(employee=self.hr_a).exists())

    def test_advances_only_by_owner_or_hr_and_not_self(self):
        from attendance.payroll_pro_models import PayrollInstallment
        today = date.today()
        body = {'employee_id': self.team_a.id, 'description': 'سلفة', 'total_amount': 1000, 'monthly_amount': 100,
                'start_month': today.month, 'start_year': today.year}
        r = self.api(self.mgr_a).post(f'{M}entries/installment/', json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        body['employee_id'] = self.hr_a.id
        r = self.api(self.hr_a).post(f'{M}entries/installment/', json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertFalse(PayrollInstallment._base_manager.exists())


class ReportsScopeTests(ScopeBase):
    def test_location_report_scoped(self):
        url = f'{M}location-report/?employee_id={self.other_a.id}&shift_date={date.today()}'
        self.assertEqual(self.api(self.mgr_a).get(url).status_code, 404)        # مش فريقه
        self.assertEqual(self.api(self.team_a).get(url).status_code, 404)       # موظف عادي
        self.assertEqual(self.api(self.hr_a).get(url).status_code, 200)

    def test_manager_without_profile_sees_nobody(self):
        from attendance.api_reports import _get_manager_scope_employees
        u = User.objects.create_user(username='mgr_noprof', password='x', role='manager', company=self.a)
        self.assertEqual(_get_manager_scope_employees(u).count(), 0)

    def test_manager_leaves_list_only_team(self):
        self.leave(self.other_a)
        self.leave(self.team_a)
        r = self.api(self.mgr_a).get(f'{M}leaves/list/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 1)
        self.assertEqual(self.api(self.hr_a).get(f'{M}leaves/list/').json()['count'], 2)

    def test_manager_cannot_export_company_payroll(self):
        self.assertEqual(self.api(self.mgr_a).get(f'{M}payroll/export-current/excel/').status_code, 403)


class AnnouncementTests(ScopeBase):
    def create(self, who, **data):
        body = {'title': 'إعلان', 'message': 'محتوى', 'send_push': False}
        body.update(data)
        return self.api(who).post(f'{M}announcements/create/', body, format='json')

    def test_manager_without_team_cannot_broadcast(self):
        lonely = self.emp(self.a, 'manager')
        r = self.create(lonely)
        self.assertEqual(r.status_code, 400)
        from accounts.company_announcements import CompanyAnnouncement
        self.assertFalse(CompanyAnnouncement._base_manager.filter(created_by=lonely.user).exists())

    def test_list_shows_only_targeted(self):
        self.create(self.mgr_a)   # لفريقه بس (team_a)
        ids_team = [a['title'] for a in self.api(self.team_a).get('/attendance/api/mobile/announcements/list/').json()['announcements']]
        ids_other = [a['title'] for a in self.api(self.other_a).get('/attendance/api/mobile/announcements/list/').json()['announcements']]
        self.assertEqual(len(ids_team), 1)
        self.assertEqual(len(ids_other), 0)

    def test_job_title_target_does_not_crash(self):
        from accounts.company_announcements import CompanyAnnouncement
        ann = CompanyAnnouncement._base_manager.create(
            company=self.a, title='بالمسمى', message='x', target_type='by_job_title',
            target_job_titles=self.team_a.job_title.name_ar, created_by=self.hr_a.user,
        )
        self.assertGreaterEqual(ann.get_target_employees().count(), 1)
        r = self.api(self.team_a).get('/attendance/api/mobile/announcements/list/')
        self.assertEqual(r.status_code, 200)


class MissionStartTests(ScopeBase):
    def test_cannot_start_cancelled_mission(self):
        m, a = self.mission(self.team_a)
        m.status = 'cancelled'
        m.save()
        a.status = 'accepted'
        a.save()
        r = self.api(self.team_a).post(f'/attendance/api/mobile/employee/missions/assignments/{a.id}/start/', {}, format='json')
        self.assertEqual(r.status_code, 400)
        m.refresh_from_db()
        self.assertEqual(m.status, 'cancelled')
