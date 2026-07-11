#!/usr/bin/env python3
"""
Patch 49a: Test Fixes
=====================
Fixes found during practical testing:
1) approval_flows.html get_item filter
2) attendance override URL
3) stealth tracking feature guard
4) send_notification.html broken block
5) visit_form.html extends/load order
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
print("  Patch 49a: Test Fixes")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) approval_flows.html → load custom_filters
# ════════════════════════════════════════════════════════════
print("\n🔧 Fix approval_flows.html...")

approval_path = os.path.join(BASE_DIR, "templates", "companies", "approval_flows.html")
if os.path.exists(approval_path):
    approval = read_file(approval_path)
    if "{% load custom_filters %}" not in approval:
        if approval.startswith("{% extends"):
            approval = approval.replace(
                "{% extends 'base/dashboard_base.html' %}",
                "{% extends 'base/dashboard_base.html' %}\n{% load custom_filters %}",
                1
            )
        else:
            approval = "{% load custom_filters %}\n" + approval
        write_file(approval_path, approval)
        print("  ✅ تم إضافة load custom_filters")
    else:
        print("  ℹ️  load custom_filters موجود بالفعل")
else:
    print("  ⚠️  approval_flows.html غير موجود")

# ════════════════════════════════════════════════════════════
# 2) attendance/urls.py → تأكيد override URL
# ════════════════════════════════════════════════════════════
print("\n🔧 Fix attendance/urls.py...")

att_urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
if os.path.exists(att_urls_path):
    att_urls = read_file(att_urls_path)

    # لو path موجود باسم مختلف أو مش موجود
    if "name='override'" not in att_urls and 'name="override"' not in att_urls:
        if "urlpatterns = [" in att_urls:
            att_urls = att_urls.rstrip()
            if att_urls.endswith("]"):
                att_urls = att_urls[:-1] + "\n    path('<int:pk>/override/', views.attendance_override, name='override'),\n]\n"
                write_file(att_urls_path, att_urls)
                print("  ✅ تم إضافة URL override")
        else:
            print("  ⚠️  urlpatterns غير متوقعة")
    else:
        print("  ℹ️  URL override موجود بالفعل")
else:
    print("  ⚠️  attendance/urls.py غير موجود")

# ════════════════════════════════════════════════════════════
# 3) subscriptions/helpers.py → stealth_tracking in demo features/aliases
# ════════════════════════════════════════════════════════════
print("\n🔧 Fix subscriptions/helpers.py...")

helpers_path = os.path.join(BASE_DIR, "subscriptions", "helpers.py")
if os.path.exists(helpers_path):
    helpers = read_file(helpers_path)

    if "'stealth_tracking'" not in helpers:
        helpers = helpers.replace(
            "'payroll_basic',",
            "'payroll_basic',\n    'stealth_tracking',"
        )
        print("  ✅ تم إضافة stealth_tracking إلى DEMO_FEATURES")

    if "'stealth_tracking': 'stealth_tracking'" not in helpers:
        # نضيف alias بسيط
        marker = "'payroll_basic': 'payroll_basic',"
        if marker in helpers:
            helpers = helpers.replace(
                marker,
                marker + "\n    'stealth_tracking': 'stealth_tracking',"
            )
            print("  ✅ تم إضافة alias للـ stealth_tracking")

    write_file(helpers_path, helpers)
else:
    print("  ⚠️  subscriptions/helpers.py غير موجود")

# ════════════════════════════════════════════════════════════
# 4) send_notification.html → إعادة كتابة نظيفة
# ════════════════════════════════════════════════════════════
print("\n🔧 Fix send_notification.html...")

send_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إرسال إشعار{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="row justify-content-center">
    <div class="col-lg-7">

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
                <input type="text" name="title" class="form-control" required placeholder="عنوان الإشعار">
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">الرسالة</label>
                <textarea name="message" class="form-control" rows="5" required placeholder="اكتب رسالة الإشعار هنا..."></textarea>
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
{% endblock %}

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
write_file(
    os.path.join(BASE_DIR, "templates", "accounts", "send_notification.html"),
    send_template
)

# ════════════════════════════════════════════════════════════
# 5) visit_form.html → تأكيد extends أول سطر
# ════════════════════════════════════════════════════════════
print("\n🔧 Fix attendance/visit_form.html...")

visit_path = os.path.join(BASE_DIR, "templates", "attendance", "visit_form.html")
if os.path.exists(visit_path):
    visit = read_file(visit_path)

    # شيل أي load من أول الملف وحطه بعد extends
    lines = visit.splitlines()
    load_lines = [ln for ln in lines if "{% load" in ln]
    other_lines = [ln for ln in lines if "{% load" not in ln]

    extends_idx = None
    for i, line in enumerate(other_lines):
        if "{% extends" in line:
            extends_idx = i
            break

    if extends_idx is not None:
        new_lines = other_lines[:extends_idx+1]
        for ln in load_lines:
            if ln not in new_lines:
                new_lines.append(ln)
        new_lines += other_lines[extends_idx+1:]
        new_content = "\n".join(new_lines)
        write_file(visit_path, new_content)
        print("  ✅ تم تصحيح ترتيب extends/load")
    else:
        print("  ⚠️  لم أجد extends")
else:
    print("  ⚠️  visit_form.html غير موجود")

print("\n" + "=" * 60)
print("  ✅ Patch 49a اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  1. ✅ approval_flows.html → get_item filter
  2. ✅ attendance override URL
  3. ✅ stealth_tracking feature guard
  4. ✅ send_notification.html
  5. ✅ visit_form.html extends/load order

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000

ثم جرّب تاني:
  /companies/approval-flows/
  /attendance/
  /attendance/stealth-manage/
  /accounts/notifications/send/
  /attendance/visits/add/
""")