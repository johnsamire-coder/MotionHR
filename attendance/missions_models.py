# ============================================================
# MISSIONS MODELS - MotionHR V1
# ============================================================

from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TenantModel


class Mission(TenantModel):
    PRIORITY_CHOICES = [
        ('urgent', 'عاجل'),
        ('high', 'عالي'),
        ('normal', 'عادي'),
    ]
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending_approval', 'في انتظار الموافقة'),
        ('approved', 'معتمدة'),
        ('in_progress', 'جارية'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغية'),
    ]
    SOURCE_CHOICES = [
        ('manager', 'من المدير'),
        ('employee_request', 'طلب موظف'),
    ]

    title = models.CharField(max_length=255, verbose_name='عنوان المهمة')
    description = models.TextField(blank=True, verbose_name='تفاصيل المهمة')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    planned_start_time = models.DateTimeField(verbose_name='وقت البدء المخطط')
    planned_end_time = models.DateTimeField(verbose_name='وقت الانتهاء المخطط')
    location_name = models.CharField(max_length=500, blank=True, verbose_name='اسم الموقع')
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    client_name = models.CharField(max_length=255, blank=True, verbose_name='اسم العميل')
    client_phone = models.CharField(max_length=50, blank=True, verbose_name='تليفون العميل')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_missions'
    )
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='manager')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة'
        verbose_name_plural = 'المهمات'

    def __str__(self):
        return self.title


class MissionAssignment(TenantModel):
    ROLE_CHOICES = [
        ('lead', 'قائد المهمة'),
        ('assistant', 'مساعد'),
        ('manager', 'مدير مرافق'),
        ('trainee', 'متدرب'),
    ]
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('accepted', 'قبل'),
        ('rejected', 'رفض'),
        ('in_progress', 'جارية'),
        ('completed', 'مكتملة'),
    ]

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='mission_assignments'
    )
    role_in_mission = models.CharField(max_length=20, choices=ROLE_CHOICES, default='lead')
    is_lead = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    responded_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    start_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    start_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    end_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    end_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mission', 'employee')
        verbose_name = 'تعيين مهمة'
        verbose_name_plural = 'تعيينات المهمات'

    def __str__(self):
        return f"{self.employee} - {self.mission.title}"


class MissionLocation(models.Model):
    assignment = models.ForeignKey(
        MissionAssignment, on_delete=models.CASCADE,
        related_name='locations'
    )
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    location_label = models.CharField(max_length=255, blank=True, verbose_name='وصف الموقع')
    recorded_at = models.DateTimeField(auto_now_add=True)
    added_by_employee = models.BooleanField(default=True)

    class Meta:
        ordering = ['recorded_at']
        verbose_name = 'موقع مهمة'

    def __str__(self):
        return f"{self.assignment.employee} @ {self.recorded_at}"


class MissionAttachment(models.Model):
    assignment = models.ForeignKey(
        MissionAssignment, on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='missions/attachments/%Y/%m/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مرفق مهمة'

    def __str__(self):
        return f"مرفق - {self.assignment.mission.title}"


class MissionRequest(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'في الانتظار'),
        ('approved', 'موافق'),
        ('rejected', 'مرفوض'),
    ]

    mission = models.OneToOneField(
        Mission, on_delete=models.CASCADE,
        related_name='mission_request', null=True, blank=True
    )
    requested_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='mission_requests'
    )
    manager_approval = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mission_approvals'
    )
    manager_responded_at = models.DateTimeField(null=True, blank=True)
    manager_notes = models.TextField(blank=True)
    hr_notified_at = models.DateTimeField(null=True, blank=True)
    final_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'طلب مهمة'
        verbose_name_plural = 'طلبات المهمات'


class MissionClient(models.Model):
    mission = models.OneToOneField(
        Mission, on_delete=models.CASCADE,
        related_name='client_info'
    )
    client_name = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    actual_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'بيانات عميل المهمة'


class MissionFeedback(models.Model):
    CLIENT_STATUS = [
        ('very_interested', 'مهتم جداً'),
        ('interested', 'مهتم'),
        ('thinking', 'يفكر'),
        ('not_interested', 'غير مهتم'),
        ('postponed', 'مؤجل'),
    ]
    CONTACT_PREF = [
        ('phone', 'تليفون'),
        ('whatsapp', 'واتساب'),
        ('email', 'إيميل'),
        ('visit', 'زيارة'),
    ]

    mission = models.OneToOneField(
        Mission, on_delete=models.CASCADE,
        related_name='feedback'
    )
    written_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='written_feedbacks'
    )
    written_at = models.DateTimeField(auto_now_add=True)
    interest_rating = models.IntegerField(default=3, choices=[(i, i) for i in range(1, 6)])
    deal_probability = models.IntegerField(default=3, choices=[(i, i) for i in range(1, 6)])
    client_status = models.CharField(max_length=30, choices=CLIENT_STATUS, default='thinking')
    client_needs = models.TextField(blank=True)
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_decision_date = models.DateField(null=True, blank=True)
    interested_in = models.TextField(blank=True)
    needs_followup = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_PREF, blank=True)
    followup_owner = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_followups'
    )
    followup_notes = models.TextField(blank=True)
    contract_signed = models.BooleanField(default=False)
    deal_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    internal_notes = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فيدباك المهمة'


class MissionFeedbackAddendum(models.Model):
    feedback = models.ForeignKey(
        MissionFeedback, on_delete=models.CASCADE,
        related_name='addenda'
    )
    added_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE
    )
    note = models.TextField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ملاحظة إضافية على الفيدباك'


class MissionFollowup(models.Model):
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('scheduled', 'مجدول'),
        ('done', 'تم'),
        ('cancelled', 'ملغي'),
    ]

    original_mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE,
        related_name='followups'
    )
    followup_mission = models.ForeignKey(
        Mission, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_from_followup'
    )
    scheduled_date = models.DateField()
    assigned_to = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'متابعة مهمة'
        verbose_name_plural = 'متابعات المهمات'

