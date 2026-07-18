from employees.visibility import get_visible_employees_qs, can_view_employee
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

MANAGER_ROLES = {"super_admin", "company_admin", "manager", "hr_manager"}


def _name_of(obj):
    if not obj:
        return None
    return getattr(obj, "name_ar", None) or getattr(obj, "name", None) or str(obj)


def _serialize_employee_full(emp):
    manager = None
    if emp.direct_manager:
        manager = {
            "id": emp.direct_manager.id,
            "name": getattr(emp.direct_manager, "full_name_ar", None) or str(emp.direct_manager),
        }
    parts = [emp.first_name_ar or "", emp.middle_name_ar or "", emp.last_name_ar or ""]
    full_ar = " ".join([p for p in parts if p]).strip()
    parts_en = [emp.first_name_en or "", emp.last_name_en or ""]
    full_en = " ".join([p for p in parts_en if p]).strip()
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "photo": emp.photo.url if emp.photo else None,
        "full_name_ar": full_ar,
        "full_name_en": full_en,
        "national_id": emp.national_id,
        "birth_date": str(emp.birth_date) if emp.birth_date else None,
        "gender": emp.get_gender_display() if emp.gender else None,
        "marital_status": emp.get_marital_status_display() if emp.marital_status else None,
        "religion": emp.get_religion_display() if emp.religion else None,
        "nationality": emp.nationality,
        "email": emp.email,
        "phone": emp.phone,
        "phone2": emp.phone2,
        "address": emp.address,
        "city": emp.city,
        "hire_date": str(emp.hire_date) if emp.hire_date else None,
        "contract_type": emp.get_contract_type_display() if emp.contract_type else None,
        "contract_end_date": str(emp.contract_end_date) if emp.contract_end_date else None,
        "branch": _name_of(emp.branch),
        "department": _name_of(emp.department),
        "job_title": _name_of(emp.job_title),
        "direct_manager": manager,
        "basic_salary": float(emp.basic_salary or 0),
        "bank_name": emp.bank_name,
        "bank_account": emp.bank_account,
        "iban": emp.iban,
        "status": emp.get_status_display() if hasattr(emp, "get_status_display") else None,
    }


def _serialize_employee_list(emp):
    parts = [emp.first_name_ar or "", emp.last_name_ar or ""]
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "photo": emp.photo.url if emp.photo else None,
        "full_name": " ".join([p for p in parts if p]).strip(),
        "job_title": _name_of(emp.job_title),
        "department": _name_of(emp.department),
        "branch": _name_of(emp.branch),
        "phone": emp.phone,
        "status": emp.get_status_display() if hasattr(emp, "get_status_display") else None,
        "status_code": emp.status if hasattr(emp, "status") else None,
    }


def _serialize_document(doc):
    today = date.today()
    return {
        "id": doc.id,
        "document_type": doc.get_document_type_display(),
        "document_type_code": doc.document_type,
        "title": doc.title,
        "file_url": doc.file.url if doc.file else None,
        "issue_date": str(doc.issue_date) if doc.issue_date else None,
        "expiry_date": str(doc.expiry_date) if doc.expiry_date else None,
        "is_expired": bool(doc.expiry_date and doc.expiry_date < today),
        "expires_soon": bool(doc.expiry_date and today <= doc.expiry_date <= today + timedelta(days=30)),
        "notes": doc.notes,
    }


def _serialize_movement(mv):
    return {
        "id": mv.id,
        "type": mv.get_movement_type_display() if hasattr(mv, "get_movement_type_display") else mv.movement_type,
        "type_code": mv.movement_type,
        "date": str(getattr(mv, "movement_date", None) or getattr(mv, "created_at", "")),
        "notes": getattr(mv, "notes", None) or getattr(mv, "description", None) or "",
    }


def _build_summary(emp):
    """يبني ملخص إحصائيات للموظف - الشهر الحالي + رصيد الإجازات + الطلبات"""
    from attendance.models import Attendance
    today = date.today()
    month_start = today.replace(day=1)

    # إحصائيات الحضور للشهر الحالي
    attendance_qs = Attendance.objects.filter(
        employee=emp,
        date__gte=month_start,
        date__lte=today,
    )
    total_days = attendance_qs.count()
    present_days = attendance_qs.filter(status="present").count()
    late_days = attendance_qs.filter(status="late").count()
    absent_days = attendance_qs.filter(status="absent").count()
    on_leave_days = attendance_qs.filter(status="on_leave").count()
    early_leave_days = attendance_qs.filter(status="early_leave").count()

    total_late_minutes = 0
    total_overtime_hours = 0.0
    total_work_hours = 0.0
    for att in attendance_qs:
        total_late_minutes += int(att.late_minutes or 0)
        try:
            total_overtime_hours += float(att.overtime_hours or 0)
            total_work_hours += float(att.work_hours or 0)
        except Exception:
            pass

    # أرصدة الإجازات
    leave_balances = []
    try:
        from leaves.models import LeaveBalance
        year = today.year
        balances = LeaveBalance.objects.filter(employee=emp, year=year).select_related("leave_type")
        for b in balances:
            leave_balances.append({
                "leave_type": _name_of(b.leave_type),
                "total": float(b.total_days or 0),
                "used": float(b.used_days or 0),
                "pending": float(b.pending_days or 0),
                "remaining": float(b.remaining_days or 0),
            })
    except Exception as e:
        logger.warning(f"leave balances error: {e}")

    # الطلبات
    requests_summary = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
    try:
        from requests_app.models import EmployeeRequest
        reqs = EmployeeRequest.objects.filter(employee=emp)
        requests_summary["total"] = reqs.count()
        requests_summary["pending"] = reqs.filter(status="pending").count()
        requests_summary["approved"] = reqs.filter(status="approved").count()
        requests_summary["rejected"] = reqs.filter(status="rejected").count()
    except Exception as e:
        logger.warning(f"requests summary error: {e}")

    # طلبات الإجازة
    leaves_summary = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
    try:
        from leaves.models import LeaveRequest
        lrs = LeaveRequest.objects.filter(employee=emp)
        leaves_summary["total"] = lrs.count()
        leaves_summary["pending"] = lrs.filter(status="pending").count()
        leaves_summary["approved"] = lrs.filter(status="approved").count()
        leaves_summary["rejected"] = lrs.filter(status="rejected").count()
    except Exception as e:
        logger.warning(f"leaves summary error: {e}")

    return {
        "month": today.strftime("%Y-%m"),
        "attendance": {
            "total_days": total_days,
            "present": present_days,
            "late": late_days,
            "absent": absent_days,
            "on_leave": on_leave_days,
            "early_leave": early_leave_days,
            "total_late_minutes": total_late_minutes,
            "total_overtime_hours": round(total_overtime_hours, 2),
            "total_work_hours": round(total_work_hours, 2),
        },
        "leave_balances": leave_balances,
        "requests": requests_summary,
        "leaves": leaves_summary,
    }


# ═══════════════════════════════════════════
# 6.7 - Employee endpoints (لنفس الموظف)
# ═══════════════════════════════════════════

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_profile(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"error": "no employee profile"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_employee_full(emp))
    except Exception as e:
        logger.exception("my_profile error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_documents(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"documents": []})
        docs = emp.documents.all().order_by("-created_at")
        return Response({"documents": [_serialize_document(d) for d in docs]})
    except Exception as e:
        logger.exception("my_documents error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_movements(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"movements": []})
        moves = emp.movements.all().order_by("-created_at")[:50]
        return Response({"movements": [_serialize_movement(m) for m in moves]})
    except Exception as e:
        logger.exception("my_movements error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_summary(request):
    try:
        emp = getattr(request.user, "employee_profile", None)
        if not emp:
            return Response({"error": "no employee profile"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_build_summary(emp))
    except Exception as e:
        logger.exception("my_summary error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════
# 6.8 - Manager endpoints (للمدير)
# ═══════════════════════════════════════════

def _check_manager(request):
    if getattr(request.user, "role", None) not in MANAGER_ROLES:
        return Response({"error": "غير مصرح"}, status=status.HTTP_403_FORBIDDEN)
    return None


def _get_employee_scoped(request, emp_id):
    """يجيب الموظف بس لو في نفس شركة المدير"""
    from employees.models import Employee
    qs = get_visible_employees_qs(request.user)
    return qs.filter(id=emp_id).first()


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_employees_list(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        from employees.models import Employee
        qs = get_visible_employees_qs(request.user).exclude(user=request.user).select_related("branch", "department", "job_title")
        # فلترة اختيارية
        search = request.GET.get("search", "").strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name_ar__icontains=search) |
                Q(last_name_ar__icontains=search) |
                Q(employee_code__icontains=search) |
                Q(phone__icontains=search)
            )
        status_filter = request.GET.get("status", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)

        qs = qs.order_by("first_name_ar", "last_name_ar")
        total = qs.count()
        data = [_serialize_employee_list(e) for e in qs]
        return Response({"count": total, "employees": data})
    except Exception as e:
        logger.exception("manager_employees_list error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_profile(request, emp_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"error": "الموظف غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_employee_full(emp))
    except Exception as e:
        logger.exception("manager_employee_profile error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_documents(request, emp_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"documents": []})
        docs = emp.documents.all().order_by("-created_at")
        return Response({"documents": [_serialize_document(d) for d in docs]})
    except Exception as e:
        logger.exception("manager_employee_documents error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_movements(request, emp_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"movements": []})
        moves = emp.movements.all().order_by("-created_at")[:100]
        return Response({"movements": [_serialize_movement(m) for m in moves]})
    except Exception as e:
        logger.exception("manager_employee_movements error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_summary(request, emp_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"error": "الموظف غير موجود"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_build_summary(emp))
    except Exception as e:
        logger.exception("manager_employee_summary error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
