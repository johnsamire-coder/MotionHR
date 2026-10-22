"""
إدارة أجهزة البصمة (لصاحب الشركة والـ HR):
- الأجهزة: تسجيل جهاز برقمه التسلسلي، تفعيل/إيقاف، الفرع والاسم
- الربط: رقم الموظف على الجهاز ↔ الموظف في البرنامج
- رفع ملف بصمات (من الفلاشة أو من برنامج الجهاز)
- تقرير البصمات ومقارنتها بحضور الموبايل (المرحلة الأولى: مابيغيرش الحضور)
"""
from datetime import datetime, time, timedelta

from django.db.models import Count, Max, Min, Q
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from biometric.models import BiometricDevice, BiometricPunch, BiometricUserMap
from biometric.services import parse_upload, relink_company, store_punches

MANAGE_ROLES = ('super_admin', 'company_admin', 'hr_manager')
STATUS_AR = {'0': 'حضور', '1': 'انصراف', '2': 'خروج استراحة', '3': 'رجوع استراحة', '4': 'دخول إضافي', '5': 'خروج إضافي'}


def _guard(request):
    u = request.user
    if not (u.is_superuser or getattr(u, 'role', '') in MANAGE_ROLES):
        return None, Response({'success': False, 'message': 'أجهزة البصمة لصاحب الشركة والموارد البشرية'}, status=403)
    cid = getattr(u, 'company_id', None)
    if not cid:
        from employees.models import Employee
        cid = Employee._base_manager.filter(user=u).values_list('company_id', flat=True).first()
    if not cid:
        return None, Response({'success': False, 'message': 'لا توجد شركة'}, status=400)
    return cid, None


def _local(dt):
    return timezone.localtime(dt) if dt else None


def _device_row(d, today_counts):
    now = timezone.now()
    online = bool(d.last_seen and (now - d.last_seen) < timedelta(minutes=10))
    branch = ''
    if d.branch_id:
        from companies.models import Branch
        branch = Branch._base_manager.filter(pk=d.branch_id).values_list('name_ar', flat=True).first() or ''
    return {
        'id': d.id, 'serial_number': d.serial_number, 'name': d.name, 'branch_id': d.branch_id, 'branch': branch,
        'is_active': d.is_active, 'online': online, 'firmware': d.firmware,
        'last_seen': _local(d.last_seen).strftime('%Y-%m-%d %H:%M') if d.last_seen else None,
        'last_upload': _local(d.last_upload).strftime('%Y-%m-%d %H:%M') if d.last_upload else None,
        'last_ip': d.last_ip, 'punches_today': today_counts.get(d.serial_number, 0), 'notes': d.notes,
    }


def _today_counts(cid):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min), tz)
    return dict(BiometricPunch.objects.filter(company_id=cid, punch_time__gte=start)
                .values('device_serial').annotate(n=Count('id')).values_list('device_serial', 'n'))


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def devices(request):
    """GET: أجهزة الشركة. POST: تسجيل جهاز برقمه التسلسلي (لو اتصل قبل كده لوحده بيتربط بالشركة)"""
    cid, err = _guard(request)
    if err:
        return err
    if request.method == 'POST':
        sn = str(request.data.get('serial_number') or '').strip()[:64]
        if len(sn) < 4:
            return Response({'success': False, 'message': 'اكتب الرقم التسلسلي (SN) المكتوب على الجهاز أو في إعداداته'}, status=400)
        dev = BiometricDevice.objects.filter(serial_number=sn).first()
        if dev and dev.company_id and dev.company_id != cid:
            return Response({'success': False, 'message': 'الجهاز ده متسجل في شركة تانية'}, status=400)
        if not dev:
            dev = BiometricDevice(serial_number=sn)
        dev.company_id = cid
        dev.name = str(request.data.get('name') or dev.name or 'جهاز بصمة')[:150]
        dev.branch_id = _branch_id(cid, request.data.get('branch_id'))
        dev.is_active = True
        dev.notes = ''
        dev.save()
        return Response({'success': True, 'message': 'الجهاز اتسجل. أول ما يتصل هيبعت البصمات لوحده.',
                         'device': _device_row(dev, _today_counts(cid))}, status=201)
    counts = _today_counts(cid)
    rows = [_device_row(d, counts) for d in BiometricDevice.objects.filter(company_id=cid)]
    return Response({'success': True, 'devices': rows})


def _branch_id(cid, value):
    if value in (None, '', 'null'):
        return None
    from companies.models import Branch
    try:
        return Branch._base_manager.filter(pk=int(value), company_id=cid).values_list('id', flat=True).first()
    except (TypeError, ValueError):
        return None


@api_view(['PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def device_detail(request, device_id):
    cid, err = _guard(request)
    if err:
        return err
    dev = BiometricDevice.objects.filter(pk=device_id, company_id=cid).first()
    if not dev:
        return Response({'success': False, 'message': 'الجهاز غير موجود'}, status=404)
    if request.method == 'DELETE':
        # بنفك الجهاز من الشركة بس؛ البصمات اللي جت منه بتفضل محفوظة
        dev.company_id = None
        dev.is_active = False
        dev.notes = 'اتشال من الشركة'
        dev.save()
        return Response({'success': True, 'message': 'الجهاز اتشال (البصمات القديمة محفوظة)'})
    d = request.data
    if 'name' in d:
        dev.name = str(d.get('name') or '')[:150]
    if 'branch_id' in d:
        dev.branch_id = _branch_id(cid, d.get('branch_id'))
    if 'is_active' in d:
        dev.is_active = str(d.get('is_active')).lower() in ('1', 'true', 'yes')
    dev.save()
    return Response({'success': True, 'device': _device_row(dev, _today_counts(cid))})


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_map(request):
    """
    GET: كل أرقام الجهاز اللي جت منها بصمات أو اتسجلت على الجهاز، ومين مربوط بيها
    POST: {pin, employee_id|null} ربط رقم بموظف (أو فك الربط)
    """
    cid, err = _guard(request)
    if err:
        return err
    from employees.models import Employee
    if request.method == 'POST':
        pin = str(request.data.get('pin') or '').strip()[:32]
        if not pin:
            return Response({'success': False, 'message': 'رقم الجهاز مطلوب'}, status=400)
        eid = request.data.get('employee_id')
        if eid not in (None, '', 'null'):
            emp = Employee._base_manager.filter(pk=eid, company_id=cid).first()
            if not emp:
                return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
            # الموظف مايتربطش برقمين في نفس الشركة
            BiometricUserMap.objects.filter(company_id=cid, employee_id=emp.id).exclude(pin=pin).update(employee_id=None)
            eid = emp.id
        else:
            eid = None
        m, _ = BiometricUserMap.objects.get_or_create(company_id=cid, pin=pin)
        m.employee_id = eid
        m.updated_by = getattr(request.user, 'username', '')[:150]
        m.save()
        # البصمات القديمة بالرقم ده تتربط (أو تتفك) على طول
        BiometricPunch.objects.filter(company_id=cid, pin=pin).update(employee_id=eid)
        relink_company(cid)
        return Response({'success': True, 'message': 'اتحفظ الربط'})

    stats = {r['pin']: r for r in BiometricPunch.objects.filter(company_id=cid).values('pin').annotate(
        n=Count('id'), last=Max('punch_time'), emp=Max('employee_id'))}
    maps = {m.pin: m for m in BiometricUserMap.objects.filter(company_id=cid)}
    emp_names = {e.id: (' '.join(p for p in [e.first_name_ar or '', e.last_name_ar or ''] if p).strip(), e.employee_code)
                 for e in Employee._base_manager.filter(company_id=cid).only('first_name_ar', 'last_name_ar', 'employee_code')}
    rows = []
    for pin in sorted(set(stats) | set(maps), key=lambda p: (len(p), p)):
        m, s = maps.get(pin), stats.get(pin, {})
        eid = (m.employee_id if m and m.employee_id else None) or s.get('emp')
        name, code = emp_names.get(eid, ('', ''))
        rows.append({
            'pin': pin, 'device_user_name': m.device_user_name if m else '',
            'employee_id': eid, 'employee_name': name, 'employee_code': code,
            'manual': bool(m and m.employee_id), 'punches': s.get('n', 0),
            'last_punch': _local(s['last']).strftime('%Y-%m-%d %H:%M') if s.get('last') else None,
        })
    return Response({'success': True, 'unmatched': sum(1 for r in rows if not r['employee_id']), 'pins': rows})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload(request):
    """رفع ملف بصمات: attlog.dat من الفلاشة، أو txt/csv/xlsx متصدّر من برنامج الجهاز"""
    cid, err = _guard(request)
    if err:
        return err
    f = request.FILES.get('file')
    if not f:
        return Response({'success': False, 'message': 'اختار ملف البصمات'}, status=400)
    if f.size > 20 * 1024 * 1024:
        return Response({'success': False, 'message': 'الملف كبير جداً (الحد 20 ميجا)'}, status=400)
    serial = 'upload'
    dev_id = request.data.get('device_id')
    if dev_id:
        dev = BiometricDevice.objects.filter(pk=dev_id, company_id=cid).first()
        if not dev:
            return Response({'success': False, 'message': 'الجهاز غير موجود'}, status=404)
        serial = dev.serial_number
    try:
        rows = parse_upload(f.name, f.read())
    except Exception:
        rows = []
    if not rows:
        return Response({'success': False, 'message': 'ماعرفتش أقرا بصمات من الملف. ابعت ملف attlog.dat من الفلاشة أو Excel فيه عمود رقم الموظف وعمود الوقت.'}, status=400)
    new, dup, unmatched = store_punches(cid, serial, rows, source='upload')
    return Response({'success': True, 'read': len(rows), 'new': new, 'duplicates': dup, 'unmatched': unmatched,
                     'message': f'اتقرا {len(rows)} بصمة: {new} جديدة و{dup} كانت متسجلة قبل كده'
                                + (f'، و{unmatched} محتاجة ربط بموظف' if unmatched else '')})


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def report(request):
    """
    تقرير البصمات ومقارنتها بحضور الموبايل:
    ?date_from&date_to&employee_id&view=daily|raw&export=xlsx
    daily: لكل موظف ولكل يوم: أول بصمة وآخر بصمة وعددهم، والحضور والانصراف المتسجلين في البرنامج
    raw: كل بصمة لوحدها
    """
    cid, err = _guard(request)
    if err:
        return err
    today = timezone.localdate()

    def pd(v, d):
        try:
            return datetime.strptime(str(v), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return d
    d_from, d_to = pd(request.GET.get('date_from'), today - timedelta(days=6)), pd(request.GET.get('date_to'), today)
    if d_to < d_from:
        d_from, d_to = d_to, d_from
    if (d_to - d_from).days > 92:
        return Response({'success': False, 'message': 'الفترة لازم تكون 3 شهور أو أقل'}, status=400)
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(d_from, time.min), tz)
    end = timezone.make_aware(datetime.combine(d_to + timedelta(days=1), time.min), tz)
    qs = BiometricPunch.objects.filter(company_id=cid, punch_time__gte=start, punch_time__lt=end)
    eid = request.GET.get('employee_id')
    if eid and str(eid).isdigit():
        qs = qs.filter(employee_id=int(eid))

    from employees.models import Employee
    names = {e.id: (' '.join(p for p in [e.first_name_ar or '', e.last_name_ar or ''] if p).strip(), e.employee_code)
             for e in Employee._base_manager.filter(company_id=cid).only('first_name_ar', 'last_name_ar', 'employee_code')}
    devs = dict(BiometricDevice.objects.filter(company_id=cid).values_list('serial_number', 'name'))
    view = request.GET.get('view') or 'daily'

    if view == 'raw':
        rows = []
        for p in qs.order_by('-punch_time')[:5000]:
            t = _local(p.punch_time)
            n, c = names.get(p.employee_id, ('', ''))
            rows.append({'date': t.strftime('%Y-%m-%d'), 'time': t.strftime('%H:%M:%S'), 'pin': p.pin,
                         'employee_id': p.employee_id, 'employee_name': n or '— مش مربوط —', 'employee_code': c,
                         'status': STATUS_AR.get(p.status_code, p.status_code), 'device': devs.get(p.device_serial) or p.device_serial,
                         'source': p.get_source_display()})
        if (request.GET.get('export') or '').lower() in ('xlsx', 'excel'):
            from attendance.report_export_helper import export_to_excel
            cols = [('date', 'التاريخ', 12), ('time', 'الوقت', 10), ('pin', 'رقم الجهاز', 10), ('employee_name', 'الموظف', 24),
                    ('employee_code', 'الكود', 10), ('status', 'النوع', 12), ('device', 'الجهاز', 18), ('source', 'المصدر', 14)]
            return export_to_excel('بصمات الأجهزة', cols, rows, request.user, filename=f'punches_{d_from}_{d_to}.xlsx',
                                   subtitle=f'من {d_from} إلى {d_to}')
        return Response({'success': True, 'view': 'raw', 'punches': rows})

    # daily: أول وآخر بصمة لكل موظف في اليوم + المقارنة بالحضور المتسجل
    days = {}
    for p in qs.exclude(employee_id=None).only('employee_id', 'punch_time'):
        t = _local(p.punch_time)
        k = (p.employee_id, t.date())
        d = days.setdefault(k, {'first': t, 'last': t, 'n': 0})
        d['first'] = min(d['first'], t)
        d['last'] = max(d['last'], t)
        d['n'] += 1
    from attendance.models import Attendance
    att = {}
    if days:
        for a in Attendance._base_manager.filter(employee_id__in={k[0] for k in days}, date__gte=d_from, date__lte=d_to):
            att[(a.employee_id, a.date)] = a
    rows = []
    for (emp_id, day), d in sorted(days.items(), key=lambda x: (x[0][1], names.get(x[0][0], ('',))[0]), reverse=True):
        a = att.get((emp_id, day))
        ci, co = _local(getattr(a, 'check_in_time', None)), _local(getattr(a, 'check_out_time', None))
        diff_in = int((d['first'] - ci).total_seconds() // 60) if ci else None
        n, c = names.get(emp_id, ('', ''))
        rows.append({
            'date': day.isoformat(), 'employee_id': emp_id, 'employee_name': n, 'employee_code': c,
            'first_punch': d['first'].strftime('%H:%M'), 'last_punch': d['last'].strftime('%H:%M') if d['n'] > 1 else '',
            'punches': d['n'],
            'system_check_in': ci.strftime('%H:%M') if ci else '', 'system_check_out': co.strftime('%H:%M') if co else '',
            'system_status': getattr(a, 'get_status_display', lambda: '')() if a else 'مفيش حضور متسجل',
            'diff_in_minutes': diff_in,
        })
    if (request.GET.get('export') or '').lower() in ('xlsx', 'excel'):
        from attendance.report_export_helper import export_to_excel
        cols = [('date', 'التاريخ', 12), ('employee_name', 'الموظف', 24), ('employee_code', 'الكود', 10),
                ('first_punch', 'أول بصمة', 10), ('last_punch', 'آخر بصمة', 10), ('punches', 'عدد البصمات', 10),
                ('system_check_in', 'حضور البرنامج', 12), ('system_check_out', 'انصراف البرنامج', 12),
                ('system_status', 'الحالة في البرنامج', 16)]
        return export_to_excel('مقارنة البصمة بالحضور', cols, rows, request.user, filename=f'biometric_{d_from}_{d_to}.xlsx',
                               subtitle=f'من {d_from} إلى {d_to}')
    unmatched = BiometricPunch.objects.filter(company_id=cid, employee_id=None, punch_time__gte=start, punch_time__lt=end).count()
    return Response({'success': True, 'view': 'daily', 'date_from': d_from.isoformat(), 'date_to': d_to.isoformat(),
                     'unmatched_punches': unmatched, 'days': rows})
