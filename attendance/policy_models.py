from django.db import models
from django.conf import settings
import os
import uuid


def policy_upload_path(instance, filename):
    """مسار رفع ملف اللائحة"""
    ext = filename.split('.')[-1]
    new_name = f"policy_{instance.pk or uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:6]}.{ext}"
    return os.path.join('company_policies', new_name)


class CompanyPolicy(models.Model):
    """لائحة الشركة"""
    
    title = models.CharField(max_length=255, verbose_name="عنوان اللائحة")
    
    # المحتوى النصي (اختياري - لو المدير عايز يكتب مباشرة)
    content = models.TextField(blank=True, null=True, verbose_name="محتوى اللائحة")
    
    # ملف مرفق (PDF, Word, صورة, أي صيغة)
    file = models.FileField(
        upload_to=policy_upload_path,
        blank=True, null=True,
        verbose_name="ملف اللائحة"
    )
    
    # اسم الملف الأصلي
    original_filename = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="اسم الملف الأصلي"
    )
    
    # نوع الملف
    file_type = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="نوع الملف"
    )
    
    # هل اللائحة فعالة (المدير يقدر يفعل/يعطل)
    is_active = models.BooleanField(default=True, verbose_name="فعالة")
    
    # هل مطلوب موافقة الموظف
    requires_acceptance = models.BooleanField(default=True, verbose_name="تتطلب موافقة")
    
    # الإصدار
    version = models.CharField(max_length=20, default="1.0", verbose_name="الإصدار")
    
    # من رفعها
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_policies',
        verbose_name="تم إنشاؤها بواسطة"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_policy'
        ordering = ['-created_at']
        verbose_name = "لائحة الشركة"
        verbose_name_plural = "لوائح الشركة"
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def get_file_url(self):
        if self.file:
            return self.file.url
        return None


class PolicyAcceptance(models.Model):
    """موافقة الموظف على اللائحة"""
    
    policy = models.ForeignKey(
        CompanyPolicy,
        on_delete=models.CASCADE,
        related_name='acceptances',
        verbose_name="اللائحة"
    )
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='policy_acceptances',
        verbose_name="الموظف"
    )
    
    # بيانات التوقيع الإلكتروني
    accepted = models.BooleanField(default=False, verbose_name="تمت الموافقة")
    
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الموافقة")
    
    # IP الموظف وقت الموافقة (كدليل)
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    
    # معلومات الجهاز
    device_info = models.CharField(
        max_length=500, blank=True, null=True,
        verbose_name="معلومات الجهاز"
    )
    
    # نص الموافقة اللي ظهر للموظف
    acceptance_text = models.TextField(
        default="أقر بأنني قرأت واطلعت على لائحة الشركة وأوافق على جميع بنودها",
        verbose_name="نص الإقرار"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'policy_acceptance'
        unique_together = ['policy', 'employee']
        ordering = ['-accepted_at']
        verbose_name = "موافقة على اللائحة"
        verbose_name_plural = "موافقات اللوائح"
    
    def __str__(self):
        status = "✅ وافق" if self.accepted else "⏳ لم يوافق"
        return f"{self.employee.username} - {self.policy.title} - {status}"
