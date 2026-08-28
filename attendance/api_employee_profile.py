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
