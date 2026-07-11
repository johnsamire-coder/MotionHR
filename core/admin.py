from django.contrib import admin
from .models import TrialSignupLead
from django.contrib import admin

# Register your models here.


@admin.register(TrialSignupLead)
class TrialSignupLeadAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'contact_name', 'phone', 'whatsapp', 'email',
        'employees_count', 'status', 'trial_start_date', 'trial_end_date',
        'is_trial_active', 'days_remaining', 'created_at',
    )
    list_filter = ('status', 'industry', 'created_at', 'trial_end_date')
    search_fields = ('company_name', 'contact_name', 'phone', 'whatsapp', 'email')
    ordering = ('-created_at',)
    readonly_fields = (
        'generated_username', 'generated_password',
        'created_company', 'created_user',
        'trial_start_date', 'trial_end_date',
        'created_at', 'updated_at',
    )

    fieldsets = (
        ('بيانات العميل', {
            'fields': ('company_name', 'contact_name', 'phone', 'whatsapp', 'email',
                       'employees_count', 'city', 'industry', 'notes'),
        }),
        ('حالة الطلب', {
            'fields': ('status', 'source', 'sales_notes'),
        }),
        ('بيانات التجربة', {
            'fields': ('trial_start_date', 'trial_end_date',
                       'created_company', 'created_user',
                       'generated_username', 'generated_password'),
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def is_trial_active(self, obj):
        return obj.is_trial_active
    is_trial_active.boolean = True
    is_trial_active.short_description = 'التجربة فعّالة؟'

    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'أيام متبقية'

