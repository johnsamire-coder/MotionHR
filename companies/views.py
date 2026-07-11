
WORK_DAYS = [
    ('work_sunday',    'الأحد',    'primary'),
    ('work_monday',    'الاثنين',  'primary'),
    ('work_tuesday',   'الثلاثاء', 'primary'),
    ('work_wednesday', 'الأربعاء', 'primary'),
    ('work_thursday',  'الخميس',  'primary'),
    ('work_friday',    'الجمعة',   'warning'),
    ('work_saturday',  'السبت',    'warning'),
]

"""
companies/views.py
صفحات إدارة الشركة والفروع والإدارات والشيفتات
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Company, Branch, Department
from attendance.models import Shift


# ════════════════════════════════════════════════════════════
# الشركة
# ════════════════════════════════════════════════════════════

@login_required
def company_settings(request):
    """إعدادات الشركة"""
    company = request.user.company
    if not company:
        messages.error(request, 'لا يوجد شركة مرتبطة بحسابك')
        return redirect('dashboard')

    if request.method == 'POST':
        company.name_ar           = request.POST.get('name_ar', company.name_ar)
        company.name_en           = request.POST.get('name_en', company.name_en)
        company.email             = request.POST.get('email', company.email)
        company.phone             = request.POST.get('phone', company.phone)
        company.address           = request.POST.get('address', company.address)
        company.website           = request.POST.get('website', company.website)
        company.commercial_register = request.POST.get('commercial_register', '')
        company.tax_number        = request.POST.get('tax_number', '')

        if 'logo' in request.FILES:
            company.logo = request.FILES['logo']

        company.save()
        messages.success(request, '✅ تم حفظ إعدادات الشركة بنجاح')
        return redirect('companies:settings')

    context = {
        'company':    company,
        'page_title': 'إعدادات الشركة',
    }
    return render(request, 'companies/settings.html', context)


# ════════════════════════════════════════════════════════════
# الفروع
# ════════════════════════════════════════════════════════════

@login_required
def branches_list(request):
    """قائمة الفروع"""
    company  = request.user.company
    branches = Branch.objects.filter(company=company).order_by('-is_main', 'name_ar')
    context  = {
        'branches':   branches,
        'page_title': 'الفروع',
    }
    return render(request, 'companies/branches_list.html', context)


@login_required
def branch_add(request):
    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
    """إضافة فرع جديد"""
    company = request.user.company

    if request.method == 'POST':
        branch = Branch(company=company)
        branch.name_ar        = request.POST.get('name_ar', '')
        branch.name_en        = request.POST.get('name_en', '')
        branch.address        = request.POST.get('address', '')
        branch.phone          = request.POST.get('phone', '')
        branch.is_main        = request.POST.get('is_main') == 'on'
        branch.is_active      = True

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        if lat:
            branch.latitude  = float(lat)
        if lng:
            branch.longitude = float(lng)

        radius = request.POST.get('check_in_radius', 100)
        branch.check_in_radius = int(radius) if radius else 100

        branch.save()
        messages.success(request, f'✅ تم إضافة الفرع "{branch.name_ar}" بنجاح')
        return redirect('companies:branches_list')

    context = {
        'page_title': 'إضافة فرع جديد',
        'action':     'add',
    }
    return render(request, 'companies/branch_form.html', context)


@login_required
def branch_edit(request, pk):
    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
    """تعديل فرع"""
    branch = get_object_or_404(Branch, pk=pk, company=request.user.company)

    if request.method == 'POST':
        branch.name_ar   = request.POST.get('name_ar', branch.name_ar)
        branch.name_en   = request.POST.get('name_en', branch.name_en)
        branch.address   = request.POST.get('address', branch.address)
        branch.phone     = request.POST.get('phone', branch.phone)
        branch.is_main   = request.POST.get('is_main') == 'on'
        branch.is_active = request.POST.get('is_active') == 'on'

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        if lat:
            branch.latitude  = float(lat)
        if lng:
            branch.longitude = float(lng)

        radius = request.POST.get('check_in_radius', 100)
        branch.check_in_radius = int(radius) if radius else 100

        branch.save()
        messages.success(request, f'✅ تم تحديث الفرع "{branch.name_ar}" بنجاح')
        return redirect('companies:branches_list')

    context = {
        'branch':     branch,
        'page_title': f'تعديل فرع: {branch.name_ar}',
        'action':     'edit',
    }
    return render(request, 'companies/branch_form.html', context)


@login_required
@require_POST
def branch_delete(request, pk):
    """حذف فرع"""
    branch = get_object_or_404(Branch, pk=pk, company=request.user.company)
    name   = branch.name_ar
    branch.delete()
    messages.success(request, f'✅ تم حذف الفرع "{name}"')
    return redirect('companies:branches_list')


# ════════════════════════════════════════════════════════════
# الإدارات
# ════════════════════════════════════════════════════════════

@login_required
def departments_list(request):
    """قائمة الإدارات"""
    company     = request.user.company
    departments = Department.objects.filter(
        company=company
    ).select_related('parent').order_by('parent__name_ar', 'name_ar')

    context = {
        'departments': departments,
        'page_title':  'الإدارات والأقسام',
    }
    return render(request, 'companies/departments_list.html', context)


@login_required
def department_add(request):
    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
    """إضافة إدارة جديدة"""
    company     = request.user.company
    departments = Department.objects.filter(company=company, is_active=True)

    if request.method == 'POST':
        dept         = Department(company=company)
        dept.name_ar = request.POST.get('name_ar', '')
        dept.name_en = request.POST.get('name_en', '')
        dept.code    = request.POST.get('code', '')
        dept.description = request.POST.get('description', '')
        dept.is_active   = True

        parent_id = request.POST.get('parent')
        if parent_id:
            dept.parent = get_object_or_404(Department, pk=parent_id, company=company)

        dept.save()
        messages.success(request, f'✅ تم إضافة الإدارة "{dept.name_ar}" بنجاح')
        return redirect('companies:departments_list')

    context = {
        'departments': departments,
        'page_title':  'إضافة إدارة جديدة',
        'action':      'add',
    }
    return render(request, 'companies/department_form.html', context)


@login_required
def department_edit(request, pk):
    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
    """تعديل إدارة"""
    company = request.user.company
    dept    = get_object_or_404(Department, pk=pk, company=company)
    departments = Department.objects.filter(
        company=company, is_active=True
    ).exclude(pk=pk)

    if request.method == 'POST':
        dept.name_ar     = request.POST.get('name_ar', dept.name_ar)
        dept.name_en     = request.POST.get('name_en', dept.name_en)
        dept.code        = request.POST.get('code', dept.code)
        dept.description = request.POST.get('description', dept.description)
        dept.is_active   = request.POST.get('is_active') == 'on'

        parent_id = request.POST.get('parent')
        if parent_id:
            dept.parent = get_object_or_404(Department, pk=parent_id, company=company)
        else:
            dept.parent = None

        dept.save()
        messages.success(request, f'✅ تم تحديث الإدارة "{dept.name_ar}" بنجاح')
        return redirect('companies:departments_list')

    context = {
        'dept':        dept,
        'departments': departments,
        'page_title':  f'تعديل: {dept.name_ar}',
        'action':      'edit',
    }
    return render(request, 'companies/department_form.html', context)


@login_required
@require_POST
def department_delete(request, pk):
    """حذف إدارة"""
    dept = get_object_or_404(Department, pk=pk, company=request.user.company)
    name = dept.name_ar
    dept.delete()
    messages.success(request, f'✅ تم حذف الإدارة "{name}"')
    return redirect('companies:departments_list')


# ════════════════════════════════════════════════════════════
# الشيفتات
# ════════════════════════════════════════════════════════════

@login_required
def shifts_list(request):
    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
    """قائمة الشيفتات"""
    company = request.user.company
    shifts  = Shift.objects.filter(company=company).order_by('name')
    context = {
        'shifts':     shifts,
        'page_title': 'الشيفتات',
    }
    return render(request, 'companies/shifts_list.html', context)


@login_required
def shift_add(request):
    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
    """إضافة شيفت جديد"""
    company = request.user.company

    if request.method == 'POST':
        shift = Shift(company=company)
        shift.name        = request.POST.get('name', '')
        shift.shift_type  = request.POST.get('shift_type', 'fixed')
        shift.start_time  = request.POST.get('start_time', '08:00')
        shift.end_time    = request.POST.get('end_time',   '17:00')
        shift.grace_period   = int(request.POST.get('grace_period', 15))
        shift.break_duration = int(request.POST.get('break_duration', 60))

        # أيام العمل
        shift.work_sunday    = 'work_sunday'    in request.POST
        shift.work_monday    = 'work_monday'    in request.POST
        shift.work_tuesday   = 'work_tuesday'   in request.POST
        shift.work_wednesday = 'work_wednesday' in request.POST
        shift.work_thursday  = 'work_thursday'  in request.POST
        shift.work_friday    = 'work_friday'    in request.POST
        shift.work_saturday  = 'work_saturday'  in request.POST

        shift.save()
        messages.success(request, f'✅ تم إضافة الشيفت "{shift.name}" بنجاح')
        return redirect('companies:shifts_list')

    context = {
        'page_title': 'إضافة شيفت جديد',
        'action':     'add',
        'days':       WORK_DAYS,
    }
    return render(request, 'companies/shift_form.html', context)


@login_required
def shift_edit(request, pk):
    """تعديل شيفت"""
    shift = get_object_or_404(Shift, pk=pk, company=request.user.company)

    if request.method == 'POST':
        shift.name        = request.POST.get('name', shift.name)
        shift.shift_type  = request.POST.get('shift_type', shift.shift_type)
        shift.start_time  = request.POST.get('start_time', shift.start_time)
        shift.end_time    = request.POST.get('end_time',   shift.end_time)
        shift.grace_period   = int(request.POST.get('grace_period',   15))
        shift.break_duration = int(request.POST.get('break_duration', 60))

        shift.work_sunday    = 'work_sunday'    in request.POST
        shift.work_monday    = 'work_monday'    in request.POST
        shift.work_tuesday   = 'work_tuesday'   in request.POST
        shift.work_wednesday = 'work_wednesday' in request.POST
        shift.work_thursday  = 'work_thursday'  in request.POST
        shift.work_friday    = 'work_friday'    in request.POST
        shift.work_saturday  = 'work_saturday'  in request.POST

        shift.save()
        messages.success(request, f'✅ تم تحديث الشيفت "{shift.name}" بنجاح')
        return redirect('companies:shifts_list')

    context = {
        'shift':      shift,
        'page_title': f'تعديل: {shift.name}',
        'action':     'edit',
        'days':       WORK_DAYS,
    }
    return render(request, 'companies/shift_form.html', context)


@login_required
@require_POST
def shift_delete(request, pk):
    """حذف شيفت"""
    shift = get_object_or_404(Shift, pk=pk, company=request.user.company)
    name  = shift.name
    shift.delete()
    messages.success(request, f'✅ تم حذف الشيفت "{name}"')
    return redirect('companies:shifts_list')


# ════════════════════════════════════════════════════════════
# ميثاق العمل
# ════════════════════════════════════════════════════════════

@login_required
def charter_view(request):
    """عرض ميثاق العمل للموظف"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    company = request.user.company
    charter = None
    accepted = False
    employee = None

    if company:
        charter = WorkCharter.objects.filter(
            company=company, is_active=True
        ).first()

        employee = Employee.objects.filter(user=request.user).first()

        if charter and employee:
            accepted = CharterAcceptance.objects.filter(
                employee=employee, charter=charter
            ).exists()

    context = {
        "charter": charter,
        "accepted": accepted,
        "employee": employee,
        "page_title": "ميثاق العمل",
    }
    return render(request, "companies/charter_view.html", context)


@login_required
def charter_accept(request):
    """الموظف يوافق على الميثاق"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    if request.method != "POST":
        return redirect("companies:charter")

    company = request.user.company
    charter = WorkCharter.objects.filter(
        company=company, is_active=True
    ).first()

    employee = Employee.objects.filter(user=request.user).first()

    if charter and employee:
        CharterAcceptance.objects.get_or_create(
            employee=employee,
            charter=charter,
            defaults={
                "ip_address": request.META.get("REMOTE_ADDR", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
            }
        )
        messages.success(request, "تم تسجيل موافقتك على ميثاق العمل بنجاح")
    else:
        messages.error(request, "حدث خطأ")

    return redirect("dashboard")


@login_required
def charter_manage(request):
    """إدارة ميثاق العمل (لصاحب الشركة / HR)"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    company = request.user.company
    charter = None
    acceptances = []
    total_employees = 0
    accepted_count = 0

    if company:
        charter, created = WorkCharter.objects.get_or_create(
            company=company,
            defaults={
                "title": "ميثاق العمل",
                "content": _default_charter_content(),
                "introduction": "نرحب بانضمامك لفريق عملنا. يرجى قراءة ميثاق العمل التالي والموافقة عليه.",
                "is_active": True,
                "is_mandatory": True,
            }
        )

        if request.method == "POST":
            charter.title = request.POST.get("title", charter.title)
            charter.introduction = request.POST.get("introduction", "")
            charter.content = request.POST.get("content", charter.content)
            charter.is_active = "is_active" in request.POST
            charter.is_mandatory = "is_mandatory" in request.POST

            if "new_version" in request.POST:
                charter.version += 1

            charter.save()
            messages.success(request, "تم حفظ ميثاق العمل بنجاح")
            return redirect("companies:charter_manage")

        total_employees = Employee.objects.filter(
            company=company, status="active"
        ).count()

        acceptances = CharterAcceptance.objects.filter(
            charter=charter
        ).select_related("employee").order_by("-accepted_at")

        accepted_count = acceptances.count()

    context = {
        "charter": charter,
        "acceptances": acceptances,
        "total_employees": total_employees,
        "accepted_count": accepted_count,
        "not_accepted": total_employees - accepted_count,
        "page_title": "إدارة ميثاق العمل",
    }
    return render(request, "companies/charter_manage.html", context)


def _default_charter_content():
    return """1. الالتزام بمواعيد العمل الرسمية والحضور والانصراف في الأوقات المحددة.

2. الحفاظ على سرية بيانات الشركة والعملاء وعدم إفشائها لأي طرف خارجي.

3. احترام بيئة العمل والزملاء والتعامل بمهنية في جميع الأوقات.

4. عدم استخدام ممتلكات الشركة أو مواردها لأغراض شخصية.

5. الالتزام بسياسة الإجازات المعتمدة وتقديم الطلبات في الوقت المناسب.

6. الحفاظ على المظهر اللائق والالتزام بقواعد اللباس المعتمدة.

7. الإبلاغ الفوري عن أي مخالفات أو سلوكيات غير مقبولة.

8. الالتزام بقواعد السلامة والصحة المهنية.

9. عدم ممارسة أي عمل يتعارض مع مصالح الشركة.

10. الالتزام بالقوانين واللوائح المعمول بها في الشركة والدولة."""


# ════════════════════════════════════════════════════════════
# سياسات الشركة / HR Controls
# ════════════════════════════════════════════════════════════

@login_required
def company_policy_manage(request):
    """إدارة سياسات الشركة"""
    from .models import CompanyPolicy

    company = request.user.company
    if not company:
        messages.error(request, "لا يوجد شركة مرتبطة بحسابك")
        return redirect("dashboard")

    policy = CompanyPolicy.get_for_company(company)

    if request.method == "POST":
        # التأخير
        policy.grace_period_minutes = int(request.POST.get("grace_period_minutes", 15) or 15)
        policy.late_handling_mode = request.POST.get("late_handling_mode", "recommendation_only")
        policy.employee_can_view_late_count = "employee_can_view_late_count" in request.POST
        policy.employee_can_view_warnings = "employee_can_view_warnings" in request.POST
        policy.hr_override_reason_required = "hr_override_reason_required" in request.POST
        policy.reset_late_counter_monthly = "reset_late_counter_monthly" in request.POST
        policy.late_first_warning_after_count = int(request.POST.get("late_first_warning_after_count", 1) or 1)
        policy.late_second_warning_after_count = int(request.POST.get("late_second_warning_after_count", 2) or 2)
        policy.late_quarter_day_deduction_after_count = int(request.POST.get("late_quarter_day_deduction_after_count", 3) or 3)
        policy.late_half_day_deduction_after_count = int(request.POST.get("late_half_day_deduction_after_count", 4) or 4)
        policy.late_full_day_deduction_after_count = int(request.POST.get("late_full_day_deduction_after_count", 5) or 5)

        # الأذونات
        policy.permission_enabled = "permission_enabled" in request.POST
        policy.permission_monthly_limit = int(request.POST.get("permission_monthly_limit", 2) or 2)
        policy.permission_max_hours_per_request = request.POST.get("permission_max_hours_per_request", 2) or 2
        policy.permission_requires_approval = "permission_requires_approval" in request.POST

        # الأوفر تايم
        policy.overtime_enabled = "overtime_enabled" in request.POST
        policy.overtime_start_after_minutes = int(request.POST.get("overtime_start_after_minutes", 30) or 30)
        policy.overtime_requires_approval = "overtime_requires_approval" in request.POST
        policy.overtime_requires_reason = "overtime_requires_reason" in request.POST
        policy.overtime_daily_max_hours = request.POST.get("overtime_daily_max_hours", 4) or 4
        policy.overtime_monthly_max_hours = request.POST.get("overtime_monthly_max_hours", 40) or 40

        # الموقع
        policy.checkin_requires_location = "checkin_requires_location" in request.POST
        policy.checkin_requires_branch_range = "checkin_requires_branch_range" in request.POST
        policy.checkout_from_anywhere = "checkout_from_anywhere" in request.POST
        policy.default_checkin_radius = int(request.POST.get("default_checkin_radius", 200) or 200)
        policy.distance_tolerance_meters = int(request.POST.get("distance_tolerance_meters", 0) or 0)

        # الغياب
        policy.auto_absence_enabled = "auto_absence_enabled" in request.POST
        auto_absence_after_time = request.POST.get("auto_absence_after_time")
        if auto_absence_after_time:
            policy.auto_absence_after_time = auto_absence_after_time

        # صلاحيات HR
        policy.hr_can_cancel_attendance = "hr_can_cancel_attendance" in request.POST
        policy.hr_can_edit_attendance = "hr_can_edit_attendance" in request.POST
        policy.attendance_edit_reason_required = "attendance_edit_reason_required" in request.POST

        # الطلبات المالية
        policy.manager_can_see_financial_requests = "manager_can_see_financial_requests" in request.POST

        # سياسات الحضور الاستثنائي
        policy.off_day_checkin_mode = request.POST.get("off_day_checkin_mode", "allow_notify_hr")
        policy.leave_day_checkin_mode = request.POST.get("leave_day_checkin_mode", "block")
        policy.unplanned_checkin_mode = request.POST.get("unplanned_checkin_mode", "create_exception")

        policy.notes = request.POST.get("notes", "")

        policy.save()
        messages.success(request, "تم حفظ سياسات الشركة بنجاح")
        return redirect("companies:policies")

    context = {
        "policy": policy,
        "page_title": "السياسات والقواعد",
    }
    return render(request, "companies/policies.html", context)


def _stealth_tracking_clause_text():
    return (
        "تحتفظ الشركة بحق متابعة الأداء المهني والتحقق من الالتزام أثناء ساعات العمل "
        "من خلال وسائل التتبع المناسبة، وذلك في إطار تنظيم العمل وحماية مصالح الشركة، "
        "وبما لا يتعارض مع سياسات الشركة والأنظمة المعمول بها."
    )


def _ensure_stealth_clause(company):
    """
    لو التتبع الصامت مفعّل والبند مش موجود، نضيفه تلقائيًا للميثاق
    """
    try:
        from .models import CompanyPolicy, WorkCharter
        policy = CompanyPolicy.get_for_company(company)
        if not policy.stealth_tracking_enabled:
            return

        if not policy.stealth_tracking_requires_charter_clause:
            return

        charter, _ = WorkCharter.objects.get_or_create(
            company=company,
            defaults={
                "title": "ميثاق العمل",
                "introduction": "يرجى قراءة الميثاق والموافقة عليه.",
                "content": "",
                "version": 1,
                "is_active": True,
                "is_mandatory": True,
            }
        )

        clause = _stealth_tracking_clause_text()
        if clause not in (charter.content or ""):
            if charter.content.strip():
                charter.content = charter.content.strip() + "\n\n" + clause
            else:
                charter.content = clause
            charter.save()
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# Approval Flows Management
# ════════════════════════════════════════════════════════════

@login_required
def approval_flows_view(request):
    """إدارة مسارات الموافقة"""
    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    from requests_app.models import RequestType, ApprovalFlow

    company = request.user.company
    request_types = RequestType.objects.filter(
        company=company,
        is_active=True
    ).select_related("category")

    flows = ApprovalFlow.objects.filter(company=company)
    flows_map = {f.request_type_id: f for f in flows}

    if request.method == "POST":
        rt_id = request.POST.get("request_type")
        rt = get_object_or_404(RequestType, pk=rt_id, company=company)

        flow, _ = ApprovalFlow.objects.get_or_create(
            company=company,
            request_type=rt,
        )
        flow.step_1_role = request.POST.get("step_1_role", "direct_manager")
        flow.step_2_role = request.POST.get("step_2_role", "hr_manager")
        flow.step_3_role = request.POST.get("step_3_role", "skip")
        flow.escalation_enabled = "escalation_enabled" in request.POST
        flow.escalation_to = request.POST.get("escalation_to", "hr_manager")
        flow.notify_employee_on_each_step = "notify_employee" in request.POST
        flow.save()

        messages.success(request, f"تم حفظ مسار الموافقة لـ {rt.name}")
        return redirect("companies:approval_flows")

    context = {
        "request_types": request_types,
        "flows_map": flows_map,
        "page_title": "مسارات الموافقة",
    }
    return render(request, "companies/approval_flows.html", context)


# ════════════════════════════════════════════════════════════
# Approval Delegations Management
# ════════════════════════════════════════════════════════════

@login_required
def delegations_view(request):
    """إدارة التفويضات"""
    from requests_app.models import ApprovalDelegation
    from accounts.models import User

    company = request.user.company
    role = getattr(request.user, "role", "")

    delegations = ApprovalDelegation.objects.filter(
        company=company
    ).select_related("delegator", "delegate").order_by("-start_date")

    eligible_users = User.objects.filter(
        company=company,
        is_active=True,
        role__in=["manager", "hr_manager", "company_admin", "super_admin"]
    )

    context = {
        "delegations": delegations,
        "eligible_users": eligible_users,
        "page_title": "التفويضات",
    }
    return render(request, "companies/delegations.html", context)


@login_required
def delegation_add(request):
    """إضافة تفويض جديد"""
    from requests_app.models import ApprovalDelegation
    from accounts.models import User
    from datetime import date as dt_date

    company = request.user.company
    role = getattr(request.user, "role", "")

    eligible_users = User.objects.filter(
        company=company,
        is_active=True
    ).exclude(pk=request.user.pk)

    if request.method == "POST":
        delegate_id = request.POST.get("delegate")
        start_str = request.POST.get("start_date")
        end_str = request.POST.get("end_date")
        scope = request.POST.get("scope", "all_approvals")
        reason = request.POST.get("reason", "")

        if not delegate_id or not start_str or not end_str:
            messages.error(request, "جميع الحقول مطلوبة")
        else:
            delegate = get_object_or_404(User, pk=delegate_id, company=company)
            start_date = dt_date.fromisoformat(start_str)
            end_date = dt_date.fromisoformat(end_str)

            if end_date < start_date:
                messages.error(request, "تاريخ الانتهاء لازم يكون بعد البداية")
            else:
                ApprovalDelegation.objects.create(
                    company=company,
                    delegator=request.user,
                    delegate=delegate,
                    delegator_role=role,
                    start_date=start_date,
                    end_date=end_date,
                    scope=scope,
                    reason=reason,
                    is_active=True,
                )
                messages.success(
                    request,
                    f"تم إنشاء التفويض لـ {delegate.get_full_name() or delegate.username}"
                )
                return redirect("companies:delegations")

    context = {
        "eligible_users": eligible_users,
        "page_title": "إضافة تفويض",
    }
    return render(request, "companies/delegation_add.html", context)


@login_required
def delegation_deactivate(request, pk):
    """إلغاء تفويض"""
    from requests_app.models import ApprovalDelegation

    delegation = get_object_or_404(
        ApprovalDelegation,
        pk=pk,
        company=request.user.company
    )

    if request.method == "POST":
        delegation.is_active = False
        delegation.save(update_fields=["is_active"])
        messages.success(request, "تم إلغاء التفويض")

    return redirect("companies:delegations")


# ════════════════════════════════════════════════════════════
# Notification Settings
# ════════════════════════════════════════════════════════════

@login_required
def notification_settings_view(request):
    """إعدادات الإشعارات للشركة"""
    from companies.models import NotificationPreference

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company

    roles = ["employee", "manager", "hr_manager", "company_admin"]
    role_labels = {
        "employee": "موظف",
        "manager": "مدير",
        "hr_manager": "مدير HR",
        "company_admin": "صاحب الشركة",
    }

    notification_types = [
        ("request_approved", "تمت الموافقة على الطلب"),
        ("request_rejected", "تم رفض الطلب"),
        ("new_request_to_approve", "طلب جديد يحتاج موافقة"),
        ("late_warning", "تحذير تأخير"),
        ("late_threshold", "تجاوز حد التأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("stealth_alert", "تنبيه تتبع صامت"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("subscription_expiry", "انتهاء الاشتراك"),
        ("general_notice", "إشعار عام"),
    ]

    # بناء matrix
    prefs_map = {}
    existing = NotificationPreference.objects.filter(company=company)
    for p in existing:
        prefs_map[f"{p.role}_{p.notification_type}"] = p.push_enabled

    if request.method == "POST":
        for r in roles:
            for nt, _ in notification_types:
                key = f"{r}_{nt}"
                is_enabled = key in request.POST
                NotificationPreference.objects.update_or_create(
                    company=company,
                    role=r,
                    notification_type=nt,
                    defaults={"push_enabled": is_enabled}
                )
        messages.success(request, "تم حفظ إعدادات الإشعارات")
        return redirect("companies:notification_settings")

    context = {
        "roles": roles,
        "role_labels": role_labels,
        "notification_types": notification_types,
        "prefs_map": prefs_map,
        "page_title": "إعدادات الإشعارات",
    }
    return render(request, "companies/notification_settings.html", context)



# ═════════════════════════════════════════════════════════════
# Patch 49e — Departments Tree View Override
# ═════════════════════════════════════════════════════════════

def _dept_display_name(dept):
    return (
        getattr(dept, 'name_ar', None)
        or getattr(dept, 'name_en', None)
        or f"Department #{getattr(dept, 'pk', '')}"
    )


def _build_department_tree_rows(departments, hierarchy_links):
    dept_map = {d.id: d for d in departments}
    child_to_parent = {}
    children_map = {}

    for link in hierarchy_links:
        if not getattr(link, 'is_active', True):
            continue
        parent_id = getattr(link, 'parent_department_id', None)
        child_id = getattr(link, 'child_department_id', None)
        if not parent_id or not child_id:
            continue
        child_to_parent[child_id] = parent_id
        children_map.setdefault(parent_id, []).append(child_id)

    root_ids = [d.id for d in departments if d.id not in child_to_parent]
    visited = set()
    rows = []

    def walk(dept_id, depth=0):
        if dept_id in visited:
            return
        visited.add(dept_id)

        dept = dept_map.get(dept_id)
        if not dept:
            return

        child_ids = children_map.get(dept_id, [])
        rows.append({
            'id': dept.id,
            'name': _dept_display_name(dept),
            'depth': depth,
            'children_count': len(child_ids),
            'parent_id': child_to_parent.get(dept_id),
            'is_root': depth == 0,
        })

        for c_id in sorted(child_ids, key=lambda x: _dept_display_name(dept_map.get(x)).lower() if dept_map.get(x) else ''):
            walk(c_id, depth + 1)

    for root_id in sorted(root_ids, key=lambda x: _dept_display_name(dept_map.get(x)).lower() if dept_map.get(x) else ''):
        walk(root_id, 0)

    # لو فيه loops/عناصر ما اتعرضتش
    remaining_ids = [d.id for d in departments if d.id not in visited]
    for rem_id in sorted(remaining_ids, key=lambda x: _dept_display_name(dept_map.get(x)).lower() if dept_map.get(x) else ''):
        walk(rem_id, 0)

    return rows


@login_required
def departments_list(request):
    """
    Patch 49e:
    صفحة الإدارات بشكل شجري + إدارة الربط بين الإدارة الأم والأقسام التابعة
    """
    from django.contrib import messages
    from django.core.exceptions import PermissionDenied
    from .models import Department, DepartmentHierarchy

    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager', 'manager']:
        raise PermissionDenied("ليس لديك صلاحية عرض صفحة الإدارات")

    company = getattr(request.user, 'company', None)
    if not company:
        try:
            company = request.user.employee.company
        except Exception:
            company = None

    if not company:
        messages.error(request, 'لا يمكن تحديد الشركة الحالية.')
        return redirect('dashboard')

    def _would_create_cycle(child_id, parent_id):
        """
        منع:
        A -> B -> A
        """
        if not child_id or not parent_id:
            return False

        if child_id == parent_id:
            return True

        links = DepartmentHierarchy.objects.filter(company=company, is_active=True)
        parent_map = {link.child_department_id: link.parent_department_id for link in links}

        current = parent_id
        seen = set()
        while current and current not in seen:
            if current == child_id:
                return True
            seen.add(current)
            current = parent_map.get(current)
        return False

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        # ── حفظ الربط ────────────────────────────────────────
        if action == 'save_hierarchy':
            child_department_id = (request.POST.get('child_department_id') or '').strip()
            parent_department_id = (request.POST.get('parent_department_id') or '').strip()
            is_active = bool(request.POST.get('is_active'))
            notes = (request.POST.get('notes') or '').strip()

            if not child_department_id:
                messages.error(request, 'يرجى اختيار الإدارة الفرعية المراد ربطها')
                return redirect('/companies/departments/')

            try:
                child_department = Department.objects.get(pk=child_department_id, company=company)
            except Exception:
                messages.error(request, 'الإدارة الفرعية غير موجودة')
                return redirect('/companies/departments/')

            # لو parent فاضي = تحويل الإدارة إلى جذر / بدون أم
            if not parent_department_id:
                deleted_count, _ = DepartmentHierarchy.objects.filter(
                    company=company,
                    child_department=child_department
                ).delete()

                if deleted_count:
                    messages.success(request, f'تم تحويل "{_dept_display_name(child_department)}" إلى إدارة رئيسية')
                else:
                    messages.info(request, f'"{_dept_display_name(child_department)}" بالفعل إدارة رئيسية')
                return redirect('/companies/departments/')

            try:
                parent_department = Department.objects.get(pk=parent_department_id, company=company)
            except Exception:
                messages.error(request, 'الإدارة الأم غير موجودة')
                return redirect('/companies/departments/')

            if child_department.id == parent_department.id:
                messages.error(request, 'لا يمكن ربط الإدارة بنفسها كإدارة أم')
                return redirect('/companies/departments/')

            if _would_create_cycle(child_department.id, parent_department.id):
                messages.error(request, 'هذا الربط سيُحدث حلقة غير صحيحة في الهيكل الإداري')
                return redirect('/companies/departments/')

            try:
                link, created = DepartmentHierarchy.objects.update_or_create(
                    company=company,
                    child_department=child_department,
                    defaults={
                        'parent_department': parent_department,
                        'is_active': is_active,
                        'notes': notes,
                    }
                )
                if created:
                    messages.success(request, f'تم ربط "{_dept_display_name(child_department)}" تحت "{_dept_display_name(parent_department)}"')
                else:
                    messages.success(request, f'تم تحديث ربط "{_dept_display_name(child_department)}"')
            except Exception as e:
                messages.error(request, f'تعذر حفظ الربط: {e}')

            return redirect('/companies/departments/')

        # ── حذف الربط ────────────────────────────────────────
        if action == 'delete_hierarchy':
            link_id = (request.POST.get('link_id') or '').strip()
            try:
                link = DepartmentHierarchy.objects.get(pk=link_id, company=company)
                child_name = _dept_display_name(link.child_department)
                link.delete()
                messages.success(request, f'تم فك ربط "{child_name}" وأصبحت إدارة رئيسية')
            except DepartmentHierarchy.DoesNotExist:
                messages.error(request, 'الرابط غير موجود')
            except Exception as e:
                messages.error(request, f'تعذر حذف الربط: {e}')
            return redirect('/companies/departments/')

    departments = list(
        Department.objects.filter(company=company).order_by('name_ar', 'name_en', 'id')
    )

    hierarchy_links = list(
        DepartmentHierarchy.objects.filter(company=company).select_related(
            'parent_department', 'child_department'
        ).order_by('parent_department__name_ar', 'child_department__name_ar', 'id')
    )

    tree_rows = _build_department_tree_rows(departments, hierarchy_links)

    child_ids = {link.child_department_id for link in hierarchy_links if getattr(link, 'is_active', True)}
    root_departments = [d for d in departments if d.id not in child_ids]

    context = {
        'page_title': 'الإدارات',
        'departments': departments,
        'root_departments': root_departments,
        'hierarchy_links': hierarchy_links,
        'tree_rows': tree_rows,
    }
    return render(request, 'companies/departments_list.html', context)


# ═════════════════════════════════════════════════════════════
# Patch 49h — Charter Digital Signature Views
# ═════════════════════════════════════════════════════════════

@login_required
def charter_sign(request, charter_id):
    """صفحة توقيع الميثاق رقميًا"""
    from .models import WorkCharter, CharterDigitalSignature, CharterVersion
    from employees.models import Employee

    charter = get_object_or_404(WorkCharter, pk=charter_id)

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'لا يوجد ملف موظف مرتبط بحسابك')
        return redirect('dashboard')

    company = getattr(request.user, 'company', None) or getattr(employee, 'company', None)

    # هل وقّع بالفعل؟
    existing_signature = CharterDigitalSignature.objects.filter(
        employee=employee,
        charter=charter,
        is_valid=True
    ).first()

    if request.method == 'POST':
        full_name = (request.POST.get('full_name_typed') or '').strip()
        national_id = (request.POST.get('national_id_typed') or '').strip()
        agreement_confirmed = bool(request.POST.get('agreement_confirmed'))

        errors = []
        if not full_name:
            errors.append('يرجى كتابة الاسم الكامل')
        if not agreement_confirmed:
            errors.append('يرجى تأكيد الموافقة على الميثاق')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            # جلب آخر version
            latest_version = CharterVersion.objects.filter(charter=charter).order_by('-version_number').first()

            # IP
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not ip:
                ip = request.META.get('REMOTE_ADDR', '')

            user_agent = request.META.get('HTTP_USER_AGENT', '')

            CharterDigitalSignature.objects.create(
                company=company,
                employee=employee,
                charter=charter,
                charter_version=latest_version,
                full_name_typed=full_name,
                national_id_typed=national_id,
                agreement_text='أقر بأنني قرأت وفهمت ميثاق العمل وأوافق على الالتزام بكل بنوده.',
                ip_address=ip or None,
                user_agent=user_agent,
                is_valid=True,
            )
            messages.success(request, 'تم توقيع الميثاق بنجاح. شكرًا لالتزامك.')
            return redirect('companies:charter_view', charter_id=charter.pk)

    context = {
        'charter': charter,
        'employee': employee,
        'existing_signature': existing_signature,
        'page_title': f'توقيع ميثاق العمل — {charter.title}',
    }
    return render(request, 'companies/charter_sign.html', context)


@login_required
def charter_acceptance_status(request, charter_id):
    """حالة قبول الميثاق — للـ HR"""
    from .models import WorkCharter, CharterDigitalSignature
    from employees.models import Employee

    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('ليس لديك صلاحية عرض هذه الصفحة')

    charter = get_object_or_404(WorkCharter, pk=charter_id)

    company = getattr(request.user, 'company', None)
    if not company:
        messages.error(request, 'لا يمكن تحديد الشركة')
        return redirect('dashboard')

    all_employees = Employee.objects.filter(company=company, status='active').order_by('employee_code')

    signed_employee_ids = set(
        CharterDigitalSignature.objects.filter(
            charter=charter,
            company=company,
            is_valid=True
        ).values_list('employee_id', flat=True)
    )

    signed = []
    unsigned = []
    for emp in all_employees:
        if emp.id in signed_employee_ids:
            sig = CharterDigitalSignature.objects.filter(
                charter=charter, employee=emp, is_valid=True
            ).order_by('-signed_at').first()
            signed.append({'employee': emp, 'signature': sig})
        else:
            unsigned.append(emp)

    # إرسال تذكير
    if request.method == 'POST' and request.POST.get('action') == 'send_reminder':
        from .models import CharterNotificationLog
        sent_count = 0
        for emp in unsigned:
            try:
                CharterNotificationLog.objects.create(
                    company=company,
                    employee=emp,
                    charter=charter,
                    notification_type='quarterly_reminder',
                )
                # إرسال إشعار داخلي
                try:
                    from accounts.models import EmployeeNotification
                    if emp.user:
                        EmployeeNotification.objects.create(
                            recipient=emp.user,
                            title='تذكير بتوقيع ميثاق العمل',
                            message=f'يرجى مراجعة وتوقيع ميثاق العمل: {charter.title}',
                            notification_type='charter_reminder',
                        )
                except Exception:
                    pass
                sent_count += 1
            except Exception:
                pass
        messages.success(request, f'تم إرسال تذكير لـ {sent_count} موظف لم يوقعوا بعد')
        return redirect('companies:charter_acceptance_status', charter_id=charter.pk)

    context = {
        'charter': charter,
        'signed': signed,
        'unsigned': unsigned,
        'signed_count': len(signed),
        'unsigned_count': len(unsigned),
        'total_count': len(signed) + len(unsigned),
        'page_title': f'حالة توقيع الميثاق — {charter.title}',
    }
    return render(request, 'companies/charter_acceptance_status.html', context)


@login_required
def charter_print_signature(request, signature_id):
    """طباعة توقيع رقمي"""
    from .models import CharterDigitalSignature

    sig = get_object_or_404(CharterDigitalSignature, pk=signature_id)

    company = getattr(request.user, 'company', None)

    context = {
        'signature': sig,
        'company': company,
        'page_title': f'طباعة توقيع — {sig.employee.full_name_ar}',
    }
    return render(request, 'companies/charter_print_signature.html', context)

