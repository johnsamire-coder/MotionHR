"""
leave_dates.py
تعديل تواريخ طلب إجازة لسه "قيد الانتظار": نفس فحوصات تقديم الطلب، وعدد الأيام والرصيد المعلق بيتعدلوا بالفرق.
"""
from datetime import date, datetime
from decimal import Decimal


class LeaveDateError(Exception):
    pass


def parse_date(value, default):
    if value in (None, ''):
        return default
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip()[:10], '%Y-%m-%d').date()
    except ValueError:
        raise LeaveDateError('صيغة التاريخ غلط. استخدم YYYY-MM-DD')


def reschedule_pending_leave(leave, start_value, end_value):
    """
    بتغيّر التواريخ وعدد الأيام وبتعدّل الرصيد المعلق. بترفع LeaveDateError برسالة واضحة لو مينفعش.
    بترجع True لو التواريخ اتغيرت فعلاً.
    """
    from attendance.models import Attendance
    from leaves.models import LeaveBalance, LeaveRequest

    if leave.status != 'pending':
        raise LeaveDateError('الإجازة دي مش "قيد الانتظار". لو عايز تغيّر تواريخها الغيها واعمل طلب جديد.')

    new_start = parse_date(start_value, leave.start_date)
    new_end = parse_date(end_value, leave.end_date)
    if new_end < new_start:
        raise LeaveDateError('تاريخ النهاية لازم يكون بعد تاريخ البداية')
    if new_start == leave.start_date and new_end == leave.end_date:
        return False
    if new_start.year != leave.start_date.year:
        raise LeaveDateError('مينفعش تنقل الإجازة لسنة تانية. الغيها واعمل طلب جديد.')

    if LeaveRequest._base_manager.filter(
        company=leave.company, employee=leave.employee, status__in=['pending', 'approved'],
        start_date__lte=new_end, end_date__gte=new_start,
    ).exclude(pk=leave.pk).exists():
        raise LeaveDateError('عندك إجازة موجودة بالفعل في نفس الفترة دي')

    conflict = list(Attendance._base_manager.filter(
        employee=leave.employee, date__gte=new_start, date__lte=new_end, check_in_time__isnull=False,
    ).values_list('date', flat=True))
    if conflict:
        raise LeaveDateError('لا يمكن تعديل الإجازة - يوجد حضور مسجل في: ' + ', '.join(d.isoformat() for d in conflict))

    # نفس طريقة العد وقت تقديم الطلب
    half_day = bool(leave.half_day_type) and new_start == new_end
    new_days = Decimal('0.5') if half_day else Decimal((new_end - new_start).days + 1)
    old_days = Decimal(str(leave.days_count or 0))
    delta = new_days - old_days

    if delta > 0 and leave.leave_type and leave.leave_type.is_paid:
        bal = LeaveBalance._base_manager.filter(
            company=leave.company, employee=leave.employee, leave_type=leave.leave_type, year=new_start.year,
        ).first()
        remaining = Decimal(str(bal.remaining_days)) if bal else Decimal('0')
        if delta > remaining:
            raise LeaveDateError(
                f'رصيدك من {leave.leave_type.name} غير كافي. المتاح: {remaining} يوم، الزيادة المطلوبة: {delta} يوم')

    leave.start_date, leave.end_date, leave.days_count = new_start, new_end, new_days
    if not half_day:
        leave.half_day_type = ''
        leave.leave_hours = None
    leave.save()
    if delta:
        leave._update_balance('add_pending', days=delta)
    return True
