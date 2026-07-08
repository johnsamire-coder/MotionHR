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