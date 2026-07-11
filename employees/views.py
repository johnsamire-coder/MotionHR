from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.crypto import get_random_string

from .models import (
    Employee, JobTitle, Deduction,
    JobHierarchyLevel, DepartmentJobTitleRule,
)
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
    if not employee:
        return '—'
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


def _can_manage_hierarchy(user):
    role = getattr(user, 'role', '') or ''
    return role in ['company_admin', 'hr_manager'] or is_admin_or_hr(user)


# ═════════════════════════════════════════════════════════════
# Hierarchy ranking helpers
# ═════════════════════════════════════════════════════════════

def _job_title_text(job_title):
    if not job_title:
        return ''
    return f"{getattr(job_title, 'name_ar', '')} {getattr(job_title, 'name_en', '')}".strip().lower()


def _job_title_explicit_rank(job_title):
    """
    لو موديل JobTitle فيه level/rank/order فعلي نستخدمه
    الأقل = أعلى
    """
    if not job_title:
        return None
    for attr in ['level', 'rank', 'sort_order', 'hierarchy_level', 'order', 'priority']:
        if hasattr(job_title, attr):
            try:
                val = getattr(job_title, attr)
                if val is not None and str(val).strip() != '':
                    return int(val)
            except Exception:
                pass
    return None


def _job_title_rank_from_keywords(job_title):
    """
    fallback heuristic لو لم تُضبط القواعد بعد
    الأقل = أعلى
    """
    text = _job_title_text(job_title)
    if not text:
        return 6

    groups = [
        (1, ['owner', 'founder', 'chairman', 'ceo', 'president', 'مالك', 'مؤسس', 'رئيس تنفيذي', 'صاحب الشركة', 'رئيس مجلس']),
        (2, ['general manager', 'executive director', 'managing director', 'chief', 'مدير عام', 'مدير تنفيذي', 'مدير قطاع', 'رئيس قطاع']),
        (3, ['manager', 'department head', 'branch manager', 'مدير', 'رئيس قسم']),
        (4, ['supervisor', 'team lead', 'lead', 'coordinator', 'مشرف', 'قائد فريق', 'منسق']),
        (5, ['senior', 'specialist', 'officer', 'executive', 'analyst', 'accountant', 'engineer', 'consultant', 'أخصائي', 'مسؤول', 'تنفيذي', 'محاسب', 'مهندس', 'محلل', 'استشاري']),
        (6, ['employee', 'staff', 'associate', 'assistant', 'representative', 'clerk', 'technician', 'administrator', 'موظف', 'مساعد', 'مندوب', 'فني', 'إداري']),
        (7, ['worker', 'labor', 'driver', 'intern', 'trainee', 'helper', 'عامل', 'سائق', 'متدرب']),
    ]
    for rank, keywords in groups:
        for kw in keywords:
            if kw in text:
                return rank
    return 6


def _job_title_hierarchy_rank(job_title):
    explicit = _job_title_explicit_rank(job_title)
    if explicit is not None:
        return explicit
    return _job_title_rank_from_keywords(job_title)


def _user_role_rank(user):
    role = getattr(user, 'role', '') if user else ''
    mapping = {
        'company_admin': 1,
        'hr_manager': 3,
        'manager': 3,
        'employee': 6,
    }
    return mapping.get(role, 6)


def _employee_hierarchy_rank(employee):
    title_rank = _job_title_hierarchy_rank(getattr(employee, 'job_title', None))
    role_rank = _user_role_rank(getattr(employee, 'user', None))
    return min(title_rank, role_rank)


def _get_selected_job_title(form=None, instance=None):
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


def _get_selected_department(form=None, instance=None):
    selected_department = None
    selected_department_id = None

    try:
        if form is not None and hasattr(form, 'data'):
            selected_department_id = form.data.get('department') or None
    except Exception:
        selected_department_id = None

    if selected_department_id:
        try:
            selected_department = Department.objects.get(pk=selected_department_id)
        except Exception:
            selected_department = None

    if not selected_department and instance is not None:
        selected_department = getattr(instance, 'department', None)

    return selected_department


def _get_manager_candidates_queryset(company=None, instance=None, selected_job_title=None, selected_department=None):
    """
    الأولوية:
    1) لو فيه Rule صريح للإدارة + المسمى الوظيفي → نعتمده
    2) لو لا → fallback heuristic
    """
    base_qs = _safe_qs(Employee, company).select_related('user', 'job_title', 'department')

    try:
        base_qs = base_qs.filter(status='active')
    except Exception:
        pass

    if instance and instance.pk:
        base_qs = base_qs.exclude(pk=instance.pk)

    if not selected_job_title:
        return base_qs.none()

    current_manager_id = getattr(instance, 'direct_manager_id', None) if instance else None

    # ── Rule-based selection ────────────────────────────────
    if company and selected_department:
        try:
            rule = DepartmentJobTitleRule.objects.select_related('level', 'parent_job_title').get(
                company=company,
                department=selected_department,
                job_title=selected_job_title,
                is_active=True,
            )
        except DepartmentJobTitleRule.DoesNotExist:
            rule = None

        if rule:
            scoped_qs = base_qs
            if rule.same_department_only:
                scoped_qs = scoped_qs.filter(department=selected_department)

            # parent exact title
            if rule.parent_job_title:
                exact_qs = scoped_qs.filter(job_title=rule.parent_job_title)
                if exact_qs.exists():
                    candidate_ids = list(exact_qs.values_list('id', flat=True))
                    if current_manager_id and current_manager_id not in candidate_ids:
                        candidate_ids.append(current_manager_id)
                    return base_qs.filter(id__in=candidate_ids).distinct().order_by('employee_code', 'id')

            # fallback to any higher level titles from same configured rules
            if rule.allow_higher_parent_fallback:
                higher_rules = DepartmentJobTitleRule.objects.filter(
                    company=company,
                    is_active=True,
                    level__sort_order__lt=rule.level.sort_order
                )
                if rule.same_department_only:
                    higher_rules = higher_rules.filter(department=selected_department)

                higher_title_ids = list(higher_rules.values_list('job_title_id', flat=True).distinct())
                if higher_title_ids:
                    higher_qs = scoped_qs.filter(job_title_id__in=higher_title_ids)
                    if higher_qs.exists():
                        candidate_ids = list(higher_qs.values_list('id', flat=True))
                        if current_manager_id and current_manager_id not in candidate_ids:
                            candidate_ids.append(current_manager_id)
                        return base_qs.filter(id__in=candidate_ids).distinct().order_by('employee_code', 'id')

            # لو القاعدة موجودة لكن لم نجد مرشحين
            if current_manager_id:
                return base_qs.filter(id=current_manager_id)
            return base_qs.none()

    # ── Heuristic fallback ──────────────────────────────────
    selected_rank = _job_title_hierarchy_rank(selected_job_title)
    candidate_ids = []

    for emp in base_qs:
        emp_rank = _employee_hierarchy_rank(emp)
        if emp_rank < selected_rank:
            candidate_ids.append(emp.id)

    if current_manager_id and current_manager_id not in candidate_ids:
        candidate_ids.append(current_manager_id)

    if not candidate_ids:
        return base_qs.none()

    return base_qs.filter(id__in=candidate_ids).distinct().order_by('employee_code', 'id')


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
            selected_department = _get_selected_department(form=form, instance=instance)

            qs = _get_manager_candidates_queryset(
                company=company,
                instance=instance,
                selected_job_title=selected_job_title,
                selected_department=selected_department,
            )
            form.fields['direct_manager'].queryset = qs

            try:
                if not selected_department and not selected_job_title:
                    form.fields['direct_manager'].empty_label = 'اختر الإدارة والمسمى الوظيفي أولًا'
                elif selected_job_title and not selected_department:
                    form.fields['direct_manager'].empty_label = 'اختر الإدارة أولًا'
                elif selected_department and not selected_job_title:
                    form.fields['direct_manager'].empty_label = 'اختر المسمى الوظيفي أولًا'
                elif qs.exists():
                    form.fields['direct_manager'].empty_label = 'اختر المدير المباشر المناسب'
                else:
                    form.fields['direct_manager'].empty_label = 'لا يوجد مدير أعلى مناسب حاليًا'
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
    for url_name in ['employees:detail', 'employees:list']:
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
# Job Hierarchy Management
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def job_hierarchy_manage(request):
    company = _get_current_company(request.user)
    if not company:
        messages.error(request, 'لا يمكن تحديد الشركة الحالية.')
        return redirect('employees:list')

    if not _can_manage_hierarchy(request.user):
        raise PermissionDenied('ليس لديك صلاحية إدارة الهيكل الوظيفي')

    departments = Department.objects.filter(company=company).order_by('name_ar', 'name_en')
    job_titles = JobTitle.objects.filter(company=company).order_by('name_ar', 'name_en')
    levels = JobHierarchyLevel.objects.filter(company=company).order_by('sort_order', 'id')

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        # ── Add level ────────────────────────────────────────
        if action == 'add_level':
            name_ar = (request.POST.get('name_ar') or '').strip()
            name_en = (request.POST.get('name_en') or '').strip()
            sort_order = (request.POST.get('sort_order') or '').strip()
            description = (request.POST.get('description') or '').strip()
            is_active = bool(request.POST.get('is_active'))

            if not name_ar:
                messages.error(request, 'اسم المستوى بالعربي مطلوب')
                return redirect('employees:hierarchy_manage')

            try:
                sort_order = int(sort_order)
            except Exception:
                messages.error(request, 'الترتيب الهرمي يجب أن يكون رقمًا صحيحًا')
                return redirect('employees:hierarchy_manage')

            try:
                JobHierarchyLevel.objects.create(
                    company=company,
                    name_ar=name_ar,
                    name_en=name_en,
                    sort_order=sort_order,
                    description=description,
                    is_active=is_active,
                )
                messages.success(request, f'تم إضافة المستوى الوظيفي: {name_ar}')
            except Exception as e:
                messages.error(request, f'تعذر إضافة المستوى الوظيفي: {e}')
            return redirect('employees:hierarchy_manage')

        # ── Delete level ─────────────────────────────────────
        if action == 'delete_level':
            level_id = request.POST.get('level_id')
            level = get_object_or_404(JobHierarchyLevel, pk=level_id, company=company)
            if DepartmentJobTitleRule.objects.filter(company=company, level=level).exists():
                messages.error(request, 'لا يمكن حذف هذا المستوى لأنه مستخدم في قواعد الربط')
            else:
                level_name = level.name_ar
                level.delete()
                messages.success(request, f'تم حذف المستوى: {level_name}')
            return redirect('employees:hierarchy_manage')

        # ── Save rule (upsert) ───────────────────────────────
        if action == 'save_rule':
            department_id = (request.POST.get('department_id') or '').strip()
            job_title_id = (request.POST.get('job_title_id') or '').strip()
            level_id = (request.POST.get('level_id') or '').strip()
            parent_job_title_id = (request.POST.get('parent_job_title_id') or '').strip()
            same_department_only = bool(request.POST.get('same_department_only'))
            allow_higher_parent_fallback = bool(request.POST.get('allow_higher_parent_fallback'))
            is_active = bool(request.POST.get('rule_is_active'))
            notes = (request.POST.get('notes') or '').strip()

            if not department_id or not job_title_id or not level_id:
                messages.error(request, 'الإدارة + المسمى الوظيفي + المستوى الوظيفي حقول مطلوبة')
                return redirect('employees:hierarchy_manage')

            department = get_object_or_404(Department, pk=department_id, company=company)
            job_title = get_object_or_404(JobTitle, pk=job_title_id, company=company)
            level = get_object_or_404(JobHierarchyLevel, pk=level_id, company=company)

            parent_job_title = None
            if parent_job_title_id:
                parent_job_title = get_object_or_404(JobTitle, pk=parent_job_title_id, company=company)

            if parent_job_title and parent_job_title.id == job_title.id:
                messages.error(request, 'لا يمكن أن يكون المسمى الوظيفي هو نفسه المسمى الأعلى المباشر')
                return redirect('employees:hierarchy_manage')

            try:
                rule, created = DepartmentJobTitleRule.objects.update_or_create(
                    company=company,
                    department=department,
                    job_title=job_title,
                    defaults={
                        'level': level,
                        'parent_job_title': parent_job_title,
                        'same_department_only': same_department_only,
                        'allow_higher_parent_fallback': allow_higher_parent_fallback,
                        'is_active': is_active,
                        'notes': notes,
                    }
                )
                if created:
                    messages.success(request, f'تم إنشاء قاعدة ربط لـ {job_title.name_ar} داخل {department.name_ar}')
                else:
                    messages.success(request, f'تم تحديث قاعدة الربط لـ {job_title.name_ar} داخل {department.name_ar}')
            except Exception as e:
                messages.error(request, f'تعذر حفظ القاعدة: {e}')

            return redirect('employees:hierarchy_manage')

        # ── Delete rule ──────────────────────────────────────
        if action == 'delete_rule':
            rule_id = request.POST.get('rule_id')
            rule = get_object_or_404(DepartmentJobTitleRule, pk=rule_id, company=company)
            title_name = getattr(rule.job_title, 'name_ar', 'القاعدة')
            dept_name = getattr(rule.department, 'name_ar', 'الإدارة')
            rule.delete()
            messages.success(request, f'تم حذف قاعدة الربط: {title_name} / {dept_name}')
            return redirect('employees:hierarchy_manage')

    rules = DepartmentJobTitleRule.objects.filter(company=company).select_related(
        'department', 'job_title', 'level', 'parent_job_title'
    ).order_by('department__name_ar', 'level__sort_order', 'job_title__name_ar')

    return render(request, 'employees/job_hierarchy_manage.html', {
        'page_title': 'إدارة الهيكل الوظيفي',
        'departments': departments,
        'job_titles': job_titles,
        'levels': levels,
        'rules': rules,
    })


# ═════════════════════════════════════════════════════════════
# Manager Options API
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_manager_options_api(request):
    company = _get_current_company(request.user)
    if not company:
        return JsonResponse({
            'success': False,
            'count': 0,
            'results': [],
            'message': 'لا يمكن تحديد الشركة الحالية',
        })

    job_title_id = (request.GET.get('job_title_id') or '').strip()
    department_id = (request.GET.get('department_id') or '').strip()
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
            selected_job_title = JobTitle.objects.get(pk=job_title_id, company=company)
        except Exception:
            selected_job_title = None

    selected_department = None
    if department_id:
        try:
            selected_department = Department.objects.get(pk=department_id, company=company)
        except Exception:
            selected_department = None

    if not selected_job_title and not selected_department:
        return JsonResponse({
            'success': True,
            'count': 0,
            'results': [],
            'message': 'اختر الإدارة والمسمى الوظيفي أولًا',
        })

    if not selected_department:
        return JsonResponse({
            'success': True,
            'count': 0,
            'results': [],
            'message': 'اختر الإدارة أولًا',
        })

    if not selected_job_title:
        return JsonResponse({
            'success': True,
            'count': 0,
            'results': [],
            'message': 'اختر المسمى الوظيفي أولًا',
        })

    qs = _get_manager_candidates_queryset(
        company=company,
        instance=instance,
        selected_job_title=selected_job_title,
        selected_department=selected_department,
    )

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
            'department': (
                getattr(emp.department, 'name_ar', None)
                or getattr(emp.department, 'name_en', None)
                or '—'
            ) if getattr(emp, 'department', None) else '—',
            'rank': _employee_hierarchy_rank(emp),
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
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
# Patch 49f — Employee Comprehensive Profile
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_comprehensive_profile(request, pk):
    """ملف شامل للموظف — كل البيانات في صفحة واحدة"""
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q

    employee = _get_employee_or_404_for_user(request.user, pk)
    company = _get_current_company(request.user)

    # ── البيانات الأساسية ──
    documents = []
    for rel_name in ['documents', 'employeedocument_set']:
        rel = getattr(employee, rel_name, None)
        if rel is not None:
            try:
                documents = list(rel.all()[:20])
                break
            except Exception:
                pass

    # ── الخصومات ──
    deductions_qs = Deduction.objects.filter(employee=employee).order_by('-date', '-id')
    deductions = list(deductions_qs[:20])
    total_deductions = deductions_qs.aggregate(total=Sum('amount'))['total'] or 0

    # ── الحضور ──
    attendance_data = {}
    try:
        from attendance.models import Attendance
        today = date.today()
        month_start = today.replace(day=1)

        att_qs = Attendance.objects.filter(employee=employee)
        att_month = att_qs.filter(date__gte=month_start, date__lte=today)

        attendance_data = {
            'total_records': att_qs.count(),
            'month_present': att_month.filter(status='present').count(),
            'month_late': att_month.filter(status='late').count(),
            'month_absent': att_month.filter(status='absent').count(),
            'month_leave': att_month.filter(status='on_leave').count(),
            'total_late_minutes': att_qs.aggregate(total=Sum('late_minutes'))['total'] or 0,
            'recent_records': list(att_qs.order_by('-date')[:10]),
        }
    except Exception:
        pass

    # ── التأخيرات ──
    late_incidents = []
    try:
        from attendance.models import LateIncident
        late_incidents = list(
            LateIncident.objects.filter(employee=employee).order_by('-date')[:10]
        )
    except Exception:
        pass

    # ── الإنذارات ──
    disciplinary_actions = []
    try:
        from attendance.models import DisciplinaryAction
        disciplinary_actions = list(
            DisciplinaryAction.objects.filter(employee=employee).order_by('-date')[:10]
        )
    except Exception:
        pass

    # ── الإجازات ──
    leave_data = {}
    try:
        from leaves.models import LeaveRequest, LeaveBalance
        leave_requests = list(
            LeaveRequest.objects.filter(employee=employee).select_related('leave_type').order_by('-start_date')[:10]
        )
        leave_balances = list(
            LeaveBalance.objects.filter(employee=employee).select_related('leave_type')
        )
        leave_data = {
            'requests': leave_requests,
            'balances': leave_balances,
            'total_requests': LeaveRequest.objects.filter(employee=employee).count(),
        }
    except Exception:
        pass

    # ── الطلبات ──
    employee_requests = []
    try:
        from requests_app.models import EmployeeRequest
        employee_requests = list(
            EmployeeRequest.objects.filter(employee=employee).select_related('request_type').order_by('-created_at')[:10]
        )
    except Exception:
        pass

    # ── الإشعارات ──
    notifications = []
    try:
        from accounts.models import EmployeeNotification
        notifications = list(
            EmployeeNotification.objects.filter(recipient=employee.user).order_by('-created_at')[:10]
        )
    except Exception:
        pass

    context = {
        'employee': employee,
        'documents': documents,
        'deductions': deductions,
        'total_deductions': total_deductions,
        'attendance_data': attendance_data,
        'late_incidents': late_incidents,
        'disciplinary_actions': disciplinary_actions,
        'leave_data': leave_data,
        'employee_requests': employee_requests,
        'notifications': notifications,
        'page_title': f'الملف الشامل - {_employee_name(employee)}',
    }
    return render(request, 'employees/comprehensive_profile.html', context)




# ═════════════════════════════════════════════════════════════
# Patch 49i — Employee Folder / Document Management
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_folder(request, pk):
    """عرض كل مستندات الموظف"""
    from .models import EmployeeFolder

    employee = _get_employee_or_404_for_user(request.user, pk)
    company = _get_current_company(request.user)

    documents = EmployeeFolder.objects.filter(
        employee=employee
    ).order_by('-created_at')

    # تصنيف حسب الكاتيجوري
    categories = {}
    for doc in documents:
        cat_name = doc.get_category_display()
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(doc)

    context = {
        'employee': employee,
        'documents': documents,
        'categories': categories,
        'total_docs': documents.count(),
        'page_title': f'ملف مستندات — {_employee_name(employee)}',
    }
    return render(request, 'employees/employee_folder.html', context)


@login_required
@feature_required('employees_management')
def employee_folder_upload(request, pk):
    """رفع مستند جديد لملف الموظف"""
    from .models import EmployeeFolder

    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية رفع مستندات لهذا الموظف')

    company = _get_current_company(request.user)

    if request.method == 'POST':
        category = (request.POST.get('category') or 'other').strip()
        custom_name = (request.POST.get('custom_name') or '').strip()
        related_event = (request.POST.get('related_event') or '').strip()
        event_date = request.POST.get('event_date') or None
        event_notes = (request.POST.get('event_notes') or '').strip()
        issue_date = request.POST.get('issue_date') or None
        expiry_date = request.POST.get('expiry_date') or None
        is_confidential = bool(request.POST.get('is_confidential'))
        notes = (request.POST.get('notes') or '').strip()
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            messages.error(request, 'يرجى اختيار ملف للرفع')
            return redirect('employees:folder', pk=employee.pk)

        # لو الكاتيجوري = other ولازم يكون فيه اسم مخصص
        if category == 'other' and not custom_name:
            custom_name = uploaded_file.name

        try:
            from datetime import date as dt_date
            if event_date:
                event_date = dt_date.fromisoformat(event_date)
            if issue_date:
                issue_date = dt_date.fromisoformat(issue_date)
            if expiry_date:
                expiry_date = dt_date.fromisoformat(expiry_date)
        except Exception:
            event_date = None
            issue_date = None
            expiry_date = None

        try:
            doc = EmployeeFolder(
                company=company,
                employee=employee,
                category=category,
                custom_name=custom_name,
                related_event=related_event,
                event_date=event_date,
                event_notes=event_notes,
                file=uploaded_file,
                issue_date=issue_date,
                expiry_date=expiry_date,
                is_confidential=is_confidential,
                notes=notes,
                uploaded_by=request.user,
            )
            doc.save()
            messages.success(request, f'تم رفع المستند: {doc.display_name}')
        except Exception as e:
            messages.error(request, f'تعذر رفع المستند: {e}')

        return redirect('employees:folder', pk=employee.pk)

    # GET
    category_choices = EmployeeFolder.DOCUMENT_CATEGORIES
    event_choices = EmployeeFolder.RELATED_EVENTS

    context = {
        'employee': employee,
        'category_choices': category_choices,
        'event_choices': event_choices,
        'page_title': f'رفع مستند — {_employee_name(employee)}',
    }
    return render(request, 'employees/employee_folder_upload.html', context)


@login_required
@feature_required('employees_management')
def employee_folder_delete(request, pk, doc_id):
    """حذف مستند"""
    from .models import EmployeeFolder

    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية حذف مستندات هذا الموظف')

    doc = get_object_or_404(EmployeeFolder, pk=doc_id, employee=employee)

    if request.method == 'POST':
        doc_name = doc.display_name
        doc.delete()
        messages.success(request, f'تم حذف المستند: {doc_name}')

    return redirect('employees:folder', pk=employee.pk)


# ═════════════════════════════════════════════════════════════
# Compatibility Aliases
# ═════════════════════════════════════════════════════════════

employee_print = employee_print_list
print_credentials_view = print_credentials
my_balance_view = my_balance
my_deductions_view = my_deductions

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
comprehensive_profile = employee_comprehensive_profile
folder = employee_folder
folder_upload = employee_folder_upload
folder_delete = employee_folder_delete
