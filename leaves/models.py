"""
leaves/models.py
نظام الإجازات الكامل
"""

from django.db import models
from django.utils import timezone
from core.models import TenantModel



class LeavePolicy(TenantModel):
    """سياسة الإجازات للشركة"""

    ACCRUAL_MODE_CHOICES = [
        ("annual_lump", "دفعة واحدة أول السنة"),
        ("monthly", "شهري"),
    ]

    STATUS_CHOICES = [
        ("draft", "مسودة"),
        ("active", "نشط"),
        ("archived", "مؤرشف"),
    ]

    name = models.CharField(max_length=200, verbose_name="اسم السياسة")
    effective_from = models.DateField(verbose_name="سارية من")
    effective_to = models.DateField(blank=True, null=True, verbose_name="سارية لحد")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default="draft", verbose_name="الحالة"
    )
    probation_months = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="فترة التجربة بالشهور",
        help_text="0 = لا توجد فترة تجربة"
    )
    probation_leave_mode = models.CharField(
        max_length=20,
        choices=[
            ("blocked", "ممنوع الإجازات"),
            ("limited_types", "أنواع محددة فقط"),
            ("accrue_no_use", "يتحسب بس مايتستخدمش"),
            ("normal", "عادي"),
        ],
        default="blocked",
        verbose_name="الإجازات في فترة التجربة"
    )
    accrual_mode = models.CharField(
        max_length=20, choices=ACCRUAL_MODE_CHOICES,
        default="annual_lump",
        verbose_name="طريقة منح الرصيد"
    )
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_leave_policies",
        verbose_name="وافق بواسطة"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "سياسة إجازات"
        verbose_name_plural = "سياسات الإجازات"
        ordering = ["-effective_from"]

    def __str__(self):
        return f"{self.name} ({self.effective_from})"


class LeavePolicyTier(models.Model):
    """شريحة مدة الخدمة"""

    policy = models.ForeignKey(
        LeavePolicy, on_delete=models.CASCADE,
        related_name="tiers", verbose_name="السياسة"
    )
    from_months = models.PositiveSmallIntegerField(
        default=0, verbose_name="من الشهر"
    )
    to_months = models.PositiveSmallIntegerField(
        blank=True, null=True,
        verbose_name="لحد الشهر",
        help_text="فاضي = بلا حد أقصى"
    )
    annual_entitlement_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=21, verbose_name="الاستحقاق السنوي بالأيام"
    )
    description = models.TextField(blank=True, verbose_name="وصف الشريحة")

    class Meta:
        verbose_name = "شريحة خدمة"
        verbose_name_plural = "شرائح الخدمة"
        ordering = ["from_months"]

    def __str__(self):
        to = f"{self.to_months}" if self.to_months else "فأكثر"
        return f"{self.policy.name}: {self.from_months}-{to} شهر = {self.annual_entitlement_days} يوم"


class LeavePolicyTypeRule(models.Model):
    """قواعد كل نوع إجازة في السياسة"""

    CARRY_MODE_CHOICES = [
        ("none", "لا ترحيل"),
        ("all", "ترحيل كامل"),
        ("percentage", "نسبة فقط"),
        ("percentage_with_cap", "نسبة بحد أقصى"),
        ("cash_only", "مقابل نقدي بدون ترحيل"),
        ("carry_and_cash_remainder", "جزء يترحل والباقي فلوس"),
    ]

    CASH_BASIS_CHOICES = [
        ("basic_salary", "المرتب الأساسي"),
        ("gross_fixed", "الأساسي + البدلات الثابتة"),
        ("daily_rate", "المعدل اليومي"),
    ]

    ENTITLEMENT_MODE_CHOICES = [
        ("from_service_tier", "من شريحة مدة الخدمة"),
        ("fixed_days", "عدد ثابت"),
        ("subset_of_parent", "جزء من نوع تاني"),
    ]

    policy = models.ForeignKey(
        LeavePolicy, on_delete=models.CASCADE,
        related_name="type_rules", verbose_name="السياسة"
    )
    leave_type = models.ForeignKey(
        "LeaveType", on_delete=models.CASCADE,
        related_name="policy_rules", verbose_name="نوع الإجازة"
    )
    enabled = models.BooleanField(default=True, verbose_name="مفعّل")

    # مصدر الرصيد
    entitlement_mode = models.CharField(
        max_length=20, choices=ENTITLEMENT_MODE_CHOICES,
        default="from_service_tier",
        verbose_name="مصدر الرصيد"
    )
    fixed_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0, verbose_name="عدد أيام ثابت"
    )
    parent_leave_type = models.ForeignKey(
        "LeaveType", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="child_policy_rules",
        verbose_name="النوع الأب",
        help_text="لو الاستحقاق جزء من نوع تاني"
    )
    subset_limit_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name="الحد الأقصى كجزء من الأب"
    )

    # قواعد الاستخدام
    requires_balance = models.BooleanField(
        default=True, verbose_name="يحتاج رصيد كافي"
    )
    allow_negative_balance = models.BooleanField(
        default=False, verbose_name="مسموح بالسالب"
    )
    negative_limit_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0, verbose_name="حد الرصيد السالب"
    )
    allow_half_day = models.BooleanField(
        default=True, verbose_name="مسموح بنص يوم"
    )
    allow_hourly = models.BooleanField(
        default=False, verbose_name="مسموح بالساعة"
    )
    max_days_per_request = models.PositiveSmallIntegerField(
        default=0, verbose_name="أقصى أيام في الطلب الواحد",
        help_text="0 = بلا حد"
    )
    max_requests_per_year = models.PositiveSmallIntegerField(
        default=0, verbose_name="أقصى طلبات في السنة",
        help_text="0 = بلا حد"
    )
    can_use_during_probation = models.BooleanField(
        default=False, verbose_name="مسموح في فترة التجربة"
    )

    # سياسة الترحيل
    carry_mode = models.CharField(
        max_length=30, choices=CARRY_MODE_CHOICES,
        default="none", verbose_name="سياسة الترحيل"
    )
    carry_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=100, verbose_name="نسبة الترحيل %"
    )
    carry_max_days = models.DecimalField(
        max_digits=5, decimal_places=1,
        default=0,
        verbose_name="أقصى أيام ترحيل",
        help_text="0 = بلا حد"
    )
    cash_compensation_enabled = models.BooleanField(
        default=False, verbose_name="مقابل نقدي مفعّل"
    )
    cash_compensation_basis = models.CharField(
        max_length=20, choices=CASH_BASIS_CHOICES,
        default="basic_salary",
        verbose_name="أساس المقابل النقدي"
    )

    class Meta:
        verbose_name = "قاعدة نوع إجازة"
        verbose_name_plural = "قواعد أنواع الإجازات"
        unique_together = [["policy", "leave_type"]]

    def __str__(self):
        return f"{self.policy.name} - {self.leave_type.name}"


class LeaveBalanceAdjustment(TenantModel):
    """تعديل يدوي على رصيد الإجازات"""

    ADJUSTMENT_TYPE_CHOICES = [
        ("opening_balance", "رصيد افتتاحي"),
        ("manual_add", "إضافة يدوية"),
        ("manual_deduct", "خصم يدوي"),
        ("carry_forward", "ترحيل من السنة السابقة"),
        ("cash_settlement", "تسوية نقدية"),
        ("policy_reset", "إعادة ضبط من السياسة"),
    ]

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE,
        related_name="leave_balance_adjustments",
        verbose_name="الموظف"
    )
    leave_type = models.ForeignKey(
        "LeaveType", on_delete=models.CASCADE,
        related_name="balance_adjustments",
        verbose_name="نوع الإجازة"
    )
    year = models.PositiveSmallIntegerField(verbose_name="السنة")
    adjustment_type = models.CharField(
        max_length=20, choices=ADJUSTMENT_TYPE_CHOICES,
        verbose_name="نوع التعديل"
    )
    days = models.DecimalField(
        max_digits=6, decimal_places=1,
        verbose_name="عدد الأيام",
        help_text="موجب = إضافة / سالب = خصم"
    )
    reason = models.TextField(blank=True, verbose_name="السبب")
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="leave_balance_adjustments_made",
        verbose_name="تم بواسطة"
    )

    class Meta:
        verbose_name = "تعديل رصيد إجازة"
        verbose_name_plural = "تعديلات أرصدة الإجازات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year}): {self.days} يوم"

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
    name_en          = models.CharField(max_length=100, blank=True, default="", verbose_name="Name (English)")
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
    gender_restriction = models.CharField(
        max_length=10,
        choices=[("all", "الجميع"), ("male", "ذكور فقط"), ("female", "إناث فقط")],
        default="all",
        verbose_name="مخصصة لـ"
    )

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

    HALF_DAY_TYPE_CHOICES = [
        ("morning", "صباحي"),
        ("afternoon", "مسائي"),
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
    half_day_type = models.CharField(
        max_length=20,
        choices=HALF_DAY_TYPE_CHOICES,
        blank=True,
        default="",
        verbose_name="نوع نصف اليوم"
    )
    leave_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="عدد ساعات الإجازة"
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
        # LEV-7: تحديث سجلات الحضور للأيام المعتمدة
        self._update_attendance_records()

    def _update_attendance_records(self):
        """LEV-7: تحديث سجلات الحضور لتصبح on_leave + شيل خصومات الغياب"""
        try:
            from attendance.models import Attendance, DailyAttendanceSummary
            from employees.models import Deduction
            from datetime import timedelta

            check_date = self.start_date
            while check_date <= self.end_date:
                # 1) تحديث سجل الحضور
                att, created = Attendance._base_manager.get_or_create(
                    company=self.company,
                    employee=self.employee,
                    date=check_date,
                    defaults={
                        'status': 'on_leave',
                    }
                )
                if not created and not att.check_in_time:
                    att.status = 'on_leave'
                    att.save(update_fields=['status'])

                # 2) تحديث DailyAttendanceSummary
                try:
                    summary = DailyAttendanceSummary._base_manager.filter(
                        employee=self.employee,
                        date=check_date,
                    ).first()
                    if summary:
                        summary.status = 'on_leave'
                        summary.effective_status = 'on_leave'
                        if hasattr(summary, 'absent_days'):
                            summary.absent_days = 0
                        summary.save()
                except Exception:
                    pass

                # 3) شيل خصومات الغياب اليوم ده
                try:
                    Deduction._base_manager.filter(
                        employee=self.employee,
                        date=check_date,
                        deduction_type='absence',
                    ).delete()
                except Exception:
                    pass

                check_date += timedelta(days=1)
        except Exception:
            pass

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
            balance = LeaveBalance._base_manager.get(
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

class LeaveRecallRequest(TenantModel):
    """استدعاء موظف من إجازته"""

    STATUS_CHOICES = [
        ('pending',   'قيد الانتظار'),
        ('approved',  'موافق عليه'),
        ('rejected',  'مرفوض'),
        ('cancelled', 'ملغي'),
    ]

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name='recall_requests',
        verbose_name='طلب الإجازة الأصلي'
    )

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_recall_requests',
        verbose_name='الموظف'
    )

    recall_date = models.DateField(
        verbose_name='يوم الاستدعاء'
    )

    reason = models.TextField(
        verbose_name='سبب الاستدعاء'
    )

    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='leave_recall_requests_made',
        verbose_name='طلب بواسطة'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة'
    )

    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='leave_recall_reviews',
        verbose_name='وافق/رفض بواسطة'
    )

    reviewed_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='تاريخ المراجعة'
    )

    review_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات المراجع'
    )

    hr_notified = models.BooleanField(
        default=False,
        verbose_name='تم إشعار HR'
    )

    balance_restored = models.BooleanField(
        default=False,
        verbose_name='تم إرجاع الرصيد'
    )

    class Meta:
        verbose_name = 'استدعاء من إجازة'
        verbose_name_plural = 'استدعاءات من الإجازات'
        ordering = ['-created_at']
        unique_together = [['employee', 'recall_date']]

    def __str__(self):
        return f"{self.employee} - {self.recall_date} - {self.get_status_display()}"

    def approve(self, user, notes=''):
        """الموافقة على الاستدعاء"""
        from django.utils import timezone
        self.status = 'approved'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
        self._restore_balance()

    def reject(self, user, notes=''):
        """رفض الاستدعاء"""
        from django.utils import timezone
        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def _restore_balance(self):
        """إرجاع يوم للرصيد عند الموافقة"""
        if self.balance_restored:
            return
        try:
            from leaves.models import LeaveBalance
            balance = LeaveBalance._base_manager.filter(
                employee=self.employee,
                leave_type=self.leave_request.leave_type,
                year=self.recall_date.year,
                company=self.company,
            ).first()
            if balance:
                balance.used_days = max(0, balance.used_days - 1)
                balance.save()
                self.balance_restored = True
                self.save(update_fields=['balance_restored'])
        except Exception:
            pass


# ── الإجازات الرسمية ──
from leaves.official_holiday_models import OfficialHoliday, OfficialHolidayRule
