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
    
    start_time = models.TimeField(
        verbose_name='وقت البداية'
    )
    
    end_time = models.TimeField(
        verbose_name='وقت النهاية'
    )
    
    # فترة السماح للتأخير بالدقائق
    grace_period = models.IntegerField(
        default=15,
        verbose_name='فترة السماح (دقيقة)',
        help_text='الوقت المسموح للتأخير بدون احتساب تأخير'
    )
    
    # أيام العمل
    work_sunday = models.BooleanField(default=True, verbose_name='الأحد')
    work_monday = models.BooleanField(default=True, verbose_name='الاثنين')
    work_tuesday = models.BooleanField(default=True, verbose_name='الثلاثاء')
    work_wednesday = models.BooleanField(default=True, verbose_name='الأربعاء')
    work_thursday = models.BooleanField(default=True, verbose_name='الخميس')
    work_friday = models.BooleanField(default=False, verbose_name='الجمعة')
    work_saturday = models.BooleanField(default=False, verbose_name='السبت')
    
    # وقت الراحة
    break_duration = models.IntegerField(
        default=60,
        verbose_name='مدة الراحة (دقيقة)'
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
        """إجمالي ساعات العمل"""
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        # لو الشيفت بالليل
        if end < start:
            end += timedelta(days=1)
        
        duration = end - start
        hours = duration.total_seconds() / 3600
        # خصم وقت الراحة
        hours -= self.break_duration / 60
        return round(hours, 2)


class EmployeeShift(TenantModel):
    """ربط الموظف بالشيفت"""
    
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
    
    class Meta:
        verbose_name = 'شيفت موظف'
        verbose_name_plural = 'شيفتات الموظفين'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.shift.name}"


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
