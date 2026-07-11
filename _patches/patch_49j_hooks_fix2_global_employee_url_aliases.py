"""
Patch 49j-Hooks Fix2 — Global Legacy Employee URL Aliases

الهدف:
- إصلاح NoReverseMatch للأسماء القديمة مثل:
  employee_list / employee_detail / employee_add ...
- إضافة aliases عالمية في motionhr/urls.py
- بدون تكسير الـ namespaced URLs الحالية
- هذا الباتش هو الحل الفعلي لمشكلة reverse القديمة الخاصة بالموظفين

مهم:
- لا تشغّل Fix1 القديمة ولا Fix1b لحل نفس المشكلة
- الاعتماد من الآن على Global URL Aliases
"""

import os
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
print("Patch 49j-Hooks Fix2 — Global Legacy Employee URL Aliases")
print("=" * 60)

urls_path = "motionhr/urls.py"
urls_content = read_file(urls_path)

if urls_content is None:
    raise SystemExit("❌ ملف motionhr/urls.py غير موجود")

# Backup
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)
backup_file = os.path.join(backup_dir, "motionhr_urls_before_patch_49j_hooks_fix2.py.bak")
shutil.copy2(os.path.join(BASE_DIR, urls_path), backup_file)
print("✅ Backup created: _patches/_backups/motionhr_urls_before_patch_49j_hooks_fix2.py.bak")

# 1) Ensure import
import_line = "from employees import views as employee_views"
if import_line not in urls_content:
    # نحاول نضيف بعد imports
    if "from django.urls import path, include" in urls_content:
        urls_content = urls_content.replace(
            "from django.urls import path, include",
            "from django.urls import path, include\n" + import_line,
            1
        )
        print("✅ تم إضافة import employee_views")
    elif "from django.urls import include, path" in urls_content:
        urls_content = urls_content.replace(
            "from django.urls import include, path",
            "from django.urls import include, path\n" + import_line,
            1
        )
        print("✅ تم إضافة import employee_views")
    else:
        # fallback
        lines = urls_content.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                insert_at = i
        lines.insert(insert_at + 1, import_line)
        urls_content = "\n".join(lines)
        print("✅ تم إضافة import employee_views (fallback)")

# 2) Append alias block if missing
marker = "# Patch 49j-Hooks Fix2 — Global Legacy Employee URL Aliases"
if marker not in urls_content:
    alias_block = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49j-Hooks Fix2 — Global Legacy Employee URL Aliases
# الغرض: دعم reverse بالأسماء القديمة غير الـ namespaced
# ═════════════════════════════════════════════════════════════

legacy_employee_urlpatterns = [
    # القائمة
    path('employees/', employee_views.employee_list, name='employee_list'),

    # إضافة
    path('employees/add/', employee_views.employee_add, name='employee_add'),
    path('employees/add/', employee_views.employee_add, name='employee_create'),
    path('employees/add/', employee_views.employee_add, name='add_employee'),

    # التفاصيل
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_profile'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_info'),

    # تعديل
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_update'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='edit_employee'),

    # حذف
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='delete_employee'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_remove'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='remove_employee'),

    # طباعة
    path('employees/print/', employee_views.employee_print, name='employee_print'),
    path('employees/print/', employee_views.employee_print, name='employee_print_all'),
    path('employees/print/', employee_views.employee_print, name='employees_print'),
    path('employees/print/', employee_views.employee_print, name='employees_print_all'),

    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employee_print_detail'),
    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employee_detail_print'),
    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employees_print_detail'),

    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='employee_print_credentials'),
    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='employee_credentials_print'),
    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='print_credentials_view'),

    # حسابات
    path('employees/<int:pk>/create-account/', employee_views.create_account_view, name='create_account_view'),
    path('employees/<int:pk>/deactivate-account/', employee_views.deactivate_account_view, name='deactivate_account_view'),
    path('employees/<int:pk>/reset-password/', employee_views.reset_password_view, name='reset_password_view'),

    # الملف الشامل
    path('employees/<int:pk>/profile/', employee_views.employee_comprehensive_profile, name='employee_comprehensive_profile'),

    # المستندات
    path('employees/<int:pk>/folder/', employee_views.employee_folder, name='employee_folder'),
    path('employees/<int:pk>/folder/upload/', employee_views.employee_folder_upload, name='employee_folder_upload'),
    path('employees/<int:pk>/folder/<int:doc_id>/delete/', employee_views.employee_folder_delete, name='employee_folder_delete'),

    # Self-service
    path('employees/my-balance/', employee_views.my_balance_view, name='my_balance_view'),
    path('employees/my-balance/', employee_views.my_balance_view, name='employee_balance'),
    path('employees/my-deductions/', employee_views.my_deductions_view, name='my_deductions_view'),
    path('employees/my-deductions/', employee_views.my_deductions_view, name='employee_deductions'),

    # APIs / hierarchy
    path('employees/api/search/', employee_views.employee_search_api, name='employee_search_api'),
    path('employees/api/manager-options/', employee_views.employee_manager_options_api, name='manager_options_api'),
    path('employees/hierarchy/', employee_views.job_hierarchy_manage, name='hierarchy_manage'),
]

urlpatterns += legacy_employee_urlpatterns
'''
    urls_content = urls_content.rstrip() + "\n" + alias_block + "\n"
    write_file(urls_path, urls_content)
    print("✅ تم إضافة legacy_employee_urlpatterns")
else:
    print("ℹ️ alias block موجود بالفعل")

print("\n" + "=" * 60)
print("✅ Patch 49j-Hooks Fix2 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ إضافة aliases عالمية للأسماء القديمة الخاصة بالموظفين داخل motionhr/urls.py
  ✅ الأسماء القديمة مثل employee_list أصبحت تعمل مرة أخرى
  ✅ تم الإبقاء على namespaced URLs الحالية كما هي
  ✅ هذا هو الحل المعتمد لمشكلة reverse القديمة الخاصة بالموظفين

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")