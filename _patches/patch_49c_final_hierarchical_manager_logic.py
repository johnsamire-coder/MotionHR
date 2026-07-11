"""
Patch 49c Final — Hierarchical Direct Manager Logic

الهدف:
1) direct_manager يعتمد على مستوى المسمى الوظيفي Hierarchy
2) كلما كان المسمى أقل → قائمة المدراء أكبر
3) كلما كان المسمى أعلى → قائمة المدراء أقل
4) تحديث القائمة Live عند تغيير job_title
5) الحفاظ على Smart Wizard UX لفورم الموظف

هذا الباتش supersedes أي Patch 49c قديم خاص بفلترة المدير المباشر
"""

import os
import re
import shutil

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
print("Patch 49c Final — Hierarchical Direct Manager Logic")
print("=" * 60)

views_path = "employees/views.py"
urls_path = "employees/urls.py"
template_path = "templates/employees/form.html"

views_full = os.path.join(BASE_DIR, views_path)
urls_full = os.path.join(BASE_DIR, urls_path)

if not os.path.exists(views_full):
    raise SystemExit("❌ ملف employees/views.py غير موجود")
if not os.path.exists(urls_full):
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

shutil.copy2(views_full, os.path.join(backup_dir, "employees_views_before_patch_49c_final.py.bak"))
print("✅ Backup created: _patches/_backups/employees_views_before_patch_49c_final.py.bak")

shutil.copy2(urls_full, os.path.join(backup_dir, "employees_urls_before_patch_49c_final.py.bak"))
print("✅ Backup created: _patches/_backups/employees_urls_before_patch_49c_final.py.bak")

if os.path.exists(os.path.join(BASE_DIR, template_path)):
    shutil.copy2(
        os.path.join(BASE_DIR, template_path),
        os.path.join(backup_dir, "employees_form_before_patch_49c_final.html.bak")
    )
    print("✅ Backup created: _patches/_backups/employees_form_before_patch_49c_final.html.bak")

# ────────────────────────────────────────────────────────────
# Step 1: Rewrite employees/views.py cleanly with hierarchy logic
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: تحديث employees/views.py بمنطق hierarchy الحقيقي")

views_code = r'''from django.shortcuts import render, redirect, get_object_or_404
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


# ═════════════════════════════════════════════════════════════
# Hierarchy Logic
# ═════════════════════════════════════════════════════════════

def _job_title_text(job_title):
    if not job_title:
        return ''
    return (
        f"{getattr(job_title, 'name_ar', '')} {getattr(job_title, 'name_en', '')}"
    ).strip().lower()


def _job_title_explicit_rank(job_title):
    """
    لو فيه level/rank/order في الموديل نستخدمه
    أصغر رقم = منصب أعلى
    """
    if not job_title:
        return None

    for attr in ['level', 'rank', 'sort_order', 'hierarchy_level', 'order', 'priority']:
        if hasattr(job_title, attr):
            try:
                value = getattr(job_title, attr)
                if value is not None and str(value).strip() != '':
                    return int(value)
            except Exception:
                pass
    return None


def _job_title_rank_from_keywords(job_title):
    """
    استنتاج المستوى من اسم المسمى الوظيفي
    الرقم الأصغر = أعلى في الهرم
    """
    text = _job_title_text(job_title)

    if not text:
        return 6

    keyword_groups = [
        # 1 = الأعلى جدًا
        (1, [
            'owner', 'founder', 'chairman', 'ceo', 'chief executive', 'president',
            'vice president', 'co-founder',
            'مالك', 'مؤسس', 'رئيس مجلس', 'رئيس تنفيذي', 'العضو المنتدب', 'صاحب الشركة'
        ]),
        # 2 = إدارة عليا
        (2, [
            'general manager', 'gm', 'executive director', 'director general',
            'managing director', 'head of sector', 'sector head', 'chief',
            'مدير عام', 'مدير تنفيذي', 'رئيس قطاع', 'مدير قطاع', 'رئيس إدارة'
        ]),
        # 3 = مدير
        (3, [
            'manager', 'department head', 'branch manager',
            'مدير', 'رئيس قسم'
        ]),
        # 4 = إشراف / قيادة فريق
        (4, [
            'supervisor', 'team lead', 'lead', 'coordinator',
            'مشرف', 'قائد فريق', 'منسق'
        ]),
        # 5 = مستوى متوسط
        (5, [
            'senior', 'specialist', 'officer', 'executive', 'analyst',
            'accountant', 'engineer', 'consultant',
            'أخصائي', 'مسؤول', 'تنفيذي', 'محاسب', 'مهندس', 'محلل', 'استشاري'
        ]),
        # 6 = موظف عادي / مساعد
        (6, [
            'employee', 'staff', 'associate', 'assistant', 'representative',
            'clerk', 'technician', 'administrator',
            'موظف', 'مساعد', 'مندوب', 'فني', 'إداري', 'كاتب'
        ]),
        # 7 = أقل مستوى
        (7, [
            'worker', 'labor', 'driver', 'intern', 'trainee', 'helper',
            'عامل', 'سائق', 'متدرب'
        ]),
    ]

    for rank, keywords in keyword_groups:
        for kw in keywords:
            if kw in text:
                return rank

    return 6


def _job_title_hierarchy_rank(job_title):
    explicit_rank = _job_title_explicit_rank(job_title)
    if explicit_rank is not None:
        return explicit_rank
    return _job_title_rank_from_keywords(job_title)


def _user_role_rank(user):
    role = getattr(user, 'role', '') or ''
    mapping = {
        'company_admin': 1,
        'hr_manager': 3,
        'manager': 3,
        'employee': 6,
    }
    return mapping.get(role, 6)


def _employee_hierarchy_rank(employee):
    """
    نأخذ الأعلى رتبة بين:
    - المسمى الوظيفي
    - role
    باستخدام أقل رقم = أعلى
    """
    title_rank = _job_title_hierarchy_rank(getattr(employee, 'job_title', None))
    role_rank = _user_role_rank(getattr(employee, 'user', None))
    return min(title_rank, role_rank)


def _get_selected_job_title(form=None, instance=None):
    """
    تحديد job_title الحالي:
    - من POST data لو الفورم bound
    - وإلا من instance في التعديل
    """
    selected_job_title = None
    selected_job_title_id = None

    try:
        if form is not None and hasattr(form, 'data'):
            selected_job_title_id = form.data.get('job_title') or None
    except Exception:
        selected_job_title_id = None

    if selected_job_title_id:
        try:
            selected_job_title = JobTitle.objects.get(pk=selected_job_title_id)
        except Exception:
            selected_job_title = None

    if not selected_job_title and instance is not None:
        selected_job_title = getattr(instance, 'job_title', None)

    return selected_job_title


def _get_manager_candidates_queryset(company=None, instance=None, selected_job_title=None):
    """
    منطق المدير المباشر الصحيح:
    - المدير المباشر يجب أن يكون أعلى من المسمى الوظيفي الحالي
    - كلما كان المسمى أقل → عدد المدراء المحتملين يزيد
    - كلما كان المسمى أعلى → القائمة تضيق
    """
    base_qs = _safe_qs(Employee, company).select_related('user', 'job_title')

    try:
        base_qs = base_qs.filter(status='active')
    except Exception:
        pass

    if instance and instance.pk:
        base_qs = base_qs.exclude(pk=instance.pk)

    if not selected_job_title:
        return base_qs.none()

    selected_rank = _job_title_hierarchy_rank(selected_job_title)

    eligible_ids = []
    current_manager_id = getattr(instance, 'direct_manager_id', None) if instance else None

    for emp in base_qs:
        emp_rank = _employee_hierarchy_rank(emp)
        if emp_rank < selected_rank:
            eligible_ids.append(emp.id)

    if current_manager_id and current_manager_id not in eligible_ids:
        eligible_ids.append(current_manager_id)

    if not eligible_ids:
        return base_qs.filter(pk__in=[])

    return base_qs.filter(pk__in=eligible_ids).distinct().order_by('employee_code', 'id')


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
            selected_job_title = _get_selected_job_title(form=form, instance=instance)
            manager_qs = _get_manager_candidates_queryset(
                company=company,
                instance=instance,
                selected_job_title=selected_job_title
            )
            form.fields['direct_manager'].queryset = manager_qs

            try:
                if selected_job_title:
                    if manager_qs.exists():
                        form.fields['direct_manager'].empty_label = 'اختر المدير المباشر المناسب للمستوى'
                    else:
                        form.fields['direct_manager'].empty_label = 'لا يوجد مدير أعلى مناسب لهذا المستوى'
                else:
                    form.fields['direct_manager'].empty_label = 'اختر المسمى الوظيفي أولًا'
            except Exception:
                pass
    except Exception:
        pass


def _try_sync_employee_account(employee):
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
# Manager Options API
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_manager_options_api(request):
    """
    API ترجع المديرين المحتملين حسب المسمى الوظيفي المختار
    """
    company = _get_current_company(request.user)
    job_title_id = (request.GET.get('job_title_id') or '').strip()
    employee_id = (request.GET.get('employee_id') or '').strip()

    instance = None
    if employee_id:
        try:
            instance = Employee.objects.get(pk=employee_id)
        except Exception:
            instance = None

    selected_job_title = None
    if job_title_id:
        try:
            selected_job_title = JobTitle.objects.get(pk=job_title_id)
        except Exception:
            selected_job_title = None

    if not selected_job_title:
        return JsonResponse({
            'success': True,
            'count': 0,
            'selected_rank': None,
            'results': [],
            'message': 'اختر المسمى الوظيفي أولًا',
        })

    qs = _get_manager_candidates_queryset(
        company=company,
        instance=instance,
        selected_job_title=selected_job_title
    )

    selected_rank = _job_title_hierarchy_rank(selected_job_title)

    results = []
    for emp in qs[:200]:
        results.append({
            'id': emp.id,
            'name': _employee_name(emp),
            'employee_code': emp.employee_code or '',
            'job_title': (
                getattr(emp.job_title, 'name_ar', None)
                or getattr(emp.job_title, 'name_en', None)
                or '—'
            ) if getattr(emp, 'job_title', None) else '—',
            'rank': _employee_hierarchy_rank(emp),
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
        'selected_rank': selected_rank,
        'results': results,
        'message': 'تم تحميل المديرين المحتملين بنجاح',
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
        temp_password = f"{base_code}@{get_random_string(4)}"

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
manager_options_api = employee_manager_options_api
'''

write_file(views_path, views_code)

# ────────────────────────────────────────────────────────────
# Step 2: Update employees/urls.py with manager options API
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إضافة route للـ manager options API")

urls_content = read_file(urls_path)
manager_route = "    path('api/manager-options/', views.employee_manager_options_api, name='manager_options_api'),"

if "name='manager_options_api'" not in urls_content and 'name="manager_options_api"' not in urls_content:
    if "urlpatterns = [" in urls_content:
        urls_content = urls_content.replace(
            "urlpatterns = [",
            "urlpatterns = [\n" + manager_route,
            1
        )
        write_file(urls_path, urls_content)
        print("✅ تم إضافة employees:manager_options_api")
    else:
        print("⚠️ لم أتمكن من حقن route بشكل تلقائي")
else:
    print("ℹ️ route manager_options_api موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 3: Rewrite employee form template with Smart Wizard + live manager hierarchy
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: تحديث templates/employees/form.html")

form_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title|default:"إضافة موظف" }}{% endblock %}

{% block extra_css %}
<style>
  .wizard-shell { border: 1px solid #e2e8f0; border-radius: 20px; background: linear-gradient(180deg, #ffffff 0%, #f8fdff 100%); }
  .wizard-stepper { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
  .wizard-step { border: 1px solid #dbeafe; background: #fff; border-radius: 16px; padding: 14px 12px; cursor: pointer; transition: .2s ease; min-height: 88px; }
  .wizard-step:hover { border-color: #06B6D4; transform: translateY(-1px); }
  .wizard-step.active { background: #06B6D4; border-color: #06B6D4; color: white; box-shadow: 0 10px 24px rgba(6,182,212,.18); }
  .wizard-step.done { background: #ecfeff; border-color: #67e8f9; }
  .wizard-step-number { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; background: rgba(6,182,212,.12); color: #0891b2; margin-bottom: 10px; }
  .wizard-step.active .wizard-step-number { background: rgba(255,255,255,.18); color: #fff; }
  .wizard-step-title { font-weight: 800; font-size: .95rem; margin-bottom: 3px; }
  .wizard-step-note { font-size: .78rem; opacity: .85; }
  .wizard-panel { display: none; }
  .wizard-panel.active { display: block; animation: fadePanel .18s ease; }
  @keyframes fadePanel { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
  .section-card { border: 1px solid #e2e8f0; border-radius: 18px; overflow: hidden; }
  .section-head { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 14px 18px; }
  .section-head h6 { margin: 0; font-weight: 800; }
  .section-head small { color: #64748b; }
  .field-box { margin-bottom: 1rem; }
  .field-box label { display: block; margin-bottom: .45rem; font-weight: 700; color: #0f172a; }
  .field-box .required-star { color: #dc2626; margin-right: 4px; }
  .field-box .errorlist { list-style: none; padding: 0; margin: .35rem 0 0; color: #dc2626; font-size: .82rem; }
  .wizard-actions { position: sticky; bottom: 0; background: #fff; border-top: 1px solid #e2e8f0; padding: 16px 0 0; margin-top: 24px; }
  .wizard-status { border: 1px dashed #cbd5e1; background: #f8fafc; border-radius: 14px; padding: 12px 14px; }
  .wizard-status .status-title { font-weight: 800; margin-bottom: 6px; }
  .missing-list { margin: 0; padding-right: 18px; }
  .missing-list li { margin-bottom: 4px; }
  .field-invalid { border-color: #dc2626 !important; box-shadow: 0 0 0 .2rem rgba(220,38,38,.08) !important; }
  .form-check-wrap { border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; background: #fff; }
  .mini-note { color: #64748b; font-size: .8rem; }
  .hierarchy-note { border: 1px solid #bae6fd; background: #f0f9ff; border-radius: 14px; padding: 12px 14px; color: #0c4a6e; font-size: .88rem; }
  .hierarchy-note strong { color: #075985; }
  @media (max-width: 991.98px) { .wizard-stepper { grid-template-columns: 1fr; } }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold">
        <i class="bi bi-person-plus-fill text-primary me-2"></i>{{ form_title|default:"إضافة موظف جديد" }}
      </h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item"><a href="{% url 'employees:list' %}">الموظفون</a></li>
          <li class="breadcrumb-item active">{{ form_title|default:"إضافة موظف جديد" }}</li>
        </ol>
      </nav>
    </div>
    <div>
      <a href="{% url 'employees:list' %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-right-circle me-1"></i>العودة للقائمة
      </a>
    </div>
  </div>

  {% if form.errors %}
  <div class="alert alert-danger border-0 shadow-sm">
    <div class="fw-bold mb-2">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>يوجد حقول مطلوبة أو بيانات غير صحيحة:
    </div>
    <ul class="mb-0">
      {% for field in form %}
        {% for error in field.errors %}
          <li><strong>{{ field.label }}:</strong> {{ error }}</li>
        {% endfor %}
      {% endfor %}
      {% for error in form.non_field_errors %}
        <li>{{ error }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  <div class="card border-0 shadow-sm wizard-shell">
    <div class="card-body p-4">

      <div class="wizard-stepper mb-4" id="wizard-stepper">
        <div class="wizard-step active" data-step="1">
          <div class="wizard-step-number">1</div>
          <div class="wizard-step-title">البيانات الأساسية</div>
          <div class="wizard-step-note">الاسم والهوية والبيانات الشخصية</div>
        </div>
        <div class="wizard-step" data-step="2">
          <div class="wizard-step-number">2</div>
          <div class="wizard-step-title">التواصل</div>
          <div class="wizard-step-note">الهاتف والعنوان والطوارئ</div>
        </div>
        <div class="wizard-step" data-step="3">
          <div class="wizard-step-number">3</div>
          <div class="wizard-step-title">بيانات التعيين</div>
          <div class="wizard-step-note">الفرع والإدارة والوظيفة والمدير</div>
        </div>
        <div class="wizard-step" data-step="4">
          <div class="wizard-step-number">4</div>
          <div class="wizard-step-title">المالية والتأمين</div>
          <div class="wizard-step-note">الراتب والبنك والتأمين</div>
        </div>
        <div class="wizard-step" data-step="5">
          <div class="wizard-step-number">5</div>
          <div class="wizard-step-title">الحضور والتتبع</div>
          <div class="wizard-step-note">الحضور والتتبع والموظف الميداني</div>
        </div>
      </div>

      <div class="wizard-status mb-4" id="wizard-status-box">
        <div class="status-title">
          <i class="bi bi-info-circle-fill text-primary me-1"></i>
          الخطوة الحالية: <span id="current-step-title">البيانات الأساسية</span>
        </div>
        <div class="mini-note">لا يمكن الانتقال للخطوة التالية إلا بعد استكمال الحقول الإلزامية في الخطوة الحالية.</div>
        <div id="missing-fields-box" class="mt-2" style="display:none;">
          <div class="fw-bold text-danger mb-1">الحقول الناقصة:</div>
          <ul class="missing-list text-danger" id="missing-fields-list"></ul>
        </div>
      </div>

      <form method="post" enctype="multipart/form-data" id="employeeWizardForm" novalidate>
        {% csrf_token %}
        {% for hidden in form.hidden_fields %}{{ hidden }}{% endfor %}

        <!-- STEP 1 -->
        <div class="wizard-panel active" data-step-panel="1">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-person-vcard me-2 text-primary"></i>البيانات الأساسية</h6>
              <small>أدخل هوية الموظف الأساسية والبيانات الشخصية</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.employee_code %}<div class="col-md-4 field-box">{{ form.employee_code.label_tag }}{{ form.employee_code }}{{ form.employee_code.errors }}</div>{% endif %}
                {% if form.first_name_ar %}<div class="col-md-4 field-box">{{ form.first_name_ar.label_tag }}{{ form.first_name_ar }}{{ form.first_name_ar.errors }}</div>{% endif %}
                {% if form.middle_name_ar %}<div class="col-md-4 field-box">{{ form.middle_name_ar.label_tag }}{{ form.middle_name_ar }}{{ form.middle_name_ar.errors }}</div>{% endif %}
                {% if form.last_name_ar %}<div class="col-md-4 field-box">{{ form.last_name_ar.label_tag }}{{ form.last_name_ar }}{{ form.last_name_ar.errors }}</div>{% endif %}
                {% if form.first_name_en %}<div class="col-md-4 field-box">{{ form.first_name_en.label_tag }}{{ form.first_name_en }}{{ form.first_name_en.errors }}</div>{% endif %}
                {% if form.last_name_en %}<div class="col-md-4 field-box">{{ form.last_name_en.label_tag }}{{ form.last_name_en }}{{ form.last_name_en.errors }}</div>{% endif %}
                {% if form.national_id %}<div class="col-md-4 field-box">{{ form.national_id.label_tag }}{{ form.national_id }}{{ form.national_id.errors }}</div>{% endif %}
                {% if form.birth_date %}<div class="col-md-4 field-box">{{ form.birth_date.label_tag }}{{ form.birth_date }}{{ form.birth_date.errors }}</div>{% endif %}
                {% if form.gender %}<div class="col-md-4 field-box">{{ form.gender.label_tag }}{{ form.gender }}{{ form.gender.errors }}</div>{% endif %}
                {% if form.marital_status %}<div class="col-md-4 field-box">{{ form.marital_status.label_tag }}{{ form.marital_status }}{{ form.marital_status.errors }}</div>{% endif %}
                {% if form.religion %}<div class="col-md-4 field-box">{{ form.religion.label_tag }}{{ form.religion }}{{ form.religion.errors }}</div>{% endif %}
                {% if form.nationality %}<div class="col-md-4 field-box">{{ form.nationality.label_tag }}{{ form.nationality }}{{ form.nationality.errors }}</div>{% endif %}
                {% if form.photo %}<div class="col-md-6 field-box">{{ form.photo.label_tag }}{{ form.photo }}{{ form.photo.errors }}</div>{% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 2 -->
        <div class="wizard-panel" data-step-panel="2">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-telephone-forward me-2 text-primary"></i>بيانات التواصل والطوارئ</h6>
              <small>بيانات الاتصال الأساسية ووسيلة التواصل في الحالات الطارئة</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.email %}<div class="col-md-4 field-box">{{ form.email.label_tag }}{{ form.email }}{{ form.email.errors }}</div>{% endif %}
                {% if form.phone %}<div class="col-md-4 field-box">{{ form.phone.label_tag }}{{ form.phone }}{{ form.phone.errors }}</div>{% endif %}
                {% if form.phone2 %}<div class="col-md-4 field-box">{{ form.phone2.label_tag }}{{ form.phone2 }}{{ form.phone2.errors }}</div>{% endif %}
                {% if form.city %}<div class="col-md-4 field-box">{{ form.city.label_tag }}{{ form.city }}{{ form.city.errors }}</div>{% endif %}
                {% if form.address %}<div class="col-md-8 field-box">{{ form.address.label_tag }}{{ form.address }}{{ form.address.errors }}</div>{% endif %}
                {% if form.emergency_contact_name %}<div class="col-md-4 field-box">{{ form.emergency_contact_name.label_tag }}{{ form.emergency_contact_name }}{{ form.emergency_contact_name.errors }}</div>{% endif %}
                {% if form.emergency_contact_relation %}<div class="col-md-4 field-box">{{ form.emergency_contact_relation.label_tag }}{{ form.emergency_contact_relation }}{{ form.emergency_contact_relation.errors }}</div>{% endif %}
                {% if form.emergency_contact_phone %}<div class="col-md-4 field-box">{{ form.emergency_contact_phone.label_tag }}{{ form.emergency_contact_phone }}{{ form.emergency_contact_phone.errors }}</div>{% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 3 -->
        <div class="wizard-panel" data-step-panel="3">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-briefcase-fill me-2 text-primary"></i>بيانات التعيين</h6>
              <small>الفرع والإدارة والمسمى الوظيفي والمدير المباشر</small>
            </div>
            <div class="p-4">
              <div class="hierarchy-note mb-3" id="managerHierarchyNote">
                <strong>منطق المدير المباشر:</strong>
                اختر المسمى الوظيفي أولًا، وبعدها النظام هيعرض لك فقط المدراء الأعلى المناسبين لهذا المستوى.
              </div>

              <div class="row">
                {% if form.hire_date %}<div class="col-md-4 field-box">{{ form.hire_date.label_tag }}{{ form.hire_date }}{{ form.hire_date.errors }}</div>{% endif %}
                {% if form.contract_type %}<div class="col-md-4 field-box">{{ form.contract_type.label_tag }}{{ form.contract_type }}{{ form.contract_type.errors }}</div>{% endif %}
                {% if form.contract_end_date %}<div class="col-md-4 field-box">{{ form.contract_end_date.label_tag }}{{ form.contract_end_date }}{{ form.contract_end_date.errors }}</div>{% endif %}

                {% if form.branch %}<div class="col-md-4 field-box">{{ form.branch.label_tag }}{{ form.branch }}{{ form.branch.errors }}</div>{% endif %}
                {% if form.department %}<div class="col-md-4 field-box">{{ form.department.label_tag }}{{ form.department }}{{ form.department.errors }}</div>{% endif %}
                {% if form.job_title %}<div class="col-md-4 field-box">{{ form.job_title.label_tag }}{{ form.job_title }}{{ form.job_title.errors }}</div>{% endif %}

                {% if form.direct_manager %}<div class="col-md-6 field-box">{{ form.direct_manager.label_tag }}{{ form.direct_manager }}{{ form.direct_manager.errors }}</div>{% endif %}
                {% if form.status %}<div class="col-md-3 field-box">{{ form.status.label_tag }}{{ form.status }}{{ form.status.errors }}</div>{% endif %}
                {% if form.termination_date %}<div class="col-md-3 field-box">{{ form.termination_date.label_tag }}{{ form.termination_date }}{{ form.termination_date.errors }}</div>{% endif %}
                {% if form.termination_reason %}<div class="col-md-12 field-box">{{ form.termination_reason.label_tag }}{{ form.termination_reason }}{{ form.termination_reason.errors }}</div>{% endif %}
                {% if form.notes %}<div class="col-md-12 field-box">{{ form.notes.label_tag }}{{ form.notes }}{{ form.notes.errors }}</div>{% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 4 -->
        <div class="wizard-panel" data-step-panel="4">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-cash-coin me-2 text-primary"></i>البيانات المالية والتأمين</h6>
              <small>الراتب وبيانات البنك والتأمينات</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.basic_salary %}<div class="col-md-4 field-box">{{ form.basic_salary.label_tag }}{{ form.basic_salary }}{{ form.basic_salary.errors }}</div>{% endif %}
                {% if form.bank_name %}<div class="col-md-4 field-box">{{ form.bank_name.label_tag }}{{ form.bank_name }}{{ form.bank_name.errors }}</div>{% endif %}
                {% if form.bank_account %}<div class="col-md-4 field-box">{{ form.bank_account.label_tag }}{{ form.bank_account }}{{ form.bank_account.errors }}</div>{% endif %}
                {% if form.iban %}<div class="col-md-4 field-box">{{ form.iban.label_tag }}{{ form.iban }}{{ form.iban.errors }}</div>{% endif %}
                {% if form.insurance_number %}<div class="col-md-4 field-box">{{ form.insurance_number.label_tag }}{{ form.insurance_number }}{{ form.insurance_number.errors }}</div>{% endif %}
                {% if form.insurance_date %}<div class="col-md-4 field-box">{{ form.insurance_date.label_tag }}{{ form.insurance_date }}{{ form.insurance_date.errors }}</div>{% endif %}

                {% if form.has_insurance %}
                <div class="col-md-12 field-box">
                  <label>{{ form.has_insurance.label }}</label>
                  <div class="form-check-wrap">
                    <div class="form-check">
                      {{ form.has_insurance }}
                      <label class="form-check-label ms-2" for="{{ form.has_insurance.id_for_label }}">
                        الموظف مشترك في التأمينات
                      </label>
                    </div>
                  </div>
                  {{ form.has_insurance.errors }}
                </div>
                {% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 5 -->
        <div class="wizard-panel" data-step-panel="5">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-fingerprint me-2 text-primary"></i>الحضور والتتبع</h6>
              <small>إعدادات الحضور ونمط العمل والتتبع</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.attendance_mode %}<div class="col-md-4 field-box">{{ form.attendance_mode.label_tag }}{{ form.attendance_mode }}{{ form.attendance_mode.errors }}</div>{% endif %}
                {% if form.required_daily_hours %}<div class="col-md-4 field-box">{{ form.required_daily_hours.label_tag }}{{ form.required_daily_hours }}{{ form.required_daily_hours.errors }}</div>{% endif %}

                {% if form.stealth_tracking_enabled %}
                <div class="col-md-6 field-box">
                  <label>{{ form.stealth_tracking_enabled.label }}</label>
                  <div class="form-check-wrap">
                    <div class="form-check">
                      {{ form.stealth_tracking_enabled }}
                      <label class="form-check-label ms-2" for="{{ form.stealth_tracking_enabled.id_for_label }}">
                        تفعيل التتبع الصامت لهذا الموظف
                      </label>
                    </div>
                  </div>
                  {{ form.stealth_tracking_enabled.errors }}
                </div>
                {% endif %}

                {% if form.is_field_worker %}
                <div class="col-md-6 field-box">
                  <label>{{ form.is_field_worker.label }}</label>
                  <div class="form-check-wrap">
                    <div class="form-check">
                      {{ form.is_field_worker }}
                      <label class="form-check-label ms-2" for="{{ form.is_field_worker.id_for_label }}">
                        موظف ميداني
                      </label>
                    </div>
                  </div>
                  {{ form.is_field_worker.errors }}
                </div>
                {% endif %}
              </div>
            </div>
          </div>
        </div>

        <div class="wizard-actions">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div class="mini-note">
              <i class="bi bi-lightbulb me-1 text-warning"></i>
              النظام سيمنعك من الانتقال لو الحقول الإلزامية في الخطوة الحالية غير مكتملة.
            </div>
            <div class="d-flex gap-2">
              <button type="button" class="btn btn-outline-secondary" id="prevStepBtn">
                <i class="bi bi-arrow-right me-1"></i>السابق
              </button>
              <button type="button" class="btn btn-primary" id="nextStepBtn">
                التالي<i class="bi bi-arrow-left ms-1"></i>
              </button>
              <button type="submit" class="btn btn-success" id="submitFormBtn" style="display:none;">
                <i class="bi bi-check2-circle me-1"></i>حفظ الموظف
              </button>
            </div>
          </div>
        </div>

      </form>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_js %}
<script>
(function() {
  const form = document.getElementById('employeeWizardForm');
  const stepButtons = Array.from(document.querySelectorAll('.wizard-step'));
  const panels = Array.from(document.querySelectorAll('.wizard-panel'));
  const prevBtn = document.getElementById('prevStepBtn');
  const nextBtn = document.getElementById('nextStepBtn');
  const submitBtn = document.getElementById('submitFormBtn');
  const currentStepTitle = document.getElementById('current-step-title');
  const missingBox = document.getElementById('missing-fields-box');
  const missingList = document.getElementById('missing-fields-list');

  let currentStep = 1;

  const stepMeta = {
    1: 'البيانات الأساسية',
    2: 'التواصل',
    3: 'بيانات التعيين',
    4: 'المالية والتأمين',
    5: 'الحضور والتتبع'
  };

  function bootstrapizeFields() {
    document.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.type === 'hidden') return;
      if (el.type === 'checkbox') {
        el.classList.add('form-check-input');
        return;
      }
      if (el.tagName === 'SELECT') {
        el.classList.add('form-select');
      } else {
        el.classList.add('form-control');
      }
    });

    document.querySelectorAll('.field-box label').forEach(label => {
      const box = label.closest('.field-box');
      if (!box) return;
      const input = box.querySelector('input, select, textarea');
      if (!input) return;

      if (input.required && !label.querySelector('.required-star')) {
        const star = document.createElement('span');
        star.className = 'required-star';
        star.textContent = '*';
        label.appendChild(star);
      }
    });
  }

  function getPanel(step) {
    return document.querySelector('.wizard-panel[data-step-panel="' + step + '"]');
  }

  function getVisibleRequiredInputs(step) {
    const panel = getPanel(step);
    if (!panel) return [];

    return Array.from(panel.querySelectorAll('input, select, textarea')).filter(el => {
      if (el.disabled) return false;
      if (el.type === 'hidden') return false;
      if (!el.required) return false;
      if (el.offsetParent === null) return false;
      return true;
    });
  }

  function clearInvalid(step) {
    const panel = getPanel(step);
    if (!panel) return;
    panel.querySelectorAll('.field-invalid').forEach(el => el.classList.remove('field-invalid'));
  }

  function getLabelText(input) {
    const box = input.closest('.field-box');
    if (box) {
      const label = box.querySelector('label');
      if (label) {
        return label.textContent.replace('*', '').trim();
      }
    }
    return input.getAttribute('placeholder') || input.name || 'حقل مطلوب';
  }

  function validateStep(step, focusFirst=true) {
    clearInvalid(step);
    const requiredInputs = getVisibleRequiredInputs(step);
    const missing = [];
    let firstInvalid = null;

    requiredInputs.forEach(input => {
      let valid = true;

      if (input.type === 'checkbox') {
        valid = input.checked;
      } else if (input.tagName === 'SELECT') {
        valid = !!String(input.value || '').trim();
      } else {
        valid = input.checkValidity() && !!String(input.value || '').trim();
      }

      if (!valid) {
        input.classList.add('field-invalid');
        const label = getLabelText(input);
        if (!missing.includes(label)) missing.push(label);
        if (!firstInvalid) firstInvalid = input;
      }
    });

    if (missing.length) {
      missingBox.style.display = 'block';
      missingList.innerHTML = missing.map(item => '<li>' + item + '</li>').join('');
      if (focusFirst && firstInvalid) firstInvalid.focus();
      return false;
    }

    missingBox.style.display = 'none';
    missingList.innerHTML = '';
    return true;
  }

  function updateStepper() {
    stepButtons.forEach(btn => {
      const step = parseInt(btn.dataset.step, 10);
      btn.classList.remove('active', 'done');
      if (step === currentStep) btn.classList.add('active');
      else if (step < currentStep) btn.classList.add('done');
    });

    panels.forEach(panel => {
      const step = parseInt(panel.dataset.stepPanel, 10);
      panel.classList.toggle('active', step === currentStep);
    });

    currentStepTitle.textContent = stepMeta[currentStep] || 'الخطوة الحالية';
    prevBtn.style.visibility = currentStep === 1 ? 'hidden' : 'visible';
    nextBtn.style.display = currentStep === panels.length ? 'none' : 'inline-block';
    submitBtn.style.display = currentStep === panels.length ? 'inline-block' : 'none';
  }

  function goToStep(step) {
    if (step < 1 || step > panels.length) return;
    currentStep = step;
    updateStepper();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  prevBtn.addEventListener('click', function() {
    if (currentStep > 1) {
      missingBox.style.display = 'none';
      goToStep(currentStep - 1);
    }
  });

  nextBtn.addEventListener('click', function() {
    if (validateStep(currentStep)) goToStep(currentStep + 1);
  });

  stepButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      const target = parseInt(btn.dataset.step, 10);
      if (target < currentStep) {
        missingBox.style.display = 'none';
        goToStep(target);
        return;
      }
      if (target === currentStep) return;
      if (validateStep(currentStep)) goToStep(target);
    });
  });

  form.addEventListener('submit', function(e) {
    for (let step = 1; step <= panels.length; step++) {
      const ok = validateStep(step, false);
      if (!ok) {
        e.preventDefault();
        goToStep(step);
        validateStep(step, true);
        return;
      }
    }
  });

  bootstrapizeFields();
  updateStepper();
})();
</script>

<script>
(function() {
  const jobTitleSelect = document.querySelector('[name="job_title"]');
  const directManagerSelect = document.querySelector('[name="direct_manager"]');
  const noteBox = document.getElementById('managerHierarchyNote');
  const employeeId = "{{ employee.id|default:'' }}";

  if (!jobTitleSelect || !directManagerSelect) return;

  directManagerSelect.dataset.originalRequired = directManagerSelect.required ? '1' : '0';

  function setNote(html) {
    if (noteBox) noteBox.innerHTML = html;
  }

  function disableManagerSelect(placeholderText) {
    const currentVal = directManagerSelect.value || '';
    directManagerSelect.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = placeholderText || 'اختر المسمى الوظيفي أولًا';
    directManagerSelect.appendChild(opt);
    directManagerSelect.disabled = true;
    directManagerSelect.required = false;
    directManagerSelect.value = '';
  }

  function enableManagerSelect() {
    directManagerSelect.disabled = false;
    if (directManagerSelect.dataset.originalRequired === '1') {
      directManagerSelect.required = true;
    }
  }

  function renderManagers(items, keepValue) {
    directManagerSelect.innerHTML = '';

    const first = document.createElement('option');
    first.value = '';
    first.textContent = 'اختر المدير المباشر';
    directManagerSelect.appendChild(first);

    items.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = `${item.name} — ${item.job_title}`;
      if (String(keepValue || '') === String(item.id)) {
        opt.selected = true;
      }
      directManagerSelect.appendChild(opt);
    });
  }

  function loadManagerOptions() {
    const jobTitleId = (jobTitleSelect.value || '').trim();
    const keepValue = directManagerSelect.value || '';

    if (!jobTitleId) {
      disableManagerSelect('اختر المسمى الوظيفي أولًا');
      setNote('<strong>منطق المدير المباشر:</strong> اختر المسمى الوظيفي أولًا، وبعدها النظام هيعرض لك فقط المدراء الأعلى المناسبين لهذا المستوى.');
      return;
    }

    setNote('<strong>جارٍ التحليل:</strong> يتم الآن تحديد المديرين الأعلى المناسبين لهذا المسمى الوظيفي...');
    directManagerSelect.disabled = true;

    const params = new URLSearchParams({
      job_title_id: jobTitleId
    });

    if (employeeId) {
      params.append('employee_id', employeeId);
    }

    fetch("{% url 'employees:manager_options_api' %}?" + params.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
      const items = data.results || [];

      if (!items.length) {
        disableManagerSelect('لا يوجد مدير أعلى مناسب لهذا المستوى');
        setNote(
          '<strong>نتيجة التحليل:</strong> هذا المستوى الوظيفي مرتفع نسبيًا، لذلك لا يوجد مدير أعلى مناسب متاح حاليًا داخل نفس الشركة.'
        );
        return;
      }

      renderManagers(items, keepValue);
      enableManagerSelect();

      const rank = data.selected_rank;
      setNote(
        `<strong>نتيجة التحليل:</strong> تم العثور على <strong>${items.length}</strong> مدير/قائد أعلى مناسب ` +
        `لهذا المستوى الوظيفي` + (rank ? ` (مستوى: ${rank})` : '') + `.`
      );
    })
    .catch(() => {
      disableManagerSelect('تعذر تحميل المديرين المحتملين');
      setNote('<strong>تعذر التحليل:</strong> حدث خطأ أثناء تحميل قائمة المديرين المحتملين.');
    });
  }

  jobTitleSelect.addEventListener('change', loadManagerOptions);
  window.addEventListener('load', loadManagerOptions);
})();
</script>
{% endblock %}
"""

write_file(template_path, form_template)

# ────────────────────────────────────────────────────────────
# Final verification
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: Final verification")

urls_after = read_file(urls_path) or ""
views_after = read_file(views_path) or ""
used_view_names = sorted(set(re.findall(r'views\.([A-Za-z_][A-Za-z0-9_]*)', urls_after)))
defined_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', views_after, re.MULTILINE))
defined_aliases = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', views_after, re.MULTILINE))
existing = defined_funcs | defined_aliases
missing = [n for n in used_view_names if n not in existing]

for name in used_view_names:
    print(f"   {'✅' if name in existing else '❌'} {name}")

if missing:
    print(f"\n⚠️ ما زال ناقص: {missing}")
else:
    print("\n✅ كل أسماء views المطلوبة من employees/urls.py موجودة")

print("\n" + "=" * 60)
print("✅ Patch 49c Final اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ direct_manager أصبح Hierarchical حسب مستوى المسمى الوظيفي
  ✅ كلما انخفض مستوى المسمى زادت قائمة المدراء المحتملين
  ✅ كلما ارتفع مستوى المسمى ضاقت القائمة
  ✅ تم إضافة API ديناميكية لتحميل المديرين المحتملين Live
  ✅ تم تحديث فورم الموظف Smart Wizard
  ✅ تم الحفاظ على validation بين الخطوات
  ✅ تم إنشاء backups قبل التعديل

الملفات المعدلة:
  ✅ employees/views.py
  ✅ employees/urls.py
  ✅ templates/employees/form.html

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")