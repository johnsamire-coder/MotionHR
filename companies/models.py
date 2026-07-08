from django.db import models


class Company(models.Model):
    """الشركة الرئيسية"""
    
    name_ar = models.CharField(
        max_length=200,
        verbose_name='اسم الشركة بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الشركة بالإنجليزي'
    )
    logo = models.ImageField(
        upload_to='companies/logos/',
        blank=True,
        null=True,
        verbose_name='الشعار'
    )
    commercial_register = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='السجل التجاري'
    )
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الرقم الضريبي'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name='الموقع الإلكتروني'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تعديل'
    )
    
    class Meta:
        verbose_name = 'شركة'
        verbose_name_plural = 'الشركات'
        ordering = ['name_ar']
    
    def __str__(self):
        return self.name_ar


class Branch(models.Model):
    """فرع الشركة"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name='الشركة'
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name='اسم الفرع بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الفرع بالإنجليزي'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    # الموقع الجغرافي - مهم للتتبع بعدين
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط العرض'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط الطول'
    )
    # نطاق الحضور بالمتر
    check_in_radius = models.IntegerField(
        default=100,
        verbose_name='نطاق تسجيل الحضور (متر)'
    )
    is_main = models.BooleanField(
        default=False,
        verbose_name='الفرع الرئيسي'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'
        ordering = ['company', 'name_ar']
    
    def __str__(self):
        return f"{self.company.name_ar} - {self.name_ar}"


class Department(models.Model):
    """الإدارة أو القسم"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='الشركة'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='sub_departments',
        verbose_name='الإدارة الأم'
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name='اسم الإدارة بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الإدارة بالإنجليزي'
    )
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='كود الإدارة'
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
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'إدارة'
        verbose_name_plural = 'الإدارات'
        ordering = ['company', 'name_ar']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name_ar} → {self.name_ar}"
        return self.name_ar