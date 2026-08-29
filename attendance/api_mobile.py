from .fcm_logic import notify_managers, notify_employee_checkin, notify_employee_checkout, notify_manager_checkin, notify_manager_checkout, notify_manager_early_leave
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from employees.models import Employee
from attendance.models import Attendance, LocationLog



def reverse_geocode(lat, lng):
    """تحويل الإحداثيات لاسم مكان مقروء (Reverse Geocoding)"""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&accept-language=ar&zoom=16"
        req = urllib.request.Request(url, headers={'User-Agent': 'MotionHR/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get('display_name', '')
    except Exception:
        return ''


def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).first()


def format_time_value(dt):
    if not dt:
        return ''
    try:
        return timezone.localtime(dt).strftime('%I:%M %p')
    except Exception:
        return dt.strftime('%I:%M %p')



def bilingual_message(employee, message_ar, message_en):
    language = getattr(employee, "language", "ar") or "ar"
    return {
        "message": message_en if language == "en" else message_ar,
        "message_ar": message_ar,
        "message_en": message_en,
    }


def get_approved_permission(employee, permission_kind, day):
    from requests_app.models import EmployeeRequest

    return EmployeeRequest._base_manager.select_related(
        "request_type"
    ).filter(
        company=employee.company,
        employee=employee,
        request_type__permission_kind=permission_kind,
        status="approved",
        start_date__lte=day,
        end_date__gte=day,
        duration_hours__gt=0,
        permission_used_at__isnull=True,
    ).order_by("start_date", "id").first()


def consume_permission(permission_request, actual_hours, used_at):
    from decimal import Decimal, ROUND_UP
    from django.db import transaction
    from requests_app.models import EmployeeRequest, PermissionUsage

    hours = Decimal(str(actual_hours))
    requested_hours = permission_request.duration_hours or hours
    hours = min(hours, requested_hours)
    hours = hours.quantize(Decimal("0.1"), rounding=ROUND_UP)

    if hours <= 0:
        return None

    with transaction.atomic():
        locked_request = EmployeeRequest._base_manager.select_for_update().get(
            id=permission_request.id
        )

        if locked_request.permission_used_at:
            return None

        month = timezone.localtime(used_at).strftime("%Y-%m")

        usage, created = PermissionUsage._base_manager.select_for_update().get_or_create(
            company=locked_request.company,
            employee=locked_request.employee,
            month=month,
        )

        usage.used_hours += hours
        usage.used_times += 1
        usage.save(update_fields=["used_hours", "used_times"])

        locked_request.permission_used_at = used_at
        locked_request.actual_used_hours = hours
        locked_request.save(update_fields=[
            "permission_used_at",
            "actual_used_hours",
        ])

    return hours





def _notify_missing_period(employee, period, shift, after_grace=False):
    """
    إشعار الموظف والمدير والـ HR لو الموظف ما حضرش فترة في split_fixed
    after_grace=False → بداية الفترة → للموظف فقط
    after_grace=True  → بعد انتهاء السماحية → للموظف + المدير + HR
    """
    try:
        from accounts.fcm_service import send_notification_to_user, send_notification_to_managers
        from accounts.models import EmployeeNotification

        period_name = period.get('name', 'فترة')
        period_start = period.get('start_str', '')
        period_end = period.get('end_str', '')
        shift_name = shift.name if shift else ''
        emp_name = getattr(employee, 'full_name_ar', '') or str(employee)

        if not after_grace:
            # تذكير للموظف فقط
            title_ar = f'⏰ تذكير: {period_name}'
            body_ar = f'حان وقت {period_name} ({period_start} - {period_end}) من شيفت {shift_name}'
            title_en = f'⏰ Reminder: {period_name}'
            body_en = f'Time for {period_name} ({period_start} - {period_end}) from shift {shift_name}'

            send_notification_to_user(
                user=employee.user,
                title=title_ar,
                body=body_ar,
                title_en=title_en,
                body_en=body_en,
                data={
                    'type': 'period_reminder',
                    'screen': 'attendance',
                    'period_number': str(period.get('period_number', 1)),
                }
            )

            # إشعار داخلي للموظف
            EmployeeNotification._base_manager.create(
                employee=employee,
                title=title_ar,
                message=body_ar,
                notification_type='general_notice',
                severity='info',
            )

        else:
            # بعد انتهاء السماحية → تصعيد للموظف + المدير + HR
            title_ar = f'🚨 غياب عن {period_name}'
            body_ar = f'الموظف {emp_name} لم يسجل حضور في {period_name} ({period_start} - {period_end}) من شيفت {shift_name}'
            title_en = f'🚨 Missing Period: {period_name}'
            body_en = f'Employee {emp_name} missed {period_name} ({period_start} - {period_end}) from shift {shift_name}'

            # إشعار للموظف
            send_notification_to_user(
                user=employee.user,
                title=f'🚨 لم تسجل حضور في {period_name}',
                body=f'لم تسجل حضور في {period_name} ({period_start} - {period_end})',
                title_en=f'🚨 Missed {period_name}',
                body_en=f'You missed {period_name} ({period_start} - {period_end})',
                data={
                    'type': 'period_missed',
                    'screen': 'attendance',
                    'period_number': str(period.get('period_number', 1)),
                }
            )

            # إشعار داخلي للموظف
            EmployeeNotification._base_manager.create(
                employee=employee,
                title=f'🚨 غياب عن {period_name}',
                message=f'لم تسجل حضور في {period_name} ({period_start} - {period_end})',
                notification_type='late_warning',
                severity='danger',
            )

            # إشعار للمدير والـ HR
            if employee.company:
                send_notification_to_managers(
                    company=employee.company,
                    title=title_ar,
                    body=body_ar,
                    title_en=title_en,
                    body_en=body_en,
                    data={
                        'type': 'employee_missed_period',
                        'screen': 'manager_attendance',
                        'employee_id': str(employee.id),
                        'period_number': str(period.get('period_number', 1)),
                    }
                )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'notify_missing_period error: {e}')


def get_active_shift(employee, day):
    """
    مصدر موحّد للشيفت الفعلي.
    بنخلّي الحضور يستخدم نفس منطق الشيفتات والمرتبات
    عشان مايبقاش فيه اختلاف بين الحضور وكشف المرتب.

    للشيفت الليلي: لو الوقت الحالي بعد نص الليل (crosses_midnight)
    ممكن الشيفت يكون بدأ يوم فات → نجرب يومين
    """
    from attendance.api_shifts import get_effective_shift
    from datetime import timedelta

    shift, _source = get_effective_shift(employee, day)

    # لو مش لاقيين شيفت ليلي → نجرب يوم فات
    if not shift or not getattr(shift, 'crosses_midnight', False):
        return shift

    # لو الشيفت ليلي وبدايته بعد ظهر اليوم → الشيفت صح
    if shift.start_time and shift.start_time.hour >= 12:
        return shift

    # لو الشيفت ليلي وبدايته قبل الظهر → ممكن يكون الشيفت بتاع امبارح
    yesterday_shift, _ = get_effective_shift(employee, day - timedelta(days=1))
    if yesterday_shift and getattr(yesterday_shift, 'crosses_midnight', False):
        return yesterday_shift

    return shift




def get_shift_periods(shift, day):
    """
    بترجع قائمة الفترات للشيفت
    - split_fixed: بترجع الفترات من schedule_config
    - غيره: بترجع فترة واحدة من start_time و end_time
    """
    from datetime import datetime, timedelta

    if not shift:
        return []

    periods = []

    shift_mode = getattr(shift, 'shift_mode', 'fixed') or 'fixed'

    if shift_mode in ('variable_weekly', 'variable_weekly_flex'):
        # جدول أسبوعي: كل يوم في الأسبوع ليه أوقات مختلفة
        # schedule_config = {"days": {"0": {"start": "09:00", "end": "17:00"}, ...}}
        # 0=الاثنين ... 6=الأحد (Python weekday)
        try:
            config = getattr(shift, 'schedule_config', {}) or {}
            days_config = config.get('days', {})
            day_key = str(day.weekday())  # 0=الاثنين, 6=الأحد
            day_cfg = days_config.get(day_key)

            if day_cfg:
                from datetime import datetime as _dt
                start_str = str(day_cfg.get('start', '09:00'))
                end_str = str(day_cfg.get('end', '17:00'))
                start_parts = start_str.split(':')
                end_parts = end_str.split(':')
                start_dt = _dt.combine(day, __import__('datetime').time(
                    int(start_parts[0]), int(start_parts[1])))
                end_dt = _dt.combine(day, __import__('datetime').time(
                    int(end_parts[0]), int(end_parts[1])))
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                tz = timezone.get_current_timezone()
                periods.append({
                    'period_number': 1,
                    'start': timezone.make_aware(start_dt, tz),
                    'end': timezone.make_aware(end_dt, tz),
                    'start_str': start_str,
                    'end_str': end_str,
                    'name': day_cfg.get('name', 'فترة العمل'),
                })
        except Exception:
            pass

        # fallback لو اليوم مش في الجدول
        if not periods and shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'فترة العمل',
            })

    elif shift_mode == 'variable_daily':
        # جدول يومي: كل تاريخ ليه أوقات مختلفة
        # schedule_config = {"dates": {"2026-07-25": {"start": "08:00", "end": "16:00"}, ...}}
        try:
            config = getattr(shift, 'schedule_config', {}) or {}
            dates_config = config.get('dates', {})
            date_key = day.isoformat()
            date_cfg = dates_config.get(date_key)

            if date_cfg:
                from datetime import datetime as _dt
                start_str = str(date_cfg.get('start', '09:00'))
                end_str = str(date_cfg.get('end', '17:00'))
                start_parts = start_str.split(':')
                end_parts = end_str.split(':')
                start_dt = _dt.combine(day, __import__('datetime').time(
                    int(start_parts[0]), int(start_parts[1])))
                end_dt = _dt.combine(day, __import__('datetime').time(
                    int(end_parts[0]), int(end_parts[1])))
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                tz = timezone.get_current_timezone()
                periods.append({
                    'period_number': 1,
                    'start': timezone.make_aware(start_dt, tz),
                    'end': timezone.make_aware(end_dt, tz),
                    'start_str': start_str,
                    'end_str': end_str,
                    'name': date_cfg.get('name', 'فترة العمل'),
                })
        except Exception:
            pass

        # fallback لو التاريخ مش في الجدول
        if not periods and shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'فترة العمل',
            })

    elif shift_mode == 'split_fixed':
        config = getattr(shift, 'schedule_config', {}) or {}
        raw_periods = config.get('periods', [])

        for i, p in enumerate(raw_periods):
            try:
                start_parts = str(p.get('start', '09:00')).split(':')
                end_parts = str(p.get('end', '17:00')).split(':')

                start_dt = datetime.combine(day,
                    __import__('datetime').time(int(start_parts[0]), int(start_parts[1])))
                end_dt = datetime.combine(day,
                    __import__('datetime').time(int(end_parts[0]), int(end_parts[1])))

                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                tz = timezone.get_current_timezone()
                periods.append({
                    'period_number': i + 1,
                    'start': timezone.make_aware(start_dt, tz),
                    'end': timezone.make_aware(end_dt, tz),
                    'start_str': p.get('start', '09:00'),
                    'end_str': p.get('end', '17:00'),
                    'name': p.get('name', f'فترة {i + 1}'),
                })
            except Exception:
                continue

        # لو schedule_config فاضل → fallback على start/end عادي
        if not periods and shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'فترة 1',
            })
    else:
        # شيفت عادي → فترة واحدة بس
        if shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'الفترة الأساسية',
            })

    return periods


def get_missing_periods(shift, day, employee):
    """
    بترجع الفترات اللي الموظف ما حضرهاش لـ split_fixed
    """

    if not shift or getattr(shift, 'shift_mode', 'fixed') != 'split_fixed':
        return []

    periods = get_shift_periods(shift, day)
    if not periods:
        return []

    attendance = Attendance._base_manager.filter(
        employee=employee, date=day
    ).first()

    if not attendance:
        return periods  # كل الفترات فاتت

    from attendance.models import AttendanceSession

    sessions = AttendanceSession._base_manager.filter(
        attendance=attendance,
        employee=employee,
    ).order_by('session_number')

    missed = []
    now = timezone.now()

    for period in periods:
        # الفترة لو لسه مجيتش ساعتها ما نعدهاش فاتت
        if period['end'] > now:
            continue

        # الفترة فاتت، شوف لو فيه session فيها
        covered = False
        for session in sessions:
            s_in = session.check_in_time
            if s_in and period['start'] <= s_in <= period['end']:
                covered = True
                break

        if not covered:
            missed.append(period)

    return missed


def get_shift_bounds(shift, day):
    """
    بترجع حدود الشيفت (start, end) كـ datetime aware.

    للشيفت الليلي (crosses_midnight):
    - لو start_time بعد 12: الشيفت بيبدأ يوم day وبينتهي يوم day+1
    - لو start_time قبل 12: الشيفت بدأ يوم day-1 وبينتهي يوم day
    """
    from datetime import datetime, timedelta

    if not shift or not shift.start_time or not shift.end_time:
        return None, None

    crosses = getattr(shift, 'crosses_midnight', False)
    start_hour = shift.start_time.hour

    if crosses and start_hour < 12:
        # الشيفت بدأ يوم فات (مثلاً: بدأ 10pm يوم 25، خلص 6am يوم 26)
        shift_day = day - timedelta(days=1)
    else:
        shift_day = day

    start_dt = datetime.combine(shift_day, shift.start_time)
    end_dt = datetime.combine(shift_day, shift.end_time)

    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    current_timezone = timezone.get_current_timezone()
    start_dt = timezone.make_aware(start_dt, current_timezone)
    end_dt = timezone.make_aware(end_dt, current_timezone)

    return start_dt, end_dt


def attendance_to_dict(attendance):
    if not attendance:
        return {
            'date': '',
            'date_display': '',
            'status': '',
            'checked_in': False,
            'check_in_time': '',
            'check_in_latitude': None,
            'check_in_longitude': None,
            'check_in_address': '',
            'checked_out': False,
            'check_out_time': '',
            'check_out_latitude': None,
            'check_out_longitude': None,
            'check_out_address': '',
        }

    return {
        'date': attendance.date.isoformat() if getattr(attendance, 'date', None) else '',
        'date_display': attendance.date.strftime('%d/%m/%Y') if getattr(attendance, 'date', None) else '',
        'status': getattr(attendance, 'status', '') or '',
        'checked_in': bool(getattr(attendance, 'check_in_time', None)),
        'check_in_time': format_time_value(getattr(attendance, 'check_in_time', None)),
        'check_in_latitude': getattr(attendance, 'check_in_latitude', None),
        'check_in_longitude': getattr(attendance, 'check_in_longitude', None),
        'check_in_address': getattr(attendance, 'check_in_address', '') or '',
        'checked_out': bool(getattr(attendance, 'check_out_time', None)),
        'check_out_time': format_time_value(getattr(attendance, 'check_out_time', None)),
        'check_out_latitude': getattr(attendance, 'check_out_latitude', None),
        'check_out_longitude': getattr(attendance, 'check_out_longitude', None),
        'check_out_address': getattr(attendance, 'check_out_address', '') or '',
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({'success': False, 'message': 'اسم المستخدم وكلمة السر مطلوبين'}, status=400)

    user = authenticate(username=username, password=password)

    if not user:
        return Response({'success': False, 'message': 'بيانات الدخول غير صحيحة'}, status=401)

    token, _ = Token._base_manager.get_or_create(user=user)

    # JWT tokens
    try:
        _refresh = RefreshToken.for_user(user)
        _jwt_access = str(_refresh.access_token)
        _jwt_refresh = str(_refresh)
    except Exception:
        _jwt_access = ''
        _jwt_refresh = ''
    must_change_password = getattr(user, 'must_change_password', False)
    role = getattr(user, 'role', 'employee') or 'employee'
    manager_roles = ['super_admin', 'company_admin', 'hr_manager', 'manager']

    employee = get_employee_for_user(user)

    company_name = ''
    company_obj = getattr(user, 'company', None)
    if employee and getattr(employee, 'company', None):
        company_obj = employee.company

    if company_obj:
        company_name = (
            getattr(company_obj, 'name', '')
            or getattr(company_obj, 'name_ar', '')
            or str(company_obj)
        )

    if not employee and role in manager_roles:
        full_name = user.get_full_name().strip() or user.get_username()
        return Response({
            'success': True,
            'message': 'تم الدخول بنجاح',
            'token': token.key,
            'access': _jwt_access,
            'refresh': _jwt_refresh,
            'must_change_password': must_change_password,
            'role': role,
            'app_mode': 'manager',
            'username': user.get_username(),
            'full_name': full_name,
            'first_name': user.first_name or full_name.split(' ')[0] if full_name else '',
            'gender': 'male',
            'company_name': company_name,
            'employee': {
                'id': None,
                'name': full_name,
                'company': company_name,
                'is_field_worker': False,
                'stealth_tracking_enabled': False,
                'should_track': False,
            }
        })

    if not employee:
        return Response({'success': False, 'message': 'لا يوجد ملف موظف مرتبط بهذا المستخدم'}, status=404)

    is_field_worker = getattr(employee, 'is_field_worker', False)
    stealth_tracking_enabled = getattr(employee, 'stealth_tracking_enabled', False)
    should_track = bool(is_field_worker or stealth_tracking_enabled)

    full_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
    if not full_name:
        full_name = user.get_username()

    app_mode = 'manager' if role in manager_roles else 'employee'

    return Response({
        'success': True,
        'message': 'تم الدخول بنجاح',
        'token': token.key,
        'access': _jwt_access,
        'refresh': _jwt_refresh,
        'must_change_password': must_change_password,
        'role': role,
        'app_mode': app_mode,
        'username': user.get_username(),
        'full_name': full_name,
        'first_name': getattr(employee, 'first_name_ar', '') or user.first_name or full_name.split(' ')[0],
        'gender': getattr(employee, 'gender', 'male') or 'male',
        'company_name': company_name,
        'employee': {
            'id': employee.id,
            'name': full_name,
            'first_name': getattr(employee, 'first_name_ar', ''),
            'gender': getattr(employee, 'gender', 'male'),
            'company': company_name,
            'is_field_worker': is_field_worker,
            'stealth_tracking_enabled': stealth_tracking_enabled,
            'should_track': should_track,
        }
    })




def _create_gps_disabled_alert(employee, source="attendance"):
    try:
        from attendance.models import TrackingAlert
        now = timezone.now()
        today = timezone.localdate()

        note = f"GPS disabled أثناء {source}"

        open_alert = TrackingAlert._base_manager.filter(
            company=employee.company,
            employee=employee,
            date=today,
            status='open'
        ).filter(notes__icontains='GPS').first()

        if open_alert:
            open_alert.last_seen_at = now
            if not getattr(open_alert, 'notes', ''):
                open_alert.notes = note
            open_alert.save(update_fields=['last_seen_at', 'notes'])
        else:
            TrackingAlert._base_manager.create(
                company=employee.company,
                employee=employee,
                date=today,
                started_at=now,
                last_seen_at=now,
                minutes_outside=0,
                last_latitude=None,
                last_longitude=None,
                last_address='',
                status='open',
                notes=note,
            )
    except Exception:
        pass

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_send_location(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    accuracy = request.data.get('accuracy', 0)

    if latitude in [None, ''] or longitude in [None, '']:
        _create_gps_disabled_alert(employee, 'location_ping')
        return Response({'success': False, 'message': 'الموقع الجغرافي غير متاح. يرجى تفعيل GPS والمحاولة مرة أخرى'}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy or 0)
    except Exception:
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)

    if not _can_track_location(employee):
        return Response({
            'success': False,
            'message': 'تتبع الموقع متاح فقط أثناء وقت الدوام'
        }, status=403)
    address = reverse_geocode(latitude, longitude)
    LocationLog._base_manager.create(
        company=employee.company,
        employee=employee,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        address=address,
        timestamp=timezone.now()
    )

    return Response({
        'success': True,
        'message': 'تم تسجيل الموقع بنجاح',
        'employee_name': f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
    })


def get_current_split_period(shift, now_dt):
    from datetime import timedelta

    if not shift or getattr(shift, 'shift_mode', 'fixed') != 'split_fixed':
        return None

    early_minutes = int(getattr(shift, 'early_checkin_minutes', 0) or 0)
    candidate_days = [
        timezone.localdate(now_dt),
        timezone.localdate(now_dt - timedelta(days=1)),
    ]
    seen_days = set()

    for day in candidate_days:
        if day in seen_days:
            continue
        seen_days.add(day)

        periods = get_shift_periods(shift, day)
        for period in periods:
            allowed_start = period['start'] - timedelta(minutes=early_minutes)
            if allowed_start <= now_dt <= period['end']:
                return period

    return None


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_action(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    action = request.data.get('action', '').strip().lower()
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    accuracy = request.data.get('accuracy', 0)

    if action not in ['check_in', 'check_out']:
        return Response({'success': False, 'message': 'نوع العملية لازم يكون check_in أو check_out'}, status=400)

    if latitude in [None, ''] or longitude in [None, '']:
        _create_gps_disabled_alert(employee, action)
        return Response({'success': False, 'message': 'الموقع الجغرافي غير متاح. يرجى تفعيل GPS والمحاولة مرة أخرى'}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy or 0)
    except Exception:
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)

    today = timezone.localdate()
    now = timezone.now()

    if action == 'check_out':
        attendance = Attendance._base_manager.filter(employee=employee, check_out_time__isnull=True).order_by('-id').first()
        if not attendance:
            attendance = Attendance._base_manager.filter(employee=employee, date=today).first()
    else:
        attendance = Attendance._base_manager.filter(employee=employee, date=today).first()

    # ── حماية الإجازات مع دعم الاستدعاء ──
    from leaves.models import LeaveRequest, LeaveRecallRequest
    has_approved_leave = LeaveRequest._base_manager.filter(
        employee=employee,
        status='approved',
        start_date__lte=today,
        end_date__gte=today,
    ).exists()

    has_approved_recall = False
    if has_approved_leave:
        has_approved_recall = LeaveRecallRequest._base_manager.filter(
            employee=employee,
            recall_date=today,
            status='approved',
        ).exists()

    if has_approved_leave and not has_approved_recall:
        return Response({
            "success": False,
            **bilingual_message(
                employee,
                "أنت في إجازة معتمدة اليوم. لا يمكنك تسجيل الحضور أو الانصراف إلا بعد تواصلك مع الموارد البشرية لعمل طلب استدعاء.",
                "You are on an approved leave today. You cannot record attendance until you contact HR to create a leave recall request."
            ),
            "is_on_leave": True,
            "can_request_recall": True,
        }, status=400)

    # ── تحقق أن الموظف مربوط فعلياً بشيفت (EmployeeShift أو ShiftAssignment) ──
    if action == 'check_in':
        from attendance.models import EmployeeShift as _EmpShift
        from attendance.models import ShiftAssignment as _ShiftAssign
        from django.db.models import Q

        # فحص 1: EmployeeShift (ربط مباشر)
        has_emp_shift = _EmpShift._base_manager.filter(
            employee=employee,
            is_active=True,
        ).exists()

        # فحص 2: ShiftAssignment (ربط بالموظف مباشرة أو بالقسم/الفرع)
        emp_dept_id = getattr(employee, 'department_id', None)
        emp_branch_id = getattr(employee, 'branch_id', None)

        assignment_q = Q(employee=employee)
        if emp_dept_id:
            assignment_q |= Q(assignment_type='department', department_id=emp_dept_id)
        if emp_branch_id:
            assignment_q |= Q(assignment_type='branch', branch_id=emp_branch_id)

        has_shift_assignment = _ShiftAssign._base_manager.filter(
            company=employee.company,
            is_active=True,
        ).filter(assignment_q).exists()

        if not has_emp_shift and not has_shift_assignment:
            return Response({
                'success': False,
                **bilingual_message(
                    employee,
                    'لا يمكن تسجيل الحضور. لم يتم ربطك بأي شيفت حتى الآن. يرجى التواصل مع الموارد البشرية.',
                    'Check-in is not allowed. You are not assigned to any shift yet. Please contact HR.'
                ),
                'no_shift_assigned': True,
            }, status=400)

    active_shift = get_active_shift(employee, today)
    shift_start, shift_end = get_shift_bounds(active_shift, today)
    
    # ═══════════════════════════════════════════════════
    # Worker Type Check - فحص نوع الموظف
    # ═══════════════════════════════════════════════════
    if action == 'check_in':
        worker_type = getattr(employee, 'worker_type', 'office') or 'office'
        company = employee.company
        
        # لو مكتبي - لازم من موقع الشركة
        if worker_type == 'office':
            if company and company.geofence_enabled and company.office_latitude and company.office_longitude:
                from attendance.location_utils import is_within_radius
                radius_check = is_within_radius(
                    latitude, longitude,
                    float(company.office_latitude),
                    float(company.office_longitude),
                    company.geofence_radius or 500,
                )
                if not radius_check['is_within']:
                    return Response({
                        'success': False,
                        **bilingual_message(
                            employee,
                            f'لا يمكن تسجيل الحضور من هنا. الموظف المكتبي يجب أن يبصم من موقع الشركة (أنت على بعد {radius_check["distance_meters"]:.0f} متر).',
                            f'You must check-in from the company location (you are {radius_check["distance_meters"]:.0f}m away).'
                        ),
                        'outside_office': True,
                        'distance_meters': radius_check['distance_meters'],
                    }, status=400)
        
        # لو ميداني محدد - لازم من موقع معتمد
        elif worker_type == 'field_assigned':
            from attendance.models import EmployeeWorkLocation
            from attendance.location_utils import is_within_radius
            from django.db.models import Q
            
            # نجيب المواقع المعتمدة للموظف
            approved_locations = EmployeeWorkLocation._base_manager.filter(
                company=company,
                status='approved',
                is_active=True,
            ).filter(
                Q(employee=employee) |
                Q(is_shared=True, shared_with_branch=None, shared_with_department=None) |
                Q(is_shared=True, shared_with_branch=employee.branch) |
                Q(is_shared=True, shared_with_department=employee.department)
            ).distinct()
            
            # نفحص لو الموظف داخل أي موقع معتمد
            current_location = None
            for loc in approved_locations:
                check = is_within_radius(
                    latitude, longitude,
                    float(loc.latitude), float(loc.longitude),
                    loc.radius or 500,
                )
                if check['is_within']:
                    current_location = loc
                    break
            
            if not current_location:
                # مش داخل أي موقع معتمد
                available_names = [loc.name for loc in approved_locations[:5]]
                return Response({
                    'success': False,
                    **bilingual_message(
                        employee,
                        'الموقع الحالي غير معتمد. المواقع المتاحة: ' + ', '.join(available_names) if available_names else 'لا توجد مواقع معتمدة لك. يرجى اقتراح موقع.',
                        'Current location is not approved.'
                    ),
                    'outside_approved_locations': True,
                    'approved_locations': available_names,
                }, status=400)
        
        # لو ميداني حر - أي مكان مسموح
        # (مفيش فحص للموقع)
    
    

    # ── إعاده حساب حدود الشيفت بناءً على تاريخ الحضور الأصلي ──
    if action == 'check_out' and attendance and getattr(attendance, 'date', None) and active_shift:
        shift_start, shift_end = get_shift_bounds(active_shift, attendance.date)

    # ── تحقق من وقت الشيفت (للانصراف) ──
    if action == 'check_out' and active_shift:
        attendance_mode = getattr(employee, 'attendance_mode', 'fixed_shift')
        shift_mode = getattr(active_shift, 'shift_mode', 'fixed') or 'fixed'
        skip_out_check = (
            attendance_mode in ('flexible_hours', 'field_worker')
            or shift_mode in ('flex_fixed', 'flex_split')
        )
        if not skip_out_check and shift_end:
            from datetime import timedelta
            late_checkout_allowed = getattr(active_shift, 'late_checkout_allowed', False)
            late_checkout_mins = getattr(active_shift, 'late_checkout_minutes', None)
            
            if late_checkout_allowed or (late_checkout_mins is not None and late_checkout_mins > 0):
                late_mins = int(late_checkout_mins or 0)
                max_checkout_time = shift_end + timedelta(minutes=late_mins)
                if now > max_checkout_time:
                    shift_end_str = shift_end.strftime('%I:%M %p')
                    return Response({
                        'success': False,
                        **bilingual_message(
                            employee,
                            f'انتهت المهلة المحددة لتسجيل الانصراف لهذا الشيفت (الموعد: {shift_end_str} + سماحية {late_mins} دقيقة).',
                            f'Check-out time window for this shift has expired (Shift end: {shift_end_str} + {late_mins} min grace).'
                        ),
                        'late_checkout_expired': True,
                    }, status=400)

    # ── تحقق من وقت الشيفت (للحضور فقط) ──
    if action == 'check_in' and active_shift:
        attendance_mode = getattr(employee, 'attendance_mode', 'fixed_shift')
        shift_mode = getattr(active_shift, 'shift_mode', 'fixed') or 'fixed'

        # الشيفت المرن والميداني: مسموح أي وقت
        # split_fixed: عنده تحقق خاص أسفل
        skip_time_check = (
            attendance_mode in ('flexible_hours', 'field_worker')
            or shift_mode in ('flex_fixed', 'flex_split', 'split_fixed')
        )

        if not skip_time_check and shift_start and shift_end:
            from datetime import timedelta
            # نقرأ فترة السماح للحضور المبكر من الشيفت نفسه
            early_val = getattr(active_shift, 'early_checkin_minutes', None)
            early_minutes = int(early_val) if early_val is not None else 30
            allowed_from = shift_start - timedelta(minutes=early_minutes)

            if now < allowed_from or now > shift_end:
                shift_start_str = shift_start.strftime('%I:%M %p')
                shift_end_str = shift_end.strftime('%I:%M %p')
                return Response({
                    'success': False,
                    **bilingual_message(
                        employee,
                        f'لا يمكن تسجيل الحضور الآن. الشيفت من {shift_start_str} إلى {shift_end_str} (مسموح الحضور قبل الشيفت بـ {early_minutes} دقيقة).',
                        f'Check-in is not allowed now. Shift is from {shift_start_str} to {shift_end_str} (check-in allowed {early_minutes} minutes before shift starts).'
                    ),
                    'outside_shift_time': True,
                    'shift_start': shift_start_str,
                    'shift_end': shift_end_str,
                }, status=400)

    current_split_period = None
    if action == 'check_in':
        current_split_period = get_current_split_period(active_shift, now)
        if active_shift and getattr(active_shift, 'shift_mode', 'fixed') == 'split_fixed' and not current_split_period:
            periods = get_shift_periods(active_shift, today)
            periods_text = " / ".join(
                [f"{p['name']}: {p['start_str']} - {p['end_str']}" for p in periods]
            ) or "لا توجد فترات معرفة"

            return Response({
                "success": False,
                **bilingual_message(
                    employee,
                    f"لا يمكن تسجيل الحضور الآن. مسموح فقط أثناء فترات الشيفت المحددة: {periods_text}",
                    f"Check-in is not allowed right now. It is only allowed during the configured shift periods: {periods_text}",
                ),
                "outside_allowed_period": True,
                "shift_periods": [
                    {
                        "period_number": p["period_number"],
                        "name": p["name"],
                        "start": p["start_str"],
                        "end": p["end_str"],
                    }
                    for p in periods
                ],
            }, status=400)

    late_minutes = 0
    late_permission = None

    if (
        action == "check_in"
        and shift_start
        and getattr(employee, "attendance_mode", "fixed_shift") != "flexible_hours"
    ):
        from datetime import timedelta

        grace_minutes = int(getattr(active_shift, "grace_period", 0) or 0)
        allowed_start = shift_start + timedelta(minutes=grace_minutes)

        if now > allowed_start:
            late_minutes = int((now - allowed_start).total_seconds() // 60)

            if late_minutes > 0:
                late_permission = get_approved_permission(
                    employee,
                    "late_arrival",
                    today,
                )

    late_permission_covers = bool(
        late_permission
        and float(late_permission.duration_hours or 0) * 60 >= late_minutes
    )

    check_in_status = (
        "present"
        if late_minutes == 0 or late_permission_covers
        else "late"
    )

    check_in_note = ""
    if late_permission_covers:
        check_in_note = "تم استخدام إذن تأخير معتمد"
    elif late_permission and late_minutes > 0:
        check_in_note = "مدة التأخير أكبر من مدة الإذن المعتمد"

    # === Late Warning System ===
    late_warning_info = None
    if action == 'check_in' and late_minutes > 0 and not late_permission_covers:
        try:
            from attendance.payroll_rules import get_late_warning_info
            late_warning_info = get_late_warning_info(employee, today, late_minutes)
        except Exception as e:
            print(f'late_warning_info error: {e}')
            late_warning_info = None

    # ═══════════════════════════════════════════════════
    # الكود ده القديم اتنقل للـ Worker Type Check (فوق)
    # اللي بيفحص حسب نوع الموظف (office/field_free/field_assigned)
    # سيبناه Empty عشان لا نكسر التسلسل
    # ═══════════════════════════════════════════════════
    if action == 'check_in':
        pass  # Handled by worker_type check above

    if action == 'check_in':
        if attendance and getattr(attendance, 'check_in_time', None):
            return Response({
                'success': False,
                'message': 'تم تسجيل الحضور اليوم بالفعل',
                'today': attendance_to_dict(attendance)
            }, status=400)

        if not attendance:
            attendance = Attendance._base_manager.create(
                company=employee.company,
                employee=employee,
                date=today,
                check_in_time=now,
                check_in_latitude=latitude,
                check_in_longitude=longitude,
                check_in_address=reverse_geocode(latitude, longitude),
                check_in_within_range=True,
                shift=active_shift,
                late_minutes=late_minutes,
                check_in_notes=check_in_note,
                status=check_in_status,
            )
        else:
            attendance.company = employee.company
            attendance.check_in_time = now
            attendance.check_in_latitude = latitude
            attendance.check_in_longitude = longitude
            attendance.check_in_address = reverse_geocode(latitude, longitude)
            attendance.check_in_within_range = True
            attendance.shift = active_shift
            attendance.late_minutes = late_minutes
            attendance.check_in_notes = check_in_note
            attendance.status = check_in_status
            attendance.save()

        # === Save LateIncident + Deduction ===
        if late_warning_info and late_warning_info.get('is_warning_enabled') and late_minutes > 0 and not late_permission_covers:
            try:
                from attendance.models import LateIncident
                from employees.models import Deduction
                LateIncident._base_manager.update_or_create(
                    employee=employee,
                    date=today,
                    defaults={
                        'company': employee.company,
                        'attendance': attendance,
                        'late_minutes': late_minutes,
                        'shift_start_time': active_shift.start_time if active_shift else None,
                        'actual_checkin_time': timezone.localtime(now).time(),
                        'grace_period_used': int(getattr(active_shift, 'grace_period', 0) or 0),
                        'month': today.month,
                        'year': today.year,
                        'incident_number_in_month': late_warning_info['incident_number'],
                        'was_deducted': late_warning_info['should_deduct'],
                        'deduction_amount': late_warning_info['deduction_days'],
                    }
                )
                # لو فيه خصم فعلي، سجله في جدول الخصومات
                if late_warning_info['should_deduct'] and late_warning_info['deduction_days'] > 0:
                    try:
                        daily_salary = float(getattr(employee, 'basic_salary', 0) or 0) / 30.0
                        deduction_amount = daily_salary * late_warning_info['deduction_days']
                        Deduction._base_manager.create(
                            company=employee.company,
                            employee=employee,
                            deduction_type='late',
                            amount=round(deduction_amount, 2),
                            date=today,
                            reason=f"تأخير متكرر - المرة رقم {late_warning_info['incident_number']} هذا الشهر",
                            month=today.month,
                            year=today.year,
                            is_visible_to_employee=True,
                            notes=f"خصم {late_warning_info['deduction_days']} من يوم عمل",
                        )
                    except Exception as _de:
                        print(f'Deduction save error: {_de}')
            except Exception as _le:
                print(f'LateIncident save error: {_le}')

        # ── on_mission flag ──
        try:
            from attendance.missions_models import MissionAssignment
            has_mission = MissionAssignment._base_manager.filter(
                employee=employee,
                mission__date=today,
                status='approved',
            ).exists()
            if has_mission:
                attendance.on_mission = True
                attendance.save(update_fields=['on_mission'])
        except Exception:
            pass

        from attendance.models import AttendanceSession

        open_session = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee,
            check_out_time__isnull=True
        ).order_by('-session_number').first()

        if not open_session:
            existing_sessions_count = AttendanceSession._base_manager.filter(
                attendance=attendance,
                employee=employee
            ).count()

            AttendanceSession._base_manager.create(
                company=employee.company,
                attendance=attendance,
                employee=employee,
                session_number=existing_sessions_count + 1,
                check_in_time=now,
                check_in_latitude=latitude,
                check_in_longitude=longitude,
                is_partial=False,
                on_mission=attendance.on_mission,
                notes='Initial check-in session',
            )

        address = reverse_geocode(latitude, longitude)
        LocationLog._base_manager.create(
            company=employee.company,
            employee=employee,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            address=address,
            timestamp=now
        )

        used_permission_hours = None

        if late_permission and late_minutes > 0:
            used_permission_hours = consume_permission(
                late_permission,
                late_minutes / 60,
                now,
            )

        if late_minutes == 0:
            message_ar = "تم تسجيل الحضور بنجاح"
            message_en = "Check-in recorded successfully"
        elif late_permission_covers:
            message_ar = "تم تسجيل الحضور وتطبيق إذن التأخير المعتمد"
            message_en = "Check-in recorded and the approved late-arrival permission was applied"
        elif late_permission:
            message_ar = "تم تسجيل الحضور، لكن مدة التأخير أكبر من مدة الإذن المعتمد"
            message_en = "Check-in recorded, but the delay exceeds the approved permission duration"
        else:
            message_ar = "تم تسجيل الحضور مع احتساب التأخير"
            message_en = "Check-in recorded and the delay was counted"

        response_data = {
            "success": True,
            **bilingual_message(employee, message_ar, message_en),
            "action": "check_in",
            "time": format_time_value(now),
            "late_minutes": late_minutes,
            "permission_applied": bool(used_permission_hours),
            "permission_used_hours": (
                float(used_permission_hours)
                if used_permission_hours
                else 0
            ),
            "today": attendance_to_dict(attendance),
        }

        # === Late Warning Alert ===
        if late_warning_info and late_warning_info.get('is_warning_enabled'):
            response_data['late_warning'] = {
                'show': True,
                'incident_number': late_warning_info['incident_number'],
                'threshold': late_warning_info['threshold'],
                'should_deduct': late_warning_info['should_deduct'],
                'deduction_days': late_warning_info['deduction_days'],
                'message_ar': late_warning_info['message_ar'],
                'message_en': late_warning_info['message_en'],
                'type': 'deduction' if late_warning_info['should_deduct'] else 'warning',
            }

        # Push + Notification center
        try:
            emp_name = request.user.get_full_name() or request.user.username
            notify_employee_checkin(request.user, format_time_value(now), address)
            notify_manager_checkin(employee.company, emp_name, format_time_value(now))
        except Exception as e:
            print(f"Check-in notification error: {e}")

        return Response(response_data)

    from datetime import datetime, timedelta

    early_permission = None
    early_permission_covers = False
    early_leave_minutes = 0

    try:
        att_date = attendance.date if (attendance and attendance.date) else timezone.localdate()
        shift = get_active_shift(employee, att_date)

        if shift:
            shift_start, shift_end = get_shift_bounds(shift, att_date)
            mode = getattr(employee, 'attendance_mode', 'fixed_shift')
            
            if mode == 'flexible_hours' and attendance and attendance.check_in_time:
                check_in_local = timezone.localtime(attendance.check_in_time)
                if shift_start and shift_end:
                    shift_duration = (shift_end - shift_start).total_seconds()
                    end_time_aware = check_in_local + timedelta(seconds=shift_duration)
                else:
                    end_time_aware = check_in_local + timedelta(hours=8)
            else:
                end_time_aware = shift_end

            now = timezone.now()
            if now < end_time_aware:
                remaining = int((end_time_aware - now).total_seconds())

                early_permission = get_approved_permission(
                    employee,
                    "early_leave",
                    today,
                )

                approved_seconds = (
                    float(early_permission.duration_hours or 0) * 3600
                    if early_permission
                    else 0
                )

                early_permission_covers = bool(
                    early_permission
                    and approved_seconds >= remaining
                )

                if not early_permission_covers:
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60

                    if early_permission:
                        message_ar = (
                            f"مدة الإذن المعتمد لا تغطي الانصراف الحالي. "
                            f"المتبقي {hours} ساعة و{minutes} دقيقة."
                        )
                        message_en = (
                            "The approved permission does not cover "
                            f"the remaining {hours} hours and {minutes} minutes."
                        )
                    else:
                        message_ar = (
                            f"لسه بدري على الانصراف، فاضل "
                            f"{hours} ساعة و{minutes} دقيقة. "
                            "قدم طلب إذن خروج مبكر."
                        )
                        message_en = (
                            f"The shift has not ended. "
                            f"{hours} hours and {minutes} minutes remain. "
                            "Submit an early-leave permission request."
                        )

                    return Response({
                        "success": False,
                        **bilingual_message(employee, message_ar, message_en),
                        "shift_not_ended": True,
                        "remaining_seconds": remaining,
                    }, status=400)

    except Exception as e:
        pass

    if not attendance or not getattr(attendance, 'check_in_time', None):
        return Response({'success': False, 'message': 'لا يمكن تسجيل الانصراف قبل الحضور'}, status=400)

    if getattr(attendance, 'check_out_time', None):
        return Response({
            'success': False,
            'message': 'تم تسجيل الانصراف اليوم بالفعل',
            'today': attendance_to_dict(attendance)
        }, status=400)

    attendance.check_out_time = now
    attendance.check_out_latitude = latitude
    attendance.check_out_longitude = longitude
    attendance.check_out_address = reverse_geocode(latitude, longitude)
    attendance.check_out_within_range = True

    from attendance.models import AttendanceSession

    open_session = AttendanceSession._base_manager.filter(
        attendance=attendance,
        employee=employee,
        check_out_time__isnull=True
    ).order_by('-session_number').first()

    if open_session:
        open_session.check_out_time = now
        open_session.check_out_latitude = latitude
        open_session.check_out_longitude = longitude
        open_session.is_partial = False
        open_session.calculate_worked_minutes()
        open_session.save()
    else:
        existing_sessions_count = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee
        ).count()

        if existing_sessions_count == 0:
            fallback_session = AttendanceSession._base_manager.create(
                company=employee.company,
                attendance=attendance,
                employee=employee,
                session_number=1,
                check_in_time=attendance.check_in_time,
                check_out_time=now,
                check_in_latitude=attendance.check_in_latitude,
                check_in_longitude=attendance.check_in_longitude,
                check_out_latitude=latitude,
                check_out_longitude=longitude,
                is_partial=False,
                notes='Backfilled from legacy attendance record',
            )
            fallback_session.calculate_worked_minutes()
            fallback_session.save()

    if shift_end and now < shift_end:
        raw_early = int((shift_end - now).total_seconds() // 60)
        # فحص سماحية الانصراف المبكر للشيفت
        allowed_early_grace = 0
        if shift and getattr(shift, 'early_checkout_allowed', False):
            allowed_early_grace = getattr(shift, 'early_checkout_minutes', 0) or 0
        elif shift and getattr(shift, 'grace_early_leave', 0):
            allowed_early_grace = getattr(shift, 'grace_early_leave', 0) or 0
        
        if raw_early <= allowed_early_grace:
            early_leave_minutes = 0
        else:
            early_leave_minutes = raw_early - allowed_early_grace

    attendance.early_leave_minutes = early_leave_minutes

    if early_permission_covers:
        attendance.check_out_notes = "تم استخدام إذن خروج مبكر معتمد"

    attendance.calculate_work_hours()
    attendance.save()

    # DailyAttendanceSummary: نعبّي الملخص اليومي بعد الانصراف
    try:
        from attendance.models import DailyAttendanceSummary
        DailyAttendanceSummary.compute_for_day(employee, today)
    except Exception as _ds_err:
        import logging
        logging.getLogger(__name__).warning(f'DailyAttendanceSummary checkout error: {_ds_err}')

    # FlexDayAdjustment: لو شيفت مرن → ننشئ/نحدث طلب التعديل
    try:
        from attendance.payroll_rules import _upsert_flex_adjustment
        _flex_shift = getattr(attendance, 'shift', None) or shift
        _flex_hours = float(getattr(attendance, 'work_hours', 0) or 0)
        _upsert_flex_adjustment(employee, attendance, _flex_shift, _flex_hours)
    except Exception as _fx_err:
        import logging
        logging.getLogger(__name__).warning(f'FlexDayAdjustment checkout error: {_fx_err}')

    LocationLog._base_manager.create(
        company=employee.company,
        employee=employee,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        timestamp=now
    )

    used_early_hours = None

    if early_permission and early_leave_minutes > 0:
        used_early_hours = consume_permission(
            early_permission,
            early_leave_minutes / 60,
            now,
        )

    if used_early_hours:
        message_ar = "تم تسجيل الانصراف وتطبيق إذن الخروج المبكر"
        message_en = "Check-out recorded and the approved early-leave permission was applied"
    else:
        message_ar = "تم تسجيل الانصراف بنجاح"
        message_en = "Check-out recorded successfully"

    response_data = {
        "success": True,
        **bilingual_message(employee, message_ar, message_en),
        "action": "check_out",
        "time": format_time_value(now),
        "early_leave_minutes": early_leave_minutes,
        "permission_applied": bool(used_early_hours),
        "permission_used_hours": (
            float(used_early_hours)
            if used_early_hours
            else 0
        ),
        "today": attendance_to_dict(attendance),
    }

    # Push + Notification center
    try:
        emp_name = request.user.get_full_name() or request.user.username
        notify_employee_checkout(request.user, format_time_value(now), hours_worked='')
        if early_leave_minutes > 0:
            notify_manager_early_leave(
                employee.company,
                emp_name,
                format_time_value(now),
                early_leave_minutes,
            )
        else:
            notify_manager_checkout(employee.company, emp_name, format_time_value(now))
    except Exception as e:
        print(f"Check-out notification error: {e}")

    return Response(response_data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_status(request):
    from datetime import datetime, timedelta, time as dt_time
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    today = timezone.localdate()

    # ═══════════════════════════════════════════════════
    # ATT-10b: GPS Detection - يسجل Alert لو GPS مقفول
    # ═══════════════════════════════════════════════════
    try:
        _lat = request.GET.get('latitude')
        _lng = request.GET.get('longitude')
        _has_gps = _lat not in (None, '', 'null') and _lng not in (None, '', 'null')

        from attendance.models import TrackingAlert
        _now = timezone.now()

        _open_alert = TrackingAlert._base_manager.filter(
            company=employee.company,
            employee=employee,
            date=today,
            status='open',
            notes__icontains='GPS'
        ).first()

        if not _has_gps:
            # GPS مقفول - نسجل Alert
            if _open_alert:
                # تحديث Alert الموجود
                _open_alert.last_seen_at = _now
                _open_alert.save(update_fields=['last_seen_at'])
            else:
                # إنشاء Alert جديد
                TrackingAlert._base_manager.create(
                    company=employee.company,
                    employee=employee,
                    date=today,
                    started_at=_now,
                    last_seen_at=_now,
                    minutes_outside=0,
                    last_latitude=None,
                    last_longitude=None,
                    last_address='',
                    status='open',
                    notes='GPS disabled - detected from status ping',
                )
        else:
            # GPS شغال - نقفل أي Alert مفتوح
            if _open_alert:
                _open_alert.status = 'resolved'
                _open_alert.resolved_at = _now
                _open_alert.save(update_fields=['status', 'resolved_at'])
    except Exception:
        pass
    # ═══════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════
    # Validation: worker_type and shift must be set
    # ═══════════════════════════════════════════════════
    worker_type = getattr(employee, 'worker_type', None)
    
    effective_shift = get_active_shift(employee, today)
    has_shift = effective_shift is not None

    
    missing = []
    if not worker_type:
        missing.append('worker_type')
    if not has_shift:
        missing.append('shift')
    
    if missing:
        messages_ar = []
        messages_en = []
        if 'worker_type' in missing:
            messages_ar.append('لم يتم تحديد نوع الموظف (مكتبي / ميداني حر / ميداني محدد)')
            messages_en.append('Worker type not specified (office / field_free / field_assigned)')
        if 'shift' in missing:
            messages_ar.append('لم يتم ربطك بأي شيفت')
            messages_en.append('You are not assigned to any shift')
        
        # Send notification to HR (once per day)
        try:
            _notify_hr_incomplete_data(employee, missing)
        except Exception:
            pass
        
        return Response({
            'success': False,
            'account_incomplete': True,
            'missing': missing,
            'message': ' | '.join(messages_ar),
            'message_en': ' | '.join(messages_en),
            'action_required': 'تواصل مع الموارد البشرية' if getattr(employee, 'language', 'ar') == 'ar' else 'Contact HR',
        }, status=200)
    
    # شيفت بعد نص الليل: نبحث في اليوم الحالي واليوم السابق
    from datetime import timedelta as _td
    attendance = (
        Attendance._base_manager.filter(
            employee=employee,
            date__in=[today, today - _td(days=1)],
            check_in_time__isnull=False,
        ).order_by('-date').first()
        or
        Attendance._base_manager.filter(employee=employee, date=today).first()
    )
    today_dict = attendance_to_dict(attendance)

    # تاريخ الشيفت الفعلي (ممكن يكون امبارح لو شيفت بعد نص الليل)
    att_date = attendance.date if attendance else today

    shift_start_str = ''
    shift_end_str = ''
    shift_name = ''
    shift_end_timestamp = None
    shift_duration_seconds = 0
    remaining_seconds = 0
    can_check_out = False
    has_early_leave = False

    try:
        shift = get_active_shift(employee, att_date)

        if shift:
            shift_name = shift.name
            shift_mode = getattr(shift, 'shift_mode', '') or getattr(shift, 'shift_type', '')
            periods = get_shift_periods(shift, att_date)

            effective_start_dt = None
            effective_end_dt = None

            # لو الشيفت بيرجع فترات فعلية → نعرض أول فترة وآخر فترة
            if periods:
                first_period = periods[0]
                last_period = periods[-1]

                effective_start_dt = first_period.get('start')
                effective_end_dt = last_period.get('end')

                if first_period.get('start_str'):
                    shift_start_str = first_period.get('start_str')
                elif effective_start_dt:
                    local_start = timezone.localtime(effective_start_dt) if timezone.is_aware(effective_start_dt) else effective_start_dt
                    shift_start_str = local_start.strftime('%I:%M %p')

                if last_period.get('end_str'):
                    shift_end_str = last_period.get('end_str')
                elif effective_end_dt:
                    local_end = timezone.localtime(effective_end_dt) if timezone.is_aware(effective_end_dt) else effective_end_dt
                    shift_end_str = local_end.strftime('%I:%M %p')

            # fallback للشيفت العادي
            elif shift.start_time and shift.end_time:
                effective_start_dt, effective_end_dt = get_shift_bounds(shift, att_date)
                shift_start_str = shift.start_time.strftime('%I:%M %p') if shift.start_time else ''
                shift_end_str = shift.end_time.strftime('%I:%M %p') if shift.end_time else '' 

            if effective_start_dt and effective_end_dt:
                shift_duration_seconds = int((effective_end_dt - effective_start_dt).total_seconds())

                if attendance and attendance.check_in_time:
                    check_in_local = timezone.localtime(attendance.check_in_time)
                    mode = getattr(employee, 'attendance_mode', 'fixed_shift')

                    # المرن بدون فترات: نهاية الشيفت = وقت الدخول + المدة
                    if mode == 'flexible_hours' and not periods:
                        end_time_dt = check_in_local + timedelta(seconds=shift_duration_seconds)
                    else:
                        end_time_dt = effective_end_dt

                    shift_end_timestamp = end_time_dt.isoformat()
                    now = timezone.now()
                    remaining = (end_time_dt - now).total_seconds()
                    remaining_seconds = max(0, int(remaining))
                    can_check_out = remaining_seconds <= 0
    except Exception as e:
        pass

    try:
        from requests_app.models import EmployeeRequest, RequestType
        from django.db.models import Q
        early_leave_types = RequestType._base_manager.filter(
            Q(company=employee.company) &
            (Q(name__icontains='خروج مبكر') | Q(name__icontains='إذن انصراف') | Q(name__icontains='اذن انصراف'))
        ).values_list('id', flat=True)
        
        if early_leave_types:
            early_req = EmployeeRequest._base_manager.filter(
                employee=employee,
                request_type__id__in=list(early_leave_types),
                start_date=today,
                status='approved'
            ).order_by('start_time').first()
            
            if early_req:
                has_early_leave = True
                current_time = timezone.localtime(timezone.now()).time()
                
                if early_req.start_time:
                    if current_time >= early_req.start_time:
                        can_check_out = True
                else:
                    can_check_out = True
    except Exception:
        pass

    # بيانات الخروج الجزئي
    allow_partial_checkout = False
    shift_mode = 'fixed'
    sessions_today = 0
    has_open_session = False
    can_partial_checkout = False
    can_resume = False

    periods_data = []
    missing_periods_data = []

    try:
        if shift:
            allow_partial_checkout = getattr(shift, 'allow_partial_checkout', False)
            shift_mode = getattr(shift, 'shift_mode', 'fixed')

            periods = get_shift_periods(shift, today)
            periods_data = [
                {
                    'period_number': p.get('period_number'),
                    'name': p.get('name'),
                    'start': p.get('start_str'),
                    'end': p.get('end_str'),
                }
                for p in periods
            ]

            missing_periods = get_missing_periods(shift, today, employee)
            missing_periods_data = [
                {
                    'period_number': p.get('period_number'),
                    'name': p.get('name'),
                    'start': p.get('start_str'),
                    'end': p.get('end_str'),
                }
                for p in missing_periods
            ]

        if allow_partial_checkout and attendance:
            from attendance.models import AttendanceSession
            sessions = AttendanceSession._base_manager.filter(
                attendance=attendance,
                employee=employee
            ).order_by('session_number')

            sessions_today = sessions.count()
            open_session = sessions.filter(check_out_time__isnull=True).first()
            has_open_session = open_session is not None

            max_sessions = getattr(shift, 'max_sessions_per_day', 2) if shift else 2

            if has_open_session:
                can_partial_checkout = True
                can_resume = False
            elif sessions_today > 0 and sessions_today < max_sessions:
                can_partial_checkout = False
                can_resume = True
    except Exception:
        pass

    response_data = {
        'success': True,
        'date': today.isoformat(),
        'checked_in': today_dict.get('checked_in', False),
        'checked_out': today_dict.get('checked_out', False),
        'check_in_time': today_dict.get('check_in_time', ''),
        'check_out_time': today_dict.get('check_out_time', ''),
        'shift_name': shift_name,
        'shift_start': shift_start_str,
        'shift_end': shift_end_str,
        'shift_end_timestamp': shift_end_timestamp,
        'shift_duration_seconds': shift_duration_seconds,
        'remaining_seconds': remaining_seconds,
        'can_check_out': can_check_out,
        'has_early_leave_permission': has_early_leave,
        'allow_partial_checkout': allow_partial_checkout,
        'shift_mode': shift_mode,
        'shift_periods': periods_data,
        'missing_periods': missing_periods_data,
        'sessions_today': sessions_today,
        'has_open_session': has_open_session,
        'can_partial_checkout': can_partial_checkout,
        'can_resume': can_resume,
        'worker_type': getattr(employee, 'worker_type', 'office') or 'office',
        'current_approved_location': _get_current_approved_location(employee, request),
        'active_field_visit': _get_active_field_visit(employee),
        'today': today_dict,
        'is_late': False,
        'late_minutes': 0,
    }

    # ── حساب التأخير ──────────────────────────────────
    try:
        if attendance and attendance.check_in_time and shift:
            from datetime import datetime, timedelta
            check_in_local = timezone.localtime(attendance.check_in_time)
            periods = get_shift_periods(shift, att_date)

            if periods:
                first_start = periods[0].get('start')
                if first_start:
                    if timezone.is_naive(first_start):
                        tz = timezone.get_current_timezone()
                        first_start = timezone.make_aware(first_start, tz)
                    diff = (check_in_local - timezone.localtime(first_start)).total_seconds()
                    if diff > 0:
                        response_data['is_late'] = True
                        response_data['late_minutes'] = int(diff // 60)
            elif shift.start_time:
                from datetime import datetime
                shift_start_dt = datetime.combine(att_date, shift.start_time)
                tz = timezone.get_current_timezone()
                shift_start_aware = timezone.make_aware(shift_start_dt, tz)
                diff = (check_in_local - shift_start_aware).total_seconds()
                if diff > 0:
                    response_data['is_late'] = True
                    response_data['late_minutes'] = int(diff // 60)
    except Exception:
        pass
    # ──────────────────────────────────────────────────

    return Response(response_data)


def _get_current_approved_location(employee, request):
    try:
        worker_type = getattr(employee, 'worker_type', 'office')
        if worker_type != 'field_assigned':
            return None
        
        try:
            lat = float(request.GET.get('latitude', 0) or 0)
            lng = float(request.GET.get('longitude', 0) or 0)
        except (ValueError, TypeError):
            return None
        
        if lat == 0 or lng == 0:
            return None
        
        from attendance.models import EmployeeWorkLocation
        from attendance.location_utils import is_within_radius
        from django.db.models import Q
        
        locations = EmployeeWorkLocation._base_manager.filter(
            company=employee.company,
            status='approved',
            is_active=True,
        ).filter(
            Q(employee=employee) |
            Q(is_shared=True, shared_with_branch=None, shared_with_department=None) |
            Q(is_shared=True, shared_with_branch=employee.branch) |
            Q(is_shared=True, shared_with_department=employee.department)
        ).distinct()
        
        for loc in locations:
            check = is_within_radius(
                lat, lng,
                float(loc.latitude), float(loc.longitude),
                loc.radius or 500,
            )
            if check['is_within']:
                return {
                    'id': loc.id,
                    'name': loc.name,
                    'type': loc.location_type,
                    'type_display': loc.get_location_type_display(),
                    'distance_meters': check['distance_meters'],
                }
    except Exception:
        pass
    
    return None


def _get_active_field_visit(employee):
    try:
        from attendance.models import LocationCheckIn
        active = LocationCheckIn._base_manager.filter(
            employee=employee,
            status__in=['arrived', 'in_progress'],
        ).first()
        
        if active:
            return {
                'id': active.id,
                'location_name': active.location_name,
                'purpose': active.purpose or '',
                'arrival_time': timezone.localtime(active.arrival_time).strftime('%I:%M %p') if active.arrival_time else None,
            }
    except Exception:
        pass
    
    return None


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_history(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    records = Attendance._base_manager.filter(employee=employee).order_by('-date')[:30]

    items = [attendance_to_dict(record) for record in records]

    return Response({
        'success': True,
        'count': len(items),
        'items': items
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_change_password(request):
    """تغيير كلمة المرور من تطبيق الموبايل"""
    user = request.user
    current_password = request.data.get('current_password', '').strip()
    new_password = request.data.get('new_password', '').strip()

    if not current_password or not new_password:
        return Response({
            'success': False,
            'message': 'كلمة المرور الحالية والجديدة مطلوبتان'
        }, status=400)

    if len(new_password) < 6:
        return Response({
            'success': False,
            'message': 'كلمة المرور الجديدة لازم تكون 6 أحرف على الأقل'
        }, status=400)

    if not user.check_password(current_password):
        return Response({
            'success': False,
            'message': 'كلمة المرور الحالية غير صحيحة'
        }, status=400)

    if current_password == new_password:
        return Response({
            'success': False,
            'message': 'كلمة المرور الجديدة لازم تختلف عن الحالية'
        }, status=400)

    user.set_password(new_password)
    user.must_change_password = False
    user.save()

    Token._base_manager.filter(user=user).delete()
    new_token = Token._base_manager.create(user=user)

    return Response({
        'success': True,
        'message': 'تم تغيير كلمة المرور بنجاح',
        'token': new_token.key,
    })



@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_logout(request):
    """تسجيل الخروج وحذف التوكن"""
    try:
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        return Response({'success': True, 'message': 'تم تسجيل الخروج بنجاح'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)

# ==================== GEOFENCE APIs ====================

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_geofence_get(request):
    """جلب إعدادات النطاق الجغرافي للشركة"""
    user = request.user
    employee = get_employee_for_user(user)

    company = None
    if employee and getattr(employee, 'company', None):
        company = employee.company
    elif hasattr(user, 'company') and user.company:
        company = user.company

    if not company:
        return Response({'success': False, 'message': 'الشركة غير موجودة'}, status=404)

    return Response({
        'success': True,
        'geofence': {
            'latitude': float(company.office_latitude) if company.office_latitude else None,
            'longitude': float(company.office_longitude) if company.office_longitude else None,
            'radius': company.geofence_radius or 100,
            'enabled': company.geofence_enabled,
            'address': company.office_address or '',
        }
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_geofence_set(request):
    """حفظ موقع الشركة من الموبايل (للمدير فقط)"""
    user = request.user
    role = getattr(user, 'role', 'employee') or 'employee'
    manager_roles = ['super_admin', 'company_admin', 'hr_manager', 'manager']

    if role not in manager_roles:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    radius = request.data.get('radius', 100)
    enabled = request.data.get('enabled', True)
    address = request.data.get('address', '')

    if latitude is None or longitude is None:
        return Response({'success': False, 'message': 'الإحداثيات مطلوبة'}, status=400)

    employee = get_employee_for_user(user)
    company = None
    if employee and getattr(employee, 'company', None):
        company = employee.company
    elif hasattr(user, 'company') and user.company:
        company = user.company

    if not company:
        return Response({'success': False, 'message': 'الشركة غير موجودة'}, status=404)

    try:
        company.office_latitude = latitude
        company.office_longitude = longitude
        company.geofence_radius = int(radius)
        company.geofence_enabled = bool(enabled)
        if address:
            company.office_address = address
        company.save()

        return Response({
            'success': True,
            'message': 'تم حفظ موقع الشركة بنجاح',
            'geofence': {
                'latitude': float(company.office_latitude),
                'longitude': float(company.office_longitude),
                'radius': company.geofence_radius,
                'enabled': company.geofence_enabled,
                'address': company.office_address,
            }
        })
    except Exception as e:
        return Response({'success': False, 'message': f'خطأ في الحفظ: {str(e)}'}, status=500)


def calculate_distance(lat1, lng1, lat2, lng2):
    """حساب المسافة بين نقطتين بالمتر"""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    lat1_rad = radians(float(lat1))
    lat2_rad = radians(float(lat2))
    delta_lat = radians(float(lat2) - float(lat1))
    delta_lng = radians(float(lng2) - float(lng1))

    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# ============================================================
# FCM Token Management (Firebase Cloud Messaging)
# ============================================================
from accounts.fcm_models import FCMDeviceToken


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_fcm_token_register(request):
    """حفظ FCM Token للمستخدم — مع refresh تلقائي لو التوكن اتغير"""
    try:
        user = request.user
        fcm_token = request.data.get('fcm_token', '').strip()
        platform = request.data.get('platform', 'android')
        device_info = request.data.get('device_info', '')
        preferred_language = request.data.get('preferred_language', 'ar')

        if not fcm_token:
            return Response({
                'success': False,
                'message': 'FCM token مطلوب'
            }, status=400)

        # تحديث Employee.language عشان تبقى مصدر الحقيقة للإشعارات
        try:
            emp = Employee._base_manager.filter(user=user).first()
            if emp and preferred_language in ('ar', 'en'):
                if emp.language != preferred_language:
                    emp.language = preferred_language
                    emp.save(update_fields=['language'])
        except Exception as _lang_err:
            import logging
            logging.getLogger(__name__).warning(f'Employee.language update error: {_lang_err}')

        # لو نفس التوكن موجود لحد تاني، امسحه
        FCMDeviceToken._base_manager.filter(fcm_token=fcm_token).exclude(user=user).delete()

        # لو عندنا توكن قديم لنفس الـ user على نفس الجهاز، حدّثه
        # لو التوكن نفسه موجود، update_or_create بالتوكن
        # لو التوكن اتغير (refresh)، شيل القديم وحط الجديد
        existing = FCMDeviceToken._base_manager.filter(user=user, platform=platform).first()
        if existing and existing.fcm_token != fcm_token:
            existing.fcm_token = fcm_token
            existing.device_info = device_info
            existing.preferred_language = preferred_language
            existing.is_active = True
            existing.save(update_fields=['fcm_token', 'device_info', 'preferred_language', 'is_active'])
            created = False
            token_obj = existing
        else:
            token_obj, created = FCMDeviceToken._base_manager.update_or_create(
                fcm_token=fcm_token,
                defaults={
                    'user': user,
                    'platform': platform,
                    'device_info': device_info,
                    'preferred_language': preferred_language,
                    'is_active': True,
                }
            )

        return Response({
            'success': True,
            'message': 'تم حفظ التوكن بنجاح' if created else 'تم تحديث التوكن',
            'created': created,
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_fcm_token_delete(request):
    """حذف FCM Token عند تسجيل الخروج"""
    try:
        fcm_token = request.data.get('fcm_token', '').strip()
        if fcm_token:
            FCMDeviceToken._base_manager.filter(
                user=request.user,
                fcm_token=fcm_token
            ).delete()
        return Response({'success': True, 'message': 'تم حذف التوكن'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)

# ============================================================
# Device Approval Workflow
# ============================================================
from accounts.fcm_models import TrustedDevice

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_device_register(request):
    """تسجيل جهاز جديد — أول جهاز يتعمد تلقائياً، الجهاز الجديد يحتاج موافقة"""
    try:
        from django.utils import timezone as tz
        from accounts.fcm_service import send_notification_to_managers
        from accounts.fcm_models import TrustedDevice

        user = request.user
        device_id = request.data.get('device_id', '').strip()
        device_name = request.data.get('device_name', '').strip()
        platform = request.data.get('platform', 'android')

        if not device_id:
            return Response({'success': False, 'message': 'device_id مطلوب'}, status=400)

        # ─── منع تعدد الحسابات على نفس الجهاز ───
        other_user_device = TrustedDevice._base_manager.filter(
            device_id=device_id
        ).exclude(user=user).first()

        if other_user_device:
            # نبعت إشعار للمديرين إن في نشاط مشبوه
            emp = Employee._base_manager.filter(user=user).first()
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else user.username
            other_emp = Employee._base_manager.filter(user=other_user_device.user).first()
            other_name = f"{getattr(other_emp, 'first_name_ar', '')} {getattr(other_emp, 'last_name_ar', '')}".strip() if other_emp else other_user_device.user.username
            try:
                from accounts.fcm_service import send_notification_to_managers
                send_notification_to_managers(
                    company=getattr(user, 'company', None),
                    title='🚨 نشاط مشبوه — تعدد حسابات',
                    body=f'الجهاز نفسه مسجل باسم {other_name} وحاول الدخول باسم {emp_name}',
                    data={
                        'type': 'suspicious_device_activity',
                        'screen': 'trusted_devices',
                        'device_id': device_id[:20],
                        'user_id': str(user.id),
                    },
                )
            except Exception:
                pass

            return Response({
                'success': False,
                'status': 'suspicious',
                'auto_attendance_enabled': False,
                'message': 'هذا الجهاز مسجل بحساب آخر — تم إبلاغ المدير',
            }, status=403)
        # ─────────────────────────────────────────────

        # هل الجهاز ده موجود قبل كده؟
        existing = TrustedDevice._base_manager.filter(user=user, device_id=device_id).first()
        if existing:
            existing.last_login_at = tz.now()
            existing.save(update_fields=['last_login_at'])
            return Response({
                'success': True,
                'status': existing.status,
                'auto_attendance_enabled': existing.auto_attendance_enabled,
                'message': 'جهاز موجود بالفعل',
                'is_new': False,
            })

        # هل ده أول جهاز للموظف؟
        existing_devices = TrustedDevice._base_manager.filter(user=user)
        is_first = not existing_devices.exists()

        status = 'approved' if is_first else 'pending'
        auto_attendance = is_first

        device = TrustedDevice._base_manager.create(
            user=user,
            device_id=device_id,
            device_name=device_name or f'{platform} device',
            platform=platform,
            status=status,
            is_first_device=is_first,
            auto_attendance_enabled=auto_attendance,
            approved_by=user if is_first else None,
            approved_at=tz.now() if is_first else None,
            last_login_at=tz.now(),
        )

        # لو جهاز جديد مش الأول → نبعت إشعار للمديرين
        if not is_first:
            emp = Employee._base_manager.filter(user=user).first()
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else user.username
            try:
                send_notification_to_managers(
                    company=getattr(user, 'company', None),
                    title=f'🔔 جهاز جديد — {emp_name}',
                    body=f'الموظف {emp_name} دخل من جهاز جديد ويحتاج موافقة. الجهاز: {device_name or device_id[:20]}',
                    data={
                        'type': 'new_device_approval',
                        'screen': 'trusted_devices',
                        'device_id': str(device.id),
                        'user_id': str(user.id),
                    },
                )
            except Exception:
                pass

        return Response({
            'success': True,
            'status': status,
            'auto_attendance_enabled': auto_attendance,
            'is_new': True,
            'is_first_device': is_first,
            'message': 'تم تسجيل الجهاز بنجاح' if is_first else 'طلب تسجيل الجهاز في انتظار موافقة المدير',
        })

    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_device_status(request):
    """حالة الجهاز الحالي"""
    try:
        from accounts.fcm_models import TrustedDevice
        device_id = request.query_params.get('device_id', '').strip()
        if not device_id:
            return Response({'success': False, 'message': 'device_id مطلوب'}, status=400)

        device = TrustedDevice._base_manager.filter(user=request.user, device_id=device_id).first()
        if not device:
            return Response({'success': False, 'status': 'not_registered', 'auto_attendance_enabled': False})

        return Response({
            'success': True,
            'status': device.status,
            'auto_attendance_enabled': device.auto_attendance_enabled,
            'is_first_device': device.is_first_device,
            'device_name': device.device_name,
            'created_at': str(device.created_at)[:10],
        })
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_devices_list(request):
    """قائمة أجهزة الموظفين — للمدير"""
    try:
        from accounts.fcm_models import TrustedDevice
        from attendance.api_reports import _check_manager
        if not _check_manager(request.user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)

        company = getattr(request.user, 'company', None)
        status_filter = request.query_params.get('status', None)

        qs = TrustedDevice._base_manager.filter(
            user__company=company
        ).select_related('user', 'approved_by').order_by('-created_at')

        if status_filter:
            qs = qs.filter(status=status_filter)

        results = []
        for d in qs:
            emp = Employee._base_manager.filter(user=d.user).first()
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else d.user.username
            results.append({
                'id': d.id,
                'employee_name': emp_name,
                'username': d.user.username,
                'device_name': d.device_name,
                'device_id': d.device_id[:20] + '...' if len(d.device_id) > 20 else d.device_id,
                'platform': d.platform,
                'status': d.status,
                'is_first_device': d.is_first_device,
                'auto_attendance_enabled': d.auto_attendance_enabled,
                'created_at': str(d.created_at)[:16],
                'last_login_at': str(d.last_login_at)[:16] if d.last_login_at else '',
            })

        return Response({'success': True, 'count': len(results), 'results': results})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_device_action(request, device_id):
    """موافقة / رفض / إلغاء جهاز — للمدير"""
    try:
        from accounts.fcm_models import TrustedDevice
        from django.utils import timezone as tz
        from attendance.api_reports import _check_manager
        from accounts.fcm_service import send_notification_to_user

        if not _check_manager(request.user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)

        action = request.data.get('action', '').strip()
        if action not in ('approve', 'reject', 'revoke'):
            return Response({'success': False, 'message': 'action لازم يكون approve / reject / revoke'}, status=400)

        device = TrustedDevice._base_manager.filter(id=device_id).first()
        if not device:
            return Response({'success': False, 'message': 'الجهاز مش موجود'}, status=404)

        if action == 'approve':
            device.status = 'approved'
            device.auto_attendance_enabled = True
            device.approved_by = request.user
            device.approved_at = tz.now()
            msg_ar = 'تم اعتماد جهازك وتفعيل الحضور التلقائي'
            msg_en = 'Your device has been approved and auto attendance is enabled'
        elif action == 'reject':
            device.status = 'rejected'
            device.auto_attendance_enabled = False
            msg_ar = 'تم رفض طلب اعتماد جهازك'
            msg_en = 'Your device registration request has been rejected'
        else:  # revoke
            device.status = 'revoked'
            device.auto_attendance_enabled = False
            msg_ar = 'تم إلغاء صلاحية جهازك'
            msg_en = 'Your device access has been revoked'

        device.save()

        # إشعار الموظف
        try:
            send_notification_to_user(
                user=device.user,
                title='📱 ' + msg_ar,
                body=f'الجهاز: {device.device_name}',
                data={'type': 'device_status_update', 'status': device.status},
                title_en='📱 ' + msg_en,
                body_en=f'Device: {device.device_name}',
            )
        except Exception:
            pass

        return Response({
            'success': True,
            'message': msg_ar,
            'status': device.status,
            'auto_attendance_enabled': device.auto_attendance_enabled,
        })
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)




@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_notifications_list(request):
    """جلب إشعارات المستخدم الحالي"""
    from accounts.fcm_models import NotificationLog

    qs = NotificationLog._base_manager.filter(user=request.user).order_by('-id')[:50]
    notifications = []
    for n in qs:
        notifications.append({
            'id': n.id,
            'title': n.title,
            'body': n.body,
            'notification_type': n.notification_type,
            'is_read': n.is_read,
            'data': n.data or {},
            'created_at': timezone.localtime(n.created_at).isoformat(),
        })

    unread_count = NotificationLog._base_manager.filter(user=request.user, is_read=False).count()

    return Response({
        'success': True,
        'unread_count': unread_count,
        'notifications': notifications,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_notifications_mark_read(request):
    """تعليم إشعار كمقروء أو تعليم الكل"""
    from accounts.fcm_models import NotificationLog

    notification_id = request.data.get('id')

    if notification_id:
        updated = NotificationLog._base_manager.filter(
            user=request.user,
            id=notification_id
        ).update(is_read=True)

        return Response({
            'success': updated > 0,
            'message': 'تم تحديث الإشعار' if updated else 'الإشعار غير موجود'
        }, status=200 if updated else 404)

    updated = NotificationLog._base_manager.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return Response({
        'success': True,
        'message': 'تم تعليم كل الإشعارات كمقروءة',
        'updated': updated
    })


# ============================================================
#                    Charter / اللائحة
# ============================================================

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_get(request):
    """جلب اللائحة الحالية للموظف أو المدير"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

    charter = WorkCharter._base_manager.filter(company=company, is_active=True).first()

    if not charter:
        return Response({
            'success': True,
            'has_charter': False,
            'needs_acceptance': False,
            'charter': None,
            'accepted': False,
            'accepted_at': None,
        })

    accepted = False
    accepted_at = None

    if employee:
        acceptance = CharterAcceptance._base_manager.filter(employee=employee, charter=charter).first()
        if acceptance:
            accepted = True
            accepted_at = acceptance.accepted_at.isoformat() if acceptance.accepted_at else None

    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

    return Response({
        'success': True,
        'has_charter': True,
        'needs_acceptance': charter.is_mandatory and not accepted,
        'charter': {
            'id': charter.id,
            'title': charter.title,
            'introduction': charter.introduction or '',
            'content': charter.content or '',
            'version': charter.version,
            'is_mandatory': charter.is_mandatory,
            'attachment_url': attachment_url,
            'attachment_name': attachment_name,
        },
        'accepted': accepted,
        'accepted_at': accepted_at,
    })

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_accept(request):
    """الموظف يوافق على اللائحة"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    company = getattr(user, 'company', None) or getattr(Employee._base_manager.filter(user=user).first(), 'company', None) or getattr(Employee._base_manager.filter(user=user).first(), 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

    charter = WorkCharter._base_manager.filter(company=company, is_active=True).first()

    if not charter:
        return Response({'success': False, 'error': 'لا توجد لائحة فعالة'}, status=404)

    employee = Employee._base_manager.filter(user=user).first()

    if not employee:
        return Response({'success': False, 'error': 'لم يتم العثور على الموظف'}, status=404)

    acceptance, created = CharterAcceptance._base_manager.get_or_create(
        employee=employee,
        charter=charter,
        defaults={
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
        }
    )

    try:
        from accounts.fcm_models import NotificationLog
        emp_name = user.get_full_name() or user.username
        from django.contrib.auth import get_user_model
        User = get_user_model()
        managers = User._base_manager.filter(is_staff=True, is_active=True)
        for mgr in managers:
            NotificationLog._base_manager.create(
                user=mgr,
                title='✅ موافقة على اللائحة',
                body=f'الموظف {emp_name} وافق على: {charter.title}',
                notification_type='general',
            )
    except Exception:
        pass

    return Response({
        'success': True,
        'message': 'تم تسجيل موافقتك بنجاح',
        'already_accepted': not created,
        'accepted_at': acceptance.accepted_at.isoformat() if acceptance.accepted_at else None,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_acceptances(request):
    """المدير يشوف مين وافق ومين لسه - للطباعة"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in ['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager']):
        return Response({'success': False, 'error': 'غير مصرح'}, status=403)

    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة'}, status=400)

    charter = WorkCharter._base_manager.filter(company=company, is_active=True).first()
    if not charter:
        return Response({'success': False, 'error': 'لا توجد لائحة'}, status=404)

    all_employees = Employee._base_manager.filter(
        company=company, status='active'
    ).select_related('user').order_by('user__first_name')

    acceptances = {
        a.employee_id: a
        for a in CharterAcceptance._base_manager.filter(charter=charter)
    }

    accepted_list = []
    pending_list = []

    for emp in all_employees:
        emp_data = {
            'id': emp.id,
            'name': emp.user.get_full_name() or emp.user.username,
            'username': emp.user.username,
        }
        acc = acceptances.get(emp.id)
        if acc:
            emp_data['accepted_at'] = acc.accepted_at.isoformat() if acc.accepted_at else ''
            emp_data['ip_address'] = str(acc.ip_address) if acc.ip_address else ''
            accepted_list.append(emp_data)
        else:
            pending_list.append(emp_data)

    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

    return Response({
        'success': True,
        'charter_title': charter.title,
        'charter_version': charter.version,
        'charter_content': charter.content or '',
        'attachment_url': attachment_url,
        'attachment_name': attachment_name,
        'print_date': timezone.now().isoformat(),
        'accepted': {'count': len(accepted_list), 'employees': accepted_list},
        'pending': {'count': len(pending_list), 'employees': pending_list},
    })

@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def mobile_charter_update(request):
    """المدير يعدل اللائحة + يرفع ملف مرفق"""
    import os
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in ['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager']):
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, "company", None) or getattr(employee, "company", None)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    charter = WorkCharter._base_manager.filter(company=company).first()

    attachment_file = request.FILES.get('attachment')
    remove_attachment = str(request.data.get('remove_attachment', '')).strip().lower() in ['1', 'true', 'yes', 'on']

    if attachment_file:
        ext = os.path.splitext(attachment_file.name.lower())[1]
        allowed = {'.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'}
        if ext not in allowed:
            return Response({
                "success": False,
                "error": "نوع الملف غير مدعوم. المسموح: PDF / Word / PNG / JPG"
            }, status=400)

        max_size = 10 * 1024 * 1024
        if attachment_file.size > max_size:
            return Response({
                "success": False,
                "error": "حجم الملف كبير. الحد الأقصى 10 MB"
            }, status=400)

    if not charter:
        charter = WorkCharter._base_manager.create(
            company=company,
            title=request.data.get("title", "لائحة الشركة"),
            content=request.data.get("content", ""),
            introduction=request.data.get("introduction", ""),
            is_active=True,
            is_mandatory=True,
            attachment=attachment_file if attachment_file else None,
        )

        attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
        attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

        return Response({
            "success": True,
            "message": "تم إنشاء اللائحة",
            "version": charter.version,
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        })

    content_changed = False
    settings_changed = False

    new_title = request.data.get("title", "").strip()
    if "title" in request.data and not new_title:
        return Response({"success": False, "error": "عنوان اللائحة لا يمكن أن يكون فارغاً"}, status=400)
    new_intro = request.data.get("introduction", "").strip()
    new_content = request.data.get("content", "").strip()

    if new_title and new_title != charter.title:
        charter.title = new_title
        content_changed = True

    if new_intro != (charter.introduction or ''):
        charter.introduction = new_intro
        content_changed = True

    if new_content and new_content != (charter.content or ''):
        charter.content = new_content
        content_changed = True

    if attachment_file:
        charter.attachment = attachment_file
        content_changed = True
    elif remove_attachment and getattr(charter, 'attachment', None):
        try:
            charter.attachment.delete(save=False)
        except Exception:
            pass
        charter.attachment = None
        content_changed = True

    if "is_active" in request.data:
        val = request.data["is_active"]
        new_val = val if isinstance(val, bool) else str(val).lower() == "true"
        if charter.is_active != new_val:
            charter.is_active = new_val
            settings_changed = True

    if "is_mandatory" in request.data:
        val = request.data["is_mandatory"]
        new_val = val if isinstance(val, bool) else str(val).lower() == "true"
        if charter.is_mandatory != new_val:
            charter.is_mandatory = new_val
            settings_changed = True

    charter.save()

    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

    if content_changed:
        charter.version += 1
        charter.save()
        deleted = CharterAcceptance._base_manager.filter(charter=charter).delete()

        return Response({
            "success": True,
            "message": f"تم تحديث اللائحة (الإصدار {charter.version}) وتم إعادة طلب الموافقة من جميع الموظفين",
            "version": charter.version,
            "acceptances_reset": deleted[0],
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        })

    if settings_changed:
        return Response({
            "success": True,
            "message": "تم حفظ إعدادات اللائحة",
            "version": charter.version,
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        })

    return Response({
        "success": True,
        "message": "لم يتم إجراء أي تغيير",
        "version": charter.version,
        "attachment_url": attachment_url,
        "attachment_name": attachment_name,
    })


def _notify_hr_incomplete_data(employee, missing):
    """
    Send notification to HR when employee has incomplete data
    (only once per day per employee)
    """
    try:
        from django.core.cache import cache
        cache_key = f'notify_hr_incomplete_{employee.id}_{timezone.localdate()}'
        if cache.get(cache_key):
            return
        cache.set(cache_key, True, 86400)  # 24 hours
        
        from accounts.fcm_service import send_notification_to_managers
        
        emp_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
        
        missing_labels_ar = []
        missing_labels_en = []
        if 'worker_type' in missing:
            missing_labels_ar.append('نوع الموظف')
            missing_labels_en.append('worker type')
        if 'shift' in missing:
            missing_labels_ar.append('الشيفت')
            missing_labels_en.append('shift')
        
        title = 'موظف بيانات ناقصة'
        body = f'[{emp_name}] لم يستطع استخدام التطبيق - ناقص: {", ".join(missing_labels_ar)}'
        
        send_notification_to_managers(
            employee.company,
            title, body,
            data={
                'type': 'employee_incomplete_data',
                'employee_id': str(employee.id),
                'employee_name': emp_name,
                'missing': ','.join(missing),
            },
            title_en='Employee Data Incomplete',
            body_en=f'[{emp_name}] cannot use the app - missing: {", ".join(missing_labels_en)}',
        )
    except Exception:
        pass



def _can_track_location(employee):
    """
    يتأكد هل مسموح نسجل موقع الموظف دلوقتي:
    - الميداني (field_free / field_assigned): مسموح دايماً
    - المكتبي (office): بس لو عنده حضور مفتوح (لسه ماسجلش انصراف)
      أو خلال 30 دقيقة قبل بداية شيفته الرسمي
    """
    worker_type = getattr(employee, 'worker_type', None)
    if worker_type != 'office':
        return True
    try:
        from attendance.models import Attendance
        today = timezone.localdate()
        att = Attendance._base_manager.filter(employee=employee, date=today).first()
        if att and att.check_in_time and not att.check_out_time:
            return True
        from attendance.payroll_rules import _get_shift_for_date
        shift = _get_shift_for_date(employee, today)
        if shift and shift.start_time and shift.end_time:
            from datetime import datetime, timedelta
            now_local = timezone.localtime(timezone.now())
            shift_start_dt = datetime.combine(now_local.date(), shift.start_time)
            shift_end_dt = datetime.combine(now_local.date(), shift.end_time)
            if shift_end_dt <= shift_start_dt:
                shift_end_dt += timedelta(days=1)
            grace_start = shift_start_dt - timedelta(minutes=30)
            grace_end = shift_end_dt + timedelta(minutes=30)
            now_naive = now_local.replace(tzinfo=None)
            if grace_start <= now_naive <= grace_end:
                return True
        return False
    except Exception:
        return True
