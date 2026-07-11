#!/usr/bin/env python3
"""
Patch 23b: URL Aliases Compatibility
====================================
يضيف أسماء URL بديلة للتوافق مع التمبلتس القديمة
- attendance aliases
- employees aliases
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def extract_paths(content):
    """
    يرجع dict:
    {
        'name': {'route': "'check-in/'", 'view': 'views.check_in_page'}
    }
    """
    pattern = re.compile(
        r"""path\(
\s*(?P<route>[^,]+?)\s*,\s*
(?P<view>[^,]+?)\s*,\s*
name\s*=\s*['"](?P<name>[^'"]+)['"]\s*
\)""",
        re.VERBOSE | re.MULTILINE,
    )
    result = {}
    for m in pattern.finditer(content):
        result[m.group("name")] = {
            "route": m.group("route").strip(),
            "view": m.group("view").strip(),
        }
    return result


def add_aliases(urls_path, aliases_map, label):
    print(f"\n🔧 تحديث {label}...")

    content = read_file(urls_path)
    parsed = extract_paths(content)

    added_lines = []

    for old_name, alias_names in aliases_map.items():
        if old_name not in parsed:
            print(f"  ⚠️  الاسم الأساسي غير موجود: {old_name}")
            continue

        route = parsed[old_name]["route"]
        view = parsed[old_name]["view"]

        for alias in alias_names:
            if alias in parsed or f"name='{alias}'" in content or f'name="{alias}"' in content:
                print(f"  ℹ️  alias موجود بالفعل: {alias}")
                continue

            line = f"    path({route}, {view}, name='{alias}'),"
            added_lines.append(line)
            print(f"  ✅ هيتم إضافة alias: {old_name} → {alias}")

    if not added_lines:
        print("  ℹ️  لا يوجد aliases جديدة")
        return

    marker = "]"
    idx = content.rfind(marker)
    if idx == -1:
        print("  ❌ لم أجد نهاية urlpatterns")
        return

    aliases_block = "\n\n    # ── Compatibility Aliases ─────────────────────\n"
    aliases_block += "\n".join(added_lines) + "\n"

    new_content = content[:idx] + aliases_block + content[idx:]
    write_file(urls_path, new_content)


print("=" * 60)
print("  Patch 23b: URL Aliases Compatibility")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) Attendance aliases
# ════════════════════════════════════════════════════════════
attendance_aliases = {
    "list": ["attendance_list"],
    "check_in": ["check_in_page"],
    "visits": ["visits_list"],
    "tracking": ["tracking_page"],
    "tracking_detail": ["employee_tracking_detail"],
    "monitor": ["field_employees_monitor"],
    "api_track": ["api_track_location"],
    "api_monitor": ["api_monitor_data"],
}

add_aliases(
    os.path.join(BASE_DIR, "attendance", "urls.py"),
    attendance_aliases,
    "attendance/urls.py"
)

# ════════════════════════════════════════════════════════════
# 2) Employees aliases
# ════════════════════════════════════════════════════════════
employees_aliases = {
    "list": ["employee_list"],
    "add": ["employee_add"],
    "detail": ["employee_detail"],
    "edit": ["employee_edit"],
    "delete": ["employee_delete"],
    "print": ["employee_print"],
    "print_detail": ["employee_print_detail"],
}

add_aliases(
    os.path.join(BASE_DIR, "employees", "urls.py"),
    employees_aliases,
    "employees/urls.py"
)

print("\n" + "=" * 60)
print("  ✅ Patch 23b اكتمل!")
print("=" * 60)
print("""
الخطوة الجاية:
1) شغّل:
   python manage.py check

2) ثم:
   python manage.py runserver 0.0.0.0:8000

3) افتح:
   http://127.0.0.1:8000/dashboard/
""")