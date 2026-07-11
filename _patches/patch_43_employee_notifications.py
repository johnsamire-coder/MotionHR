#!/usr/bin/env python3
"""
Patch 43: Employee Notifications from HR
========================================
1) EmployeeNotification model
2) Auto notification after HR action
3) Notifications page update
4) Header badge
5) HR manual send notification page
"""

import os
import sys
import re

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
print("  Patch 43: Employee Notifications from HR")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) accounts/models.py → EmployeeNotification
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/models.py...")

models_path = os.path.join(BASE_DIR, "accounts", "models.py")
models_content = read_file(models_path)

notification_model = '''

class EmployeeNotification(models.Model):
    """إشعار داخلي للموظف"""

    NOTIFICATION_TYPES = [
        ("late_warning", "تحذير تأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("general_notice", "إشعار عام"),
        ("policy_reminder", "تذكير بسياسة"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("request_update", "تحديث طلب"),
    ]

    SEVERITY_CHOICES = [
        ("info", "معلومة"),
        ("warning", "تحذير"),
        ("danger", "هام"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="الموظف"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="العنوان"
    )
    message = models.TextField(
        verbose_name="الرسالة"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="general_notice",
        verbose_name="نوع الإشعار"
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default="info",
        verbose_name="الأهمية"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="تمت القراءة"
    )
    related_action = models.ForeignKey(
        "attendance.DisciplinaryAction",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="employee_notifications",
        verbose_name="الإجراء المرتبط"
    )
    sent_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sent_employee_notifications",
        verbose_name="مرسل بواسطة"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "إشعار موظف"
        verbose_name_plural = "إشعارات الموظفين"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"
'''

if "class EmployeeNotification" not in models_content:
    models_content += notification_model
    write_file(models_path, models_content)
    print("  ✅ تم إضافة EmployeeNotification model")
else:
    print("  ℹ️  EmployeeNotification موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

call_command("makemigrations", "accounts")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 3) Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/admin.py...")

admin_path = os.path.join(BASE_DIR, "accounts", "admin.py")
admin_content = read_file(admin_path)

if "EmployeeNotification" not in admin_content:
    admin_content += '''

from .models import EmployeeNotification

@admin.register(EmployeeNotification)
class EmployeeNotificationAdmin(admin.ModelAdmin):
    list_display = ["employee", "title", "notification_type", "severity", "is_read", "created_at"]
    list_filter = ["notification_type", "severity", "is_read"]
    search_fields = ["employee__first_name_ar", "employee__employee_code", "title"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل EmployeeNotification في Admin")
else:
    print("  ℹ️  EmployeeNotification مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 4) custom_filters.py → unread_notifications_count
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث custom_filters.py...")

filters_path = os.path.join(BASE_DIR, "accounts", "templatetags", "custom_filters.py")
filters_content = read_file(filters_path)

tag_code = '''

@register.simple_tag(name="unread_notifications_count")
def unread_notifications_count(user):
    """
    عدد الإشعارات غير المقروءة للموظف الحالي
    """
    try:
        if not user or not user.is_authenticated:
            return 0
        from employees.models import Employee
        from accounts.models import EmployeeNotification
        emp = Employee.all_objects.filter(user=user).first()
        if not emp:
            return 0
        return EmployeeNotification.objects.filter(
            employee=emp,
            is_read=False
        ).count()
    except Exception:
        return 0
'''

if "unread_notifications_count" not in filters_content:
    filters_content += tag_code
    write_file(filters_path, filters_content)
    print("  ✅ تم إضافة unread_notifications_count tag")
else:
    print("  ℹ️  unread_notifications_count موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 5) attendance/views.py → helper + call after HR action
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

att_views_path = os.path.join(BASE_DIR, "attendance", "views.py")
att_views = read_file(att_views_path)

notify_helper = '''

# ════════════════════════════════════════════════════════════
# Employee Notification Helper
# ════════════════════════════════════════════════════════════
def _send_employee_notification_for_action(employee, action, sent_by=None):
    """
    إرسال إشعار داخلي للموظف بعد اعتماد HR للإجراء
    """
    try:
        from accounts.models import EmployeeNotification

        action_label = ""
        try:
            action_label = action.get_action_type_display()
        except Exception:
            action_label = action.action_type

        # تجاهل / إعفاء → لا نرسل إشعار
        if action.action_type == "dismissed":
            return None

        if action.action_type in ["verbal_warning", "written_warning"]:
            title = "تنبيه بخصوص التأخير"
            message = (
                "عزيزي الموظف،\\n"
                "تم تسجيل تأخير عليك، ونرجو عدم تكرار ذلك مرة أخرى "
                "احترامًا لميثاق العمل وسياسات الشركة.\\n\\n"
                f"الإجراء المتخذ: {action_label}"
            )
            notif_type = "late_warning"
            severity = "warning"
        elif action.action_type in ["quarter_day_deduction", "half_day_deduction", "full_day_deduction"]:
            title = "إشعار خصم بسبب التأخير"
            amount_text = ""
            if action.deduction_amount:
                amount_text = f"\\nقيمة الخصم: {action.deduction_amount} ج.م"
            message = (
                "عزيزي الموظف،\\n"
                "تم اتخاذ إجراء خصم بسبب تكرار التأخير "
                "وفقًا لسياسة الشركة.\\n\\n"
                f"الإجراء المتخذ: {action_label}"
                f"{amount_text}"
            )
            notif_type = "deduction_notice"
            severity = "danger"
        else:
            title = "تحديث بخصوص التأخير"
            message = (
                "تم اتخاذ إجراء بخصوص التأخير المسجل عليك.\\n\\n"
                f"الإجراء المتخذ: {action_label}"
            )
            notif_type = "general_notice"
            severity = "info"

        return EmployeeNotification.objects.create(
            employee=employee,
            title=title,
            message=message,
            notification_type=notif_type,
            severity=severity,
            is_read=False,
            related_action=action,
            sent_by=sent_by,
        )
    except Exception:
        return None
'''

if "_send_employee_notification_for_action" not in att_views:
    att_views += notify_helper
    write_file(att_views_path, att_views)
    print("  ✅ تم إضافة helper إرسال الإشعار")
else:
    print("  ℹ️  helper موجود بالفعل")

# حقن call بعد notif.save()
att_views = read_file(att_views_path)

old_block = """        notif.is_acted_upon = True
        notif.action_taken = chosen_action
        notif.action_by = request.user
        notif.action_at = timezone.now()
        notif.action_notes = action_notes
        notif.save()

        messages.success(request, "تم تسجيل الإجراء بنجاح")
        return redirect("attendance:late_notification_detail", pk=pk)"""

new_block = """        notif.is_acted_upon = True
        notif.action_taken = chosen_action
        notif.action_by = request.user
        notif.action_at = timezone.now()
        notif.action_notes = action_notes
        notif.save()

        # إشعار الموظف
        _send_employee_notification_for_action(
            employee=notif.employee,
            action=action,
            sent_by=request.user
        )

        messages.success(request, "تم تسجيل الإجراء بنجاح")
        return redirect("attendance:late_notification_detail", pk=pk)"""

if old_block in att_views:
    att_views = att_views.replace(old_block, new_block)
    write_file(att_views_path, att_views)
    print("  ✅ تم ربط الإشعار بعد إجراء HR")
else:
    print("  ℹ️  لم أجد البلوك المتوقع — قد يكون تم تحديثه قبل كده")


# ════════════════════════════════════════════════════════════
# 6) accounts/views.py → notifications_view + send view
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/views.py...")

acc_views_path = os.path.join(BASE_DIR, "accounts", "views.py")
acc_views = read_file(acc_views_path)

# إضافة send_notification_view لو مش موجود
manual_send_view = '''

# ════════════════════════════════════════════════════════════
# HR Manual Employee Notifications
# ════════════════════════════════════════════════════════════

@login_required
def send_employee_notification_view(request):
    """
    HR / الإدارة يبعث إشعار لموظف أو قسم أو الكل
    """
    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية إرسال إشعارات")
        return redirect("dashboard")

    from employees.models import Employee
    from companies.models import Department
    from accounts.models import EmployeeNotification

    company = request.user.company
    employees = Employee.all_objects.filter(
        company=company,
        status="active"
    ).select_related("department").order_by("first_name_ar")

    departments = Department.objects.filter(
        company=company,
        is_active=True
    ).order_by("name_ar")

    if request.method == "POST":
        audience_type = request.POST.get("audience_type", "single")
        employee_id = request.POST.get("employee")
        department_id = request.POST.get("department")
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        severity = request.POST.get("severity", "info")

        if not title or not message:
            messages.error(request, "العنوان والرسالة مطلوبان")
            return redirect("accounts:send_employee_notification")

        target_employees = Employee.all_objects.none()

        if audience_type == "single" and employee_id:
            target_employees = Employee.all_objects.filter(
                company=company,
                pk=employee_id
            )

        elif audience_type == "department" and department_id:
            target_employees = Employee.all_objects.filter(
                company=company,
                department_id=department_id,
                status="active"
            )

        elif audience_type == "all":
            target_employees = Employee.all_objects.filter(
                company=company,
                status="active"
            )

        count = 0
        for emp in target_employees:
            EmployeeNotification.objects.create(
                employee=emp,
                title=title,
                message=message,
                notification_type="general_notice",
                severity=severity,
                is_read=False,
                sent_by=request.user,
            )
            count += 1

        messages.success(request, f"تم إرسال الإشعار إلى {count} موظف")
        return redirect("accounts:notifications")

    context = {
        "employees": employees,
        "departments": departments,
        "page_title": "إرسال إشعار",
    }
    return render(request, "accounts/send_notification.html", context)
'''

if "def send_employee_notification_view" not in acc_views:
    acc_views += manual_send_view
    write_file(acc_views_path, acc_views)
    print("  ✅ تم إضافة send_employee_notification_view")
else:
    print("  ℹ️  send view موجود بالفعل")

# تحديث notifications_view بشكل آمن
notif_marker = "def notifications_view(request):"
if notif_marker in acc_views and "db_notifications_qs" not in acc_views:
    start = acc_views.find(notif_marker)
    end = acc_views.find("\ndef _get_notifications", start)
    if end == -1:
        end = len(acc_views)

    old_func = acc_views[start:end]

    new_func = '''def notifications_view(request):
    """مركز الإشعارات"""
    from accounts.models import EmployeeNotification
    from employees.models import Employee

    current_emp = Employee.all_objects.filter(user=request.user).first()

    # إشعارات النظام القديمة
    notifications = _get_notifications(request.user)

    # إشعارات الموظف الجديدة
    db_notifications_qs = EmployeeNotification.objects.none()
    if current_emp:
        db_notifications_qs = EmployeeNotification.objects.filter(
            employee=current_emp
        ).order_by("-created_at")

    # Mark all read
    if request.method == "POST" and request.POST.get("mark_all_read") == "1":
        db_notifications_qs.filter(is_read=False).update(is_read=True)
        messages.success(request, "تم تعليم كل الإشعارات كمقروءة")
        return redirect("accounts:notifications")

    db_notifications = []
    for n in db_notifications_qs[:30]:
        icon_map = {
            "late_warning": "exclamation-triangle",
            "deduction_notice": "receipt-cutoff",
            "general_notice": "info-circle",
            "policy_reminder": "journal-text",
            "charter_reminder": "file-earmark-text",
            "request_update": "inbox",
        }
        type_map = {
            "info": "info",
            "warning": "warning",
            "danger": "danger",
        }
        db_notifications.append({
            "type": type_map.get(n.severity, "info"),
            "icon": icon_map.get(n.notification_type, "info-circle"),
            "title": n.title,
            "message": n.message,
            "time": n.created_at.strftime("%d/%m/%Y %H:%M"),
            "url": "",
            "unread": not n.is_read,
            "is_db": True,
            "id": n.pk,
        })

    merged_notifications = db_notifications + notifications

    context = {
        "page_title": "الإشعارات",
        "notifications": merged_notifications,
        "db_unread_count": db_notifications_qs.filter(is_read=False).count() if current_emp else 0,
    }
    return render(request, "accounts/notifications.html", context)
'''
    acc_views = acc_views.replace(old_func, new_func)
    write_file(acc_views_path, acc_views)
    print("  ✅ تم تحديث notifications_view")
else:
    print("  ℹ️  notifications_view محدث بالفعل أو لم يتم العثور عليه")


# ════════════════════════════════════════════════════════════
# 7) accounts/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/urls.py...")

urls_path = os.path.join(BASE_DIR, "accounts", "urls.py")
urls_content = read_file(urls_path)

if "send_employee_notification" not in urls_content:
    urls_content = urls_content.rstrip()
    if urls_content.endswith("]"):
        urls_content = urls_content[:-1]
        urls_content += """
    path('notifications/send/', views.send_employee_notification_view, name='send_employee_notification'),
]
"""
        write_file(urls_path, urls_content)
        print("  ✅ تم إضافة URL الإرسال اليدوي")
else:
    print("  ℹ️  URL موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 8) notifications template
# ════════════════════════════════════════════════════════════
print("\n📄 تحديث notifications.html...")

notifications_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}الإشعارات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-0">
        <i class="bi bi-bell me-2" style="color:#06B6D4;"></i>
        الإشعارات
      </h4>
      {% if db_unread_count %}
      <small class="text-muted">غير المقروءة: {{ db_unread_count }}</small>
      {% endif %}
    </div>

    <div class="d-flex gap-2">
      {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
      <a href="{% url 'accounts:send_employee_notification' %}"
         class="btn btn-sm text-white"
         style="background:#06B6D4;">
        <i class="bi bi-send me-1"></i>إرسال إشعار
      </a>
      {% endif %}

      {% if db_unread_count %}
      <form method="post" class="m-0">
        {% csrf_token %}
        <input type="hidden" name="mark_all_read" value="1">
        <button type="submit" class="btn btn-sm btn-outline-secondary">
          تعليم الكل كمقروء
        </button>
      </form>
      {% endif %}
    </div>
  </div>

  {% if notifications %}
  <div class="card border-0 shadow-sm">
    <div class="card-body p-0">
      {% for notif in notifications %}
      <div class="d-flex align-items-start gap-3 p-4 border-bottom {% if forloop.last %}border-0{% endif %}"
           style="{% if notif.unread %}background:#f8fafc;{% endif %}">

        <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
             style="width:44px;height:44px;
                    background:
                    {% if notif.type == 'warning' %}#fff3e0
                    {% elif notif.type == 'danger' %}#fde8e8
                    {% elif notif.type == 'success' %}#e8f5e9
                    {% else %}#e0f7fa{% endif %};">
          <i class="bi bi-{{ notif.icon }}"
             style="font-size:1.1rem;
                    color:{% if notif.type == 'warning' %}#f59e0b
                    {% elif notif.type == 'danger' %}#ef4444
                    {% elif notif.type == 'success' %}#10b981
                    {% else %}#06B6D4{% endif %};"></i>
        </div>

        <div class="flex-grow-1">
          <div class="fw-semibold text-dark">{{ notif.title }}</div>
          {% if notif.message %}
          <div class="text-muted small mt-1" style="white-space:pre-line;">{{ notif.message }}</div>
          {% endif %}
          {% if notif.time %}
          <small class="text-muted d-block mt-1">{{ notif.time }}</small>
          {% endif %}
        </div>

        {% if notif.unread %}
        <div class="rounded-circle flex-shrink-0"
             style="width:8px;height:8px;background:#06B6D4;margin-top:6px;"></div>
        {% endif %}

      </div>
      {% endfor %}
    </div>
  </div>
  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-bell-slash" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا توجد إشعارات</h5>
      <p class="text-muted">كل شيء هادئ الآن 👌</p>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
write_file(
    os.path.join(BASE_DIR, "templates", "accounts", "notifications.html"),
    notifications_template
)

# send_notification.html
create_file(
    os.path.join(BASE_DIR, "templates", "accounts", "send_notification.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إرسال إشعار{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="row justify-content-center">
    <div class="col-lg-8">

      <div class="d-flex align-items-center mb-4">
        <a href="{% url 'accounts:notifications' %}" class="btn btn-outline-secondary btn-sm me-3">
          <i class="bi bi-arrow-right"></i>
        </a>
        <h4 class="fw-bold mb-0">إرسال إشعار</h4>
      </div>

      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-4">
                <label class="form-label fw-semibold small">إرسال إلى</label>
                <select name="audience_type" id="audienceType" class="form-select" onchange="toggleAudienceFields()">
                  <option value="single">موظف واحد</option>
                  <option value="department">قسم كامل</option>
                  <option value="all">كل الموظفين</option>
                </select>
              </div>

              <div class="col-md-4" id="employeeField">
                <label class="form-label fw-semibold small">الموظف</label>
                <select name="employee" class="form-select">
                  <option value="">اختر الموظف</option>
                  {% for emp in employees %}
                  <option value="{{ emp.pk }}">{{ emp.full_name_ar }} ({{ emp.employee_code }})</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-4 d-none" id="departmentField">
                <label class="form-label fw-semibold small">القسم</label>
                <select name="department" class="form-select">
                  <option value="">اختر القسم</option>
                  {% for dept in departments %}
                  <option value="{{ dept.pk }}">{{ dept.name_ar }}</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-4">
                <label class="form-label fw-semibold small">الأهمية</label>
                <select name="severity" class="form-select">
                  <option value="info">معلومة</option>
                  <option value="warning">تحذير</option>
                  <option value="danger">هام</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">العنوان</label>
                <input type="text" name="title" class="form-control" required
                       placeholder="عنوان الإشعار">
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">الرسالة</label>
                <textarea name="message" class="form-control" rows="5" required
                          placeholder="اكتب رسالة الإشعار هنا..."></textarea>
              </div>

            </div>

            <div class="mt-4">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-send me-1"></i>إرسال الإشعار
              </button>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>
</div>

{% block extra_js %}
<script>
function toggleAudienceFields() {
  const audience = document.getElementById('audienceType').value;
  const empField = document.getElementById('employeeField');
  const deptField = document.getElementById('departmentField');

  empField.classList.add('d-none');
  deptField.classList.add('d-none');

  if (audience === 'single') {
    empField.classList.remove('d-none');
  } else if (audience === 'department') {
    deptField.classList.remove('d-none');
  }
}
</script>
{% endblock %}
"""
)

# ════════════════════════════════════════════════════════════
# 9) dashboard_base badge
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث dashboard_base.html (badge)...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "unread_notifications_count" not in sidebar:
    # نضيف tag بعد load custom_filters
    if "{% load custom_filters %}" in sidebar:
        sidebar = sidebar.replace(
            "{% load custom_filters %}",
            "{% load custom_filters %}\n{% unread_notifications_count request.user as unread_notif_count %}"
        )

    old_bell = """      <a href="{% url 'global_search' %}"
         class="btn btn-sm btn-light" style="border-radius:8px;width:34px;height:34px;padding:0;display:flex;align-items:center;justify-content:center;">
        <i class="bi bi-search" style="color:#06B6D4;"></i>
      </a>

      <div class="dropdown">"""

    new_bell = """      <a href="{% url 'global_search' %}"
         class="btn btn-sm btn-light" style="border-radius:8px;width:34px;height:34px;padding:0;display:flex;align-items:center;justify-content:center;">
        <i class="bi bi-search" style="color:#06B6D4;"></i>
      </a>

      <a href="{% url 'accounts:notifications' %}"
         class="btn btn-sm btn-light position-relative"
         style="border-radius:8px;width:34px;height:34px;padding:0;display:flex;align-items:center;justify-content:center;">
        <i class="bi bi-bell" style="color:#6b7280;"></i>
        {% if unread_notif_count > 0 %}
        <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
              style="font-size:0.6rem;">
          {{ unread_notif_count }}
        </span>
        {% endif %}
      </a>

      <div class="dropdown">"""

    if old_bell in sidebar:
        sidebar = sidebar.replace(old_bell, new_bell)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة badge الإشعارات")
    else:
        print("  ℹ️  لم أجد مكان أيقونة الجرس المتوقع")
else:
    print("  ℹ️  badge موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 10) dashboard employee badge count
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/views.py + dashboard/index.html...")

acc_views_path = os.path.join(BASE_DIR, "accounts", "views.py")
acc_views = read_file(acc_views_path)

# إضافة count في employee dashboard branch
if "employee_unread_notifications_count" not in acc_views:
    old_part = """        # الميثاق
        charter_accepted = True"""
    new_part = """        # إشعاراتي
        employee_unread_notifications_count = 0
        try:
            from accounts.models import EmployeeNotification
            if current_employee:
                employee_unread_notifications_count = EmployeeNotification.objects.filter(
                    employee=current_employee,
                    is_read=False
                ).count()
        except Exception:
            pass

        # الميثاق
        charter_accepted = True"""
    if old_part in acc_views:
        acc_views = acc_views.replace(old_part, new_part)

    old_context_part = '''            "charter_accepted": charter_accepted,'''
    new_context_part = '''            "charter_accepted": charter_accepted,
            "employee_unread_notifications_count": employee_unread_notifications_count,'''
    if old_context_part in acc_views:
        acc_views = acc_views.replace(old_context_part, new_context_part)

    write_file(acc_views_path, acc_views)
    print("  ✅ تم إضافة عداد إشعارات الموظف في dashboard view")
else:
    print("  ℹ️  عداد الإشعارات موجود بالفعل")


dashboard_path = os.path.join(BASE_DIR, "templates", "dashboard", "index.html")
dashboard = read_file(dashboard_path)

if "employee_unread_notifications_count" not in dashboard:
    marker = """    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold text-danger">{{ deductions_month_total }}</div>
          <small class="text-muted">خصومات الشهر</small>
        </div>
      </div>
    </div>"""

    replacement = marker + """

    <div class="col-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4 text-center">
          <div class="fs-3 fw-bold" style="color:#7c3aed;">{{ employee_unread_notifications_count }}</div>
          <small class="text-muted">إشعارات جديدة</small>
        </div>
      </div>
    </div>"""

    if marker in dashboard:
        dashboard = dashboard.replace(marker, replacement)
        write_file(dashboard_path, dashboard)
        print("  ✅ تم إضافة كارت الإشعارات في Dashboard الموظف")
    else:
        print("  ℹ️  لم أجد المكان المتوقع في dashboard template")
else:
    print("  ℹ️  كارت الإشعارات موجود بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 43 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ EmployeeNotification model
  2. ✅ إشعار تلقائي للموظف بعد إجراء HR
  3. ✅ notifications_view محدثة
  4. ✅ صفحة إرسال إشعار يدوي
  5. ✅ Badge للإشعارات في الـ Header
  6. ✅ كارت إشعارات جديدة في Dashboard الموظف
  7. ✅ صفحة إشعاراتي محدثة

جرب:
  1) hr_manager → افتح Late Notification وخد إجراء
  2) emp10003 → افتح /accounts/notifications/
  3) HR/Admin → /accounts/notifications/send/
""")