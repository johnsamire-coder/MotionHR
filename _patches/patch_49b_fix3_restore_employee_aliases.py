"""
Patch 49b Fix3 — Restore Legacy Employee View Aliases

الهدف:
- إصلاح AttributeError الناتج عن أسماء views القديمة في employees/urls.py
- إضافة compatibility aliases داخل employees/views.py
- عدم تعديل urls.py نفسها
- عدم كسر rebuild الأخير

يعالج أمثلة مثل:
- employee_print -> employee_print_list
- employee_print_detail -> employee_print_detail
- employee_print_credentials -> print_credentials
- employee_balance -> my_balance
- employee_deductions -> my_deductions
"""

import os
import re
import shutil

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
print("Patch 49b Fix3 — Restore Legacy Employee View Aliases")
print("=" * 60)

views_path = "employees/views.py"
urls_path = "employees/urls.py"

views_content = read_file(views_path)
urls_content = read_file(urls_path)

if views_content is None:
    raise SystemExit("❌ ملف employees/views.py غير موجود")
if urls_content is None:
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

# Backup
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

views_backup = os.path.join(backup_dir, "employees_views_before_patch_49b_fix3.py.bak")
urls_backup = os.path.join(backup_dir, "employees_urls_before_patch_49b_fix3.py.bak")

shutil.copy2(os.path.join(BASE_DIR, views_path), views_backup)
shutil.copy2(os.path.join(BASE_DIR, urls_path), urls_backup)

print("✅ Backup created:")
print("   _patches/_backups/employees_views_before_patch_49b_fix3.py.bak")
print("   _patches/_backups/employees_urls_before_patch_49b_fix3.py.bak")

# استخراج كل أسماء views المستخدمة في urls.py
used_view_names = set(re.findall(r'views\.([A-Za-z_][A-Za-z0-9_]*)', urls_content))
print(f"\n📌 Views referenced in urls.py: {sorted(used_view_names)}")

# استخراج الأسماء الموجودة فعليًا في views.py
defined_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', views_content, re.MULTILINE))
defined_aliases = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', views_content, re.MULTILINE))
existing_names = defined_funcs | defined_aliases

print(f"📌 Existing names in views.py: {len(existing_names)} name(s) detected")

# خريطة aliases معتمدة
alias_map = {
    # list / add / edit / delete / detail
    "employee_create": "employee_add",
    "create_employee": "employee_add",
    "add_employee": "employee_add",
    "add": "employee_add",

    "employee_update": "employee_edit",
    "update_employee": "employee_edit",
    "edit_employee": "employee_edit",
    "edit": "employee_edit",

    "employee_remove": "employee_delete",
    "delete_employee": "employee_delete",
    "remove_employee": "employee_delete",
    "delete": "employee_delete",

    "detail": "employee_detail",
    "employee_profile": "employee_detail",
    "employee_info": "employee_detail",

    # print aliases
    "employee_print": "employee_print_list",
    "employee_print_all": "employee_print_list",
    "print_all": "employee_print_list",
    "employees_print": "employee_print_list",
    "employees_print_all": "employee_print_list",
    "print_list": "employee_print_list",
    "print_list_view": "employee_print_list",

    "employee_detail_print": "employee_print_detail",
    "employee_profile_print": "employee_print_detail",
    "print_detail": "employee_print_detail",
    "print_detail_view": "employee_print_detail",
    "employees_print_detail": "employee_print_detail",

    "employee_print_credentials": "print_credentials",
    "employee_credentials_print": "print_credentials",
    "credentials_print": "print_credentials",
    "print_credentials_view": "print_credentials",
    "employee_credentials": "print_credentials",

    # self-service
    "employee_balance": "my_balance",
    "employee_balance_view": "my_balance",
    "my_balance_view": "my_balance",

    "employee_deductions": "my_deductions",
    "employee_deductions_view": "my_deductions",
    "my_deductions_view": "my_deductions",

    # search
    "employee_search": "employee_search_api",
    "search_api": "employee_search_api",
}

# نضيف فقط اللي urls.py محتاجاه ومش موجود
missing = sorted(name for name in used_view_names if name not in existing_names)
print(f"📌 Missing referenced names: {missing}")

alias_lines = []
unresolved = []

for missing_name in missing:
    target = alias_map.get(missing_name)
    if target:
        # لازم الهدف نفسه يكون موجود أو حتى alias معروف بالفعل
        if target in existing_names or re.search(rf'^def\s+{re.escape(target)}\s*\(', views_content, re.MULTILINE):
            alias_lines.append(f"{missing_name} = {target}")
            existing_names.add(missing_name)
        else:
            unresolved.append((missing_name, target))
    else:
        unresolved.append((missing_name, None))

if alias_lines:
    marker = "# ═════════════════════════════════════════════════════════════\n# Compatibility Aliases"
    if marker in views_content:
        # نضيف قبل آخر aliases block end أو في آخر الملف
        views_content = views_content.rstrip() + "\n\n# Legacy URL compatibility aliases restored by Patch 49b Fix3\n"
        for line in alias_lines:
            if re.search(rf'^{re.escape(line.split("=")[0].strip())}\s*=', views_content, re.MULTILINE):
                continue
            views_content += line + "\n"
    else:
        views_content = views_content.rstrip() + "\n\n# Legacy URL compatibility aliases restored by Patch 49b Fix3\n"
        for line in alias_lines:
            views_content += line + "\n"

    write_file(views_path, views_content)
    print("\n✅ Added aliases:")
    for line in alias_lines:
        print("   ", line)
else:
    print("\nℹ️ لا توجد aliases جديدة مطلوبة")

if unresolved:
    print("\n⚠️ Unresolved names:")
    for missing_name, target in unresolved:
        if target:
            print(f"   - {missing_name} -> target '{target}' غير موجود")
        else:
            print(f"   - {missing_name} -> لا يوجد mapping معروف")
else:
    print("\n✅ كل الأسماء المطلوبة تم حلها")

print("\n" + "=" * 60)
print("✅ Patch 49b Fix3 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ قراءة employees/urls.py واستخراج أسماء views المستخدمة
  ✅ مقارنة الأسماء مع الموجود فعليًا في employees/views.py
  ✅ إضافة aliases ناقصة تلقائيًا بدون تعديل urls.py
  ✅ عمل Backup قبل التعديل

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")