"""
System Announcements - إشعارات النظام العامة
لما الأدمن يعمل تحديث/ميزة جديدة، يبعت إشعار لكل المشتركين
"""
from django.db import models
from django.utils import timezone


class SystemAnnouncement(models.Model):
    """إشعار نظام عام - يذهب لكل المشتركين"""

    TYPE_CHOICES = [
        ('feature', '✨ ميزة جديدة'),
        ('update', '🔄 تحديث'),
        ('maintenance', '🔧 صيانة'),
        ('offer', '🎁 عرض خاص'),
        ('general', '📢 إعلان عام'),
        ('warning', '⚠️ تنبيه هام'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('urgent', '🚨 عاجل'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان الإشعار"
    )
    message = models.TextField(
        verbose_name="محتوى الإشعار",
        help_text="اكتب تفاصيل الإشعار بوضوح"
    )
    announcement_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='general',
        verbose_name="نوع الإشعار"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="الأولوية"
    )
    action_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="رابط الإجراء (اختياري)",
        help_text="لو فيه رابط للمزيد من التفاصيل"
    )
    action_text = models.CharField(
        max_length=50,
        blank=True,
        default="اعرف المزيد",
        verbose_name="نص الزر"
    )

    # التوقيت
    publish_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ النشر"
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="تاريخ الانتهاء (اختياري)"
    )

    # الحالة
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    send_push = models.BooleanField(
        default=True,
        verbose_name="إرسال Push Notification للموبايل"
    )
    send_to_all = models.BooleanField(
        default=True,
        verbose_name="إرسال لكل المشتركين"
    )

    # إحصائيات
    total_sent = models.IntegerField(
        default=0,
        verbose_name="عدد المرسل إليهم"
    )
    total_read = models.IntegerField(
        default=0,
        verbose_name="عدد القراءات"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="أنشئ بواسطة"
    )

    class Meta:
        verbose_name = "إشعار نظام"
        verbose_name_plural = "📢 إشعارات النظام"
        ordering = ['-publish_at', '-created_at']

    def __str__(self):
        return f"{self.get_announcement_type_display()} - {self.title}"

    def is_valid(self):
        """هل الإشعار ساري حالياً؟"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.publish_at > now:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return True


class UserAnnouncementRead(models.Model):
    """تتبع قراءة المستخدم للإشعارات"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='announcement_reads'
    )
    announcement = models.ForeignKey(
        SystemAnnouncement,
        on_delete=models.CASCADE,
        related_name='user_reads'
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'announcement']
