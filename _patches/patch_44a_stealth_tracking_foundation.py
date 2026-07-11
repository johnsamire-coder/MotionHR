#!/usr/bin/env python3
"""
Patch 44a: Stealth Tracking Foundation
======================================
1) CompanyPolicy fields for stealth tracking
2) Employee-level stealth flag
3) TrackingAlert model
4) Admin registration
5) Manager/HR pages to enable tracking per employee
6) Charter mandatory clause if stealth enabled
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command


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
print("  Patch 44a: Stealth Tracking Foundation")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) employees/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employees/models.py...")

emp_models_path = os.path.join(BASE_DIR, "employees", "models.py")
emp_models = read_file(emp_models_path)

emp_field_block = '''
    stealth_tracking_enabled = models.BooleanField(
        default=False,
        verbose_name="التتبع الصامت مفعل"
    )
'''

if "stealth_tracking_enabled" not in emp_models:
    if "is_field_worker" in emp_models:
        emp_models = emp_models.replace(
            "    is_field_worker",
            emp_field_block + "\n    is_field_worker",
            1
        )
    else:
        emp_models = emp_models.replace(
            "    status",
            emp_field_block + "\n    status",
            1
        )
    write_file(emp_models_path, emp_models)
    print("  ✅ تم إضافة stealth_tracking_enabled للموظف")
else:
    print("  ℹ️  stealth_tracking_enabled موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) companies/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/models.py...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

policy_fields = '''
    # ── التتبع الصامت / Workforce Monitoring ───────────
    stealth_tracking_enabled = models.BooleanField(
        default=False,
        verbose_name="تفعيل التتبع الصامت"
    )
    stealth_tracking_alert_after_minutes = models.PositiveSmallIntegerField(
        default=15,
        verbose_name="تنبيه بعد عدد دقائق خارج النطاق"
    )
    stealth_tracking_notify_manager = models.BooleanField(
        default=True,
        verbose_name="تنبيه المدير المباشر"
    )
    stealth_tracking_notify_hr = models.BooleanField(
        default=False,
        verbose_name="تنبيه HR"
    )
    stealth_tracking_notify_company_admin = models.BooleanField(
        default=False,
        verbose_name="تنبيه صاحب الشركة"
    )
    stealth_tracking_requires_charter_clause = models.BooleanField(
        default=True,
        verbose_name="إلزام بند المراقبة في الميثاق"
    )
'''

if "stealth_tracking_enabled = models.BooleanField" not in comp_models:
    if "    notes = models.TextField(" in comp_models:
        comp_models = comp_models.replace(
            "    notes = models.TextField(",
            policy_fields + "\n    notes = models.TextField(",
            1
        )
    else:
        comp_models = comp_models.replace(
            "    created_at = models.DateTimeField(auto_now_add=True)",
            policy_fields + "\n    created_at = models.DateTimeField(auto_now_add=True)",
            1
        )
    write_file(comp_models_path, comp_models)
    print("  ✅ تم إضافة سياسات التتبع الصامت")
else:
    print("  ℹ️  سياسات التتبع الصامت موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 3) attendance/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/models.py...")

att_models_path = os.path.join(BASE_DIR, "attendance", "models.py")
att_models = read_file(att_models_path)

tracking_alert_model = '''

class TrackingAlert(TenantModel):
    """تنبيه تتبع صامت عند الخروج من النطاق أثناء العمل"""

    STATUS_CHOICES = [
        ("open", "مفتوح"),
        ("resolved", "تمت المعالجة"),
        ("ignored", "تم التجاهل"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="tracking_alerts",
        verbose_name="الموظف"
    )
    date = models.DateField(
        verbose_name="التاريخ"
    )
    started_at = models.DateTimeField(
        verbose_name="وقت بداية الخروج من النطاق"
    )
    last_seen_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="آخر وقت رصد"
    )
    minutes_outside = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="عدد الدقائق خارج النطاق"
    )

    last_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="آخر خط عرض"
    )
    last_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True,
        verbose_name="آخر خط طول"
    )
    last_address = models.TextField(
        blank=True,
        verbose_name="آخر عنوان"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        verbose_name="الحالة"
    )

    notified_manager = models.BooleanField(
        default=False,
        verbose_name="تم تنبيه المدير"
    )
    notified_hr = models.BooleanField(
        default=False,
        verbose_name="تم تنبيه HR"
    )
    notified_company_admin = models.BooleanField(
        default=False,
        verbose_name="تم تنبيه صاحب الشركة"
    )

    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="resolved_tracking_alerts",
        verbose_name="تمت المعالجة بواسطة"
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت المعالجة"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "تنبيه تتبع"
        verbose_name_plural = "تنبيهات التتبع"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.minutes_outside} دقيقة"
'''

if "class TrackingAlert" not in att_models:
    att_models += tracking_alert_model
    write_file(att_models_path, att_models)
    print("  ✅ تم إضافة TrackingAlert model")
else:
    print("  ℹ️  TrackingAlert موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 4) Admin registrations
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث admin files...")

# employees/admin.py
emp_admin_path = os.path.join(BASE_DIR, "employees", "admin.py")
emp_admin = read_file(emp_admin_path)
if "stealth_tracking_enabled" not in emp_admin:
    # مجرد تذكير، مش هنعدل EmployeeAdmin بتفصيل كبير لتجنب الكسر
    if "list_display" in emp_admin and "EmployeeAdmin" in emp_admin:
        print("  ℹ️  EmployeeAdmin موجود — يمكن تعديله لاحقًا يدويًا لو حبيت تضيف العمود")
else:
    print("  ℹ️  admin الموظفين محدث بالفعل")

# companies/admin.py
comp_admin_path = os.path.join(BASE_DIR, "companies", "admin.py")
comp_admin = read_file(comp_admin_path)
if "stealth_tracking_enabled" not in comp_admin and "CompanyPolicyAdmin" in comp_admin:
    comp_admin = comp_admin.replace(
        '    list_display = [\n        "company",\n        "grace_period_minutes",\n        "permission_monthly_limit",\n        "overtime_enabled",\n        "default_checkin_radius",\n        "hr_can_edit_attendance",\n    ]',
        '''    list_display = [
        "company",
        "grace_period_minutes",
        "permission_monthly_limit",
        "overtime_enabled",
        "default_checkin_radius",
        "stealth_tracking_enabled",
        "hr_can_edit_attendance",
    ]'''
    )
    write_file(comp_admin_path, comp_admin)
    print("  ✅ تم تحديث CompanyPolicyAdmin")
else:
    print("  ℹ️  CompanyPolicyAdmin محدث بالفعل أو النص مختلف")

# attendance/admin.py
att_admin_path = os.path.join(BASE_DIR, "attendance", "admin.py")
att_admin = read_file(att_admin_path)
if "TrackingAlert" not in att_admin:
    att_admin += '''

from .models import TrackingAlert

@admin.register(TrackingAlert)
class TrackingAlertAdmin(admin.ModelAdmin):
    list_display = [
        "employee", "date", "minutes_outside",
        "status", "notified_manager", "notified_hr",
        "notified_company_admin", "started_at"
    ]
    list_filter = ["status", "date", "notified_manager", "notified_hr", "notified_company_admin"]
'''
    write_file(att_admin_path, att_admin)
    print("  ✅ تم تسجيل TrackingAlert في Admin")
else:
    print("  ℹ️  TrackingAlert مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 5) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

call_command("makemigrations", "employees", "companies", "attendance")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 6) companies/views.py → helper + save policy + charter clause
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/views.py...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

charter_helper = '''

def _stealth_tracking_clause_text():
    return (
        "تحتفظ الشركة بحق متابعة الأداء المهني والتحقق من الالتزام أثناء ساعات العمل "
        "من خلال وسائل التتبع المناسبة، وذلك في إطار تنظيم العمل وحماية مصالح الشركة، "
        "وبما لا يتعارض مع سياسات الشركة والأنظمة المعمول بها."
    )


def _ensure_stealth_clause(company):
    """
    لو التتبع الصامت مفعّل والبند مش موجود، نضيفه تلقائيًا للميثاق
    """
    try:
        from .models import CompanyPolicy, WorkCharter
        policy = CompanyPolicy.get_for_company(company)
        if not policy.stealth_tracking_enabled:
            return

        if not policy.stealth_tracking_requires_charter_clause:
            return

        charter, _ = WorkCharter.objects.get_or_create(
            company=company,
            defaults={
                "title": "ميثاق العمل",
                "introduction": "يرجى قراءة الميثاق والموافقة عليه.",
                "content": "",
                "version": 1,
                "is_active": True,
                "is_mandatory": True,
            }
        )

        clause = _stealth_tracking_clause_text()
        if clause not in (charter.content or ""):
            if charter.content.strip():
                charter.content = charter.content.strip() + "\\n\\n" + clause
            else:
                charter.content = clause
            charter.save()
    except Exception:
        pass
'''

if "_stealth_tracking_clause_text" not in comp_views:
    comp_views += charter_helper
    write_file(comp_views_path, comp_views)
    print("  ✅ تم إضافة helper الميثاق")
else:
    print("  ℹ️  helper الميثاق موجود بالفعل")

# ربط الحفظ في company_policy_manage
comp_views = read_file(comp_views_path)
if "stealth_tracking_enabled" not in comp_views:
    old_part = '''        # سياسات الحضور الاستثنائي
        policy.off_day_checkin_mode = request.POST.get("off_day_checkin_mode", "allow_notify_hr")
        policy.leave_day_checkin_mode = request.POST.get("leave_day_checkin_mode", "block")
        policy.unplanned_checkin_mode = request.POST.get("unplanned_checkin_mode", "create_exception")

        policy.notes = request.POST.get("notes", "")

        policy.save()
        messages.success(request, "تم حفظ سياسات الشركة بنجاح")
        return redirect("companies:policies")'''
    new_part = '''        # سياسات الحضور الاستثنائي
        policy.off_day_checkin_mode = request.POST.get("off_day_checkin_mode", "allow_notify_hr")
        policy.leave_day_checkin_mode = request.POST.get("leave_day_checkin_mode", "block")
        policy.unplanned_checkin_mode = request.POST.get("unplanned_checkin_mode", "create_exception")

        # التتبع الصامت
        policy.stealth_tracking_enabled = "stealth_tracking_enabled" in request.POST
        policy.stealth_tracking_alert_after_minutes = int(request.POST.get("stealth_tracking_alert_after_minutes", 15) or 15)
        policy.stealth_tracking_notify_manager = "stealth_tracking_notify_manager" in request.POST
        policy.stealth_tracking_notify_hr = "stealth_tracking_notify_hr" in request.POST
        policy.stealth_tracking_notify_company_admin = "stealth_tracking_notify_company_admin" in request.POST
        policy.stealth_tracking_requires_charter_clause = "stealth_tracking_requires_charter_clause" in request.POST

        policy.notes = request.POST.get("notes", "")

        policy.save()

        # تأكيد بند الميثاق
        _ensure_stealth_clause(company)

        messages.success(request, "تم حفظ سياسات الشركة بنجاح")
        return redirect("companies:policies")'''
    if old_part in comp_views:
        comp_views = comp_views.replace(old_part, new_part)
        write_file(comp_views_path, comp_views)
        print("  ✅ تم ربط حفظ سياسات التتبع الصامت")
    else:
        print("  ℹ️  لم أجد block الحفظ المتوقع — قد يكون اتعدل قبل كده")
else:
    print("  ℹ️  حفظ سياسات التتبع الصامت مربوط بالفعل")


# ════════════════════════════════════════════════════════════
# 7) attendance/views.py → manage + alerts pages
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py (management pages)...")

att_views_path = os.path.join(BASE_DIR, "attendance", "views.py")
att_views = read_file(att_views_path)

stealth_views = '''

# ════════════════════════════════════════════════════════════
# Stealth Tracking Management
# ════════════════════════════════════════════════════════════

@login_required
def stealth_tracking_manage(request):
    """
    المدير / HR / صاحب الشركة يديروا مين عليه تتبع صامت
    """
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company
    policy = _get_company_policy(company)

    if not policy or not getattr(policy, "stealth_tracking_enabled", False):
        messages.warning(request, "ميزة التتبع الصامت غير مفعلة في سياسات الشركة")
        return redirect("companies:policies")

    if role == "manager":
        manager_emp = Employee.all_objects.filter(user=request.user).first()
        employees = Employee.all_objects.filter(
            company=company,
            direct_manager=manager_emp,
            status="active"
        ).select_related("department", "job_title")
    else:
        employees = Employee.all_objects.filter(
            company=company,
            status="active"
        ).select_related("department", "job_title")

    if request.method == "POST":
        emp_id = request.POST.get("employee_id")
        emp = get_object_or_404(Employee.all_objects, pk=emp_id, company=company)

        # manager ما يعدلش غير فريقه
        if role == "manager":
            manager_emp = Employee.all_objects.filter(user=request.user).first()
            if emp.direct_manager_id != getattr(manager_emp, "id", None):
                messages.error(request, "لا يمكنك تعديل هذا الموظف")
                return redirect("attendance:stealth_manage")

        emp.stealth_tracking_enabled = not bool(getattr(emp, "stealth_tracking_enabled", False))
        emp.save(update_fields=["stealth_tracking_enabled"])

        status = "تم تفعيل" if emp.stealth_tracking_enabled else "تم إيقاف"
        messages.success(request, f"{status} التتبع الصامت للموظف {emp.full_name_ar}")
        return redirect("attendance:stealth_manage")

    context = {
        "employees": employees,
        "policy": policy,
        "page_title": "إدارة التتبع الصامت",
    }
    return render(request, "attendance/stealth_manage.html", context)


@login_required
def stealth_tracking_alerts(request):
    """
    قائمة تنبيهات التتبع الصامت
    """
    from attendance.models import TrackingAlert
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company
    alerts = TrackingAlert.objects.filter(company=company).select_related("employee").order_by("-started_at")

    if role == "manager":
        manager_emp = Employee.all_objects.filter(user=request.user).first()
        alerts = alerts.filter(employee__direct_manager=manager_emp)

    status_filter = request.GET.get("status")
    if status_filter:
        alerts = alerts.filter(status=status_filter)

    context = {
        "alerts": alerts,
        "status_filter": status_filter,
        "page_title": "تنبيهات التتبع",
    }
    return render(request, "attendance/stealth_alerts.html", context)
'''

if "def stealth_tracking_manage" not in att_views:
    att_views += stealth_views
    write_file(att_views_path, att_views)
    print("  ✅ تم إضافة صفحات إدارة التتبع الصامت")
else:
    print("  ℹ️  صفحات التتبع الصامت موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 8) attendance/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls_content = read_file(urls_path)

if "stealth-manage" not in urls_content:
    urls_content = urls_content.rstrip()
    if urls_content.endswith("]"):
        urls_content = urls_content[:-1]
        urls_content += """
    # Stealth tracking
    path('stealth-manage/', views.stealth_tracking_manage, name='stealth_manage'),
    path('stealth-alerts/', views.stealth_tracking_alerts, name='stealth_alerts'),
]
"""
        write_file(urls_path, urls_content)
        print("  ✅ تم إضافة URLs")
else:
    print("  ℹ️  URLs موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 9) templates
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء Templates...")

create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "stealth_manage.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إدارة التتبع الصامت{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-eye-slash me-2" style="color:#7c3aed;"></i>
        إدارة التتبع الصامت
      </h4>
      <p class="text-muted mb-0">
        فعل أو أوقف التتبع أثناء ساعات العمل للموظفين المحددين
      </p>
    </div>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <div class="row g-3 text-center">
        <div class="col-md-3">
          <div class="p-3 rounded" style="background:#f8fafc;">
            <div class="fw-bold fs-4" style="color:#06B6D4;">
              {% if policy.stealth_tracking_enabled %}مفعّل{% else %}معطل{% endif %}
            </div>
            <small class="text-muted">حالة الميزة</small>
          </div>
        </div>
        <div class="col-md-3">
          <div class="p-3 rounded" style="background:#f8fafc;">
            <div class="fw-bold fs-4 text-warning">
              {{ policy.stealth_tracking_alert_after_minutes }}
            </div>
            <small class="text-muted">دقيقة قبل التنبيه</small>
          </div>
        </div>
        <div class="col-md-6 text-start">
          <div class="p-3 rounded" style="background:#f8fafc;">
            <div class="small">
              <strong>التنبيه يذهب إلى:</strong>
              {% if policy.stealth_tracking_notify_manager %}<span class="badge bg-light text-dark border ms-1">المدير</span>{% endif %}
              {% if policy.stealth_tracking_notify_hr %}<span class="badge bg-light text-dark border ms-1">HR</span>{% endif %}
              {% if policy.stealth_tracking_notify_company_admin %}<span class="badge bg-light text-dark border ms-1">صاحب الشركة</span>{% endif %}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  {% if employees %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th>القسم</th>
            <th>المسمى</th>
            <th>الوضع</th>
            <th class="text-center">التفعيل</th>
          </tr>
        </thead>
        <tbody>
          {% for emp in employees %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold">{{ emp.full_name_ar }}</div>
              <small class="text-muted">{{ emp.employee_code }}</small>
            </td>
            <td class="text-muted small">{{ emp.department.name_ar|default:"—" }}</td>
            <td class="text-muted small">{{ emp.job_title.name_ar|default:"—" }}</td>
            <td>
              {% if emp.stealth_tracking_enabled %}
                <span class="badge bg-success">مفعل</span>
              {% else %}
                <span class="badge bg-secondary">غير مفعل</span>
              {% endif %}
            </td>
            <td class="text-center">
              <form method="post" class="d-inline">
                {% csrf_token %}
                <input type="hidden" name="employee_id" value="{{ emp.pk }}">
                <button type="submit"
                        class="btn btn-sm {% if emp.stealth_tracking_enabled %}btn-outline-danger{% else %}btn-outline-primary{% endif %}">
                  {% if emp.stealth_tracking_enabled %}
                    إيقاف
                  {% else %}
                    تفعيل
                  {% endif %}
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5 text-muted">
      لا يوجد موظفون
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "stealth_alerts.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تنبيهات التتبع{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-radar me-2" style="color:#ef4444;"></i>
        تنبيهات التتبع
      </h4>
      <p class="text-muted mb-0">الموظفون الخارجون من النطاق أثناء ساعات العمل</p>
    </div>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" class="d-flex gap-2">
        <select name="status" class="form-select" style="max-width:200px;" onchange="this.form.submit()">
          <option value="">كل الحالات</option>
          <option value="open" {% if status_filter == 'open' %}selected{% endif %}>مفتوح</option>
          <option value="resolved" {% if status_filter == 'resolved' %}selected{% endif %}>تمت المعالجة</option>
          <option value="ignored" {% if status_filter == 'ignored' %}selected{% endif %}>تم التجاهل</option>
        </select>
        <a href="{% url 'attendance:stealth_alerts' %}" class="btn btn-light btn-sm">إعادة تعيين</a>
      </form>
    </div>
  </div>

  {% if alerts %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th>التاريخ</th>
            <th>بداية الخروج</th>
            <th>عدد الدقائق</th>
            <th>آخر عنوان</th>
            <th>الحالة</th>
          </tr>
        </thead>
        <tbody>
          {% for alert in alerts %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold">{{ alert.employee.full_name_ar }}</div>
              <small class="text-muted">{{ alert.employee.employee_code }}</small>
            </td>
            <td>{{ alert.date|date:"d/m/Y" }}</td>
            <td>{{ alert.started_at|date:"H:i" }}</td>
            <td class="fw-bold text-danger">{{ alert.minutes_outside }}</td>
            <td class="text-muted small">{{ alert.last_address|default:"—"|truncatechars:40 }}</td>
            <td>
              {% if alert.status == 'open' %}
                <span class="badge bg-danger">مفتوح</span>
              {% elif alert.status == 'resolved' %}
                <span class="badge bg-success">تمت المعالجة</span>
              {% else %}
                <span class="badge bg-secondary">تم التجاهل</span>
              {% endif %}
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
      <i class="bi bi-shield-check" style="font-size:4rem; color:#10b981;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا توجد تنبيهات تتبع</h5>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

# ════════════════════════════════════════════════════════════
# 10) Sidebar + policies template
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Sidebar + policies template...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "attendance:stealth_manage" not in sidebar:
    target = """      <a href="{% url 'attendance:schedule_week' %}"
         class="nav-link {% if 'schedule' in request.path %}active{% endif %}">
        <i class="bi bi-calendar3"></i><span>جدول العمل</span>
      </a>"""
    replacement = target + """
      <a href="{% url 'attendance:stealth_manage' %}"
         class="nav-link {% if 'stealth-manage' in request.path %}active{% endif %}">
        <i class="bi bi-eye-slash"></i><span>إدارة التتبع الصامت</span>
      </a>
      <a href="{% url 'attendance:stealth_alerts' %}"
         class="nav-link {% if 'stealth-alerts' in request.path %}active{% endif %}">
        <i class="bi bi-radar"></i><span>تنبيهات التتبع</span>
      </a>"""
    if target in sidebar:
        sidebar = sidebar.replace(target, replacement)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة روابط التتبع الصامت")
    else:
        print("  ℹ️  لم أجد مكان الإدراج المتوقع")
else:
    print("  ℹ️  روابط التتبع الصامت موجودة بالفعل")

policies_path = os.path.join(BASE_DIR, "templates", "companies", "policies.html")
policies = read_file(policies_path)

if "stealth_tracking_enabled" not in policies:
    stealth_block = """
      <!-- التتبع الصامت -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-eye-slash me-2" style="color:#7c3aed;"></i>
              التتبع الصامت (ميزة مدفوعة)
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="form-check form-switch mb-3">
              <input class="form-check-input" type="checkbox"
                     name="stealth_tracking_enabled" id="stealthEnabled"
                     {% if policy.stealth_tracking_enabled %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="stealthEnabled">
                تفعيل التتبع الصامت
              </label>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold small">التنبيه بعد عدد دقائق</label>
              <select name="stealth_tracking_alert_after_minutes" class="form-select">
                <option value="10" {% if policy.stealth_tracking_alert_after_minutes == 10 %}selected{% endif %}>10 دقائق</option>
                <option value="15" {% if policy.stealth_tracking_alert_after_minutes == 15 %}selected{% endif %}>15 دقيقة</option>
                <option value="20" {% if policy.stealth_tracking_alert_after_minutes == 20 %}selected{% endif %}>20 دقيقة</option>
                <option value="30" {% if policy.stealth_tracking_alert_after_minutes == 30 %}selected{% endif %}>30 دقيقة</option>
              </select>
            </div>

            <div class="small fw-semibold mb-2">من يستقبل التنبيه؟</div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="stealth_tracking_notify_manager" id="stMgr"
                     {% if policy.stealth_tracking_notify_manager %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label" for="stMgr">المدير المباشر</label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="stealth_tracking_notify_hr" id="stHr"
                     {% if policy.stealth_tracking_notify_hr %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label" for="stHr">HR</label>
            </div>

            <div class="form-check form-switch mb-2">
              <input class="form-check-input" type="checkbox"
                     name="stealth_tracking_notify_company_admin" id="stAdmin"
                     {% if policy.stealth_tracking_notify_company_admin %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label" for="stAdmin">صاحب الشركة</label>
            </div>

            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox"
                     name="stealth_tracking_requires_charter_clause" id="stClause"
                     {% if policy.stealth_tracking_requires_charter_clause %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="stClause">
                إضافة بند إلزامي في ميثاق العمل
              </label>
            </div>

            <small class="text-muted d-block mt-2">
              هذه الميزة متقدمة ومدفوعة، وتحتاج بندًا واضحًا في الميثاق.
            </small>

          </div>
        </div>
      </div>
"""
    target = """      <!-- ملاحظات -->"""
    if target in policies:
        policies = policies.replace(target, stealth_block + "\n" + target)
        write_file(policies_path, policies)
        print("  ✅ تم إضافة قسم التتبع الصامت في السياسات")
    else:
        print("  ℹ️  لم أجد مكان إدراج قسم السياسات")
else:
    print("  ℹ️  قسم التتبع الصامت موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 11) Seed defaults
# ════════════════════════════════════════════════════════════
print("\n🌱 ضبط القيم الافتراضية...")

from companies.models import Company, CompanyPolicy

for company in Company.objects.all():
    policy = CompanyPolicy.get_for_company(company)
    changed = False

    if getattr(policy, "stealth_tracking_alert_after_minutes", None) in [None, 0]:
        policy.stealth_tracking_alert_after_minutes = 15
        changed = True

    if getattr(policy, "stealth_tracking_requires_charter_clause", None) is None:
        policy.stealth_tracking_requires_charter_clause = True
        changed = True

    if changed:
        policy.save()

print("  ✅ تم ضبط القيم الافتراضية")

print("\n" + "=" * 60)
print("  ✅ Patch 44a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ stealth_tracking_enabled للموظف
  2. ✅ CompanyPolicy fields للتتبع الصامت
  3. ✅ TrackingAlert model
  4. ✅ صفحات:
       - إدارة التتبع الصامت
       - تنبيهات التتبع
  5. ✅ Sidebar links
  6. ✅ بند إلزامي يضاف للميثاق لو الميزة اتفعلت
  7. ✅ Admin + Migration

جرب:
  - /companies/policies/
  - /attendance/stealth-manage/
  - /attendance/stealth-alerts/

الجاي:
  Patch 44b = المنطق الفعلي للتتبع والتنبيه
""")