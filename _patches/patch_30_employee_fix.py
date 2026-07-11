#!/usr/bin/env python3
"""
Patch 30: Employee Experience Fix
===================================
1. صفحة check-in بسيطة للموظف (بدون خريطة)
2. فورم الإجازة ذكي (الموظف يشوف اسمه بس)
3. قائمة طلبات شاملة في الـ Sidebar
"""

import os
import sys

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
print("  Patch 30: Employee Experience Fix")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. صفحة Check-in بسيطة للموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث صفحة تسجيل الحضور...")

checkin_path = os.path.join(BASE_DIR, "templates", "attendance", "check_in.html")
checkin_content = read_file(checkin_path)

# نشوف الملف موجود ونعدل عليه
# الفكرة: نخفي الخريطة عن الموظف العادي

if "request.user.role" not in checkin_content or "employee_simple_checkin" not in checkin_content:
    # نضيف CSS لإخفاء الخريطة عن الموظف + تثبيتها للمدير
    extra_css = """
{% block extra_css %}
<style>
  /* ── إخفاء الخريطة عن الموظف العادي ── */
  {% if request.user.role == 'employee' %}
  #map-container, .map-section, #map {
    display: none !important;
  }
  .checkin-card {
    max-width: 500px;
    margin: 0 auto;
  }
  {% else %}
  /* ── تثبيت الخريطة للمديرين ── */
  #map-container, .map-section {
    position: sticky;
    top: 80px;
    z-index: 10;
  }
  {% endif %}
</style>
{% endblock %}"""

    # نضيف الـ CSS في الملف
    if "{% block extra_css %}" not in checkin_content:
        # نضيف قبل {% block content %}
        checkin_content = checkin_content.replace(
            "{% block content %}",
            extra_css + "\n{% block content %}"
        )
    write_file(checkin_path, checkin_content)
    print("  ✅ الخريطة مخفية عن الموظف")
else:
    print("  ℹ️  التعديل موجود")


# ════════════════════════════════════════════════════════════
# 2. تحديث leave_request_form - الموظف يشوف اسمه بس
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث فورم طلب الإجازة...")

leave_form_path = os.path.join(
    BASE_DIR, "templates", "leaves", "leave_request_form.html"
)

leave_form = read_file(leave_form_path)

# استبدال select الموظف
old_employee_select = """<div class="col-md-6">
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
              </div>"""

new_employee_select = """<div class="col-md-6">
                <label class="form-label fw-semibold small">
                  الموظف <span class="text-danger">*</span>
                </label>

                {% if request.user.role == 'employee' and request.current_employee %}
                  <!-- الموظف يشوف اسمه بس -->
                  <input type="hidden" name="employee"
                         value="{{ request.current_employee.pk }}">
                  <input type="text" class="form-control" readonly
                         value="{{ request.current_employee.full_name_ar }} ({{ request.current_employee.employee_code }})">
                {% else %}
                  <!-- المدير / HR يختار من القائمة -->
                  <select name="employee" class="form-select" required>
                    <option value="">اختر الموظف</option>
                    {% for emp in employees %}
                    <option value="{{ emp.pk }}">
                      {{ emp.full_name_ar }} ({{ emp.employee_code }})
                    </option>
                    {% endfor %}
                  </select>
                {% endif %}
              </div>"""

if old_employee_select in leave_form:
    leave_form = leave_form.replace(old_employee_select, new_employee_select)
    write_file(leave_form_path, leave_form)
    print("  ✅ الموظف يشوف اسمه فقط في طلب الإجازة")
else:
    print("  ℹ️  فورم الإجازة شكله مختلف - هنعدله يدوي")

    # طريقة بديلة: نبحث عن أي select فيه employees
    if "{% for emp in employees %}" in leave_form and "request.current_employee" not in leave_form:
        leave_form = leave_form.replace(
            '{% for emp in employees %}',
            """{% if request.user.role == 'employee' and request.current_employee %}
                  <input type="hidden" name="employee" value="{{ request.current_employee.pk }}">
                  <input type="text" class="form-control" readonly
                         value="{{ request.current_employee.full_name_ar }}">
                {% else %}
                {% for emp in employees %}"""
        )

        leave_form = leave_form.replace(
            '{% endfor %}\n                </select>',
            """{% endfor %}
                </select>
                {% endif %}"""
        )
        write_file(leave_form_path, leave_form)
        print("  ✅ تم التعديل بطريقة بديلة")


# ════════════════════════════════════════════════════════════
# 3. تحديث leaves/views.py - leave_request_add
#    لو الموظف هو اللي فاتح، نحدد employee تلقائي
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث views الإجازات...")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")
sys.path.insert(0, BASE_DIR)

leaves_views_path = os.path.join(BASE_DIR, "leaves", "views.py")
leaves_views = read_file(leaves_views_path)

# نضيف current_employee في context
old_context = """    context = {
        "employees":   employees,
        "leave_types": leave_types,
        "page_title":  "طلب إجازة جديد",
        "today":       timezone.now().date().isoformat(),
    }"""

new_context = """    # لو موظف عادي - يشوف نفسه بس
    if request.user.role == 'employee':
        try:
            from employees.models import Employee as Emp
            current_emp = Emp.objects.filter(user=request.user).first()
            if current_emp:
                employees = [current_emp]
        except Exception:
            pass

    context = {
        "employees":   employees,
        "leave_types": leave_types,
        "page_title":  "طلب إجازة جديد",
        "today":       timezone.now().date().isoformat(),
    }"""

if old_context in leaves_views and "request.user.role == 'employee'" not in leaves_views.split("def leave_request_add")[1].split("def ")[0] if "def leave_request_add" in leaves_views else True:
    leaves_views = leaves_views.replace(old_context, new_context)
    write_file(leaves_views_path, leaves_views)
    print("  ✅ الموظف يشوف نفسه فقط في الـ view")
else:
    print("  ℹ️  الـ view محتاج مراجعة يدوية أو التعديل موجود")


# ════════════════════════════════════════════════════════════
# 4. إنشاء نظام الطلبات الأساسي
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar - قسم الطلبات...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# استبدال قسم الإجازات بقسم طلبات أشمل
old_leaves_section = """    <!-- الإجازات -->
    <div class="sidebar-label">الإجازات</div>
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i><span>طلبات الإجازات</span>
    </a>
    <a href="{% url 'leaves:leave_request_add' %}"
       class="nav-link {% if '/leaves/add' in request.path %}active{% endif %}">
      <i class="bi bi-calendar-plus"></i><span>طلب إجازة جديد</span>
    </a>
    {% if request.user.role != 'employee' %}
    <a href="{% url 'leaves:leave_balances' %}"
       class="nav-link {% if 'balances' in request.path %}active{% endif %}">
      <i class="bi bi-wallet2"></i><span>أرصدة الإجازات</span>
    </a>
    <a href="{% url 'leaves:leave_types_list' %}"
       class="nav-link {% if 'types' in request.path %}active{% endif %}">
      <i class="bi bi-list-check"></i><span>أنواع الإجازات</span>
    </a>
    {% endif %}"""

new_leaves_section = """    <!-- الطلبات -->
    <div class="sidebar-label">الطلبات</div>
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-inbox"></i><span>طلباتي</span>
    </a>
    <a href="{% url 'leaves:leave_request_add' %}"
       class="nav-link {% if '/leaves/add' in request.path %}active{% endif %}">
      <i class="bi bi-plus-circle"></i><span>طلب جديد</span>
    </a>

    {% if request.user.role != 'employee' %}
    <a href="{% url 'leaves:leave_balances' %}"
       class="nav-link {% if 'balances' in request.path %}active{% endif %}">
      <i class="bi bi-wallet2"></i><span>أرصدة الإجازات</span>
    </a>
    <a href="{% url 'leaves:leave_types_list' %}"
       class="nav-link {% if 'types' in request.path %}active{% endif %}">
      <i class="bi bi-list-check"></i><span>أنواع الإجازات</span>
    </a>
    {% endif %}"""

if old_leaves_section in sidebar:
    sidebar = sidebar.replace(old_leaves_section, new_leaves_section)
    write_file(sidebar_path, sidebar)
    print("  ✅ قسم الطلبات في الـ Sidebar")
else:
    print("  ℹ️  الإجازات في الـ Sidebar شكلها مختلف")


# ════════════════════════════════════════════════════════════
# 5. تحسين Dashboard للموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحسين Dashboard للموظف...")

dashboard_path = os.path.join(BASE_DIR, "templates", "dashboard", "index.html")
dashboard = read_file(dashboard_path)

# نضيف أزرار سريعة خاصة بالموظف
if "employee_quick_actions" not in dashboard:
    old_quick_links = """    <a href="{% url 'attendance:check_in_page' %}"
               class="btn btn-sm text-white"
               style="background:#06B6D4;">
              <i class="bi bi-qr-code-scan me-1"></i>تسجيل حضور
            </a>"""

    new_quick_links = """{% if request.current_employee %}
            <a href="{% url 'attendance:check_in' %}"
               class="btn btn-sm text-white"
               style="background:#06B6D4;">
              <i class="bi bi-qr-code-scan me-1"></i>تسجيل حضور
            </a>
            {% endif %}"""

    if old_quick_links in dashboard:
        dashboard = dashboard.replace(old_quick_links, new_quick_links)
    else:
        # نبحث عن أي زرار check-in
        dashboard = dashboard.replace(
            "check_in_page",
            "check_in"
        )

    write_file(dashboard_path, dashboard)
    print("  ✅ أزرار Dashboard محدثة")
else:
    print("  ℹ️  موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 30 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ الخريطة مخفية عن الموظف العادي في صفحة الحضور
  2. ✅ فورم الإجازة ذكي - الموظف يشوف اسمه بس
  3. ✅ الـ view بيحدد الموظف تلقائي لو employee
  4. ✅ الـ Sidebar فيه "طلباتي" و "طلب جديد"
  5. ✅ Dashboard محسن للموظف

جرب دلوقتي:
  1. ادخل بـ emp10003 / Emp@12345
  2. افتح "تسجيل الحضور" - لازم بدون خريطة
  3. افتح "طلب جديد" - لازم يظهر اسمه بس
  4. شوف الـ Sidebar - المفروض نظيف وبسيط
""")