"""
اختبارات دفعة 10 (حاجات متوسطة مالهاش علاقة بالمرتبات ولا الحضور):
290 فلتر المواقع المعلقة، 296 استبدال الطالب في مهمة، 300 استهداف الإعلانات، 304 أدوار القسم،
328/329 الاستيراد، 336 إشعار الإجازة، 368/387 التوقيت، 371 اللي سابوا الشغل، 375/376 التصدير،
386 حضور الشركة للـ HR، 399 فحص الملفات، 402 طريقة القبض، 403 قايمة المديرين

التشغيل:
  python manage.py test attendance.test_group10_misc --settings=motionhr.settings_test
"""
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.utils import timezone

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/'


class WorkLocationPendingFilterTests(ScopeBase):
    def test_pending_filter_finds_pending_manager_and_hr(self):
        from attendance.api_work_locations import logger  # 289: كان مش معرّف
        from attendance.models import EmployeeWorkLocation
        for st in ('pending_manager', 'pending_hr', 'approved'):
            EmployeeWorkLocation._base_manager.create(company=self.a, employee=self.team_a, name=st, status=st,
                                                      latitude=30, longitude=31)
        r = self.api(self.hr_a).get(f'{M}manager/work-locations/?filter=pending')
        self.assertEqual(r.status_code, 200, r.data)
        names = sorted(x.get('name') for x in (r.data.get('locations') or r.data.get('results') or []))
        self.assertEqual(names, ['pending_hr', 'pending_manager'])
        self.assertIsNotNone(logger)


class MissionReplaceRequesterTests(ScopeBase):
    def test_original_request_leaves_manager_pending_list(self):
        from attendance.missions_models import Mission, MissionRequest
        now = timezone.now()
        m = Mission._base_manager.create(company=self.a, title='زيارة', planned_start_time=now + timedelta(days=1),
                                         planned_end_time=now + timedelta(days=1, hours=2),
                                         created_by=self.team_a.user, status='pending_approval', source='employee_request')
        mr = MissionRequest._base_manager.create(mission=m, requested_by=self.team_a)
        r = self.api(self.hr_a).post(f'{M}manager/missions/{m.id}/reassign/',
                                     {'old_employee_id': self.team_a.id, 'new_employee_id': self.other_a.id}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        mr.refresh_from_db()
        self.assertEqual((mr.final_status, mr.manager_approval), ('rejected', 'rejected'))


class AnnouncementTargetingTests(ScopeBase):
    def ann(self, **kw):
        from accounts.company_announcements import CompanyAnnouncement
        return CompanyAnnouncement._base_manager.create(company=self.a, title='t', message='m',
                                                        created_by=self.hr_a.user, **kw)

    def test_specific_target_and_exclusion(self):
        from attendance.api_announcements import _is_announcement_targeted_to_employee
        a1 = self.ann(target_type='specific')
        a1.target_employees.through._default_manager.create(companyannouncement_id=a1.id, employee_id=self.team_a.id)
        self.assertTrue(_is_announcement_targeted_to_employee(a1, self.team_a))
        self.assertFalse(_is_announcement_targeted_to_employee(a1, self.other_a))
        a2 = self.ann(target_type='all')
        a2.excluded_employees.through._default_manager.create(companyannouncement_id=a2.id, employee_id=self.other_a.id)
        self.assertFalse(_is_announcement_targeted_to_employee(a2, self.other_a))
        self.assertTrue(_is_announcement_targeted_to_employee(a2, self.team_a))

    def test_excluded_job_title_by_name(self):
        a = self.ann(target_type='all', excluded_job_titles='م')
        self.assertEqual(a.get_target_employees().count(), 0)


class DepartmentRoleTests(ScopeBase):
    def test_transfer_keeps_other_custom_roles(self):
        from accounts.permissions_models import CustomRole as Role, UserRole
        from companies.models import Department
        r_old = Role._base_manager.create(company=self.a, name='دور قسم قديم')
        r_new = Role._base_manager.create(company=self.a, name='دور قسم جديد')
        r_extra = Role._base_manager.create(company=self.a, name='دور إضافي')
        old = self.team_a.department
        old.default_role = r_old
        old.save()
        new = Department._base_manager.create(company=self.a, name_ar='جديد', name_en='New', default_role=r_new)
        UserRole._base_manager.create(user=self.team_a.user, role=r_old)
        UserRole._base_manager.create(user=self.team_a.user, role=r_extra)
        from attendance.api_departments import _swap_department_role
        self.team_a.department = new
        _swap_department_role(self.team_a, old, new)
        roles = set(UserRole._base_manager.filter(user=self.team_a.user).values_list('role__name', flat=True))
        self.assertEqual(roles, {'دور قسم جديد', 'دور إضافي'})


class ImportCommandTests(ScopeBase):
    def test_import_refuses_without_company(self):
        with self.assertRaises(CommandError):
            call_command('import_employees_bulk', file='x.xlsx', company_id=None)

    def test_manager_name_not_guessed_from_first_name(self):
        from employees.management.commands.import_employees_bulk import Command
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(first_name_ar='محمد', last_name_ar='سعيد')
        # "محمد علي" مش موجود؛ قبل كده كان بيختار أي "محمد"
        got = Command()._resolve_manager(self.a, 'محمد علي')
        self.assertNotEqual(getattr(got, 'id', None), self.other_a.id)
        exact = Command()._resolve_manager(self.a, 'محمد سعيد')
        self.assertEqual(exact.id, self.other_a.id)


class LeaveNotificationTests(ScopeBase):
    def test_leave_notification_reaches_direct_manager_not_other_managers(self):
        from accounts import fcm_service
        sent_to = []
        with mock.patch.object(fcm_service, 'send_notification_to_user',
                               side_effect=lambda u, *a, **k: sent_to.append(u.id) or {'sent': 1}):
            fcm_service.notify_manager_new_leave(company=self.a, employee_name='x', leave_type='سنوي',
                                                 leave_id=1, employee=self.team_a)
        other_mgr = self.emp(self.a, 'manager')
        self.assertIn(self.mgr_a.user_id, sent_to)
        self.assertIn(self.hr_a.user_id, sent_to)
        self.assertNotIn(other_mgr.user_id, sent_to)


class TimeAndDashboardTests(ScopeBase):
    def test_report_time_in_cairo(self):
        from attendance.api_reports import _format_time
        utc = datetime(2026, 10, 1, 6, 0, tzinfo=dt_timezone.utc)   # 9 الصبح في مصر (صيفي)
        self.assertEqual(_format_time(utc), timezone.localtime(utc).strftime('%I:%M %p'))
        self.assertNotEqual(_format_time(utc), '06:00 AM')

    def test_dashboard_counts_people_who_left_this_month(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(status='resigned',
                                                                 termination_date=timezone.localdate())
        r = self.api(self.owner_a).get(f'{M}manager/dashboard/')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        self.assertEqual(r.data['turnover']['terminated_this_month'], 1)

    def test_hr_with_direct_team_sees_whole_company_attendance(self):
        from attendance.models import Attendance
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(direct_manager=self.hr_a)
        today = timezone.localdate()
        for e in (self.team_a, self.other_a):
            Attendance._base_manager.create(company=self.a, employee=e, date=today, status='present',
                                            check_in_time=timezone.now())
        r = self.api(self.hr_a).get(f'{M}manager/attendance/?date={today.isoformat()}')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        codes = {x.get('employee_code') for x in r.data.get('items', [])}
        self.assertTrue({self.team_a.employee_code, self.other_a.employee_code} <= codes, codes)


class ExportSafetyTests(ScopeBase):
    def test_formula_and_pdf_text(self):
        from core.export_safety import pdf_text, safe_cell_value
        self.assertEqual(safe_cell_value('=HYPERLINK("x")'), '\'=HYPERLINK("x")')
        self.assertEqual(safe_cell_value('-5'), '-5')
        self.assertEqual(safe_cell_value(-5), -5)
        self.assertEqual(safe_cell_value('أحمد'), 'أحمد')
        self.assertEqual(pdf_text('A & B <x>'), 'A &amp; B &lt;x&gt;')


class UploadContentTests(ScopeBase):
    def test_fake_pdf_refused_real_pdf_ok(self):
        from core.upload_validation import upload_error
        self.assertIsNotNone(upload_error(SimpleUploadedFile('a.pdf', b'MZ\x90\x00 not a pdf', 'application/pdf')))
        self.assertIsNone(upload_error(SimpleUploadedFile('a.pdf', b'%PDF-1.4 ok', 'application/pdf')))
        self.assertIsNone(upload_error(SimpleUploadedFile('a.docx', b'PK\x03\x04 zip', 'application/octet-stream')))


class EmployeeEditTests(ScopeBase):
    def test_default_payment_method_none_accepted(self):
        from attendance.api_employee_management import manager_update_employee  # noqa: F401
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(salary_payment_method='none')
        e = Employee._base_manager.get(pk=self.team_a.pk)
        body = {
            'first_name_ar': e.first_name_ar, 'last_name_ar': e.last_name_ar, 'first_name_en': 'Emp', 'last_name_en': 'Xy',
            'phone': e.phone, 'national_id': e.national_id, 'birth_date': '1990-01-01', 'gender': 'male',
            'hire_date': '2020-01-01', 'branch_id': e.branch_id, 'department_id': e.department_id,
            'job_title_id': e.job_title_id, 'basic_salary': '5000', 'contract_type': 'permanent',
        }
        r = self.api(self.hr_a).put(f'{M}manager/employees/{e.id}/update/', body, format='json')
        self.assertNotEqual(getattr(r, 'data', {}).get('error'), 'طريقة القبض غير صحيحة')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))

    def test_manager_dropdown_search(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(first_name_ar='زكريا')
        r = self.api(self.owner_a).get(f'{M}manager/employees/simple/?search=زكريا')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        ids = [x['id'] for x in r.data.get('employees', [])]
        self.assertEqual(ids, [self.other_a.id])
