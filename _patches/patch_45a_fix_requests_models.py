#!/usr/bin/env python3
"""
Patch 45a-fix: Rewrite requests_app/models.py cleanly
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 45a-fix: Rewrite requests_app models")
print("=" * 60)

models_content = '''from django.db import models
from core.models import TenantModel


class RequestCategory(TenantModel):
    """فئات الطلبات"""
    name = models.CharField(max_length=100, verbose_name="الاسم")
    icon = models.CharField(max_length=50, default="bi-inbox", verbose_name="الأيقونة")
    color = models.CharField(max_length=7, default="#06B6D4", verbose_name="اللون")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "فئة طلب"
        verbose_name_plural = "فئات الطلبات"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class RequestType(TenantModel):
    """أنواع الطلبات"""
    category = models.ForeignKey(
        RequestCategory,
        on_delete=models.CASCADE,
        related_name="types",
        verbose_name="الفئة"
    )
    name = models.CharField(max_length=100, verbose_name="الاسم")
    description = models.TextField(blank=True, verbose_name="الوصف")
    requires_date_range = models.BooleanField(default=False, verbose_name="يحتاج تاريخ من/إلى")
    requires_amount = models.BooleanField(default=False, verbose_name="يحتاج مبلغ")
    requires_document = models.BooleanField(default=False, verbose_name="يحتاج مرفق")
    requires_approval = models.BooleanField(default=True, verbose_name="يحتاج موافقة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="الترتيب")

    class Meta:
        verbose_name = "نوع طلب"
        verbose_name_plural = "أنواع الطلبات"
        ordering = ["category__order", "order", "name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


APPROVAL_ROLE_CHOICES = [
    ("skip", "تخطي"),
    ("direct_manager", "المدير المباشر"),
    ("hr_manager", "مدير HR"),
    ("company_admin", "صاحب الشركة"),
]


class ApprovalFlow(TenantModel):
    """مسار الموافقة لكل نوع طلب"""

    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.CASCADE,
        related_name="approval_flows",
        verbose_name="نوع الطلب"
    )

    step_1_role = models.CharField(
        max_length=20,
        choices=APPROVAL_ROLE_CHOICES,
        default="direct_manager",
        verbose_name="الخطوة 1"
    )
    step_2_role = models.CharField(
        max_length=20,
        choices=APPROVAL_ROLE_CHOICES,
        default="hr_manager",
        verbose_name="الخطوة 2"
    )
    step_3_role = models.CharField(
        max_length=20,
        choices=APPROVAL_ROLE_CHOICES,
        default="skip",
        verbose_name="الخطوة 3"
    )

    escalation_enabled = models.BooleanField(
        default=True,
        verbose_name="تصعيد تلقائي لو المسؤول غير متاح"
    )
    escalation_to = models.CharField(
        max_length=20,
        choices=[
            ("hr_manager", "مدير HR"),
            ("company_admin", "صاحب الشركة"),
        ],
        default="hr_manager",
        verbose_name="التصعيد يروح لمين"
    )
    notify_employee_on_each_step = models.BooleanField(
        default=True,
        verbose_name="إشعار الموظف في كل خطوة"
    )

    class Meta:
        verbose_name = "مسار موافقة"
        verbose_name_plural = "مسارات الموافقة"
        unique_together = [["company", "request_type"]]

    def __str__(self):
        return f"مسار: {self.request_type.name}"

    def get_active_steps(self):
        steps = []
        if self.step_1_role != "skip":
            steps.append(("step_1", self.step_1_role, self.get_step_1_role_display()))
        if self.step_2_role != "skip":
            steps.append(("step_2", self.step_2_role, self.get_step_2_role_display()))
        if self.step_3_role != "skip":
            steps.append(("step_3", self.step_3_role, self.get_step_3_role_display()))
        return steps


class ApprovalDelegation(TenantModel):
    """تفويض الصلاحيات"""

    SCOPE_CHOICES = [
        ("all_approvals", "كل الموافقات"),
        ("team_only", "فريقه فقط"),
    ]

    delegator = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="delegations_given",
        verbose_name="المُفوِّض"
    )
    delegate = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="delegations_received",
        verbose_name="المُفوَّض إليه"
    )
    delegator_role = models.CharField(max_length=20, verbose_name="دور المُفوِّض")
    start_date = models.DateField(verbose_name="من تاريخ")
    end_date = models.DateField(verbose_name="إلى تاريخ")
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default="all_approvals",
        verbose_name="نطاق التفويض"
    )
    reason = models.TextField(blank=True, verbose_name="السبب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "تفويض صلاحيات"
        verbose_name_plural = "تفويضات الصلاحيات"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.delegator} → {self.delegate} ({self.start_date} - {self.end_date})"

    @property
    def is_currently_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date


class EmployeeRequest(TenantModel):
    """الطلب نفسه"""

    STATUS_CHOICES = [
        ("pending", "قيد الانتظار"),
        ("manager_approved", "موافقة المدير"),
        ("hr_approved", "موافقة HR"),
        ("approved", "موافق عليه"),
        ("rejected", "مرفوض"),
        ("cancelled", "ملغي"),
    ]

    PRIORITY_CHOICES = [
        ("normal", "عادي"),
        ("urgent", "عاجل"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="الموظف"
    )
    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="نوع الطلب"
    )

    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    details = models.TextField(verbose_name="التفاصيل")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="normal",
        verbose_name="الأولوية"
    )

    start_date = models.DateField(null=True, blank=True, verbose_name="من تاريخ")
    end_date = models.DateField(null=True, blank=True, verbose_name="إلى تاريخ")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="المبلغ")
    document = models.FileField(upload_to="request_documents/", null=True, blank=True, verbose_name="مرفق")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="الحالة"
    )

    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_requests",
        verbose_name="تمت المراجعة بواسطة"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")
    review_notes = models.TextField(blank=True, verbose_name="ملاحظات المراجع")

    # Workflow steps
    current_step = models.PositiveSmallIntegerField(default=1, verbose_name="الخطوة الحالية")

    step_1_status = models.CharField(
        max_length=20,
        blank=True,
        default="pending",
        choices=[
            ("pending", "قيد الانتظار"),
            ("approved", "موافق"),
            ("rejected", "مرفوض"),
            ("skipped", "تخطي"),
        ],
        verbose_name="حالة الخطوة 1"
    )
    step_1_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="step1_approvals",
        verbose_name="الخطوة 1 بواسطة"
    )
    step_1_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الخطوة 1")
    step_1_notes = models.TextField(blank=True, verbose_name="ملاحظات الخطوة 1")

    step_2_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("pending", "قيد الانتظار"),
            ("approved", "موافق"),
            ("rejected", "مرفوض"),
            ("skipped", "تخطي"),
        ],
        verbose_name="حالة الخطوة 2"
    )
    step_2_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="step2_approvals",
        verbose_name="الخطوة 2 بواسطة"
    )
    step_2_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الخطوة 2")
    step_2_notes = models.TextField(blank=True, verbose_name="ملاحظات الخطوة 2")

    step_3_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("pending", "قيد الانتظار"),
            ("approved", "موافق"),
            ("rejected", "مرفوض"),
            ("skipped", "تخطي"),
        ],
        verbose_name="حالة الخطوة 3"
    )
    step_3_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="step3_approvals",
        verbose_name="الخطوة 3 بواسطة"
    )
    step_3_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الخطوة 3")
    step_3_notes = models.TextField(blank=True, verbose_name="ملاحظات الخطوة 3")

    substitute_employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="substituted_requests",
        verbose_name="البديل"
    )
    substitute_notified = models.BooleanField(default=False, verbose_name="تم إشعار البديل")

    notes = models.TextField(blank=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.request_type.name} - {self.subject}"

    @property
    def status_color(self):
        colors = {
            "pending": "warning",
            "approved": "success",
            "rejected": "danger",
            "cancelled": "secondary",
            "manager_approved": "info",
            "hr_approved": "info",
        }
        return colors.get(self.status, "secondary")

    @property
    def status_icon(self):
        icons = {
            "pending": "hourglass-split",
            "approved": "check-circle-fill",
            "rejected": "x-circle-fill",
            "cancelled": "slash-circle",
            "manager_approved": "check-circle",
            "hr_approved": "check-circle",
        }
        return icons.get(self.status, "circle")
'''

write_file(req_models_path, models_content)
print("  ✅ تم تثبيت requests_app/models.py بشكل نظيف")

print("\n" + "=" * 60)
print("  ✅ Patch 45a-fix اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  ✅ requests_app/models.py بقى مطابق للمigrations
  ✅ ApprovalFlow موجود في الكود
  ✅ ApprovalDelegation موجود في الكود
  ✅ EmployeeRequest فيها approval steps
  ✅ substitute_employee موجود
""")