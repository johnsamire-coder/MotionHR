"""
اختبارات مجموعة 3: رصيد الإجازات بيتحسب مرة واحدة بس، وتعديل الحالة أو التواريخ بيظبط الرصيد.
الأرقام محسوبة يدوي: رصيد سنوي 21 يوم.

التشغيل:
  python manage.py test leaves.test_leave_balance --settings=motionhr.settings_test
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from companies.models import Branch, Company, Department
from employees.models import Employee, JobTitle
from leaves.models import LeaveBalance, LeaveRequest, LeaveType

ACTION = '/attendance/api/mobile/manager/action/'


class LeaveBalanceBase(TestCase):
    def setUp(self):
        self.co = Company.objects.create(name_ar='شركة', name_en='Co')
        self.branch = Branch.objects.create(company=self.co, name_ar='ر', name_en='M')
        self.dept = Department.objects.create(company=self.co, name_ar='د', name_en='D')
        self.job = JobTitle._base_manager.create(company=self.co, name_ar='م', name_en='S')
        self.hr = self.emp('hr_manager')
        self.e = self.emp()
        self.lt = LeaveType._base_manager.create(company=self.co, name='سنوي', category='annual', days_allowed=21, is_paid=True)
        # بداية الشهر الجاي (نفس السنة لو أمكن) عشان مايبقاش فيه حضور ولا سنة تانية
        today = date.today()
        self.d0 = date(today.year, 12, 1) if today.month < 12 else date(today.year, 12, 20)
        self.bal, _ = LeaveBalance._base_manager.update_or_create(
            company=self.co, employee=self.e, leave_type=self.lt, year=self.d0.year,
            defaults={'total_days': Decimal('21'), 'used_days': 0, 'pending_days': 0},
        )

    _n = 0

    def emp(self, role='employee'):
        LeaveBalanceBase._n += 1
        n = LeaveBalanceBase._n
        u = User.objects.create_user(username=f'lb{n}', password='x', role=role, company=self.co)
        return Employee._base_manager.create(
            user=u, company=self.co, employee_code=f'L{n}', first_name_ar='م', last_name_ar=str(n),
            first_name_en='E', last_name_en=str(n), national_id=f'2920101{n:07d}', hire_date=date(2020, 1, 1),
            birth_date=date(1990, 1, 1), gender='male', basic_salary=Decimal('6000'), phone=f'0155{n:07d}',
            branch=self.branch, department=self.dept, job_title=self.job,
        )

    def request_leave(self, days):
        """زي تقديم الطلب: الأيام بتتحجز في الرصيد المعلق"""
        lv = LeaveRequest._base_manager.create(
            company=self.co, employee=self.e, leave_type=self.lt, start_date=self.d0,
            end_date=self.d0 + timedelta(days=days - 1), days_count=Decimal(days), reason='ت', status='pending',
        )
        LeaveBalance._base_manager.filter(pk=self.bal.pk).update(pending_days=Decimal(days))
        return lv

    def balance(self):
        self.bal.refresh_from_db()
        return float(self.bal.used_days), float(self.bal.pending_days), float(self.bal.remaining_days)

    def client_for(self, emp):
        c = APIClient()
        c.force_authenticate(emp.user)
        return c


class DoubleClickTests(LeaveBalanceBase):
    """1: الضغط مرتين مابيخصمش مرتين"""

    def test_approve_twice_counts_once(self):
        lv = self.request_leave(2)
        c = self.client_for(self.hr)
        self.assertEqual(c.post(ACTION, {'type': 'leave', 'id': lv.id, 'action': 'approve'}, format='json').status_code, 200)
        r = c.post(ACTION, {'type': 'leave', 'id': lv.id, 'action': 'approve'}, format='json')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['message'], 'الطلب ده اتراجع قبل كده')
        self.assertEqual(self.balance(), (2.0, 0.0, 19.0))   # 21 - 2

    def test_reject_after_approve_refused(self):
        lv = self.request_leave(2)
        c = self.client_for(self.hr)
        c.post(ACTION, {'type': 'leave', 'id': lv.id, 'action': 'approve'}, format='json')
        r = c.post(ACTION, {'type': 'leave', 'id': lv.id, 'action': 'reject', 'notes': 'لا'}, format='json')
        self.assertEqual(r.status_code, 409)
        lv.refresh_from_db()
        self.assertEqual(lv.status, 'approved')
        self.assertEqual(self.balance(), (2.0, 0.0, 19.0))

    def test_cancel_twice_returns_balance_once(self):
        lv = self.request_leave(3)
        lv.approve(self.hr.user)
        self.assertEqual(self.balance(), (3.0, 0.0, 18.0))
        c = self.client_for(self.hr)
        url = f'/attendance/api/mobile/manager/leaves/{lv.id}/cancel/'
        self.assertEqual(c.post(url, {'reason': 'خطأ'}, format='json').status_code, 200)
        self.assertEqual(c.post(url, {'reason': 'خطأ'}, format='json').status_code, 400)  # "ملغية مسبقاً"
        self.assertFalse(lv.cancel())
        self.assertEqual(self.balance(), (0.0, 0.0, 21.0))

    def test_model_methods_return_false_second_time(self):
        lv = self.request_leave(1)
        self.assertTrue(lv.approve(self.hr.user))
        self.assertFalse(lv.approve(self.hr.user))
        self.assertFalse(lv.reject(self.hr.user))
        self.assertEqual(self.balance(), (1.0, 0.0, 20.0))


class ManagerEditStatusTests(LeaveBalanceBase):
    """2: تغيير الحالة من شاشة التعديل بيظبط الرصيد"""

    def edit(self, lv, data):
        return self.client_for(self.hr).patch(f'/attendance/api/mobile/manager/leaves/{lv.id}/edit/', data, format='json')

    def test_status_approved_deducts_balance(self):
        lv = self.request_leave(2)
        self.assertEqual(self.edit(lv, {'status': 'approved'}).status_code, 200)
        lv.refresh_from_db()
        self.assertEqual(lv.status, 'approved')
        self.assertEqual(self.balance(), (2.0, 0.0, 19.0))

    def test_status_rejected_releases_pending(self):
        lv = self.request_leave(2)
        self.assertEqual(self.edit(lv, {'status': 'rejected'}).status_code, 200)
        self.assertEqual(self.balance(), (0.0, 0.0, 21.0))

    def test_cancel_approved_returns_used(self):
        lv = self.request_leave(4)
        self.edit(lv, {'status': 'approved'})
        self.assertEqual(self.balance(), (4.0, 0.0, 17.0))
        self.assertEqual(self.edit(lv, {'status': 'cancelled'}).status_code, 200)
        self.assertEqual(self.balance(), (0.0, 0.0, 21.0))

    def test_weird_status_refused(self):
        lv = self.request_leave(2)
        self.assertEqual(self.edit(lv, {'status': 'bogus'}).status_code, 400)
        self.edit(lv, {'status': 'approved'})
        self.assertEqual(self.edit(lv, {'status': 'pending'}).status_code, 400)
        lv.refresh_from_db()
        self.assertEqual(lv.status, 'approved')
        self.assertEqual(self.balance(), (2.0, 0.0, 19.0))

    def test_dates_of_approved_leave_cannot_change(self):
        lv = self.request_leave(2)
        self.edit(lv, {'status': 'approved'})
        r = self.edit(lv, {'end_date': str(self.d0 + timedelta(days=5))})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.balance(), (2.0, 0.0, 19.0))


class EditDatesTests(LeaveBalanceBase):
    """29: تعديل التواريخ بيعيد حساب الأيام والرصيد"""

    def edit(self, lv, data):
        return self.client_for(self.e).patch(f'/attendance/api/mobile/my-leaves/{lv.id}/edit/', data, format='json')

    def test_extend_one_day_to_three_then_approve(self):
        lv = self.request_leave(1)
        r = self.edit(lv, {'end_date': str(self.d0 + timedelta(days=2))})
        self.assertEqual(r.status_code, 200)
        lv.refresh_from_db()
        self.assertEqual(lv.days_count, Decimal('3'))
        self.assertEqual(self.balance(), (0.0, 3.0, 18.0))
        lv.approve(self.hr.user)
        self.assertEqual(self.balance(), (3.0, 0.0, 18.0))

    def test_shorten_releases_pending(self):
        lv = self.request_leave(5)
        self.assertEqual(self.edit(lv, {'end_date': str(self.d0 + timedelta(days=1))}).status_code, 200)
        self.assertEqual(self.balance(), (0.0, 2.0, 19.0))

    def test_extend_beyond_balance_refused(self):
        lv = self.request_leave(1)
        r = self.edit(lv, {'end_date': str(self.d0 + timedelta(days=24))})   # 25 يوم والمتاح 21
        self.assertEqual(r.status_code, 400)
        self.assertIn('غير كافي', r.json()['message'])
        lv.refresh_from_db()
        self.assertEqual(lv.days_count, Decimal('1'))
        self.assertEqual(self.balance(), (0.0, 1.0, 20.0))

    def test_bad_date_is_a_message_not_a_crash(self):
        lv = self.request_leave(1)
        r = self.edit(lv, {'end_date': '2026-13-45'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('صيغة التاريخ', r.json()['message'])

    def test_overlap_refused(self):
        lv = self.request_leave(1)
        LeaveRequest._base_manager.create(
            company=self.co, employee=self.e, leave_type=self.lt, start_date=self.d0 + timedelta(days=3),
            end_date=self.d0 + timedelta(days=3), days_count=Decimal('1'), reason='ت', status='approved',
        )
        r = self.edit(lv, {'end_date': str(self.d0 + timedelta(days=4))})
        self.assertEqual(r.status_code, 400)
        self.assertIn('نفس الفترة', r.json()['message'])

    def test_end_before_start_refused(self):
        lv = self.request_leave(2)
        r = self.edit(lv, {'end_date': str(self.d0 - timedelta(days=1))})
        self.assertEqual(r.status_code, 400)
