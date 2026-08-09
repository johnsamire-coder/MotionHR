"""
MotionHR - Shifts Management API
نظام الشيفتات الكامل مع الموافقات والاستثناءات والتناوب
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils import timezone
from datetime import date, timedelta, datetime
import logging

logger = logging.getLogger(__name__)

def _get_shift_assigned_employees(shift):
    from employees.models import Employee
    from attendance.models import ShiftAssignment

    affected = {}

    # لو الشيفت افتراضي: بيطبق على كل الموظفين اللي مالهمش شيفت معيّن
    if getattr(shift, 'is_default', False):
        assigned_employee_ids = set(
            ShiftAssignment._base_manager.filter(
                company=shift.company,
                assignment_type='employee',
                is_active=True,
            ).exclude(shift=shift).values_list('employee_id', flat=True)
        )
        for emp in Employee._base_manager.filter(
            company=shift.company,
            status='active',
        ).exclude(id__in=assigned_employee_ids):
            affected[emp.id] = emp
        return list(affected.values())

    assignments = ShiftAssignment._base_manager.filter(
        company=shift.company, shift=shift, is_active=True,
    ).select_related('employee', 'department', 'branch').prefetch_related('excluded_employees')
    for a in assignments:
        excluded_ids = set(a.excluded_employees.values_list('id', flat=True))
        if a.assignment_type == 'employee' and a.employee:
            affected[a.employee.id] = a.employee
        elif a.assignment_type == 'department' and a.department:
            for emp in Employee._base_manager.filter(
                company=shift.company,
                department=a.department,
                status='active'
            ).exclude(id__in=excluded_ids):
                affected[emp.id] = emp
        elif a.assignment_type == 'branch' and a.branch:
            for emp in Employee._base_manager.filter(
                company=shift.company,
                branch=a.branch,
                status='active'
            ).exclude(id__in=excluded_ids):
                affected[emp.id] = emp
        elif a.assignment_type == 'company':
            for emp in Employee._base_manager.filter(
                company=shift.company,
                status='active'
            ).exclude(id__in=excluded_ids):
                affected[emp.id] = emp
    return list(affected.values())


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
        "employee_count": len(_get_shift_assigned_employees(shift)),
        "shift_mode": shift.shift_mode,
        "time_preset": shift.time_preset,
        "required_daily_hours": float(shift.required_daily_hours),
        "allow_partial_checkout": shift.allow_partial_checkout,
        "max_sessions_per_day": shift.max_sessions_per_day,
        "variable_schedule_type": shift.variable_schedule_type,
        "schedule_config": shift.schedule_config or {},
        "shift_mode_label": dict(shift.SHIFT_MODE_CHOICES).get(shift.shift_mode, shift.shift_mode),
        "time_preset_label": dict(shift.TIME_PRESET_CHOICES).get(shift.time_preset, shift.time_preset),
    }


def get_effective_shift(employee, target_date):
    """
    يجيب الشيفت الفعلي للموظف في يوم معين
    الأولوية:
    1. ShiftOverride
    2. ShiftAssignment للموظف
    3. ShiftAssignment للقسم
    4. ShiftAssignment للفرع
    5. ShiftAssignment للشركة
    6. EmployeeShift القديم (fallback)
    7. Shift الافتراضي للشركة
    8. None
    """
    from django.db.models import Q
    from attendance.models import ShiftOverride, ShiftAssignment, EmployeeShift, Shift

    # 1) override يومي
    override = ShiftOverride._base_manager.filter(
        employee=employee,
        override_date=target_date,
        company=employee.company
    ).select_related('shift').first()
    if override:
        return override.shift, 'override'

    active_date_filter = Q(end_date__isnull=True) | Q(end_date__gte=target_date)

    # 2) تعيين مباشر للموظف
    employee_assignment = ShiftAssignment._base_manager.filter(
        company=employee.company,
        assignment_type='employee',
        employee=employee,
        is_active=True,
        start_date__lte=target_date,
    ).filter(active_date_filter).select_related('shift').order_by('priority', '-start_date').first()
    if employee_assignment:
        return employee_assignment.shift, 'employee_assignment'

    # 3) تعيين القسم
    if getattr(employee, 'department_id', None):
        department_assignment = ShiftAssignment._base_manager.filter(
            company=employee.company,
            assignment_type='department',
            department_id=employee.department_id,
            is_active=True,
            start_date__lte=target_date,
        ).exclude(excluded_employees=employee).filter(active_date_filter).select_related('shift').order_by('priority', '-start_date').first()
        if department_assignment:
            return department_assignment.shift, 'department_assignment'

    # 4) تعيين الفرع
    if getattr(employee, 'branch_id', None):
        branch_assignment = ShiftAssignment._base_manager.filter(
            company=employee.company,
            assignment_type='branch',
            branch_id=employee.branch_id,
            is_active=True,
            start_date__lte=target_date,
        ).exclude(excluded_employees=employee).filter(active_date_filter).select_related('shift').order_by('priority', '-start_date').first()
        if branch_assignment:
            return branch_assignment.shift, 'branch_assignment'

    # 5) تعيين الشركة
    company_assignment = ShiftAssignment._base_manager.filter(
        company=employee.company,
        assignment_type='company',
        is_active=True,
        start_date__lte=target_date,
    ).exclude(excluded_employees=employee).filter(active_date_filter).select_related('shift').order_by('priority', '-start_date').first()
    if company_assignment:
        return company_assignment.shift, 'company_assignment'

    # 6) تناوب الشيفتات (ShiftRotation)
    from attendance.models import ShiftRotation, ShiftRotationSlot, ShiftRotationAssignment
    active_rotation_filter = Q(end_date__isnull=True) | Q(end_date__gte=target_date)

    def _get_shift_from_rotation(rotation):
        """بيحسب أنهي شيفت في هذا اليوم من الدورة"""
        if not rotation.start_date:
            return None
        days_diff = (target_date - rotation.start_date).days
        if days_diff < 0:
            return None
        day_in_cycle = days_diff % rotation.cycle_length_days
        slot = ShiftRotationSlot._base_manager.filter(
            rotation=rotation,
            start_day_index__lte=day_in_cycle,
            end_day_index__gte=day_in_cycle,
            company=employee.company,
        ).select_related('shift').first()
        return slot.shift if slot else None

    # 6a) تناوب للموظف مباشرة
    emp_rotation_assignment = ShiftRotationAssignment._base_manager.filter(
        company=employee.company,
        assignment_type='employee',
        employee=employee,
        is_active=True,
        start_date__lte=target_date,
    ).filter(active_rotation_filter).select_related('rotation').order_by('priority', '-start_date').first()
    if emp_rotation_assignment:
        rotation_shift = _get_shift_from_rotation(emp_rotation_assignment.rotation)
        if rotation_shift:
            return rotation_shift, 'rotation_employee'

    # 6b) تناوب للقسم
    if getattr(employee, 'department_id', None):
        dept_rotation_assignment = ShiftRotationAssignment._base_manager.filter(
            company=employee.company,
            assignment_type='department',
            department_id=employee.department_id,
            is_active=True,
            start_date__lte=target_date,
        ).filter(active_rotation_filter).select_related('rotation').order_by('priority', '-start_date').first()
        if dept_rotation_assignment:
            rotation_shift = _get_shift_from_rotation(dept_rotation_assignment.rotation)
            if rotation_shift:
                return rotation_shift, 'rotation_department'

    # 6c) تناوب للفرع
    if getattr(employee, 'branch_id', None):
        branch_rotation_assignment = ShiftRotationAssignment._base_manager.filter(
            company=employee.company,
            assignment_type='branch',
            branch_id=employee.branch_id,
            is_active=True,
            start_date__lte=target_date,
        ).filter(active_rotation_filter).select_related('rotation').order_by('priority', '-start_date').first()
        if branch_rotation_assignment:
            rotation_shift = _get_shift_from_rotation(branch_rotation_assignment.rotation)
            if rotation_shift:
                return rotation_shift, 'rotation_branch'

    # 6d) تناوب للشركة
    company_rotation_assignment = ShiftRotationAssignment._base_manager.filter(
        company=employee.company,
        assignment_type='company',
        is_active=True,
        start_date__lte=target_date,
    ).filter(active_rotation_filter).select_related('rotation').order_by('priority', '-start_date').first()
    if company_rotation_assignment:
        rotation_shift = _get_shift_from_rotation(company_rotation_assignment.rotation)
        if rotation_shift:
            return rotation_shift, 'rotation_company'

    # 7) fallback قديم على EmployeeShift لعدم كسر النظام الحالي
    legacy_emp_shift = EmployeeShift._base_manager.filter(
        employee=employee,
        company=employee.company,
        is_active=True,
        start_date__lte=target_date,
    ).filter(active_date_filter).select_related('shift').order_by('priority', '-start_date').first()
    if legacy_emp_shift:
        return legacy_emp_shift.shift, 'legacy_employee_shift'

    # 7) default shift
    default_shift = Shift._base_manager.filter(
        company=employee.company,
        is_default=True,
        is_active=True
    ).first()
    if default_shift:
        return default_shift, 'company_default'

    return None, None


VALID_SHIFT_MODES = (
    'fixed', 'flex_fixed', 'flex_split',
    'variable_daily', 'variable_weekly', 'variable_weekly_flex',
    'split_fixed',
)

VALID_SHIFT_TYPES = ('fixed', 'flexible', 'rotating', 'morning', 'evening', 'night', 'split')

VALID_TIME_PRESETS = ('custom', 'morning', 'evening', 'night')

VALID_VARIABLE_SCHEDULE_TYPES = ('none', 'daily', 'weekly', 'weekly_flex')


def _validate_schedule_config(shift_mode, schedule_config):
    """
    بترجع (is_valid, error_message)
    - split_fixed / flex_split: لازم يبقى فيه periods بصيغة صحيحة ومش متداخلة
    - variable_*: لازم يبقى فيه days
    """
    if shift_mode not in ('split_fixed', 'flex_split', 'variable_daily', 'variable_weekly', 'variable_weekly_flex'):
        return True, None

    if not isinstance(schedule_config, dict):
        return False, "schedule_config لازم يكون object"

    # فترات (split_fixed / flex_split)
    if shift_mode in ('split_fixed', 'flex_split'):
        periods = schedule_config.get('periods', [])
        if not isinstance(periods, list) or len(periods) < 2:
            return False, "شيفت مقسم لازم يحتوي على فترتين على الأقل"

        parsed_periods = []
        for idx, p in enumerate(periods, start=1):
            if not isinstance(p, dict):
                return False, f"فترة رقم {idx}: صيغة غير صحيحة"
            start = p.get('start')
            end = p.get('end')
            if not start or not end:
                return False, f"فترة رقم {idx}: بداية ونهاية مطلوبة"
            try:
                start_t = datetime.strptime(str(start), "%H:%M").time()
                end_t = datetime.strptime(str(end), "%H:%M").time()
            except (ValueError, TypeError):
                return False, f"فترة رقم {idx}: صيغة الوقت لازم تكون HH:MM"
            if start_t >= end_t:
                return False, f"فترة رقم {idx}: البداية لازم تكون قبل النهاية"
            parsed_periods.append((start_t, end_t, idx))

        # نتأكد إن الفترات مش متداخلة
        sorted_periods = sorted(parsed_periods, key=lambda x: x[0])
        for i in range(len(sorted_periods) - 1):
            if sorted_periods[i][1] > sorted_periods[i + 1][0]:
                return False, (
                    f"الفترة {sorted_periods[i][2]} متداخلة مع الفترة {sorted_periods[i + 1][2]}"
                )

    # variable_*
    if shift_mode.startswith('variable'):
        days = schedule_config.get('days', {})
        if not isinstance(days, dict) or not days:
            return False, "الجدول المتغير لازم يحتوي على أيام"

    return True, None


# ── LIST SHIFTS ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_shifts_list(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة"}, status=400)
        from attendance.models import Shift
        lang = request.GET.get("lang", "ar")
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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

        try:
            start_time = datetime.strptime(str(start_time), "%H:%M").time()
            end_time = datetime.strptime(str(end_time), "%H:%M").time()
        except ValueError:
            return Response({"success": False, "error": "صيغة الوقت لازم تكون HH:MM"}, status=400)

        shift_type = str(data.get("shift_type", "fixed")).strip()
        if shift_type not in VALID_SHIFT_TYPES:
            shift_type = "fixed"

        shift_mode = str(data.get("shift_mode", "fixed")).strip()
        if shift_mode not in VALID_SHIFT_MODES:
            return Response({
                "success": False,
                "error": f"shift_mode غير صحيح. المسموح: {', '.join(VALID_SHIFT_MODES)}"
            }, status=400)

        schedule_config = data.get("schedule_config", {})
        is_valid, err_msg = _validate_schedule_config(shift_mode, schedule_config)
        if not is_valid:
            return Response({"success": False, "error": err_msg}, status=400)

        time_preset = str(data.get("time_preset", "custom")).strip()
        if time_preset not in VALID_TIME_PRESETS:
            time_preset = "custom"

        variable_schedule_type = str(data.get("variable_schedule_type", "none")).strip()
        if variable_schedule_type not in VALID_VARIABLE_SCHEDULE_TYPES:
            variable_schedule_type = "none"

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
            shift_mode=shift_mode,
            time_preset=time_preset,
            required_daily_hours=float(data.get("required_daily_hours", 8)),
            allow_partial_checkout=bool(data.get("allow_partial_checkout", False)),
            max_sessions_per_day=int(data.get("max_sessions_per_day", 1)),
            variable_schedule_type=variable_schedule_type,
            schedule_config=schedule_config,
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
            try:
                shift.start_time = datetime.strptime(str(data["start_time"]), "%H:%M").time()
            except ValueError:
                return Response({"success": False, "error": "صيغة وقت البداية لازم تكون HH:MM"}, status=400)
        if "end_time" in data:
            try:
                shift.end_time = datetime.strptime(str(data["end_time"]), "%H:%M").time()
            except ValueError:
                return Response({"success": False, "error": "صيغة وقت النهاية لازم تكون HH:MM"}, status=400)
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
        if "shift_mode" in data:
            new_shift_mode = str(data["shift_mode"]).strip()
            if new_shift_mode not in VALID_SHIFT_MODES:
                return Response({
                    "success": False,
                    "error": f"shift_mode غير صحيح. المسموح: {', '.join(VALID_SHIFT_MODES)}"
                }, status=400)
            shift.shift_mode = new_shift_mode
        if "time_preset" in data:
            new_time_preset = str(data["time_preset"]).strip()
            if new_time_preset not in VALID_TIME_PRESETS:
                new_time_preset = "custom"
            shift.time_preset = new_time_preset
        if "required_daily_hours" in data:
            shift.required_daily_hours = float(data["required_daily_hours"])
        if "allow_partial_checkout" in data:
            shift.allow_partial_checkout = bool(data["allow_partial_checkout"])
        if "max_sessions_per_day" in data:
            shift.max_sessions_per_day = int(data["max_sessions_per_day"])
        if "variable_schedule_type" in data:
            new_var_type = str(data["variable_schedule_type"]).strip()
            if new_var_type not in VALID_VARIABLE_SCHEDULE_TYPES:
                new_var_type = "none"
            shift.variable_schedule_type = new_var_type
        if "schedule_config" in data:
            # نتحقق من الـ schedule_config حسب shift_mode النهائي
            final_shift_mode = shift.shift_mode
            is_valid, err_msg = _validate_schedule_config(final_shift_mode, data["schedule_config"])
            if not is_valid:
                return Response({"success": False, "error": err_msg}, status=400)
            shift.schedule_config = data["schedule_config"]
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_delete(request, shift_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import (
            Shift, EmployeeShift, ShiftAssignment,
            ShiftOverride, ShiftRotationSlot, Attendance
        )
        try:
            shift = Shift._base_manager.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)

        # نجمع كل الاستخدامات النشطة
        active_employee_shifts = EmployeeShift._base_manager.filter(shift=shift, is_active=True).count()
        active_assignments = ShiftAssignment._base_manager.filter(shift=shift, is_active=True).count()
        active_overrides = ShiftOverride._base_manager.filter(shift=shift, override_date__gte=timezone.now().date()).count()
        rotation_slots = ShiftRotationSlot._base_manager.filter(shift=shift).count()
        attendance_count = Attendance._base_manager.filter(shift=shift).count()

        total_usage = active_employee_shifts + active_assignments + active_overrides + rotation_slots

        if total_usage > 0 or attendance_count > 0:
            # فيه ارتباطات → soft delete (إلغاء تفعيل)
            shift.is_active = False
            shift.save()

            details = []
            if active_employee_shifts > 0:
                details.append(f"{active_employee_shifts} تعيين قديم")
            if active_assignments > 0:
                details.append(f"{active_assignments} تعيين نشط")
            if active_overrides > 0:
                details.append(f"{active_overrides} استثناء قادم")
            if rotation_slots > 0:
                details.append(f"{rotation_slots} فترة تناوب")
            if attendance_count > 0:
                details.append(f"{attendance_count} سجل حضور")

            details_text = " / ".join(details) if details else ""

            return Response({
                "success": True,
                "soft_deleted": True,
                "message": f"تم إلغاء تفعيل الشيفت (لا يمكن حذفه لوجود: {details_text})",
                "usage": {
                    "employee_shifts": active_employee_shifts,
                    "assignments": active_assignments,
                    "overrides": active_overrides,
                    "rotation_slots": rotation_slots,
                    "attendance_records": attendance_count,
                }
            })

        # مفيش أي ارتباطات → hard delete آمن
        shift.delete()
        return Response({"success": True, "soft_deleted": False, "message": "تم حذف الشيفت بنجاح"})
    except Exception as e:
        logger.exception("manager_shift_delete error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── ASSIGN SHIFT TO EMPLOYEE ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_assign(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        data = request.data
        shift_id = data.get("shift_id")
        start_date_raw = data.get("start_date")
        end_date_raw = data.get("end_date") or None
        reason = data.get("reason", "")
        lang = data.get("lang", "ar")

        if not all([shift_id, start_date_raw]):
            return Response({"success": False, "error": "shift_id و start_date مطلوبان"}, status=400)

        try:
            start_date = datetime.strptime(str(start_date_raw), "%Y-%m-%d").date()
            end_date = datetime.strptime(str(end_date_raw), "%Y-%m-%d").date() if end_date_raw else None
        except ValueError:
            return Response({"success": False, "error": "صيغة التاريخ لازم تكون YYYY-MM-DD"}, status=400)

        from attendance.models import Shift, EmployeeShift, ShiftAssignment, ShiftChangeRequest
        from employees.models import Employee
        from companies.models import Department, Branch

        try:
            shift = Shift._base_manager.get(id=shift_id, company=company)
        except Shift.DoesNotExist:
            return Response({"success": False, "error": "الشيفت غير موجود"}, status=404)

        def _as_int_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                raw = value
            else:
                raw = [value]
            result = []
            seen = set()
            for item in raw:
                if item in (None, "", []):
                    continue
                try:
                    num = int(item)
                except (TypeError, ValueError):
                    continue
                if num not in seen:
                    seen.add(num)
                    result.append(num)
            return result

        employee_ids = _as_int_list(data.get("employee_ids")) + _as_int_list(data.get("employee_id"))
        department_ids = _as_int_list(data.get("department_ids")) + _as_int_list(data.get("department_id"))
        branch_ids = _as_int_list(data.get("branch_ids")) + _as_int_list(data.get("branch_id"))
        excluded_employee_ids = _as_int_list(data.get("excluded_employee_ids")) + _as_int_list(data.get("excluded_employee_id"))

        # dedupe with order
        employee_ids = list(dict.fromkeys(employee_ids))
        department_ids = list(dict.fromkeys(department_ids))
        branch_ids = list(dict.fromkeys(branch_ids))
        excluded_employee_ids = list(dict.fromkeys(excluded_employee_ids))

        assign_to_company = bool(data.get("assign_to_company", False))
        assignment_type = str(data.get("assignment_type", "")).strip()
        if assignment_type == "company":
            assign_to_company = True

        if not employee_ids and not department_ids and not branch_ids and not assign_to_company:
            return Response({
                "success": False,
                "error": "لازم تختار موظف أو قسم أو فرع أو الشركة كلها"
            }, status=400)

        direct_employees = []
        departments = []
        branches = []
        excluded_employees = []

        if employee_ids:
            direct_employees = list(Employee._base_manager.filter(id__in=employee_ids, company=company))
            if len(direct_employees) != len(employee_ids):
                return Response({"success": False, "error": "بعض الموظفين غير موجودين"}, status=404)

        if excluded_employee_ids:
            excluded_employees = list(Employee._base_manager.filter(id__in=excluded_employee_ids, company=company))
            if len(excluded_employees) != len(excluded_employee_ids):
                return Response({"success": False, "error": "بعض الموظفين المستثنين غير موجودين"}, status=404)

        if department_ids:
            departments = list(Department.objects.filter(id__in=department_ids, company=company))
            if len(departments) != len(department_ids):
                return Response({"success": False, "error": "بعض الأقسام غير موجودة"}, status=404)

        if branch_ids:
            branches = list(Branch.objects.filter(id__in=branch_ids, company=company))
            if len(branches) != len(branch_ids):
                return Response({"success": False, "error": "بعض الفروع غير موجودة"}, status=404)

        # جمع الموظفين المتأثرين مع إزالة التكرار + تطبيق الاستثناءات على التعيينات الجماعية فقط
        affected = {}
        grouped_affected = {}

        for emp in direct_employees:
            affected[emp.id] = emp

        if departments:
            dept_emps = Employee._base_manager.filter(
                company=company,
                department__in=departments,
                status='active'
            )
            for emp in dept_emps:
                grouped_affected[emp.id] = emp

        if branches:
            branch_emps = Employee._base_manager.filter(
                company=company,
                branch__in=branches,
                status='active'
            )
            for emp in branch_emps:
                grouped_affected[emp.id] = emp

        if assign_to_company:
            company_emps = Employee._base_manager.filter(
                company=company,
                status='active'
            )
            for emp in company_emps:
                grouped_affected[emp.id] = emp

        for excluded_emp in excluded_employees:
            grouped_affected.pop(excluded_emp.id, None)

        affected.update(grouped_affected)
        affected_employees = list(affected.values())

        user_role = _get_user_role(request)
        requires_approval = user_role not in HR_ROLES and not request.user.is_superuser

        # المدير العادي: يسمح فقط بطلب تغيير لموظف واحد
        if requires_approval:
            if len(affected_employees) != 1 or department_ids or branch_ids or assign_to_company:
                return Response({
                    "success": False,
                    "error": "التعيين الجماعي متاح حاليًا لـ HR أو صاحب الشركة فقط"
                }, status=403)

            employee = affected_employees[0]
            current_shift = EmployeeShift._base_manager.filter(
                employee=employee,
                company=company,
                is_active=True
            ).select_related('shift').order_by('-start_date').first()

            change_req = ShiftChangeRequest._base_manager.create(
                company=company,
                employee=employee,
                requested_by=request.user,
                old_shift=current_shift.shift if current_shift else None,
                new_shift=shift,
                effective_from=start_date,
                effective_to=end_date,
                status='pending',
                requires_approval=True,
                reason=reason,
                notified_hr=False,
            )

            _notify_hr_shift_change(employee, shift, request.user, company)

            return Response({
                "success": True,
                "pending_approval": True,
                "message": "تم إرسال طلب تغيير الشيفت لـ HR للموافقة" if lang == 'ar' else "Shift change request sent to HR for approval",
                "request_id": change_req.id,
                "affected_employees_count": 1,
            }, status=201)

        def _find_same_scope_overlapping_assignment(assignment_type, branch=None, department=None):
            qs = ShiftAssignment._base_manager.filter(
                company=company,
                assignment_type=assignment_type,
                is_active=True
            ).select_related('shift', 'branch', 'department', 'employee', 'employee__user')

            if assignment_type == 'branch' and branch is not None:
                qs = qs.filter(branch=branch)
            elif assignment_type == 'department' and department is not None:
                qs = qs.filter(department=department)

            new_end = end_date or date.max
            for existing_assignment in qs.order_by('-start_date'):
                existing_end = existing_assignment.end_date or date.max
                if existing_assignment.start_date <= new_end and start_date <= existing_end:
                    return existing_assignment
            return None

        def _build_assignment_conflict(scope_key, scope_label_ar, scope_label_en, existing_assignment, target_id=None, target_name=None):
            return {
                "scope": scope_key,
                "scope_label": scope_label_ar if lang == 'ar' else scope_label_en,
                "target_id": target_id,
                "target_name": target_name,
                "existing_assignment_id": existing_assignment.id,
                "existing_shift_id": existing_assignment.shift_id,
                "existing_shift_name": existing_assignment.shift.name if existing_assignment.shift else None,
                "existing_start_date": str(existing_assignment.start_date),
                "existing_end_date": str(existing_assignment.end_date) if existing_assignment.end_date else None,
            }

        # م-7: نتحقق من كل التعارضات قبل أي create/update عشان مايبقاش فيه تعطيل صامت أو partial writes
        assignment_conflicts = []

        if assign_to_company:
            existing_company_assignment = _find_same_scope_overlapping_assignment('company')
            if existing_company_assignment:
                assignment_conflicts.append(
                    _build_assignment_conflict(
                        'company', 'الشركة', 'Company',
                        existing_company_assignment,
                        target_name=(getattr(company, 'name_ar', None) or getattr(company, 'name_en', None) or str(company))
                    )
                )

        for branch in branches:
            existing_branch_assignment = _find_same_scope_overlapping_assignment('branch', branch=branch)
            if existing_branch_assignment:
                assignment_conflicts.append(
                    _build_assignment_conflict(
                        'branch', 'الفرع', 'Branch',
                        existing_branch_assignment,
                        target_id=branch.id,
                        target_name=(getattr(branch, 'name_ar', None) or getattr(branch, 'name_en', None) or f'#{branch.id}')
                    )
                )

        for department in departments:
            existing_department_assignment = _find_same_scope_overlapping_assignment('department', department=department)
            if existing_department_assignment:
                assignment_conflicts.append(
                    _build_assignment_conflict(
                        'department', 'القسم', 'Department',
                        existing_department_assignment,
                        target_id=department.id,
                        target_name=(getattr(department, 'name_ar', None) or getattr(department, 'name_en', None) or f'#{department.id}')
                    )
                )

        for employee in direct_employees:
            active_direct_assignments = ShiftAssignment._base_manager.filter(
                company=company,
                assignment_type='employee',
                employee=employee,
                is_active=True
            ).select_related('shift', 'employee', 'employee__user').order_by('-start_date')

            new_end = end_date or date.max
            overlapping_assignment = None

            for existing_assignment in active_direct_assignments:
                existing_end = existing_assignment.end_date or date.max
                if existing_assignment.start_date <= new_end and start_date <= existing_end:
                    overlapping_assignment = existing_assignment
                    break

            if overlapping_assignment:
                _user = getattr(employee, 'user', None)
                employee_name = (
                    (_user.get_full_name() if _user else '')
                    or getattr(_user, 'username', '')
                    or getattr(employee, 'full_name_ar', '')
                    or f'#{employee.id}'
                )
                assignment_conflicts.append({
                    "scope": "employee",
                    "scope_label": "موظف مباشر" if lang == 'ar' else "Direct Employee",
                    "target_id": employee.id,
                    "target_name": employee_name,
                    "existing_assignment_id": overlapping_assignment.id,
                    "existing_shift_id": overlapping_assignment.shift_id,
                    "existing_shift_name": overlapping_assignment.shift.name if overlapping_assignment.shift else None,
                    "existing_start_date": str(overlapping_assignment.start_date),
                    "existing_end_date": str(overlapping_assignment.end_date) if overlapping_assignment.end_date else None,
                })

        if assignment_conflicts:
            conflicts_count = len(assignment_conflicts)
            return Response({
                "success": False,
                "error": (
                    "يوجد تعيين شيفت متداخل على نفس النطاق. عدّل أو احذف التعيين الحالي أولاً"
                    if conflicts_count == 1 else
                    f"يوجد {conflicts_count} تعارضات في التعيينات الحالية. عدّل أو احذف التعيينات الحالية أولاً"
                ) if lang == 'ar' else (
                    "There is an overlapping shift assignment on the same scope. Update or delete the current assignment first"
                    if conflicts_count == 1 else
                    f"There are {conflicts_count} conflicts in current assignments. Update or delete them first"
                ),
                "conflicts": assignment_conflicts,
            }, status=400)

        created_assignments = []

        # company assignment
        if assign_to_company:
            assignment = ShiftAssignment._base_manager.create(
                company=company,
                shift=shift,
                assignment_type='company',
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                priority=4,
                notes=reason,
                created_by=request.user,
            )
            if excluded_employees:
                assignment.excluded_employees.set(excluded_employees)
            created_assignments.append(assignment)

        # branch assignments
        for branch in branches:
            assignment = ShiftAssignment._base_manager.create(
                company=company,
                shift=shift,
                assignment_type='branch',
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                priority=3,
                notes=reason,
                created_by=request.user,
            )
            if excluded_employees:
                assignment.excluded_employees.set(excluded_employees)
            created_assignments.append(assignment)

        # department assignments
        for department in departments:
            assignment = ShiftAssignment._base_manager.create(
                company=company,
                shift=shift,
                assignment_type='department',
                department=department,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                priority=2,
                notes=reason,
                created_by=request.user,
            )
            if excluded_employees:
                assignment.excluded_employees.set(excluded_employees)
            created_assignments.append(assignment)

        # direct employee assignments
        for employee in direct_employees:
            active_direct_assignments = ShiftAssignment._base_manager.filter(
                company=company,
                assignment_type='employee',
                employee=employee,
                is_active=True
            ).select_related('shift')

            new_end = end_date or date.max
            overlapping_assignment = None

            for existing_assignment in active_direct_assignments:
                existing_end = existing_assignment.end_date or date.max
                if existing_assignment.start_date <= new_end and start_date <= existing_end:
                    overlapping_assignment = existing_assignment
                    break

            if overlapping_assignment:
                employee_name = (
                    employee.user.get_full_name()
                    or getattr(employee.user, 'username', '')
                    or f'#{employee.id}'
                )
                return Response({
                    "success": False,
                    "error": (
                        f"الموظف {employee_name} عليه شيفت مباشر متداخل بالفعل"
                        if lang == 'ar'
                        else f"Employee {employee_name} already has an overlapping direct shift assignment"
                    ),
                    "employee_id": employee.id,
                    "existing_shift_id": overlapping_assignment.shift_id,
                    "existing_shift_name": overlapping_assignment.shift.name if overlapping_assignment.shift else None,
                    "existing_start_date": str(overlapping_assignment.start_date),
                    "existing_end_date": str(overlapping_assignment.end_date) if overlapping_assignment.end_date else None,
                }, status=400)

            ShiftAssignment._base_manager.filter(
                company=company,
                assignment_type='employee',
                employee=employee,
                is_active=True
            ).update(is_active=False)

            created_assignments.append(
                ShiftAssignment._base_manager.create(
                    company=company,
                    shift=shift,
                    assignment_type='employee',
                    employee=employee,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True,
                    priority=1,
                    notes=reason,
                    created_by=request.user,
                )
            )

            # legacy mirror للموظف المباشر فقط
            EmployeeShift._base_manager.filter(
                employee=employee,
                is_active=True,
                company=company
            ).update(is_active=False)

            EmployeeShift._base_manager.create(
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

        # إشعار لكل الموظفين المتأثرين مرة واحدة فقط
        for employee in affected_employees:
            _notify_employee_shift_changed(employee, shift, request.user)

        return Response({
            "success": True,
            "pending_approval": False,
            "message": (
                f"تم تعيين الشيفت '{shift.name}' بنجاح على {len(affected_employees)} موظف"
                if lang == 'ar'
                else f"Shift '{shift.name}' assigned successfully to {len(affected_employees)} employees"
            ),
            "affected_employees_count": len(affected_employees),
            "selected_employee_count": len(direct_employees),
            "selected_department_count": len(departments),
            "selected_branch_count": len(branches),
            "excluded_employee_count": len(excluded_employees),
            "assign_to_company": assign_to_company,
            "created_assignments_count": len(created_assignments),
        }, status=201)

    except Exception as e:
        logger.exception("manager_shift_assign error")
        return Response({"success": False, "error": str(e)}, status=500)

# ── LIST EMPLOYEE SHIFTS ──
@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
                # جيب الوقت الحقيقي لو variable shift
                day_start = str(day_shift.start_time)[:5] if day_shift.start_time else None
                day_end = str(day_shift.end_time)[:5] if day_shift.end_time else None
                day_mode = getattr(day_shift, 'shift_mode', 'fixed')

                try:
                    config = getattr(day_shift, 'schedule_config', {}) or {}
                    if day_mode in ('variable_weekly', 'variable_weekly_flex'):
                        # weekday: 0=Monday في Python، بس عندنا 0=Sunday
                        # نحول: Sunday=0, Monday=1, ...
                        wd = (day.weekday() + 1) % 7  # Python: Mon=0 → Sunday=0
                        days_config = config.get('days', {})
                        day_cfg = days_config.get(str(wd), {})
                        if day_cfg.get('start'):
                            day_start = day_cfg['start']
                        if day_cfg.get('end'):
                            day_end = day_cfg['end']
                    elif day_mode == 'variable_daily':
                        dates_config = config.get('dates', {})
                        day_cfg = dates_config.get(str(day), {})
                        if day_cfg.get('start'):
                            day_start = day_cfg['start']
                        if day_cfg.get('end'):
                            day_end = day_cfg['end']
                except Exception:
                    pass

                schedule.append({
                    "date": str(day),
                    "day_name": day.strftime("%A"),
                    "shift_name": day_shift.name,
                    "start_time": day_start,
                    "end_time": day_end,
                    "crosses_midnight": day_shift.crosses_midnight,
                    "work_hours": day_shift.work_hours,
                    "is_work_day": day_shift.is_work_day(day),
                    "shift_mode": day_mode,
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def shift_change_request_action(request, request_id):
    try:
        company = _get_company(request)
        user_role = _get_user_role(request)
        if user_role not in HR_ROLES and not request.user.is_superuser:
            return Response({"success": False, "error": "غير مصرح - HR فقط"}, status=403)

        from attendance.models import ShiftChangeRequest, EmployeeShift, ShiftAssignment
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
            # طبّق الشيفت الجديد على النظام الحالي
            ShiftAssignment._base_manager.filter(
                company=company,
                assignment_type='employee',
                employee=change_req.employee,
                is_active=True
            ).update(is_active=False)

            ShiftAssignment._base_manager.create(
                company=company,
                shift=change_req.new_shift,
                assignment_type='employee',
                employee=change_req.employee,
                start_date=change_req.effective_from,
                end_date=change_req.effective_to,
                is_active=True,
                priority=1,
                notes=change_req.reason or 'Approved shift change request',
                created_by=request.user,
            )

            # legacy mirror لعدم كسر أي جزء قديم
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




# ══════════════════════════════════════════════════════
# FLEX DAY ADJUSTMENT APIs
# ══════════════════════════════════════════════════════

@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def flex_adjustments_list(request):
    """قايمة تسويات الشيفت المرن — HR فقط"""
    try:
        company = _get_company(request)
        user_role = _get_user_role(request)
        if user_role not in HR_ROLES and not request.user.is_superuser:
            return Response({"success": False, "error": "غير مصرح - HR فقط"}, status=403)

        from attendance.models import FlexDayAdjustment
        status_filter = request.query_params.get('status', 'pending')
        emp_id = request.query_params.get('employee_id')

        qs = FlexDayAdjustment._base_manager.filter(company=company)
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)
        if emp_id:
            qs = qs.filter(employee_id=emp_id)

        qs = qs.select_related('employee', 'shift', 'reviewed_by').order_by('-date')[:100]

        data = []
        for adj in qs:
            data.append({
                "id": adj.id,
                "employee_id": adj.employee_id,
                "employee_name": getattr(adj.employee, 'full_name_ar', str(adj.employee)),
                "date": str(adj.date),
                "shift_name": adj.shift.name if adj.shift else "",
                "required_hours": float(adj.required_hours),
                "actual_hours": float(adj.actual_hours),
                "delta_hours": float(adj.delta_hours),
                "adjustment_type": adj.adjustment_type,
                "adjustment_type_label": "ساعات إضافية" if adj.adjustment_type == "overtime" else "نقص ساعات",
                "status": adj.status,
                "status_label": {"pending": "قيد المراجعة", "approved": "معتمد", "rejected": "مرفوض"}.get(adj.status, adj.status),
                "reviewed_by": adj.reviewed_by.get_full_name() if adj.reviewed_by else None,
                "reviewed_at": str(adj.reviewed_at)[:16] if adj.reviewed_at else None,
                "review_notes": adj.review_notes,
            })

        return Response({"success": True, "adjustments": data, "count": len(data)})
    except Exception as e:
        logger.exception("flex_adjustments_list error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def flex_adjustment_review(request, adjustment_id):
    """HR يوافق أو يرفض تسوية شيفت مرن"""
    try:
        company = _get_company(request)
        user_role = _get_user_role(request)
        if user_role not in HR_ROLES and not request.user.is_superuser:
            return Response({"success": False, "error": "غير مصرح - HR فقط"}, status=403)

        from attendance.models import FlexDayAdjustment

        try:
            adj = FlexDayAdjustment._base_manager.get(id=adjustment_id, company=company)
        except FlexDayAdjustment.DoesNotExist:
            return Response({"success": False, "error": "التسوية غير موجودة"}, status=404)

        if adj.status != 'pending':
            return Response({"success": False, "error": "التسوية تم البت فيها مسبقاً"}, status=400)

        action = request.data.get('action')
        if action not in ('approve', 'reject'):
            return Response({"success": False, "error": "action لازم يكون approve أو reject"}, status=400)

        notes = request.data.get('notes', '')
        adj.status = 'approved' if action == 'approve' else 'rejected'
        adj.reviewed_by = request.user
        adj.reviewed_at = tz.now()
        adj.review_notes = notes
        adj.save()

        # إشعار الموظف بنتيجة المراجعة
        try:
            from accounts.fcm_service import send_notification_to_user
            employee = adj.employee
            if hasattr(employee, 'user') and employee.user:
                lang = getattr(employee, 'language', 'ar') or 'ar'
                adj_type = getattr(adj, 'adjustment_type', '')
                day_str = str(adj.date) if hasattr(adj, 'date') else ''

                if action == 'approve':
                    if lang == 'en':
                        title = '✅ Flex Adjustment Approved'
                        body  = f'Your flex day adjustment ({adj_type}) for {day_str} has been approved and will be included in your payroll.'
                    else:
                        title = '✅ تمت الموافقة على تسوية الشيفت'
                        body  = f'تمت الموافقة على تسوية شيفتك ({adj_type}) ليوم {day_str} وستُحتسب في المرتب.'
                else:
                    if lang == 'en':
                        title = '❌ Flex Adjustment Rejected'
                        body  = f'Your flex day adjustment ({adj_type}) for {day_str} has been rejected.'
                        if notes:
                            body += f' Reason: {notes}'
                    else:
                        title = '❌ تم رفض تسوية الشيفت'
                        body  = f'تم رفض تسوية شيفتك ({adj_type}) ليوم {day_str}.'
                        if notes:
                            body += f' السبب: {notes}'

                send_notification_to_user(
                    user=employee.user,
                    title=title,
                    body=body,
                    data={
                        'type': 'flex_adjustment_reviewed',
                        'adjustment_id': str(adj.id),
                        'action': action,
                        'screen': 'flex_adjustments',
                    },
                    title_en=title if lang == 'en' else None,
                    body_en=body if lang == 'en' else None,
                )
        except Exception as _notify_err:
            logging.getLogger(__name__).warning(f'flex_adjustment notify error: {_notify_err}')

        msg = "تمت الموافقة على التسوية وستُحتسب في المرتب" if action == 'approve' else "تم رفض التسوية"
        return Response({"success": True, "message": msg, "status": adj.status})

    except Exception as e:
        logger.exception("flex_adjustment_review error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_flex_adjustments(request, emp_id):
    """طلبات تسوية الشيفت المرن لموظف معين — HR أو المدير"""
    try:
        company = _get_company(request)
        user_role = _get_user_role(request)
        if user_role not in HR_ROLES and not request.user.is_superuser:
            return Response({"success": False, "error": "غير مصرح"}, status=403)

        from attendance.models import FlexDayAdjustment
        qs = FlexDayAdjustment._base_manager.filter(
            company=company,
            employee_id=emp_id,
        ).select_related('shift', 'reviewed_by').order_by('-date')[:60]

        data = [{
            "id": adj.id,
            "date": str(adj.date),
            "shift_name": adj.shift.name if adj.shift else "",
            "required_hours": float(adj.required_hours),
            "actual_hours": float(adj.actual_hours),
            "delta_hours": float(adj.delta_hours),
            "adjustment_type": adj.adjustment_type,
            "adjustment_type_label": "ساعات إضافية" if adj.adjustment_type == "overtime" else "نقص ساعات",
            "status": adj.status,
            "status_label": {"pending": "قيد المراجعة", "approved": "معتمد", "rejected": "مرفوض"}.get(adj.status, adj.status),
            "reviewed_by": adj.reviewed_by.get_full_name() if adj.reviewed_by else None,
            "reviewed_at": str(adj.reviewed_at)[:16] if adj.reviewed_at else None,
            "review_notes": adj.review_notes,
        } for adj in qs]

        return Response({"success": True, "adjustments": data, "count": len(data)})
    except Exception as e:
        logger.exception("employee_flex_adjustments error")
        return Response({"success": False, "error": str(e)}, status=500)


# ── SHIFT OVERRIDE ──

@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def shift_override_list(request):
    """قائمة كل الاستثناءات الحالية والمستقبلية"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftOverride

        show_past = request.GET.get('show_past', 'false').lower() == 'true'
        employee_id = request.GET.get('employee_id')

        qs = ShiftOverride._base_manager.filter(
            company=company,
        ).select_related('employee', 'employee__job_title', 'employee__department', 'shift').order_by('-override_date')

        if not show_past:
            qs = qs.filter(override_date__gte=date.today() - timedelta(days=7))

        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        data = []
        for o in qs[:200]:
            is_past = o.override_date < date.today()
            data.append({
                "id": o.id,
                "employee_id": o.employee_id,
                "employee_name": getattr(o.employee, "full_name_ar", str(o.employee)),
                "employee_code": getattr(o.employee, "employee_code", ""),
                "department": getattr(o.employee.department, "name_ar", "") if o.employee.department else "",
                "branch": getattr(o.employee.branch, "name_ar", "") if o.employee.branch else "",
                "shift_id": o.shift_id,
                "shift_name": o.shift.name if o.shift else "",
                "override_date": str(o.override_date),
                "reason": o.reason or "",
                "is_past": is_past,
                "created_at": str(o.created_at) if hasattr(o, 'created_at') else "",
            })

        return Response({"success": True, "overrides": data, "count": len(data)})
    except Exception as e:
        logger.exception("shift_override_list error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
        if not (hasattr(employee, 'user') and employee.user):
            return

        lang = getattr(employee, 'language', 'ar') or 'ar'

        # وقت الشيفت لو موجود
        start_str = str(shift.start_time) if shift.start_time else ''
        end_str   = str(shift.end_time)   if shift.end_time   else ''
        time_part = f' ({start_str} - {end_str})' if start_str and end_str else ''

        if lang == 'en':
            title = '🔄 Shift Updated'
            body  = f'Your shift has been changed to: {shift.name}{time_part}'
        else:
            title = '🔄 تم تحديث شيفتك'
            body  = f'تم تغيير شيفتك إلى: {shift.name}{time_part}'

        send_notification_to_user(
            user=employee.user,
            title=title,
            body=body,
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
        from accounts.fcm_service import send_notification_to_user, _get_user_lang
        from accounts.models import User
        emp_name = getattr(employee, "full_name_ar", str(employee))
        hr_users = User.objects.filter(company=company, role__in=['hr_manager', 'company_admin'])
        for hr_user in hr_users:
            lang = _get_user_lang(hr_user)
            if lang == 'en':
                title = '📋 Shift Change Request'
                body  = f'Employee {emp_name} requested a shift change to: {shift.name}'
            else:
                title = '📋 طلب تغيير شيفت'
                body  = f'طلب تغيير شيفت الموظف {emp_name} إلى: {shift.name}'
            send_notification_to_user(
                user=hr_user,
                title=title,
                body=body,
                data={
                    'type': 'shift_change_request',
                    'screen': 'shift_change_requests',
                },
                title_en='📋 Shift Change Request',
                body_en=f'Employee {emp_name} requested a shift change to: {shift.name}',
            )
    except Exception:
        pass


def _notify_manager_shift_approved(change_req):
    try:
        from accounts.fcm_service import send_notification_to_user, _get_user_lang
        if change_req.requested_by:
            emp_name = getattr(change_req.employee, "full_name_ar", str(change_req.employee))
            lang = _get_user_lang(change_req.requested_by)
            if lang == 'en':
                title = '✅ Shift Change Approved'
                body  = f'Shift change for {emp_name} to {change_req.new_shift.name} has been approved'
            else:
                title = '✅ تمت الموافقة على تغيير الشيفت'
                body  = f'تمت الموافقة على تغيير شيفت {emp_name} إلى: {change_req.new_shift.name}'
            send_notification_to_user(
                user=change_req.requested_by,
                title=title,
                body=body,
                data={
                    'type': 'shift_change_approved',
                    'request_id': str(change_req.id),
                    'screen': 'shift_change_requests',
                },
                title_en='✅ Shift Change Approved',
                body_en=f'Shift change for {emp_name} to {change_req.new_shift.name} has been approved',
            )
    except Exception:
        pass


def _notify_manager_shift_rejected(change_req):
    try:
        from accounts.fcm_service import send_notification_to_user, _get_user_lang
        if change_req.requested_by:
            emp_name = getattr(change_req.employee, "full_name_ar", str(change_req.employee))
            reason = getattr(change_req, 'rejection_reason', '') or ''
            lang = _get_user_lang(change_req.requested_by)
            if lang == 'en':
                title = '❌ Shift Change Rejected'
                body  = f'Shift change request for {emp_name} was rejected'
                if reason:
                    body += f'. Reason: {reason}'
            else:
                title = '❌ تم رفض طلب تغيير الشيفت'
                body  = f'تم رفض طلب تغيير شيفت {emp_name}'
                if reason:
                    body += f'. السبب: {reason}'
            send_notification_to_user(
                user=change_req.requested_by,
                title=title,
                body=body,
                data={
                    'type': 'shift_change_rejected',
                    'request_id': str(change_req.id),
                    'screen': 'shift_change_requests',
                },
                title_en='❌ Shift Change Rejected',
                body_en=f'Shift change request for {emp_name} was rejected',
            )
    except Exception:
        pass


def _notify_employee_shift_override(employee, shift, override_date):
    try:
        from accounts.fcm_service import send_notification_to_user
        if not (hasattr(employee, 'user') and employee.user):
            return
        lang = getattr(employee, 'language', 'ar') or 'ar'
        if lang == 'en':
            title = '📅 Exceptional Shift Override'
            body  = f'An exceptional shift has been set for you on {override_date}: {shift.name}'
        else:
            title = '📅 تعديل شيفت استثنائي'
            body  = f'تم تحديد شيفت استثنائي لك في {override_date}: {shift.name}'
        send_notification_to_user(
            user=employee.user,
            title=title,
            body=body,
            data={
                'type': 'shift_override',
                'date': str(override_date),
                'screen': 'my_shift',
            },
            title_en='📅 Exceptional Shift Override',
            body_en=f'An exceptional shift has been set for you on {override_date}: {shift.name}',
        )
    except Exception:
        pass


# ── PARTIAL CHECKOUT / SESSION APIs ──
@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def partial_checkout(request):
    """
    خروج جزئي — الموظف بيخرج ويرجع تاني
    يُستخدم مع shift_mode: flex_split أو split_fixed
    """
    try:
        from employees.models import Employee
        from attendance.models import Attendance, AttendanceSession

        employee = Employee._base_manager.filter(user=request.user).first()
        if not employee:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

        today = timezone.localdate()
        attendance = Attendance._base_manager.filter(
            employee=employee, date=today
        ).first()

        if not attendance:
            return Response({"success": False, "error": "مفيش سجل حضور لليوم ده"}, status=400)

        shift, _ = get_effective_shift(employee, today)
        if shift and not shift.allow_partial_checkout:
            return Response({"success": False, "error": "الشيفت ده مش بيسمح بخروج جزئي"}, status=400)

        # شوف آخر session مفتوحة (مالهاش check_out)
        open_session = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee,
            check_out_time__isnull=True
        ).order_by('-session_number').first()

        if not open_session:
            return Response({"success": False, "error": "مفيش فترة مفتوحة تقدر تخرج منها"}, status=400)

        now = timezone.now()
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')

        open_session.check_out_time = now
        if lat:
            open_session.check_out_latitude = lat
        if lon:
            open_session.check_out_longitude = lon
        open_session.is_partial = True
        open_session.calculate_worked_minutes()
        open_session.save()

        return Response({
            "success": True,
            "message": "تم تسجيل الخروج الجزئي",
            "session_number": open_session.session_number,
            "worked_minutes": open_session.worked_minutes,
            "check_out_time": now.strftime('%I:%M %p'),
        })

    except Exception as e:
        logger.exception("partial_checkout error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def resume_checkin(request):
    """
    عودة للعمل بعد خروج جزئي
    بتفتح session جديدة
    """
    try:
        from employees.models import Employee
        from attendance.models import Attendance, AttendanceSession

        employee = Employee._base_manager.filter(user=request.user).first()
        if not employee:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

        today = timezone.localdate()
        attendance = Attendance._base_manager.filter(
            employee=employee, date=today
        ).first()

        if not attendance:
            return Response({"success": False, "error": "مفيش سجل حضور لليوم ده"}, status=400)

        shift, _ = get_effective_shift(employee, today)
        if shift and not shift.allow_partial_checkout:
            return Response({"success": False, "error": "الشيفت ده مش بيسمح بالرجوع بعد الخروج"}, status=400)

        # تأكيد إن فيه partial checkout قبل كده
        last_session = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee
        ).order_by('-session_number').first()

        if not last_session:
            return Response({"success": False, "error": "مفيش خروج جزئي قبل كده"}, status=400)

        if last_session.check_out_time is None:
            return Response({"success": False, "error": "لسه مسجلتش خروج جزئي"}, status=400)

        # شوف max sessions
        max_sessions = shift.max_sessions_per_day if shift else 2
        current_count = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee
        ).count()

        if current_count >= max_sessions:
            return Response({
                "success": False,
                "error": f"وصلت للحد الأقصى من الفترات ({max_sessions} فترات)"
            }, status=400)

        now = timezone.now()

        from attendance.api_mobile import get_current_split_period, get_shift_periods
        current_split_period = get_current_split_period(shift, now)
        if shift and getattr(shift, 'shift_mode', 'fixed') == 'split_fixed' and not current_split_period:
            periods = get_shift_periods(shift, today)
            periods_text = " / ".join(
                [f"{p['name']}: {p['start_str']} - {p['end_str']}" for p in periods]
            ) or "لا توجد فترات معرفة"
            return Response({
                "success": False,
                "error": f"لا يمكن تسجيل العودة الآن. مسموح فقط أثناء فترات الشيفت المحددة: {periods_text}",
                "outside_allowed_period": True,
                "shift_periods": [
                    {
                        "period_number": p["period_number"],
                        "name": p["name"],
                        "start": p["start_str"],
                        "end": p["end_str"],
                    }
                    for p in periods
                ],
            }, status=400)

        lat = request.data.get('latitude')
        lon = request.data.get('longitude')

        new_session = AttendanceSession._base_manager.create(
            company=employee.company,
            attendance=attendance,
            employee=employee,
            session_number=current_count + 1,
            check_in_time=now,
            check_in_latitude=lat,
            check_in_longitude=lon,
            is_partial=False,
        )

        return Response({
            "success": True,
            "message": "تم تسجيل العودة للعمل",
            "session_number": new_session.session_number,
            "check_in_time": now.strftime('%I:%M %p'),
        })

    except Exception as e:
        logger.exception("resume_checkin error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def today_sessions(request):
    """
    جيب كل الفترات لليوم ده للموظف
    """
    try:
        from employees.models import Employee
        from attendance.models import Attendance, AttendanceSession

        employee = Employee._base_manager.filter(user=request.user).first()
        if not employee:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

        today = timezone.localdate()
        attendance = Attendance._base_manager.filter(
            employee=employee, date=today
        ).first()

        if not attendance:
            return Response({"success": True, "sessions": [], "total_worked_minutes": 0})

        sessions = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee
        ).order_by('session_number')

        total_minutes = 0
        data = []
        for s in sessions:
            worked = s.worked_minutes if s.is_complete else 0
            total_minutes += worked
            data.append({
                "session_number": s.session_number,
                "check_in": s.check_in_time.strftime('%I:%M %p') if s.check_in_time else None,
                "check_out": s.check_out_time.strftime('%I:%M %p') if s.check_out_time else None,
                "is_partial": s.is_partial,
                "is_complete": s.is_complete,
                "worked_minutes": worked,
            })

        return Response({
            "success": True,
            "sessions": data,
            "total_worked_minutes": total_minutes,
            "sessions_count": len(data),
        })

    except Exception as e:
        logger.exception("today_sessions error")
        return Response({"success": False, "error": str(e)}, status=500)



# ══════════════════════════════════════
# BATCH 1: Shift Assignments Management APIs
# ══════════════════════════════════════

@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_assignments_list(request):
    """قائمة كل التعيينات الحالية للشيفتات في الشركة"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftAssignment
        lang = request.GET.get("lang", "ar")
        shift_id = request.GET.get("shift_id")

        qs = ShiftAssignment._base_manager.filter(
            company=company,
            is_active=True,
        ).select_related(
            "shift", "employee", "employee__job_title", "employee__department", "employee__branch",
            "department", "branch"
        ).prefetch_related(
            "excluded_employees"
        ).order_by("shift__name", "assignment_type", "-start_date")

        if shift_id:
            qs = qs.filter(shift_id=shift_id)

        data = []
        for a in qs:
            excluded_list = []
            if a.assignment_type in ("department", "branch", "company"):
                for excl_emp in a.excluded_employees.all():
                    excluded_list.append({
                        "id": excl_emp.id,
                        "full_name": getattr(excl_emp, "full_name_ar", str(excl_emp)),
                        "employee_code": getattr(excl_emp, "employee_code", ""),
                        "department": getattr(excl_emp.department, "name_ar", "") if excl_emp.department else "",
                        "branch": getattr(excl_emp.branch, "name_ar", "") if excl_emp.branch else "",
                    })

            item = {
                "id": a.id,
                "shift_id": a.shift_id,
                "shift_name": a.shift.name if a.shift else "",
                "assignment_type": a.assignment_type,
                "start_date": str(a.start_date),
                "end_date": str(a.end_date) if a.end_date else None,
                "notes": a.notes or "",
                "priority": a.priority,
                "excluded_employees": excluded_list,
                "excluded_count": len(excluded_list),
            }
            if a.assignment_type == "employee" and a.employee:
                item["target_id"] = a.employee.id
                item["target_name"] = getattr(a.employee, "full_name_ar", str(a.employee))
                item["target_sub"] = getattr(a.employee.job_title, "name_ar", "") if a.employee.job_title else ""
                item["department"] = getattr(a.employee.department, "name_ar", "") if a.employee.department else ""
                item["branch"] = getattr(a.employee.branch, "name_ar", "") if a.employee.branch else ""
            elif a.assignment_type == "department" and a.department:
                item["target_id"] = a.department.id
                item["target_name"] = a.department.name_ar if lang == "ar" else (a.department.name_en or a.department.name_ar)
                item["target_sub"] = ""
                item["department"] = item["target_name"]
                item["branch"] = ""
            elif a.assignment_type == "branch" and a.branch:
                item["target_id"] = a.branch.id
                item["target_name"] = a.branch.name_ar if lang == "ar" else (a.branch.name_en or a.branch.name_ar)
                item["target_sub"] = ""
                item["department"] = ""
                item["branch"] = item["target_name"]
            elif a.assignment_type == "company":
                item["target_id"] = company.id
                item["target_name"] = company.name_ar if lang == "ar" else (company.name_en or company.name_ar)
                item["target_sub"] = ""
                item["department"] = ""
                item["branch"] = ""
            else:
                continue
            data.append(item)

        return Response({"success": True, "assignments": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_shift_assignments_list error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["PUT", "PATCH"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_assignment_update(request, assignment_id):
    """تعديل تعيين شيفت موجود (تاريخ / ملاحظات)"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftAssignment
        try:
            assignment = ShiftAssignment._base_manager.get(id=assignment_id, company=company, is_active=True)
        except ShiftAssignment.DoesNotExist:
            return Response({"success": False, "error": "التعيين غير موجود"}, status=404)

        data = request.data
        changed = False

        if "start_date" in data:
            try:
                assignment.start_date = datetime.strptime(str(data["start_date"]), "%Y-%m-%d").date()
                changed = True
            except ValueError:
                return Response({"success": False, "error": "صيغة start_date غلط"}, status=400)

        if "end_date" in data:
            if data["end_date"]:
                try:
                    assignment.end_date = datetime.strptime(str(data["end_date"]), "%Y-%m-%d").date()
                    changed = True
                except ValueError:
                    return Response({"success": False, "error": "صيغة end_date غلط"}, status=400)
            else:
                assignment.end_date = None
                changed = True

        if "notes" in data:
            assignment.notes = data["notes"]
            changed = True

        if changed:
            assignment.save()

        # تعديل قائمة المستثنيين (مسموح لأي assignment_type غير employee)
        if "excluded_employee_ids" in data and assignment.assignment_type != "employee":
            from employees.models import Employee
            ids = data.get("excluded_employee_ids") or []
            if not isinstance(ids, list):
                return Response({"success": False, "error": "excluded_employee_ids لازم يكون list"}, status=400)

            clean_ids = []
            seen = set()
            for v in ids:
                try:
                    n = int(v)
                except (TypeError, ValueError):
                    continue
                if n not in seen:
                    seen.add(n)
                    clean_ids.append(n)

            if clean_ids:
                excluded_employees = list(Employee._base_manager.filter(id__in=clean_ids, company=company))
                if len(excluded_employees) != len(clean_ids):
                    return Response({"success": False, "error": "بعض الموظفين المستثنين غير موجودين"}, status=404)
                assignment.excluded_employees.set(excluded_employees)
            else:
                assignment.excluded_employees.clear()

        return Response({
            "success": True,
            "message": "تم تعديل التعيين بنجاح",
            "assignment_id": assignment.id,
            "excluded_count": assignment.excluded_employees.count(),
        })
    except Exception as e:
        logger.exception("manager_shift_assignment_update error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_shift_assignment_delete(request, assignment_id):
    """حذف (إلغاء تفعيل) تعيين شيفت"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftAssignment
        try:
            assignment = ShiftAssignment._base_manager.get(id=assignment_id, company=company, is_active=True)
        except ShiftAssignment.DoesNotExist:
            return Response({"success": False, "error": "التعيين غير موجود أو اتحذف قبل كده"}, status=404)

        assignment.is_active = False
        assignment.save()

        # لو التعيين كان لموظف مباشر → نلغي الـ EmployeeShift المرآة برضو
        if assignment.assignment_type == 'employee' and assignment.employee:
            from attendance.models import EmployeeShift
            EmployeeShift._base_manager.filter(
                company=company,
                employee=assignment.employee,
                shift=assignment.shift,
                is_active=True,
            ).update(is_active=False)

        return Response({"success": True, "message": "تم إلغاء التعيين بنجاح", "assignment_id": assignment_id})
    except Exception as e:
        logger.exception("manager_shift_assignment_delete error")
        return Response({"success": False, "error": str(e)}, status=500)


# ══════════════════════════════════════
# ROTATION APIs
# ══════════════════════════════════════

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def rotation_list_create(request):
    err = _check_manager(request)
    if err:
        return err
    company = _get_company(request)
    from attendance.models import ShiftRotation, ShiftRotationSlot

    if request.method == "GET":
        rotations = ShiftRotation._base_manager.filter(
            company=company
        ).prefetch_related('slots', 'slots__shift').order_by('-start_date')

        data = []
        for r in rotations:
            slots = []
            for s in r.slots.all():
                slots.append({
                    "id": s.id,
                    "start_day_index": s.start_day_index,
                    "end_day_index": s.end_day_index,
                    "shift_id": s.shift_id,
                    "shift_name": s.shift.name if s.shift else None,
                })
            data.append({
                "id": r.id,
                "name": r.name,
                "cycle_length_days": r.cycle_length_days,
                "start_date": str(r.start_date),
                "is_active": r.is_active,
                "slots": slots,
            })
        return Response({"success": True, "rotations": data, "count": len(data)})

    # POST - إنشاء rotation جديد
    d = request.data
    name = d.get("name", "").strip()
    start_date = d.get("start_date")
    slots_data = d.get("slots", [])

    try:
        cycle_length_days = int(d.get("cycle_length_days", 7))
    except (TypeError, ValueError):
        return Response({"success": False, "error": "cycle_length_days لازم يكون رقم صحيح"}, status=400)

    if not name or not start_date:
        return Response({"success": False, "error": "name و start_date مطلوبان"}, status=400)

    if cycle_length_days <= 0:
        return Response({"success": False, "error": "cycle_length_days لازم يكون أكبر من صفر"}, status=400)

    try:
        start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()
    except ValueError:
        return Response({"success": False, "error": "صيغة التاريخ لازم تكون YYYY-MM-DD"}, status=400)

    if not isinstance(slots_data, list):
        return Response({"success": False, "error": "slots لازم تكون قائمة"}, status=400)

    from attendance.models import Shift
    from django.db import transaction

    validated_slots = []
    covered_days = set()

    for index, slot in enumerate(slots_data, start=1):
        if not isinstance(slot, dict):
            return Response({"success": False, "error": f"slot رقم {index} غير صالح"}, status=400)

        try:
            start_idx = int(slot["start_day_index"])
            end_idx = int(slot["end_day_index"])
        except (KeyError, TypeError, ValueError):
            return Response({
                "success": False,
                "error": f"slot رقم {index}: start_day_index و end_day_index لازم يكونوا أرقام صحيحة"
            }, status=400)

        if start_idx < 0 or end_idx < 0:
            return Response({
                "success": False,
                "error": f"slot رقم {index}: أرقام الأيام لازم تبدأ من 0 أو أكبر"
            }, status=400)

        if start_idx > end_idx:
            return Response({
                "success": False,
                "error": f"slot رقم {index}: start_day_index لازم يكون أصغر من أو يساوي end_day_index"
            }, status=400)

        if end_idx >= cycle_length_days:
            return Response({
                "success": False,
                "error": f"slot رقم {index}: end_day_index خارج حدود دورة التناوب"
            }, status=400)

        shift_id = slot.get("shift_id")
        if not shift_id:
            return Response({
                "success": False,
                "error": f"slot رقم {index}: لازم تختار شيفت لكل فترة في دورة التناوب"
            }, status=400)

        try:
            shift = Shift._base_manager.get(id=int(shift_id), company=company)
        except (TypeError, ValueError, Shift.DoesNotExist):
            return Response({
                "success": False,
                "error": f"slot رقم {index}: الشيفت غير موجود أو لا ينتمي للشركة"
            }, status=400)

        slot_days = set(range(start_idx, end_idx + 1))
        overlap_days = sorted(slot_days & covered_days)
        if overlap_days:
            return Response({
                "success": False,
                "error": f"slot رقم {index}: يوجد تداخل في الأيام داخل دورة التناوب",
                "overlap_day_indexes": overlap_days,
            }, status=400)

        covered_days.update(slot_days)
        validated_slots.append({
            "start_day_index": start_idx,
            "end_day_index": end_idx,
            "shift": shift,
        })

    missing_days = [day for day in range(cycle_length_days) if day not in covered_days]
    if missing_days:
        return Response({
            "success": False,
            "error": "دورة التناوب لازم تغطي كل أيام الدورة من غير فجوات",
            "missing_day_indexes": missing_days,
        }, status=400)

    with transaction.atomic():
        rotation = ShiftRotation._base_manager.create(
            company=company,
            name=name,
            cycle_length_days=cycle_length_days,
            start_date=start_date,
            is_active=True,
            created_by=request.user,
        )

        for slot in validated_slots:
            ShiftRotationSlot._base_manager.create(
                company=company,
                rotation=rotation,
                start_day_index=slot["start_day_index"],
                end_day_index=slot["end_day_index"],
                shift=slot["shift"],
                created_by=request.user,
            )

    return Response({
        "success": True,
        "rotation_id": rotation.id,
        "slots_count": len(validated_slots),
        "message": f"تم إنشاء التناوب '{name}'"
    }, status=201)


@api_view(["PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def rotation_detail(request, rotation_id):
    err = _check_manager(request)
    if err:
        return err
    company = _get_company(request)
    from attendance.models import ShiftRotation, ShiftRotationSlot

    try:
        rotation = ShiftRotation._base_manager.get(id=rotation_id, company=company)
    except ShiftRotation.DoesNotExist:
        return Response({"success": False, "error": "التناوب غير موجود"}, status=404)

    if request.method == "DELETE":
        rotation.delete()
        return Response({"success": True, "message": "تم حذف التناوب"})

    # PUT
    d = request.data
    if "name" in d:
        rotation.name = d["name"]

    if "cycle_length_days" in d:
        try:
            rotation.cycle_length_days = int(d["cycle_length_days"])
        except (TypeError, ValueError):
            return Response({"success": False, "error": "cycle_length_days لازم يكون رقم صحيح"}, status=400)

        if rotation.cycle_length_days <= 0:
            return Response({"success": False, "error": "cycle_length_days لازم يكون أكبر من صفر"}, status=400)

    if "start_date" in d:
        try:
            rotation.start_date = datetime.strptime(str(d["start_date"]), "%Y-%m-%d").date()
        except ValueError:
            return Response({"success": False, "error": "صيغة التاريخ لازم تكون YYYY-MM-DD"}, status=400)

    if "is_active" in d:
        rotation.is_active = bool(d["is_active"])

    rotation.save()

    slots = list(
        ShiftRotationSlot._base_manager.filter(
            rotation=rotation,
            company=company
        ).select_related('shift').order_by('start_day_index', 'id')
    )

    covered_days = set()
    overlap_days = set()
    invalid_slot_ids = []
    missing_shift_slot_ids = []

    for slot in slots:
        try:
            start_idx = int(slot.start_day_index)
            end_idx = int(slot.end_day_index)
        except (TypeError, ValueError):
            invalid_slot_ids.append(slot.id)
            continue

        if start_idx < 0 or end_idx < 0 or start_idx > end_idx or end_idx >= rotation.cycle_length_days:
            invalid_slot_ids.append(slot.id)
            continue

        if not slot.shift_id:
            missing_shift_slot_ids.append(slot.id)

        slot_days = set(range(start_idx, end_idx + 1))
        overlap_days.update(slot_days & covered_days)
        covered_days.update(slot_days)

    missing_days = [day for day in range(rotation.cycle_length_days) if day not in covered_days]
    coverage_ok = not invalid_slot_ids and not overlap_days and not missing_days and not missing_shift_slot_ids

    response_data = {
        "success": True,
        "message": "تم تعديل التناوب",
        "rotation_coverage_ok": coverage_ok,
    }

    if not coverage_ok:
        response_data["warning"] = "تم تعديل التناوب لكن التغطية فيها فجوات أو مشاكل. راجع الـ slots"
        response_data["coverage_details"] = {
            "missing_day_indexes": missing_days,
            "overlap_day_indexes": sorted(overlap_days),
            "invalid_slot_ids": invalid_slot_ids,
            "missing_shift_slot_ids": missing_shift_slot_ids,
        }

    return Response(response_data)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def rotation_assign(request, rotation_id):
    err = _check_manager(request)
    if err:
        return err
    company = _get_company(request)
    from attendance.models import ShiftRotation, ShiftRotationAssignment
    from employees.models import Employee
    from companies.models import Department, Branch

    try:
        rotation = ShiftRotation._base_manager.get(id=rotation_id, company=company)
    except ShiftRotation.DoesNotExist:
        return Response({"success": False, "error": "التناوب غير موجود"}, status=404)

    d = request.data
    assignment_type = d.get("assignment_type", "employee")
    start_date_raw = d.get("start_date")
    end_date_raw = d.get("end_date")

    if not start_date_raw:
        return Response({"success": False, "error": "start_date مطلوب"}, status=400)

    start_date = datetime.strptime(str(start_date_raw), "%Y-%m-%d").date()
    end_date = datetime.strptime(str(end_date_raw), "%Y-%m-%d").date() if end_date_raw else None

    priority_map = {"employee": 1, "department": 2, "branch": 3, "company": 4}
    priority = priority_map.get(assignment_type, 4)

    kwargs = {
        "company": company,
        "rotation": rotation,
        "assignment_type": assignment_type,
        "start_date": start_date,
        "end_date": end_date,
        "priority": priority,
        "is_active": True,
        "created_by": request.user,
    }

    if assignment_type == "employee":
        emp_id = d.get("employee_id")
        if not emp_id:
            return Response({"success": False, "error": "employee_id مطلوب"}, status=400)
        kwargs["employee"] = Employee._base_manager.get(id=emp_id, company=company)

    elif assignment_type == "department":
        dept_id = d.get("department_id")
        if not dept_id:
            return Response({"success": False, "error": "department_id مطلوب"}, status=400)
        kwargs["department"] = Department.objects.get(id=dept_id, company=company)

    elif assignment_type == "branch":
        branch_id = d.get("branch_id")
        if not branch_id:
            return Response({"success": False, "error": "branch_id مطلوب"}, status=400)
        kwargs["branch"] = Branch.objects.get(id=branch_id, company=company)

    # نلغي أي تناوب نشط قديم من نفس النوع لنفس الهدف قبل ما نضيف الجديد
    dedup_filter = {
        "company": company,
        "assignment_type": assignment_type,
        "is_active": True,
    }

    if assignment_type == "employee":
        dedup_filter["employee"] = kwargs.get("employee")
    elif assignment_type == "department":
        dedup_filter["department"] = kwargs.get("department")
    elif assignment_type == "branch":
        dedup_filter["branch"] = kwargs.get("branch")

    ShiftRotationAssignment._base_manager.filter(**dedup_filter).update(is_active=False)

    ShiftRotationAssignment._base_manager.create(**kwargs)

    return Response({"success": True, "message": f"تم تعيين التناوب '{rotation.name}' بنجاح"}, status=201)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def rotation_assignments_list(request, rotation_id):
    err = _check_manager(request)
    if err:
        return err
    company = _get_company(request)
    from attendance.models import ShiftRotation, ShiftRotationAssignment

    try:
        rotation = ShiftRotation._base_manager.get(id=rotation_id, company=company)
    except ShiftRotation.DoesNotExist:
        return Response({"success": False, "error": "التناوب غير موجود"}, status=404)

    assignments = ShiftRotationAssignment._base_manager.filter(
        rotation=rotation,
        is_active=True,
        company=company,
    ).select_related("employee", "department", "branch")

    data = []
    for a in assignments:
        item = {
            "id": a.id,
            "assignment_type": a.assignment_type,
            "start_date": str(a.start_date),
            "end_date": str(a.end_date) if a.end_date else None,
        }
        if a.assignment_type == "employee" and a.employee:
            item["target_name"] = getattr(a.employee, "full_name_ar", str(a.employee))
        elif a.assignment_type == "department" and a.department:
            item["target_name"] = a.department.name_ar
        elif a.assignment_type == "branch" and a.branch:
            item["target_name"] = a.branch.name_ar
        else:
            item["target_name"] = "الشركة كلها"
        data.append(item)

    return Response({"success": True, "assignments": data, "rotation_name": rotation.name})


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def rotation_assignment_delete(request, assignment_id):
    """حذف (إلغاء تفعيل) تعيين تناوب"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        from attendance.models import ShiftRotationAssignment
        try:
            assignment = ShiftRotationAssignment._base_manager.get(
                id=assignment_id, company=company, is_active=True
            )
        except ShiftRotationAssignment.DoesNotExist:
            return Response(
                {"success": False, "error": "تعيين التناوب غير موجود أو اتحذف قبل كده"},
                status=404,
            )

        assignment.is_active = False
        assignment.save()

        return Response({
            "success": True,
            "message": "تم إلغاء تعيين التناوب بنجاح",
            "assignment_id": assignment_id,
        })
    except Exception as e:
        logger.exception("rotation_assignment_delete error")
        return Response({"success": False, "error": str(e)}, status=500)

