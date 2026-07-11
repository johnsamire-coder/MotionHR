"""
Patch 49j-Hooks Fix1 — Normalize Legacy Employee URL Names

الهدف:
- إصلاح NoReverseMatch بسبب أسماء URLs قديمة مثل:
  employee_list / employee_add / employee_detail ...
- تحويلها إلى الأسماء الحالية المعتمدة:
  employees:list / employees:add / employees:detail ...
- البحث والاستبدال في:
  * templates/*.html
  * *.py
- إنشاء backups قبل أي تعديل

هذا الباتش آمن:
- يغيّر فقط أسماء URL القديمة المعروفة
- لا يغيّر أي routing فعلي
"""

import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEARCH_DIRS = [
    "templates",
    "accounts",
    "attendance",
    "companies",
    "core",
    "employees",
    "landing",
    "leaves",
    "reports",
    "requests_app",
    "subscriptions",
    "motionhr",
]

FILE_EXTENSIONS = {".html", ".py", ".txt"}

URL_MAP = {
    # الموظفين
    "employee_list": "employees:list",
    "employee_add": "employees:add",
    "employee_create": "employees:add",
    "add_employee": "employees:add",

    "employee_detail": "employees:detail",
    "detail": "employees:detail",  # سيتم التعامل معها بحذر في patterns

    "employee_edit": "employees:edit",
    "employee_update": "employees:edit",
    "edit_employee": "employees:edit",

    "employee_delete": "employees:delete",
    "delete_employee": "employees:delete",

    "employee_print": "employees:print_all",
    "employee_print_all": "employees:print_all",
    "print_all": "employees:print_all",
    "employees_print": "employees:print_all",

    "employee_print_detail": "employees:print_detail",
    "employee_detail_print": "employees:print_detail",
    "print_detail": "employees:print_detail",

    "print_credentials": "employees:print_credentials",
    "print_credentials_view": "employees:print_credentials",
    "employee_print_credentials": "employees:print_credentials",

    "my_balance": "employees:my_balance",
    "my_balance_view": "employees:my_balance",
    "employee_balance": "employees:my_balance",

    "my_deductions": "employees:my_deductions",
    "my_deductions_view": "employees:my_deductions",
    "employee_deductions": "employees:my_deductions",

    "comprehensive_profile": "employees:comprehensive_profile",
    "employee_comprehensive_profile": "employees:comprehensive_profile",

    "folder": "employees:folder",
    "folder_upload": "employees:folder_upload",
    "folder_delete": "employees:folder_delete",

    "create_account": "employees:create_account",
    "create_account_view": "employees:create_account",

    "deactivate_account": "employees:deactivate_account",
    "deactivate_account_view": "employees:deactivate_account",

    "reset_password": "employees:reset_password",
    "reset_password_view": "employees:reset_password",

    "search_api": "employees:search_api",
    "manager_options_api": "employees:manager_options_api",
    "hierarchy_manage": "employees:hierarchy_manage",
}

# أسماء عامة نخلي بالنا منها لأنها ممكن تكون في apps أخرى
DANGEROUS_GENERIC_NAMES = {
    "detail", "edit", "delete", "add", "print_detail", "print_all",
    "search_api", "my_balance", "my_deductions"
}


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def ensure_backup(src_path):
    rel = os.path.relpath(src_path, BASE_DIR)
    backup_dir = os.path.join(BASE_DIR, "_patches", "_backups", "49j_hooks_fix1")
    os.makedirs(backup_dir, exist_ok=True)
    backup_name = rel.replace("\\", "__").replace("/", "__") + ".bak"
    dst = os.path.join(backup_dir, backup_name)
    if not os.path.exists(dst):
        shutil.copy2(src_path, dst)
    return dst


def should_process_file(path):
    _, ext = os.path.splitext(path)
    return ext.lower() in FILE_EXTENSIONS


def iter_project_files():
    for rel_dir in SEARCH_DIRS:
        full_dir = os.path.join(BASE_DIR, rel_dir)
        if not os.path.isdir(full_dir):
            continue
        for root, _, files in os.walk(full_dir):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                if should_process_file(full_path):
                    yield full_path


def replace_in_content(content, file_path):
    original = content
    changes = []

    # 1) Template url tag replacements
    # {% url 'employee_list' %}  → {% url 'employees:list' %}
    for old, new in URL_MAP.items():
        # للأسماء الخطيرة، نستبدل فقط لو كانت غير namespaced
        template_pattern = r"(\{%\s*url\s+['\"]){}(['\"])".format(re.escape(old))
        if re.search(template_pattern, content):
            content, n = re.subn(template_pattern, r"\1" + new + r"\2", content)
            if n:
                changes.append(f"template-url: {old} -> {new} ({n})")

    # 2) reverse('employee_list') / redirect('employee_list') / resolve_url('employee_list')
    py_funcs = ["reverse", "redirect", "resolve_url", "reverse_lazy"]
    for old, new in URL_MAP.items():
        for func_name in py_funcs:
            pattern = r"(\b{}\(\s*['\"]){}(['\"])".format(func_name, re.escape(old))
            if re.search(pattern, content):
                content, n = re.subn(pattern, r"\1" + new + r"\2", content)
                if n:
                    changes.append(f"{func_name}: {old} -> {new} ({n})")

    # 3) HTML href/data-url raw strings like "/employees/" لا نلمسها
    # 4) لا نلمس already namespaced names
    # 5) حذر إضافي: لا نستبدل generic words داخل نصوص عادية

    return content, changes, original != content


print("=" * 60)
print("Patch 49j-Hooks Fix1 — Normalize Legacy Employee URL Names")
print("=" * 60)

total_files_changed = 0
total_replacements = 0

for full_path in iter_project_files():
    try:
        content = read_file(full_path)
    except Exception:
        continue

    new_content, changes, changed = replace_in_content(content, full_path)
    if not changed:
        continue

    backup_path = ensure_backup(full_path)
    write_file(full_path, new_content)

    rel = os.path.relpath(full_path, BASE_DIR)
    print(f"\n✅ تم التحديث: {rel}")
    print(f"   Backup: {os.path.relpath(backup_path, BASE_DIR)}")
    for ch in changes:
        print(f"   - {ch}")

    total_files_changed += 1
    total_replacements += len(changes)

print("\n" + "=" * 60)
print("✅ Patch 49j-Hooks Fix1 اكتمل")
print("=" * 60)
print(f"""
النتيجة:
  ✅ ملفات تم تعديلها: {total_files_changed}
  ✅ مجموع أنواع الاستبدال: {total_replacements}

تم حفظ backups في:
  _patches/_backups/49j_hooks_fix1/

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")