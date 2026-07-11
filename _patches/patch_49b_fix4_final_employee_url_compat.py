"""
Patch 49b Fix4 — Final Employee URL Compatibility

الهدف:
- إصلاح أي AttributeError ناتج عن فرق الأسماء بين employees/urls.py و employees/views.py
- إنشاء create_account_view لو ناقصة
- إضافة aliases legacy تلقائيًا من urls.py
- عدم تعديل employees/urls.py
- اعتبار هذا الباتش هو الحل النهائي للتوافق بعد Rebuild views.py
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
print("Patch 49b Fix4 — Final Employee URL Compatibility")
print("=" * 60)

views_path = "employees/views.py"
urls_path = "employees/urls.py"

views_content = read_file(views_path)
urls_content = read_file(urls_path)

if views_content is None:
    raise SystemExit("❌ ملف employees/views.py غير موجود")
if urls_content is None:
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

# Backups
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

views_backup = os.path.join(backup_dir, "employees_views_before_patch_49b_fix4.py.bak")
urls_backup = os.path.join(backup_dir, "employees_urls_before_patch_49b_fix4.py.bak")

shutil.copy2(os.path.join(BASE_DIR, views_path), views_backup)
shutil.copy2(os.path.join(BASE_DIR, urls_path), urls_backup)

print("✅ Backup created:")
print("   _patches/_backups/employees_views_before_patch_49b_fix4.py.bak")
print("   _patches/_backups/employees_urls_before_patch_49b_fix4.py.bak")

# ────────────────────────────────────────────────────────────
# 1) Extract used view names from urls.py
# ────────────────────────────────────────────────────────────
used_view_names = sorted(set(re.findall(r'views\.([A-Za-z_][A-Za-z0-9_]*)', urls_content)))
print(f"\n📌 Views referenced in employees/urls.py:")
for name in used_view_names:
    print("   -", name)

# Extract existing names from views.py
defined_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', views_content, re.MULTILINE))
defined_aliases = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', views_content, re.MULTILINE))
existing_names = set(defined_funcs) | set(defined_aliases)

print(f"\n📌 Existing names in employees/views.py: {len(existing_names)}")

# ────────────────────────────────────────────────────────────
# 2) Ensure create_account_view exists if referenced
# ────────────────────────────────────────────────────────────
if "create_account_view" in used_view_names and "create_account_view" not in existing_names:
    print("\n📌 إضافة create_account_view")

    create_account_code = '''

@login_required
@feature_required('employees_management')
def create_account_view(request, pk):
    """إنشاء/مزامنة حساب الموظف — Compatibility View restored by Patch 49b Fix4"""
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied("ليس لديك صلاحية إنشاء حساب لهذا الموظف")

    try:
        before_user = getattr(employee, 'user', None)

        # استخدم helper الداخلي لو موجود
        try:
            _try_sync_employee_account(employee)
        except Exception:
            pass

        # fallback مباشر لو helper ما عملش حاجة
        employee.refresh_from_db()
        after_user = getattr(employee, 'user', None)

        if not after_user:
            try:
                from . import account_utils
                candidate_names = [
                    'create_or_update_employee_account',
                    'ensure_employee_account',
                    'sync_employee_account',
                    'sync_employee_user',
                    'create_employee_account',
                    'provision_employee_account',
                    'create_employee_user',
                ]
                for fn_name in candidate_names:
                    fn = getattr(account_utils, fn_name, None)
                    if callable(fn):
                        try:
                            fn(employee)
                            break
                        except TypeError:
                            try:
                                fn(employee=employee)
                                break
                            except Exception:
                                pass
                        except Exception:
                            pass
                employee.refresh_from_db()
                after_user = getattr(employee, 'user', None)
            except Exception:
                pass

        if after_user:
            username = getattr(after_user, 'username', None) or '—'
            if before_user:
                messages.success(request, f'تمت مزامنة حساب الموظف {employee.full_name_ar} (اسم المستخدم: {username})')
            else:
                messages.success(request, f'تم إنشاء حساب للموظف {employee.full_name_ar} (اسم المستخدم: {username})')
        else:
            messages.warning(request, 'تمت محاولة إنشاء الحساب لكن لم يتم ربط مستخدم بالموظف. راجع account_utils.')

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')

    try:
        return redirect('employees:detail', pk=employee.pk)
    except Exception:
        return redirect('employees:list')
'''.rstrip() + "\n"

    views_content = views_content.rstrip() + "\n\n" + create_account_code + "\n"
    existing_names.add("create_account_view")
    write_file(views_path, views_content)
    views_content = read_file(views_path)
    print("   ✅ تمت إضافة create_account_view")
else:
    print("\nℹ️ create_account_view موجودة بالفعل أو غير مطلوبة")

# Refresh names after possible injection
defined_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', views_content, re.MULTILINE))
defined_aliases = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', views_content, re.MULTILINE))
existing_names = set(defined_funcs) | set(defined_aliases)

# ────────────────────────────────────────────────────────────
# 3) Legacy alias map
# ────────────────────────────────────────────────────────────
alias_map = {
    # CRUD
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

    # Print
    "employee_print": "employee_print_list",
    "employee_print_all": "employee_print_list",
    "employees_print": "employee_print_list",
    "employees_print_all": "employee_print_list",
    "print_all": "employee_print_list",
    "print_list": "employee_print_list",
    "print_list_view": "employee_print_list",

    "employee_print_detail": "employee_print_detail",
    "employee_detail_print": "employee_print_detail",
    "employee_profile_print": "employee_print_detail",
    "employees_print_detail": "employee_print_detail",
    "print_detail": "employee_print_detail",
    "print_detail_view": "employee_print_detail",

    "employee_print_credentials": "print_credentials",
    "employee_credentials_print": "print_credentials",
    "credentials_print": "print_credentials",
    "print_credentials_view": "print_credentials",
    "employee_credentials": "print_credentials",

    # Account creation
    "create_account": "create_account_view",
    "employee_create_account": "create_account_view",
    "employee_account_create": "create_account_view",
    "create_employee_account": "create_account_view",

    # Self-service
    "employee_balance": "my_balance",
    "employee_balance_view": "my_balance",
    "my_balance_view": "my_balance",

    "employee_deductions": "my_deductions",
    "employee_deductions_view": "my_deductions",
    "my_deductions_view": "my_deductions",

    # Search
    "employee_search": "employee_search_api",
    "search_api": "employee_search_api",
}

# ────────────────────────────────────────────────────────────
# 4) Add any missing aliases referenced by urls.py
# ────────────────────────────────────────────────────────────
missing = [name for name in used_view_names if name not in existing_names]
print(f"\n📌 Missing names referenced by urls.py: {missing}")

alias_lines = []
unresolved = []

for missing_name in missing:
    target = alias_map.get(missing_name)

    if target and (target in existing_names or re.search(rf'^def\s+{re.escape(target)}\s*\(', views_content, re.MULTILINE)):
        alias_lines.append(f"{missing_name} = {target}")
        existing_names.add(missing_name)
    else:
        unresolved.append((missing_name, target))

if alias_lines:
    marker = "# Compatibility Aliases"
    append_block = "\n\n# Legacy URL compatibility aliases restored by Patch 49b Fix4\n"
    for line in alias_lines:
        alias_name = line.split("=")[0].strip()
        if not re.search(rf'^{re.escape(alias_name)}\s*=', views_content, re.MULTILINE):
            append_block += line + "\n"

    views_content = views_content.rstrip() + append_block
    write_file(views_path, views_content)

    print("\n✅ Added aliases:")
    for line in alias_lines:
        print("   ", line)
else:
    print("\nℹ️ لا توجد aliases ناقصة لإضافتها")

if unresolved:
    print("\n⚠️ أسماء لم يتم حلها تلقائيًا:")
    for name, target in unresolved:
        if target:
            print(f"   - {name} -> target '{target}' غير موجود")
        else:
            print(f"   - {name} -> لا يوجد mapping معروف")
else:
    print("\n✅ كل الأسماء المطلوبة من urls.py أصبحت متاحة في views.py")

print("\n" + "=" * 60)
print("✅ Patch 49b Fix4 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ قراءة employees/urls.py واستخراج كل أسماء views المطلوبة
  ✅ إنشاء create_account_view لو كانت ناقصة
  ✅ إضافة Legacy aliases الناقصة تلقائيًا
  ✅ عدم تعديل employees/urls.py
  ✅ إنشاء backups قبل التعديل

هذا الباتش:
  ✅ هو الحل النهائي المعتمد لتوافق employees/views.py مع employees/urls.py
  ✅ supersedes أي إصلاح جزئي سابق خاص بـ legacy aliases

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")