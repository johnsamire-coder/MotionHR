"""
Subscription System Models
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class FeatureFlag(models.Model):
    """قائمة كل الميزات المتاحة في النظام"""
    
    CATEGORY_CHOICES = [
        ('core', 'أساسي'),
        ('attendance', 'الحضور'),
        ('tracking', 'التتبع'),
        ('leaves', 'الإجازات'),
        ('payroll', 'المرتبات'),
        ('reports', 'التقارير'),
        ('recruitment', 'التوظيف'),
        ('performance', 'الأداء'),
        ('training', 'التدريب'),
        ('advanced', 'متقدم'),
    ]
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='المفتاح',
        help_text='مثال: continuous_tracking'
    )
    name_ar = models.CharField(max_length=200, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=200, verbose_name='الاسم بالإنجليزي')
    description = models.TextField(blank=True, verbose_name='الوصف')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='core',
        verbose_name='التصنيف'
    )
    icon = models.CharField(
        max_length=50,
        default='bi-check-circle',
        verbose_name='الأيقونة'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    order = models.IntegerField(default=0, verbose_name='الترتيب')
    
    class Meta:
        verbose_name = 'ميزة'
        verbose_name_plural = 'الميزات'
        ordering = ['category', 'order', 'name_ar']
    
    def __str__(self):
        return f"{self.name_ar} ({self.key})"


class SubscriptionPlan(models.Model):
    """خطط الاشتراك"""
    
    TIER_CHOICES = [
        ('trial', 'تجربة'),
        ('starter', 'Starter'),
        ('business', 'Business'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
        ('custom', 'مخصصة'),
    ]
    
    name_ar = models.CharField(max_length=100, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=100, verbose_name='الاسم بالإنجليزي')
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='starter',
        verbose_name='المستوى'
    )
    description = models.TextField(blank=True, verbose_name='الوصف')
    
    # الأسعار
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='السعر الشهري'
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='السعر السنوي'
    )
    
    # حدود
    max_employees = models.IntegerField(
        default=15,
        verbose_name='حد الموظفين',
        help_text='0 = غير محدود'
    )
    max_branches = models.IntegerField(
        default=1,
        verbose_name='حد الفروع',
        help_text='0 = غير محدود'
    )
    max_departments = models.IntegerField(
        default=5,
        verbose_name='حد الإدارات',
        help_text='0 = غير محدود'
    )
    
    # الميزات المتاحة (Many-to-Many)
    features = models.ManyToManyField(
        FeatureFlag,
        blank=True,
        related_name='plans',
        verbose_name='الميزات المتاحة'
    )
    
    # التجربة
    is_trial = models.BooleanField(default=False, verbose_name='خطة تجريبية')
    trial_days = models.IntegerField(default=14, verbose_name='أيام التجربة')
    
    # للعرض
    color = models.CharField(
        max_length=20,
        default='#06B6D4',
        verbose_name='اللون'
    )
    is_featured = models.BooleanField(default=False, verbose_name='مميزة')
    is_active = models.BooleanField(default=True, verbose_name='نشطة')
    order = models.IntegerField(default=0, verbose_name='الترتيب')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'خطة اشتراك'
        verbose_name_plural = 'خطط الاشتراك'
        ordering = ['order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name_ar}"
    
    @property
    def yearly_discount(self):
        """نسبة الخصم في الاشتراك السنوي"""
        if self.price_monthly and self.price_yearly:
            monthly_total = self.price_monthly * 12
            if monthly_total > 0:
                discount = ((monthly_total - self.price_yearly) / monthly_total) * 100
                return round(discount, 1)
        return 0


class CompanySubscription(models.Model):
    """اشتراك الشركة"""
    
    BILLING_CYCLE_CHOICES = [
        ('trial', 'تجربة'),
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('yearly', 'سنوي'),
        ('custom', 'مخصص'),
        ('lifetime', 'مدى الحياة'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('trial', 'تجربة'),
        ('expired', 'منتهي'),
        ('cancelled', 'ملغي'),
        ('suspended', 'موقوف'),
        ('grace_period', 'فترة سماح'),
    ]
    
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='الشركة'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='الخطة'
    )
    
    # التواريخ
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(verbose_name='تاريخ الانتهاء')
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        verbose_name='الحالة'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='trial',
        verbose_name='دورة الفوترة'
    )
    
    # التجربة
    is_trial = models.BooleanField(default=False, verbose_name='تجربة')
    trial_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='نهاية التجربة'
    )
    
    # الفترة السماح
    grace_period_days = models.IntegerField(
        default=7,
        verbose_name='أيام فترة السماح'
    )
    
    # ميزات إضافية (Add-ons) - ميزات خارج الخطة
    extra_features = models.ManyToManyField(
        FeatureFlag,
        blank=True,
        related_name='extra_subscriptions',
        verbose_name='ميزات إضافية'
    )
    
    # حدود مخصصة (تتخطى حدود الخطة)
    custom_max_employees = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='حد موظفين مخصص',
        help_text='لو فارغ يستخدم حد الخطة'
    )
    
    # الأسعار الفعلية
    price_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='السعر المدفوع'
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='الخصم'
    )
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # تواريخ النظام
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'اشتراك شركة'
        verbose_name_plural = 'اشتراكات الشركات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.name_ar} - {self.plan.name_ar}"
    
    @property
    def days_remaining(self):
        """الأيام المتبقية"""
        today = timezone.now().date()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days
    
    @property
    def is_expired(self):
        """هل الاشتراك منتهي؟"""
        return self.end_date < timezone.now().date()
    
    @property
    def is_in_grace_period(self):
        """هل في فترة سماح؟"""
        if not self.is_expired:
            return False
        today = timezone.now().date()
        grace_end = self.end_date + timedelta(days=self.grace_period_days)
        return today <= grace_end
    
    @property
    def is_valid(self):
        """هل الاشتراك ساري؟"""
        return not self.is_expired or self.is_in_grace_period
    
    @property
    def max_employees(self):
        """حد الموظفين الفعلي"""
        if self.custom_max_employees is not None:
            return self.custom_max_employees
        return self.plan.max_employees
    
    @property
    def all_features(self):
        """كل الميزات المتاحة (خطة + إضافية)"""
        plan_features = set(self.plan.features.values_list('key', flat=True))
        extra_features = set(self.extra_features.values_list('key', flat=True))
        return plan_features | extra_features
    
    def has_feature(self, feature_key):
        """هل الميزة متاحة؟"""
        return feature_key in self.all_features
    
    def get_status_display_ar(self):
        """عرض الحالة بشكل جميل"""
        if self.is_trial and self.status == 'trial':
            return f"تجربة ({self.days_remaining} يوم متبقي)"
        return self.get_status_display()
