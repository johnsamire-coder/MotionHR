"""
MotionHR - Attendance Policy API
إدارة سياسات الحضور والخصم
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

HR_ROLES = {"super_admin", "company_admin", "hr_manager"}
OWNER_ROLES = {"super_admin", "company_admin"}


def _check_hr(request):
    role = getattr(request.user, "role", None)
    if role not in HR_ROLES and not request.user.is_superuser:
        return Response({"success": False, "error": "غير مصرح - HR فقط"}, status=403)
    return None


def _get_company(request):
    company = getattr(request.user, "company", None)
    if company:
        return company
    try:
        from employees.models import Employee
        emp = Employee._base_manager.filter(user=request.user).first()
        if emp and emp.company:
            return emp.company
    except Exception:
        pass
    return None


def _policy_data(policy):
    assignments = []
    for a in policy.assignments.all():
        assignments.append({
            "id": a.id,
            "assignment_type": a.assignment_type,
            "branch_id": a.branch_id,
            "branch_name": a.branch.name_ar if a.branch else None,
            "department_id": a.department_id,
            "department_name": a.department.name_ar if a.department else None,
            "priority": a.priority,
        })

    late_rules = []
    for r in policy.late_rules.all():
        late_rules.append({
            "id": r.id,
            "from_minutes": r.from_minutes,
            "to_minutes": r.to_minutes,
            "deduction_type": r.deduction_type,
            "deduction_value": float(r.deduction_value),
            "display_order": r.display_order,
        })

    absence_rules = []
    for r in policy.absence_rules.all():
        absence_rules.append({
            "id": r.id,
            "absence_type": r.absence_type,
            "consecutive_days": r.consecutive_days,
            "occurrences_in_month": r.occurrences_in_month,
            "deduction_type": r.deduction_type,
            "deduction_value": float(r.deduction_value),
        })

    overtime_rules = []
    for r in policy.overtime_rules.all():
        overtime_rules.append({
            "id": r.id,
            "overtime_type": r.overtime_type,
            "multiplier": float(r.multiplier),
            "min_minutes": r.min_minutes,
            "max_hours_per_day": r.max_hours_per_day,
            "max_hours_per_month": r.max_hours_per_month,
            "requires_approval": r.requires_approval,
        })

    night_rules = []
    for r in policy.night_shift_rules.all():
        night_rules.append({
            "id": r.id,
            "allowance_type": r.allowance_type,
            "amount": float(r.amount),
            "percentage": float(r.percentage),
            "night_start_hour": r.night_start_hour,
            "min_night_hours": r.min_night_hours,
        })

    weekend_rules = []
    for r in policy.weekend_work_rules.all():
        weekend_rules.append({
            "id": r.id,
            "compensation_type": r.compensation_type,
            "multiplier": float(r.multiplier),
            "amount": float(r.amount or 0),
        })

    late_repeat = []
    for r in policy.late_repeat_penalties.all():
        late_repeat.append({
            "id": r.id,
            "occurrences": r.occurrences,
            "penalty_type": r.penalty_type,
            "deduction_value": float(r.deduction_value or 0),
            "description": r.description,
        })

    return {
        "id": policy.id,
        "name": policy.name,
        "effective_from": str(policy.effective_from),
        "effective_to": str(policy.effective_to) if policy.effective_to else None,
        "status": policy.status,
        "notes": policy.notes,
        "approved_by": policy.approved_by.get_full_name() if policy.approved_by else None,
        "approved_at": str(policy.approved_at)[:16] if policy.approved_at else None,
        "created_at": str(policy.created_at)[:16],
        "assignments": assignments,
        "late_rules": late_rules,
        "absence_rules": absence_rules,
        "overtime_rules": overtime_rules,
        "night_shift_rules": night_rules,
        "weekend_work_rules": weekend_rules,
        "late_repeat_penalties": late_repeat,
    }


# ── LIST + CREATE ──
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def policy_list_create(request):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    from attendance.models import AttendancePolicy

    if request.method == "GET":
        policies = AttendancePolicy._base_manager.filter(
            company=company
        ).prefetch_related(
            'assignments', 'late_rules', 'absence_rules',
            'overtime_rules', 'night_shift_rules',
            'weekend_work_rules', 'late_repeat_penalties'
        ).order_by('-effective_from')
        return Response({
            "success": True,
            "policies": [_policy_data(p) for p in policies],
            "count": policies.count(),
        })

    # POST - إنشاء سياسة جديدة
    data = request.data
    name = str(data.get("name", "")).strip()
    effective_from = data.get("effective_from")

    if not name or not effective_from:
        return Response({"success": False, "error": "الاسم وتاريخ البداية مطلوبان"}, status=400)

    try:
        policy = AttendancePolicy._base_manager.create(
            company=company,
            name=name,
            effective_from=effective_from,
            effective_to=data.get("effective_to") or None,
            status='draft',
            notes=data.get("notes", ""),
            created_by=request.user,
        )

        # إضافة القواعد لو موجودة في الـ request
        _save_policy_rules(policy, data)

        return Response({
            "success": True,
            "message": f"تم إنشاء السياسة '{name}' بنجاح",
            "policy": _policy_data(policy),
        }, status=201)
    except Exception as e:
        logger.exception("policy_list_create error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── GET + UPDATE + DELETE ──
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def policy_detail(request, policy_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from attendance.models import AttendancePolicy

    try:
        policy = AttendancePolicy._base_manager.get(id=policy_id, company=company)
    except AttendancePolicy.DoesNotExist:
        return Response({"success": False, "error": "السياسة غير موجودة"}, status=404)

    if request.method == "GET":
        return Response({"success": True, "policy": _policy_data(policy)})

    if request.method == "DELETE":
        if policy.status == 'active':
            return Response({"success": False, "error": "لا يمكن حذف سياسة نشطة"}, status=400)
        policy.delete()
        return Response({"success": True, "message": "تم حذف السياسة"})

    # PUT - تعديل
    if policy.status == 'active':
        return Response({"success": False, "error": "لا يمكن تعديل سياسة نشطة - قم بإنشاء سياسة جديدة"}, status=400)

    data = request.data
    if "name" in data:
        policy.name = str(data["name"]).strip()
    if "effective_from" in data:
        policy.effective_from = data["effective_from"]
    if "effective_to" in data:
        policy.effective_to = data["effective_to"] or None
    if "notes" in data:
        policy.notes = data["notes"]
    policy.updated_by = request.user
    policy.save()

    _save_policy_rules(policy, data)

    return Response({
        "success": True,
        "message": "تم تحديث السياسة",
        "policy": _policy_data(policy),
    })


# ── APPROVE ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def policy_approve(request, policy_id):
    role = getattr(request.user, "role", None)
    if role not in OWNER_ROLES and not request.user.is_superuser:
        return Response({"success": False, "error": "الموافقة للـ Company Admin أو Super Admin فقط"}, status=403)

    company = _get_company(request)
    from attendance.models import AttendancePolicy

    try:
        policy = AttendancePolicy._base_manager.get(id=policy_id, company=company)
    except AttendancePolicy.DoesNotExist:
        return Response({"success": False, "error": "السياسة غير موجودة"}, status=404)

    if policy.status not in ('draft',):
        return Response({"success": False, "error": "السياسة مش في حالة مسودة"}, status=400)

    # أرشف أي سياسة active موجودة بنفس النطاق
    AttendancePolicy._base_manager.filter(
        company=company, status='active'
    ).update(status='archived')

    policy.status = 'active'
    policy.approved_by = request.user
    policy.approved_at = timezone.now()
    policy.save()

    return Response({
        "success": True,
        "message": f"تم اعتماد السياسة '{policy.name}' وتفعيلها",
    })


# ── ASSIGN TO BRANCH/DEPT/COMPANY ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def policy_assign(request, policy_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from attendance.models import AttendancePolicy, AttendancePolicyAssignment

    try:
        policy = AttendancePolicy._base_manager.get(id=policy_id, company=company)
    except AttendancePolicy.DoesNotExist:
        return Response({"success": False, "error": "السياسة غير موجودة"}, status=404)

    data = request.data
    assignment_type = str(data.get("assignment_type", "company")).strip()
    department_id = data.get("department_id")
    branch_id = data.get("branch_id")

    priority_map = {"department": 1, "branch": 2, "company": 3}
    priority = priority_map.get(assignment_type, 3)

    AttendancePolicyAssignment.objects.filter(
        policy__company=company,
        assignment_type=assignment_type,
        department_id=department_id,
        branch_id=branch_id,
    ).delete()

    assignment = AttendancePolicyAssignment.objects.create(
        company=company,
        policy=policy,
        assignment_type=assignment_type,
        department_id=department_id or None,
        branch_id=branch_id or None,
        priority=priority,
    )

    return Response({
        "success": True,
        "message": "تم ربط السياسة بنجاح",
        "assignment_id": assignment.id,
    })


def _save_policy_rules(policy, data):
    """حفظ قواعد السياسة"""
    from attendance.models import (
        LateRule, AbsenceRule, OvertimeRule,
        NightShiftRule, WeekendWorkRule, LateRepeatPenalty
    )

    # Late Rules
    if "late_rules" in data:
        policy.late_rules.all().delete()
        for i, rule in enumerate(data["late_rules"]):
            LateRule.objects.create(
                policy=policy,
                from_minutes=int(rule.get("from_minutes", 0)),
                to_minutes=int(rule.get("to_minutes", 15)),
                deduction_type=str(rule.get("deduction_type", "none")),
                deduction_value=float(rule.get("deduction_value", 0)),
                display_order=i,
            )

    # Absence Rules
    if "absence_rules" in data:
        policy.absence_rules.all().delete()
        for i, rule in enumerate(data["absence_rules"]):
            AbsenceRule.objects.create(
                policy=policy,
                absence_type=str(rule.get("absence_type", "unexcused")),
                consecutive_days=rule.get("consecutive_days"),
                occurrences_in_month=rule.get("occurrences_in_month"),
                deduction_type=str(rule.get("deduction_type", "day_fraction")),
                deduction_value=float(rule.get("deduction_value", 1)),
                display_order=i,
            )

    # Overtime Rules
    if "overtime_rules" in data:
        policy.overtime_rules.all().delete()
        for i, rule in enumerate(data["overtime_rules"]):
            OvertimeRule.objects.create(
                policy=policy,
                overtime_type=str(rule.get("overtime_type", "after_shift")),
                multiplier=float(rule.get("multiplier", 1.5)),
                min_minutes=int(rule.get("min_minutes", 30)),
                max_hours_per_day=rule.get("max_hours_per_day"),
                max_hours_per_month=rule.get("max_hours_per_month"),
                requires_approval=bool(rule.get("requires_approval", False)),
                display_order=i,
            )

    # Night Shift Rules
    if "night_shift_rules" in data:
        policy.night_shift_rules.all().delete()
        for rule in data["night_shift_rules"]:
            NightShiftRule.objects.create(
                policy=policy,
                allowance_type=str(rule.get("allowance_type", "fixed_amount")),
                amount=float(rule.get("amount", 0)),
                percentage=float(rule.get("percentage", 0)),
                night_start_hour=int(rule.get("night_start_hour", 20)),
                min_night_hours=int(rule.get("min_night_hours", 4)),
            )

    # Weekend Work Rules
    if "weekend_work_rules" in data:
        policy.weekend_work_rules.all().delete()
        for rule in data["weekend_work_rules"]:
            WeekendWorkRule.objects.create(
                policy=policy,
                compensation_type=str(rule.get("compensation_type", "overtime_multiplier")),
                multiplier=float(rule.get("multiplier", 2.0)),
                amount=float(rule.get("amount", 0)) or None,
            )

    # Late Repeat Penalties
    if "late_repeat_penalties" in data:
        policy.late_repeat_penalties.all().delete()
        for rule in data["late_repeat_penalties"]:
            LateRepeatPenalty.objects.create(
                policy=policy,
                occurrences=int(rule.get("occurrences", 3)),
                penalty_type=str(rule.get("penalty_type", "warning")),
                deduction_value=float(rule.get("deduction_value", 0)) or None,
                description=str(rule.get("description", "")),
            )
