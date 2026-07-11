#!/usr/bin/env python3
"""
Patch 32: Employee Balance + Deductions
========================================
1. الموظف يشوف رصيد إجازاته في الـ Sidebar أو Dashboard
2. نظام الخصومات (Deductions)
3. الموظف يشوف خصوماته مع الأسباب (شفافية)
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
print("  Patch 32: Balance + Deductions")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. نموذج الخصومات في employees/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة نموذج الخصومات...")

emp_models_path = os.path.join(BASE_DIR, "employees", "models.py")
emp_models = read_file(emp_models_path)

deduction_model = '''

class Deduction(TenantModel):
    """خصومات الموظف"""

    DEDUCTION_TYPES = [
        ("late",        "تأخير"),
        ("absence",     "غياب"),
        ("early_leave", "انصراف مبكر"),
        ("violation",   "مخالفة"),
        ("loan",        "قسط سلفة"),
        ("insurance",   "تأمينات"),
        ("tax",         "ضرائب"),
        ("penalty",     "جزاء إداري"),
        ("other",       "أخرى"),
    ]

    employee = models.ForeignKey(
        "Employee",
        on_delete=models.CASCADE,
        related_name="deductions",
        verbose_name="الموظف"
    )
    deduction_type = models.CharField(
        max_length=20,
        choices=DEDUCTION_TYPES,
        default="other",
        verbose_name="نوع الخصم"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="المبلغ"
    )
    date = models.DateField(
        verbose_name="التاريخ"
    )
    reason = models.TextField(
        verbose_name="السبب"
    )
    month = models.PositiveSmallIntegerField(
        verbose_name="الشهر"
    )
    year = models.PositiveSmallIntegerField(
        verbose_name="السنة"
    )
    is_visible_to_employee = models.BooleanField(
        default=True,
        verbose_name="ظاهر للموظف"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات إدارية"
    )

    class Meta:
        verbose_name = "خصم"
        verbose_name_plural = "الخصومات"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee} - {self.get_deduction_type_display()} - {self.amount}"
'''

if "class Deduction" not in emp_models:
    emp_models += deduction_model
    write_file(emp_models_path, emp_models)
    print("  ✅ تم إضافة Deduction model")
else:
    print("  ℹ️  Deduction model موجود")


# ════════════════════════════════════════════════════════════
# 2. Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء migration...")

import django
django.setup()

from django.core.management import call_command
call_command("makemigrations", "employees")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 3. Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employees/admin.py...")

admin_path = os.path.join(BASE_DIR, "employees", "admin.py")
admin_content = read_file(admin_path)

if "Deduction" not in admin_content:
    admin_content += '''
from .models import Deduction

@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ["employee", "deduction_type", "amount", "date", "reason"]
    list_filter = ["deduction_type", "month", "year"]
    search_fields = ["employee__first_name_ar", "reason"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ Deduction مسجل في Admin")


# ════════════════════════════════════════════════════════════
# 4. Views - صفحة رصيد الإجازات والخصومات للموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة views للموظف...")

emp_views_path = os.path.join(BASE_DIR, "employees", "views.py")
emp_views = read_file(emp_views_path)

new_views = '''

# ════════════════════════════════════════════════════════════
# صفحة الموظف — رصيد الإجازات والخصومات
# ════════════════════════════════════════════════════════════

@login_required
def my_balance_view(request):
    """رصيد إجازاتي"""
    from leaves.models import LeaveBalance
    from django.utils import timezone

    current_year = timezone.now().year
    emp = None
    balances = []

    if request.current_employee:
        emp = request.current_employee
    else:
        emp = Employee.objects.filter(user=request.user).first()

    if emp:
        balances = LeaveBalance.objects.filter(
            company=request.user.company,
            employee=emp,
            year=current_year
        ).select_related("leave_type")

    context = {
        "employee": emp,
        "balances": balances,
        "current_year": current_year,
        "page_title": "رصيد إجازاتي",
    }
    return render(request, "employees/my_balance.html", context)


@login_required
def my_deductions_view(request):
    """خصوماتي"""
    from django.utils import timezone
    from .models import Deduction

    emp = None
    deductions = []
    current_month = timezone.now().month
    current_year = timezone.now().year

    if request.current_employee:
        emp = request.current_employee
    else:
        emp = Employee.objects.filter(user=request.user).first()

    month = request.GET.get("month")
    year = request.GET.get("year")

    if emp:
        qs = Deduction.objects.filter(
            company=request.user.company,
            employee=emp,
            is_visible_to_employee=True
        )
        if month:
            qs = qs.filter(month=int(month))
        if year:
            qs = qs.filter(year=int(year))

        deductions = qs.order_by("-date")

    context = {
        "employee": emp,
        "deductions": deductions,
        "current_month": current_month,
        "current_year": current_year,
        "months": range(1, 13),
        "years": range(current_year - 1, current_year + 1),
        "page_title": "خصوماتي",
    }
    return render(request, "employees/my_deductions.html", context)
'''

if "my_balance_view" not in emp_views:
    emp_views += new_views
    write_file(emp_views_path, emp_views)
    print("  ✅ تم إضافة views")
else:
    print("  ℹ️  views موجودة")


# ════════════════════════════════════════════════════════════
# 5. URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employees/urls.py...")

urls_path = os.path.join(BASE_DIR, "employees", "urls.py")
urls = read_file(urls_path)

if "my-balance" not in urls:
    urls = urls.rstrip()
    if urls.endswith("]"):
        urls = urls[:-1]
        urls += "\n    path('my-balance/', views.my_balance_view, name='my_balance'),\n"
        urls += "    path('my-deductions/', views.my_deductions_view, name='my_deductions'),\n"
        urls += "]\n"
        write_file(urls_path, urls)
        print("  ✅ URLs محدثة")
else:
    print("  ℹ️  URLs موجودة")


# ════════════════════════════════════════════════════════════
# 6. Template — رصيد إجازاتي
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء my_balance.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "employees", "my_balance.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}رصيد إجازاتي{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-wallet2 me-2" style="color:#06B6D4;"></i>
      رصيد إجازاتي — {{ current_year }}
    </h4>
    {% if employee %}
    <p class="text-muted mb-0">
      {{ employee.full_name_ar }} | {{ employee.employee_code }}
    </p>
    {% endif %}
  </div>

  {% if balances %}
  <div class="row g-3">
    {% for bal in balances %}
    <div class="col-md-6 col-lg-4">
      <div class="card border-0 shadow-sm h-100"
           style="border-right: 4px solid {{ bal.leave_type.color }} !important;">
        <div class="card-body p-4">

          <div class="d-flex align-items-center justify-content-between mb-3">
            <h6 class="fw-bold mb-0">{{ bal.leave_type.name }}</h6>
            <span class="badge rounded-pill"
                  style="background:{{ bal.leave_type.color }};">
              {% if bal.leave_type.is_paid %}بمرتب{% else %}بدون مرتب{% endif %}
            </span>
          </div>

          <!-- الأرقام -->
          <div class="row g-2 text-center mb-3">
            <div class="col-4">
              <div class="p-2 rounded" style="background:#e0f7fa;">
                <div class="fw-black fs-4" style="color:#06B6D4;">{{ bal.total_days }}</div>
                <small class="text-muted">الإجمالي</small>
              </div>
            </div>
            <div class="col-4">
              <div class="p-2 rounded" style="background:#fde8e8;">
                <div class="fw-black fs-4 text-danger">{{ bal.used_days }}</div>
                <small class="text-muted">المستخدم</small>
              </div>
            </div>
            <div class="col-4">
              <div class="p-2 rounded" style="background:#e8f5e9;">
                <div class="fw-black fs-4 text-success">{{ bal.remaining_days_display }}</div>
                <small class="text-muted">المتبقي</small>
              </div>
            </div>
          </div>

          <!-- Progress -->
          <div class="progress" style="height:8px;">
            {% widthratio bal.used_days bal.total_days 100 as used_pct %}
            <div class="progress-bar
              {% if bal.remaining_days <= 3 %}bg-danger
              {% elif bal.remaining_days <= 7 %}bg-warning
              {% else %}bg-success{% endif %}"
                 style="width: {% widthratio bal.used_days bal.total_days 100 %}%">
            </div>
          </div>

          {% if bal.pending_days > 0 %}
          <div class="mt-2 text-end">
            <small class="text-warning fw-semibold">
              <i class="bi bi-hourglass-split me-1"></i>
              {{ bal.pending_days }} يوم قيد الانتظار
            </small>
          </div>
          {% endif %}

        </div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-wallet2" style="font-size:4rem; color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد أرصدة إجازات</h5>
      <p class="text-muted">تواصل مع HR لتحديد رصيد إجازاتك</p>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 7. Template — خصوماتي
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء my_deductions.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "employees", "my_deductions.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}خصوماتي{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-receipt-cutoff me-2" style="color:#e91e63;"></i>
        خصوماتي
      </h4>
      {% if employee %}
      <p class="text-muted mb-0">
        {{ employee.full_name_ar }} | {{ employee.employee_code }}
      </p>
      {% endif %}
    </div>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" class="d-flex gap-3 align-items-center flex-wrap">
        <select name="month" class="form-select" style="max-width:140px;">
          <option value="">كل الشهور</option>
          {% for m in months %}
          <option value="{{ m }}"
            {% if request.GET.month == m|stringformat:"d" %}selected{% endif %}>
            شهر {{ m }}
          </option>
          {% endfor %}
        </select>
        <select name="year" class="form-select" style="max-width:120px;">
          {% for y in years %}
          <option value="{{ y }}"
            {% if request.GET.year == y|stringformat:"d" %}selected{% endif %}>
            {{ y }}
          </option>
          {% endfor %}
        </select>
        <button type="submit" class="btn btn-sm"
                style="background:#06B6D4; color:white;">عرض</button>
        <a href="{% url 'employees:my_deductions' %}"
           class="btn btn-light btn-sm">إعادة تعيين</a>
      </form>
    </div>
  </div>

  {% if deductions %}

  <!-- إجمالي -->
  <div class="row g-3 mb-4">
    <div class="col-md-4">
      <div class="card border-0 shadow-sm text-center p-3">
        <div class="fs-3 fw-bold text-danger">
          {% load custom_filters %}
          {{ deductions|length }}
        </div>
        <small class="text-muted">عدد الخصومات</small>
      </div>
    </div>
  </div>

  <!-- الجدول -->
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">التاريخ</th>
            <th>النوع</th>
            <th>المبلغ</th>
            <th>السبب</th>
          </tr>
        </thead>
        <tbody>
          {% for ded in deductions %}
          <tr>
            <td class="px-4">{{ ded.date|date:"d/m/Y" }}</td>
            <td>
              <span class="badge
                {% if ded.deduction_type == 'late' %}bg-warning text-dark
                {% elif ded.deduction_type == 'absence' %}bg-danger
                {% elif ded.deduction_type == 'penalty' %}bg-danger
                {% elif ded.deduction_type == 'loan' %}bg-info
                {% elif ded.deduction_type == 'insurance' %}bg-secondary
                {% else %}bg-secondary{% endif %}">
                {{ ded.get_deduction_type_display }}
              </span>
            </td>
            <td class="fw-bold text-danger">{{ ded.amount }} ج.م</td>
            <td class="text-muted small">{{ ded.reason }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-emoji-smile" style="font-size:4rem; color:#10b981;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد خصومات</h5>
      <p class="text-muted">ممتاز! سجلك نظيف</p>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 8. تحديث الـ Sidebar — إضافة رصيدي + خصوماتي
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# نضيف قبل قسم "حسابي"
old_my_account = """    <!-- حسابي -->
    <div class="sidebar-label">حسابي</div>"""

new_my_account = """    <!-- رصيدي وخصوماتي -->
    {% if request.current_employee or request.user.role == 'employee' %}
    <div class="sidebar-label">حسابي المالي</div>
    <a href="{% url 'employees:my_balance' %}"
       class="nav-link {% if 'my-balance' in request.path %}active{% endif %}">
      <i class="bi bi-wallet2"></i><span>رصيد إجازاتي</span>
    </a>
    <a href="{% url 'employees:my_deductions' %}"
       class="nav-link {% if 'my-deductions' in request.path %}active{% endif %}">
      <i class="bi bi-receipt-cutoff"></i><span>خصوماتي</span>
    </a>
    {% endif %}

    <!-- حسابي -->
    <div class="sidebar-label">حسابي</div>"""

if old_my_account in sidebar:
    sidebar = sidebar.replace(old_my_account, new_my_account)
    write_file(sidebar_path, sidebar)
    print("  ✅ تم إضافة رصيدي وخصوماتي في الـ Sidebar")
else:
    print("  ℹ️  قسم حسابي شكله مختلف")


# ════════════════════════════════════════════════════════════
# 9. Seed Data — خصومات تجريبية
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء خصومات تجريبية...")

from employees.models import Employee, Deduction
from companies.models import Company
from datetime import date
from decimal import Decimal

company = Company.objects.first()

if company and not Deduction.objects.filter(company=company).exists():
    emps = Employee.objects.filter(company=company)[:3]
    today = date.today()

    sample_deductions = [
        (emps[0] if len(emps) > 0 else None, "late", Decimal("50"), "تأخير 25 دقيقة يوم 5/7"),
        (emps[0] if len(emps) > 0 else None, "late", Decimal("30"), "تأخير 15 دقيقة يوم 8/7"),
        (emps[1] if len(emps) > 1 else None, "absence", Decimal("300"), "غياب بدون إذن يوم 3/7"),
        (emps[2] if len(emps) > 2 else None, "loan", Decimal("500"), "قسط سلفة شهر يوليو"),
        (emps[2] if len(emps) > 2 else None, "insurance", Decimal("200"), "حصة التأمينات الاجتماعية"),
    ]

    for emp, dtype, amount, reason in sample_deductions:
        if emp:
            Deduction.objects.create(
                company=company,
                employee=emp,
                deduction_type=dtype,
                amount=amount,
                date=today,
                reason=reason,
                month=today.month,
                year=today.year,
                is_visible_to_employee=True,
            )

    print("  ✅ تم إنشاء خصومات تجريبية")
else:
    print("  ℹ️  خصومات موجودة أو لا يوجد شركة")


print("\n" + "=" * 60)
print("  ✅ Patch 32 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ نموذج الخصومات Deduction
  2. ✅ Migration
  3. ✅ Admin registration
  4. ✅ my_balance_view — رصيد إجازاتي
  5. ✅ my_deductions_view — خصوماتي
  6. ✅ my_balance.html — صفحة احترافية
  7. ✅ my_deductions.html — جدول شفاف
  8. ✅ Sidebar محدث
  9. ✅ خصومات تجريبية

جرب بـ emp10003 / Emp@12345:
  - رصيد إجازاتي
  - خصوماتي
""")