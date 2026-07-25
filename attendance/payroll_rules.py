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

    # الشيفت المرن: مفيش تأخير بالوقت — المهم الساعات (بتتحسب في FlexDayAdjustment)
    shift_mode = getattr(shift, 'shift_mode', '') or ''
    if shift_mode in ('flex_fixed', 'flex_split'):
        return 0

    try:
        from django.utils import timezone
        check_in_local = timezone.localtime(att.check_in_time)
        shift_start = datetime.combine(check_in_local.date(), shift.start_time)

        # الشيفت الليلي: لو الحضور بعد نص الليل والشيفت بيبدأ قبله → الشيفت بدأ امبارح
        if getattr(shift, 'crosses_midnight', False):
            if check_in_local.time() < shift.start_time:
                shift_start -= timedelta(days=1)

        grace = int(shift.grace_period or 0)
        deadline = shift_start + timedelta(minutes=grace)
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

    # الشيفت المرن: الأوفر تايم بيجي من FlexDayAdjustment المعتمد بس
    shift_mode = getattr(shift, 'shift_mode', '') or ''
    if shift_mode in ('flex_fixed', 'flex_split'):
        try:
            from attendance.models import FlexDayAdjustment
            approved = FlexDayAdjustment._base_manager.filter(
                employee=att.employee,
                date=att.date,
                adjustment_type='overtime',
                status='approved',
            ).order_by('-reviewed_at').first()
            if approved:
                return float(approved.delta_hours or 0)
            return 0.0
        except Exception:
            return 0.0

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




def _calc_split_shift_metrics(shift, att, sessions, target_date):
    """
    يحسب التأخير والعجز للشيفت المقسم (split_fixed)
    بيطابق كل session مع فترتها في الشيفت
    """
    try:
        from django.utils import timezone
        from datetime import datetime, timedelta

        # جيب فترات الشيفت
        periods = shift.get_shift_periods(target_date) if hasattr(shift, 'get_shift_periods') else []
        if not periods:
            return {'late_minutes': 0, 'shortage_minutes': 0, 'is_fully_absent': False, 'worked_minutes': 0}

        total_late = 0
        total_shortage = 0
        total_worked = 0
        periods_attended = 0

        for idx, period in enumerate(periods):
            # F2: الدالة بترجع 'start' و 'end' كـ datetime aware
            period_start_dt_aware = period.get('start')
            period_end_dt_aware = period.get('end')
            if not period_start_dt_aware or not period_end_dt_aware:
                continue

            # حول لـ naive datetime بتوقيت محلي للمقارنة
            period_start_dt = timezone.localtime(period_start_dt_aware).replace(tzinfo=None)
            period_end_dt = timezone.localtime(period_end_dt_aware).replace(tzinfo=None)
            period_minutes = int((period_end_dt - period_start_dt).total_seconds() / 60)

            # دور على الـ session المقابلة للفترة دي
            matched_session = None
            for s in sessions:
                s_in = timezone.localtime(s.check_in_time)
                s_in_naive = s_in.replace(tzinfo=None)
                # الـ session بتتطابق لو بداتها قريبة من بداية الفترة (±60 دقيقة)
                diff = abs((s_in_naive - period_start_dt).total_seconds() / 60)
                if diff <= 60:
                    matched_session = s
                    break

            if matched_session:
                periods_attended += 1
                # حساب التأخير للفترة دي
                grace = int(shift.grace_period or 0)
                deadline = period_start_dt + timedelta(minutes=grace)
                s_in_local = timezone.localtime(matched_session.check_in_time).replace(tzinfo=None)
                if s_in_local > deadline:
                    total_late += int((s_in_local - deadline).total_seconds() / 60)
                # حساب الدقائق اللي اشتغلها
                if matched_session.check_out_time:
                    s_out_local = timezone.localtime(matched_session.check_out_time).replace(tzinfo=None)
                    worked = int((s_out_local - s_in_local).total_seconds() / 60)
                    total_worked += max(worked, 0)
                else:
                    total_worked += matched_session.worked_minutes or 0
            else:
                # مجاش الفترة دي → عجز بساعاتها
                total_shortage += period_minutes

        is_fully_absent = periods_attended == 0

        return {
            'late_minutes': total_late,
            'shortage_minutes': total_shortage,
            'is_fully_absent': is_fully_absent,
            'worked_minutes': total_worked,
        }
    except Exception:
        return {'late_minutes': 0, 'shortage_minutes': 0, 'is_fully_absent': False, 'worked_minutes': 0}



def _is_night_shift(shift):
    """هل الشيفت ليلي؟"""
    if not shift:
        return False
    return bool(getattr(shift, 'crosses_midnight', False)) or getattr(shift, 'shift_type', '') == 'night'


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


def get_payroll_period_bounds(company, year, month):
    """
    يحسب فترة المرتب الفعلية حسب إعدادات الشركة.
    year/month = شهر القفل دايماً.

    calendar_month: من 1 الشهر لآخره
    cutoff_day=20:  من 21 الشهر اللي فات لـ 20 الشهر ده
    """
    try:
        cycle_type = getattr(company, 'payroll_cycle_type', 'calendar_month') or 'calendar_month'
        cutoff_day = int(getattr(company, 'payroll_cutoff_day', 1) or 1)
        cutoff_day = max(1, min(cutoff_day, 28))  # نحمي من أيام غير موجودة

        if cycle_type == 'cutoff_day':
            # نهاية الفترة = cutoff_day من شهر القفل (year/month)
            last_day = date(year, month, cutoff_day)

            # بداية الفترة = cutoff_day + 1 من الشهر اللي فاته
            if month == 1:
                prev_year, prev_month = year - 1, 12
            else:
                prev_year, prev_month = year, month - 1

            first_day = date(prev_year, prev_month, cutoff_day + 1)
            return first_day, last_day

    except Exception:
        pass

    # fallback: شهر ميلادي عادي
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

    company_obj = company if hasattr(company, 'payroll_cycle_type') else None
    if company_obj:
        first_day, last_day = get_payroll_period_bounds(company_obj, year, month)
    else:
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
    _company = getattr(employee, 'company', None)
    if _company and hasattr(_company, 'payroll_cycle_type'):
        first_day, last_day = get_payroll_period_bounds(_company, year, month)
    else:
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
    half_day_dates = {}  # date -> {'type': morning/afternoon, 'hours': float}
    _company = getattr(employee, 'company', None)
    if _company and hasattr(_company, 'payroll_cycle_type'):
        first_day, last_day = get_payroll_period_bounds(_company, year, month)
    else:
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
            _half = getattr(lv, 'half_day_type', '') or ''
            _hours = float(getattr(lv, 'leave_hours', 0) or 0)
            while current <= end:
                if _half and lv.days_count <= 0.5:
                    # نص يوم: نسجله لكن ما نضيفوش لـ leave_dates
                    half_day_dates[current] = {
                        'type': _half,
                        'hours': _hours if _hours > 0 else 4.0,
                    }
                else:
                    leave_dates.add(current)
                current += timedelta(days=1)
    except Exception:
        pass

    # استثناء أيام الاستدعاء المعتمدة من أيام الإجازة
    try:
        from leaves.models import LeaveRecallRequest
        recalled_dates = set(
            LeaveRecallRequest._base_manager.filter(
                employee=employee,
                status='approved',
                recall_date__gte=first_day,
                recall_date__lte=last_day,
            ).values_list('recall_date', flat=True)
        )
        leave_dates -= recalled_dates
    except Exception:
        pass

    return leave_dates, half_day_dates



def get_approved_permission_minutes(employee, first_day, last_day):
    """
    يجيب الدقايق المعتمدة من الطلبات (EmployeeRequest) في فترة المرتب
    بيرجع:
        late_approved_minutes: دقايق إذن التأخير المعتمدة
        early_approved_minutes: دقايق إذن الانصراف المبكر المعتمدة
    """
    late_minutes = 0
    early_minutes = 0
    try:
        from requests_app.models import EmployeeRequest
        approved_requests = EmployeeRequest._base_manager.filter(
            employee=employee,
            status='approved',
            start_date__gte=first_day,
            start_date__lte=last_day,
            request_type__permission_kind__in=('late_arrival', 'early_leave'),
        ).select_related('request_type')

        for req in approved_requests:
            kind = getattr(req.request_type, 'permission_kind', '') or ''
            hours = float(req.duration_hours or 0)
            minutes = int(hours * 60)
            if kind == 'late_arrival':
                late_minutes += minutes
            elif kind == 'early_leave':
                early_minutes += minutes
    except Exception:
        pass
    return late_minutes, early_minutes

def get_unpaid_leave_dates(employee, year, month):
    unpaid_dates = set()
    _company = getattr(employee, 'company', None)
    if _company and hasattr(_company, 'payroll_cycle_type'):
        first_day, last_day = get_payroll_period_bounds(_company, year, month)
    else:
        first_day, last_day = _period_bounds(year, month)

    try:
        from leaves.models import LeaveRequest
        for lv in LeaveRequest._base_manager.filter(
            employee=employee,
            status='approved',
            leave_type__is_paid=False,
            start_date__lte=last_day,
            end_date__gte=first_day,
        ).select_related('leave_type'):
            current = max(lv.start_date, first_day)
            end = min(lv.end_date, last_day)
            while current <= end:
                unpaid_dates.add(current)
                current += timedelta(days=1)
    except Exception:
        pass

    try:
        from leaves.models import LeaveRecallRequest
        recalled_dates = set(
            LeaveRecallRequest._base_manager.filter(
                employee=employee,
                status='approved',
                recall_date__gte=first_day,
                recall_date__lte=last_day,
            ).values_list('recall_date', flat=True)
        )
        unpaid_dates -= recalled_dates
    except Exception:
        pass

    return unpaid_dates


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

    _emp_company = getattr(employee, 'company', None)
    if _emp_company and hasattr(_emp_company, 'payroll_cycle_type'):
        first_day, last_day = get_payroll_period_bounds(_emp_company, year, month)
    else:
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





def _upsert_flex_adjustment(employee, att, day_shift, actual_hours):
    """
    ينشئ أو يحدث FlexDayAdjustment لليوم ده.
    بيشتغل بس لو الشيفت مرن (flex_fixed / flex_split).
    القواعد:
      - لو الفرق = 0 → ماينشئش حاجة
      - لو فيه سجل Pending → يحدثه
      - لو فيه سجل Approved/Rejected → ينشئ سجل Pending جديد
    """
    try:
        if not day_shift or not employee or not att:
            return

        shift_mode = getattr(day_shift, 'shift_mode', '') or ''
        if shift_mode not in ('flex_fixed', 'flex_split'):
            return

        required = float(getattr(day_shift, 'required_daily_hours', 8) or 8)
        actual = float(actual_hours or 0)
        delta = round(actual - required, 2)

        if abs(delta) < 0.01:
            return

        adj_type = 'overtime' if delta > 0 else 'shortage'
        target_date = getattr(att, 'date', None)
        if not target_date:
            return

        from attendance.models import FlexDayAdjustment
        from django.db.models import Q

        company = getattr(employee, 'company', None)

        existing_pending = FlexDayAdjustment._base_manager.filter(
            employee=employee,
            date=target_date,
            status='pending',
        ).first()

        if existing_pending:
            existing_pending.attendance = att
            existing_pending.shift = day_shift
            existing_pending.required_hours = required
            existing_pending.actual_hours = actual
            existing_pending.delta_hours = delta
            existing_pending.adjustment_type = adj_type
            existing_pending.save()
            return

        closed = FlexDayAdjustment._base_manager.filter(
            employee=employee,
            date=target_date,
            status__in=('approved', 'rejected'),
        ).exists()

        if not closed:
            FlexDayAdjustment._base_manager.create(
                company=company,
                employee=employee,
                attendance=att,
                shift=day_shift,
                date=target_date,
                required_hours=required,
                actual_hours=actual,
                delta_hours=delta,
                adjustment_type=adj_type,
                status='pending',
            )
        else:
            FlexDayAdjustment._base_manager.create(
                company=company,
                employee=employee,
                attendance=att,
                shift=day_shift,
                date=target_date,
                required_hours=required,
                actual_hours=actual,
                delta_hours=delta,
                adjustment_type=adj_type,
                status='pending',
            )

    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning(f'_upsert_flex_adjustment error: {_e}')


def _apply_permission_balance(employee, late_minutes, reference_date, policy):
    """
    لو الموظف عنده رصيد أذونات → نحول التأخير لإذن تلقائي
    ونرجع الدقايق اللي اتحولت + الدقايق اللي فضلت (لازم تتحسب خصم)
    """
    if not policy or not policy.permission_enabled:
        return 0, late_minutes  # مفيش سياسة → كل التأخير خصم

    if late_minutes <= 0:
        return 0, 0

    from attendance.models import PermissionLedger
    from datetime import date

    today = reference_date or date.today()

    # نحدد فترة الشهر حسب نوع الدورة
    emp_company = getattr(employee, 'company', None)

    if policy.permission_reset_cycle == 'payroll' and emp_company and hasattr(emp_company, 'payroll_cycle_type'):
        # نستخدم نفس دورة المرتب
        period_start, period_end = get_payroll_period_bounds(emp_company, today.year, today.month)
    else:
        # دورة شهرية ميلادية عادية
        period_start = today.replace(day=1)
        if today.month == 12:
            period_end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            period_end = today.replace(month=today.month + 1, day=1)

    # نجيب الحركات في الفترة دي
    entries = PermissionLedger._base_manager.filter(
        employee=employee,
        reference_date__gte=period_start,
        reference_date__lt=period_end,
    )

    total_minutes_used = sum(e.minutes_used for e in entries)
    total_count_used = sum(e.count_used for e in entries)

    monthly_minutes = int(float(policy.permission_monthly_hours) * 60)
    monthly_count = policy.permission_monthly_count

    remaining_minutes = max(0, monthly_minutes - total_minutes_used)
    remaining_count = max(0, monthly_count - total_count_used)

    if remaining_minutes <= 0 or remaining_count <= 0:
        return 0, late_minutes  # الرصيد خلص → كل التأخير خصم

    # نحسب كام دقيقة هنحولها لإذن
    max_per_request = int(float(policy.permission_max_hours_per_request) * 60)

    # لو الكسر بمرة كاملة → نحسب المرة كاملة
    if policy.permission_fraction_as_full:
        minutes_to_convert = min(max_per_request, remaining_minutes)
        count_to_use = 1
    else:
        minutes_to_convert = min(late_minutes, max_per_request, remaining_minutes)
        count_to_use = 1

    # مش هنحول أكتر من التأخير نفسه
    minutes_to_convert = min(minutes_to_convert, late_minutes)

    if minutes_to_convert <= 0 or count_to_use > remaining_count:
        return 0, late_minutes

    # نسجل الحركة في الـ Ledger
    try:
        PermissionLedger._base_manager.create(
            employee=employee,
            company=employee.company,
            entry_type='auto_late',
            minutes_used=minutes_to_convert,
            count_used=count_to_use,
            reference_date=reference_date,
            notes=f'خصم تلقائي من رصيد الأذونات بسبب تأخير {late_minutes} دقيقة',
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'PermissionLedger create error: {e}')
        return 0, late_minutes

    remaining_late = max(0, late_minutes - minutes_to_convert)
    return minutes_to_convert, remaining_late

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

    company = getattr(employee, 'company', None)
    department = getattr(employee, 'department', None)
    branch = getattr(employee, 'branch', None)

    # Phase 1: فترة المرتب حسب إعدادات الشركة
    if company and hasattr(company, 'payroll_cycle_type'):
        first_day, last_day = get_payroll_period_bounds(company, year, month)
    else:
        first_day, last_day = _period_bounds(year, month)

    # م-6: السياسة بتتجاب لكل يوم مش مرة واحدة للشهر كله
    # active_policy = للتوافق مع القديم (بتاخد السياسة السائدة في الشهر)
    active_policy = _get_active_policy(company, first_day, department=department, branch=branch)
    _policy_cache = {}  # cache عشان ما نعملش query لكل يوم لوحده

    def _get_day_policy(d):
        if d not in _policy_cache:
            _policy_cache[d] = _get_active_policy(company, d, department=department, branch=branch)
        return _policy_cache[d]

    working_dates = get_company_working_days(company, year, month)
    mission_dates = get_mission_dates(employee, year, month)
    leave_dates, half_day_dates = get_leave_dates(employee, year, month)
    unpaid_leave_dates = get_unpaid_leave_dates(employee, year, month)

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

    # Hybrid: جلب الملخصات اليومية المتاحة (لو موجودة تسرّع الحساب)
    try:
        from attendance.models import DailyAttendanceSummary
        from datetime import date as _date_cls
        _today = _date_cls.today()
        _summaries = {
            s.date: s
            for s in DailyAttendanceSummary._base_manager.filter(
                employee=employee,
                date__gte=first_day,
                date__lte=last_day,
            ).select_related('shift', 'policy')
            if s.date < _today  # نتجاهل النهارده لأنه ممكن يكون ناقص
        }
    except Exception:
        _summaries = {}

    present_days = 0
    late_days = 0
    absent_days = 0
    on_leave_days = 0
    unpaid_leave_days = 0
    mission_days = 0
    total_late_minutes = 0
    total_early_leave_minutes = 0
    total_work_hours = 0.0
    total_overtime_hours = 0.0
    daily_details = []

    night_shift_days = 0
    weekend_work_days = 0

    # ندمج أيام الشركة مع أي أيام الموظف اشتغلها فعلياً وهي مش أيام عمل للشركة
    all_eval_dates = sorted(list(set(working_dates) | attended_dates))
    for d in all_eval_dates:
        att = attendance_by_date.get(d)

        # Hybrid: لو عندنا summary لليوم ده نستخدمها
        _summary = _summaries.get(d)
        if _summary and d not in leave_dates and d not in mission_dates:
            _es = _summary.effective_status or _summary.status
            _day_shift = _summary.shift or _get_shift_for_date(employee, d)

            if _es == 'present':
                present_days += 1
            elif _es == 'late':
                late_days += 1
                _day_pol = _get_day_policy(d)
                _conv, _remaining = _apply_permission_balance(
                    employee, _summary.late_minutes, d, _day_pol
                )
                total_late_minutes += _remaining
            elif _es == 'absent':
                absent_days += 1
            elif _es == 'weekend':
                pass
            elif _es == 'on_leave':
                on_leave_days += 1

            _wh = float(_summary.work_hours or 0)
            _oth = float(_summary.overtime_hours or 0)
            _elm = int(getattr(att, 'early_leave_minutes', 0) or 0)
            total_work_hours += _wh
            total_overtime_hours += _oth
            total_early_leave_minutes += _elm

            if _summary.is_night_shift:
                night_shift_days += 1
            if _summary.is_weekend_work:
                weekend_work_days += 1

            daily_details.append({
                'date': d.isoformat(),
                'status': _summary.status,
                'effective_status': _es,
                'check_in': att.check_in_time.strftime('%H:%M') if att and att.check_in_time else None,
                'check_out': att.check_out_time.strftime('%H:%M') if att and att.check_out_time else None,
                'work_hours': round(_wh, 2),
                'late_minutes': _summary.late_minutes,
                'early_leave_minutes': _elm,
                'overtime_hours': round(_oth, 2),
                'shift_name': _day_shift.name if _day_shift else '',
                'is_night_shift': _summary.is_night_shift,
                'is_weekend_work': _summary.is_weekend_work,
            })
            continue

        # Fallback: الحساب التقليدي لو مفيش summary
        day_shift = _get_shift_for_date(employee, d)

        if d in leave_dates:
            on_leave_days += 1
            if d in unpaid_leave_dates:
                unpaid_leave_days += 1
        elif d in half_day_dates:
            # نص يوم: حاضر نص الوقت فقط
            on_leave_days += 0.5
            _hd = half_day_dates[d]
            _hd_hours = _hd.get('hours', 4.0)
            _hd_daily_deduct = round(_hd_hours / max(float(getattr(att.employee if att else employee, 'required_daily_hours', 8) or 8), 1) * daily_salary, 2)
            absence_deduction += _hd_daily_deduct
            daily_details.append({
                'date': d.isoformat(), 'status': 'on_leave',
                'effective_status': 'on_leave', 'check_in': None,
                'check_out': None, 'work_hours': 0,
                'late_minutes': 0, 'early_leave_minutes': 0, 'overtime_hours': 0,
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': False, 'is_weekend_work': False,
            })
            continue

        if d in mission_dates:
            mission_days += 1
            work_h = _safe_float(att.work_hours if att else 0)
            ot_h = _calc_overtime_hours(day_shift, att)
            elm = int(getattr(att, 'early_leave_minutes', 0) or 0) if att else 0
            total_work_hours += work_h
            total_overtime_hours += ot_h
            total_early_leave_minutes += elm
            is_night = _is_night_shift(day_shift)
            if is_night:
                night_shift_days += 1
            daily_details.append({
                'date': d.isoformat(), 'status': 'mission_day',
                'effective_status': 'present',
                'check_in': att.check_in_time.strftime('%H:%M') if att and att.check_in_time else None,
                'check_out': att.check_out_time.strftime('%H:%M') if att and att.check_out_time else None,
                'work_hours': round(work_h, 2),
                'late_minutes': 0, 'early_leave_minutes': elm, 'overtime_hours': round(ot_h, 2),
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': is_night, 'is_weekend_work': False,
            })
            continue

        if d in attended_dates and att:
            # شيفت مقسم أو متغير له منطق خاص
            shift_mode = getattr(day_shift, 'shift_mode', '') or getattr(day_shift, 'shift_type', '')
            _VARIABLE_MODES = ('split_fixed', 'variable_weekly', 'variable_weekly_flex', 'variable_daily')
            if day_shift and shift_mode in _VARIABLE_MODES:
                from attendance.models import AttendanceSession
                day_sessions = list(AttendanceSession._base_manager.filter(
                    attendance=att
                ).order_by('session_number'))
                split_metrics = _calc_split_shift_metrics(day_shift, att, day_sessions, d)
                if split_metrics['is_fully_absent']:
                    absent_days += 1
                    daily_details.append({
                        'date': d.isoformat(), 'status': 'absent',
                        'effective_status': 'absent', 'check_in': None,
                        'check_out': None, 'work_hours': 0,
                        'late_minutes': 0, 'overtime_hours': 0,
                        'shift_name': day_shift.name if day_shift else '',
                        'is_night_shift': False, 'is_weekend_work': False,
                    })
                    continue
                work_h = round(split_metrics['worked_minutes'] / 60, 2)
                late_min = split_metrics['late_minutes'] + split_metrics['shortage_minutes']
                ot_h = 0.0
            else:
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

            elm = int(getattr(att, 'early_leave_minutes', 0) or 0)
            total_early_leave_minutes += elm

            if late_min > 0:
                late_days += 1
                # نحاول نحول التأخير لإذن لو الموظف عنده رصيد (م-6: سياسة اليوم)
                _day_pol = _get_day_policy(d)
                converted, remaining_late = _apply_permission_balance(
                    employee, late_min, d, _day_pol
                )
                effective_late_min = remaining_late
                total_late_minutes += effective_late_min
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
                'early_leave_minutes': elm,
                'overtime_hours': round(ot_h, 2),
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': is_night,
                'is_weekend_work': is_weekend,
            })
            continue

        if day_shift and not day_shift.is_work_day(d):
            # لو الموظف مجاش في يوم راحته -> مش غياب
            daily_details.append({
                'date': d.isoformat(), 'status': 'weekend',
                'effective_status': 'weekend', 'check_in': None,
                'check_out': None, 'work_hours': 0,
                'late_minutes': 0, 'early_leave_minutes': 0, 'overtime_hours': 0,
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': False, 'is_weekend_work': True,
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
    # اجيب الشيفت الافتراضي للموظف عشان احسب أجر الساعة منه
    _default_shift_for_rate = _get_shift_for_date(employee, first_day)
    _work_hours_for_rate = float(_default_shift_for_rate.work_hours) if _default_shift_for_rate and _default_shift_for_rate.work_hours else 8.0
    hourly_rate = round(daily_salary / _work_hours_for_rate, 4)

    # م-6: نجمع الأرقام لكل سياسة لوحدها ثم نطبق قواعدها
    _policy_totals = {}  # policy_id -> {late, absent, overtime, night, weekend}
    _no_policy_totals = {'late': 0, 'absent': 0, 'overtime': 0.0, 'night': 0, 'weekend': 0}

    for dd in daily_details:
        _d_date = None
        try:
            from datetime import date as _date_cls
            _d_date = _date_cls.fromisoformat(dd['date'])
        except Exception:
            pass

        _dp = _get_day_policy(_d_date) if _d_date else None
        _es = dd.get('effective_status', '')

        if _dp:
            _pid = _dp.id
            if _pid not in _policy_totals:
                _policy_totals[_pid] = {'policy': _dp, 'late': 0, 'absent': 0, 'overtime': 0.0, 'night': 0, 'weekend': 0}
            if _es in ('late',):
                _policy_totals[_pid]['late'] += dd.get('late_minutes', 0)
            if _es == 'absent':
                _policy_totals[_pid]['absent'] += 1
            _policy_totals[_pid]['overtime'] += dd.get('overtime_hours', 0.0)
            if dd.get('is_night_shift'):
                _policy_totals[_pid]['night'] += 1
            if dd.get('is_weekend_work'):
                _policy_totals[_pid]['weekend'] += 1
        else:
            if _es in ('late',):
                _no_policy_totals['late'] += dd.get('late_minutes', 0)
            if _es == 'absent':
                _no_policy_totals['absent'] += 1
            _no_policy_totals['overtime'] += dd.get('overtime_hours', 0.0)
            if dd.get('is_night_shift'):
                _no_policy_totals['night'] += 1
            if dd.get('is_weekend_work'):
                _no_policy_totals['weekend'] += 1

    # نجمع الناتج من كل السياسات
    late_deduction = 0.0
    absence_deduction = 0.0
    overtime_bonus = 0.0
    night_allowance = 0.0
    weekend_allowance = 0.0

    for _pid, _pt in _policy_totals.items():
        _pol = _pt['policy']
        late_deduction += _apply_late_rule(_pol, _pt['late'], daily_salary)
        absence_deduction += _apply_absence_rule(_pol, _pt['absent'], daily_salary)
        overtime_bonus += _apply_overtime_rule(_pol, _pt['overtime'], hourly_rate)
        night_allowance += _apply_night_allowance(_pol, _pt['night'], daily_salary)
        weekend_allowance += _apply_weekend_allowance(_pol, _pt['weekend'], daily_salary)

    # الأيام بدون سياسة -> settings الافتراضية
    if _no_policy_totals['late'] or _no_policy_totals['absent'] or _no_policy_totals['overtime']:
        late_deduction += round(max(0, _no_policy_totals['late'] - _approved_late_min) * late_per_min, 2)
        absence_deduction += round(_no_policy_totals['absent'] * absence_per_day, 2)
        overtime_bonus += round(_no_policy_totals['overtime'] * overtime_per_hour, 2)

    late_deduction = round(late_deduction, 2)
    absence_deduction = round(absence_deduction, 2)
    overtime_bonus = round(overtime_bonus, 2)
    night_allowance = round(night_allowance, 2)
    weekend_allowance = round(weekend_allowance, 2)

    # policy_name: لو فيه أكتر من سياسة نقول "سياسات متعددة"
    _used_policies = list(_policy_totals.values())
    if len(_used_policies) == 0:
        active_policy = None
    elif len(_used_policies) == 1:
        active_policy = _used_policies[0]['policy']
    else:
        active_policy = type('_MultiPolicy', (), {'name': 'سياسات متعددة' if True else 'Multiple Policies'})()

    # [ب] خصم نقص ساعات الشيفت المرن (approved فقط)
    flex_shortage_deduction = 0.0
    try:
        from attendance.models import FlexDayAdjustment
        _shortage_adjs = FlexDayAdjustment._base_manager.filter(
            employee=employee,
            date__gte=first_day,
            date__lte=last_day,
            adjustment_type='shortage',
            status='approved',
        )
        for _adj in _shortage_adjs:
            flex_shortage_deduction += abs(float(_adj.delta_hours or 0)) * hourly_rate
        flex_shortage_deduction = round(flex_shortage_deduction, 2)
    except Exception:
        flex_shortage_deduction = 0.0

    # خصم الانصراف المبكر = بنفس معدل التأخير الحالي
    # خصم الإذن المعتمد من التأخير والانصراف المبكر
    _approved_late_min, _approved_early_min = get_approved_permission_minutes(
        employee, first_day, last_day
    )
    effective_late_minutes = max(0, total_late_minutes - _approved_late_min)
    effective_early_minutes = max(0, total_early_leave_minutes - _approved_early_min)

    early_leave_deduction = round(effective_early_minutes * late_per_min, 2)

    unpaid_leave_deduction = round(unpaid_leave_days * daily_salary, 2)

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
        + extra_deductions_total
        + flex_shortage_deduction
        + early_leave_deduction
        + unpaid_leave_deduction,
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
        'flex_shortage_deduction': round(flex_shortage_deduction, 2),
        'early_leave_deduction': round(early_leave_deduction, 2),
        'unpaid_leave_deduction': round(unpaid_leave_deduction, 2),
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
        'unpaid_leave_days': unpaid_leave_days,
        'total_late_minutes': total_late_minutes,
        'approved_late_minutes': _approved_late_min,
        'approved_early_minutes': _approved_early_min,
        'total_early_leave_minutes': total_early_leave_minutes,
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
