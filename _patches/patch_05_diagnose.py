"""
============================================================
Patch 05: تشخيص المشكلة
============================================================
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()


def diagnose():
    from django.contrib.auth import get_user_model
    from companies.models import Company, Branch, Department
    from employees.models import JobTitle, Employee
    
    User = get_user_model()
    
    print("=" * 60)
    print("🔍 تشخيص شامل للمشكلة")
    print("=" * 60)
    print()
    
    # 1. الشركات
    print("📊 1. الشركات:")
    print("-" * 60)
    for company in Company.objects.all():
        print(f"  🏢 ID: {company.id} | {company.name_ar}")
    print()
    
    # 2. المستخدمين
    print("👥 2. المستخدمين:")
    print("-" * 60)
    for user in User.objects.all():
        company_name = user.company.name_ar if user.company else "❌ بدون شركة"
        role = user.get_role_display() if user.role else "❌ بدون دور"
        print(f"  👤 {user.username}")
        print(f"      الدور: {role}")
        print(f"      الشركة: {company_name}")
        print()
    
    # 3. المسميات الوظيفية
    print("💼 3. المسميات الوظيفية:")
    print("-" * 60)
    for title in JobTitle.all_objects.all():
        company_name = title.company.name_ar if title.company else "❌ بدون شركة"
        print(f"  📋 {title.name_ar}")
        print(f"      الشركة: {company_name}")
        print(f"      نشط: {'✅' if title.is_active else '❌'}")
        print()
    
    # 4. الفروع
    print("🏬 4. الفروع:")
    print("-" * 60)
    for branch in Branch.objects.all():
        print(f"  📍 {branch.name_ar}")
        print(f"      الشركة: {branch.company.name_ar}")
        print()
    
    # 5. الإدارات
    print("🏛️  5. الإدارات:")
    print("-" * 60)
    for dept in Department.objects.all():
        print(f"  📂 {dept.name_ar}")
        print(f"      الشركة: {dept.company.name_ar}")
        print()
    
    # 6. الموظفين
    print("👨‍💼 6. الموظفين:")
    print("-" * 60)
    for emp in Employee.objects.all():
        print(f"  🧑 {emp.full_name_ar}")
        print(f"      الكود: {emp.employee_code}")
        print(f"      المسمى: {emp.job_title.name_ar}")
        print(f"      الشركة: {emp.company.name_ar}")
        print()
    
    print("=" * 60)
    print("🎯 التحليل:")
    print("=" * 60)
    
    # فحص الحالة
    issues = []
    
    # هل الـ superuser مربوط بشركة؟
    superusers = User.objects.filter(is_superuser=True)
    for su in superusers:
        if not su.company:
            issues.append(f"⚠️  المستخدم '{su.username}' Superuser بدون شركة")
        if su.role != 'super_admin':
            issues.append(f"⚠️  المستخدم '{su.username}' دوره '{su.role}' مش 'super_admin'")
    
    # هل المسميات مربوطة بالشركة الصح؟
    company = Company.objects.first()
    if company:
        titles_wrong_company = JobTitle.all_objects.exclude(company=company)
        if titles_wrong_company.exists():
            issues.append(f"⚠️  فيه {titles_wrong_company.count()} مسميات مش مربوطة بـ '{company.name_ar}'")
    
    if issues:
        print()
        for issue in issues:
            print(issue)
    else:
        print()
        print("✅ كل حاجة تمام على المستوى ده")
        print()
        print("💡 المشكلة على الأرجح في الـ Session/Middleware")
        print("   الحل: اعمل Logout و Login تاني")
    
    print()


if __name__ == '__main__':
    diagnose()