"""
Location Utilities
──────────────────────────────
دوال حساب المسافات والأوقات الجغرافية
- Haversine formula للمسافة
- Travel time estimation ذكي
- Anti-fraud detection
"""
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2


# ═══════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════
EARTH_RADIUS_KM = 6371

SPEED_WALKING = 5
SPEED_TRAFFIC_JAM = 15
SPEED_NORMAL_CITY = 30
SPEED_HIGHWAY = 60

RUSH_HOURS = [(7, 10), (16, 19)]


def haversine_distance(lat1, lng1, lat2, lng2):
    """حساب المسافة بين نقطتين بالكيلومتر"""
    try:
        lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
    except (ValueError, TypeError):
        return 0.0
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def estimate_speed(distance_km, current_time=None):
    """تقدير السرعة الذكي"""
    if distance_km < 0.5:
        return SPEED_WALKING
    if distance_km < 2:
        return SPEED_WALKING * 2
    
    if current_time:
        hour = current_time.hour if hasattr(current_time, 'hour') else 12
        for start, end in RUSH_HOURS:
            if start <= hour < end:
                if distance_km < 10:
                    return SPEED_TRAFFIC_JAM
                else:
                    return SPEED_TRAFFIC_JAM * 1.5
    
    if distance_km < 15:
        return SPEED_NORMAL_CITY
    else:
        return SPEED_HIGHWAY


def estimate_travel_time_minutes(from_lat, from_lng, to_lat, to_lng, current_time=None):
    """تقدير الوقت المطلوب للتنقل بالدقائق"""
    distance = haversine_distance(from_lat, from_lng, to_lat, to_lng)
    if distance == 0:
        return 0
    
    speed = estimate_speed(distance, current_time)
    time_hours = distance / speed
    time_minutes = (time_hours * 60) + 5  # 5 minutes buffer
    
    return round(time_minutes)


def is_realistic_travel(from_lat, from_lng, to_lat, to_lng, 
                        actual_time_minutes, tolerance_percent=30):
    """كشف الحركة المستحيلة"""
    distance = haversine_distance(from_lat, from_lng, to_lat, to_lng)
    expected_minutes = estimate_travel_time_minutes(from_lat, from_lng, to_lat, to_lng)
    
    fastest_time_hours = distance / SPEED_HIGHWAY
    min_acceptable_minutes = max(1, round(fastest_time_hours * 60 * (1 - tolerance_percent / 100)))
    
    is_realistic = actual_time_minutes >= min_acceptable_minutes
    
    reason = ''
    if not is_realistic:
        reason = (
            f'المسافة {distance:.1f} كم تحتاج على الأقل {min_acceptable_minutes} دقيقة، '
            f'ولكن الفارق الفعلي {actual_time_minutes} دقيقة فقط'
        )
    
    return {
        'is_realistic': is_realistic,
        'distance_km': round(distance, 2),
        'expected_minutes': expected_minutes,
        'actual_minutes': actual_time_minutes,
        'min_acceptable_minutes': min_acceptable_minutes,
        'reason': reason,
    }


def calculate_auto_checkout_time(from_lat, from_lng, to_lat, to_lng, new_checkin_time):
    """حساب وقت الانصراف التلقائي من الموقع القديم"""
    travel_time = estimate_travel_time_minutes(
        from_lat, from_lng, to_lat, to_lng, new_checkin_time
    )
    distance = haversine_distance(from_lat, from_lng, to_lat, to_lng)
    auto_checkout = new_checkin_time - timedelta(minutes=travel_time)
    
    return {
        'auto_checkout_time': auto_checkout,
        'travel_time_minutes': travel_time,
        'distance_km': round(distance, 2),
    }


def is_within_radius(target_lat, target_lng, center_lat, center_lng, radius_meters):
    """فحص لو الموقع الحالي داخل نطاق موقع معتمد"""
    distance_km = haversine_distance(target_lat, target_lng, center_lat, center_lng)
    distance_meters = distance_km * 1000
    
    return {
        'is_within': distance_meters <= radius_meters,
        'distance_meters': round(distance_meters, 2),
    }


def get_time_period(current_time):
    """يحدد فترة اليوم (morning/noon/evening/night)"""
    hour = current_time.hour if hasattr(current_time, 'hour') else 12
    if 6 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 16:
        return 'noon'
    elif 16 <= hour < 20:
        return 'evening'
    else:
        return 'night'


# ═══════════════════════════════════════════════════
# Smart Travel Time - يستخدم تاريخ الرحلات لدقة أعلى
# ═══════════════════════════════════════════════════
def get_smart_travel_time(employee, from_lat, from_lng, to_lat, to_lng, current_time=None):
    """
    الوقت المتوقع للتنقل بدقة أعلى باستخدام تاريخ الرحلات
    
    Logic:
    - لو عندنا 3+ رحلات مشابهة → استخدم المتوسط الشخصي
    - أقل من 3 رحلات → استخدم الحسبة العامة
    
    Args:
        employee: الموظف
        from_lat, from_lng: نقطة البداية
        to_lat, to_lng: نقطة النهاية
        current_time: الوقت الحالي (اختياري)
    
    Returns:
        dict: {
            'travel_time_minutes': int,
            'source': 'personal_history' | 'general_estimate',
            'sample_size': int,
            'confidence': 'high' | 'medium' | 'low',
        }
    """
    from django.utils import timezone as tz
    from decimal import Decimal
    
    if current_time is None:
        current_time = tz.now()
    
    time_period = get_time_period(current_time)
    
    # نبحث في تاريخ الرحلات المشابهة
    try:
        from attendance.models import RouteHistory
        from django.db.models import Avg
        
        # نطاق تسامح لتحديد "نفس النقاط" (0.001 درجة = ~100 متر)
        lat_tolerance = Decimal('0.005')
        lng_tolerance = Decimal('0.005')
        
        history = RouteHistory._base_manager.filter(
            employee=employee,
            from_latitude__gte=Decimal(str(from_lat)) - lat_tolerance,
            from_latitude__lte=Decimal(str(from_lat)) + lat_tolerance,
            from_longitude__gte=Decimal(str(from_lng)) - lng_tolerance,
            from_longitude__lte=Decimal(str(from_lng)) + lng_tolerance,
            to_latitude__gte=Decimal(str(to_lat)) - lat_tolerance,
            to_latitude__lte=Decimal(str(to_lat)) + lat_tolerance,
            to_longitude__gte=Decimal(str(to_lng)) - lng_tolerance,
            to_longitude__lte=Decimal(str(to_lng)) + lng_tolerance,
            time_period=time_period,
            is_verified=True,
        )
        
        count = history.count()
        
        if count >= 3:
            # عندنا بيانات كافية → المتوسط الشخصي
            avg_data = history.aggregate(avg_time=Avg('travel_time_minutes'))
            avg_time = int(avg_data['avg_time'])
            
            confidence = 'high' if count >= 10 else 'medium'
            
            return {
                'travel_time_minutes': avg_time,
                'source': 'personal_history',
                'sample_size': count,
                'confidence': confidence,
            }
    
    except Exception:
        # لو حصل خطأ، نرجع للحسبة العامة
        pass
    
    # الحسبة العامة (default)
    general_time = estimate_travel_time_minutes(
        from_lat, from_lng, to_lat, to_lng, current_time
    )
    
    return {
        'travel_time_minutes': general_time,
        'source': 'general_estimate',
        'sample_size': 0,
        'confidence': 'low',
    }


# ═══════════════════════════════════════════════════
# Save Route to History - يحفظ الرحلة في التاريخ
# ═══════════════════════════════════════════════════
def save_route_to_history(employee, from_lat, from_lng, from_name,
                          to_lat, to_lng, to_name,
                          departed_at, arrived_at):
    """
    يحفظ رحلة في RouteHistory للتعلم منها لاحقاً
    
    Returns:
        RouteHistory instance أو None لو حصل خطأ
    """
    try:
        from attendance.models import RouteHistory
        
        distance = haversine_distance(from_lat, from_lng, to_lat, to_lng)
        travel_time = int((arrived_at - departed_at).total_seconds() / 60)
        
        # لو الرحلة أقل من دقيقة أو أكتر من 8 ساعات، متجاهلها
        if travel_time < 1 or travel_time > 480:
            return None
        
        # لو المسافة صفر، متجاهلها
        if distance < 0.1:  # أقل من 100 متر
            return None
        
        time_period = get_time_period(arrived_at)
        day_of_week = arrived_at.weekday()  # 0=الاثنين, 6=الأحد
        # تحويل: Django بيعتبر الأحد=6، إحنا عايزينه=0
        day_of_week_ar = (day_of_week + 1) % 7  # 0=الأحد, 6=السبت
        
        route = RouteHistory._base_manager.create(
            company=employee.company,
            employee=employee,
            from_latitude=from_lat,
            from_longitude=from_lng,
            from_location_name=from_name or '',
            to_latitude=to_lat,
            to_longitude=to_lng,
            to_location_name=to_name or '',
            distance_km=round(distance, 2),
            travel_time_minutes=travel_time,
            departed_at=departed_at,
            arrived_at=arrived_at,
            time_period=time_period,
            day_of_week=day_of_week_ar,
            is_verified=True,
        )
        
        return route
    
    except Exception as e:
        print(f"Error saving route history: {e}")
        return None


# ═══════════════════════════════════════════════════
# Smart Anti-Fraud - يستخدم Route History للدقة
# ═══════════════════════════════════════════════════
def is_realistic_travel_smart(employee, from_lat, from_lng, to_lat, to_lng, 
                              actual_time_minutes, current_time=None,
                              tolerance_percent=20):
    """
    Anti-Fraud محسّن يستخدم تاريخ الموظف
    
    Logic:
    - لو عندنا 3+ رحلات مشابهة → نستخدم أسرع رحلة (Minimum)
    - أقل من 3 رحلات → نستخدم الحسبة العامة (Highway Speed)
    
    Args:
        employee: الموظف
        from_lat, from_lng: نقطة البداية
        to_lat, to_lng: نقطة النهاية
        actual_time_minutes: الوقت الفعلي
        current_time: الوقت الحالي
        tolerance_percent: نسبة السماح (20% default)
    
    Returns:
        dict: {
            'is_realistic': bool,
            'distance_km': float,
            'actual_minutes': int,
            'min_acceptable_minutes': int,
            'source': 'personal_min' | 'general_estimate',
            'sample_size': int,
            'reason': str,
        }
    """
    from django.utils import timezone as tz
    from decimal import Decimal
    
    if current_time is None:
        current_time = tz.now()
    
    distance = haversine_distance(from_lat, from_lng, to_lat, to_lng)
    time_period = get_time_period(current_time)
    
    # نبحث في تاريخ الرحلات المشابهة
    min_acceptable = None
    source = 'general_estimate'
    sample_size = 0
    
    try:
        from attendance.models import RouteHistory
        from django.db.models import Min
        
        lat_tolerance = Decimal('0.005')
        lng_tolerance = Decimal('0.005')
        
        history = RouteHistory._base_manager.filter(
            employee=employee,
            from_latitude__gte=Decimal(str(from_lat)) - lat_tolerance,
            from_latitude__lte=Decimal(str(from_lat)) + lat_tolerance,
            from_longitude__gte=Decimal(str(from_lng)) - lng_tolerance,
            from_longitude__lte=Decimal(str(from_lng)) + lng_tolerance,
            to_latitude__gte=Decimal(str(to_lat)) - lat_tolerance,
            to_latitude__lte=Decimal(str(to_lat)) + lat_tolerance,
            to_longitude__gte=Decimal(str(to_lng)) - lng_tolerance,
            to_longitude__lte=Decimal(str(to_lng)) + lng_tolerance,
            time_period=time_period,
            is_verified=True,
        )
        
        sample_size = history.count()
        
        if sample_size >= 3:
            # عندنا بيانات كافية → نستخدم أسرع رحلة
            min_data = history.aggregate(min_time=Min('travel_time_minutes'))
            fastest = min_data['min_time']
            
            # نسبة السماح 20% أقل من أسرع رحلة
            min_acceptable = max(1, int(fastest * (1 - tolerance_percent / 100)))
            source = 'personal_min'
    
    except Exception:
        pass
    
    # لو مفيش تاريخ، نستخدم الحسبة العامة
    if min_acceptable is None:
        fastest_time_hours = distance / SPEED_HIGHWAY
        min_acceptable = max(1, round(fastest_time_hours * 60 * (1 - tolerance_percent / 100)))
    
    is_realistic = actual_time_minutes >= min_acceptable
    
    reason = ''
    if not is_realistic:
        if source == 'personal_min':
            reason = (
                f'المسافة {distance:.1f} كم — بناءً على تاريخك، '
                f'أسرع مرة عملت الرحلة دي كانت {int(min_acceptable / (1 - tolerance_percent / 100))} دقيقة، '
                f'الحد الأدنى المقبول {min_acceptable} دقيقة، '
                f'ولكن الفارق الفعلي {actual_time_minutes} دقيقة فقط'
            )
        else:
            reason = (
                f'المسافة {distance:.1f} كم تحتاج على الأقل {min_acceptable} دقيقة، '
                f'ولكن الفارق الفعلي {actual_time_minutes} دقيقة فقط'
            )
    
    return {
        'is_realistic': is_realistic,
        'distance_km': round(distance, 2),
        'actual_minutes': actual_time_minutes,
        'min_acceptable_minutes': min_acceptable,
        'source': source,
        'sample_size': sample_size,
        'reason': reason,
    }

