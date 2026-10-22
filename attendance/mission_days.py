from datetime import timedelta

from django.utils import timezone

# حالات تعيين المهمة اللي بتعفي الموظف من الغياب
COUNTED_ASSIGNMENT_STATUSES = ('accepted', 'in_progress', 'completed')
MAX_SPAN_DAYS = 62


def employee_mission_dates(employee, start_date, end_date):
    """الأيام (بين start_date و end_date) اللي الموظف فيها على مهمة مقبولة أو جارية أو مكتملة."""
    from attendance.missions_models import MissionAssignment

    days = set()
    assignments = MissionAssignment._base_manager.filter(
        employee=employee,
        status__in=COUNTED_ASSIGNMENT_STATUSES,
    ).select_related('mission')
    for a in assignments:
        m = a.mission
        if not m or not m.planned_start_time:
            continue
        s = timezone.localtime(m.planned_start_time).date()
        e = timezone.localtime(m.planned_end_time).date() if m.planned_end_time else s
        if e < s:
            e = s
        e = min(e, s + timedelta(days=MAX_SPAN_DAYS))
        d = max(s, start_date)
        last = min(e, end_date)
        while d <= last:
            days.add(d)
            d += timedelta(days=1)
    return days
