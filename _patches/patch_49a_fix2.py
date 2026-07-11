"""
Patch 49a Fix2 — إصلاح الأخطاء الناتجة عن 49a
1. dashboard namespace → core:dashboard أو الـ URL الصح
2. Attendance check_in field name
3. Company.name → company.name_ar أو name
4. Department.name → name_ar
5. Stealth Tracking — لماذا بيتلغى
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ كُتب: {path}")

def read_file(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        return None
    with open(full, 'r', encoding='utf-8') as f:
        return f.read()

print("=" * 60)
print("Patch 49a Fix2 — إصلاح الأخطاء")
print("=" * 60)


# ════════════════════════════════════════════════
# STEP 1: اكتشف الـ dashboard URL الصح
# ════════════════════════════════════════════════
print("\n📌 Step 1: اكتشف الـ dashboard namespace")

urls_content = read_file('motionhr/urls.py')
print("محتوى urls.py:")
if urls_content:
    for line in urls_content.split('\n'):
        if 'dashboard' in line.lower() or 'namespace' in line.lower():
            print(f"   {line}")

# ════════════════════════════════════════════════
# STEP 2: اكتشف Attendance model fields
# ════════════════════════════════════════════════
print("\n📌 Step 2: اكتشف Attendance model fields")

from attendance.models import Attendance
att_fields = [f.name for f in Attendance._meta.get_fields()]
print(f"   Attendance fields: {att_fields}")

# check_in field name
check_in_field = None
check_out_field = None
for f in att_fields:
    if 'check' in f.lower() and 'in' in f.lower():
        check_in_field = f
    if 'check' in f.lower() and 'out' in f.lower():
        check_out_field = f

print(f"   check_in field: {check_in_field}")
print(f"   check_out field: {check_out_field}")

# ════════════════════════════════════════════════
# STEP 3: اكتشف Company model fields
# ════════════════════════════════════════════════
print("\n📌 Step 3: اكتشف Company model fields")

from companies.models import Company
company_fields = [f.name for f in Company._meta.get_fields()]
name_fields = [f for f in company_fields if 'name' in f.lower()]
print(f"   Company name fields: {name_fields}")

# ════════════════════════════════════════════════
# STEP 4: اكتشف Department model fields
# ════════════════════════════════════════════════
print("\n📌 Step 4: اكتشف Department model fields")

from companies.models import Department
dept_fields = [f.name for f in Department._meta.get_fields()]
dept_name_fields = [f for f in dept_fields if 'name' in f.lower()]
print(f"   Department name fields: {dept_name_fields}")

# ════════════════════════════════════════════════
# STEP 5: اكتشف CompanyPolicy stealth field
# ════════════════════════════════════════════════
print("\n📌 Step 5: اكتشف CompanyPolicy stealth fields")

from companies.models import CompanyPolicy
policy_fields = [f.name for f in CompanyPolicy._meta.get_fields()]
stealth_fields = [f for f in policy_fields if 'stealth' in f.lower()]
print(f"   Stealth fields: {stealth_fields}")

# جرب تجيب السياسة الحالية
try:
    from accounts.models import User
    admin_user = User.objects.filter(role='company_admin').first()
    if admin_user and admin_user.company:
        policy = CompanyPolicy.objects.filter(company=admin_user.company).first()
        if policy:
            print(f"   stealth_tracking_enabled = {policy.stealth_tracking_enabled}")
        else:
            print("   ⚠️ لا توجد سياسة للشركة — محتاج تُنشئ واحدة")
except Exception as e:
    print(f"   خطأ: {e}")

print("\n" + "=" * 60)
print("نتائج الفحص اتعملت — شوف الـ output وابعته")
print("=" * 60)