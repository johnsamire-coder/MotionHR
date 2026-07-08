from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {
            'fields': ('phone', 'role')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات إضافية', {
            'fields': ('phone', 'role', 'email', 'first_name', 'last_name')
        }),
    )