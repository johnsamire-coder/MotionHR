"""
Patch 49j-Hooks Fix3 — Find & Fix dashboard employee_list reference
"""

import os
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
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")

print("=" * 60)
print("Fix3 — Find dashboard employee_list reference")
print("=" * 60)

# Step 1: ابحث في accounts/views.py
views_path = "accounts/views.py"
content = read_file(views_path)

if content is None:
    raise SystemExit("❌ accounts/views.py غير موجود")

print("\n📌 البحث عن 'employee_list' في accounts/views.py")
lines = content.splitlines()
found_lines = []
for i, line in enumerate(lines, 1):
    if "employee_list" in line:
        found_lines.append((i, line))
        print(f"   سطر {i}: {line.strip()}")

if not found_lines:
    print("   ℹ️ مش موجودة في accounts/views.py")
    
    # ابحث في كل المشروع
    print("\n📌 البحث الشامل في المشروع...")
    search_dirs = ["accounts", "motionhr", "core", "templates"]
    for d in search_dirs:
        full_dir = os.path.join(BASE_DIR, d)
        if not os.path.isdir(full_dir):
            continue
        for root, _, files in os.walk(full_dir):
            for fname in files:
                if not fname.endswith((".py", ".html")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    fcontent = open(fpath, encoding="utf-8").read()
                except Exception:
                    continue
                if "employee_list" in fcontent:
                    rel = os.path.relpath(fpath, BASE_DIR)
                    flines = fcontent.splitlines()
                    for i, line in enumerate(flines, 1):
                        if "employee_list" in line:
                            print(f"   [{rel}] سطر {i}: {line.strip()}")
else:
    # Fix مباشر في accounts/views.py
    print("\n📌 إصلاح مباشر في accounts/views.py")
    import shutil
    backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(
        os.path.join(BASE_DIR, views_path),
        os.path.join(backup_dir, "accounts_views_before_fix3.py.bak")
    )
    
    # استبدال كل أشكال الـ reverse القديمة
    replacements = {
        "reverse('employee_list')": "reverse('employees:list')",
        'reverse("employee_list")': 'reverse("employees:list")',
        "redirect('employee_list')": "redirect('employees:list')",
        'redirect("employee_list")': 'redirect("employees:list")',
        "url('employee_list')": "url('employees:list')",
        "'employee_list'": "'employees:list'",
        '"employee_list"': '"employees:list"',
    }
    
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            print(f"   ✅ استبدال: {old} -> {new}")
    
    write_file(views_path, content)

print("\n✅ Fix3 اكتمل")
print("شغّل: python manage.py check")