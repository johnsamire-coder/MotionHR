"""
اختبارات دفعة 7:
129/198/199 صلاحيات الشيفتات، 130/197 إيقاف الشيفت من غير مسح تاريخه، 41/43 التقارير مابتحسبش الإجازة غياب،
112/173 تطبيق سياسة الإجازات بيحافظ على الترحيل والتعديلات، 89 فحص الملفات المرفوعة

التشغيل:
  python manage.py test attendance.test_group7_safety --settings=motionhr.settings_test
"""
import io
import shutil
import tempfile
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/manager/'
_TMP_MEDIA = tempfile.mkdtemp(prefix='motionhr_test_media_')


def _shift(company, name='صباحي'):
    from attendance.models import Shift
    return Shift._base_manager.create(company=company, name=name, start_time=time(9), end_time=time(17))


class ShiftPermissionTests(ScopeBase):
    def test_manager_cannot_create_shift_hr_can(self):
        body = {'name': 'مسائي', 'start_time': '14:00', 'end_time': '22:00'}
        self.assertEqual(self.api(self.mgr_a).post(f'{M}shifts/create/', body, format='json').status_code, 403)
        self.assertIn(self.api(self.hr_a).post(f'{M}shifts/create/', body, format='json').status_code, (200, 201))

    def test_manager_override_only_team_and_not_past(self):
        sh = _shift(self.a)
        tomorrow = str(timezone.localdate() + timedelta(days=1))
        yesterday = str(timezone.localdate() - timedelta(days=1))
        c = self.api(self.mgr_a)
        url = f'{M}shifts/override/create/'
        self.assertEqual(c.post(url, {'employee_id': self.other_a.id, 'shift_id': sh.id, 'override_date': tomorrow}, format='json').status_code, 403)
        self.assertEqual(c.post(url, {'employee_id': self.team_a.id, 'shift_id': sh.id, 'override_date': yesterday}, format='json').status_code, 403)
        self.assertIn(c.post(url, {'employee_id': self.team_a.id, 'shift_id': sh.id, 'override_date': tomorrow}, format='json').status_code, (200, 201))


class ShiftDeleteKeepsHistoryTests(ScopeBase):
    def test_deactivate_keeps_attendance_and_old_assignments(self):
        from attendance.models import Attendance, EmployeeShift
        sh = _shift(self.a)
        es = EmployeeShift._base_manager.create(company=self.a, employee=self.other_a, shift=sh,
                                                start_date=date(2026, 1, 1), is_active=True)
        att = Attendance._base_manager.create(company=self.a, employee=self.other_a, date=date(2026, 9, 1), shift=sh)
        r = self.api(self.hr_a).delete(f'{M}shifts/{sh.id}/delete/')
        self.assertEqual(r.status_code, 200, r.content)
        att.refresh_from_db()
        self.assertEqual(att.shift_id, sh.id)                    # الحضور القديم لسه مربوط بشيفته
        es.refresh_from_db()
        self.assertFalse(es.is_active)                           # التعيين اتقفل مش اتمسح
        self.assertEqual(es.end_date, timezone.localdate())
        sh.refresh_from_db()
        self.assertFalse(sh.is_active)

    def test_shift_in_rotation_must_be_removed_first(self):
        from attendance.models import ShiftRotation, ShiftRotationSlot
        sh = _shift(self.a)
        rot = ShiftRotation._base_manager.create(company=self.a, name='تناوب أ', start_date=date(2026, 1, 1))
        ShiftRotationSlot._base_manager.create(company=self.a, rotation=rot, shift=sh, start_day_index=0, end_day_index=0)
        r = self.api(self.hr_a).delete(f'{M}shifts/{sh.id}/delete/')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(ShiftRotationSlot._base_manager.filter(rotation=rot, shift=sh).exists())


class ReportsDayOffTests(ScopeBase):
    def test_absence_report_skips_approved_leave_days(self):
        from leaves.models import LeaveRequest, LeaveType
        lt = LeaveType._base_manager.create(company=self.a, name='سنوي', category='annual', days_allowed=21)
        LeaveRequest._base_manager.create(company=self.a, employee=self.other_a, leave_type=lt,
                                          start_date=date(2026, 9, 1), end_date=date(2026, 9, 30),
                                          days_count=Decimal('30'), reason='x', status='approved')
        from employees.models import Employee
        from datetime import datetime as _dt
        Employee._base_manager.filter(company=self.a).update(created_at=timezone.make_aware(_dt(2026, 1, 1)))
        r = self.api(self.hr_a).get(f'{M}reports/absence/?year=2026&month=9')
        self.assertEqual(r.status_code, 200)
        ids = [e['employee_id'] for e in r.json()['employees']]
        self.assertNotIn(self.other_a.id, ids)        # إجازة الشهر كله = صفر غياب
        self.assertIn(self.team_a.id, ids)            # اللي ماحضرش ومش في إجازة لسه غايب

    def test_daily_report_shows_on_leave(self):
        from leaves.models import LeaveRequest, LeaveType
        lt = LeaveType._base_manager.create(company=self.a, name='سنوي', category='annual', days_allowed=21)
        d = date(2026, 9, 2)
        LeaveRequest._base_manager.create(company=self.a, employee=self.other_a, leave_type=lt, start_date=d, end_date=d,
                                          days_count=Decimal('1'), reason='x', status='approved')
        r = self.api(self.hr_a).get(f'{M}reports/daily-attendance/?date={d}')
        self.assertEqual(r.status_code, 200)
        row = next(e for e in r.json()['employees'] if e['employee_id'] == self.other_a.id)
        self.assertEqual(row['status'], 'on_leave')


class LeavePolicyApplyTests(ScopeBase):
    def test_apply_keeps_manual_adjustments_and_skips_terminated(self):
        from leaves.models import LeaveBalance, LeaveBalanceAdjustment, LeavePolicy, LeaveType
        year = timezone.localdate().year
        left = self.emp(self.a, status='terminated')   # قبل نوع الإجازة، فمالوش رصيد
        lt = LeaveType._base_manager.create(company=self.a, name='سنوي', category='annual', days_allowed=21)
        LeavePolicy._base_manager.create(company=self.a, name='سياسة', status='active', effective_from=date(year, 1, 1))
        bal = LeaveBalance._base_manager.get(employee=self.other_a, leave_type=lt, year=year)
        # ترحيل 5 أيام من السنة اللي فاتت
        LeaveBalanceAdjustment._base_manager.create(company=self.a, employee=self.other_a, leave_type=lt, year=year,
                                                    adjustment_type='carry_forward', days=5, reason='ترحيل')
        LeaveBalance._base_manager.filter(pk=bal.pk).update(total_days=bal.total_days + 5)
        r = self.api(self.hr_a).post(f'{M}leave-policy/apply-to-existing/', {'year': year}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        bal.refresh_from_db()
        from leaves.signals import _get_entitlement_days
        self.assertEqual(float(bal.total_days), float(_get_entitlement_days(self.a, self.other_a, lt, year)) + 5)
        self.assertFalse(LeaveBalance._base_manager.filter(employee=left, leave_type=lt, year=year).exists())


@override_settings(MEDIA_ROOT=_TMP_MEDIA)
class UploadValidationTests(ScopeBase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TMP_MEDIA, ignore_errors=True)

    def test_mission_upload_rejects_executable(self):
        _, a = self.mission(self.team_a)
        f = SimpleUploadedFile('virus.exe', b'MZ...', content_type='application/pdf')
        r = self.api(self.team_a).post(f'/attendance/api/mobile/employee/missions/assignments/{a.id}/upload/', {'file': f}, format='multipart')
        self.assertEqual(r.status_code, 400)

    def test_profile_photo_must_be_real_image(self):
        fake = SimpleUploadedFile('me.jpg', b'not an image', content_type='image/jpeg')
        r = self.api(self.other_a).post('/attendance/api/mobile/employee/upload-photo/', {'photo': fake}, format='multipart')
        self.assertEqual(r.status_code, 400)
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', (4, 4)).save(buf, format='PNG')
        ok = SimpleUploadedFile('me.png', buf.getvalue(), content_type='image/png')
        r = self.api(self.other_a).post('/attendance/api/mobile/employee/upload-photo/', {'photo': ok}, format='multipart')
        self.assertEqual(r.status_code, 200, r.content)
