"""
MotionHR - Payroll Rules Engine
Phase 15: Payroll Pro
Mission-aware + Shift-aware + Policy-aware
+ Allowances / Deductions / Bonuses / Penalties / Installments / Insurance
"""
from datetime import date, timedelta, datetime
from calendar import monthrange
from django.db.models import Q
from .models import Attendance


def _get_shift_for_date(employee, target_date):
    """يجيب الشيفت الفعلي للموظف في يوم معين"""
    try:
        from attendance.api_shifts import get_effective_shift
        shift, source = get_effective_shift(employee, target_date)
        return shift
    except Exception:
        return None


def _calc_late_minutes(shift, att):
    """يحسب دقائق التأخير بناءً على الشيفت الفعلي"""
    if not shift or not att or not att.check_in_time:
        return 0
    try:
        from django.utils import timezone
        shift_start = datetime.combine(att.check_in_time.date(), shift.start_time)
        grace = int(shift.grace_period or 0)
        deadline = shift_start + timedelta(minutes=grace)
        check_in_local = timezone.localtime(att.check_in_time)
        check_in_naive = check_in_local.replace(tzinfo=None)
        if check_in_naive > deadline:
            return int((check_in_naive - deadline).total_seconds() / 60)
        return 0
    except Exception:
        return int(getattr(att, 'late_minutes', 0) or 0)


def _calc_overtime_hours(shift, att):
    """يحسب ساعات الأوفر تايم بناءً على الشيفت الفعلي"""
    if not shift or not att or not att.check_in_time or not att.check_out_time:
        return float(getattr(att, 'overtime_hours', 0) or 0)
    try:
        from django.utils import timezone
        today = att.check_in_time.date()
        shift_end = datetime.combine(today, shift.end_time)
        if shift.crosses_midnight or shift.end_time <= shift.start_time:
            shift_end += timedelta(days=1)
        check_out_local = timezone.localtime(att.check_out_time)
        check_out_naive = check_out_local.replace(tzinfo=None)
        if check_out_naive > shift_end:
            ot_minutes = (check_out_naive - shift_end).total_seconds() / 60
            return round(ot_minutes / 60, 2)
        return 0.0
    except Exception:
        return float(getattr(att, 'overtime_hours', 0) or 0)


def _is_night_shift(shift):
    """هل الشيفت ليلي؟"""
    if not shift:
        return False
    return bool(getattr(shift, 'crosses_midnight', False)) or shift.shift_mode == 'night'


def _is_weekend_work(shift, target_date):
    """هل الموظف اشتغل يوم راحة؟"""
    if not shift:
        return False
    try:
        return not shift.is_work_day(target_date)
    except Exception:
        return False


def _safe_float(value, default=0.0):
    try:
        return float(value or 0)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(value or 0)
    except Exception:
        return default


def _period_bounds(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return first_day, last_day


def _employee_name(employee, lang='ar'):
    if lang == 'en':
        parts = [
            getattr(employee, 'first_name_en', None),
            getattr(employee, 'last_name_en', None),
        ]
        text = ' '.join([p for p in parts if p]).strip()
        if text:
            return text
    parts = [
        getattr(employee, 'first_name_ar', None),
        getattr(employee, 'middle_name_ar', None),
        getattr(employee, 'last_name_ar', None),
    ]
    text = ' '.join([p for p in parts if p]).strip()
    return text or str(employee)


def _obj_name(obj, lang='ar'):
    if not obj:
        return ''
    if lang == 'en':
        return (
            getattr(obj, 'name_en', None)
            or getattr(obj, 'name', None)
            or getattr(obj, 'name_ar', None)
            or str(obj)
        )
    return (
        getattr(obj, 'name_ar', None)
        or getattr(obj, 'name', None)
        or getattr(obj, 'name_en', None)
        or str(obj)
    )


def get_company_working_days(company, year, month):
    work_days_map = {
        0: True, 1: True, 2: True, 3: True,
        4: False, 5: True, 6: True,
    }
    try:
        from .company_policy_models import CompanyWorkPolicy
        policy = CompanyWorkPolicy.objects.filter(company=company).first()
        if policy:
            work_days_map = {
                0: policy.work_monday,
                1: policy.work_tuesday,
                2: policy.work_wednesday,
                3: policy.work_thursday,
                4: policy.work_friday,
                5: policy.work_saturday,
                6: policy.work_sunday,
            }
    except Exception:
        pass

    first_day, last_day = _period_bounds(year, month)
    today = date.today()
    upper_bound = min(last_day, today)

    working_dates = []
    current = first_day
    while current <= upper_bound:
        if work_days_map.get(current.weekday(), True):
            working_dates.append(current)
        current += timedelta(days=1)
    return working_dates


def get_mission_dates(employee, year, month):
    mission_dates = set()
    first_day, last_day = _period_bounds(year, month)

    try:
        from .models import DailyAssignment
        for a in DailyAssignment._base_manager.filter(
            employee=employee,
            date__gte=first_day,
            date__lte=last_day,
            day_type='mission_day',
        ):
            mission_dates.add(a.date)
    except Exception:
        pass

    try:
        try:
            from .missions_models import MissionAssignment
        except Exception:
            from .models import MissionAssignment
        for m in MissionAssignment._base_manager.filter(
            employee=employee,
            status__in=['accepted', 'in_progress', 'completed'],
        ):
            if getattr(m, 'mission', None) and getattr(m.mission, 'start_date', None):
                d = m.mission.start_date
                if isinstance(d, date) and first_day <= d <= last_day:
                    mission_dates.add(d)
    except Exception:
        pass

    return mission_dates


def get_leave_dates(employee, year, month):
    leave_dates = set()
    first_day, last_day = _period_bounds(year, month)

    try:
        from leaves.models import LeaveRequest
        for lv in LeaveRequest._base_manager.filter(
            employee=employee,
            status='approved',
            start_date__lte=last_day,
            end_date__gte=first_day,
        ):
            current = max(lv.start_date, first_day)
            end = min(lv.end_date, last_day)
            while current <= end:
                leave_dates.add(current)
                current += timedelta(days=1)
    except Exception:
        pass

    return leave_dates


def _get_allowances(employee, first_day, last_day, lang='ar'):
    total = 0.0
    items = []
    try:
        from .company_policy_models import PayrollAllowance
        qs = PayrollAllowance.objects.filter(
            employee=employee,
            is_active=True,
            start_date__lte=last_day,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

        for item in qs:
            amount = _safe_float(item.amount)
            total += amount
            items.append({
                'type': item.allowance_type,
                'name_ar': item.name_ar,
                'name_en': item.name_en or item.name_ar,
                'name': item.name_en if lang == 'en' and item.name_en else item.name_ar,
                'amount': round(amount, 2),
                'is_monthly': bool(item.is_monthly),
            })
    except Exception:
        pass
    return round(total, 2), items


def _get_monthly_deductions(employee, year, month, lang='ar'):
    insurance_total = 0.0
    installments_total = 0.0
    penalties_total = 0.0
    extra_total = 0.0
    insurance_items = []
    installment_items = []
    penalty_items = []
    extra_items = []
    legacy_items = []

    first_day, last_day = _period_bounds(year, month)

    try:
        from .company_policy_models import PayrollDeduction
        qs = PayrollDeduction.objects.filter(
            employee=employee,
            is_active=True,
            start_date__lte=last_day,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

        for item in qs:
            amount = _safe_float(item.amount)
            row = {
                'type': item.deduction_type,
                'name_ar': item.name_ar,
                'name_en': item.name_en or item.name_ar,
                'name': item.name_en if lang == 'en' and item.name_en else item.name_ar,
                'amount': round(amount, 2),
                'notes': item.notes or '',
            }
            if item.deduction_type == 'social_insurance':
                insurance_total += amount
                insurance_items.append(row)
            elif item.deduction_type in ['loan', 'installment']:
                installments_total += amount
                installment_items.append(row)
            elif item.deduction_type == 'penalty':
                penalties_total += amount
                penalty_items.append(row)
            else:
                extra_total += amount
                extra_items.append(row)
    except Exception:
        pass

    try:
        from employees.models import Deduction
        for item in Deduction.objects.filter(employee=employee, year=year, month=month):
            amount = _safe_float(item.amount)
            dtype = getattr(item, 'deduction_type', '') or ''
            dtype_lower = dtype.strip().lower()
            row = {
                'type': dtype or 'manual',
                'name_ar': getattr(item, 'reason', '') or dtype or 'خصم يدوي',
                'name_en': getattr(item, 'reason', '') or dtype or 'Manual deduction',
                'name': getattr(item, 'reason', '') or dtype or 'Manual',
                'amount': round(amount, 2),
                'notes': getattr(item, 'notes', '') or '',
                'source': 'legacy',
            }
            legacy_items.append(row)

            if any(x in dtype_lower for x in ['insurance', 'تأمين']):
                insurance_total += amount
                insurance_items.append(row)
            elif any(x in dtype_lower for x in ['loan', 'installment', 'سلفة', 'قسط']):
                installments_total += amount
                installment_items.append(row)
            elif any(x in dtype_lower for x in ['penalty', 'جزاء']):
                penalties_total += amount
                penalty_items.append(row)
            else:
                extra_total += amount
                extra_items.append(row)
    except Exception:
        pass

    return {
        'insurance_total': round(insurance_total, 2),
        'installments_total': round(installments_total, 2),
        'penalties_total': round(penalties_total, 2),
        'extra_total': round(extra_total, 2),
        'insurance_items': insurance_items,
        'installment_items': installment_items,
        'penalty_items': penalty_items,
        'extra_items': extra_items,
        'legacy_items': legacy_items,
    }


def _get_bonuses(employee, year, month, lang='ar'):
    total = 0.0
    items = []
    try:
        from .payroll_pro_models import PayrollBonus
        for item in PayrollBonus.objects.filter(employee=employee, year=year, month=month):
            amount = _safe_float(item.amount)
            total += amount
            items.append({
                'name_ar': item.name_ar,
                'name_en': item.name_en or item.name_ar,
                'name': item.name_en if lang == 'en' and item.name_en else item.name_ar,
                'amount': round(amount, 2),
                'reason': item.reason or '',
            })
    except Exception:
        pass
    return round(total, 2), items


def _get_penalties(employee, year, month, lang='ar'):
    total = 0.0
    items = []
    try:
        from .payroll_pro_models import PayrollPenalty
        for item in PayrollPenalty.objects.filter(employee=employee, year=year, month=month):
            amount = _safe_float(item.amount)
            total += amount
            items.append({
                'name_ar': item.name_ar,
                'name_en': item.name_en or item.name_ar,
                'name': item.name_en if lang == 'en' and item.name_en else item.name_ar,
                'amount': round(amount, 2),
                'reason': item.reason or '',
            })
    except Exception:
        pass
    return round(total, 2), items


def _get_installments(employee, year, month):
    total = 0.0
    items = []
    try:
        from .payroll_pro_models import PayrollInstallment
        for item in PayrollInstallment.objects.filter(employee=employee, status='active'):
            if (item.start_year < year) or (item.start_year == year and item.start_month <= month):
                remaining = _safe_float(item.remaining_amount())
                if remaining <= 0:
                    continue
                amount = min(_safe_float(item.monthly_amount), remaining)
                total += amount
                items.append({
                    'description': item.description,
                    'monthly_amount': round(amount, 2),
                    'remaining_amount': round(remaining, 2),
                })
    except Exception:
        pass
    return round(total, 2), items



def _get_active_policy(company, target_date, department=None, branch=None):
    """
    يجيب السياسة الفعالة للشركة/الفرع/القسم في تاريخ معين
    الأولوية: قسم > فرع > شركة
    """
    try:
        from attendance.models import AttendancePolicy, AttendancePolicyAssignment
        from django.db.models import Q

        date_filter = Q(policy__effective_from__lte=target_date) & (
            Q(policy__effective_to__isnull=True) | Q(policy__effective_to__gte=target_date)
        )
        status_filter = Q(policy__status='active')
        company_filter = Q(policy__company=company)

        # قسم أولاً
        if department:
            dept_assignment = AttendancePolicyAssignment.objects.filter(
                date_filter & status_filter & company_filter,
                assignment_type='department',
                department=department
            ).select_related('policy').order_by('priority').first()
            if dept_assignment:
                return dept_assignment.policy

        # فرع تانياً
        if branch:
            branch_assignment = AttendancePolicyAssignment.objects.filter(
                date_filter & status_filter & company_filter,
                assignment_type='branch',
                branch=branch
            ).select_related('policy').order_by('priority').first()
            if branch_assignment:
                return branch_assignment.policy

        # شركة أخيراً
        company_assignment = AttendancePolicyAssignment.objects.filter(
            date_filter & status_filter & company_filter,
            assignment_type='company'
        ).select_related('policy').order_by('priority').first()
        if company_assignment:
            return company_assignment.policy

    except Exception:
        pass
    return None


def _apply_late_rule(policy, late_minutes, daily_salary):
    """يطبق قاعدة الخصم على دقائق التأخير"""
    if not policy or late_minutes <= 0:
        return 0.0
    try:
        from attendance.models import LateRule
        rules = LateRule.objects.filter(
            policy=policy,
            from_minutes__lte=late_minutes,
            to_minutes__gte=late_minutes
        ).order_by('display_order').first()

        if not rules:
            rules = LateRule.objects.filter(
                policy=policy,
                from_minutes__lte=late_minutes
            ).order_by('-from_minutes').first()

        if not rules:
            return 0.0

        if rules.deduction_type == 'none':
            return 0.0
        elif rules.deduction_type == 'day_fraction':
            return round(daily_salary * float(rules.deduction_value), 2)
        elif rules.deduction_type == 'fixed_amount':
            return round(float(rules.deduction_value), 2)
        elif rules.deduction_type == 'per_minute':
            return round(late_minutes * float(rules.deduction_value), 2)
    except Exception:
        pass
    return 0.0


def _apply_absence_rule(policy, absent_days, daily_salary):
    """يطبق قاعدة الخصم على أيام الغياب"""
    if not policy or absent_days <= 0:
        return 0.0
    try:
        from attendance.models import AbsenceRule
        rule = AbsenceRule.objects.filter(
            policy=policy,
            absence_type='unexcused'
        ).order_by('display_order').first()

        if not rule:
            return round(absent_days * daily_salary, 2)

        if rule.deduction_type == 'day_fraction':
            return round(absent_days * daily_salary * float(rule.deduction_value), 2)
        elif rule.deduction_type == 'fixed_amount':
            return round(absent_days * float(rule.deduction_value), 2)
    except Exception:
        pass
    return round(absent_days * daily_salary, 2)


def _apply_overtime_rule(policy, overtime_hours, hourly_rate, overtime_type='after_shift'):
    """يطبق قاعدة الأوفر تايم"""
    if not policy or overtime_hours <= 0:
        return 0.0
    try:
        from attendance.models import OvertimeRule
        rule = OvertimeRule.objects.filter(
            policy=policy,
            overtime_type=overtime_type
        ).order_by('display_order').first()

        if not rule:
            rule = OvertimeRule.objects.filter(
                policy=policy,
                overtime_type='after_shift'
            ).order_by('display_order').first()

        if not rule:
            return round(overtime_hours * hourly_rate * 1.5, 2)

        min_hours = float(rule.min_minutes) / 60
        if overtime_hours < min_hours:
            return 0.0

        return round(overtime_hours * hourly_rate * float(rule.multiplier), 2)
    except Exception:
        pass
    return round(overtime_hours * hourly_rate * 1.5, 2)


def _apply_night_allowance(policy, night_shift_days, daily_salary):
    """يحسب بدل الشيفت الليلي"""
    if not policy or night_shift_days <= 0:
        return 0.0
    try:
        from attendance.models import NightShiftRule
        rule = NightShiftRule.objects.filter(policy=policy).first()
        if not rule:
            return 0.0
        if rule.allowance_type == 'fixed_amount':
            return round(night_shift_days * float(rule.amount), 2)
        elif rule.allowance_type == 'percentage':
            return round(night_shift_days * daily_salary * float(rule.percentage) / 100, 2)
    except Exception:
        pass
    return 0.0


def _apply_weekend_allowance(policy, weekend_work_days, daily_salary):
    """يحسب بدل العمل في يوم الراحة"""
    if not policy or weekend_work_days <= 0:
        return 0.0
    try:
        from attendance.models import WeekendWorkRule
        rule = WeekendWorkRule.objects.filter(policy=policy).first()
        if not rule:
            return round(weekend_work_days * daily_salary * 2, 2)
        if rule.compensation_type == 'overtime_multiplier':
            return round(weekend_work_days * daily_salary * float(rule.multiplier), 2)
        elif rule.compensation_type == 'fixed_amount':
            return round(weekend_work_days * float(rule.amount or 0), 2)
    except Exception:
        pass
    return round(weekend_work_days * daily_salary * 2, 2)

def calculate_effective_payroll(employee, year, month, settings=None, lang='ar'):
    """
    الحساب الكامل للراتب:
    Basic + Allowances + Overtime + Bonuses
    - Late - Absence - Insurance - Installments - Penalties - Extra
    = Net Salary
    """
    if settings is None:
        settings = {}

    late_per_min = _safe_float(settings.get('late_deduction_per_minute', 1.0))
    absence_per_day = _safe_float(settings.get('absence_deduction_per_day', 200.0))
    overtime_per_hour = _safe_float(settings.get('overtime_rate_per_hour', 50.0))
    insurance_mode = settings.get('insurance_mode', 'none')
    insurance_fixed_amount = _safe_float(settings.get('insurance_fixed_amount', 0))
    insurance_percent = _safe_float(settings.get('insurance_percent', 0))

    first_day, last_day = _period_bounds(year, month)
    company = getattr(employee, 'company', None)
    department = getattr(employee, 'department', None)
    branch = getattr(employee, 'branch', None)

    # جيب السياسة الفعالة
    active_policy = _get_active_policy(company, first_day, department=department, branch=branch)

    working_dates = get_company_working_days(company, year, month)
    mission_dates = get_mission_dates(employee, year, month)
    leave_dates = get_leave_dates(employee, year, month)

    attendances = list(
        Attendance._base_manager.filter(
            employee=employee,
            date__gte=first_day,
            date__lte=last_day,
        ).order_by('date')
    )
    attendance_by_date = {a.date: a for a in attendances}
    attended_dates = {
        a.date for a in attendances
        if getattr(a, 'check_in_time', None) is not None
    }

    present_days = 0
    late_days = 0
    absent_days = 0
    on_leave_days = 0
    mission_days = 0
    total_late_minutes = 0
    total_work_hours = 0.0
    total_overtime_hours = 0.0
    daily_details = []

    night_shift_days = 0
    weekend_work_days = 0

    for d in working_dates:
        att = attendance_by_date.get(d)
        day_shift = _get_shift_for_date(employee, d)

        if d in leave_dates:
            on_leave_days += 1
            daily_details.append({
                'date': d.isoformat(), 'status': 'on_leave',
                'effective_status': 'on_leave', 'check_in': None,
                'check_out': None, 'work_hours': 0,
                'late_minutes': 0, 'overtime_hours': 0,
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': False, 'is_weekend_work': False,
            })
            continue

        if d in mission_dates:
            mission_days += 1
            work_h = _safe_float(att.work_hours if att else 0)
            ot_h = _calc_overtime_hours(day_shift, att)
            total_work_hours += work_h
            total_overtime_hours += ot_h
            is_night = _is_night_shift(day_shift)
            if is_night:
                night_shift_days += 1
            daily_details.append({
                'date': d.isoformat(), 'status': 'mission_day',
                'effective_status': 'present',
                'check_in': att.check_in_time.strftime('%H:%M') if att and att.check_in_time else None,
                'check_out': att.check_out_time.strftime('%H:%M') if att and att.check_out_time else None,
                'work_hours': round(work_h, 2),
                'late_minutes': 0, 'overtime_hours': round(ot_h, 2),
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': is_night, 'is_weekend_work': False,
            })
            continue

        if d in attended_dates and att:
            work_h = _safe_float(att.work_hours)
            ot_h = _calc_overtime_hours(day_shift, att)
            late_min = _calc_late_minutes(day_shift, att)
            is_night = _is_night_shift(day_shift)
            is_weekend = _is_weekend_work(day_shift, d)

            total_work_hours += work_h
            total_overtime_hours += ot_h

            if is_night:
                night_shift_days += 1
            if is_weekend:
                weekend_work_days += 1

            if late_min > 0:
                late_days += 1
                total_late_minutes += late_min
                eff_status = 'late'
            else:
                present_days += 1
                eff_status = 'present'

            daily_details.append({
                'date': d.isoformat(),
                'status': getattr(att, 'status', 'present'),
                'effective_status': eff_status,
                'check_in': att.check_in_time.strftime('%H:%M') if att.check_in_time else None,
                'check_out': att.check_out_time.strftime('%H:%M') if att.check_out_time else None,
                'work_hours': round(work_h, 2),
                'late_minutes': late_min,
                'overtime_hours': round(ot_h, 2),
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': is_night,
                'is_weekend_work': is_weekend,
            })
            continue

        absent_days += 1
        daily_details.append({
            'date': d.isoformat(), 'status': 'absent',
            'effective_status': 'absent', 'check_in': None,
            'check_out': None, 'work_hours': 0,
            'late_minutes': 0, 'overtime_hours': 0,
            'shift_name': day_shift.name if day_shift else '',
            'is_night_shift': False, 'is_weekend_work': False,
        })

    basic_salary = _safe_float(getattr(employee, 'basic_salary', 0))
    currency = getattr(employee, 'currency', None) or 'EGP'
    has_insurance = bool(getattr(employee, 'has_insurance', False))

    # حساب اليومي والساعي للموظف
    working_days_count = max(len(working_dates), 1)
    basic_salary_temp = _safe_float(getattr(employee, 'basic_salary', 0))
    daily_salary = round(basic_salary_temp / working_days_count, 4)
    hourly_rate = round(daily_salary / 8, 4)

    # تطبيق السياسة أو الـ settings الافتراضية
    if active_policy:
        late_deduction = _apply_late_rule(active_policy, total_late_minutes, daily_salary)
        absence_deduction = _apply_absence_rule(active_policy, absent_days, daily_salary)
        overtime_bonus = _apply_overtime_rule(active_policy, total_overtime_hours, hourly_rate)
        night_allowance = _apply_night_allowance(active_policy, night_shift_days, daily_salary)
        weekend_allowance = _apply_weekend_allowance(active_policy, weekend_work_days, daily_salary)
    else:
        late_deduction = round(total_late_minutes * late_per_min, 2)
        absence_deduction = round(absent_days * absence_per_day, 2)
        overtime_bonus = round(total_overtime_hours * overtime_per_hour, 2)
        night_allowance = 0.0
        weekend_allowance = 0.0

    allowances_total, allowance_items = _get_allowances(employee, first_day, last_day, lang=lang)
    deductions = _get_monthly_deductions(employee, year, month, lang=lang)
    bonuses_total, bonus_items = _get_bonuses(employee, year, month, lang=lang)
    penalties_total_new, penalty_items_new = _get_penalties(employee, year, month, lang=lang)
    installments_total_new, installment_items_new = _get_installments(employee, year, month)

    insurance_deduction = deductions['insurance_total']
    if has_insurance:
        if insurance_mode == 'fixed':
            insurance_deduction += insurance_fixed_amount
        elif insurance_mode == 'percent':
            insurance_deduction += round((basic_salary * insurance_percent) / 100.0, 2)
    insurance_deduction = round(insurance_deduction, 2)

    installments_total = round(deductions['installments_total'] + installments_total_new, 2)
    penalties_total = round(deductions['penalties_total'] + penalties_total_new, 2)
    extra_deductions_total = deductions['extra_total']

    gross_salary = round(basic_salary + allowances_total + overtime_bonus + bonuses_total + night_allowance + weekend_allowance, 2)

    total_deductions = round(
        late_deduction
        + absence_deduction
        + insurance_deduction
        + installments_total
        + penalties_total
        + extra_deductions_total,
        2
    )

    net_salary = round(gross_salary - total_deductions, 2)
    attended_days = present_days + late_days + mission_days

    return {
        'employee_id': employee.id,
        'employee_code': getattr(employee, 'employee_code', '') or '',
        'employee_name': _employee_name(employee, lang=lang),
        'company_name': str(company) if company else '',
        'branch_name': _obj_name(getattr(employee, 'branch', None), lang=lang),
        'department_name': _obj_name(getattr(employee, 'department', None), lang=lang),
        'job_title_name': _obj_name(getattr(employee, 'job_title', None), lang=lang),
        'currency': currency,

        'basic_salary': round(basic_salary, 2),
        'allowances_total': round(allowances_total, 2),
        'overtime_bonus': round(overtime_bonus, 2),
        'bonuses_total': round(bonuses_total, 2),
        'gross_salary': round(gross_salary, 2),

        'night_allowance': round(night_allowance, 2),
        'weekend_allowance': round(weekend_allowance, 2),
        'policy_name': active_policy.name if active_policy else None,
        'late_deduction': round(late_deduction, 2),
        'absence_deduction': round(absence_deduction, 2),
        'insurance_deduction': round(insurance_deduction, 2),
        'installments_total': round(installments_total, 2),
        'penalties_total': round(penalties_total, 2),
        'extra_deductions_total': round(extra_deductions_total, 2),
        'total_deductions': round(total_deductions, 2),
        'net_salary': round(net_salary, 2),

        'total_working_days': len(working_dates),
        'attended_days': attended_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'mission_days': mission_days,
        'on_leave_days': on_leave_days,
        'total_late_minutes': total_late_minutes,
        'total_work_hours': round(total_work_hours, 2),
        'overtime_hours': round(total_overtime_hours, 2),
        'night_shift_days': night_shift_days,
        'weekend_work_days': weekend_work_days,

        'allowance_items': allowance_items,
        'bonus_items': bonus_items,
        'insurance_items': deductions['insurance_items'],
        'installment_items': deductions['installment_items'] + installment_items_new,
        'penalty_items': deductions['penalty_items'] + penalty_items_new,
        'extra_deduction_items': deductions['extra_items'],
        'legacy_deduction_items': deductions['legacy_items'],

        'daily_details': daily_details,
    }
