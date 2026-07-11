#!/usr/bin/env python3
"""
Patch 41c: HR Late Actions
==========================
1) صفحات إشعارات التأخير
2) HR يختار الإجراء
3) إنشاء DisciplinaryAction
4) إنشاء Deduction تلقائي لو الإجراء خصم
5) صفحة إنذاراتي للموظف
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


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
print("  Patch 41c: HR Late Actions")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) attendance/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

late_action_views = '''

# ════════════════════════════════════════════════════════════
# Late Notifications & Actions
# ════════════════════════════════════════════════════════════
@login_required
def late_notifications_list(request):
    """قائمة إشعارات التأخير لـ HR / الإدارة"""
    from attendance.models import LateNotification

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول لهذه الصفحة")
        return redirect("dashboard")

    qs = LateNotification.objects.filter(
        company=request.user.company
    ).select_related("employee").order_by("-created_at")

    status_filter = request.GET.get("status")
    if status_filter == "pending":
        qs = qs.filter(is_acted_upon=False)
    elif status_filter == "done":
        qs = qs.filter(is_acted_upon=True)
    elif status_filter == "unread":
        qs = qs.filter(is_read=False)

    context = {
        "notifications": qs,
        "status_filter": status_filter,
        "page_title": "إشعارات التأخير",
    }
    return render(request, "attendance/late_notifications_list.html", context)


@login_required
def late_notification_detail(request, pk):
    """تفاصيل إشعار التأخير + اتخاذ الإجراء"""
    from attendance.models import LateNotification, DisciplinaryAction
    from employees.models import Deduction
    from django.utils import timezone

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول لهذه الصفحة")
        return redirect("dashboard")

    notif = get_object_or_404(
        LateNotification.objects.select_related("employee"),
        pk=pk,
        company=request.user.company
    )

    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=["is_read"])

    policy = _get_company_policy(request.user.company)

    if request.method == "POST":
        chosen_action = request.POST.get("action_taken", "").strip()
        action_notes = request.POST.get("action_notes", "").strip()

        if not chosen_action:
            messages.error(request, "اختر الإجراء أولاً")
            return redirect("attendance:late_notification_detail", pk=pk)

        # لو الشركة طالبة سبب في حالة override / ignore
        require_reason = False
        if policy and hasattr(policy, "hr_override_reason_required"):
            require_reason = bool(policy.hr_override_reason_required)

        if require_reason and chosen_action == "dismissed" and not action_notes:
            messages.error(request, "سبب تجاهل الإجراء المقترح إجباري")
            return redirect("attendance:late_notification_detail", pk=pk)

        # لو اتاخد إجراء قبل كده
        if notif.is_acted_upon:
            messages.warning(request, "تم اتخاذ إجراء على هذا الإشعار مسبقًا")
            return redirect("attendance:late_notification_detail", pk=pk)

        # إنشاء إجراء تأديبي
        action = DisciplinaryAction.objects.create(
            company=request.user.company,
            employee=notif.employee,
            action_type=chosen_action,
            reason=notif.message,
            related_notification=notif,
            auto_generated=False,
            performed_by=request.user,
            notes=action_notes,
        )

        # لو خصم → أنشئ Deduction
        deduction_amount = None
        if chosen_action in ["quarter_day_deduction", "half_day_deduction", "full_day_deduction"]:
            salary = getattr(notif.employee, "basic_salary", None) or 0
            day_value = 0
            try:
                day_value = float(salary) / 30 if salary else 0
            except Exception:
                day_value = 0

            if chosen_action == "quarter_day_deduction":
                deduction_amount = round(day_value / 4, 2)
                reason_text = "خصم ربع يوم بسبب تكرار التأخير"
            elif chosen_action == "half_day_deduction":
                deduction_amount = round(day_value / 2, 2)
                reason_text = "خصم نصف يوم بسبب تكرار التأخير"
            else:
                deduction_amount = round(day_value, 2)
                reason_text = "خصم يوم كامل بسبب تكرار التأخير"

            Deduction.objects.create(
                company=request.user.company,
                employee=notif.employee,
                deduction_type="penalty",
                amount=deduction_amount,
                date=timezone.now().date(),
                reason=reason_text,
                month=timezone.now().month,
                year=timezone.now().year,
                is_visible_to_employee=True,
                notes=action_notes,
            )

            action.deduction_amount = deduction_amount
            action.deduction_created = True
            action.save(update_fields=["deduction_amount", "deduction_created"])

        # تحديث الإشعار
        notif.is_acted_upon = True
        notif.action_taken = chosen_action
        notif.action_by = request.user
        notif.action_at = timezone.now()
        notif.action_notes = action_notes
        notif.save()

        messages.success(request, "تم تسجيل الإجراء بنجاح")
        return redirect("attendance:late_notification_detail", pk=pk)

    context = {
        "notif": notif,
        "page_title": "تفاصيل إشعار التأخير",
    }
    return render(request, "attendance/late_notification_detail.html", context)


@login_required
def my_warnings_view(request):
    """إنذاراتي / إجراءاتي التأديبية للموظف"""
    from attendance.models import DisciplinaryAction
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    current_employee = Employee.all_objects.filter(user=request.user).first()

    if not current_employee:
        messages.error(request, "لم يتم ربط حسابك بملف موظف")
        return redirect("dashboard")

    policy = _get_company_policy(request.user.company)
    can_view = True
    if policy and hasattr(policy, "employee_can_view_warnings"):
        can_view = bool(policy.employee_can_view_warnings)

    if not can_view:
        messages.warning(request, "عرض الإنذارات غير متاح حسب سياسة الشركة")
        return redirect("dashboard")

    actions = DisciplinaryAction.objects.filter(
        company=request.user.company,
        employee=current_employee
    ).order_by("-performed_at")

    context = {
        "actions": actions,
        "page_title": "إنذاراتي وإجراءاتي",
    }
    return render(request, "attendance/my_warnings.html", context)
'''

if "def late_notifications_list" not in views:
    views += late_action_views
    write_file(views_path, views)
    print("  ✅ تم إضافة Late Notifications views")
else:
    print("  ℹ️  Late Notifications views موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) attendance/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls = read_file(urls_path)

if "late-notifications" not in urls:
    urls = urls.rstrip()
    if urls.endswith("]"):
        urls = urls[:-1]
        urls += """
    # Late notifications
    path('late-notifications/', views.late_notifications_list, name='late_notifications'),
    path('late-notifications/<int:pk>/', views.late_notification_detail, name='late_notification_detail'),
    path('my-warnings/', views.my_warnings_view, name='my_warnings'),
]
"""
        write_file(urls_path, urls)
        print("  ✅ تم إضافة URLs")
else:
    print("  ℹ️  URLs موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 3) Templates
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء Templates...")

# list
create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "late_notifications_list.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إشعارات التأخير{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-bell me-2" style="color:#f59e0b;"></i>
        إشعارات التأخير
      </h4>
      <p class="text-muted mb-0">تابع التأخيرات والإجراءات المطلوبة</p>
    </div>
  </div>

  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" class="d-flex gap-2 flex-wrap">
        <select name="status" class="form-select" style="max-width:200px;" onchange="this.form.submit()">
          <option value="">كل الإشعارات</option>
          <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>تحتاج إجراء</option>
          <option value="done" {% if status_filter == 'done' %}selected{% endif %}>تم اتخاذ إجراء</option>
          <option value="unread" {% if status_filter == 'unread' %}selected{% endif %}>غير مقروءة</option>
        </select>
        <a href="{% url 'attendance:late_notifications' %}" class="btn btn-light btn-sm">إعادة تعيين</a>
      </form>
    </div>
  </div>

  {% if notifications %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموظف</th>
            <th>العنوان</th>
            <th>النوع</th>
            <th>مرات التأخير</th>
            <th>الحالة</th>
            <th>التاريخ</th>
            <th class="text-center">إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {% for n in notifications %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold">{{ n.employee.full_name_ar }}</div>
              <small class="text-muted">{{ n.employee.employee_code }}</small>
            </td>
            <td>
              <div class="fw-semibold small">{{ n.title }}</div>
              <small class="text-muted">{{ n.message|truncatechars:55 }}</small>
            </td>
            <td>
              {% if n.notification_type == 'threshold_reached' %}
                <span class="badge bg-danger">وصل الحد</span>
              {% else %}
                <span class="badge bg-warning text-dark">تأخير عادي</span>
              {% endif %}
            </td>
            <td class="fw-bold">{{ n.incident_count }}</td>
            <td>
              {% if n.is_acted_upon %}
                <span class="badge bg-success">تم الإجراء</span>
              {% elif n.is_read %}
                <span class="badge bg-info">قيد المراجعة</span>
              {% else %}
                <span class="badge bg-danger">جديد</span>
              {% endif %}
            </td>
            <td class="text-muted small">{{ n.created_at|date:"d/m/Y H:i" }}</td>
            <td class="text-center">
              <a href="{% url 'attendance:late_notification_detail' n.pk %}"
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
      <i class="bi bi-bell-slash" style="font-size:4rem; color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا توجد إشعارات تأخير</h5>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

# detail
create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "late_notification_detail.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}تفاصيل إشعار التأخير{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="row justify-content-center">
    <div class="col-lg-8">

      <div class="d-flex align-items-center mb-4">
        <a href="{% url 'attendance:late_notifications' %}" class="btn btn-outline-secondary btn-sm me-3">
          <i class="bi bi-arrow-right"></i>
        </a>
        <h4 class="fw-bold mb-0">تفاصيل إشعار التأخير</h4>
      </div>

      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="text-muted small">الموظف</label>
              <div class="fw-bold">{{ notif.employee.full_name_ar }}</div>
              <small class="text-muted">{{ notif.employee.employee_code }}</small>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">نوع الإشعار</label>
              <div class="fw-bold">
                {% if notif.notification_type == 'threshold_reached' %}
                  وصل للحد
                {% else %}
                  تأخير عادي
                {% endif %}
              </div>
            </div>
            <div class="col-12">
              <label class="text-muted small">العنوان</label>
              <div class="fw-semibold">{{ notif.title }}</div>
            </div>
            <div class="col-12">
              <label class="text-muted small">الرسالة</label>
              <div class="p-3 rounded" style="background:#f8fafc;">{{ notif.message }}</div>
            </div>
            {% if notif.details %}
            <div class="col-12">
              <label class="text-muted small">تفاصيل التأخيرات</label>
              <div class="p-3 rounded" style="background:#fff7ed; white-space:pre-line;">{{ notif.details }}</div>
            </div>
            {% endif %}
            {% if notif.suggested_action %}
            <div class="col-12">
              <label class="text-muted small">الإجراء المقترح</label>
              <div class="fw-bold text-danger">{{ notif.suggested_action }}</div>
            </div>
            {% endif %}
          </div>
        </div>
      </div>

      {% if not notif.is_acted_upon %}
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">اتخاذ إجراء</h5>
        </div>
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">
              <div class="col-12">
                <label class="form-label fw-semibold small">الإجراء من جانبك</label>
                <select name="action_taken" class="form-select" required>
                  <option value="">اختر الإجراء</option>
                  <option value="verbal_warning">إنذار شفهي</option>
                  <option value="written_warning">إنذار كتابي</option>
                  <option value="quarter_day_deduction">خصم ربع يوم</option>
                  <option value="half_day_deduction">خصم نصف يوم</option>
                  <option value="full_day_deduction">خصم يوم كامل</option>
                  <option value="dismissed">إعفاء / تجاهل</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">ملاحظات / سبب القرار</label>
                <textarea name="action_notes" class="form-control" rows="3"
                          placeholder="اكتب سبب اعتماد أو تجاهل الإجراء..."></textarea>
              </div>
            </div>

            <div class="mt-4">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                اعتماد الإجراء
              </button>
            </div>
          </form>
        </div>
      </div>
      {% else %}
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h5 class="fw-bold text-success mb-3">تم اتخاذ الإجراء</h5>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="text-muted small">الإجراء المتخذ</label>
              <div class="fw-bold">{{ notif.action_taken }}</div>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">بواسطة</label>
              <div class="fw-bold">{{ notif.action_by.get_full_name|default:notif.action_by.username }}</div>
            </div>
            <div class="col-12">
              <label class="text-muted small">ملاحظات</label>
              <div class="p-3 rounded" style="background:#f8fafc;">{{ notif.action_notes|default:"—" }}</div>
            </div>
          </div>
        </div>
      </div>
      {% endif %}

    </div>
  </div>
</div>
{% endblock %}
"""
)

# employee warnings
create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "my_warnings.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إنذاراتي وإجراءاتي{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-exclamation-triangle me-2" style="color:#f59e0b;"></i>
      إنذاراتي وإجراءاتي
    </h4>
    <p class="text-muted mb-0">السجل الخاص بك حسب سياسة الشركة</p>
  </div>

  {% if actions %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">التاريخ</th>
            <th>الإجراء</th>
            <th>السبب</th>
            <th>ملاحظات</th>
          </tr>
        </thead>
        <tbody>
          {% for act in actions %}
          <tr>
            <td class="px-4">{{ act.performed_at|date:"d/m/Y H:i" }}</td>
            <td>
              <span class="badge
                {% if 'warning' in act.action_type %}bg-warning text-dark
                {% elif 'deduction' in act.action_type %}bg-danger
                {% elif act.action_type == 'dismissed' %}bg-secondary
                {% else %}bg-info{% endif %}">
                {{ act.get_action_type_display }}
              </span>
            </td>
            <td class="small text-muted">{{ act.reason|truncatechars:70 }}</td>
            <td class="small text-muted">{{ act.notes|default:"—" }}</td>
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
      <h5 class="mt-3 fw-bold text-muted">لا توجد إنذارات أو إجراءات</h5>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

# ════════════════════════════════════════════════════════════
# 4) Sidebar links
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "attendance:late_notifications" not in sidebar:
    # نضيف للإدارة تحت التقارير أو الحضور
    target = """      <a href="{% url 'attendance:visits' %}"
         class="nav-link {% if 'visits' in request.path %}active{% endif %}">
        <i class="bi bi-geo-alt"></i><span>الزيارات</span>
      </a>"""
    replacement = target + """
      <a href="{% url 'attendance:late_notifications' %}"
         class="nav-link {% if 'late-notifications' in request.path %}active{% endif %}">
        <i class="bi bi-bell"></i><span>إشعارات التأخير</span>
      </a>"""
    if target in sidebar:
        sidebar = sidebar.replace(target, replacement)

    # نضيف للموظف رابط إنذاراتي في حسابي المالي أو حسابي
    target2 = """      <a href="{% url 'employees:my_deductions' %}"
         class="nav-link {% if 'my-deductions' in request.path %}active{% endif %}">
        <i class="bi bi-receipt-cutoff"></i><span>خصوماتي</span>
      </a>"""
    replacement2 = target2 + """
      <a href="{% url 'attendance:my_warnings' %}"
         class="nav-link {% if 'my-warnings' in request.path %}active{% endif %}">
        <i class="bi bi-exclamation-triangle"></i><span>إنذاراتي</span>
      </a>"""
    if target2 in sidebar:
        sidebar = sidebar.replace(target2, replacement2)

    write_file(sidebar_path, sidebar)
    print("  ✅ تم تحديث الـ Sidebar")
else:
    print("  ℹ️  الروابط موجودة بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 41c اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ قائمة إشعارات التأخير
  2. ✅ صفحة تفاصيل الإشعار
  3. ✅ HR يختار الإجراء
  4. ✅ إنشاء DisciplinaryAction
  5. ✅ إنشاء Deduction تلقائي عند الخصم
  6. ✅ صفحة إنذاراتي للموظف
  7. ✅ روابط في الـ Sidebar

جرب:
  - hr_manager / demo_admin
    /attendance/late-notifications/
  - emp10003
    /attendance/my-warnings/
""")