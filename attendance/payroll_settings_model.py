"""
MotionHR - Payroll Settings Model
Phase 15: إعدادات الرواتب المتقدمة
"""
from django.db import models


class PayrollSettings(models.Model):
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payroll_settings',
        null=True,
        blank=True,
    )

    # الإعدادات الأساسية
    late_deduction_per_minute = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1.0,
        verbose_name='خصم التأخير (لكل دقيقة)'
    )
    absence_deduction_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=200.0,
        verbose_name='خصم الغياب (لكل يوم)'
    )
    overtime_rate_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=50.0,
        verbose_name='بدل العمل الإضافي (لكل ساعة)'
    )

    # التأمينات
    INSURANCE_MODE_CHOICES = [
        ('none', 'بدون'),
        ('fixed', 'مبلغ ثابت'),
        ('percent', 'نسبة من الأساسي'),
    ]
    insurance_mode = models.CharField(
        max_length=10,
        choices=INSURANCE_MODE_CHOICES,
        default='none',
        verbose_name='طريقة حساب التأمينات'
    )
    insurance_fixed_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0,
        verbose_name='مبلغ التأمين الثابت'
    )
    insurance_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        verbose_name='نسبة التأمين من الأساسي'
    )


    # بدل الانتقالات للموظفين الميدانيين
    FIELD_ALLOWANCE_TYPE_CHOICES = [
        ('none', 'بدون بدل انتقالات'),
        ('fixed', 'بدل ثابت شهري'),
        ('per_visit', 'بدل بالزيارة'),
    ]
    field_allowance_type = models.CharField(
        max_length=10,
        choices=FIELD_ALLOWANCE_TYPE_CHOICES,
        default='none',
        verbose_name='نوع بدل الانتقالات'
    )
    fixed_field_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name='بدل الانتقالات الثابت الشهري'
    )
    per_visit_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0,
        verbose_name='بدل الانتقالات بالزيارة'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'إعدادات الرواتب'
        verbose_name_plural = 'إعدادات الرواتب'

    def __str__(self):
        return f"PayrollSettings - {self.company}"
