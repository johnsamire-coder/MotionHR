#!/usr/bin/env python3
"""
Patch 49c: Fix Django template extends/load order
=================================================
- يخلي {% extends %} أول tag في الملف
- يحط كل {% load ... %} بعده مباشرة
- يطبق على كل templates اللي فيها المشكلة
"""

import os
import glob
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 49c: Fix Template Order")
print("=" * 60)

template_files = glob.glob(
    os.path.join(BASE_DIR, "templates", "**", "*.html"),
    recursive=True
)

fixed_count = 0
checked_count = 0

for path in template_files:
    checked_count += 1
    content = read_file(path)

    if "{% extends" not in content:
        continue

    lines = content.splitlines()

    # لاقي أول extends
    extends_idx = None
    extends_line = None
    for i, line in enumerate(lines):
        if "{% extends" in line:
            extends_idx = i
            extends_line = line
            break

    if extends_idx is None:
        continue

    # اجمع كل load lines
    load_lines = []
    new_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if i == extends_idx:
            continue

        if stripped.startswith("{% load ") and stripped.endswith("%}"):
            if line not in load_lines:
                load_lines.append(line)
            continue

        new_lines.append(line)

    # شيل whitespace الفارغ من أول الملف
    while new_lines and new_lines[0].strip() == "":
        new_lines.pop(0)

    # ابني الملف من جديد
    rebuilt = [extends_line]
    rebuilt.extend(load_lines)
    rebuilt.append("")  # سطر فاصل
    rebuilt.extend(new_lines)

    new_content = "\n".join(rebuilt).rstrip() + "\n"

    # لو extends ماكانش أول tag أو كان فيه load قبله → عدّل
    first_non_empty = None
    for line in lines:
        if line.strip():
            first_non_empty = line.strip()
            break

    has_problem = (
        first_non_empty != extends_line.strip()
        or any(
            line.strip().startswith("{% load ")
            for line in lines[:extends_idx]
        )
    )

    if has_problem and new_content != content:
        write_file(path, new_content)
        fixed_count += 1

print("\n" + "=" * 60)
print("  Patch 49c اكتمل!")
print("=" * 60)
print(f"تم فحص: {checked_count} ملف")
print(f"تم إصلاح: {fixed_count} ملف")
print("")
print("اللي اتقفل:")
print("  ✅ مشكلة {% extends %} must be the first tag")
print("  ✅ attendance/visits/add المفروض تشتغل")
print("  ✅ أي template مشابه اتصلح تلقائيًا")
print("")
print("شغّل بعده:")
print("  python manage.py check")
print("  python manage.py runserver 0.0.0.0:8000")
