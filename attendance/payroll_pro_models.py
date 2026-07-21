"""
MotionHR - Payroll Pro Models
Phase 15: نظام رواتب متكامل
"""
from django.db import models
from core.models import TenantModel


class PayrollRun(TenantModel):
    """
    تشغيل رواتب شهر كامل
    """
    STATUS_CHOICES = [
        ('draft',    'مسودة'),
        ('approved', 'معتمد'),
        ('locked',   'مقفل'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payroll_runs',
        verbose_name='الشركة',
        null=True, blank=True,
    )
    year  = models.IntegerField(verbose_name='السنة')
    month = models.IntegerField(verbose_name='الشهر')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_payrolls',
        verbose_name='معتمد من',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at   = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'تشغيل رواتب'
        verbose_name_plural = 'تشغيلات الرواتب'
        unique_together = ('company', 'year', 'month')
        ordering = ['-year', '-month']

    def __str__(self):
        return f'رواتب {self.month}/{self.year} - {self.company}'


class PayrollLine(TenantModel):
    """
    سطر راتب لكل موظف في الشهر
    """
    payroll_run = models.ForeignKey(
        PayrollRun,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name='تشغيل الرواتب',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='payroll_lines',
        verbose_name='الموظف',
    )

    # ─── الراتب الأساسي ───────────────────────────────
    basic_salary = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='الراتب الأساسي',
    )

    # ─── الاستحقاقات ──────────────────────────────────
    allowances_total  = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي البدلات')
    overtime_total    = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الأوفرتايم')
    bonuses_total     = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي المكافآت')
    gross_salary      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الاستحقاقات')

    # ─── الخصومات ─────────────────────────────────────
    late_deduction        = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='خصم التأخير')
    absence_deduction     = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='خصم الغياب')
    insurance_deduction   = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='خصم التأمينات')
    installments_total    = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الأقساط')
    penalties_total       = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الجزاءات')
    extra_deductions_total= models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='خصومات إضافية')
    total_deductions      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الخصومات')

    # ─── الصافي ───────────────────────────────────────
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='صافي الراتب')
    currency   = models.CharField(max_length=10, default='EGP', verbose_name='العملة')

    # ─── إحصاءات الحضور ───────────────────────────────
    working_days  = models.IntegerField(default=0, verbose_name='أيام العمل')
    attended_days = models.IntegerField(default=0, verbose_name='أيام الحضور')
    absent_days   = models.IntegerField(default=0, verbose_name='أيام الغياب')
    late_days     = models.IntegerField(default=0, verbose_name='أيام التأخير')
    mission_days  = models.IntegerField(default=0, verbose_name='أيام المهمات')
    on_leave_days = models.IntegerField(default=0, verbose_name='أيام الإجازة')
    late_minutes  = models.IntegerField(default=0, verbose_name='دقائق التأخير')
    overtime_hours= models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='ساعات الأوفرتايم')

    # ─── تعديل يدوي ───────────────────────────────────
    manual_adjustment = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='تعديل يدوي',
        help_text='موجب = زيادة، سالب = خصم',
    )
    manual_notes = models.TextField(blank=True, verbose_name='ملاحظات التعديل')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'سطر راتب'
        verbose_name_plural = 'سطور الرواتب'
        unique_together = ('payroll_run', 'employee')

    def __str__(self):
        return f'{self.employee} - {self.payroll_run}'


class PayrollBonus(TenantModel):
    """
    مكافآت الموظفين
    """
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='payroll_bonuses',
        verbose_name='الموظف',
    )
    name_ar = models.CharField(max_length=100, verbose_name='اسم المكافأة بالعربي')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='اسم المكافأة بالإنجليزي')
    amount  = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    month   = models.IntegerField(verbose_name='الشهر')
    year    = models.IntegerField(verbose_name='السنة')
    reason  = models.TextField(blank=True, verbose_name='السبب')
    is_visible_to_employee = models.BooleanField(default=True, verbose_name='مرئي للموظف')

    class Meta:
        verbose_name = 'مكافأة'
        verbose_name_plural = 'المكافآت'

    def __str__(self):
        return f'{self.employee} - {self.name_ar} - {self.amount}'


class PayrollPenalty(TenantModel):
    """
    جزاءات الموظفين
    """
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='payroll_penalties',
        verbose_name='الموظف',
    )
    name_ar = models.CharField(max_length=100, verbose_name='اسم الجزاء بالعربي')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='اسم الجزاء بالإنجليزي')
    amount  = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    month   = models.IntegerField(verbose_name='الشهر')
    year    = models.IntegerField(verbose_name='السنة')
    reason  = models.TextField(blank=True, verbose_name='السبب')
    is_visible_to_employee = models.BooleanField(default=True, verbose_name='مرئي للموظف')

    class Meta:
        verbose_name = 'جزاء'
        verbose_name_plural = 'الجزاءات'

    def __str__(self):
        return f'{self.employee} - {self.name_ar} - {self.amount}'


class PayrollInstallment(TenantModel):
    """
    سلف وأقساط الموظفين
    """
    STATUS_CHOICES = [
        ('active',    'نشط'),
        ('completed', 'منتهي'),
        ('cancelled', 'ملغي'),
    ]

    employee      = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='payroll_installments',
        verbose_name='الموظف',
    )
    description   = models.CharField(max_length=200, verbose_name='الوصف')
    total_amount  = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='إجمالي المبلغ')
    monthly_amount= models.DecimalField(max_digits=12, decimal_places=2, verbose_name='القسط الشهري')
    paid_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المدفوع')
    start_month   = models.IntegerField(verbose_name='شهر البدء')
    start_year    = models.IntegerField(verbose_name='سنة البدء')
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    notes         = models.TextField(blank=True)

    class Meta:
        verbose_name = 'قسط / سلفة'
        verbose_name_plural = 'الأقساط والسلف'

    def remaining_amount(self):
        return float(self.total_amount) - float(self.paid_amount)

    def __str__(self):
        return f'{self.employee} - {self.description}'
