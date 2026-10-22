"""
اختبارات مجموعة 2: محدش ينفّذ إجراء على موظف بره نطاقه (شركة تانية / مش فريقه)،
ومحدش يوافق على طلبه هو إلا صاحب الشركة.

التشغيل:
  python manage.py test attendance.test_action_scope --settings=motionhr.settings_test
"""
import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from companies.models import Branch, Company, Department
from employees.models import Employee, JobTitle

ACTION = '/attendance/api/mobile/manager/action/'


class ScopeBase(TestCase):
    _seq = 0

    def setUp(self):
        self.a = Company.objects.create(name_ar='شركة أ', name_en='A')
        self.b = Company.objects.create(name_ar='شركة ب', name_en='B')
        self.owner_a = self.emp(self.a, 'company_admin')
        self.hr_a = self.emp(self.a, 'hr_manager')
        self.mgr_a = self.emp(self.a, 'manager')
        self.team_a = self.emp(self.a, direct_manager=self.mgr_a)       # في فريق المدير
        self.other_a = self.emp(self.a)                                  # نفس الشركة، مش فريقه
        self.emp_b = self.emp(self.b)                                    # شركة تانية
        self.hr_b = self.emp(self.b, 'hr_manager')

    def emp(self, company, role='employee', **kw):
        ScopeBase._seq += 1
        n = ScopeBase._seq
        branch = Branch.objects.filter(company=company).first() or Branch.objects.create(company=company, name_ar='ر', name_en='M')
        dept = Department.objects.filter(company=company).first() or Department.objects.create(company=company, name_ar='د', name_en='D')
        job = JobTitle._base_manager.filter(company=company).first() or JobTitle._base_manager.create(company=company, name_ar='م', name_en='S')
        user = User.objects.create_user(username=f'sc{n}', password='x', role=role, company=company)
        return Employee._base_manager.create(
            user=user, company=company, employee_code=f'S{n}', first_name_ar='موظف', last_name_ar=str(n),
            first_name_en='E', last_name_en=str(n), national_id=f'2910101{n:07d}', hire_date=date(2020, 1, 1),
            birth_date=date(1990, 1, 1), gender='male', basic_salary=Decimal('5000'), phone=f'0122{n:07d}',
            branch=branch, department=dept, job_title=job, **kw,
        )

    def api(self, who):
        c = APIClient()
        c.force_authenticate(who.user)
        return c

    def leave(self, emp, status='pending'):
        from leaves.models import LeaveRequest, LeaveType
        lt = LeaveType._base_manager.filter(company=emp.company).first() or \
            LeaveType._base_manager.create(company=emp.company, name='سنوي', category='annual', days_allowed=21)
        d = date.today() + timedelta(days=10)
        return LeaveRequest._base_manager.create(
            company=emp.company, employee=emp, leave_type=lt, start_date=d, end_date=d,
            days_count=Decimal('1'), reason='اختبار', status=status,
        )

    def req(self, emp, status='pending'):
        from requests_app.models import EmployeeRequest, RequestCategory, RequestType
        cat = RequestCategory._base_manager.filter(company=emp.company).first() or \
            RequestCategory._base_manager.create(company=emp.company, name='عام', name_en='General')
        rt = RequestType._base_manager.filter(company=emp.company).first() or \
            RequestType._base_manager.create(company=emp.company, category=cat, name='طلب', name_en='Req')
        return EmployeeRequest._base_manager.create(
            company=emp.company, employee=emp, request_type=rt, subject='طلب', status=status,
        )

    def mission(self, emp):
        from attendance.missions_models import Mission, MissionAssignment
        now = timezone.now()
        m = Mission._base_manager.create(
            company=emp.company, title='مأمورية', planned_start_time=now + timedelta(days=1),
            planned_end_time=now + timedelta(days=1, hours=2), created_by=emp.user, status='pending_approval',
            source='employee',
        )
        a = MissionAssignment._base_manager.create(company=emp.company, mission=m, employee=emp)
        return m, a

    def act(self, who, type_, obj, action='approve'):
        return self.api(who).post(ACTION, {'type': type_, 'id': obj.id, 'action': action, 'notes': 'سبب'}, format='json')


class ApproveRejectScopeTests(ScopeBase):
    """12 و139"""

    def test_hr_cannot_approve_leave_of_other_company(self):
        lv = self.leave(self.emp_b)
        r = self.act(self.hr_a, 'leave', lv)
        self.assertEqual(r.status_code, 404)
        lv.refresh_from_db()
        self.assertEqual(lv.status, 'pending')

    def test_hr_approves_leave_in_own_company(self):
        lv = self.leave(self.other_a)
        self.assertEqual(self.act(self.hr_a, 'leave', lv).status_code, 200)
        lv.refresh_from_db()
        self.assertEqual(lv.status, 'approved')

    def test_manager_only_his_team(self):
        lv_out = self.leave(self.other_a)
        self.assertEqual(self.act(self.mgr_a, 'leave', lv_out).status_code, 404)
        lv_team = self.leave(self.team_a)
        self.assertEqual(self.act(self.mgr_a, 'leave', lv_team).status_code, 200)
        lv_team.refresh_from_db()
        self.assertEqual(lv_team.status, 'approved')

    def test_nobody_approves_own_leave_except_owner(self):
        for who in (self.mgr_a, self.hr_a):
            lv = self.leave(who)
            r = self.act(who, 'leave', lv)
            self.assertEqual(r.status_code, 403)
            lv.refresh_from_db()
            self.assertEqual(lv.status, 'pending')
        lv = self.leave(self.owner_a)
        self.assertEqual(self.act(self.owner_a, 'leave', lv).status_code, 200)

    def test_substitute_manager_can_act_on_absent_managers_team(self):
        from leaves.models import ManagerSubstitution
        sub = self.emp(self.a, 'manager')
        today = date.today()
        ManagerSubstitution._base_manager.create(
            company=self.a, manager_employee=self.mgr_a, substitute_employee=sub, leave_request=self.leave(self.mgr_a, 'approved'),
            start_date=today, end_date=today, is_active=True,
        )
        lv = self.leave(self.team_a)
        self.assertEqual(self.act(sub, 'leave', lv).status_code, 200)

    def test_request_other_company(self):
        rq = self.req(self.emp_b)
        self.assertEqual(self.act(self.hr_a, 'request', rq, 'reject').status_code, 404)
        rq.refresh_from_db()
        self.assertEqual(rq.status, 'pending')

    def test_mission_other_company_and_team(self):
        m_b, _ = self.mission(self.emp_b)
        self.assertEqual(self.act(self.hr_a, 'mission', m_b).status_code, 404)
        m_b.refresh_from_db()
        self.assertEqual(m_b.status, 'pending_approval')
        m_out, _ = self.mission(self.other_a)
        self.assertEqual(self.act(self.mgr_a, 'mission', m_out).status_code, 404)
        m_team, _ = self.mission(self.team_a)
        self.assertEqual(self.act(self.mgr_a, 'mission', m_team).status_code, 200)


class EditCancelScopeTests(ScopeBase):
    """2 و13"""

    def test_edit_cancel_reopen_other_company_refused(self):
        c = self.api(self.hr_a)
        rq = self.req(self.emp_b)
        self.assertEqual(c.patch(f'/attendance/api/mobile/manager/requests/{rq.id}/edit/', {'subject': 'x'}, format='json').status_code, 404)
        self.assertEqual(c.post(f'/attendance/api/mobile/manager/requests/{rq.id}/cancel/', {}, format='json').status_code, 404)
        rq.status = 'rejected'
        rq.save()
        self.assertEqual(c.post(f'/attendance/api/mobile/manager/requests/{rq.id}/reopen/', {}, format='json').status_code, 404)
        rq.refresh_from_db()
        self.assertEqual(rq.status, 'rejected')

        lv = self.leave(self.emp_b)
        self.assertEqual(c.patch(f'/attendance/api/mobile/manager/leaves/{lv.id}/edit/', {'status': 'approved'}, format='json').status_code, 404)
        self.assertEqual(c.post(f'/attendance/api/mobile/manager/leaves/{lv.id}/cancel/', {}, format='json').status_code, 404)
        lv.refresh_from_db()
        self.assertEqual(lv.status, 'pending')

    def test_cancel_in_own_company_still_works(self):
        lv = self.leave(self.other_a)
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/leaves/{lv.id}/cancel/', {'reason': 'x'}, format='json')
        self.assertEqual(r.status_code, 200)


class PermissionBalanceScopeTests(ScopeBase):
    """80 و142 (المنح لنفسه)"""

    URL = '/attendance/api/mobile/manager/employees/{}/permission-{}/'

    def test_other_company_refused(self):
        c = self.api(self.hr_a)
        self.assertEqual(c.get(f'/attendance/api/mobile/manager/employees/{self.emp_b.id}/permission-balance/').status_code, 404)
        r = c.post(self.URL.format(self.emp_b.id, 'grant'), {'minutes': 60}, format='json')
        self.assertEqual(r.status_code, 404)
        r = c.post(self.URL.format(self.emp_b.id, 'rollback'), {'reference_date': str(date.today())}, format='json')
        self.assertEqual(r.status_code, 404)
        from attendance.models import PermissionLedger
        self.assertFalse(PermissionLedger._base_manager.filter(employee=self.emp_b).exists())

    def test_cannot_grant_self(self):
        r = self.api(self.mgr_a).post(self.URL.format(self.mgr_a.id, 'grant'), {'minutes': 60}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_grant_team_member_works(self):
        r = self.api(self.mgr_a).post(self.URL.format(self.team_a.id, 'grant'), {'minutes': 30}, format='json')
        self.assertEqual(r.status_code, 200)
        from attendance.models import PermissionLedger
        self.assertEqual(PermissionLedger._base_manager.get(employee=self.team_a).minutes_used, -30)


_TMP_MEDIA = tempfile.mkdtemp(prefix='motionhr_test_media_')


@override_settings(MEDIA_ROOT=_TMP_MEDIA)  # ملفات الاختبار ماتتكتبش في media الحقيقي
class DeviceTimelineAttachmentTests(ScopeBase):
    """81 و83 و155/204"""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TMP_MEDIA, ignore_errors=True)

    def device(self, emp):
        from accounts.fcm_models import TrustedDevice
        return TrustedDevice._base_manager.create(user=emp.user, device_id=f'dev{emp.id}', device_name='Phone', platform='android', status='pending')

    def test_device_other_company_refused(self):
        d = self.device(self.emp_b)
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/devices/{d.id}/action/', {'action': 'approve'}, format='json')
        self.assertEqual(r.status_code, 404)
        d.refresh_from_db()
        self.assertEqual(d.status, 'pending')

    def test_device_team_member_approved(self):
        d = self.device(self.team_a)
        r = self.api(self.mgr_a).post(f'/attendance/api/mobile/manager/devices/{d.id}/action/', {'action': 'approve'}, format='json')
        self.assertEqual(r.status_code, 200)
        d.refresh_from_db()
        self.assertEqual(d.status, 'approved')

    def test_timeline(self):
        _, a_b = self.mission(self.emp_b)
        url = f'/attendance/api/mobile/employee/missions/assignments/{a_b.id}/locations/'
        self.assertEqual(self.api(self.hr_a).get(url).status_code, 404)
        self.assertEqual(self.api(self.emp_b).get(url).status_code, 200)   # الموظف نفسه
        self.assertEqual(self.api(self.hr_b).get(url).status_code, 200)    # HR شركته

    def attachment(self, emp, obj):
        from core.models_attachment import Attachment
        return Attachment.all_objects.create(
            company=emp.company, content_type=ContentType.objects.get_for_model(obj), object_id=obj.id,
            file=ContentFile(b'x', name='a.txt'), original_name='a.txt', file_type='document',
            file_size=1, mime_type='text/plain', uploaded_by=emp.user,
        )

    def test_attachment_delete_other_company_refused(self):
        from core.models_attachment import Attachment
        rq = self.req(self.emp_b)
        att = self.attachment(self.emp_b, rq)
        r = self.api(self.owner_a).delete(f'/attendance/api/mobile/attachments/{att.id}/delete/')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Attachment.all_objects.filter(id=att.id).exists())
        r = self.api(self.hr_b).delete(f'/attendance/api/mobile/attachments/{att.id}/delete/')
        self.assertEqual(r.status_code, 200)

    def test_orphan_attachment_download_only_owner_or_company_admin(self):
        rq = self.req(self.emp_b)
        att = self.attachment(self.emp_b, rq)
        rq.delete()
        url = f'/attendance/api/mobile/attachments/{att.id}/download/'
        self.assertEqual(self.api(self.owner_a).get(url).status_code, 403)
        self.assertEqual(self.api(self.other_a).get(url).status_code, 403)
        self.assertEqual(self.api(self.emp_b).get(url).status_code, 200)
