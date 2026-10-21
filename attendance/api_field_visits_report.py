"""
تقرير الزيارات الميدانية (للـ HR وصاحب الشركة والمدير على فريقه)
──────────────────────────────────────────────────────────────
كل زيارة: الموظف، النوع، المكان، وقت الوصول والمغادرة، المدة، العنوان والإحداثيات،
والمسافة بين مكان الوصول والمغادرة، وعدد نقاط التتبع خلال الزيارة.
وتفاصيل زيارة واحدة فيها كل نقاط التتبع (خط السير جوه الزيارة).

مابيضيفش أي جداول جديدة؛ بيقرا من LocationCheckIn و LocationLog الموجودين.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from attendance.models import LocationCheckIn, LocationLog
from employees.models import Employee

ALLOWED_ROLES = ('super_admin', 'company_admin', 'hr_manager', 'manager')


def _visible_employee_ids(user):
    """None = كل موظفي الشركة، وإلا IDs فريق المدير (نفس نطاق القرارات)"""
    from attendance.action_scope import actionable_employee_ids, is_full_access
    if user.is_superuser or is_full_access(user):
        return None
    return actionable_employee_ids(user) or set()


def _company(user):
    company = getattr(user, 'company', None)
    if company:
        return company
    emp = Employee._base_manager.filter(user=user).select_related('company').first()
    return emp.company if emp else None


def _parse_date(value, default):
    try:
        return datetime.strptime(str(value), '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return default


def _local(dt):
    return timezone.localtime(dt) if dt else None


def _maps_link(lat, lng):
    if lat is None or lng is None:
        return ''
    return f'https://maps.google.com/?q={float(lat)},{float(lng)}'


def _employee_name(emp):
    name = ' '.join(p for p in [emp.first_name_ar or '', emp.last_name_ar or ''] if p).strip()
    return name or ' '.join(p for p in [emp.first_name_en or '', emp.last_name_en or ''] if p).strip() or emp.employee_code or ''


def _visit_row(v, now, points_count):
    from attendance.location_utils import haversine_distance
    arrival, departure = _local(v.arrival_time), _local(v.departure_time)
    ongoing = v.status in ('arrived', 'in_progress') and not v.departure_time
    end = v.departure_time or (now if ongoing else None)
    minutes = int((end - v.arrival_time).total_seconds() // 60) if (end and v.arrival_time) else None
    distance_m = None
    if v.departure_latitude is not None and v.arrival_latitude is not None:
        try:
            distance_m = int(round(haversine_distance(v.arrival_latitude, v.arrival_longitude,
                                                      v.departure_latitude, v.departure_longitude) * 1000))
        except Exception:
            distance_m = None
    emp = v.employee
    return {
        'id': v.id,
        'employee_id': emp.id,
        'employee_name': _employee_name(emp),
        'employee_code': emp.employee_code or '',
        'department': getattr(emp.department, 'name_ar', '') if emp.department_id else '',
        'branch': getattr(emp.branch, 'name_ar', '') if emp.branch_id else '',
        'visit_type': v.visit_type,
        'visit_type_display': v.get_visit_type_display(),
        'location_name': v.location_name or '',
        'purpose': v.purpose or '',
        'notes': v.notes or '',
        'status': v.status,
        'status_display': v.get_status_display(),
        'is_ongoing': ongoing,
        'date': arrival.date().isoformat() if arrival else None,
        'arrival_time': arrival.strftime('%H:%M') if arrival else None,
        'arrival_at': arrival.isoformat() if arrival else None,
        'arrival_address': v.arrival_address or '',
        'arrival_latitude': float(v.arrival_latitude) if v.arrival_latitude is not None else None,
        'arrival_longitude': float(v.arrival_longitude) if v.arrival_longitude is not None else None,
        'arrival_map': _maps_link(v.arrival_latitude, v.arrival_longitude),
        'departure_time': departure.strftime('%H:%M') if departure else None,
        'departure_at': departure.isoformat() if departure else None,
        'departure_latitude': float(v.departure_latitude) if v.departure_latitude is not None else None,
        'departure_longitude': float(v.departure_longitude) if v.departure_longitude is not None else None,
        'departure_map': _maps_link(v.departure_latitude, v.departure_longitude),
        'duration_minutes': minutes,
        'distance_arrival_departure_m': distance_m,
        'tracking_points': points_count,
        'has_photo': bool(getattr(v, 'photo', None)),
    }


def _duration_text(minutes):
    if minutes is None:
        return ''
    return f'{minutes // 60} س {minutes % 60} د'


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visits_report(request):
    """
    GET /attendance/api/mobile/manager/reports/field-visits/
      ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&employee_id=&status=&visit_type=&export=xlsx|pdf
    """
    user = request.user
    if not (user.is_superuser or getattr(user, 'role', '') in ALLOWED_ROLES):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    company = _company(user)
    if not company:
        return Response({'success': False, 'message': 'لا توجد شركة'}, status=400)

    today = timezone.localdate()
    date_from = _parse_date(request.GET.get('date_from'), today.replace(day=1))
    date_to = _parse_date(request.GET.get('date_to'), today)
    if date_to < date_from:
        date_from, date_to = date_to, date_from
    if (date_to - date_from).days > 366:
        return Response({'success': False, 'message': 'الفترة لازم تكون سنة أو أقل'}, status=400)

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(date_from, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(date_to + timedelta(days=1), time.min), tz)

    qs = LocationCheckIn._base_manager.filter(
        employee__company=company, arrival_time__gte=start_dt, arrival_time__lt=end_dt,
    ).select_related('employee', 'employee__department', 'employee__branch').order_by('-arrival_time')

    visible = _visible_employee_ids(user)
    if visible is not None:
        qs = qs.filter(employee_id__in=visible)
    emp_id = request.GET.get('employee_id')
    if emp_id and str(emp_id).isdigit():
        qs = qs.filter(employee_id=int(emp_id))
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    if request.GET.get('visit_type'):
        qs = qs.filter(visit_type=request.GET['visit_type'])

    visits = list(qs[:5000])
    now = timezone.now()

    # عدد نقاط التتبع خلال كل زيارة (استعلام واحد لكل موظف بدل واحد لكل زيارة)
    counts = {}
    by_emp = {}
    for v in visits:
        by_emp.setdefault(v.employee_id, []).append(v)
    for eid, vs in by_emp.items():
        lo = min(v.arrival_time for v in vs)
        hi = max((v.departure_time or now) for v in vs)
        stamps = list(LocationLog._base_manager.filter(
            employee_id=eid, timestamp__gte=lo, timestamp__lte=hi,
        ).values_list('timestamp', flat=True))
        for v in vs:
            end = v.departure_time or now
            counts[v.id] = sum(1 for t in stamps if v.arrival_time <= t <= end)

    rows = [_visit_row(v, now, counts.get(v.id, 0)) for v in visits]

    # ملخص لكل موظف
    summary = {}
    for r in rows:
        s = summary.setdefault(r['employee_id'], {
            'employee_id': r['employee_id'], 'employee_name': r['employee_name'],
            'employee_code': r['employee_code'], 'visits': 0, 'completed': 0, 'ongoing': 0, 'total_minutes': 0,
        })
        s['visits'] += 1
        s['completed'] += 1 if r['status'] == 'completed' else 0
        s['ongoing'] += 1 if r['is_ongoing'] else 0
        s['total_minutes'] += r['duration_minutes'] or 0
    per_employee = sorted(summary.values(), key=lambda s: -s['total_minutes'])
    for s in per_employee:
        s['avg_minutes'] = int(s['total_minutes'] / s['visits']) if s['visits'] else 0

    fmt = (request.GET.get('export') or '').lower()   # (format محجوز في DRF)
    if fmt in ('xlsx', 'excel', 'pdf'):
        from attendance.report_export_helper import export_to_excel, export_to_pdf
        columns = [
            ('date', 'التاريخ', 12), ('employee_name', 'الموظف', 22), ('employee_code', 'الكود', 10),
            ('visit_type_display', 'النوع', 14), ('location_name', 'المكان', 22),
            ('arrival_time', 'الوصول', 9), ('departure_time', 'المغادرة', 9), ('duration', 'المدة', 11),
            ('status_display', 'الحالة', 11), ('arrival_address', 'عنوان الوصول', 30),
            ('distance', 'المسافة بين الوصول والمغادرة', 14), ('tracking_points', 'نقاط التتبع', 10),
            ('purpose', 'الغرض', 24), ('notes', 'ملاحظات', 24), ('arrival_map', 'خريطة الوصول', 30),
            ('departure_map', 'خريطة المغادرة', 30),
        ]
        out = []
        for r in rows:
            out.append({**r,
                        'duration': _duration_text(r['duration_minutes']) + (' (لسه جارية)' if r['is_ongoing'] else ''),
                        'departure_time': r['departure_time'] or '—',
                        'distance': f"{r['distance_arrival_departure_m']} م" if r['distance_arrival_departure_m'] is not None else ''})
        subtitle = f'من {date_from.isoformat()} إلى {date_to.isoformat()}'
        if fmt == 'pdf':
            pdf_cols = [c for c in columns if c[0] in (
                'date', 'employee_name', 'visit_type_display', 'location_name', 'arrival_time',
                'departure_time', 'duration', 'status_display', 'arrival_address')]
            return export_to_pdf('تقرير الزيارات الميدانية', pdf_cols, out, user,
                                 filename=f'field_visits_{date_from}_{date_to}.pdf', subtitle=subtitle)
        return export_to_excel('تقرير الزيارات الميدانية', columns, out, user,
                               filename=f'field_visits_{date_from}_{date_to}.xlsx', subtitle=subtitle)

    return Response({
        'success': True,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'total_visits': len(rows),
        'total_minutes': sum(r['duration_minutes'] or 0 for r in rows),
        'ongoing': sum(1 for r in rows if r['is_ongoing']),
        'per_employee': per_employee,
        'visits': rows,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visit_report_detail(request, visit_id):
    """تفاصيل زيارة واحدة: كل البيانات + كل نقاط التتبع اللي اتسجلت خلالها (خط السير)"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'role', '') in ALLOWED_ROLES):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    company = _company(user)
    v = LocationCheckIn._base_manager.filter(id=visit_id, employee__company=company).select_related(
        'employee', 'employee__department', 'employee__branch').first()
    visible = _visible_employee_ids(user)
    if not v or (visible is not None and v.employee_id not in visible):
        return Response({'success': False, 'message': 'الزيارة غير موجودة'}, status=404)

    now = timezone.now()
    end = v.departure_time or now
    points = LocationLog._base_manager.filter(
        employee_id=v.employee_id, timestamp__gte=v.arrival_time, timestamp__lte=end,
    ).order_by('timestamp')
    track = [{
        'time': timezone.localtime(p.timestamp).strftime('%H:%M:%S'),
        'at': timezone.localtime(p.timestamp).isoformat(),
        'latitude': float(p.latitude) if p.latitude is not None else None,
        'longitude': float(p.longitude) if p.longitude is not None else None,
        'accuracy': float(p.accuracy) if getattr(p, 'accuracy', None) is not None else None,
        'address': p.address or '',
    } for p in points[:2000]]
    row = _visit_row(v, now, len(track))
    row['photo_url'] = request.build_absolute_uri(v.photo.url) if getattr(v, 'photo', None) else ''
    return Response({'success': True, 'visit': row, 'tracking': track})
