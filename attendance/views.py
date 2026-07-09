from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator

from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import math

from subscriptions.helpers import feature_required
from .models import Shift, EmployeeShift, Attendance, LocationLog, LocationCheckIn
from employees.models import Employee


def calculate_distance(lat1, lon1, lat2, lon2):
    """حساب المسافة بين نقطتين GPS بالمتر"""
    R = 6371000
    
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return round(R * c, 2)


@login_required
@feature_required('attendance_records')
def attendance_list(request):
    """قائمة سجلات الحضور"""
    
    attendances = Attendance.objects.all().select_related('employee', 'shift')
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        attendances = attendances.filter(date__gte=date_from)
    if date_to:
        attendances = attendances.filter(date__lte=date_to)
    
    employee_id = request.GET.get('employee', '')
    if employee_id:
        attendances = attendances.filter(employee_id=employee_id)
    
    status = request.GET.get('status', '')
    if status:
        attendances = attendances.filter(status=status)
    
    today = date.today()
    today_stats = {
        'total': Attendance.objects.filter(date=today).count(),
        'present': Attendance.objects.filter(date=today, status='present').count(),
        'late': Attendance.objects.filter(date=today, status='late').count(),
        'absent': Attendance.objects.filter(date=today, status='absent').count(),
    }
    
    paginator = Paginator(attendances, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    employees = Employee.objects.filter(status='active')
    
    context = {
        'page_obj': page_obj,
        'attendances': page_obj.object_list,
        'employees': employees,
        'today_stats': today_stats,
        'date_from': date_from,
        'date_to': date_to,
        'employee_id': employee_id,
        'status': status,
        'status_choices': Attendance.STATUS_CHOICES,
        'total_count': paginator.count,
    }
    
    return render(request, 'attendance/list.html', context)


@login_required
@feature_required('attendance_gps')
def check_in_page(request):
    """صفحة تسجيل الحضور والانصراف"""
    
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
    
    today = date.today()
    today_attendance = None
    if employee:
        today_attendance = Attendance.objects.filter(
            employee=employee,
            date=today
        ).first()
    
    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'today': today,
    }
    
    return render(request, 'attendance/check_in.html', context)


@login_required
@require_http_methods(["POST"])
def api_check_in(request):
    """API لتسجيل الحضور"""
    
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy', 0)
        address = data.get('address', '')
        
        if not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم تحديد الموقع'
            })
        
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم العثور على بيانات الموظف. تواصل مع المدير.'
            })
        
        today = date.today()
        
        existing = Attendance.objects.filter(employee=employee, date=today).first()
        if existing and existing.check_in_time:
            return JsonResponse({
                'success': False,
                'message': f'تم تسجيل الحضور مسبقاً في {existing.check_in_time.strftime("%H:%M")}'
            })
        
        within_range = False
        distance = None
        if employee.branch and employee.branch.latitude and employee.branch.longitude:
            distance = calculate_distance(
                latitude, longitude,
                employee.branch.latitude, employee.branch.longitude
            )
            within_range = distance <= employee.branch.check_in_radius
        else:
            within_range = True
        
        current_shift = EmployeeShift.objects.filter(
            employee=employee,
            is_active=True,
            start_date__lte=today
        ).order_by('-start_date').first()
        
        shift = current_shift.shift if current_shift else None
        
        if existing:
            attendance = existing
        else:
            attendance = Attendance(
                employee=employee,
                date=today,
                shift=shift,
                company=employee.company
            )
        
        attendance.check_in_time = timezone.now()
        attendance.check_in_latitude = latitude
        attendance.check_in_longitude = longitude
        attendance.check_in_address = address
        attendance.check_in_within_range = within_range
        attendance.status = 'present'
        
        if shift:
            attendance.calculate_late_minutes()
            if attendance.late_minutes > 0:
                attendance.status = 'late'
        
        attendance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم تسجيل الحضور بنجاح ✅',
            'time': attendance.check_in_time.strftime('%H:%M:%S'),
            'within_range': within_range,
            'distance': distance,
            'late_minutes': attendance.late_minutes,
            'address': address,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def api_check_out(request):
    """API لتسجيل الانصراف"""
    
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '')
        
        if not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم تحديد الموقع'
            })
        
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم العثور على بيانات الموظف'
            })
        
        today = date.today()
        attendance = Attendance.objects.filter(employee=employee, date=today).first()
        
        if not attendance or not attendance.check_in_time:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم تسجيل حضور اليوم. سجل حضور أولاً.'
            })
        
        if attendance.check_out_time:
            return JsonResponse({
                'success': False,
                'message': f'تم تسجيل الانصراف مسبقاً في {attendance.check_out_time.strftime("%H:%M")}'
            })
        
        within_range = False
        if employee.branch and employee.branch.latitude and employee.branch.longitude:
            distance = calculate_distance(
                latitude, longitude,
                employee.branch.latitude, employee.branch.longitude
            )
            within_range = distance <= employee.branch.check_in_radius
        else:
            within_range = True
        
        attendance.check_out_time = timezone.now()
        attendance.check_out_latitude = latitude
        attendance.check_out_longitude = longitude
        attendance.check_out_address = address
        attendance.check_out_within_range = within_range
        attendance.calculate_work_hours()
        attendance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم تسجيل الانصراف بنجاح ✅',
            'time': attendance.check_out_time.strftime('%H:%M:%S'),
            'work_hours': float(attendance.work_hours),
            'address': address,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })


@login_required
@feature_required('location_visits')
def visits_list(request):
    """قائمة زيارات المواقع"""
    visits = LocationCheckIn.objects.all().select_related('employee').order_by('-arrival_time')
    
    paginator = Paginator(visits, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'visits': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': paginator.count,
    }
    
    return render(request, 'attendance/visits.html', context)


@login_required
@feature_required('location_visits')
def visit_add(request):
    """إضافة زيارة موقع"""
    
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
    
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee_id')
            visit_type = request.POST.get('visit_type')
            location_name = request.POST.get('location_name')
            purpose = request.POST.get('purpose', '')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            address = request.POST.get('address', '')
            
            if not all([employee_id, visit_type, location_name, latitude, longitude]):
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة وتحديد الموقع')
                return redirect('attendance:visit_add')
            
            selected_employee = Employee.objects.get(id=employee_id)
            
            visit = LocationCheckIn.objects.create(
                company=selected_employee.company,
                employee=selected_employee,
                visit_type=visit_type,
                location_name=location_name,
                purpose=purpose,
                arrival_time=timezone.now(),
                arrival_latitude=latitude,
                arrival_longitude=longitude,
                arrival_address=address,
                status='arrived'
            )
            
            messages.success(request, f'تم تسجيل الزيارة بنجاح ✅')
            return redirect('attendance:visits')
            
        except Exception as e:
            messages.error(request, f'خطأ: {str(e)}')
    
    employees = Employee.objects.filter(status='active')
    
    context = {
        'employees': employees,
        'current_employee': employee,
        'visit_types': LocationCheckIn.VISIT_TYPE_CHOICES,
    }
    
    return render(request, 'attendance/visit_form.html', context)


@login_required
@feature_required('live_map')
def live_map(request):
    """خريطة الموظفين الميدانيين Live"""
    
    field_employees = Employee.objects.filter(
        is_field_worker=True,
        status='active'
    )
    
    context = {
        'field_employees': field_employees,
        'total_field': field_employees.count(),
    }
    
    return render(request, 'attendance/live_map.html', context)


@login_required
def api_live_locations(request):
    """API لآخر مواقع الموظفين الميدانيين"""
    
    two_hours_ago = timezone.now() - timedelta(hours=2)
    
    locations = []
    field_employees = Employee.objects.filter(
        is_field_worker=True,
        status='active'
    )
    
    for emp in field_employees:
        last_location = LocationLog.objects.filter(
            employee=emp,
            timestamp__gte=two_hours_ago
        ).order_by('-timestamp').first()
        
        if not last_location:
            today_attendance = Attendance.objects.filter(
                employee=emp,
                date=date.today(),
                check_in_latitude__isnull=False
            ).first()
            
            if today_attendance:
                locations.append({
                    'id': emp.id,
                    'name': emp.full_name_ar,
                    'code': emp.employee_code,
                    'latitude': float(today_attendance.check_in_latitude),
                    'longitude': float(today_attendance.check_in_longitude),
                    'timestamp': today_attendance.check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'address': today_attendance.check_in_address or 'غير محدد',
                    'source': 'attendance',
                    'photo': emp.photo.url if emp.photo else None,
                    'phone': emp.phone,
                    'job_title': emp.job_title.name_ar,
                })
        else:
            locations.append({
                'id': emp.id,
                'name': emp.full_name_ar,
                'code': emp.employee_code,
                'latitude': float(last_location.latitude),
                'longitude': float(last_location.longitude),
                'timestamp': last_location.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'address': last_location.address or 'جاري التحديد...',
                'battery': last_location.battery_level,
                'source': 'live',
                'photo': emp.photo.url if emp.photo else None,
                'phone': emp.phone,
                'job_title': emp.job_title.name_ar,
            })
    
    return JsonResponse({
        'success': True,
        'locations': locations,
        'count': len(locations),
        'last_update': timezone.now().strftime('%H:%M:%S'),
    })


@login_required
@require_http_methods(["POST"])
def api_track_location(request):
    """API لاستقبال المواقع من التطبيق"""
    
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy', 0)
        speed = data.get('speed', 0)
        battery = data.get('battery')
        address = data.get('address', '')
        
        if not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'message': 'الموقع غير محدد'
            })
        
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم العثور على الموظف'
            })
        
        if not employee.is_field_worker:
            return JsonResponse({
                'success': False,
                'message': 'التتبع متاح للموظفين الميدانيين فقط'
            })
        
        LocationLog.objects.create(
            company=employee.company,
            employee=employee,
            timestamp=timezone.now(),
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            battery_level=battery,
            address=address,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'تم تسجيل الموقع'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })


@login_required
@feature_required('continuous_tracking')
def tracking_page(request):
    """صفحة التتبع للموظف الميداني"""
    
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
    
    today_locations = []
    today_count = 0
    if employee:
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        today_locations = LocationLog.objects.filter(
            employee=employee,
            timestamp__gte=today_start
        ).order_by('-timestamp')[:50]
        today_count = today_locations.count()
    
    context = {
        'employee': employee,
        'today_locations': today_locations,
        'today_count': today_count,
    }
    
    return render(request, 'attendance/tracking.html', context)


@login_required
def employee_tracking_detail(request, employee_id):
    """عرض تتبع موظف معين (للمدير)"""
    
    employee = get_object_or_404(Employee, pk=employee_id)
    
    date_str = request.GET.get('date', '')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    day_start = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
    day_end = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
    
    locations = LocationLog.objects.filter(
        employee=employee,
        timestamp__gte=day_start,
        timestamp__lte=day_end,
    ).order_by('timestamp')
    
    context = {
        'employee': employee,
        'locations': locations,
        'selected_date': selected_date,
        'total_points': locations.count(),
    }
    
    return render(request, 'attendance/tracking_detail.html', context)


@login_required
@feature_required('continuous_tracking')
def field_employees_monitor(request):
    """صفحة متابعة الموظفين الميدانيين للمدير"""
    
    field_employees = Employee.objects.filter(
        is_field_worker=True,
        status='active'
    ).select_related('job_title', 'branch', 'department')
    
    employees_data = []
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    for emp in field_employees:
        last_location = LocationLog.objects.filter(
            employee=emp
        ).order_by('-timestamp').first()
        
        today_locations = LocationLog.objects.filter(
            employee=emp,
            timestamp__gte=today_start
        ).order_by('timestamp')
        
        total_distance = 0
        if today_locations.count() >= 2:
            prev = None
            for loc in today_locations:
                if prev:
                    total_distance += calculate_distance(
                        prev.latitude, prev.longitude,
                        loc.latitude, loc.longitude
                    )
                prev = loc
        
        is_moving = False
        minutes_since_update = None
        
        if last_location:
            time_diff = (now - last_location.timestamp).total_seconds() / 60
            minutes_since_update = int(time_diff)
            
            if time_diff < 5 and today_locations.count() >= 2:
                last_two = list(today_locations.reverse()[:2])
                if len(last_two) == 2:
                    distance_moved = calculate_distance(
                        last_two[0].latitude, last_two[0].longitude,
                        last_two[1].latitude, last_two[1].longitude
                    )
                    if distance_moved > 50:
                        is_moving = True
        
        connection_status = 'offline'
        if last_location:
            time_diff = (now - last_location.timestamp).total_seconds() / 60
            if time_diff < 5:
                connection_status = 'online'
            elif time_diff < 30:
                connection_status = 'idle'
        
        employees_data.append({
            'employee': emp,
            'last_location': last_location,
            'today_points': today_locations.count(),
            'total_distance_km': round(total_distance / 1000, 2),
            'is_moving': is_moving,
            'minutes_since_update': minutes_since_update,
            'connection_status': connection_status,
        })
    
    online_count = sum(1 for e in employees_data if e['connection_status'] == 'online')
    moving_count = sum(1 for e in employees_data if e['is_moving'])
    offline_count = sum(1 for e in employees_data if e['connection_status'] == 'offline')
    
    context = {
        'employees_data': employees_data,
        'total_count': len(employees_data),
        'online_count': online_count,
        'moving_count': moving_count,
        'offline_count': offline_count,
    }
    
    return render(request, 'attendance/monitor.html', context)


@login_required
def api_monitor_data(request):
    """API للتحديث المباشر لبيانات المتابعة"""
    
    field_employees = Employee.objects.filter(
        is_field_worker=True,
        status='active'
    )
    
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    employees_data = []
    
    for emp in field_employees:
        last_location = LocationLog.objects.filter(
            employee=emp
        ).order_by('-timestamp').first()
        
        today_locations = LocationLog.objects.filter(
            employee=emp,
            timestamp__gte=today_start
        ).order_by('timestamp')
        
        total_distance = 0
        if today_locations.count() >= 2:
            prev = None
            for loc in today_locations:
                if prev:
                    total_distance += calculate_distance(
                        prev.latitude, prev.longitude,
                        loc.latitude, loc.longitude
                    )
                prev = loc
        
        is_moving = False
        minutes_since_update = None
        connection_status = 'offline'
        distance_moved_recently = 0
        
        if last_location:
            time_diff = (now - last_location.timestamp).total_seconds() / 60
            minutes_since_update = int(time_diff)
            
            if time_diff < 5:
                connection_status = 'online'
                if today_locations.count() >= 2:
                    last_two = list(today_locations.reverse()[:2])
                    if len(last_two) == 2:
                        distance_moved_recently = calculate_distance(
                            last_two[0].latitude, last_two[0].longitude,
                            last_two[1].latitude, last_two[1].longitude
                        )
                        if distance_moved_recently > 50:
                            is_moving = True
            elif time_diff < 30:
                connection_status = 'idle'
        
        employees_data.append({
            'id': emp.id,
            'name': emp.full_name_ar,
            'code': emp.employee_code,
            'job_title': emp.job_title.name_ar,
            'phone': emp.phone,
            'photo': emp.photo.url if emp.photo else None,
            'latitude': float(last_location.latitude) if last_location else None,
            'longitude': float(last_location.longitude) if last_location else None,
            'address': last_location.address if last_location else 'لم يبدأ التتبع',
            'last_update': last_location.timestamp.strftime('%H:%M:%S') if last_location else None,
            'minutes_since_update': minutes_since_update,
            'battery': last_location.battery_level if last_location else None,
            'today_points': today_locations.count(),
            'total_distance_km': round(total_distance / 1000, 2),
            'is_moving': is_moving,
            'distance_moved': round(distance_moved_recently, 0),
            'connection_status': connection_status,
        })
    
    online_count = sum(1 for e in employees_data if e['connection_status'] == 'online')
    moving_count = sum(1 for e in employees_data if e['is_moving'])
    offline_count = sum(1 for e in employees_data if e['connection_status'] == 'offline')
    
    return JsonResponse({
        'success': True,
        'employees': employees_data,
        'stats': {
            'total': len(employees_data),
            'online': online_count,
            'moving': moving_count,
            'offline': offline_count,
        },
        'last_update': now.strftime('%H:%M:%S'),
    })


@login_required
def employee_tracking_detail(request, employee_id):
    """عرض تتبع موظف معين (للمدير)"""
    
    from datetime import datetime as dt
    
    employee = get_object_or_404(Employee, pk=employee_id)
    
    date_str = request.GET.get('date', '')
    if date_str:
        try:
            selected_date = dt.strptime(date_str, '%Y-%m-%d').date()
        except:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    day_start = timezone.make_aware(dt.combine(selected_date, dt.min.time()))
    day_end = timezone.make_aware(dt.combine(selected_date, dt.max.time()))
    
    locations = LocationLog.objects.filter(
        employee=employee,
        timestamp__gte=day_start,
        timestamp__lte=day_end,
    ).order_by('timestamp')
    
    context = {
        'employee': employee,
        'locations': locations,
        'selected_date': selected_date,
        'total_points': locations.count(),
    }
    
    return render(request, 'attendance/tracking_detail.html', context)
