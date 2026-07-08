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