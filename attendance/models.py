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