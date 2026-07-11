from django.contrib import admin
from .models import Company, Branch, Department


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name_ar', 'name_en', 'email', 'commercial_register')
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name_ar', 'name_en', 'logo', 'is_active')
        }),
        ('البيانات القانونية', {
            'fields': ('commercial_register', 'tax_number')
        }),
        ('بيانات التواصل', {
            'fields': ('email', 'phone', 'website', 'address')
        }),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'company', 'is_main', 'is_active')
    list_filter = ('company', 'is_main', 'is_active')
    search_fields = ('name_ar', 'name_en')
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('company', 'name_ar', 'name_en', 'is_main', 'is_active')
        }),
        ('بيانات التواصل', {
            'fields': ('address', 'phone')
        }),
        ('الموقع الجغرافي', {
            'fields': ('latitude', 'longitude', 'check_in_radius'),
            'description': 'الإحداثيات الخاصة بموقع الفرع لتسجيل الحضور'
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'company', 'parent', 'code', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('name_ar', 'name_en', 'code')
from .models import WorkCharter, CharterAcceptance

@admin.register(WorkCharter)
class WorkCharterAdmin(admin.ModelAdmin):
    list_display = ["company", "title", "version", "is_active", "is_mandatory"]

@admin.register(CharterAcceptance)
class CharterAcceptanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "charter", "accepted_at"]

from .models import CompanyPolicy

@admin.register(CompanyPolicy)
class CompanyPolicyAdmin(admin.ModelAdmin):
    list_display = [
        "company",
        "grace_period_minutes",
        "permission_monthly_limit",
        "overtime_enabled",
        "default_checkin_radius",
        "stealth_tracking_enabled",
        "hr_can_edit_attendance",
    ]

from .models import DepartmentHierarchy


@admin.register(DepartmentHierarchy)
class DepartmentHierarchyAdmin(admin.ModelAdmin):
    list_display = ('parent_department', 'child_department', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = (
        'parent_department__name_ar', 'parent_department__name_en',
        'child_department__name_ar', 'child_department__name_en',
    )

