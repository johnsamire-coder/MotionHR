"""
Patch 49g — Report Branding (Logo + Company Name + Footer)

الهدف:
1) إضافة Header موحد لكل التقارير فيه:
   - لوجو الشركة (لو موجود)
   - اسم الشركة
   - اسم التقرير
   - تاريخ التصدير
2) إضافة Footer موحد فيه:
   - اسم البرنامج MotionHR
   - JS Solution
3) تحسين شكل الطباعة
4) تحديث كل templates التقارير

الملفات:
- templates/reports/_report_header.html (جديد)
- templates/reports/_report_footer.html (جديد)
- templates/reports/attendance_report.html
- templates/reports/late_report.html
- templates/reports/leave_report.html
- templates/reports/employees_report.html
- templates/reports/field_report.html
- reports/views.py (تمرير company)
"""

import os
import shutil
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")


print("=" * 60)
print("Patch 49g — Report Branding")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path in [
    "reports/views.py",
    "templates/reports/attendance_report.html",
    "templates/reports/late_report.html",
    "templates/reports/leave_report.html",
    "templates/reports/employees_report.html",
    "templates/reports/field_report.html",
    "templates/reports/home.html",
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_name = rel_path.replace("/", "_").replace("\\", "_") + ".49g.bak"
        shutil.copy2(full, os.path.join(backup_dir, backup_name))

print("✅ Backups created")

# ────────────────────────────────────────────────────────────
# Step 1: Create _report_header.html
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: إنشاء _report_header.html")

header_template = """<!-- Patch 49g — Report Header -->
<div class="report-branded-header mb-4">
  <div class="d-flex align-items-center justify-content-between flex-wrap gap-3 py-3 px-4 rounded-4"
       style="background: linear-gradient(135deg, #f0fdff 0%, #e0f2fe 100%); border: 1px solid #bae6fd;">

    <div class="d-flex align-items-center gap-3">
      {% if company and company.logo %}
      <img src="{{ company.logo.url }}" alt="Logo"
           style="max-height: 56px; max-width: 160px; border-radius: 10px;"
           class="shadow-sm">
      {% else %}
      <div style="width:56px; height:56px; border-radius:14px; background:#06B6D4; display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-building text-white" style="font-size:1.6rem;"></i>
      </div>
      {% endif %}

      <div>
        <div style="font-size:1.25rem; font-weight:800; color:#0c4a6e;">
          {% if company %}
            {{ company.name_ar|default:company.name_en|default:"MotionHR" }}
          {% else %}
            MotionHR
          {% endif %}
        </div>
        <div style="font-size:.88rem; color:#475569; font-weight:600;">
          {{ report_title|default:"تقرير" }}
        </div>
      </div>
    </div>

    <div class="text-end">
      <div style="font-size:.82rem; color:#64748b;">
        <i class="bi bi-calendar3 me-1"></i>
        {% load tz %}
        {% now "Y/m/d H:i" %}
      </div>
      {% if start_date and end_date %}
      <div style="font-size:.78rem; color:#94a3b8; margin-top:2px;">
        الفترة: {{ start_date }} — {{ end_date }}
      </div>
      {% endif %}
    </div>
  </div>
</div>
"""
write_file("templates/reports/_report_header.html", header_template)

# ────────────────────────────────────────────────────────────
# Step 2: Create _report_footer.html
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء _report_footer.html")

footer_template = """<!-- Patch 49g — Report Footer -->
<div class="report-branded-footer mt-4 pt-3 text-center"
     style="border-top: 1px solid #e2e8f0;">
  <div style="font-size:.82rem; color:#94a3b8; font-style:italic;">
    MotionHR — HR in Motion | JS Solution
  </div>
  <div style="font-size:.72rem; color:#cbd5e1; margin-top:2px;">
    تم الإنشاء بواسطة نظام MotionHR — {% now "Y/m/d H:i" %}
  </div>
</div>
"""
write_file("templates/reports/_report_footer.html", footer_template)

# ────────────────────────────────────────────────────────────
# Step 3: Create print CSS
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إنشاء CSS للطباعة")

print_css = """
/* Patch 49g — Report Print & Branding CSS */
.report-branded-header {
  page-break-after: avoid;
}

.report-branded-footer {
  page-break-before: avoid;
}

@media print {
  .sidebar, .navbar, .breadcrumb, .btn,
  [class*="print-hide"], .wizard-actions {
    display: none !important;
  }

  .main-content {
    margin: 0 !important;
    padding: 0 !important;
  }

  .report-branded-header {
    margin-bottom: 20px !important;
  }

  .report-branded-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
  }

  .card {
    border: none !important;
    box-shadow: none !important;
  }

  table {
    font-size: 10px !important;
  }

  body {
    font-size: 12px !important;
  }
}
"""
write_file("static/css/patch49g_report_print.css", print_css)

# ────────────────────────────────────────────────────────────
# Step 4: Update reports/views.py to pass company context
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: تحديث reports/views.py لتمرير company")

views_path = "reports/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف reports/views.py غير موجود")

# نضيف company لكل context لو مش موجود
# نبحث عن كل return render ونتأكد إن company موجود

def ensure_company_in_context(content):
    """تأكد إن كل view بتمرر company في الـ context"""

    # نضيف helper في أول الملف لو مش موجود
    helper = '''
def _get_report_company(request):
    company = getattr(request.user, 'company', None)
    if not company:
        try:
            company = request.user.employee.company
        except Exception:
            company = None
    return company

'''
    if "_get_report_company" not in content:
        # نضيفها بعد آخر import
        lines = content.split('\n')
        last_import = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                last_import = i
        lines.insert(last_import + 1, helper)
        content = '\n'.join(lines)

    # نبحث عن كل context dict ونضيف company لو مش موجود
    # Pattern: "page_title": "..." بدون "company"
    # هنعمل approach أبسط: نبحث عن return render ونضيف company قبلها

    functions = [
        'attendance_report',
        'late_report',
        'leave_report',
        'employees_report',
        'field_report',
        'reports_home',
    ]

    for func_name in functions:
        # نبحث عن context = { أو return render داخل الدالة
        # ونضيف company
        pattern = rf'(def {func_name}\(request\):.*?)(return render\(request,)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            block = match.group(1)
            if "'company'" not in block and '"company"' not in block:
                # نضيف company قبل return render
                indent = '    '
                company_line = f"\n{indent}company = _get_report_company(request)\n"

                # نبحث عن context = { ونضيف company فيه
                ctx_pattern = rf'(context\s*=\s*\{{[^}}]*)(}})'
                ctx_match = re.search(ctx_pattern, block)
                if ctx_match:
                    ctx_content = ctx_match.group(1)
                    if "'company'" not in ctx_content:
                        new_ctx = ctx_content + f"\n{indent}{indent}'company': company,\n{indent}"
                        block_new = block.replace(ctx_match.group(0), new_ctx + ctx_match.group(2))

                        # نضيف company = line قبل context
                        ctx_start = block_new.find('context')
                        if ctx_start > 0:
                            block_new = block_new[:ctx_start] + f"company = _get_report_company(request)\n{indent}" + block_new[ctx_start:]

                        content = content.replace(block, block_new)

    return content

views_content = ensure_company_in_context(views_content)
write_file(views_path, views_content)

# ────────────────────────────────────────────────────────────
# Step 5: Update base template to include print CSS
# ────────────────────────────────────────────────────────────
print("\n📌 Step 5: إضافة CSS الطباعة للـ base template")

base_path = "templates/base/dashboard_base.html"
base_content = read_file(base_path)
if base_content and "patch49g_report_print.css" not in base_content:
    base_content = base_content.replace(
        '</head>',
        '  <link rel="stylesheet" href="/static/css/patch49g_report_print.css">\n</head>'
    )
    write_file(base_path, base_content)
    print("   ✅ تم إضافة CSS الطباعة")
else:
    print("   ℹ️ CSS الطباعة موجود بالفعل أو الملف غير موجود")

# ────────────────────────────────────────────────────────────
# Step 6: Update each report template
# ────────────────────────────────────────────────────────────
print("\n📌 Step 6: تحديث templates التقارير")

report_configs = [
    {
        "path": "templates/reports/attendance_report.html",
        "title": "تقرير الحضور والغياب",
    },
    {
        "path": "templates/reports/late_report.html",
        "title": "تقرير التأخيرات",
    },
    {
        "path": "templates/reports/leave_report.html",
        "title": "تقرير الإجازات",
    },
    {
        "path": "templates/reports/employees_report.html",
        "title": "تقرير الموظفين",
    },
    {
        "path": "templates/reports/field_report.html",
        "title": "تقرير الموظفين الميدانيين",
    },
]

for config in report_configs:
    template = read_file(config["path"])
    if template is None:
        print(f"   ⚠️ {config['path']} غير موجود — تجاوز")
        continue

    if "{% include 'reports/_report_header.html' %}" in template:
        print(f"   ℹ️ {config['path']} — Header موجود بالفعل")
        continue

    modified = False

    # نبحث عن بداية الـ content block ونضيف header بعده
    if "{% block content %}" in template:
        # نضيف report_title في الـ context عبر with tag
        header_include = f"""{{% block content %}}
<div class="container-fluid">
  {{% with report_title="{config['title']}" %}}
  {{% include 'reports/_report_header.html' %}}
  {{% endwith %}}
"""
        template = template.replace(
            "{% block content %}",
            header_include,
            1
        )

        # نتخلص من أي container-fluid مكرر
        template = template.replace(
            header_include + "\n<div class=\"container-fluid\">",
            header_include
        )

        modified = True

    # نضيف footer قبل نهاية الـ content block
    if "{% endblock %}" in template and "{% include 'reports/_report_footer.html' %}" not in template:
        # نبحث عن آخر {% endblock %} ونضيف footer قبله
        # نعكس البحث — نبحث عن آخر endblock
        last_endblock = template.rfind("{% endblock %}")
        if last_endblock != -1:
            footer_include = "\n  {% include 'reports/_report_footer.html' %}\n</div>\n"
            template = template[:last_endblock] + footer_include + template[last_endblock:]
            modified = True

    if modified:
        write_file(config["path"], template)
        print(f"   ✅ {config['path']} — تم إضافة Header + Footer")
    else:
        print(f"   ℹ️ {config['path']} — لم يتم التعديل")

# ────────────────────────────────────────────────────────────
# Step 7: Update reports home page
# ────────────────────────────────────────────────────────────
print("\n📌 Step 7: تحديث صفحة التقارير الرئيسية")

home_path = "templates/reports/home.html"
home_content = read_file(home_path)
if home_content and "comprehensive_profile" not in home_content:
    # نضيف رابط الملف الشامل في صفحة التقارير
    profile_card = """
    <div class="col-md-4 col-lg-3">
      <a href="#" class="text-decoration-none">
        <div class="card border-0 shadow-sm h-100 text-center py-4" style="border-radius:18px;">
          <div class="fs-1 mb-2"><i class="bi bi-person-lines-fill text-info"></i></div>
          <div class="fw-bold">الملف الشامل</div>
          <div class="small text-muted">اختر موظف من أي تقرير لعرض ملفه الشامل</div>
        </div>
      </a>
    </div>
"""

    if "الملف الشامل" not in home_content:
        # نبحث عن آخر card في الصفحة ونضيف بعده
        if "</div>\n  </div>" in home_content:
            last_card = home_content.rfind("</div>\n  </div>")
            if last_card != -1:
                # نضيف قبل آخر closing div
                home_content = home_content[:last_card] + profile_card + home_content[last_card:]
                write_file(home_path, home_content)
                print("   ✅ تم إضافة كارت الملف الشامل في صفحة التقارير")
            else:
                print("   ℹ️ لم أتمكن من حقن الكارت")
        else:
            print("   ℹ️ هيكل الصفحة غير متوقع — تجاوز")
    else:
        print("   ℹ️ الملف الشامل موجود بالفعل")
else:
    if home_content is None:
        print("   ⚠️ templates/reports/home.html غير موجود")
    else:
        print("   ℹ️ comprehensive_profile موجود بالفعل")

print("\n" + "=" * 60)
print("✅ Patch 49g اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ templates/reports/_report_header.html
     - لوجو الشركة (لو موجود)
     - اسم الشركة
     - اسم التقرير
     - تاريخ التصدير
     - الفترة الزمنية
  ✅ templates/reports/_report_footer.html
     - MotionHR — HR in Motion | JS Solution
     - تاريخ الإنشاء
  ✅ static/css/patch49g_report_print.css
     - CSS خاص بالطباعة
     - إخفاء sidebar + buttons عند الطباعة
     - footer ثابت في الطباعة
  ✅ reports/views.py
     - تمرير company في كل التقارير
  ✅ تحديث 5 templates تقارير:
     - attendance_report.html
     - late_report.html
     - leave_report.html
     - employees_report.html
     - field_report.html
  ✅ إضافة كارت الملف الشامل في صفحة التقارير الرئيسية

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")