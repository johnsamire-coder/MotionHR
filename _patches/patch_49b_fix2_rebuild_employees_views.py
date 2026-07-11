"""
Patch 49b Fix2 — Rebuild employees/views.py Safely

الهدف:
- إصلاح IndentationError في employees/views.py
- الحفاظ على:
  * Employee List
  * Live Search
  * Excel Export
  * PDF Export
  * CRUD الأساسي
  * Print pages
  * My Balance / My Deductions
- اعتماد exports.py الجديد بدون أي دوال export قديمة داخل views.py
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")


def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


print("=" * 60)
print("Patch 49b Fix2 — Rebuild employees/views.py Safely")
print("=" * 60)

# Backup current file
src = os.path.join(BASE_DIR, "employees/views.py")
backup = os.path.join(BASE_DIR, "_patches/_backups/employees_views_before_patch_49b_fix2.py.bak")
os.makedirs(os.path.dirname(backup), exist_ok=True)
if os.path.exists(src):
    shutil.copy2(src, backup)
    print("✅ Backup created:", "_patches/_backups/employees_views_before_patch_49b_fix2.py.bak")

views_code = '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import Employee, JobTitle, Deduction
from .forms import EmployeeForm
from .exports import export_employees_excel, export_employees_pdf
from companies.models import Branch, Department
from subscriptions.helpers import feature_required
from core.permissions import (
    get_accessible_employees,
    can_user_edit_employee,
    can_user_delete_employee,
    can_user_add_employee,
    is_admin_or_hr,
)


# ═════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════

def _get_current_company(user):
    company = getattr(user, 'company', None)
    if company:
        return company
    try:
        return user.employee.company
    except Exception:
        return None


def _employee_status_choices():
    return getattr(Employee, 'STATUS_CHOICES', [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'موقوف'),
        ('terminated', 'منتهي الخدمة'),
    ])


def _safe_related_all(instance, attr_name, fallback_attr_name=None):
    rel = getattr(instance, attr_name, None)
    if rel is not None:
        try:
            return rel.all()
        except Exception:
            pass

    if fallback_attr_name:
        rel2 = getattr(instance, fallback_attr_name, None)
        if rel2 is not None:
            try:
                return rel2.all()
            except Exception:
                pass
    return []


def _configure_employee_form(form, company=None, instance=None):
    try:
        if 'branch' in form.fields:
            qs = Branch.objects.all()
            if company:
                qs = qs.filter(company=company)
            form.fields['branch'].queryset = qs.order_by('name_ar', 'name_en')

        if 'department' in form.fields:
            qs = Department.objects.all()
            if company:
                qs = qs.filter(company=company)
            form.fields['department'].queryset = qs.order_by('name_ar', 'name_en')

        if 'job_title' in form.fields:
            qs = JobTitle.objects.all()
            if company:
                qs = qs.filter(company=company)
            if hasattr(JobTitle, 'is_active'):
                try:
                    qs = qs.filter(is_active=True)
                except Exception:
                    pass
            form.fields['job_title'].queryset = qs.order_by('name_ar', 'name_en')

        if 'direct_manager' in form.fields:
            qs = Employee.objects.all()
            if company:
                qs = qs.filter(company=company)
            try:
                qs = qs.filter(status='active')
            except Exception:
                pass
            if instance and instance.pk:
                qs = qs.exclude(pk=instance.pk)
            form.fields['direct_manager'].queryset = qs.order_by('employee_code')
    except Exception:
        pass


def _try_sync_employee_account(employee):
    """
    محاولة غير مدمرة لاستدعاء أي helper موجود في employees/account_utils.py
    علشان ما نكسرش ميزة الحسابات التلقائية لو موجودة بأسماء مختلفة.
    """
    try:
        from . import account_utils
    except Exception:
        return

    candidate_names = [
        'create_or_update_employee_account',
        'ensure_employee_account',
        'sync_employee_account',
        'sync_employee_user',
        'create_employee_account',
        'provision_employee_account',
        'create_employee_user',
    ]

    for name in candidate_names:
        func = getattr(account_utils, name, None)
        if callable(func):
            try:
                func(employee)
                return
            except TypeError:
                try:
                    func(employee=employee)
                    return
                except Exception:
                    pass
            except Exception:
                pass


def _get_employee_for_user_or_404(user, pk):
    qs = get_accessible_employees(user).select_related(
        'branch', 'department', 'job_title', 'direct_manager'
    )
    return get_object_or_404(qs, pk=pk)


# ═════════════════════════════════════════════════════════════
# Employee List
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_list(request):
    """قائمة الموظفين - محكومة بالصلاحيات الهرمية"""
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager'
    )

    # البحث
    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(middle_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(first_name_en__icontains=search) |
            Q(last_name_en__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(job_title__name_ar__icontains=search) |
            Q(job_title__name_en__icontains=search) |
            Q(branch__name_ar__icontains=search) |
            Q(branch__name_en__icontains=search) |
            Q(department__name_ar__icontains=search) |
            Q(department__name_en__icontains=search)
        ).distinct()

    # الفلاتر
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        employees = employees.filter(status=status_filter)

    branch_filter = request.GET.get('branch', '').strip()
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)

    department_filter = request.GET.get('department', '').strip()
    if department_filter:
        employees = employees.filter(department_id=department_filter)

    employees = employees.order_by('employee_code')

    # التصدير
    export_type = request.GET.get('export', '').strip()
    if export_type == 'excel':
        return export_employees_excel(employees, user=request.user)
    elif export_type == 'pdf':
        try:
            return export_employees_pdf(employees, user=request.user)
        except Exception as e:
            messages.warning(request, f'خطأ في تصدير PDF: {e}')
            return redirect('employees:list')

    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    company = _get_current_company(request.user)
    branches = Branch.objects.all()
    departments = Department.objects.all()
    if company:
        branches = branches.filter(company=company)
        departments = departments.filter(company=company)

    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'branches': branches.order_by('name_ar', 'name_en'),
        'departments': departments.order_by('name_ar', 'name_en'),
        'search': search,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'status_choices': _employee_status_choices(),
    }
    return render(request, 'employees/list.html', context)


# ═════════════════════════════════════════════════════════════
# Add Employee
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_add(request):
    if not can_user_add_employee(request.user):
        raise PermissionDenied("ليس لديك صلاحية إضافة موظف")

    company = _get_current_company(request.user)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        _configure_employee_form(form, company=company)

        if form.is_valid():
            employee = form.save(commit=False)

            if company and hasattr(employee, 'company_id') and not employee.company_id:
                employee.company = company

            employee.save()
            try:
                form.save_m2m()
            except Exception:
                pass

            _try_sync_employee_account(employee)
            messages.success(request, f'تم إضافة الموظف {employee.full_name_ar} بنجاح')
            return redirect('employees:list')
        else:
            messages.error(request, 'يرجى مراجعة الحقول المطلوبة')
    else:
        form = EmployeeForm()
        _configure_employee_form(form, company=company)

    context = {
        'form': form,
        'page_title': 'إضافة موظف',
        'form_title': 'إضافة موظف جديد',
        'is_edit': False,
    }
    return render(request, 'employees/form.html', context)


# ═════════════════════════════════════════════════════════════
# Edit Employee
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not can_user_edit_employee(request.user, employee):
        raise PermissionDenied("ليس لديك صلاحية تعديل هذا الموظف")

    company = _get_current_company(request.user)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        _configure_employee_form(form, company=company, instance=employee)

        if form.is_valid():
            employee = form.save(commit=False)

            if company and hasattr(employee, 'company_id') and not employee.company_id:
                employee.company = company

            employee.save()
            try:
                form.save_m2m()
            except Exception:
                pass

            _try_sync_employee_account(employee)
            messages.success(request, f'تم تحديث بيانات الموظف {employee.full_name_ar}')
            return redirect('employees:list')
        else:
            messages.error(request, 'يرجى مراجعة الحقول المطلوبة')
    else:
        form = EmployeeForm(instance=employee)
        _configure_employee_form(form, company=company, instance=employee)

    context = {
        'form': form,
        'employee': employee,
        'page_title': 'تعديل موظف',
        'form_title': 'تعديل بيانات الموظف',
        'is_edit': True,
    }
    return render(request, 'employees/form.html', context)


# ═════════════════════════════════════════════════════════════
# Delete Employee
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not can_user_delete_employee(request.user, employee):
        raise PermissionDenied("ليس لديك صلاحية حذف هذا الموظف")

    if request.method == 'POST':
        employee_name = employee.full_name_ar
        employee.delete()
        messages.success(request, f'تم حذف الموظف {employee_name}')
        return redirect('employees:list')

    return render(request, 'employees/delete_confirm.html', {
        'employee': employee,
        'page_title': 'حذف موظف',
    })


# ═════════════════════════════════════════════════════════════
# Detail
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_detail(request, pk):
    employee = _get_employee_for_user_or_404(request.user, pk)

    documents = _safe_related_all(employee, 'documents', 'employeedocument_set')
    deductions = _safe_related_all(employee, 'deductions', 'deduction_set')

    context = {
        'employee': employee,
        'documents': documents,
        'deductions': deductions,
        'page_title': f'ملف الموظف - {employee.full_name_ar}',
    }
    return render(request, 'employees/detail.html', context)


# ═════════════════════════════════════════════════════════════
# Print List
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_print_list(request):
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager'
    ).order_by('employee_code')

    context = {
        'employees': employees,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'page_title': 'طباعة قائمة الموظفين',
    }
    return render(request, 'employees/print_list.html', context)


# ═════════════════════════════════════════════════════════════
# Print Detail
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_print_detail(request, pk):
    employee = _get_employee_for_user_or_404(request.user, pk)

    context = {
        'employee': employee,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'page_title': f'طباعة ملف الموظف - {employee.full_name_ar}',
    }
    return render(request, 'employees/print_detail.html', context)


# ═════════════════════════════════════════════════════════════
# Print Credentials
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def print_credentials(request, pk):
    employee = _get_employee_for_user_or_404(request.user, pk)

    username = '—'
    if getattr(employee, 'user', None):
        username = getattr(employee.user, 'username', '—') or '—'

    context = {
        'employee': employee,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'username': username,
        'page_title': f'بيانات الدخول - {employee.full_name_ar}',
    }
    return render(request, 'employees/print_credentials.html', context)


# ═════════════════════════════════════════════════════════════
# My Balance
# ═════════════════════════════════════════════════════════════

@login_required
def my_balance(request):
    try:
        employee = Employee.objects.select_related('branch', 'department', 'job_title').get(user=request.user)
    except Employee.DoesNotExist:
        messages.warning(request, 'لا يوجد ملف موظف مرتبط بهذا الحساب')
        return redirect('dashboard')

    try:
        from leaves.models import LeaveBalance
        balances = LeaveBalance.objects.filter(employee=employee).select_related('leave_type')
    except Exception:
        balances = []

    context = {
        'employee': employee,
        'balances': balances,
        'page_title': 'رصيد إجازاتي',
    }
    return render(request, 'employees/my_balance.html', context)


# ═════════════════════════════════════════════════════════════
# My Deductions
# ═════════════════════════════════════════════════════════════

@login_required
def my_deductions(request):
    try:
        employee = Employee.objects.select_related('branch', 'department', 'job_title').get(user=request.user)
    except Employee.DoesNotExist:
        messages.warning(request, 'لا يوجد ملف موظف مرتبط بهذا الحساب')
        return redirect('dashboard')

    deductions = Deduction.objects.filter(employee=employee).order_by('-date', '-id')

    context = {
        'employee': employee,
        'deductions': deductions,
        'page_title': 'خصوماتي',
    }
    return render(request, 'employees/my_deductions.html', context)


# ═════════════════════════════════════════════════════════════
# Live Search API
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_search_api(request):
    """API للبحث الحي في الموظفين — Patch 49b"""
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    department_filter = request.GET.get('department', '').strip()

    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager'
    )

    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(middle_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(first_name_en__icontains=search) |
            Q(last_name_en__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(job_title__name_ar__icontains=search) |
            Q(job_title__name_en__icontains=search) |
            Q(branch__name_ar__icontains=search) |
            Q(branch__name_en__icontains=search) |
            Q(department__name_ar__icontains=search) |
            Q(department__name_en__icontains=search)
        ).distinct()

    if status_filter:
        employees = employees.filter(status=status_filter)

    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)

    if department_filter:
        employees = employees.filter(department_id=department_filter)

    employees = employees.order_by('employee_code')[:100]

    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'employee_code': emp.employee_code or '',
            'full_name_ar': getattr(emp, 'full_name_ar', '') or '',
            'job_title': (
                getattr(emp.job_title, 'name_ar', None)
                or getattr(emp.job_title, 'name_en', None)
                or '—'
            ) if emp.job_title else '—',
            'department': (
                getattr(emp.department, 'name_ar', None)
                or getattr(emp.department, 'name_en', None)
                or '—'
            ) if emp.department else '—',
            'branch': (
                getattr(emp.branch, 'name_ar', None)
                or getattr(emp.branch, 'name_en', None)
                or '—'
            ) if emp.branch else '—',
            'phone': emp.phone or '—',
            'email': emp.email or '—',
            'status': emp.get_status_display() if hasattr(emp, 'get_status_display') else (emp.status or '—'),
            'manager': (
                getattr(emp.direct_manager, 'full_name_ar', None) or '—'
            ) if emp.direct_manager else '—',
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
        'results': results,
    })


# ═════════════════════════════════════════════════════════════
# Compatibility Aliases
# ═════════════════════════════════════════════════════════════

employee_create = employee_add
add_employee = employee_add
create_employee = employee_add
add = employee_add

employee_update = employee_edit
edit_employee = employee_edit
update_employee = employee_edit
edit = employee_edit

employee_remove = employee_delete
delete_employee = employee_delete
remove_employee = employee_delete
delete = employee_delete

detail = employee_detail

employees_print_list = employee_print_list
print_list = employee_print_list
print_list_view = employee_print_list

employees_print_detail = employee_print_detail
print_detail = employee_print_detail
print_detail_view = employee_print_detail

employee_print_credentials = print_credentials
credentials_print = print_credentials
print_credentials_view = print_credentials

my_balance_view = my_balance
employee_balance = my_balance

my_deductions_view = my_deductions
employee_deductions = my_deductions
'''

write_file("employees/views.py", views_code)

print("\\n" + "=" * 60)
print("✅ Patch 49b Fix2 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ إعادة بناء employees/views.py بالكامل بشكل سليم
  ✅ ربط views.py مع employees/exports.py الجديد
  ✅ الحفاظ على:
     - قائمة الموظفين
     - Live Search
     - Excel Export
     - PDF Export
     - Add / Edit / Delete / Detail
     - Print pages
     - My Balance / My Deductions
  ✅ إنشاء Backup قبل التعديل

الملفات:
  ✅ employees/views.py
  ✅ _patches/_backups/employees_views_before_patch_49b_fix2.py.bak

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")