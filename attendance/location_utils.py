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
