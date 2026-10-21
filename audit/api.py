"""
تقارير سجل التعديلات:
1) سجل البرنامج كله: مين عمل إيه وإمتى (لصاحب الشركة).
2) سجل موظف: كل اللي اتغير في الموظف ده (المرتب، الاسم، التليفون، ...) قبل وبعد وبالتاريخ واليوزر.
   بيضم كمان السجلات القديمة اللي كانت موجودة قبل السجل الجديد (حركات الموظف وتعديلات الحضور).
"""
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from audit.models import AuditLog

ACTION_AR = dict(AuditLog.ACTIONS)
SOURCE_AR = {'web': 'الموقع', 'mobile': 'الموبايل', 'admin': 'لوحة الأدمن', 'old_site': 'الموقع القديم', 'system': 'النظام'}
OWNER_ROLES = ('super_admin', 'company_admin')
EMPLOYEE_HISTORY_ROLES = ('super_admin', 'company_admin', 'hr_manager')


def _company_id(user):
    cid = getattr(user, 'company_id', None)
    if cid:
        return cid
    from employees.models import Employee
    return Employee._base_manager.filter(user=user).values_list('company_id', flat=True).first()


def _date_range(request, default_days=30):
    today = timezone.localdate()

    def parse(v, d):
        try:
            return datetime.strptime(str(v), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return d
    d_from = parse(request.GET.get('date_from'), today - timedelta(days=default_days))
    d_to = parse(request.GET.get('date_to'), today)
    if d_to < d_from:
        d_from, d_to = d_to, d_from
    tz = timezone.get_current_timezone()
    return d_from, d_to, (timezone.make_aware(datetime.combine(d_from, time.min), tz),
                          timezone.make_aware(datetime.combine(d_to + timedelta(days=1), time.min), tz))


def _row(log):
    at = timezone.localtime(log.created_at)
    return {
        'id': log.id,
        'at': at.isoformat(),
        'date': at.strftime('%Y-%m-%d'),
        'time': at.strftime('%H:%M:%S'),
        'user_id': log.user_id,
        'username': log.username,
        'user_name': log.user_name or log.username or ('النظام' if log.source == 'system' else ''),
        'user_role': log.user_role,
        'action': log.action,
        'action_display': ACTION_AR.get(log.action, log.action),
        'model': log.model,
        'model_label': log.model_label,
        'object_id': log.object_id,
        'object_repr': log.object_repr,
        'employee_id': log.employee_id,
        'employee_name': log.employee_name,
        'changes': log.changes or [],
        'note': log.note,
        'source': log.source,
        'source_display': SOURCE_AR.get(log.source, log.source),
        'ip': log.ip,
    }


def _flat_rows(rows):
    """لكل تغيير في حقل سطر لوحده (عشان ملف الإكسل يبقى واضح: قبل / بعد)"""
    out = []
    for r in rows:
        changes = r['changes'] or [{'label': '', 'old': '', 'new': ''}]
        for c in changes:
            out.append({
                'date': r['date'], 'time': r['time'], 'user': r['user_name'], 'username': r['username'],
                'action': r['action_display'], 'what': r['model_label'], 'object': r['object_repr'],
                'employee': r['employee_name'], 'field': c.get('label', ''), 'old': c.get('old', ''),
                'new': c.get('new', ''), 'source': r['source_display'], 'note': r['note'],
            })
    return out


EXPORT_COLUMNS = [
    ('date', 'التاريخ', 12), ('time', 'الوقت', 10), ('user', 'اتعمل بواسطة', 22), ('username', 'اليوزر', 16),
    ('action', 'العملية', 10), ('what', 'على إيه', 18), ('object', 'العنصر', 24), ('employee', 'الموظف', 22),
    ('field', 'الحقل', 18), ('old', 'قبل', 24), ('new', 'بعد', 24), ('source', 'منين', 12), ('note', 'ملاحظة', 24),
]


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def audit_logs(request):
    """
    سجل البرنامج كله (لصاحب الشركة):
    GET /audit/api/logs/?date_from&date_to&user_id&employee_id&model&action&q&page&page_size&export=xlsx
    """
    user = request.user
    if not (user.is_superuser or getattr(user, 'role', '') in OWNER_ROLES):
        return Response({'success': False, 'message': 'سجل التعديلات لصاحب الشركة بس'}, status=403)
    d_from, d_to, (start, end) = _date_range(request)
    qs = AuditLog.objects.filter(created_at__gte=start, created_at__lt=end)
    if not (user.is_superuser or getattr(user, 'role', '') == 'super_admin'):
        qs = qs.filter(company_id=_company_id(user))
    g = request.GET
    if g.get('user_id', '').isdigit():
        qs = qs.filter(user_id=int(g['user_id']))
    if g.get('employee_id', '').isdigit():
        qs = qs.filter(employee_id=int(g['employee_id']))
    if g.get('model'):
        qs = qs.filter(model=g['model'])
    if g.get('action'):
        qs = qs.filter(action=g['action'])
    if g.get('q'):
        q = g['q'].strip()
        qs = qs.filter(Q(object_repr__icontains=q) | Q(employee_name__icontains=q) | Q(username__icontains=q)
                       | Q(user_name__icontains=q) | Q(note__icontains=q))

    if (g.get('export') or '').lower() in ('xlsx', 'excel'):
        from attendance.report_export_helper import export_to_excel
        rows = [_row(l) for l in qs[:20000]]
        return export_to_excel('سجل التعديلات', EXPORT_COLUMNS, _flat_rows(rows), user,
                               filename=f'audit_{d_from}_{d_to}.xlsx', subtitle=f'من {d_from} إلى {d_to}')

    try:
        page = max(1, int(g.get('page', 1)))
        size = min(500, max(1, int(g.get('page_size', 100))))
    except ValueError:
        page, size = 1, 100
    total = qs.count()
    rows = [_row(l) for l in qs[(page - 1) * size: page * size]]
    return Response({'success': True, 'date_from': d_from.isoformat(), 'date_to': d_to.isoformat(),
                     'total': total, 'page': page, 'page_size': size, 'logs': rows})


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def audit_filters(request):
    """قوايم الفلاتر: اليوزرز اللي ليهم تعديلات، وأنواع الجداول"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'role', '') in EMPLOYEE_HISTORY_ROLES):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    qs = AuditLog.objects.all()
    if not (user.is_superuser or getattr(user, 'role', '') == 'super_admin'):
        qs = qs.filter(company_id=_company_id(user))
    users = list(qs.exclude(user_id=None).values('user_id', 'username', 'user_name').distinct()[:500])
    models = list(qs.values('model', 'model_label').distinct()[:300])
    return Response({'success': True, 'users': users, 'models': models})


def _legacy_entries(emp, start, end):
    """السجلات القديمة اللي كانت بتتسجل قبل سجل التعديلات (عشان التقرير يبقى فيه تاريخ قبل النهارده)"""
    out = []
    from employees.models import EmployeeMovement
    for m in EmployeeMovement._base_manager.filter(employee=emp).order_by('-movement_date')[:500]:
        d = m.movement_date
        if not (start.date() <= d < end.date()):
            continue
        out.append({
            'id': f'mv{m.id}', 'at': datetime.combine(d, time.min).isoformat(), 'date': d.isoformat(), 'time': '',
            'user_id': None, 'username': '', 'user_name': '', 'user_role': '',
            'action': 'update', 'action_display': 'حركة موظف', 'model': 'employees.EmployeeMovement',
            'model_label': 'حركة موظف', 'object_id': str(m.id), 'object_repr': m.get_movement_type_display(),
            'employee_id': emp.id, 'employee_name': '',
            'changes': [{'field': m.movement_type, 'label': m.get_movement_type_display(),
                         'old': m.old_value or '', 'new': m.new_value or ''}],
            'note': m.reason or '', 'source': 'legacy', 'source_display': 'سجل قديم', 'ip': '', 'legacy': True,
        })
    from attendance.models import AttendanceActionLog
    for a in AttendanceActionLog._base_manager.filter(
            attendance__employee=emp, action_at__gte=start, action_at__lt=end).select_related('performed_by', 'attendance')[:500]:
        at = timezone.localtime(a.action_at)
        old, new = a.old_data or {}, a.new_data or {}
        keys = sorted(set(old) | set(new))
        changes = [{'field': k, 'label': k, 'old': str(old.get(k, '')), 'new': str(new.get(k, ''))}
                   for k in keys if str(old.get(k, '')) != str(new.get(k, ''))]
        u = a.performed_by
        out.append({
            'id': f'att{a.id}', 'at': at.isoformat(), 'date': at.strftime('%Y-%m-%d'), 'time': at.strftime('%H:%M:%S'),
            'user_id': getattr(u, 'id', None), 'username': getattr(u, 'username', '') or '',
            'user_name': (u.get_full_name() if u else '') or getattr(u, 'username', '') or '',
            'user_role': getattr(u, 'role', '') or '', 'action': 'update', 'action_display': a.get_action_type_display(),
            'model': 'attendance.Attendance', 'model_label': 'حضور',
            'object_id': str(a.attendance_id), 'object_repr': f'حضور يوم {a.attendance.date}' if a.attendance else '',
            'employee_id': emp.id, 'employee_name': '', 'changes': changes, 'note': a.reason or '',
            'source': 'legacy', 'source_display': 'سجل قديم', 'ip': '', 'legacy': True,
        })
    return out


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_history(request, employee_id):
    """
    كل اللي اتغير في موظف معيّن (لصاحب الشركة والـ HR):
    GET /audit/api/employee/<id>/?date_from&date_to&only_profile=1&export=xlsx
    only_profile=1 → بيانات الموظف وحسابه بس (المرتب، الاسم، التليفون...) من غير الحضور والطلبات
    """
    user = request.user
    if not (user.is_superuser or getattr(user, 'role', '') in EMPLOYEE_HISTORY_ROLES):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    from employees.models import Employee
    emp = Employee._base_manager.filter(id=employee_id).first()
    if not emp or (not user.is_superuser and getattr(user, 'role', '') != 'super_admin'
                   and emp.company_id != _company_id(user)):
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    d_from, d_to, (start, end) = _date_range(request, default_days=3650)
    qs = AuditLog.objects.filter(employee_id=emp.id, created_at__gte=start, created_at__lt=end)
    only_profile = request.GET.get('only_profile') == '1'
    if only_profile:
        qs = qs.filter(model__in=('employees.Employee', 'accounts.User'))
    rows = [_row(l) for l in qs[:5000]]
    if not only_profile:
        rows += _legacy_entries(emp, start, end)
    elif request.GET.get('include_legacy', '1') == '1':
        rows += [r for r in _legacy_entries(emp, start, end) if r['model'] == 'employees.EmployeeMovement']
    rows.sort(key=lambda r: r['at'], reverse=True)
    name = ' '.join(p for p in [emp.first_name_ar or '', emp.middle_name_ar or '', emp.last_name_ar or ''] if p)
    for r in rows:
        r['employee_name'] = r['employee_name'] or name

    if (request.GET.get('export') or '').lower() in ('xlsx', 'excel'):
        from attendance.report_export_helper import export_to_excel
        return export_to_excel(f'سجل تعديلات الموظف - {name}', EXPORT_COLUMNS, _flat_rows(rows), user,
                               filename=f'employee_{emp.id}_history.xlsx', subtitle=f'من {d_from} إلى {d_to}')

    return Response({'success': True, 'employee': {'id': emp.id, 'name': name, 'code': emp.employee_code},
                     'date_from': d_from.isoformat(), 'date_to': d_to.isoformat(),
                     'total': len(rows), 'history': rows})
