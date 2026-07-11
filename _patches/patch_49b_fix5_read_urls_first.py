"""
Patch 49b Fix5 — نقرأ employees/urls.py الأول وبعدين نحل
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

urls_content = read_file("employees/urls.py")
views_content = read_file("employees/views.py")

# كل الأسماء المطلوبة من urls.py
used = sorted(set(re.findall(r'views\.([A-Za-z_][A-Za-z0-9_]*)', urls_content)))

# كل الأسماء الموجودة فعلاً في views.py
existing = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', views_content, re.MULTILINE))
existing |= set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', views_content, re.MULTILINE))

missing = [n for n in used if n not in existing]

print("كل الأسماء المطلوبة في urls.py:")
for n in used:
    status = "✅" if n in existing else "❌"
    print(f"  {status} {n}")

print(f"\nالناقص: {missing}")