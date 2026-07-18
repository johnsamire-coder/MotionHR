from django.db import models
from django.conf import settings


class FCMDeviceToken(models.Model):
    """FCM Device Token لتطبيقات الموبايل (Android/iOS)"""

    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fcm_tokens',
        verbose_name='المستخدم'
    )
    fcm_token = models.TextField(
        unique=True,
        verbose_name='FCM Token'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='android',
        verbose_name='نوع الجهاز'
    )
    device_info = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='معلومات الجهاز'
    )
    preferred_language = models.CharField(
        max_length=10,
        default='ar',
        verbose_name='اللغة المفضلة'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FCM Token'
        verbose_name_plural = 'FCM Tokens'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.fcm_token[:20]}..."


class NotificationLog(models.Model):
    """سجل الإشعارات المرسلة"""

    NOTIFICATION_TYPES = [
        ('new_request', 'طلب جديد'),
        ('new_leave', 'إجازة جديدة'),
        ('request_approved', 'موافقة على طلب'),
        ('request_rejected', 'رفض طلب'),
        ('leave_approved', 'موافقة على إجازة'),
        ('leave_rejected', 'رفض إجازة'),
        ('geofence_violation', 'مخالفة نطاق'),
        ('general', 'عام'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستخدم'
    )
    title = models.CharField(max_length=200, verbose_name='العنوان')
    body = models.TextField(verbose_name='النص')
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='general',
        verbose_name='النوع'
    )
    data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات إضافية'
    )
    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
