from django.db import models
from django.conf import settings
from core.models import TenantModel, TimeStampedModel


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