"""
MotionHR - Company Work Policy
Phase 14: مرونة أيام العمل والإجازات
"""
from datetime import date
from django.db import models
from core.models import TenantModel


class CompanyWorkPolicy(TenantModel):
    """
    سياسة أيام العمل لكل شركة
    """
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='work_policy',
        verbose_name='الشركة',
    )

    # أيام العمل
    work_sunday    = models.BooleanField(default=True,  verbose_name='الأحد')
    work_monday    = models.BooleanField(default=True,  verbose_name='الاثنين')
    work_tuesday   = models.BooleanField(default=True,  verbose_name='الثلاثاء')
    work_wednesday = models.BooleanField(default=True,  verbose_name='الأربعاء')
    work_thursday  = models.BooleanField(default=True,  verbose_name='الخميس')
    work_friday    = models.BooleanField(default=False, verbose_name='الجمعة')
    work_saturday  = models.BooleanField(default=False, verbose_name='السبت')

    # نظام العمل
    is_24_7 = models.BooleanField(
        default=False,
        verbose_name='عمل 24/7',
        help_text='الإجازات بالتناوب بدون يوم ثابت'
    )

    ROTATION_CHOICES = [
        ('none',    'بدون تناوب'),
        ('weekly',  'تناوب أسبوعي'),
        ('monthly', 'تناوب شهري'),
    ]
    rotation_type = models.CharField(
        max_length=10,
        choices=ROTATION_CHOICES,
        default='none',
        verbose_name='نوع التناوب'
    )

    # إعدادات الرواتب
    late_deduction_per_minute  = models.DecimalField(
        max_digits=6, decimal_places=2,
        default=1.0,
        verbose_name='خصم التأخير / دقيقة'
    )
    absence_deduction_per_day  = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=200.0,
        verbose_name='خصم الغياب / يوم'
    )
    overtime_rate_per_hour     = models.DecimalField(
        max_digits=6, decimal_places=2,
        default=50.0,
        verbose_name='معدل Overtime / ساعة'
    )

    # إعدادات الحضور الأوتوماتيك
    auto_checkin_enabled  = models.BooleanField(
        default=False,
        verbose_name='تسجيل حضور أوتوماتيك'
    )
    auto_checkout_enabled = models.BooleanField(
        default=False,
        verbose_name='تسجيل انصراف أوتوماتيك'
    )
    auto_checkin_radius   = models.IntegerField(
        default=100,
        verbose_name='نطاق الحضور الأوتوماتيك (متر)'
    )
    auto_checkout_grace   = models.IntegerField(
        default=30,
        verbose_name='وقت السماح بعد الشيفت (دقيقة)'
    )

    class Meta:
        verbose_name = 'سياسة عمل الشركة'
        verbose_name_plural = 'سياسات عمل الشركات'

    def __str__(self):
        return f'سياسة {self.company}'

    @property
    def working_weekdays(self):
        """قائمة أرقام أيام العمل (0=الاثنين ... 6=الأحد)"""
        days = {
            0: self.work_monday,
            1: self.work_tuesday,
            2: self.work_wednesday,
            3: self.work_thursday,
            4: self.work_friday,
            5: self.work_saturday,
            6: self.work_sunday,
        }
        return [d for d, active in days.items() if active]

    @property
    def payroll_settings(self):
        return {
            'late_deduction_per_minute':  float(self.late_deduction_per_minute),
            'absence_deduction_per_day':  float(self.absence_deduction_per_day),
            'overtime_rate_per_hour':     float(self.overtime_rate_per_hour),
        }


class PayrollAllowance(TenantModel):
    """
    بدلات الموظف
    """
    ALLOWANCE_TYPES = [
        ('transport',    'بدل مواصلات'),
        ('housing',      'بدل سكن'),
        ('phone',        'بدل هاتف'),
        ('meal',         'بدل وجبة'),
        ('performance',  'علاوة أداء'),
        ('other',        'أخرى'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='allowances',
        verbose_name='الموظف'
    )
    allowance_type = models.CharField(
        max_length=20,
        choices=ALLOWANCE_TYPES,
        verbose_name='نوع البدل'
    )
    name_ar = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=100, blank=True, default='', verbose_name='الاسم بالإنجليزي')
    amount  = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='المبلغ'
    )
    is_monthly = models.BooleanField(default=True, verbose_name='شهري')
    is_active  = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(default=date.today, verbose_name='من تاريخ')
    end_date   = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')

    class Meta:
        verbose_name = 'بدل'
        verbose_name_plural = 'البدلات'

    def __str__(self):
        return f'{self.employee} - {self.name_ar} - {self.amount}'


class PayrollDeduction(TenantModel):
    """
    خصومات إضافية للموظف
    """
    DEDUCTION_TYPES = [
        ('social_insurance', 'تأمينات اجتماعية'),
        ('tax',              'ضريبة'),
        ('loan',             'سلفة'),
        ('installment',      'قسط'),
        ('penalty',          'جزاء'),
        ('other',            'أخرى'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='extra_deductions',
        verbose_name='الموظف'
    )
    deduction_type = models.CharField(
        max_length=20,
        choices=DEDUCTION_TYPES,
        verbose_name='نوع الخصم'
    )
    name_ar    = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en    = models.CharField(max_length=100, blank=True, verbose_name='الاسم بالإنجليزي')
    amount     = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='المبلغ'
    )
    is_monthly = models.BooleanField(default=True, verbose_name='شهري')
    is_active  = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date   = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    notes      = models.TextField(blank=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'خصم إضافي'
        verbose_name_plural = 'الخصومات الإضافية'

    def __str__(self):
        return f'{self.employee} - {self.name_ar} - {self.amount}'


class CompanyAllowancePolicy(TenantModel):
    """
    بدل عام - ينطبق على الشركة أو فرع أو إدارة أو موظفين محددين
    """
    ALLOWANCE_TYPES = [
        ('transport',       'بدل مواصلات'),
        ('housing',         'بدل سكن'),
        ('phone',           'بدل هاتف'),
        ('meal',            'بدل وجبة'),
        ('performance',     'علاوة أداء'),
        ('clothing',        'بدل ملابس'),
        ('risk',            'بدل مخاطر'),
        ('supervision',     'بدل إشراف'),
        ('shift_night',     'بدل وردية ليلية'),
        ('travel',          'بدل سفر'),
        ('remote_work',     'بدل عمل عن بُعد'),
        ('childcare',       'بدل رعاية أطفال'),
        ('education',       'بدل تعليم'),
        ('medical',         'بدل طبي'),
        ('social',          'بدل اجتماعي'),
        ('technical',       'بدل فني'),
        ('representation',  'بدل تمثيل'),
        ('nature_of_work',  'بدل طبيعة عمل'),
        ('overtime_fixed',  'بدل ساعات إضافية ثابت'),
        ('field',           'بدل انتقالات ميدانية'),
        ('other',           'أخرى'),
    ]

    SCOPE_CHOICES = [
        ('company',    'الشركة كلها'),
        ('branch',     'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees',  'موظفين محددين'),
    ]

    allowance_type = models.CharField(
        max_length=20,
        choices=ALLOWANCE_TYPES,
        verbose_name='نوع البدل',
    )
    name_ar = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=100, blank=True, default='', verbose_name='الاسم بالإنجليزي')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='المبلغ',
    )

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='company',
        verbose_name='نطاق التطبيق',
    )
    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='allowance_policies',
        verbose_name='الفرع',
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='allowance_policies',
        verbose_name='الإدارة',
    )
    specific_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='specific_allowance_policies',
        verbose_name='موظفين محددين',
    )

    is_monthly = models.BooleanField(default=True, verbose_name='شهري')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سياسة بدل عام'
        verbose_name_plural = 'سياسات البدلات العامة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_scope_display()} - {self.name_ar} - {self.amount}'

    def applies_to_employee(self, employee):
        """هل البدل ده ينطبق على الموظف ده؟"""
        if not self.is_active:
            return False
        if self.scope == 'company':
            return True
        elif self.scope == 'branch':
            return getattr(employee, 'branch_id', None) == self.branch_id
        elif self.scope == 'department':
            return getattr(employee, 'department_id', None) == self.department_id
        elif self.scope == 'employees':
            return self.specific_employees.filter(id=employee.id).exists()
        return False


class CompanyDeductionPolicy(TenantModel):
    """
    خصم عام - ينطبق على الشركة أو فرع أو إدارة أو موظفين محددين
    """
    DEDUCTION_TYPES = [
        ('social_insurance', 'تأمينات اجتماعية'),
        ('health_insurance', 'تأمين صحي'),
        ('tax', 'ضريبة دخل'),
        ('union_fee', 'اشتراك نقابة'),
        ('savings', 'صندوق ادخار'),
        ('parking', 'خصم انتظار سيارات'),
        ('uniform', 'خصم زي رسمي'),
        ('tools', 'خصم عهد / أدوات'),
        ('loan_recovery', 'استرداد سلفة'),
        ('other', 'أخرى'),
    ]

    SCOPE_CHOICES = [
        ('company', 'الشركة كلها'),
        ('branch', 'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees', 'موظفين محددين'),
    ]

    deduction_type = models.CharField(
        max_length=30,
        choices=DEDUCTION_TYPES,
        verbose_name='نوع الخصم',
    )
    name_ar = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=100, blank=True, default='', verbose_name='الاسم بالإنجليزي')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='المبلغ',
    )

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='company',
        verbose_name='نطاق التطبيق',
    )
    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='deduction_policies',
        verbose_name='الفرع',
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='deduction_policies',
        verbose_name='الإدارة',
    )
    specific_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='specific_deduction_policies',
        verbose_name='موظفين محددين',
    )

    is_monthly = models.BooleanField(default=True, verbose_name='شهري')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سياسة خصم عام'
        verbose_name_plural = 'سياسات الخصومات العامة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_scope_display()} - {self.name_ar} - {self.amount}'

    def applies_to_employee(self, employee):
        if not self.is_active:
            return False
        if self.scope == 'company':
            return True
        elif self.scope == 'branch':
            return getattr(employee, 'branch_id', None) == self.branch_id
        elif self.scope == 'department':
            return getattr(employee, 'department_id', None) == self.department_id
        elif self.scope == 'employees':
            return self.specific_employees.filter(id=employee.id).exists()
        return False


class CompanyBonusPolicy(TenantModel):
    """
    مكافأة / حافز عام - ينطبق على الشركة أو فرع أو إدارة أو موظفين محددين
    """
    BONUS_TYPES = [
        ('incentive', 'حافز'),
        ('eid', 'مكافأة عيد'),
        ('annual', 'مكافأة سنوية'),
        ('performance', 'مكافأة أداء'),
        ('profit_share', 'حصة أرباح'),
        ('attendance_bonus', 'مكافأة انتظام'),
        ('project_completion', 'مكافأة إتمام مشروع'),
        ('referral', 'مكافأة ترشيح'),
        ('loyalty', 'مكافأة ولاء'),
        ('ramadan', 'مكافأة رمضان'),
        ('back_to_school', 'مكافأة دخول مدارس'),
        ('marriage', 'مكافأة زواج'),
        ('newborn', 'مكافأة مولود جديد'),
        ('other', 'أخرى'),
    ]

    SCOPE_CHOICES = [
        ('company', 'الشركة كلها'),
        ('branch', 'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees', 'موظفين محددين'),
    ]

    bonus_type = models.CharField(
        max_length=30,
        choices=BONUS_TYPES,
        verbose_name='نوع المكافأة',
    )
    name_ar = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=100, blank=True, default='', verbose_name='الاسم بالإنجليزي')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='المبلغ',
    )

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='company',
        verbose_name='نطاق التطبيق',
    )
    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='bonus_policies',
        verbose_name='الفرع',
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='bonus_policies',
        verbose_name='الإدارة',
    )
    specific_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='specific_bonus_policies',
        verbose_name='موظفين محددين',
    )

    is_monthly = models.BooleanField(default=True, verbose_name='شهري')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سياسة مكافأة عامة'
        verbose_name_plural = 'سياسات المكافآت العامة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_scope_display()} - {self.name_ar} - {self.amount}'

    def applies_to_employee(self, employee):
        if not self.is_active:
            return False
        if self.scope == 'company':
            return True
        elif self.scope == 'branch':
            return getattr(employee, 'branch_id', None) == self.branch_id
        elif self.scope == 'department':
            return getattr(employee, 'department_id', None) == self.department_id
        elif self.scope == 'employees':
            return self.specific_employees.filter(id=employee.id).exists()
        return False
