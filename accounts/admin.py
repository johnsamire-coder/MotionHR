from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'company', 'is_active')
    list_filter = ('role', 'company', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات MotionHR', {
            'fields': ('phone', 'role', 'company', 'avatar')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات MotionHR', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'role', 'company')
        }),
    )

from .models import EmployeeNotification

@admin.register(EmployeeNotification)
class EmployeeNotificationAdmin(admin.ModelAdmin):
    list_display = ["employee", "title", "notification_type", "severity", "is_read", "created_at"]
    list_filter = ["notification_type", "severity", "is_read"]
    search_fields = ["employee__first_name_ar", "employee__employee_code", "title"]


from .models import PushSubscription

@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "created_at"]
    list_filter = ["is_active"]
