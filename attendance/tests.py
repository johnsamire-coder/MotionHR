from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from attendance.reminders import (
    _employee_has_approved_leave,
    _shift_reminder_is_workday,
)
from leaves.models import LeaveRequest


class ShiftReminderGuardTests(SimpleTestCase):
    def setUp(self):
        self.day = date(2026, 10, 6)  # Tuesday
        self.shift = SimpleNamespace(
            is_active=True,
            shift_mode='fixed',
            schedule_config={},
            is_work_day=lambda day: day.weekday() < 4,
        )

    def test_fallback_shift_without_active_assignment_is_rejected(self):
        self.assertFalse(
            _shift_reminder_is_workday(self.shift, 'company_default', self.day)
        )
        self.assertFalse(_shift_reminder_is_workday(self.shift, None, self.day))

    def test_inactive_shift_is_rejected(self):
        self.shift.is_active = False
        self.assertFalse(_shift_reminder_is_workday(self.shift, 'employee_assignment', self.day))

    def test_regular_assignment_respects_weekly_rest_day(self):
        self.shift.is_work_day = lambda day: False
        self.assertFalse(_shift_reminder_is_workday(self.shift, 'employee_assignment', self.day))

    def test_date_override_and_rotation_slot_are_workdays(self):
        self.shift.is_work_day = lambda day: False
        self.assertTrue(_shift_reminder_is_workday(self.shift, 'override', self.day))
        self.assertTrue(_shift_reminder_is_workday(self.shift, 'rotation_employee', self.day))

    def test_variable_weekly_schedule_only_works_on_configured_days(self):
        self.shift.shift_mode = 'variable_weekly'
        self.shift.schedule_config = {'days': {'1': {'start': '09:00', 'end': '17:00'}}}
        self.assertTrue(_shift_reminder_is_workday(self.shift, 'employee_assignment', self.day))
        self.assertFalse(_shift_reminder_is_workday(self.shift, 'employee_assignment', date(2026, 10, 7)))

    def test_variable_daily_schedule_requires_an_explicit_date(self):
        self.shift.shift_mode = 'variable_daily'
        self.shift.schedule_config = {'dates': {self.day.isoformat(): {'start': '09:00', 'end': '17:00'}}}
        self.assertTrue(_shift_reminder_is_workday(self.shift, 'employee_assignment', self.day))
        self.assertFalse(_shift_reminder_is_workday(self.shift, 'employee_assignment', date(2026, 10, 7)))

    def test_approved_leave_overlapping_the_date_includes_half_day_requests(self):
        employee = object()
        manager = Mock()
        manager.filter.return_value.exists.return_value = True
        with patch.object(LeaveRequest, '_base_manager', manager):
            self.assertTrue(_employee_has_approved_leave(employee, self.day))
        manager.filter.assert_called_once_with(
            employee=employee,
            status='approved',
            start_date__lte=self.day,
            end_date__gte=self.day,
        )
