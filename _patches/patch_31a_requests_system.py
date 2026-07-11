#!/usr/bin/env python3
"""
Patch 31a: Generic Requests System
====================================
نظام طلبات شامل يدعم كل أنواع الطلبات
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 31a: Requests System")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إنشاء requests_app
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء requests_app...")

app_dir = os.path.join(BASE_DIR, "requests_app")
os.makedirs(app_dir, exist_ok=True)
os.makedirs(os.path.join(app_dir, "migrations"), exist_ok=True)

create_file(os.path.join(app_dir, "__init__.py"), "")
create_file(os.path.join(app_dir, "migrations", "__init__.py"), "")
create_file(os.path.join(app_dir, "tests.py"), "")

create_file(os.path.join(app_dir, "apps.py"), """from django.apps import AppConfig

class RequestsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "requests_app"
    verbose_name = "الطلبات"
""")


# ════════════════════════════════════════════════════════════
# 2. Models
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء models.py...")

create_file(os.path.join(app_dir, "models.py"), '''from django.db import models
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
    requires_date_range = models.BooleanField(
        default=False, verbose_name="يحتاج تاريخ من/إلى"
    )
    requires_amount = models.BooleanField(
        default=False, verbose_name="يحتاج مبلغ"
    )
    requires_document = models.BooleanField(
        default=False, verbose_name="يحتاج مرفق"
    )
    requires_approval = models.BooleanField(
        default=True, verbose_name="يحتاج موافقة"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="الترتيب")

    class Meta:
        verbose_name = "نوع طلب"
        verbose_name_plural = "أنواع الطلبات"
        ordering = ["category__order", "order", "name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class EmployeeRequest(TenantModel):
    """الطلب نفسه"""

    STATUS_CHOICES = [
        ("pending",    "قيد الانتظار"),
        ("manager_approved", "موافقة المدير"),
        ("hr_approved", "موافقة HR"),
        ("approved",   "موافق عليه"),
        ("rejected",   "مرفوض"),
        ("cancelled",  "ملغي"),
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

    # التفاصيل
    subject = models.CharField(
        max_length=200, verbose_name="الموضوع"
    )
    details = models.TextField(
        verbose_name="التفاصيل"
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES,
        default="normal", verbose_name="الأولوية"
    )

    # تواريخ (اختياري حسب نوع الطلب)
    start_date = models.DateField(
        null=True, blank=True, verbose_name="من تاريخ"
    )
    end_date = models.DateField(
        null=True, blank=True, verbose_name="إلى تاريخ"
    )

    # مبلغ (اختياري حسب نوع الطلب)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True, verbose_name="المبلغ"
    )

    # مرفق
    document = models.FileField(
        upload_to="request_documents/",
        null=True, blank=True, verbose_name="مرفق"
    )

    # الحالة
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default="pending", verbose_name="الحالة"
    )

    # المراجعة
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_requests",
        verbose_name="تمت المراجعة بواسطة"
    )
    reviewed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="تاريخ المراجعة"
    )
    review_notes = models.TextField(
        blank=True, verbose_name="ملاحظات المراجع"
    )

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
            "manager_approved": "info",
            "hr_approved": "info",
            "approved": "success",
            "rejected": "danger",
            "cancelled": "secondary",
        }
        return colors.get(self.status, "secondary")

    @property
    def status_icon(self):
        icons = {
            "pending": "hourglass-split",
            "manager_approved": "check-circle",
            "hr_approved": "check-circle",
            "approved": "check-circle-fill",
            "rejected": "x-circle-fill",
            "cancelled": "slash-circle",
        }
        return icons.get(self.status, "circle")
''')


# ════════════════════════════════════════════════════════════
# 3. Admin
# ════════════════════════════════════════════════════════════
create_file(os.path.join(app_dir, "admin.py"), """from django.contrib import admin
from .models import RequestCategory, RequestType, EmployeeRequest

@admin.register(RequestCategory)
class RequestCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]

@admin.register(RequestType)
class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "requires_approval", "is_active"]
    list_filter = ["category", "is_active"]

@admin.register(EmployeeRequest)
class EmployeeRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "request_type", "subject", "status", "created_at"]
    list_filter = ["status", "request_type"]
""")


# ════════════════════════════════════════════════════════════
# 4. Views
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء views.py...")

create_file(os.path.join(app_dir, "views.py"), '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q

from .models import RequestCategory, RequestType, EmployeeRequest
from employees.models import Employee


@login_required
def requests_list(request):
    """قائمة الطلبات"""
    company = request.user.company

    if request.user.role == "employee":
        emp = Employee.objects.filter(user=request.user).first()
        if emp:
            reqs = EmployeeRequest.objects.filter(company=company, employee=emp)
        else:
            reqs = EmployeeRequest.objects.none()
    else:
        reqs = EmployeeRequest.objects.filter(company=company)

    reqs = reqs.select_related("employee", "request_type", "request_type__category")

    status = request.GET.get("status")
    if status:
        reqs = reqs.filter(status=status)

    context = {
        "requests": reqs.order_by("-created_at"),
        "status_filter": status,
        "page_title": "الطلبات",
    }
    return render(request, "requests_app/list.html", context)


@login_required
def request_add(request):
    """طلب جديد"""
    company = request.user.company
    categories = RequestCategory.objects.filter(
        company=company, is_active=True
    ).prefetch_related("types")
    request_types = RequestType.objects.filter(
        company=company, is_active=True
    ).select_related("category")

    if request.user.role == "employee":
        emp = Employee.objects.filter(user=request.user).first()
        employees = [emp] if emp else []
    else:
        employees = Employee.objects.filter(company=company, status="active")

    if request.method == "POST":
        employee_id = request.POST.get("employee")
        type_id = request.POST.get("request_type")
        subject = request.POST.get("subject", "")
        details = request.POST.get("details", "")
        priority = request.POST.get("priority", "normal")

        if not all([employee_id, type_id, subject, details]):
            messages.error(request, "يرجى ملء جميع الحقول المطلوبة")
        else:
            emp = get_object_or_404(Employee, pk=employee_id, company=company)
            req_type = get_object_or_404(RequestType, pk=type_id, company=company)

            req_obj = EmployeeRequest(company=company)
            req_obj.employee = emp
            req_obj.request_type = req_type
            req_obj.subject = subject
            req_obj.details = details
            req_obj.priority = priority
            req_obj.status = "pending"

            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            if start_date:
                req_obj.start_date = start_date
            if end_date:
                req_obj.end_date = end_date

            amount = request.POST.get("amount")
            if amount:
                req_obj.amount = amount

            if "document" in request.FILES:
                req_obj.document = request.FILES["document"]

            req_obj.save()
            messages.success(request, "تم تقديم الطلب بنجاح")
            return redirect("requests_app:list")

    context = {
        "categories": categories,
        "request_types": request_types,
        "employees": employees,
        "page_title": "طلب جديد",
    }
    return render(request, "requests_app/add.html", context)


@login_required
def request_detail(request, pk):
    """تفاصيل طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    context = {
        "req": req_obj,
        "page_title": f"طلب: {req_obj.subject}",
    }
    return render(request, "requests_app/detail.html", context)


@login_required
@require_POST
def request_approve(request, pk):
    """موافقة على طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")
    req_obj.status = "approved"
    req_obj.reviewed_by = request.user
    req_obj.reviewed_at = timezone.now()
    req_obj.review_notes = notes
    req_obj.save()
    messages.success(request, "تمت الموافقة على الطلب")
    return redirect("requests_app:detail", pk=pk)


@login_required
@require_POST
def request_reject(request, pk):
    """رفض طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")
    req_obj.status = "rejected"
    req_obj.reviewed_by = request.user
    req_obj.reviewed_at = timezone.now()
    req_obj.review_notes = notes
    req_obj.save()
    messages.warning(request, "تم رفض الطلب")
    return redirect("requests_app:detail", pk=pk)


@login_required
@require_POST
def request_cancel(request, pk):
    """إلغاء طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    req_obj.status = "cancelled"
    req_obj.save()
    messages.info(request, "تم إلغاء الطلب")
    return redirect("requests_app:list")
''')


# ════════════════════════════════════════════════════════════
# 5. URLs
# ════════════════════════════════════════════════════════════
create_file(os.path.join(app_dir, "urls.py"), """from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    path("",               views.requests_list,   name="list"),
    path("add/",           views.request_add,     name="add"),
    path("<int:pk>/",      views.request_detail,  name="detail"),
    path("<int:pk>/approve/", views.request_approve, name="approve"),
    path("<int:pk>/reject/",  views.request_reject,  name="reject"),
    path("<int:pk>/cancel/",  views.request_cancel,  name="cancel"),
]
""")


# ════════════════════════════════════════════════════════════
# 6. إضافة في settings + urls
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings + urls...")

settings_path = os.path.join(BASE_DIR, "motionhr", "settings.py")
settings = read_file(settings_path)

if "'requests_app'" not in settings:
    settings = settings.replace(
        "'reports',",
        "'reports',\n    'requests_app',"
    )
    write_file(settings_path, settings)

main_urls_path = os.path.join(BASE_DIR, "motionhr", "urls.py")
main_urls = read_file(main_urls_path)

if "requests_app" not in main_urls:
    main_urls = main_urls.replace(
        "path('reports/',",
        "path('requests/',    include('requests_app.urls', namespace='requests_app')),\n    path('reports/',"
    )
    write_file(main_urls_path, main_urls)


# ════════════════════════════════════════════════════════════
# 7. Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء migration...")

import django
django.setup()

from django.core.management import call_command
call_command("makemigrations", "requests_app")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 8. Seed Data — أنواع الطلبات
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء أنواع الطلبات...")

from companies.models import Company
from requests_app.models import RequestCategory, RequestType

company = Company.objects.first()

categories_data = [
    {
        "name": "الإجازات والغياب",
        "icon": "bi-calendar-check",
        "color": "#06B6D4",
        "order": 1,
        "types": [
            ("إجازة سنوية", True, False, False, "إجازة مدفوعة الأجر"),
            ("إجازة مرضية", True, False, True, "بناءً على تقرير طبي"),
            ("إجازة طارئة", True, False, False, "لظروف شخصية مفاجئة"),
            ("إجازة زواج", True, False, True, "إجازة مناسبة"),
            ("إجازة وضع", True, False, True, "إجازة أمومة"),
            ("إجازة حج", True, False, True, "مرة واحدة"),
        ]
    },
    {
        "name": "الطلبات المالية",
        "icon": "bi-cash-stack",
        "color": "#10b981",
        "order": 2,
        "types": [
            ("سلفة مالية", False, True, False, "جزء من الراتب مقدماً"),
            ("زيادة راتب", False, False, False, "طلب مراجعة الراتب"),
            ("مكافأة", False, True, False, "حافز مالي استثنائي"),
            ("تعويض نفقات", False, True, True, "استرداد مبالغ مدفوعة"),
        ]
    },
    {
        "name": "الطلبات الإدارية",
        "icon": "bi-file-earmark-text",
        "color": "#7c3aed",
        "order": 3,
        "types": [
            ("شهادة راتب", False, False, False, "لأغراض بنكية أو رسمية"),
            ("شهادة لمن يهمه الأمر", False, False, False, "خطاب رسمي"),
            ("طلب ترقية", False, False, False, "طلب ترقية وظيفية"),
            ("طلب نقل داخلي", False, False, False, "نقل لإدارة أو فرع آخر"),
            ("استقالة", False, False, False, "إنهاء عقد العمل"),
        ]
    },
    {
        "name": "التطوير والبيئة العملية",
        "icon": "bi-rocket-takeoff",
        "color": "#f59e0b",
        "order": 4,
        "types": [
            ("تدريب أو مؤتمر", True, True, False, "دورة تدريبية أو مؤتمر"),
            ("معدات أو أدوات عمل", False, True, False, "أجهزة أو معدات"),
            ("تعديل مواعيد العمل", True, False, False, "تغيير أوقات العمل"),
        ]
    },
]

for cat_data in categories_data:
    cat, created = RequestCategory.objects.get_or_create(
        company=company,
        name=cat_data["name"],
        defaults={
            "icon": cat_data["icon"],
            "color": cat_data["color"],
            "order": cat_data["order"],
            "is_active": True,
        }
    )
    status = "جديد" if created else "موجود"
    print(f"  {'✅' if created else 'ℹ️ '} فئة: {cat.name} ({status})")

    for type_data in cat_data["types"]:
        name, needs_dates, needs_amount, needs_doc, desc = type_data
        rt, created = RequestType.objects.get_or_create(
            company=company,
            category=cat,
            name=name,
            defaults={
                "description": desc,
                "requires_date_range": needs_dates,
                "requires_amount": needs_amount,
                "requires_document": needs_doc,
                "requires_approval": True,
                "is_active": True,
            }
        )

print("  ✅ تم تجهيز أنواع الطلبات")


# ════════════════════════════════════════════════════════════
# 9. تحديث الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

old_requests = """    <!-- الطلبات -->
    <div class="sidebar-label">الطلبات</div>
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-inbox"></i><span>طلباتي</span>
    </a>
    <a href="{% url 'leaves:leave_request_add' %}"
       class="nav-link {% if '/leaves/add' in request.path %}active{% endif %}">
      <i class="bi bi-plus-circle"></i><span>طلب جديد</span>
    </a>"""

new_requests = """    <!-- الطلبات -->
    <div class="sidebar-label">الطلبات</div>
    <a href="{% url 'requests_app:list' %}"
       class="nav-link {% if '/requests/' in request.path and 'add' not in request.path %}active{% endif %}">
      <i class="bi bi-inbox"></i><span>طلباتي</span>
    </a>
    <a href="{% url 'requests_app:add' %}"
       class="nav-link {% if '/requests/add' in request.path %}active{% endif %}">
      <i class="bi bi-plus-circle"></i><span>طلب جديد</span>
    </a>
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i><span>الإجازات</span>
    </a>"""

if old_requests in sidebar:
    sidebar = sidebar.replace(old_requests, new_requests)
    write_file(sidebar_path, sidebar)
    print("  ✅ Sidebar محدث")
else:
    print("  ℹ️  الـ Sidebar شكله مختلف - محتاج مراجعة")


print("\n" + "=" * 60)
print("  ✅ Patch 31a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ requests_app - نظام طلبات شامل
  2. ✅ RequestCategory + RequestType + EmployeeRequest models
  3. ✅ Views (list + add + detail + approve + reject + cancel)
  4. ✅ URLs
  5. ✅ Migration
  6. ✅ 18 نوع طلب في 4 فئات
  7. ✅ Sidebar محدث

الخطوة الجاية: الـ Templates
""")