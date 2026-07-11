#!/usr/bin/env python3
"""
Patch 45c: Workflow UI
=======================
1) صفحة مسارات الموافقة (ApprovalFlow management)
2) صفحة التفويضات (ApprovalDelegation)
3) تحديث request detail بالخطوات
4) URLs + Sidebar
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
print("  Patch 45c: Workflow UI")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) companies/views.py — Approval Flows + Delegations
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/views.py...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

workflow_company_views = '''

# ════════════════════════════════════════════════════════════
# Approval Flows Management
# ════════════════════════════════════════════════════════════

@login_required
def approval_flows_view(request):
    """إدارة مسارات الموافقة"""
    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    from requests_app.models import RequestType, ApprovalFlow

    company = request.user.company
    request_types = RequestType.objects.filter(
        company=company,
        is_active=True
    ).select_related("category")

    flows = ApprovalFlow.objects.filter(company=company)
    flows_map = {f.request_type_id: f for f in flows}

    if request.method == "POST":
        rt_id = request.POST.get("request_type")
        rt = get_object_or_404(RequestType, pk=rt_id, company=company)

        flow, _ = ApprovalFlow.objects.get_or_create(
            company=company,
            request_type=rt,
        )
        flow.step_1_role = request.POST.get("step_1_role", "direct_manager")
        flow.step_2_role = request.POST.get("step_2_role", "hr_manager")
        flow.step_3_role = request.POST.get("step_3_role", "skip")
        flow.escalation_enabled = "escalation_enabled" in request.POST
        flow.escalation_to = request.POST.get("escalation_to", "hr_manager")
        flow.notify_employee_on_each_step = "notify_employee" in request.POST
        flow.save()

        messages.success(request, f"تم حفظ مسار الموافقة لـ {rt.name}")
        return redirect("companies:approval_flows")

    context = {
        "request_types": request_types,
        "flows_map": flows_map,
        "page_title": "مسارات الموافقة",
    }
    return render(request, "companies/approval_flows.html", context)


# ════════════════════════════════════════════════════════════
# Approval Delegations Management
# ════════════════════════════════════════════════════════════

@login_required
def delegations_view(request):
    """إدارة التفويضات"""
    from requests_app.models import ApprovalDelegation
    from accounts.models import User

    company = request.user.company
    role = getattr(request.user, "role", "")

    delegations = ApprovalDelegation.objects.filter(
        company=company
    ).select_related("delegator", "delegate").order_by("-start_date")

    eligible_users = User.objects.filter(
        company=company,
        is_active=True,
        role__in=["manager", "hr_manager", "company_admin", "super_admin"]
    )

    context = {
        "delegations": delegations,
        "eligible_users": eligible_users,
        "page_title": "التفويضات",
    }
    return render(request, "companies/delegations.html", context)


@login_required
def delegation_add(request):
    """إضافة تفويض جديد"""
    from requests_app.models import ApprovalDelegation
    from accounts.models import User
    from datetime import date as dt_date

    company = request.user.company
    role = getattr(request.user, "role", "")

    eligible_users = User.objects.filter(
        company=company,
        is_active=True
    ).exclude(pk=request.user.pk)

    if request.method == "POST":
        delegate_id = request.POST.get("delegate")
        start_str = request.POST.get("start_date")
        end_str = request.POST.get("end_date")
        scope = request.POST.get("scope", "all_approvals")
        reason = request.POST.get("reason", "")

        if not delegate_id or not start_str or not end_str:
            messages.error(request, "جميع الحقول مطلوبة")
        else:
            delegate = get_object_or_404(User, pk=delegate_id, company=company)
            start_date = dt_date.fromisoformat(start_str)
            end_date = dt_date.fromisoformat(end_str)

            if end_date < start_date:
                messages.error(request, "تاريخ الانتهاء لازم يكون بعد البداية")
            else:
                ApprovalDelegation.objects.create(
                    company=company,
                    delegator=request.user,
                    delegate=delegate,
                    delegator_role=role,
                    start_date=start_date,
                    end_date=end_date,
                    scope=scope,
                    reason=reason,
                    is_active=True,
                )
                messages.success(
                    request,
                    f"تم إنشاء التفويض لـ {delegate.get_full_name() or delegate.username}"
                )
                return redirect("companies:delegations")

    context = {
        "eligible_users": eligible_users,
        "page_title": "إضافة تفويض",
    }
    return render(request, "companies/delegation_add.html", context)


@login_required
def delegation_deactivate(request, pk):
    """إلغاء تفويض"""
    from requests_app.models import ApprovalDelegation

    delegation = get_object_or_404(
        ApprovalDelegation,
        pk=pk,
        company=request.user.company
    )

    if request.method == "POST":
        delegation.is_active = False
        delegation.save(update_fields=["is_active"])
        messages.success(request, "تم إلغاء التفويض")

    return redirect("companies:delegations")
'''

if "def approval_flows_view" not in comp_views:
    comp_views += workflow_company_views
    write_file(comp_views_path, comp_views)
    print("  ✅ تم إضافة Approval Flows + Delegations views")
else:
    print("  ℹ️  views موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) companies/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/urls.py...")

comp_urls_path = os.path.join(BASE_DIR, "companies", "urls.py")
comp_urls = read_file(comp_urls_path)

if "approval_flows" not in comp_urls:
    comp_urls = comp_urls.rstrip()
    if comp_urls.endswith("]"):
        comp_urls = comp_urls[:-1]
        comp_urls += """
    # Workflow
    path('approval-flows/', views.approval_flows_view, name='approval_flows'),
    path('delegations/', views.delegations_view, name='delegations'),
    path('delegations/add/', views.delegation_add, name='delegation_add'),
    path('delegations/<int:pk>/deactivate/', views.delegation_deactivate, name='delegation_deactivate'),
]
"""
        write_file(comp_urls_path, comp_urls)
        print("  ✅ تم إضافة URLs")
else:
    print("  ℹ️  URLs موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 3) Templates
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء Templates...")

# approval_flows.html
create_file(
    os.path.join(BASE_DIR, "templates", "companies", "approval_flows.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}مسارات الموافقة{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-diagram-2 me-2" style="color:#06B6D4;"></i>
      مسارات الموافقة
    </h4>
    <p class="text-muted mb-0">حدد من يوافق على كل نوع طلب وبأي ترتيب</p>
  </div>

  {% for rt in request_types %}
  {% with flow=flows_map|get_item:rt.pk %}
  <div class="card border-0 shadow-sm mb-3">
    <div class="card-body p-4">
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="request_type" value="{{ rt.pk }}">

        <div class="row align-items-center g-3">

          <div class="col-md-3">
            <div class="d-flex align-items-center gap-2">
              <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                   style="width:36px;height:36px;background:#e0f7fa;">
                <i class="bi bi-file-text" style="color:#06B6D4;font-size:0.9rem;"></i>
              </div>
              <div>
                <div class="fw-bold small">{{ rt.name }}</div>
                <small class="text-muted">{{ rt.category.name }}</small>
              </div>
            </div>
          </div>

          <div class="col-md-2">
            <label class="form-label small fw-semibold">الخطوة 1</label>
            <select name="step_1_role" class="form-select form-select-sm">
              <option value="skip" {% if not flow or flow.step_1_role == 'skip' %}selected{% endif %}>تخطي</option>
              <option value="direct_manager" {% if flow and flow.step_1_role == 'direct_manager' %}selected{% endif %}>المدير المباشر</option>
              <option value="hr_manager" {% if flow and flow.step_1_role == 'hr_manager' %}selected{% endif %}>مدير HR</option>
              <option value="company_admin" {% if flow and flow.step_1_role == 'company_admin' %}selected{% endif %}>صاحب الشركة</option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label small fw-semibold">الخطوة 2</label>
            <select name="step_2_role" class="form-select form-select-sm">
              <option value="skip" {% if not flow or flow.step_2_role == 'skip' %}selected{% endif %}>تخطي</option>
              <option value="direct_manager" {% if flow and flow.step_2_role == 'direct_manager' %}selected{% endif %}>المدير المباشر</option>
              <option value="hr_manager" {% if flow and flow.step_2_role == 'hr_manager' %}selected{% endif %}>مدير HR</option>
              <option value="company_admin" {% if flow and flow.step_2_role == 'company_admin' %}selected{% endif %}>صاحب الشركة</option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label small fw-semibold">الخطوة 3</label>
            <select name="step_3_role" class="form-select form-select-sm">
              <option value="skip" {% if not flow or flow.step_3_role == 'skip' %}selected{% endif %}>تخطي</option>
              <option value="direct_manager" {% if flow and flow.step_3_role == 'direct_manager' %}selected{% endif %}>المدير المباشر</option>
              <option value="hr_manager" {% if flow and flow.step_3_role == 'hr_manager' %}selected{% endif %}>مدير HR</option>
              <option value="company_admin" {% if flow and flow.step_3_role == 'company_admin' %}selected{% endif %}>صاحب الشركة</option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label small fw-semibold">التصعيد لـ</label>
            <select name="escalation_to" class="form-select form-select-sm">
              <option value="hr_manager" {% if not flow or flow.escalation_to == 'hr_manager' %}selected{% endif %}>HR</option>
              <option value="company_admin" {% if flow and flow.escalation_to == 'company_admin' %}selected{% endif %}>صاحب الشركة</option>
            </select>
          </div>

          <div class="col-md-1 text-end">
            <div class="d-flex gap-1 flex-column">
              <div class="form-check form-check-inline m-0">
                <input class="form-check-input" type="checkbox"
                       name="escalation_enabled" id="esc_{{ rt.pk }}"
                       {% if not flow or flow.escalation_enabled %}checked{% endif %}>
                <label class="form-check-label" style="font-size:0.7rem;" for="esc_{{ rt.pk }}">تصعيد</label>
              </div>
              <div class="form-check form-check-inline m-0">
                <input class="form-check-input" type="checkbox"
                       name="notify_employee" id="notif_{{ rt.pk }}"
                       {% if not flow or flow.notify_employee_on_each_step %}checked{% endif %}>
                <label class="form-check-label" style="font-size:0.7rem;" for="notif_{{ rt.pk }}">إشعار</label>
              </div>
            </div>
          </div>

          <div class="col-12 col-md-auto">
            <button type="submit" class="btn btn-sm text-white"
                    style="background:#06B6D4; border-radius:8px;">
              حفظ
            </button>
          </div>

        </div>
      </form>
    </div>
  </div>
  {% endwith %}
  {% endfor %}

</div>
{% endblock %}
"""
)

# delegations.html
create_file(
    os.path.join(BASE_DIR, "templates", "companies", "delegations.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}التفويضات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-person-check me-2" style="color:#06B6D4;"></i>
        التفويضات
      </h4>
      <p class="text-muted mb-0">إدارة تفويضات الصلاحيات</p>
    </div>
    <a href="{% url 'companies:delegation_add' %}"
       class="btn text-white"
       style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i>تفويض جديد
    </a>
  </div>

  {% if delegations %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">المُفوِّض</th>
            <th>المُفوَّض إليه</th>
            <th>من</th>
            <th>إلى</th>
            <th>النطاق</th>
            <th>الحالة</th>
            <th>السبب</th>
            <th class="text-center">إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {% for d in delegations %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold small">{{ d.delegator.get_full_name|default:d.delegator.username }}</div>
              <small class="text-muted">{{ d.delegator_role }}</small>
            </td>
            <td class="fw-semibold small">
              {{ d.delegate.get_full_name|default:d.delegate.username }}
            </td>
            <td class="text-muted small">{{ d.start_date|date:"d/m/Y" }}</td>
            <td class="text-muted small">{{ d.end_date|date:"d/m/Y" }}</td>
            <td>
              <span class="badge bg-light text-dark border">
                {% if d.scope == 'all_approvals' %}كل الموافقات
                {% else %}فريقه فقط{% endif %}
              </span>
            </td>
            <td>
              {% if d.is_currently_active %}
                <span class="badge bg-success">نشط</span>
              {% elif d.is_active %}
                <span class="badge bg-secondary">منتهي</span>
              {% else %}
                <span class="badge bg-danger">ملغي</span>
              {% endif %}
            </td>
            <td class="text-muted small">{{ d.reason|default:"—"|truncatechars:30 }}</td>
            <td class="text-center">
              {% if d.is_active %}
              <form method="post"
                    action="{% url 'companies:delegation_deactivate' d.pk %}"
                    onsubmit="return confirm('إلغاء التفويض؟')">
                {% csrf_token %}
                <button type="submit" class="btn btn-sm btn-outline-danger">إلغاء</button>
              </form>
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
      <i class="bi bi-person-check" style="font-size:4rem; color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا توجد تفويضات</h5>
      <a href="{% url 'companies:delegation_add' %}"
         class="btn mt-2 text-white"
         style="background:#06B6D4;">
        <i class="bi bi-plus me-1"></i>أضف تفويض
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)

# delegation_add.html
create_file(
    os.path.join(BASE_DIR, "templates", "companies", "delegation_add.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إضافة تفويض{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="row justify-content-center">
    <div class="col-lg-7">

      <div class="d-flex align-items-center mb-4">
        <a href="{% url 'companies:delegations' %}" class="btn btn-outline-secondary btn-sm me-3">
          <i class="bi bi-arrow-right"></i>
        </a>
        <h4 class="fw-bold mb-0">إضافة تفويض جديد</h4>
      </div>

      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-12">
                <div class="alert alert-info border-0 small">
                  <i class="bi bi-info-circle me-2"></i>
                  <strong>أنت:</strong> {{ request.user.get_full_name|default:request.user.username }}
                  — تفوّض صلاحياتك لشخص آخر خلال فترة غيابك.
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">المُفوَّض إليه <span class="text-danger">*</span></label>
                <select name="delegate" class="form-select" required>
                  <option value="">اختر الشخص</option>
                  {% for u in eligible_users %}
                  <option value="{{ u.pk }}">
                    {{ u.get_full_name|default:u.username }}
                    ({{ u.get_role_display|default:u.role }})
                  </option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">من تاريخ <span class="text-danger">*</span></label>
                <input type="date" name="start_date" class="form-control" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">إلى تاريخ <span class="text-danger">*</span></label>
                <input type="date" name="end_date" class="form-control" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">نطاق التفويض</label>
                <select name="scope" class="form-select">
                  <option value="all_approvals">كل الموافقات</option>
                  <option value="team_only">فريقي فقط</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">السبب</label>
                <input type="text" name="reason" class="form-control"
                       placeholder="مثال: إجازة سنوية، سفر عمل...">
              </div>

            </div>

            <div class="mt-4">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>إنشاء التفويض
              </button>
              <a href="{% url 'companies:delegations' %}"
                 class="btn btn-outline-secondary px-4 ms-2"
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

# request detail محدث بالخطوات
create_file(
    os.path.join(BASE_DIR, "templates", "requests_app", "detail.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}تفاصيل الطلب{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'requests_app:list' %}" class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">تفاصيل الطلب</h4>
    <span class="badge bg-{{ req.status_color }} ms-3 fs-6 px-3">
      <i class="bi bi-{{ req.status_icon }} me-1"></i>
      {{ req.get_status_display }}
    </span>
    {% if req.priority == 'urgent' %}
    <span class="badge bg-danger ms-2">عاجل</span>
    {% endif %}
  </div>

  <div class="row g-4">

    <div class="col-lg-8">

      <!-- بيانات الطلب -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">{{ req.subject }}</h5>
          <small class="text-muted">
            {{ req.request_type.category.name }} ← {{ req.request_type.name }}
          </small>
        </div>
        <div class="card-body px-4 pb-4">
          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="text-muted small">الموظف</label>
              <div class="fw-bold">{{ req.employee.full_name_ar }}</div>
              <small class="text-muted">{{ req.employee.employee_code }}</small>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">تاريخ الطلب</label>
              <div class="fw-bold">{{ req.created_at|date:"d/m/Y H:i" }}</div>
            </div>
            {% if req.start_date %}
            <div class="col-md-6">
              <label class="text-muted small">من تاريخ</label>
              <div class="fw-bold">{{ req.start_date|date:"d/m/Y" }}</div>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">إلى تاريخ</label>
              <div class="fw-bold">{{ req.end_date|date:"d/m/Y"|default:"—" }}</div>
            </div>
            {% endif %}
            {% if req.amount %}
            <div class="col-md-6">
              <label class="text-muted small">المبلغ</label>
              <div class="fw-bold fs-5" style="color:#06B6D4;">{{ req.amount }} ج.م</div>
            </div>
            {% endif %}
            {% if req.substitute_employee %}
            <div class="col-md-6">
              <label class="text-muted small">البديل</label>
              <div class="fw-bold">{{ req.substitute_employee.full_name_ar }}</div>
            </div>
            {% endif %}
          </div>

          <label class="text-muted small">التفاصيل</label>
          <div class="p-3 rounded mb-3" style="background:#f8fafc;">{{ req.details }}</div>

          {% if req.document %}
          <a href="{{ req.document.url }}" target="_blank" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-file-earmark me-1"></i>عرض المرفق
          </a>
          {% endif %}
        </div>
      </div>

      <!-- مسار الموافقة -->
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">مسار الموافقة</h5>
        </div>
        <div class="card-body p-4">
          <div class="d-flex align-items-start gap-3 flex-wrap">

            {% for step_num, step_status, step_by, step_at, step_label in steps_info %}
            <div class="text-center" style="min-width:120px;">
              <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-2"
                   style="width:50px;height:50px;
                          background:{% if step_status == 'approved' %}#e8f5e9
                          {% elif step_status == 'rejected' %}#fde8e8
                          {% elif step_status == 'pending' %}#fff7ed
                          {% else %}#f3f4f6{% endif %};">
                <i class="bi bi-{% if step_status == 'approved' %}check-circle-fill text-success
                                 {% elif step_status == 'rejected' %}x-circle-fill text-danger
                                 {% elif step_status == 'pending' %}hourglass-split text-warning
                                 {% else %}dash-circle text-muted{% endif %}"
                   style="font-size:1.3rem;"></i>
              </div>
              <div class="fw-semibold small">الخطوة {{ step_num }}</div>
              <div class="text-muted" style="font-size:0.72rem;">{{ step_label }}</div>
              {% if step_status == 'approved' or step_status == 'rejected' %}
              <div class="text-muted" style="font-size:0.7rem;">
                {{ step_by.get_full_name|default:step_by.username }}
              </div>
              {% endif %}
            </div>

            {% if not forloop.last %}
            <div class="d-flex align-items-center mt-3">
              <i class="bi bi-arrow-left text-muted"></i>
            </div>
            {% endif %}
            {% endfor %}

          </div>
        </div>
      </div>

    </div>

    <!-- الإجراءات -->
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h6 class="fw-bold mb-3">الإجراءات</h6>

          {% if req.status == 'pending' and can_approve %}

          <form method="post" action="{% url 'requests_app:approve' req.pk %}" class="mb-2">
            {% csrf_token %}
            <textarea name="notes" class="form-control form-control-sm mb-2"
                      placeholder="ملاحظات الموافقة" rows="2"></textarea>
            <button type="submit" class="btn btn-success w-100 fw-bold"
                    onclick="return confirm('الموافقة على الطلب؟')">
              <i class="bi bi-check-lg me-1"></i>موافقة
            </button>
          </form>

          <form method="post" action="{% url 'requests_app:reject' req.pk %}" class="mb-2">
            {% csrf_token %}
            <textarea name="notes" class="form-control form-control-sm mb-2"
                      placeholder="سبب الرفض" rows="2"></textarea>
            <button type="submit" class="btn btn-danger w-100 fw-bold"
                    onclick="return confirm('رفض الطلب؟')">
              <i class="bi bi-x-lg me-1"></i>رفض
            </button>
          </form>

          {% elif req.status == 'pending' and not can_approve %}
          <div class="alert alert-warning border-0 small">
            <i class="bi bi-hourglass-split me-2"></i>
            الطلب في انتظار موافقة الخطوة {{ req.current_step }}
          </div>

          {% else %}
          <div class="text-center text-muted py-3">
            <i class="bi bi-check-all fs-3"></i>
            <p class="mb-0 mt-1 small">تم اتخاذ الإجراء</p>
          </div>
          {% endif %}

          {% if req.status == 'pending' %}
          <form method="post" action="{% url 'requests_app:cancel' req.pk %}">
            {% csrf_token %}
            <button type="submit" class="btn btn-outline-secondary w-100 mt-2"
                    onclick="return confirm('إلغاء الطلب؟')">
              <i class="bi bi-slash-circle me-1"></i>إلغاء الطلب
            </button>
          </form>
          {% endif %}

          <hr>
          <a href="{% url 'requests_app:list' %}" class="btn btn-light w-100">
            <i class="bi bi-arrow-right me-1"></i>رجوع للقائمة
          </a>
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 4) تحديث request_detail view لإرسال steps_info و can_approve
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث request_detail view...")

req_views_path = os.path.join(BASE_DIR, "requests_app", "views.py")
req_views = read_file(req_views_path)

old_detail = '''@login_required
def request_detail(request, pk):
    """تفاصيل طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    context = {
        "req": req_obj,
        "page_title": f"طلب: {req_obj.subject}",
    }
    return render(request, "requests_app/detail.html", context)'''

new_detail = '''@login_required
def request_detail(request, pk):
    """تفاصيل طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )

    # بناء خطوات المسار
    steps_info = []
    step_labels = {
        "direct_manager": "المدير المباشر",
        "hr_manager": "مدير HR",
        "company_admin": "صاحب الشركة",
        "skip": "تخطي",
    }
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)
    if flow:
        active_steps = flow.get_active_steps()
        step_data = [
            (1, req_obj.step_1_status, req_obj.step_1_by, req_obj.step_1_at),
            (2, req_obj.step_2_status, req_obj.step_2_by, req_obj.step_2_at),
            (3, req_obj.step_3_status, req_obj.step_3_by, req_obj.step_3_at),
        ]
        for step_key, role, label in active_steps:
            num = int(step_key[-1])
            sn, ss, sb, sa = step_data[num - 1]
            steps_info.append((sn, ss or "", sb, sa, label))
    else:
        steps_info = [
            (1, req_obj.step_1_status or "pending", req_obj.step_1_by, req_obj.step_1_at, "HR"),
        ]

    can_approve, step_num, role = _can_user_approve_step(req_obj, request.user)

    context = {
        "req": req_obj,
        "steps_info": steps_info,
        "can_approve": can_approve and req_obj.status == "pending",
        "page_title": f"طلب: {req_obj.subject}",
    }
    return render(request, "requests_app/detail.html", context)'''

if old_detail in req_views:
    req_views = req_views.replace(old_detail, new_detail)
    write_file(req_views_path, req_views)
    print("  ✅ تم تحديث request_detail")
else:
    print("  ℹ️  request_detail مختلف — قد يكون محدث")


# ════════════════════════════════════════════════════════════
# 5) Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "companies:approval_flows" not in sidebar:
    target = """      <a href="{% url 'companies:charter_manage' %}"
         class="nav-link {% if 'charter/manage' in request.path %}active{% endif %}">
        <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
      </a>"""
    replacement = target + """
      <a href="{% url 'companies:approval_flows' %}"
         class="nav-link {% if 'approval-flows' in request.path %}active{% endif %}">
        <i class="bi bi-diagram-2"></i><span>مسارات الموافقة</span>
      </a>
      <a href="{% url 'companies:delegations' %}"
         class="nav-link {% if 'delegations' in request.path %}active{% endif %}">
        <i class="bi bi-person-check"></i><span>التفويضات</span>
      </a>"""
    if target in sidebar:
        sidebar = sidebar.replace(target, replacement)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة روابط Workflow")
    else:
        print("  ℹ️  لم أجد مكان الإدراج")
else:
    print("  ℹ️  روابط Workflow موجودة")


print("\n" + "=" * 60)
print("  ✅ Patch 45c اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ صفحة مسارات الموافقة
  2. ✅ صفحة التفويضات
  3. ✅ صفحة إضافة تفويض
  4. ✅ صفحة تفاصيل الطلب محدثة بالخطوات
  5. ✅ Sidebar links

جرب:
  - /companies/approval-flows/    ← مسارات الموافقة
  - /companies/delegations/       ← التفويضات
  - /requests/add/                ← طلب جديد (يطبق workflow تلقائي)
  - /requests/<pk>/               ← تفاصيل الطلب بالخطوات
""")