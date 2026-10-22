"""
MotionHR - Payroll Rules Engine
Phase 15: Payroll Pro
Mission-aware + Shift-aware + Policy-aware
+ Allowances / Deductions / Bonuses / Penalties / Installments / Insurance
"""
from datetime import date, timedelta, datetime
from calendar import monthrange
from django.db.models import Q
import logging
logger = logging.getLogger(__name__)
from django.utils import timezone
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
    """يحسب دقائق التأخير بناءً على الشيفت الفعلي وطبيعة الموظف"""
    if not shift or not att or not att.check_in_time:
        return 0

    employee = getattr(att, 'employee', None)
    if employee:
        mode = getattr(employee, 'attendance_mode', 'fixed_shift')
        if mode in ('flexible_hours', 'field_worker'):
            return 0

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
        today = timezone.localtime(att.check_in_time).date()
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

            # لو اليوم ده مش موجود في الشهر اللي فات (يوم 29 في فبراير مثلاً) الفترة تبدأ من أول شهر القفل،
            # وإلا كانت بتقع للشهر الميلادي وأيام آخر الشهر بتتحسب مرتين
            if cutoff_day + 1 > monthrange(prev_year, prev_month)[1]:
                first_day = date(year, month, 1)
            else:
                first_day = date(prev_year, prev_month, cutoff_day + 1)
            return first_day, last_day

    except Exception:
        logger.exception("payroll_rules error in get_payroll_period_bounds")

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
        policy = CompanyWorkPolicy._base_manager.filter(company=company).first()
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
        logger.exception(
        "payroll_rules error in get_company_working_days",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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




def get_official_holiday_treatment(employee, year, month):
    """
    بيرجع dict من التواريخ -> treatment
    مثلاً: {date(2026, 8, 6): 'paid_leave', date(2026, 8, 7): 'work_with_bonus'}
    بيأخذ الـ rule ذات الأولوية الأعلى (رقم أقل) اللي بتنطبق على الموظف
    """
    result = {}
    try:
        from leaves.official_holiday_models import OfficialHoliday, OfficialHolidayRule
        from datetime import timedelta

        company = getattr(employee, 'company', None)
        if not company:
            return result

        if hasattr(company, 'payroll_cycle_type'):
            first_day, last_day = get_payroll_period_bounds(company, year, month)
        else:
            first_day, last_day = _period_bounds(year, month)

        holidays = OfficialHoliday._base_manager.filter(
            company=company,
            is_active=True,
            start_date__lte=last_day,
            end_date__gte=first_day,
        ).prefetch_related("rules__employees")

        for holiday in holidays:
            rules = list(
                OfficialHolidayRule._base_manager.filter(holiday=holiday)
                .prefetch_related("employees")
                .order_by("priority")
            )

            matched_rule = None
            for rule in rules:
                if rule.applies_to_employee(employee):
                    matched_rule = rule
                    break

            # إجازة رسمية من غير قاعدة تخص الموظف = إجازة مدفوعة (مش غياب)
            treatment = matched_rule.treatment if matched_rule else 'paid_leave'

            current = max(holiday.start_date, first_day)
            end = min(holiday.end_date, last_day)
            while current <= end:
                if current not in result:
                    result[current] = {
                        'treatment': treatment,
                        'rule': matched_rule,
                        'holiday_name': holiday.name,
                    }
                current += timedelta(days=1)

    except Exception:
        logger.exception(
        "payroll_rules error in get_official_holiday_treatment",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    return result

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
        logger.exception(
        "payroll_rules error in get_mission_dates",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    try:
        try:
            from .missions_models import MissionAssignment
        except Exception:
            from .models import MissionAssignment
        for m in MissionAssignment._base_manager.filter(
            employee=employee,
            status__in=['accepted', 'in_progress', 'completed'],
        ):
            if getattr(m, 'mission', None):
                _start_dt = getattr(m.mission, 'planned_start_time', None)
                _end_dt = getattr(m.mission, 'planned_end_time', None)
                if _start_dt:
                    _start_d = _start_dt.date() if hasattr(_start_dt, 'date') else _start_dt
                    _end_d = _end_dt.date() if _end_dt and hasattr(_end_dt, 'date') else _start_d
                    _cur = max(_start_d, first_day)
                    _end_d = min(_end_d, last_day)
                    while _cur <= _end_d:
                        mission_dates.add(_cur)
                        _cur += timedelta(days=1)
    except Exception:
        logger.exception(
        "payroll_rules error in get_mission_dates",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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
                        'paid': bool(getattr(getattr(lv, 'leave_type', None), 'is_paid', True)),
                    }
                else:
                    leave_dates.add(current)
                current += timedelta(days=1)
    except Exception:
        logger.exception(
        "payroll_rules error in get_leave_dates",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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
        logger.exception(
        "payroll_rules error in get_leave_dates",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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
        logger.exception(
        "payroll_rules error in get_approved_permission_minutes",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )
    return late_minutes, early_minutes

def get_approved_permission_minutes_by_day(employee, first_day, last_day):
    """
    نفس get_approved_permission_minutes بس متقسمة على الأيام:
    {date: {'late': دقايق, 'early': دقايق}}
    """
    result = {}
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
            minutes = int(float(req.duration_hours or 0) * 60)
            day = result.setdefault(req.start_date, {'late': 0, 'early': 0})
            if kind == 'late_arrival':
                day['late'] += minutes
            elif kind == 'early_leave':
                day['early'] += minutes
    except Exception:
        logger.exception("payroll_rules error in get_approved_permission_minutes_by_day")
    return result


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
        logger.exception(
        "payroll_rules error in get_unpaid_leave_dates",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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
        logger.exception(
        "payroll_rules error in get_unpaid_leave_dates",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    return unpaid_dates


def _one_time_outside(item, first_day, last_day):
    """بند "مش شهري" (مرة واحدة) بيدخل بس في فترة المرتب اللي فيها تاريخ بدايته"""
    if getattr(item, 'is_monthly', True):
        return False
    start = getattr(item, 'start_date', None)
    return not (start and first_day <= start <= last_day)


_SCOPE_RANK = {'employees': 4, 'department': 3, 'branch': 2, 'company': 1}


def pick_effective_insurance_policies(policies, employee):
    """
    سياسة واحدة بس لكل نوع تأمين (اجتماعي/طبي) على الموظف: الأخص (موظفين > قسم > فرع > شركة)،
    ولو متساويين الأحدث. قبل كده كل السياسات المنطبقة كانت بتتجمع فالتأمين بيتخصم مرتين.
    """
    best = {}
    for p in policies:
        if not p.applies_to_employee(employee):
            continue
        key = (_SCOPE_RANK.get(p.scope, 0), p.start_date, getattr(p, 'version_number', 0) or 0, p.id)
        cur = best.get(p.insurance_type)
        if cur is None or key > cur[0]:
            best[p.insurance_type] = (key, p)
    return [v[1] for v in best.values()]


def daily_salary_for(employee, year, month):
    """أجر اليوم الواحد في كل الحسابات: الأساسي ÷ عدد أيام شهر القفل"""
    return _safe_float(getattr(employee, 'basic_salary', 0)) / monthrange(year, month)[1]


def _get_allowances(employee, first_day, last_day, lang='ar', year=None, month=None):
    total = 0.0
    items = []

    # 1) بدلات فردية للموظف
    try:
        from .company_policy_models import PayrollAllowance
        qs = PayrollAllowance._base_manager.filter(
            employee=employee,
            is_active=True,
            start_date__lte=last_day,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

        for item in qs:
            if _one_time_outside(item, first_day, last_day):
                continue
            amount = _safe_float(item.amount)
            total += amount
            items.append({
                'type': item.allowance_type,
                'name_ar': item.name_ar,
                'name_en': item.name_en or item.name_ar,
                'name': item.name_en if lang == 'en' and item.name_en else item.name_ar,
                'amount': round(amount, 2),
                'is_monthly': bool(item.is_monthly),
                'source': 'individual',
            })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_allowances",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # 2) بدلات عامة (الشركة / فرع / إدارة / موظفين محددين)
    try:
        from .company_policy_models import CompanyAllowancePolicy
        company = getattr(employee, 'company', None)
        if company:
            policies = CompanyAllowancePolicy._base_manager.filter(
                company=company,
                is_active=True,
                start_date__lte=last_day,
            ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

            for policy in policies:
                if not policy.applies_to_employee(employee) or _one_time_outside(policy, first_day, last_day):
                    continue
                amount = _safe_float(policy.amount)
                total += amount
                items.append({
                    'type': policy.allowance_type,
                    'name_ar': policy.name_ar,
                    'name_en': policy.name_en or policy.name_ar,
                    'name': policy.name_en if lang == 'en' and policy.name_en else policy.name_ar,
                    'amount': round(amount, 2),
                    'is_monthly': bool(policy.is_monthly),
                    'source': 'policy',
                    'scope': policy.scope,
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_allowances",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # 3) بدلات يدوية معتمدة من HR (ManualAllowance)
    try:
        from .company_policy_models import ManualAllowance
        # شهر القفل نفسه (مع يوم قفل، أول يوم في الفترة بيبقى في الشهر اللي قبله)
        _y, _m = (year, month) if year and month else (last_day.year, last_day.month)
        days_in_month = monthrange(_y, _m)[1]
        manual_allowances = ManualAllowance._base_manager.filter(
            employee=employee,
            target_year=_y,
            target_month=_m,
            status__in=['approved', 'applied'],
        )
        for entry in manual_allowances:
            basic = float(getattr(employee, 'basic_salary', 0) or 0)
            amount = float(entry.calculate_amount(basic_salary=basic, days_in_month=days_in_month))
            if amount > 0:
                total += amount
                cat = entry.get_category_display() if hasattr(entry, 'get_category_display') else entry.category
                items.append({
                    'type': entry.category,
                    'name_ar': f"بدل يدوي - {cat}",
                    'name_en': f"Manual Allowance - {cat}",
                    'name': f"بدل يدوي - {cat}" if lang == 'ar' else f"Manual Allowance - {cat}",
                    'amount': round(amount, 2),
                    'is_monthly': False,
                    'source': 'manual_entry',
                    'reason': entry.reason or '',
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_allowances",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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
        qs = PayrollDeduction._base_manager.filter(
            employee=employee,
            is_active=True,
            start_date__lte=last_day,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

        for item in qs:
            if _one_time_outside(item, first_day, last_day):
                continue
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
        logger.exception(
        "payroll_rules error in _get_monthly_deductions",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    try:
        from employees.models import Deduction
        for item in Deduction._base_manager.filter(employee=employee, year=year, month=month):
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
        logger.exception(
        "payroll_rules error in _get_monthly_deductions",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

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
    from datetime import date
    total = 0.0
    items = []

    # 1) مكافآت فردية للموظف
    try:
        from .payroll_pro_models import PayrollBonus
        for item in PayrollBonus._base_manager.filter(employee=employee, year=year, month=month):
            amount = _safe_float(item.amount)
            total += amount
            items.append({
                'name_ar': item.name_ar,
                'name_en': item.name_en or item.name_ar,
                'name': item.name_en if lang == 'en' and item.name_en else item.name_ar,
                'amount': round(amount, 2),
                'reason': item.reason or '',
                'source': 'individual',
            })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_bonuses",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # 2) مكافآت عامة (الشركة / فرع / إدارة / موظفين محددين)
    try:
        from .company_policy_models import CompanyBonusPolicy
        from datetime import date
        company = getattr(employee, 'company', None)
        _bounds = get_payroll_period_bounds(company, year, month) if company else _period_bounds(year, month)
        first_day, last_day = _bounds

        if company:
            policies = CompanyBonusPolicy._base_manager.filter(
                company=company,
                is_active=True,
                start_date__lte=last_day,
            ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

            for policy in policies:
                if not policy.applies_to_employee(employee) or _one_time_outside(policy, first_day, last_day):
                    continue
                amount = _safe_float(policy.amount)
                total += amount
                items.append({
                    'name_ar': policy.name_ar,
                    'name_en': policy.name_en or policy.name_ar,
                    'name': policy.name_en if lang == 'en' and policy.name_en else policy.name_ar,
                    'amount': round(amount, 2),
                    'reason': policy.notes or '',
                    'source': 'policy',
                    'scope': policy.scope,
                    'bonus_type': policy.bonus_type,
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_bonuses",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # 3) مقابل إضافي للعمل في الإجازات الرسمية
    try:
        company = getattr(employee, 'company', None)
        if company:
            if hasattr(company, 'payroll_cycle_type'):
                _first_day, _last_day = get_payroll_period_bounds(company, year, month)
            else:
                _first_day, _last_day = _period_bounds(year, month)

            official_holiday_map = get_official_holiday_treatment(employee, year, month)

            attended_dates = set(
                Attendance._base_manager.filter(
                    employee=employee,
                    date__gte=_first_day,
                    date__lte=_last_day,
                    check_in_time__isnull=False,
                ).values_list('date', flat=True)
            )

            # نفس أجر اليوم المستخدم في باقي المرتب (المرتب ÷ أيام الشهر)
            basic_salary_val = _safe_float(getattr(employee, 'basic_salary', 0))
            daily_salary = round(basic_salary_val / monthrange(year, month)[1], 4)

            grouped = {}

            for d, holiday_info in official_holiday_map.items():
                if holiday_info.get('treatment') != 'work_with_bonus':
                    continue
                if d not in attended_dates:
                    continue

                rule = holiday_info.get('rule')
                if not rule:
                    continue

                day_bonus = _safe_float(rule.calculate_bonus(daily_salary, basic_salary_val))
                if day_bonus <= 0:
                    continue

                holiday_name = holiday_info.get('holiday_name') or 'إجازة رسمية'
                rule_id = getattr(rule, 'id', None)
                key = (holiday_name, rule_id, round(day_bonus, 2))

                if key not in grouped:
                    grouped[key] = {
                        'holiday_name': holiday_name,
                        'bonus_days': 0,
                        'day_bonus': round(day_bonus, 2),
                        'amount': 0.0,
                    }

                grouped[key]['bonus_days'] += 1
                grouped[key]['amount'] = round(grouped[key]['amount'] + day_bonus, 2)

            for row in grouped.values():
                total += row['amount']
                items.append({
                    'name_ar': f"مقابل عمل في إجازة رسمية: {row['holiday_name']}",
                    'name_en': f"Official Holiday Work Bonus: {row['holiday_name']}",
                    'name': f"مقابل عمل في إجازة رسمية: {row['holiday_name']}",
                    'amount': round(row['amount'], 2),
                    'reason': f"{row['bonus_days']} يوم × {row['day_bonus']} جنيه/يوم",
                    'source': 'official_holiday_bonus',
                    'holiday_name': row['holiday_name'],
                    'bonus_days': row['bonus_days'],
                    'day_bonus': row['day_bonus'],
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_bonuses",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # 4) مكافآت يدوية معتمدة من HR (ManualBonus)
    try:
        from .company_policy_models import ManualBonus
        import calendar
        _bounds = get_payroll_period_bounds(company, year, month) if company else None
        days_in_month = monthrange(year, month)[1]   # نفس أجر اليوم في باقي المرتب (الأساسي ÷ أيام شهر القفل)
        manual_bonuses = ManualBonus._base_manager.filter(
            employee=employee,
            target_year=year,
            target_month=month,
            status__in=['approved', 'applied'],
        )
        for entry in manual_bonuses:
            basic = float(getattr(employee, 'basic_salary', 0) or 0)
            amount = float(entry.calculate_amount(basic_salary=basic, days_in_month=days_in_month))
            if amount > 0:
                total += amount
                cat = entry.get_category_display() if hasattr(entry, 'get_category_display') else entry.category
                items.append({
                    'name_ar': f"مكافأة يدوية - {cat}",
                    'name_en': f"Manual Bonus - {cat}",
                    'name': f"مكافأة يدوية - {cat}" if lang == 'ar' else f"Manual Bonus - {cat}",
                    'amount': round(amount, 2),
                    'reason': entry.reason or '',
                    'source': 'manual_entry',
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_bonuses",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    return round(total, 2), items




def _get_general_deductions(employee, first_day, last_day, lang='ar'):
    """خصومات عامة من CompanyDeductionPolicy"""
    total = 0.0
    items = []
    try:
        from .company_policy_models import CompanyDeductionPolicy
        company = getattr(employee, 'company', None)
        if company:
            policies = CompanyDeductionPolicy._base_manager.filter(
                company=company,
                is_active=True,
                start_date__lte=last_day,
            ).filter(Q(end_date__isnull=True) | Q(end_date__gte=first_day))

            for policy in policies:
                if not policy.applies_to_employee(employee) or _one_time_outside(policy, first_day, last_day):
                    continue
                amount = _safe_float(policy.amount)
                total += amount
                items.append({
                    'type': policy.deduction_type,
                    'name_ar': policy.name_ar,
                    'name_en': policy.name_en or policy.name_ar,
                    'name': policy.name_en if lang == 'en' and policy.name_en else policy.name_ar,
                    'amount': round(amount, 2),
                    'notes': policy.notes or '',
                    'source': 'policy',
                    'scope': policy.scope,
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_general_deductions",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )
    return round(total, 2), items

def _get_penalties(employee, year, month, lang='ar'):
    total = 0.0
    items = []

    # PayrollPenalty (يدوي من HR)
    try:
        from .payroll_pro_models import PayrollPenalty
        for item in PayrollPenalty._base_manager.filter(employee=employee, year=year, month=month):
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
        logger.exception(
        "payroll_rules error in _get_penalties",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # DisciplinaryAction (جزاءات تأديبية معتمدة)
    try:
        from .models import DisciplinaryAction
        payroll_month_str = f"{year}-{month:02d}"
        disc_actions = DisciplinaryAction._base_manager.filter(
            employee=employee,
            status="approved",
            payroll_month=payroll_month_str,
            payroll_applied=False,
        )
        _fractions = {'quarter_day_deduction': 0.25, 'half_day_deduction': 0.5, 'full_day_deduction': 1.0}
        for action in disc_actions:
            if getattr(action, 'deduction_created', False):
                continue   # النظام القديم عمله خصم منفصل (Deduction) فبيتحسب من هناك
            amount = _safe_float(action.deduction_amount)
            if amount <= 0 and action.action_type in _fractions:
                # خصم يوم/نص/ربع من غير مبلغ مكتوب: بنفس أجر اليوم في المرتب
                amount = round(daily_salary_for(employee, year, month) * _fractions[action.action_type], 2)
            if amount > 0:
                total += amount
                name_ar = f"جزاء تأديبي - {action.get_action_type_display()}"
                name_en = f"Disciplinary - {action.get_action_type_display()}"
                items.append({
                    'name_ar': name_ar,
                    'name_en': name_en,
                    'name': name_en if lang == 'en' else name_ar,
                    'amount': round(amount, 2),
                    'reason': action.reason or '',
                })
                # commit منفصل بعد الحساب (نمنع side effect أثناء القراءة)
                # (الـapplied_action_ids بيتمرر للـhelper)
    except Exception:
        logger.exception(
        "payroll_rules error in _get_penalties",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    # ManualPenalty - جزاءات يدوية معتمدة من HR
    try:
        from .company_policy_models import ManualPenalty
        import calendar
        company = getattr(employee, 'company', None)
        _bounds = get_payroll_period_bounds(company, year, month) if company else None
        days_in_month = monthrange(year, month)[1]   # نفس أجر اليوم في باقي المرتب (الأساسي ÷ أيام شهر القفل)
        manual_penalties = ManualPenalty._base_manager.filter(
            employee=employee,
            target_year=year,
            target_month=month,
            status__in=['approved', 'applied'],
        )
        for entry in manual_penalties:
            basic = float(getattr(employee, 'basic_salary', 0) or 0)
            amount = float(entry.calculate_amount(basic_salary=basic, days_in_month=days_in_month))
            if amount > 0:
                total += amount
                cat = entry.get_category_display() if hasattr(entry, 'get_category_display') else entry.category
                items.append({
                    'name_ar': f"جزاء يدوي - {cat}",
                    'name_en': f"Manual Penalty - {cat}",
                    'name': f"جزاء يدوي - {cat}" if lang == 'ar' else f"Manual Penalty - {cat}",
                    'amount': round(amount, 2),
                    'reason': entry.reason or '',
                    'source': 'manual_entry',
                })
    except Exception:
        logger.exception(
        "payroll_rules error in _get_penalties",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )

    return round(total, 2), items


def _get_installments(employee, year, month):
    total = 0.0
    items = []
    try:
        from .payroll_pro_models import PayrollInstallment
        for item in PayrollInstallment._base_manager.filter(employee=employee, status='active'):
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
        logger.exception(
        "payroll_rules error in _get_installments",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )
    return round(total, 2), items



def _get_active_policy(company, target_date, department=None, branch=None):
    """
    يجيب السياسة الفعالة للشركة/الفرع/القسم في تاريخ معين
    الأولوية: قسم > فرع > شركة
    """
    try:
        from attendance.models import AttendancePolicy, AttendancePolicyAssignment

        date_filter = Q(policy__effective_from__lte=target_date) & (
            Q(policy__effective_to__isnull=True) | Q(policy__effective_to__gte=target_date)
        )
        status_filter = Q(policy__status='active')
        company_filter = Q(policy__company=company)

        # قسم أولاً
        if department:
            dept_assignment = AttendancePolicyAssignment._base_manager.filter(
                date_filter & status_filter & company_filter,
                assignment_type='department',
                department=department
            ).select_related('policy').order_by('priority').first()
            if dept_assignment:
                return dept_assignment.policy

        # فرع تانياً
        if branch:
            branch_assignment = AttendancePolicyAssignment._base_manager.filter(
                date_filter & status_filter & company_filter,
                assignment_type='branch',
                branch=branch
            ).select_related('policy').order_by('priority').first()
            if branch_assignment:
                return branch_assignment.policy

        # شركة أخيراً
        company_assignment = AttendancePolicyAssignment._base_manager.filter(
            date_filter & status_filter & company_filter,
            assignment_type='company'
        ).select_related('policy').order_by('priority').first()
        if company_assignment:
            return company_assignment.policy

        # سياسة معتمدة ومش مربوطة بأي نطاق = بتتطبق على الشركة كلها
        unassigned = AttendancePolicy._base_manager.filter(
            company=company,
            status='active',
            effective_from__lte=target_date,
            assignments__isnull=True,
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=target_date)
        ).order_by('-effective_from', '-id').first()
        if unassigned:
            return unassigned

    except Exception:
        logger.exception(
        "payroll_rules error in _get_active_policy",
        extra={'employee_id': getattr(employee, 'id', None) if 'employee' in dir() else None}
        )
    return None


# أنواع قديمة كان الويب بيحفظها في قواعد التأخير/الغياب ومش من اختيارات الموديل
_LEGACY_DAY_FRACTIONS = {'quarter_day': 0.25, 'half_day': 0.5, 'full_day': 1.0}


def normalize_rule_type(deduction_type, value):
    """
    (نوع الخصم، القيمة) بأسماء الموديل: day_fraction / fixed_amount / per_minute / warning.
    الأنواع القديمة: fixed = مبلغ ثابت، ربع/نص/يوم كامل = كسر يوم، percent = نسبة من اليوم،
    hourly = مبلغ للساعة، none = من غير خصم.
    """
    kind = (deduction_type or '').strip()
    value = _safe_float(value)
    if kind in ('day_fraction', 'fixed_amount', 'per_minute', 'warning'):
        return kind, value
    if kind == 'fixed':
        return 'fixed_amount', value
    if kind in _LEGACY_DAY_FRACTIONS:
        return 'day_fraction', _LEGACY_DAY_FRACTIONS[kind] * (value if value > 0 else 1)
    if kind == 'percent':
        return 'day_fraction', value / 100.0
    if kind == 'hourly':
        return 'per_minute', value / 60.0
    if kind == 'none':
        return 'warning', 0.0
    return kind, value


def _apply_late_rule(policy, late_minutes, daily_salary, per_minute=0.0):
    """قواعد التأخير بتاعة سياسة الحضور (LateRule) على تأخير يوم واحد.
    لائحة الجزاءات (PenaltyRule) بتتطبق قبلها في calculate_effective_payroll.
    التأخير الأكبر من آخر شريحة: آخر شريحة + الدقايق الزيادة بخصم الدقيقة الافتراضي."""
    if not policy or late_minutes <= 0:
        return 0.0
    try:
        from attendance.models import LateRule
        all_rules = list(LateRule.objects.filter(policy=policy))
        if not all_rules:
            return 0.0
        max_to = max(int(r.to_minutes or 0) for r in all_rules)
        extra = 0
        if late_minutes > max_to:
            extra = late_minutes - max_to
            late_minutes = max_to

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

        amount = 0.0
        if rules:
            kind, value = normalize_rule_type(rules.deduction_type, rules.deduction_value)
            if kind == 'day_fraction':
                amount = daily_salary * value
            elif kind == 'fixed_amount':
                amount = value
            elif kind == 'per_minute':
                amount = late_minutes * value
        return round(amount + extra * per_minute, 2)
    except Exception:
        logger.exception("payroll_rules error in _apply_late_rule")
    return 0.0


def _policy_has_late_rules(policy):
    if not policy:
        return False
    try:
        from attendance.models import LateRule
        return LateRule.objects.filter(policy=policy).exists()
    except Exception:
        return False


def _load_scoped_rules(model, company, employee, first_day, last_day, type_field):
    """
    بيجيب قواعد (PenaltyRule / BonusRule / AllowanceRule) الشركة اللي
    بتنطبق على الموظف وسارية في أي جزء من الفترة، متجمعة حسب النوع.
    الأحدث (رقم نسخة أعلى) الأول.
    """
    by_type = {}
    if not company:
        return by_type
    try:
        qs = model._base_manager.filter(
            company=company,
            is_active=True,
            start_date__lte=last_day,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=first_day)
        ).order_by('-version_number', '-created_at', '-id')
        for r in qs:
            if r.applies_to_employee(employee):
                by_type.setdefault(getattr(r, type_field), []).append(r)
    except Exception:
        logger.exception("payroll_rules error in _load_scoped_rules for %s", model.__name__)
    return by_type


def _rule_for_day(rules, d):
    """أول قاعدة سارية في اليوم ده (القائمة مترتبة الأحدث الأول)"""
    for r in rules or []:
        if r.start_date <= d and (r.end_date is None or r.end_date >= d):
            return r
    return None


def _match_tier(tiers, value):
    for tier in tiers or []:
        t_from = float(tier.get('from', 0) or 0)
        t_to = tier.get('to')
        if value >= t_from and (t_to in (None, '') or value <= float(t_to)):
            return tier
    return None


def _tiers_max_to(tiers):
    """أكبر "إلى" في الشرائح، أو None لو آخر شريحة مفتوحة (بدون حد)"""
    max_to = 0.0
    for tier in tiers or []:
        t_to = tier.get('to')
        if t_to in (None, ''):
            return None
        max_to = max(max_to, float(t_to))
    return max_to


def _penalty_tier_amount(tier, quantity, daily_salary, basic_salary):
    """مبلغ شريحة جزاء واحدة. quantity = عدد الوحدات (دقايق) لنوع fixed_per_unit"""
    if not tier:
        return 0.0
    dt = tier.get('deduction_type', 'fixed_per_unit')
    val = float(tier.get('value', 0) or 0)
    if dt == 'fixed_per_unit':
        return quantity * val
    if dt == 'fixed_total':
        return val
    if dt == 'day_fraction':
        return daily_salary * val
    if dt == 'percent_basic':
        return basic_salary * val / 100.0
    if dt == 'quarter_day':
        return daily_salary / 4.0
    if dt == 'half_day':
        return daily_salary / 2.0
    if dt in ('full_day', 'day_plus_warning'):
        return daily_salary
    if dt == 'two_days':
        return daily_salary * 2
    if dt == 'three_days':
        return daily_salary * 3
    return 0.0


def _bonus_overtime_day_hours(rule, day_hours):
    """
    قاعدة أوفر تايم (BonusRule): ساعات اليوم بعد "أقل مدة في اليوم" (بالدقايق، محفوظة
    في الشرائح min_minutes_per_day) و"الحد الأقصى في اليوم" (max_per_day بالساعات).
    """
    min_minutes = max([float(t.get('min_minutes_per_day', 0) or 0) for t in (rule.tiers or [])] or [0])
    if day_hours * 60 < min_minutes:
        return 0.0
    if float(rule.max_per_day or 0) > 0:
        day_hours = min(day_hours, float(rule.max_per_day))
    return day_hours


def _bonus_tier_amount(rule, units, unit_rate, basic_salary):
    """BonusRule: الشريحة بتتحدد بإجمالي الوحدات في الشهر (ساعات أو أيام)"""
    if not rule or units <= 0:
        return 0.0
    tier = _match_tier(rule.tiers, units)
    if not tier:
        return 0.0
    vt = tier.get('value_type', 'multiplier')
    val = float(tier.get('value', 0) or 0)
    if vt == 'multiplier':
        amount = units * unit_rate * val
    elif vt == 'fixed_per_unit':
        amount = units * val
    elif vt == 'fixed_total':
        amount = val
    elif vt == 'percent_basic':
        amount = basic_salary * val / 100.0
    else:
        amount = 0.0
    return amount


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
            _notify_hr_flex_pending(employee, adj_type, target_date, delta, company)
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
            _notify_hr_flex_pending(employee, adj_type, target_date, delta, company)

    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning(f'_upsert_flex_adjustment error: {_e}')


def _notify_hr_flex_pending(employee, adj_type, target_date, delta, company):
    """إشعار الـ HR/Manager لما يتعمل FlexDayAdjustment pending جديد"""
    try:
        from accounts.fcm_service import send_notification_to_managers
        emp_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
        if not emp_name:
            emp_name = str(employee)

        delta_abs = abs(round(delta, 2))
        day_str = str(target_date)

        if adj_type == 'overtime':
            title_ar = '⏰ طلب أوفر تايم مرن'
            body_ar  = f'الموظف {emp_name} اشتغل {delta_abs} ساعة زيادة يوم {day_str} — في انتظار موافقتك'
            title_en = '⏰ Flex Overtime Request'
            body_en  = f'Employee {emp_name} worked {delta_abs} extra hours on {day_str} — awaiting your approval'
        else:
            title_ar = '⚠️ نقص ساعات مرن'
            body_ar  = f'الموظف {emp_name} اشتغل {delta_abs} ساعة أقل يوم {day_str} — في انتظار موافقتك'
            title_en = '⚠️ Flex Shortage Request'
            body_en  = f'Employee {emp_name} worked {delta_abs} fewer hours on {day_str} — awaiting your approval'

        send_notification_to_managers(
            company=company,
            title=title_ar,
            body=body_ar,
            data={
                'type': 'flex_adjustment_pending',
                'screen': 'flex_adjustments',
            },
            title_en=title_en,
            body_en=body_en,
            employee=employee,
        )
    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning(f'_notify_hr_flex_pending error: {_e}')


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

    # لو اليوم ده اتحول لإذن قبل كده (حساب مرتب سابق) نستخدم نفس الحركة
    # عشان كل مرة نفتح فيها المرتب مايتسحبش من الرصيد تاني
    if reference_date:
        existing = PermissionLedger._base_manager.filter(
            employee=employee,
            entry_type='auto_late',
            reference_date=reference_date,
        ).first()
        if existing:
            converted = min(int(existing.minutes_used or 0), late_minutes)
            return converted, max(0, late_minutes - converted)

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

    # التأخير اللي هيتحول لإذن (مش أكتر من حد المرة ولا الرصيد ولا التأخير نفسه)
    minutes_to_convert = min(late_minutes, max_per_request, remaining_minutes)
    count_to_use = 1
    # لو "الكسر بمرة كاملة": المرة بتتخصم من الرصيد كاملة حتى لو التأخير أقل
    minutes_charged = minutes_to_convert
    if policy.permission_fraction_as_full:
        minutes_charged = min(max_per_request, remaining_minutes)

    if minutes_to_convert <= 0 or count_to_use > remaining_count:
        return 0, late_minutes

    # نسجل الحركة في الـ Ledger
    try:
        PermissionLedger._base_manager.create(
            employee=employee,
            company=employee.company,
            entry_type='auto_late',
            minutes_used=minutes_charged,
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
    """قاعدة الغياب بتاعة سياسة الحضور (AbsenceRule) — absent_days ممكن يكون كسر (نص يوم)"""
    if not policy or absent_days <= 0:
        return 0.0
    try:
        from attendance.models import AbsenceRule
        rules = AbsenceRule.objects.filter(policy=policy)
        # قاعدة الغياب بدون إذن، ولو مش موجودة أول قاعدة غياب في السياسة
        rule = rules.filter(absence_type='unexcused').order_by('display_order').first() or \
            rules.order_by('display_order').first()

        if not rule:
            return round(absent_days * daily_salary, 2)

        kind, value = normalize_rule_type(rule.deduction_type, rule.deduction_value)
        if kind == 'day_fraction':
            return round(absent_days * daily_salary * value, 2)
        elif kind == 'fixed_amount':
            return round(absent_days * value, 2)
        elif kind == 'warning':
            return 0.0
    except Exception:
        logger.exception("payroll_rules error in _apply_absence_rule")
    return round(absent_days * daily_salary, 2)


def _policy_overtime_rule(policy, overtime_type='after_shift'):
    if not policy:
        return None
    try:
        from attendance.models import OvertimeRule
        rule = OvertimeRule.objects.filter(
            policy=policy, overtime_type=overtime_type
        ).order_by('display_order').first()
        if not rule:
            rule = OvertimeRule.objects.filter(
                policy=policy, overtime_type='after_shift'
            ).order_by('display_order').first()
        return rule
    except Exception:
        logger.exception("payroll_rules error in _policy_overtime_rule")
        return None


def _apply_overtime_rule(policy, overtime_hours, hourly_rate, overtime_type='after_shift'):
    """قاعدة الأوفر تايم بتاعة سياسة الحضور. بترجع None لو السياسة مفيهاش قاعدة."""
    if overtime_hours <= 0:
        return 0.0
    rule = _policy_overtime_rule(policy, overtime_type)
    if not rule:
        return None
    # أقل مدة والحد اليومي بيتطبقوا على كل يوم لوحده (_policy_overtime_day_hours)
    hours = overtime_hours
    if rule.max_hours_per_month:
        hours = min(hours, float(rule.max_hours_per_month))
    return round(hours * hourly_rate * float(rule.multiplier), 2)


def _policy_overtime_day_hours(rule, day_hours):
    """ساعات أوفر تايم يوم واحد بعد "أقل مدة" و"الحد اليومي" بتوع قاعدة سياسة الحضور"""
    if day_hours * 60 < float(rule.min_minutes or 0):
        return 0.0
    if rule.max_hours_per_day:
        day_hours = min(day_hours, float(rule.max_hours_per_day))
    return day_hours


def _apply_night_allowance(policy, night_shift_days, daily_salary):
    """بدل الشيفت الليلي من سياسة الحضور (NightShiftRule)"""
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
        logger.exception("payroll_rules error in _apply_night_allowance")
    return 0.0


def _apply_weekend_allowance(policy, weekend_work_days, daily_salary):
    """مقابل الشغل في يوم الراحة من سياسة الحضور (WeekendWorkRule)"""
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
        elif rule.compensation_type == 'day_off':
            return 0.0
    except Exception:
        logger.exception("payroll_rules error in _apply_weekend_allowance")
    return round(weekend_work_days * daily_salary * 2, 2)



def _is_exempt_from_attendance(role):
    """هل الموظف معفي من خصم الغياب/التأخير (أدمن/HR)؟"""
    return role in ('company_admin', 'hr_manager', 'super_admin')



_applies_cache = {}

def _is_policy_applicable(policy, employee, year, month):
    """بديل memoized لـpolicy.applies_to_employee() لتقليل N+1 queries."""
    key = (policy.__class__.__name__, policy.id, employee.id)
    if key in _applies_cache:
        return _applies_cache[key]
    try:
        result = policy.applies_to_employee(employee)
        _applies_cache[key] = result
        return result
    except Exception:
        logger.exception("applies_to_employee failed for %s on %s", policy, employee)
        return False


_DEFAULT_SETTINGS = {
    # نفس DEFAULT_SETTINGS في api_payroll — لما الشركة مالهاش إعدادات رواتب محفوظة
    'late_deduction_per_minute': 1.0,
    'absence_deduction_per_day': 0.0,  # 0 = أجر اليوم
    'overtime_rate_per_hour': 0.0,     # 0 = مفيش أوفر تايم إلا لو فيه قاعدة
    'insurance_mode': 'none',
    'insurance_fixed_amount': 0.0,
    'insurance_percent': 0.0,
    'field_allowance_type': 'none',
    'fixed_field_allowance': 0.0,
    'per_visit_allowance': 0.0,
}


def _resolve_payroll_settings(company, settings=None):
    """
    إعدادات الرواتب دايماً من شركة الموظف نفسه (مش من شركة المستخدم اللي فاتح الشاشة)،
    عشان كل الشاشات والتقارير تطلع نفس الرقم.
    """
    try:
        from attendance.payroll_settings_model import PayrollSettings
        s = PayrollSettings._base_manager.filter(company=company).first() if company else None
        if s:
            return {
                'late_deduction_per_minute': float(s.late_deduction_per_minute),
                'absence_deduction_per_day': float(s.absence_deduction_per_day),
                'overtime_rate_per_hour': float(s.overtime_rate_per_hour),
                'insurance_mode': getattr(s, 'insurance_mode', 'none') or 'none',
                'insurance_fixed_amount': float(getattr(s, 'insurance_fixed_amount', 0) or 0),
                'insurance_percent': float(getattr(s, 'insurance_percent', 0) or 0),
                'field_allowance_type': getattr(s, 'field_allowance_type', 'none') or 'none',
                'fixed_field_allowance': float(getattr(s, 'fixed_field_allowance', 0) or 0),
                'per_visit_allowance': float(getattr(s, 'per_visit_allowance', 0) or 0),
            }
    except Exception:
        logger.exception("payroll_rules error in _resolve_payroll_settings")
    merged = dict(_DEFAULT_SETTINGS)
    if settings:
        merged.update(settings)
    return merged


def calculate_effective_payroll(employee, year, month, settings=None, lang='ar'):
    """
    الحساب الكامل للراتب:
    Basic + Allowances + Overtime + Bonuses
    - Late - Absence - Insurance - Installments - Penalties - Extra
    = Net Salary

    ترتيب الأولوية في الخصومات (التأخير / الغياب / الانصراف المبكر):
      1) لائحة الجزاءات (PenaltyRule) لو فيه قاعدة سارية تخص الموظف
      2) قواعد سياسة الحضور المعتمدة (LateRule / AbsenceRule)
      3) إعدادات الرواتب (خصم الدقيقة / خصم يوم الغياب، والصفر = أجر اليوم)
    فترة السماح بتتطبق مرة واحدة: الأكبر بين سماحية الشيفت وسماحية اللائحة،
    والخصم بيبدأ بعدها.
    """
    company = getattr(employee, 'company', None)
    settings = _resolve_payroll_settings(company, settings)

    late_per_min = _safe_float(settings.get('late_deduction_per_minute', 1.0))
    absence_per_day = _safe_float(settings.get('absence_deduction_per_day', 0))
    overtime_per_hour = _safe_float(settings.get('overtime_rate_per_hour', 0))
    insurance_mode = settings.get('insurance_mode', 'none')
    insurance_fixed_amount = _safe_float(settings.get('insurance_fixed_amount', 0))
    insurance_percent = _safe_float(settings.get('insurance_percent', 0))

    # الأدمن/HR/Super Admin ملهومش نظام حضور وانصراف أصلاً، فمينفعش يتحسبلهم غياب أو تأخير
    _emp_user_role = getattr(getattr(employee, 'user', None), 'role', None)
    _exempt = _is_exempt_from_attendance(_emp_user_role)

    department = getattr(employee, 'department', None)
    branch = getattr(employee, 'branch', None)

    # Phase 1: فترة المرتب حسب إعدادات الشركة
    if company and hasattr(company, 'payroll_cycle_type'):
        first_day, last_day = get_payroll_period_bounds(company, year, month)
    else:
        first_day, last_day = _period_bounds(year, month)

    # فترة التعيين جوه فترة المرتب (اللي قبل التعيين أو بعد انتهاء الخدمة مش مستحق)
    _hire = getattr(employee, 'hire_date', None)
    _term = getattr(employee, 'termination_date', None)
    emp_start = max(first_day, _hire) if _hire else first_day
    emp_end = min(last_day, _term) if _term else last_day

    def _employed(d):
        return emp_start <= d <= emp_end

    # ═══ قواعد مركز السياسات اللي بتخص الموظف ═══
    from attendance.company_policy_models import PenaltyRule, BonusRule, AllowanceRule
    penalty_rules = _load_scoped_rules(PenaltyRule, company, employee, first_day, last_day, 'penalty_type')
    bonus_rules = _load_scoped_rules(BonusRule, company, employee, first_day, last_day, 'bonus_type')
    allowance_rules = _load_scoped_rules(AllowanceRule, company, employee, first_day, last_day, 'allowance_type')

    def _tiered_rule(kind, d):
        r = _rule_for_day(penalty_rules.get(kind), d)
        return r if r and r.tiers else None

    _policy_cache = {}

    def _get_day_policy(d):
        if d not in _policy_cache:
            _policy_cache[d] = _get_active_policy(company, d, department=department, branch=branch)
        return _policy_cache[d]

    working_dates = [d for d in get_company_working_days(company, year, month) if _employed(d)]
    mission_dates = get_mission_dates(employee, year, month)
    leave_dates, half_day_dates = get_leave_dates(employee, year, month)
    unpaid_leave_dates = get_unpaid_leave_dates(employee, year, month)
    official_holiday_map = get_official_holiday_treatment(employee, year, month)
    permissions_by_day = get_approved_permission_minutes_by_day(employee, first_day, last_day)

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
        if getattr(a, 'check_in_time', None) is not None and _employed(a.date)
    }

    # Hybrid: جلب الملخصات اليومية المتاحة (لو موجودة تسرّع الحساب)
    try:
        from attendance.models import DailyAttendanceSummary
        _today = date.today()
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
    approved_late_minutes = 0
    approved_early_minutes = 0
    daily_details = []

    night_shift_days = 0
    weekend_work_days = 0

    def _late_for_day(d, late_min, shift, half):
        """
        late_min جاي بعد سماحية الشيفت.
        بيرجع (التأخير بعد السماح الموحد، التأخير اللي يتخصم بعد الأذونات)
        """
        nonlocal approved_late_minutes
        if half and half.get('type') == 'morning':
            late_min = max(0, late_min - int(float(half.get('hours', 4)) * 60))
        if late_min <= 0:
            return 0, 0
        rule = _tiered_rule('late_arrival', d)
        if rule and rule.grace_amount:
            shift_grace = int(getattr(shift, 'grace_period', 0) or 0) if shift else 0
            late_min = max(0, late_min - max(0, int(rule.grace_amount) - shift_grace))
        if late_min <= 0:
            return 0, 0
        approved = min(late_min, permissions_by_day.get(d, {}).get('late', 0))
        approved_late_minutes += approved
        remaining = late_min - approved
        if remaining > 0:
            _conv, remaining = _apply_permission_balance(employee, remaining, d, _get_day_policy(d))
        return late_min, remaining

    def _early_for_day(d, att, half):
        nonlocal approved_early_minutes
        elm = int(getattr(att, 'early_leave_minutes', 0) or 0) if att else 0
        if half and half.get('type') == 'afternoon':
            elm = max(0, elm - int(float(half.get('hours', 4)) * 60))
        approved = min(elm, permissions_by_day.get(d, {}).get('early', 0))
        approved_early_minutes += approved
        return elm, elm - approved

    def _fmt(t):
        return timezone.localtime(t).strftime('%I:%M %p') if t else None

    # ندمج أيام الشركة مع أي أيام الموظف اشتغلها فعلياً وهي مش أيام عمل للشركة
    # الأدمن/HR/Super Admin ملهومش نظام حضور وانصراف أصلاً، فمفيش أيام تتحسب ليهم خالص
    if _exempt:
        all_eval_dates = []
    else:
        all_eval_dates = sorted(list(set(working_dates) | attended_dates))
    for d in all_eval_dates:
        att = attendance_by_date.get(d)
        half = half_day_dates.get(d)

        # إجازة رسمية مدفوعة → يتحسب on_leave مش absent
        _official = official_holiday_map.get(d)
        if _official and _official['treatment'] == 'paid_leave':
            if d not in attended_dates:
                on_leave_days += 1
                continue

        # لو الموظف عنده طلب إجازة معتمد لليوم ده، الأولوية للإجازة
        # حتى لو فيه summary محفوظة قديمة بحالة "absent" من قبل الموافقة
        if d in leave_dates:
            on_leave_days += 1
            if d in unpaid_leave_dates:
                unpaid_leave_days += 1
            daily_details.append({
                'date': d.isoformat(), 'status': 'on_leave',
                'effective_status': 'on_leave', 'check_in': None,
                'check_out': None, 'work_hours': 0,
                'late_minutes': 0, 'overtime_hours': 0,
                'shift_name': '', 'is_night_shift': False, 'is_weekend_work': False,
            })
            continue

        # نص يوم إجازة: النص التاني يا حضور يا غياب
        if half and d not in mission_dates:
            on_leave_days += 0.5
            if not half.get('paid', True):
                unpaid_leave_days += 0.5
            day_shift = _get_shift_for_date(employee, d)
            if att and att.check_in_time:
                present_days += 0.5
                late_min, deductible_late = _late_for_day(d, _calc_late_minutes(day_shift, att), day_shift, half)
                elm, deductible_early = _early_for_day(d, att, half)
                work_h = _safe_float(att.work_hours)
                ot_h = _calc_overtime_hours(day_shift, att)
                total_work_hours += work_h
                total_overtime_hours += ot_h
                total_early_leave_minutes += deductible_early
                total_late_minutes += deductible_late
                if late_min > 0:
                    late_days += 1
                daily_details.append({
                    'date': d.isoformat(), 'status': 'half_day_leave',
                    'effective_status': 'late' if late_min > 0 else 'present',
                    'check_in': _fmt(att.check_in_time), 'check_out': _fmt(att.check_out_time),
                    'work_hours': round(work_h, 2), 'late_minutes': late_min,
                    'deductible_late_minutes': deductible_late,
                    'early_leave_minutes': elm, 'deductible_early_minutes': deductible_early,
                    'overtime_hours': round(ot_h, 2),
                    'shift_name': day_shift.name if day_shift else '',
                    'is_night_shift': False, 'is_weekend_work': False, 'half_day_leave': True,
                })
            else:
                absent_days += 0.5
                daily_details.append({
                    'date': d.isoformat(), 'status': 'half_day_leave',
                    'effective_status': 'absent', 'absent_fraction': 0.5,
                    'check_in': None, 'check_out': None, 'work_hours': 0,
                    'late_minutes': 0, 'early_leave_minutes': 0, 'overtime_hours': 0,
                    'shift_name': day_shift.name if day_shift else '',
                    'is_night_shift': False, 'is_weekend_work': False, 'half_day_leave': True,
                })
            continue

        # Hybrid: لو عندنا summary لليوم ده نستخدمها
        _summary = _summaries.get(d)
        if _summary and d not in mission_dates:
            _es = _summary.effective_status or _summary.status
            # ملخص قديم بيقول غياب والموظف عنده حضور فعلي (اتعدل بعدين) → نتجاهل الملخص
            if _es == 'absent' and d in attended_dates:
                _summary = None
        if _summary and d not in mission_dates:
            _day_shift = _summary.shift or _get_shift_for_date(employee, d)
            _late_shown = 0
            _late_deductible = 0

            if _es == 'present':
                present_days += 1
            elif _es == 'late':
                _late_shown, _late_deductible = _late_for_day(d, int(_summary.late_minutes or 0), _day_shift, None)
                if _late_shown > 0:
                    late_days += 1
                    total_late_minutes += _late_deductible
                else:
                    present_days += 1
                    _es = 'present'
            elif _es == 'absent':
                absent_days += 1
            elif _es == 'weekend':
                pass
            elif _es == 'on_leave':
                on_leave_days += 1

            _wh = float(_summary.work_hours or 0)
            _oth = float(_summary.overtime_hours or 0)
            _elm, _elm_deductible = _early_for_day(d, att, None)
            total_work_hours += _wh
            total_overtime_hours += _oth
            total_early_leave_minutes += _elm_deductible

            if _summary.is_night_shift:
                night_shift_days += 1
            if _summary.is_weekend_work:
                weekend_work_days += 1

            daily_details.append({
                'date': d.isoformat(),
                'status': _summary.status,
                'effective_status': _es,
                'check_in': _fmt(att.check_in_time) if att else None,
                'check_out': _fmt(att.check_out_time) if att else None,
                'work_hours': round(_wh, 2),
                'late_minutes': _late_shown,
                'deductible_late_minutes': _late_deductible,
                'early_leave_minutes': _elm,
                'deductible_early_minutes': _elm_deductible,
                'overtime_hours': round(_oth, 2),
                'shift_name': _day_shift.name if _day_shift else '',
                'is_night_shift': _summary.is_night_shift,
                'is_weekend_work': _summary.is_weekend_work,
            })
            continue

        # Fallback: الحساب التقليدي لو مفيش summary
        day_shift = _get_shift_for_date(employee, d)

        if d in mission_dates:
            mission_days += 1
            work_h = _safe_float(att.work_hours if att else 0)
            ot_h = _calc_overtime_hours(day_shift, att)
            elm = int(getattr(att, 'early_leave_minutes', 0) or 0) if att else 0
            total_work_hours += work_h
            total_overtime_hours += ot_h
            is_night = _is_night_shift(day_shift)
            if is_night:
                night_shift_days += 1
            daily_details.append({
                'date': d.isoformat(), 'status': 'mission_day',
                'effective_status': 'present',
                'check_in': _fmt(att.check_in_time) if att else None,
                'check_out': _fmt(att.check_out_time) if att else None,
                'work_hours': round(work_h, 2),
                # يوم المأمورية مفيهوش خصم تأخير ولا انصراف مبكر
                'late_minutes': 0, 'early_leave_minutes': elm, 'deductible_early_minutes': 0,
                'overtime_hours': round(ot_h, 2),
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
                    # لو فيه check-in ومفيش check-out على Attendance الأساسي
                    # يبقى اليوم مش غياب كامل، ده checkout ناقص
                    if att and att.check_in_time and not att.check_out_time:
                        present_days += 1
                        elm, deductible_early = _early_for_day(d, att, None)
                        total_early_leave_minutes += deductible_early
                        daily_details.append({
                            'date': d.isoformat(),
                            'status': getattr(att, 'status', 'present'),
                            'effective_status': 'present',
                            'check_in': _fmt(att.check_in_time),
                            'check_out': None,
                            'work_hours': 0,
                            'late_minutes': 0,
                            'early_leave_minutes': elm,
                            'deductible_early_minutes': deductible_early,
                            'overtime_hours': 0,
                            'shift_name': day_shift.name if day_shift else '',
                            'is_night_shift': False,
                            'is_weekend_work': False,
                        })
                    else:
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
                raw_late = split_metrics['late_minutes'] + split_metrics['shortage_minutes']
                ot_h = 0.0
            else:
                work_h = _safe_float(att.work_hours)
                ot_h = _calc_overtime_hours(day_shift, att)
                raw_late = _calc_late_minutes(day_shift, att)
            is_night = _is_night_shift(day_shift)
            is_weekend = _is_weekend_work(day_shift, d)

            total_work_hours += work_h
            total_overtime_hours += ot_h

            if is_night:
                night_shift_days += 1
            if is_weekend:
                weekend_work_days += 1

            elm, deductible_early = _early_for_day(d, att, None)
            total_early_leave_minutes += deductible_early

            late_min, deductible_late = _late_for_day(d, raw_late, day_shift, None)
            if late_min > 0:
                late_days += 1
                total_late_minutes += deductible_late
                eff_status = 'late'
            else:
                present_days += 1
                eff_status = 'present'

            daily_details.append({
                'date': d.isoformat(),
                'status': getattr(att, 'status', 'present'),
                'effective_status': eff_status,
                'check_in': _fmt(att.check_in_time),
                'check_out': _fmt(att.check_out_time),
                'work_hours': round(work_h, 2),
                'late_minutes': late_min,
                'deductible_late_minutes': deductible_late,
                'early_leave_minutes': elm,
                'deductible_early_minutes': deductible_early,
                'overtime_hours': round(ot_h, 2),
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': is_night,
                'is_weekend_work': is_weekend,
            })
            continue

        if day_shift and not day_shift.is_work_day(d):
            # لو الموظف مجاش في يوم راحته -> مش غياب ومش شغل في يوم راحة
            daily_details.append({
                'date': d.isoformat(), 'status': 'weekend',
                'effective_status': 'weekend', 'check_in': None,
                'check_out': None, 'work_hours': 0,
                'late_minutes': 0, 'early_leave_minutes': 0, 'overtime_hours': 0,
                'shift_name': day_shift.name if day_shift else '',
                'is_night_shift': False, 'is_weekend_work': False,
            })
            continue
        # لو النهارده ولسه وقت شيفت الموظف ما جاش، منحسبوش غياب
        if d == timezone.localdate() and day_shift and getattr(day_shift, 'start_time', None):
            _now_time = timezone.localtime(timezone.now()).time()
            if _now_time < day_shift.start_time:
                daily_details.append({
                    'date': d.isoformat(), 'status': 'pending',
                    'effective_status': 'pending', 'check_in': None,
                    'check_out': None, 'work_hours': 0,
                    'late_minutes': 0, 'overtime_hours': 0,
                    'shift_name': day_shift.name if day_shift else '',
                    'is_night_shift': False, 'is_weekend_work': False,
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

    # ── إضافة بيانات الزيارات الميدانية لكل يوم في daily_details ──
    try:
        from attendance.models import LocationCheckIn
        from collections import defaultdict

        _visits_qs = LocationCheckIn._base_manager.filter(
            employee=employee,
            arrival_time__date__gte=first_day,
            arrival_time__date__lte=last_day,
        ).values('arrival_time', 'departure_time', 'status')

        _visits_by_date = defaultdict(list)
        for _v in _visits_qs:
            _vdate = timezone.localtime(_v['arrival_time']).date() if _v['arrival_time'] else None
            if _vdate:
                _visits_by_date[_vdate].append(_v)

        for _dd in daily_details:
            try:
                _dd_date = date.fromisoformat(_dd['date'])
            except Exception:
                _dd['visit_count'] = 0
                _dd['visit_total_minutes'] = 0
                _dd['auto_closed_visits_count'] = 0
                continue

            _day_visits = _visits_by_date.get(_dd_date, [])
            _visit_count = len(_day_visits)
            _visit_total_minutes = 0
            _auto_closed_count = 0

            for _v in _day_visits:
                if _v['departure_time'] and _v['arrival_time']:
                    _dur = (_v['departure_time'] - _v['arrival_time']).total_seconds() / 60
                    _visit_total_minutes += max(0, int(_dur))
                if _v.get('status') == 'auto_closed':
                    _auto_closed_count += 1

            _dd['visit_count'] = _visit_count
            _dd['visit_total_minutes'] = _visit_total_minutes
            _dd['auto_closed_visits_count'] = _auto_closed_count
    except Exception:
        for _dd in daily_details:
            _dd.setdefault('visit_count', 0)
            _dd.setdefault('visit_total_minutes', 0)
            _dd.setdefault('auto_closed_visits_count', 0)

    # ── تعليم الأيام اللي فيها check-in بدون check-out ──
    missing_checkout_days_count = 0
    for _dd in daily_details:
        _missing_checkout = bool(_dd.get('check_in')) and not bool(_dd.get('check_out'))
        _dd['missing_checkout'] = _missing_checkout
        if _missing_checkout:
            missing_checkout_days_count += 1

    basic_salary = _safe_float(getattr(employee, 'basic_salary', 0))
    currency = getattr(employee, 'currency', None) or 'EGP'
    has_insurance = bool(getattr(employee, 'has_insurance', False))

    # حساب اليومي والساعي للموظف — المرتب اليومي = المرتب ÷ عدد أيام الشهر التقويمي كامل (مش أيام العمل)
    calendar_days_in_month = monthrange(year, month)[1]
    daily_salary = round(basic_salary / calendar_days_in_month, 4)
    # اجيب الشيفت الافتراضي للموظف عشان احسب أجر الساعة منه
    _default_shift_for_rate = _get_shift_for_date(employee, first_day)
    _work_hours_for_rate = float(_default_shift_for_rate.work_hours) if _default_shift_for_rate and _default_shift_for_rate.work_hours else 8.0
    hourly_rate = round(daily_salary / _work_hours_for_rate, 4)

    # ═══════════════════════════════════════════════════
    # تحويل الأيام لفلوس — يوم بيوم، وكل يوم بالقاعدة السارية فيه
    # ═══════════════════════════════════════════════════
    late_deduction = 0.0
    early_leave_deduction = 0.0
    absence_deduction = 0.0
    missing_checkout_deduction = 0.0
    _absence_counter = {}
    _missing_counter = {}
    _ot_bonus = {}       # rule_id -> [rule, hours]
    _ot_policy = {}      # policy_id -> [policy, hours]
    _ot_settings_hours = 0.0
    _night_bonus = {}    # rule_id -> [rule, hours]
    _night_policy = {}   # policy_id -> [policy, days]
    _weekend_bonus = {}  # rule_id -> [rule, days]
    _weekend_policy = {} # policy_id -> [policy, days]
    _used_policies = {}
    _today_local = timezone.localdate()

    for dd in daily_details:
        try:
            _d = date.fromisoformat(dd['date'])
        except Exception:
            continue
        _dp = _get_day_policy(_d)
        if _dp:
            _used_policies[_dp.id] = _dp
        _es = dd.get('effective_status', '')

        # التأخير
        _dl = int(dd.get('deductible_late_minutes', 0) or 0)
        if _dl > 0:
            _rule = _tiered_rule('late_arrival', _d)
            if _rule:
                # التأخير الأكبر من آخر شريحة: آخر شريحة + الدقايق الزيادة بخصم الدقيقة الافتراضي
                _max_to = _tiers_max_to(_rule.tiers)
                _extra = max(0, _dl - _max_to) if _max_to is not None else 0
                _cov = _dl - _extra
                late_deduction += round(
                    _penalty_tier_amount(_match_tier(_rule.tiers, _cov), _cov, daily_salary, basic_salary)
                    + _extra * late_per_min, 2)
            elif _policy_has_late_rules(_dp):
                late_deduction += _apply_late_rule(_dp, _dl, daily_salary, late_per_min)
            else:
                late_deduction += _dl * late_per_min

        # الانصراف المبكر
        _de = int(dd.get('deductible_early_minutes', 0) or 0)
        if _de > 0:
            _rule = _tiered_rule('early_leave', _d)
            if _rule:
                _eff = max(0, _de - int(_rule.grace_amount or 0))
                if _eff > 0:
                    early_leave_deduction += round(_penalty_tier_amount(_match_tier(_rule.tiers, _eff), _eff, daily_salary, basic_salary), 2)
            else:
                early_leave_deduction += _de * late_per_min

        # نسيان تسجيل الانصراف (النهارده لسه ممكن يسجل)
        if dd.get('missing_checkout') and _d < _today_local:
            _rule = _tiered_rule('missing_checkout', _d)
            if _rule:
                _n = _missing_counter.get(_rule.id, 0) + 1
                _missing_counter[_rule.id] = _n
                _idx = _n - int(_rule.grace_amount or 0)
                if _idx > 0:
                    missing_checkout_deduction += round(_penalty_tier_amount(_match_tier(_rule.tiers, _idx), 1, daily_salary, basic_salary), 2)

        # الغياب: الشرائح تصاعدية — يوم الغياب رقم N بيتخصم بالشريحة اللي N واقع فيها
        if _es == 'absent':
            _frac = float(dd.get('absent_fraction', 1) or 1)
            _rule = _tiered_rule('absence', _d)
            if _rule:
                _cur = _absence_counter.get(_rule.id, 0.0) + _frac
                _absence_counter[_rule.id] = _cur
                _idx = int(-(-_cur // 1)) - int(_rule.grace_amount or 0)  # ceil
                if _idx > 0:
                    absence_deduction += round(_penalty_tier_amount(_match_tier(_rule.tiers, _idx), 1, daily_salary, basic_salary) * _frac, 2)
            elif _dp:
                absence_deduction += _apply_absence_rule(_dp, _frac, daily_salary)
            else:
                absence_deduction += _frac * (absence_per_day if absence_per_day > 0 else daily_salary)

        # الأوفر تايم
        _oth = float(dd.get('overtime_hours', 0) or 0)
        if _oth > 0:
            _br = _rule_for_day(bonus_rules.get('overtime'), _d)
            if _br and _br.tiers:
                _ot_bonus.setdefault(_br.id, [_br, 0.0])[1] += _bonus_overtime_day_hours(_br, _oth)
            elif _dp and _policy_overtime_rule(_dp):
                _ot_policy.setdefault(_dp.id, [_dp, 0.0])[1] += _policy_overtime_day_hours(_policy_overtime_rule(_dp), _oth)
            else:
                _ot_settings_hours += _oth

        # الشيفت الليلي
        if dd.get('is_night_shift') and dd.get('check_in'):
            _br = _rule_for_day(bonus_rules.get('night_shift'), _d)
            if _br and _br.tiers:
                _night_bonus.setdefault(_br.id, [_br, 0.0])[1] += float(dd.get('work_hours', 0) or 0)
            elif _dp:
                _night_policy.setdefault(_dp.id, [_dp, 0])[1] += 1

        # الشغل في يوم الراحة
        if dd.get('is_weekend_work'):
            _br = _rule_for_day(bonus_rules.get('weekend_work'), _d)
            if _br and _br.tiers:
                _weekend_bonus.setdefault(_br.id, [_br, 0])[1] += 1
            elif _dp:
                _weekend_policy.setdefault(_dp.id, [_dp, 0])[1] += 1

    overtime_bonus = 0.0
    for _r, _h in _ot_bonus.values():
        if float(_r.max_per_month or 0) > 0:
            _h = min(_h, float(_r.max_per_month))  # الحد الشهري بالساعات
        overtime_bonus += _bonus_tier_amount(_r, _h, hourly_rate, basic_salary)
    for _p, _h in _ot_policy.values():
        overtime_bonus += _apply_overtime_rule(_p, _h, hourly_rate) or 0.0
    overtime_bonus += _ot_settings_hours * overtime_per_hour

    night_allowance = 0.0
    for _r, _h in _night_bonus.values():
        night_allowance += _bonus_tier_amount(_r, _h, hourly_rate, basic_salary)
    for _p, _n in _night_policy.values():
        night_allowance += _apply_night_allowance(_p, _n, daily_salary)

    weekend_allowance = 0.0
    for _r, _n in _weekend_bonus.values():
        weekend_allowance += _bonus_tier_amount(_r, _n, daily_salary, basic_salary)
    for _p, _n in _weekend_policy.values():
        weekend_allowance += _apply_weekend_allowance(_p, _n, daily_salary)

    if _exempt:
        late_deduction = early_leave_deduction = absence_deduction = missing_checkout_deduction = 0.0

    late_deduction = round(late_deduction, 2)
    early_leave_deduction = round(early_leave_deduction, 2)
    absence_deduction = round(absence_deduction, 2)
    missing_checkout_deduction = round(missing_checkout_deduction, 2)
    overtime_bonus = round(overtime_bonus, 2)
    night_allowance = round(night_allowance, 2)
    weekend_allowance = round(weekend_allowance, 2)

    # policy_name: لو فيه أكتر من سياسة نقول "سياسات متعددة"
    _used_list = list(_used_policies.values())
    if len(_used_list) == 0:
        active_policy = None
    elif len(_used_list) == 1:
        active_policy = _used_list[0]
    else:
        active_policy = type('_MultiPolicy', (), {'name': 'سياسات متعددة' if lang == 'ar' else 'Multiple Policies'})()

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

    unpaid_leave_deduction = round(unpaid_leave_days * daily_salary, 2)

    # الأيام اللي قبل التعيين أو بعد انتهاء الخدمة جوه فترة المرتب
    if emp_start > emp_end:
        not_employed_days = (last_day - first_day).days + 1
    else:
        not_employed_days = (emp_start - first_day).days + (last_day - emp_end).days
    not_employed_deduction = round(not_employed_days * daily_salary, 2)

    allowances_total, allowance_items = _get_allowances(employee, first_day, last_day, lang=lang, year=year, month=month)
    deductions = _get_monthly_deductions(employee, year, month, lang=lang)
    general_deductions_total, general_deduction_items = _get_general_deductions(employee, first_day, last_day, lang=lang)
    bonuses_total, bonus_items = _get_bonuses(employee, year, month, lang=lang)
    penalties_total_new, penalty_items_new = _get_penalties(employee, year, month, lang=lang)
    installments_total_new, installment_items_new = _get_installments(employee, year, month)

    general_insurance_total = 0.0
    general_installments_total = 0.0
    general_extra_total = 0.0
    general_insurance_items = []
    general_installment_items = []
    general_extra_items = []

    for item in general_deduction_items:
        dtype = (item.get('type') or '').lower()
        amount = _safe_float(item.get('amount'))

        if dtype in ('social_insurance', 'health_insurance'):
            general_insurance_total += amount
            general_insurance_items.append(item)
        elif dtype in ('loan_recovery',):
            general_installments_total += amount
            general_installment_items.append(item)
        else:
            general_extra_total += amount
            general_extra_items.append(item)

    # ═══════════════════════════════════════════════════
    # التأمينات — مصدر واحد بس (من الأخص للأعم) عشان مايتخصمش مرتين:
    #   1) خصم تأمين مسجل على الموظف نفسه
    #   2) سياسة التأمينات (CompanyInsurancePolicy)
    #   3) خصم عام بنوع تأمين (CompanyDeductionPolicy)
    #   4) إعدادات الرواتب (insurance_mode) للموظف المؤمن عليه
    # ═══════════════════════════════════════════════════
    social_insurance_employee = 0.0
    social_insurance_company = 0.0
    medical_insurance_employee = 0.0
    medical_insurance_company = 0.0

    try:
        from attendance.company_policy_models import CompanyInsurancePolicy
        insurance_policies = CompanyInsurancePolicy._base_manager.filter(
            company=company,
            is_active=True,
            start_date__lte=last_day,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=last_day)
        )
        for policy in pick_effective_insurance_policies(insurance_policies, employee):
            calc = policy.calculate_deduction(employee)
            if policy.insurance_type == 'social':
                social_insurance_employee += float(calc['employee_share'])
                social_insurance_company += float(calc['company_share'])
            elif policy.insurance_type == 'medical':
                medical_insurance_employee += float(calc['employee_share'])
                medical_insurance_company += float(calc['company_share'])
    except Exception:
        logger.exception("payroll_rules error in insurance policies")

    _policy_insurance = social_insurance_employee + medical_insurance_employee
    _settings_insurance = 0.0
    if has_insurance:
        if insurance_mode == 'fixed':
            _settings_insurance = insurance_fixed_amount
        elif insurance_mode == 'percent':
            _settings_insurance = (basic_salary * insurance_percent) / 100.0

    insurance_items = []
    if deductions['insurance_total'] > 0:
        insurance_deduction = deductions['insurance_total']
        insurance_items = deductions['insurance_items']
        social_insurance_employee = social_insurance_company = 0.0
        medical_insurance_employee = medical_insurance_company = 0.0
    elif _policy_insurance > 0 or social_insurance_company > 0 or medical_insurance_company > 0:
        insurance_deduction = _policy_insurance
    elif general_insurance_total > 0:
        insurance_deduction = general_insurance_total
        insurance_items = general_insurance_items
    else:
        insurance_deduction = _settings_insurance

    social_insurance_employee = round(social_insurance_employee, 2)
    social_insurance_company = round(social_insurance_company, 2)
    medical_insurance_employee = round(medical_insurance_employee, 2)
    medical_insurance_company = round(medical_insurance_company, 2)
    total_company_insurance_contribution = round(social_insurance_company + medical_insurance_company, 2)
    insurance_deduction = round(insurance_deduction, 2)

    # ═══════════════════════════════════════════════════
    # بدلات مركز السياسات (AllowanceRule) — كل نوع بقاعدته
    # ═══════════════════════════════════════════════════
    field_allowance = 0.0
    meal_allowance = 0.0
    transport_allowance = 0.0
    other_rule_allowances = 0.0
    rule_allowance_items = []
    ps = None  # للحفاظ على compatibility مع الكود اللاحق

    _is_field_worker = (
        getattr(employee, 'worker_type', None) in ('field_free', 'field_assigned')
        or bool(getattr(employee, 'is_field_worker', False))
    )

    def _visits_count():
        """
        الزيارات اللي بتتحسب في بدل الزيارة: اللي خلصت فعلاً (ليها وقت مغادرة ومش ملغية)
        ومدتها 5 دقايق على الأقل، والزيارات المتكررة لنفس المكان في نفس اليوم بتتحسب مرة واحدة.
        """
        try:
            from attendance.models import LocationCheckIn
            visits = LocationCheckIn._base_manager.filter(
                employee=employee,
                arrival_time__date__gte=first_day,
                arrival_time__date__lte=last_day,
                departure_time__isnull=False,
            ).exclude(status='cancelled').values_list(
                'arrival_time', 'departure_time', 'arrival_latitude', 'arrival_longitude', 'location_name')
            seen = set()
            for arr, dep, lat, lng, name in visits:
                if (dep - arr).total_seconds() < 5 * 60:
                    continue
                if lat is not None and lng is not None:
                    place = (round(float(lat), 3), round(float(lng), 3))   # ~100 متر
                else:
                    place = (name or '').strip().lower()
                seen.add((timezone.localtime(arr).date(), place))
            return len(seen)
        except Exception:
            logger.exception('payroll_rules error in _visits_count')
            return 0

    def _worked_days(min_hours=0):
        n = 0
        for _dd in daily_details:
            worked = _dd.get('status') == 'mission_day' or (
                _dd.get('check_in') and _dd.get('effective_status') in ('present', 'late')
            )
            if not worked:
                continue
            if min_hours and _dd.get('status') != 'mission_day' and float(_dd.get('work_hours', 0) or 0) < min_hours:
                continue
            n += 1
        return n

    for _atype, _rules in allowance_rules.items():
        _rule = _rule_for_day(_rules, emp_end) or _rules[0]
        if _atype == 'field_work' and not _is_field_worker:
            continue
        _ct = _rule.calculation_type
        _val = float(_rule.fixed_amount or 0)
        if _ct == 'fixed_monthly':
            _amt = _val
        elif _ct == 'per_day':
            _amt = _worked_days(int(_rule.min_work_hours_per_day or 0)) * _val
        elif _ct == 'per_visit':
            _amt = _visits_count() * _val
        elif _ct == 'tiered':
            _tier = _match_tier(_rule.tiers, _worked_days(int(_rule.min_work_hours_per_day or 0)))
            _amt = float(_tier.get('value', 0) or 0) if _tier else 0.0
        else:
            _amt = 0.0  # per_km: مفيش بيانات مسافات
        _amt = round(_amt, 2)
        if _amt <= 0:
            continue
        if _atype == 'field_work':
            field_allowance += _amt
        elif _atype == 'meals':
            meal_allowance += _amt
        elif _atype == 'transport':
            transport_allowance += _amt
        else:
            other_rule_allowances += _amt
        rule_allowance_items.append({
            'type': _atype,
            'name': _rule.name,
            'name_ar': _rule.name,
            'name_en': _rule.name,
            'amount': _amt,
            'calculation_type': _ct,
            'source': 'allowance_rule',
        })

    # بدل الميدان من إعدادات الرواتب لو مفيش قاعدة بدل ميدان
    if 'field_work' not in allowance_rules:
        try:
            from attendance.payroll_settings_model import PayrollSettings
            ps = PayrollSettings._base_manager.filter(company=company).first()
            if ps and _is_field_worker:
                if ps.field_allowance_type == 'fixed':
                    field_allowance = float(ps.fixed_field_allowance or 0)
                elif ps.field_allowance_type == 'per_visit':
                    field_allowance = _visits_count() * float(ps.per_visit_allowance or 0)
        except Exception:
            logger.exception("payroll_rules error in settings field allowance")

    field_allowance = round(field_allowance, 2)
    meal_allowance = round(meal_allowance, 2)
    transport_allowance = round(transport_allowance, 2)
    other_rule_allowances = round(other_rule_allowances, 2)
    rule_allowances_total = round(field_allowance + meal_allowance + transport_allowance + other_rule_allowances, 2)

    installments_total = round(deductions['installments_total'] + installments_total_new + general_installments_total, 2)
    penalties_total = round(deductions['penalties_total'] + penalties_total_new, 2)
    extra_deductions_total = round(deductions['extra_total'] + general_extra_total, 2)

    gross_salary = round(
        basic_salary + allowances_total + overtime_bonus + bonuses_total
        + night_allowance + weekend_allowance + rule_allowances_total, 2
    )

    # ═══ الأيام اللي مالهاش أي علاقة شغل ═══
    try:
        _period_upper = min(emp_end, date.today())
        _total_period_days = max(0, (_period_upper - emp_start).days + 1)
        weekend_days = max(0, _total_period_days - len(working_dates))
    except Exception:
        weekend_days = 0

    # استثناء: لو الموظف صفر حضور وصفر إجازات طول الفترة بالكامل (مفيش أي علاقة شغل حقيقية)،
    # الجمعة والسبت كمان بتتخصم (بدل ما تفضل مدفوعة مجانًا)
    _had_real_engagement = (present_days + late_days + mission_days + on_leave_days) > 0
    _weekend_extra_deduction = 0.0
    if not _exempt and not _had_real_engagement and weekend_days > 0:
        # الويكند بيتخصم بنفس سعر يوم الغياب الفعلي (لو قاعدة الغياب إنذار بس أو نص يوم، الويكند زيها)
        if absent_days > 0:
            _weekend_rate = min(absence_deduction / absent_days, daily_salary)
        else:
            _weekend_rate = daily_salary
        _weekend_extra_deduction = round(weekend_days * max(_weekend_rate, 0), 2)
        absence_deduction = round(absence_deduction + _weekend_extra_deduction, 2)
        attended_days = present_days + late_days + mission_days + on_leave_days
    else:
        attended_days = present_days + late_days + mission_days + on_leave_days + weekend_days

    # ═══════════════════════════════════════════════════
    # الضرايب — على المرتب المستحق فعلاً (الإجمالي بعد خصومات الحضور)
    # ═══════════════════════════════════════════════════
    _attendance_deductions = (
        late_deduction + absence_deduction + early_leave_deduction + unpaid_leave_deduction
        + flex_shortage_deduction + missing_checkout_deduction + not_employed_deduction
    )
    tax_deduction = 0.0
    try:
        from attendance.company_policy_models import TaxPolicy
        # بالتاريخ مش بـ is_superseded: النسخة القديمة بتفضل سارية لآخر الشهر اللي اتعدلت فيه
        _tax_policies = TaxPolicy._base_manager.filter(
            company=company,
            is_active=True,
            start_date__lte=last_day,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=last_day)
        ).order_by('-version_number', '-created_at')
        tax_policy = next((t for t in _tax_policies if t.applies_to_employee(employee)), None)

        if tax_policy:
            marital_status = getattr(employee, 'marital_status', 'single') or 'single'
            if marital_status not in ('single', 'married'):
                marital_status = 'single'

            taxable_monthly = max(0.0, gross_salary - _attendance_deductions)
            if getattr(tax_policy, 'exempt_social_insurance', True):
                taxable_monthly -= (insurance_deduction - medical_insurance_employee)
            if getattr(tax_policy, 'exempt_medical_insurance', True):
                taxable_monthly -= medical_insurance_employee

            tax_result = tax_policy.calculate_annual_tax(
                annual_income=max(0.0, taxable_monthly) * 12,
                marital_status=marital_status,
            )
            tax_deduction = float(tax_result.get('annual_tax', 0)) / 12
    except Exception:
        logger.exception("payroll_rules error in tax")
        tax_deduction = 0.0
    tax_deduction = round(tax_deduction, 2)

    total_deductions = round(
        late_deduction
        + absence_deduction
        + insurance_deduction
        + tax_deduction
        + installments_total
        + penalties_total
        + extra_deductions_total
        + flex_shortage_deduction
        + early_leave_deduction
        + unpaid_leave_deduction
        + missing_checkout_deduction
        + not_employed_deduction,
        2
    )

    net_salary = round(gross_salary - total_deductions, 2)

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
        'field_allowance': round(field_allowance, 2),
        'meal_allowance': round(meal_allowance, 2),
        'transport_allowance': round(transport_allowance, 2),
        'other_rule_allowances': other_rule_allowances,
        'rule_allowances_total': rule_allowances_total,
        'rule_allowance_items': rule_allowance_items,
        'field_allowance_type': getattr(ps, 'field_allowance_type', 'none') if ps else 'none',
        'policy_name': active_policy.name if active_policy else None,
        'flex_shortage_deduction': round(flex_shortage_deduction, 2),
        'early_leave_deduction': round(early_leave_deduction, 2),
        'unpaid_leave_deduction': round(unpaid_leave_deduction, 2),
        'missing_checkout_deduction': missing_checkout_deduction,
        'not_employed_days': not_employed_days,
        'not_employed_deduction': not_employed_deduction,
        'late_deduction': round(late_deduction, 2),
        'absence_deduction': round(absence_deduction, 2),
        'insurance_deduction': round(insurance_deduction, 2),
        'tax_deduction': round(tax_deduction, 2),
        # ═══ New insurance system ═══
        'social_insurance_employee': social_insurance_employee,
        'social_insurance_company': social_insurance_company,
        'medical_insurance_employee': medical_insurance_employee,
        'medical_insurance_company': medical_insurance_company,
        'total_company_insurance_contribution': total_company_insurance_contribution,
        'installments_total': round(installments_total, 2),
        'penalties_total': round(penalties_total, 2),
        'extra_deductions_total': round(extra_deductions_total, 2),
        'general_deductions_total': round(general_deductions_total, 2),
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
        'approved_late_minutes': approved_late_minutes,
        'approved_early_minutes': approved_early_minutes,
        'total_early_leave_minutes': total_early_leave_minutes,
        'total_work_hours': round(total_work_hours, 2),
        'overtime_hours': round(total_overtime_hours, 2),
        'missing_checkout_days_count': missing_checkout_days_count,
        'night_shift_days': night_shift_days,
        'weekend_work_days': weekend_work_days,

        'allowance_items': allowance_items,
        'bonus_items': bonus_items,
        'insurance_items': insurance_items,
        'installment_items': deductions['installment_items'] + general_installment_items + installment_items_new,
        'penalty_items': deductions['penalty_items'] + penalty_items_new,
        'extra_deduction_items': deductions['extra_items'] + general_extra_items,
        'general_deduction_items': general_deduction_items,
        'legacy_deduction_items': deductions['legacy_items'],

        'daily_details': daily_details,
    }


# ═══════════════════════════════════════════════════════════════
# Late Warning System
# ═══════════════════════════════════════════════════════════════
def get_late_warning_info(employee, target_date, late_minutes):
    """
    ترجع معلومات الإنذار للموظف بناءً على عدد مرات التأخير في الشهر

    Args:
        employee: الموظف
        target_date: تاريخ التأخير
        late_minutes: عدد دقائق التأخير (محسوبة بعد فترة السماح)

    Returns:
        dict: {
            'warning_level': 0-2,    # 0 = عادي, 1 = إنذار أول, 2 = إنذار ثاني
            'late_count': int,       # عدد مرات التأخير في الشهر
            'message': str,          # رسالة عربية
            'deduction_days': float, # عدد أيام الخصم
        }
        or None في حالة الخطأ
    """
    try:
        from attendance.models import Attendance
        from attendance.company_policy_models import PenaltyRule

        company = getattr(employee, 'company', None)
        if not company:
            return None

        # الشهر الحالي
        if isinstance(target_date, str):
            from datetime import datetime
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        month_start = target_date.replace(day=1)

        # عدد مرات التأخير في الشهر (بما فيها الحالية)
        late_count = Attendance._base_manager.filter(
            employee=employee,
            date__gte=month_start,
            date__lte=target_date,
            late_minutes__gt=0,
        ).count()

        # نجيب الـ PenaltyRule للشركة
        rule = PenaltyRule._base_manager.filter(
            company=company,
            warnings_enabled=True,
            is_active=True,
        ).first()

        # الحالة الافتراضية (بدون rule)
        if not rule:
            return {
                'warning_level': 0,
                'late_count': late_count,
                'message': f'عدد مرات التأخير هذا الشهر: {late_count}',
                'deduction_days': 0,
            }

        # تحديد مستوى الإنذار
        warning_level = 0
        deduction_days = 0
        message = f'عدد مرات التأخير هذا الشهر: {late_count}'

        if rule.second_warning_after and late_count >= rule.second_warning_after:
            warning_level = 2
            message = f'إنذار ثاني - وصل التأخير إلى {late_count} مرات في الشهر'
        elif rule.first_warning_after and late_count >= rule.first_warning_after:
            warning_level = 1
            message = f'إنذار أول - وصل التأخير إلى {late_count} مرات في الشهر'

        return {
            'warning_level': warning_level,
            'late_count': late_count,
            'message': message,
            'deduction_days': deduction_days,
        }
    except Exception:
        return None
