"""
MotionHR - Company Work Policy
Phase 14: مرونة أيام العمل والإجازات
"""
from datetime import date
from django.db import models
from core.models import TenantModel


def _policy_has_specific_employee(policy, employee_id):
    try:
        if not getattr(policy, "id", None) or not employee_id:
            return False

        through = policy.specific_employees.through
        source_fk = None
        employee_fk = None

        for f in through._meta.fields:
            remote_model = getattr(getattr(f, "remote_field", None), "model", None)
            if remote_model == policy.__class__:
                source_fk = f.attname
            elif getattr(getattr(remote_model, "_meta", None), "label_lower", "") == "employees.employee":
                employee_fk = f.attname

        if not source_fk or not employee_fk:
            return False

        return through._base_manager.filter(**{
            source_fk: policy.id,
            employee_fk: employee_id,
        }).exists()
    except Exception:
        return False



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
            return _policy_has_specific_employee(self, employee.id)
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
            return _policy_has_specific_employee(self, employee.id)
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
            return _policy_has_specific_employee(self, employee.id)
        return False


class CompanyInsurancePolicy(TenantModel):
    """
    سياسة تأمين - اجتماعي أو طبي
    ينطبق على الشركة كلها أو فرع أو إدارة أو موظفين محددين
    """
    INSURANCE_TYPES = [
        ('social',  'تأمين اجتماعي'),
        ('medical', 'تأمين طبي'),
    ]

    SHARE_TYPES = [
        ('percent', 'نسبة من المرتب'),
        ('fixed',   'مبلغ ثابت'),
    ]

    SCOPE_CHOICES = [
        ('company',    'الشركة كلها'),
        ('branch',     'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees',  'موظفين محددين'),
    ]

    # نوع التأمين
    insurance_type = models.CharField(
        max_length=10,
        choices=INSURANCE_TYPES,
        verbose_name='نوع التأمين',
    )
    name_ar = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=100, blank=True, default='', verbose_name='الاسم بالإنجليزي')

    # حصة الشركة
    company_share_type = models.CharField(
        max_length=10,
        choices=SHARE_TYPES,
        default='percent',
        verbose_name='نوع حصة الشركة',
    )
    company_share_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        verbose_name='قيمة حصة الشركة',
        help_text='لو نسبة اكتب رقم من 0 لـ 100، لو ثابت اكتب المبلغ',
    )

    # حصة الموظف
    employee_share_type = models.CharField(
        max_length=10,
        choices=SHARE_TYPES,
        default='percent',
        verbose_name='نوع حصة الموظف',
    )
    employee_share_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        verbose_name='قيمة حصة الموظف',
        help_text='لو نسبة اكتب رقم من 0 لـ 100، لو ثابت اكتب المبلغ',
    )

    # ═══ أساس حساب التأمين ═══
    calculation_base = models.CharField(
        max_length=20,
        choices=[
            ('basic',              'الراتب الأساسي فقط'),
            ('gross',              'الراتب الإجمالي (أساسي + بدلات)'),
            ('employee_custom',    'المرتب التأميني الخاص بالموظف'),
        ],
        default='basic',
        verbose_name='أساس حساب التأمين',
        help_text='على أي مبلغ يُحسب التأمين؟',
    )

    # حدود المرتب المؤمّن عليه (اختياري، مفيد للاجتماعي)
    min_insured_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='الحد الأدنى للمرتب المؤمّن',
    )
    max_insured_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='الحد الأقصى للمرتب المؤمّن',
    )

    # النطاق
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
        related_name='insurance_policies',
        verbose_name='الفرع',
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='insurance_policies',
        verbose_name='الإدارة',
    )
    specific_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='specific_insurance_policies',
        verbose_name='موظفين محددين',
    )

    # التفعيل
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')

    # ═══════ VERSIONING ═══════
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='next_versions',
        verbose_name='النسخة السابقة',
    )
    version_number = models.PositiveIntegerField(
        default=1,
        verbose_name='رقم النسخة',
    )
    change_reason = models.TextField(
        blank=True, default='',
        verbose_name='سبب التغيير',
        help_text='مثال: قرار وزاري رقم 12/2026 - تعديل نسبة التأمين',
    )
    is_superseded = models.BooleanField(
        default=False,
        verbose_name='تم استبدالها بنسخة أحدث',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سياسة تأمين'
        verbose_name_plural = 'سياسات التأمين'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_insurance_type_display()} - {self.name_ar} - {self.get_scope_display()}'

    def applies_to_employee(self, employee):
        """هل التأمين ده ينطبق على الموظف ده؟"""
        if not self.is_active:
            return False
        if self.scope == 'company':
            return True
        elif self.scope == 'branch':
            return getattr(employee, 'branch_id', None) == self.branch_id
        elif self.scope == 'department':
            return getattr(employee, 'department_id', None) == self.department_id
        elif self.scope == 'employees':
            return _policy_has_specific_employee(self, employee.id)
        return False

    def _resolve_base_amount(self, employee):
        """
        يحسب المبلغ الأساسي للتأمين حسب calculation_base
        Returns: Decimal
        """
        from decimal import Decimal

        basic = Decimal(str(getattr(employee, 'basic_salary', 0) or 0))

        if self.calculation_base == 'employee_custom':
            # لو الموظف عنده insurance_base_salary، نستخدمه
            # لو مافيش، نرجع للـ basic
            custom = getattr(employee, 'insurance_base_salary', None)
            if custom:
                return Decimal(str(custom))
            return basic

        elif self.calculation_base == 'gross':
            # basic + كل البدلات الفعّالة
            # للبساطة دلوقتي: basic فقط (البدلات هتضاف بعدين لما نعمل integration مع payroll engine)
            return basic

        # default = basic
        return basic

    def calculate_deduction(self, base_salary_or_employee):
        """
        يحسب حصة الشركة وحصة الموظف من التأمين
        - لو مررت employee object: هيستخدم calculation_base + insurance_base_salary
        - لو مررت رقم مباشرة: هيستخدمه كما هو (backward compatibility)
        Returns: dict { company_share, employee_share, insured_salary, calculation_base }
        """
        from decimal import Decimal

        # نحدد المصدر
        if hasattr(base_salary_or_employee, 'id'):
            # ده Employee object
            base_salary = self._resolve_base_amount(base_salary_or_employee)
            source = self.calculation_base
        else:
            # ده رقم مباشر (backward compatible)
            base_salary = Decimal(str(base_salary_or_employee or 0))
            source = 'direct'

        # تطبيق حدود المرتب المؤمّن
        insured_salary = base_salary
        if self.min_insured_salary and insured_salary < self.min_insured_salary:
            insured_salary = self.min_insured_salary
        if self.max_insured_salary and insured_salary > self.max_insured_salary:
            insured_salary = self.max_insured_salary

        # حصة الشركة
        if self.company_share_type == 'percent':
            company_share = (insured_salary * self.company_share_value) / Decimal('100')
        else:
            company_share = self.company_share_value

        # حصة الموظف
        if self.employee_share_type == 'percent':
            employee_share = (insured_salary * self.employee_share_value) / Decimal('100')
        else:
            employee_share = self.employee_share_value

        return {
            'company_share':    round(company_share, 2),
            'employee_share':   round(employee_share, 2),
            'insured_salary':   round(insured_salary, 2),
            'base_salary':      round(base_salary, 2),
            'calculation_base': source,
        }


class CompanyPayrollCyclePolicy(TenantModel):
    """
    سياسة دورة الرواتب - كل التفاصيل المتعلقة بحساب وصرف المرتبات
    """

    CYCLE_TYPES = [
        ('calendar_month',  'شهر ميلادي (1 → آخر يوم)'),
        ('custom_month',    'شهر مخصص (تحديد يوم بداية ونهاية)'),
        ('weekly',          'أسبوعي'),
        ('bi_weekly',       'كل أسبوعين'),
    ]

    HOLIDAY_HANDLING = [
        ('before',  'الصرف اليوم اللي قبله'),
        ('after',   'الصرف اليوم اللي بعده'),
        ('same',    'الصرف نفس اليوم (لو ينفع)'),
    ]

    CURRENCIES = [
        ('EGP', 'جنيه مصري'),
        ('USD', 'دولار أمريكي'),
        ('EUR', 'يورو'),
        ('SAR', 'ريال سعودي'),
        ('AED', 'درهم إماراتي'),
    ]

    PRORATION_METHODS = [
        ('30_days',       '30 يوم دائماً'),
        ('actual_days',   'أيام الشهر الفعلية'),
        ('working_days',  'أيام العمل فقط'),
    ]

    NEW_EMPLOYEE_HANDLING = [
        ('full',        'مرتب كامل من أول يوم'),
        ('prorated',    'بالنسبة والتناسب'),
        ('next_cycle',  'يبدأ من الدورة الجاية'),
    ]

    APPROVAL_LEVELS = [
        ('hr_only',                     'HR فقط'),
        ('hr_plus_manager',             'HR + المدير العام'),
        ('hr_plus_finance_plus_ceo',    'HR + مالي + مدير عام'),
    ]

    # ═══ نوع الدورة ═══
    cycle_type = models.CharField(
        max_length=20,
        choices=CYCLE_TYPES,
        default='calendar_month',
        verbose_name='نوع الدورة',
    )

    # يوم قفل الدورة (لو custom_month)
    cutoff_day = models.PositiveSmallIntegerField(
        default=25,
        verbose_name='يوم قفل الشهر',
        help_text='من 1 لـ 31',
    )

    # يوم صرف المرتبات (للشهري)
    pay_day = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='يوم صرف المرتبات',
        help_text='من 1 لـ 31',
    )

    # يوم صرف المرتبات (للأسبوعي/نصف شهري)
    weekly_pay_day = models.CharField(
        max_length=10,
        choices=[
            ('sunday',    'الأحد'),
            ('monday',    'الاثنين'),
            ('tuesday',   'الثلاثاء'),
            ('wednesday', 'الأربعاء'),
            ('thursday',  'الخميس'),
            ('friday',    'الجمعة'),
            ('saturday',  'السبت'),
        ],
        default='sunday',
        verbose_name='يوم الصرف الأسبوعي',
    )

    # ═══ معالجة عطلات الصرف ═══
    holiday_handling = models.CharField(
        max_length=10,
        choices=HOLIDAY_HANDLING,
        default='before',
        verbose_name='معالجة عطلات الصرف',
    )

    # ═══ العملة ═══
    default_currency = models.CharField(
        max_length=5,
        choices=CURRENCIES,
        default='EGP',
        verbose_name='العملة الافتراضية',
    )

    # ═══ طريقة الحساب ═══
    proration_method = models.CharField(
        max_length=20,
        choices=PRORATION_METHODS,
        default='30_days',
        verbose_name='طريقة حساب النسبة والتناسب',
    )

    working_days_per_month = models.PositiveSmallIntegerField(
        default=22,
        verbose_name='أيام العمل الشهرية',
        help_text='يُستخدم لو طريقة الحساب = أيام العمل',
    )

    # ═══ الموظف الجديد ═══
    new_employee_handling = models.CharField(
        max_length=20,
        choices=NEW_EMPLOYEE_HANDLING,
        default='prorated',
        verbose_name='معالجة الموظف الجديد',
    )

    # ═══ الإشعارات ═══
    payslip_notify_days_before = models.PositiveSmallIntegerField(
        default=2,
        verbose_name='إشعار قبل الصرف بكام يوم',
    )

    auto_generate_payroll = models.BooleanField(
        default=True,
        verbose_name='توليد Payroll تلقائي',
    )

    # ═══ الرقم المسلسل ═══
    payroll_ref_prefix = models.CharField(
        max_length=10,
        default='PR',
        verbose_name='بادئة الرقم المسلسل',
        help_text='مثال: PR → PR-2026-08',
    )

    # ═══ الموافقات ═══
    approval_level = models.CharField(
        max_length=30,
        choices=APPROVAL_LEVELS,
        default='hr_only',
        verbose_name='مستوى الموافقة',
    )

    require_approval_before_pay = models.BooleanField(
        default=True,
        verbose_name='الموافقة مطلوبة قبل الصرف',
    )

    # ═══ من يعتمد كل مستوى ═══
    # نستخدم CharField لتخزين اسم الدور (role name)
    # مثال: "hr_manager" / "company_admin" / "manager" أو اسم دور مخصص
    first_approver_role = models.CharField(
        max_length=100,
        blank=True, default='hr_manager',
        verbose_name='الموافق الأول (الدور)',
        help_text='مثال: hr_manager - أي موظف بهذا الدور يقدر يعتمد',
    )
    second_approver_role = models.CharField(
        max_length=100,
        blank=True, default='',
        verbose_name='الموافق الثاني (الدور)',
        help_text='يظهر لو مستوى الموافقة "HR + المدير"',
    )
    third_approver_role = models.CharField(
        max_length=100,
        blank=True, default='',
        verbose_name='الموافق الثالث (الدور)',
        help_text='يظهر لو مستوى الموافقة "HR + مالي + مدير عام"',
    )

    # ═══ Versioning ═══
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='next_versions',
        verbose_name='النسخة السابقة',
    )
    version_number = models.PositiveIntegerField(
        default=1,
        verbose_name='رقم النسخة',
    )
    change_reason = models.TextField(
        blank=True, default='',
        verbose_name='سبب التغيير',
    )
    is_superseded = models.BooleanField(
        default=False,
        verbose_name='تم استبدالها بنسخة أحدث',
    )

    # ═══ Metadata ═══
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سياسة دورة الرواتب'
        verbose_name_plural = 'سياسات دورة الرواتب'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_cycle_type_display()} - v{self.version_number}'


# ═══════════════════════════════════════════════════════════════
# قواعد الجزاءات / المكافآت / البدلات (Rules with Tiers)
# ═══════════════════════════════════════════════════════════════

class PenaltyRule(TenantModel):
    """
    قواعد الجزاءات — تدعم Tiers (شرائح تصاعدية)
    كل قاعدة تخص نوع واحد من الجزاءات: تأخير / غياب / خروج مبكر / عدم تسجيل خروج
    """

    PENALTY_TYPES = [
        ('late_arrival',      'تأخير الحضور'),
        ('absence',           'الغياب'),
        ('early_leave',       'الخروج المبكر'),
        ('missing_checkout',  'عدم تسجيل الخروج'),
    ]

    SCOPE_CHOICES = [
        ('company',    'الشركة كلها'),
        ('branch',     'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees',  'موظفين محددين'),
    ]

    name = models.CharField(max_length=100, verbose_name='اسم القاعدة')
    penalty_type = models.CharField(
        max_length=20, choices=PENALTY_TYPES,
        verbose_name='نوع الجزاء',
    )

    # ═══ فترة السماح ═══
    grace_amount = models.PositiveIntegerField(
        default=0,
        verbose_name='فترة السماح',
        help_text='بالدقائق لو تأخير/خروج مبكر، بالأيام لو غياب',
    )

    # ═══ الشرائح (Tiers) ═══
    # JSON structure:
    # [
    #   {"from": 1, "to": 15, "deduction_type": "fixed_per_unit", "value": 1},
    #   {"from": 16, "to": 30, "deduction_type": "fixed_per_unit", "value": 2},
    #   {"from": 31, "to": 60, "deduction_type": "quarter_day"},
    #   {"from": 61, "to": null, "deduction_type": "half_day"}
    # ]
    tiers = models.JSONField(
        default=list,
        verbose_name='الشرائح التصاعدية',
        help_text='قائمة الشرائح من الأقل للأعلى',
    )

    # ═══ العقوبات التصاعدية (اختياري) ═══
    warnings_enabled = models.BooleanField(default=False, verbose_name='تفعيل الإنذارات التصاعدية')
    first_warning_after = models.PositiveIntegerField(default=3, verbose_name='الإنذار الأول بعد كام مرة')
    second_warning_after = models.PositiveIntegerField(default=5, verbose_name='الإنذار الثاني بعد كام مرة')
    termination_after = models.PositiveIntegerField(default=10, verbose_name='الفصل بعد كام مرة')

    # ═══ Scoping ═══
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='company', verbose_name='نطاق التطبيق')
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.CASCADE,
        null=True, blank=True, related_name='penalty_rules', verbose_name='الفرع',
    )
    department = models.ForeignKey(
        'companies.Department', on_delete=models.CASCADE,
        null=True, blank=True, related_name='penalty_rules', verbose_name='الإدارة',
    )
    specific_employees = models.ManyToManyField(
        'employees.Employee', blank=True,
        related_name='specific_penalty_rules', verbose_name='موظفين محددين',
    )

    # ═══ Versioning ═══
    previous_version = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='next_versions',
        verbose_name='النسخة السابقة',
    )
    version_number = models.PositiveIntegerField(default=1, verbose_name='رقم النسخة')
    change_reason = models.TextField(blank=True, default='', verbose_name='سبب التغيير')
    is_superseded = models.BooleanField(default=False, verbose_name='تم استبدالها بنسخة أحدث')

    # ═══ Metadata ═══
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قاعدة جزاء'
        verbose_name_plural = 'قواعد الجزاءات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_penalty_type_display()} - {self.name} - v{self.version_number}'

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
            return _policy_has_specific_employee(self, employee.id)
        return False

    def calculate(self, amount, basic_salary=0, days_in_month=30):
        """
        يحسب مبلغ الخصم بناءً على الشرائح
        - amount: القيمة المدخلة (دقايق أو أيام)
        - basic_salary: للحسابات النسبية
        - days_in_month: لحساب مرتب اليوم
        """
        from decimal import Decimal

        # تطبيق فترة السماح
        effective = max(0, amount - self.grace_amount)
        if effective == 0:
            return Decimal('0'), None

        basic = Decimal(str(basic_salary or 0))
        daily = basic / Decimal(str(days_in_month))

        # نلاقي الشريحة المناسبة
        matched_tier = None
        for tier in self.tiers:
            t_from = tier.get('from', 0)
            t_to = tier.get('to')
            if effective >= t_from and (t_to is None or effective <= t_to):
                matched_tier = tier
                break

        if not matched_tier:
            return Decimal('0'), None

        dt = matched_tier.get('deduction_type', 'fixed_per_unit')
        val = Decimal(str(matched_tier.get('value', 0) or 0))

        if dt == 'fixed_per_unit':
            return effective * val, matched_tier
        elif dt == 'fixed_total':
            return val, matched_tier
        elif dt == 'percent_basic':
            return (basic * val) / Decimal('100'), matched_tier
        elif dt == 'quarter_day':
            return daily / Decimal('4'), matched_tier
        elif dt == 'half_day':
            return daily / Decimal('2'), matched_tier
        elif dt == 'full_day':
            return daily, matched_tier
        elif dt == 'two_days':
            return daily * Decimal('2'), matched_tier
        elif dt == 'three_days':
            return daily * Decimal('3'), matched_tier
        elif dt == 'day_plus_warning':
            return daily, matched_tier  # الإنذار يُسجَّل منفصل

        return Decimal('0'), matched_tier


class BonusRule(TenantModel):
    """
    قواعد المكافآت — تدعم Tiers
    كل قاعدة تخص نوع واحد: أوفرتايم / شيفت ليلي / ويكند / عيد رسمي
    """

    BONUS_TYPES = [
        ('overtime',       'الأوفرتايم'),
        ('night_shift',    'الشيفت الليلي'),
        ('weekend_work',   'العمل في الويكند'),
        ('holiday_work',   'العمل في الأعياد الرسمية'),
    ]

    SCOPE_CHOICES = [
        ('company',    'الشركة كلها'),
        ('branch',     'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees',  'موظفين محددين'),
    ]

    name = models.CharField(max_length=100, verbose_name='اسم القاعدة')
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPES, verbose_name='نوع المكافأة')

    # ═══ الشرائح ═══
    # مثال للأوفرتايم:
    # [
    #   {"from": 1, "to": 2, "value_type": "multiplier", "value": 1.5},
    #   {"from": 3, "to": 4, "value_type": "multiplier", "value": 2.0},
    #   {"from": 5, "to": null, "value_type": "multiplier", "value": 2.5}
    # ]
    tiers = models.JSONField(default=list, verbose_name='الشرائح')

    # ═══ الحدود ═══
    max_per_day = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name='الحد الأقصى في اليوم (ساعات/EGP)',
    )
    max_per_month = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name='الحد الأقصى في الشهر (ساعات/EGP)',
    )

    # ═══ إعدادات إضافية ═══
    requires_approval = models.BooleanField(default=False, verbose_name='يحتاج موافقة مسبقة')

    # ═══ Scoping ═══
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='company', verbose_name='نطاق التطبيق')
    branch = models.ForeignKey('companies.Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='bonus_rules_new', verbose_name='الفرع')
    department = models.ForeignKey('companies.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='bonus_rules_new', verbose_name='الإدارة')
    specific_employees = models.ManyToManyField('employees.Employee', blank=True, related_name='specific_bonus_rules_new', verbose_name='موظفين محددين')

    # ═══ Versioning ═══
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_versions', verbose_name='النسخة السابقة')
    version_number = models.PositiveIntegerField(default=1, verbose_name='رقم النسخة')
    change_reason = models.TextField(blank=True, default='', verbose_name='سبب التغيير')
    is_superseded = models.BooleanField(default=False, verbose_name='تم استبدالها بنسخة أحدث')

    # ═══ Metadata ═══
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قاعدة مكافأة'
        verbose_name_plural = 'قواعد المكافآت'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_bonus_type_display()} - {self.name} - v{self.version_number}'

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
            return _policy_has_specific_employee(self, employee.id)
        return False


class AllowanceRule(TenantModel):
    """
    قواعد البدلات — تدعم Tiers
    كل قاعدة تخص نوع واحد: ميدان / وجبات / مواصلات / سكن / تليفون / إلخ
    """

    ALLOWANCE_TYPES = [
        ('field_work',     'بدل الميدان'),
        ('meals',          'بدل الوجبات'),
        ('transport',      'بدل المواصلات'),
        ('housing',        'بدل السكن'),
        ('phone',          'بدل التليفون'),
        ('clothing',       'بدل الملابس'),
        ('representation', 'بدل تمثيل'),
        ('education',      'بدل تعليم'),
        ('other',          'بدل آخر'),
    ]

    SCOPE_CHOICES = [
        ('company',    'الشركة كلها'),
        ('branch',     'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees',  'موظفين محددين'),
    ]

    name = models.CharField(max_length=100, verbose_name='اسم القاعدة')
    allowance_type = models.CharField(max_length=20, choices=ALLOWANCE_TYPES, verbose_name='نوع البدل')

    # ═══ نوع الحساب + القيمة ═══
    calculation_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed_monthly',   'مبلغ شهري ثابت'),
            ('per_day',         'لكل يوم عمل'),
            ('per_visit',       'لكل زيارة'),
            ('per_km',          'لكل كيلومتر'),
            ('tiered',          'شرائح تصاعدية'),
        ],
        default='fixed_monthly',
        verbose_name='طريقة الحساب',
    )
    fixed_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='المبلغ (لو ثابت أو per_day/per_visit/per_km)',
    )

    # ═══ الشرائح (لو tiered) ═══
    # مثال:
    # [
    #   {"from": 1, "to": 10, "value": 500},   {"from": 11, "to": 20, "value": 750}, ...
    # ]
    tiers = models.JSONField(default=list, verbose_name='الشرائح (لو tiered)')

    # ═══ شروط الاستحقاق ═══
    min_work_hours_per_day = models.PositiveIntegerField(
        default=0, verbose_name='أقل ساعات عمل للاستحقاق',
    )

    # ═══ Scoping ═══
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='company', verbose_name='نطاق التطبيق')
    branch = models.ForeignKey('companies.Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='allowance_rules_new', verbose_name='الفرع')
    department = models.ForeignKey('companies.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='allowance_rules_new', verbose_name='الإدارة')
    specific_employees = models.ManyToManyField('employees.Employee', blank=True, related_name='specific_allowance_rules_new', verbose_name='موظفين محددين')

    # ═══ Versioning ═══
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_versions', verbose_name='النسخة السابقة')
    version_number = models.PositiveIntegerField(default=1, verbose_name='رقم النسخة')
    change_reason = models.TextField(blank=True, default='', verbose_name='سبب التغيير')
    is_superseded = models.BooleanField(default=False, verbose_name='تم استبدالها بنسخة أحدث')

    # ═══ Metadata ═══
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قاعدة بدل'
        verbose_name_plural = 'قواعد البدلات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_allowance_type_display()} - {self.name} - v{self.version_number}'

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
            return _policy_has_specific_employee(self, employee.id)
        return False


# ═══════════════════════════════════════════════════════════════
# قواعد الإجازات الشاملة (Leave Rules)
# ═══════════════════════════════════════════════════════════════

class LeaveRule(TenantModel):
    """
    قاعدة إجازات شاملة — تشمل كل أنواع الإجازات في قاعدة واحدة:
    - الإجازة السنوية (Annual)
    - الإجازة المرضية (Sick)
    - الإجازة الطارئة (Emergency)
    - إجازة الأمومة (Maternity)
    - إجازة الأبوة (Paternity)
    - الإجازة بدون رصيد (Unpaid)
    - الحج (Hajj)
    - الوفاة (Bereavement)
    - الزواج (Marriage)
    مع دعم Versioning و Scoping
    """

    SCOPE_CHOICES = [
        ('company',    'الشركة كلها'),
        ('branch',     'فرع محدد'),
        ('department', 'إدارة محددة'),
        ('employees',  'موظفين محددين'),
    ]

    ANNUAL_EARN_START = [
        ('immediate',       'من أول يوم'),
        ('after_probation', 'بعد فترة الاختبار'),
        ('after_year',      'بعد سنة كاملة'),
    ]

    UNPAID_DEDUCTION_TYPES = [
        ('full_day',    'يوم كامل من المرتب'),
        ('basic_only',  'من الأساسي فقط'),
        ('custom',      'مبلغ مخصص لكل يوم'),
    ]

    name = models.CharField(max_length=100, default='قواعد الإجازات الافتراضية', verbose_name='اسم القاعدة')

    # ═══════════════════════════════════════
    # 1. الإجازة السنوية (Annual Leave)
    # ═══════════════════════════════════════
    annual_leave_enabled = models.BooleanField(default=True, verbose_name='الإجازة السنوية مفعلة')
    annual_leave_days = models.PositiveSmallIntegerField(default=21, verbose_name='عدد أيام السنوية')
    annual_earn_start = models.CharField(
        max_length=20, choices=ANNUAL_EARN_START, default='after_probation',
        verbose_name='متى يبدأ الاستحقاق',
    )
    annual_carry_over = models.BooleanField(default=True, verbose_name='ترحيل الرصيد للسنة التالية')
    annual_max_carry_over = models.PositiveSmallIntegerField(default=7, verbose_name='الحد الأقصى للترحيل')
    annual_cash_out_allowed = models.BooleanField(default=False, verbose_name='صرف نقدي للرصيد المتبقي')
    annual_min_notice_days = models.PositiveSmallIntegerField(default=7, verbose_name='أقل مدة إخطار (أيام)')
    annual_max_consecutive_days = models.PositiveSmallIntegerField(default=30, verbose_name='أقصى إجازة متتالية')

    # ═══════════════════════════════════════
    # 2. الإجازة المرضية (Sick Leave)
    # ═══════════════════════════════════════
    sick_leave_enabled = models.BooleanField(default=True, verbose_name='الإجازة المرضية مفعلة')
    sick_leave_max_days = models.PositiveSmallIntegerField(default=14, verbose_name='أقصى أيام مرضي في السنة')
    sick_requires_certificate_after = models.PositiveSmallIntegerField(
        default=3, verbose_name='شهادة طبية بعد كام يوم',
    )
    sick_paid_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=75,
        verbose_name='نسبة الأجر المدفوعة (%)',
    )

    # ═══════════════════════════════════════
    # 3. الإجازة الطارئة (Emergency Leave)
    # ═══════════════════════════════════════
    emergency_leave_enabled = models.BooleanField(default=True, verbose_name='الإجازة الطارئة مفعلة')
    emergency_max_days = models.PositiveSmallIntegerField(default=3, verbose_name='أقصى أيام في السنة')
    emergency_max_per_month = models.PositiveSmallIntegerField(default=1, verbose_name='أقصى مرات في الشهر')
    emergency_min_notice_hours = models.PositiveSmallIntegerField(
        default=2, verbose_name='أقل ساعات إخطار مسبق',
    )
    emergency_requires_reason = models.BooleanField(default=True, verbose_name='السبب مطلوب')
    emergency_deducted_from_annual = models.BooleanField(
        default=False, verbose_name='تُخصم من رصيد السنوية',
    )

    # ═══════════════════════════════════════
    # 4. إجازة الأمومة (Maternity)
    # ═══════════════════════════════════════
    maternity_enabled = models.BooleanField(default=True, verbose_name='إجازة الأمومة مفعلة')
    maternity_days = models.PositiveSmallIntegerField(default=90, verbose_name='عدد الأيام')
    maternity_paid = models.BooleanField(default=True, verbose_name='مدفوعة')
    maternity_paid_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=100,
        verbose_name='نسبة الأجر (%)',
    )
    maternity_extension_days = models.PositiveSmallIntegerField(
        default=0, verbose_name='أيام تمديد (اختياري)',
    )
    maternity_max_times = models.PositiveSmallIntegerField(default=3, verbose_name='الحد الأقصى (مرات)')

    # ═══════════════════════════════════════
    # 5. إجازة الأبوة (Paternity)
    # ═══════════════════════════════════════
    paternity_enabled = models.BooleanField(default=True, verbose_name='إجازة الأبوة مفعلة')
    paternity_days = models.PositiveSmallIntegerField(default=3, verbose_name='عدد الأيام')
    paternity_paid = models.BooleanField(default=True, verbose_name='مدفوعة')

    # ═══════════════════════════════════════
    # 6. الإجازة بدون رصيد (Unpaid Leave)
    # ═══════════════════════════════════════
    unpaid_leave_enabled = models.BooleanField(default=True, verbose_name='الإجازة بدون رصيد مفعلة')
    unpaid_deduction_type = models.CharField(
        max_length=20, choices=UNPAID_DEDUCTION_TYPES, default='full_day',
        verbose_name='طريقة الحسم',
    )
    unpaid_custom_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='المبلغ المخصص لكل يوم',
    )
    max_unpaid_days_per_year = models.PositiveSmallIntegerField(
        default=30, verbose_name='أقصى أيام بدون رصيد في السنة',
    )
    unpaid_requires_approval = models.BooleanField(default=True, verbose_name='يحتاج موافقة')

    # ═══════════════════════════════════════
    # 7. الحج (Hajj)
    # ═══════════════════════════════════════
    hajj_enabled = models.BooleanField(default=True, verbose_name='إجازة الحج مفعلة')
    hajj_days = models.PositiveSmallIntegerField(default=21, verbose_name='عدد الأيام')
    hajj_paid = models.BooleanField(default=True, verbose_name='مدفوعة')
    hajj_once_in_lifetime = models.BooleanField(
        default=True, verbose_name='مرة واحدة طوال الخدمة',
    )
    hajj_min_service_years = models.PositiveSmallIntegerField(
        default=5, verbose_name='أقل سنوات خدمة للاستحقاق',
    )

    # ═══════════════════════════════════════
    # 8. الوفاة (Bereavement)
    # ═══════════════════════════════════════
    bereavement_enabled = models.BooleanField(default=True, verbose_name='إجازة الوفاة مفعلة')
    bereavement_days_first_degree = models.PositiveSmallIntegerField(
        default=3, verbose_name='أيام (درجة أولى: أب/أم/زوج/زوجة/ابن)',
    )
    bereavement_days_second_degree = models.PositiveSmallIntegerField(
        default=1, verbose_name='أيام (درجة ثانية: أخ/جد)',
    )

    # ═══════════════════════════════════════
    # 9. الزواج (Marriage)
    # ═══════════════════════════════════════
    marriage_enabled = models.BooleanField(default=True, verbose_name='إجازة الزواج مفعلة')
    marriage_days = models.PositiveSmallIntegerField(default=3, verbose_name='عدد الأيام')
    marriage_once_in_lifetime = models.BooleanField(default=True, verbose_name='مرة واحدة')

    # ═══════════════════════════════════════
    # Scoping
    # ═══════════════════════════════════════
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='company', verbose_name='نطاق التطبيق')
    branch = models.ForeignKey('companies.Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='leave_rules', verbose_name='الفرع')
    department = models.ForeignKey('companies.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='leave_rules', verbose_name='الإدارة')
    specific_employees = models.ManyToManyField('employees.Employee', blank=True, related_name='specific_leave_rules', verbose_name='موظفين محددين')

    # ═══════════════════════════════════════
    # Versioning
    # ═══════════════════════════════════════
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_versions', verbose_name='النسخة السابقة')
    version_number = models.PositiveIntegerField(default=1, verbose_name='رقم النسخة')
    change_reason = models.TextField(blank=True, default='', verbose_name='سبب التغيير')
    is_superseded = models.BooleanField(default=False, verbose_name='مستبدلة')

    # ═══════════════════════════════════════
    # Metadata
    # ═══════════════════════════════════════
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    start_date = models.DateField(verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='لحد تاريخ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قاعدة إجازات'
        verbose_name_plural = 'قواعد الإجازات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - v{self.version_number}'

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
            return _policy_has_specific_employee(self, employee.id)
        return False

