
LEAVE_SWITCHES = [
    ('is_paid',           'بمرتب'),
    ('requires_approval', 'تحتاج موافقة'),
    ('requires_document', 'تحتاج وثيقة'),
    ('carry_forward',     'ترحيل للسنة القادمة'),
    ('is_active',         'نشط'),
]

"""
leaves/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import LeaveType, LeaveBalance, LeaveRequest
from employees.models import Employee


# ════════════════════════════════════════════════════════════
# أنواع الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_types_list(request):
    company     = request.user.company
    leave_types = LeaveType.objects.filter(company=company).order_by("name")
    context = {
        "leave_types": leave_types,
        "page_title":  "أنواع الإجازات",
    }
    return render(request, "leaves/leave_types_list.html", context)


@login_required
def leave_type_add(request):
    if request.method == "POST":
        lt = LeaveType(company=request.user.company)
        lt.name              = request.POST.get("name", "")
        lt.category          = request.POST.get("category", "other")
        lt.days_allowed      = int(request.POST.get("days_allowed", 0))
        lt.is_paid           = "is_paid"           in request.POST
        lt.requires_approval = "requires_approval" in request.POST
        lt.requires_document = "requires_document" in request.POST
        lt.carry_forward     = "carry_forward"     in request.POST
        lt.max_carry_days    = int(request.POST.get("max_carry_days", 0))
        lt.color             = request.POST.get("color", "#06B6D4")
        lt.description       = request.POST.get("description", "")
        lt.save()
        messages.success(request, f'✅ تم إضافة نوع الإجازة "{lt.name}"')
        return redirect("leaves:leave_types_list")

    context = {
        "categories": LeaveType.LEAVE_CATEGORIES,
        "switches":   LEAVE_SWITCHES,
        "page_title": "إضافة نوع إجازة",
        "action":     "add",
    }
    return render(request, "leaves/leave_type_form.html", context)


@login_required
def leave_type_edit(request, pk):
    lt = get_object_or_404(LeaveType, pk=pk, company=request.user.company)

    if request.method == "POST":
        lt.name              = request.POST.get("name", lt.name)
        lt.category          = request.POST.get("category", lt.category)
        lt.days_allowed      = int(request.POST.get("days_allowed", 0))
        lt.is_paid           = "is_paid"           in request.POST
        lt.requires_approval = "requires_approval" in request.POST
        lt.requires_document = "requires_document" in request.POST
        lt.carry_forward     = "carry_forward"     in request.POST
        lt.max_carry_days    = int(request.POST.get("max_carry_days", 0))
        lt.color             = request.POST.get("color", lt.color)
        lt.is_active         = "is_active"         in request.POST
        lt.description       = request.POST.get("description", "")
        lt.save()
        messages.success(request, f'✅ تم تحديث "{lt.name}"')
        return redirect("leaves:leave_types_list")

    context = {
        "lt":         lt,
        "categories": LeaveType.LEAVE_CATEGORIES,
        "switches":   LEAVE_SWITCHES,
        "page_title": f"تعديل: {lt.name}",
        "action":     "edit",
    }
    return render(request, "leaves/leave_type_form.html", context)


@login_required
@require_POST
def leave_type_delete(request, pk):
    lt = get_object_or_404(LeaveType, pk=pk, company=request.user.company)
    name = lt.name
    lt.delete()
    messages.success(request, f'✅ تم حذف "{name}"')
    return redirect("leaves:leave_types_list")


# ════════════════════════════════════════════════════════════
# طلبات الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_requests_list(request):
    company = request.user.company

    requests = LeaveRequest.objects.filter(
        company=company
    ).select_related("employee", "leave_type", "reviewed_by").order_by("-created_at")

    # لو الموظف العادي - يشوف طلباته هو فقط
    if request.user.role == "employee":
        current_emp = Employee.objects.filter(user=request.user).first()
        if current_emp:
            requests = requests.filter(employee=current_emp)
        else:
            requests = LeaveRequest.objects.none()

    # فلترة
    status = request.GET.get("status")
    if status:
        requests = requests.filter(status=status)

    # البحث بالاسم للإدارة فقط
    emp_search = request.GET.get("employee")
    if emp_search and request.user.role != "employee":
        requests = requests.filter(
            Q(employee__first_name_ar__icontains=emp_search) |
            Q(employee__last_name_ar__icontains=emp_search)
        )

    context = {
        "requests": requests,
        "page_title": "طلباتي" if request.user.role == "employee" else "طلبات الإجازات",
        "status": status,
    }
    return render(request, "leaves/leave_requests_list.html", context)


@login_required
def leave_request_add(request):
    company     = request.user.company
    employees   = Employee.objects.filter(company=company, status="active")
    leave_types = LeaveType.objects.filter(company=company, is_active=True)

    if request.method == "POST":
        employee_id   = request.POST.get("employee")
        leave_type_id = request.POST.get("leave_type")
        start_date    = request.POST.get("start_date")
        end_date      = request.POST.get("end_date")
        reason        = request.POST.get("reason", "")

        if not all([employee_id, leave_type_id, start_date, end_date]):
            messages.error(request, "يرجى ملء جميع الحقول المطلوبة")
        else:
            from datetime import date
            start = date.fromisoformat(start_date)
            end   = date.fromisoformat(end_date)

            if end < start:
                messages.error(request, "تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية")
            else:
                days = (end - start).days + 1

                lr = LeaveRequest(company=company)
                lr.employee    = get_object_or_404(Employee, pk=employee_id, company=company)
                lr.leave_type  = get_object_or_404(LeaveType, pk=leave_type_id, company=company)
                lr.start_date  = start
                lr.end_date    = end
                lr.days_count  = days
                lr.reason      = reason
                lr.notes       = request.POST.get("notes", "")
                lr.status      = "pending"

                if "document" in request.FILES:
                    lr.document = request.FILES["document"]

                lr.save()

                # تحديث الرصيد المنتظر
                try:
                    bal = LeaveBalance.objects.get(
                        company=company,
                        employee=lr.employee,
                        leave_type=lr.leave_type,
                        year=start.year,
                    )
                    bal.pending_days += days
                    bal.save()
                except LeaveBalance.DoesNotExist:
                    pass

                messages.success(request, "✅ تم تقديم طلب الإجازة بنجاح")
                return redirect("leaves:leave_requests_list")

    # لو موظف عادي - يشوف نفسه بس
    if request.user.role == 'employee':
        try:
            from employees.models import Employee as Emp
            current_emp = Emp.objects.filter(user=request.user).first()
            if current_emp:
                employees = [current_emp]
        except Exception:
            pass

    context = {
        "employees":   employees,
        "leave_types": leave_types,
        "page_title":  "طلب إجازة جديد",
        "today":       timezone.now().date().isoformat(),
    }
    return render(request, "leaves/leave_request_form.html", context)


@login_required
def leave_request_detail(request, pk):
    lr = get_object_or_404(
        LeaveRequest, pk=pk, company=request.user.company
    )
    context = {
        "lr":         lr,
        "page_title": f"طلب إجازة - {lr.employee.full_name_ar}",
    }
    return render(request, "leaves/leave_request_detail.html", context)


@login_required
@require_POST
def leave_approve(request, pk):
    lr    = get_object_or_404(LeaveRequest, pk=pk, company=request.user.company)
    notes = request.POST.get("notes", "")
    lr.approve(request.user, notes)
    messages.success(request, "✅ تمت الموافقة على طلب الإجازة")
    return redirect("leaves:leave_request_detail", pk=pk)


@login_required
@require_POST
def leave_reject(request, pk):
    lr    = get_object_or_404(LeaveRequest, pk=pk, company=request.user.company)
    notes = request.POST.get("notes", "")
    lr.reject(request.user, notes)
    messages.warning(request, "⚠️ تم رفض طلب الإجازة")
    return redirect("leaves:leave_request_detail", pk=pk)


@login_required
@require_POST
def leave_cancel(request, pk):
    lr = get_object_or_404(LeaveRequest, pk=pk, company=request.user.company)
    lr.cancel()
    messages.info(request, "ℹ️ تم إلغاء طلب الإجازة")
    return redirect("leaves:leave_requests_list")


# ════════════════════════════════════════════════════════════
# أرصدة الإجازات
# ════════════════════════════════════════════════════════════

@login_required
def leave_balances(request):
    company     = request.user.company
    leave_types = LeaveType.objects.filter(company=company, is_active=True)
    employees   = Employee.objects.filter(company=company, status="active")
    year        = int(request.GET.get("year", timezone.now().year))

    balances = LeaveBalance.objects.filter(
        company=company, year=year
    ).select_related("employee", "leave_type").order_by(
        "employee__first_name_ar"
    )

    context = {
        "balances":    balances,
        "leave_types": leave_types,
        "employees":   employees,
        "year":        year,
        "years":       range(2023, timezone.now().year + 2),
        "page_title":  "أرصدة الإجازات",
    }
    return render(request, "leaves/leave_balances.html", context)


@login_required
@require_POST
def set_leave_balance(request):
    """تحديد رصيد إجازة لموظف"""
    company       = request.user.company
    employee_id   = request.POST.get("employee")
    leave_type_id = request.POST.get("leave_type")
    year          = int(request.POST.get("year", timezone.now().year))
    total_days    = float(request.POST.get("total_days", 0))

    employee   = get_object_or_404(Employee,   pk=employee_id,   company=company)
    leave_type = get_object_or_404(LeaveType,  pk=leave_type_id, company=company)

    bal, created = LeaveBalance.objects.get_or_create(
        company=company,
        employee=employee,
        leave_type=leave_type,
        year=year,
        defaults={"total_days": total_days},
    )
    if not created:
        bal.total_days = total_days
        bal.save()

    action = "إنشاء" if created else "تحديث"
    messages.success(
        request,
        f"✅ تم {action} رصيد {leave_type.name} للموظف {employee.full_name_ar}"
    )
    return redirect("leaves:leave_balances")
