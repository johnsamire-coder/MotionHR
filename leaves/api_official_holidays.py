"""
MotionHR - Official Holidays API
إدارة الإجازات الرسمية
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
from leaves.official_holiday_models import OfficialHoliday, OfficialHolidayRule

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


def _rule_data(rule):
    return {
        "id": rule.id,
        "scope": rule.scope,
        "scope_display": rule.get_scope_display(),
        "branch_id": rule.branch_id,
        "branch_name": rule.branch.name_ar if rule.branch else None,
        "department_id": rule.department_id,
        "department_name": rule.department.name_ar if rule.department else None,
        "employee_ids": list(rule.employees.values_list("id", flat=True)),
        "treatment": rule.treatment,
        "treatment_display": rule.get_treatment_display(),
        "bonus_calc_method": rule.bonus_calc_method,
        "bonus_fixed_amount": float(rule.bonus_fixed_amount),
        "bonus_salary_percentage": float(rule.bonus_salary_percentage),
        "bonus_day_multiplier": float(rule.bonus_day_multiplier),
        "priority": rule.priority,
    }


def _holiday_data(holiday):
    return {
        "id": holiday.id,
        "name": holiday.name,
        "start_date": str(holiday.start_date),
        "end_date": str(holiday.end_date),
        "days_count": holiday.days_count,
        "notes": holiday.notes,
        "is_active": holiday.is_active,
        "send_notification": holiday.send_notification,
        "remind_day_before": holiday.remind_day_before,
        "created_at": str(holiday.created_at)[:16],
        "rules": [
            _rule_data(r)
            for r in OfficialHolidayRule._base_manager.filter(holiday=holiday).prefetch_related("employees")
        ],
    }


def _save_rules(holiday, rules_data, company):
    from leaves.official_holiday_models import OfficialHolidayRule
    from companies.models import Branch, Department
    from employees.models import Employee

    OfficialHolidayRule._base_manager.filter(holiday=holiday).delete()

    for r in rules_data:
        scope = r.get("scope", "company")
        branch = None
        department = None

        if scope == "branch" and r.get("branch_id"):
            branch = Branch._base_manager.filter(
                id=r["branch_id"], company=company
            ).first()

        if scope == "department" and r.get("department_id"):
            department = Department._base_manager.filter(
                id=r["department_id"], company=company
            ).first()

        rule = OfficialHolidayRule._base_manager.create(
            company=company,
            holiday=holiday,
            scope=scope,
            branch=branch,
            department=department,
            treatment=r.get("treatment", "paid_leave"),
            bonus_calc_method=r.get("bonus_calc_method", ""),
            bonus_fixed_amount=r.get("bonus_fixed_amount", 0),
            bonus_salary_percentage=r.get("bonus_salary_percentage", 0),
            bonus_day_multiplier=r.get("bonus_day_multiplier", 2.0),
            priority=r.get("priority", 10),
            created_by=holiday.created_by,
        )

        if scope == "employees" and r.get("employee_ids"):
            emps = Employee._base_manager.filter(
                id__in=r["employee_ids"], company=company
            )
            rule.employees.set(emps)


def _send_holiday_notification(holiday, company):
    try:
        from accounts.models import EmployeeNotification
        from employees.models import Employee

        rules = list(OfficialHolidayRule._base_manager.filter(holiday=holiday).prefetch_related("employees"))

        notified_ids = set()

        for rule in rules:
            if rule.treatment == "normal_work":
                continue

            if rule.scope == "company":
                employees = Employee._base_manager.filter(
                    company=company, status="active"
                )
            elif rule.scope == "branch" and rule.branch_id:
                employees = Employee._base_manager.filter(
                    company=company, branch_id=rule.branch_id, status="active"
                )
            elif rule.scope == "department" and rule.department_id:
                employees = Employee._base_manager.filter(
                    company=company, department_id=rule.department_id, status="active"
                )
            elif rule.scope == "employees":
                employees = rule.employees.filter(status="active")
            else:
                continue

            if rule.treatment == "paid_leave":
                title = f"إجازة رسمية: {holiday.name}"
                message = (
                    f"تم الإعلان عن إجازة رسمية بعنوان '{holiday.name}' "
                    f"من {holiday.start_date} إلى {holiday.end_date} "
                    f"({holiday.days_count} يوم). هذه إجازة مدفوعة."
                )
            else:
                title = f"عمل في إجازة رسمية: {holiday.name}"
                message = (
                    f"ستكون يوم '{holiday.name}' يوم عمل بمقابل إضافي "
                    f"من {holiday.start_date} إلى {holiday.end_date}."
                )

            for emp in employees:
                if emp.id in notified_ids:
                    continue
                notified_ids.add(emp.id)
                EmployeeNotification._base_manager.create(
                    employee=emp,
                    title=title,
                    message=message,
                    notification_type="general",
                    severity="info",
                )

        logger.info(
            f"Holiday notifications sent for '{holiday.name}' to {len(notified_ids)} employees"
        )
    except Exception:
        logger.exception("_send_holiday_notification error")


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def official_holiday_list_create(request):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    from leaves.official_holiday_models import OfficialHoliday

    if request.method == "GET":
        qs = OfficialHoliday._base_manager.filter(
            company=company, is_active=True
        ).prefetch_related("rules__employees", "rules__branch", "rules__department")
        return Response({
            "success": True,
            "holidays": [_holiday_data(h) for h in qs],
            "count": qs.count(),
        })

    data = request.data
    name = str(data.get("name", "")).strip()
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not name or not start_date or not end_date:
        return Response({
            "success": False,
            "error": "اسم الإجازة وتاريخ البداية والنهاية مطلوبين"
        }, status=400)

    try:
        from datetime import date as _date
        start_date = _date.fromisoformat(str(start_date))
        end_date = _date.fromisoformat(str(end_date))
    except Exception:
        return Response({
            "success": False,
            "error": "صيغة التاريخ غلط، لازم تكون YYYY-MM-DD"
        }, status=400)

    try:
        from datetime import date as _date
        start_date = _date.fromisoformat(str(start_date))
        end_date = _date.fromisoformat(str(end_date))
    except Exception:
        return Response({
            "success": False,
            "error": "صيغة التاريخ غلط، لازم تكون YYYY-MM-DD"
        }, status=400)

    if end_date < start_date:
        return Response({
            "success": False,
            "error": "تاريخ النهاية لازم يكون بعد تاريخ البداية"
        }, status=400)

    try:
        holiday = OfficialHoliday._base_manager.create(
            company=company,
            name=name,
            start_date=start_date,
            end_date=end_date,
            notes=str(data.get("notes", "")),
            send_notification=bool(data.get("send_notification", True)),
            remind_day_before=bool(data.get("remind_day_before", False)),
            created_by=request.user,
        )

        rules_data = data.get("rules", [])
        if not rules_data:
            from leaves.official_holiday_models import OfficialHolidayRule
            OfficialHolidayRule._base_manager.create(
                company=company,
                holiday=holiday,
                scope="company",
                treatment="paid_leave",
                created_by=request.user,
            )
        else:
            _save_rules(holiday, rules_data, company)

        if holiday.send_notification:
            _send_holiday_notification(holiday, company)

        return Response({
            "success": True,
            "holiday": _holiday_data(holiday)
        }, status=201)

    except Exception as e:
        logger.exception("official_holiday_list_create POST error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def official_holiday_detail(request, holiday_id):
    err = _check_hr(request)
    if err:
        return err
    company = _get_company(request)

    from leaves.official_holiday_models import OfficialHoliday

    try:
        holiday = OfficialHoliday._base_manager.get(
            id=holiday_id, company=company
        )
    except OfficialHoliday.DoesNotExist:
        return Response({"success": False, "error": "الإجازة غير موجودة"}, status=404)

    if request.method == "GET":
        return Response({"success": True, "holiday": _holiday_data(holiday)})

    if request.method == "DELETE":
        holiday.is_active = False
        holiday.save(update_fields=["is_active"])
        return Response({"success": True, "message": "تم حذف الإجازة"})

    data = request.data
    name = str(data.get("name", holiday.name)).strip()
    start_date = data.get("start_date", str(holiday.start_date))
    end_date = data.get("end_date", str(holiday.end_date))

    try:
        from datetime import date as _date
        start_date = _date.fromisoformat(str(start_date))
        end_date = _date.fromisoformat(str(end_date))
    except Exception:
        return Response({
            "success": False,
            "error": "صيغة التاريخ غلط، لازم تكون YYYY-MM-DD"
        }, status=400)

    try:
        from datetime import date as _date
        start_date = _date.fromisoformat(str(start_date))
        end_date = _date.fromisoformat(str(end_date))
    except Exception:
        return Response({
            "success": False,
            "error": "صيغة التاريخ غلط، لازم تكون YYYY-MM-DD"
        }, status=400)

    if end_date < start_date:
        return Response({
            "success": False,
            "error": "تاريخ النهاية لازم يكون بعد تاريخ البداية"
        }, status=400)

    try:
        holiday.name = name
        holiday.start_date = start_date
        holiday.end_date = end_date
        holiday.notes = str(data.get("notes", holiday.notes))
        holiday.send_notification = bool(data.get("send_notification", holiday.send_notification))
        holiday.remind_day_before = bool(data.get("remind_day_before", holiday.remind_day_before))
        holiday.updated_by = request.user
        holiday.save()

        if "rules" in data:
            _save_rules(holiday, data["rules"], company)

        return Response({"success": True, "holiday": _holiday_data(holiday)})

    except Exception as e:
        logger.exception("official_holiday_detail PUT error")
        return Response({"success": False, "error": str(e)}, status=500)
