"""
MotionHR - Shifts Management API
نظام الشيفتات الكامل مع الموافقات والاستثناءات والتناوب
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.utils import timezone
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

MANAGER_ROLES = {"super_admin", "company_admin", "manager", "hr_manager"}
HR_ROLES = {"super_admin", "company_admin", "hr_manager"}
OWNER_ROLES = {"super_admin", "company_admin"}


def _check_manager(request):
    role = getattr(request.user, "role", None)
    if role not in MANAGER_ROLES and not request.user.is_superuser and not request.user.is_staff:
        return Response({"success": False, "error": "غير مصرح"}, status=403)
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


def _get_user_role(request):
    return getattr(request.user, "role", None)


def _shift_data(shift, lang='ar'):
    days_ar = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
    days_en = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    days_flags = [
        shift.work_sunday, shift.work_monday, shift.work_tuesday,
        shift.work_wednesday, shift.work_thursday, shift.work_friday, shift.work_saturday
    ]
    work_days = []
    for i, flag in enumerate(days_flags):
        if flag:
            work_days.append(days_ar[i] if lang == 'ar' else days_en[i])

    shift_types = {
        'fixed':    ('ثابت', 'Fixed'),
        'flexible': ('مرن', 'Flexible'),
        'rotating': ('متغير', 'Rotating'),
        'morning':  ('صباحي', 'Morning'),
        'evening':  ('مسائي', 'Evening'),
        'night':    ('ليلي', 'Night'),
        'split':    ('مقسم', 'Split'),
    }
    stype = shift_types.get(shift.shift_type, (shift.shift_type, shift.shift_type))

    return {
        "id": shift.id,
        "name": shift.name,
        "shift_type": shift.shift_type,
        "shift_type_label": stype[0] if lang == 'ar' else stype[1],
        "start_time": str(shift.start_time)[:5] if shift.start_time else None,
        "end_time": str(shift.end_time)[:5] if shift.end_time else None,
        "crosses_midnight": shift.crosses_midnight,
        "grace_period": shift.grace_period or 0,
        "grace_early_leave": shift.grace_early_leave or 0,
        "early_checkin_minutes": shift.early_checkin_minutes or 30,
        "break_duration": shift.break_duration or 0,
        "work_hours": shift.work_hours,
        "work_sunday": shift.work_sunday,
        "work_monday": shift.work_monday,
        "work_tuesday": shift.work_tuesday,
        "work_wednesday": shift.work_wednesday,
        "work_thursday": shift.work_thursday,
        "work_friday": shift.work_friday,
        "work_saturday": shift.work_saturday,
        "work_days": work_days,
        "is_default": shift.is_default,
        "is_active": shift.is_active,
        "employee_count": shift.employees.filter(is_active=True).count(),
    }


def get_effective_shift(employee, target_date):
    """
    يجيب الشيفت الفعلي للموظف في يوم معين
    الأولوية:
    1. ShiftOverride (استثناء يوم معين)
    2. EmployeeShift للموظف نفسه
    3. EmployeeShift للقسم
    4. EmployeeShift للفرع
    5. EmployeeShift للشركة
    6. Shift is_default = True
    7. None
    """
    from attendance.models import ShiftOverride, EmployeeShift, Shift

    # 1. شوف لو فيه override لليوم ده
    override = ShiftOverride._base_manager.filter(
        employee=employee,
        override_date=target_date,
        company=employee.company
    ).select_related('shift').first()
    if override:
        return override.shift, 'override'

    # 2. شوف EmployeeShift للموظف نفسه
    from django.db.models import Q
    emp_shift = EmployeeShift._base_manager.filter(
        employee=employee,
        company=employee.company,
        is_active=True,
        start_date__lte=target_date,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=target_date)
    ).select_related('shift').order_by('priority', '-start_date').first()

    if emp_shift:
        return emp_shift.shift, emp_shift.assignment_type

    # 3. شوف default shift للشركة
    default_shift = Shift._base_manager.filter(
        company=employee.company,
        is_default=True,
        is_active=True
    ).first()
    if default_shift:
        return default_shift, 'company_default'

    return None, None


# ── LIST SHIFTS ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shifts_list(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة"}, status=400)
        lang = request.GET.get('lang', 'ar')
        from attendance.models import Shift
        shifts = Shift._base_manager.filter(
            company=company
        ).order_by('-is_active', '-is_default', 'name')
        data = [_shift_data(s, lang) for s in shifts]
        return Response({"success": True, "shifts": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_shifts_list error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── CREATE SHIFT ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_create(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة"}, status=400)
        data = request.data
        name = str(data.get("name", "")).strip()
        if not name:
            return Response({"success": False, "error": "اسم الشيفت مطلوب"}, status=400)
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        if not start_time or not end_time:
            return Response({"success": False, "error": "وقت البداية والنهاية مطلوبان"}, status=400)

        valid_types = ("fixed", "flexible", "rotating", "morning", "evening", "night", "split")
        shift_type = str(data.get("shift_type", "fixed")).strip()
        if shift_type not in valid_types:
            shift_type = "fixed"

        is_default = bool(data.get("is_default", False))

        from attendance.models import Shift
        # لو هيبقى default، شيل default من الباقيين
        if is_default:
            Shift._base_manager.filter(company=company, is_default=True).update(is_default=False)

        shift = Shift._base_manager.create(
            company=company,
            name=name,
            shift_type=shift_type,
            start_time=start_time,
            end_time=end_time,
            crosses_midnight=bool(data.get("crosses_midnight", False)),
            grace_period=int(data.get("grace_period", 15)),
            grace_early_leave=int(data.get("grace_early_leave", 0)),
            early_checkin_minutes=int(data.get("early_checkin_minutes", 30)),
            break_duration=int(data.get("break_duration", 60)),
            work_sunday=bool(data.get("work_sunday", True)),
            work_monday=bool(data.get("work_monday", True)),
            work_tuesday=bool(data.get("work_tuesday", True)),
            work_wednesday=bool(data.get("work_wednesday", True)),
            work_thursday=bool(data.get("work_thursday", True)),
            work_friday=bool(data.get("work_friday", False)),
            work_saturday=bool(data.get("work_saturday", False)),
            is_default=is_default,
            is_active=True,
            created_by=request.user,
        )
        lang = data.get("lang", "ar")
        return Response({
            "success": True,
            "message": f"تم إنشاء الشيفت '{name}' بنجاح" if lang == 'ar' else f"Shift '{name}' created successfully",
            "shift": _shift_data(shift, lang)
        }, status=201)
    except Exception as e:
        logger.exception("manager_shift_create error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── UPDATE SHIFT ──
@api_view(["PUT", "PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_update(request, shift_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import Shift
        try:
            shift = Shift._base_manager.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)

        data = request.data
        if "name" in data and data["name"]:
            shift.name = str(data["name"]).strip()
        if "shift_type" in data:
            shift.shift_type = data["shift_type"]
        if "start_time" in data:
            shift.start_time = data["start_time"]
        if "end_time" in data:
            shift.end_time = data["end_time"]
        if "crosses_midnight" in data:
            shift.crosses_midnight = bool(data["crosses_midnight"])
        if "grace_period" in data:
            shift.grace_period = int(data["grace_period"])
        if "grace_early_leave" in data:
            shift.grace_early_leave = int(data["grace_early_leave"])
        if "early_checkin_minutes" in data:
            shift.early_checkin_minutes = int(data["early_checkin_minutes"])
        if "break_duration" in data:
            shift.break_duration = int(data["break_duration"])
        for day in ["work_sunday", "work_monday", "work_tuesday", "work_wednesday",
                    "work_thursday", "work_friday", "work_saturday"]:
            if day in data:
                setattr(shift, day, bool(data[day]))
        if "is_active" in data:
            shift.is_active = bool(data["is_active"])
        if "is_default" in data:
            is_default = bool(data["is_default"])
            if is_default:
                Shift._base_manager.filter(
                    company=company, is_default=True
                ).exclude(id=shift_id).update(is_default=False)
            shift.is_default = is_default

        shift.updated_by = request.user
        shift.save()
        lang = data.get("lang", "ar")
        return Response({
            "success": True,
            "message": "تم تحديث الشيفت بنجاح" if lang == 'ar' else "Shift updated successfully",
            "shift": _shift_data(shift, lang)
        })
    except Exception as e:
        logger.exception("manager_shift_update error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── DELETE SHIFT ──
@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_delete(request, shift_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import Shift
        try:
            shift = Shift._base_manager.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)
        if shift.employees.filter(is_active=True).count() > 0:
            shift.is_active = False
            shift.save()
            return Response({"success": True, "message": "تم إلغاء تفعيل الشيفت (يوجد موظفون مرتبطون)"})
        shift.delete()
        return Response({"success": True, "message": "تم حذف الشيفت بنجاح"})
    except Exception as e:
        logger.exception("manager_shift_delete error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── ASSIGN SHIFT TO EMPLOYEE ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_assign(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        data = request.data
        employee_id = data.get("employee_id")
        shift_id = data.get("shift_id")
        start_date = data.get("start_date")
        if not all([employee_id, shift_id, start_date]):
            return Response({"success": False, "error": "employee_id و shift_id و start_date مطلوبة"}, status=400)

        from attendance.models import Shift, EmployeeShift
        from employees.models import Employee

        try:
            employee = Employee._base_manager.get(id=employee_id, company=company)
        except Employee.DoesNotExist:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

        try:
            shift = Shift._base_manager.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)

        user_role = _get_user_role(request)
        requires_approval = user_role not in HR_ROLES

        if requires_approval:
            # المدير محتاج موافقة HR
            from attendance.models import ShiftChangeRequest
            current_shift = EmployeeShift._base_manager.filter(
                employee=employee, company=company, is_active=True
            ).select_related('shift').order_by('-start_date').first()

            change_req = ShiftChangeRequest._base_manager.create(
                company=company,
                employee=employee,
                requested_by=request.user,
                old_shift=current_shift.shift if current_shift else None,
                new_shift=shift,
                effective_from=start_date,
                effective_to=data.get("end_date") or None,
                status='pending',
                requires_approval=True,
                reason=data.get("reason", ""),
                notified_hr=False,
            )

            # إشعار HR
            _notify_hr_shift_change(employee, shift, request.user, company)

            lang = data.get("lang", "ar")
            emp_name = getattr(employee, "full_name_ar", str(employee))
            return Response({
                "success": True,
                "pending_approval": True,
                "message": f"تم إرسال طلب تغيير الشيفت لـ HR للموافقة" if lang == 'ar' else "Shift change request sent to HR for approval",
                "request_id": change_req.id,
            }, status=201)

        else:
            # HR أو صاحب الشركة → يطبق مباشرة
            EmployeeShift._base_manager.filter(
                employee=employee, is_active=True, company=company
            ).update(is_active=False)

            end_date = data.get("end_date") or None
            emp_shift = EmployeeShift._base_manager.create(
                company=company,
                employee=employee,
                shift=shift,
                assignment_type='employee',
                priority=1,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                created_by=request.user,
            )

            # إشعار الموظف والمدير
            _notify_employee_shift_changed(employee, shift, request.user)

            lang = data.get("lang", "ar")
            emp_name = getattr(employee, "full_name_ar", str(employee))
            return Response({
                "success": True,
                "pending_approval": False,
                "message": f"تم تعيين شيفت '{shift.name}' للموظف {emp_name}" if lang == 'ar' else f"Shift '{shift.name}' assigned to {emp_name}",
                "assignment": {
                    "id": emp_shift.id,
                    "employee_id": employee.id,
                    "employee_name": emp_name,
                    "shift_id": shift.id,
                    "shift_name": shift.name,
                    "start_date": str(emp_shift.start_date),
                    "end_date": str(emp_shift.end_date) if emp_shift.end_date else None,
                }
            }, status=201)
    except Exception as e:
        logger.exception("manager_shift_assign error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── LIST EMPLOYEE SHIFTS ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_shifts(request, employee_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import EmployeeShift
        assignments = EmployeeShift._base_manager.filter(
            employee_id=employee_id, company=company
        ).select_related("shift").order_by("-start_date")
        lang = request.GET.get("lang", "ar")
        data = []
        for a in assignments:
            data.append({
                "id": a.id,
                "shift_id": a.shift.id,
                "shift_name": a.shift.name,
                "shift_type": a.shift.shift_type,
                "start_time": str(a.shift.start_time)[:5] if a.shift.start_time else None,
                "end_time": str(a.shift.end_time)[:5] if a.shift.end_time else None,
                "crosses_midnight": a.shift.crosses_midnight,
                "work_hours": a.shift.work_hours,
                "start_date": str(a.start_date),
                "end_date": str(a.end_date) if a.end_date else None,
                "is_active": a.is_active,
                "assignment_type": a.assignment_type,
            })
        return Response({"success": True, "assignments": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_employee_shifts error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── SHIFT EMPLOYEES LIST ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_employees(request, shift_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import EmployeeShift
        assignments = EmployeeShift._base_manager.filter(
            shift_id=shift_id, company=company, is_active=True
        ).select_related("employee", "employee__job_title", "employee__department")
        data = []
        for a in assignments:
            emp = a.employee
            data.append({
                "id": emp.id,
                "employee_code": emp.employee_code,
                "full_name": getattr(emp, "full_name_ar", str(emp)),
                "job_title": getattr(emp.job_title, "name_ar", "") if emp.job_title else "",
                "department": getattr(emp.department, "name_ar", "") if emp.department else "",
                "start_date": str(a.start_date),
                "end_date": str(a.end_date) if a.end_date else None,
            })
        return Response({"success": True, "employees": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_shift_employees error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── MY SHIFT (للموظف نفسه) ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_shift(request):
    try:
        from employees.models import Employee
        employee = Employee._base_manager.filter(user=request.user).first()
        if not employee:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

        today = date.today()
        shift, source = get_effective_shift(employee, today)

        if not shift:
            return Response({
                "success": True,
                "has_shift": False,
                "message": "لا يوجد شيفت محدد لك حالياً"
            })

        # جيب جدول الأسبوع الجاي
        schedule = []
        for i in range(14):
            day = today + timedelta(days=i)
            day_shift, day_source = get_effective_shift(employee, day)
            if day_shift:
                schedule.append({
                    "date": str(day),
                    "day_name": day.strftime("%A"),
                    "shift_name": day_shift.name,
                    "start_time": str(day_shift.start_time)[:5] if day_shift.start_time else None,
                    "end_time": str(day_shift.end_time)[:5] if day_shift.end_time else None,
                    "crosses_midnight": day_shift.crosses_midnight,
                    "work_hours": day_shift.work_hours,
                    "is_work_day": day_shift.is_work_day(day),
                    "source": day_source,
                })
            else:
                schedule.append({
                    "date": str(day),
                    "day_name": day.strftime("%A"),
                    "shift_name": None,
                    "is_work_day": False,
                    "source": None,
                })

        return Response({
            "success": True,
            "has_shift": True,
            "today_shift": _shift_data(shift),
            "shift_source": source,
            "schedule": schedule,
        })
    except Exception as e:
        logger.exception("my_shift error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── SHIFT CHANGE REQUESTS (للـ HR) ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def shift_change_requests_list(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftChangeRequest
        status_filter = request.GET.get('status', 'pending')
        qs = ShiftChangeRequest._base_manager.filter(
            company=company
        ).select_related(
            'employee', 'requested_by', 'old_shift', 'new_shift', 'approved_by'
        ).order_by('-created_at')

        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        data = []
        for req in qs:
            emp = req.employee
            data.append({
                "id": req.id,
                "employee_id": emp.id,
                "employee_name": getattr(emp, "full_name_ar", str(emp)),
                "employee_code": emp.employee_code,
                "requested_by": req.requested_by.get_full_name() if req.requested_by else None,
                "old_shift": req.old_shift.name if req.old_shift else None,
                "new_shift": req.new_shift.name,
                "new_shift_id": req.new_shift.id,
                "effective_from": str(req.effective_from),
                "effective_to": str(req.effective_to) if req.effective_to else None,
                "status": req.status,
                "reason": req.reason,
                "rejection_reason": req.rejection_reason,
                "created_at": str(req.created_at)[:16],
            })
        return Response({"success": True, "requests": data, "count": len(data)})
    except Exception as e:
        logger.exception("shift_change_requests_list error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── APPROVE/REJECT SHIFT CHANGE REQUEST ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def shift_change_request_action(request, request_id):
    try:
        company = _get_company(request)
        user_role = _get_user_role(request)
        if user_role not in HR_ROLES and not request.user.is_superuser:
            return Response({"success": False, "error": "غير مصرح - HR فقط"}, status=403)

        from attendance.models import ShiftChangeRequest, EmployeeShift
        try:
            change_req = ShiftChangeRequest._base_manager.get(id=request_id, company=company)
        except ShiftChangeRequest.DoesNotExist:
            return Response({"success": False, "error": "الطلب غير موجود"}, status=404)

        if change_req.status != 'pending':
            return Response({"success": False, "error": "الطلب تم البت فيه مسبقاً"}, status=400)

        action = request.data.get('action')
        if action not in ('approve', 'reject'):
            return Response({"success": False, "error": "action لازم يكون approve أو reject"}, status=400)

        if action == 'approve':
            # طبّق الشيفت الجديد
            EmployeeShift._base_manager.filter(
                employee=change_req.employee,
                company=company,
                is_active=True
            ).update(is_active=False)

            EmployeeShift._base_manager.create(
                company=company,
                employee=change_req.employee,
                shift=change_req.new_shift,
                assignment_type='employee',
                priority=1,
                start_date=change_req.effective_from,
                end_date=change_req.effective_to,
                is_active=True,
                created_by=request.user,
            )

            change_req.status = 'approved'
            change_req.approved_by = request.user
            change_req.save()

            # إشعار الموظف والمدير
            _notify_employee_shift_changed(change_req.employee, change_req.new_shift, request.user)
            _notify_manager_shift_approved(change_req)

            return Response({
                "success": True,
                "message": "تمت الموافقة على تغيير الشيفت وتطبيقه"
            })

        else:
            rejection_reason = request.data.get('rejection_reason', '')
            change_req.status = 'rejected'
            change_req.approved_by = request.user
            change_req.rejection_reason = rejection_reason
            change_req.save()

            # إشعار المدير بالرفض
            _notify_manager_shift_rejected(change_req)

            return Response({
                "success": True,
                "message": "تم رفض طلب تغيير الشيفت"
            })

    except Exception as e:
        logger.exception("shift_change_request_action error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── SHIFT OVERRIDE ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def shift_override_create(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        data = request.data
        employee_id = data.get('employee_id')
        shift_id = data.get('shift_id')
        override_date = data.get('override_date')
        reason = data.get('reason', '')

        if not all([employee_id, shift_id, override_date]):
            return Response({"success": False, "error": "employee_id و shift_id و override_date مطلوبة"}, status=400)

        from attendance.models import Shift, ShiftOverride
        from employees.models import Employee

        employee = Employee._base_manager.get(id=employee_id, company=company)
        shift = Shift._base_manager.get(id=shift_id, company=company)

        override, created = ShiftOverride._base_manager.update_or_create(
            employee=employee,
            override_date=override_date,
            company=company,
            defaults={
                'shift': shift,
                'reason': reason,
                'created_by': request.user,
            }
        )

        # إشعار الموظف
        _notify_employee_shift_override(employee, shift, override_date)

        emp_name = getattr(employee, "full_name_ar", str(employee))
        return Response({
            "success": True,
            "message": f"تم تحديد شيفت استثنائي للموظف {emp_name} في {override_date}",
            "override_id": override.id,
        }, status=201 if created else 200)
    except Exception as e:
        logger.exception("shift_override_create error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def shift_override_delete(request, override_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftOverride
        override = ShiftOverride._base_manager.get(id=override_id, company=company)
        override.delete()
        return Response({"success": True, "message": "تم حذف الاستثناء"})
    except ShiftOverride.DoesNotExist:
        return Response({"success": False, "error": "الاستثناء غير موجود"}, status=404)
    except Exception as e:
        logger.exception("shift_override_delete error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── GET EFFECTIVE SHIFT FOR EMPLOYEE (API) ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_effective_shift(request, employee_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        from employees.models import Employee
        company = _get_company(request)
        employee = Employee._base_manager.get(id=employee_id, company=company)

        target_date_str = request.GET.get('date', str(date.today()))
        try:
            from datetime import datetime
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()

        shift, source = get_effective_shift(employee, target_date)

        if not shift:
            return Response({
                "success": True,
                "has_shift": False,
                "message": "لا يوجد شيفت محدد لهذا الموظف"
            })

        return Response({
            "success": True,
            "has_shift": True,
            "shift": _shift_data(shift),
            "source": source,
            "date": str(target_date),
        })
    except Exception as e:
        logger.exception("employee_effective_shift error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── NOTIFICATION HELPERS ──
def _notify_employee_shift_changed(employee, shift, changed_by):
    try:
        from accounts.fcm_service import send_notification_to_user
        if hasattr(employee, 'user') and employee.user:
            send_notification_to_user(
                user=employee.user,
                title="🔄 تم تحديث شيفتك",
                body=f"تم تغيير شيفتك إلى: {shift.name} ({shift.start_time} - {shift.end_time})",
                data={
                    'type': 'shift_changed',
                    'shift_id': str(shift.id),
                    'screen': 'my_shift',
                }
            )
    except Exception:
        pass


def _notify_hr_shift_change(employee, shift, requested_by, company):
    try:
        from accounts.fcm_service import send_notification_to_user
        from accounts.models import User
        emp_name = getattr(employee, "full_name_ar", str(employee))
        hr_users = User.objects.filter(company=company, role__in=['hr_manager', 'company_admin'])
        for hr_user in hr_users:
            send_notification_to_user(
                user=hr_user,
                title="📋 طلب تغيير شيفت",
                body=f"طلب تغيير شيفت الموظف {emp_name} إلى: {shift.name}",
                data={
                    'type': 'shift_change_request',
                    'screen': 'shift_change_requests',
                }
            )
    except Exception:
        pass


def _notify_manager_shift_approved(change_req):
    try:
        from accounts.fcm_service import send_notification_to_user
        if change_req.requested_by:
            emp_name = getattr(change_req.employee, "full_name_ar", str(change_req.employee))
            send_notification_to_user(
                user=change_req.requested_by,
                title="✅ تمت الموافقة على تغيير الشيفت",
                body=f"تمت الموافقة على تغيير شيفت {emp_name} إلى: {change_req.new_shift.name}",
                data={
                    'type': 'shift_change_approved',
                    'request_id': str(change_req.id),
                    'screen': 'shift_change_requests',
                }
            )
    except Exception:
        pass


def _notify_manager_shift_rejected(change_req):
    try:
        from accounts.fcm_service import send_notification_to_user
        if change_req.requested_by:
            emp_name = getattr(change_req.employee, "full_name_ar", str(change_req.employee))
            send_notification_to_user(
                user=change_req.requested_by,
                title="❌ تم رفض طلب تغيير الشيفت",
                body=f"تم رفض طلب تغيير شيفت {emp_name}. السبب: {change_req.rejection_reason}",
                data={
                    'type': 'shift_change_rejected',
                    'request_id': str(change_req.id),
                    'screen': 'shift_change_requests',
                }
            )
    except Exception:
        pass


def _notify_employee_shift_override(employee, shift, override_date):
    try:
        from accounts.fcm_service import send_notification_to_user
        if hasattr(employee, 'user') and employee.user:
            send_notification_to_user(
                user=employee.user,
                title="📅 تعديل شيفت استثنائي",
                body=f"تم تحديد شيفت استثنائي لك في {override_date}: {shift.name}",
                data={
                    'type': 'shift_override',
                    'date': str(override_date),
                    'screen': 'my_shift',
                }
            )
    except Exception:
        pass
