"""
Field Visits Mobile APIs
──────────────────────────────
نظام الزيارات الميدانية للموظفين (بدون موافقات)
مثل: مسئول مشتريات، مندوب مبيعات، فني صيانة
"""
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from attendance.models import LocationCheckIn, LocationLog
from employees.models import Employee


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════
def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).first()


def reverse_geocode_safe(lat, lng):
    """جيب اسم الموقع من الإحداثيات"""
    try:
        from attendance.api_mobile import reverse_geocode
        return reverse_geocode(lat, lng)
    except Exception:
        return ''


def auto_close_previous_visit(employee, new_latitude, new_longitude, new_time):
    """
    Auto-Close الزيارة القديمة لو الموظف بدأ زيارة جديدة بدون إنهاء
    يستخدم الحسبة الذكية للمسافة والوقت
    
    Returns: dict فيه معلومات الإغلاق التلقائي، أو None لو مفيش زيارة نشطة
    """
    from attendance.location_utils import (
        calculate_auto_checkout_time,
        is_realistic_travel_smart,
        haversine_distance,
    )
    
    # نبحث عن الزيارة النشطة القديمة
    active_visit = LocationCheckIn._base_manager.filter(
        employee=employee,
        status__in=['arrived', 'in_progress'],
    ).order_by('-arrival_time').first()
    
    if not active_visit:
        return None  # مفيش زيارة نشطة
    
    # نحسب لو الحركة منطقية (Smart Anti-fraud بيستخدم Route History)
    time_diff_minutes = int((new_time - active_visit.arrival_time).total_seconds() / 60)
    
    realistic_check = is_realistic_travel_smart(
        employee,
        float(active_visit.arrival_latitude),
        float(active_visit.arrival_longitude),
        new_latitude,
        new_longitude,
        time_diff_minutes,
        new_time,
    )
    
    # لو الحركة غير منطقية، بنسيبها للتحقق اليدوي + إشعار للمدير
    if not realistic_check['is_realistic']:
        try:
            from accounts.fcm_service import notify_fraud_attempt
            notify_fraud_attempt(
                user=employee.user,
                previous_visit_name=active_visit.location_name,
                reason=realistic_check['reason'],
                company=employee.company,
            )
        except Exception:
            pass
        
        return {
            'closed': False,
            'fraud_alert': True,
            'reason': realistic_check['reason'],
            'previous_visit_id': active_visit.id,
            'previous_visit_name': active_visit.location_name,
            'fraud_source': realistic_check.get('source', 'general_estimate'),
            'fraud_sample_size': realistic_check.get('sample_size', 0),
            'min_acceptable_minutes': realistic_check.get('min_acceptable_minutes', 0),
            'actual_minutes': realistic_check.get('actual_minutes', 0),
        }
    
    # نحسب وقت الخروج التلقائي (بالحسبة الذكية + Route History)
    from attendance.location_utils import get_smart_travel_time, save_route_to_history
    from datetime import timedelta
    
    # نستخدم Smart Travel Time (يستخدم التاريخ لو موجود)
    smart_time = get_smart_travel_time(
        employee,
        float(active_visit.arrival_latitude),
        float(active_visit.arrival_longitude),
        new_latitude,
        new_longitude,
        new_time,
    )
    
    travel_minutes = smart_time['travel_time_minutes']
    auto_close_data = {
        'auto_checkout_time': new_time - timedelta(minutes=travel_minutes),
        'travel_time_minutes': travel_minutes,
        'distance_km': round(haversine_distance(
            float(active_visit.arrival_latitude),
            float(active_visit.arrival_longitude),
            new_latitude,
            new_longitude,
        ), 2),
        'source': smart_time['source'],
        'sample_size': smart_time['sample_size'],
    }
    
    auto_checkout_time = auto_close_data['auto_checkout_time']
    
    # نتأكد إن الوقت التلقائي مش قبل وقت الوصول (يبقى وقت الوصول)
    if auto_checkout_time < active_visit.arrival_time:
        auto_checkout_time = active_visit.arrival_time
    
    # نقفل الزيارة القديمة
    active_visit.departure_time = auto_checkout_time
    active_visit.departure_latitude = new_latitude  # آخر موقع معروف
    active_visit.departure_longitude = new_longitude
    active_visit.status = 'completed'
    
    # نضيف ملاحظة إن الإغلاق كان تلقائي
    auto_note = (
        f'\n\n[إغلاق تلقائي في {timezone.localtime(new_time).strftime("%I:%M %p")}]'
        f' - تم حساب وقت الخروج بناءً على المسافة ({auto_close_data["distance_km"]} كم) '
        f'ووقت التنقل المتوقع ({auto_close_data["travel_time_minutes"]} دقيقة)'
    )
    active_visit.notes = (active_visit.notes or '') + auto_note
    active_visit.save()
    
    # نحفظ الرحلة في التاريخ (Route History) للتعلم منها
    try:
        save_route_to_history(
            employee=employee,
            from_lat=float(active_visit.arrival_latitude),
            from_lng=float(active_visit.arrival_longitude),
            from_name=active_visit.location_name,
            to_lat=new_latitude,
            to_lng=new_longitude,
            to_name=None,
            departed_at=auto_checkout_time,
            arrived_at=new_time,
        )
    except Exception as e:
        pass  # لو حصل خطأ، ما تكسرش الـ flow
    
    # نبعت إشعار للموظف والمدير إن الزيارة اتقفلت تلقائياً
    try:
        from accounts.fcm_service import notify_visit_auto_closed
        notify_visit_auto_closed(
            user=employee.user,
            previous_visit_name=active_visit.location_name,
            auto_checkout_time=timezone.localtime(auto_checkout_time).strftime('%I:%M %p'),
            travel_minutes=auto_close_data['travel_time_minutes'],
            distance_km=auto_close_data['distance_km'],
            company=employee.company,
        )
    except Exception:
        pass
    
    return {
        'closed': True,
        'fraud_alert': False,
        'previous_visit_id': active_visit.id,
        'previous_visit_name': active_visit.location_name,
        'auto_checkout_time': timezone.localtime(auto_checkout_time).strftime('%I:%M %p'),
        'travel_time_minutes': auto_close_data['travel_time_minutes'],
        'distance_km': auto_close_data['distance_km'],
        'time_source': auto_close_data.get('source', 'general_estimate'),
        'sample_size': auto_close_data.get('sample_size', 0),
    }


def visit_to_dict(visit, include_tracking=False):
    """تحويل الزيارة لـ dict للـ API response"""
    data = {
        'id': visit.id,
        'visit_type': visit.visit_type,
        'visit_type_display': visit.get_visit_type_display(),
        'location_name': visit.location_name,
        'purpose': visit.purpose or '',
        'notes': visit.notes or '',
        'status': visit.status,
        'status_display': visit.get_status_display(),
        'arrival_time': timezone.localtime(visit.arrival_time).strftime('%I:%M %p') if visit.arrival_time else None,
        'arrival_date': visit.arrival_time.date().isoformat() if visit.arrival_time else None,
        'arrival_address': visit.arrival_address or '',
        'arrival_latitude': float(visit.arrival_latitude) if visit.arrival_latitude else None,
        'arrival_longitude': float(visit.arrival_longitude) if visit.arrival_longitude else None,
        'departure_time': timezone.localtime(visit.departure_time).strftime('%I:%M %p') if visit.departure_time else None,
        'is_active': visit.status in ('arrived', 'in_progress'),
        'duration_minutes': None,
    }
    
    # حساب المدة
    if visit.arrival_time and visit.departure_time:
        diff = visit.departure_time - visit.arrival_time
        data['duration_minutes'] = int(diff.total_seconds() / 60)
    elif visit.arrival_time and visit.status in ('arrived', 'in_progress'):
        diff = timezone.now() - visit.arrival_time
        data['duration_minutes'] = int(diff.total_seconds() / 60)
    
    return data


# ═══════════════════════════════════════════════════
# API 1: بدء زيارة جديدة
# ═══════════════════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visit_start(request):
    """
    POST /attendance/api/mobile/field-visits/start/
    
    Body:
    {
        "visit_type": "client_visit",     // إجباري
        "location_name": "شركة X",        // إجباري
        "purpose": "شراء أدوات مكتبية",   // إجباري
        "latitude": 30.05,                // إجباري
        "longitude": 31.24,               // إجباري
        "notes": "ملاحظات إضافية"        // اختياري
    }
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    # نتحقق من البيانات
    visit_type = request.data.get('visit_type', '').strip()
    location_name = request.data.get('location_name', '').strip()
    purpose = request.data.get('purpose', '').strip()
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    notes = request.data.get('notes', '').strip()
    
    if not visit_type:
        return Response({'success': False, 'message': 'نوع الزيارة مطلوب'}, status=400)
    if not location_name:
        return Response({'success': False, 'message': 'اسم الموقع مطلوب'}, status=400)
    if not purpose:
        return Response({'success': False, 'message': 'الغرض من الزيارة مطلوب'}, status=400)
    if latitude in [None, ''] or longitude in [None, '']:
        return Response({'success': False, 'message': 'الموقع الجغرافي مطلوب'}, status=400)
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)
    
    # نتحقق من نوع الزيارة
    valid_types = [c[0] for c in LocationCheckIn.VISIT_TYPE_CHOICES]
    if visit_type not in valid_types:
        return Response({
            'success': False,
            'message': f'نوع زيارة غير معروف. الأنواع المسموحة: {valid_types}'
        }, status=400)
    
    # ═══════════════════════════════════════════════════
    # Auto-Close: نقفل الزيارة القديمة أوتوماتيك لو موجودة
    # ═══════════════════════════════════════════════════
    now = timezone.now()
    auto_close_info = auto_close_previous_visit(
        employee, latitude, longitude, now
    )
    
    # لو فيه حالة استهبال (fraud) → نرفض
    if auto_close_info and auto_close_info.get('fraud_alert'):
        return Response({
            'success': False,
            'message': (
                f'حركة غير منطقية! {auto_close_info["reason"]}. '
                f'يرجى إنهاء زيارة [{auto_close_info["previous_visit_name"]}] يدوياً أولاً.'
            ),
            'fraud_alert': True,
            'previous_visit_id': auto_close_info['previous_visit_id'],
        }, status=400)
    
    # نجيب اسم الموقع (address)
    address = reverse_geocode_safe(latitude, longitude)
    
    # ننشئ الزيارة
    visit = LocationCheckIn._base_manager.create(
        company=employee.company,
        employee=employee,
        visit_type=visit_type,
        location_name=location_name,
        purpose=purpose,
        notes=notes,
        arrival_time=timezone.now(),
        arrival_latitude=latitude,
        arrival_longitude=longitude,
        arrival_address=address,
        status='arrived',
    )
    
    return Response({
        'success': True,
        'message': 'تم بدء الزيارة بنجاح',
        'visit': visit_to_dict(visit),
    }, status=201)


# ═══════════════════════════════════════════════════
# API 2: إنهاء زيارة
# ═══════════════════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visit_end(request, visit_id):
    """
    POST /attendance/api/mobile/field-visits/end/{visit_id}/
    
    Body:
    {
        "latitude": 30.05,
        "longitude": 31.24,
        "notes": "ملاحظات نهاية الزيارة"  // اختياري
    }
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    visit = LocationCheckIn._base_manager.filter(
        id=visit_id,
        employee=employee,
    ).first()
    
    if not visit:
        return Response({'success': False, 'message': 'الزيارة غير موجودة'}, status=404)
    
    if visit.status == 'completed':
        return Response({
            'success': False,
            'message': 'الزيارة منتهية بالفعل',
            'visit': visit_to_dict(visit),
        }, status=400)
    
    if visit.status == 'cancelled':
        return Response({'success': False, 'message': 'الزيارة ملغاة'}, status=400)
    
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    additional_notes = request.data.get('notes', '').strip()
    
    if latitude in [None, ''] or longitude in [None, '']:
        return Response({'success': False, 'message': 'الموقع الجغرافي مطلوب'}, status=400)
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)
    
    # نحدث الزيارة
    visit.departure_time = timezone.now()
    visit.departure_latitude = latitude
    visit.departure_longitude = longitude
    visit.status = 'completed'
    
    if additional_notes:
        if visit.notes:
            visit.notes = f"{visit.notes}\n\n[نهاية الزيارة]: {additional_notes}"
        else:
            visit.notes = f"[نهاية الزيارة]: {additional_notes}"
    
    visit.save()
    
    return Response({
        'success': True,
        'message': 'تم إنهاء الزيارة بنجاح',
        'visit': visit_to_dict(visit),
    })


# ═══════════════════════════════════════════════════
# API 3: قائمة زياراتي
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visits_list(request):
    """
    GET /attendance/api/mobile/field-visits/
    
    Query params:
    - filter: 'today' | 'active' | 'all'  (default: today)
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    filter_type = request.GET.get('filter', 'today').lower()
    
    qs = LocationCheckIn._base_manager.filter(employee=employee).order_by('-arrival_time')
    
    if filter_type == 'today':
        today = timezone.localdate()
        qs = qs.filter(arrival_time__date=today)
    elif filter_type == 'active':
        qs = qs.filter(status__in=['arrived', 'in_progress'])
    # 'all' → مفيش فلتر
    
    # حد أقصى 100 زيارة
    visits = list(qs[:100])
    
    active_visit = None
    for v in visits:
        if v.status in ('arrived', 'in_progress'):
            active_visit = visit_to_dict(v)
            break
    
    return Response({
        'success': True,
        'count': len(visits),
        'active_visit': active_visit,
        'visits': [visit_to_dict(v) for v in visits],
    })


# ═══════════════════════════════════════════════════
# API 4: تفاصيل زيارة
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visit_detail(request, visit_id):
    """
    GET /attendance/api/mobile/field-visits/{visit_id}/
    
    يرجع تفاصيل الزيارة + نقاط التتبع (كل 5 دقائق)
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    visit = LocationCheckIn._base_manager.filter(
        id=visit_id,
        employee=employee,
    ).first()
    
    if not visit:
        return Response({'success': False, 'message': 'الزيارة غير موجودة'}, status=404)
    
    data = visit_to_dict(visit)
    
    # نجيب نقاط التتبع خلال فترة الزيارة
    end_time = visit.departure_time or timezone.now()
    
    tracking_points = LocationLog._base_manager.filter(
        employee=employee,
        timestamp__gte=visit.arrival_time,
        timestamp__lte=end_time,
    ).order_by('timestamp')
    
    data['tracking_points'] = [
        {
            'time': timezone.localtime(p.timestamp).strftime('%I:%M %p'),
            'latitude': float(p.latitude) if p.latitude else None,
            'longitude': float(p.longitude) if p.longitude else None,
            'address': p.address or '',
        }
        for p in tracking_points
    ]
    
    return Response({
        'success': True,
        'visit': data,
    })


# ═══════════════════════════════════════════════════
# API 5: أنواع الزيارات المتاحة (للتطبيق)
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def field_visit_types(request):
    """
    GET /attendance/api/mobile/field-visits/types/
    
    يرجع الأنواع المتاحة للاختيار
    """
    types = [
        {'value': choice[0], 'label': choice[1]}
        for choice in LocationCheckIn.VISIT_TYPE_CHOICES
    ]
    return Response({'success': True, 'types': types})
