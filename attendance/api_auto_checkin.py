"""
MotionHR - Auto Check-in / Check-out API
Phase 14: تسجيل حضور وانصراف أوتوماتيك - Bilingual AR/EN
"""
import math
from datetime import datetime, date, time
from django.db import models
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Attendance

# ─────────────────────────────────────────
# الرسائل AR/EN
# ─────────────────────────────────────────
MESSAGES = {
    'checked_in': {
        'ar': 'تم تسجيل حضورك تلقائياً ✅',
        'en': 'Attendance recorded automatically ✅',
    },
    'checked_in_late': {
        'ar': 'تم تسجيل حضورك — تأخير {minutes} دقيقة ⚠️',
        'en': 'Checked in — {minutes} minutes late ⚠️',
    },
    'checked_out': {
        'ar': 'تم تسجيل انصرافك تلقائياً ✅',
        'en': 'Check-out recorded automatically ✅',
    },
    'already_checked_in': {
        'ar': 'تم تسجيل الحضور مسبقاً',
        'en': 'Already checked in today',
    },
    'out_of_range': {
        'ar': 'أنت خارج نطاق موقع العمل',
        'en': 'You are outside the work location range',
    },
    'still_inside': {
        'ar': 'لا يزال داخل نطاق موقع العمل',
        'en': 'Still within work location range',
    },
    'no_checkin': {
        'ar': 'لم يتم تسجيل الحضور أو تم تسجيل الانصراف مسبقاً',
        'en': 'No check-in found or already checked out',
    },
    'not_checked_in': {
        'ar': 'لم يتم تسجيل الحضور بعد',
        'en': 'Not checked in yet',
    },
    'employee_not_found': {
        'ar': 'الموظف غير موجود',
        'en': 'Employee not found',
    },
    'invalid_coords': {
        'ar': 'إحداثيات غير صحيحة',
        'en': 'Invalid coordinates',
    },
    'coords_required': {
        'ar': 'يرجى إرسال الإحداثيات',
        'en': 'Latitude and longitude are required',
    },
}


def _msg(key, lang='ar', **kwargs):
    """جيب الرسالة بالغة المطلوبة"""
    lang = lang if lang in ('ar', 'en') else 'ar'
    text = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get('ar', key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def _get_user_lang(user, employee=None):
    """جيب لغة المستخدم من FCMDeviceToken أو Employee"""
    # أولاً من FCMDeviceToken
    try:
        from accounts.fcm_models import FCMDeviceToken
        token = FCMDeviceToken.objects.filter(user=user, is_active=True).first()
        lang = getattr(token, 'preferred_language', None)
        if lang in ('ar', 'en'):
            return lang
    except Exception:
        pass

    # ثانياً من Employee model
    if employee:
        lang = getattr(employee, 'language', None)
        if lang in ('ar', 'en'):
            return lang

    return 'ar'


def _haversine_distance(lat1, lon1, lat2, lon2):
    """المسافة بين نقطتين بالمتر"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_employee(user):
    try:
        from employees.models import Employee
        return Employee.objects.get(user=user)
    except Exception:
        return None


def _get_active_geofence(employee):
    try:
        from .models import Geofence
        company = getattr(employee, 'company', None)
        if company:
            return Geofence.objects.filter(company=company, is_active=True).first()
        return Geofence.objects.filter(is_active=True).first()
    except Exception:
        return None


def _get_employee_shift(employee):
    try:
        from .models import EmployeeShift
        today = date.today()
        emp_shift = EmployeeShift.objects.filter(
            employee=employee,
            is_active=True,
            start_date__lte=today,
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        ).select_related('shift').first()
        if emp_shift:
            return emp_shift.shift
    except Exception:
        pass
    try:
        from .models import Shift
        return Shift.objects.filter(is_active=True).first()
    except Exception:
        return None


def _calculate_late_minutes(shift, check_in_time):
    """حساب دقائق التأخير بناءً على الشيفت"""
    if not shift:
        return 0
    try:
        shift_start = shift.start_time
        grace = int(getattr(shift, 'grace_period', 15) or 15)

        if isinstance(shift_start, str):
            h, m = shift_start.split(':')
            shift_start = time(int(h), int(m))

        today = date.today()
        deadline_dt = datetime.combine(today, shift_start)
        total_grace_minutes = deadline_dt.minute + grace
        deadline_with_grace = deadline_dt.replace(
            hour=deadline_dt.hour + total_grace_minutes // 60,
            minute=total_grace_minutes % 60,
        )
        check_in_dt = datetime.combine(today, check_in_time)
        if check_in_dt > deadline_with_grace:
            delta = check_in_dt - deadline_with_grace
            return int(delta.total_seconds() / 60)
    except Exception:
        pass
    return 0


def _send_auto_checkin_notification(user, employee, lang, check_in_str, late_minutes):
    """FCM notification بعد auto check-in"""
    try:
        from .fcm_logic import send_fcm_notification
        if late_minutes > 0:
            title_ar = 'تسجيل حضور تلقائي ⚠️'
            body_ar = f'تم تسجيل حضورك في {check_in_str} — تأخير {late_minutes} دقيقة'
            title_en = 'Auto Check-in ⚠️'
            body_en = f'Checked in at {check_in_str} — {late_minutes} min late'
        else:
            title_ar = 'تسجيل حضور تلقائي ✅'
            body_ar = f'تم تسجيل حضورك في {check_in_str} بدون تأخير'
            title_en = 'Auto Check-in ✅'
            body_en = f'Checked in at {check_in_str} — on time'

        title = title_en if lang == 'en' else title_ar
        body = body_en if lang == 'en' else body_ar

        send_fcm_notification(
            user, title, body,
            data={'type': 'auto_checkin', 'action': 'checkin'},
            title_en=title_en,
            body_en=body_en,
        )
    except Exception as e:
        print(f'Auto check-in FCM error: {e}')


def _send_auto_checkout_notification(user, employee, lang, check_out_str, work_hours, overtime_hours):
    """FCM notification بعد auto check-out"""
    try:
        from .fcm_logic import send_fcm_notification
        title_ar = 'تسجيل انصراف تلقائي ✅'
        body_ar = f'تم تسجيل انصرافك في {check_out_str} — {work_hours} ساعة عمل'
        title_en = 'Auto Check-out ✅'
        body_en = f'Checked out at {check_out_str} — {work_hours} hours worked'

        if overtime_hours > 0:
            body_ar += f' (أوفرتايم: {overtime_hours} ساعة)'
            body_en += f' (Overtime: {overtime_hours} hrs)'

        title = title_en if lang == 'en' else title_ar
        body = body_en if lang == 'en' else body_ar

        send_fcm_notification(
            user, title, body,
            data={'type': 'auto_checkout', 'action': 'checkout'},
            title_en=title_en,
            body_en=body_en,
        )
    except Exception as e:
        print(f'Auto check-out FCM error: {e}')


# ─────────────────────────────────────────
# API Views
# ─────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def auto_check_in(request):
    """
    تسجيل حضور أوتوماتيك
    Body: { "latitude": ..., "longitude": ... }
    """
    user = request.user
    emp = _get_employee(user)
    lang = _get_user_lang(user, emp)

    if not emp:
        return Response({'error': _msg('employee_not_found', lang)}, status=404)

    lat = request.data.get('latitude')
    lon = request.data.get('longitude')

    if lat is None or lon is None:
        return Response({'error': _msg('coords_required', lang)}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return Response({'error': _msg('invalid_coords', lang)}, status=400)

    today = date.today()
    now = timezone.now()

    # هل عمل check-in النهارده؟
    existing = Attendance.objects.filter(
        employee=emp,
        date=today,
        check_in_time__isnull=False,
    ).first()

    if existing:
        return Response({
            'status': 'already_checked_in',
            'message': _msg('already_checked_in', lang),
            'check_in': existing.check_in_time.strftime('%H:%M') if existing.check_in_time else None,
        })

    # تحقق من الـ Geofence
    geofence = _get_active_geofence(emp)
    is_within = True
    distance = None

    if geofence and geofence.latitude and geofence.longitude:
        distance = _haversine_distance(
            lat, lon,
            float(geofence.latitude),
            float(geofence.longitude),
        )
        radius = float(getattr(geofence, 'radius', 100) or 100)
        is_within = distance <= radius

    if not is_within:
        return Response({
            'status': 'out_of_range',
            'message': _msg('out_of_range', lang),
            'distance_meters': round(distance, 1) if distance else None,
        }, status=400)

    # حساب التأخير
    shift = _get_employee_shift(emp)
    check_in_time = now.time().replace(microsecond=0)
    late_minutes = _calculate_late_minutes(shift, check_in_time)
    status_val = 'late' if late_minutes > 0 else 'present'
    check_in_str = check_in_time.strftime('%H:%M')

    # إنشاء أو تحديث سجل الحضور
    att, created = Attendance.objects.get_or_create(
        employee=emp,
        date=today,
        defaults={
            'check_in_time': check_in_time,
            'status': status_val,
            'late_minutes': late_minutes,
            'check_in_latitude': lat,
            'check_in_longitude': lon,
        }
    )

    if not created and att.check_in_time is None:
        att.check_in_time = check_in_time
        att.status = status_val
        att.late_minutes = late_minutes
        att.check_in_latitude = lat
        att.check_in_longitude = lon
        att.save()

    # FCM notification
    _send_auto_checkin_notification(user, emp, lang, check_in_str, late_minutes)

    # الرسالة
    if late_minutes > 0:
        message = _msg('checked_in_late', lang, minutes=late_minutes)
    else:
        message = _msg('checked_in', lang)

    return Response({
        'status': 'checked_in',
        'message': message,
        'check_in': check_in_str,
        'attendance_status': status_val,
        'late_minutes': late_minutes,
        'auto': True,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def auto_check_out(request):
    """
    تسجيل انصراف أوتوماتيك
    Body: { "latitude": ..., "longitude": ... }
    """
    user = request.user
    emp = _get_employee(user)
    lang = _get_user_lang(user, emp)

    if not emp:
        return Response({'error': _msg('employee_not_found', lang)}, status=404)

    lat = request.data.get('latitude')
    lon = request.data.get('longitude')

    if lat is None or lon is None:
        return Response({'error': _msg('coords_required', lang)}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return Response({'error': _msg('invalid_coords', lang)}, status=400)

    today = date.today()
    now = timezone.now()

    # لازم يكون عمل check-in الأول
    att = Attendance.objects.filter(
        employee=emp,
        date=today,
        check_in_time__isnull=False,
        check_out_time__isnull=True,
    ).first()

    if not att:
        return Response({
            'status': 'no_checkin',
            'message': _msg('no_checkin', lang),
        }, status=400)

    # تحقق إن الموظف خرج من النطاق
    geofence = _get_active_geofence(emp)
    is_outside = True

    if geofence and geofence.latitude and geofence.longitude:
        distance = _haversine_distance(
            lat, lon,
            float(geofence.latitude),
            float(geofence.longitude),
        )
        radius = float(getattr(geofence, 'radius', 100) or 100)
        is_outside = distance > radius

    if not is_outside:
        return Response({
            'status': 'still_inside',
            'message': _msg('still_inside', lang),
        }, status=400)

    # حساب ساعات العمل
    check_out_time = now.time().replace(microsecond=0)
    check_in_dt = datetime.combine(today, att.check_in_time)
    check_out_dt = datetime.combine(today, check_out_time)
    work_duration = check_out_dt - check_in_dt
    work_hours = round(work_duration.total_seconds() / 3600, 2)
    check_out_str = check_out_time.strftime('%H:%M')

    # حساب الأوفرتايم
    shift = _get_employee_shift(emp)
    overtime_hours = 0.0
    if shift and shift.end_time:
        try:
            shift_end = shift.end_time
            if isinstance(shift_end, str):
                h, m = shift_end.split(':')
                shift_end = time(int(h), int(m))
            shift_end_dt = datetime.combine(today, shift_end)
            if check_out_dt > shift_end_dt:
                ot = check_out_dt - shift_end_dt
                overtime_hours = round(ot.total_seconds() / 3600, 2)
        except Exception:
            pass

    att.check_out_time = check_out_time
    att.work_hours = work_hours
    att.overtime_hours = overtime_hours
    att.check_out_latitude = lat
    att.check_out_longitude = lon
    att.save()

    # FCM notification
    _send_auto_checkout_notification(
        user, emp, lang, check_out_str,
        work_hours, overtime_hours,
    )

    return Response({
        'status': 'checked_out',
        'message': _msg('checked_out', lang),
        'check_in': att.check_in_time.strftime('%H:%M'),
        'check_out': check_out_str,
        'work_hours': work_hours,
        'overtime_hours': overtime_hours,
        'auto': True,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def auto_checkin_status(request):
    """حالة الحضور اليوم للموظف"""
    user = request.user
    emp = _get_employee(user)
    lang = _get_user_lang(user, emp)

    if not emp:
        return Response({'error': _msg('employee_not_found', lang)}, status=404)

    today = date.today()
    att = Attendance.objects.filter(employee=emp, date=today).first()

    if not att or att.check_in_time is None:
        return Response({
            'status': 'not_checked_in',
            'message': _msg('not_checked_in', lang),
            'has_check_in': False,
            'has_check_out': False,
        })

    return Response({
        'status': att.status,
        'has_check_in': att.check_in_time is not None,
        'has_check_out': att.check_out_time is not None,
        'check_in': att.check_in_time.strftime('%H:%M') if att.check_in_time else None,
        'check_out': att.check_out_time.strftime('%H:%M') if att.check_out_time else None,
        'work_hours': float(att.work_hours or 0),
        'late_minutes': int(att.late_minutes or 0),
        'overtime_hours': float(att.overtime_hours or 0),
    })
