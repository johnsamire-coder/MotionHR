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