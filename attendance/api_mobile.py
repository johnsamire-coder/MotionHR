from .fcm_logic import notify_managers
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
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
                status='present'
            )
        else:
            attendance.company = employee.company
            attendance.check_in_time = now
            attendance.check_in_latitude = latitude
            attendance.check_in_longitude = longitude
            attendance.check_in_address = reverse_geocode(latitude, longitude)
            attendance.check_in_within_range = True
            attendance.status = 'present'
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

        return Response({
            'success': True,
            'message': 'تم تسجيل الحضور بنجاح',
            'action': 'check_in',
            'time': format_time_value(now),
            'today': attendance_to_dict(attendance)
        })

    from datetime import datetime, timedelta
    try:
        from attendance.models import EmployeeShift
        emp_shift = EmployeeShift._base_manager.filter(
            employee=employee
        ).order_by('-start_date').first()

        if emp_shift and emp_shift.shift and emp_shift.shift.start_time and emp_shift.shift.end_time:
            shift = emp_shift.shift
            today = timezone.localdate()
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
                has_early_leave = False
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

                if not has_early_leave:
                    remaining = int((end_time_aware - now).total_seconds())
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60
                    return Response({
                        'success': False,
                        'message': f'لسه بدري ع الانصراف يا نجم، فاضل {hours} ساعة و {minutes} دقيقة.\nلو محتاج تخرج بدري، قدم طلب إذن خروج مبكر.',
                        'shift_not_ended': True,
                        'remaining_seconds': remaining,
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
    attendance.save()

    LocationLog._base_manager.create(
        company=employee.company,
        employee=employee,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        timestamp=now
    )

    return Response({
        'success': True,
        'message': 'تم تسجيل الانصراف بنجاح',
        'action': 'check_out',
        'time': format_time_value(now),
        'today': attendance_to_dict(attendance)
    })


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
        from attendance.models import EmployeeShift
        emp_shift = EmployeeShift._base_manager.filter(
            employee=employee
        ).order_by('-start_date').first()

        if emp_shift and emp_shift.shift:
            shift = emp_shift.shift
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
