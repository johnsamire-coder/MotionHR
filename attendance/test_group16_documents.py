"""
مجموعة 16: مستندات الموظف — إضافة وتعديل وحذف من شاشة الموظف، وتذكير قبل انتهاء المستند.
  python manage.py test attendance.test_group16_documents --settings=motionhr.settings_test
"""
import shutil
import tempfile
from datetime import timedelta
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from accounts.models import EmployeeNotification
from attendance.test_action_scope import ScopeBase
from employees.models import EmployeeDocument

PDF = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n'


def pdf(name='doc.pdf'):
    return SimpleUploadedFile(name, PDF, content_type='application/pdf')


def url(emp, doc=None):
    base = f'/attendance/api/mobile/manager/employees/{emp.id}/documents/'
    return f'{base}{doc.id}/' if doc else base


class DocumentsBase(ScopeBase):
    def setUp(self):
        super().setUp()
        self._media = tempfile.mkdtemp()
        self._ovr = override_settings(MEDIA_ROOT=self._media)
        self._ovr.enable()

    def tearDown(self):
        self._ovr.disable()
        shutil.rmtree(self._media, ignore_errors=True)
        super().tearDown()

    def add(self, who, emp, **data):
        body = {'file': pdf(), 'document_type': 'license', 'title': 'رخصة القيادة'}
        body.update(data)
        return self.api(who).post(url(emp), body, format='multipart')


class AddEditDeleteTests(DocumentsBase):
    def test_hr_adds_document_with_type_and_dates(self):
        r = self.add(self.hr_a, self.team_a, issue_date='2025-11-01', expiry_date='2026-11-20', notes='أصل في الملف')
        self.assertEqual(r.status_code, 201, r.data)
        doc = EmployeeDocument._base_manager.get(employee=self.team_a)
        self.assertEqual((doc.document_type, doc.title, str(doc.expiry_date), doc.notes),
                         ('license', 'رخصة القيادة', '2026-11-20', 'أصل في الملف'))
        self.assertEqual(doc.company_id, self.a.id)
        lst = self.api(self.hr_a).get(url(self.team_a)).data
        self.assertTrue(lst['can_edit'])
        self.assertEqual(lst['documents'][0]['document_type_code'], 'license')

    def test_validation(self):
        self.assertEqual(self.api(self.hr_a).post(url(self.team_a), {'document_type': 'license'},
                                                  format='multipart').status_code, 400)      # من غير ملف
        self.assertEqual(self.add(self.hr_a, self.team_a, document_type='xxx').status_code, 400)
        self.assertEqual(self.add(self.hr_a, self.team_a, expiry_date='20-20-2026').status_code, 400)
        r = self.add(self.hr_a, self.team_a, issue_date='2026-05-01', expiry_date='2026-04-01')
        self.assertEqual(r.status_code, 400)
        self.assertIn('بعد تاريخ الإصدار', r.data['message'])
        bad = SimpleUploadedFile('x.pdf', b'MZ\x90\x00 not a pdf', content_type='application/pdf')
        self.assertEqual(self.add(self.hr_a, self.team_a, file=bad).status_code, 400)
        self.assertFalse(EmployeeDocument._base_manager.exists())

    def test_edit_and_delete(self):
        self.add(self.hr_a, self.team_a, expiry_date='2026-11-20')
        doc = EmployeeDocument._base_manager.get(employee=self.team_a)
        r = self.api(self.owner_a).patch(url(self.team_a, doc), {'expiry_date': '2027-11-20', 'document_type': 'passport'},
                                         format='json')
        self.assertEqual(r.status_code, 200, r.data)
        doc.refresh_from_db()
        self.assertEqual((str(doc.expiry_date), doc.document_type, doc.title), ('2027-11-20', 'passport', 'رخصة القيادة'))
        # مسح تاريخ الانتهاء
        self.api(self.hr_a).patch(url(self.team_a, doc), {'expiry_date': ''}, format='json')
        doc.refresh_from_db()
        self.assertIsNone(doc.expiry_date)
        # مستند موظف تاني مايتعدلش من رابط موظف غيره
        self.assertEqual(self.api(self.hr_a).delete(url(self.other_a, doc)).status_code, 404)
        self.assertEqual(self.api(self.hr_a).delete(url(self.team_a, doc)).status_code, 200)
        self.assertFalse(EmployeeDocument._base_manager.exists())

    def test_permissions(self):
        self.assertEqual(self.add(self.mgr_a, self.team_a).status_code, 403)       # المدير بيشوف بس
        self.assertEqual(self.add(self.team_a, self.team_a).status_code, 403)      # الموظف مش من الشاشة دي
        self.assertEqual(self.add(self.hr_b, self.team_a).status_code, 404)        # شركة تانية
        self.assertFalse(self.api(self.mgr_a).get(url(self.team_a)).data['can_edit'])
        self.add(self.hr_a, self.team_a)
        doc = EmployeeDocument._base_manager.get()
        self.assertEqual(self.api(self.mgr_a).delete(url(self.team_a, doc)).status_code, 403)
        self.assertEqual(self.api(self.hr_b).patch(url(self.team_a, doc), {'title': 'x'}, format='json').status_code, 404)

    def test_employee_upload_from_app_keeps_expiry(self):
        r = self.api(self.team_a).post('/attendance/api/mobile/employee/upload-document/',
                                       {'file': pdf(), 'document_type': 'national_id', 'expiry_date': '2030-01-31'},
                                       format='multipart')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['document']['expiry_date'], '2030-01-31')
        self.assertEqual(r.data['document']['title'], 'doc.pdf')


@mock.patch('attendance.fcm_logic.send_fcm_notification', return_value=True)
class ExpiryReminderTests(DocumentsBase):
    def doc(self, emp, days, title='رخصة القيادة'):
        return EmployeeDocument._base_manager.create(
            company=emp.company, employee=emp, document_type='license', title=title, file=pdf(),
            expiry_date=timezone.localdate() + timedelta(days=days))

    def run_reminders(self):
        from attendance.reminders import remind_expiring_documents
        return remind_expiring_documents()

    def recipients(self, send):
        return {c.args[0].pk for c in send.call_args_list}

    def test_who_gets_notified_and_only_once_per_stage(self, send):
        self.doc(self.team_a, 30)
        self.assertEqual(self.run_reminders(), 1)
        # الموظف + مديره المباشر + الـ HR + صاحب الشركة، ومش حد من شركة تانية ولا زميل
        self.assertEqual(self.recipients(send),
                         {self.team_a.user_id, self.mgr_a.user_id, self.hr_a.user_id, self.owner_a.user_id})
        body = send.call_args_list[0].args[2]
        self.assertIn('باقي 30 يوم', body)
        self.assertIn('رخصة القيادة', body)
        # الأمر اشتغل تاني في نفس اليوم أو بعدها بيومين (لسه نفس المرحلة) → مفيش تكرار
        send.reset_mock()
        self.assertEqual(self.run_reminders(), 0)
        self.assertEqual(send.call_count, 0)
        self.assertEqual(EmployeeNotification.objects.filter(employee=self.team_a).count(), 1)
        self.assertEqual(EmployeeNotification.objects.filter(employee=self.mgr_a).count(), 1)

    def test_stages(self, send):
        from attendance.reminders import _document_stage
        # 31 يوم: لسه بدري. 30..8: شهر. 7..2: أسبوع. 1: بكره. 0: النهارده. -1..-30: انتهى. أقدم من كده: لا
        self.assertEqual([(_document_stage(d) or ('-',))[0] for d in (31, 30, 8, 7, 2, 1, 0, -1, -30, -31)],
                         ['-', 'month', 'month', 'week', 'week', 'tomorrow', 'today', 'expired', 'expired', '-'])

    def test_next_stage_sends_again(self, send):
        d = self.doc(self.team_a, 30)
        self.run_reminders()
        EmployeeDocument._base_manager.filter(pk=d.pk).update(expiry_date=timezone.localdate() + timedelta(days=7))
        send.reset_mock()
        self.assertEqual(self.run_reminders(), 1)
        self.assertIn('باقي 7 يوم', send.call_args_list[0].args[2])
        EmployeeDocument._base_manager.filter(pk=d.pk).update(expiry_date=timezone.localdate() - timedelta(days=3))
        send.reset_mock()
        self.assertEqual(self.run_reminders(), 1)
        self.assertIn('انتهى من 3 يوم', send.call_args_list[0].args[2])

    def test_skips_far_old_and_inactive(self, send):
        self.doc(self.team_a, 31)                      # لسه بدري
        self.doc(self.team_a, -31, title='قديم')       # منتهي من زمان
        self.doc(self.other_a, 5)
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(status='terminated')
        EmployeeDocument._base_manager.create(company=self.a, employee=self.team_a, document_type='cv',
                                              title='من غير تاريخ', file=pdf())
        self.assertEqual(self.run_reminders(), 0)
        self.assertEqual(send.call_count, 0)

    def test_send_reminders_command_runs_documents(self, send):
        from django.core.management import call_command
        self.doc(self.team_a, 1)
        call_command('send_reminders', type='documents', stdout=open('/dev/null', 'w'))
        self.assertEqual(len(self.recipients(send)), 4)
        self.assertIn('بينتهي بكره', send.call_args_list[0].args[1])
