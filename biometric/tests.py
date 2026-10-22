"""
اختبارات أجهزة البصمة
  python manage.py test biometric --settings=motionhr.settings_test
"""
import io
from datetime import datetime, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from attendance.test_action_scope import ScopeBase
from biometric.models import BiometricDevice, BiometricPunch, BiometricUserMap

SN = 'CQZ7231260001'


def local(y, mo, d, h, mi, s=0):
    return timezone.make_aware(datetime(y, mo, d, h, mi, s), timezone.get_current_timezone())


class BiometricBase(ScopeBase):
    def setUp(self):
        super().setUp()
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(employee_code='EMP00915')
        Employee._base_manager.filter(pk=self.other_a.pk).update(employee_code='77')
        self.dev_client = Client()   # الجهاز مابيبعتش أي تسجيل دخول

    def register(self, who=None):
        return self.api(who or self.hr_a).post('/biometric/api/devices/', {'serial_number': SN, 'name': 'جهاز المدخل'},
                                               format='json')

    def push(self, body):
        return self.dev_client.post(f'/iclock/cdata?SN={SN}&table=ATTLOG&Stamp=9999', data=body,
                                    content_type='text/plain')


class AdmsTests(BiometricBase):
    def test_unknown_device_kept_waiting_then_accepted_after_registration(self):
        r = self.dev_client.get(f'/iclock/cdata?SN={SN}&options=all&pushver=2.4.1')
        self.assertEqual(r.status_code, 200)
        self.assertIn(f'GET OPTION FROM: {SN}', r.content.decode())
        dev = BiometricDevice.objects.get(serial_number=SN)
        self.assertFalse(dev.is_active)
        self.assertIsNone(dev.company_id)

        body = '915\t2026-10-20 08:58:10\t0\t1\t0\t0\n'
        self.assertEqual(self.push(body).status_code, 403)          # الجهاز بيحتفظ بيها ويعيد
        self.assertEqual(BiometricPunch.objects.count(), 0)

        self.assertEqual(self.register().status_code, 201)
        r = self.push(body + '77\t2026-10-20 09:20:00\t0\t1\t0\t0\n999\t2026-10-20 09:30:00\t0\t1\n')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.decode().startswith('OK'))
        punches = {p.pin: p for p in BiometricPunch.objects.all()}
        self.assertEqual(punches['915'].employee_id, self.team_a.id)       # EMP00915 ← 915
        self.assertEqual(punches['77'].employee_id, self.other_a.id)      # كود 77 بالظبط
        self.assertIsNone(punches['999'].employee_id)                     # محتاج ربط
        self.assertEqual(punches['915'].punch_time, local(2026, 10, 20, 8, 58, 10))
        self.assertEqual(punches['915'].company_id, self.a.id)

        self.push(body)    # الجهاز بعتها تاني
        self.assertEqual(BiometricPunch.objects.filter(pin='915').count(), 1)

    def test_getrequest_and_userinfo(self):
        self.register()
        self.assertEqual(self.dev_client.get(f'/iclock/getrequest?SN={SN}').content.decode(), 'OK')
        r = self.dev_client.post(f'/iclock/cdata?SN={SN}&table=OPERLOG', data='USER PIN=999\tName=Ali Hassan\tPri=0\n',
                                 content_type='text/plain')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(BiometricUserMap.objects.get(company_id=self.a.id, pin='999').device_user_name, 'Ali Hassan')

    def test_device_of_other_company_cannot_be_taken(self):
        self.register()
        r = self.api(self.hr_b).post('/biometric/api/devices/', {'serial_number': SN}, format='json')
        self.assertEqual(r.status_code, 400)


class ManageTests(BiometricBase):
    def test_manual_map_relinks_old_punches(self):
        self.register()
        self.push('999\t2026-10-20 09:30:00\t0\t1\n')
        r = self.api(self.hr_a).post('/biometric/api/user-map/', {'pin': '999', 'employee_id': self.mgr_a.id}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(BiometricPunch.objects.get(pin='999').employee_id, self.mgr_a.id)
        rows = {p['pin']: p for p in self.api(self.hr_a).get('/biometric/api/user-map/').data['pins']}
        self.assertEqual(rows['999']['employee_id'], self.mgr_a.id)
        self.assertTrue(rows['999']['manual'])

    def test_upload_dat_and_excel(self):
        dat = SimpleUploadedFile('attlog.dat', b'   915\t2026-10-19 08:55:00\t0\t1\t0\t0\n   915\t2026-10-19 17:05:00\t1\t1\t0\t0\n')
        r = self.api(self.hr_a).post('/biometric/api/upload/', {'file': dat}, format='multipart')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual((r.data['new'], r.data['unmatched']), (2, 0))

        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(['AC-No.', 'Name', 'Time'])
        ws.append([77, 'x', datetime(2026, 10, 19, 9, 10)])
        ws.append([915, 'y', '2026-10-19 08:55:00'])        # مكررة من الملف اللي فات
        buf = io.BytesIO()
        wb.save(buf)
        xl = SimpleUploadedFile('export.xlsx', buf.getvalue())
        r = self.api(self.hr_a).post('/biometric/api/upload/', {'file': xl}, format='multipart')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual((r.data['read'], r.data['new'], r.data['duplicates']), (2, 1, 1))

    def test_daily_report_compares_with_attendance(self):
        from attendance.models import Attendance
        self.register()
        day = timezone.localdate() - timedelta(days=1)
        d = day.isoformat()
        self.push(f'915\t{d} 08:58:00\t0\t1\n915\t{d} 17:02:00\t1\t1\n')
        Attendance._base_manager.create(company=self.a, employee=self.team_a, date=day, status='present',
                                        check_in_time=local(day.year, day.month, day.day, 9, 10))
        r = self.api(self.hr_a).get(f'/biometric/api/report/?date_from={d}&date_to={d}')
        self.assertEqual(r.status_code, 200, r.data)
        row = [x for x in r.data['days'] if x['employee_id'] == self.team_a.id][0]
        self.assertEqual((row['first_punch'], row['last_punch'], row['punches']), ('08:58', '17:02', 2))
        self.assertEqual(row['system_check_in'], '09:10')
        self.assertEqual(row['diff_in_minutes'], -12)
        # المرحلة الأولى: البصمة مابتغيرش الحضور
        self.assertEqual(Attendance._base_manager.get(employee=self.team_a, date=day).check_in_time,
                         local(day.year, day.month, day.day, 9, 10))
        x = self.api(self.hr_a).get(f'/biometric/api/report/?date_from={d}&date_to={d}&export=xlsx')
        self.assertEqual(x.status_code, 200)

    def test_permissions_and_isolation(self):
        self.register()
        self.push('915\t2026-10-20 08:58:10\t0\t1\n')
        self.assertEqual(self.api(self.mgr_a).get('/biometric/api/devices/').status_code, 403)
        self.assertEqual(self.api(self.team_a).get('/biometric/api/report/').status_code, 403)
        self.assertEqual(self.api(self.hr_b).get('/biometric/api/devices/').data['devices'], [])
        r = self.api(self.hr_b).get('/biometric/api/report/?view=raw&date_from=2026-10-01&date_to=2026-10-31')
        self.assertEqual(r.data['punches'], [])
