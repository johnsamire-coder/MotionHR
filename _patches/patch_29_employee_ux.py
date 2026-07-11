#!/usr/bin/env python3
"""
Patch 29: Employee UX + Fix my_plan + Sidebar cleanup
======================================================
1. إصلاح my_plan.html (extends must be first)
2. إخفاء خطتي/تواصل من الموظف العادي
3. تحسين Sidebar للموظف
"""

import os
import sys
import glob

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
print("  Patch 29: Employee UX + Fixes")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إصلاح كل الملفات اللي فيها load قبل extends
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح {% load %} قبل {% extends %}...")

all_templates = glob.glob(
    os.path.join(BASE_DIR, "templates", "**", "*.html"),
    recursive=True
)

fixed_count = 0
for tmpl in all_templates:
    content = read_file(tmpl)

    if "{% load custom_filters %}" in content and "{% extends" in content:
        lines = content.split("\n")
        load_line_idx = None
        extends_line_idx = None

        for i, line in enumerate(lines):
            if "{% load custom_filters %}" in line and load_line_idx is None:
                load_line_idx = i
            if "{% extends" in line and extends_line_idx is None:
                extends_line_idx = i

        if load_line_idx is not None and extends_line_idx is not None:
            if load_line_idx < extends_line_idx:
                # load قبل extends - لازم نشيل load ونحطه بعد extends
                load_line = lines.pop(load_line_idx)
                # extends بقى في مكان مختلف
                for j, line in enumerate(lines):
                    if "{% extends" in line:
                        # نحط load بعد extends
                        lines.insert(j + 1, load_line)
                        break
                new_content = "\n".join(lines)
                if new_content != content:
                    write_file(tmpl, new_content)
                    fixed_count += 1

print(f"  ✅ تم إصلاح {fixed_count} ملف")


# ════════════════════════════════════════════════════════════
# 2. تحديث dashboard_base.html — Sidebar للموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Sidebar للموظف...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# استبدال قسم الاشتراك ليكون admin فقط
old_subscription = """    <!-- ── الاشتراك ── -->
    <div class="sidebar-section">
      <div class="sidebar-section-label">الاشتراك</div>
    </div>

    <a href="{% url 'subscriptions:my_plan' %}"
       class="nav-link {% if 'my-plan' in request.path %}active{% endif %}">
      <i class="bi bi-star"></i>
      <span>خطتي</span>
    </a>

    <a href="{% url 'subscriptions:contact_sales' %}"
       class="nav-link {% if 'contact-sales' in request.path %}active{% endif %}">
      <i class="bi bi-headset"></i>
      <span>تواصل / ترقية</span>
    </a>"""

new_subscription = """    <!-- ── الاشتراك (للإدارة فقط) ── -->
    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <div class="sidebar-section">
      <div class="sidebar-section-label">الاشتراك</div>
    </div>

    <a href="{% url 'subscriptions:my_plan' %}"
       class="nav-link {% if 'my-plan' in request.path %}active{% endif %}">
      <i class="bi bi-star"></i>
      <span>خطتي</span>
    </a>

    <a href="{% url 'subscriptions:contact_sales' %}"
       class="nav-link {% if 'contact-sales' in request.path %}active{% endif %}">
      <i class="bi bi-headset"></i>
      <span>تواصل / ترقية</span>
    </a>
    {% endif %}"""

if old_subscription in sidebar:
    sidebar = sidebar.replace(old_subscription, new_subscription)
    write_file(sidebar_path, sidebar)
    print("  ✅ تم إخفاء الاشتراك من الموظف")
else:
    print("  ℹ️  قسم الاشتراك شكله مختلف - هنبحث بطريقة تانية")

    # نبحث عن الجزء بطريقة أقل تحديدًا
    if "subscriptions:my_plan" in sidebar and "{% if request.user.role" not in sidebar.split("subscriptions:my_plan")[0][-200:]:
        # نلف الجزء ده بـ if
        sidebar = sidebar.replace(
            """<a href="{% url 'subscriptions:my_plan' %}"""",
            """{% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <a href="{% url 'subscriptions:my_plan' %}" """
        )
        sidebar = sidebar.replace(
            """<span>تواصل / ترقية</span>
    </a>

  </nav>""",
            """<span>تواصل / ترقية</span>
    </a>
    {% endif %}

  </nav>"""
        )
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إخفاء الاشتراك من الموظف (طريقة بديلة)")


# ════════════════════════════════════════════════════════════
# 3. إخفاء "تسجيل الحضور" لو المستخدم مش مربوط بموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحسين عرض تسجيل الحضور في الـ Sidebar...")

sidebar = read_file(sidebar_path)

old_checkin = """<a href="{% url 'attendance:check_in' %}"
       class="nav-link {% if 'check-in' in request.path %}active{% endif %}">
      <i class="bi bi-qr-code-scan"></i>
      <span>تسجيل الحضور</span>
    </a>"""

new_checkin = """{% if request.current_employee or request.user.role == 'employee' %}
    <a href="{% url 'attendance:check_in' %}"
       class="nav-link {% if 'check-in' in request.path %}active{% endif %}">
      <i class="bi bi-qr-code-scan"></i>
      <span>تسجيل الحضور</span>
    </a>
    {% endif %}"""

if old_checkin in sidebar:
    sidebar = sidebar.replace(old_checkin, new_checkin)
    write_file(sidebar_path, sidebar)
    print("  ✅ تسجيل الحضور يظهر للموظفين فقط")
else:
    print("  ℹ️  تسجيل الحضور - النص مختلف شوية")


# ════════════════════════════════════════════════════════════
# 4. إضافة "طلب إجازة" سريع للموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة 'طلب إجازة' في الـ Sidebar...")

sidebar = read_file(sidebar_path)

old_leaves = """<a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i>
      <span>طلبات الإجازات</span>
    </a>"""

new_leaves = """<a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'types' not in request.path and 'balances' not in request.path and 'add' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i>
      <span>طلبات الإجازات</span>
    </a>

    <a href="{% url 'leaves:leave_request_add' %}"
       class="nav-link {% if '/leaves/add' in request.path %}active{% endif %}">
      <i class="bi bi-calendar-plus"></i>
      <span>طلب إجازة جديد</span>
    </a>"""

if old_leaves in sidebar:
    sidebar = sidebar.replace(old_leaves, new_leaves)
    write_file(sidebar_path, sidebar)
    print("  ✅ تم إضافة 'طلب إجازة جديد' في الـ Sidebar")
else:
    print("  ℹ️  الإجازات - النص مختلف")


# ════════════════════════════════════════════════════════════
# 5. إضافة رابط الملف الشخصي في الـ Sidebar للموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة الملف الشخصي في الـ Sidebar...")

sidebar = read_file(sidebar_path)

if "accounts:profile" not in sidebar or sidebar.count("accounts:profile") < 2:
    # نضيف قبل نهاية الـ nav
    profile_link = """
    <!-- ── حسابي ── -->
    <div class="sidebar-section">
      <div class="sidebar-section-label">حسابي</div>
    </div>

    <a href="{% url 'accounts:profile' %}"
       class="nav-link {% if 'profile' in request.path %}active{% endif %}">
      <i class="bi bi-person-circle"></i>
      <span>الملف الشخصي</span>
    </a>

    <a href="{% url 'password_change' %}"
       class="nav-link {% if 'password-change' in request.path %}active{% endif %}">
      <i class="bi bi-key"></i>
      <span>تغيير كلمة المرور</span>
    </a>
"""

    # نضيف قبل الاشتراك أو قبل نهاية الـ nav
    if "<!-- ── الاشتراك" in sidebar:
        sidebar = sidebar.replace(
            "<!-- ── الاشتراك",
            profile_link + "\n    <!-- ── الاشتراك"
        )
    elif "</nav>" in sidebar:
        sidebar = sidebar.replace(
            "</nav>",
            profile_link + "\n  </nav>"
        )

    write_file(sidebar_path, sidebar)
    print("  ✅ تم إضافة الملف الشخصي وتغيير كلمة المرور")
else:
    print("  ℹ️  الملف الشخصي موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 29 اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  1. ✅ {% load %} قبل {% extends %} في كل التمبلتس
  2. ✅ خطتي / تواصل - ظاهرين للإدارة فقط
  3. ✅ تسجيل الحضور - يظهر للموظفين المربوطين فقط
  4. ✅ طلب إجازة جديد - في الـ Sidebar
  5. ✅ الملف الشخصي + تغيير كلمة المرور - في الـ Sidebar

جرب دلوقتي:
  1. ادخل بـ emp10001 / Emp@12345
     - لازم يشوف: حضور + إجازات + ملفه
     - ما يشوفش: خطتي + تواصل + إعدادات الشركة

  2. ادخل بـ demo_admin / Demo@12345
     - لازم يشوف: كل حاجة ما عدا تسجيل الحضور

  3. افتح /subscriptions/my-plan/ بـ demo_admin
     - لازم يشتغل بدون خطأ
""")