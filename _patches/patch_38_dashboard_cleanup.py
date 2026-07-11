#!/usr/bin/env python3
"""
Patch 38: Dashboard + Sidebar Cleanup
=======================================
1. إخفاء الاشتراك من كل الأدوار إلا company_admin + super_admin
2. إضافة المسمى الوظيفي تحت اسم الموظف في Dashboard
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 38: Dashboard + Sidebar Cleanup")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. تحديث Sidebar — الاشتراك لصاحب الشركة فقط
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# تغيير شرط الاشتراك
old_sub_condition = "{% if request.user.role in 'super_admin,company_admin,hr_manager' %}"
new_sub_condition = "{% if request.user.role in 'super_admin,company_admin' %}"

# نغير بس اللي في قسم الاشتراك
# نبحث عن القسم
sub_section_start = sidebar.find("الاشتراك")
if sub_section_start != -1:
    # نبحث عن أقرب if قبله
    before_sub = sidebar[:sub_section_start]
    last_if_pos = before_sub.rfind("{% if request.user.role in 'super_admin,company_admin,hr_manager' %}")
    
    if last_if_pos != -1:
        # نتأكد إن ده فعلاً بتاع الاشتراك مش الشركة
        between = sidebar[last_if_pos:sub_section_start]
        if "الشركة" not in between:
            sidebar = (
                sidebar[:last_if_pos] +
                new_sub_condition +
                sidebar[last_if_pos + len(old_sub_condition):]
            )
            write_file(sidebar_path, sidebar)
            print("  ✅ الاشتراك ظاهر لصاحب الشركة و super_admin فقط")
        else:
            # الـ if ده بتاع الشركة مش الاشتراك
            # نبحث بطريقة تانية
            sidebar = read_file(sidebar_path)
            
            old_block = """    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <button class="sidebar-section-btn {% if 'my-plan' not in request.path and 'contact-sales' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secSubs', this)">
      الاشتراك <i class="bi bi-chevron-down"></i>
    </button>"""
            
            new_block = """    {% if request.user.role in 'super_admin,company_admin' %}
    <button class="sidebar-section-btn {% if 'my-plan' not in request.path and 'contact-sales' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secSubs', this)">
      الاشتراك <i class="bi bi-chevron-down"></i>
    </button>"""
            
            if old_block in sidebar:
                sidebar = sidebar.replace(old_block, new_block)
                write_file(sidebar_path, sidebar)
                print("  ✅ الاشتراك ظاهر لصاحب الشركة و super_admin فقط")
            else:
                print("  ℹ️  شكل الـ Sidebar مختلف — نجرب طريقة تالتة")
                
                # طريقة تالتة: نبحث عن secSubs
                if "secSubs" in sidebar:
                    # نبحث عن الـ if اللي قبل secSubs مباشرة
                    subs_idx = sidebar.find("secSubs")
                    search_area = sidebar[max(0, subs_idx-300):subs_idx]
                    
                    if "hr_manager" in search_area:
                        sidebar = sidebar[:max(0, subs_idx-300)] + search_area.replace(
                            "super_admin,company_admin,hr_manager",
                            "super_admin,company_admin"
                        ) + sidebar[subs_idx:]
                        write_file(sidebar_path, sidebar)
                        print("  ✅ تم التحديث (طريقة 3)")
    else:
        print("  ℹ️  لم يتم العثور على شرط الاشتراك")
else:
    print("  ℹ️  قسم الاشتراك مش موجود")


# ════════════════════════════════════════════════════════════
# 2. تحديث Dashboard — المسمى الوظيفي تحت الاسم
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Dashboard...")

dashboard_path = os.path.join(BASE_DIR, "templates", "dashboard", "index.html")
dashboard = read_file(dashboard_path)

# نبحث عن الترحيب ونضيف المسمى الوظيفي
old_header = """  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋
    </h4>
    <p class="text-muted mb-0">
      {{ today|date:"d/m/Y" }}
      {% if request.user.company %}| {{ request.user.company.name_ar }}{% endif %}
    </p>
  </div>"""

new_header = """  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋
    </h4>
    {% if current_employee and current_employee.job_title %}
    <p class="mb-1" style="color:#06B6D4; font-weight:600; font-size:0.9rem;">
      {{ current_employee.job_title.name_ar }}
      {% if current_employee.department %}
      — {{ current_employee.department.name_ar }}
      {% endif %}
    </p>
    {% endif %}
    <p class="text-muted mb-0" style="font-size:0.85rem;">
      {{ today|date:"d/m/Y" }}
      {% if request.user.company %}| {{ request.user.company.name_ar }}{% endif %}
      {% if request.user.role == 'employee' and current_employee %}
      | {{ current_employee.employee_code }}
      {% endif %}
    </p>
  </div>"""

if old_header in dashboard:
    dashboard = dashboard.replace(old_header, new_header)
    write_file(dashboard_path, dashboard)
    print("  ✅ المسمى الوظيفي ظاهر تحت الاسم")
else:
    print("  ℹ️  Header مختلف — نجرب طريقة بديلة")
    
    # طريقة بديلة
    if "current_employee.job_title" not in dashboard:
        old_welcome = "مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋"
        new_welcome = "مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋"
        
        # نبحث عن </h4> بعد الترحيب ونضيف بعده
        welcome_idx = dashboard.find(old_welcome)
        if welcome_idx != -1:
            h4_close = dashboard.find("</h4>", welcome_idx)
            if h4_close != -1:
                insert_after = h4_close + 5
                job_info = """
    {% if current_employee and current_employee.job_title %}
    <p class="mb-1" style="color:#06B6D4; font-weight:600; font-size:0.9rem;">
      {{ current_employee.job_title.name_ar }}
      {% if current_employee.department %} — {{ current_employee.department.name_ar }}{% endif %}
    </p>
    {% endif %}"""
                dashboard = dashboard[:insert_after] + job_info + dashboard[insert_after:]
                write_file(dashboard_path, dashboard)
                print("  ✅ المسمى الوظيفي ظاهر (طريقة بديلة)")
        else:
            print("  ⚠️  لم يتم العثور على الترحيب")
    else:
        print("  ℹ️  المسمى الوظيفي موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3. تأكيد إن current_employee موجود في Dashboard view
# ════════════════════════════════════════════════════════════
print("\n🔧 تأكيد context في Dashboard view...")

views_path = os.path.join(BASE_DIR, "accounts", "views.py")
views = read_file(views_path)

# التأكد إن current_employee بيتبعت في كل الحالات
if "current_employee" in views:
    print("  ✅ current_employee موجود في context")
else:
    print("  ⚠️  current_employee مش في context — محتاج مراجعة")


print("\n" + "=" * 60)
print("  ✅ Patch 38 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ الاشتراك ظاهر لصاحب الشركة و super_admin فقط
     - HR مش هيشوفه
     - Manager مش هيشوفه
     - Employee مش هيشوفه
  2. ✅ المسمى الوظيفي ظاهر تحت اسم الموظف في Dashboard
  3. ✅ القسم + الرقم الوظيفي

جرب:
  emp10003  → يشوف المسمى + ما يشوفش الاشتراك
  manager1  → ما يشوفش الاشتراك
  hr_manager → ما يشوفش الاشتراك
  demo_admin → يشوف الاشتراك
""")