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


# ═══════════════════════════════════════════
# 📢 System Announcements Admin
# ═══════════════════════════════════════════
from .announcements import SystemAnnouncement, UserAnnouncementRead


@admin.register(SystemAnnouncement)
class SystemAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'priority', 'is_active',
                    'publish_at', 'total_sent', 'total_read', 'send_push']
    list_filter = ['announcement_type', 'priority', 'is_active', 'send_push']
    search_fields = ['title', 'message']
    readonly_fields = ['total_sent', 'total_read', 'created_at', 'created_by']
    date_hierarchy = 'publish_at'

    fieldsets = (
        ('📢 محتوى الإشعار', {
            'fields': ('title', 'message', 'announcement_type', 'priority')
        }),
        ('🔗 الإجراء (اختياري)', {
            'fields': ('action_url', 'action_text'),
            'classes': ('collapse',)
        }),
        ('⏰ التوقيت', {
            'fields': ('publish_at', 'expires_at')
        }),
        ('⚙️ إعدادات الإرسال', {
            'fields': ('is_active', 'send_push', 'send_to_all')
        }),
        ('📊 الإحصائيات', {
            'fields': ('total_sent', 'total_read', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

        # لو الإشعار جديد ونشط، ابعت push notifications
        if not change and obj.is_active and obj.send_push:
            from .announcements_service import broadcast_announcement
            try:
                sent_count = broadcast_announcement(obj)
                obj.total_sent = sent_count
                obj.save(update_fields=['total_sent'])
                self.message_user(
                    request,
                    f"✅ تم إرسال الإشعار لـ {sent_count} مستخدم"
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"⚠️ الإشعار تم حفظه لكن حدث خطأ في الإرسال: {e}",
                    level='WARNING'
                )


@admin.register(UserAnnouncementRead)
class UserAnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ['user', 'announcement', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'announcement__title']
    readonly_fields = ['user', 'announcement', 'read_at']
