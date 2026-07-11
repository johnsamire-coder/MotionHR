#!/usr/bin/env python3
"""
Patch 38c: Fix Manager/HR Employee Link + current_employee resolution
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from accounts.models import User
from employees.models import Employee


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 38c: Fix Manager/HR Employee Link")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) تأكيد الربط بين اليوزر والموظف
# ════════════════════════════════════════════════════════════
print("\n🔧 تأكيد ربط اليوزرات بالموظفين...")

links = [
    ("manager1", "EMP10001"),
    ("hr_manager", "EMP10002"),
]

for username, emp_code in links:
    user = User.objects.filter(username=username).first()
    emp = Employee.all_objects.filter(employee_code=emp_code).first()

    if not user:
        print(f"  ⚠️  اليوزر غير موجود: {username}")
        continue

    if not emp:
        print(f"  ⚠️  الموظف غير موجود: {emp_code}")
        continue

    if emp.user_id != user.id:
        emp.user = user
        emp.save(update_fields=["user"])
        print(f"  ✅ تم ربط {username} بـ {emp_code}")
    else:
        print(f"  ℹ️  {username} مربوط بالفعل بـ {emp_code}")

# ════════════════════════════════════════════════════════════
# 2) تحديث CurrentEmployeeMiddleware
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث core/middleware.py...")

middleware_path = os.path.join(BASE_DIR, "core", "middleware.py")
middleware = read_file(middleware_path)

old_line = """                from employees.models import Employee
                request.current_employee = Employee.objects.filter(
                    user=request.user
                ).first()"""

new_line = """                from employees.models import Employee
                request.current_employee = Employee.all_objects.filter(
                    user=request.user
                ).select_related("job_title", "department", "branch").first()"""

if old_line in middleware:
    middleware = middleware.replace(old_line, new_line)
    write_file(middleware_path, middleware)
    print("  ✅ تم تحديث CurrentEmployeeMiddleware")
else:
    print("  ℹ️  النص مختلف أو تم تحديثه قبل كده")

# ════════════════════════════════════════════════════════════
# 3) تحديث dashboard view fallback
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/views.py...")

views_path = os.path.join(BASE_DIR, "accounts", "views.py")
views = read_file(views_path)

old_fallback = """    current_employee = getattr(request, "current_employee", None)
    if not current_employee and Employee:
        current_employee = Employee.all_objects.filter(user=request.user).first()"""

new_fallback = """    current_employee = getattr(request, "current_employee", None)
    if not current_employee and Employee:
        current_employee = Employee.all_objects.filter(
            user=request.user
        ).select_related("job_title", "department", "branch").first()"""

if old_fallback in views:
    views = views.replace(old_fallback, new_fallback)
    write_file(views_path, views)
    print("  ✅ تم تحديث fallback في dashboard")
else:
    print("  ℹ️  fallback مختلف أو تم تحديثه قبل كده")

# ════════════════════════════════════════════════════════════
# 4) طباعة تأكيد نهائي
# ════════════════════════════════════════════════════════════
print("\n🔍 التحقق النهائي...")

for username in ["manager1", "hr_manager"]:
    user = User.objects.filter(username=username).first()
    emp = Employee.all_objects.filter(user=user).select_related("job_title", "department").first()
    if emp:
        print(f"  ✅ {username} -> {emp.employee_code} | {emp.full_name_ar} | {getattr(emp.job_title, 'name_ar', 'بدون مسمى')}")
    else:
        print(f"  ❌ {username} غير مربوط بموظف")

print("\n" + "=" * 60)
print("  ✅ Patch 38c اكتمل!")
print("=" * 60)
print("""
جرب الآن:
- manager1
- hr_manager

على /dashboard/
المفروض يظهر تحت الاسم:
- المسمى الوظيفي
- القسم
- الرقم الوظيفي
""")