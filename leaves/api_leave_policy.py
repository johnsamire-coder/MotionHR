"""
MotionHR - Leave Policy API
إدارة سياسات الإجازات
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

HR_ROLES = {"super_admin", "company_admin", "hr_manager"}


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


def _tier_data(tier):
    return {
        "id": tier.id,
        "from_months": tier.from_months,
        "to_months": tier.to_months,
        "annual_entitlement_days": float(tier.annual_entitlement_days),
        "description": tier.description,
    }


def _type_rule_data(rule):
    return {
        "id": rule.id,
        "leave_type_id": rule.leave_type_id,
        "leave_type_name": rule.leave_type.name if rule.leave_type else None,
        "enabled": rule.enabled,
        "entitlement_mode": rule.entitlement_mode,
        "fixed_days": float(rule.fixed_days),
        "parent_leave_type_id": rule.parent_leave_type_id,
        "subset_limit_days": float(rule.subset_limit_days),
        "requires_balance": rule.requires_balance,
        "allow_negative_balance": rule.allow_negative_balance,
        "negative_limit_days": float(rule.negative_limit_days),
        "allow_half_day": rule.allow_half_day,
        "allow_hourly": rule.allow_hourly,
        "max_days_per_request": rule.max_days_per_request,
        "max_requests_per_year": rule.max_requests_per_year,
        "can_use_during_probation": rule.can_use_during_probation,
        "carry_mode": rule.carry_mode,
        "carry_percentage": float(rule.carry_percentage),
        "carry_max_days": float(rule.carry_max_days),
        "cash_compensation_enabled": rule.cash_compensation_enabled,
        "cash_compensation_basis": rule.cash_compensation_basis,
    }


def _policy_data(policy):
    return {
        "id": policy.id,
        "name": policy.name,
        "effective_from": str(policy.effective_from),
        "effective_to": str(policy.effective_to) if policy.effective_to else None,
        "status": policy.status,
        "probation_months": policy.probation_months,
        "probation_leave_mode": policy.probation_leave_mode,
        "accrual_mode": policy.accrual_mode,
        "notes": policy.notes,
        "approved_by": policy.approved_by.get_full_name() if policy.approved_by else None,
        "approved_at": str(policy.approved_at)[:16] if policy.approved_at else None,
        "created_at": str(policy.created_at)[:16],
        "tiers": [_tier_data(t) for t in policy.tiers.all().order_by("from_months")],
        "type_rules": [_type_rule_data(r) for r in policy.type_rules.all().select_related("leave_type")],
    }


# ── قائمة السياسات + إنشاء ──
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leave_policy_list_create(request):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    from leaves.models import LeavePolicy

    if request.method == "GET":
        policies = LeavePolicy._base_manager.filter(
            company=company
        ).prefetch_related("tiers", "type_rules__leave_type").order_by("-effective_from")
        return Response({
            "success": True,
            "policies": [_policy_data(p) for p in policies],
            "count": policies.count(),
        })

    data = request.data
    name = str(data.get("name", "")).strip()
    effective_from = data.get("effective_from")

    if not name or not effective_from:
        return Response({"success": False, "error": "الاسم وتاريخ البداية مطلوبان"}, status=400)

    try:
        policy = LeavePolicy._base_manager.create(
            company=company,
            name=name,
            effective_from=effective_from,
            effective_to=data.get("effective_to") or None,
            status="draft",
            probation_months=int(data.get("probation_months", 3)),
            probation_leave_mode=str(data.get("probation_leave_mode", "blocked")),
            accrual_mode=str(data.get("accrual_mode", "annual_lump")),
            notes=str(data.get("notes", "")),
            created_by=request.user,
        )
        _save_policy_details(policy, data)
        return Response({"success": True, "policy": _policy_data(policy)}, status=201)
    except Exception as e:
        logger.exception("leave_policy_list_create POST error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── تفاصيل سياسة + تعديل + حذف ──
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leave_policy_detail(request, policy_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from leaves.models import LeavePolicy

    try:
        policy = LeavePolicy._base_manager.get(id=policy_id, company=company)
    except LeavePolicy.DoesNotExist:
        return Response({"success": False, "error": "السياسة غير موجودة"}, status=404)

    if request.method == "GET":
        return Response({"success": True, "policy": _policy_data(policy)})

    if request.method == "DELETE":
        if policy.status == "active":
            return Response({"success": False, "error": "لا يمكن حذف سياسة نشطة"}, status=400)
        policy.delete()
        return Response({"success": True, "message": "تم حذف السياسة"})

    data = request.data
    for field, cast in [
        ("name", str), ("effective_from", str), ("effective_to", str),
        ("probation_months", int), ("probation_leave_mode", str),
        ("accrual_mode", str), ("notes", str),
    ]:
        if field in data:
            val = cast(data[field]) if data[field] else None
            setattr(policy, field, val if field != "effective_to" else (val or None))
    policy.updated_by = request.user
    policy.save()
    _save_policy_details(policy, data)
    return Response({"success": True, "policy": _policy_data(policy)})


# ── اعتماد السياسة ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leave_policy_approve(request, policy_id):
    role = getattr(request.user, "role", None)
    if role not in {"super_admin", "company_admin"} and not request.user.is_superuser:
        return Response({"success": False, "error": "الاعتماد للـ Company Admin فقط"}, status=403)

    company = _get_company(request)
    from leaves.models import LeavePolicy

    try:
        policy = LeavePolicy._base_manager.get(id=policy_id, company=company)
    except LeavePolicy.DoesNotExist:
        return Response({"success": False, "error": "السياسة غير موجودة"}, status=404)

    if policy.status != "draft":
        return Response({"success": False, "error": "السياسة مش مسودة"}, status=400)

    LeavePolicy._base_manager.filter(company=company, status="active").update(status="archived")
    policy.status = "active"
    policy.approved_by = request.user
    policy.approved_at = timezone.now()
    policy.save()

    return Response({"success": True, "message": f"تم اعتماد سياسة '{policy.name}'"})


# ── تعديل أرصدة الإجازات (للموظفين القدامى) ──
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leave_balance_adjustments(request):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from leaves.models import LeaveBalanceAdjustment, LeaveBalance, LeaveType
    from employees.models import Employee

    if request.method == "GET":
        emp_id = request.query_params.get("employee_id")
        year = request.query_params.get("year")
        qs = LeaveBalanceAdjustment._base_manager.filter(
            employee__company=company
        ).select_related("employee", "leave_type", "created_by").order_by("-created_at")
        if emp_id:
            qs = qs.filter(employee_id=emp_id)
        if year:
            qs = qs.filter(year=year)
        return Response({
            "success": True,
            "adjustments": [{
                "id": a.id,
                "employee_id": a.employee_id,
                "employee_name": getattr(a.employee, "full_name_ar", str(a.employee_id)),
                "leave_type_id": a.leave_type_id,
                "leave_type_name": a.leave_type.name if a.leave_type else None,
                "year": a.year,
                "adjustment_type": a.adjustment_type,
                "days": float(a.days),
                "reason": a.reason,
                "created_by": a.created_by.get_full_name() if a.created_by else None,
                "created_at": str(a.created_at)[:16],
            } for a in qs],
        })

    data = request.data
    emp_id = data.get("employee_id")
    leave_type_id = data.get("leave_type_id")
    year = data.get("year")
    days = data.get("days")

    if not all([emp_id, leave_type_id, year, days is not None]):
        return Response({"success": False, "error": "employee_id و leave_type_id و year و days مطلوبين"}, status=400)

    try:
        employee = Employee._base_manager.get(id=emp_id, company=company)
        leave_type = LeaveType._base_manager.get(id=leave_type_id, company=company)
        days_val = float(days)

        adj = LeaveBalanceAdjustment._base_manager.create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            year=int(year),
            adjustment_type=str(data.get("adjustment_type", "manual_add")),
            days=days_val,
            reason=str(data.get("reason", "")),
            created_by=request.user,
        )

        balance, created = LeaveBalance._base_manager.get_or_create(
            company=company,
            employee=employee,
            leave_type=leave_type,
            year=int(year),
            defaults={"total_days": 0},
        )
        balance.total_days = float(balance.total_days) + days_val
        balance.save()

        return Response({
            "success": True,
            "message": f"تم تعديل رصيد {leave_type.name} للموظف {employee.full_name_ar}",
            "new_balance": float(balance.total_days),
            "adjustment_id": adj.id,
        }, status=201)

    except Exception as e:
        logger.exception("leave_balance_adjustments POST error")
        return Response({"success": False, "error": str(e)}, status=500)


def _save_policy_details(policy, data):
    from leaves.models import LeavePolicyTier, LeavePolicyTypeRule

    if "tiers" in data:
        policy.tiers.all().delete()
        for tier in data["tiers"]:
            LeavePolicyTier.objects.create(
                policy=policy,
                from_months=int(tier.get("from_months", 0)),
                to_months=tier.get("to_months") or None,
                annual_entitlement_days=float(tier.get("annual_entitlement_days", 21)),
                description=str(tier.get("description", "")),
            )

    if "type_rules" in data:
        policy.type_rules.all().delete()
        for rule in data["type_rules"]:
            LeavePolicyTypeRule.objects.create(
                policy=policy,
                leave_type_id=int(rule["leave_type_id"]),
                enabled=bool(rule.get("enabled", True)),
                entitlement_mode=str(rule.get("entitlement_mode", "from_service_tier")),
                fixed_days=float(rule.get("fixed_days", 0)),
                parent_leave_type_id=rule.get("parent_leave_type_id") or None,
                subset_limit_days=float(rule.get("subset_limit_days", 0)),
                requires_balance=bool(rule.get("requires_balance", True)),
                allow_negative_balance=bool(rule.get("allow_negative_balance", False)),
                negative_limit_days=float(rule.get("negative_limit_days", 0)),
                allow_half_day=bool(rule.get("allow_half_day", True)),
                allow_hourly=bool(rule.get("allow_hourly", False)),
                max_days_per_request=int(rule.get("max_days_per_request", 0)),
                max_requests_per_year=int(rule.get("max_requests_per_year", 0)),
                can_use_during_probation=bool(rule.get("can_use_during_probation", False)),
                carry_mode=str(rule.get("carry_mode", "none")),
                carry_percentage=float(rule.get("carry_percentage", 100)),
                carry_max_days=float(rule.get("carry_max_days", 0)),
                cash_compensation_enabled=bool(rule.get("cash_compensation_enabled", False)),
                cash_compensation_basis=str(rule.get("cash_compensation_basis", "basic_salary")),
            )
