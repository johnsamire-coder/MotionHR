"""
Company Announcements - إشعارات الشركة الداخلية
كل شركة تقدر تبعت إشعارات لموظفيها مع استهداف ذكي
"""
from django.db import models
from django.utils import timezone


class CompanyAnnouncement(models.Model):
    """إشعار داخلي من الشركة لموظفيها"""

    TYPE_CHOICES = [
        ('holiday', '🏖️ إجازة رسمية'),
        ('meeting', '👥 اجتماع'),
        ('event', '🎉 فعالية'),
        ('policy', '📋 سياسة جديدة'),
        ('reminder', '🔔 تذكير'),
        ('urgent', '🚨 عاجل'),
        ('general', '📢 إعلان عام'),
        ('celebration', '🎊 مناسبة'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('urgent', '🚨 عاجل'),
    ]

    TARGET_CHOICES = [
        ('all', 'كل الموظفين'),
        ('specific', 'موظفين محددين'),
        ('by_job_title', 'حسب المسمى الوظيفي'),
        ('by_department', 'حسب الإدارة'),
        ('by_branch', 'حسب الفرع'),
    ]

    # الشركة
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='company_announcements',
        verbose_name="الشركة"
    )

    # محتوى الإشعار
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان الإشعار"
    )
    message = models.TextField(
        verbose_name="محتوى الإشعار"
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

    # الاستهداف
    target_type = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default='all',
        verbose_name="نوع الاستهداف"
    )
    target_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='received_announcements',
        verbose_name="الموظفون المستهدفون"
    )
    target_job_titles = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="المسميات الوظيفية (مفصولة بفاصلة)",
        help_text="مثال: مندوب مبيعات, مدير, محاسب"
    )
    target_departments = models.ManyToManyField(
        'companies.Department',
        blank=True,
        related_name='received_announcements',
        verbose_name="الإدارات المستهدفة"
    )
    target_branches = models.ManyToManyField(
        'companies.Branch',
        blank=True,
        related_name='received_announcements',
        verbose_name="الفروع المستهدفة"
    )

    # الاستثناءات
    excluded_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='excluded_from_announcements',
        verbose_name="🚫 موظفون مستثنون"
    )
    excluded_job_titles = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="🚫 مسميات مستثناة (مفصولة بفاصلة)"
    )
    excluded_departments = models.ManyToManyField(
        'companies.Department',
        blank=True,
        related_name='excluded_from_announcements',
        verbose_name="🚫 إدارات مستثناة"
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

    # إعدادات الإرسال
    send_push = models.BooleanField(
        default=True,
        verbose_name="إرسال Push Notification"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )

    # إحصائيات
    total_sent = models.IntegerField(default=0, verbose_name="عدد المرسل إليهم")
    total_read = models.IntegerField(default=0, verbose_name="عدد القراءات")

    # التتبع
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="أنشئ بواسطة"
    )

    class Meta:
        verbose_name = "إشعار شركة"
        verbose_name_plural = "🏢 إشعارات الشركات"
        ordering = ['-publish_at', '-created_at']

    def __str__(self):
        return f"{self.get_announcement_type_display()} - {self.title}"

    def get_target_employees(self):
        """يحسب قائمة الموظفين المستهدفين بعد الاستثناءات"""
        from employees.models import Employee
        
        # ابدأ بكل موظفي الشركة النشطين
        qs = Employee.objects.filter(company=self.company)

        # حدد المستهدفين
        if self.target_type == 'specific':
            qs = qs.filter(id__in=self.target_employees.values_list('id', flat=True))
        elif self.target_type == 'by_job_title':
            titles = [t.strip() for t in self.target_job_titles.split(',') if t.strip()]
            if titles:
                qs = qs.filter(job_title__in=titles)
        elif self.target_type == 'by_department':
            qs = qs.filter(department__in=self.target_departments.all())
        elif self.target_type == 'by_branch':
            qs = qs.filter(branch__in=self.target_branches.all())

        # طبّق الاستثناءات
        excluded_ids = list(self.excluded_employees.values_list('id', flat=True))
        if excluded_ids:
            qs = qs.exclude(id__in=excluded_ids)

        excluded_titles = [t.strip() for t in self.excluded_job_titles.split(',') if t.strip()]
        if excluded_titles:
            qs = qs.exclude(job_title__in=excluded_titles)

        excluded_dept_ids = list(self.excluded_departments.values_list('id', flat=True))
        if excluded_dept_ids:
            qs = qs.exclude(department_id__in=excluded_dept_ids)

        return qs


class CompanyAnnouncementRead(models.Model):
    """تتبع قراءة الموظف للإشعارات"""
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='announcement_reads'
    )
    announcement = models.ForeignKey(
        CompanyAnnouncement,
        on_delete=models.CASCADE,
        related_name='reads'
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'announcement']
        verbose_name = "قراءة إشعار"
        verbose_name_plural = "قراءات الإشعارات"
