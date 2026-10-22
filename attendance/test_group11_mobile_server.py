"""
اختبارات دفعة 11 (مشاكل في تطبيق الموبايل بتتصلح من السيرفر من غير تحديث للتطبيق):
170 مدة مفتاح التجديد، 175 تعديل الإعلان من الموبايل، 184 رفض الجزاء من الموبايل، 188 إضافة جزاء من الموبايل،
190 شاشة الصلاحيات الجماعية، 207 رد المصروفات بتاريخ، 433 الاستيراد بـ JWT، 476 الإجازة الممتدة على شهرين

التشغيل:
  python manage.py test attendance.test_group11_mobile_server --settings=motionhr.settings_test
"""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/'


class TokenLifetimeTests(ScopeBase):
    def test_refresh_outlives_access(self):
        jwt = settings.SIMPLE_JWT
        self.assertGreater(jwt['REFRESH_TOKEN_LIFETIME'], jwt['ACCESS_TOKEN_LIFETIME'])

    def test_app_can_refresh(self):
        refresh = RefreshToken.for_user(self.team_a.user)
        r = APIClient().post(f'{M}jwt/refresh/', {'refresh': str(refresh)}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data.get('access'))


class AnnouncementEditFromAppTests(ScopeBase):
    def test_app_edit_keeps_department_target(self):
        from accounts.company_announcements import CompanyAnnouncement
        ann = CompanyAnnouncement._base_manager.create(company=self.a, title='t', message='m',
                                                        created_by=self.hr_a.user, target_type='by_department')
        ann.target_departments.through._default_manager.create(companyannouncement_id=ann.id,
                                                                department_id=self.team_a.department_id)
        # التطبيق بيبعت "كل الموظفين" مع أي تعديل
        r = self.api(self.hr_a).put(f'{M}manager/announcements/{ann.id}/update/',
                                    {'title': 'عنوان جديد', 'message': 'm', 'target_type': 'all'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        ann.refresh_from_db()
        self.assertEqual((ann.title, ann.target_type), ('عنوان جديد', 'by_department'))

    def test_explicit_branch_choice_applies(self):
        from accounts.company_announcements import CompanyAnnouncement
        ann = CompanyAnnouncement._base_manager.create(company=self.a, title='t', message='m', created_by=self.hr_a.user)
        r = self.api(self.hr_a).put(f'{M}manager/announcements/{ann.id}/update/',
                                    {'target_type': 'by_branch', 'branch_ids': [self.team_a.branch_id]}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        ann.refresh_from_db()
        self.assertEqual(ann.target_type, 'by_branch')
        ids = list(ann.target_branches.through._default_manager.filter(companyannouncement_id=ann.id)
                   .values_list('branch_id', flat=True))
        self.assertEqual(ids, [self.team_a.branch_id])


class ManualEntriesFromAppTests(ScopeBase):
    def test_app_add_penalty_with_employee_key(self):
        from attendance.company_policy_models import ManualPenalty
        today = timezone.localdate()
        r = self.api(self.owner_a).post(f'{M}manager/entries/penalty/', {
            'employee': self.team_a.id, 'category': 'other', 'amount_type': 'fixed', 'amount_value': 50,
            'reason': 'تأخير', 'target_year': today.year, 'target_month': today.month,
        }, format='json')
        self.assertIn(r.status_code, (200, 201), getattr(r, 'content', b'')[:300])
        self.assertTrue(ManualPenalty._base_manager.filter(employee=self.team_a).exists())

    def test_app_reject_without_body(self):
        from attendance.company_policy_models import ManualPenalty
        today = timezone.localdate()
        e = ManualPenalty._base_manager.create(company=self.a, employee=self.team_a, requested_by=self.mgr_a.user,
                                               category='other', amount_type='fixed', amount_value=Decimal('50'),
                                               reason='x', target_year=today.year, target_month=today.month,
                                               status='pending')
        r = self.api(self.owner_a).post(f'{M}manager/entries/penalty/{e.id}/reject/')
        self.assertEqual(r.status_code, 200, getattr(r, 'content', b'')[:300])
        e.refresh_from_db()
        self.assertEqual(e.status, 'rejected')


class BulkPermissionsScreenTests(ScopeBase):
    def test_department_summary_marks_only_shared_permissions(self):
        from accounts.permissions_models import UserPermissionOverride
        UserPermissionOverride._base_manager.create(user=self.team_a.user, permission='reports.view',
                                                    scope='company', is_granted=True)
        r = self.api(self.owner_a).get(f'{M}manager/permissions/summary/?type=department&id={self.team_a.department_id}')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn('permissions', r.data)
        # الصلاحية دي عند موظف واحد بس، فمش متعلّمة (عشان الحفظ مايدّيهاش للقسم كله)
        self.assertNotIn('reports.view', [p['code'] for p in r.data['permissions']])


class ExpenseRequestTests(ScopeBase):
    def test_expense_with_date_and_no_time_accepted(self):
        from attendance.models import Attendance
        from requests_app.models import RequestCategory, RequestType
        d = timezone.localdate() - timedelta(days=1)
        Attendance._base_manager.create(company=self.a, employee=self.team_a, date=d, status='present',
                                        check_in_time=timezone.now() - timedelta(days=1))
        cat = RequestCategory._base_manager.create(company=self.a, name='مالية', name_en='Fin')
        rt = RequestType._base_manager.create(company=self.a, category=cat, name='رد مصروفات', name_en='Expense',
                                              requires_date_range=True, requires_amount=True)
        r = self.api(self.team_a).post(f'{M}submit-request/', {
            'request_type_id': rt.id, 'subject': 'مواصلات', 'details': 'تاكسي',
            'start_date': d.isoformat(), 'end_date': d.isoformat(), 'amount': '120',
        }, format='json')
        self.assertNotEqual(r.data.get('message'), 'صيغة الوقت غير صحيحة')
        self.assertIn(r.status_code, (200, 201), r.data)


class ImportWithJwtTests(ScopeBase):
    def test_import_logs_accepts_jwt(self):
        access = str(RefreshToken.for_user(self.owner_a.user).access_token)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        r = c.get('/employees/api/mobile/import-logs/')
        self.assertNotEqual(r.status_code, 401)


class LeaveAcrossMonthsTests(ScopeBase):
    def test_leave_split_between_months(self):
        from attendance.api_reports import _leave_days_in_month
        from leaves.models import LeaveRequest, LeaveType
        lt = LeaveType._base_manager.create(company=self.a, name='سنوي', category='annual', days_allowed=21)
        lv = LeaveRequest._base_manager.create(company=self.a, employee=self.team_a, leave_type=lt,
                                               start_date=date(2026, 9, 28), end_date=date(2026, 10, 7),
                                               days_count=Decimal('10'), reason='سفر', status='approved')
        # 3 أيام في سبتمبر (28-30) و7 في أكتوبر
        self.assertEqual(_leave_days_in_month(lv, date(2026, 9, 1), date(2026, 9, 30)), 3.0)
        self.assertEqual(_leave_days_in_month(lv, date(2026, 10, 1), date(2026, 10, 31)), 7.0)
