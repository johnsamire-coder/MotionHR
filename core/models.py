"""
Base Models للاستخدام في كل التطبيقات
"""

from django.db import models
from django.conf import settings
from .middleware import get_current_company, get_current_user


class TenantManager(models.Manager):
    """
    Manager يفلتر البيانات أوتوماتيك حسب الشركة الحالية
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # جلب المستخدم الحالي
        user = get_current_user()
        
        # لو Super Admin يشوف كل حاجة
        if user and hasattr(user, 'role') and user.role == 'super_admin':
            return queryset
        
        # جلب الشركة الحالية
        company = get_current_company()
        
        # لو فيه شركة، فلتر عليها
        if company:
            return queryset.filter(company=company)
        
        # لو مفيش شركة، مفيش نتائج (أمان)
        return queryset.none()


class AllObjectsManager(models.Manager):
    """
    Manager بيرجع كل البيانات بدون فلترة
    للاستخدام في الحالات الخاصة
    """
    pass


class TimeStampedModel(models.Model):
    """
    Model أساسي يضيف تواريخ الإنشاء والتعديل
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تعديل'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='أنشئ بواسطة'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='آخر تعديل بواسطة'
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:  # جديد
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)


class TenantModel(TimeStampedModel):
    """
    Model أساسي لكل شيء مرتبط بشركة
    يفلتر البيانات أوتوماتيك حسب الشركة الحالية
    """
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='الشركة'
    )
    
    # Manager الأساسي - يفلتر أوتوماتيك
    objects = TenantManager()
    
    # Manager بديل - يرجع كل شيء (للحالات الخاصة)
    all_objects = AllObjectsManager()
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # لو الشركة مش محددة، خذها من المستخدم الحالي
        if not self.company_id:
            company = get_current_company()
            if company:
                self.company = company
        super().save(*args, **kwargs)


# ═════════════════════════════════════════════════════════════
# Patch 49M — Trial Signup Lead (Enhanced)
# ═════════════════════════════════════════════════════════════

class TrialSignupLead(models.Model):
    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('activated', 'تم التفعيل'),
        ('contacted', 'تم التواصل'),
        ('converted', 'تم التحويل لعميل'),
        ('expired', 'انتهت التجربة'),
        ('rejected', 'مرفوض'),
    ]

    # بيانات الشركة
    company_name = models.CharField(max_length=200, verbose_name='اسم الشركة')
    contact_name = models.CharField(max_length=200, verbose_name='اسم المسؤول')

    # بيانات التواصل
    phone = models.CharField(max_length=30, verbose_name='رقم الموبايل')
    whatsapp = models.CharField(max_length=30, verbose_name='رقم الواتساب')
    email = models.EmailField(verbose_name='البريد الإلكتروني')

    # تفاصيل إضافية
    employees_count = models.PositiveIntegerField(default=1, verbose_name='عدد الموظفين المتوقع')
    city = models.CharField(max_length=100, blank=True, verbose_name='المدينة')
    industry = models.CharField(max_length=150, blank=True, verbose_name='نوع النشاط')
    notes = models.TextField(blank=True, verbose_name='ملاحظات العميل')

    # مصدر وحالة
    source = models.CharField(max_length=100, blank=True, default='free_trial', verbose_name='مصدر التسجيل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='حالة الطلب')

    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التسجيل')
    updated_at = models.DateTimeField(auto_now=True)
    trial_start_date = models.DateField(null=True, blank=True, verbose_name='بداية التجربة')
    trial_end_date = models.DateField(null=True, blank=True, verbose_name='نهاية التجربة')

    # ربط بالحساب المنشأ
    created_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trial_leads',
        verbose_name='الشركة المنشأة',
    )
    created_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trial_leads',
        verbose_name='الحساب المنشأ',
    )
    generated_username = models.CharField(max_length=100, blank=True, verbose_name='اسم المستخدم المولّد')
    generated_password = models.CharField(max_length=100, blank=True, verbose_name='كلمة المرور المولّدة')

    # ملاحظات المبيعات
    sales_notes = models.TextField(blank=True, verbose_name='ملاحظات فريق المبيعات')

    class Meta:
        verbose_name = 'طلب تجربة مجانية'
        verbose_name_plural = 'طلبات التجربة المجانية'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} — {self.contact_name} ({self.get_status_display()})"

    @property
    def is_trial_active(self):
        if not self.trial_end_date:
            return False
        from datetime import date
        return date.today() <= self.trial_end_date

    @property
    def days_remaining(self):
        if not self.trial_end_date:
            return 0
        from datetime import date
        delta = self.trial_end_date - date.today()
        return max(0, delta.days)

