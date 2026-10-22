"""
مجموعة 19: الحضور والشيفتات.
  python manage.py test attendance.test_group19_attendance --settings=motionhr.settings_test
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import mock

from django.utils import timezone
from rest_framework.test import APIClient

from attendance.models import (
    Attendance, DailyAttendanceSummary, EmployeeShift, Shift, ShiftAssignment, ShiftRotation,
    ShiftRotationAssignment, ShiftRotationSlot,
)
from attendance.test_payroll_scenarios import CAIRO, PayrollScenarioBase, dt


def api(emp):
    c = APIClient()
    c.force_authenticate(emp.user)
    return c


def at(d, hh, mm=0):
    return datetime.combine(d, time(hh, mm)).replace(tzinfo=CAIRO)


class SummaryTests(PayrollScenarioBase):
    def test_approved_leave_and_holiday_not_absent(self):
        from attendance.test_payroll_scenarios import _leave, _leave_type
        from leaves.official_holiday_models import OfficialHoliday
        _leave(self.emp, _leave_type(self.company), date(2026, 9, 1), date(2026, 9, 1), days=1)
        OfficialHoliday._base_manager.create(company=self.company, name='عيد', start_date=date(2026, 9, 2),
                                             end_date=date(2026, 9, 2))
        DailyAttendanceSummary.compute_for_day(self.emp, date(2026, 9, 1))
        DailyAttendanceSummary.compute_for_day(self.emp, date(2026, 9, 2))
        DailyAttendanceSummary.compute_for_day(self.emp, date(2026, 9, 3))
        st = dict(DailyAttendanceSummary._base_manager.filter(employee=self.emp).values_list('date', 'status'))
        self.assertEqual((st[date(2026, 9, 1)], st[date(2026, 9, 2)], st[date(2026, 9, 3)]),
                         ('on_leave', 'holiday', 'absent'))

    def test_hr_forgiven_late_survives_nightly_recompute(self):
        a = self.attend(date(2026, 9, 1), in_hm=(9, 30))
        Attendance._base_manager.filter(pk=a.pk).update(late_minutes=0, status='present', is_manually_edited=True)
        DailyAttendanceSummary.compute_for_day(self.emp, date(2026, 9, 1))
        s = DailyAttendanceSummary._base_manager.get(employee=self.emp, date=date(2026, 9, 1))
        self.assertEqual((s.status, s.late_minutes), ('present', 0))      # قبل كده: متأخر 30 دقيقة تاني
        self.assertMoney(self.payroll()['late_deduction'], 0)


class LeaveDaysTests(PayrollScenarioBase):
    def test_week_of_annual_leave_counts_working_days_only(self):
        from attendance.test_payroll_scenarios import _leave_type
        from leaves.leave_dates import count_leave_days
        lt = _leave_type(self.company)
        # من الأحد 6 لحد السبت 12 سبتمبر: الجمعة والسبت راحة → 5 أيام
        self.assertEqual(count_leave_days(self.emp, lt, date(2026, 9, 6), date(2026, 9, 12)), 5)
        lt.category = 'sick'
        self.assertEqual(count_leave_days(self.emp, lt, date(2026, 9, 6), date(2026, 9, 12)), 7)

    def test_mobile_request_uses_working_days(self):
        from attendance.test_payroll_scenarios import _leave_type
        from leaves.models import LeaveRequest
        lt = _leave_type(self.company, paid=False, name='بدون أجر')     # من غير رصيد
        r = api(self.emp).post('/attendance/api/mobile/leave-request/', {
            'leave_type_id': lt.id, 'start_date': '2026-11-01', 'end_date': '2026-11-07', 'reason': 'سفر'}, format='json')
        self.assertIn(r.status_code, (200, 201), r.data)
        self.assertEqual(float(LeaveRequest._base_manager.get(employee=self.emp).days_count), 5)


class ShiftPriorityTests(PayrollScenarioBase):
    def rotation_for_employee(self, shift):
        rot = ShiftRotation._base_manager.create(company=self.company, name='تناوب', cycle_length_days=7,
                                                 start_date=date(2026, 1, 4))
        ShiftRotationSlot._base_manager.create(company=self.company, rotation=rot, start_day_index=0,
                                               end_day_index=6, shift=shift)
        ShiftRotationAssignment._base_manager.create(company=self.company, rotation=rot, assignment_type='employee',
                                                     employee=self.emp, start_date=date(2026, 1, 1))

    def test_employee_rotation_beats_company_assignment(self):
        from attendance.api_shifts import get_effective_shift
        night = Shift._base_manager.create(company=self.company, name='ليلي', start_time=time(13), end_time=time(21))
        self.rotation_for_employee(night)
        self.assertEqual(get_effective_shift(self.emp, date(2026, 9, 1)), (night, 'rotation_employee'))

    def test_company_assignment_lets_employee_check_in(self):
        r = api(self.emp).post('/attendance/api/mobile/attendance/', {'action': 'check_in', 'latitude': 30.0, 'longitude': 31.0},
                               format='json')
        self.assertFalse(r.data.get('no_shift_assigned'), r.data)   # قبل كده: "مش مربوط بشيفت"

    def test_variable_weekly_shift_late_from_day_schedule(self):
        from attendance.payroll_rules import _calc_late_minutes
        var = Shift._base_manager.create(company=self.company, name='متغير', shift_mode='variable_weekly',
                                         start_time=time(9), end_time=time(17), grace_period=0,
                                         schedule_config={'days': {'1': {'start': '11:00', 'end': '19:00'}}})
        a = self.attend(date(2026, 9, 1), in_hm=(11, 5))       # الثلاثاء (weekday 1)
        self.assertEqual(_calc_late_minutes(var, a), 5)        # قبل كده 125 من الساعة 9
        from attendance.api_mobile import get_shift_bounds
        start, end = get_shift_bounds(var, date(2026, 9, 1))
        self.assertEqual((timezone.localtime(start).time(), timezone.localtime(end).time()), (time(11), time(19)))


class ShiftAssignmentTests(PayrollScenarioBase):
    def test_future_shift_closes_current_one_day_before(self):
        from attendance.api_shifts import _close_overlapping
        cur = ShiftAssignment._base_manager.create(company=self.company, shift=self.shift, assignment_type='employee',
                                                   employee=self.emp, start_date=date(2026, 1, 1), is_active=True)
        later = ShiftAssignment._base_manager.create(company=self.company, shift=self.shift, assignment_type='employee',
                                                     employee=self.emp, start_date=date(2027, 3, 1), is_active=True)
        _close_overlapping(ShiftAssignment._base_manager.filter(employee=self.emp), date(2026, 11, 1), date(2026, 12, 31))
        cur.refresh_from_db()
        later.refresh_from_db()
        self.assertEqual((cur.is_active, cur.end_date), (True, date(2026, 10, 31)))   # قبل كده كان بيتلغي خالص
        self.assertTrue(later.is_active)

    def test_cancel_department_assignment_stops_mirrors(self):
        from accounts.models import User
        hr = User.objects.create_user(username='hr19', password='x', company=self.company, role='hr_manager')
        a = ShiftAssignment._base_manager.create(company=self.company, shift=self.shift, assignment_type='department',
                                                 department=self.dept, start_date=date(2026, 1, 1), is_active=True)
        m = EmployeeShift._base_manager.create(company=self.company, employee=self.emp, shift=self.shift,
                                               assignment_type='employee', priority=1, start_date=date(2026, 1, 1),
                                               is_active=True)
        c = APIClient()
        c.force_authenticate(hr)
        r = c.delete(f'/attendance/api/mobile/manager/shifts/assignments/{a.id}/delete/')
        if r.status_code == 405:
            r = c.post(f'/attendance/api/mobile/manager/shifts/assignments/{a.id}/delete/')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', r))
        m.refresh_from_db()
        a.refresh_from_db()
        today = timezone.localdate()
        self.assertEqual(m.end_date, today - timedelta(days=1))    # الأيام القديمة على شيفتها والجاية لا
        self.assertEqual(a.end_date, today - timedelta(days=1))


class AutoAttendanceTests(PayrollScenarioBase):
    def test_closed_yesterday_does_not_block_today(self):
        y = timezone.localdate() - timedelta(days=1)
        Attendance._base_manager.create(company=self.company, employee=self.emp, date=y, status='present',
                                        check_in_time=at(y, 9), check_out_time=at(y, 17))
        r = api(self.emp).get('/attendance/api/mobile/employee/auto-checkin-status/')
        self.assertEqual((r.data['status'], r.data['checked_in'], r.data.get('success')), ('not_checked_in', False, True))

    def checkout_at(self, hh, mm=0):
        d = date(2026, 9, 1)
        Attendance._base_manager.update_or_create(
            company=self.company, employee=self.emp, date=d,
            defaults={'status': 'present', 'check_in_time': at(d, 9), 'check_out_time': None, 'shift': self.shift})
        with mock.patch('django.utils.timezone.now', return_value=at(d, hh, mm)):
            return api(self.emp).post('/attendance/api/mobile/employee/auto-check-out/',
                                      {'latitude': 30.0, 'longitude': 31.0}, format='json')

    def test_auto_checkout_overtime_and_early_leave(self):
        r = self.checkout_at(15, 0)
        self.assertEqual((r.status_code, r.data['status']), (400, 'shift_not_ended'))
        r = self.checkout_at(16, 45)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(Attendance._base_manager.get(employee=self.emp, date=date(2026, 9, 1)).early_leave_minutes, 15)
        Attendance._base_manager.filter(employee=self.emp).update(check_out_time=None)
        r = self.checkout_at(18, 30)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(float(Attendance._base_manager.get(employee=self.emp, date=date(2026, 9, 1)).overtime_hours), 1.5)

    def test_mocked_location_rejected(self):
        r = api(self.emp).post('/attendance/api/mobile/attendance/', {
            'action': 'check_in', 'latitude': 30.0, 'longitude': 31.0, 'is_mocked': True}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.data.get('mocked_location'))
        from attendance.models import TrackingAlert
        self.assertTrue(TrackingAlert._base_manager.filter(employee=self.emp, notes__contains='مزيف').exists())

    def test_unknown_device_rejected_for_auto(self):
        r = api(self.emp).post('/attendance/api/mobile/employee/auto-check-out/',
                               {'latitude': 30.0, 'longitude': 31.0, 'device_id': 'not-registered'}, format='json')
        self.assertEqual((r.status_code, r.data['status']), (403, 'device_not_approved'))
