"""
MotionHR - Disciplinary Actions API
إدارة الجزاءات التأديبية
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

from accounts.fcm_service import notify_disciplinary_action

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


def _action_data(action):
    return {
        "id": action.id,
        "employee_id": action.employee_id,
        "employee_name": getattr(action.employee, "full_name_ar", str(action.employee_id)),
        "action_type": action.action_type,
        "action_type_display": action.get_action_type_display(),
        "reason": action.reason,
        "deduction_amount": float(action.deduction_amount or 0),
        "status": action.status,
        "payroll_month": action.payroll_month,
        "payroll_applied": action.payroll_applied,
        "performed_by": action.performed_by.get_full_name() if action.performed_by else None,
        "performed_at": str(action.performed_at)[:16] if action.performed_at else None,
        "approved_by": action.approved_by.get_full_name() if action.approved_by else None,
        "approved_at": str(action.approved_at)[:16] if action.approved_at else None,
        "notes": action.notes,
    }


def _rule_data(rule):
    return {
        "id": rule.id,
        "violation_type": rule.violation_type,
        "violation_type_display": rule.get_violation_type_display(),
        "occurrence_from": rule.occurrence_from,
        "occurrence_to": rule.occurrence_to,
        "penalty_type": rule.penalty_type,
        "penalty_type_display": rule.get_penalty_type_display(),
        "deduction_days": float(rule.deduction_days),
        "deduction_amount": float(rule.deduction_amount),
        "description": rule.description,
        "display_order": rule.display_order,
    }


# ── قواعد الجزاءات في السياسة ──
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def disciplinary_rules(request, policy_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from attendance.models import AttendancePolicy, DisciplinaryRule

    try:
        policy = AttendancePolicy._base_manager.get(id=policy_id, company=company)
    except AttendancePolicy.DoesNotExist:
        return Response({"success": False, "error": "السياسة غير موجودة"}, status=404)

    if request.method == "GET":
        rules = policy.disciplinary_rules.all().order_by("violation_type", "occurrence_from")
        return Response({
            "success": True,
            "rules": [_rule_data(r) for r in rules],
            "count": rules.count(),
        })

    # POST - إضافة قاعدة
    data = request.data
    try:
        rule = DisciplinaryRule._base_manager.create(
            policy=policy,
            violation_type=str(data.get("violation_type", "policy_violation")),
            occurrence_from=int(data.get("occurrence_from", 1)),
            occurrence_to=int(data.get("occurrence_to", 1)),
            penalty_type=str(data.get("penalty_type", "verbal_warning")),
            deduction_days=float(data.get("deduction_days", 0)),
            deduction_amount=float(data.get("deduction_amount", 0)),
            description=str(data.get("description", "")),
            display_order=int(data.get("display_order", 0)),
        )
        return Response({"success": True, "rule": _rule_data(rule)}, status=201)
    except Exception as e:
        logger.exception("disciplinary_rules POST error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def disciplinary_rule_detail(request, policy_id, rule_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from attendance.models import AttendancePolicy, DisciplinaryRule

    try:
        policy = AttendancePolicy._base_manager.get(id=policy_id, company=company)
        rule = DisciplinaryRule._base_manager.get(id=rule_id, policy=policy)
    except (AttendancePolicy.DoesNotExist, DisciplinaryRule.DoesNotExist):
        return Response({"success": False, "error": "غير موجود"}, status=404)

    if request.method == "DELETE":
        rule.delete()
        return Response({"success": True, "message": "تم حذف القاعدة"})

    # PUT
    data = request.data
    for field, val in [
        ("violation_type", str),
        ("occurrence_from", int),
        ("occurrence_to", int),
        ("penalty_type", str),
        ("deduction_days", float),
        ("deduction_amount", float),
        ("description", str),
        ("display_order", int),
    ]:
        if field in data:
            setattr(rule, field, val(data[field]))
    rule.save()
    return Response({"success": True, "rule": _rule_data(rule)})


# ── جزاءات الموظفين ──
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def disciplinary_actions(request):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from attendance.models import DisciplinaryAction
    from employees.models import Employee

    if request.method == "GET":
        emp_id = request.query_params.get("employee_id")
        status_filter = request.query_params.get("status")
        month_filter = request.query_params.get("payroll_month")

        qs = DisciplinaryAction._base_manager.filter(
            employee__company=company
        ).select_related("employee", "performed_by", "approved_by")

        if emp_id:
            qs = qs.filter(employee_id=emp_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if month_filter:
            qs = qs.filter(payroll_month=month_filter)

        return Response({
            "success": True,
            "actions": [_action_data(a) for a in qs.order_by("-performed_at")],
            "count": qs.count(),
        })

    # POST - إضافة جزاء
    data = request.data
    emp_id = data.get("employee_id")
    if not emp_id:
        return Response({"success": False, "error": "employee_id مطلوب"}, status=400)

    try:
        employee = Employee._base_manager.get(id=emp_id, company=company)
    except Employee.DoesNotExist:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    try:
        action = DisciplinaryAction._base_manager.create(
            company=company,
            employee=employee,
            action_type=str(data.get("action_type", "verbal_warning")),
            reason=str(data.get("reason", "")),
            deduction_amount=float(data.get("deduction_amount", 0)),
            payroll_month=str(data.get("payroll_month", "")),
            notes=str(data.get("notes", "")),
            status="pending",
            performed_by=request.user,
        )
        return Response({"success": True, "action": _action_data(action)}, status=201)
    except Exception as e:
        logger.exception("disciplinary_actions POST error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def disciplinary_action_review(request, action_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from attendance.models import DisciplinaryAction

    try:
        action = DisciplinaryAction._base_manager.get(id=action_id, employee__company=company)
    except DisciplinaryAction.DoesNotExist:
        return Response({"success": False, "error": "الجزاء غير موجود"}, status=404)

    if action.status != "pending":
        return Response({"success": False, "error": "الجزاء مش في حالة معلق"}, status=400)

    decision = str(request.data.get("decision", "")).lower()
    if decision not in ("approve", "reject"):
        return Response({"success": False, "error": "القرار لازم يكون approve أو reject"}, status=400)

    if decision == "approve":
        action.status = "approved"
        action.approved_by = request.user
        action.approved_at = timezone.now()
        msg = "تم اعتماد الجزاء"
    else:
        action.status = "rejected"
        msg = "تم رفض الجزاء"

    action.notes = str(request.data.get("notes", action.notes))
    action.save()

    # إشعار الموظف بنتيجة الإجراء التأديبي
    if action.employee and action.employee.user:
        try:
            notify_disciplinary_action(
                user=action.employee.user,
                action_type_display=action.get_action_type_display(),
                approved=(decision == "approve"),
                reason=action.reason,
            )
        except Exception:
            pass

    return Response({"success": True, "message": msg, "action": _action_data(action)})
