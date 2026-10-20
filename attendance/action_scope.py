"""
action_scope.py
مين يقدر ينفّذ إجراء (موافقة/رفض/تعديل/إلغاء/منح) على موظف معيّن.

نفس الناس اللي بيظهروا في قايمة "الطلبات المعلقة" عنده:
- السوبر أدمن: الكل
- صاحب الشركة والـ HR: موظفين شركتهم بس
- المدير: فريقه (بالتسلسل) + فريق المدير اللي هو بديله مؤقتاً
- غير كده: ولا حد

ومحدش يوافق على طلبه هو، إلا صاحب الشركة والسوبر أدمن.
"""
from django.utils import timezone
from rest_framework.response import Response

FULL_ACCESS_ROLES = ('company_admin', 'hr_manager')
SELF_APPROVE_ROLES = ('company_admin', 'super_admin')

NOT_FOUND_MSG = 'الطلب غير موجود'
SELF_ACTION_MSG = 'مينفعش تنفّذ الإجراء ده على طلبك أنت. لازم حد أعلى منك يعمله.'


def _is_super(user):
    return bool(getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'super_admin')


def _user_company_id(user):
    cid = getattr(user, 'company_id', None)
    if cid:
        return cid
    from employees.models import Employee
    return Employee._base_manager.filter(user_id=user.pk).values_list('company_id', flat=True).first()


def actionable_employee_ids(user):
    """None = الكل (سوبر أدمن)، وإلا set بأرقام الموظفين"""
    if _is_super(user):
        return None
    from employees.models import Employee
    role = getattr(user, 'role', '') or ''
    company_id = _user_company_id(user)
    if not company_id:
        return set()
    if role in FULL_ACCESS_ROLES:
        return set(Employee._base_manager.filter(company_id=company_id).values_list('id', flat=True))
    if role != 'manager':
        return set()

    from attendance.api_reports import _get_direct_team_employees
    ids = set(_get_direct_team_employees(user).values_list('id', flat=True))

    # البديل المؤقت بيشوف فريق المدير الغايب (زي قايمة الطلبات المعلقة)
    try:
        from leaves.models import ManagerSubstitution
        me = Employee._base_manager.filter(user=user, company_id=company_id).first()
        if me:
            today = timezone.localdate()
            for sub in ManagerSubstitution._base_manager.filter(
                substitute_employee=me, is_active=True, start_date__lte=today, end_date__gte=today,
            ):
                ids |= set(Employee._base_manager.filter(
                    direct_manager=sub.manager_employee, company_id=company_id, status='active',
                ).values_list('id', flat=True))
    except Exception:
        pass
    return ids


def in_scope(user, employee):
    if employee is None:
        return _is_super(user)
    ids = actionable_employee_ids(user)
    return ids is None or employee.id in ids


def is_self(user, employee):
    return bool(employee is not None and employee.user_id and employee.user_id == user.pk)


def deny_action(user, employee, allow_self=False):
    """
    بترجع Response بالرفض، أو None لو مسموح.
    الطلب اللي بره النطاق بيرجع "غير موجود" (عشان محدش يعرف إنه موجود في شركة تانية).
    """
    if is_self(user, employee):
        if allow_self or _is_super(user) or getattr(user, 'role', '') in SELF_APPROVE_ROLES:
            return None
        return Response({'success': False, 'message': SELF_ACTION_MSG}, status=403)
    if not in_scope(user, employee):
        return Response({'success': False, 'message': NOT_FOUND_MSG}, status=404)
    return None


def mission_employee(mission):
    """الموظف اللي طلب المأمورية"""
    creator = getattr(mission, 'created_by', None)
    if not creator:
        return None
    from employees.models import Employee
    return Employee._base_manager.filter(user=creator).first()


def deny_mission_action(user, mission):
    if _is_super(user):
        return None
    if mission.company_id != _user_company_id(user):
        return Response({'success': False, 'message': NOT_FOUND_MSG}, status=404)
    emp = mission_employee(mission)
    if emp is None:
        # مأمورية من غير موظف طالبها: للإدارة الكاملة في نفس الشركة بس
        if getattr(user, 'role', '') in FULL_ACCESS_ROLES:
            return None
        return Response({'success': False, 'message': NOT_FOUND_MSG}, status=404)
    return deny_action(user, emp)
