"""
============================================================
Patch 04: إصلاح البيانات الناقصة
============================================================
- ربط المسميات الوظيفية بالشركة
- ربط الفروع بالشركة
- ربط الإدارات بالشركة
- إنشاء بيانات افتراضية لو مفيش
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


def fix_data():
    from companies.models import Company, Branch, Department
    from employees.models import JobTitle
    
    print("🔍 فحص البيانات الحالية...")
    print("-" * 60)
    
    # 1. الشركة
    companies = Company.objects.all()
    print(f"عدد الشركات: {companies.count()}")
    
    if not companies.exists():
        print("❌ لا توجد شركة! جاري إنشاء شركة افتراضية...")
        company = Company.objects.create(
            name_ar='شركة الاختبار',
            name_en='Test Company',
            email='test@test.com',
            phone='01000000000',
            is_active=True
        )
        print(f"✅ تم إنشاء الشركة: {company.name_ar}")
    else:
        company = companies.first()
        print(f"✅ الشركة موجودة: {company.name_ar}")
    
    print()
    
    # 2. الفروع
    print("🔍 فحص الفروع...")
    all_branches = Branch.objects.all()
    print(f"إجمالي الفروع: {all_branches.count()}")
    
    branches_without_company = Branch.objects.filter(company__isnull=True)
    if branches_without_company.exists():
        print(f"⚠️  {branches_without_company.count()} فرع بدون شركة - جاري الربط...")
        branches_without_company.update(company=company)
        print("✅ تم ربط الفروع بالشركة")
    
    if not all_branches.exists():
        print("❌ لا توجد فروع! جاري إنشاء فرع رئيسي...")
        Branch.objects.create(
            company=company,
            name_ar='الفرع الرئيسي',
            name_en='Main Branch',
            is_main=True,
            is_active=True
        )
        print("✅ تم إنشاء الفرع الرئيسي")
    
    print()
    
    # 3. الإدارات
    print("🔍 فحص الإدارات...")
    all_departments = Department.objects.all()
    print(f"إجمالي الإدارات: {all_departments.count()}")
    
    departments_without_company = Department.objects.filter(company__isnull=True)
    if departments_without_company.exists():
        print(f"⚠️  {departments_without_company.count()} إدارة بدون شركة - جاري الربط...")
        departments_without_company.update(company=company)
        print("✅ تم ربط الإدارات بالشركة")
    
    if not all_departments.exists():
        print("❌ لا توجد إدارات! جاري إنشاء إدارات افتراضية...")
        default_departments = [
            'الموارد البشرية',
            'المبيعات',
            'التسويق',
            'المالية',
            'تكنولوجيا المعلومات',
            'خدمة العملاء',
            'العمليات',
        ]
        for dept_name in default_departments:
            Department.objects.create(
                company=company,
                name_ar=dept_name,
                is_active=True
            )
        print(f"✅ تم إنشاء {len(default_departments)} إدارة")
    
    print()
    
    # 4. المسميات الوظيفية
    print("🔍 فحص المسميات الوظيفية...")
    
    # نستخدم all_objects عشان نتخطى الـ tenant filter
    all_job_titles = JobTitle.all_objects.all()
    print(f"إجمالي المسميات: {all_job_titles.count()}")
    
    titles_without_company = JobTitle.all_objects.filter(company__isnull=True)
    if titles_without_company.exists():
        print(f"⚠️  {titles_without_company.count()} مسمى بدون شركة - جاري الربط...")
        titles_without_company.update(company=company)
        print("✅ تم ربط المسميات بالشركة")
    
    if not all_job_titles.exists():
        print("❌ لا توجد مسميات وظيفية! جاري إنشاء مسميات افتراضية...")
        default_titles = [
            ('مدير عام', 'General Manager'),
            ('مدير موارد بشرية', 'HR Manager'),
            ('محاسب', 'Accountant'),
            ('مطور برامج', 'Software Developer'),
            ('مصمم جرافيك', 'Graphic Designer'),
            ('مندوب مبيعات', 'Sales Representative'),
            ('مسؤول تسويق', 'Marketing Officer'),
            ('سكرتير', 'Secretary'),
            ('موظف خدمة عملاء', 'Customer Service'),
            ('فني صيانة', 'Maintenance Technician'),
            ('سائق', 'Driver'),
            ('عامل', 'Worker'),
        ]
        for name_ar, name_en in default_titles:
            JobTitle.objects.create(
                company=company,
                name_ar=name_ar,
                name_en=name_en,
                is_active=True
            )
        print(f"✅ تم إنشاء {len(default_titles)} مسمى وظيفي")
    
    print()
    print("=" * 60)
    print("📊 الملخص النهائي:")
    print("-" * 60)
    print(f"  الشركة:           {Company.objects.count()}")
    print(f"  الفروع:           {Branch.objects.count()}")
    print(f"  الإدارات:         {Department.objects.count()}")
    print(f"  المسميات:         {JobTitle.all_objects.count()}")
    print("=" * 60)


def main():
    print("=" * 60)
    print("🔧 Patch 04: إصلاح البيانات الناقصة")
    print("=" * 60)
    print()
    
    try:
        fix_data()
        print()
        print("✨ تم الانتهاء بنجاح!")
        print()
        print("دلوقتي:")
        print("  1. ارجع لصفحة التعديل")
        print("  2. هتلاقي كل المسميات والفروع والإدارات")
        print("  3. اختار المسمى الوظيفي واحفظ")
        print()
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()