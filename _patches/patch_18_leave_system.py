#!/usr/bin/env python3
"""
Patch 18: نظام الإجازات
=========================
- LeaveType (أنواع الإجازات)
- LeaveBalance (رصيد الإجازات)
- LeaveRequest (طلب إجازة)
- Workflow الموافقات
- صفحات Frontend كاملة
"""

import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def append_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

print("=" * 60)
print("  Patch 18: Leave System")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إنشاء leaves app
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء leaves app...")

leaves_dir = os.path.join(BASE_DIR, 'leaves')
os.makedirs(leaves_dir, exist_ok=True)
os.makedirs(os.path.join(leaves_dir, 'migrations'), exist_ok=True)

# __init__.py
create_file(os.path.join(leaves_dir, '__init__.py'), '')
create_file(os.path.join(leaves_dir, 'migrations', '__init__.py'), '')

# apps.py
create_file(os.path.join(leaves_dir, 'apps.py'), '''from django.apps import AppConfig

class LeavesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "leaves"
    verbose_name = "الإجازات"
''')


# ════════════════════════════════════════════════════════════
# 2. leaves/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء leaves/models.py...")

create_file(os.path.join(leaves_dir, 'models.py'), '''"""
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
''')


# ════════════════════════════════════════════════════════════
# 3. leaves/migrations/0001_initial.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء migration...")

create_file(
    os.path.join(leaves_dir, 'migrations', '0001_initial.py'),
    '''from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("employees", "0001_initial"),
        ("accounts",  "0001_initial"),
    ]

    operations = [

        migrations.CreateModel(
            name="LeaveType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
                ("name",        models.CharField(max_length=100, verbose_name="الاسم")),
                ("category",    models.CharField(max_length=20, default="other",
                                                  verbose_name="الفئة",
                                                  choices=[
                                                      ("annual","إجازة سنوية"),
                                                      ("sick","إجازة مرضية"),
                                                      ("emergency","إجازة طارئة"),
                                                      ("maternity","إجازة أمومة"),
                                                      ("paternity","إجازة أبوة"),
                                                      ("unpaid","إجازة بدون مرتب"),
                                                      ("other","أخرى"),
                                                  ])),
                ("days_allowed",      models.PositiveSmallIntegerField(default=0)),
                ("is_paid",           models.BooleanField(default=True)),
                ("requires_approval", models.BooleanField(default=True)),
                ("requires_document", models.BooleanField(default=False)),
                ("carry_forward",     models.BooleanField(default=False)),
                ("max_carry_days",    models.PositiveSmallIntegerField(default=0)),
                ("color",             models.CharField(max_length=7, default="#06B6D4")),
                ("is_active",         models.BooleanField(default=True)),
                ("description",       models.TextField(blank=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user",
                    verbose_name="أنشئ بواسطة")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user",
                    verbose_name="عدّل بواسطة")),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company", verbose_name="الشركة")),
            ],
            options={"verbose_name": "نوع إجازة",
                     "verbose_name_plural": "أنواع الإجازات"},
        ),

        migrations.CreateModel(
            name="LeaveBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at",    models.DateTimeField(auto_now_add=True)),
                ("updated_at",    models.DateTimeField(auto_now=True)),
                ("year",          models.PositiveSmallIntegerField(default=2025)),
                ("total_days",    models.DecimalField(max_digits=5, decimal_places=1, default=0)),
                ("used_days",     models.DecimalField(max_digits=5, decimal_places=1, default=0)),
                ("pending_days",  models.DecimalField(max_digits=5, decimal_places=1, default=0)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="leave_balances",
                    to="employees.employee")),
                ("leave_type", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="balances",
                    to="leaves.leavetype")),
            ],
            options={"verbose_name": "رصيد إجازة",
                     "verbose_name_plural": "أرصدة الإجازات"},
        ),

        migrations.AddConstraint(
            model_name="leavebalance",
            constraint=models.UniqueConstraint(
                fields=["company", "employee", "leave_type", "year"],
                name="unique_leave_balance"
            ),
        ),

        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at",    models.DateTimeField(auto_now_add=True)),
                ("updated_at",    models.DateTimeField(auto_now=True)),
                ("start_date",    models.DateField()),
                ("end_date",      models.DateField()),
                ("days_count",    models.DecimalField(max_digits=4,
                                                       decimal_places=1, default=1)),
                ("reason",        models.TextField()),
                ("document",      models.FileField(blank=True, null=True,
                                                    upload_to="leave_documents/")),
                ("notes",         models.TextField(blank=True)),
                ("status",        models.CharField(max_length=20, default="pending",
                                                    choices=[
                                                        ("pending","قيد الانتظار"),
                                                        ("approved","موافق عليه"),
                                                        ("rejected","مرفوض"),
                                                        ("cancelled","ملغي"),
                                                    ])),
                ("reviewed_at",   models.DateTimeField(null=True, blank=True)),
                ("review_notes",  models.TextField(blank=True)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="leave_requests",
                    to="employees.employee")),
                ("leave_type", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="requests",
                    to="leaves.leavetype")),
                ("reviewed_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="reviewed_leaves",
                    to="accounts.user")),
            ],
            options={"verbose_name": "طلب إجازة",
                     "verbose_name_plural": "طلبات الإجازات",
                     "ordering": ["-created_at"]},
        ),
    ]
'''
)


# ════════════════════════════════════════════════════════════
# 4. leaves/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء leaves/views.py...")

create_file(os.path.join(leaves_dir, 'views.py'), '''"""
leaves/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import LeaveType, LeaveBalance, LeaveRequest
from employees.models import Employee


# ════════════════════════════════════════════════════════════
# أنواع الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_types_list(request):
    company     = request.user.company
    leave_types = LeaveType.objects.filter(company=company).order_by("name")
    context = {
        "leave_types": leave_types,
        "page_title":  "أنواع الإجازات",
    }
    return render(request, "leaves/leave_types_list.html", context)


@login_required
def leave_type_add(request):
    if request.method == "POST":
        lt = LeaveType(company=request.user.company)
        lt.name              = request.POST.get("name", "")
        lt.category          = request.POST.get("category", "other")
        lt.days_allowed      = int(request.POST.get("days_allowed", 0))
        lt.is_paid           = "is_paid"           in request.POST
        lt.requires_approval = "requires_approval" in request.POST
        lt.requires_document = "requires_document" in request.POST
        lt.carry_forward     = "carry_forward"     in request.POST
        lt.max_carry_days    = int(request.POST.get("max_carry_days", 0))
        lt.color             = request.POST.get("color", "#06B6D4")
        lt.description       = request.POST.get("description", "")
        lt.save()
        messages.success(request, f\'✅ تم إضافة نوع الإجازة "{lt.name}"\')
        return redirect("leaves:leave_types_list")

    context = {
        "categories": LeaveType.LEAVE_CATEGORIES,
        "page_title": "إضافة نوع إجازة",
        "action":     "add",
    }
    return render(request, "leaves/leave_type_form.html", context)


@login_required
def leave_type_edit(request, pk):
    lt = get_object_or_404(LeaveType, pk=pk, company=request.user.company)

    if request.method == "POST":
        lt.name              = request.POST.get("name", lt.name)
        lt.category          = request.POST.get("category", lt.category)
        lt.days_allowed      = int(request.POST.get("days_allowed", 0))
        lt.is_paid           = "is_paid"           in request.POST
        lt.requires_approval = "requires_approval" in request.POST
        lt.requires_document = "requires_document" in request.POST
        lt.carry_forward     = "carry_forward"     in request.POST
        lt.max_carry_days    = int(request.POST.get("max_carry_days", 0))
        lt.color             = request.POST.get("color", lt.color)
        lt.is_active         = "is_active"         in request.POST
        lt.description       = request.POST.get("description", "")
        lt.save()
        messages.success(request, f\'✅ تم تحديث "{lt.name}"\')
        return redirect("leaves:leave_types_list")

    context = {
        "lt":         lt,
        "categories": LeaveType.LEAVE_CATEGORIES,
        "page_title": f"تعديل: {lt.name}",
        "action":     "edit",
    }
    return render(request, "leaves/leave_type_form.html", context)


@login_required
@require_POST
def leave_type_delete(request, pk):
    lt = get_object_or_404(LeaveType, pk=pk, company=request.user.company)
    name = lt.name
    lt.delete()
    messages.success(request, f\'✅ تم حذف "{name}"\')
    return redirect("leaves:leave_types_list")


# ════════════════════════════════════════════════════════════
# طلبات الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_requests_list(request):
    company  = request.user.company
    requests = LeaveRequest.objects.filter(
        company=company
    ).select_related("employee", "leave_type", "reviewed_by").order_by("-created_at")

    # فلترة
    status = request.GET.get("status")
    if status:
        requests = requests.filter(status=status)

    emp_search = request.GET.get("employee")
    if emp_search:
        requests = requests.filter(
            Q(employee__first_name_ar__icontains=emp_search) |
            Q(employee__last_name_ar__icontains=emp_search)
        )

    context = {
        "requests":   requests,
        "page_title": "طلبات الإجازات",
        "status":     status,
    }
    return render(request, "leaves/leave_requests_list.html", context)


@login_required
def leave_request_add(request):
    company     = request.user.company
    employees   = Employee.objects.filter(company=company, status="active")
    leave_types = LeaveType.objects.filter(company=company, is_active=True)

    if request.method == "POST":
        employee_id   = request.POST.get("employee")
        leave_type_id = request.POST.get("leave_type")
        start_date    = request.POST.get("start_date")
        end_date      = request.POST.get("end_date")
        reason        = request.POST.get("reason", "")

        if not all([employee_id, leave_type_id, start_date, end_date]):
            messages.error(request, "يرجى ملء جميع الحقول المطلوبة")
        else:
            from datetime import date
            start = date.fromisoformat(start_date)
            end   = date.fromisoformat(end_date)

            if end < start:
                messages.error(request, "تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية")
            else:
                days = (end - start).days + 1

                lr = LeaveRequest(company=company)
                lr.employee    = get_object_or_404(Employee, pk=employee_id, company=company)
                lr.leave_type  = get_object_or_404(LeaveType, pk=leave_type_id, company=company)
                lr.start_date  = start
                lr.end_date    = end
                lr.days_count  = days
                lr.reason      = reason
                lr.notes       = request.POST.get("notes", "")
                lr.status      = "pending"

                if "document" in request.FILES:
                    lr.document = request.FILES["document"]

                lr.save()

                # تحديث الرصيد المنتظر
                try:
                    bal = LeaveBalance.objects.get(
                        company=company,
                        employee=lr.employee,
                        leave_type=lr.leave_type,
                        year=start.year,
                    )
                    bal.pending_days += days
                    bal.save()
                except LeaveBalance.DoesNotExist:
                    pass

                messages.success(request, "✅ تم تقديم طلب الإجازة بنجاح")
                return redirect("leaves:leave_requests_list")

    context = {
        "employees":   employees,
        "leave_types": leave_types,
        "page_title":  "طلب إجازة جديد",
        "today":       timezone.now().date().isoformat(),
    }
    return render(request, "leaves/leave_request_form.html", context)


@login_required
def leave_request_detail(request, pk):
    lr = get_object_or_404(
        LeaveRequest, pk=pk, company=request.user.company
    )
    context = {
        "lr":         lr,
        "page_title": f"طلب إجازة - {lr.employee.full_name_ar}",
    }
    return render(request, "leaves/leave_request_detail.html", context)


@login_required
@require_POST
def leave_approve(request, pk):
    lr    = get_object_or_404(LeaveRequest, pk=pk, company=request.user.company)
    notes = request.POST.get("notes", "")
    lr.approve(request.user, notes)
    messages.success(request, "✅ تمت الموافقة على طلب الإجازة")
    return redirect("leaves:leave_request_detail", pk=pk)


@login_required
@require_POST
def leave_reject(request, pk):
    lr    = get_object_or_404(LeaveRequest, pk=pk, company=request.user.company)
    notes = request.POST.get("notes", "")
    lr.reject(request.user, notes)
    messages.warning(request, "⚠️ تم رفض طلب الإجازة")
    return redirect("leaves:leave_request_detail", pk=pk)


@login_required
@require_POST
def leave_cancel(request, pk):
    lr = get_object_or_404(LeaveRequest, pk=pk, company=request.user.company)
    lr.cancel()
    messages.info(request, "ℹ️ تم إلغاء طلب الإجازة")
    return redirect("leaves:leave_requests_list")


# ════════════════════════════════════════════════════════════
# أرصدة الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_balances(request):
    company     = request.user.company
    leave_types = LeaveType.objects.filter(company=company, is_active=True)
    employees   = Employee.objects.filter(company=company, status="active")
    year        = int(request.GET.get("year", timezone.now().year))

    balances = LeaveBalance.objects.filter(
        company=company, year=year
    ).select_related("employee", "leave_type").order_by(
        "employee__first_name_ar"
    )

    context = {
        "balances":    balances,
        "leave_types": leave_types,
        "employees":   employees,
        "year":        year,
        "years":       range(2023, timezone.now().year + 2),
        "page_title":  "أرصدة الإجازات",
    }
    return render(request, "leaves/leave_balances.html", context)


@login_required
@require_POST
def set_leave_balance(request):
    """تحديد رصيد إجازة لموظف"""
    company       = request.user.company
    employee_id   = request.POST.get("employee")
    leave_type_id = request.POST.get("leave_type")
    year          = int(request.POST.get("year", timezone.now().year))
    total_days    = float(request.POST.get("total_days", 0))

    employee   = get_object_or_404(Employee,   pk=employee_id,   company=company)
    leave_type = get_object_or_404(LeaveType,  pk=leave_type_id, company=company)

    bal, created = LeaveBalance.objects.get_or_create(
        company=company,
        employee=employee,
        leave_type=leave_type,
        year=year,
        defaults={"total_days": total_days},
    )
    if not created:
        bal.total_days = total_days
        bal.save()

    action = "إنشاء" if created else "تحديث"
    messages.success(
        request,
        f"✅ تم {action} رصيد {leave_type.name} للموظف {employee.full_name_ar}"
    )
    return redirect("leaves:leave_balances")
''')


# ════════════════════════════════════════════════════════════
# 5. leaves/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء leaves/urls.py...")

create_file(os.path.join(leaves_dir, 'urls.py'), '''from django.urls import path
from . import views

app_name = "leaves"

urlpatterns = [

    # أنواع الإجازات
    path("types/",
         views.leave_types_list, name="leave_types_list"),
    path("types/add/",
         views.leave_type_add, name="leave_type_add"),
    path("types/<int:pk>/edit/",
         views.leave_type_edit, name="leave_type_edit"),
    path("types/<int:pk>/delete/",
         views.leave_type_delete, name="leave_type_delete"),

    # الطلبات
    path("",
         views.leave_requests_list, name="leave_requests_list"),
    path("add/",
         views.leave_request_add, name="leave_request_add"),
    path("<int:pk>/",
         views.leave_request_detail, name="leave_request_detail"),
    path("<int:pk>/approve/",
         views.leave_approve, name="leave_approve"),
    path("<int:pk>/reject/",
         views.leave_reject, name="leave_reject"),
    path("<int:pk>/cancel/",
         views.leave_cancel, name="leave_cancel"),

    # الأرصدة
    path("balances/",
         views.leave_balances, name="leave_balances"),
    path("balances/set/",
         views.set_leave_balance, name="set_leave_balance"),
]
''')


# ════════════════════════════════════════════════════════════
# 6. إضافة leaves في settings.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة leaves في INSTALLED_APPS...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')
settings_content = read_file(settings_path)

if "'leaves'" not in settings_content and '"leaves"' not in settings_content:
    settings_content = settings_content.replace(
        "'attendance',",
        "'attendance',\n    'leaves',"
    )
    write_file(settings_path, settings_content)
else:
    print("  ℹ️  leaves موجود في INSTALLED_APPS")


# ════════════════════════════════════════════════════════════
# 7. إضافة leaves في motionhr/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة leaves URLs...")

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

if "leaves.urls" not in main_urls_content:
    main_urls_content = main_urls_content.replace(
        "path('companies/',     include('companies.urls',     namespace='companies')),",
        "path('companies/',     include('companies.urls',     namespace='companies')),\n    path('leaves/',        include('leaves.urls',        namespace='leaves')),"
    )
    write_file(main_urls_path, main_urls_content)
else:
    print("  ℹ️  leaves URLs موجود")


# ════════════════════════════════════════════════════════════
# 8. leaves/admin.py
# ════════════════════════════════════════════════════════════
create_file(os.path.join(leaves_dir, 'admin.py'), '''from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "days_allowed", "is_paid", "is_active"]
    list_filter  = ["category", "is_paid", "is_active"]

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "year", "total_days", "used_days"]

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "status"]
    list_filter  = ["status", "leave_type"]
''')

create_file(os.path.join(leaves_dir, 'tests.py'), '')


# ════════════════════════════════════════════════════════════
# 9. Templates
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء Templates...")

# ── leave_types_list.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_types_list.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}أنواع الإجازات{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-calendar-check me-2" style="color:#06B6D4;"></i>
        أنواع الإجازات
      </h4>
      <p class="text-muted mb-0">تعريف وإدارة أنواع الإجازات</p>
    </div>
    <a href="{% url 'leaves:leave_type_add' %}"
       class="btn text-white" style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i> نوع جديد
    </a>
  </div>

  {% if leave_types %}
  <div class="row g-3">
    {% for lt in leave_types %}
    <div class="col-md-6 col-lg-4">
      <div class="card border-0 shadow-sm h-100"
           style="border-right: 4px solid {{ lt.color }} !important;">
        <div class="card-body p-4">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h6 class="fw-bold mb-0">{{ lt.name }}</h6>
            <span class="badge rounded-pill"
                  style="background:{{ lt.color }};">
              {{ lt.get_category_display }}
            </span>
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <div class="text-center p-2 rounded" style="background:#f8fafc;">
                <div class="fw-bold fs-5">
                  {% if lt.days_allowed == 0 %}∞{% else %}{{ lt.days_allowed }}{% endif %}
                </div>
                <small class="text-muted">يوم/سنة</small>
              </div>
            </div>
            <div class="col-6">
              <div class="text-center p-2 rounded" style="background:#f8fafc;">
                <div class="fw-bold fs-5">
                  {% if lt.is_paid %}
                    <i class="bi bi-check-circle-fill text-success"></i>
                  {% else %}
                    <i class="bi bi-x-circle-fill text-danger"></i>
                  {% endif %}
                </div>
                <small class="text-muted">بمرتب</small>
              </div>
            </div>
          </div>

          <div class="d-flex flex-wrap gap-1 mb-3">
            {% if lt.requires_approval %}
              <span class="badge bg-light text-dark border">تحتاج موافقة</span>
            {% endif %}
            {% if lt.requires_document %}
              <span class="badge bg-light text-dark border">تحتاج وثيقة</span>
            {% endif %}
            {% if lt.carry_forward %}
              <span class="badge bg-light text-dark border">ترحيل</span>
            {% endif %}
            {% if not lt.is_active %}
              <span class="badge bg-danger">موقوف</span>
            {% endif %}
          </div>

          <div class="d-flex gap-2 pt-3 border-top">
            <a href="{% url 'leaves:leave_type_edit' lt.pk %}"
               class="btn btn-sm btn-outline-primary flex-fill">
              <i class="bi bi-pencil me-1"></i>تعديل
            </a>
            <form method="post"
                  action="{% url 'leaves:leave_type_delete' lt.pk %}"
                  onsubmit="return confirm('حذف {{ lt.name }}؟')">
              {% csrf_token %}
              <button type="submit" class="btn btn-sm btn-outline-danger">
                <i class="bi bi-trash"></i>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-calendar-x" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد أنواع إجازات بعد</h5>
      <a href="{% url 'leaves:leave_type_add' %}"
         class="btn mt-2 text-white" style="background:#06B6D4;">
        أضف أول نوع
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

# ── leave_type_form.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_type_form.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'leaves:leave_types_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">{{ page_title }}</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-7">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  اسم الإجازة <span class="text-danger">*</span>
                </label>
                <input type="text" name="name" class="form-control"
                       value="{{ lt.name|default:'' }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الفئة</label>
                <select name="category" class="form-select">
                  {% for val, label in categories %}
                  <option value="{{ val }}"
                    {% if lt.category == val %}selected{% endif %}>
                    {{ label }}
                  </option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  عدد الأيام المسموحة سنوياً
                  <small class="text-muted">(0 = بدون حد)</small>
                </label>
                <input type="number" name="days_allowed" class="form-control"
                       value="{{ lt.days_allowed|default:0 }}" min="0">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">أقصى أيام ترحيل</label>
                <input type="number" name="max_carry_days" class="form-control"
                       value="{{ lt.max_carry_days|default:0 }}" min="0">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">اللون</label>
                <div class="d-flex gap-2 align-items-center">
                  <input type="color" name="color" class="form-control form-control-color"
                         value="{{ lt.color|default:'#06B6D4' }}"
                         style="width:50px;height:38px;">
                  <small class="text-muted">لون تمييز نوع الإجازة</small>
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">الوصف</label>
                <textarea name="description" class="form-control" rows="2">
                  {{ lt.description|default:'' }}
                </textarea>
              </div>

              <!-- Switches -->
              <div class="col-12">
                <div class="row g-2">
                  {% for field, label in switches %}
                  <div class="col-md-6">
                    <div class="d-flex align-items-center justify-content-between
                                p-3 border rounded-3">
                      <span class="fw-semibold small">{{ label }}</span>
                      <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox"
                               name="{{ field }}" id="{{ field }}"
                               {% if lt and lt|getattr:field %}checked{% endif %}
                               {% if not lt and field == 'is_paid' %}checked{% endif %}
                               {% if not lt and field == 'requires_approval' %}checked{% endif %}
                               style="width:2.5rem;height:1.25rem;">
                      </div>
                    </div>
                  </div>
                  {% endfor %}
                </div>
              </div>

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة{% else %}حفظ{% endif %}
              </button>
              <a href="{% url 'leaves:leave_types_list' %}"
                 class="btn btn-outline-secondary px-4"
                 style="border-radius:10px;">إلغاء</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
)

# ── leave_requests_list.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_requests_list.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}طلبات الإجازات{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-calendar2-week me-2" style="color:#06B6D4;"></i>
        طلبات الإجازات
      </h4>
    </div>
    <a href="{% url 'leaves:leave_request_add' %}"
       class="btn text-white" style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i> طلب جديد
    </a>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" class="d-flex gap-3 align-items-center flex-wrap">
        <select name="status" class="form-select" style="max-width:200px;"
                onchange="this.form.submit()">
          <option value="">كل الحالات</option>
          <option value="pending"  {% if status == 'pending'  %}selected{% endif %}>قيد الانتظار</option>
          <option value="approved" {% if status == 'approved' %}selected{% endif %}>موافق عليه</option>
          <option value="rejected" {% if status == 'rejected' %}selected{% endif %}>مرفوض</option>
          <option value="cancelled"{% if status == 'cancelled'%}selected{% endif %}>ملغي</option>
        </select>
        <input type="text" name="employee" class="form-control"
               style="max-width:200px;" placeholder="اسم الموظف"
               value="{{ request.GET.employee|default:'' }}">
        <button type="submit" class="btn btn-outline-secondary btn-sm">بحث</button>
        <a href="{% url 'leaves:leave_requests_list' %}"
           class="btn btn-light btn-sm">إعادة تعيين</a>
      </form>
    </div>
  </div>

  {% if requests %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th>نوع الإجازة</th>
            <th>من</th>
            <th>إلى</th>
            <th>الأيام</th>
            <th>الحالة</th>
            <th>تاريخ الطلب</th>
            <th class="text-center">إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {% for lr in requests %}
          <tr>
            <td class="px-4 fw-semibold">{{ lr.employee.full_name_ar }}</td>
            <td>
              <span class="badge rounded-pill"
                    style="background:{{ lr.leave_type.color }};">
                {{ lr.leave_type.name }}
              </span>
            </td>
            <td>{{ lr.start_date|date:"d/m/Y" }}</td>
            <td>{{ lr.end_date|date:"d/m/Y" }}</td>
            <td class="fw-bold">{{ lr.days_count }}</td>
            <td>
              <span class="badge bg-{{ lr.status_color }}">
                <i class="bi bi-{{ lr.status_icon }} me-1"></i>
                {{ lr.get_status_display }}
              </span>
            </td>
            <td class="text-muted small">{{ lr.created_at|date:"d/m/Y" }}</td>
            <td class="text-center">
              <a href="{% url 'leaves:leave_request_detail' lr.pk %}"
                 class="btn btn-sm btn-outline-primary">
                <i class="bi bi-eye"></i>
              </a>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-calendar2-x" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد طلبات إجازات</h5>
      <a href="{% url 'leaves:leave_request_add' %}"
         class="btn mt-2 text-white" style="background:#06B6D4;">
        <i class="bi bi-plus me-1"></i>أضف طلب
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

# ── leave_request_form.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_request_form.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}طلب إجازة جديد{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">طلب إجازة جديد</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  الموظف <span class="text-danger">*</span>
                </label>
                <select name="employee" class="form-select" required>
                  <option value="">اختر الموظف</option>
                  {% for emp in employees %}
                  <option value="{{ emp.pk }}">
                    {{ emp.full_name_ar }} ({{ emp.employee_code }})
                  </option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  نوع الإجازة <span class="text-danger">*</span>
                </label>
                <select name="leave_type" class="form-select" required>
                  <option value="">اختر النوع</option>
                  {% for lt in leave_types %}
                  <option value="{{ lt.pk }}">{{ lt.name }}</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  من تاريخ <span class="text-danger">*</span>
                </label>
                <input type="date" name="start_date" class="form-control"
                       value="{{ today }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  إلى تاريخ <span class="text-danger">*</span>
                </label>
                <input type="date" name="end_date" class="form-control"
                       value="{{ today }}" required>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">
                  السبب <span class="text-danger">*</span>
                </label>
                <textarea name="reason" class="form-control" rows="3"
                          placeholder="اذكر سبب طلب الإجازة..." required></textarea>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  وثيقة مرفقة
                  <small class="text-muted">(إن وجدت)</small>
                </label>
                <input type="file" name="document" class="form-control">
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">ملاحظات</label>
                <textarea name="notes" class="form-control" rows="2"></textarea>
              </div>

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-send me-1"></i>
                تقديم الطلب
              </button>
              <a href="{% url 'leaves:leave_requests_list' %}"
                 class="btn btn-outline-secondary px-4"
                 style="border-radius:10px;">إلغاء</a>
            </div>

          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
)

# ── leave_request_detail.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_request_detail.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تفاصيل طلب الإجازة{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">تفاصيل طلب الإجازة</h4>
    <span class="badge bg-{{ lr.status_color }} ms-3 fs-6 px-3">
      <i class="bi bi-{{ lr.status_icon }} me-1"></i>
      {{ lr.get_status_display }}
    </span>
  </div>

  <div class="row g-4">
    <div class="col-lg-8">

      <!-- بيانات الطلب -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">بيانات الطلب</h5>
        </div>
        <div class="card-body px-4 pb-4">
          <div class="row g-3">

            <div class="col-md-6">
              <label class="text-muted small">الموظف</label>
              <div class="fw-bold">{{ lr.employee.full_name_ar }}</div>
              <small class="text-muted">{{ lr.employee.employee_code }}</small>
            </div>

            <div class="col-md-6">
              <label class="text-muted small">نوع الإجازة</label>
              <div>
                <span class="badge rounded-pill fs-6"
                      style="background:{{ lr.leave_type.color }};">
                  {{ lr.leave_type.name }}
                </span>
              </div>
            </div>

            <div class="col-md-4">
              <label class="text-muted small">من تاريخ</label>
              <div class="fw-bold">{{ lr.start_date|date:"d/m/Y" }}</div>
            </div>

            <div class="col-md-4">
              <label class="text-muted small">إلى تاريخ</label>
              <div class="fw-bold">{{ lr.end_date|date:"d/m/Y" }}</div>
            </div>

            <div class="col-md-4">
              <label class="text-muted small">عدد الأيام</label>
              <div class="fw-bold fs-4" style="color:#06B6D4;">
                {{ lr.days_count }}
              </div>
            </div>

            <div class="col-12">
              <label class="text-muted small">السبب</label>
              <div class="p-3 rounded" style="background:#f8fafc;">
                {{ lr.reason }}
              </div>
            </div>

            {% if lr.notes %}
            <div class="col-12">
              <label class="text-muted small">ملاحظات</label>
              <div>{{ lr.notes }}</div>
            </div>
            {% endif %}

            {% if lr.document %}
            <div class="col-12">
              <label class="text-muted small">الوثيقة المرفقة</label>
              <div>
                <a href="{{ lr.document.url }}" target="_blank"
                   class="btn btn-sm btn-outline-primary">
                  <i class="bi bi-file-earmark me-1"></i>
                  عرض الوثيقة
                </a>
              </div>
            </div>
            {% endif %}

          </div>
        </div>
      </div>

      <!-- المراجعة -->
      {% if lr.reviewed_by %}
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h6 class="fw-bold mb-3">تفاصيل المراجعة</h6>
          <div class="d-flex align-items-center gap-3 mb-2">
            <i class="bi bi-person-check fs-4" style="color:#06B6D4;"></i>
            <div>
              <div class="fw-semibold">{{ lr.reviewed_by.get_full_name }}</div>
              <small class="text-muted">{{ lr.reviewed_at|date:"d/m/Y H:i" }}</small>
            </div>
          </div>
          {% if lr.review_notes %}
          <div class="p-3 rounded mt-2" style="background:#f8fafc;">
            {{ lr.review_notes }}
          </div>
          {% endif %}
        </div>
      </div>
      {% endif %}

    </div>

    <!-- أزرار الإجراءات -->
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h6 class="fw-bold mb-3">الإجراءات</h6>

          {% if lr.status == 'pending' %}

          <!-- موافقة -->
          <form method="post" action="{% url 'leaves:leave_approve' lr.pk %}"
                class="mb-2">
            {% csrf_token %}
            <textarea name="notes" class="form-control form-control-sm mb-2"
                      placeholder="ملاحظات (اختياري)" rows="2"></textarea>
            <button type="submit" class="btn btn-success w-100"
                    onclick="return confirm('الموافقة على الطلب؟')">
              <i class="bi bi-check-lg me-1"></i>
              الموافقة
            </button>
          </form>

          <!-- رفض -->
          <form method="post" action="{% url 'leaves:leave_reject' lr.pk %}"
                class="mb-2">
            {% csrf_token %}
            <textarea name="notes" class="form-control form-control-sm mb-2"
                      placeholder="سبب الرفض" rows="2"></textarea>
            <button type="submit" class="btn btn-danger w-100"
                    onclick="return confirm('رفض الطلب؟')">
              <i class="bi bi-x-lg me-1"></i>
              رفض
            </button>
          </form>

          <!-- إلغاء -->
          <form method="post" action="{% url 'leaves:leave_cancel' lr.pk %}">
            {% csrf_token %}
            <button type="submit" class="btn btn-outline-secondary w-100"
                    onclick="return confirm('إلغاء الطلب؟')">
              <i class="bi bi-slash-circle me-1"></i>
              إلغاء الطلب
            </button>
          </form>

          {% elif lr.status == 'approved' %}
          <form method="post" action="{% url 'leaves:leave_cancel' lr.pk %}">
            {% csrf_token %}
            <button type="submit" class="btn btn-outline-warning w-100"
                    onclick="return confirm('إلغاء الموافقة؟')">
              <i class="bi bi-arrow-counterclockwise me-1"></i>
              إلغاء الموافقة
            </button>
          </form>

          {% else %}
          <div class="text-center text-muted py-3">
            <i class="bi bi-check-all fs-3"></i>
            <p class="mb-0 mt-1 small">تم اتخاذ الإجراء</p>
          </div>
          {% endif %}

          <hr>
          <a href="{% url 'leaves:leave_requests_list' %}"
             class="btn btn-light w-100">
            <i class="bi bi-arrow-right me-1"></i>
            رجوع للقائمة
          </a>
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)

# ── leave_balances.html ──
create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_balances.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}أرصدة الإجازات{% endblock %}
{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-wallet2 me-2" style="color:#06B6D4;"></i>
        أرصدة الإجازات
      </h4>
    </div>
    <!-- فلترة السنة -->
    <form method="get" class="d-flex align-items-center gap-2">
      <select name="year" class="form-select" onchange="this.form.submit()">
        {% for y in years %}
        <option value="{{ y }}" {% if y == year %}selected{% endif %}>{{ y }}</option>
        {% endfor %}
      </select>
    </form>
  </div>

  <!-- فورم تحديد رصيد -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
      <h5 class="fw-bold mb-0">تحديد رصيد إجازة</h5>
    </div>
    <div class="card-body px-4 pb-4">
      <form method="post" action="{% url 'leaves:set_leave_balance' %}">
        {% csrf_token %}
        <input type="hidden" name="year" value="{{ year }}">
        <div class="row g-3 align-items-end">
          <div class="col-md-3">
            <label class="form-label fw-semibold small">الموظف</label>
            <select name="employee" class="form-select" required>
              <option value="">اختر الموظف</option>
              {% for emp in employees %}
              <option value="{{ emp.pk }}">{{ emp.full_name_ar }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label fw-semibold small">نوع الإجازة</label>
            <select name="leave_type" class="form-select" required>
              <option value="">اختر النوع</option>
              {% for lt in leave_types %}
              <option value="{{ lt.pk }}">{{ lt.name }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label fw-semibold small">عدد الأيام</label>
            <input type="number" name="total_days" class="form-control"
                   min="0" step="0.5" value="21" required>
          </div>
          <div class="col-md-2">
            <button type="submit" class="btn w-100 text-white"
                    style="background:#06B6D4;">
              <i class="bi bi-check me-1"></i>تحديد
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <!-- جدول الأرصدة -->
  {% if balances %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th>نوع الإجازة</th>
            <th class="text-center">الإجمالي</th>
            <th class="text-center">المستخدم</th>
            <th class="text-center">قيد الانتظار</th>
            <th class="text-center">المتبقي</th>
          </tr>
        </thead>
        <tbody>
          {% for bal in balances %}
          <tr>
            <td class="px-4 fw-semibold">{{ bal.employee.full_name_ar }}</td>
            <td>
              <span class="badge rounded-pill"
                    style="background:{{ bal.leave_type.color }};">
                {{ bal.leave_type.name }}
              </span>
            </td>
            <td class="text-center fw-bold">{{ bal.total_days }}</td>
            <td class="text-center text-danger fw-bold">{{ bal.used_days }}</td>
            <td class="text-center text-warning fw-bold">{{ bal.pending_days }}</td>
            <td class="text-center fw-bold">
              <span class="badge fs-6 px-3
                {% if bal.remaining_days <= 0 %}bg-danger
                {% elif bal.remaining_days <= 3 %}bg-warning text-dark
                {% else %}bg-success{% endif %}">
                {{ bal.remaining_days_display }}
              </span>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-wallet2" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد أرصدة لسنة {{ year }}</h5>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 10. تحديث leave_type_form view بـ switches context
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث leave_type views بـ switches context...")

views_content = read_file(os.path.join(leaves_dir, 'views.py'))

switches_list = """
LEAVE_SWITCHES = [
    ('is_paid',           'بمرتب'),
    ('requires_approval', 'تحتاج موافقة'),
    ('requires_document', 'تحتاج وثيقة'),
    ('carry_forward',     'ترحيل للسنة القادمة'),
    ('is_active',         'نشط'),
]
"""

if 'LEAVE_SWITCHES' not in views_content:
    views_content = switches_list + '\n' + views_content
    views_content = views_content.replace(
        '''    context = {
        "categories": LeaveType.LEAVE_CATEGORIES,
        "page_title": "إضافة نوع إجازة",
        "action":     "add",
    }''',
        '''    context = {
        "categories": LeaveType.LEAVE_CATEGORIES,
        "switches":   LEAVE_SWITCHES,
        "page_title": "إضافة نوع إجازة",
        "action":     "add",
    }'''
    )
    views_content = views_content.replace(
        '''    context = {
        "lt":         lt,
        "categories": LeaveType.LEAVE_CATEGORIES,
        "page_title": f"تعديل: {lt.name}",
        "action":     "edit",
    }''',
        '''    context = {
        "lt":         lt,
        "categories": LeaveType.LEAVE_CATEGORIES,
        "switches":   LEAVE_SWITCHES,
        "page_title": f"تعديل: {lt.name}",
        "action":     "edit",
    }'''
    )
    write_file(os.path.join(leaves_dir, 'views.py'), views_content)


# ════════════════════════════════════════════════════════════
# 11. تحديث الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
sidebar_content = read_file(sidebar_path)

if 'leaves:leave_requests_list' not in sidebar_content:
    leaves_links = """
                <!-- ══ الإجازات ══ -->
                <li class="nav-item mt-3">
                  <div class="px-3 mb-1">
                    <small style="color:rgba(255,255,255,0.35);
                                  font-size:0.7rem;letter-spacing:1px;
                                  text-transform:uppercase;">
                      الإجازات
                    </small>
                  </div>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'leaves:leave_requests_list' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-calendar2-week"></i>
                    <span>طلبات الإجازات</span>
                  </a>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'leaves:leave_balances' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-wallet2"></i>
                    <span>أرصدة الإجازات</span>
                  </a>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'leaves:leave_types_list' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-list-check"></i>
                    <span>أنواع الإجازات</span>
                  </a>
                </li>"""

    # نضيف قبل إعدادات الشركة
    if 'companies:settings' in sidebar_content:
        comp_idx = sidebar_content.find("{% url 'companies:settings' %}")
        li_start = sidebar_content.rfind('<li', 0, comp_idx)
        # نلاقي بداية السيكشن (الـ comment)
        section_start = sidebar_content.rfind('<!-- ══', 0, li_start)
        if section_start == -1:
            section_start = li_start
        sidebar_content = (
            sidebar_content[:section_start] +
            leaves_links + '\n' +
            sidebar_content[section_start:]
        )
        write_file(sidebar_path, sidebar_content)
        print("  ✅ تم إضافة روابط الإجازات في الـ Sidebar")
    else:
        print("  ⚠️  مش لاقي مكان مناسب")
else:
    print("  ℹ️  روابط الإجازات موجودة")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 18 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ leaves app كامل
  2.  ✅ LeaveType, LeaveBalance, LeaveRequest models
  3.  ✅ Migration كامل
  4.  ✅ leaves/views.py - كل الـ views
  5.  ✅ leaves/urls.py
  6.  ✅ leaves/admin.py
  7.  ✅ 6 صفحات HTML كاملة
  8.  ✅ INSTALLED_APPS محدث
  9.  ✅ motionhr/urls.py محدث
  10. ✅ Sidebar محدث

🔗 URLs الجديدة:
  /leaves/                  ← طلبات الإجازات
  /leaves/add/              ← طلب جديد
  /leaves/<pk>/             ← تفاصيل طلب
  /leaves/types/            ← أنواع الإجازات
  /leaves/balances/         ← الأرصدة

⚠️  مطلوب تشغيل:
  python manage.py migrate

🚀 الخطوة الجاية: Patch 19 - التقارير
""")