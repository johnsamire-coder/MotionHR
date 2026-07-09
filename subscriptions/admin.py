from django.contrib import admin
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
