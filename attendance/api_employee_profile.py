def _get_emp_effective_shift(emp):
    if not emp:
        return None
    try:
        from attendance.models import EmployeeShift, ShiftAssignment, Shift
        es = EmployeeShift._base_manager.filter(employee=emp, is_active=True).select_related('shift').first()
        if es and es.shift and es.shift.is_active:
            s = es.shift
            return {
                "id": s.id,
                "name": s.name,
                "start_time": str(s.start_time)[:5] if s.start_time else "",
                "end_time": str(s.end_time)[:5] if s.end_time else "",
                "shift_type": s.shift_type,
            }
        if emp.department:
            sa = ShiftAssignment._base_manager.filter(company=emp.company, department=emp.department, is_active=True).select_related('shift').first()
            if sa and sa.shift and sa.shift.is_active:
                s = sa.shift
                return {
                    "id": s.id,
                    "name": s.name,
                    "start_time": str(s.start_time)[:5] if s.start_time else "",
                    "end_time": str(s.end_time)[:5] if s.end_time else "",
                    "shift_type": s.shift_type,
                }
        if emp.branch:
            sa = ShiftAssignment._base_manager.filter(company=emp.company, branch=emp.branch, is_active=True).select_related('shift').first()
            if sa and sa.shift and sa.shift.is_active:
                s = sa.shift
                return {
                    "id": s.id,
                    "name": s.name,
                    "start_time": str(s.start_time)[:5] if s.start_time else "",
                    "end_time": str(s.end_time)[:5] if s.end_time else "",
                    "shift_type": s.shift_type,
                }
        s_def = Shift._base_manager.filter(company=emp.company, is_default=True, is_active=True).first()
        if s_def:
            return {
                "id": s_def.id,
                "name": s_def.name,
                "start_time": str(s_def.start_time)[:5] if s_def.start_time else "",
                "end_time": str(s_def.end_time)[:5] if s_def.end_time else "",
                "shift_type": s_def.shift_type,
            }
    except Exception:
        pass
    return None

from employees.visibility import get_visible_employees_qs, can_view_employee
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
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
        "worker_type": getattr(emp, "worker_type", "office") or "office",
        "worker_type_display": {"office": "مكتبي", "field_free": "ميداني حر", "field_assigned": "ميداني محدد"}.get(getattr(emp, "worker_type", "office") or "office", "مكتبي"),
        "shift": _get_emp_effective_shift(emp),
        "shift_name": _get_emp_effective_shift(emp)["name"] if _get_emp_effective_shift(emp) else "غير معين",
        "shift_timing": f"{_get_emp_effective_shift(emp)['start_time']} - {_get_emp_effective_shift(emp)['end_time']}" if _get_emp_effective_shift(emp) and _get_emp_effective_shift(emp).get('start_time') else "",

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
        "department_id": emp.department_id,
        "branch": _name_of(emp.branch),
        "branch_id": emp.branch_id,
        "phone": emp.phone,
        "national_id": emp.national_id,
        "status": emp.get_status_display() if hasattr(emp, "get_status_display") else None,
        "status_code": emp.status if hasattr(emp, "status") else None,
        "hire_date": str(emp.hire_date) if emp.hire_date else None,
        "basic_salary": float(emp.basic_salary) if emp.basic_salary is not None else None,
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
    attendance_qs = Attendance._base_manager.filter(
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
        balances = LeaveBalance._base_manager.filter(employee=emp, year=year).select_related("leave_type")
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
        reqs = EmployeeRequest._base_manager.filter(employee=emp)
        requests_summary["total"] = reqs.count()
        requests_summary["pending"] = reqs.filter(status="pending").count()
        requests_summary["approved"] = reqs.filter(status="approved").count()
        requests_summary["rejected"] = reqs.filter(status="rejected").count()
    except Exception as e:
        logger.warning(f"requests summary error: {e}")

    # طلبات الإجازة
    leaves_summary = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
    leaves_list = []
    try:
        from leaves.models import LeaveRequest
        lrs = LeaveRequest._base_manager.filter(employee=emp)
        leaves_summary["total"] = lrs.count()
        leaves_summary["pending"] = lrs.filter(status="pending").count()
        leaves_summary["approved"] = lrs.filter(status="approved").count()
        leaves_summary["rejected"] = lrs.filter(status="rejected").count()

        for lr in lrs.select_related("leave_type").order_by("-start_date")[:100]:
            leaves_list.append({
                "id": lr.id,
                "leave_type": _name_of(getattr(lr, "leave_type", None)) or "",
                "start_date": str(lr.start_date) if lr.start_date else None,
                "end_date": str(lr.end_date) if lr.end_date else None,
                "days_count": float(lr.days_count) if lr.days_count else 0,
                "status": lr.status or "",
                "reason": lr.reason or "",
                "created_at": str(lr.created_at) if getattr(lr, "created_at", None) else None,
            })
    except Exception as e:
        logger.warning(f"leaves summary error: {e}")

    # قائمة الطلبات الكاملة
    requests_list = []
    try:
        from requests_app.models import EmployeeRequest
        for req in EmployeeRequest._base_manager.filter(employee=emp).select_related("request_type").order_by("-created_at")[:100]:
            requests_list.append({
                "id": req.id,
                "type_name": _name_of(getattr(req, "request_type", None)) or "",
                "subject": req.subject or "",
                "details": req.details or "",
                "status": req.status or "",
                "start_date": str(req.start_date) if req.start_date else None,
                "end_date": str(req.end_date) if req.end_date else None,
                "amount": float(req.amount) if req.amount else None,
                "created_at": str(req.created_at) if getattr(req, "created_at", None) else None,
            })
    except Exception as e:
        logger.warning(f"requests list error: {e}")

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
        "requests_list": requests_list,
        "leaves": leaves_summary,
        "leaves_list": leaves_list,
    }


# ═══════════════════════════════════════════
# 6.7 - Employee endpoints (لنفس الموظف)
# ═══════════════════════════════════════════

@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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

        department_filter = request.GET.get("department", "").strip()
        if department_filter:
            try:
                qs = qs.filter(department_id=int(department_filter))
            except (ValueError, TypeError):
                qs = qs.filter(department__name_ar__icontains=department_filter)

        branch_filter = request.GET.get("branch", "").strip()
        if branch_filter:
            try:
                qs = qs.filter(branch_id=int(branch_filter))
            except (ValueError, TypeError):
                pass

        worker_type_filter = request.GET.get("worker_type", "").strip()
        if worker_type_filter:
            qs = qs.filter(worker_type=worker_type_filter)

        page_size = int(request.GET.get("page_size", 25))
        page = int(request.GET.get("page", 1))
        offset = (page - 1) * page_size

        qs = qs.order_by("first_name_ar", "last_name_ar")
        total = qs.count()

        active_count = qs.filter(status="active").count()
        inactive_count = qs.exclude(status="active").exclude(status="on_leave").count()
        on_leave_count = qs.filter(status="on_leave").count()

        paged_qs = qs[offset:offset + page_size]
        data = [_serialize_employee_list(e) for e in paged_qs]

        total_pages = max(1, (total + page_size - 1) // page_size)

        return Response({
            "count": total,
            "total": total,
            "employees": data,
            "results": data,
            "total_pages": total_pages,
            "current_page": page,
            "stats": {
                "total": total,
                "active": active_count,
                "inactive": inactive_count,
                "on_leave": on_leave_count,
            }
        })
    except Exception as e:
        logger.exception("manager_employees_list error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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


# ═══════════════════════════════════════════
# E-T17: Attendance / Leaves / Requests tabs
# ═══════════════════════════════════════════

@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_attendance(request, emp_id):
    """حضور موظف واحد — للمدير"""
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"error": "الموظف غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        from attendance.models import Attendance
        from django.utils import timezone

        # فلترة بالتاريخ (اختيارية)
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        qs = Attendance._base_manager.filter(employee=emp).order_by("-date")

        if date_from:
            try:
                from datetime import date
                qs = qs.filter(date__gte=date_from)
            except Exception:
                pass
        if date_to:
            try:
                qs = qs.filter(date__lte=date_to)
            except Exception:
                pass

        qs = qs[:90]  # آخر 90 يوم كحد أقصى

        records = []
        for att in qs:
            records.append({
                "date": str(att.date),
                "status": att.status,
                "check_in": timezone.localtime(att.check_in_time).strftime("%I:%M %p") if att.check_in_time else None,
                "check_out": timezone.localtime(att.check_out_time).strftime("%I:%M %p") if att.check_out_time else None,
                "work_hours": float(att.work_hours or 0),
                "late_minutes": int(att.late_minutes or 0),
                "overtime_hours": float(att.overtime_hours or 0),
            })

        return Response({"attendance": records, "count": len(records)})
    except Exception as e:
        logger.exception("manager_employee_attendance error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_leaves(request, emp_id):
    """إجازات موظف واحد — للمدير"""
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"error": "الموظف غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        from leaves.models import LeaveRequest

        qs = LeaveRequest._base_manager.filter(employee=emp).order_by("-created_at")[:50]

        records = []
        for lv in qs:
            records.append({
                "id": lv.id,
                "leave_type": str(lv.leave_type) if lv.leave_type else "",
                "start_date": str(lv.start_date) if lv.start_date else None,
                "end_date": str(lv.end_date) if lv.end_date else None,
                "days": float(lv.days_count or 0),
                "status": lv.status,
                "reason": lv.reason or "",
                "created_at": lv.created_at.strftime("%Y-%m-%d") if lv.created_at else None,
            })

        return Response({"leaves": records, "count": len(records)})
    except Exception as e:
        logger.exception("manager_employee_leaves error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_requests(request, emp_id):
    """طلبات موظف واحد — للمدير"""
    err = _check_manager(request)
    if err:
        return err
    try:
        emp = _get_employee_scoped(request, emp_id)
        if not emp:
            return Response({"error": "الموظف غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        from requests_app.models import EmployeeRequest

        qs = EmployeeRequest._base_manager.filter(employee=emp).order_by("-created_at")[:50]

        records = []
        for req in qs:
            records.append({
                "id": req.id,
                "request_type": str(req.request_type) if req.request_type else "",
                "title": req.title or "",
                "status": req.status,
                "created_at": req.created_at.strftime("%Y-%m-%d") if req.created_at else None,
                "notes": req.notes or "",
            })

        return Response({"requests": records, "count": len(records)})
    except Exception as e:
        logger.exception("manager_employee_requests error")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employees_export_excel(request):
    """تصدير كشف الموظفين Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    qs = get_visible_employees_qs(request.user).exclude(user=request.user).select_related("branch", "department", "job_title").order_by("first_name_ar", "last_name_ar")

    rows = []
    for emp in qs:
        parts = [emp.first_name_ar or "", emp.last_name_ar or ""]
        rows.append({
            "employee_code": emp.employee_code or "",
            "full_name": " ".join([p for p in parts if p]).strip(),
            "department": _name_of(emp.department),
            "job_title": _name_of(emp.job_title),
            "phone": emp.phone or "",
            "status": emp.get_status_display() if hasattr(emp, "get_status_display") else "",
            "hire_date": str(emp.hire_date) if emp.hire_date else "",
            "basic_salary": float(emp.basic_salary) if emp.basic_salary is not None else "",
        })

    columns = [
        ("employee_code", "الكود", 12),
        ("full_name", "الاسم", 24),
        ("department", "القسم", 18),
        ("job_title", "المسمى", 18),
        ("phone", "الموبايل", 14),
        ("status", "الحالة", 12),
        ("hire_date", "تاريخ التعيين", 14),
        ("basic_salary", "الراتب", 12),
    ]
    return export_to_excel(title="كشف الموظفين", columns=columns, rows=rows, user=request.user, filename="employees.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employees_export_pdf(request):
    """تصدير كشف الموظفين PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    qs = get_visible_employees_qs(request.user).exclude(user=request.user).select_related("branch", "department", "job_title").order_by("first_name_ar", "last_name_ar")

    rows = []
    for emp in qs:
        parts = [emp.first_name_ar or "", emp.last_name_ar or ""]
        rows.append({
            "employee_code": emp.employee_code or "",
            "full_name": " ".join([p for p in parts if p]).strip(),
            "department": _name_of(emp.department),
            "job_title": _name_of(emp.job_title),
            "phone": emp.phone or "",
            "status": emp.get_status_display() if hasattr(emp, "get_status_display") else "",
            "hire_date": str(emp.hire_date) if emp.hire_date else "",
            "basic_salary": float(emp.basic_salary) if emp.basic_salary is not None else "",
        })

    columns = [
        ("employee_code", "الكود", 12),
        ("full_name", "الاسم", 24),
        ("department", "القسم", 18),
        ("job_title", "المسمى", 18),
        ("phone", "الموبايل", 14),
        ("status", "الحالة", 12),
        ("hire_date", "تاريخ التعيين", 14),
        ("basic_salary", "الراتب", 12),
    ]
    return export_to_pdf(title="كشف الموظفين", columns=columns, rows=rows, user=request.user, filename="employees.pdf")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_attendance_export_excel(request):
    """تصدير تقرير الحضور اليومي Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel
    from attendance.models import Attendance
    from django.utils import timezone
    from datetime import datetime

    company = getattr(request.user, "company", None)
    date_str = request.GET.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    records = Attendance._base_manager.filter(date=target_date).select_related("employee", "employee__department").order_by("employee__first_name_ar")
    if company:
        records = records.filter(company=company)

    def fmt_time(dt):
        if not dt:
            return ""
        try:
            return timezone.localtime(dt).strftime("%I:%M %p")
        except Exception:
            return str(dt)

    status_labels = {
        "present": "حاضر", "late": "متأخر", "absent": "غائب",
        "on_leave": "إجازة", "weekend": "عطلة", "mission": "مهمة",
    }

    rows = []
    for att in records:
        emp = att.employee
        emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else ""
        rows.append({
            "employee_name": emp_name,
            "department": _name_of(emp.department) if emp else "",
            "status": status_labels.get(getattr(att, "status", ""), getattr(att, "status", "")),
            "check_in": fmt_time(getattr(att, "check_in_time", None)),
            "check_out": fmt_time(getattr(att, "check_out_time", None)),
            "late_minutes": getattr(att, "late_minutes", 0) or 0,
            "work_hours": float(getattr(att, "work_hours", 0) or 0),
        })

    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("status", "الحالة", 12),
        ("check_in", "حضور", 12),
        ("check_out", "انصراف", 12),
        ("late_minutes", "تأخير (د)", 12),
        ("work_hours", "ساعات العمل", 14),
    ]
    subtitle = f"تاريخ: {target_date.strftime('%Y-%m-%d')}"
    return export_to_excel(title="تقرير الحضور اليومي", columns=columns, rows=rows, user=request.user, filename="attendance.xlsx", subtitle=subtitle)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_attendance_export_pdf(request):
    """تصدير تقرير الحضور اليومي PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf
    from attendance.models import Attendance
    from django.utils import timezone
    from datetime import datetime

    company = getattr(request.user, "company", None)
    date_str = request.GET.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    records = Attendance._base_manager.filter(date=target_date).select_related("employee", "employee__department").order_by("employee__first_name_ar")
    if company:
        records = records.filter(company=company)

    def fmt_time(dt):
        if not dt:
            return ""
        try:
            return timezone.localtime(dt).strftime("%I:%M %p")
        except Exception:
            return str(dt)

    status_labels = {
        "present": "حاضر", "late": "متأخر", "absent": "غائب",
        "on_leave": "إجازة", "weekend": "عطلة", "mission": "مهمة",
    }

    rows = []
    for att in records:
        emp = att.employee
        emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else ""
        rows.append({
            "employee_name": emp_name,
            "department": _name_of(emp.department) if emp else "",
            "status": status_labels.get(getattr(att, "status", ""), getattr(att, "status", "")),
            "check_in": fmt_time(getattr(att, "check_in_time", None)),
            "check_out": fmt_time(getattr(att, "check_out_time", None)),
            "late_minutes": getattr(att, "late_minutes", 0) or 0,
            "work_hours": float(getattr(att, "work_hours", 0) or 0),
        })

    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("status", "الحالة", 12),
        ("check_in", "حضور", 12),
        ("check_out", "انصراف", 12),
        ("late_minutes", "تأخير (د)", 12),
        ("work_hours", "ساعات العمل", 14),
    ]
    subtitle = f"تاريخ: {target_date.strftime('%Y-%m-%d')}"
    return export_to_pdf(title="تقرير الحضور اليومي", columns=columns, rows=rows, user=request.user, filename="attendance.pdf", subtitle=subtitle)


def _leaves_export_data(request):
    """داتا الإجازات (خام - status بالإنجليزي) - للتصدير والقائمة"""
    from leaves.models import LeaveRequest

    company = getattr(request.user, "company", None)
    status_filter = request.GET.get("status", "").strip()
    all_pending = request.GET.get("all_pending", "").strip()
    year = request.GET.get("year", "").strip()
    month = request.GET.get("month", "").strip()

    qs = LeaveRequest._base_manager.filter(employee__company=company).select_related(
        "employee", "employee__department", "leave_type"
    ).order_by("-start_date")

    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)

    # لو all_pending مفعّل، نتجاهل فلتر الشهر/السنة عشان يطابق الداشبورد
    if not (status_filter == "pending" and all_pending):
        if year and month:
            try:
                from datetime import date
                from calendar import monthrange
                y, m = int(year), int(month)
                first_day = date(y, m, 1)
                last_day = date(y, m, monthrange(y, m)[1])
                qs = qs.filter(start_date__gte=first_day, start_date__lte=last_day)
            except (ValueError, TypeError):
                pass
        elif year:
            try:
                y = int(year)
                qs = qs.filter(start_date__year=y)
            except (ValueError, TypeError):
                pass

    rows = []
    for lv in qs:
        emp = lv.employee
        days = int(getattr(lv, "days_count", 0) or 0)
        if days == 0:
            try:
                days = (lv.end_date - lv.start_date).days + 1
            except Exception:
                days = 1
        rows.append({
            "employee_name": _name_of(emp) if emp else "",
            "department": _name_of(emp.department) if emp and emp.department else "",
            "leave_type": str(lv.leave_type) if lv.leave_type else "",
            "from_date": str(lv.start_date) if lv.start_date else "",
            "to_date": str(lv.end_date) if lv.end_date else "",
            "days": days,
            "status": lv.status,
        })
    return rows


_LEAVE_STATUS_LABELS_AR = {
    "pending": "معلق", "approved": "مقبول",
    "rejected": "مرفوض", "cancelled": "ملغي",
}


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_leaves_export_excel(request):
    """تصدير تقرير الإجازات Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _leaves_export_data(request)
    for r in rows:
        r["status"] = _LEAVE_STATUS_LABELS_AR.get(r["status"], r["status"])

    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("leave_type", "النوع", 16),
        ("from_date", "من", 14),
        ("to_date", "إلى", 14),
        ("days", "أيام", 10),
        ("status", "الحالة", 12),
    ]
    return export_to_excel(title="تقرير الإجازات", columns=columns, rows=rows, user=request.user, filename="leaves.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_leaves_export_pdf(request):
    """تصدير تقرير الإجازات PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _leaves_export_data(request)
    for r in rows:
        r["status"] = _LEAVE_STATUS_LABELS_AR.get(r["status"], r["status"])

    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("leave_type", "النوع", 16),
        ("from_date", "من", 14),
        ("to_date", "إلى", 14),
        ("days", "أيام", 10),
        ("status", "الحالة", 12),
    ]
    return export_to_pdf(title="تقرير الإجازات", columns=columns, rows=rows, user=request.user, filename="leaves.pdf")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_leaves_list(request):
    """قائمة الإجازات للمدير (لصفحة hr/leaves)"""
    err = _check_manager(request)
    if err:
        return err

    rows = _leaves_export_data(request)
    stats = {
        "total": len(rows),
        "pending": len([r for r in rows if r["status"] == "pending"]),
        "approved": len([r for r in rows if r["status"] == "approved"]),
        "rejected": len([r for r in rows if r["status"] == "rejected"]),
    }
    return Response({"leaves": rows, "stats": stats, "count": len(rows)})


def _requests_export_data(request):
    """داتا الطلبات لتصدير الإكسل/PDF"""
    from requests_app.models import EmployeeRequest

    company = getattr(request.user, "company", None)
    status_filter = request.GET.get("status", "").strip()

    qs = EmployeeRequest._base_manager.filter(employee__company=company).select_related(
        "employee", "employee__department", "request_type"
    ).order_by("-created_at")

    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)

    rows = []
    for r in qs:
        emp = r.employee
        rows.append({
            "employee_name": _name_of(emp) if emp else "",
            "department": _name_of(emp.department) if emp and emp.department else "",
            "request_type": str(r.request_type) if r.request_type else "",
            "subject": getattr(r, "subject", "") or "",
            "status": r.status,
            "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
        })
    return rows


_REQUEST_STATUS_LABELS_AR = {
    "pending": "قيد الانتظار", "manager_approved": "موافقة المدير",
    "hr_approved": "موافقة HR", "approved": "موافق عليه",
    "rejected": "مرفوض", "cancelled": "ملغي",
}


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_requests_export_excel(request):
    """تصدير تقرير الطلبات Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _requests_export_data(request)
    for r in rows:
        r["status"] = _REQUEST_STATUS_LABELS_AR.get(r["status"], r["status"])

    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("request_type", "نوع الطلب", 20),
        ("subject", "السبب", 26),
        ("status", "الحالة", 14),
        ("created_at", "التاريخ", 14),
    ]
    return export_to_excel(title="تقرير الطلبات", columns=columns, rows=rows, user=request.user, filename="requests.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_requests_export_pdf(request):
    """تصدير تقرير الطلبات PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _requests_export_data(request)
    for r in rows:
        r["status"] = _REQUEST_STATUS_LABELS_AR.get(r["status"], r["status"])

    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("request_type", "نوع الطلب", 20),
        ("subject", "السبب", 26),
        ("status", "الحالة", 14),
        ("created_at", "التاريخ", 14),
    ]
    return export_to_pdf(title="تقرير الطلبات", columns=columns, rows=rows, user=request.user, filename="requests.pdf")


def _payroll_export_data(request):
    """داتا الرواتب لتصدير الإكسل/PDF (نفس منطق payroll_summary)"""
    from attendance.api_payroll import _get_company_employees, _get_payroll_settings, _parse_month, _get_lang
    from attendance.payroll_rules import calculate_effective_payroll
    import calendar
    from datetime import date

    year, month = _parse_month(request)
    lang = _get_lang(request)
    employees = _get_company_employees(request.user)
    settings = _get_payroll_settings(request.user)

    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    rows = []
    for emp in employees:
        if emp.hire_date and emp.hire_date > month_end:
            continue
        if getattr(emp, "termination_date", None) and emp.termination_date < month_start:
            continue
        payroll = calculate_effective_payroll(emp, year, month, settings, lang=lang)
        rows.append({
            "employee_code": getattr(emp, "employee_code", "") or "",
            "employee_name": payroll.get("employee_name", ""),
            "department": payroll.get("department_name", ""),
            "basic_salary": payroll.get("basic_salary", 0),
            "allowances_total": payroll.get("allowances_total", 0),
            "overtime_bonus": payroll.get("overtime_bonus", 0),
            "total_deductions": payroll.get("total_deductions", 0),
            "net_salary": payroll.get("net_salary", 0),
        })
    return rows, year, month


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_payroll_export_excel(request):
    """تصدير مسير الرواتب الحالي Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows, year, month = _payroll_export_data(request)
    columns = [
        ("employee_code", "الكود", 12),
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 16),
        ("basic_salary", "الأساسي", 12),
        ("allowances_total", "البدلات", 12),
        ("overtime_bonus", "إضافي", 12),
        ("total_deductions", "الخصومات", 12),
        ("net_salary", "الصافي", 12),
    ]
    subtitle = f"{month}/{year}"
    return export_to_excel(title="مسير الرواتب", columns=columns, rows=rows, user=request.user, filename="payroll.xlsx", subtitle=subtitle)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_payroll_export_pdf(request):
    """تصدير مسير الرواتب الحالي PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows, year, month = _payroll_export_data(request)
    columns = [
        ("employee_code", "الكود", 12),
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 16),
        ("basic_salary", "الأساسي", 12),
        ("allowances_total", "البدلات", 12),
        ("overtime_bonus", "إضافي", 12),
        ("total_deductions", "الخصومات", 12),
        ("net_salary", "الصافي", 12),
    ]
    subtitle = f"{month}/{year}"
    return export_to_pdf(title="مسير الرواتب", columns=columns, rows=rows, user=request.user, filename="payroll.pdf", subtitle=subtitle)


def _missions_export_data(request):
    """داتا المهمات لتصدير الإكسل/PDF"""
    from attendance.missions_models import Mission, MissionAssignment
    from employees.visibility import get_visible_employees_qs
    from django.db import models as dj_models

    company = getattr(request.user, "company", None)
    visible_emps = get_visible_employees_qs(request.user)

    qs = Mission._base_manager.filter(company=company).filter(
        dj_models.Q(created_by=request.user) |
        dj_models.Q(assignments__employee__in=visible_emps)
    ).distinct().prefetch_related("assignments__employee").order_by("-planned_start_time")

    status_filter = request.GET.get("status", "").strip()
    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)

    status_labels = {
        "pending": "معلقة", "assigned": "مسندة", "in_progress": "جارية",
        "completed": "مكتملة", "cancelled": "ملغاة",
    }

    rows = []
    for m in qs:
        assignees = [f"{a.employee.first_name_ar} {a.employee.last_name_ar}".strip() for a in m.assignments.all() if a.employee]
        rows.append({
            "title": m.title or "",
            "status": status_labels.get(m.status, m.status),
            "employees": ", ".join(assignees) if assignees else "",
            "employees_count": len(assignees),
            "start_date": m.planned_start_time.strftime("%Y-%m-%d %H:%M") if m.planned_start_time else "",
            "end_date": m.planned_end_time.strftime("%Y-%m-%d %H:%M") if m.planned_end_time else "",
            "location": m.location_name or "",
        })
    return rows


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_missions_export_excel(request):
    """تصدير تقرير المهمات Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _missions_export_data(request)
    columns = [
        ("title", "المهمة", 26),
        ("employees", "الموظفين", 26),
        ("employees_count", "العدد", 10),
        ("start_date", "البداية", 16),
        ("end_date", "النهاية", 16),
        ("location", "الموقع", 20),
        ("status", "الحالة", 14),
    ]
    return export_to_excel(title="تقرير المهمات", columns=columns, rows=rows, user=request.user, filename="missions.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_missions_export_pdf(request):
    """تصدير تقرير المهمات PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _missions_export_data(request)
    columns = [
        ("title", "المهمة", 26),
        ("employees", "الموظفين", 26),
        ("employees_count", "العدد", 10),
        ("start_date", "البداية", 16),
        ("end_date", "النهاية", 16),
        ("location", "الموقع", 20),
        ("status", "الحالة", 14),
    ]
    return export_to_pdf(title="تقرير المهمات", columns=columns, rows=rows, user=request.user, filename="missions.pdf")


def _absence_export_data(request):
    """داتا تقرير الغياب لتصدير الإكسل/PDF (نفس منطق absence_report)"""
    from attendance.api_reports import _get_manager_scope_employees, _employee_name, _parse_month
    from attendance.models import Attendance
    from datetime import date, timedelta
    from calendar import monthrange

    user = request.user
    year, month = _parse_month(request)
    employee_id = request.GET.get("employee_id")

    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    today = date.today()
    upper_bound = min(last_day, today)

    working_dates = []
    current = first_day
    while current <= upper_bound:
        if current.weekday() != 4:
            working_dates.append(current)
        current += timedelta(days=1)

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    rows = []
    for emp in employees:
        attended_dates = set(
            Attendance._base_manager.filter(
                employee=emp,
                date__gte=first_day,
                date__lte=upper_bound,
                check_in_time__isnull=False,
            ).values_list("date", flat=True)
        )
        absent_dates = [d for d in working_dates if d not in attended_dates]
        if absent_dates:
            rows.append({
                "employee_name": _employee_name(emp),
                "employee_code": getattr(emp, "employee_code", "") or "",
                "department": _name_of(emp.department) if emp.department else "",
                "total_working_days": len(working_dates),
                "attended_days": len(attended_dates),
                "absent_days": len(absent_dates),
            })
    return rows


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_absence_export_excel(request):
    """تصدير تقرير الغياب Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _absence_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_working_days", "أيام العمل", 14),
        ("attended_days", "أيام الحضور", 14),
        ("absent_days", "أيام الغياب", 14),
    ]
    return export_to_excel(title="تقرير الغياب", columns=columns, rows=rows, user=request.user, filename="absence.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_absence_export_pdf(request):
    """تصدير تقرير الغياب PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _absence_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_working_days", "أيام العمل", 14),
        ("attended_days", "أيام الحضور", 14),
        ("absent_days", "أيام الغياب", 14),
    ]
    return export_to_pdf(title="تقرير الغياب", columns=columns, rows=rows, user=request.user, filename="absence.pdf")


def _late_export_data(request):
    """داتا تقرير التأخير لتصدير الإكسل/PDF"""
    from attendance.api_reports import _get_manager_scope_employees, _employee_name, _parse_month
    from attendance.models import Attendance
    from datetime import date
    from calendar import monthrange

    user = request.user
    year, month = _parse_month(request)
    employee_id = request.GET.get("employee_id")

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    rows = []
    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp, date__gte=first_day, date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by("date")
        late_count = 0
        total_late_minutes = 0
        for rec in records:
            minutes_late = int(rec.late_minutes or 0)
            if minutes_late > 0:
                late_count += 1
                total_late_minutes += minutes_late
        if late_count:
            rows.append({
                "employee_name": _employee_name(emp),
                "employee_code": getattr(emp, "employee_code", "") or "",
                "department": _name_of(emp.department) if emp.department else "",
                "total_late_days": late_count,
                "total_late_minutes": total_late_minutes,
                "total_late_hours": round(total_late_minutes / 60, 2),
            })
    return rows


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_late_export_excel(request):
    """تصدير تقرير التأخير Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _late_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_late_days", "أيام التأخير", 14),
        ("total_late_minutes", "دقائق التأخير", 14),
        ("total_late_hours", "ساعات التأخير", 14),
    ]
    return export_to_excel(title="تقرير التأخير", columns=columns, rows=rows, user=request.user, filename="late.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_late_export_pdf(request):
    """تصدير تقرير التأخير PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _late_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_late_days", "أيام التأخير", 14),
        ("total_late_minutes", "دقائق التأخير", 14),
        ("total_late_hours", "ساعات التأخير", 14),
    ]
    return export_to_pdf(title="تقرير التأخير", columns=columns, rows=rows, user=request.user, filename="late.pdf")


def _work_hours_export_data(request):
    """داتا تقرير ساعات العمل لتصدير الإكسل/PDF"""
    from attendance.api_reports import _get_manager_scope_employees, _employee_name, _parse_month
    from attendance.models import Attendance
    from datetime import date
    from calendar import monthrange

    user = request.user
    year, month = _parse_month(request)
    employee_id = request.GET.get("employee_id")

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    rows = []
    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp, date__gte=first_day, date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by("date")
        total_hours = 0.0
        days_worked = 0
        for rec in records:
            hours = float(rec.work_hours or 0)
            if hours > 0:
                total_hours += hours
                days_worked += 1
        rows.append({
            "employee_name": _employee_name(emp),
            "employee_code": getattr(emp, "employee_code", "") or "",
            "department": _name_of(emp.department) if emp.department else "",
            "total_hours": round(total_hours, 2),
            "total_days_worked": days_worked,
            "average_hours_per_day": round(total_hours / days_worked, 2) if days_worked else 0,
        })
    return rows


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_work_hours_export_excel(request):
    """تصدير تقرير ساعات العمل Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _work_hours_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_hours", "إجمالي الساعات", 14),
        ("total_days_worked", "أيام العمل", 14),
        ("average_hours_per_day", "متوسط الساعات", 14),
    ]
    return export_to_excel(title="تقرير ساعات العمل", columns=columns, rows=rows, user=request.user, filename="work_hours.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_work_hours_export_pdf(request):
    """تصدير تقرير ساعات العمل PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _work_hours_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_hours", "إجمالي الساعات", 14),
        ("total_days_worked", "أيام العمل", 14),
        ("average_hours_per_day", "متوسط الساعات", 14),
    ]
    return export_to_pdf(title="تقرير ساعات العمل", columns=columns, rows=rows, user=request.user, filename="work_hours.pdf")


def _monthly_attendance_export_data(request):
    """داتا تقرير الحضور الشهري لتصدير الإكسل/PDF"""
    from attendance.api_reports import _get_manager_scope_employees, _employee_name, _parse_month
    from attendance.models import Attendance
    from datetime import date
    from calendar import monthrange

    user = request.user
    year, month = _parse_month(request)
    employee_id = request.GET.get("employee_id")

    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    rows = []
    for emp in employees:
        records = Attendance._base_manager.filter(employee=emp, date__gte=first_day, date__lte=last_day)
        checkins = records.filter(check_in_time__isnull=False).count()
        checkouts = records.filter(check_out_time__isnull=False).count()
        rows.append({
            "employee_name": _employee_name(emp),
            "employee_code": getattr(emp, "employee_code", "") or "",
            "department": _name_of(emp.department) if emp.department else "",
            "total_checkins": checkins,
            "total_checkouts": checkouts,
            "total_month_days": last_day_num,
        })
    return rows


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_monthly_attendance_export_excel(request):
    """تصدير تقرير الحضور الشهري Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _monthly_attendance_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_checkins", "أيام الحضور", 14),
        ("total_checkouts", "أيام الانصراف", 14),
        ("total_month_days", "أيام الشهر", 14),
    ]
    return export_to_excel(title="تقرير الحضور الشهري", columns=columns, rows=rows, user=request.user, filename="monthly_attendance.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_monthly_attendance_export_pdf(request):
    """تصدير تقرير الحضور الشهري PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _monthly_attendance_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("employee_code", "الكود", 12),
        ("department", "القسم", 18),
        ("total_checkins", "أيام الحضور", 14),
        ("total_checkouts", "أيام الانصراف", 14),
        ("total_month_days", "أيام الشهر", 14),
    ]
    return export_to_pdf(title="تقرير الحضور الشهري", columns=columns, rows=rows, user=request.user, filename="monthly_attendance.pdf")


def _permissions_report_export_data(request):
    """داتا تقرير الأذونات لتصدير الإكسل/PDF"""
    from attendance.api_reports import _get_manager_scope_employees, _employee_name, _parse_month
    from attendance.models import PermissionLedger
    from requests_app.models import PermissionPolicy
    from datetime import date
    from calendar import monthrange

    user = request.user
    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    employees = _get_manager_scope_employees(user)

    rows = []
    for emp in employees:
        entries = PermissionLedger._base_manager.filter(
            employee=emp, reference_date__gte=first_day, reference_date__lte=last_day,
        )
        total_minutes = sum(int(e.minutes_used or 0) for e in entries)
        policy = PermissionPolicy._base_manager.filter(company=emp.company).first()
        max_hours = float(policy.max_hours_per_month) if policy else 0.0
        max_times = policy.max_times_per_month if policy else 0
        rows.append({
            "employee_name": _employee_name(emp),
            "department": _name_of(emp.department) if emp.department else "",
            "max_hours_per_month": max_hours,
            "max_times_per_month": max_times,
            "used_hours": round(total_minutes / 60, 2),
            "movements_count": entries.count(),
        })
    return rows


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_permissions_report_export_excel(request):
    """تصدير تقرير الأذونات Excel"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_excel

    rows = _permissions_report_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("max_hours_per_month", "الحد الأقصى (ساعات)", 16),
        ("max_times_per_month", "الحد الأقصى (مرات)", 16),
        ("used_hours", "المستخدم (ساعات)", 14),
        ("movements_count", "عدد الحركات", 12),
    ]
    return export_to_excel(title="تقرير الأذونات", columns=columns, rows=rows, user=request.user, filename="permissions_report.xlsx")


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_permissions_report_export_pdf(request):
    """تصدير تقرير الأذونات PDF"""
    err = _check_manager(request)
    if err:
        return err
    from attendance.report_export_helper import export_to_pdf

    rows = _permissions_report_export_data(request)
    columns = [
        ("employee_name", "الموظف", 22),
        ("department", "القسم", 18),
        ("max_hours_per_month", "الحد الأقصى (ساعات)", 16),
        ("max_times_per_month", "الحد الأقصى (مرات)", 16),
        ("used_hours", "المستخدم (ساعات)", 14),
        ("movements_count", "عدد الحركات", 12),
    ]
    return export_to_pdf(title="تقرير الأذونات", columns=columns, rows=rows, user=request.user, filename="permissions_report.pdf")
