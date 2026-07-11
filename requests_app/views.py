from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q

from .models import RequestCategory, RequestType, EmployeeRequest
from employees.models import Employee


@login_required
def requests_list(request):
    """قائمة الطلبات"""
    company = request.user.company

    if request.user.role == "employee":
        emp = Employee.objects.filter(user=request.user).first()
        if emp:
            reqs = EmployeeRequest.objects.filter(company=company, employee=emp)
        else:
            reqs = EmployeeRequest.objects.none()
    else:
        reqs = EmployeeRequest.objects.filter(company=company)

    reqs = reqs.select_related("employee", "request_type", "request_type__category")

    status = request.GET.get("status")
    if status:
        reqs = reqs.filter(status=status)

    context = {
        "requests": reqs.order_by("-created_at"),
        "status_filter": status,
        "page_title": "الطلبات",
    }
    return render(request, "requests_app/list.html", context)


@login_required
def request_add(request):
    """طلب جديد"""
    company = request.user.company
    categories = RequestCategory.objects.filter(
        company=company, is_active=True
    ).prefetch_related("types")
    request_types = RequestType.objects.filter(
        company=company, is_active=True
    ).select_related("category")

    if request.user.role == "employee":
        emp = Employee.objects.filter(user=request.user).first()
        employees = [emp] if emp else []
    else:
        employees = Employee.objects.filter(company=company, status="active")

    if request.method == "POST":
        employee_id = request.POST.get("employee")
        type_id = request.POST.get("request_type")
        subject = request.POST.get("subject", "")
        details = request.POST.get("details", "")
        priority = request.POST.get("priority", "normal")

        if not all([employee_id, type_id, subject, details]):
            messages.error(request, "يرجى ملء جميع الحقول المطلوبة")
        else:
            emp = get_object_or_404(Employee, pk=employee_id, company=company)
            req_type = get_object_or_404(RequestType, pk=type_id, company=company)

            req_obj = EmployeeRequest(company=company)
            req_obj.employee = emp
            req_obj.request_type = req_type
            req_obj.subject = subject
            req_obj.details = details
            req_obj.priority = priority
            req_obj.status = "pending"

            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            if start_date:
                req_obj.start_date = start_date
            if end_date:
                req_obj.end_date = end_date

            amount = request.POST.get("amount")
            if amount:
                req_obj.amount = amount

            if "document" in request.FILES:
                req_obj.document = request.FILES["document"]

            req_obj.save()
            messages.success(request, "تم تقديم الطلب بنجاح")
            return redirect("requests_app:list")

    context = {
        "categories": categories,
        "request_types": request_types,
        "employees": employees,
        "page_title": "طلب جديد",
    }
    return render(request, "requests_app/add.html", context)


@login_required
def request_detail(request, pk):
    """تفاصيل طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )

    # بناء خطوات المسار
    steps_info = []
    step_labels = {
        "direct_manager": "المدير المباشر",
        "hr_manager": "مدير HR",
        "company_admin": "صاحب الشركة",
        "skip": "تخطي",
    }
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)
    if flow:
        active_steps = flow.get_active_steps()
        step_data = [
            (1, req_obj.step_1_status, req_obj.step_1_by, req_obj.step_1_at),
            (2, req_obj.step_2_status, req_obj.step_2_by, req_obj.step_2_at),
            (3, req_obj.step_3_status, req_obj.step_3_by, req_obj.step_3_at),
        ]
        for step_key, role, label in active_steps:
            num = int(step_key[-1])
            sn, ss, sb, sa = step_data[num - 1]
            steps_info.append((sn, ss or "", sb, sa, label))
    else:
        steps_info = [
            (1, req_obj.step_1_status or "pending", req_obj.step_1_by, req_obj.step_1_at, "HR"),
        ]

    can_approve, step_num, role = _can_user_approve_step(req_obj, request.user)

    context = {
        "req": req_obj,
        "steps_info": steps_info,
        "can_approve": can_approve and req_obj.status == "pending",
        "page_title": f"طلب: {req_obj.subject}",
    }
    return render(request, "requests_app/detail.html", context)


@login_required
@require_POST
def request_approve(request, pk):
    """موافقة على طلب — مع Workflow"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")

    can_approve, step_num, role = _can_user_approve_step(req_obj, request.user)

    if can_approve:
        _process_step_action(req_obj, step_num, "approved", request.user, notes)
        if req_obj.status == "approved":
            messages.success(request, "تمت الموافقة النهائية على الطلب ✅")
        else:
            messages.success(request, f"تمت الموافقة على الخطوة {step_num}")
    else:
        messages.error(request, "ليس لديك صلاحية الموافقة في هذه الخطوة")

    return redirect("requests_app:detail", pk=pk)


@login_required
@require_POST
def request_reject(request, pk):
    """رفض طلب — مع Workflow"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")

    can_approve, step_num, role = _can_user_approve_step(req_obj, request.user)

    if can_approve:
        _process_step_action(req_obj, step_num, "rejected", request.user, notes)
        messages.warning(request, "تم رفض الطلب ❌")
    else:
        messages.error(request, "ليس لديك صلاحية الرفض في هذه الخطوة")

    return redirect("requests_app:detail", pk=pk)


@login_required
@require_POST
def request_cancel(request, pk):
    """إلغاء طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    req_obj.status = "cancelled"
    req_obj.save()
    messages.info(request, "تم إلغاء الطلب")
    return redirect("requests_app:list")


# ════════════════════════════════════════════════════════════
# Workflow Engine
# ════════════════════════════════════════════════════════════

def _get_approval_flow(company, request_type):
    """جلب مسار الموافقة لنوع الطلب"""
    try:
        from requests_app.models import ApprovalFlow
        return ApprovalFlow.objects.filter(
            company=company,
            request_type=request_type
        ).first()
    except Exception:
        return None


def _get_active_delegation(company, role):
    """
    هل فيه تفويض نشط لهذا الدور؟
    لو أيوه → إيه الـ delegate؟
    """
    try:
        from requests_app.models import ApprovalDelegation
        from django.utils import timezone
        today = timezone.now().date()

        delegation = ApprovalDelegation.objects.filter(
            company=company,
            delegator_role=role,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        ).first()

        if delegation:
            return delegation.delegate
    except Exception:
        pass
    return None


def _get_approver_for_role(role, employee, company):
    """
    جلب المستخدم المسؤول عن الموافقة حسب الدور
    مع مراعاة التفويض
    """
    from accounts.models import User

    # أولًا: هل فيه تفويض نشط؟
    delegate = _get_active_delegation(company, role)
    if delegate:
        return delegate

    if role == "direct_manager":
        # المدير المباشر للموظف
        try:
            manager_emp = employee.direct_manager
            if manager_emp and manager_emp.user:
                return manager_emp.user
        except Exception:
            pass
        # لو مفيش مدير → escalate لـ HR
        return User.objects.filter(
            company=company,
            role="hr_manager"
        ).first()

    elif role == "hr_manager":
        return User.objects.filter(
            company=company,
            role="hr_manager"
        ).first()

    elif role == "company_admin":
        return User.objects.filter(
            company=company,
            role__in=["company_admin", "super_admin"]
        ).first()

    return None


def _initialize_workflow(req_obj):
    """
    تهيئة workflow للطلب الجديد
    - جلب مسار الموافقة
    - تحديد الخطوة الأولى
    - إشعار أول approver
    """
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)

    if not flow:
        # لو مفيش flow → يروح لـ HR مباشرة
        req_obj.current_step = 1
        req_obj.step_1_status = "pending"
        req_obj.save(update_fields=["current_step", "step_1_status"])
        _notify_approver_for_step(req_obj, 1, "hr_manager")
        return

    steps = flow.get_active_steps()

    if not steps:
        # مفيش خطوات → approve تلقائي
        req_obj.status = "approved"
        req_obj.save(update_fields=["status"])
        return

    req_obj.current_step = 1
    req_obj.step_1_status = "pending"
    req_obj.save(update_fields=["current_step", "step_1_status"])

    # إشعار الـ approver الأول
    first_step_key, first_role, _ = steps[0]
    _notify_approver_for_step(req_obj, 1, first_role)


def _notify_approver_for_step(req_obj, step_num, role):
    """إشعار المسؤول عن خطوة معينة"""
    try:
        from accounts.models import EmployeeNotification
        from employees.models import Employee

        approver = _get_approver_for_role(role, req_obj.employee, req_obj.company)
        if not approver:
            return

        approver_emp = Employee.all_objects.filter(user=approver).first()
        if not approver_emp:
            return

        role_labels = {
            "direct_manager": "المدير المباشر",
            "hr_manager": "مدير HR",
            "company_admin": "صاحب الشركة",
        }

        title = f"طلب جديد يحتاج موافقتك"
        message = (
            f"الموظف {req_obj.employee.full_name_ar} قدم طلب:\n"
            f"النوع: {req_obj.request_type.name}\n"
            f"الموضوع: {req_obj.subject}\n"
            f"الخطوة {step_num} من {role_labels.get(role, role)}"
        )

        EmployeeNotification.objects.create(
            employee=approver_emp,
            title=title,
            message=message,
            notification_type="request_update",
            severity="warning",
            is_read=False,
        )
    except Exception:
        pass


def _notify_employee_step_result(req_obj, step_num, action):
    """إشعار الموظف بنتيجة خطوة"""
    try:
        from accounts.models import EmployeeNotification

        action_label = "وافق" if action == "approved" else "رفض"
        step_label = f"الخطوة {step_num}"

        title = f"تحديث على طلبك: {req_obj.request_type.name}"
        message = (
            f"طلبك ({req_obj.subject}) "
            f"تم {'الموافقة عليه' if action == 'approved' else 'رفضه'} "
            f"في {step_label}."
        )
        severity = "info" if action == "approved" else "danger"

        EmployeeNotification.objects.create(
            employee=req_obj.employee,
            title=title,
            message=message,
            notification_type="request_update",
            severity=severity,
            is_read=False,
        )
    except Exception:
        pass


def _process_step_action(req_obj, step_num, action, by_user, notes=""):
    """
    معالجة action (approve/reject) على خطوة معينة
    """
    from django.utils import timezone

    now = timezone.now()
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)

    # حفظ بيانات الخطوة
    if step_num == 1:
        req_obj.step_1_status = action
        req_obj.step_1_by = by_user
        req_obj.step_1_at = now
        req_obj.step_1_notes = notes
    elif step_num == 2:
        req_obj.step_2_status = action
        req_obj.step_2_by = by_user
        req_obj.step_2_at = now
        req_obj.step_2_notes = notes
    elif step_num == 3:
        req_obj.step_3_status = action
        req_obj.step_3_by = by_user
        req_obj.step_3_at = now
        req_obj.step_3_notes = notes

    if action == "rejected":
        req_obj.status = "rejected"
        req_obj.reviewed_by = by_user
        req_obj.reviewed_at = now
        req_obj.save()

        notify_emp = True
        if flow:
            notify_emp = flow.notify_employee_on_each_step
        if notify_emp:
            _notify_employee_step_result(req_obj, step_num, "rejected")
        return

    # approved → نروح للخطوة الجاية
    if action == "approved":
        notify_emp = True
        if flow:
            notify_emp = flow.notify_employee_on_each_step
        if notify_emp:
            _notify_employee_step_result(req_obj, step_num, "approved")

        # نحدد الخطوة الجاية
        next_step = step_num + 1
        all_steps = ["skip", "skip", "skip"]
        if flow:
            all_steps = [flow.step_1_role, flow.step_2_role, flow.step_3_role]

        while next_step <= 3:
            next_role = all_steps[next_step - 1]
            if next_role != "skip":
                # فيه خطوة جاية
                req_obj.current_step = next_step
                if next_step == 2:
                    req_obj.step_2_status = "pending"
                elif next_step == 3:
                    req_obj.step_3_status = "pending"
                req_obj.save()
                _notify_approver_for_step(req_obj, next_step, next_role)
                return
            next_step += 1

        # كل الخطوات خلصت → Approved
        req_obj.status = "approved"
        req_obj.reviewed_by = by_user
        req_obj.reviewed_at = now
        req_obj.save()

        # إشعار الموظف بالموافقة النهائية
        try:
            from accounts.models import EmployeeNotification
            EmployeeNotification.objects.create(
                employee=req_obj.employee,
                title=f"تمت الموافقة على طلبك",
                message=(
                    f"تمت الموافقة على طلبك ({req_obj.subject}) بشكل نهائي.\n"
                    f"النوع: {req_obj.request_type.name}"
                ),
                notification_type="request_update",
                severity="info",
                is_read=False,
            )
        except Exception:
            pass

        # لو الطلب بديل + إجازة → إشعار البديل
        if req_obj.substitute_employee and not req_obj.substitute_notified:
            try:
                from accounts.models import EmployeeNotification
                EmployeeNotification.objects.create(
                    employee=req_obj.substitute_employee,
                    title="تم تحديدك بديلًا",
                    message=(
                        f"تم تحديدك بديلًا للموظف {req_obj.employee.full_name_ar}\n"
                        f"خلال الفترة: {req_obj.start_date} - {req_obj.end_date or 'غير محدد'}"
                    ),
                    notification_type="general_notice",
                    severity="info",
                    is_read=False,
                )
                req_obj.substitute_notified = True
                req_obj.save(update_fields=["substitute_notified"])
            except Exception:
                pass


def _can_user_approve_step(req_obj, user):
    """
    هل هذا المستخدم مسؤول عن الخطوة الحالية؟
    """
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)
    current = req_obj.current_step

    if flow:
        steps = flow.get_active_steps()
        if current <= len(steps):
            step_key, role, _ = steps[current - 1]
            approver = _get_approver_for_role(role, req_obj.employee, req_obj.company)
            if approver and approver.id == user.id:
                return True, current, role

    # fallback: HR يقدر يوافق دايمًا
    if getattr(user, "role", "") in ["hr_manager", "company_admin", "super_admin"]:
        return True, current, getattr(user, "role", "hr_manager")

    return False, current, None
