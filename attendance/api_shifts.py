"""
MotionHR - Shifts Management API
Phase 16: نظام الشيفتات
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

MANAGER_ROLES = {"super_admin", "company_admin", "manager", "hr_manager"}

def _check_manager(request):
    role = getattr(request.user, "role", None)
    if role not in MANAGER_ROLES and not request.user.is_superuser and not request.user.is_staff:
        return Response({"success": False, "error": "غير مصرح"}, status=403)
    return None

def _get_company(request):
    company = getattr(request.user, "company", None)
    if company: return company
    try:
        from employees.models import Employee
        emp = Employee.objects.filter(user=request.user).first()
        if emp and emp.company: return emp.company
    except: pass
    return None

def _shift_data(shift, lang='ar'):
    days_ar = ['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت']
    days_en = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    days_flags = [
        shift.work_sunday, shift.work_monday, shift.work_tuesday,
        shift.work_wednesday, shift.work_thursday, shift.work_friday, shift.work_saturday
    ]
    work_days = []
    for i, flag in enumerate(days_flags):
        if flag:
            work_days.append(days_ar[i] if lang == 'ar' else days_en[i])

    shift_types = {
        'morning': ('صباحي', 'Morning'),
        'evening': ('مسائي', 'Evening'),
        'night': ('ليلي', 'Night'),
        'flexible': ('مرن', 'Flexible'),
        'split': ('مقسم', 'Split'),
    }
    stype = shift_types.get(shift.shift_type, (shift.shift_type, shift.shift_type))

    return {
        "id": shift.id,
        "name": shift.name,
        "shift_type": shift.shift_type,
        "shift_type_label": stype[0] if lang == 'ar' else stype[1],
        "start_time": str(shift.start_time)[:5] if shift.start_time else None,
        "end_time": str(shift.end_time)[:5] if shift.end_time else None,
        "grace_period": shift.grace_period or 0,
        "break_duration": shift.break_duration or 0,
        "work_sunday": shift.work_sunday,
        "work_monday": shift.work_monday,
        "work_tuesday": shift.work_tuesday,
        "work_wednesday": shift.work_wednesday,
        "work_thursday": shift.work_thursday,
        "work_friday": shift.work_friday,
        "work_saturday": shift.work_saturday,
        "work_days": work_days,
        "is_active": shift.is_active,
        "employee_count": shift.employees.filter(is_active=True).count(),
    }

# ── LIST SHIFTS ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_shifts_list(request):
    err = _check_manager(request)
    if err: return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة"}, status=400)
        lang = request.GET.get('lang', 'ar')
        from attendance.models import Shift
        shifts = Shift.objects.filter(company=company).order_by('-is_active', 'name')
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
    if err: return err
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
        shift_type = str(data.get("shift_type", "morning")).strip()
        if shift_type not in ("morning","evening","night","flexible","split"):
            shift_type = "morning"
        from attendance.models import Shift
        shift = Shift.objects.create(
            company=company,
            name=name,
            shift_type=shift_type,
            start_time=start_time,
            end_time=end_time,
            grace_period=int(data.get("grace_period", 15)),
            break_duration=int(data.get("break_duration", 60)),
            work_sunday=bool(data.get("work_sunday", True)),
            work_monday=bool(data.get("work_monday", True)),
            work_tuesday=bool(data.get("work_tuesday", True)),
            work_wednesday=bool(data.get("work_wednesday", True)),
            work_thursday=bool(data.get("work_thursday", True)),
            work_friday=bool(data.get("work_friday", False)),
            work_saturday=bool(data.get("work_saturday", False)),
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
    if err: return err
    try:
        company = _get_company(request)
        from attendance.models import Shift
        try:
            shift = Shift.objects.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)
        data = request.data
        if "name" in data and data["name"]: shift.name = str(data["name"]).strip()
        if "shift_type" in data: shift.shift_type = data["shift_type"]
        if "start_time" in data: shift.start_time = data["start_time"]
        if "end_time" in data: shift.end_time = data["end_time"]
        if "grace_period" in data: shift.grace_period = int(data["grace_period"])
        if "break_duration" in data: shift.break_duration = int(data["break_duration"])
        for day in ["work_sunday","work_monday","work_tuesday","work_wednesday","work_thursday","work_friday","work_saturday"]:
            if day in data: setattr(shift, day, bool(data[day]))
        if "is_active" in data: shift.is_active = bool(data["is_active"])
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
    if err: return err
    try:
        company = _get_company(request)
        from attendance.models import Shift
        try:
            shift = Shift.objects.get(id=shift_id, company=company)
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
    if err: return err
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
            employee = Employee.objects.get(id=employee_id, company=company)
        except Employee.DoesNotExist:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)
        try:
            shift = Shift.objects.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)
        # إلغاء تفعيل الشيفتات السابقة
        EmployeeShift.objects.filter(employee=employee, is_active=True).update(is_active=False)
        # إنشاء شيفت جديد
        end_date = data.get("end_date") or None
        emp_shift = EmployeeShift.objects.create(
            company=company,
            employee=employee,
            shift=shift,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            created_by=request.user,
        )
        lang = data.get("lang", "ar")
        emp_name = getattr(employee, "full_name_ar", str(employee))
        return Response({
            "success": True,
            "message": f"تم تعيين شيفت '{shift.name}' للموظف {emp_name}" if lang == 'ar'
                       else f"Shift '{shift.name}' assigned to {emp_name}",
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
    if err: return err
    try:
        company = _get_company(request)
        from attendance.models import EmployeeShift
        assignments = EmployeeShift.objects.filter(
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
                "start_date": str(a.start_date),
                "end_date": str(a.end_date) if a.end_date else None,
                "is_active": a.is_active,
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
    if err: return err
    try:
        company = _get_company(request)
        from attendance.models import EmployeeShift
        assignments = EmployeeShift.objects.filter(
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
            })
        return Response({"success": True, "employees": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_shift_employees error")
        return Response({"success": False, "error": str(e)}, status=500)
