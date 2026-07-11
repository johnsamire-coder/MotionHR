"""
Patch 49j-Hooks Fix1b — Normalize Legacy Employee URL Names (Safe)

الهدف:
- إصلاح NoReverseMatch بسبب أسماء URLs قديمة مثل:
  employee_list / employee_add / employee_detail ...
- تحويلها إلى الأسماء الحالية المعتمدة:
  employees:list / employees:add / employees:detail ...
- البحث والاستبدال في:
  * templates/*.html
  * *.py
- إنشاء backups قبل أي تعديل

مهم:
- هذه النسخة تصلح bug الـ regex الموجود في Fix1
- لا تشغّل Fix1 القديمة بعد هذا الباتش
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

# فقط الأسماء الواضحة الخاصة بالموظفين
URL_MAP = {
    "employee_list": "employees:list",

    "employee_add": "employees:add",
    "employee_create": "employees:add",
    "add_employee": "employees:add",

    "employee_detail": "employees:detail",
    "employee_profile": "employees:detail",
    "employee_info": "employees:detail",

    "employee_edit": "employees:edit",
    "employee_update": "employees:edit",
    "edit_employee": "employees:edit",

    "employee_delete": "employees:delete",
    "delete_employee": "employees:delete",
    "employee_remove": "employees:delete",
    "remove_employee": "employees:delete",

    "employee_print": "employees:print_all",
    "employee_print_all": "employees:print_all",
    "employees_print": "employees:print_all",
    "employees_print_all": "employees:print_all",

    "employee_print_detail": "employees:print_detail",
    "employee_detail_print": "employees:print_detail",
    "employees_print_detail": "employees:print_detail",

    "employee_print_credentials": "employees:print_credentials",
    "employee_credentials_print": "employees:print_credentials",
    "print_credentials_view": "employees:print_credentials",

    "my_balance_view": "employees:my_balance",
    "employee_balance": "employees:my_balance",
    "employee_balance_view": "employees:my_balance",

    "my_deductions_view": "employees:my_deductions",
    "employee_deductions": "employees:my_deductions",
    "employee_deductions_view": "employees:my_deductions",

    "employee_comprehensive_profile": "employees:comprehensive_profile",

    "employee_folder": "employees:folder",
    "employee_folder_upload": "employees:folder_upload",
    "employee_folder_delete": "employees:folder_delete",

    "create_account_view": "employees:create_account",
    "employee_create_account": "employees:create_account",
    "employee_account_create": "employees:create_account",
    "create_employee_account": "employees:create_account",

    "deactivate_account_view": "employees:deactivate_account",
    "employee_deactivate_account": "employees:deactivate_account",

    "reset_password_view": "employees:reset_password",
    "employee_reset_password": "employees:reset_password",

    "employee_search_api": "employees:search_api",
    "manager_options_api": "employees:manager_options_api",
    "hierarchy_manage": "employees:hierarchy_manage",
}


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


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


def ensure_backup(src_path):
    rel = os.path.relpath(src_path, BASE_DIR)
    backup_dir = os.path.join(BASE_DIR, "_patches", "_backups", "49j_hooks_fix1b")
    os.makedirs(backup_dir, exist_ok=True)
    backup_name = rel.replace("\\", "__").replace("/", "__") + ".bak"
    dst = os.path.join(backup_dir, backup_name)
    if not os.path.exists(dst):
        shutil.copy2(src_path, dst)
    return dst


def replace_in_content(content):
    original = content
    changes = []

    # 1) Template url tags
    for old, new in URL_MAP.items():
        pattern = re.compile(
            r"(\{%\s*url\s+['\"])"
            + re.escape(old) +
            r"(['\"])",
            re.MULTILINE
        )

        def _tpl_repl(match):
            return match.group(1) + new + match.group(2)

        content, n = pattern.subn(_tpl_repl, content)
        if n:
            changes.append(f"template-url: {old} -> {new} ({n})")

    # 2) Python reverse/redirect/resolve_url/reverse_lazy
    py_funcs = ["reverse", "redirect", "resolve_url", "reverse_lazy"]
    for old, new in URL_MAP.items():
        for func_name in py_funcs:
            pattern = re.compile(
                r"(\b" + re.escape(func_name) + r"\(\s*['\"])"
                + re.escape(old) +
                r"(['\"])",
                re.MULTILINE
            )

            def _py_repl(match):
                return match.group(1) + new + match.group(2)

            content, n = pattern.subn(_py_repl, content)
            if n:
                changes.append(f"{func_name}: {old} -> {new} ({n})")

    return content, changes, original != content


print("=" * 60)
print("Patch 49j-Hooks Fix1b — Normalize Legacy Employee URL Names (Safe)")
print("=" * 60)

total_files_changed = 0
total_replacement_groups = 0

for full_path in iter_project_files():
    try:
        content = read_file(full_path)
    except Exception:
        continue

    new_content, changes, changed = replace_in_content(content)
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
    total_replacement_groups += len(changes)

print("\n" + "=" * 60)
print("✅ Patch 49j-Hooks Fix1b اكتمل")
print("=" * 60)
print(f"""
النتيجة:
  ✅ ملفات تم تعديلها: {total_files_changed}
  ✅ مجموع مجموعات الاستبدال: {total_replacement_groups}

Backups:
  _patches/_backups/49j_hooks_fix1b/

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")