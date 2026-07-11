#!/usr/bin/env python3
"""
Patch 38b: Show Job Title for Any User Linked to Employee
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
print("  Patch 38b: Dashboard Job Title")
print("=" * 60)

dashboard_path = os.path.join(BASE_DIR, "templates", "dashboard", "index.html")
content = read_file(dashboard_path)

# نعيد كتابة الجزء العلوي بشكل واضح
old_block_start = content.find("<!-- Header -->")
old_block_end = content.find("{% if dashboard_mode == 'employee' %}")

if old_block_start != -1 and old_block_end != -1:
    new_header = """<!-- Header -->
  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      مرحباً، {{ request.user.get_full_name|default:request.user.username }} 👋
    </h4>

    {% if current_employee and current_employee.job_title %}
    <p class="mb-1" style="color:#06B6D4; font-weight:600; font-size:0.92rem;">
      {{ current_employee.job_title.name_ar }}
      {% if current_employee.department %}
        — {{ current_employee.department.name_ar }}
      {% endif %}
    </p>
    {% endif %}

    <p class="text-muted mb-0" style="font-size:0.85rem;">
      {{ today|date:"d/m/Y" }}
      {% if request.user.company %}| {{ request.user.company.name_ar }}{% endif %}
      {% if current_employee %}| {{ current_employee.employee_code }}{% endif %}
    </p>
  </div>

"""
    content = content[:old_block_start] + new_header + content[old_block_end:]
    write_file(dashboard_path, content)
    print("  ✅ تم تثبيت Header الـ Dashboard")
else:
    print("  ⚠️  لم أتمكن من تحديد Header بشكل تلقائي")

print("\n" + "=" * 60)
print("  ✅ Patch 38b اكتمل!")
print("=" * 60)
print("""
جرب الآن:
- manager1
- hr_manager
- demo_admin (لو مربوط بموظف مش هيظهر، وده طبيعي)
- أي user مربوط بموظف لازم يظهر له المسمى الوظيفي
""")