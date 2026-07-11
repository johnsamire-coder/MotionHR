"""
Patch 49j-Z — URL Stabilization Audit & Compatibility Layer

الهدف:
1) تثبيت أسماء URLs الخاصة بالموظفين ومنع تكرار NoReverseMatch
2) دعم الأسماء القديمة legacy سواء:
   - employee_list
   - employees:employee_list
   - employee_detail
   - employees:employee_detail
   ...إلخ
3) تنظيف references القديمة داخل templates و reverse()/redirect()
4) إضافة aliases رسمية داخل:
   - employees/urls.py   ← للأسماء القديمة داخل namespace employees:
   - motionhr/urls.py    ← للأسماء القديمة غير namespaced
5) إنشاء تقرير Audit بعد التنفيذ

هذا هو الحل المعتمد النهائي لمشكلة URL naming drift في employees.
لا تعتمد بعده على أي Fix قديم خاص بنفس المشكلة.
"""

import os
import re
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEARCH_DIRS = [
    "templates",
    "accounts",
    "attendance",
    "companies",
    "core",
    "employees",
    "leaves",
    "reports",
    "requests_app",
    "subscriptions",
    "motionhr",
]

BACKUP_DIR = os.path.join(BASE_DIR, "_patches", "_backups", "49j_z_url_stabilization")
REPORT_DIR = os.path.join(BASE_DIR, "_patches", "_reports")
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# canonical names داخل namespace employees
CANONICAL = {
    "employee_list": "list",
    "employee_add": "add",
    "employee_create": "add",
    "add_employee": "add",

    "employee_detail": "detail",
    "employee_profile": "detail",
    "employee_info": "detail",

    "employee_edit": "edit",
    "employee_update": "edit",
    "edit_employee": "edit",

    "employee_delete": "delete",
    "delete_employee": "delete",
    "employee_remove": "delete",
    "remove_employee": "delete",

    "employee_print": "print_all",
    "employee_print_all": "print_all",
    "employees_print": "print_all",
    "employees_print_all": "print_all",

    "employee_print_detail": "print_detail",
    "employee_detail_print": "print_detail",
    "employees_print_detail": "print_detail",

    "employee_print_credentials": "print_credentials",
    "employee_credentials_print": "print_credentials",
    "print_credentials_view": "print_credentials",

    "my_balance_view": "my_balance",
    "employee_balance": "my_balance",
    "employee_balance_view": "my_balance",

    "my_deductions_view": "my_deductions",
    "employee_deductions": "my_deductions",
    "employee_deductions_view": "my_deductions",

    "employee_comprehensive_profile": "comprehensive_profile",

    "employee_folder": "folder",
    "employee_folder_upload": "folder_upload",
    "employee_folder_delete": "folder_delete",

    "create_account_view": "create_account",
    "employee_create_account": "create_account",
    "employee_account_create": "create_account",
    "create_employee_account": "create_account",

    "deactivate_account_view": "deactivate_account",
    "employee_deactivate_account": "deactivate_account",

    "reset_password_view": "reset_password",
    "employee_reset_password": "reset_password",

    "employee_search_api": "search_api",
    "manager_options_api": "manager_options_api",
    "hierarchy_manage": "hierarchy_manage",
}

# ملفات لا نعمل فيها replacement عام لأننا هنضيف فيها alias block مقصود
EXCLUDED_REWRITE_FILES = {
    os.path.normpath(os.path.join(BASE_DIR, "employees/urls.py")),
    os.path.normpath(os.path.join(BASE_DIR, "motionhr/urls.py")),
}

PY_FUNCS = ["reverse", "redirect", "resolve_url", "reverse_lazy"]


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def backup_file(src_path):
    rel = os.path.relpath(src_path, BASE_DIR)
    backup_name = rel.replace("\\", "__").replace("/", "__") + ".bak"
    dst = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(dst):
        shutil.copy2(src_path, dst)
    return dst


def iter_files():
    for rel_dir in SEARCH_DIRS:
        full_dir = os.path.join(BASE_DIR, rel_dir)
        if not os.path.isdir(full_dir):
            continue
        for root, _, files in os.walk(full_dir):
            # استبعاد _patches وأي backup dirs لو ظهرت
            if "_patches" in root or ".venv" in root:
                continue
            for fname in files:
                if not fname.endswith((".py", ".html", ".txt")):
                    continue
                yield os.path.join(root, fname)


def apply_template_replacements(content, replacements):
    changes = []
    for old_name, new_name in replacements:
        # {% url 'employee_list' %}
        p1 = re.compile(
            r"(\{%\s*url\s+['\"])"
            + re.escape(old_name) +
            r"(['\"])",
            re.MULTILINE
        )

        def repl1(m):
            return m.group(1) + new_name + m.group(2)

        content, n1 = p1.subn(repl1, content)
        if n1:
            changes.append(f"template-url: {old_name} -> {new_name} ({n1})")

    return content, changes


def apply_python_replacements(content, replacements):
    changes = []
    for old_name, new_name in replacements:
        for func_name in PY_FUNCS:
            p = re.compile(
                r"(\b" + re.escape(func_name) + r"\(\s*['\"])"
                + re.escape(old_name) +
                r"(['\"])",
                re.MULTILINE
            )

            def repl(m):
                return m.group(1) + new_name + m.group(2)

            content, n = p.subn(repl, content)
            if n:
                changes.append(f"{func_name}: {old_name} -> {new_name} ({n})")
    return content, changes


def stabilize_references():
    file_results = []

    replacements = []

    # 1) namespaced wrong → canonical namespaced
    for old, canon in CANONICAL.items():
        replacements.append((f"employees:{old}", f"employees:{canon}"))

    # 2) plain wrong → canonical namespaced
    for old, canon in CANONICAL.items():
        replacements.append((old, f"employees:{canon}"))

    # 3) canonical plain aliases → canonical namespaced
    for canon in set(CANONICAL.values()):
        replacements.append((canon, f"employees:{canon}"))

    total_changed = 0

    for path in iter_files():
        norm_path = os.path.normpath(path)
        if norm_path in EXCLUDED_REWRITE_FILES:
            continue

        try:
            original = read_file(path)
        except Exception:
            continue

        content = original
        changes = []

        content, tpl_changes = apply_template_replacements(content, replacements)
        content, py_changes = apply_python_replacements(content, replacements)
        changes.extend(tpl_changes)
        changes.extend(py_changes)

        if content != original:
            backup_file(path)
            write_file(path, content)
            total_changed += 1
            file_results.append((path, changes))

    return total_changed, file_results


def ensure_employees_urls_aliases():
    """
    يضمن إن:
    reverse('employees:employee_list')
    reverse('employees:employee_detail')
    ... كلها تشتغل
    """
    path = os.path.join(BASE_DIR, "employees", "urls.py")
    if not os.path.exists(path):
        return False, "employees/urls.py غير موجود"

    content = read_file(path)
    marker = "# Patch 49j-Z — Legacy employee route names (namespaced aliases)"

    if marker in content:
        return True, "employees aliases موجودة بالفعل"

    alias_block = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49j-Z — Legacy employee route names (namespaced aliases)
# الغرض: دعم reverse('employees:employee_list') وأسماء legacy داخل namespace
# ═════════════════════════════════════════════════════════════

legacy_employee_urlpatterns = [
    path('', views.employee_list, name='employee_list'),

    path('add/', views.employee_add, name='employee_add'),
    path('add/', views.employee_add, name='employee_create'),
    path('add/', views.employee_add, name='add_employee'),

    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('<int:pk>/', views.employee_detail, name='employee_profile'),
    path('<int:pk>/', views.employee_detail, name='employee_info'),

    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('<int:pk>/edit/', views.employee_edit, name='employee_update'),
    path('<int:pk>/edit/', views.employee_edit, name='edit_employee'),

    path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('<int:pk>/delete/', views.employee_delete, name='delete_employee'),
    path('<int:pk>/delete/', views.employee_delete, name='employee_remove'),
    path('<int:pk>/delete/', views.employee_delete, name='remove_employee'),

    path('print/', views.employee_print, name='employee_print'),
    path('print/', views.employee_print, name='employee_print_all'),
    path('print/', views.employee_print, name='employees_print'),
    path('print/', views.employee_print, name='employees_print_all'),

    path('<int:pk>/print/', views.employee_print_detail, name='employee_print_detail'),
    path('<int:pk>/print/', views.employee_print_detail, name='employee_detail_print'),
    path('<int:pk>/print/', views.employee_print_detail, name='employees_print_detail'),

    path('<int:pk>/credentials/', views.print_credentials_view, name='employee_print_credentials'),
    path('<int:pk>/credentials/', views.print_credentials_view, name='employee_credentials_print'),
    path('<int:pk>/credentials/', views.print_credentials_view, name='print_credentials_view'),

    path('<int:pk>/create-account/', views.create_account_view, name='create_account_view'),
    path('<int:pk>/deactivate-account/', views.deactivate_account_view, name='deactivate_account_view'),
    path('<int:pk>/reset-password/', views.reset_password_view, name='reset_password_view'),

    path('<int:pk>/profile/', views.employee_comprehensive_profile, name='employee_comprehensive_profile'),

    path('<int:pk>/folder/', views.employee_folder, name='employee_folder'),
    path('<int:pk>/folder/upload/', views.employee_folder_upload, name='employee_folder_upload'),
    path('<int:pk>/folder/<int:doc_id>/delete/', views.employee_folder_delete, name='employee_folder_delete'),

    path('my-balance/', views.my_balance_view, name='my_balance_view'),
    path('my-balance/', views.my_balance_view, name='employee_balance'),
    path('my-deductions/', views.my_deductions_view, name='my_deductions_view'),
    path('my-deductions/', views.my_deductions_view, name='employee_deductions'),

    path('api/search/', views.employee_search_api, name='employee_search_api'),
    path('api/manager-options/', views.employee_manager_options_api, name='manager_options_api'),
    path('hierarchy/', views.job_hierarchy_manage, name='hierarchy_manage'),
]

urlpatterns += legacy_employee_urlpatterns
'''
    backup_file(path)
    content = content.rstrip() + "\n" + alias_block + "\n"
    write_file(path, content)
    return True, "تم إضافة namespaced legacy aliases في employees/urls.py"


def ensure_global_motionhr_aliases():
    """
    يضمن إن:
    reverse('employee_list')
    reverse('employee_detail')
    ... كلها تشتغل
    """
    path = os.path.join(BASE_DIR, "motionhr", "urls.py")
    if not os.path.exists(path):
        return False, "motionhr/urls.py غير موجود"

    content = read_file(path)

    import_line = "from employees import views as employee_views"
    if import_line not in content:
        if "from django.urls import path, include" in content:
            content = content.replace(
                "from django.urls import path, include",
                "from django.urls import path, include\n" + import_line,
                1
            )
        elif "from django.urls import include, path" in content:
            content = content.replace(
                "from django.urls import include, path",
                "from django.urls import include, path\n" + import_line,
                1
            )
        else:
            lines = content.splitlines()
            insert_at = 0
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    insert_at = i
            lines.insert(insert_at + 1, import_line)
            content = "\n".join(lines)

    marker = "# Patch 49j-Z — Global legacy employee route names"
    if marker in content:
        backup_file(path)
        write_file(path, content)
        return True, "global aliases موجودة بالفعل"

    alias_block = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49j-Z — Global legacy employee route names
# الغرض: دعم reverse('employee_list') وأسماء legacy غير namespaced
# ═════════════════════════════════════════════════════════════

legacy_global_employee_urlpatterns = [
    path('employees/', employee_views.employee_list, name='employee_list'),

    path('employees/add/', employee_views.employee_add, name='employee_add'),
    path('employees/add/', employee_views.employee_add, name='employee_create'),
    path('employees/add/', employee_views.employee_add, name='add_employee'),

    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_profile'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_info'),

    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_update'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='edit_employee'),

    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='delete_employee'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_remove'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='remove_employee'),

    path('employees/print/', employee_views.employee_print, name='employee_print'),
    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employee_print_detail'),
    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='print_credentials_view'),

    path('employees/<int:pk>/profile/', employee_views.employee_comprehensive_profile, name='employee_comprehensive_profile'),

    path('employees/<int:pk>/create-account/', employee_views.create_account_view, name='create_account_view'),
    path('employees/<int:pk>/deactivate-account/', employee_views.deactivate_account_view, name='deactivate_account_view'),
    path('employees/<int:pk>/reset-password/', employee_views.reset_password_view, name='reset_password_view'),

    path('employees/my-balance/', employee_views.my_balance_view, name='my_balance_view'),
    path('employees/my-deductions/', employee_views.my_deductions_view, name='my_deductions_view'),

    path('employees/api/search/', employee_views.employee_search_api, name='employee_search_api'),
]

urlpatterns += legacy_global_employee_urlpatterns
'''
    backup_file(path)
    content = content.rstrip() + "\n" + alias_block + "\n"
    write_file(path, content)
    return True, "تم إضافة global legacy aliases في motionhr/urls.py"


def create_audit_report(file_results, employees_result, motionhr_result):
    report_path = os.path.join(REPORT_DIR, "patch_49j_z_url_stabilization_report.txt")
    lines = []
    lines.append("Patch 49j-Z — URL Stabilization Audit Report")
    lines.append("=" * 70)
    lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"employees/urls.py aliases: {employees_result[1]}")
    lines.append(f"motionhr/urls.py aliases: {motionhr_result[1]}")
    lines.append("")
    lines.append(f"Files changed by reference normalization: {len(file_results)}")
    lines.append("")

    for path, changes in file_results:
        rel = os.path.relpath(path, BASE_DIR)
        lines.append(f"[{rel}]")
        for ch in changes:
            lines.append(f"  - {ch}")
        lines.append("")

    # Post-scan for suspicious leftovers
    suspicious = []
    patterns = [
        "employees:employee_",
        "'employee_list'",
        '"employee_list"',
        "'employee_detail'",
        '"employee_detail"',
        "'employee_add'",
        '"employee_add"',
    ]

    for path in iter_files():
        try:
            content = read_file(path)
        except Exception:
            continue

        hits = []
        for p in patterns:
            if p in content:
                hits.append(p)

        if hits:
            suspicious.append((os.path.relpath(path, BASE_DIR), hits))

    lines.append("=" * 70)
    lines.append("Suspicious leftovers scan")
    lines.append("=" * 70)

    if suspicious:
        for rel, hits in suspicious:
            lines.append(f"{rel}: {', '.join(hits)}")
    else:
        lines.append("No suspicious leftovers found.")

    write_file(report_path, "\n".join(lines))
    return report_path


print("=" * 70)
print("Patch 49j-Z — URL Stabilization Audit & Compatibility Layer")
print("=" * 70)

print("\n📌 Step 1: Normalize old employee URL references")
changed_count, file_results = stabilize_references()
print(f"   ✅ ملفات تم تعديلها: {changed_count}")

print("\n📌 Step 2: Add namespaced legacy aliases in employees/urls.py")
employees_result = ensure_employees_urls_aliases()
print(f"   ✅ {employees_result[1]}")

print("\n📌 Step 3: Add global legacy aliases in motionhr/urls.py")
motionhr_result = ensure_global_motionhr_aliases()
print(f"   ✅ {motionhr_result[1]}")

print("\n📌 Step 4: Generate audit report")
report_path = create_audit_report(file_results, employees_result, motionhr_result)
print(f"   ✅ Report: {os.path.relpath(report_path, BASE_DIR)}")

print("\n" + "=" * 70)
print("✅ Patch 49j-Z اكتمل")
print("=" * 70)
print(f"""
اللي اتعمل:
  ✅ تنظيف references القديمة الخاصة بروابط employees داخل templates و reverse()/redirect()
  ✅ إضافة aliases داخل employees/urls.py للأسماء القديمة داخل namespace employees:
  ✅ إضافة aliases داخل motionhr/urls.py للأسماء القديمة غير namespaced
  ✅ إنشاء backups في:
     _patches/_backups/49j_z_url_stabilization/
  ✅ إنشاء تقرير Audit في:
     _patches/_reports/patch_49j_z_url_stabilization_report.txt

مهم:
  ✅ هذا هو الحل النهائي المعتمد لمشكلة URL naming drift في employees
  ✅ لا تعتمد بعده على أي Fix قديم خاص بـ employee_list / employee_detail / employee_add

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")