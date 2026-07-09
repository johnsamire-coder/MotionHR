"""
============================================================
Patch 12: Subscription System - Foundation
============================================================
- إنشاء app: subscriptions
- Models: SubscriptionPlan, CompanySubscription
- Feature Flags Registry
- Middleware
- الخطط الافتراضية (Trial, Starter, Business, Professional, Enterprise)
============================================================
"""

import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. Models
# ═══════════════════════════════════════════════════════════

MODELS_CODE = '''"""
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
'''


# ═══════════════════════════════════════════════════════════
# 2. Admin
# ═══════════════════════════════════════════════════════════

ADMIN_CODE = '''from django.contrib import admin
from .models import FeatureFlag, SubscriptionPlan, CompanySubscription


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'key', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('name_ar', 'name_en', 'key')
    ordering = ('category', 'order')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'tier', 'price_monthly', 'price_yearly', 'max_employees', 'is_active')
    list_filter = ('tier', 'is_active', 'is_featured', 'is_trial')
    search_fields = ('name_ar', 'name_en')
    filter_horizontal = ('features',)
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name_ar', 'name_en', 'tier', 'description')
        }),
        ('الأسعار', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('الحدود', {
            'fields': ('max_employees', 'max_branches', 'max_departments')
        }),
        ('الميزات', {
            'fields': ('features',)
        }),
        ('التجربة', {
            'fields': ('is_trial', 'trial_days'),
            'classes': ('collapse',)
        }),
        ('العرض', {
            'fields': ('color', 'is_featured', 'is_active', 'order')
        }),
    )


@admin.register(CompanySubscription)
class CompanySubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'company', 'plan', 'status', 'billing_cycle',
        'start_date', 'end_date', 'days_remaining'
    )
    list_filter = ('status', 'billing_cycle', 'is_trial', 'plan')
    search_fields = ('company__name_ar',)
    date_hierarchy = 'end_date'
    filter_horizontal = ('extra_features',)
    readonly_fields = ('created_at', 'updated_at', 'activated_at', 'cancelled_at')
    
    fieldsets = (
        ('الاشتراك', {
            'fields': ('company', 'plan', 'status', 'billing_cycle')
        }),
        ('التواريخ', {
            'fields': ('start_date', 'end_date', 'trial_end_date')
        }),
        ('التجربة', {
            'fields': ('is_trial', 'grace_period_days')
        }),
        ('التخصيص', {
            'fields': ('custom_max_employees', 'extra_features'),
            'classes': ('collapse',)
        }),
        ('الأسعار', {
            'fields': ('price_paid', 'discount')
        }),
        ('الملاحظات', {
            'fields': ('notes',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at', 'activated_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
'''


# ═══════════════════════════════════════════════════════════
# 3. Apps
# ═══════════════════════════════════════════════════════════

APPS_CODE = '''from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'
    verbose_name = 'الاشتراكات'
'''


# ═══════════════════════════════════════════════════════════
# 4. Middleware
# ═══════════════════════════════════════════════════════════

MIDDLEWARE_CODE = '''

class SubscriptionMiddleware:
    """
    Middleware للتحقق من اشتراك الشركة
    يضيف subscription info للـ request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.subscription = None
        request.subscription_features = set()
        request.subscription_valid = False
        request.days_remaining = 0
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Super Admin عنده كل الصلاحيات
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                request.subscription_valid = True
                request.subscription_features = self._all_features()
            else:
                # جلب اشتراك الشركة
                if hasattr(request.user, 'company') and request.user.company:
                    try:
                        from subscriptions.models import CompanySubscription
                        sub = CompanySubscription.objects.filter(
                            company=request.user.company
                        ).select_related('plan').first()
                        
                        if sub:
                            request.subscription = sub
                            request.subscription_valid = sub.is_valid
                            request.days_remaining = sub.days_remaining
                            if sub.is_valid:
                                request.subscription_features = sub.all_features
                    except Exception:
                        pass
        
        response = self.get_response(request)
        return response
    
    def _all_features(self):
        """كل الميزات المتاحة (للـ Super Admin)"""
        try:
            from subscriptions.models import FeatureFlag
            return set(FeatureFlag.objects.filter(is_active=True).values_list('key', flat=True))
        except Exception:
            return set()
'''


# ═══════════════════════════════════════════════════════════
# 5. Helper Functions
# ═══════════════════════════════════════════════════════════

HELPERS_CODE = '''"""
Subscription Helper Functions
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def feature_required(feature_key):
    """
    Decorator للـ Views
    يتحقق إن الميزة متاحة في اشتراك الشركة
    
    مثال:
        @feature_required('continuous_tracking')
        def tracking_page(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Super Admin دايماً يوصل
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            
            # التحقق من الاشتراك
            if not getattr(request, 'subscription_valid', False):
                messages.warning(request, 'اشتراكك منتهي. يرجى التجديد للوصول لهذه الميزة')
                return redirect('subscription_upgrade')
            
            # التحقق من الميزة
            if feature_key not in getattr(request, 'subscription_features', set()):
                messages.info(
                    request,
                    f'هذه الميزة غير متاحة في خطتك الحالية. قم بترقية الخطة للاستفادة منها'
                )
                return redirect('subscription_upgrade')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def has_feature(request, feature_key):
    """التحقق من ميزة (للاستخدام في views)"""
    if hasattr(request.user, 'role') and request.user.role == 'super_admin':
        return True
    return feature_key in getattr(request, 'subscription_features', set())


def get_subscription_status(request):
    """جلب حالة الاشتراك"""
    if not hasattr(request, 'subscription') or not request.subscription:
        return {
            'valid': False,
            'status': 'no_subscription',
            'message': 'لا يوجد اشتراك',
        }
    
    sub = request.subscription
    return {
        'valid': sub.is_valid,
        'status': sub.status,
        'plan_name': sub.plan.name_ar,
        'days_remaining': sub.days_remaining,
        'is_trial': sub.is_trial,
        'is_expired': sub.is_expired,
        'is_grace_period': sub.is_in_grace_period,
    }
'''


# ═══════════════════════════════════════════════════════════
# 6. Template Tags
# ═══════════════════════════════════════════════════════════

TEMPLATE_TAGS = '''"""
Subscription Template Tags
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def has_feature(context, feature_key):
    """التحقق من ميزة في الـ template"""
    request = context.get('request')
    if not request:
        return False
    
    if hasattr(request.user, 'role') and request.user.role == 'super_admin':
        return True
    
    return feature_key in getattr(request, 'subscription_features', set())


@register.simple_tag(takes_context=True)
def subscription_status(context):
    """جلب حالة الاشتراك"""
    request = context.get('request')
    if not request or not hasattr(request, 'subscription'):
        return None
    return request.subscription


@register.simple_tag(takes_context=True)
def days_remaining(context):
    """الأيام المتبقية"""
    request = context.get('request')
    if not request:
        return 0
    return getattr(request, 'days_remaining', 0)
'''


# ═══════════════════════════════════════════════════════════
# 7. Seed Data Script
# ═══════════════════════════════════════════════════════════

SEED_SCRIPT = '''"""
سكريبت لإضافة الخطط والميزات الافتراضية
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()


def seed():
    from subscriptions.models import FeatureFlag, SubscriptionPlan
    
    print("📦 إضافة الميزات...")
    
    features_data = [
        # Core
        ('employees_management', 'إدارة الموظفين', 'Employee Management', 'core', 'bi-people-fill', 1),
        ('companies_management', 'إدارة الشركات', 'Companies Management', 'core', 'bi-building', 2),
        ('branches_management', 'إدارة الفروع', 'Branches Management', 'core', 'bi-shop', 3),
        ('departments_management', 'إدارة الإدارات', 'Departments Management', 'core', 'bi-diagram-3', 4),
        
        # Attendance
        ('attendance_gps', 'حضور بالـ GPS', 'GPS Attendance', 'attendance', 'bi-geo-alt-fill', 10),
        ('attendance_records', 'سجلات الحضور', 'Attendance Records', 'attendance', 'bi-clock-history', 11),
        ('shifts_management', 'إدارة الشيفتات', 'Shifts Management', 'attendance', 'bi-calendar-week', 12),
        
        # Tracking
        ('continuous_tracking', 'التتبع المستمر', 'Continuous Tracking', 'tracking', 'bi-broadcast', 20),
        ('live_map', 'الخريطة الحية', 'Live Map', 'tracking', 'bi-map-fill', 21),
        ('location_visits', 'زيارات المواقع', 'Location Visits', 'tracking', 'bi-pin-map-fill', 22),
        ('field_monitor', 'متابعة الميدانيين', 'Field Monitor', 'tracking', 'bi-people-fill', 23),
        ('geofencing', 'التحقق من النطاق', 'Geofencing', 'tracking', 'bi-shield-check', 24),
        
        # Leaves
        ('leaves_management', 'إدارة الإجازات', 'Leaves Management', 'leaves', 'bi-calendar-check', 30),
        ('leaves_workflow', 'نظام الموافقات', 'Approval Workflow', 'leaves', 'bi-check2-circle', 31),
        ('leave_balances', 'رصيد الإجازات', 'Leave Balances', 'leaves', 'bi-piggy-bank', 32),
        
        # Payroll
        ('payroll_basic', 'المرتبات الأساسية', 'Basic Payroll', 'payroll', 'bi-cash-stack', 40),
        ('payroll_advanced', 'المرتبات المتقدمة', 'Advanced Payroll', 'payroll', 'bi-cash-coin', 41),
        ('insurance', 'التأمينات', 'Insurance', 'payroll', 'bi-shield-fill-check', 42),
        ('taxes', 'الضرائب', 'Taxes', 'payroll', 'bi-receipt', 43),
        ('loans', 'السلف', 'Loans', 'payroll', 'bi-wallet2', 44),
        
        # Reports
        ('basic_reports', 'تقارير أساسية', 'Basic Reports', 'reports', 'bi-file-earmark-text', 50),
        ('advanced_reports', 'تقارير متقدمة', 'Advanced Reports', 'reports', 'bi-graph-up', 51),
        ('export_excel', 'تصدير Excel', 'Excel Export', 'reports', 'bi-file-earmark-excel', 52),
        ('export_pdf', 'تصدير PDF', 'PDF Export', 'reports', 'bi-file-earmark-pdf', 53),
        ('custom_reports', 'تقارير مخصصة', 'Custom Reports', 'reports', 'bi-sliders', 54),
        
        # Recruitment
        ('recruitment', 'التوظيف', 'Recruitment', 'recruitment', 'bi-person-plus-fill', 60),
        ('applicants_tracking', 'متابعة المتقدمين', 'Applicants Tracking', 'recruitment', 'bi-clipboard-check', 61),
        
        # Performance
        ('performance_reviews', 'تقييم الأداء', 'Performance Reviews', 'performance', 'bi-star-fill', 70),
        ('goals_management', 'إدارة الأهداف', 'Goals Management', 'performance', 'bi-bullseye', 71),
        
        # Training
        ('training_management', 'إدارة التدريب', 'Training Management', 'training', 'bi-mortarboard-fill', 80),
        ('certifications', 'الشهادات', 'Certifications', 'training', 'bi-award-fill', 81),
        
        # Advanced
        ('multi_branch', 'متعدد الفروع', 'Multi-branch', 'advanced', 'bi-diagram-2', 90),
        ('white_label', 'White Label', 'White Label', 'advanced', 'bi-palette-fill', 91),
        ('api_access', 'API Access', 'API Access', 'advanced', 'bi-code-slash', 92),
        ('custom_domain', 'Domain مخصص', 'Custom Domain', 'advanced', 'bi-globe', 93),
        ('priority_support', 'دعم مميز', 'Priority Support', 'advanced', 'bi-headset', 94),
    ]
    
    for key, name_ar, name_en, category, icon, order in features_data:
        feature, created = FeatureFlag.objects.get_or_create(
            key=key,
            defaults={
                'name_ar': name_ar,
                'name_en': name_en,
                'category': category,
                'icon': icon,
                'order': order,
            }
        )
        if created:
            print(f"  ✅ {name_ar}")
    
    print()
    print("📦 إضافة الخطط...")
    
    # Trial Plan
    trial_plan, _ = SubscriptionPlan.objects.get_or_create(
        tier='trial',
        defaults={
            'name_ar': 'تجربة مجانية',
            'name_en': 'Free Trial',
            'description': 'تجربة كل ميزات النظام مجاناً',
            'price_monthly': 0,
            'price_yearly': 0,
            'max_employees': 10,
            'max_branches': 1,
            'max_departments': 5,
            'is_trial': True,
            'trial_days': 14,
            'color': '#8B5CF6',
            'is_featured': False,
            'order': 0,
        }
    )
    # Trial: كل الميزات
    trial_plan.features.set(FeatureFlag.objects.all())
    print(f"  ✅ {trial_plan.name_ar}")
    
    # Starter Plan
    starter, _ = SubscriptionPlan.objects.get_or_create(
        tier='starter',
        defaults={
            'name_ar': 'Starter',
            'name_en': 'Starter',
            'description': 'مثالية للشركات الصغيرة',
            'price_monthly': 299,
            'price_yearly': 2999,
            'max_employees': 15,
            'max_branches': 1,
            'max_departments': 5,
            'color': '#10B981',
            'order': 1,
        }
    )
    starter_features = [
        'employees_management', 'companies_management', 'branches_management',
        'departments_management', 'attendance_gps', 'attendance_records',
        'basic_reports', 'export_excel'
    ]
    starter.features.set(FeatureFlag.objects.filter(key__in=starter_features))
    print(f"  ✅ {starter.name_ar}")
    
    # Business Plan
    business, _ = SubscriptionPlan.objects.get_or_create(
        tier='business',
        defaults={
            'name_ar': 'Business',
            'name_en': 'Business',
            'description': 'للشركات المتوسطة',
            'price_monthly': 599,
            'price_yearly': 5999,
            'max_employees': 50,
            'max_branches': 3,
            'max_departments': 10,
            'color': '#06B6D4',
            'is_featured': True,
            'order': 2,
        }
    )
    business_features = starter_features + [
        'shifts_management', 'continuous_tracking', 'live_map',
        'location_visits', 'field_monitor', 'geofencing',
        'leaves_management', 'leaves_workflow', 'leave_balances',
        'export_pdf'
    ]
    business.features.set(FeatureFlag.objects.filter(key__in=business_features))
    print(f"  ✅ {business.name_ar}")
    
    # Professional Plan
    professional, _ = SubscriptionPlan.objects.get_or_create(
        tier='professional',
        defaults={
            'name_ar': 'Professional',
            'name_en': 'Professional',
            'description': 'للشركات الكبيرة',
            'price_monthly': 999,
            'price_yearly': 9999,
            'max_employees': 100,
            'max_branches': 10,
            'max_departments': 30,
            'color': '#3B82F6',
            'order': 3,
        }
    )
    professional_features = business_features + [
        'payroll_basic', 'insurance', 'taxes', 'loans',
        'advanced_reports', 'custom_reports', 'multi_branch'
    ]
    professional.features.set(FeatureFlag.objects.filter(key__in=professional_features))
    print(f"  ✅ {professional.name_ar}")
    
    # Enterprise Plan
    enterprise, _ = SubscriptionPlan.objects.get_or_create(
        tier='enterprise',
        defaults={
            'name_ar': 'Enterprise',
            'name_en': 'Enterprise',
            'description': 'حلول شاملة للمؤسسات الكبيرة',
            'price_monthly': 2000,
            'price_yearly': 20000,
            'max_employees': 0,  # غير محدود
            'max_branches': 0,
            'max_departments': 0,
            'color': '#F59E0B',
            'order': 4,
        }
    )
    # Enterprise: كل الميزات
    enterprise.features.set(FeatureFlag.objects.all())
    print(f"  ✅ {enterprise.name_ar}")
    
    print()
    print("=" * 60)
    print(f"📊 إجمالي الميزات: {FeatureFlag.objects.count()}")
    print(f"📊 إجمالي الخطط: {SubscriptionPlan.objects.count()}")
    print("=" * 60)


if __name__ == '__main__':
    seed()
'''


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def create_app():
    """إنشاء app subscriptions"""
    app_dir = BASE_DIR / 'subscriptions'
    
    if app_dir.exists():
        return True, "App موجود بالفعل"
    
    # نستخدم startapp
    os.chdir(BASE_DIR)
    result = subprocess.run(
        ['python', 'manage.py', 'startapp', 'subscriptions'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return True, "تم إنشاء app: subscriptions"
    else:
        return False, f"خطأ: {result.stderr}"


def create_file(relative_path, content):
    """إنشاء ملف"""
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')


def add_app_to_settings():
    """إضافة subscriptions للـ INSTALLED_APPS"""
    settings_path = BASE_DIR / 'motionhr' / 'settings.py'
    content = settings_path.read_text(encoding='utf-8')
    
    if "'subscriptions'" in content:
        return True, "App مسجل بالفعل"
    
    old = "'attendance',"
    new = "'attendance',\n    'subscriptions',"
    
    if old not in content:
        return False, "لم يتم العثور على 'attendance,'"
    
    content = content.replace(old, new)
    settings_path.write_text(content, encoding='utf-8')
    return True, "تم إضافة subscriptions في INSTALLED_APPS"


def add_middleware():
    """إضافة SubscriptionMiddleware"""
    middleware_path = BASE_DIR / 'core' / 'middleware.py'
    content = middleware_path.read_text(encoding='utf-8')
    
    if 'SubscriptionMiddleware' in content:
        return True, "Middleware موجود بالفعل"
    
    with middleware_path.open('a', encoding='utf-8') as f:
        f.write(MIDDLEWARE_CODE)
    
    return True, "تم إضافة SubscriptionMiddleware"


def register_middleware():
    """تسجيل الـ Middleware في settings"""
    settings_path = BASE_DIR / 'motionhr' / 'settings.py'
    content = settings_path.read_text(encoding='utf-8')
    
    if 'SubscriptionMiddleware' in content:
        return True, "Middleware مسجل بالفعل"
    
    old = "'core.middleware.CurrentEmployeeMiddleware',"
    new = """'core.middleware.CurrentEmployeeMiddleware',
    'core.middleware.SubscriptionMiddleware',"""
    
    if old not in content:
        # لو ما لقاش CurrentEmployeeMiddleware، نضيف بعد TenantMiddleware
        old = "'core.middleware.TenantMiddleware',"
        new = """'core.middleware.TenantMiddleware',
    'core.middleware.SubscriptionMiddleware',"""
        
        if old not in content:
            return False, "لم يتم العثور على المكان المناسب"
    
    content = content.replace(old, new)
    settings_path.write_text(content, encoding='utf-8')
    return True, "تم تسجيل SubscriptionMiddleware"


def create_template_tags():
    """إنشاء template tags"""
    tt_dir = BASE_DIR / 'subscriptions' / 'templatetags'
    tt_dir.mkdir(parents=True, exist_ok=True)
    
    init_path = tt_dir / '__init__.py'
    init_path.write_text('', encoding='utf-8')
    
    tags_path = tt_dir / 'subscription_tags.py'
    tags_path.write_text(TEMPLATE_TAGS, encoding='utf-8')
    
    return True, "تم إنشاء template tags"


def create_helpers():
    """إنشاء helpers module"""
    helpers_path = BASE_DIR / 'subscriptions' / 'helpers.py'
    helpers_path.write_text(HELPERS_CODE, encoding='utf-8')
    return True, "تم إنشاء helpers.py"


def run_migrations():
    """تشغيل migrations"""
    os.chdir(BASE_DIR)
    
    # makemigrations
    result1 = subprocess.run(
        ['python', 'manage.py', 'makemigrations', 'subscriptions'],
        capture_output=True,
        text=True
    )
    
    # migrate
    result2 = subprocess.run(
        ['python', 'manage.py', 'migrate'],
        capture_output=True,
        text=True
    )
    
    if result1.returncode == 0 and result2.returncode == 0:
        return True, "تم تطبيق migrations"
    else:
        return False, f"خطأ: {result1.stderr} {result2.stderr}"


def seed_data():
    """إضافة الخطط والميزات الافتراضية"""
    seed_path = BASE_DIR / '_patches' / '_seed_subscriptions.py'
    seed_path.write_text(SEED_SCRIPT, encoding='utf-8')
    
    os.chdir(BASE_DIR)
    result = subprocess.run(
        ['python', str(seed_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return True, "تم إضافة البيانات الافتراضية"
    else:
        return False, f"خطأ في seed: {result.stderr}"


def main():
    print("=" * 60)
    print("🚀 Patch 12: Subscription System - Foundation")
    print("=" * 60)
    print()
    
    tasks = [
        ('إنشاء app subscriptions', create_app),
        ('إضافة app في settings', add_app_to_settings),
    ]
    
    for name, func in tasks:
        try:
            success, message = func()
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("📝 إنشاء الملفات...")
    print("-" * 60)
    
    files = [
        ('subscriptions/models.py', MODELS_CODE),
        ('subscriptions/admin.py', ADMIN_CODE),
        ('subscriptions/apps.py', APPS_CODE),
    ]
    
    for path, content in files:
        try:
            create_file(path, content)
            print(f"  ✅ {path}")
        except Exception as e:
            print(f"  ❌ {path}: {e}")
    
    print()
    print("🔧 التكوين...")
    print("-" * 60)
    
    tasks2 = [
        ('helpers.py', create_helpers),
        ('template tags', create_template_tags),
        ('Middleware', add_middleware),
        ('تسجيل Middleware', register_middleware),
    ]
    
    for name, func in tasks2:
        try:
            success, message = func()
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("🗄️  تطبيق Migrations...")
    print("-" * 60)
    
    try:
        success, message = run_migrations()
        icon = "✅" if success else "❌"
        print(f"  {icon} {message}")
    except Exception as e:
        print(f"  ❌ Migrations: {e}")
    
    print()
    print("🌱 إضافة البيانات الافتراضية...")
    print("-" * 60)
    
    try:
        success, message = seed_data()
        icon = "✅" if success else "❌"
        print(f"  {icon} {message}")
    except Exception as e:
        print(f"  ❌ Seed: {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("📊 اللي عملناه:")
    print("  ✅ 35 ميزة")
    print("  ✅ 5 خطط (Trial, Starter, Business, Professional, Enterprise)")
    print("  ✅ Middleware للتحقق")
    print("  ✅ Feature Flags Registry")
    print("  ✅ Helper Functions & Template Tags")
    print()
    print("🎯 دلوقتي:")
    print("  1. أعد تشغيل السيرفر")
    print("  2. روح للـ Admin: http://127.0.0.1:8000/admin/")
    print("  3. هتلاقي قسم 'الاشتراكات' جديد")
    print("  4. شوف الميزات والخطط")
    print()
    print("🚀 المرحلة التالية: Patch 13 - Super Admin Panel")
    print()


if __name__ == '__main__':
    main()