from django.db import models
from django.conf import settings
from core.models import TenantModel, TimeStampedModel
from django_countries.fields import CountryField


class JobTitle(TenantModel):
    """المسمى الوظيفي"""
    
    name_ar = models.CharField(
        max_length=200,
        verbose_name='المسمى بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='المسمى بالإنجليزي'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='الوصف'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    class Meta:
        verbose_name = 'مسمى وظيفي'
        verbose_name_plural = 'المسميات الوظيفية'
        ordering = ['name_ar']
    
    def __str__(self):
        return self.name_ar


class Employee(TenantModel):
    """الموظف - الموديل الأساسي"""
    
    # الخيارات
    GENDER_CHOICES = [
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    ]

    LANGUAGE_CHOICES = [
        ('ar', 'العربية'),
        ('en', 'English'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'أعزب'),
        ('married', 'متزوج'),
        ('divorced', 'مطلق'),
        ('widowed', 'أرمل'),
    ]
    
    RELIGION_CHOICES = [
        ('muslim', 'مسلم'),
        ('christian', 'مسيحي'),
        ('other', 'أخرى'),
    ]
    
    CONTRACT_TYPE_CHOICES = [
        ('permanent', 'دائم'),
        ('temporary', 'مؤقت'),
        ('training', 'تدريب'),
        ('freelance', 'حر'),
        ('part_time', 'دوام جزئي'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('on_leave', 'في إجازة'),
        ('suspended', 'موقوف'),
        ('resigned', 'مستقيل'),
        ('terminated', 'مفصول'),
        ('retired', 'متقاعد'),
    ]
    
    # ربط بالمستخدم
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='employee_profile',
        verbose_name='حساب المستخدم'
    )
    
    # الرقم الوظيفي
    employee_code = models.CharField(
        max_length=20,
        blank = True,
        verbose_name='الرقم الوظيفي',
        help_text='يتم توليده تلقائياً لو تركته فارغاً'
    )
    
    # ═══════════════════════════════
    # البيانات الشخصية
    # ═══════════════════════════════
    first_name_ar = models.CharField(
        max_length=100,
        verbose_name='الاسم الأول بالعربي'
    )
    middle_name_ar = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الاسم الأوسط بالعربي'
    )
    last_name_ar = models.CharField(
        max_length=100,
        verbose_name='الاسم الأخير بالعربي'
    )
    
    first_name_en = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الاسم الأول بالإنجليزي'
    )
    last_name_en = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الاسم الأخير بالإنجليزي'
    )
    
    national_id = models.CharField(
        max_length=20,
        verbose_name='الرقم القومي'
    )
    
    birth_date = models.DateField(
        verbose_name='تاريخ الميلاد'
    )
    
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        verbose_name='النوع'
    )

    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ar',
        verbose_name='اللغة المفضلة'
    )

    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ar',
        verbose_name='اللغة المفضلة'
    )
    
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        default='single',
        verbose_name='الحالة الاجتماعية'
    )
    
    religion = models.CharField(
        max_length=20,
        choices=RELIGION_CHOICES,
        blank=True,
        null=True,
        verbose_name='الديانة'
    )
    
    nationality = models.CharField(
        max_length=100,
        default='مصري',
        verbose_name='الجنسية'
    )
    
    photo = models.ImageField(
        upload_to='employees/photos/',
        blank=True,
        null=True,
        verbose_name='الصورة الشخصية'
    )
    
    # ═══════════════════════════════
    # بيانات التواصل
    # ═══════════════════════════════
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني'
    )
    country = CountryField(blank_label='اختر الدولة', default='EG', verbose_name='الدولة')
    phone = models.CharField(
        max_length=20,
        verbose_name='رقم الموبايل'
    )
    phone2 = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم موبايل آخر'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المدينة'
    )
    
    # ═══════════════════════════════
    # بيانات التعيين
    # ═══════════════════════════════
    hire_date = models.DateField(
        verbose_name='تاريخ التعيين'
    )
    
    contract_type = models.CharField(
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        default='permanent',
        verbose_name='نوع العقد'
    )
    
    contract_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ انتهاء العقد',
        help_text='في حالة العقد المؤقت'
    )
    
    branch = models.ForeignKey(
        'companies.Branch',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='الفرع'
    )
    
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='الإدارة'
    )
    
    job_title = models.ForeignKey(
        JobTitle,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='المسمى الوظيفي'
    )
    
    direct_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='subordinates',
        verbose_name='المدير المباشر'
    )
    
    # ═══════════════════════════════
    # الراتب
    # ═══════════════════════════════
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='الراتب الأساسي'
    )

    currency = models.CharField(
        max_length=10,
        default='EGP',
        verbose_name='العملة'
    )
    
    # ═══════════════════════════════
    # البيانات البنكية
    # ═══════════════════════════════
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='اسم البنك'
    )
    bank_account = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='رقم الحساب'
    )
    iban = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='IBAN'
    )
    
    # ═══════════════════════════════
    # بيانات التأمينات
    # ═══════════════════════════════
    insurance_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الرقم التأميني'
    )
    insurance_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ التأمين'
    )
    has_insurance = models.BooleanField(
        default=False,
        verbose_name='مؤمن عليه'
    )
    
    # ═══════════════════════════════
    # جهة اتصال للطوارئ
    # ═══════════════════════════════
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم جهة الاتصال'
    )
    emergency_contact_relation = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='صلة القرابة'
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم جهة الاتصال'
    )
    
    # ═══════════════════════════════
    # الحالة
    # ═══════════════════════════════
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة'
    )
    
    termination_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ انتهاء الخدمة'
    )
    
    termination_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='سبب انتهاء الخدمة'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    
    # ═══════════════════════════════
    # ميزة التتبع الميداني
    # ═══════════════════════════════

    # ── نظام الحضور ────────────────────────────────────
    ATTENDANCE_MODES = [
        ("fixed_shift", "شيفت ثابت"),
        ("flexible_hours", "ساعات مرنة"),
        ("field_worker", "موظف ميداني"),
        ("rotating", "شيفت متناوب"),
    ]

    attendance_mode = models.CharField(
        max_length=20,
        choices=ATTENDANCE_MODES,
        default="fixed_shift",
        verbose_name="نظام الحضور"
    )
    required_daily_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=8,
        verbose_name="ساعات العمل اليومية المطلوبة"
    )


    stealth_tracking_enabled = models.BooleanField(
        default=False,
        verbose_name="التتبع الصامت مفعل"
    )

    is_field_worker = models.BooleanField(
        default=False,
        verbose_name='موظف ميداني',
        help_text='يتم تتبع موقعه أثناء العمل'
    )
    
    class Meta:
        verbose_name = 'موظف'
        verbose_name_plural = 'الموظفون'
        ordering = ['employee_code']
        unique_together = [['company', 'employee_code'], ['company', 'national_id']]
    
    def __str__(self):
        return f"{self.employee_code} - {self.full_name_ar}"
    
    @property
    def full_name_ar(self):
        """الاسم الكامل بالعربي"""
        parts = [self.first_name_ar]
        if self.middle_name_ar:
            parts.append(self.middle_name_ar)
        parts.append(self.last_name_ar)
        return ' '.join(parts)
    
    @property
    def full_name_en(self):
        """الاسم الكامل بالإنجليزي"""
        if self.first_name_en and self.last_name_en:
            return f"{self.first_name_en} {self.last_name_en}"
        return None
    
    @property
    def age(self):
        """حساب العمر"""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def years_of_service(self):
        """سنوات الخدمة"""
        from datetime import date
        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )
    
    def save(self, *args, **kwargs):
        # توليد الرقم الوظيفي أوتوماتيك لو فاضي
        if not self.employee_code:
            # جلب آخر رقم للشركة
            last_employee = Employee.all_objects.filter(
                company=self.company
            ).order_by('-id').first()
            
            if last_employee and last_employee.employee_code.startswith('EMP'):
                try:
                    last_num = int(last_employee.employee_code.replace('EMP', ''))
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.employee_code = f'EMP{new_num:05d}'
        
        super().save(*args, **kwargs)



    
    # ═══════════════════════════════
    # Hierarchical Permissions Methods
    # ═══════════════════════════════
    
    def get_all_subordinates(self):
        """
        جلب كل المرؤوسين (بشكل شجري)
        يعني الموظفين المباشرين + موظفينهم + هكذا
        """
        subordinates = list(self.subordinates.all())
        all_subs = list(subordinates)
        
        for sub in subordinates:
            all_subs.extend(sub.get_all_subordinates())
        
        return all_subs
    
    def get_all_subordinates_ids(self):
        """جلب IDs كل المرؤوسين + نفسه"""
        ids = [self.id]
        for sub in self.get_all_subordinates():
            ids.append(sub.id)
        return ids
    
    def get_manager_chain(self):
        """جلب سلسلة المديرين من فوق"""
        chain = []
        current = self.direct_manager
        while current:
            chain.append(current)
            current = current.direct_manager
        return chain
    
    def can_view_employee(self, other_employee):
        """هل يقدر يشوف بيانات موظف تاني؟"""
        # لو نفس الموظف
        if self.id == other_employee.id:
            return True
        
        # لو المدير المباشر أو من فوق
        if other_employee in self.get_all_subordinates():
            return True
        
        return False
    
    def is_manager_of(self, other_employee):
        """هل هو مدير للموظف ده؟"""
        return other_employee in self.get_all_subordinates()


class EmployeeDocument(TenantModel):
    """مستندات الموظف"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('national_id', 'صورة البطاقة'),
        ('passport', 'جواز السفر'),
        ('contract', 'العقد'),
        ('certificate', 'شهادة'),
        ('cv', 'السيرة الذاتية'),
        ('medical', 'ملف طبي'),
        ('license', 'رخصة'),
        ('insurance', 'وثيقة تأمين'),
        ('other', 'أخرى'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='الموظف'
    )
    
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name='نوع المستند'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='العنوان'
    )
    
    file = models.FileField(
        upload_to='employees/documents/',
        verbose_name='الملف'
    )
    
    issue_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ الإصدار'
    )
    
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ الانتهاء'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    
    class Meta:
        verbose_name = 'مستند'
        verbose_name_plural = 'المستندات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.title}"


class EmployeeMovement(TenantModel):
    """سجل حركة الموظف - ترقيات ونقل وتعديلات"""
    
    MOVEMENT_TYPE_CHOICES = [
        ('promotion', 'ترقية'),
        ('transfer', 'نقل'),
        ('salary_change', 'تعديل راتب'),
        ('department_change', 'تغيير إدارة'),
        ('branch_change', 'تغيير فرع'),
        ('job_title_change', 'تغيير مسمى'),
        ('contract_renewal', 'تجديد عقد'),
        ('warning', 'إنذار'),
        ('suspension', 'إيقاف'),
        ('resignation', 'استقالة'),
        ('termination', 'فصل'),
        ('return_from_leave', 'عودة من إجازة'),
        ('other', 'أخرى'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name='الموظف'
    )
    
    movement_type = models.CharField(
        max_length=30,
        choices=MOVEMENT_TYPE_CHOICES,
        verbose_name='نوع الحركة'
    )
    
    movement_date = models.DateField(
        verbose_name='تاريخ الحركة'
    )
    
    old_value = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='القيمة القديمة'
    )
    
    new_value = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='القيمة الجديدة'
    )
    
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='السبب'
    )
    
    document = models.FileField(
        upload_to='employees/movements/',
        blank=True,
        null=True,
        verbose_name='مستند مرفق'
    )
    
    class Meta:
        verbose_name = 'حركة موظف'
        verbose_name_plural = 'حركات الموظفين'
        ordering = ['-movement_date']
    
    def __str__(self):
        return f"{self.employee.full_name_ar} - {self.get_movement_type_display()} - {self.movement_date}"

class Deduction(TenantModel):
    """خصومات الموظف"""

    DEDUCTION_TYPES = [
        ("late",        "تأخير"),
        ("absence",     "غياب"),
        ("early_leave", "انصراف مبكر"),
        ("violation",   "مخالفة"),
        ("loan",        "قسط سلفة"),
        ("insurance",   "تأمينات"),
        ("tax",         "ضرائب"),
        ("penalty",     "جزاء إداري"),
        ("other",       "أخرى"),
    ]

    employee = models.ForeignKey(
        "Employee",
        on_delete=models.CASCADE,
        related_name="deductions",
        verbose_name="الموظف"
    )
    deduction_type = models.CharField(
        max_length=20,
        choices=DEDUCTION_TYPES,
        default="other",
        verbose_name="نوع الخصم"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="المبلغ"
    )
    date = models.DateField(
        verbose_name="التاريخ"
    )
    reason = models.TextField(
        verbose_name="السبب"
    )
    month = models.PositiveSmallIntegerField(
        verbose_name="الشهر"
    )
    year = models.PositiveSmallIntegerField(
        verbose_name="السنة"
    )
    is_visible_to_employee = models.BooleanField(
        default=True,
        verbose_name="ظاهر للموظف"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات إدارية"
    )

    class Meta:
        verbose_name = "خصم"
        verbose_name_plural = "الخصومات"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee} - {self.get_deduction_type_display()} - {self.amount}"


# ═════════════════════════════════════════════════════════════
# Patch 49c Revised — Job Hierarchy Models
# ═════════════════════════════════════════════════════════════

class JobHierarchyLevel(models.Model):
    """
    مستوى وظيفي معرف من الشركة:
    الرقم الأقل = مستوى أعلى
    مثال:
      1 صاحب الشركة
      2 مدير عام
      3 مدير
      4 مشرف
      5 أخصائي
      6 موظف
      7 عامل
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='job_hierarchy_levels',
        verbose_name='الشركة',
    )
    name_ar = models.CharField(max_length=150, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=150, blank=True, verbose_name='الاسم بالإنجليزي')
    sort_order = models.PositiveIntegerField(default=1, verbose_name='الترتيب الهرمي')
    description = models.TextField(blank=True, verbose_name='الوصف')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستوى وظيفي'
        verbose_name_plural = 'المستويات الوظيفية'
        ordering = ['sort_order', 'id']
        unique_together = [
            ['company', 'sort_order'],
            ['company', 'name_ar'],
        ]

    def __str__(self):
        return f"{self.sort_order} - {self.name_ar}"


class DepartmentJobTitleRule(models.Model):
    """
    ربط:
      الإدارة + المسمى الوظيفي + المستوى + المسمى الوظيفي الأب المباشر
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='department_job_title_rules',
        verbose_name='الشركة',
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        related_name='job_title_rules',
        verbose_name='الإدارة',
    )
    job_title = models.ForeignKey(
        'employees.JobTitle',
        on_delete=models.CASCADE,
        related_name='hierarchy_rules',
        verbose_name='المسمى الوظيفي',
    )
    level = models.ForeignKey(
        'employees.JobHierarchyLevel',
        on_delete=models.CASCADE,
        related_name='job_title_rules',
        verbose_name='المستوى الوظيفي',
    )
    parent_job_title = models.ForeignKey(
        'employees.JobTitle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_hierarchy_rules',
        verbose_name='المسمى الأعلى المباشر',
    )
    same_department_only = models.BooleanField(
        default=True,
        verbose_name='المدير من نفس الإدارة فقط',
    )
    allow_higher_parent_fallback = models.BooleanField(
        default=True,
        verbose_name='السماح ببدائل أعلى لو المسمى الأب غير موجود',
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قاعدة ربط وظيفي'
        verbose_name_plural = 'قواعد الربط الوظيفي'
        ordering = ['department_id', 'level__sort_order', 'job_title_id', 'id']
        unique_together = [
            ['company', 'department', 'job_title']
        ]

    def __str__(self):
        parent = self.parent_job_title.name_ar if self.parent_job_title else 'بدون'
        return f"{self.department.name_ar} | {self.job_title.name_ar} -> {parent}"


# ═════════════════════════════════════════════════════════════
# Patch 49i — Employee Document Management
# ═════════════════════════════════════════════════════════════

class EmployeeFolder(models.Model):
    """
    ملف/مستند في فولدر الموظف
    يدعم أنواع ثابتة + أنواع حرة
    """

    DOCUMENT_CATEGORIES = [
        ('id_card', 'بطاقة الهوية / الرقم القومي'),
        ('employment_contract', 'عقد التعيين'),
        ('contract_renewal', 'عقد تجديد'),
        ('contract_amendment', 'ملحق عقد / تعديل'),
        ('qualification', 'شهادة المؤهل الدراسي'),
        ('experience_cert', 'شهادة الخبرة'),
        ('personal_photo', 'صورة شخصية'),
        ('birth_cert', 'شهادة الميلاد'),
        ('criminal_record', 'فيش وتشبيه'),
        ('medical_report', 'تقرير طبي'),
        ('medical_insurance', 'بطاقة التأمين الصحي'),
        ('social_insurance', 'مستند التأمينات الاجتماعية'),
        ('promotion_letter', 'خطاب ترقية'),
        ('transfer_letter', 'خطاب نقل'),
        ('salary_adjustment', 'خطاب تعديل راتب'),
        ('warning_letter', 'إنذار'),
        ('disciplinary', 'إجراء تأديبي'),
        ('resignation', 'استقالة'),
        ('termination', 'إنهاء خدمة'),
        ('clearance', 'إخلاء طرف'),
        ('leave_request', 'طلب إجازة مرفق'),
        ('marriage_cert', 'عقد زواج'),
        ('military_cert', 'شهادة الخدمة العسكرية / الإعفاء'),
        ('driving_license', 'رخصة قيادة'),
        ('passport', 'جواز سفر'),
        ('training_cert', 'شهادة تدريب'),
        ('performance_review', 'تقييم أداء'),
        ('other', 'أخرى'),
    ]

    RELATED_EVENTS = [
        ('hiring', 'التعيين'),
        ('contract_renewal', 'تجديد العقد'),
        ('promotion', 'ترقية'),
        ('transfer', 'نقل'),
        ('salary_change', 'تعديل راتب'),
        ('leave', 'إجازة'),
        ('medical', 'حالة طبية'),
        ('warning', 'إنذار / تأديب'),
        ('resignation', 'استقالة'),
        ('termination', 'إنهاء خدمة'),
        ('training', 'تدريب'),
        ('personal', 'شخصي'),
        ('other', 'أخرى'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='employee_folder_docs',
        verbose_name='الشركة',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='folder_documents',
        verbose_name='الموظف',
    )

    # التصنيف
    category = models.CharField(
        max_length=30,
        choices=DOCUMENT_CATEGORIES,
        default='other',
        verbose_name='تصنيف المستند',
    )
    custom_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='اسم المستند (لو أخرى أو اسم مخصص)',
        help_text='يمكن ترك هذا الحقل فارغًا لو اخترت تصنيف ثابت',
    )

    # الحدث المرتبط
    related_event = models.CharField(
        max_length=30,
        choices=RELATED_EVENTS,
        blank=True,
        verbose_name='الحدث المرتبط',
    )
    event_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ الحدث',
    )
    event_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات الحدث',
    )

    # الملف
    file = models.FileField(
        upload_to='employee_folders/%Y/%m/',
        verbose_name='الملف',
    )
    file_size_kb = models.PositiveIntegerField(
        default=0,
        verbose_name='حجم الملف (KB)',
    )

    # معلومات إضافية
    issue_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ الإصدار',
    )
    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ الانتهاء',
    )
    is_confidential = models.BooleanField(
        default=False,
        verbose_name='سري',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='رفع بواسطة',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستند في ملف الموظف'
        verbose_name_plural = 'مستندات ملفات الموظفين'
        ordering = ['-created_at']

    def __str__(self):
        display_name = self.custom_name or self.get_category_display()
        emp_name = getattr(self.employee, 'full_name_ar', '') or f"#{self.employee_id}"
        return f"{emp_name} — {display_name}"

    @property
    def display_name(self):
        if self.custom_name:
            return self.custom_name
        return self.get_category_display()

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.file_size_kb = self.file.size // 1024
            except Exception:
                pass
        super().save(*args, **kwargs)

