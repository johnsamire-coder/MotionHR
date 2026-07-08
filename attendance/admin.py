from django.contrib import admin
from .models import Shift, EmployeeShift, Attendance, LocationLog, LocationCheckIn


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift_type', 'start_time', 'end_time', 'work_hours', 'is_active')
    list_filter = ('shift_type', 'is_active', 'company')
    search_fields = ('name',)
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'shift_type', 'is_active')
        }),
        ('الأوقات', {
            'fields': ('start_time', 'end_time', 'grace_period', 'break_duration')
        }),
        ('أيام العمل', {
            'fields': (
                ('work_sunday', 'work_monday', 'work_tuesday'),
                ('work_wednesday', 'work_thursday'),
                ('work_friday', 'work_saturday'),
            )
        }),
    )


@admin.register(EmployeeShift)
class EmployeeShiftAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'shift')
    search_fields = ('employee__first_name_ar', 'employee__last_name_ar')
    date_hierarchy = 'start_date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'date', 'check_in_time', 'check_out_time',
        'work_hours', 'late_minutes', 'status'
    )
    list_filter = ('status', 'date', 'is_manually_edited', 'company')
    search_fields = (
        'employee__first_name_ar', 'employee__last_name_ar',
        'employee__employee_code'
    )
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('employee', 'date', 'shift', 'status')
        }),
        ('الحضور', {
            'fields': (
                'check_in_time',
                ('check_in_latitude', 'check_in_longitude'),
                'check_in_address',
                'check_in_within_range',
                'check_in_notes',
            )
        }),
        ('الانصراف', {
            'fields': (
                'check_out_time',
                ('check_out_latitude', 'check_out_longitude'),
                'check_out_address',
                'check_out_within_range',
                'check_out_notes',
            )
        }),
        ('الحسابات', {
            'fields': ('work_hours', 'late_minutes', 'early_leave_minutes', 'overtime_hours')
        }),
        ('الإدارة', {
            'fields': ('is_manually_edited', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'timestamp', 'latitude', 'longitude', 'accuracy', 'battery_level')
    list_filter = ('timestamp', 'employee')
    search_fields = ('employee__first_name_ar', 'employee__last_name_ar')
    date_hierarchy = 'timestamp'
    readonly_fields = ('created_at',)


@admin.register(LocationCheckIn)
class LocationCheckInAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'visit_type', 'location_name',
        'arrival_time', 'departure_time', 'status'
    )
    list_filter = ('visit_type', 'status', 'arrival_time')
    search_fields = (
        'employee__first_name_ar', 'employee__last_name_ar',
        'location_name'
    )
    date_hierarchy = 'arrival_time'
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('employee', 'visit_type', 'location_name', 'status')
        }),
        ('الوصول', {
            'fields': (
                'arrival_time',
                ('arrival_latitude', 'arrival_longitude'),
                'arrival_address',
            )
        }),
        ('المغادرة', {
            'fields': (
                'departure_time',
                ('departure_latitude', 'departure_longitude'),
            )
        }),
        ('التفاصيل', {
            'fields': ('purpose', 'notes', 'photo')
        }),
    )