"""
Patch 49j-Hooks Fix4 — Direct Fix
إصلاح مباشر للمشكلة في:
- templates/base/dashboard_base.html
- templates/dashboard/index.html
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
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")


print("=" * 60)
print("Patch 49j-Hooks Fix4 — Direct Fix")
print("=" * 60)

backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

# قائمة كل الاستبدالات المطلوبة
# أسماء قديمة -> أسماء صحيحة
REPLACEMENTS = {
    # الأسماء اللي بتيجي مع namespace employees:
    "employees:employee_list":   "employees:list",
    "employees:employee_add":    "employees:add",
    "employees:employee_detail": "employees:detail",
    "employees:employee_edit":   "employees:edit",
    "employees:employee_delete": "employees:delete",
    "employees:employee_print":  "employees:print_all",
    "employees:employee_print_detail": "employees:print_detail",
    "employees:employee_print_credentials": "employees:print_credentials",
    "employees:employee_comprehensive_profile": "employees:comprehensive_profile",
    "employees:employee_folder": "employees:folder",
    "employees:employee_folder_upload": "employees:folder_upload",
    "employees:employee_folder_delete": "employees:folder_delete",
    "employees:create_account_view": "employees:create_account",
    "employees:deactivate_account_view": "employees:deactivate_account",
    "employees:reset_password_view": "employees:reset_password",
    "employees:my_balance_view": "employees:my_balance",
    "employees:my_deductions_view": "employees:my_deductions",
    "employees:employee_search_api": "employees:search_api",
}

# الملفات التي سيتم تعديلها
TARGET_DIRS = [
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

total_changed = 0

for rel_dir in TARGET_DIRS:
    full_dir = os.path.join(BASE_DIR, rel_dir)
    if not os.path.isdir(full_dir):
        continue

    for root, _, files in os.walk(full_dir):
        for fname in files:
            if not fname.endswith((".py", ".html")):
                continue

            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            original = content
            changes = []

            for old, new in REPLACEMENTS.items():
                if old in content:
                    content = content.replace(old, new)
                    changes.append(f"{old} -> {new}")

            if changes:
                # Backup
                rel = os.path.relpath(fpath, BASE_DIR)
                backup_name = rel.replace("\\", "__").replace("/", "__") + ".fix4.bak"
                shutil.copy2(fpath, os.path.join(backup_dir, backup_name))

                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"\n✅ {rel}")
                for ch in changes:
                    print(f"   - {ch}")

                total_changed += 1

# كمان صلح الـ motionhr/urls.py
print("\n📌 التحقق من motionhr/urls.py")
urls_path = "motionhr/urls.py"
urls_content = read_file(urls_path)

if urls_content:
    # تأكد إن الـ alias block شغال صح
    if "name='employee_list'" in urls_content:
        print("   ℹ️ Legacy aliases موجودة في motionhr/urls.py")
    else:
        print("   ⚠️ Legacy aliases مش موجودة")

print(f"\n{'=' * 60}")
print(f"✅ Patch 49j-Hooks Fix4 اكتمل")
print(f"{'=' * 60}")
print(f"""
ملفات تم تعديلها: {total_changed}

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")