from django.contrib import admin
from .models import JobHierarchyLevel, DepartmentJobTitleRule, Employee, JobTitle, EmployeeDocument, EmployeeMovement


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'company', 'is_active')
    list_filter = ('is_active', 'company')
    search_fields = ('name_ar', 'name_en')


class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    fields = ('document_type', 'title', 'file', 'issue_date', 'expiry_date')


class EmployeeMovementInline(admin.TabularInline):
    model = EmployeeMovement
    extra = 0
    fields = ('movement_type', 'movement_date', 'old_value', 'new_value', 'reason')
    readonly_fields = ('created_at',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_code', 'full_name_ar', 'job_title', 
        'department', 'branch', 'status', 'is_field_worker'
    )
    list_filter = (
        'status', 'contract_type', 'is_field_worker',
        'branch', 'department', 'company'
    )
    search_fields = (
        'employee_code', 'first_name_ar', 'last_name_ar',
        'first_name_en', 'last_name_en', 'national_id',
        'phone', 'email'
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                'employee_code', 'photo', 'user',
                'first_name_ar', 'middle_name_ar', 'last_name_ar',
                'first_name_en', 'last_name_en',
            )
        }),
        ('البيانات الشخصية', {
            'fields': (
                'national_id', 'birth_date', 'gender',
                'marital_status', 'religion', 'nationality',
            )
        }),
        ('بيانات التواصل', {
            'fields': ('email', 'phone', 'phone2', 'address', 'city')
        }),
        ('بيانات التعيين', {
            'fields': (
                'hire_date', 'contract_type', 'contract_end_date',
                'company', 'branch', 'department', 'job_title',
                'direct_manager', 'basic_salary',
            )
        }),
        ('التتبع الميداني', {
            'fields': ('is_field_worker',),
            'description': 'فعّل هذا الخيار للموظفين الذين يعملون خارج المكتب'
        }),
        ('البيانات البنكية', {
            'fields': ('bank_name', 'bank_account', 'iban'),
            'classes': ('collapse',)
        }),
        ('بيانات التأمينات', {
            'fields': ('has_insurance', 'insurance_number', 'insurance_date'),
            'classes': ('collapse',)
        }),
        ('جهة اتصال للطوارئ', {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_relation',
                'emergency_contact_phone'
            ),
            'classes': ('collapse',)
        }),
        ('الحالة والملاحظات', {
            'fields': (
                'status', 'termination_date',
                'termination_reason', 'notes'
            )
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [EmployeeDocumentInline, EmployeeMovementInline]


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_type', 'title', 'issue_date', 'expiry_date')
    list_filter = ('document_type',)
    search_fields = ('employee__first_name_ar', 'employee__last_name_ar', 'title')


@admin.register(EmployeeMovement)
class EmployeeMovementAdmin(admin.ModelAdmin):
    list_display = ('employee', 'movement_type', 'movement_date', 'created_at')
    list_filter = ('movement_type', 'movement_date')
    search_fields = ('employee__first_name_ar', 'employee__last_name_ar')
    date_hierarchy = 'movement_date'
from .models import Deduction

@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ["employee", "deduction_type", "amount", "date", "reason"]
    list_filter = ["deduction_type", "month", "year"]
    search_fields = ["employee__first_name_ar", "reason"]


@admin.register(JobHierarchyLevel)
class JobHierarchyLevelAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'company', 'sort_order', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('name_ar', 'name_en')
    ordering = ('company', 'sort_order', 'id')


@admin.register(DepartmentJobTitleRule)
class DepartmentJobTitleRuleAdmin(admin.ModelAdmin):
    list_display = ('department', 'job_title', 'level', 'parent_job_title', 'same_department_only', 'is_active')
    list_filter = ('company', 'department', 'level', 'same_department_only', 'is_active')
    search_fields = ('department__name_ar', 'job_title__name_ar', 'parent_job_title__name_ar')

