from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('company_admin', 'مدير الشركة'),
        ('hr_manager', 'مدير الموارد البشرية'),
        ('manager', 'مدير'),
        ('employee', 'موظف'),
    ]
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الموبايل'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee',
        verbose_name='الدور'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='users',
        verbose_name='الشركة'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='الصورة الشخصية'
    )
    
    must_change_password = models.BooleanField(
        default=False,
        verbose_name='يجب تغيير كلمة المرور'
    )

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"

class EmployeeNotification(models.Model):
    """إشعار داخلي للموظف"""

    NOTIFICATION_TYPES = [
        ("late_warning", "تحذير تأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("general_notice", "إشعار عام"),
        ("policy_reminder", "تذكير بسياسة"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("request_update", "تحديث طلب"),
    ]

    SEVERITY_CHOICES = [
        ("info", "معلومة"),
        ("warning", "تحذير"),
        ("danger", "هام"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="الموظف"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="العنوان"
    )
    message = models.TextField(
        verbose_name="الرسالة"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="general_notice",
        verbose_name="نوع الإشعار"
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default="info",
        verbose_name="الأهمية"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="تمت القراءة"
    )
    related_action = models.ForeignKey(
        "attendance.DisciplinaryAction",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="employee_notifications",
        verbose_name="الإجراء المرتبط"
    )
    sent_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sent_employee_notifications",
        verbose_name="مرسل بواسطة"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "إشعار موظف"
        verbose_name_plural = "إشعارات الموظفين"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            try:
                from accounts.views import trigger_push_for_employee_notification
                trigger_push_for_employee_notification(self)
            except Exception:
                pass


class PushSubscription(models.Model):
    """اشتراك Push Notification لكل جهاز"""

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name="المستخدم"
    )
    endpoint = models.TextField(
        verbose_name="Endpoint URL"
    )
    p256dh = models.TextField(
        verbose_name="P256DH Key"
    )
    auth = models.TextField(
        verbose_name="Auth Key"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="المتصفح"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "اشتراك Push"
        verbose_name_plural = "اشتراكات Push"
        unique_together = [["user", "endpoint"]]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."

# System Announcements
from .announcements import SystemAnnouncement, UserAnnouncementRead

# Company Announcements
from .company_announcements import CompanyAnnouncement, CompanyAnnouncementRead

# FCM Device Tokens (Mobile Push Notifications)
from .fcm_models import FCMDeviceToken
