from .fcm_logic import notify_managers, notify_employee_checkin, notify_employee_checkout, notify_manager_checkin, notify_manager_checkout
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate
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



def get_active_shift(employee, day):
    from django.db.models import Q
    from attendance.models import ShiftOverride, EmployeeShift, Shift

    # 1. شوف لو فيه override لليوم ده
    override = ShiftOverride._base_manager.filter(
        employee=employee,
        override_date=day,
        company=employee.company
    ).select_related('shift').first()
    if override:
        return override.shift

    # 2. شوف EmployeeShift للموظف نفسه
    assignment = EmployeeShift._base_manager.filter(
        company=employee.company,
        employee=employee,
        is_active=True,
        start_date__lte=day,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=day)
    ).select_related("shift").order_by("priority", "-start_date").first()

    if assignment:
        return assignment.shift

    # 3. لو مفيش شيء، دور على default shift للشركة
    default_shift = Shift._base_manager.filter(
        company=employee.company,
        is_default=True,
        is_active=True
    ).first()
    return default_shift


def get_shift_bounds(shift, day):
    from datetime import datetime, timedelta

    if not shift or not shift.start_time or not shift.end_time:
        return None, None

    start_dt = datetime.combine(day, shift.start_time)
    end_dt = datetime.combine(day, shift.end_time)

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

    token, _ = Token.objects.get_or_create(user=user)
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


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_send_location(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    accuracy = request.data.get('accuracy', 0)

    if latitude in [None, ''] or longitude in [None, '']:
        return Response({'success': False, 'message': 'خط العرض وخط الطول مطلوبان'}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy or 0)
    except Exception:
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)

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


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
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
        return Response({'success': False, 'message': 'خط العرض وخط الطول مطلوبان'}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy or 0)
    except Exception:
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)

    today = timezone.localdate()
    now = timezone.now()

    attendance = Attendance._base_manager.filter(employee=employee, date=today).first()

    active_shift = get_active_shift(employee, today)
    shift_start, shift_end = get_shift_bounds(active_shift, today)

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

    if action == 'check_in':
        try:
            company = employee.company
            is_field = getattr(employee, 'is_field_worker', False)

            if not is_field and company and company.geofence_enabled:
                if company.office_latitude and company.office_longitude:
                    distance = calculate_distance(
                        latitude, longitude,
                        company.office_latitude, company.office_longitude
                    )
                    allowed_radius = company.geofence_radius or 100

                    if distance > allowed_radius:
                        return Response({
                            'success': False,
                            'message': f'أنت خارج نطاق الشركة!\nالمسافة الحالية: {int(distance)} متر\nالنطاق المسموح: {allowed_radius} متر',
                            'out_of_range': True,
                            'distance': int(distance),
                            'allowed_radius': allowed_radius,
                        }, status=400)
        except Exception as e:
            pass

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
        today = timezone.localdate()
        shift = get_active_shift(employee, today)

        if shift and shift.start_time and shift.end_time:
            start_dt = datetime.combine(today, shift.start_time)
            end_dt = datetime.combine(today, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            mode = getattr(employee, 'attendance_mode', 'fixed_shift')
            if mode == 'flexible_hours' and attendance and attendance.check_in_time:
                check_in_local = timezone.localtime(attendance.check_in_time)
                shift_duration = (end_dt - start_dt).total_seconds()
                end_time_aware = check_in_local + timedelta(seconds=shift_duration)
            else:
                end_time_aware = timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt

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

    if shift_end and now < shift_end:
        early_leave_minutes = int((shift_end - now).total_seconds() // 60)

    attendance.early_leave_minutes = early_leave_minutes

    if early_permission_covers:
        attendance.check_out_notes = "تم استخدام إذن خروج مبكر معتمد"

    attendance.calculate_work_hours()
    attendance.save()

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
        notify_manager_checkout(employee.company, emp_name, format_time_value(now))
    except Exception as e:
        print(f"Check-out notification error: {e}")

    return Response(response_data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_status(request):
    from datetime import datetime, timedelta, time as dt_time
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    today = timezone.localdate()
    attendance = Attendance._base_manager.filter(employee=employee, date=today).first()
    today_dict = attendance_to_dict(attendance)

    shift_start_str = ''
    shift_end_str = ''
    shift_name = ''
    shift_end_timestamp = None
    shift_duration_seconds = 0
    remaining_seconds = 0
    can_check_out = False
    has_early_leave = False

    try:
        shift = get_active_shift(employee, today)

        if shift:
            shift_name = shift.name
            if shift.start_time:
                shift_start_str = shift.start_time.strftime('%H:%M')
            if shift.end_time:
                shift_end_str = shift.end_time.strftime('%H:%M')

            if shift.start_time and shift.end_time:
                start_dt = datetime.combine(today, shift.start_time)
                end_dt = datetime.combine(today, shift.end_time)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                shift_duration_seconds = int((end_dt - start_dt).total_seconds())

                if attendance and attendance.check_in_time:
                    check_in_local = timezone.localtime(attendance.check_in_time)
                    mode = getattr(employee, 'attendance_mode', 'fixed_shift')
                    if mode == 'flexible_hours':
                        end_time_dt = check_in_local + timedelta(seconds=shift_duration_seconds)
                    else:
                        end_time_dt = timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt

                    shift_end_timestamp = end_time_dt.isoformat()
                    now = timezone.now()
                    remaining = (end_time_dt - now).total_seconds()
                    remaining_seconds = max(0, int(remaining))
                    can_check_out = remaining_seconds <= 0
    except Exception as e:
        pass

    try:
        from requests_app.models import EmployeeRequest, RequestType
        early_leave_types = RequestType._base_manager.filter(
            company=employee.company,
            name__icontains='خروج مبكر'
        ).values_list('id', flat=True)
        if early_leave_types:
            has_early_leave = EmployeeRequest._base_manager.filter(
                employee=employee,
                request_type__id__in=list(early_leave_types),
                created_at__date=today,
                status='approved'
            ).exists()
    except Exception:
        pass

    if has_early_leave:
        can_check_out = True

    # بيانات الخروج الجزئي
    allow_partial_checkout = False
    shift_mode = 'fixed'
    sessions_today = 0
    has_open_session = False
    can_partial_checkout = False
    can_resume = False

    try:
        if shift:
            allow_partial_checkout = getattr(shift, 'allow_partial_checkout', False)
            shift_mode = getattr(shift, 'shift_mode', 'fixed')

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
        'sessions_today': sessions_today,
        'has_open_session': has_open_session,
        'can_partial_checkout': can_partial_checkout,
        'can_resume': can_resume,
        'today': today_dict,
    }
    return Response(response_data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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

    from rest_framework.authtoken.models import Token
    Token.objects.filter(user=user).delete()
    new_token = Token.objects.create(user=user)

    return Response({
        'success': True,
        'message': 'تم تغيير كلمة المرور بنجاح',
        'token': new_token.key,
    })


# ==================== GEOFENCE APIs ====================

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_fcm_token_register(request):
    """حفظ FCM Token للمستخدم"""
    try:
        fcm_token = request.data.get('fcm_token', '').strip()
        platform = request.data.get('platform', 'android')
        device_info = request.data.get('device_info', '')
        preferred_language = request.data.get('preferred_language', 'ar')

        if not fcm_token:
            return Response({
                'success': False,
                'message': 'FCM token مطلوب'
            }, status=400)

        user = request.user

        FCMDeviceToken.objects.filter(fcm_token=fcm_token).exclude(user=user).delete()

        token_obj, created = FCMDeviceToken.objects.update_or_create(
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_fcm_token_delete(request):
    """حذف FCM Token عند تسجيل الخروج"""
    try:
        fcm_token = request.data.get('fcm_token', '').strip()
        if fcm_token:
            FCMDeviceToken.objects.filter(
                user=request.user,
                fcm_token=fcm_token
            ).delete()
        return Response({'success': True, 'message': 'تم حذف التوكن'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_notifications_list(request):
    """جلب إشعارات المستخدم الحالي"""
    from accounts.fcm_models import NotificationLog

    qs = NotificationLog.objects.filter(user=request.user).order_by('-id')[:50]
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

    unread_count = NotificationLog.objects.filter(user=request.user, is_read=False).count()

    return Response({
        'success': True,
        'unread_count': unread_count,
        'notifications': notifications,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_notifications_mark_read(request):
    """تعليم إشعار كمقروء أو تعليم الكل"""
    from accounts.fcm_models import NotificationLog

    notification_id = request.data.get('id')

    if notification_id:
        updated = NotificationLog.objects.filter(
            user=request.user,
            id=notification_id
        ).update(is_read=True)

        return Response({
            'success': updated > 0,
            'message': 'تم تحديث الإشعار' if updated else 'الإشعار غير موجود'
        }, status=200 if updated else 404)

    updated = NotificationLog.objects.filter(
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_get(request):
    """جلب اللائحة الحالية للموظف أو المدير"""
    from companies.models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    user = request.user
    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

    charter = WorkCharter.objects.filter(company=company, is_active=True).first()

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
        acceptance = CharterAcceptance.objects.filter(employee=employee, charter=charter).first()
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_accept(request):
    """الموظف يوافق على اللائحة"""
    from companies.models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    user = request.user
    company = getattr(user, 'company', None) or getattr(Employee._base_manager.filter(user=user).first(), 'company', None) or getattr(Employee._base_manager.filter(user=user).first(), 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

    charter = WorkCharter.objects.filter(company=company, is_active=True).first()

    if not charter:
        return Response({'success': False, 'error': 'لا توجد لائحة فعالة'}, status=404)

    employee = Employee._base_manager.filter(user=user).first()

    if not employee:
        return Response({'success': False, 'error': 'لم يتم العثور على الموظف'}, status=404)

    acceptance, created = CharterAcceptance.objects.get_or_create(
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
        managers = User.objects.filter(is_staff=True, is_active=True)
        for mgr in managers:
            NotificationLog.objects.create(
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_acceptances(request):
    """المدير يشوف مين وافق ومين لسه - للطباعة"""
    from companies.models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in ['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager']):
        return Response({'success': False, 'error': 'غير مصرح'}, status=403)

    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة'}, status=400)

    charter = WorkCharter.objects.filter(company=company, is_active=True).first()
    if not charter:
        return Response({'success': False, 'error': 'لا توجد لائحة'}, status=404)

    all_employees = Employee._base_manager.filter(
        company=company, is_active=True
    ).select_related('user').order_by('user__first_name')

    acceptances = {
        a.employee_id: a
        for a in CharterAcceptance.objects.filter(charter=charter)
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def mobile_charter_update(request):
    """المدير يعدل اللائحة + يرفع ملف مرفق"""
    import os
    from companies.models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in ['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager']):
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, "company", None) or getattr(employee, "company", None)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    charter = WorkCharter.objects.filter(company=company).first()

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
        charter = WorkCharter.objects.create(
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
        deleted = CharterAcceptance.objects.filter(charter=charter).delete()

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

