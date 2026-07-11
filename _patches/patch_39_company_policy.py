#!/usr/bin/env python3
"""
Patch 39: Company Policy / HR Controls
======================================
1) CompanyPolicy model
2) Company policy page
3) Admin registration
4) Sidebar link
5) Attendance APIs use company policy
6) Seed default policy
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 39: Company Policy / HR Controls")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) إضافة CompanyPolicy model
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/models.py...")

models_path = os.path.join(BASE_DIR, "companies", "models.py")
models_content = read_file(models_path)

policy_model = '''

# ════════════════════════════════════════════════════════════
# سياسات الشركة / HR Controls
# ════════════════════════════════════════════════════════════
class CompanyPolicy(models.Model):
    """
    السياسات العامة للشركة:
    - التأخير
    - الأذونات
    - الأوفر تايم
    - النطاق / المسافة
    - صلاحيات HR
    """

    company = models.OneToOneField(
        "Company",
        on_delete=models.CASCADE,
        related_name="policy",
        verbose_name="الشركة"
    )

    # ── سياسة التأخير ─────────────────────────────────
    grace_period_minutes = models.PositiveSmallIntegerField(
        default=15,
        verbose_name="سماحية التأخير بالدقائق"
    )
    reset_late_counter_monthly = models.BooleanField(
        default=True,
        verbose_name="تصفير عداد التأخير شهريًا"
    )

    late_first_warning_after_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="أول إنذار بعد عدد مرات"
    )
    late_second_warning_after_count = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="ثاني إنذار بعد عدد مرات"
    )
    late_quarter_day_deduction_after_count = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="خصم ربع يوم بعد عدد مرات"
    )
    late_half_day_deduction_after_count = models.PositiveSmallIntegerField(
        default=4,
        verbose_name="خصم نصف يوم بعد عدد مرات"
    )
    late_full_day_deduction_after_count = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="خصم يوم كامل بعد عدد مرات"
    )

    # ── سياسة الأذونات ─────────────────────────────────
    permission_enabled = models.BooleanField(
        default=True,
        verbose_name="الأذونات مفعلة"
    )
    permission_monthly_limit = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="عدد الأذونات المسموح بها شهريًا"
    )
    permission_max_hours_per_request = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=2,
        verbose_name="أقصى عدد ساعات للإذن الواحد"
    )
    permission_requires_approval = models.BooleanField(
        default=True,
        verbose_name="الأذونات تحتاج موافقة"
    )

    # ── سياسة الأوفر تايم ─────────────────────────────
    overtime_enabled = models.BooleanField(
        default=True,
        verbose_name="الأوفر تايم مفعل"
    )
    overtime_start_after_minutes = models.PositiveSmallIntegerField(
        default=30,
        verbose_name="يبدأ الأوفر تايم بعد عدد دقائق"
    )
    overtime_requires_approval = models.BooleanField(
        default=True,
        verbose_name="الأوفر تايم يحتاج موافقة"
    )
    overtime_requires_reason = models.BooleanField(
        default=True,
        verbose_name="الموظف لازم يكتب سبب الأوفر تايم"
    )
    overtime_daily_max_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=4,
        verbose_name="أقصى أوفر تايم يومي"
    )
    overtime_monthly_max_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=40,
        verbose_name="أقصى أوفر تايم شهري"
    )

    # ── سياسة الحضور بالموقع ──────────────────────────
    checkin_requires_location = models.BooleanField(
        default=True,
        verbose_name="الحضور يحتاج موقع GPS"
    )
    checkin_requires_branch_range = models.BooleanField(
        default=True,
        verbose_name="الحضور لازم يكون داخل نطاق الفرع"
    )
    checkout_from_anywhere = models.BooleanField(
        default=True,
        verbose_name="الانصراف مسموح من أي مكان"
    )
    default_checkin_radius = models.PositiveSmallIntegerField(
        default=200,
        verbose_name="النطاق الافتراضي للحضور (متر)"
    )
    distance_tolerance_meters = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="سماحية مسافة إضافية (متر)"
    )

    # ── سياسة الغياب ───────────────────────────────────
    auto_absence_enabled = models.BooleanField(
        default=False,
        verbose_name="تفعيل الغياب التلقائي"
    )
    auto_absence_after_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="بعد الساعة يعتبر غياب"
    )

    # ── صلاحيات HR ─────────────────────────────────────
    hr_can_cancel_attendance = models.BooleanField(
        default=True,
        verbose_name="HR يقدر يلغي حضور/انصراف"
    )
    hr_can_edit_attendance = models.BooleanField(
        default=True,
        verbose_name="HR يقدر يعدل الحضور"
    )
    attendance_edit_reason_required = models.BooleanField(
        default=True,
        verbose_name="سبب التعديل إجباري"
    )

    # ── الطلبات المالية ────────────────────────────────
    manager_can_see_financial_requests = models.BooleanField(
        default=False,
        verbose_name="المدير يشوف الطلبات المالية"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات إضافية"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سياسات الشركة"
        verbose_name_plural = "سياسات الشركات"

    def __str__(self):
        return f"سياسات {self.company.name_ar}"

    @classmethod
    def get_for_company(cls, company):
        obj, _ = cls.objects.get_or_create(
            company=company,
            defaults={
                "grace_period_minutes": 15,
                "permission_monthly_limit": 2,
                "permission_max_hours_per_request": 2,
                "overtime_enabled": True,
                "overtime_start_after_minutes": 30,
                "default_checkin_radius": 200,
                "distance_tolerance_meters": 0,
                "late_first_warning_after_count": 1,
                "late_second_warning_after_count": 2,
                "late_quarter_day_deduction_after_count": 3,
                "late_half_day_deduction_after_count": 4,
                "late_full_day_deduction_after_count": 5,
            }
        )
        return obj
'''

if "class CompanyPolicy" not in models_content:
    models_content += policy_model
    write_file(models_path, models_content)
    print("  ✅ تم إضافة CompanyPolicy model")
else:
    print("  ℹ️  CompanyPolicy موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

import django
django.setup()

from django.core.management import call_command
call_command("makemigrations", "companies")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 3) Admin registration
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/admin.py...")

admin_path = os.path.join(BASE_DIR, "companies", "admin.py")
admin_content = read_file(admin_path)

if "CompanyPolicy" not in admin_content:
    admin_content += '''
from .models import CompanyPolicy

@admin.register(CompanyPolicy)
class CompanyPolicyAdmin(admin.ModelAdmin):
    list_display = [
        "company",
        "grace_period_minutes",
        "permission_monthly_limit",
        "overtime_enabled",
        "default_checkin_radius",
        "hr_can_edit_attendance",
    ]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل CompanyPolicy في Admin")
else:
    print("  ℹ️  CompanyPolicy مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 4) Views
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/views.py...")

views_path = os.path.join(BASE_DIR, "companies", "views.py")
views_content = read_file(views_path)

policy_views = '''

# ════════════════════════════════════════════════════════════
# سياسات الشركة / HR Controls
# ════════════════════════════════════════════════════════════

@login_required
def company_policy_manage(request):
    """إدارة سياسات الشركة"""
    from .models import CompanyPolicy

    company = request.user.company
    if not company:
        messages.error(request, "لا يوجد شركة مرتبطة بحسابك")
        return redirect("dashboard")

    policy = CompanyPolicy.get_for_company(company)

    if request.method == "POST":
        # التأخير
        policy.grace_period_minutes = int(request.POST.get("grace_period_minutes", 15) or 15)
        policy.reset_late_counter_monthly = "reset_late_counter_monthly" in request.POST
        policy.late_first_warning_after_count = int(request.POST.get("late_first_warning_after_count", 1) or 1)
        policy.late_second_warning_after_count = int(request.POST.get("late_second_warning_after_count", 2) or 2)
        policy.late_quarter_day_deduction_after_count = int(request.POST.get("late_quarter_day_deduction_after_count", 3) or 3)
        policy.late_half_day_deduction_after_count = int(request.POST.get("late_half_day_deduction_after_count", 4) or 4)
        policy.late_full_day_deduction_after_count = int(request.POST.get("late_full_day_deduction_after_count", 5) or 5)

        # الأذونات
        policy.permission_enabled = "permission_enabled" in request.POST
        policy.permission_monthly_limit = int(request.POST.get("permission_monthly_limit", 2) or 2)
        policy.permission_max_hours_per_request = request.POST.get("permission_max_hours_per_request", 2) or 2
        policy.permission_requires_approval = "permission_requires_approval" in request.POST

        # الأوفر تايم
        policy.overtime_enabled = "overtime_enabled" in request.POST
        policy.overtime_start_after_minutes = int(request.POST.get("overtime_start_after_minutes", 30) or 30)
        policy.overtime_requires_approval = "overtime_requires_approval" in request.POST
        policy.overtime_requires_reason = "overtime_requires_reason" in request.POST
        policy.overtime_daily_max_hours = request.POST.get("overtime_daily_max_hours", 4) or 4
        policy.overtime_monthly_max_hours = request.POST.get("overtime_monthly_max_hours", 40) or 40

        # الموقع
        policy.checkin_requires_location = "checkin_requires_location" in request.POST
        policy.checkin_requires_branch_range = "checkin_requires_branch_range" in request.POST
        policy.checkout_from_anywhere = "checkout_from_anywhere" in request.POST
        policy.default_checkin_radius = int(request.POST.get("default_checkin_radius", 200) or 200)
        policy.distance_tolerance_meters = int(request.POST.get("distance_tolerance_meters", 0) or 0)

        # الغياب
        policy.auto_absence_enabled = "auto_absence_enabled" in request.POST
        auto_absence_after_time = request.POST.get("auto_absence_after_time")
        if auto_absence_after_time:
            policy.auto_absence_after_time = auto_absence_after_time

        # صلاحيات HR
        policy.hr_can_cancel_attendance = "hr_can_cancel_attendance" in request.POST
        policy.hr_can_edit_attendance = "hr_can_edit_attendance" in request.POST
        policy.attendance_edit_reason_required = "attendance_edit_reason_required" in request.POST

        # الطلبات المالية
        policy.manager_can_see_financial_requests = "manager_can_see_financial_requests" in request.POST

        policy.notes = request.POST.get("notes", "")

        policy.save()
        messages.success(request, "تم حفظ سياسات الشركة بنجاح")
        return redirect("companies:policies")

    context = {
        "policy": policy,
        "page_title": "السياسات والقواعد",
    }
    return render(request, "companies/policies.html", context)
'''

if "def company_policy_manage" not in views_content:
    views_content += policy_views
    write_file(views_path, views_content)
    print("  ✅ تم إضافة view السياسات")
else:
    print("  ℹ️  view السياسات موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 5) URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/urls.py...")

urls_path = os.path.join(BASE_DIR, "companies", "urls.py")
urls_content = read_file(urls_path)

if "name='policies'" not in urls_content:
    if "path('charter/manage/'" in urls_content:
        urls_content = urls_content.replace(
            "path('charter/manage/', views.charter_manage, name='charter_manage'),",
            "path('charter/manage/', views.charter_manage, name='charter_manage'),\n    path('policies/', views.company_policy_manage, name='policies'),"
        )
    else:
        urls_content = urls_content.rstrip()
        if urls_content.endswith("]"):
            urls_content = urls_content[:-1] + "\n    path('policies/', views.company_policy_manage, name='policies'),\n]\n"

    write_file(urls_path, urls_content)
    print("  ✅ تم إضافة URL السياسات")
else:
    print("  ℹ️  URL السياسات موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 6) Template
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء companies/policies.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "companies", "policies.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}السياسات والقواعد{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-sliders me-2" style="color:#06B6D4;"></i>
      السياسات والقواعد
    </h4>
    <p class="text-muted mb-0">
      حدّد قواعد الشركة الخاصة بالحضور، التأخير، الأذونات، الأوفر تايم، وصلاحيات HR
    </p>
  </div>

  <form method="post">
    {% csrf_token %}

    <div class="row g-4">

      <!-- سياسة التأخير -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-clock-history me-2" style="color:#f59e0b;"></i>
              سياسة التأخير
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="mb-3">
              <label class="form-label fw-semibold small">سماحية التأخير (دقيقة)</label>
              <select name="grace_period_minutes" class="form-select">
                {% for n in "5,10,15,20,30"|cut:" "|split:"," %}
                <option value="{{ n }}"
                  {% if policy.grace_period_minutes == n|add:0 %}selected{% endif %}>
                  {{ n }} دقيقة
                </option>
                {% endfor %}
              </select>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="reset_late_counter_monthly" id="resetLate"
                     {% if policy.reset_late_counter_monthly %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="resetLate">
                تصفير عداد التأخير شهريًا
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">أول إنذار بعد</label>
                <input type="number" name="late_first_warning_after_count"
                       class="form-control" value="{{ policy.late_first_warning_after_count }}" min="1">
              </div>
              <div class="col-md-6">
                <label class="form-label small">ثاني إنذار بعد</label>
                <input type="number" name="late_second_warning_after_count"
                       class="form-control" value="{{ policy.late_second_warning_after_count }}" min="1">
              </div>
              <div class="col-md-4">
                <label class="form-label small">ربع يوم بعد</label>
                <input type="number" name="late_quarter_day_deduction_after_count"
                       class="form-control" value="{{ policy.late_quarter_day_deduction_after_count }}" min="1">
              </div>
              <div class="col-md-4">
                <label class="form-label small">نصف يوم بعد</label>
                <input type="number" name="late_half_day_deduction_after_count"
                       class="form-control" value="{{ policy.late_half_day_deduction_after_count }}" min="1">
              </div>
              <div class="col-md-4">
                <label class="form-label small">يوم كامل بعد</label>
                <input type="number" name="late_full_day_deduction_after_count"
                       class="form-control" value="{{ policy.late_full_day_deduction_after_count }}" min="1">
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- سياسة الأذونات -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-hourglass-split me-2" style="color:#10b981;"></i>
              سياسة الأذونات
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="permission_enabled" id="permEnabled"
                     {% if policy.permission_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="permEnabled">
                الأذونات مفعلة
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">عدد الأذونات شهريًا</label>
                <input type="number" name="permission_monthly_limit"
                       class="form-control" value="{{ policy.permission_monthly_limit }}" min="0">
              </div>
              <div class="col-md-6">
                <label class="form-label small">أقصى ساعات للإذن الواحد</label>
                <input type="number" step="0.5" name="permission_max_hours_per_request"
                       class="form-control" value="{{ policy.permission_max_hours_per_request }}" min="0">
              </div>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="permission_requires_approval" id="permApproval"
                     {% if policy.permission_requires_approval %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="permApproval">
                الإذن يحتاج موافقة
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- سياسة الأوفر تايم -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-lightning-charge me-2" style="color:#7c3aed;"></i>
              سياسة الأوفر تايم
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="overtime_enabled" id="otEnabled"
                     {% if policy.overtime_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="otEnabled">
                الأوفر تايم مفعّل
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">يبدأ بعد (دقيقة)</label>
                <input type="number" name="overtime_start_after_minutes"
                       class="form-control" value="{{ policy.overtime_start_after_minutes }}" min="0">
              </div>
              <div class="col-md-6">
                <label class="form-label small">أقصى أوفر تايم يومي</label>
                <input type="number" step="0.5" name="overtime_daily_max_hours"
                       class="form-control" value="{{ policy.overtime_daily_max_hours }}" min="0">
              </div>
              <div class="col-md-6">
                <label class="form-label small">أقصى أوفر تايم شهري</label>
                <input type="number" step="0.5" name="overtime_monthly_max_hours"
                       class="form-control" value="{{ policy.overtime_monthly_max_hours }}" min="0">
              </div>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="overtime_requires_approval" id="otApproval"
                     {% if policy.overtime_requires_approval %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="otApproval">
                يحتاج موافقة المدير
              </label>
            </div>

            <div class="form-check form-switch mt-2">
              <input class="form-check-input" type="checkbox"
                     name="overtime_requires_reason" id="otReason"
                     {% if policy.overtime_requires_reason %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="otReason">
                الموظف لازم يكتب السبب
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- سياسة الموقع -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-geo-alt me-2" style="color:#06B6D4;"></i>
              سياسة الحضور بالموقع
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="checkin_requires_location" id="gpsRequired"
                     {% if policy.checkin_requires_location %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="gpsRequired">
                الحضور يحتاج GPS
              </label>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="checkin_requires_branch_range" id="rangeRequired"
                     {% if policy.checkin_requires_branch_range %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="rangeRequired">
                الحضور لازم يكون داخل نطاق الفرع
              </label>
            </div>

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="checkout_from_anywhere" id="checkoutAnywhere"
                     {% if policy.checkout_from_anywhere %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="checkoutAnywhere">
                الانصراف من أي مكان
              </label>
            </div>

            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label small">النطاق الافتراضي (متر)</label>
                <input type="number" name="default_checkin_radius"
                       class="form-control" value="{{ policy.default_checkin_radius }}" min="0">
                <small class="text-muted">يمكن تغييره لكل فرع</small>
              </div>
              <div class="col-md-6">
                <label class="form-label small">سماحية مسافة إضافية (متر)</label>
                <input type="number" name="distance_tolerance_meters"
                       class="form-control" value="{{ policy.distance_tolerance_meters }}" min="0">
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- الغياب + صلاحيات HR -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-person-x me-2" style="color:#ef4444;"></i>
              الغياب وصلاحيات HR
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="auto_absence_enabled" id="autoAbsence"
                     {% if policy.auto_absence_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="autoAbsence">
                تفعيل الغياب التلقائي
              </label>
            </div>

            <div class="mb-3">
              <label class="form-label small">بعد الساعة يعتبر غياب</label>
              <input type="time" name="auto_absence_after_time"
                     class="form-control"
                     value="{{ policy.auto_absence_after_time|time:'H:i'|default:'' }}">
            </div>

            <hr>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="hr_can_cancel_attendance" id="hrCancel"
                     {% if policy.hr_can_cancel_attendance %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="hrCancel">
                HR يقدر يلغي حضور/انصراف
              </label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="hr_can_edit_attendance" id="hrEdit"
                     {% if policy.hr_can_edit_attendance %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="hrEdit">
                HR يقدر يعدل الحضور
              </label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="attendance_edit_reason_required" id="editReason"
                     {% if policy.attendance_edit_reason_required %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="editReason">
                سبب التعديل إجباري
              </label>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="manager_can_see_financial_requests" id="mgrFinancial"
                     {% if policy.manager_can_see_financial_requests %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="mgrFinancial">
                المدير يشوف الطلبات المالية
              </label>
            </div>

          </div>
        </div>
      </div>

      <!-- ملاحظات -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-journal-text me-2" style="color:#6b7280;"></i>
              ملاحظات إضافية
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <textarea name="notes" class="form-control" rows="10"
                      placeholder="أي سياسات أو ملاحظات إضافية...">{{ policy.notes }}</textarea>
          </div>
        </div>
      </div>

    </div>

    <!-- حفظ -->
    <div class="mt-4">
      <button type="submit" class="btn btn-lg text-white px-5"
              style="background:#06B6D4; border-radius:12px;">
        <i class="bi bi-check-lg me-2"></i>
        حفظ السياسات
      </button>
    </div>

  </form>

</div>
{% endblock %}
"""
)

# ════════════════════════════════════════════════════════════
# 7) تحديث Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "companies:policies" not in sidebar:
    old_link = """      <a href="{% url 'companies:charter_manage' %}"
         class="nav-link {% if 'charter/manage' in request.path %}active{% endif %}">
        <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
      </a>"""

    new_link = """      <a href="{% url 'companies:charter_manage' %}"
         class="nav-link {% if 'charter/manage' in request.path %}active{% endif %}">
        <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
      </a>
      <a href="{% url 'companies:policies' %}"
         class="nav-link {% if 'companies/policies' in request.path %}active{% endif %}">
        <i class="bi bi-sliders"></i><span>السياسات والقواعد</span>
      </a>"""

    if old_link in sidebar:
        sidebar = sidebar.replace(old_link, new_link)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة رابط السياسات")
    else:
        print("  ℹ️  مكان الإدراج مختلف")
else:
    print("  ℹ️  رابط السياسات موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 8) تحديث attendance/views.py لاستخدام CompanyPolicy
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py لاستخدام السياسة...")

attendance_views_path = os.path.join(BASE_DIR, "attendance", "views.py")
attendance_views = read_file(attendance_views_path)

smart_policy_patch = '''

# ════════════════════════════════════════════════════════════
# Policy Helper for Attendance
# ════════════════════════════════════════════════════════════
def _get_company_policy(company):
    try:
        from companies.models import CompanyPolicy
        return CompanyPolicy.get_for_company(company)
    except Exception:
        return None
'''

if "_get_company_policy" not in attendance_views:
    attendance_views += smart_policy_patch
    write_file(attendance_views_path, attendance_views)
    print("  ✅ تم إضافة policy helper")
else:
    print("  ℹ️  policy helper موجود")


# نضيف ملاحظة فقط لو الـ API موجودة
if "def smart_api_check_in" in attendance_views:
    print("  ℹ️  smart_api_check_in موجود — يستخدم branch radius حاليًا")
    print("  ℹ️  في Patch لاحق هنربط كل التفاصيل الحسابية الأعمق (warnings / deductions / overtime approval)")


# ════════════════════════════════════════════════════════════
# 9) Seed default policy
# ════════════════════════════════════════════════════════════
print("\n🌱 Seed default policy...")

from companies.models import Company, CompanyPolicy

for company in Company.objects.all():
    policy = CompanyPolicy.get_for_company(company)
    print(f"  ✅ سياسة جاهزة لـ: {company.name_ar}")

print("\n" + "=" * 60)
print("  ✅ Patch 39 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ CompanyPolicy model
  2. ✅ Migration
  3. ✅ Admin registration
  4. ✅ company_policy_manage view
  5. ✅ URL: /companies/policies/
  6. ✅ Template كاملة للسياسات
  7. ✅ Sidebar link
  8. ✅ Seed افتراضي لكل شركة

السياسات الموجودة:
  - سماحية التأخير
  - مراحل الإنذار/الخصم
  - عدد الأذونات شهريًا
  - أقصى ساعات الإذن
  - الأوفر تايم
  - النطاق والمسافة
  - الغياب التلقائي
  - صلاحيات HR
  - رؤية المدير للطلبات المالية

جرب:
  demo_admin / hr_manager
  ثم:
  /companies/policies/
""")