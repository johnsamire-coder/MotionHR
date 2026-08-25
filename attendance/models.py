from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime, time
from core.models import TenantModel


class Shift(TenantModel):
    """ط§ظ„ط´ظٹظپطھ - ط£ظˆظ‚ط§طھ ط§ظ„ط¹ظ…ظ„"""

    SHIFT_TYPE_CHOICES = [
        ('fixed', 'ط«ط§ط¨طھ'),
        ('flexible', 'ظ…ط±ظ†'),
        ('rotating', 'ظ…طھط؛ظٹط±'),
        ('morning', 'طµط¨ط§ط­ظٹ'),
        ('evening', 'ظ…ط³ط§ط¦ظٹ'),
        ('night', 'ظ„ظٹظ„ظٹ'),
        ('split', 'ظ…ظ‚ط³ظ…'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name='ط§ط³ظ… ط§ظ„ط´ظٹظپطھ'
    )

    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPE_CHOICES,
        default='fixed',
        verbose_name='ظ†ظˆط¹ ط§ظ„ط´ظٹظپطھ'
    )

    # ط§ظ„ظ†ظˆط¹ ط§ظ„ط³ظ„ظˆظƒظٹ ط§ظ„ط­ظ‚ظٹظ‚ظٹ ظ„ظ„ط´ظٹظپطھ (ظ†ط¶ظٹظپظ‡ ظ…ظ† ط؛ظٹط± ظ…ط§ ظ†ظƒط³ط± ط§ظ„ظ‚ط¯ظٹظ…)
    SHIFT_MODE_CHOICES = [
        ('fixed', 'ط«ط§ط¨طھ'),
        ('flex_fixed', 'ظ…ط±ظ† ط«ط§ط¨طھ'),
        ('flex_split', 'ظ…ط±ظ† ظ…ظ‚ط³ظ…'),
        ('variable_daily', 'ظ…طھط؛ظٹط± ظٹظˆظ…ظٹ'),
        ('variable_weekly', 'ظ…طھط؛ظٹط± ط£ط³ط¨ظˆط¹ظٹ'),
        ('variable_weekly_flex', 'ظ…طھط؛ظٹط± ط£ط³ط¨ظˆط¹ظٹ ظ…ط±ظ†'),
        ('split_fixed', 'ظ…ظ‚ط³ظ… ط«ط§ط¨طھ'),
    ]

    shift_mode = models.CharField(
        max_length=30,
        choices=SHIFT_MODE_CHOICES,
        default='fixed',
        verbose_name='ط§ظ„ظ†ظ…ط· ط§ظ„ط³ظ„ظˆظƒظٹ ظ„ظ„ط´ظٹظپطھ',
        help_text='ط¨ظٹط­ط¯ط¯ ظ…ظ†ط·ظ‚ ط§ظ„ط´ظٹظپطھ: ط«ط§ط¨طھطŒ ظ…ط±ظ†طŒ ظ…طھط؛ظٹط±طŒ ظ…ظ‚ط³ظ…...'
    )

    # preset ظ„ظ„طھظˆظ‚ظٹطھ ط§ظ„ط§ظپطھط±ط§ط¶ظٹ ظپظٹ ط§ظ„ظˆط§ط¬ظ‡ط©
    TIME_PRESET_CHOICES = [
        ('custom', 'ظ…ط®طµطµ'),
        ('morning', 'طµط¨ط§ط­ظٹ'),
        ('evening', 'ظ…ط³ط§ط¦ظٹ'),
        ('night', 'ظ„ظٹظ„ظٹ'),
    ]

    time_preset = models.CharField(
        max_length=20,
        choices=TIME_PRESET_CHOICES,
        default='custom',
        verbose_name='طھظˆظ‚ظٹطھ ط§ظپطھط±ط§ط¶ظٹ',
        help_text='ظ„ظ„ظˆط§ط¬ظ‡ط© ظپظ‚ط·: طµط¨ط§ط­ظٹ / ظ…ط³ط§ط¦ظٹ / ظ„ظٹظ„ظٹ / ظ…ط®طµطµ'
    )

    # ط¹ط¯ط¯ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط·ظ„ظˆط¨ط© ظٹظˆظ…ظٹظ‹ط§ ظپظٹ ط§ظ„ط´ظٹظپطھط§طھ ط§ظ„ظ…ط±ظ†ط©
    required_daily_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=8,
        verbose_name='ط¹ط¯ط¯ ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط·ظ„ظˆط¨ط© ظٹظˆظ…ظٹظ‹ط§',
        help_text='ظ…ظ‡ظ… ظ„ظ„ظ…ط±ظ† ط§ظ„ط«ط§ط¨طھ ظˆط§ظ„ظ…ط±ظ† ط§ظ„ظ…ظ‚ط³ظ…'
    )

    # ظ‡ظ„ ظ…ط³ظ…ظˆط­ ط¨ط®ط±ظˆط¬ ط¬ط²ط¦ظٹ ط«ظ… ط±ط¬ظˆط¹طں
    allow_partial_checkout = models.BooleanField(
        default=False,
        verbose_name='ظٹط³ظ…ط­ ط¨ط®ط±ظˆط¬ ط¬ط²ط¦ظٹ',
        help_text='ظ…ط·ظ„ظˆط¨ ظ„ظ„ظ…ط±ظ† ط§ظ„ظ…ظ‚ط³ظ… ظˆط§ظ„ظ…ظ‚ط³ظ… ط§ظ„ط«ط§ط¨طھ'
    )

    # ط£ظ‚طµظ‰ ط¹ط¯ط¯ ظپطھط±ط§طھ ط´ط؛ظ„ ظپظٹ ط§ظ„ظٹظˆظ…
    max_sessions_per_day = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='ط£ظ‚طµظ‰ ط¹ط¯ط¯ ظپطھط±ط§طھ ظپظٹ ط§ظ„ظٹظˆظ…',
        help_text='ظ…ط«ظ„ط§ظ‹ 2 ظ„ظ„ظ…ط±ظ† ط§ظ„ظ…ظ‚ط³ظ… ط£ظˆ ط§ظ„ظ…ظ‚ط³ظ… ط§ظ„ط«ط§ط¨طھ'
    )

    # ظ†ظˆط¹ ط§ظ„ط¬ط¯ظˆظ„ ط§ظ„ظ…طھط؛ظٹط±
    VARIABLE_SCHEDULE_TYPE_CHOICES = [
        ('none', 'ظ„ط§ ظٹظˆط¬ط¯'),
        ('daily', 'ظٹظˆظ…ظٹ'),
        ('weekly', 'ط£ط³ط¨ظˆط¹ظٹ'),
        ('weekly_flex', 'ط£ط³ط¨ظˆط¹ظٹ ظ…ط±ظ†'),
    ]

    variable_schedule_type = models.CharField(
        max_length=20,
        choices=VARIABLE_SCHEDULE_TYPE_CHOICES,
        default='none',
        verbose_name='ظ†ظˆط¹ ط§ظ„ط¬ط¯ظˆظ„ ط§ظ„ظ…طھط؛ظٹط±'
    )

    # ط¬ط¯ظˆظ„ ط¯ظٹظ†ط§ظ…ظٹظƒظٹ JSON:
    # variable_daily  -> ط£ظˆظ‚ط§طھ ط§ظ„ظٹظˆظ…
    # variable_weekly -> ط£ظˆظ‚ط§طھ ط§ظ„ط£ظٹط§ظ…
    # split_fixed     -> ظپطھط±طھظٹظ† ط£ظˆ ط£ظƒط«ط±
    # flex_split      -> ظ‚ظˆط§ط¹ط¯ ط§ظ„ظپطھط±ط§طھ
    schedule_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ط¬ط¯ظˆظ„ ط§ظ„ط¯ظٹظ†ط§ظ…ظٹظƒظٹ'
    )

    start_time = models.TimeField(
        verbose_name='ظˆظ‚طھ ط§ظ„ط¨ط¯ط§ظٹط©'
    )

    end_time = models.TimeField(
        verbose_name='ظˆظ‚طھ ط§ظ„ظ†ظ‡ط§ظٹط©'
    )

    crosses_midnight = models.BooleanField(
        default=False,
        verbose_name='ظٹظ…طھط¯ ظ„ظ„ظٹظˆظ… ط§ظ„طھط§ظ„ظٹ',
        help_text='ظپط¹ظ‘ظ„ ظ„ظˆ ط§ظ„ط´ظٹظپطھ ط¨ظٹط¨ط¯ط£ ط¨ط§ظ„ظ„ظٹظ„ ظˆط¨ظٹظ†طھظ‡ظٹ ط§ظ„طµط¨ط­'
    )

    
    early_checkin_grace = models.IntegerField(default=30, verbose_name="سماحية الحضور المبكر (دقائق)")
    early_checkout_grace = models.IntegerField(default=0, verbose_name="سماحية الانصراف المبكر (دقائق)")
        default=15,
        verbose_name='ظپطھط±ط© ط§ظ„ط³ظ…ط§ط­ ظ„ظ„طھط£ط®ظٹط± (ط¯ظ‚ظٹظ‚ط©)',
        help_text='ط§ظ„ظˆظ‚طھ ط§ظ„ظ…ط³ظ…ظˆط­ ظ„ظ„طھط£ط®ظٹط± ط¨ط¯ظˆظ† ط§ط­طھط³ط§ط¨ طھط£ط®ظٹط±'
    )

    # ظ…ط±ظˆظ†ط© ط§ظ„ط§ظ†طµط±ط§ظپ (ظ…ظپظٹط¯ط© ظ„ظ…ظ‡ظ†ط¯ط³ظٹ ط§ظ„ظ…ظˆط§ظ‚ط¹ ظˆط§ظ„ظ…ظٹط¯ط§ظ†ظٹظٹظ†)
    early_checkout_allowed = models.BooleanField(
        default=False,
        verbose_name='ط§ظ„ط³ظ…ط§ط­ ط¨ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…ط¨ظƒط±'
    )
    early_checkout_minutes = models.IntegerField(
        default=0,
        verbose_name='ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…ط¨ظƒط± ط§ظ„ظ…ط³ظ…ظˆط­ (ط¯ظ‚ط§ط¦ظ‚)',
        help_text='ظ…ط«ط§ظ„: 60 = ط§ظ„ط³ظ…ط§ط­ ط¨ط§ظ„ط§ظ†طµط±ط§ظپ ظ‚ط¨ظ„ ظ…ظٹط¹ط§ط¯ ط§ظ„ط´ظٹظپطھ ط¨ط³ط§ط¹ط©'
    )
    late_checkout_allowed = models.BooleanField(
        default=False,
        verbose_name='ط§ظ„ط³ظ…ط§ط­ ط¨ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…طھط£ط®ط±'
    )
    late_checkout_minutes = models.IntegerField(
        default=0,
        verbose_name='ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…طھط£ط®ط± ط§ظ„ظ…ط³ظ…ظˆط­ (ط¯ظ‚ط§ط¦ظ‚)',
        help_text='ظ…ط«ط§ظ„: 180 = ط§ظ„ط³ظ…ط§ط­ ط¨ط§ظ„ط§ظ†طµط±ط§ظپ ط¨ط¹ط¯ ظ…ظٹط¹ط§ط¯ ط§ظ„ط´ظٹظپطھ ط¨ظ€ 3 ط³ط§ط¹ط§طھ'
    )

    grace_early_leave = models.IntegerField(
        default=0,
        verbose_name='ظپطھط±ط© ط§ظ„ط³ظ…ط§ط­ ظ„ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…ط¨ظƒط± (ط¯ظ‚ظٹظ‚ط©)',
        help_text='ط§ظ„ظˆظ‚طھ ط§ظ„ظ…ط³ظ…ظˆط­ ظ„ظ„ط§ظ†طµط±ط§ظپ ظ‚ط¨ظ„ ظ†ظ‡ط§ظٹط© ط§ظ„ط´ظٹظپطھ ط¨ط¯ظˆظ† ط§ط­طھط³ط§ط¨ ط§ظ†طµط±ط§ظپ ظ…ط¨ظƒط±'
    )

    early_checkin_minutes = models.IntegerField(
        default=30,
        verbose_name='ظ…ط³ظ…ظˆط­ ط§ظ„ط­ط¶ظˆط± ظ‚ط¨ظ„ ط§ظ„ط´ظٹظپطھ (ط¯ظ‚ظٹظ‚ط©)',
        help_text='ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ط§ظ„ظ…ط³ظ…ظˆط­ ظ„طھط³ط¬ظٹظ„ ط§ظ„ط­ط¶ظˆط± ظ‚ط¨ظ„ ط¨ط¯ط§ظٹط© ط§ظ„ط´ظٹظپطھ'
    )

    work_sunday = models.BooleanField(default=True, verbose_name='ط§ظ„ط£ط­ط¯')
    work_monday = models.BooleanField(default=True, verbose_name='ط§ظ„ط§ط«ظ†ظٹظ†')
    work_tuesday = models.BooleanField(default=True, verbose_name='ط§ظ„ط«ظ„ط§ط«ط§ط،')
    work_wednesday = models.BooleanField(default=True, verbose_name='ط§ظ„ط£ط±ط¨ط¹ط§ط،')
    work_thursday = models.BooleanField(default=True, verbose_name='ط§ظ„ط®ظ…ظٹط³')
    work_friday = models.BooleanField(default=False, verbose_name='ط§ظ„ط¬ظ…ط¹ط©')
    work_saturday = models.BooleanField(default=False, verbose_name='ط§ظ„ط³ط¨طھ')

    break_duration = models.IntegerField(
        default=60,
        verbose_name='ظ…ط¯ط© ط§ظ„ط±ط§ط­ط© (ط¯ظ‚ظٹظ‚ط©)'
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name='ط´ظٹظپطھ ط§ظپطھط±ط§ط¶ظٹ ظ„ظ„ط´ط±ظƒط©',
        help_text='ظ„ظˆ ظ…ظپظٹط´ ط´ظٹظپطھ ظ…ط­ط¯ط¯ ظ„ظ„ظ…ظˆط¸ظپطŒ ظ‡ظٹط³طھط®ط¯ظ… ط§ظ„ط´ظٹظپطھ ط§ظ„ط§ظپطھط±ط§ط¶ظٹ'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='ظ†ط´ط·'
    )

    class Meta:
        verbose_name = 'ط´ظٹظپطھ'
        verbose_name_plural = 'ط§ظ„ط´ظٹظپطھط§طھ'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company'],
                condition=models.Q(is_default=True),
                name='uniq_default_shift_per_company',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    @property
    def work_hours(self):
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)

        if self.crosses_midnight or end <= start:
            end += timedelta(days=1)

        duration = end - start
        hours = duration.total_seconds() / 3600
        hours -= self.break_duration / 60
        return round(hours, 2)

    def is_work_day(self, date):
        # date.weekday(): 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        day_map = {
            6: self.work_sunday,
            0: self.work_monday,
            1: self.work_tuesday,
            2: self.work_wednesday,
            3: self.work_thursday,
            4: self.work_friday,
            5: self.work_saturday,
        }
        return day_map.get(date.weekday(), False)

    def get_shift_periods(self, day):
        """
        ط¨طھط±ط¬ط¹ ظپطھط±ط§طھ ط§ظ„ط´ظٹظپطھ ظ„ظ„ظٹظˆظ… ط¯ظ‡
        method wrapper ظ„ظ€ get_shift_periods ظپظٹ api_mobile
        ط¨طھظپط¹ظ‘ظ„ _calc_split_shift_metrics ظپظٹ payroll_rules
        """
        try:
            from attendance.api_mobile import get_shift_periods as _get_periods
            return _get_periods(self, day)
        except Exception:
            return []



class AttendanceSession(TenantModel):
    """
    ظپطھط±ط© ط­ط¶ظˆط± ظˆط§ط­ط¯ط© â€” ظ„ظ„ط´ظٹظپطھط§طھ ط§ظ„ظ…ظ‚ط³ظ…ط© ظˆط§ظ„ظ…ط±ظ†ط© ط§ظ„ظ…ظ‚ط³ظ…ط©
    ظƒظ„ ظٹظˆظ… ظ…ظ…ظƒظ† ظٹظƒظˆظ† ظپظٹظ‡ ط£ظƒطھط± ظ…ظ† ظپطھط±ط© (session)
    """

    attendance = models.ForeignKey(
        'Attendance',
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='ط³ط¬ظ„ ط§ظ„ط­ط¶ظˆط±'
    )

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    session_number = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='ط±ظ‚ظ… ط§ظ„ظپطھط±ط©',
        help_text='1 ظ„ظ„ظپطھط±ط© ط§ظ„ط£ظˆظ„ظ‰طŒ 2 ظ„ظ„ط«ط§ظ†ظٹط©...'
    )

    check_in_time = models.DateTimeField(
        verbose_name='ظˆظ‚طھ ط¯ط®ظˆظ„ ط§ظ„ظپطھط±ط©'
    )

    check_out_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='ظˆظ‚طھ ط®ط±ظˆط¬ ط§ظ„ظپطھط±ط©'
    )

    check_in_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ط¯ط®ظˆظ„'
    )

    check_in_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ط¯ط®ظˆظ„'
    )

    check_out_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ط®ط±ظˆط¬'
    )

    check_out_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ط®ط±ظˆط¬'
    )

    on_mission = models.BooleanField(default=False, verbose_name='ظپظٹ ظ…ط£ظ…ظˆط±ظٹط©')
    is_partial = models.BooleanField(
        default=False,
        verbose_name='ط®ط±ظˆط¬ ط¬ط²ط¦ظٹ',
        help_text='True ظ„ظˆ ط§ظ„ظ…ظˆط¸ظپ ط®ط±ط¬ ظˆط±ط¬ط¹ طھط§ظ†ظٹ'
    )

    worked_minutes = models.IntegerField(
        default=0,
        verbose_name='ط¯ظ‚ط§ط¦ظ‚ ط§ظ„ط¹ظ…ظ„ ظپظٹ ط§ظ„ظپطھط±ط© ط¯ظٹ'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ'
    )

    class Meta:
        verbose_name = 'ظپطھط±ط© ط­ط¶ظˆط±'
        verbose_name_plural = 'ظپطھط±ط§طھ ط§ظ„ط­ط¶ظˆط±'
        ordering = ['attendance', 'session_number']
        unique_together = [['attendance', 'session_number']]

    def __str__(self):
        return f"{self.employee} - ظٹظˆظ… {self.attendance.date} - ظپطھط±ط© {self.session_number}"

    def calculate_worked_minutes(self):
        """ط¨ظٹط­ط³ط¨ ط¯ظ‚ط§ط¦ظ‚ ط§ظ„ط¹ظ…ظ„ ظ„ظˆ ظپظٹظ‡ check_out"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            self.worked_minutes = int(delta.total_seconds() / 60)
            return self.worked_minutes
        return 0

    @property
    def is_complete(self):
        """ظ‡ظ„ ط§ظ„ظپطھط±ط© ط§ظƒطھظ…ظ„طھ (ظپظٹظ‡ط§ ط¯ط®ظˆظ„ ظˆط®ط±ظˆط¬)"""
        return self.check_in_time is not None and self.check_out_time is not None


class AttendancePolicy(TenantModel):
    # ط³ظٹط§ط³ط© ط§ظ„ط£ط°ظˆظ†ط§طھ
    permission_enabled = models.BooleanField(default=False)
    permission_monthly_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    permission_monthly_count = models.IntegerField(default=0)
    permission_max_hours_per_request = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    permission_fraction_as_full = models.BooleanField(default=False)
    permission_reset_cycle = models.CharField(
        max_length=20, 
        choices=[('calendar', 'ط´ظ‡ط± ظ…ظٹظ„ط§ط¯ظٹ'), ('payroll', 'ط¯ظˆط±ط© ط§ظ„ظ…ط±طھط¨')],
        default='calendar'
    )

    """ط³ظٹط§ط³ط© ط§ظ„ط­ط¶ظˆط± ظˆط§ظ„ط®طµظ… â€” ظ„ظƒظ„ ط´ط±ظƒط©/ظپط±ط¹/ظ‚ط³ظ…"""

    # === Late Warning System ===
    late_warning_enabled = models.BooleanField(
        default=False,
        verbose_name='طھظپط¹ظٹظ„ ظ†ط¸ط§ظ… ط§ظ„ط¥ظ†ط°ط§ط±ط§طھ'
    )
    late_warning_threshold = models.PositiveSmallIntegerField(
        default=2,
        verbose_name='ط¹ط¯ط¯ ط§ظ„ط¥ظ†ط°ط§ط±ط§طھ ظ‚ط¨ظ„ ط§ظ„ط®طµظ…'
    )
    late_warning_deduction_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'ط«ط§ط¨طھ'),
            ('progressive', 'طھطµط§ط¹ط¯ظٹ ط¨ط­ط¯ ط£ظ‚طµظ‰'),
            ('progressive_step', 'طھطµط§ط¹ط¯ظٹ ظƒظ„ ط¹ط¯ط¯ ظ…ط±ط§طھ'),
        ],
        default='fixed',
        verbose_name='ظ†ظˆط¹ ط§ظ„ط®طµظ…'
    )
    late_warning_deduction_value = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.25,
        verbose_name='ظ‚ظٹظ…ط© ط§ظ„ط®طµظ… ط§ظ„ط£ط³ط§ط³ظٹط© (ط¬ط²ط، ظ…ظ† ط§ظ„ظٹظˆظ…)'
    )
    late_warning_max_deduction = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        verbose_name='ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ظ„ظ„ط®طµظ… (ط¬ط²ط، ظ…ظ† ط§ظ„ظٹظˆظ…)'
    )
    late_warning_step_rate = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='ظ…ط¹ط¯ظ„ ط§ظ„ط²ظٹط§ط¯ط© ظƒظ„ N ظ…ط±ط§طھ'
    )

    STATUS_CHOICES = [
        ('draft', 'ظ…ط³ظˆط¯ط©'),
        ('approved', 'ظ…ط¹طھظ…ط¯'),
        ('active', 'ظ†ط´ط·'),
        ('archived', 'ظ…ط¤ط±ط´ظپ'),
    ]

    name = models.CharField(max_length=200, verbose_name='ط§ط³ظ… ط§ظ„ط³ظٹط§ط³ط©')
    effective_from = models.DateField(verbose_name='ط³ط§ط±ظٹط© ظ…ظ†')
    effective_to = models.DateField(blank=True, null=True, verbose_name='ط³ط§ط±ظٹط© ظ„ط­ط¯')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='ط§ظ„ط­ط§ظ„ط©')
    approved_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_policies',
        verbose_name='ظˆط§ظپظ‚ ط¨ظˆط§ط³ط·ط©'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ')

    class Meta:
        verbose_name = 'ط³ظٹط§ط³ط© ط­ط¶ظˆط±'
        verbose_name_plural = 'ط³ظٹط§ط³ط§طھ ط§ظ„ط­ط¶ظˆط±'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.name} ({self.effective_from})"


class AttendancePolicyAssignment(TenantModel):
    """ط±ط¨ط· ط§ظ„ط³ظٹط§ط³ط© ط¨ط´ط±ظƒط©/ظپط±ط¹/ظ‚ط³ظ…"""

    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'ط´ط±ظƒط©'),
        ('branch', 'ظپط±ط¹'),
        ('department', 'ظ‚ط³ظ…'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='assignments', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    assignment_type = models.CharField(
        max_length=20, choices=ASSIGNMENT_TYPE_CHOICES,
        default='company', verbose_name='ظ†ظˆط¹ ط§ظ„طھط¹ظٹظٹظ†'
    )
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظپط±ط¹'
    )
    department = models.ForeignKey(
        'companies.Department', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظ‚ط³ظ…'
    )
    priority = models.IntegerField(
        default=3,
        help_text='1=ظ‚ط³ظ…, 2=ظپط±ط¹, 3=ط´ط±ظƒط©',
        verbose_name='ط§ظ„ط£ظˆظ„ظˆظٹط©'
    )

    class Meta:
        verbose_name = 'طھط¹ظٹظٹظ† ط³ظٹط§ط³ط©'
        verbose_name_plural = 'طھط¹ظٹظٹظ†ط§طھ ط§ظ„ط³ظٹط§ط³ط§طھ'


class LateRule(models.Model):
    # LateRule_branch_added
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظپط±ط¹ ط§ظ„ظ…ط³طھظ‡ط¯ظپ'
    )
    department = models.ForeignKey(
        'companies.Department', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظ‚ط³ظ… ط§ظ„ظ…ط³طھظ‡ط¯ظپ'
    )

    """ظ‚ظˆط§ط¹ط¯ ط®طµظ… ط§ظ„طھط£ط®ظٹط±"""

    DEDUCTION_TYPE_CHOICES = [
        ('none', 'ظ„ط§ ط®طµظ…'),
        ('day_fraction', 'ظ†ط³ط¨ط© ظ…ظ† ط§ظ„ظٹظˆظ…'),
        ('fixed_amount', 'ظ…ط¨ظ„ط؛ ط«ط§ط¨طھ'),
        ('per_minute', 'ظ„ظƒظ„ ط¯ظ‚ظٹظ‚ط©'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='late_rules', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    from_minutes = models.IntegerField(default=0, verbose_name='ظ…ظ† ط¯ظ‚ظٹظ‚ط©')
    to_minutes = models.IntegerField(default=15, verbose_name='ط¥ظ„ظ‰ ط¯ظ‚ظٹظ‚ط©')
    deduction_type = models.CharField(
        max_length=20, choices=DEDUCTION_TYPE_CHOICES,
        default='none', verbose_name='ظ†ظˆط¹ ط§ظ„ط®طµظ…'
    )
    deduction_value = models.DecimalField(
        max_digits=8, decimal_places=4, default=0,
        verbose_name='ظ‚ظٹظ…ط© ط§ظ„ط®طµظ…',
        help_text='0.25 = ط±ط¨ط¹ ظٹظˆظ… / 50 = ظ…ط¨ظ„ط؛ ط«ط§ط¨طھ / 1 = ظ„ظƒظ„ ط¯ظ‚ظٹظ‚ط©'
    )
    display_order = models.IntegerField(default=0, verbose_name='ط§ظ„طھط±طھظٹط¨')

    class Meta:
        verbose_name = 'ظ‚ط§ط¹ط¯ط© طھط£ط®ظٹط±'
        verbose_name_plural = 'ظ‚ظˆط§ط¹ط¯ ط§ظ„طھط£ط®ظٹط±'
        ordering = ['display_order', 'from_minutes']

    def __str__(self):
        return f"{self.policy.name}: {self.from_minutes}-{self.to_minutes} ط¯ â†’ {self.deduction_type}"


class AbsenceRule(models.Model):
    # AbsenceRule_branch_added
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظپط±ط¹ ط§ظ„ظ…ط³طھظ‡ط¯ظپ'
    )
    department = models.ForeignKey(
        'companies.Department', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظ‚ط³ظ… ط§ظ„ظ…ط³طھظ‡ط¯ظپ'
    )

    """ظ‚ظˆط§ط¹ط¯ ط®طµظ… ط§ظ„ط؛ظٹط§ط¨"""

    ABSENCE_TYPE_CHOICES = [
        ('unexcused', 'ط¨ط¯ظˆظ† ط¥ط°ظ†'),
        ('consecutive', 'ظ…طھطھط§ظ„ظٹ'),
        ('repeated', 'ظ…طھظƒط±ط± ظپظٹ ط§ظ„ط´ظ‡ط±'),
    ]

    DEDUCTION_TYPE_CHOICES = [
        ('day_fraction', 'ظ†ط³ط¨ط© ظ…ظ† ط§ظ„ظٹظˆظ…'),
        ('fixed_amount', 'ظ…ط¨ظ„ط؛ ط«ط§ط¨طھ'),
        ('warning', 'ط¥ظ†ط°ط§ط± ظپظ‚ط·'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='absence_rules', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    absence_type = models.CharField(
        max_length=20, choices=ABSENCE_TYPE_CHOICES,
        default='unexcused', verbose_name='ظ†ظˆط¹ ط§ظ„ط؛ظٹط§ط¨'
    )
    consecutive_days = models.IntegerField(
        default=1, null=True, blank=True,
        verbose_name='ط¹ط¯ط¯ ط§ظ„ط£ظٹط§ظ… ط§ظ„ظ…طھطھط§ظ„ظٹط©'
    )
    occurrences_in_month = models.IntegerField(
        default=1, null=True, blank=True,
        verbose_name='ط¹ط¯ط¯ ط§ظ„ظ…ط±ط§طھ ظپظٹ ط§ظ„ط´ظ‡ط±'
    )
    deduction_type = models.CharField(
        max_length=20, choices=DEDUCTION_TYPE_CHOICES,
        default='day_fraction', verbose_name='ظ†ظˆط¹ ط§ظ„ط®طµظ…'
    )
    deduction_value = models.DecimalField(
        max_digits=8, decimal_places=4, default=1,
        verbose_name='ظ‚ظٹظ…ط© ط§ظ„ط®طµظ…',
        help_text='1 = ظٹظˆظ… ظƒط§ظ…ظ„ / 1.5 = ظٹظˆظ… ظˆظ†طµ / 50 = ظ…ط¨ظ„ط؛ ط«ط§ط¨طھ'
    )
    display_order = models.IntegerField(default=0, verbose_name='ط§ظ„طھط±طھظٹط¨')

    class Meta:
        verbose_name = 'ظ‚ط§ط¹ط¯ط© ط؛ظٹط§ط¨'
        verbose_name_plural = 'ظ‚ظˆط§ط¹ط¯ ط§ظ„ط؛ظٹط§ط¨'
        ordering = ['display_order']


class OvertimeRule(models.Model):
    # OvertimeRule_branch_added
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظپط±ط¹ ط§ظ„ظ…ط³طھظ‡ط¯ظپ'
    )
    department = models.ForeignKey(
        'companies.Department', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='ط§ظ„ظ‚ط³ظ… ط§ظ„ظ…ط³طھظ‡ط¯ظپ'
    )

    """ظ‚ظˆط§ط¹ط¯ ط§ظ„ط£ظˆظپط± طھط§ظٹظ…"""

    OVERTIME_TYPE_CHOICES = [
        ('regular', 'ط¹ط§ط¯ظٹ'),
        ('after_shift', 'ط¨ط¹ط¯ ط§ظ„ط´ظٹظپطھ'),
        ('weekend', 'ظٹظˆظ… ط±ط§ط­ط©'),
        ('holiday', 'ط¥ط¬ط§ط²ط© ط±ط³ظ…ظٹط©'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='overtime_rules', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    overtime_type = models.CharField(
        max_length=20, choices=OVERTIME_TYPE_CHOICES,
        default='after_shift', verbose_name='ظ†ظˆط¹ ط§ظ„ط£ظˆظپط± طھط§ظٹظ…'
    )
    multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.5,
        verbose_name='ط§ظ„ظ…ط¶ط§ط¹ظپ',
        help_text='1.5 = ظ…ط±ط© ظˆظ†طµ / 2.0 = ط¶ط¹ظپظٹظ†'
    )
    min_minutes = models.IntegerField(
        default=30,
        verbose_name='ط£ظ‚ظ„ ظˆظ‚طھ ظٹطھط­ط³ط¨ (ط¯ظ‚ظٹظ‚ط©)'
    )
    max_hours_per_day = models.IntegerField(
        default=4, null=True, blank=True,
        verbose_name='ط£ظ‚طµظ‰ ط³ط§ط¹ط§طھ ظپظٹ ط§ظ„ظٹظˆظ…'
    )
    max_hours_per_month = models.IntegerField(
        default=40, null=True, blank=True,
        verbose_name='ط£ظ‚طµظ‰ ط³ط§ط¹ط§طھ ظپظٹ ط§ظ„ط´ظ‡ط±'
    )
    requires_approval = models.BooleanField(
        default=False, verbose_name='ظٹط­طھط§ط¬ ظ…ظˆط§ظپظ‚ط© ظ…ط³ط¨ظ‚ط©'
    )
    display_order = models.IntegerField(default=0, verbose_name='ط§ظ„طھط±طھظٹط¨')

    class Meta:
        verbose_name = 'ظ‚ط§ط¹ط¯ط© ط£ظˆظپط± طھط§ظٹظ…'
        verbose_name_plural = 'ظ‚ظˆط§ط¹ط¯ ط§ظ„ط£ظˆظپط± طھط§ظٹظ…'
        ordering = ['display_order']


class NightShiftRule(models.Model):
    """ظ‚ظˆط§ط¹ط¯ ط¨ط¯ظ„ ط§ظ„ط´ظٹظپطھ ط§ظ„ظ„ظٹظ„ظٹ"""

    ALLOWANCE_TYPE_CHOICES = [
        ('fixed_amount', 'ظ…ط¨ظ„ط؛ ط«ط§ط¨طھ'),
        ('percentage', 'ظ†ط³ط¨ط© ظ…ظ† ط§ظ„ظٹظˆظ…ظٹ'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='night_shift_rules', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    allowance_type = models.CharField(
        max_length=20, choices=ALLOWANCE_TYPE_CHOICES,
        default='fixed_amount', verbose_name='ظ†ظˆط¹ ط§ظ„ط¨ط¯ظ„'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=50,
        verbose_name='ط§ظ„ظ…ط¨ظ„ط؛ ط§ظ„ط«ط§ط¨طھ'
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        verbose_name='ط§ظ„ظ†ط³ط¨ط© ط§ظ„ظ…ط¦ظˆظٹط© ظ…ظ† ط§ظ„ط£ط¬ط± ط§ظ„ظٹظˆظ…ظٹ'
    )
    night_start_hour = models.IntegerField(
        default=20, verbose_name='ط¨ط¯ط§ظٹط© ط§ظ„ظ„ظٹظ„ (ط³ط§ط¹ط©)',
        help_text='20 = 8 ظ…ط³ط§ط،ظ‹'
    )
    min_night_hours = models.IntegerField(
        default=4, verbose_name='ط£ظ‚ظ„ ط³ط§ط¹ط§طھ ظ„ظٹظ„ظٹط© ظ„ظ„ط§ط³طھط­ظ‚ط§ظ‚'
    )

    class Meta:
        verbose_name = 'ظ‚ط§ط¹ط¯ط© ط¨ط¯ظ„ ظ„ظٹظ„ظٹ'
        verbose_name_plural = 'ظ‚ظˆط§ط¹ط¯ ط§ظ„ط¨ط¯ظ„ ط§ظ„ظ„ظٹظ„ظٹ'


class WeekendWorkRule(models.Model):
    """ظ‚ظˆط§ط¹ط¯ ط§ظ„ط¹ظ…ظ„ ظٹظˆظ… ط§ظ„ط±ط§ط­ط©"""

    COMPENSATION_TYPE_CHOICES = [
        ('overtime_multiplier', 'ظ†ط³ط¨ط© ظ…ظ† ط§ظ„ظ…ط±طھط¨'),
        ('fixed_amount', 'ظ…ط¨ظ„ط؛ ط«ط§ط¨طھ'),
        ('day_off', 'ظٹظˆظ… ط¥ط¬ط§ط²ط© ط¨ط¯ظٹظ„'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='weekend_work_rules', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    compensation_type = models.CharField(
        max_length=30, choices=COMPENSATION_TYPE_CHOICES,
        default='overtime_multiplier', verbose_name='ظ†ظˆط¹ ط§ظ„طھط¹ظˆظٹط¶'
    )
    multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=2.0,
        verbose_name='ط§ظ„ظ…ط¶ط§ط¹ظپ'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        null=True, blank=True, verbose_name='ط§ظ„ظ…ط¨ظ„ط؛ ط§ظ„ط«ط§ط¨طھ'
    )

    class Meta:
        verbose_name = 'ظ‚ط§ط¹ط¯ط© ط¹ظ…ظ„ ظٹظˆظ… ط§ظ„ط±ط§ط­ط©'
        verbose_name_plural = 'ظ‚ظˆط§ط¹ط¯ ط§ظ„ط¹ظ…ظ„ ظٹظˆظ… ط§ظ„ط±ط§ط­ط©'


class LateRepeatPenalty(models.Model):
    """ط¬ط²ط§ط، طھظƒط±ط§ط± ط§ظ„طھط£ط®ظٹط± ظپظٹ ط§ظ„ط´ظ‡ط±"""

    PENALTY_TYPE_CHOICES = [
        ('warning', 'ط¥ظ†ط°ط§ط±'),
        ('deduction', 'ط®طµظ…'),
        ('suspension', 'ظˆظ‚ظپ'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='late_repeat_penalties', verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )
    occurrences = models.IntegerField(
        default=3, verbose_name='ط¹ط¯ط¯ ظ…ط±ط§طھ ط§ظ„طھط£ط®ظٹط± ظپظٹ ط§ظ„ط´ظ‡ط±'
    )
    penalty_type = models.CharField(
        max_length=20, choices=PENALTY_TYPE_CHOICES,
        default='warning', verbose_name='ظ†ظˆط¹ ط§ظ„ط¬ط²ط§ط،'
    )
    deduction_value = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        null=True, blank=True, verbose_name='ظ‚ظٹظ…ط© ط§ظ„ط®طµظ…'
    )
    description = models.TextField(blank=True, verbose_name='ظˆطµظپ ط§ظ„ط¬ط²ط§ط،')

    class Meta:
        verbose_name = 'ط¬ط²ط§ط، طھظƒط±ط§ط± ط§ظ„طھط£ط®ظٹط±'
        verbose_name_plural = 'ط¬ط²ط§ط،ط§طھ طھظƒط±ط§ط± ط§ظ„طھط£ط®ظٹط±'
        ordering = ['occurrences']


class ShiftAssignment(TenantModel):
    """طھط¹ظٹظٹظ† ط§ظ„ط´ظٹظپطھ ط¹ظ„ظ‰ ظ…ط³طھظˆظ‰ ط´ط±ظƒط© / ظپط±ط¹ / ظ‚ط³ظ… / ظ…ظˆط¸ظپ"""

    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'ط´ط±ظƒط©'),
        ('branch', 'ظپط±ط¹'),
        ('department', 'ظ‚ط³ظ…'),
        ('employee', 'ظ…ظˆط¸ظپ'),
    ]

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name='ط§ظ„ط´ظٹظپطھ'
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        verbose_name='ظ†ظˆط¹ ط§ظ„طھط¹ظٹظٹظ†'
    )

    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shift_assignments',
        verbose_name='ط§ظ„ظپط±ط¹'
    )

    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shift_assignments',
        verbose_name='ط§ظ„ظ‚ط³ظ…'
    )

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shift_assignments',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    excluded_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='excluded_from_shift_assignments',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپظˆظ† ط§ظ„ظ…ط³طھط«ظ†ظˆظ†'
    )

    start_date = models.DateField(
        verbose_name='طھط§ط±ظٹط® ط§ظ„ط¨ط¯ط§ظٹط©'
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='طھط§ط±ظٹط® ط§ظ„ظ†ظ‡ط§ظٹط©'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='ظ†ط´ط·'
    )

    priority = models.IntegerField(
        default=4,
        verbose_name='ط§ظ„ط£ظˆظ„ظˆظٹط©',
        help_text='1=ظ…ظˆط¸ظپ, 2=ظ‚ط³ظ…, 3=ظپط±ط¹, 4=ط´ط±ظƒط©'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ'
    )

    class Meta:
        verbose_name = 'طھط¹ظٹظٹظ† ط´ظٹظپطھ'
        verbose_name_plural = 'طھط¹ظٹظٹظ†ط§طھ ط§ظ„ط´ظٹظپطھط§طھ'
        ordering = ['priority', '-start_date']

    def __str__(self):
        target = 'ط؛ظٹط± ظ…ط­ط¯ط¯'
        if self.assignment_type == 'employee' and self.employee:
            target = self.employee.full_name_ar
        elif self.assignment_type == 'department' and self.department:
            target = self.department.name_ar
        elif self.assignment_type == 'branch' and self.branch:
            target = self.branch.name_ar
        elif self.assignment_type == 'company' and self.company:
            target = self.company.name_ar
        return f"{self.shift.name} â†’ {target}"


class EmployeeShift(TenantModel):
    """ط±ط¨ط· ط§ظ„ظ…ظˆط¸ظپ ط¨ط§ظ„ط´ظٹظپطھ"""

    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'ط´ط±ظƒط©'),
        ('branch', 'ظپط±ط¹'),
        ('department', 'ظ‚ط³ظ…'),
        ('employee', 'ظ…ظˆط¸ظپ'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='ط§ظ„ط´ظٹظپطھ'
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default='employee',
        verbose_name='ظ†ظˆط¹ ط§ظ„طھط¹ظٹظٹظ†'
    )

    start_date = models.DateField(
        verbose_name='طھط§ط±ظٹط® ط§ظ„ط¨ط¯ط§ظٹط©'
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='طھط§ط±ظٹط® ط§ظ„ظ†ظ‡ط§ظٹط©'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='ظ†ط´ط·'
    )

    priority = models.IntegerField(
        default=1,
        verbose_name='ط§ظ„ط£ظˆظ„ظˆظٹط©',
        help_text='1=ظ…ظˆط¸ظپ, 2=ظ‚ط³ظ…, 3=ظپط±ط¹, 4=ط´ط±ظƒط©'
    )

    class Meta:
        verbose_name = 'ط´ظٹظپطھ ظ…ظˆط¸ظپ'
        verbose_name_plural = 'ط´ظٹظپطھط§طھ ط§ظ„ظ…ظˆط¸ظپظٹظ†'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.shift.name}"


class ShiftChangeRequest(TenantModel):
    """ط·ظ„ط¨ طھط؛ظٹظٹط± ط´ظٹظپطھ ظ…ط¹ ظ…ظˆط§ظپظ‚ط§طھ"""

    STATUS_CHOICES = [
        ('pending', 'ظپظٹ ط§ظ„ط§ظ†طھط¸ط§ط±'),
        ('approved', 'ظ…ظˆط§ظپظ‚ ط¹ظ„ظٹظ‡'),
        ('rejected', 'ظ…ط±ظپظˆط¶'),
        ('cancelled', 'ظ…ظ„ط؛ظٹ'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shift_change_requests',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='shift_changes_requested',
        verbose_name='ط·ظ„ط¨ ط¨ظˆط§ط³ط·ط©'
    )

    old_shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='old_change_requests',
        verbose_name='ط§ظ„ط´ظٹظپطھ ط§ظ„ظ‚ط¯ظٹظ…'
    )

    new_shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='new_change_requests',
        verbose_name='ط§ظ„ط´ظٹظپطھ ط§ظ„ط¬ط¯ظٹط¯'
    )

    effective_from = models.DateField(
        verbose_name='طھط§ط±ظٹط® ط¨ط¯ط§ظٹط© ط§ظ„ط³ط±ظٹط§ظ†'
    )

    effective_to = models.DateField(
        blank=True,
        null=True,
        verbose_name='طھط§ط±ظٹط® ظ†ظ‡ط§ظٹط© ط§ظ„ط³ط±ظٹط§ظ†'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='ط§ظ„ط­ط§ظ„ط©'
    )

    requires_approval = models.BooleanField(
        default=True,
        verbose_name='ظٹط­طھط§ط¬ ظ…ظˆط§ظپظ‚ط©'
    )

    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_changes_approved',
        verbose_name='ظˆط§ظپظ‚ ط¨ظˆط§ط³ط·ط©'
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name='ط³ط¨ط¨ ط§ظ„ط±ظپط¶'
    )

    reason = models.TextField(
        blank=True,
        verbose_name='ط³ط¨ط¨ ط·ظ„ط¨ ط§ظ„طھط؛ظٹظٹط±'
    )

    notified_manager = models.BooleanField(default=False, verbose_name='طھظ… ط¥ط¨ظ„ط§ط؛ ط§ظ„ظ…ط¯ظٹط±')
    notified_hr = models.BooleanField(default=False, verbose_name='طھظ… ط¥ط¨ظ„ط§ط؛ HR')
    notified_employee = models.BooleanField(default=False, verbose_name='طھظ… ط¥ط¨ظ„ط§ط؛ ط§ظ„ظ…ظˆط¸ظپ')

    class Meta:
        verbose_name = 'ط·ظ„ط¨ طھط؛ظٹظٹط± ط´ظٹظپطھ'
        verbose_name_plural = 'ط·ظ„ط¨ط§طھ طھط؛ظٹظٹط± ط§ظ„ط´ظٹظپطھط§طھ'
        ordering = ['-created_at']

    def __str__(self):
        return f"ط·ظ„ط¨ طھط؛ظٹظٹط± ط´ظٹظپطھ - {self.employee} - {self.status}"


class ShiftOverride(TenantModel):
    """ط§ط³طھط«ظ†ط§ط، ط´ظٹظپطھ ظ„ظٹظˆظ… ظ…ط¹ظٹظ†"""

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shift_overrides',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    override_date = models.DateField(
        verbose_name='طھط§ط±ظٹط® ط§ظ„ط§ط³طھط«ظ†ط§ط،'
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='overrides',
        verbose_name='ط§ظ„ط´ظٹظپطھ ط§ظ„ط¨ط¯ظٹظ„'
    )

    reason = models.TextField(
        blank=True,
        verbose_name='ط³ط¨ط¨ ط§ظ„ط§ط³طھط«ظ†ط§ط،'
    )

    class Meta:
        verbose_name = 'ط§ط³طھط«ظ†ط§ط، ط´ظٹظپطھ'
        verbose_name_plural = 'ط§ط³طھط«ظ†ط§ط،ط§طھ ط§ظ„ط´ظٹظپطھط§طھ'
        ordering = ['-override_date']
        unique_together = [['employee', 'override_date']]

    def __str__(self):
        return f"{self.employee} - {self.override_date} - {self.shift.name}"


class ShiftRotation(TenantModel):
    """ط¯ظˆط±ط© ط§ظ„طھظ†ط§ظˆط¨"""
    name = models.CharField(max_length=100, verbose_name='ط§ط³ظ… ط§ظ„طھظ†ط§ظˆط¨')
    cycle_length_days = models.PositiveSmallIntegerField(default=7, verbose_name='ط·ظˆظ„ ط§ظ„ط¯ظˆط±ط© (ط£ظٹط§ظ…)')
    start_date = models.DateField(verbose_name='طھط§ط±ظٹط® ط¨ط¯ط§ظٹط© ط§ظ„طھظ†ط§ظˆط¨ ط§ظ„ظ…ط±ط¬ط¹ظٹ')
    is_active = models.BooleanField(default=True, verbose_name='ظ†ط´ط·')

    class Meta:
        verbose_name = 'طھظ†ط§ظˆط¨ ط´ظٹظپطھط§طھ'
        verbose_name_plural = 'طھظ†ط§ظˆط¨ط§طھ ط§ظ„ط´ظٹظپطھط§طھ'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.cycle_length_days} ظٹظˆظ…)"


class ShiftRotationSlot(TenantModel):
    """ظپطھط±ط§طھ ط§ظ„ط´ظٹظپطھط§طھ ط¯ط§ط®ظ„ ط§ظ„ط¯ظˆط±ط©"""
    rotation = models.ForeignKey(
        ShiftRotation,
        on_delete=models.CASCADE,
        related_name='slots',
        verbose_name='ط§ظ„طھظ†ط§ظˆط¨'
    )
    start_day_index = models.PositiveSmallIntegerField(
        verbose_name='ظ…ظ† ظٹظˆظ… ط±ظ‚ظ…',
        help_text='0 = ط£ظˆظ„ ظٹظˆظ… ظپظٹ ط§ظ„ط¯ظˆط±ط©'
    )
    end_day_index = models.PositiveSmallIntegerField(
        verbose_name='ط¥ظ„ظ‰ ظٹظˆظ… ط±ظ‚ظ…'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rotation_slots',
        verbose_name='ط§ظ„ط´ظٹظپطھ (ظپط§ط±ط؛ = ط¥ط¬ط§ط²ط©)'
    )

    class Meta:
        ordering = ['start_day_index']

    def __str__(self):
        shift_name = self.shift.name if self.shift else 'ط±ط§ط­ط©'
        return f"ظٹظˆظ… {self.start_day_index} - {self.end_day_index}: {shift_name}"


class ShiftRotationAssignment(TenantModel):
    """طھط¹ظٹظٹظ† ط§ظ„طھظ†ط§ظˆط¨ ط¹ظ„ظ‰ ط§ظ„ظ…ظˆط¸ظپظٹظ†/ط§ظ„ط£ظ‚ط³ط§ظ…/ط§ظ„ظپط±ظˆط¹"""
    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'ط´ط±ظƒط©'),
        ('branch', 'ظپط±ط¹'),
        ('department', 'ظ‚ط³ظ…'),
        ('employee', 'ظ…ظˆط¸ظپ'),
    ]
    rotation = models.ForeignKey(
        ShiftRotation,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='ط§ظ„طھظ†ط§ظˆط¨'
    )
    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        verbose_name='ظ†ظˆط¹ ط§ظ„طھط¹ظٹظٹظ†'
    )
    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='ط§ظ„ظپط±ط¹'
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='ط§ظ„ظ‚ط³ظ…'
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )
    start_date = models.DateField(verbose_name='طھط§ط±ظٹط® ط§ظ„ط¨ط¯ط§ظٹط©')
    end_date = models.DateField(blank=True, null=True, verbose_name='طھط§ط±ظٹط® ط§ظ„ظ†ظ‡ط§ظٹط©')
    priority = models.IntegerField(
        default=4,
        verbose_name='ط§ظ„ط£ظˆظ„ظˆظٹط©',
        help_text='1=ظ…ظˆط¸ظپ, 2=ظ‚ط³ظ…, 3=ظپط±ط¹, 4=ط´ط±ظƒط©'
    )
    is_active = models.BooleanField(default=True, verbose_name='ظ†ط´ط·')

    class Meta:
        ordering = ['priority', '-start_date']

class Attendance(TenantModel):
    """ط³ط¬ظ„ ط§ظ„ط­ط¶ظˆط± ط§ظ„ظٹظˆظ…ظٹ"""
    
    STATUS_CHOICES = [
        ('present', 'ط­ط§ط¶ط±'),
        ('absent', 'ط؛ط§ط¦ط¨'),
        ('late', 'ظ…طھط£ط®ط±'),
        ('early_leave', 'ط§ظ†طµط±ط§ظپ ظ…ط¨ظƒط±'),
        ('on_leave', 'ظپظٹ ط¥ط¬ط§ط²ط©'),
        ('holiday', 'ط¹ط·ظ„ط© ط±ط³ظ…ظٹط©'),
        ('weekend', 'ط¥ط¬ط§ط²ط© ط£ط³ط¨ظˆط¹ظٹط©'),
    ]
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )
    
    date = models.DateField(
        verbose_name='ط§ظ„طھط§ط±ظٹط®'
    )
    
    # ط§ظ„ط­ط¶ظˆط±
    check_in_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='ظˆظ‚طھ ط§ظ„ط­ط¶ظˆط±'
    )
    check_in_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ط­ط¶ظˆط±'
    )
    check_in_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ط­ط¶ظˆط±'
    )
    check_in_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='ط¹ظ†ظˆط§ظ† ط§ظ„ط­ط¶ظˆط±'
    )
    check_in_within_range = models.BooleanField(
        default=False,
        verbose_name='ط¯ط§ط®ظ„ ظ†ط·ط§ظ‚ ط§ظ„ظپط±ط¹'
    )
    check_in_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ ط§ظ„ط­ط¶ظˆط±'
    )
    
    # ط§ظ„ط§ظ†طµط±ط§ظپ
    check_out_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='ظˆظ‚طھ ط§ظ„ط§ظ†طµط±ط§ظپ'
    )
    check_out_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ط§ظ†طµط±ط§ظپ'
    )
    check_out_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ط§ظ†طµط±ط§ظپ'
    )
    check_out_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='ط¹ظ†ظˆط§ظ† ط§ظ„ط§ظ†طµط±ط§ظپ'
    )
    check_out_within_range = models.BooleanField(
        default=False,
        verbose_name='ط¯ط§ط®ظ„ ظ†ط·ط§ظ‚ ط§ظ„ظپط±ط¹'
    )
    check_out_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ ط§ظ„ط§ظ†طµط±ط§ظپ'
    )
    
    # ط§ظ„ط­ط³ط§ط¨ط§طھ
    work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ط³ط§ط¹ط§طھ ط§ظ„ط¹ظ…ظ„'
    )
    late_minutes = models.IntegerField(
        default=0,
        verbose_name='ط¯ظ‚ط§ط¦ظ‚ ط§ظ„طھط£ط®ظٹط±'
    )
    early_leave_minutes = models.IntegerField(
        default=0,
        verbose_name='ط¯ظ‚ط§ط¦ظ‚ ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…ط¨ظƒط±'
    )
    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ط³ط§ط¹ط§طھ ط§ظ„ط£ظˆظپط± طھط§ظٹظ…'
    )
    
    # ط§ظ„ط­ط§ظ„ط©
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present',
        verbose_name='ط§ظ„ط­ط§ظ„ط©'
    )
    
    # ط§ظ„ط´ظٹظپطھ ط§ظ„ظ…ط³ظ†ط¯
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='attendances',
        verbose_name='ط§ظ„ط´ظٹظپطھ'
    )
    
    # ظ‡ظ„ طھظ… طھط¹ط¯ظٹظ„ظ‡ ظٹط¯ظˆظٹط§ظ‹
    on_mission = models.BooleanField(default=False, verbose_name='ظپظٹ ظ…ط£ظ…ظˆط±ظٹط©')
    is_manually_edited = models.BooleanField(
        default=False,
        verbose_name='ظ…ط¹ط¯ظ„ ظٹط¯ظˆظٹط§ظ‹'
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ ط§ظ„ط¥ط¯ط§ط±ط©'
    )
    
    class Meta:
        verbose_name = 'ط³ط¬ظ„ ط­ط¶ظˆط±'
        verbose_name_plural = 'ط³ط¬ظ„ط§طھ ط§ظ„ط­ط¶ظˆط±'
        ordering = ['-date', '-check_in_time']
        unique_together = [['employee', 'date']]
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.date}"
    
    def calculate_work_hours(self):
        """ط­ط³ط§ط¨ ط³ط§ط¹ط§طھ ط§ظ„ط¹ظ…ظ„ - ظٹط¹طھظ…ط¯ ط¹ظ„ظ‰ AttendanceSession ظ„ظˆ ظ…ظˆط¬ظˆط¯ط©"""
        try:
            from attendance.models import AttendanceSession

            sessions = list(
                AttendanceSession._base_manager.filter(
                    attendance=self
                ).order_by('session_number')
            )

            complete_sessions = [s for s in sessions if s.check_in_time and s.check_out_time]

            if complete_sessions:
                total_minutes = 0
                for session in complete_sessions:
                    if not (session.worked_minutes or 0):
                        session.calculate_worked_minutes()
                        session.save(update_fields=['worked_minutes'])
                    total_minutes += int(session.worked_minutes or 0)

                self.work_hours = round(total_minutes / 60.0, 2)
                return self.work_hours
        except Exception:
            pass

        # fallback ط§ظ„ظ‚ط¯ظٹظ… ظ„ظˆ ظ…ظپظٹط´ sessions
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours = duration.total_seconds() / 3600
            self.work_hours = round(hours, 2)
            return self.work_hours

        self.work_hours = 0
        return 0
    
    def calculate_late_minutes(self):
        """ط­ط³ط§ط¨ ط¯ظ‚ط§ط¦ظ‚ ط§ظ„طھط£ط®ظٹط±"""
        if self.check_in_time and self.shift:
            shift_start = datetime.combine(
                self.date,
                self.shift.start_time
            )
            # طھط­ظˆظٹظ„ check_in_time ظ„ظ†ظپط³ timezone
            check_in_naive = self.check_in_time.replace(tzinfo=None)
            
            if check_in_naive > shift_start:
                diff = check_in_naive - shift_start
                minutes = int(diff.total_seconds() / 60)
                # ط®طµظ… ظپطھط±ط© ط§ظ„ط³ظ…ط§ط­
                minutes -= self.shift.grace_period
                self.late_minutes = max(0, minutes)
            else:
                self.late_minutes = 0
        return self.late_minutes


class LocationLog(TenantModel):
    """
    ط³ط¬ظ„ طھطھط¨ط¹ ط§ظ„ظ…ظˆط§ظ‚ط¹ ط§ظ„ظ…ط³طھظ…ط±
    ظ„ظ„ظ…ظˆط¸ظپظٹظ† ط§ظ„ظ…ظٹط¯ط§ظ†ظٹظٹظ† ط§ظ„ظ„ظٹ ظپط¹ظ‘ط§ظ„ظٹظ† is_field_worker
    """
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_logs',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )
    
    timestamp = models.DateTimeField(
        verbose_name='ط§ظ„ظˆظ‚طھ'
    )
    
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='ط®ط· ط§ظ„ط¹ط±ط¶'
    )
    
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='ط®ط· ط§ظ„ط·ظˆظ„'
    )
    
    accuracy = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='ط¯ظ‚ط© ط§ظ„ظ…ظˆظ‚ط¹ (ظ…طھط±)'
    )
    
    speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='ط§ظ„ط³ط±ط¹ط© (ظƒظ…/ط³)'
    )
    
    battery_level = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='ظ…ط³طھظˆظ‰ ط§ظ„ط¨ط·ط§ط±ظٹط© %'
    )
    
    address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='ط§ظ„ط¹ظ†ظˆط§ظ†'
    )
    
    class Meta:
        verbose_name = 'ط³ط¬ظ„ ظ…ظˆظ‚ط¹'
        verbose_name_plural = 'ط³ط¬ظ„ط§طھ ط§ظ„ظ…ظˆط§ظ‚ط¹'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['employee', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.timestamp}"


class LocationCheckIn(TenantModel):
    """
    Check-in ظپظٹ ظ…ظˆط§ظ‚ط¹ ظ…ط­ط¯ط¯ط©
    ظ…ظپظٹط¯ ظ„ظ„ظ…ط´طھط±ظٹط§طھطŒ ط§ظ„ظ…ط¨ظٹط¹ط§طھطŒ ط§ظ„طµظٹط§ظ†ط©طŒ ط§ظ„ط®
    """
    
    VISIT_TYPE_CHOICES = [
        ('client_visit', 'ط²ظٹط§ط±ط© ط¹ظ…ظٹظ„'),
        ('supplier_visit', 'ط²ظٹط§ط±ط© ظ…ظˆط±ط¯'),
        ('site_inspection', 'ظ…ط¹ط§ظٹظ†ط© ظ…ظˆظ‚ط¹'),
        ('maintenance', 'طµظٹط§ظ†ط©'),
        ('delivery', 'طھظˆطµظٹظ„'),
        ('meeting', 'ط§ط¬طھظ…ط§ط¹'),
        ('purchase', 'ط´ط±ط§ط،'),
        ('other', 'ط£ط®ط±ظ‰'),
    ]
    
    STATUS_CHOICES = [
        ('arrived', 'ظˆطµظ„'),
        ('in_progress', 'ط¬ط§ط±ظٹ ط§ظ„ط¹ظ…ظ„'),
        ('completed', 'ظ…ظƒطھظ…ظ„'),
        ('cancelled', 'ظ…ظ„ط؛ظٹ'),
    ]
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_checkins',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )
    
    visit_type = models.CharField(
        max_length=30,
        choices=VISIT_TYPE_CHOICES,
        verbose_name='ظ†ظˆط¹ ط§ظ„ط²ظٹط§ط±ط©'
    )
    
    location_name = models.CharField(
        max_length=300,
        verbose_name='ط§ط³ظ… ط§ظ„ظ…ظˆظ‚ط¹/ط§ظ„ط¹ظ…ظٹظ„'
    )
    
    # ظˆظ‚طھ ط§ظ„ظˆطµظˆظ„
    arrival_time = models.DateTimeField(
        verbose_name='ظˆظ‚طھ ط§ظ„ظˆطµظˆظ„'
    )
    arrival_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ظˆطµظˆظ„'
    )
    arrival_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ظˆطµظˆظ„'
    )
    arrival_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='ط¹ظ†ظˆط§ظ† ط§ظ„ظˆطµظˆظ„'
    )
    
    # ظˆظ‚طھ ط§ظ„ظ…ط؛ط§ط¯ط±ط©
    departure_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='ظˆظ‚طھ ط§ظ„ظ…ط؛ط§ط¯ط±ط©'
    )
    departure_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ظ…ط؛ط§ط¯ط±ط©'
    )
    departure_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ظ…ط؛ط§ط¯ط±ط©'
    )
    
    # ط§ظ„طھظپط§طµظٹظ„
    purpose = models.TextField(
        blank=True,
        null=True,
        verbose_name='ط§ظ„ط؛ط±ط¶ ظ…ظ† ط§ظ„ط²ظٹط§ط±ط©'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ'
    )
    
    photo = models.ImageField(
        upload_to='attendance/checkins/',
        blank=True,
        null=True,
        verbose_name='طµظˆط±ط©'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='arrived',
        verbose_name='ط§ظ„ط­ط§ظ„ط©'
    )
    
    class Meta:
        verbose_name = 'ط²ظٹط§ط±ط© ظ…ظˆظ‚ط¹'
        verbose_name_plural = 'ط²ظٹط§ط±ط§طھ ط§ظ„ظ…ظˆط§ظ‚ط¹'
        ordering = ['-arrival_time']
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.location_name} - {self.arrival_time}"
    
    @property
    def duration_minutes(self):
        """ظ…ط¯ط© ط§ظ„ط²ظٹط§ط±ط© ط¨ط§ظ„ط¯ظ‚ط§ط¦ظ‚"""
        if self.arrival_time and self.departure_time:
            duration = self.departure_time - self.arrival_time
            return int(duration.total_seconds() / 60)
        return None



class DailyAttendanceSummary(TenantModel):
    """
    ظ…ظ„ط®طµ ظٹظˆظ…ظٹ ظ„ط­ط¶ظˆط± ظƒظ„ ظ…ظˆط¸ظپ.
    ط¨ظٹطھط­ط³ط¨ ظˆظ‚طھ check_out ظˆظٹطھط­ط¯ط« ط¨ظ€ Cron ظƒظ„ ظ„ظٹظ„ط©.
    ط¨ظٹط³ط±ظ‘ط¹ ط­ط³ط§ط¨ ط§ظ„ظ…ط±طھط¨ط§طھ ظˆط§ظ„طھظ‚ط§ط±ظٹط±.
    """

    STATUS_CHOICES = [
        ('present', 'ط­ط§ط¶ط±'),
        ('absent', 'ط؛ط§ط¦ط¨'),
        ('late', 'ظ…طھط£ط®ط±'),
        ('on_leave', 'ظپظٹ ط¥ط¬ط§ط²ط©'),
        ('weekend', 'ط¥ط¬ط§ط²ط© ط£ط³ط¨ظˆط¹ظٹط©'),
        ('mission', 'ظ…ط£ظ…ظˆط±ظٹط©'),
        ('holiday', 'ط¹ط·ظ„ط© ط±ط³ظ…ظٹط©'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='daily_summaries',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    date = models.DateField(
        verbose_name='ط§ظ„طھط§ط±ظٹط®'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent',
        verbose_name='ط§ظ„ط­ط§ظ„ط©'
    )

    effective_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent',
        verbose_name='ط§ظ„ط­ط§ظ„ط© ط§ظ„ظپط¹ظ„ظٹط© (ط¨ط¹ط¯ ط§ظ„ط£ط°ظˆظ†ط§طھ)'
    )

    late_minutes = models.IntegerField(
        default=0,
        verbose_name='ط¯ظ‚ط§ط¦ظ‚ ط§ظ„طھط£ط®ظٹط±'
    )

    work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ط³ط§ط¹ط§طھ ط§ظ„ط¹ظ…ظ„'
    )

    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ط³ط§ط¹ط§طھ ط§ظ„ط£ظˆظپط±طھط§ظٹظ…'
    )

    is_night_shift = models.BooleanField(
        default=False,
        verbose_name='ط´ظٹظپطھ ظ„ظٹظ„ظٹ'
    )

    is_weekend_work = models.BooleanField(
        default=False,
        verbose_name='ط¹ظ…ظ„ ظپظٹ ظٹظˆظ… ط§ظ„ط±ط§ط­ط©'
    )

    early_leave_minutes = models.IntegerField(
        default=0,
        verbose_name='ط¯ظ‚ط§ط¦ظ‚ ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…ط¨ظƒط±'
    )

    permission_hours_used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ط³ط§ط¹ط§طھ ط§ظ„ط¥ط°ظ† ط§ظ„ظ…ط³طھط®ط¯ظ…ط©'
    )

    flex_delta_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ظپط±ظ‚ ط³ط§ط¹ط§طھ ط§ظ„ط´ظٹظپطھ ط§ظ„ظ…ط±ظ†'
    )

    flex_status = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='ط­ط§ظ„ط© طھط³ظˆظٹط© ط§ظ„ط´ظٹظپطھ ط§ظ„ظ…ط±ظ†',
        help_text='pending / approved / rejected / none'
    )

    shift = models.ForeignKey(
        'attendance.Shift',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_summaries',
        verbose_name='ط§ظ„ط´ظٹظپطھ'
    )

    policy = models.ForeignKey(
        'attendance.AttendancePolicy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_summaries',
        verbose_name='ط§ظ„ط³ظٹط§ط³ط©'
    )

    class Meta:
        verbose_name = 'ظ…ظ„ط®طµ ظٹظˆظ…ظٹ'
        verbose_name_plural = 'ط§ظ„ظ…ظ„ط®طµط§طھ ط§ظ„ظٹظˆظ…ظٹط©'
        ordering = ['-date']
        unique_together = [['employee', 'date']]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"

    @classmethod
    def compute_for_day(cls, employee, target_date):
        """
        ظٹط­ط³ط¨ ط£ظˆ ظٹط­ط¯ط« ط§ظ„ظ…ظ„ط®طµ ط§ظ„ظٹظˆظ…ظٹ ظ„ظ…ظˆط¸ظپ ظپظٹ ظٹظˆظ… ظ…ط¹ظٹظ†.
        ط¨ظٹط³طھط®ط¯ظ… ظ†ظپط³ ط§ظ„ظ…ظ†ط·ظ‚ ط§ظ„ظ„ظٹ ظپظٹ payroll_rules.
        """
        try:
            from attendance.payroll_rules import (
                _get_shift_for_date,
                _calc_late_minutes,
                _calc_overtime_hours,
                _calc_split_shift_metrics,
                _is_night_shift,
                _is_weekend_work,
                _get_active_policy,
            )
            from attendance.models import Attendance, AttendanceSession

            from django.utils import timezone

            att = Attendance._base_manager.filter(
                employee=employee,
                date=target_date,
            ).first()

            # ظ„ظˆ ظپظٹظ‡ Attendance ظ…طھط³ط¬ظ„ ط¹ظ„ظ‰ ط´ظٹظپطھ ظ…ط¹ظٹظ†طŒ ط¯ظ‡ ط£ظˆظ„ظ‰ ظ…ظ† ط¥ط¹ط§ط¯ط© ط¬ظ„ط¨ ط§ظ„ط´ظٹظپطھ ط§ظ„ظپط¹ظ„ظٹ
            day_shift = getattr(att, 'shift', None) or _get_shift_for_date(employee, target_date)
            company = getattr(employee, 'company', None)
            department = getattr(employee, 'department', None)
            branch = getattr(employee, 'branch', None)
            policy = _get_active_policy(company, target_date, department=department, branch=branch)

            # ط£ظٹ ظٹظˆظ… ظپظٹظ‡ ط­ط¶ظˆط± ظ…ظپطھظˆط­ ظ…ظ† ط؛ظٹط± check_out -> ظ…ط§ ظ†ط·ظ„ط¹ط´ ظ„ظ‡ summary ظ†ظ‡ط§ط¦ظٹط©
            # ظˆظ„ظˆ ظپظٹظ‡ summary ظ‚ط¯ظٹظ…ط© ظ„ظ†ظپط³ ط§ظ„ظٹظˆظ… ظ†ظ…ط³ط­ظ‡ط§ ط¹ط´ط§ظ† ظ…ط§ ظٹط¨ظ‚ط§ط´ ظپظٹظ‡ ط¨ظٹط§ظ†ط§طھ ظƒط¯ط§ط¨ط©
            if att and getattr(att, 'check_in_time', None) and not getattr(att, 'check_out_time', None):
                cls._base_manager.filter(employee=employee, date=target_date).delete()
                return None

            # ظ…ط§ ظ†ط­ط³ط¨ط´ ظ…ظ„ط®طµ ظ†ظ‡ط§ط¦ظٹ ظ„ظ„ظٹظˆظ… ط§ظ„ط­ط§ظ„ظٹ ظ„ظˆ ظ„ط³ظ‡ ظ…ظپظٹط´ ط­ط¶ظˆط±/ط§ظ†طµط±ط§ظپ ظ…ظƒطھظ…ظ„
            if target_date == timezone.localdate() and (not att or not getattr(att, 'check_out_time', None)):
                cls._base_manager.filter(employee=employee, date=target_date).delete()
                return None

            if not att or not getattr(att, 'check_in_time', None):
                if day_shift and not day_shift.is_work_day(target_date):
                    status = 'weekend'
                else:
                    status = 'absent'

                obj, _ = cls._base_manager.update_or_create(
                    employee=employee,
                    date=target_date,
                    defaults=dict(
                        company=company,
                        status=status,
                        effective_status=status,
                        late_minutes=0,
                        work_hours=0,
                        overtime_hours=0,
                        is_night_shift=False,
                        is_weekend_work=False,
                        shift=day_shift,
                        policy=policy,
                    )
                )
                return obj

            shift_mode = getattr(day_shift, 'shift_mode', '') if day_shift else ''
            if day_shift and shift_mode == 'split_fixed':
                sessions = list(AttendanceSession._base_manager.filter(
                    attendance=att
                ).order_by('session_number'))
                metrics = _calc_split_shift_metrics(day_shift, att, sessions, target_date)
                late_min = metrics['late_minutes'] + metrics['shortage_minutes']
                work_h = round(metrics['worked_minutes'] / 60, 2)
                ot_h = 0.0
            else:
                late_min = _calc_late_minutes(day_shift, att)
                work_h = float(getattr(att, 'work_hours', 0) or 0)
                ot_h = _calc_overtime_hours(day_shift, att)

            is_night = _is_night_shift(day_shift)
            is_weekend = _is_weekend_work(day_shift, target_date)

            if late_min > 0:
                status = 'late'
            else:
                status = 'present'

            _early_leave = int(getattr(att, 'early_leave_minutes', 0) or 0)

            _perm_hours = 0.0
            try:
                from attendance.models import PermissionLedger
                from decimal import Decimal
                _entries = PermissionLedger._base_manager.filter(
                    employee=employee,
                    reference_date=target_date,
                )
                _perm_hours = float(sum(
                    Decimal(str(e.minutes_used or 0)) for e in _entries
                ) / 60)
            except Exception:
                pass

            _flex_delta = 0.0
            _flex_status = ''
            try:
                from attendance.models import FlexDayAdjustment
                _flex = FlexDayAdjustment._base_manager.filter(
                    employee=employee,
                    date=target_date,
                ).order_by('-created_at').first()
                if _flex:
                    _flex_delta = float(_flex.delta_hours or 0)
                    _flex_status = _flex.status or ''
            except Exception:
                pass

            obj, _ = cls._base_manager.update_or_create(
                employee=employee,
                date=target_date,
                defaults=dict(
                    company=company,
                    status=status,
                    effective_status=status,
                    late_minutes=late_min,
                    work_hours=work_h,
                    overtime_hours=ot_h,
                    is_night_shift=is_night,
                    is_weekend_work=is_weekend,
                    shift=day_shift,
                    policy=policy,
                    early_leave_minutes=_early_leave,
                    permission_hours_used=_perm_hours,
                    flex_delta_hours=_flex_delta,
                    flex_status=_flex_status,
                )
            )
            # FlexDayAdjustment: ظ…ط²ط§ظ…ظ†ط© ط£ظ…ط§ظ† ظ„ظ„ط´ظٹظپطھ ط§ظ„ظ…ط±ظ†
            try:
                from attendance.payroll_rules import _upsert_flex_adjustment
                _upsert_flex_adjustment(employee, att, day_shift, work_h)
            except Exception as _fx_err:
                import logging
                logging.getLogger(__name__).warning(f'FlexDayAdjustment sync error: {_fx_err}')

            return obj

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'DailyAttendanceSummary.compute_for_day error: {e}')
            return None


class FlexDayAdjustment(TenantModel):
    """
    طھط³ظˆظٹط© ظٹظˆظ…ظٹط© ظ„ظ„ط´ظٹظپطھ ط§ظ„ظ…ط±ظ† (flex_fixed / flex_split).
    ط¨طھطھظ†ط´ط£ طھظ„ظ‚ط§ط¦ظٹ ظˆظ‚طھ check-out ط£ظˆ compute_for_day.
    HR ظٹظˆط§ظپظ‚ ط£ظˆ ظٹط±ظپط¶ ظ‚ط¨ظ„ ظ…ط§ طھطھط­ط³ط¨ ظپظٹ ط§ظ„ظ…ط±طھط¨.
    """

    TYPE_CHOICES = [
        ('overtime', 'ط³ط§ط¹ط§طھ ط¥ط¶ط§ظپظٹط©'),
        ('shortage', 'ظ†ظ‚طµ ط³ط§ط¹ط§طھ'),
    ]

    STATUS_CHOICES = [
        ('pending',  'ظ‚ظٹط¯ ظ…ط±ط§ط¬ط¹ط© HR'),
        ('approved', 'ظ…ط¹طھظ…ط¯'),
        ('rejected', 'ظ…ط±ظپظˆط¶'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='flex_adjustments',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )

    attendance = models.ForeignKey(
        'Attendance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flex_adjustments',
        verbose_name='ط³ط¬ظ„ ط§ظ„ط­ط¶ظˆط±'
    )

    shift = models.ForeignKey(
        'Shift',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flex_adjustments',
        verbose_name='ط§ظ„ط´ظٹظپطھ'
    )

    date = models.DateField(verbose_name='ط§ظ„طھط§ط±ظٹط®')

    required_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…ط·ظ„ظˆط¨ط©'
    )

    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظپط¹ظ„ظٹط©'
    )

    delta_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='ط§ظ„ظپط±ظ‚ (ظ…ظˆط¬ط¨ = ط²ظٹط§ط¯ط©طŒ ط³ط§ظ„ط¨ = ظ†ظ‚طµ)'
    )

    adjustment_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name='ط§ظ„ظ†ظˆط¹'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='ط§ظ„ط­ط§ظ„ط©'
    )

    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flex_reviews',
        verbose_name='طھظ…طھ ط§ظ„ظ…ط±ط§ط¬ط¹ط© ط¨ظˆط§ط³ط·ط©'
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='طھط§ط±ظٹط® ط§ظ„ظ…ط±ط§ط¬ط¹ط©'
    )

    review_notes = models.TextField(
        blank=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ HR'
    )

    class Meta:
        verbose_name = 'طھط³ظˆظٹط© ط´ظٹظپطھ ظ…ط±ظ†'
        verbose_name_plural = 'طھط³ظˆظٹط§طھ ط§ظ„ط´ظٹظپطھ ط§ظ„ظ…ط±ظ†'
        ordering = ['-date']
        unique_together = [['employee', 'date', 'status']]

    def __str__(self):
        return (
            f"{self.employee} - {self.date} - "
            f"{self.adjustment_type} - {self.delta_hours}h - {self.status}"
        )


class AttendanceActionLog(TenantModel):
    """ط³ط¬ظ„ طھط¹ط¯ظٹظ„ط§طھ ط§ظ„ط­ط¶ظˆط± ظˆط§ظ„ط§ظ†طµط±ط§ظپ"""

    ACTION_CHOICES = [
        ("edit", "طھط¹ط¯ظٹظ„"),
        ("cancel_checkin", "ط¥ظ„ط؛ط§ط، ط­ط¶ظˆط±"),
        ("cancel_checkout", "ط¥ظ„ط؛ط§ط، ط§ظ†طµط±ط§ظپ"),
        ("delete", "ط­ط°ظپ ط³ط¬ظ„"),
    ]

    attendance = models.ForeignKey(
        "Attendance",
        on_delete=models.CASCADE,
        related_name="action_logs",
        verbose_name="ط³ط¬ظ„ ط§ظ„ط­ط¶ظˆط±"
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="ظ†ظˆط¹ ط§ظ„ط¥ط¬ط±ط§ط،"
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_actions",
        verbose_name="طھظ… ط¨ظˆط§ط³ط·ط©"
    )
    reason = models.TextField(
        verbose_name="ط³ط¨ط¨ ط§ظ„طھط¹ط¯ظٹظ„"
    )
    old_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="ط§ظ„ط¨ظٹط§ظ†ط§طھ ظ‚ط¨ظ„ ط§ظ„طھط¹ط¯ظٹظ„"
    )
    new_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="ط§ظ„ط¨ظٹط§ظ†ط§طھ ط¨ط¹ط¯ ط§ظ„طھط¹ط¯ظٹظ„"
    )
    action_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="طھط§ط±ظٹط® ط§ظ„ط¥ط¬ط±ط§ط،"
    )

    class Meta:
        verbose_name = "ط³ط¬ظ„ طھط¹ط¯ظٹظ„ ط­ط¶ظˆط±"
        verbose_name_plural = "ط³ط¬ظ„ط§طھ طھط¹ط¯ظٹظ„ط§طھ ط§ظ„ط­ط¶ظˆط±"
        ordering = ["-action_at"]

    def __str__(self):
        return f"{self.attendance} - {self.get_action_type_display()}"


# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# ظ†ط¸ط§ظ… ط§ظ„طھط£ط®ظٹط±ط§طھ ظˆط§ظ„ط¥ط¬ط±ط§ط،ط§طھ ط§ظ„طھط£ط¯ظٹط¨ظٹط©
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ

class LateIncident(TenantModel):
    """ط­ط§ط¯ط«ط© طھط£ط®ظٹط±"""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="late_incidents",
        verbose_name="ط§ظ„ظ…ظˆط¸ظپ"
    )
    attendance = models.ForeignKey(
        "Attendance",
        on_delete=models.CASCADE,
        related_name="late_incidents",
        verbose_name="ط³ط¬ظ„ ط§ظ„ط­ط¶ظˆط±",
        null=True,
        blank=True
    )
    date = models.DateField(verbose_name="ط§ظ„طھط§ط±ظٹط®")
    late_minutes = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ط¯ظ‚ط§ط¦ظ‚ ط§ظ„طھط£ط®ظٹط±"
    )
    shift_start_time = models.TimeField(
        null=True, blank=True,
        verbose_name="ط¨ط¯ط§ظٹط© ط§ظ„ط´ظٹظپطھ"
    )
    actual_checkin_time = models.TimeField(
        null=True, blank=True,
        verbose_name="ظˆظ‚طھ ط§ظ„ط­ط¶ظˆط± ط§ظ„ظپط¹ظ„ظٹ"
    )
    grace_period_used = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ط§ظ„ط³ظ…ط§ط­ظٹط© ط§ظ„ظ…ط³طھط®ط¯ظ…ط©"
    )
    month = models.PositiveSmallIntegerField(verbose_name="ط§ظ„ط´ظ‡ط±")
    year = models.PositiveSmallIntegerField(verbose_name="ط§ظ„ط³ظ†ط©")
    incident_number_in_month = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="ط±ظ‚ظ… ط§ظ„ط­ط§ط¯ط«ط© ظپظٹ ط§ظ„ط´ظ‡ط±"
    )
    is_excused = models.BooleanField(
        default=False,
        verbose_name="ظ…ط¹ط°ظˆط±"
    )
    excuse_reason = models.TextField(
        blank=True,
        verbose_name="ط³ط¨ط¨ ط§ظ„ط¹ط°ط±"
    )
    was_deducted = models.BooleanField(
        default=False,
        verbose_name="طھظ… ط§ظ„ط®طµظ…"
    )
    deduction_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="ظ‚ظٹظ…ط© ط§ظ„ط®طµظ… (ط¬ط²ط، ظ…ظ† ط§ظ„ظٹظˆظ…)"
    )

    class Meta:
        verbose_name = "ط­ط§ط¯ط«ط© طھط£ط®ظٹط±"
        verbose_name_plural = "ط­ظˆط§ط¯ط« ط§ظ„طھط£ط®ظٹط±"
        ordering = ["-date"]
        unique_together = [["employee", "date"]]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.late_minutes} ط¯ظ‚ظٹظ‚ط©"


class LateNotification(TenantModel):
    """ط¥ط´ط¹ط§ط± طھط£ط®ظٹط± ظ„ظ€ HR"""

    NOTIFICATION_TYPES = [
        ("single_late", "طھط£ط®ظٹط± ط¹ط§ط¯ظٹ"),
        ("threshold_reached", "ظˆطµظ„ ط§ظ„ط­ط¯"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="late_notifications",
        verbose_name="ط§ظ„ظ…ظˆط¸ظپ"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="single_late",
        verbose_name="ظ†ظˆط¹ ط§ظ„ط¥ط´ط¹ط§ط±"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="ط§ظ„ط¹ظ†ظˆط§ظ†"
    )
    message = models.TextField(
        verbose_name="ط§ظ„ط±ط³ط§ظ„ط©"
    )
    details = models.TextField(
        blank=True,
        verbose_name="ط§ظ„طھظپط§طµظٹظ„"
    )
    suggested_action = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ط§ظ„ط¥ط¬ط±ط§ط، ط§ظ„ظ…ظ‚طھط±ط­"
    )
    incident_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="ط¹ط¯ط¯ ظ…ط±ط§طھ ط§ظ„طھط£ط®ظٹط±"
    )
    month = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="ط§ظ„ط´ظ‡ط±"
    )
    year = models.PositiveSmallIntegerField(
        default=2025,
        verbose_name="ط§ظ„ط³ظ†ط©"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="طھظ… ط§ظ„ظ‚ط±ط§ط،ط©"
    )
    is_acted_upon = models.BooleanField(
        default=False,
        verbose_name="طھظ… ط§طھط®ط§ط° ط¥ط¬ط±ط§ط،"
    )
    action_taken = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ط§ظ„ط¥ط¬ط±ط§ط، ط§ظ„ظ…طھط®ط°"
    )
    action_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="late_actions_taken",
        verbose_name="طھظ… ط¨ظˆط§ط³ط·ط©"
    )
    action_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="ظˆظ‚طھ ط§ظ„ط¥ط¬ط±ط§ط،"
    )
    action_notes = models.TextField(
        blank=True,
        verbose_name="ظ…ظ„ط§ط­ط¸ط§طھ ط§ظ„ط¥ط¬ط±ط§ط،"
    )

    class Meta:
        verbose_name = "ط¥ط´ط¹ط§ط± طھط£ط®ظٹط±"
        verbose_name_plural = "ط¥ط´ط¹ط§ط±ط§طھ ط§ظ„طھط£ط®ظٹط±"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"


class DisciplinaryRule(models.Model):
    """ظ‚ظˆط§ط¹ط¯ ط§ظ„ط¬ط²ط§ط،ط§طھ ط§ظ„طھط£ط¯ظٹط¨ظٹط© ظپظٹ ط§ظ„ط³ظٹط§ط³ط©"""

    VIOLATION_TYPE_CHOICES = [
        ("late_repeat", "طھظƒط±ط§ط± ط§ظ„طھط£ط®ظٹط±"),
        ("absence_repeat", "طھظƒط±ط§ط± ط§ظ„ط؛ظٹط§ط¨"),
        ("early_leave_repeat", "طھظƒط±ط§ط± ط§ظ„ط§ظ†طµط±ط§ظپ ط§ظ„ظ…ط¨ظƒط±"),
        ("policy_violation", "ظ…ط®ط§ظ„ظپط© ظ„ط§ط¦ط­ط©"),
        ("misconduct", "ط³ظˆط، ط³ظ„ظˆظƒ"),
        ("negligence", "ط¥ظ‡ظ…ط§ظ„"),
        ("other", "ط£ط®ط±ظ‰"),
    ]

    PENALTY_TYPE_CHOICES = [
        ("verbal_warning", "ط¥ظ†ط°ط§ط± ط´ظپظ‡ظٹ"),
        ("written_warning", "ط¥ظ†ط°ط§ط± ظƒطھط§ط¨ظٹ"),
        ("deduction_days", "ط®طµظ… ط£ظٹط§ظ…"),
        ("deduction_amount", "ط®طµظ… ظ…ط¨ظ„ط؛"),
        ("suspension", "ط¥ظٹظ‚ط§ظپ ط¹ظ† ط§ظ„ط¹ظ…ظ„"),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name="disciplinary_rules",
        verbose_name="ط§ظ„ط³ظٹط§ط³ط©"
    )
    violation_type = models.CharField(
        max_length=30, choices=VIOLATION_TYPE_CHOICES,
        default="policy_violation", verbose_name="ظ†ظˆط¹ ط§ظ„ظ…ط®ط§ظ„ظپط©"
    )
    occurrence_from = models.IntegerField(
        default=1, verbose_name="ظ…ظ† ط§ظ„ظ…ط±ط©"
    )
    occurrence_to = models.IntegerField(
        default=1, verbose_name="ط¥ظ„ظ‰ ط§ظ„ظ…ط±ط©"
    )
    penalty_type = models.CharField(
        max_length=30, choices=PENALTY_TYPE_CHOICES,
        default="verbal_warning", verbose_name="ظ†ظˆط¹ ط§ظ„ط¬ط²ط§ط،"
    )
    deduction_days = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="ط£ظٹط§ظ… ط§ظ„ط®طµظ…",
        help_text="0.25=ط±ط¨ط¹ ظٹظˆظ… / 0.5=ظ†طµ ظٹظˆظ… / 1=ظٹظˆظ… ظƒط§ظ…ظ„"
    )
    deduction_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="ظ…ط¨ظ„ط؛ ط§ظ„ط®طµظ… ط§ظ„ط«ط§ط¨طھ"
    )
    description = models.TextField(
        blank=True, verbose_name="ظˆطµظپ ط§ظ„ظ‚ط§ط¹ط¯ط©"
    )
    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "ظ‚ط§ط¹ط¯ط© ط¬ط²ط§ط، طھط£ط¯ظٹط¨ظٹ"
        verbose_name_plural = "ظ‚ظˆط§ط¹ط¯ ط§ظ„ط¬ط²ط§ط،ط§طھ ط§ظ„طھط£ط¯ظٹط¨ظٹط©"
        ordering = ["violation_type", "occurrence_from"]

    def __str__(self):
        return f"{self.get_violation_type_display()} ({self.occurrence_from}-{self.occurrence_to}): {self.get_penalty_type_display()}"


class DisciplinaryAction(TenantModel):
    """ط¥ط¬ط±ط§ط، طھط£ط¯ظٹط¨ظٹ"""

    ACTION_TYPES = [
        ("verbal_warning", "ط¥ظ†ط°ط§ط± ط´ظپظ‡ظٹ"),
        ("written_warning", "ط¥ظ†ط°ط§ط± ظƒطھط§ط¨ظٹ"),
        ("quarter_day_deduction", "ط®طµظ… ط±ط¨ط¹ ظٹظˆظ…"),
        ("half_day_deduction", "ط®طµظ… ظ†طµظپ ظٹظˆظ…"),
        ("full_day_deduction", "ط®طµظ… ظٹظˆظ… ظƒط§ظ…ظ„"),
        ("suspension", "ط¥ظٹظ‚ط§ظپ ط¹ظ† ط§ظ„ط¹ظ…ظ„"),
        ("termination_warning", "ط¥ظ†ط°ط§ط± ظپطµظ„"),
        ("dismissed", "طھظ… ط§ظ„ط¥ط¹ظپط§ط، / ط§ظ„طھط¬ط§ظ‡ظ„"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="disciplinary_actions",
        verbose_name="ط§ظ„ظ…ظˆط¸ظپ"
    )
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES,
        verbose_name="ظ†ظˆط¹ ط§ظ„ط¥ط¬ط±ط§ط،"
    )
    reason = models.TextField(
        verbose_name="ط§ظ„ط³ط¨ط¨"
    )
    related_notification = models.ForeignKey(
        LateNotification,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="disciplinary_actions",
        verbose_name="ط§ظ„ط¥ط´ط¹ط§ط± ط§ظ„ظ…ط±طھط¨ط·"
    )
    auto_generated = models.BooleanField(
        default=False,
        verbose_name="طھظ… طھظ„ظ‚ط§ط¦ظٹظ‹ط§"
    )
    deduction_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name="ظ…ط¨ظ„ط؛ ط§ظ„ط®طµظ…"
    )
    deduction_created = models.BooleanField(
        default=False,
        verbose_name="طھظ… ط¥ظ†ط´ط§ط، ط®طµظ… ظپط¹ظ„ظٹ"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "ظ…ط¹ظ„ظ‚"),
            ("approved", "ظ…ط¹طھظ…ط¯"),
            ("rejected", "ظ…ط±ظپظˆط¶"),
            ("cancelled", "ظ…ظ„ط؛ظٹ"),
        ],
        default="pending",
        verbose_name="ط§ظ„ط­ط§ظ„ط©"
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_disciplinary_actions",
        verbose_name="ظˆط§ظپظ‚ ط¨ظˆط§ط³ط·ط©"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="طھط§ط±ظٹط® ط§ظ„ط§ط¹طھظ…ط§ط¯"
    )
    payroll_month = models.CharField(
        max_length=7, blank=True,
        verbose_name="ط´ظ‡ط± ط§ظ„ظ…ط±طھط¨",
        help_text="YYYY-MM"
    )
    payroll_applied = models.BooleanField(
        default=False,
        verbose_name="طھظ… طھط·ط¨ظٹظ‚ظ‡ ط¹ظ„ظ‰ ط§ظ„ظ…ط±طھط¨"
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="disciplinary_actions_performed",
        verbose_name="طھظ… ط¨ظˆط§ط³ط·ط©"
    )
    performed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="طھط§ط±ظٹط® ط§ظ„ط¥ط¬ط±ط§ط،"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ظ…ظ„ط§ط­ط¸ط§طھ"
    )

    class Meta:
        verbose_name = "ط¥ط¬ط±ط§ط، طھط£ط¯ظٹط¨ظٹ"
        verbose_name_plural = "ط§ظ„ط¥ط¬ط±ط§ط،ط§طھ ط§ظ„طھط£ط¯ظٹط¨ظٹط©"
        ordering = ["-performed_at"]

    def __str__(self):
        return f"{self.employee} - {self.get_action_type_display()}"


# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# طھظƒظ„ظٹظپ ظٹظˆظ…ظٹ / ط¬ط¯ظˆظ„ ط§ظ„ط¹ظ…ظ„ ط§ظ„ظٹظˆظ…ظٹ
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
class DailyAssignment(TenantModel):
    """
    طھظƒظ„ظٹظپ ظٹظˆظ…ظٹ ظ„ظƒظ„ ظ…ظˆط¸ظپ
    ط¯ظ‡ ط§ظ„ظ„ظٹ ط¨ظٹط­ط¯ط¯ ظ†ظˆط¹ ظٹظˆظ… ط§ظ„ط¹ظ…ظ„ ظˆط·ط±ظٹظ‚ط© طھظ†ظپظٹط°ظ‡
    """

    # â”€â”€ ظ†ظˆط¹ ط§ظ„ظٹظˆظ… â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    DAY_TYPES = [
        ("work_day", "ظٹظˆظ… ط¹ظ…ظ„"),
        ("off_day", "ط±ط§ط­ط© ط£ط³ط¨ظˆط¹ظٹط©"),
        ("leave_day", "ط¥ط¬ط§ط²ط©"),
        ("holiday", "ط¥ط¬ط§ط²ط© ط±ط³ظ…ظٹط©"),
        ("mission_day", "ظ…ط£ظ…ظˆط±ظٹط© / ظ…ظ‡ظ…ط©"),
        ("standby_day", "ط§ط³طھط¯ط¹ط§ط، / on-call"),
        ("training_day", "ظٹظˆظ… طھط¯ط±ظٹط¨"),
    ]

    # â”€â”€ ط·ط±ظٹظ‚ط© ط§ظ„طھظ†ظپظٹط° â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    WORK_MODES = [
        ("fixed", "ط«ط§ط¨طھ"),
        ("flexible", "ظ…ط±ظ†"),
        ("split", "ظ…طھظ‚ط³ظ…"),
        ("field", "ظ…ظٹط¯ط§ظ†ظٹ"),
        ("remote", "ط¹ظ† ط¨ظڈط¹ط¯"),
        ("mixed", "ظ…ط®طھظ„ط·"),
    ]

    # â”€â”€ ط­ط§ظ„ط© ط§ظ„طھظƒظ„ظٹظپ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    STATUS_CHOICES = [
        ("scheduled", "ظ…ط¬ط¯ظˆظ„"),
        ("in_progress", "ط¬ط§ط±ظٹ"),
        ("completed", "ظ…ظƒطھظ…ظ„"),
        ("cancelled", "ظ…ظ„ط؛ظٹ"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="daily_assignments",
        verbose_name="ط§ظ„ظ…ظˆط¸ظپ"
    )
    date = models.DateField(
        verbose_name="ط§ظ„طھط§ط±ظٹط®"
    )

    # â”€â”€ ظ†ظˆط¹ ط§ظ„ظٹظˆظ… ظˆط·ط±ظٹظ‚ط© ط§ظ„ط¹ظ…ظ„ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    day_type = models.CharField(
        max_length=20,
        choices=DAY_TYPES,
        default="work_day",
        verbose_name="ظ†ظˆط¹ ط§ظ„ظٹظˆظ…"
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODES,
        default="fixed",
        verbose_name="ط·ط±ظٹظ‚ط© ط§ظ„طھظ†ظپظٹط°"
    )

    # â”€â”€ ط£ظˆظ‚ط§طھ ط§ظ„ط¹ظ…ظ„ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    shift = models.ForeignKey(
        "Shift",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ط§ظ„ط´ظٹظپطھ"
    )
    start_time = models.TimeField(
        null=True, blank=True,
        verbose_name="ط¨ط¯ط§ظٹط© ط§ظ„ط¹ظ…ظ„"
    )
    end_time = models.TimeField(
        null=True, blank=True,
        verbose_name="ظ†ظ‡ط§ظٹط© ط§ظ„ط¹ظ…ظ„"
    )
    expected_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True, blank=True,
        verbose_name="ط§ظ„ط³ط§ط¹ط§طھ ط§ظ„ظ…طھظˆظ‚ط¹ط©"
    )

    # â”€â”€ Split Shift (ط¬ط²ط¦ظٹظ†) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    segment_2_start = models.TimeField(
        null=True, blank=True,
        verbose_name="ط¨ط¯ط§ظٹط© ط§ظ„ط¬ط²ط، ط§ظ„ط«ط§ظ†ظٹ"
    )
    segment_2_end = models.TimeField(
        null=True, blank=True,
        verbose_name="ظ†ظ‡ط§ظٹط© ط§ظ„ط¬ط²ط، ط§ظ„ط«ط§ظ†ظٹ"
    )

    # â”€â”€ Flags â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    is_replacement = models.BooleanField(
        default=False,
        verbose_name="ط¨ط¯ظٹظ„ ظ„ط²ظ…ظٹظ„"
    )
    replaces_employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="replaced_assignments",
        verbose_name="ط¨ط¯ظٹظ„ ط¹ظ†"
    )
    is_extra_shift = models.BooleanField(
        default=False,
        verbose_name="ط´ظٹظپطھ ط¥ط¶ط§ظپظٹ"
    )
    count_as_overtime = models.BooleanField(
        default=False,
        verbose_name="ظٹط­ط³ط¨ ط£ظˆظپط± طھط§ظٹظ…"
    )
    count_as_compensatory = models.BooleanField(
        default=False,
        verbose_name="ظٹظˆظ… طھط¹ظˆظٹط¶ظٹ"
    )

    # â”€â”€ ظ…طھط·ظ„ط¨ط§طھ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    requires_tracking = models.BooleanField(
        default=False,
        verbose_name="ظٹط­طھط§ط¬ طھطھط¨ط¹ GPS"
    )
    requires_visits = models.BooleanField(
        default=False,
        verbose_name="ظٹط­طھط§ط¬ طھط³ط¬ظٹظ„ ط²ظٹط§ط±ط§طھ"
    )
    requires_geofence = models.BooleanField(
        default=True,
        verbose_name="ظٹط­طھط§ط¬ ظ†ط·ط§ظ‚ ط§ظ„ظپط±ط¹"
    )
    requires_manager_approval = models.BooleanField(
        default=False,
        verbose_name="ظٹط­طھط§ط¬ ظ…ظˆط§ظپظ‚ط© ط§ظ„ظ…ط¯ظٹط± ظ…ط³ط¨ظ‚ط§ظ‹"
    )

    # â”€â”€ ط§ظ„ظ…ظ‡ظ…ط© â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    task_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ط¹ظ†ظˆط§ظ† ط§ظ„ظ…ظ‡ظ…ط©"
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ط§ط³ظ… ط§ظ„ظ…ظˆظ‚ط¹"
    )

    # â”€â”€ ط§ظ„ط­ط§ظ„ط© ظˆط§ظ„ط§ط¹طھظ…ط§ط¯ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name="ط§ظ„ط­ط§ظ„ط©"
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_assignments",
        verbose_name="ط§ط¹طھظ…ط¯ ط¨ظˆط§ط³ط·ط©"
    )

    # â”€â”€ Exception â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    is_exception = models.BooleanField(
        default=False,
        verbose_name="ط­ط§ظ„ط© ط§ط³طھط«ظ†ط§ط¦ظٹط©"
    )
    exception_reason = models.TextField(
        blank=True,
        verbose_name="ط³ط¨ط¨ ط§ظ„ط§ط³طھط«ظ†ط§ط،"
    )
    exception_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("pending_review", "ظ‚ظٹط¯ ط§ظ„ظ…ط±ط§ط¬ط¹ط©"),
            ("approved", "ظ…ط¹طھظ…ط¯"),
            ("rejected", "ظ…ط±ظپظˆط¶"),
        ],
        verbose_name="ط­ط§ظ„ط© ط§ظ„ط§ط³طھط«ظ†ط§ط،"
    )

    # â”€â”€ Auto Generated â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    is_auto_generated = models.BooleanField(
        default=False,
        verbose_name="طھظ… طھظˆظ„ظٹط¯ظ‡ طھظ„ظ‚ط§ط¦ظٹط§ظ‹"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ظ…ظ„ط§ط­ط¸ط§طھ"
    )

    class Meta:
        verbose_name = "طھظƒظ„ظٹظپ ظٹظˆظ…ظٹ"
        verbose_name_plural = "ط§ظ„طھظƒظ„ظٹظپط§طھ ط§ظ„ظٹظˆظ…ظٹط©"
        ordering = ["-date"]
        unique_together = [["employee", "date"]]

    def __str__(self):
        return (
            f"{self.employee} - {self.date} - "
            f"{self.get_day_type_display()} / {self.get_work_mode_display()}"
        )

    @property
    def is_working_day(self):
        return self.day_type in ["work_day", "mission_day", "training_day", "standby_day"]

    @property
    def is_off(self):
        return self.day_type in ["off_day", "leave_day", "holiday"]

    @property
    def apply_late_policy(self):
        if self.day_type != "work_day":
            return False
        return self.work_mode in ["fixed", "split"]

    @property
    def apply_geofence(self):
        if not self.requires_geofence:
            return False
        return self.work_mode in ["fixed", "split", "mixed"]


class TrackingAlert(TenantModel):
    """طھظ†ط¨ظٹظ‡ طھطھط¨ط¹ طµط§ظ…طھ ط¹ظ†ط¯ ط§ظ„ط®ط±ظˆط¬ ظ…ظ† ط§ظ„ظ†ط·ط§ظ‚ ط£ط«ظ†ط§ط، ط§ظ„ط¹ظ…ظ„"""

    STATUS_CHOICES = [
        ("open", "ظ…ظپطھظˆط­"),
        ("resolved", "طھظ…طھ ط§ظ„ظ…ط¹ط§ظ„ط¬ط©"),
        ("ignored", "طھظ… ط§ظ„طھط¬ط§ظ‡ظ„"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="tracking_alerts",
        verbose_name="ط§ظ„ظ…ظˆط¸ظپ"
    )
    date = models.DateField(
        verbose_name="ط§ظ„طھط§ط±ظٹط®"
    )
    started_at = models.DateTimeField(
        verbose_name="ظˆظ‚طھ ط¨ط¯ط§ظٹط© ط§ظ„ط®ط±ظˆط¬ ظ…ظ† ط§ظ„ظ†ط·ط§ظ‚"
    )
    last_seen_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="ط¢ط®ط± ظˆظ‚طھ ط±طµط¯"
    )
    minutes_outside = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ط¹ط¯ط¯ ط§ظ„ط¯ظ‚ط§ط¦ظ‚ ط®ط§ط±ط¬ ط§ظ„ظ†ط·ط§ظ‚"
    )

    last_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="ط¢ط®ط± ط®ط· ط¹ط±ط¶"
    )
    last_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="ط¢ط®ط± ط®ط· ط·ظˆظ„"
    )
    last_address = models.TextField(
        blank=True,
        verbose_name="ط¢ط®ط± ط¹ظ†ظˆط§ظ†"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        verbose_name="ط§ظ„ط­ط§ظ„ط©"
    )

    notified_manager = models.BooleanField(
        default=False,
        verbose_name="طھظ… طھظ†ط¨ظٹظ‡ ط§ظ„ظ…ط¯ظٹط±"
    )
    notified_hr = models.BooleanField(
        default=False,
        verbose_name="طھظ… طھظ†ط¨ظٹظ‡ HR"
    )
    notified_company_admin = models.BooleanField(
        default=False,
        verbose_name="طھظ… طھظ†ط¨ظٹظ‡ طµط§ط­ط¨ ط§ظ„ط´ط±ظƒط©"
    )

    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="resolved_tracking_alerts",
        verbose_name="طھظ…طھ ط§ظ„ظ…ط¹ط§ظ„ط¬ط© ط¨ظˆط§ط³ط·ط©"
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="ظˆظ‚طھ ط§ظ„ظ…ط¹ط§ظ„ط¬ط©"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ظ…ظ„ط§ط­ط¸ط§طھ"
    )

    class Meta:
        verbose_name = "طھظ†ط¨ظٹظ‡ طھطھط¨ط¹"
        verbose_name_plural = "طھظ†ط¨ظٹظ‡ط§طھ ط§ظ„طھطھط¨ط¹"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.minutes_outside} ط¯ظ‚ظٹظ‚ط©"

class LocationHistory(TenantModel):
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_history',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7, verbose_name='ط®ط· ط§ظ„ط¹ط±ط¶')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, verbose_name='ط®ط· ط§ظ„ط·ظˆظ„')
    accuracy = models.FloatField(null=True, blank=True, verbose_name='ط§ظ„ط¯ظ‚ط©')
    recorded_at = models.DateTimeField(verbose_name='ظˆظ‚طھ ط§ظ„طھط³ط¬ظٹظ„')
    shift_date = models.DateField(verbose_name='طھط§ط±ظٹط® ط§ظ„ط´ظٹظپطھ')
    point_index = models.IntegerField(default=0, verbose_name='ط±ظ‚ظ… ط§ظ„ظ†ظ‚ط·ط©')
    address = models.CharField(max_length=500, blank=True, verbose_name='ط§ظ„ط¹ظ†ظˆط§ظ†')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['shift_date', 'recorded_at']
        verbose_name = 'ط³ط¬ظ„ ظ…ظˆظ‚ط¹'
        verbose_name_plural = 'ط³ط¬ظ„ط§طھ ط§ظ„ظ…ظˆط§ظ‚ط¹'

    def __str__(self):
        return f"{self.employee} - {self.shift_date} - ظ†ظ‚ط·ط© {self.point_index}"


# Import Missions Models
from .missions_models import *

# Phase 14 - Company Work Policy
from .company_policy_models import CompanyWorkPolicy
from .payroll_settings_model import PayrollSettings

from .payroll_pro_models import PayrollRun, PayrollLine, PayrollBonus, PayrollPenalty, PayrollInstallment


class PermissionLedger(TenantModel):
    """
    ط³ط¬ظ„ ط­ط±ظƒط© ط§ظ„ط£ط°ظˆظ†ط§طھ ظ„ظ„ظ…ظˆط¸ظپ
    """
    ENTRY_TYPE_CHOICES = [
        ('manual_request', 'Manual Permission Request'),
        ('auto_late', 'Auto Deduction From Late'),
        ('manual_grant', 'Manual Grant Extra'),
        ('rollback', 'Rollback / Cancel Late'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='permission_ledger'
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    minutes_used = models.IntegerField(default=0)
    count_used = models.IntegerField(default=0)
    reference_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.entry_type} - {self.minutes_used} min"


# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# EmployeeWorkLocation - ظ…ظˆط§ظ‚ط¹ ط§ظ„ط¹ظ…ظ„ ط§ظ„ظ…طھط¹ط¯ط¯ط© ظ„ظ„ظ…ظˆط¸ظپظٹظ†
# ظ„ظ„ظ…ظ‡ظ†ط¯ط³ظٹظ† ظˆط§ظ„ظ…ظ†ط¯ظˆط¨ظٹظ† ط§ظ„ظ„ظٹ ط¨ظٹط´طھط؛ظ„ظˆط§ ظ…ظ† ظ…ظˆط§ظ‚ط¹ ظ…طھط¹ط¯ط¯ط©
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
class EmployeeWorkLocation(TenantModel):
    """
    ظ…ظˆط§ظ‚ط¹ ط§ظ„ط¹ظ…ظ„ ط§ظ„ظ…ط¹طھظ…ط¯ط© ظ„ظ„ظ…ظˆط¸ظپظٹظ† (Multi-Site System)
    ط§ظ„ظ…ظˆط¸ظپ ظٹظ‚طھط±ط­ ظ…ظˆظ‚ط¹ â†’ ط§ظ„ظ…ط¯ظٹط±/HR ظٹظˆط§ظپظ‚ â†’ ط§ظ„ظ…ظˆط¸ظپ ظٹظ‚ط¯ط± ظٹط¨طµظ… ظ…ظ†ظ‡
    """
    
    # ط§ظ„ظ…ظˆط¸ظپظٹظ† ط§ظ„ظ…ط®طµطµ ظ„ظ‡ظ… ط§ظ„ظ…ظˆظ‚ط¹ (Many-to-Many)
    assigned_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='assigned_work_locations',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپظٹظ† ط§ظ„ظ…ط®طµطµظٹظ†'
    )

    LOCATION_TYPE_CHOICES = [
        ('project', 'ظ…ظˆظ‚ط¹ ظ…ط´ط±ظˆط¹'),
        ('client', 'ظ…ظˆظ‚ط¹ ط¹ظ…ظٹظ„'),
        ('warehouse', 'ظ…ط®ط²ظ†'),
        ('office', 'ظ…ظƒطھط¨ ظپط±ط¹ظٹ'),
        ('factory', 'ظ…طµظ†ط¹'),
        ('site', 'ظ…ظˆظ‚ط¹ ط¨ظ†ط§ط،'),
        ('remote', 'ط¹ظ…ظ„ ط¹ظ† ط¨ط¹ط¯'),
        ('other', 'ط£ط®ط±ظ‰'),
    ]
    
    STATUS_CHOICES = [
        ('pending_manager', 'ظ‚ظٹط¯ ظ…ظˆط§ظپظ‚ط© ط§ظ„ظ…ط¯ظٹط±'),
        ('pending_hr',      'ظ‚ظٹط¯ ط§ط¹طھظ…ط§ط¯ HR'),
        ('approved',        'ظ…ط¹طھظ…ط¯'),
        ('rejected',        'ظ…ط±ظپظˆط¶'),
        ('expired',         'ظ…ظ†طھظ‡ظٹ'),
        ('suspended',       'ظ…ظˆظ‚ظپ ظ…ط¤ظ‚طھط§ظ‹'),
    ]
    
    # â•گâ•گâ•گ ظ…ط¹ظ„ظˆظ…ط§طھ ط£ط³ط§ط³ظٹط© â•گâ•گâ•گ
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='work_locations',
        null=True, blank=True,
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ',
        help_text='ظپط§ط±ط؛ ظ„ظˆ ط§ظ„ظ…ظˆظ‚ط¹ ظ…ط´طھط±ظƒ ط¨ظٹظ† ظ…ظˆط¸ظپظٹظ†'
    )
    name = models.CharField(max_length=200, verbose_name='ط§ط³ظ… ط§ظ„ظ…ظˆظ‚ط¹')
    description = models.TextField(blank=True, null=True, verbose_name='ط§ظ„ظˆطµظپ')
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        default='project',
        verbose_name='ظ†ظˆط¹ ط§ظ„ظ…ظˆظ‚ط¹'
    )
    
    # â•گâ•گâ•گ ط§ظ„ط¥ط­ط¯ط§ط«ظٹط§طھ â•گâ•گâ•گ
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        verbose_name='ط®ط· ط§ظ„ط¹ط±ط¶'
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        verbose_name='ط®ط· ط§ظ„ط·ظˆظ„'
    )
    radius = models.PositiveIntegerField(
        default=500,
        verbose_name='ظ†طµظپ ظ‚ط·ط± ط§ظ„ط³ظ…ط§ط­ (ظ…طھط±)',
        help_text='ط§ظ„ظ…ط³ط§ظپط© ط§ظ„ظ…ط³ظ…ظˆط­ط© ط­ظˆظ„ ط§ظ„ظ…ظˆظ‚ط¹ ظ„ظ„ط¨طµظ…ط©'
    )
    address = models.TextField(blank=True, null=True, verbose_name='ط§ظ„ط¹ظ†ظˆط§ظ†')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='ط§ظ„ظ…ط¯ظٹظ†ط©')
    country = models.CharField(max_length=10, default='EG', verbose_name='ط§ظ„ط¯ظˆظ„ط©')
    
    # â•گâ•گâ•گ ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ظ…ط´ط±ظˆط¹/ط§ظ„ط¹ظ…ظٹظ„ â•گâ•گâ•گ
    project_code = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name='ظƒظˆط¯ ط§ظ„ظ…ط´ط±ظˆط¹'
    )
    client_name = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name='ط§ط³ظ… ط§ظ„ط¹ظ…ظٹظ„'
    )
    contact_person = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name='ط§ظ„ط´ط®طµ ط§ظ„ظ…ط³ط¦ظˆظ„'
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name='ط±ظ‚ظ… ط§ظ„طھظˆط§طµظ„'
    )
    
    # â•گâ•گâ•گ ط§ظ„طµظ„ط§ط­ظٹط§طھ ظˆط§ظ„ظ…ط´ط§ط±ظƒط© â•گâ•گâ•گ
    is_shared = models.BooleanField(
        default=False,
        verbose_name='ظ…ظˆظ‚ط¹ ظ…ط´طھط±ظƒ',
        help_text='ظ…طھط§ط­ ظ„ظƒظ„ ظ…ظˆط¸ظپظٹظ† ط§ظ„ط´ط±ظƒط©/ط§ظ„ظپط±ط¹/ط§ظ„ظ‚ط³ظ…'
    )
    shared_with_branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shared_work_locations',
        verbose_name='ظ…ط´طھط±ظƒ ظ…ط¹ ظپط±ط¹'
    )
    shared_with_department = models.ForeignKey(
        'companies.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shared_work_locations',
        verbose_name='ظ…ط´طھط±ظƒ ظ…ط¹ ظ‚ط³ظ…'
    )
    requires_checkin_photo = models.BooleanField(
        default=False,
        verbose_name='ظٹط·ظ„ط¨ طµظˆط±ط© ط¹ظ†ط¯ ط§ظ„ط­ط¶ظˆط±'
    )
    allow_checkout_only = models.BooleanField(
        default=False,
        verbose_name='ظ…ط³ظ…ظˆط­ ط§ظ„ط§ظ†طµط±ط§ظپ ظپظ‚ط·'
    )
    
    # â•گâ•گâ•گ ط§ظ„ط¬ط¯ظˆظ„ط© ط§ظ„ط²ظ…ظ†ظٹط© â•گâ•گâ•گ
    valid_from = models.DateField(
        null=True, blank=True,
        verbose_name='طµط§ظ„ط­ ظ…ظ† طھط§ط±ظٹط®'
    )
    valid_until = models.DateField(
        null=True, blank=True,
        verbose_name='طµط§ظ„ط­ ط­طھظ‰ طھط§ط±ظٹط®',
        help_text='ظ„ظ„ظ…ط´ط§ط±ظٹط¹ ط§ظ„ظ…ط¤ظ‚طھط©'
    )
    working_days = models.JSONField(
        default=dict, blank=True,
        verbose_name='ط£ظٹط§ظ… ط§ظ„ط¹ظ…ظ„',
        help_text='ظ…ط«ط§ظ„: {"sun": true, "mon": true, ...}'
    )
    working_hours_start = models.TimeField(
        null=True, blank=True,
        verbose_name='ط¨ط¯ط§ظٹط© ط§ظ„ط¹ظ…ظ„'
    )
    working_hours_end = models.TimeField(
        null=True, blank=True,
        verbose_name='ظ†ظ‡ط§ظٹط© ط§ظ„ط¹ظ…ظ„'
    )
    
    # â•گâ•گâ•گ ط§ظ„ظ…ظˆط§ظپظ‚ط§طھ (Workflow) â•گâ•گâ•گ
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_manager',
        verbose_name='ط§ظ„ط­ط§ظ„ط©'
    )
    proposed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='proposed_work_locations',
        verbose_name='ظ…ظ‚طھط±ط­ ط¨ظˆط§ط³ط·ط©'
    )
    proposed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='طھط§ط±ظٹط® ط§ظ„ط§ظ‚طھط±ط§ط­'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_work_locations',
        verbose_name='ظ…ط¹طھظ…ط¯ ط¨ظˆط§ط³ط·ط©'
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='طھط§ط±ظٹط® ط§ظ„ط§ط¹طھظ…ط§ط¯'
    )
    rejection_reason = models.TextField(
        blank=True, null=True,
        verbose_name='ط³ط¨ط¨ ط§ظ„ط±ظپط¶'
    )
    approval_notes = models.TextField(
        blank=True, null=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ ط§ظ„ط§ط¹طھظ…ط§ط¯'
    )
    
    # â•گâ•گâ•گ ط§ظ„ط¥ط­طµط§ط¦ظٹط§طھ â•گâ•گâ•گ
    total_visits_count = models.PositiveIntegerField(
        default=0,
        verbose_name='ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ط²ظٹط§ط±ط§طھ'
    )
    last_visited_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='ط¢ط®ط± ط²ظٹط§ط±ط©'
    )
    average_visit_duration = models.PositiveIntegerField(
        default=0,
        verbose_name='ظ…طھظˆط³ط· ظ…ط¯ط© ط§ظ„ط²ظٹط§ط±ط© (ط¯ظ‚ط§ط¦ظ‚)'
    )
    
    # â•گâ•گâ•گ ط­ط§ظ„ط© ط§ظ„ظ…ظˆظ‚ط¹ â•گâ•گâ•گ
    is_active = models.BooleanField(default=True, verbose_name='ظ…ظپط¹ظ„')
    suspended_reason = models.TextField(
        blank=True, null=True,
        verbose_name='ط³ط¨ط¨ ط§ظ„ط¥ظٹظ‚ط§ظپ'
    )
    priority = models.PositiveIntegerField(
        default=0,
        verbose_name='ط§ظ„ط£ظˆظ„ظˆظٹط©',
        help_text='ط§ظ„ط£ط¹ظ„ظ‰ ط±ظ‚ظ… = ط§ظ„ط£ط¹ظ„ظ‰ ط£ظˆظ„ظˆظٹط©'
    )
    color_code = models.CharField(
        max_length=7, default='#3498db',
        verbose_name='ظ„ظˆظ† ط§ظ„طھظ…ظٹظٹط²',
        help_text='ظ…ط«ط§ظ„: #FF5733'
    )
    icon = models.CharField(
        max_length=50, default='location',
        verbose_name='ط§ظ„ط£ظٹظ‚ظˆظ†ط©'
    )
    
    # â•گâ•گâ•گ ظ…ط¹ظ„ظˆظ…ط§طھ ط¥ط¶ط§ظپظٹط© â•گâ•گâ•گ
    notes = models.TextField(blank=True, null=True, verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ')
    tags = models.JSONField(
        default=list, blank=True,
        verbose_name='Tags',
        help_text='ظ…ط«ط§ظ„: ["remote", "high-priority"]'
    )
    photo = models.ImageField(
        upload_to='work_locations/photos/',
        blank=True, null=True,
        verbose_name='طµظˆط±ط© ط§ظ„ظ…ظˆظ‚ط¹'
    )
    metadata = models.JSONField(
        default=dict, blank=True,
        verbose_name='ط¨ظٹط§ظ†ط§طھ ط¥ط¶ط§ظپظٹط©'
    )
    
    class Meta:
        verbose_name = 'ظ…ظˆظ‚ط¹ ط¹ظ…ظ„'
        verbose_name_plural = 'ظ…ظˆط§ظ‚ط¹ ط§ظ„ط¹ظ…ظ„'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['company', 'employee', 'status']),
            models.Index(fields=['company', 'status', 'is_active']),
        ]
    
    def __str__(self):
        emp_name = self.employee.first_name_ar if self.employee else 'ظ…ط´طھط±ظƒ'
        return f"{self.name} ({emp_name})"


# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# RouteHistory - طھط§ط±ظٹط® ط±ط­ظ„ط§طھ ط§ظ„ظ…ظˆط¸ظپظٹظ† (Machine Learning)
# ط§ظ„ط³ظٹط³طھظ… ط¨ظٹطھط¹ظ„ظ… ط¹ط§ط¯ط§طھ ظƒظ„ ظ…ظˆط¸ظپ ظ…ظ† ظ†ظ‚ط·ط© ظ„ط£ط®ط±ظ‰
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
class RouteHistory(TenantModel):
    """
    طھط§ط±ظٹط® ط§ظ„ط±ط­ظ„ط§طھ ط§ظ„ظ…طھظƒط±ط±ط© ظ„ظ„ظ…ظˆط¸ظپ ط¨ظٹظ† ظ†ظ‚ط·طھظٹظ†
    ط§ظ„ط³ظٹط³طھظ… ط¨ظٹط³طھط®ط¯ظ…ظ‡ط§ ط¹ط´ط§ظ† ظٹط­ط³ط¨ ط§ظ„ظˆظ‚طھ ط§ظ„ظ…طھظˆظ‚ط¹ ط¨ط¯ظ‚ط© ط£ط¹ظ„ظ‰
    """
    
    TIME_PERIOD_CHOICES = [
        ('morning', 'طµط¨ط§ط­ط§ظ‹ (6طµ-12ط¸)'),
        ('noon', 'ط¸ظ‡ط±ط§ظ‹ (12ط¸-4ط¹)'),
        ('evening', 'ظ…ط³ط§ط،ظ‹ (4ط¹-8ظ…)'),
        ('night', 'ظ„ظٹظ„ط§ظ‹ (8ظ…-6طµ)'),
    ]
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='route_history',
        verbose_name='ط§ظ„ظ…ظˆط¸ظپ'
    )
    
    # ظ†ظ‚ط·ط© ط§ظ„ط¨ط¯ط§ظٹط©
    from_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ط¨ط¯ط§ظٹط©'
    )
    from_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ط¨ط¯ط§ظٹط©'
    )
    from_location_name = models.CharField(
        max_length=300,
        blank=True, null=True,
        verbose_name='ط§ط³ظ… ظ…ظˆظ‚ط¹ ط§ظ„ط¨ط¯ط§ظٹط©'
    )
    
    # ظ†ظ‚ط·ط© ط§ظ„ظ†ظ‡ط§ظٹط©
    to_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        verbose_name='ط®ط· ط¹ط±ط¶ ط§ظ„ظ†ظ‡ط§ظٹط©'
    )
    to_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        verbose_name='ط®ط· ط·ظˆظ„ ط§ظ„ظ†ظ‡ط§ظٹط©'
    )
    to_location_name = models.CharField(
        max_length=300,
        blank=True, null=True,
        verbose_name='ط§ط³ظ… ظ…ظˆظ‚ط¹ ط§ظ„ظ†ظ‡ط§ظٹط©'
    )
    
    # ط§ظ„ظ‚ظٹط§ط³ط§طھ
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='ط§ظ„ظ…ط³ط§ظپط© (ظƒظ…)'
    )
    travel_time_minutes = models.PositiveIntegerField(
        verbose_name='ظˆظ‚طھ ط§ظ„طھظ†ظ‚ظ„ (ط¯ظ‚ط§ط¦ظ‚)'
    )
    
    # ط§ظ„طھظˆظ‚ظٹطھ
    departed_at = models.DateTimeField(
        verbose_name='طھط§ط±ظٹط® ظˆظˆظ‚طھ ط§ظ„ظ…ط؛ط§ط¯ط±ط©'
    )
    arrived_at = models.DateTimeField(
        verbose_name='طھط§ط±ظٹط® ظˆظˆظ‚طھ ط§ظ„ظˆطµظˆظ„'
    )
    
    # ظ„ظ„طھط­ظ„ظٹظ„
    time_period = models.CharField(
        max_length=20,
        choices=TIME_PERIOD_CHOICES,
        verbose_name='ظپطھط±ط© ط§ظ„ظٹظˆظ…'
    )
    day_of_week = models.PositiveSmallIntegerField(
        verbose_name='ظٹظˆظ… ط§ظ„ط£ط³ط¨ظˆط¹ (0=ط§ظ„ط£ط­ط¯, 6=ط§ظ„ط³ط¨طھ)'
    )
    
    # ظ…ظ„ط§ط­ط¸ط§طھ
    notes = models.TextField(
        blank=True, null=True,
        verbose_name='ظ…ظ„ط§ط­ط¸ط§طھ'
    )
    is_verified = models.BooleanField(
        default=True,
        verbose_name='ط±ط­ظ„ط© ظ…ظˆط«ظˆظ‚ط©',
        help_text='ظ„ظˆ falseطŒ ظ…ط´ ظ‡طھظڈط³طھط®ط¯ظ… ظپظٹ ط­ط³ط§ط¨ ط§ظ„ظ…طھظˆط³ط·'
    )
    
    class Meta:
        verbose_name = 'ط³ط¬ظ„ ط±ط­ظ„ط©'
        verbose_name_plural = 'ط³ط¬ظ„ط§طھ ط§ظ„ط±ط­ظ„ط§طھ'
        ordering = ['-arrived_at']
        indexes = [
            models.Index(fields=['employee', 'time_period']),
            models.Index(fields=['employee', 'from_latitude', 'from_longitude']),
        ]
    
    def __str__(self):
        return f"{self.employee}: {self.from_location_name or 'ظ…ظˆظ‚ط¹'} â†’ {self.to_location_name or 'ظ…ظˆظ‚ط¹'} ({self.travel_time_minutes} ط¯)"


from .company_policy_models import CompanyAllowancePolicy, CompanyDeductionPolicy, CompanyBonusPolicy

