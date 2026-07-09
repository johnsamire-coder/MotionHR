"""
============================================================
Patch 06: إصلاح فورم الموظف للـ Super Admin
============================================================
المشكلة: Super Admin مش شايف المسميات والفروع والإدارات
لأنه مش مربوط بشركة
الحل: نخلي Super Admin يشوف كل حاجة
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def fix_form():
    """إصلاح فلترة الفورم"""
    form_path = BASE_DIR / 'employees' / 'forms.py'
    
    if not form_path.exists():
        return False, "ملف forms.py مش موجود"
    
    content = form_path.read_text(encoding='utf-8')
    
    # نستبدل الـ __init__ بالكامل
    old_init = '''    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # فلترة القوائم حسب الشركة الحالية
        company = get_current_company()
        
        if company:
            self.fields['branch'].queryset = Branch.objects.filter(company=company)
            self.fields['department'].queryset = Department.objects.filter(company=company)
            self.fields['job_title'].queryset = JobTitle.objects.filter(company=company)
            self.fields['direct_manager'].queryset = Employee.objects.filter(company=company)'''
    
    new_init = '''    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # فلترة القوائم حسب الشركة الحالية
        company = get_current_company()
        user = get_current_user()
        
        # لو Super Admin يشوف كل حاجة
        if user and hasattr(user, 'role') and user.role == 'super_admin':
            self.fields['branch'].queryset = Branch.objects.all()
            self.fields['department'].queryset = Department.objects.all()
            self.fields['job_title'].queryset = JobTitle.all_objects.all()
            self.fields['direct_manager'].queryset = Employee.all_objects.all()
        elif company:
            self.fields['branch'].queryset = Branch.objects.filter(company=company)
            self.fields['department'].queryset = Department.objects.filter(company=company)
            self.fields['job_title'].queryset = JobTitle.objects.filter(company=company)
            self.fields['direct_manager'].queryset = Employee.objects.filter(company=company)'''
    
    if new_init in content:
        return True, "الإصلاح موجود بالفعل"
    
    if old_init not in content:
        return False, "لم يتم العثور على الكود القديم"
    
    content = content.replace(old_init, new_init)
    
    # نتأكد إن get_current_user موجود في الـ imports
    old_import = "from core.middleware import get_current_company"
    new_import = "from core.middleware import get_current_company, get_current_user"
    
    if old_import in content and 'get_current_user' not in content:
        content = content.replace(old_import, new_import)
    
    form_path.write_text(content, encoding='utf-8')
    
    return True, "تم إصلاح الفورم"


def fix_employee_views():
    """إصلاح views الموظفين ليشوف Super Admin كل حاجة"""
    views_path = BASE_DIR / 'employees' / 'views.py'
    
    if not views_path.exists():
        return False, "ملف views.py مش موجود"
    
    content = views_path.read_text(encoding='utf-8')
    
    # نستبدل السطر اللي بيجيب الـ branches و departments
    old_code = '''    branches = Branch.objects.all()
    departments = Department.objects.all()'''
    
    new_code = '''    # Super Admin يشوف كل حاجة
    if request.user.role == 'super_admin':
        branches = Branch.objects.all()
        departments = Department.objects.all()
    else:
        branches = Branch.objects.all()
        departments = Department.objects.all()'''
    
    # مش هنغير حاجة هنا لأن Branch و Department مش TenantModel
    # هما شغالين عادي
    
    return True, "views شغالة صح"


def main():
    print("=" * 60)
    print("🔧 Patch 06: إصلاح فورم الموظف للـ Super Admin")
    print("=" * 60)
    print()
    
    try:
        success, message = fix_form()
        icon = "✅" if success else "❌"
        print(f"  {icon} {message}")
        
        print()
        print("=" * 60)
        print("✨ تم الانتهاء!")
        print("=" * 60)
        print()
        print("دلوقتي:")
        print("  1. ارجع لصفحة تعديل الموظف")
        print("  2. اضغط F5 لتحديث الصفحة")
        print("  3. هتلاقي المسمى الوظيفي والفرع والإدارة")
        print("  4. اختار وادوس حفظ")
        print()
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()