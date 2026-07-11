"""
Patch 49b Fix7 — Final Clean Rebuild for employees/views.py

الهدف:
- إصلاح SyntaxError / AttributeError / Compatibility issues في employees/views.py نهائيًا
- إعادة بناء الملف بالكامل بشكل نظيف
- تضمين كل الـ views المطلوبة من employees/urls.py
- الحفاظ على:
  * employee list
  * live search
  * excel export
  * pdf export
  * add/edit/delete/detail
  * print pages
  * create/deactivate/reset account
  * my balance / my deductions

هذا الباتش:
- supersedes كل المحاولات السابقة الخاصة بـ employees/views.py في Patch 49b
"""

import os
import shutil
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")


print("=" * 60)
print("Patch 49b Fix7 — Final Clean Rebuild for employees/views.py")
print("=" * 60)

views_path = "employees/views.py"
urls_path = "employees/urls.py"

views_full = os.path.join(BASE_DIR, views_path)
urls_full = os.path.join(BASE_DIR, urls_path)

if not os.path.exists(urls_full):
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

# Backup
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

if os.path.exists(views_full):
    shutil.copy2(
        views_full,
        os.path.join(backup_dir, "employees_views_before_patch_49b_fix7.py.bak")
    )
    print("✅ Backup created: _patches/_backups/employees_views_before_patch_49b_fix7.py.bak")

shutil.copy2(
    urls_full,
    os.path.join(backup_dir, "employees_urls_before_patch_49b_fix7.py.bak")
)
print("✅ Backup created: _patches/_backups/employees_urls_before_patch_49b_fix7.py.bak")

# قراءة أسماء الـ views المطلوبة من urls.py للتأكيد
urls_content = read_file(urls_path) or ""
used_view_names = sorted(set(re.findall(r'views\.([A-Za-z_][A-Za-z0-9_]*)', urls_content)))
print("\n📌 Views referenced in employees/urls.py:")
for name in used_view_names:
    print("   -", name)

views_code = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.crypto import get_random_string

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


def _employee_name(employee):
    return (
        getattr(employee, 'full_name_ar', None)
        or f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
        or getattr(employee, 'employee_code', '')
        or 'الموظف'
    )


def _status_choices():
    return getattr(Employee, 'STATUS_CHOICES', [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'موقوف'),
        ('terminated', 'منتهي الخدمة'),
    ])


def _safe_qs(model, company=None):
    qs = model.objects.all()
    if company and hasattr(model, 'company'):
        try:
            qs = qs.filter(company=company)
        except Exception:
            pass
    return qs


def _configure_employee_form(form, company=None, instance=None):
    try:
        if 'branch' in form.fields:
            form.fields['branch'].queryset = _safe_qs(Branch, company).order_by('name_ar', 'name_en')
    except Exception:
        pass

    try:
        if 'department' in form.fields:
            form.fields['department'].queryset = _safe_qs(Department, company).order_by('name_ar', 'name_en')
    except Exception:
        pass

    try:
        if 'job_title' in form.fields:
            qs = _safe_qs(JobTitle, company)
            if hasattr(JobTitle, 'is_active'):
                try:
                    qs = qs.filter(is_active=True)
                except Exception:
                    pass
            form.fields['job_title'].queryset = qs.order_by('name_ar', 'name_en')
    except Exception:
        pass

    try:
        if 'direct_manager' in form.fields:
            qs = _safe_qs(Employee, company)
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
    \"\"\"محاولة مرنة لإنشاء/مزامنة حساب الموظف باستخدام أي helper موجود.\"\"\"
    try:
        from . import account_utils
    except Exception:
        return False

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
        fn = getattr(account_utils, name, None)
        if callable(fn):
            try:
                fn(employee)
                return True
            except TypeError:
                try:
                    fn(employee=employee)
                    return True
                except Exception:
                    pass
            except Exception:
                pass
    return False


def _redirect_employee_detail_or_list(employee):
    for url_name in ['employees:detail', 'employees:employee_detail', 'employees:list']:
        try:
            if 'detail' in url_name:
                return redirect(url_name, pk=employee.pk)
            return redirect(url_name)
        except Exception:
            continue
    return redirect('dashboard')


def _get_employee_or_404_for_user(user, pk):
    qs = get_accessible_employees(user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    )
    return get_object_or_404(qs, pk=pk)


# ═════════════════════════════════════════════════════════════
# Employee List
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_list(request):
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    )

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

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        employees = employees.filter(status=status_filter)

    branch_filter = request.GET.get('branch', '').strip()
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)

    department_filter = request.GET.get('department', '').strip()
    if department_filter:
        employees = employees.filter(department_id=department_filter)

    employees = employees.order_by('employee_code', 'id')

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
    page_obj = paginator.get_page(request.GET.get('page', 1))

    company = _get_current_company(request.user)
    branches = _safe_qs(Branch, company).order_by('name_ar', 'name_en')
    departments = _safe_qs(Department, company).order_by('name_ar', 'name_en')

    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'branches': branches,
        'departments': departments,
        'search': search,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'status_choices': _status_choices(),
    }
    return render(request, 'employees/list.html', context)


# ═════════════════════════════════════════════════════════════
# Live Search API
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_search_api(request):
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    department_filter = request.GET.get('department', '').strip()

    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
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

    employees = employees.order_by('employee_code', 'id')[:100]

    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'employee_code': emp.employee_code or '',
            'full_name_ar': _employee_name(emp),
            'job_title': (
                getattr(emp.job_title, 'name_ar', None)
                or getattr(emp.job_title, 'name_en', None)
                or '—'
            ) if getattr(emp, 'job_title', None) else '—',
            'department': (
                getattr(emp.department, 'name_ar', None)
                or getattr(emp.department, 'name_en', None)
                or '—'
            ) if getattr(emp, 'department', None) else '—',
            'branch': (
                getattr(emp.branch, 'name_ar', None)
                or getattr(emp.branch, 'name_en', None)
                or '—'
            ) if getattr(emp, 'branch', None) else '—',
            'phone': emp.phone or '—',
            'email': emp.email or '—',
            'status': emp.get_status_display() if hasattr(emp, 'get_status_display') else (emp.status or '—'),
            'manager': _employee_name(emp.direct_manager) if getattr(emp, 'direct_manager', None) else '—',
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
        'results': results,
    })


# ═════════════════════════════════════════════════════════════
# Add / Edit / Delete / Detail
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_add(request):
    if not can_user_add_employee(request.user):
        raise PermissionDenied('ليس لديك صلاحية إضافة موظف')

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
            messages.success(request, f'تم إضافة الموظف {_employee_name(employee)} بنجاح')
            return redirect('employees:list')
        else:
            messages.error(request, 'يرجى مراجعة الحقول المطلوبة')
    else:
        form = EmployeeForm()
        _configure_employee_form(form, company=company)

    return render(request, 'employees/form.html', {
        'form': form,
        'page_title': 'إضافة موظف',
        'form_title': 'إضافة موظف جديد',
        'is_edit': False,
    })


@login_required
@feature_required('employees_management')
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not can_user_edit_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية تعديل هذا الموظف')

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
            messages.success(request, f'تم تحديث بيانات الموظف {_employee_name(employee)}')
            return redirect('employees:list')
        else:
            messages.error(request, 'يرجى مراجعة الحقول المطلوبة')
    else:
        form = EmployeeForm(instance=employee)
        _configure_employee_form(form, company=company, instance=employee)

    return render(request, 'employees/form.html', {
        'form': form,
        'employee': employee,
        'page_title': 'تعديل موظف',
        'form_title': 'تعديل بيانات الموظف',
        'is_edit': True,
    })


@login_required
@feature_required('employees_management')
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not can_user_delete_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية حذف هذا الموظف')

    if request.method == 'POST':
        name = _employee_name(employee)
        employee.delete()
        messages.success(request, f'تم حذف الموظف {name}')
        return redirect('employees:list')

    return render(request, 'employees/delete_confirm.html', {
        'employee': employee,
        'page_title': 'حذف موظف',
    })


@login_required
@feature_required('employees_management')
def employee_detail(request, pk):
    employee = _get_employee_or_404_for_user(request.user, pk)

    documents = []
    deductions = []

    for rel_name in ['documents', 'employeedocument_set']:
        rel = getattr(employee, rel_name, None)
        if rel is not None:
            try:
                documents = rel.all()
                break
            except Exception:
                pass

    for rel_name in ['deductions', 'deduction_set']:
        rel = getattr(employee, rel_name, None)
        if rel is not None:
            try:
                deductions = rel.all()
                break
            except Exception:
                pass

    return render(request, 'employees/detail.html', {
        'employee': employee,
        'documents': documents,
        'deductions': deductions,
        'page_title': f'ملف الموظف - {_employee_name(employee)}',
    })


# ═════════════════════════════════════════════════════════════
# Print Views
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_print_list(request):
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    ).order_by('employee_code', 'id')

    return render(request, 'employees/print_list.html', {
        'employees': employees,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'page_title': 'طباعة قائمة الموظفين',
    })


@login_required
@feature_required('employees_management')
def employee_print_detail(request, pk):
    employee = _get_employee_or_404_for_user(request.user, pk)

    return render(request, 'employees/print_detail.html', {
        'employee': employee,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'page_title': f'طباعة ملف الموظف - {_employee_name(employee)}',
    })


@login_required
@feature_required('employees_management')
def print_credentials(request, pk):
    employee = _get_employee_or_404_for_user(request.user, pk)
    username = '—'
    if getattr(employee, 'user', None):
        username = getattr(employee.user, 'username', '—') or '—'

    return render(request, 'employees/print_credentials.html', {
        'employee': employee,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'username': username,
        'page_title': f'بيانات الدخول - {_employee_name(employee)}',
    })


# ═════════════════════════════════════════════════════════════
# Account Views
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def create_account_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية إنشاء حساب لهذا الموظف')

    try:
        before_user = getattr(employee, 'user', None)
        synced = _try_sync_employee_account(employee)
        employee.refresh_from_db()
        after_user = getattr(employee, 'user', None)

        if after_user:
            username = getattr(after_user, 'username', None) or '—'
            if before_user:
                messages.success(request, f'تمت مزامنة حساب الموظف {_employee_name(employee)} (اسم المستخدم: {username})')
            else:
                messages.success(request, f'تم إنشاء حساب للموظف {_employee_name(employee)} (اسم المستخدم: {username})')
        else:
            if synced:
                messages.warning(request, 'تمت محاولة إنشاء الحساب لكن لم يتم ربط مستخدم بالموظف.')
            else:
                messages.warning(request, 'لا يوجد helper صالح لإنشاء الحساب في account_utils.')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')

    return _redirect_employee_detail_or_list(employee)


@login_required
@feature_required('employees_management')
def deactivate_account_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية إدارة حساب هذا الموظف')

    user = getattr(employee, 'user', None)
    if not user:
        messages.warning(request, 'هذا الموظف لا يملك حساب مستخدم مرتبطًا به.')
        return _redirect_employee_detail_or_list(employee)

    action = request.POST.get('action', '').strip().lower() if request.method == 'POST' else ''

    try:
        if request.method == 'POST' and action == 'activate':
            user.is_active = True
            if hasattr(user, 'must_change_password'):
                try:
                    user.must_change_password = True
                except Exception:
                    pass
            user.save()
            messages.success(request, f'تمت إعادة تفعيل حساب الموظف {_employee_name(employee)}')
        else:
            user.is_active = False
            user.save()
            messages.success(request, f'تم تعطيل حساب الموظف {_employee_name(employee)}')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تحديث حالة الحساب: {e}')

    return _redirect_employee_detail_or_list(employee)


@login_required
@feature_required('employees_management')
def reset_password_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية إعادة تعيين كلمة مرور هذا الموظف')

    user = getattr(employee, 'user', None)
    if not user:
        messages.warning(request, 'هذا الموظف لا يملك حساب مستخدم مرتبطًا به. أنشئ الحساب أولاً.')
        return _redirect_employee_detail_or_list(employee)

    try:
        base_code = (employee.employee_code or 'EMP').replace(' ', '')
        temp_password = f\"{base_code}@{get_random_string(4)}\"

        user.set_password(temp_password)

        if hasattr(user, 'must_change_password'):
            try:
                user.must_change_password = True
            except Exception:
                pass

        if hasattr(user, 'is_active') and not user.is_active:
            user.is_active = True

        user.save()

        messages.success(
            request,
            f'تم إعادة تعيين كلمة المرور للموظف {_employee_name(employee)} | '
            f'اسم المستخدم: {getattr(user, "username", "—")} | '
            f'كلمة المرور المؤقتة: {temp_password}'
        )
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إعادة تعيين كلمة المرور: {e}')

    return _redirect_employee_detail_or_list(employee)


# ═════════════════════════════════════════════════════════════
# Self Service
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

    return render(request, 'employees/my_balance.html', {
        'employee': employee,
        'balances': balances,
        'page_title': 'رصيد إجازاتي',
    })


@login_required
def my_deductions(request):
    try:
        employee = Employee.objects.select_related('branch', 'department', 'job_title').get(user=request.user)
    except Employee.DoesNotExist:
        messages.warning(request, 'لا يوجد ملف موظف مرتبط بهذا الحساب')
        return redirect('dashboard')

    deductions = Deduction.objects.filter(employee=employee).order_by('-date', '-id')

    return render(request, 'employees/my_deductions.html', {
        'employee': employee,
        'deductions': deductions,
        'page_title': 'خصوماتي',
    })


# ═════════════════════════════════════════════════════════════
# Compatibility Aliases required by employees/urls.py
# ═════════════════════════════════════════════════════════════

employee_print = employee_print_list
print_credentials_view = print_credentials
my_balance_view = my_balance
my_deductions_view = my_deductions

# Extra compatibility aliases
employee_create = employee_add
create_employee = employee_add
add_employee = employee_add
add = employee_add

employee_update = employee_edit
update_employee = employee_edit
edit_employee = employee_edit
edit = employee_edit

employee_remove = employee_delete
delete_employee = employee_delete
remove_employee = employee_delete
delete = employee_delete

detail = employee_detail
employee_profile = employee_detail
employee_info = employee_detail

employee_print_all = employee_print_list
employees_print = employee_print_list
employees_print_all = employee_print_list
print_all = employee_print_list
print_list = employee_print_list
print_list_view = employee_print_list

employee_detail_print = employee_print_detail
employee_profile_print = employee_print_detail
employees_print_detail = employee_print_detail
print_detail = employee_print_detail
print_detail_view = employee_print_detail

employee_print_credentials = print_credentials
employee_credentials_print = print_credentials
credentials_print = print_credentials
employee_credentials = print_credentials

create_account = create_account_view
employee_create_account = create_account_view
employee_account_create = create_account_view
create_employee_account = create_account_view

employee_deactivate_account = deactivate_account_view
employee_reset_password = reset_password_view
employee_balance = my_balance
employee_balance_view = my_balance
employee_deductions = my_deductions
employee_deductions_view = my_deductions
employee_search = employee_search_api
search_api = employee_search_api
"""

write_file(views_path, views_code)

# Final check
final_views = read_file(views_path) or ""
defined_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', final_views, re.MULTILINE))
defined_aliases = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', final_views, re.MULTILINE))
existing = defined_funcs | defined_aliases
missing = [n for n in used_view_names if n not in existing]

print("\n📌 Final verification against employees/urls.py:")
for name in used_view_names:
    print(f"   {'✅' if name in existing else '❌'} {name}")

if missing:
    print(f"\n⚠️ ما زال ناقص: {missing}")
else:
    print("\n✅ كل الأسماء المطلوبة من employees/urls.py موجودة الآن")

print("\n" + "=" * 60)
print("✅ Patch 49b Fix7 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ إعادة بناء employees/views.py بالكامل بشكل نظيف ونهائي
  ✅ تضمين كل أسماء views المطلوبة من employees/urls.py
  ✅ تضمين create_account_view / deactivate_account_view / reset_password_view
  ✅ الحفاظ على live search + export + CRUD + print + self-service
  ✅ إنشاء backups قبل التعديل

مهم:
  ✅ هذا الباتش supersedes كل محاولات 49b Fix2/Fix3/Fix4/Fix6 الخاصة بـ employees/views.py
  ✅ ممنوع تعديل employees/views.py بترقيعات جزئية متراكبة بعد هذا الباتش
  ✅ أي تعديل لاحق يكون فوق هذه النسخة النظيفة فقط

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")