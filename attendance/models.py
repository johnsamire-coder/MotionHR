from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime, time
from core.models import TenantModel


class Shift(TenantModel):
    """الشيفت - أوقات العمل"""

    SHIFT_TYPE_CHOICES = [
        ('fixed', 'ثابت'),
        ('flexible', 'مرن'),
        ('rotating', 'متغير'),
        ('morning', 'صباحي'),
        ('evening', 'مسائي'),
        ('night', 'ليلي'),
        ('split', 'مقسم'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name='اسم الشيفت'
    )

    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPE_CHOICES,
        default='fixed',
        verbose_name='نوع الشيفت'
    )

    # النوع السلوكي الحقيقي للشيفت (نضيفه من غير ما نكسر القديم)
    SHIFT_MODE_CHOICES = [
        ('fixed', 'ثابت'),
        ('flex_fixed', 'مرن ثابت'),
        ('flex_split', 'مرن مقسم'),
        ('variable_daily', 'متغير يومي'),
        ('variable_weekly', 'متغير أسبوعي'),
        ('variable_weekly_flex', 'متغير أسبوعي مرن'),
        ('split_fixed', 'مقسم ثابت'),
    ]

    shift_mode = models.CharField(
        max_length=30,
        choices=SHIFT_MODE_CHOICES,
        default='fixed',
        verbose_name='النمط السلوكي للشيفت',
        help_text='بيحدد منطق الشيفت: ثابت، مرن، متغير، مقسم...'
    )

    # preset للتوقيت الافتراضي في الواجهة
    TIME_PRESET_CHOICES = [
        ('custom', 'مخصص'),
        ('morning', 'صباحي'),
        ('evening', 'مسائي'),
        ('night', 'ليلي'),
    ]

    time_preset = models.CharField(
        max_length=20,
        choices=TIME_PRESET_CHOICES,
        default='custom',
        verbose_name='توقيت افتراضي',
        help_text='للواجهة فقط: صباحي / مسائي / ليلي / مخصص'
    )

    # عدد الساعات المطلوبة يوميًا في الشيفتات المرنة
    required_daily_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=8,
        verbose_name='عدد الساعات المطلوبة يوميًا',
        help_text='مهم للمرن الثابت والمرن المقسم'
    )

    # هل مسموح بخروج جزئي ثم رجوع؟
    allow_partial_checkout = models.BooleanField(
        default=False,
        verbose_name='يسمح بخروج جزئي',
        help_text='مطلوب للمرن المقسم والمقسم الثابت'
    )

    # أقصى عدد فترات شغل في اليوم
    max_sessions_per_day = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='أقصى عدد فترات في اليوم',
        help_text='مثلاً 2 للمرن المقسم أو المقسم الثابت'
    )

    # نوع الجدول المتغير
    VARIABLE_SCHEDULE_TYPE_CHOICES = [
        ('none', 'لا يوجد'),
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('weekly_flex', 'أسبوعي مرن'),
    ]

    variable_schedule_type = models.CharField(
        max_length=20,
        choices=VARIABLE_SCHEDULE_TYPE_CHOICES,
        default='none',
        verbose_name='نوع الجدول المتغير'
    )

    # جدول ديناميكي JSON:
    # variable_daily  -> أوقات اليوم
    # variable_weekly -> أوقات الأيام
    # split_fixed     -> فترتين أو أكثر
    # flex_split      -> قواعد الفترات
    schedule_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='إعدادات الجدول الديناميكي'
    )

    start_time = models.TimeField(
        verbose_name='وقت البداية'
    )

    end_time = models.TimeField(
        verbose_name='وقت النهاية'
    )

    crosses_midnight = models.BooleanField(
        default=False,
        verbose_name='يمتد لليوم التالي',
        help_text='فعّل لو الشيفت بيبدأ بالليل وبينتهي الصبح'
    )

    grace_period = models.IntegerField(
        default=15,
        verbose_name='فترة السماح للتأخير (دقيقة)',
        help_text='الوقت المسموح للتأخير بدون احتساب تأخير'
    )

    grace_early_leave = models.IntegerField(
        default=0,
        verbose_name='فترة السماح للانصراف المبكر (دقيقة)',
        help_text='الوقت المسموح للانصراف قبل نهاية الشيفت بدون احتساب انصراف مبكر'
    )

    early_checkin_minutes = models.IntegerField(
        default=30,
        verbose_name='مسموح الحضور قبل الشيفت (دقيقة)',
        help_text='الحد الأقصى المسموح لتسجيل الحضور قبل بداية الشيفت'
    )

    work_sunday = models.BooleanField(default=True, verbose_name='الأحد')
    work_monday = models.BooleanField(default=True, verbose_name='الاثنين')
    work_tuesday = models.BooleanField(default=True, verbose_name='الثلاثاء')
    work_wednesday = models.BooleanField(default=True, verbose_name='الأربعاء')
    work_thursday = models.BooleanField(default=True, verbose_name='الخميس')
    work_friday = models.BooleanField(default=False, verbose_name='الجمعة')
    work_saturday = models.BooleanField(default=False, verbose_name='السبت')

    break_duration = models.IntegerField(
        default=60,
        verbose_name='مدة الراحة (دقيقة)'
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name='شيفت افتراضي للشركة',
        help_text='لو مفيش شيفت محدد للموظف، هيستخدم الشيفت الافتراضي'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )

    class Meta:
        verbose_name = 'شيفت'
        verbose_name_plural = 'الشيفتات'
        ordering = ['name']

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
        day_map = {
            0: self.work_sunday,
            1: self.work_monday,
            2: self.work_tuesday,
            3: self.work_wednesday,
            4: self.work_thursday,
            5: self.work_friday,
            6: self.work_saturday,
        }
        return day_map.get(date.weekday(), False)



class AttendanceSession(TenantModel):
    """
    فترة حضور واحدة — للشيفتات المقسمة والمرنة المقسمة
    كل يوم ممكن يكون فيه أكتر من فترة (session)
    """

    attendance = models.ForeignKey(
        'Attendance',
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='سجل الحضور'
    )

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        verbose_name='الموظف'
    )

    session_number = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='رقم الفترة',
        help_text='1 للفترة الأولى، 2 للثانية...'
    )

    check_in_time = models.DateTimeField(
        verbose_name='وقت دخول الفترة'
    )

    check_out_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت خروج الفترة'
    )

    check_in_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='خط عرض الدخول'
    )

    check_in_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='خط طول الدخول'
    )

    check_out_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='خط عرض الخروج'
    )

    check_out_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        blank=True, null=True,
        verbose_name='خط طول الخروج'
    )

    is_partial = models.BooleanField(
        default=False,
        verbose_name='خروج جزئي',
        help_text='True لو الموظف خرج ورجع تاني'
    )

    worked_minutes = models.IntegerField(
        default=0,
        verbose_name='دقائق العمل في الفترة دي'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'فترة حضور'
        verbose_name_plural = 'فترات الحضور'
        ordering = ['attendance', 'session_number']
        unique_together = [['attendance', 'session_number']]

    def __str__(self):
        return f"{self.employee} - يوم {self.attendance.date} - فترة {self.session_number}"

    def calculate_worked_minutes(self):
        """بيحسب دقائق العمل لو فيه check_out"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            self.worked_minutes = int(delta.total_seconds() / 60)
            return self.worked_minutes
        return 0

    @property
    def is_complete(self):
        """هل الفترة اكتملت (فيها دخول وخروج)"""
        return self.check_in_time is not None and self.check_out_time is not None


class AttendancePolicy(TenantModel):
    """سياسة الحضور والخصم — لكل شركة/فرع/قسم"""

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('approved', 'معتمد'),
        ('active', 'نشط'),
        ('archived', 'مؤرشف'),
    ]

    name = models.CharField(max_length=200, verbose_name='اسم السياسة')
    effective_from = models.DateField(verbose_name='سارية من')
    effective_to = models.DateField(blank=True, null=True, verbose_name='سارية لحد')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    approved_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_policies',
        verbose_name='وافق بواسطة'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'سياسة حضور'
        verbose_name_plural = 'سياسات الحضور'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.name} ({self.effective_from})"


class AttendancePolicyAssignment(TenantModel):
    """ربط السياسة بشركة/فرع/قسم"""

    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'شركة'),
        ('branch', 'فرع'),
        ('department', 'قسم'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='assignments', verbose_name='السياسة'
    )
    assignment_type = models.CharField(
        max_length=20, choices=ASSIGNMENT_TYPE_CHOICES,
        default='company', verbose_name='نوع التعيين'
    )
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='الفرع'
    )
    department = models.ForeignKey(
        'companies.Department', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='القسم'
    )
    priority = models.IntegerField(
        default=3,
        help_text='1=قسم, 2=فرع, 3=شركة',
        verbose_name='الأولوية'
    )

    class Meta:
        verbose_name = 'تعيين سياسة'
        verbose_name_plural = 'تعيينات السياسات'


class LateRule(models.Model):
    """قواعد خصم التأخير"""

    DEDUCTION_TYPE_CHOICES = [
        ('none', 'لا خصم'),
        ('day_fraction', 'نسبة من اليوم'),
        ('fixed_amount', 'مبلغ ثابت'),
        ('per_minute', 'لكل دقيقة'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='late_rules', verbose_name='السياسة'
    )
    from_minutes = models.IntegerField(default=0, verbose_name='من دقيقة')
    to_minutes = models.IntegerField(default=15, verbose_name='إلى دقيقة')
    deduction_type = models.CharField(
        max_length=20, choices=DEDUCTION_TYPE_CHOICES,
        default='none', verbose_name='نوع الخصم'
    )
    deduction_value = models.DecimalField(
        max_digits=8, decimal_places=4, default=0,
        verbose_name='قيمة الخصم',
        help_text='0.25 = ربع يوم / 50 = مبلغ ثابت / 1 = لكل دقيقة'
    )
    display_order = models.IntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'قاعدة تأخير'
        verbose_name_plural = 'قواعد التأخير'
        ordering = ['display_order', 'from_minutes']

    def __str__(self):
        return f"{self.policy.name}: {self.from_minutes}-{self.to_minutes} د → {self.deduction_type}"


class AbsenceRule(models.Model):
    """قواعد خصم الغياب"""

    ABSENCE_TYPE_CHOICES = [
        ('unexcused', 'بدون إذن'),
        ('consecutive', 'متتالي'),
        ('repeated', 'متكرر في الشهر'),
    ]

    DEDUCTION_TYPE_CHOICES = [
        ('day_fraction', 'نسبة من اليوم'),
        ('fixed_amount', 'مبلغ ثابت'),
        ('warning', 'إنذار فقط'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='absence_rules', verbose_name='السياسة'
    )
    absence_type = models.CharField(
        max_length=20, choices=ABSENCE_TYPE_CHOICES,
        default='unexcused', verbose_name='نوع الغياب'
    )
    consecutive_days = models.IntegerField(
        default=1, null=True, blank=True,
        verbose_name='عدد الأيام المتتالية'
    )
    occurrences_in_month = models.IntegerField(
        default=1, null=True, blank=True,
        verbose_name='عدد المرات في الشهر'
    )
    deduction_type = models.CharField(
        max_length=20, choices=DEDUCTION_TYPE_CHOICES,
        default='day_fraction', verbose_name='نوع الخصم'
    )
    deduction_value = models.DecimalField(
        max_digits=8, decimal_places=4, default=1,
        verbose_name='قيمة الخصم',
        help_text='1 = يوم كامل / 1.5 = يوم ونص / 50 = مبلغ ثابت'
    )
    display_order = models.IntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'قاعدة غياب'
        verbose_name_plural = 'قواعد الغياب'
        ordering = ['display_order']


class OvertimeRule(models.Model):
    """قواعد الأوفر تايم"""

    OVERTIME_TYPE_CHOICES = [
        ('regular', 'عادي'),
        ('after_shift', 'بعد الشيفت'),
        ('weekend', 'يوم راحة'),
        ('holiday', 'إجازة رسمية'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='overtime_rules', verbose_name='السياسة'
    )
    overtime_type = models.CharField(
        max_length=20, choices=OVERTIME_TYPE_CHOICES,
        default='after_shift', verbose_name='نوع الأوفر تايم'
    )
    multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.5,
        verbose_name='المضاعف',
        help_text='1.5 = مرة ونص / 2.0 = ضعفين'
    )
    min_minutes = models.IntegerField(
        default=30,
        verbose_name='أقل وقت يتحسب (دقيقة)'
    )
    max_hours_per_day = models.IntegerField(
        default=4, null=True, blank=True,
        verbose_name='أقصى ساعات في اليوم'
    )
    max_hours_per_month = models.IntegerField(
        default=40, null=True, blank=True,
        verbose_name='أقصى ساعات في الشهر'
    )
    requires_approval = models.BooleanField(
        default=False, verbose_name='يحتاج موافقة مسبقة'
    )
    display_order = models.IntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'قاعدة أوفر تايم'
        verbose_name_plural = 'قواعد الأوفر تايم'
        ordering = ['display_order']


class NightShiftRule(models.Model):
    """قواعد بدل الشيفت الليلي"""

    ALLOWANCE_TYPE_CHOICES = [
        ('fixed_amount', 'مبلغ ثابت'),
        ('percentage', 'نسبة من اليومي'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='night_shift_rules', verbose_name='السياسة'
    )
    allowance_type = models.CharField(
        max_length=20, choices=ALLOWANCE_TYPE_CHOICES,
        default='fixed_amount', verbose_name='نوع البدل'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=50,
        verbose_name='المبلغ الثابت'
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        verbose_name='النسبة المئوية من الأجر اليومي'
    )
    night_start_hour = models.IntegerField(
        default=20, verbose_name='بداية الليل (ساعة)',
        help_text='20 = 8 مساءً'
    )
    min_night_hours = models.IntegerField(
        default=4, verbose_name='أقل ساعات ليلية للاستحقاق'
    )

    class Meta:
        verbose_name = 'قاعدة بدل ليلي'
        verbose_name_plural = 'قواعد البدل الليلي'


class WeekendWorkRule(models.Model):
    """قواعد العمل يوم الراحة"""

    COMPENSATION_TYPE_CHOICES = [
        ('overtime_multiplier', 'نسبة من المرتب'),
        ('fixed_amount', 'مبلغ ثابت'),
        ('day_off', 'يوم إجازة بديل'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='weekend_work_rules', verbose_name='السياسة'
    )
    compensation_type = models.CharField(
        max_length=30, choices=COMPENSATION_TYPE_CHOICES,
        default='overtime_multiplier', verbose_name='نوع التعويض'
    )
    multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=2.0,
        verbose_name='المضاعف'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        null=True, blank=True, verbose_name='المبلغ الثابت'
    )

    class Meta:
        verbose_name = 'قاعدة عمل يوم الراحة'
        verbose_name_plural = 'قواعد العمل يوم الراحة'


class LateRepeatPenalty(models.Model):
    """جزاء تكرار التأخير في الشهر"""

    PENALTY_TYPE_CHOICES = [
        ('warning', 'إنذار'),
        ('deduction', 'خصم'),
        ('suspension', 'وقف'),
    ]

    policy = models.ForeignKey(
        AttendancePolicy, on_delete=models.CASCADE,
        related_name='late_repeat_penalties', verbose_name='السياسة'
    )
    occurrences = models.IntegerField(
        default=3, verbose_name='عدد مرات التأخير في الشهر'
    )
    penalty_type = models.CharField(
        max_length=20, choices=PENALTY_TYPE_CHOICES,
        default='warning', verbose_name='نوع الجزاء'
    )
    deduction_value = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        null=True, blank=True, verbose_name='قيمة الخصم'
    )
    description = models.TextField(blank=True, verbose_name='وصف الجزاء')

    class Meta:
        verbose_name = 'جزاء تكرار التأخير'
        verbose_name_plural = 'جزاءات تكرار التأخير'
        ordering = ['occurrences']

class ShiftAssignment(TenantModel):
    """تعيين الشيفت على مستوى شركة / فرع / قسم / موظف"""

    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'شركة'),
        ('branch', 'فرع'),
        ('department', 'قسم'),
        ('employee', 'موظف'),
    ]

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name='الشيفت'
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        verbose_name='نوع التعيين'
    )

    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shift_assignments',
        verbose_name='الفرع'
    )

    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shift_assignments',
        verbose_name='القسم'
    )

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shift_assignments',
        verbose_name='الموظف'
    )

    start_date = models.DateField(
        verbose_name='تاريخ البداية'
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ النهاية'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )

    priority = models.IntegerField(
        default=4,
        verbose_name='الأولوية',
        help_text='1=موظف, 2=قسم, 3=فرع, 4=شركة'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'تعيين شيفت'
        verbose_name_plural = 'تعيينات الشيفتات'
        ordering = ['priority', '-start_date']

    def __str__(self):
        target = 'غير محدد'
        if self.assignment_type == 'employee' and self.employee:
            target = self.employee.full_name_ar
        elif self.assignment_type == 'department' and self.department:
            target = self.department.name_ar
        elif self.assignment_type == 'branch' and self.branch:
            target = self.branch.name_ar
        elif self.assignment_type == 'company' and self.company:
            target = self.company.name_ar
        return f"{self.shift.name} → {target}"


class EmployeeShift(TenantModel):
    """ربط الموظف بالشيفت"""

    ASSIGNMENT_TYPE_CHOICES = [
        ('company', 'شركة'),
        ('branch', 'فرع'),
        ('department', 'قسم'),
        ('employee', 'موظف'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name='الموظف'
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='الشيفت'
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default='employee',
        verbose_name='نوع التعيين'
    )

    start_date = models.DateField(
        verbose_name='تاريخ البداية'
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ النهاية'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )

    priority = models.IntegerField(
        default=1,
        verbose_name='الأولوية',
        help_text='1=موظف, 2=قسم, 3=فرع, 4=شركة'
    )

    class Meta:
        verbose_name = 'شيفت موظف'
        verbose_name_plural = 'شيفتات الموظفين'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.shift.name}"


class ShiftChangeRequest(TenantModel):
    """طلب تغيير شيفت مع موافقات"""

    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shift_change_requests',
        verbose_name='الموظف'
    )

    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='shift_changes_requested',
        verbose_name='طلب بواسطة'
    )

    old_shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='old_change_requests',
        verbose_name='الشيفت القديم'
    )

    new_shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='new_change_requests',
        verbose_name='الشيفت الجديد'
    )

    effective_from = models.DateField(
        verbose_name='تاريخ بداية السريان'
    )

    effective_to = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ نهاية السريان'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة'
    )

    requires_approval = models.BooleanField(
        default=True,
        verbose_name='يحتاج موافقة'
    )

    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_changes_approved',
        verbose_name='وافق بواسطة'
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name='سبب الرفض'
    )

    reason = models.TextField(
        blank=True,
        verbose_name='سبب طلب التغيير'
    )

    notified_manager = models.BooleanField(default=False, verbose_name='تم إبلاغ المدير')
    notified_hr = models.BooleanField(default=False, verbose_name='تم إبلاغ HR')
    notified_employee = models.BooleanField(default=False, verbose_name='تم إبلاغ الموظف')

    class Meta:
        verbose_name = 'طلب تغيير شيفت'
        verbose_name_plural = 'طلبات تغيير الشيفتات'
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب تغيير شيفت - {self.employee} - {self.status}"


class ShiftOverride(TenantModel):
    """استثناء شيفت ليوم معين"""

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shift_overrides',
        verbose_name='الموظف'
    )

    override_date = models.DateField(
        verbose_name='تاريخ الاستثناء'
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='overrides',
        verbose_name='الشيفت البديل'
    )

    reason = models.TextField(
        blank=True,
        verbose_name='سبب الاستثناء'
    )

    class Meta:
        verbose_name = 'استثناء شيفت'
        verbose_name_plural = 'استثناءات الشيفتات'
        ordering = ['-override_date']
        unique_together = [['employee', 'override_date']]

    def __str__(self):
        return f"{self.employee} - {self.override_date} - {self.shift.name}"


class ShiftRotation(TenantModel):
    """تناوب الشيفتات"""

    ROTATION_TYPE_CHOICES = [
        ('weekly', 'أسبوعي'),
        ('biweekly', 'كل أسبوعين'),
        ('monthly', 'شهري'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name='اسم التناوب'
    )

    rotation_type = models.CharField(
        max_length=20,
        choices=ROTATION_TYPE_CHOICES,
        default='weekly',
        verbose_name='نوع التناوب'
    )

    shifts = models.ManyToManyField(
        Shift,
        related_name='rotations',
        verbose_name='الشيفتات'
    )

    employees = models.ManyToManyField(
        'employees.Employee',
        related_name='rotations',
        verbose_name='الموظفون'
    )

    start_date = models.DateField(
        verbose_name='تاريخ بداية التناوب'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )

    class Meta:
        verbose_name = 'تناوب شيفتات'
        verbose_name_plural = 'تناوبات الشيفتات'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.get_rotation_type_display()})"


class Attendance(TenantModel):
    """سجل الحضور اليومي"""
    
    STATUS_CHOICES = [
        ('present', 'حاضر'),
        ('absent', 'غائب'),
        ('late', 'متأخر'),
        ('early_leave', 'انصراف مبكر'),
        ('on_leave', 'في إجازة'),
        ('holiday', 'عطلة رسمية'),
        ('weekend', 'إجازة أسبوعية'),
    ]
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='الموظف'
    )
    
    date = models.DateField(
        verbose_name='التاريخ'
    )
    
    # الحضور
    check_in_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت الحضور'
    )
    check_in_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط عرض الحضور'
    )
    check_in_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط طول الحضور'
    )
    check_in_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='عنوان الحضور'
    )
    check_in_within_range = models.BooleanField(
        default=False,
        verbose_name='داخل نطاق الفرع'
    )
    check_in_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات الحضور'
    )
    
    # الانصراف
    check_out_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت الانصراف'
    )
    check_out_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط عرض الانصراف'
    )
    check_out_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط طول الانصراف'
    )
    check_out_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='عنوان الانصراف'
    )
    check_out_within_range = models.BooleanField(
        default=False,
        verbose_name='داخل نطاق الفرع'
    )
    check_out_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات الانصراف'
    )
    
    # الحسابات
    work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ساعات العمل'
    )
    late_minutes = models.IntegerField(
        default=0,
        verbose_name='دقائق التأخير'
    )
    early_leave_minutes = models.IntegerField(
        default=0,
        verbose_name='دقائق الانصراف المبكر'
    )
    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='ساعات الأوفر تايم'
    )
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present',
        verbose_name='الحالة'
    )
    
    # الشيفت المسند
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='attendances',
        verbose_name='الشيفت'
    )
    
    # هل تم تعديله يدوياً
    is_manually_edited = models.BooleanField(
        default=False,
        verbose_name='معدل يدوياً'
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات الإدارة'
    )
    
    class Meta:
        verbose_name = 'سجل حضور'
        verbose_name_plural = 'سجلات الحضور'
        ordering = ['-date', '-check_in_time']
        unique_together = [['employee', 'date']]
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.date}"
    
    def calculate_work_hours(self):
        """حساب ساعات العمل"""
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours = duration.total_seconds() / 3600
            self.work_hours = round(hours, 2)
            return self.work_hours
        return 0
    
    def calculate_late_minutes(self):
        """حساب دقائق التأخير"""
        if self.check_in_time and self.shift:
            shift_start = datetime.combine(
                self.date,
                self.shift.start_time
            )
            # تحويل check_in_time لنفس timezone
            check_in_naive = self.check_in_time.replace(tzinfo=None)
            
            if check_in_naive > shift_start:
                diff = check_in_naive - shift_start
                minutes = int(diff.total_seconds() / 60)
                # خصم فترة السماح
                minutes -= self.shift.grace_period
                self.late_minutes = max(0, minutes)
            else:
                self.late_minutes = 0
        return self.late_minutes


class LocationLog(TenantModel):
    """
    سجل تتبع المواقع المستمر
    للموظفين الميدانيين اللي فعّالين is_field_worker
    """
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_logs',
        verbose_name='الموظف'
    )
    
    timestamp = models.DateTimeField(
        verbose_name='الوقت'
    )
    
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='خط العرض'
    )
    
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='خط الطول'
    )
    
    accuracy = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='دقة الموقع (متر)'
    )
    
    speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='السرعة (كم/س)'
    )
    
    battery_level = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='مستوى البطارية %'
    )
    
    address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    
    class Meta:
        verbose_name = 'سجل موقع'
        verbose_name_plural = 'سجلات المواقع'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['employee', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.timestamp}"


class LocationCheckIn(TenantModel):
    """
    Check-in في مواقع محددة
    مفيد للمشتريات، المبيعات، الصيانة، الخ
    """
    
    VISIT_TYPE_CHOICES = [
        ('client_visit', 'زيارة عميل'),
        ('supplier_visit', 'زيارة مورد'),
        ('site_inspection', 'معاينة موقع'),
        ('maintenance', 'صيانة'),
        ('delivery', 'توصيل'),
        ('meeting', 'اجتماع'),
        ('purchase', 'شراء'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('arrived', 'وصل'),
        ('in_progress', 'جاري العمل'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_checkins',
        verbose_name='الموظف'
    )
    
    visit_type = models.CharField(
        max_length=30,
        choices=VISIT_TYPE_CHOICES,
        verbose_name='نوع الزيارة'
    )
    
    location_name = models.CharField(
        max_length=300,
        verbose_name='اسم الموقع/العميل'
    )
    
    # وقت الوصول
    arrival_time = models.DateTimeField(
        verbose_name='وقت الوصول'
    )
    arrival_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='خط عرض الوصول'
    )
    arrival_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='خط طول الوصول'
    )
    arrival_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='عنوان الوصول'
    )
    
    # وقت المغادرة
    departure_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت المغادرة'
    )
    departure_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط عرض المغادرة'
    )
    departure_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط طول المغادرة'
    )
    
    # التفاصيل
    purpose = models.TextField(
        blank=True,
        null=True,
        verbose_name='الغرض من الزيارة'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    
    photo = models.ImageField(
        upload_to='attendance/checkins/',
        blank=True,
        null=True,
        verbose_name='صورة'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='arrived',
        verbose_name='الحالة'
    )
    
    class Meta:
        verbose_name = 'زيارة موقع'
        verbose_name_plural = 'زيارات المواقع'
        ordering = ['-arrival_time']
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.location_name} - {self.arrival_time}"
    
    @property
    def duration_minutes(self):
        """مدة الزيارة بالدقائق"""
        if self.arrival_time and self.departure_time:
            duration = self.departure_time - self.arrival_time
            return int(duration.total_seconds() / 60)
        return None

class AttendanceActionLog(TenantModel):
    """سجل تعديلات الحضور والانصراف"""

    ACTION_CHOICES = [
        ("edit", "تعديل"),
        ("cancel_checkin", "إلغاء حضور"),
        ("cancel_checkout", "إلغاء انصراف"),
        ("delete", "حذف سجل"),
    ]

    attendance = models.ForeignKey(
        "Attendance",
        on_delete=models.CASCADE,
        related_name="action_logs",
        verbose_name="سجل الحضور"
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="نوع الإجراء"
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_actions",
        verbose_name="تم بواسطة"
    )
    reason = models.TextField(
        verbose_name="سبب التعديل"
    )
    old_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="البيانات قبل التعديل"
    )
    new_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="البيانات بعد التعديل"
    )
    action_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإجراء"
    )

    class Meta:
        verbose_name = "سجل تعديل حضور"
        verbose_name_plural = "سجلات تعديلات الحضور"
        ordering = ["-action_at"]

    def __str__(self):
        return f"{self.attendance} - {self.get_action_type_display()}"


# ════════════════════════════════════════════════════════════
# نظام التأخيرات والإجراءات التأديبية
# ════════════════════════════════════════════════════════════

class LateIncident(TenantModel):
    """حادثة تأخير"""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="late_incidents",
        verbose_name="الموظف"
    )
    attendance = models.ForeignKey(
        "Attendance",
        on_delete=models.CASCADE,
        related_name="late_incidents",
        verbose_name="سجل الحضور",
        null=True,
        blank=True
    )
    date = models.DateField(verbose_name="التاريخ")
    late_minutes = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="دقائق التأخير"
    )
    shift_start_time = models.TimeField(
        null=True, blank=True,
        verbose_name="بداية الشيفت"
    )
    actual_checkin_time = models.TimeField(
        null=True, blank=True,
        verbose_name="وقت الحضور الفعلي"
    )
    grace_period_used = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="السماحية المستخدمة"
    )
    month = models.PositiveSmallIntegerField(verbose_name="الشهر")
    year = models.PositiveSmallIntegerField(verbose_name="السنة")
    incident_number_in_month = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="رقم الحادثة في الشهر"
    )
    is_excused = models.BooleanField(
        default=False,
        verbose_name="معذور"
    )
    excuse_reason = models.TextField(
        blank=True,
        verbose_name="سبب العذر"
    )

    class Meta:
        verbose_name = "حادثة تأخير"
        verbose_name_plural = "حوادث التأخير"
        ordering = ["-date"]
        unique_together = [["employee", "date"]]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.late_minutes} دقيقة"


class LateNotification(TenantModel):
    """إشعار تأخير لـ HR"""

    NOTIFICATION_TYPES = [
        ("single_late", "تأخير عادي"),
        ("threshold_reached", "وصل الحد"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="late_notifications",
        verbose_name="الموظف"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="single_late",
        verbose_name="نوع الإشعار"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="العنوان"
    )
    message = models.TextField(
        verbose_name="الرسالة"
    )
    details = models.TextField(
        blank=True,
        verbose_name="التفاصيل"
    )
    suggested_action = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="الإجراء المقترح"
    )
    incident_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="عدد مرات التأخير"
    )
    month = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="الشهر"
    )
    year = models.PositiveSmallIntegerField(
        default=2025,
        verbose_name="السنة"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="تم القراءة"
    )
    is_acted_upon = models.BooleanField(
        default=False,
        verbose_name="تم اتخاذ إجراء"
    )
    action_taken = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="الإجراء المتخذ"
    )
    action_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="late_actions_taken",
        verbose_name="تم بواسطة"
    )
    action_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت الإجراء"
    )
    action_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات الإجراء"
    )

    class Meta:
        verbose_name = "إشعار تأخير"
        verbose_name_plural = "إشعارات التأخير"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"


class DisciplinaryAction(TenantModel):
    """إجراء تأديبي"""

    ACTION_TYPES = [
        ("verbal_warning", "إنذار شفهي"),
        ("written_warning", "إنذار كتابي"),
        ("quarter_day_deduction", "خصم ربع يوم"),
        ("half_day_deduction", "خصم نصف يوم"),
        ("full_day_deduction", "خصم يوم كامل"),
        ("suspension", "إيقاف عن العمل"),
        ("termination_warning", "إنذار فصل"),
        ("dismissed", "تم الإعفاء / التجاهل"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="disciplinary_actions",
        verbose_name="الموظف"
    )
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES,
        verbose_name="نوع الإجراء"
    )
    reason = models.TextField(
        verbose_name="السبب"
    )
    related_notification = models.ForeignKey(
        LateNotification,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="disciplinary_actions",
        verbose_name="الإشعار المرتبط"
    )
    auto_generated = models.BooleanField(
        default=False,
        verbose_name="تم تلقائيًا"
    )
    deduction_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name="مبلغ الخصم"
    )
    deduction_created = models.BooleanField(
        default=False,
        verbose_name="تم إنشاء خصم فعلي"
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="disciplinary_actions_performed",
        verbose_name="تم بواسطة"
    )
    performed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإجراء"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "إجراء تأديبي"
        verbose_name_plural = "الإجراءات التأديبية"
        ordering = ["-performed_at"]

    def __str__(self):
        return f"{self.employee} - {self.get_action_type_display()}"


# ════════════════════════════════════════════════════════════
# تكليف يومي / جدول العمل اليومي
# ════════════════════════════════════════════════════════════
class DailyAssignment(TenantModel):
    """
    تكليف يومي لكل موظف
    ده اللي بيحدد نوع يوم العمل وطريقة تنفيذه
    """

    # ── نوع اليوم ────────────────────────────────────
    DAY_TYPES = [
        ("work_day", "يوم عمل"),
        ("off_day", "راحة أسبوعية"),
        ("leave_day", "إجازة"),
        ("holiday", "إجازة رسمية"),
        ("mission_day", "مأمورية / مهمة"),
        ("standby_day", "استدعاء / on-call"),
        ("training_day", "يوم تدريب"),
    ]

    # ── طريقة التنفيذ ────────────────────────────────
    WORK_MODES = [
        ("fixed", "ثابت"),
        ("flexible", "مرن"),
        ("split", "متقسم"),
        ("field", "ميداني"),
        ("remote", "عن بُعد"),
        ("mixed", "مختلط"),
    ]

    # ── حالة التكليف ─────────────────────────────────
    STATUS_CHOICES = [
        ("scheduled", "مجدول"),
        ("in_progress", "جاري"),
        ("completed", "مكتمل"),
        ("cancelled", "ملغي"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="daily_assignments",
        verbose_name="الموظف"
    )
    date = models.DateField(
        verbose_name="التاريخ"
    )

    # ── نوع اليوم وطريقة العمل ─────────────────────
    day_type = models.CharField(
        max_length=20,
        choices=DAY_TYPES,
        default="work_day",
        verbose_name="نوع اليوم"
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODES,
        default="fixed",
        verbose_name="طريقة التنفيذ"
    )

    # ── أوقات العمل ──────────────────────────────────
    shift = models.ForeignKey(
        "Shift",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="الشيفت"
    )
    start_time = models.TimeField(
        null=True, blank=True,
        verbose_name="بداية العمل"
    )
    end_time = models.TimeField(
        null=True, blank=True,
        verbose_name="نهاية العمل"
    )
    expected_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True, blank=True,
        verbose_name="الساعات المتوقعة"
    )

    # ── Split Shift (جزئين) ──────────────────────────
    segment_2_start = models.TimeField(
        null=True, blank=True,
        verbose_name="بداية الجزء الثاني"
    )
    segment_2_end = models.TimeField(
        null=True, blank=True,
        verbose_name="نهاية الجزء الثاني"
    )

    # ── Flags ────────────────────────────────────────
    is_replacement = models.BooleanField(
        default=False,
        verbose_name="بديل لزميل"
    )
    replaces_employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="replaced_assignments",
        verbose_name="بديل عن"
    )
    is_extra_shift = models.BooleanField(
        default=False,
        verbose_name="شيفت إضافي"
    )
    count_as_overtime = models.BooleanField(
        default=False,
        verbose_name="يحسب أوفر تايم"
    )
    count_as_compensatory = models.BooleanField(
        default=False,
        verbose_name="يوم تعويضي"
    )

    # ── متطلبات ──────────────────────────────────────
    requires_tracking = models.BooleanField(
        default=False,
        verbose_name="يحتاج تتبع GPS"
    )
    requires_visits = models.BooleanField(
        default=False,
        verbose_name="يحتاج تسجيل زيارات"
    )
    requires_geofence = models.BooleanField(
        default=True,
        verbose_name="يحتاج نطاق الفرع"
    )
    requires_manager_approval = models.BooleanField(
        default=False,
        verbose_name="يحتاج موافقة المدير مسبقاً"
    )

    # ── المهمة ───────────────────────────────────────
    task_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="عنوان المهمة"
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="اسم الموقع"
    )

    # ── الحالة والاعتماد ─────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name="الحالة"
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_assignments",
        verbose_name="اعتمد بواسطة"
    )

    # ── Exception ────────────────────────────────────
    is_exception = models.BooleanField(
        default=False,
        verbose_name="حالة استثنائية"
    )
    exception_reason = models.TextField(
        blank=True,
        verbose_name="سبب الاستثناء"
    )
    exception_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("pending_review", "قيد المراجعة"),
            ("approved", "معتمد"),
            ("rejected", "مرفوض"),
        ],
        verbose_name="حالة الاستثناء"
    )

    # ── Auto Generated ───────────────────────────────
    is_auto_generated = models.BooleanField(
        default=False,
        verbose_name="تم توليده تلقائياً"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "تكليف يومي"
        verbose_name_plural = "التكليفات اليومية"
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
    """تنبيه تتبع صامت عند الخروج من النطاق أثناء العمل"""

    STATUS_CHOICES = [
        ("open", "مفتوح"),
        ("resolved", "تمت المعالجة"),
        ("ignored", "تم التجاهل"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="tracking_alerts",
        verbose_name="الموظف"
    )
    date = models.DateField(
        verbose_name="التاريخ"
    )
    started_at = models.DateTimeField(
        verbose_name="وقت بداية الخروج من النطاق"
    )
    last_seen_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="آخر وقت رصد"
    )
    minutes_outside = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الدقائق خارج النطاق"
    )

    last_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="آخر خط عرض"
    )
    last_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="آخر خط طول"
    )
    last_address = models.TextField(
        blank=True,
        verbose_name="آخر عنوان"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        verbose_name="الحالة"
    )

    notified_manager = models.BooleanField(
        default=False,
        verbose_name="تم تنبيه المدير"
    )
    notified_hr = models.BooleanField(
        default=False,
        verbose_name="تم تنبيه HR"
    )
    notified_company_admin = models.BooleanField(
        default=False,
        verbose_name="تم تنبيه صاحب الشركة"
    )

    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="resolved_tracking_alerts",
        verbose_name="تمت المعالجة بواسطة"
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت المعالجة"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "تنبيه تتبع"
        verbose_name_plural = "تنبيهات التتبع"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.minutes_outside} دقيقة"

class LocationHistory(TenantModel):
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_history',
        verbose_name='الموظف'
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7, verbose_name='خط العرض')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, verbose_name='خط الطول')
    accuracy = models.FloatField(null=True, blank=True, verbose_name='الدقة')
    recorded_at = models.DateTimeField(verbose_name='وقت التسجيل')
    shift_date = models.DateField(verbose_name='تاريخ الشيفت')
    point_index = models.IntegerField(default=0, verbose_name='رقم النقطة')
    address = models.CharField(max_length=500, blank=True, verbose_name='العنوان')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['shift_date', 'recorded_at']
        verbose_name = 'سجل موقع'
        verbose_name_plural = 'سجلات المواقع'

    def __str__(self):
        return f"{self.employee} - {self.shift_date} - نقطة {self.point_index}"


# Import Missions Models
from .missions_models import *

# Phase 14 - Company Work Policy
from .company_policy_models import CompanyWorkPolicy
from .payroll_settings_model import PayrollSettings

from .payroll_pro_models import PayrollRun, PayrollLine, PayrollBonus, PayrollPenalty, PayrollInstallment
