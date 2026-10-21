"""
أجهزة البصمة (ZKTeco) والبصمات اللي جاية منها.

زي سجل التعديلات: جداول مستقلة من غير أي ربط (ForeignKey) بجداول تانية، ومن غير ملفات migrations،
وبتتعمل بأمر biometric_setup. كده إضافتها مابتلمسش أي جدول تاني.

المرحلة الأولى: البصمات بتتسجل وبتتربط بالموظفين وبتظهر في تقرير مقارنة مع حضور الموبايل،
ومابتدخلش الحضور ولا المرتبات لحد ما يتقرر.
"""
from django.db import models


class BiometricDevice(models.Model):
    """جهاز بصمة. الجهاز بيتعرف برقمه التسلسلي (SN)، ومابنقبلش بصمات غير من جهاز متسجل ومفعّل"""
    serial_number = models.CharField(max_length=64, unique=True)
    company_id = models.IntegerField(null=True, blank=True, db_index=True)   # فاضي = جهاز جديد لسه ماتسجلش
    branch_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=150, blank=True, default='')
    is_active = models.BooleanField(default=False)
    model_name = models.CharField(max_length=100, blank=True, default='')
    firmware = models.CharField(max_length=100, blank=True, default='')
    last_seen = models.DateTimeField(null=True, blank=True)
    last_ip = models.CharField(max_length=64, blank=True, default='')
    last_upload = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'biometric_device'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name or "جهاز"} ({self.serial_number})'


class BiometricUserMap(models.Model):
    """رقم الموظف على الجهاز (PIN) ↔ الموظف في البرنامج، لكل شركة"""
    company_id = models.IntegerField(db_index=True)
    pin = models.CharField(max_length=32)
    employee_id = models.IntegerField(null=True, blank=True, db_index=True)
    device_user_name = models.CharField(max_length=150, blank=True, default='')  # الاسم المتسجل على الجهاز
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, blank=True, default='')

    class Meta:
        db_table = 'biometric_user_map'
        constraints = [models.UniqueConstraint(fields=['company_id', 'pin'], name='biometric_map_company_pin')]


class BiometricPunch(models.Model):
    """بصمة واحدة زي ما جت من الجهاز أو من ملف"""
    SOURCES = [('device', 'الجهاز مباشرة'), ('upload', 'رفع ملف')]

    company_id = models.IntegerField(null=True, blank=True, db_index=True)
    device_serial = models.CharField(max_length=64, db_index=True)
    pin = models.CharField(max_length=32, db_index=True)
    punch_time = models.DateTimeField(db_index=True)
    status_code = models.CharField(max_length=8, blank=True, default='')   # 0 حضور، 1 انصراف، 2/3 استراحة، 4/5 إضافي
    verify_code = models.CharField(max_length=8, blank=True, default='')   # بصمة/كارت/وجه/باسورد
    employee_id = models.IntegerField(null=True, blank=True, db_index=True)
    source = models.CharField(max_length=10, choices=SOURCES, default='device')
    applied_to_attendance = models.BooleanField(default=False)   # المرحلة التانية
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'biometric_punch'
        ordering = ['-punch_time']
        constraints = [models.UniqueConstraint(fields=['device_serial', 'pin', 'punch_time'],
                                               name='biometric_punch_unique')]
        indexes = [models.Index(fields=['company_id', 'punch_time'], name='biometric_company_time')]
