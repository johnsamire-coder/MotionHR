"""
Patch 49b Fix6 — Add Missing Account Views

الهدف:
- إضافة view حقيقية لـ deactivate_account_view
- إضافة view حقيقية لـ reset_password_view
- إغلاق آخر Missing Views المطلوبة من employees/urls.py
- عمل backup قبل التعديل

يعتمد على:
- employees/views.py الحالي
- وجود Employee.user
- وجود can_user_edit_employee / is_admin_or_hr
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
print("Patch 49b Fix6 — Add Missing Account Views")
print("=" * 60)

views_path = "employees/views.py"
urls_path = "employees/urls.py"

views_content = read_file(views_path)
urls_content = read_file(urls_path)

if views_content is None:
    raise SystemExit("❌ ملف employees/views.py غير موجود")
if urls_content is None:
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

# ────────────────────────────────────────────────────────────
# Backup
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

views_backup = os.path.join(backup_dir, "employees_views_before_patch_49b_fix6.py.bak")
urls_backup = os.path.join(backup_dir, "employees_urls_before_patch_49b_fix6.py.bak")

shutil.copy2(os.path.join(BASE_DIR, views_path), views_backup)
shutil.copy2(os.path.join(BASE_DIR, urls_path), urls_backup)

print("✅ Backup created:")
print("   _patches/_backups/employees_views_before_patch_49b_fix6.py.bak")
print("   _patches/_backups/employees_urls_before_patch_49b_fix6.py.bak")

# ────────────────────────────────────────────────────────────
# Optional import: get_random_string
# ────────────────────────────────────────────────────────────
if "from django.utils.crypto import get_random_string" not in views_content:
    lines = views_content.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("from ") or s.startswith("import "):
            insert_at = i
    lines.insert(insert_at + 1, "from django.utils.crypto import get_random_string")
    views_content = "\n".join(lines)
    print("✅ تم إضافة import get_random_string")

# ────────────────────────────────────────────────────────────
# Add deactivate_account_view
# ────────────────────────────────────────────────────────────
deactivate_view_code = '''

@login_required
@feature_required('employees_management')
def deactivate_account_view(request, pk):
    """تعطيل/إعادة تفعيل حساب الموظف — Compatibility View restored by Patch 49b Fix6"""
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied("ليس لديك صلاحية إدارة حساب هذا الموظف")

    user = getattr(employee, 'user', None)

    if not user:
        messages.warning(request, 'هذا الموظف لا يملك حساب مستخدم مرتبطًا به.')
        try:
            return redirect('employees:detail', pk=employee.pk)
        except Exception:
            return redirect('employees:list')

    action = request.POST.get('action', '').strip().lower() if request.method == 'POST' else ''

    try:
        # لو POST وجاي action=activate نفعّل
        if request.method == 'POST' and action == 'activate':
            user.is_active = True
            if hasattr(user, 'must_change_password'):
                try:
                    user.must_change_password = True
                except Exception:
                    pass
            user.save()
            messages.success(request, f'تمت إعادة تفعيل حساب الموظف {employee.full_name_ar}')
        else:
            # الافتراضي: تعطيل
            user.is_active = False
            user.save()
            messages.success(request, f'تم تعطيل حساب الموظف {employee.full_name_ar}')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تحديث حالة الحساب: {e}')

    try:
        return redirect('employees:detail', pk=employee.pk)
    except Exception:
        return redirect('employees:list')
'''.strip() + "\n"

if "def deactivate_account_view(request, pk):" not in views_content:
    views_content = views_content.rstrip() + "\n\n" + deactivate_view_code + "\n"
    print("✅ تمت إضافة deactivate_account_view")
else:
    print("ℹ️ deactivate_account_view موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Add reset_password_view
# ────────────────────────────────────────────────────────────
reset_view_code = '''

@login_required
@feature_required('employees_management')
def reset_password_view(request, pk):
    """إعادة تعيين كلمة مرور حساب الموظف — Compatibility View restored by Patch 49b Fix6"""
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied("ليس لديك صلاحية إعادة تعيين كلمة مرور هذا الموظف")

    user = getattr(employee, 'user', None)

    if not user:
        messages.warning(request, 'هذا الموظف لا يملك حساب مستخدم مرتبطًا به. أنشئ الحساب أولاً.')
        try:
            return redirect('employees:detail', pk=employee.pk)
        except Exception:
            return redirect('employees:list')

    try:
        # كلمة مرور مؤقتة واضحة لكن معقولة
        base_code = (employee.employee_code or 'EMP').replace(' ', '')
        temp_password = f"{base_code}@{get_random_string(4)}"

        user.set_password(temp_password)

        if hasattr(user, 'must_change_password'):
            try:
                user.must_change_password = True
            except Exception:
                pass

        if hasattr(user, 'is_active') and not user.is_active:
            user.is_active = True

        user.save()

        messages.success(
            request,
            f'تم إعادة تعيين كلمة المرور للموظف {employee.full_name_ar} | '
            f'اسم المستخدم: {user.username} | كلمة المرور المؤقتة: {temp_password}'
        )

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إعادة تعيين كلمة المرور: {e}')

    try:
        return redirect('employees:detail', pk=employee.pk)
    except Exception:
        return redirect('employees:list')
'''.strip() + "\n"

if "def reset_password_view(request, pk):" not in views_content:
    views_content = views_content.rstrip() + "\n\n" + reset_view_code + "\n"
    print("✅ تمت إضافة reset_password_view")
else:
    print("ℹ️ reset_password_view موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Safety aliases if urls ever use alternate names later
# ────────────────────────────────────────────────────────────
alias_block = """

# Missing account compatibility aliases restored by Patch 49b Fix6
employee_deactivate_account = deactivate_account_view
employee_reset_password = reset_password_view
"""

if "employee_deactivate_account = deactivate_account_view" not in views_content:
    views_content = views_content.rstrip() + "\n" + alias_block + "\n"
    print("✅ تمت إضافة account aliases")

write_file(views_path, views_content)

# ────────────────────────────────────────────────────────────
# Final validation by reading urls referenced names
# ────────────────────────────────────────────────────────────
final_views_content = read_file(views_path)
used_view_names = sorted(set(re.findall(r'views\.([A-Za-z_][A-Za-z0-9_]*)', urls_content)))
defined_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', final_views_content, re.MULTILINE))
defined_aliases = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', final_views_content, re.MULTILINE))
existing_names = defined_funcs | defined_aliases
missing = [n for n in used_view_names if n not in existing_names]

print("\n📌 Final check against employees/urls.py")
for n in used_view_names:
    print(f"   {'✅' if n in existing_names else '❌'} {n}")

if missing:
    print(f"\n⚠️ ما زال ناقص: {missing}")
else:
    print("\n✅ كل الأسماء المطلوبة في employees/urls.py موجودة الآن في employees/views.py")

print("\n" + "=" * 60)
print("✅ Patch 49b Fix6 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ إضافة deactivate_account_view
  ✅ إضافة reset_password_view
  ✅ إضافة import get_random_string
  ✅ إضافة aliases إضافية للأمان
  ✅ التحقق النهائي من كل الأسماء المستخدمة في employees/urls.py

هذا الباتش:
  ✅ هو الإغلاق النهائي الحالي لنواقص Employee Account Views
  ✅ يمنع تكرار الأخطاء من نوع AttributeError الخاصة بـ employees/urls.py

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")