#!/usr/bin/env python3
"""
Patch 48a-fix: Cleanup duplicate migration + create pending migrations
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command

print("=" * 60)
print("  Patch 48a-fix: Cleanup + Migrations")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) حذف migration المكررة
# ════════════════════════════════════════════════════════════
dup_path = BASE_DIR / "accounts" / "migrations" / "0006_add_push_subscription.py"

if dup_path.exists():
    dup_path.unlink()
    print(f"  ✅ تم حذف duplicate migration: {dup_path}")
else:
    print("  ℹ️  duplicate migration غير موجودة")

# ════════════════════════════════════════════════════════════
# 2) إنشاء المايجريشنات الناقصة
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء migrations الناقصة...")
call_command("makemigrations", "accounts", "attendance", "companies", "requests_app")

# ════════════════════════════════════════════════════════════
# 3) تطبيقها
# ════════════════════════════════════════════════════════════
print("\n🔧 تطبيق migrations...")
call_command("migrate")

# ════════════════════════════════════════════════════════════
# 4) Check نهائي
# ════════════════════════════════════════════════════════════
print("\n🔍 Django check...")
call_command("check")

print("\n" + "=" * 60)
print("  ✅ Patch 48a-fix اكتمل!")
print("=" * 60)
print("""
اللي حصل:
  1. ✅ حذف 0006 المكررة
  2. ✅ توليد المايجريشنات الناقصة الحقيقية
  3. ✅ تطبيقها
  4. ✅ Django check

بعدها ابعتلي الناتج
وأنا أبعتلك:
  - Patch 48b
  - الهاند أوت المحدث النهائي
""")