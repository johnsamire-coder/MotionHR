"""
اختبارات الجزء اللي في السيرفر من دفعة 6 (شاشات الويب):
220 تعديل الإعلان من الويب، 221 السلفة بمبلغ سالب، 224 تغيير كلمة السر من إعدادات HR

التشغيل:
  python manage.py test attendance.test_group6_web_server --settings=motionhr.settings_test
"""
import json
from datetime import date

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/manager/'


class AnnouncementEditTests(ScopeBase):
    def make(self, who):
        from accounts.company_announcements import CompanyAnnouncement
        return CompanyAnnouncement._base_manager.create(company=self.a, title='قديم', message='نص قديم', created_by=who.user)

    def test_web_edit_with_content_field(self):
        ann = self.make(self.hr_a)
        r = self.api(self.hr_a).put(f'{M}announcements/{ann.id}/update/', {'title': 'جديد', 'content': 'نص جديد'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        ann.refresh_from_db()
        self.assertEqual((ann.title, ann.message), ('جديد', 'نص جديد'))

    def test_manager_edits_only_own(self):
        ann = self.make(self.hr_a)
        r = self.api(self.mgr_a).put(f'{M}announcements/{ann.id}/update/', {'title': 'x'}, format='json')
        self.assertEqual(r.status_code, 403)


class AdvanceValidationTests(ScopeBase):
    def post(self, total, monthly):
        today = date.today()
        body = {'employee_id': self.other_a.id, 'description': 'سلفة', 'total_amount': total, 'monthly_amount': monthly,
                'start_month': today.month, 'start_year': today.year}
        return self.api(self.hr_a).post(f'{M}entries/installment/', json.dumps(body), content_type='application/json')

    def test_negative_and_oversized_refused(self):
        from attendance.payroll_pro_models import PayrollInstallment
        self.assertEqual(self.post(1000, -100).status_code, 400)
        self.assertEqual(self.post(-1000, 100).status_code, 400)
        self.assertEqual(self.post(1000, 2000).status_code, 400)
        self.assertFalse(PayrollInstallment._base_manager.exists())
        self.assertEqual(self.post(1000, 250).status_code, 201)   # الصح بيتعمل عادي


class ChangePasswordTests(ScopeBase):
    def test_web_old_password_field_works_and_returns_new_token(self):
        self.hr_a.user.set_password('OldPass123')
        self.hr_a.user.save()
        r = self.api(self.hr_a).post('/attendance/api/mobile/change-password/',
                                     {'old_password': 'OldPass123', 'new_password': 'NewPass456'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()['token'])
        self.hr_a.user.refresh_from_db()
        self.assertTrue(self.hr_a.user.check_password('NewPass456'))
