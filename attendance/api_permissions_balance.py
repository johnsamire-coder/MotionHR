"""
MotionHR - Employee Permission (Leave Hours) API
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils import timezone
from datetime import date
import logging

logger = logging.getLogger(__name__)

HR_ROLES = {"super_admin", "company_admin", "hr_manager", "manager", "branch_manager"}


def _get_employee(request):
    try:
        from employees.models import Employee
        return Employee._base_manager.filter(user=request.user).first()
    except Exception:
        return None


def _get_active_policy(employee):
    """جيب السياسة الفعالة للموظف"""
    from attendance.models import AttendancePolicy, AttendancePolicyAssignment

    company = employee.company
    if not company:
        return None

    today = date.today()

    # الأولوية: قسم > فرع > شركة
    for assignment_type in ['department', 'branch', 'company']:
        assignments = AttendancePolicyAssignment._base_manager.filter(
            policy__company=company,
            policy__status='active',
            policy__effective_from__lte=today,
            assignment_type=assignment_type,
        )
        if assignment_type == 'department' and employee.department:
            assignments = assignments.filter(department=employee.department)
        elif assignment_type == 'branch' and employee.branch:
            assignments = assignments.filter(branch=employee.branch)
        elif assignment_type == 'company':
            assignments = assignments.filter(branch__isnull=True, department__isnull=True)
        else:
            continue

        assignment = assignments.order_by('-policy__effective_from').first()
        if assignment:
            return assignment.policy

    # fallback: آخر سياسة active للشركة
    return AttendancePolicy._base_manager.filter(
        company=company, status='active'
    ).order_by('-effective_from').first()


def _get_period_range(policy, employee):
    """حساب بداية ونهاية الفترة الحالية"""
    today = date.today()

    if policy and policy.permission_reset_cycle == 'payroll':
        # TODO: لما نعمل PayrollCycle model نربطه هنا
        # حاليا fallback على الشهر الميلادي
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)
    else:
        # شهر ميلادي
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)

    return start, end


# ── رصيد الأذونات للموظف ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_permission_balance(request):
    employee = _get_employee(request)
    if not employee:
        return Response({"success": False, "error": "لا يوجد موظف"}, status=400)

    policy = _get_active_policy(employee)

    if not policy or not policy.permission_enabled:
        return Response({
            "success": True,
            "enabled": False,
            "message": "لا توجد سياسة أذونات مفعلة",
        })

    from attendance.models import PermissionLedger

    start, end = _get_period_range(policy, employee)

    # جيب كل الحركات في الفترة الحالية
    entries = PermissionLedger._base_manager.filter(
        employee=employee,
        reference_date__gte=start,
        reference_date__lt=end,
    ).order_by('-created_at')

    total_minutes_used = 0
    total_count_used = 0
    history = []

    for e in entries:
        total_minutes_used += e.minutes_used
        total_count_used += e.count_used
        history.append({
            "id": e.id,
            "entry_type": e.entry_type,
            "entry_type_display": dict(PermissionLedger.ENTRY_TYPE_CHOICES).get(e.entry_type, e.entry_type),
            "minutes_used": e.minutes_used,
            "count_used": e.count_used,
            "reference_date": str(e.reference_date) if e.reference_date else None,
            "notes": e.notes,
            "created_at": str(e.created_at)[:16],
        })

    monthly_hours = float(policy.permission_monthly_hours)
    monthly_minutes = int(monthly_hours * 60)
    remaining_minutes = max(0, monthly_minutes - total_minutes_used)
    remaining_count = max(0, policy.permission_monthly_count - total_count_used)

    return Response({
        "success": True,
        "enabled": True,
        "policy_name": policy.name,
        "period_start": str(start),
        "period_end": str(end),
        "monthly_hours": monthly_hours,
        "monthly_minutes": monthly_minutes,
        "monthly_count": policy.permission_monthly_count,
        "max_hours_per_request": float(policy.permission_max_hours_per_request),
        "fraction_as_full": policy.permission_fraction_as_full,
        "reset_cycle": policy.permission_reset_cycle,
        "used_minutes": total_minutes_used,
        "used_count": total_count_used,
        "remaining_minutes": remaining_minutes,
        "remaining_count": remaining_count,
        "remaining_hours": round(remaining_minutes / 60, 2),
        "history": history,
    })


# ── المدير يشوف رصيد موظف معين ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_permission_balance(request, employee_id):
    role = getattr(request.user, "role", None)
    if role not in HR_ROLES and not request.user.is_superuser:
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    from employees.models import Employee
    try:
        employee = Employee._base_manager.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    # نستخدم نفس المنطق
    policy = _get_active_policy(employee)

    if not policy or not policy.permission_enabled:
        return Response({
            "success": True,
            "enabled": False,
            "employee_name": employee.user.get_full_name(),
        })

    from attendance.models import PermissionLedger

    start, end = _get_period_range(policy, employee)

    entries = PermissionLedger._base_manager.filter(
        employee=employee,
        reference_date__gte=start,
        reference_date__lt=end,
    ).order_by('-created_at')

    total_minutes_used = sum(e.minutes_used for e in entries)
    total_count_used = sum(e.count_used for e in entries)

    monthly_hours = float(policy.permission_monthly_hours)
    monthly_minutes = int(monthly_hours * 60)

    return Response({
        "success": True,
        "enabled": True,
        "employee_id": employee.id,
        "employee_name": employee.user.get_full_name(),
        "policy_name": policy.name,
        "period_start": str(start),
        "period_end": str(end),
        "monthly_hours": monthly_hours,
        "monthly_count": policy.permission_monthly_count,
        "used_minutes": total_minutes_used,
        "used_count": total_count_used,
        "remaining_minutes": max(0, monthly_minutes - total_minutes_used),
        "remaining_count": max(0, policy.permission_monthly_count - total_count_used),
    })


# ── المدير يمنح إذن إضافي ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def grant_extra_permission(request, employee_id):
    role = getattr(request.user, "role", None)
    if role not in HR_ROLES and not request.user.is_superuser:
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    from employees.models import Employee
    from attendance.models import PermissionLedger

    try:
        employee = Employee._base_manager.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    data = request.data
    minutes = int(data.get("minutes", 0))
    count = int(data.get("count", 0))
    notes = str(data.get("notes", ""))

    if minutes <= 0 and count <= 0:
        return Response({"success": False, "error": "لازم تحدد دقايق أو عدد مرات"}, status=400)

    # الإذن الإضافي بيتسجل بقيم سالبة عشان يزود الرصيد
    PermissionLedger._base_manager.create(
        employee=employee,
        company=employee.company,
        entry_type='manual_grant',
        minutes_used=-minutes,
        count_used=-count,
        reference_date=date.today(),
        notes=f"إذن إضافي من {request.user.get_full_name()}: {notes}",
    )

    return Response({
        "success": True,
        "message": f"تم منح إذن إضافي {minutes} دقيقة / {count} مرة",
    })


# ── المدير يلغي تأخير (rollback) ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def rollback_late(request, employee_id):
    role = getattr(request.user, "role", None)
    if role not in HR_ROLES and not request.user.is_superuser:
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    from employees.models import Employee
    from attendance.models import PermissionLedger

    try:
        employee = Employee._base_manager.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    data = request.data
    reference_date = data.get("reference_date")
    notes = str(data.get("notes", ""))

    if not reference_date:
        return Response({"success": False, "error": "لازم تحدد تاريخ التأخير"}, status=400)

    # نشوف لو فيه حركة تأخير في اليوم ده
    late_entry = PermissionLedger._base_manager.filter(
        employee=employee,
        entry_type='auto_late',
        reference_date=reference_date,
    ).first()

    if not late_entry:
        return Response({"success": False, "error": "مفيش تأخير مسجل في اليوم ده"}, status=404)

    # نعمل حركة عكسية
    PermissionLedger._base_manager.create(
        employee=employee,
        company=employee.company,
        entry_type='rollback',
        minutes_used=-late_entry.minutes_used,
        count_used=-late_entry.count_used,
        reference_date=date.today(),
        notes=f"إلغاء تأخير يوم {reference_date} بواسطة {request.user.get_full_name()}: {notes}",
    )

    return Response({
        "success": True,
        "message": f"تم إلغاء تأخير يوم {reference_date} وإرجاع الرصيد",
    })
