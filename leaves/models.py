"""
leaves/models.py
نظام الإجازات الكامل
"""

from django.db import models
from django.utils import timezone
from core.models import TenantModel


class LeaveType(TenantModel):
    """أنواع الإجازات"""

    LEAVE_CATEGORIES = [
        ("annual",      "إجازة سنوية"),
        ("sick",        "إجازة مرضية"),
        ("emergency",   "إجازة طارئة"),
        ("maternity",   "إجازة أمومة"),
        ("paternity",   "إجازة أبوة"),
        ("unpaid",      "إجازة بدون مرتب"),
        ("other",       "أخرى"),
    ]

    name             = models.CharField(max_length=100, verbose_name="الاسم")
    category         = models.CharField(
        max_length=20, choices=LEAVE_CATEGORIES,
        default="other", verbose_name="الفئة"
    )
    days_allowed     = models.PositiveSmallIntegerField(
        default=0, verbose_name="عدد الأيام المسموحة سنوياً",
        help_text="0 = بدون حد"
    )
    is_paid          = models.BooleanField(default=True,  verbose_name="بمرتب")
    requires_approval= models.BooleanField(default=True,  verbose_name="تحتاج موافقة")
    requires_document= models.BooleanField(default=False, verbose_name="تحتاج وثيقة")
    carry_forward    = models.BooleanField(default=False, verbose_name="ترحيل للسنة القادمة")
    max_carry_days   = models.PositiveSmallIntegerField(
        default=0, verbose_name="أقصى أيام ترحيل"
    )
    color            = models.CharField(
        max_length=7, default="#06B6D4", verbose_name="اللون"
    )
    is_active        = models.BooleanField(default=True, verbose_name="نشط")
    description      = models.TextField(blank=True, verbose_name="الوصف")

    class Meta:
        verbose_name        = "نوع إجازة"
        verbose_name_plural = "أنواع الإجازات"

    def __str__(self):
        return self.name


class LeaveBalance(TenantModel):
    """رصيد الإجازات لكل موظف"""

    employee    = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="leave_balances",
        verbose_name="الموظف"
    )
    leave_type  = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances",
        verbose_name="نوع الإجازة"
    )
    year        = models.PositiveSmallIntegerField(
        default=2025, verbose_name="السنة"
    )
    total_days  = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0, verbose_name="إجمالي الأيام"
    )
    used_days   = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0, verbose_name="الأيام المستخدمة"
    )
    pending_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0, verbose_name="الأيام قيد الانتظار"
    )

    class Meta:
        verbose_name        = "رصيد إجازة"
        verbose_name_plural = "أرصدة الإجازات"
        unique_together     = [["company", "employee", "leave_type", "year"]]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year})"

    @property
    def remaining_days(self):
        return self.total_days - self.used_days - self.pending_days

    @property
    def remaining_days_display(self):
        rem = self.remaining_days
        if rem < 0:
            return "0"
        return str(rem)


class LeaveRequest(TenantModel):
    """طلب إجازة"""

    STATUS_CHOICES = [
        ("pending",   "قيد الانتظار"),
        ("approved",  "موافق عليه"),
        ("rejected",  "مرفوض"),
        ("cancelled", "ملغي"),
    ]

    employee    = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="leave_requests",
        verbose_name="الموظف"
    )
    leave_type  = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="نوع الإجازة"
    )

    # التواريخ
    start_date  = models.DateField(verbose_name="من تاريخ")
    end_date    = models.DateField(verbose_name="إلى تاريخ")
    days_count  = models.DecimalField(
        max_digits=4, decimal_places=1,
        default=1, verbose_name="عدد الأيام"
    )

    # التفاصيل
    reason      = models.TextField(verbose_name="السبب")
    document    = models.FileField(
        upload_to="leave_documents/",
        blank=True, null=True,
        verbose_name="وثيقة مرفقة"
    )
    notes       = models.TextField(blank=True, verbose_name="ملاحظات")

    # الحالة
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default="pending", verbose_name="الحالة"
    )

    # الموافقة
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_leaves",
        verbose_name="تمت المراجعة بواسطة"
    )
    reviewed_at  = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")
    review_notes = models.TextField(blank=True, verbose_name="ملاحظات المراجع")

    class Meta:
        verbose_name        = "طلب إجازة"
        verbose_name_plural = "طلبات الإجازات"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date})"

    @property
    def status_color(self):
        colors = {
            "pending":   "warning",
            "approved":  "success",
            "rejected":  "danger",
            "cancelled": "secondary",
        }
        return colors.get(self.status, "secondary")

    @property
    def status_icon(self):
        icons = {
            "pending":   "hourglass-split",
            "approved":  "check-circle-fill",
            "rejected":  "x-circle-fill",
            "cancelled": "slash-circle",
        }
        return icons.get(self.status, "circle")

    def approve(self, user, notes=""):
        """الموافقة على الطلب"""
        self.status      = "approved"
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
        self._update_balance("approve")

    def reject(self, user, notes=""):
        """رفض الطلب"""
        self.status       = "rejected"
        self.reviewed_by  = user
        self.reviewed_at  = timezone.now()
        self.review_notes = notes
        self.save()
        self._update_balance("reject")

    def cancel(self):
        """إلغاء الطلب"""
        old_status  = self.status
        self.status = "cancelled"
        self.save()
        if old_status == "pending":
            self._update_balance("cancel_pending")
        elif old_status == "approved":
            self._update_balance("cancel_approved")

    def _update_balance(self, action):
        """تحديث رصيد الإجازات"""
        try:
            balance = LeaveBalance.objects.get(
                employee=self.employee,
                leave_type=self.leave_type,
                year=self.start_date.year,
                company=self.company,
            )
            if action == "approve":
                balance.pending_days -= self.days_count
                balance.used_days    += self.days_count
            elif action in ("reject", "cancel_pending"):
                balance.pending_days -= self.days_count
            elif action == "cancel_approved":
                balance.used_days -= self.days_count
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass
