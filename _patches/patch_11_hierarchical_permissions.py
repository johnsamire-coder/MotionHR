"""
============================================================
Patch 11: الصلاحيات الهرمية (Hierarchical Permissions)
============================================================
كل مستخدم يشوف بس اللي يخصه:
- Super Admin & Company Admin & HR → الكل
- Manager → نفسه + مرؤوسيه (بشكل شجري)
- Employee → بياناته فقط
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. إضافة methods في Employee Model
# ═══════════════════════════════════════════════════════════

EMPLOYEE_METHODS = '''
    
    # ═══════════════════════════════
    # Hierarchical Permissions Methods
    # ═══════════════════════════════
    
    def get_all_subordinates(self):
        """
        جلب كل المرؤوسين (بشكل شجري)
        يعني الموظفين المباشرين + موظفينهم + هكذا
        """
        subordinates = list(self.subordinates.all())
        all_subs = list(subordinates)
        
        for sub in subordinates:
            all_subs.extend(sub.get_all_subordinates())
        
        return all_subs
    
    def get_all_subordinates_ids(self):
        """جلب IDs كل المرؤوسين + نفسه"""
        ids = [self.id]
        for sub in self.get_all_subordinates():
            ids.append(sub.id)
        return ids
    
    def get_manager_chain(self):
        """جلب سلسلة المديرين من فوق"""
        chain = []
        current = self.direct_manager
        while current:
            chain.append(current)
            current = current.direct_manager
        return chain
    
    def can_view_employee(self, other_employee):
        """هل يقدر يشوف بيانات موظف تاني؟"""
        # لو نفس الموظف
        if self.id == other_employee.id:
            return True
        
        # لو المدير المباشر أو من فوق
        if other_employee in self.get_all_subordinates():
            return True
        
        return False
    
    def is_manager_of(self, other_employee):
        """هل هو مدير للموظف ده؟"""
        return other_employee in self.get_all_subordinates()
'''


# ═══════════════════════════════════════════════════════════
# 2. Permissions Module
# ═══════════════════════════════════════════════════════════

PERMISSIONS_MODULE = '''"""
Permissions Helper Functions
دوال مساعدة للصلاحيات الهرمية
"""

from django.db.models import Q


def get_user_employee(user):
    """جلب الـ Employee profile للمستخدم"""
    from employees.models import Employee
    
    if not user or not user.is_authenticated:
        return None
    
    try:
        return Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return None


def get_accessible_employees(user):
    """
    جلب الموظفين اللي المستخدم يقدر يشوفهم حسب دوره
    """
    from employees.models import Employee
    
    if not user or not user.is_authenticated:
        return Employee.objects.none()
    
    # Super Admin و Company Admin و HR Manager يشوفوا الكل
    if user.role in ['super_admin', 'company_admin', 'hr_manager']:
        return Employee.objects.all()
    
    # Manager يشوف نفسه + مرؤوسيه
    if user.role == 'manager':
        my_profile = get_user_employee(user)
        if not my_profile:
            return Employee.objects.none()
        
        ids = my_profile.get_all_subordinates_ids()
        return Employee.objects.filter(id__in=ids)
    
    # Employee يشوف نفسه فقط
    if user.role == 'employee':
        my_profile = get_user_employee(user)
        if not my_profile:
            return Employee.objects.none()
        return Employee.objects.filter(id=my_profile.id)
    
    return Employee.objects.none()


def get_accessible_employee_ids(user):
    """جلب IDs الموظفين اللي يقدر يشوفهم"""
    return list(get_accessible_employees(user).values_list('id', flat=True))


def can_user_edit_employee(user, employee):
    """هل المستخدم يقدر يعدل بيانات موظف معين؟"""
    if not user or not user.is_authenticated:
        return False
    
    # Super Admin و Company Admin و HR Manager يقدروا يعدلوا الكل
    if user.role in ['super_admin', 'company_admin', 'hr_manager']:
        return True
    
    # Manager يقدر يعدل مرؤوسيه بس
    if user.role == 'manager':
        my_profile = get_user_employee(user)
        if my_profile:
            return my_profile.is_manager_of(employee)
    
    # Employee مش يقدر يعدل
    return False


def can_user_delete_employee(user, employee):
    """هل يقدر يحذف؟ - Super Admin و Company Admin بس"""
    if not user or not user.is_authenticated:
        return False
    
    return user.role in ['super_admin', 'company_admin']


def can_user_add_employee(user):
    """هل يقدر يضيف موظف جديد؟"""
    if not user or not user.is_authenticated:
        return False
    
    return user.role in ['super_admin', 'company_admin', 'hr_manager']


def is_admin_or_hr(user):
    """هل هو Admin أو HR؟"""
    if not user or not user.is_authenticated:
        return False
    return user.role in ['super_admin', 'company_admin', 'hr_manager']
'''


# ═══════════════════════════════════════════════════════════
# 3. Middleware للحفاظ على الموظف الحالي
# ═══════════════════════════════════════════════════════════

EMPLOYEE_MIDDLEWARE = '''

class CurrentEmployeeMiddleware:
    """
    Middleware يضيف employee profile للـ request
    عشان نقدر نستخدمه في الـ views و templates
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.current_employee = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from employees.models import Employee
                request.current_employee = Employee.objects.filter(user=request.user).first()
            except Exception:
                pass
        
        response = self.get_response(request)
        return response
'''


# ═══════════════════════════════════════════════════════════
# 4. Template Tags
# ═══════════════════════════════════════════════════════════

TEMPLATE_TAGS = '''"""
Template Tags للصلاحيات الهرمية
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def can_edit_employee(context, employee):
    """هل المستخدم الحالي يقدر يعدل هذا الموظف؟"""
    from core.permissions import can_user_edit_employee
    request = context.get('request')
    if not request:
        return False
    return can_user_edit_employee(request.user, employee)


@register.simple_tag(takes_context=True)
def can_delete_employee(context, employee):
    """هل يقدر يحذف؟"""
    from core.permissions import can_user_delete_employee
    request = context.get('request')
    if not request:
        return False
    return can_user_delete_employee(request.user, employee)


@register.simple_tag(takes_context=True)
def can_add_employee(context):
    """هل يقدر يضيف موظف جديد؟"""
    from core.permissions import can_user_add_employee
    request = context.get('request')
    if not request:
        return False
    return can_user_add_employee(request.user)


@register.simple_tag(takes_context=True)
def is_admin_hr(context):
    """هل هو Admin أو HR؟"""
    from core.permissions import is_admin_or_hr
    request = context.get('request')
    if not request:
        return False
    return is_admin_or_hr(request.user)
'''


# ═══════════════════════════════════════════════════════════
# 5. Employee views محدث
# ═══════════════════════════════════════════════════════════

NEW_EMPLOYEE_VIEWS = '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import csv
from datetime import datetime

from .models import Employee, JobTitle
from .forms import EmployeeForm
from companies.models import Branch, Department
from core.permissions import (
    get_accessible_employees,
    can_user_edit_employee,
    can_user_delete_employee,
    can_user_add_employee,
    is_admin_or_hr,
)


@login_required
def employee_list(request):
    """قائمة الموظفين - محكومة بالصلاحيات الهرمية"""
    
    # جلب الموظفين المسموح رؤيتهم
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title'
    )
    
    # البحث
    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    # الفلترة
    status_filter = request.GET.get('status', '')
    if status_filter:
        employees = employees.filter(status=status_filter)
    
    branch_filter = request.GET.get('branch', '')
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)
    
    department_filter = request.GET.get('department', '')
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    # التصدير
    export_type = request.GET.get('export', '')
    if export_type == 'excel':
        return export_employees_excel(employees)
    elif export_type == 'pdf':
        try:
            return export_employees_pdf(employees)
        except Exception as e:
            messages.warning(request, f'PDF غير متاح - جرب Excel')
            return redirect('employees:list')
    
    # Pagination
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    branches = Branch.objects.all()
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'total_count': paginator.count,
        'search': search,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'branches': branches,
        'departments': departments,
        'status_choices': Employee.STATUS_CHOICES,
        'can_add': can_user_add_employee(request.user),
        'is_admin_hr': is_admin_or_hr(request.user),
    }
    
    return render(request, 'employees/list.html', context)


def export_employees_excel(employees):
    """تصدير Excel"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'الرقم الوظيفي', 'الاسم بالعربي', 'الاسم بالإنجليزي',
        'الرقم القومي', 'تاريخ الميلاد', 'النوع', 'رقم الموبايل',
        'البريد الإلكتروني', 'الفرع', 'الإدارة', 'المسمى الوظيفي',
        'تاريخ التعيين', 'الراتب الأساسي', 'الحالة', 'موظف ميداني',
    ])
    
    for emp in employees:
        writer.writerow([
            emp.employee_code, emp.full_name_ar, emp.full_name_en or '',
            emp.national_id, emp.birth_date, emp.get_gender_display(),
            emp.phone, emp.email or '', emp.branch.name_ar,
            emp.department.name_ar, emp.job_title.name_ar,
            emp.hire_date, emp.basic_salary, emp.get_status_display(),
            'نعم' if emp.is_field_worker else 'لا',
        ])
    
    return response


def export_employees_pdf(employees):
    """تصدير PDF"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.utils import timezone
    
    html_string = render_to_string('employees/print_list.html', {
        'employees': employees,
        'generated_at': timezone.now(),
        'total_count': employees.count() if hasattr(employees, 'count') else len(employees),
    })
    
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def employee_add(request):
    """إضافة موظف جديد - Admin/HR فقط"""
    
    if not can_user_add_employee(request.user):
        raise PermissionDenied('ليس لديك صلاحية لإضافة موظفين')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            messages.success(
                request,
                f'تم إضافة الموظف {employee.full_name_ar} بنجاح ✅'
            )
            return redirect('employees:detail', pk=employee.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'title': 'إضافة موظف جديد',
        'is_edit': False,
    }
    
    return render(request, 'employees/form.html', context)


@login_required
def employee_detail(request, pk):
    """تفاصيل الموظف - محكومة بالصلاحيات"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # التحقق من الصلاحية
    accessible = get_accessible_employees(request.user)
    if not accessible.filter(pk=pk).exists():
        raise PermissionDenied('ليس لديك صلاحية لعرض هذا الموظف')
    
    context = {
        'employee': employee,
        'can_edit': can_user_edit_employee(request.user, employee),
        'can_delete': can_user_delete_employee(request.user, employee),
    }
    
    return render(request, 'employees/detail.html', context)


@login_required
def employee_edit(request, pk):
    """تعديل الموظف - محكومة بالصلاحيات"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # التحقق من الصلاحية
    if not can_user_edit_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية لتعديل هذا الموظف')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(
                request,
                f'تم تحديث بيانات {employee.full_name_ar} بنجاح ✅'
            )
            return redirect('employees:detail', pk=employee.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'employee': employee,
        'title': f'تعديل بيانات {employee.full_name_ar}',
        'is_edit': True,
    }
    
    return render(request, 'employees/form.html', context)


@login_required
def employee_delete(request, pk):
    """حذف الموظف - Admin فقط"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if not can_user_delete_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية لحذف هذا الموظف')
    
    if request.method == 'POST':
        name = employee.full_name_ar
        employee.delete()
        messages.success(request, f'تم حذف الموظف {name} بنجاح')
        return redirect('employees:list')
    
    return render(request, 'employees/delete_confirm.html', {'employee': employee})


@login_required
def employee_print(request, pk=None):
    """صفحة طباعة"""
    from django.utils import timezone
    
    if pk:
        employee = get_object_or_404(Employee, pk=pk)
        accessible = get_accessible_employees(request.user)
        if not accessible.filter(pk=pk).exists():
            raise PermissionDenied('ليس لديك صلاحية')
        employees = accessible.filter(pk=pk)
        title = f"بيانات {employee.full_name_ar}"
    else:
        employees = get_accessible_employees(request.user).select_related(
            'branch', 'department', 'job_title'
        )
        title = "قائمة الموظفين"
    
    context = {
        'employees': employees,
        'title': title,
        'generated_at': timezone.now(),
        'is_single': pk is not None,
    }
    
    return render(request, 'employees/print_list.html', context)


@login_required
def employee_print_detail(request, pk):
    """طباعة بيانات موظف"""
    from django.utils import timezone
    
    employee = get_object_or_404(Employee, pk=pk)
    accessible = get_accessible_employees(request.user)
    if not accessible.filter(pk=pk).exists():
        raise PermissionDenied('ليس لديك صلاحية')
    
    context = {
        'employee': employee,
        'generated_at': timezone.now(),
    }
    
    return render(request, 'employees/print_detail.html', context)
'''


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def create_file(relative_path, content):
    """إنشاء ملف"""
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')


def add_methods_to_employee_model():
    """إضافة methods جديدة في Employee model"""
    models_path = BASE_DIR / 'employees' / 'models.py'
    
    if not models_path.exists():
        return False, "ملف models.py مش موجود"
    
    content = models_path.read_text(encoding='utf-8')
    
    if 'get_all_subordinates' in content:
        return True, "الـ methods موجودة بالفعل"
    
    # نضيف قبل نهاية class Employee (قبل class EmployeeDocument)
    old = 'class EmployeeDocument(TenantModel):'
    new = EMPLOYEE_METHODS + '\n\nclass EmployeeDocument(TenantModel):'
    
    if old not in content:
        return False, "لم يتم العثور على نقطة الإدراج"
    
    content = content.replace(old, new)
    models_path.write_text(content, encoding='utf-8')
    return True, "تم إضافة methods للـ Employee model"


def create_permissions_module():
    """إنشاء core/permissions.py"""
    path = BASE_DIR / 'core' / 'permissions.py'
    path.write_text(PERMISSIONS_MODULE, encoding='utf-8')
    return True, "تم إنشاء core/permissions.py"


def add_employee_middleware():
    """إضافة CurrentEmployeeMiddleware"""
    middleware_path = BASE_DIR / 'core' / 'middleware.py'
    
    if not middleware_path.exists():
        return False, "ملف middleware.py مش موجود"
    
    content = middleware_path.read_text(encoding='utf-8')
    
    if 'CurrentEmployeeMiddleware' in content:
        return True, "Middleware موجود بالفعل"
    
    with middleware_path.open('a', encoding='utf-8') as f:
        f.write(EMPLOYEE_MIDDLEWARE)
    
    return True, "تم إضافة CurrentEmployeeMiddleware"


def register_middleware_in_settings():
    """تسجيل الـ Middleware في settings"""
    settings_path = BASE_DIR / 'motionhr' / 'settings.py'
    
    if not settings_path.exists():
        return False, "ملف settings.py مش موجود"
    
    content = settings_path.read_text(encoding='utf-8')
    
    if 'CurrentEmployeeMiddleware' in content:
        return True, "Middleware مسجل بالفعل"
    
    old = "'core.middleware.TenantMiddleware',"
    new = """'core.middleware.TenantMiddleware',
    'core.middleware.CurrentEmployeeMiddleware',"""
    
    if old not in content:
        return False, "لم يتم العثور على TenantMiddleware"
    
    content = content.replace(old, new)
    settings_path.write_text(content, encoding='utf-8')
    return True, "تم تسجيل CurrentEmployeeMiddleware"


def create_template_tags():
    """إنشاء template tags"""
    templatetags_dir = BASE_DIR / 'core' / 'templatetags'
    templatetags_dir.mkdir(parents=True, exist_ok=True)
    
    # __init__.py
    init_path = templatetags_dir / '__init__.py'
    init_path.write_text('', encoding='utf-8')
    
    # permissions.py
    tags_path = templatetags_dir / 'permissions.py'
    tags_path.write_text(TEMPLATE_TAGS, encoding='utf-8')
    
    return True, "تم إنشاء template tags"


def update_employee_views():
    """تحديث employees/views.py"""
    views_path = BASE_DIR / 'employees' / 'views.py'
    
    if not views_path.exists():
        return False, "ملف views.py مش موجود"
    
    # نستبدل الملف بالكامل
    views_path.write_text(NEW_EMPLOYEE_VIEWS, encoding='utf-8')
    return True, "تم تحديث views.py"


def add_permission_tags_to_list_template():
    """تحديث list.html لاستخدام Permission Tags"""
    list_path = BASE_DIR / 'templates' / 'employees' / 'list.html'
    
    if not list_path.exists():
        return False, "ملف list.html مش موجود"
    
    content = list_path.read_text(encoding='utf-8')
    
    if '{% load permissions %}' in content:
        return True, "التعديل موجود بالفعل"
    
    # نضيف load في الأول
    old = "{% extends 'base/dashboard_base.html' %}"
    new = "{% extends 'base/dashboard_base.html' %}\n{% load permissions %}"
    
    content = content.replace(old, new, 1)
    list_path.write_text(content, encoding='utf-8')
    
    return True, "تم إضافة load permissions"


def main():
    print("=" * 60)
    print("🔧 Patch 11: الصلاحيات الهرمية")
    print("=" * 60)
    print()
    
    tasks = [
        ('إضافة methods للـ Employee model', add_methods_to_employee_model),
        ('إنشاء core/permissions.py', create_permissions_module),
        ('إضافة CurrentEmployeeMiddleware', add_employee_middleware),
        ('تسجيل Middleware في settings', register_middleware_in_settings),
        ('إنشاء Template Tags', create_template_tags),
        ('تحديث employees/views.py', update_employee_views),
        ('تحديث list.html', add_permission_tags_to_list_template),
    ]
    
    for name, func in tasks:
        try:
            success, message = func()
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("🎯 كيف يعمل النظام:")
    print()
    print("  Super Admin      → يشوف كل الشركات والموظفين")
    print("  Company Admin    → يشوف كل موظفي شركته")
    print("  HR Manager       → يشوف كل موظفي شركته")
    print("  Manager          → يشوف نفسه + مرؤوسيه فقط")
    print("  Employee         → يشوف بياناته فقط")
    print()
    print("🧪 للاختبار:")
    print("  1. اعمل موظف جديد وحدد له 'المدير المباشر'")
    print("  2. اعمل User للموظف ده وحدد له role='manager'")
    print("  3. سجل دخول بيه وشوف اللي بيقدر يشوفه")
    print()
    print("⚠️  لازم كل موظف يكون مربوط بـ User عشان النظام يشتغل")
    print()


if __name__ == '__main__':
    main()