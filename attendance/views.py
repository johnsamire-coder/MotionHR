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
    
    # هل نعرض الخريطة؟
    show_map = getattr(request.user, 'role', 'employee') != 'employee'
    if 'context' in dir():
        context['show_map'] = show_map
    else:
        context = {'show_map': show_map}

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
                'address': last_location.address or '',
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


@csrf_exempt


@login_required
def api_employee_route(request, employee_id):
    """API لخط سير موظف اليوم"""
    from datetime import date as _date
    from django.http import JsonResponse
    from attendance.models import LocationLog
    from employees.models import Employee

    try:
        emp = Employee._base_manager.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    logs = LocationLog._base_manager.filter(
        employee=emp,
        timestamp__gte=start,
        timestamp__lte=end,
    ).order_by('timestamp')

    points = [{
        'lat': float(l.latitude),
        'lng': float(l.longitude),
        'address': l.address or '',
        'timestamp': timezone.localtime(l.timestamp).strftime('%H:%M'),
    } for l in logs]

    return JsonResponse({
        'success': True,
        'employee_name': emp.first_name_ar + ' ' + emp.last_name_ar,
        'count': len(points),
        'points': points,
    })


@csrf_exempt
def api_track_location(request):
    """API لاستقبال المواقع من التطبيق"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST required"})
    
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


# ════════════════════════════════════════════════════════════
# صفحة تسجيل الحضور المحسنة
# ════════════════════════════════════════════════════════════
@login_required
def smart_check_in_page(request):
    """صفحة تسجيل الحضور الذكية"""
    from datetime import date as dt_date
    from employees.models import Employee

    employee = None
    today_attendance = None
    show_map = request.user.role != 'employee'

    # جلب الموظف
    emp = Employee.objects.filter(user=request.user).first()
    if emp:
        employee = emp
        # جلب حضور اليوم
        today_attendance = Attendance.objects.filter(
            employee=emp,
            date=dt_date.today()
        ).first()

    # جلب تكليف اليوم
    today_assignment = None
    if employee:
        today_assignment = _get_today_assignment(employee)

    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'today_assignment': today_assignment,
        'show_map': show_map,
        'page_title': 'تسجيل الحضور',
    }
    return render(request, 'attendance/check_in.html', context)


# ════════════════════════════════════════════════════════════
# Guarded Visit Add Page (للميداني فقط)
# ════════════════════════════════════════════════════════════
@login_required
def field_visit_add_page(request):
    """
    الموظف العادي ما يفتحش صفحة الزيارة
    الموظف الميداني فقط هو اللي يقدر يفتحها
    المديرين / HR / company admin يقدروا يفتحوها
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from employees.models import Employee

    # الموظف العادي
    if getattr(request.user, "role", "") == "employee":
        employee = Employee.objects.filter(user=request.user).first()

        if not employee:
            messages.error(request, "لم يتم ربط حسابك بأي موظف")
            return redirect("dashboard")

        if not getattr(employee, "is_field_worker", False):
            messages.warning(request, "تسجيل الزيارات الميدانية متاح للموظفين الميدانيين فقط")
            return redirect("attendance:check_in")

    # لو ميداني أو مدير/HR/صاحب شركة
    return visit_add(request)


# ════════════════════════════════════════════════════════════
# Smart Check-in API (مع Geofencing)
# ════════════════════════════════════════════════════════════
@login_required
def smart_api_check_in(request):
    """
    API تسجيل الحضور مع Geofencing
    - لازم يكون في نطاق الفرع
    - بيسجل المسافة والعنوان
    """
    import json
    from datetime import date as dt_date, datetime as dt_datetime
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    lat = body.get("latitude")
    lng = body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"success": False, "message": "لم يتم تحديد الموقع"})

    lat = float(lat)
    lng = float(lng)

    # جلب الموظف
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    # التحقق من عدم وجود حضور اليوم
    today = dt_date.today()
    existing = Attendance.objects.filter(
        employee=employee,
        date=today
    ).first()

    if existing:
        return JsonResponse({"success": False, "message": "تم تسجيل حضورك بالفعل اليوم"})

    # ═══ Geofencing ═══
    branch = employee.branch
    within_range = True
    distance = 0

    if branch and branch.latitude and branch.longitude:
        distance = round(calculate_distance(lat, lng, float(branch.latitude), float(branch.longitude)))
        radius = branch.check_in_radius or 100

        if distance > radius:
            return JsonResponse({
                "success": False,
                "message": f"أنت خارج نطاق الفرع. المسافة: {distance} متر (النطاق المسموح: {radius} متر)"
            })
        within_range = True
    else:
        within_range = True
        distance = 0

    # تسجيل الحضور
    now = dt_datetime.now()

    att_kwargs = {
        "company": employee.company,
        "employee": employee,
        "date": today,
        "status": "present",
    }

    # حقول اختيارية حسب الموجود في Model
    att_fields = {f.name for f in Attendance._meta.fields}

    if "check_in_time" in att_fields:
        att_kwargs["check_in_time"] = now.time()
    if "check_in_latitude" in att_fields:
        att_kwargs["check_in_latitude"] = Decimal(str(lat))
    if "check_in_longitude" in att_fields:
        att_kwargs["check_in_longitude"] = Decimal(str(lng))
    if "check_in_address" in att_fields:
        att_kwargs["check_in_address"] = address
    if "within_range" in att_fields:
        att_kwargs["within_range"] = within_range
    if "check_in_within_range" in att_fields:
        att_kwargs["check_in_within_range"] = within_range

    # حساب التأخير
    if "late_minutes" in att_fields:
        late_mins = 0
        try:
            from attendance.models import EmployeeShift
            emp_shift = EmployeeShift.objects.filter(
                employee=employee, is_active=True
            ).select_related("shift").first()

            if emp_shift and emp_shift.shift:
                shift = emp_shift.shift
                grace = shift.grace_period or 0
                shift_start = dt_datetime.combine(today, shift.start_time)
                allowed_time = shift_start + __import__("datetime").timedelta(minutes=grace)

                if now > allowed_time:
                    late_mins = int((now - shift_start).total_seconds() / 60)
                    att_kwargs["status"] = "late"
        except Exception:
            pass

        att_kwargs["late_minutes"] = late_mins

    if "shift" in att_fields:
        try:
            from attendance.models import EmployeeShift
            emp_shift = EmployeeShift.objects.filter(
                employee=employee, is_active=True
            ).select_related("shift").first()
            if emp_shift:
                att_kwargs["shift"] = emp_shift.shift
        except Exception:
            pass

    try:
        Attendance.objects.create(**att_kwargs)

        msg = "تم تسجيل حضورك بنجاح"
        if distance > 0:
            msg += f" (المسافة: {distance} متر)"

        return JsonResponse({"success": True, "status": "success", "message": msg})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})


# ════════════════════════════════════════════════════════════
# Smart Check-out API (بدون Geofencing)
# ════════════════════════════════════════════════════════════
@login_required
def smart_api_check_out(request):
    """
    API تسجيل الانصراف
    - من أي مكان (بدون geofencing)
    - بيحسب ساعات العمل
    """
    import json
    from datetime import date as dt_date, datetime as dt_datetime
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    lat = body.get("latitude")
    lng = body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"success": False, "message": "لم يتم تحديد الموقع"})

    lat = float(lat)
    lng = float(lng)

    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    attendance = Attendance.objects.filter(
        employee=employee,
        date=today
    ).first()

    if not attendance:
        return JsonResponse({"success": False, "message": "لم تسجل حضور اليوم بعد"})

    att_fields = {f.name for f in Attendance._meta.fields}

    if "check_out_time" in att_fields:
        if attendance.check_out_time:
            return JsonResponse({"success": False, "message": "تم تسجيل انصرافك بالفعل"})

    # تسجيل الانصراف
    now = dt_datetime.now()

    if "check_out_time" in att_fields:
        attendance.check_out_time = now.time()
    if "check_out_latitude" in att_fields:
        attendance.check_out_latitude = Decimal(str(lat))
    if "check_out_longitude" in att_fields:
        attendance.check_out_longitude = Decimal(str(lng))
    if "check_out_address" in att_fields:
        attendance.check_out_address = address

    # حساب ساعات العمل
    if "work_hours" in att_fields and "check_in_time" in att_fields:
        try:
            check_in_dt = dt_datetime.combine(today, attendance.check_in_time)
            diff = now - check_in_dt
            hours = round(diff.total_seconds() / 3600, 1)
            attendance.work_hours = Decimal(str(hours))
        except Exception:
            pass

    try:
        attendance.save()
        return JsonResponse({
            "success": True,
            "status": "success",
            "message": "تم تسجيل انصرافك بنجاح"
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})


# ════════════════════════════════════════════════════════════
# Policy Helper for Attendance
# ════════════════════════════════════════════════════════════
def _get_company_policy(company):
    try:
        from companies.models import CompanyPolicy
        return CompanyPolicy.get_for_company(company)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# Policy Helpers
# ════════════════════════════════════════════════════════════
def _get_company_policy(company):
    try:
        from companies.models import CompanyPolicy
        return CompanyPolicy.get_for_company(company)
    except Exception:
        return None


def _get_checkin_radius(branch, policy):
    """النطاق الفعلي = branch radius أو default policy + tolerance"""
    radius = 100
    tolerance = 0

    if policy:
        try:
            radius = int(policy.default_checkin_radius or 100)
        except Exception:
            radius = 100
        try:
            tolerance = int(policy.distance_tolerance_meters or 0)
        except Exception:
            tolerance = 0

    if branch and getattr(branch, "check_in_radius", None):
        try:
            radius = int(branch.check_in_radius or radius)
        except Exception:
            pass

    return radius + tolerance


def _get_grace_period_minutes(employee, policy):
    """سماحية التأخير من سياسة الشركة، ولو مش موجودة من الشيفت"""
    if policy and getattr(policy, "grace_period_minutes", None) is not None:
        try:
            return int(policy.grace_period_minutes or 0)
        except Exception:
            pass

    try:
        from attendance.models import EmployeeShift
        emp_shift = EmployeeShift.objects.filter(
            employee=employee, is_active=True
        ).select_related("shift").first()
        if emp_shift and emp_shift.shift:
            return int(getattr(emp_shift.shift, "grace_period", 0) or 0)
    except Exception:
        pass

    return 0


def _can_hr_manage_attendance(user, company):
    """هل المستخدم له صلاحية تعديل/إلغاء الحضور؟"""
    role = getattr(user, "role", "")
    if role == "super_admin":
        return True

    if role not in ["hr_manager", "company_admin"]:
        return False

    policy = _get_company_policy(company)
    if not policy:
        return role in ["hr_manager", "company_admin"]

    return bool(
        getattr(policy, "hr_can_edit_attendance", False) or
        getattr(policy, "hr_can_cancel_attendance", False)
    )


def _attendance_snapshot(attendance):
    """لقطة من السجل قبل/بعد التعديل"""
    data = {}
    for field_name in [
        "status",
        "check_in_time",
        "check_out_time",
        "late_minutes",
        "work_hours",
        "check_in_address",
        "check_out_address",
    ]:
        if hasattr(attendance, field_name):
            val = getattr(attendance, field_name)
            data[field_name] = str(val) if val is not None else None
    return data


# ════════════════════════════════════════════════════════════
# Policy-based Check-in API
# ════════════════════════════════════════════════════════════
@login_required
def policy_api_check_in(request):
    import json
    from datetime import date as dt_date, datetime as dt_datetime
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    lat = body.get("latitude")
    lng = body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"success": False, "message": "لم يتم تحديد الموقع"})

    lat = float(lat)
    lng = float(lng)

    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    existing = Attendance.objects.filter(employee=employee, date=today).first()
    if existing:
        return JsonResponse({"success": False, "message": "تم تسجيل حضورك بالفعل اليوم"})

    policy = _get_company_policy(employee.company)

    # ═══ Assignment Check ═══
    assignment = _get_today_assignment(employee)
    allowed, msg, checkin_mode = _check_assignment_allows_checkin(assignment, policy)

    if not allowed:
        return JsonResponse({"success": False, "message": msg})

    branch = employee.branch

    within_range = True
    distance = 0
    radius = _get_checkin_radius(branch, policy)

    # هل الحضور لازم داخل النطاق؟
    requires_range = True
    if policy and hasattr(policy, "checkin_requires_branch_range"):
        requires_range = bool(policy.checkin_requires_branch_range)

    if branch and branch.latitude and branch.longitude:
        distance = round(calculate_distance(lat, lng, float(branch.latitude), float(branch.longitude)))
        if requires_range and distance > radius:
            return JsonResponse({
                "success": False,
                "message": f"أنت خارج نطاق الفرع. المسافة: {distance} متر (المسموح: {radius} متر)"
            })
        within_range = distance <= radius
    else:
        within_range = True

    now = dt_datetime.now()

    att_kwargs = {
        "company": employee.company,
        "employee": employee,
        "date": today,
        "status": "present",
    }

    att_fields = {f.name for f in Attendance._meta.fields}

    if "check_in_time" in att_fields:
        att_kwargs["check_in_time"] = now.time()
    if "check_in_latitude" in att_fields:
        att_kwargs["check_in_latitude"] = Decimal(str(lat))
    if "check_in_longitude" in att_fields:
        att_kwargs["check_in_longitude"] = Decimal(str(lng))
    if "check_in_address" in att_fields:
        att_kwargs["check_in_address"] = address
    if "within_range" in att_fields:
        att_kwargs["within_range"] = within_range
    if "check_in_within_range" in att_fields:
        att_kwargs["check_in_within_range"] = within_range

    # الشيفت
    if "shift" in att_fields:
        try:
            from attendance.models import EmployeeShift
            emp_shift = EmployeeShift.objects.filter(
                employee=employee, is_active=True
            ).select_related("shift").first()
            if emp_shift:
                att_kwargs["shift"] = emp_shift.shift
        except Exception:
            pass

    # التأخير باستخدام policy grace_period
    if "late_minutes" in att_fields:
        late_mins = 0
        try:
            from attendance.models import EmployeeShift
            emp_shift = EmployeeShift.objects.filter(
                employee=employee, is_active=True
            ).select_related("shift").first()

            if emp_shift and emp_shift.shift:
                shift = emp_shift.shift
                grace = _get_grace_period_minutes(employee, policy)
                shift_start = dt_datetime.combine(today, shift.start_time)
                allowed_time = shift_start + __import__("datetime").timedelta(minutes=grace)

                if now > allowed_time:
                    late_mins = int((now - shift_start).total_seconds() / 60)
                    att_kwargs["status"] = "late"
        except Exception:
            pass

        att_kwargs["late_minutes"] = late_mins

    try:
        attendance_obj = Attendance.objects.create(**att_kwargs)

        # ═══ Assignment post-processing ═══
        _handle_assignment_checkin(employee, assignment, policy, attendance_obj, now)

        # لو exception
        if checkin_mode == "exception" and assignment is None:
            from attendance.models import DailyAssignment
            DailyAssignment.objects.create(
                company=employee.company,
                employee=employee,
                date=today,
                day_type="work_day",
                work_mode=getattr(employee, "attendance_mode", "fixed") or "fixed",
                expected_hours=getattr(employee, "required_daily_hours", 8) or 8,
                is_exception=True,
                exception_reason="حضور بدون تكليف مسبق",
                exception_status="pending_review",
                is_auto_generated=True,
            )

        # لو Late → سجل حادثة تأخير + إشعار
        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:
            _record_late_incident(
                employee=employee,
                attendance_obj=attendance_obj,
                late_minutes=att_kwargs.get("late_minutes", 0)
            )

        msg = "تم تسجيل حضورك بنجاح"
        if branch and branch.latitude and branch.longitude:
            msg += f" - المسافة من الفرع: {distance} متر"

        if int(att_kwargs.get("late_minutes", 0) or 0) > 0:
            msg += f" - تم تسجيل {att_kwargs.get('late_minutes', 0)} دقيقة تأخير"

        if checkin_mode == "exception":
            msg += " (حالة استثنائية - سيتم مراجعتها)"
        elif checkin_mode == "off_notify":
            msg += " (يوم راحة - تم إشعار HR)"
        elif checkin_mode == "holiday_extra":
            msg += " (إجازة رسمية - سيتحسب شيفت إضافي)"

        return JsonResponse({"success": True, "status": "success", "message": msg})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})


# ════════════════════════════════════════════════════════════
# Policy-based Check-out API
# ════════════════════════════════════════════════════════════
@login_required
def policy_api_check_out(request):
    import json
    from datetime import date as dt_date, datetime as dt_datetime
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    lat = body.get("latitude")
    lng = body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"success": False, "message": "لم يتم تحديد الموقع"})

    lat = float(lat)
    lng = float(lng)

    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"success": False, "message": "لم يتم ربط حسابك بملف موظف"})

    today = dt_date.today()
    attendance = Attendance.objects.filter(employee=employee, date=today).first()

    if not attendance:
        return JsonResponse({"success": False, "message": "لم تسجل حضور اليوم بعد"})

    att_fields = {f.name for f in Attendance._meta.fields}
    if "check_out_time" in att_fields and getattr(attendance, "check_out_time", None):
        return JsonResponse({"success": False, "message": "تم تسجيل انصرافك بالفعل"})

    policy = _get_company_policy(employee.company)
    allow_anywhere = True
    if policy and hasattr(policy, "checkout_from_anywhere"):
        allow_anywhere = bool(policy.checkout_from_anywhere)

    # لو مش مسموح من أي مكان → نتحقق من النطاق
    if not allow_anywhere:
        branch = employee.branch
        if branch and branch.latitude and branch.longitude:
            distance = round(calculate_distance(lat, lng, float(branch.latitude), float(branch.longitude)))
            radius = _get_checkin_radius(branch, policy)
            if distance > radius:
                return JsonResponse({
                    "success": False,
                    "message": f"الانصراف خارج النطاق غير مسموح. المسافة: {distance} متر"
                })

    now = dt_datetime.now()

    if "check_out_time" in att_fields:
        attendance.check_out_time = now.time()
    if "check_out_latitude" in att_fields:
        attendance.check_out_latitude = Decimal(str(lat))
    if "check_out_longitude" in att_fields:
        attendance.check_out_longitude = Decimal(str(lng))
    if "check_out_address" in att_fields:
        attendance.check_out_address = address

    # حساب ساعات العمل
    if "work_hours" in att_fields and hasattr(attendance, "check_in_time") and attendance.check_in_time:
        try:
            check_in_dt = dt_datetime.combine(today, attendance.check_in_time)
            diff = now - check_in_dt
            hours = round(diff.total_seconds() / 3600, 1)
            attendance.work_hours = Decimal(str(hours))
        except Exception:
            pass

    try:
        attendance.save()
        return JsonResponse({
            "success": True,
            "status": "success",
            "message": "تم تسجيل انصرافك بنجاح"
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": f"خطأ: {str(e)}"})


# ════════════════════════════════════════════════════════════
# HR Attendance Override
# ════════════════════════════════════════════════════════════
@login_required
def attendance_override(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    from attendance.models import Attendance, AttendanceActionLog

    attendance = get_object_or_404(
        Attendance.all_objects if hasattr(Attendance, "all_objects") else Attendance.objects,
        pk=pk
    )

    if not _can_hr_manage_attendance(request.user, attendance.company):
        messages.error(request, "ليس لديك صلاحية تعديل/إلغاء الحضور")
        return redirect("attendance:list")

    policy = _get_company_policy(attendance.company)

    if request.method == "POST":
        action = request.POST.get("action")
        reason = request.POST.get("reason", "").strip()

        require_reason = True
        if policy and hasattr(policy, "attendance_edit_reason_required"):
            require_reason = bool(policy.attendance_edit_reason_required)

        if require_reason and not reason:
            messages.error(request, "سبب التعديل / الإلغاء إجباري")
            return redirect("attendance:override", pk=attendance.pk)

        old_data = _attendance_snapshot(attendance)

        if action == "edit":
            if hasattr(attendance, "check_in_time") and request.POST.get("check_in_time"):
                attendance.check_in_time = request.POST.get("check_in_time")
            if hasattr(attendance, "check_out_time") and request.POST.get("check_out_time"):
                attendance.check_out_time = request.POST.get("check_out_time")
            if hasattr(attendance, "status") and request.POST.get("status"):
                attendance.status = request.POST.get("status")
            if hasattr(attendance, "admin_notes"):
                attendance.admin_notes = reason
            if hasattr(attendance, "is_manually_edited"):
                attendance.is_manually_edited = True
            attendance.save()

            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="edit",
                performed_by=request.user,
                reason=reason or "تعديل يدوي",
                old_data=old_data,
                new_data=_attendance_snapshot(attendance),
            )
            messages.success(request, "تم تعديل سجل الحضور بنجاح")

        elif action == "cancel_checkin":
            if hasattr(attendance, "check_in_time"):
                attendance.check_in_time = None
            if hasattr(attendance, "check_in_latitude"):
                attendance.check_in_latitude = None
            if hasattr(attendance, "check_in_longitude"):
                attendance.check_in_longitude = None
            if hasattr(attendance, "check_in_address"):
                attendance.check_in_address = ""
            if hasattr(attendance, "admin_notes"):
                attendance.admin_notes = reason
            if hasattr(attendance, "is_manually_edited"):
                attendance.is_manually_edited = True
            attendance.save()

            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="cancel_checkin",
                performed_by=request.user,
                reason=reason or "إلغاء حضور",
                old_data=old_data,
                new_data=_attendance_snapshot(attendance),
            )
            messages.success(request, "تم إلغاء تسجيل الحضور")

        elif action == "cancel_checkout":
            if hasattr(attendance, "check_out_time"):
                attendance.check_out_time = None
            if hasattr(attendance, "check_out_latitude"):
                attendance.check_out_latitude = None
            if hasattr(attendance, "check_out_longitude"):
                attendance.check_out_longitude = None
            if hasattr(attendance, "check_out_address"):
                attendance.check_out_address = ""
            if hasattr(attendance, "admin_notes"):
                attendance.admin_notes = reason
            if hasattr(attendance, "is_manually_edited"):
                attendance.is_manually_edited = True
            attendance.save()

            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="cancel_checkout",
                performed_by=request.user,
                reason=reason or "إلغاء انصراف",
                old_data=old_data,
                new_data=_attendance_snapshot(attendance),
            )
            messages.success(request, "تم إلغاء تسجيل الانصراف")

        elif action == "delete":
            AttendanceActionLog.objects.create(
                company=attendance.company,
                attendance=attendance,
                action_type="delete",
                performed_by=request.user,
                reason=reason or "حذف السجل",
                old_data=old_data,
                new_data={},
            )
            attendance.delete()
            messages.success(request, "تم حذف سجل الحضور")
            return redirect("attendance:list")

        return redirect("attendance:override", pk=pk)

    context = {
        "attendance_obj": attendance,
        "page_title": "تعديل / إلغاء الحضور",
    }
    return render(request, "attendance/override_form.html", context)


# ════════════════════════════════════════════════════════════
# Late Engine Helpers
# ════════════════════════════════════════════════════════════
def _get_late_stage(policy, incident_count):
    """
    تحديد المرحلة الحالية حسب عدد مرات التأخير
    """
    if not policy:
        return None, None

    if incident_count >= getattr(policy, "late_full_day_deduction_after_count", 999):
        return "full_day_deduction", "خصم يوم كامل"
    elif incident_count >= getattr(policy, "late_half_day_deduction_after_count", 999):
        return "half_day_deduction", "خصم نصف يوم"
    elif incident_count >= getattr(policy, "late_quarter_day_deduction_after_count", 999):
        return "quarter_day_deduction", "خصم ربع يوم"
    elif incident_count >= getattr(policy, "late_second_warning_after_count", 999):
        return "written_warning", "إنذار كتابي"
    elif incident_count >= getattr(policy, "late_first_warning_after_count", 999):
        return "verbal_warning", "إنذار شفهي"

    return None, None


def _build_late_details(employee, month, year):
    """
    بناء تفاصيل كل مرات التأخير في الشهر
    """
    try:
        from attendance.models import LateIncident
        incidents = LateIncident.objects.filter(
            company=employee.company,
            employee=employee,
            month=month,
            year=year
        ).order_by("date")

        lines = []
        for inc in incidents:
            lines.append(
                f"• {inc.date.strftime('%d/%m/%Y')} — "
                f"{inc.actual_checkin_time.strftime('%H:%M') if inc.actual_checkin_time else '—'} — "
                f"{inc.late_minutes} دقيقة"
            )
        return "\n".join(lines)
    except Exception:
        return ""


def _create_late_notification(employee, incident, policy):
    """
    إنشاء إشعار HR عن التأخير
    """
    try:
        from attendance.models import LateNotification

        stage_key, stage_label = _get_late_stage(policy, incident.incident_number_in_month)

        # عادي
        if not stage_key:
            title = "تنبيه تأخير"
            message = (
                f"الموظف {employee.full_name_ar} تأخر اليوم "
                f"{incident.late_minutes} دقيقة"
            )
            details = (
                f"التاريخ: {incident.date.strftime('%d/%m/%Y')}\n"
                f"وقت الحضور: {incident.actual_checkin_time.strftime('%H:%M') if incident.actual_checkin_time else '—'}\n"
                f"عدد مرات التأخير هذا الشهر: {incident.incident_number_in_month}"
            )
            suggested_action = ""
            notif_type = "single_late"
        else:
            # وصل للحد
            title = "تكرار تأخير - يتطلب إجراء"
            details_text = _build_late_details(employee, incident.month, incident.year)
            message = (
                f"الموظف {employee.full_name_ar} تأخر "
                f"{incident.incident_number_in_month} مرات هذا الشهر."
            )
            details = (
                f"عدد مرات التأخير هذا الشهر: {incident.incident_number_in_month}\n\n"
                f"{details_text}"
            )
            suggested_action = stage_label
            notif_type = "threshold_reached"

        LateNotification.objects.create(
            company=employee.company,
            employee=employee,
            notification_type=notif_type,
            title=title,
            message=message,
            details=details,
            suggested_action=suggested_action or "",
            incident_count=incident.incident_number_in_month,
            month=incident.month,
            year=incident.year,
        )

        return True
    except Exception:
        return False


def _record_late_incident(employee, attendance_obj, late_minutes):
    """
    تسجيل حادثة التأخير وإنشاء الإشعار
    """
    try:
        from attendance.models import LateIncident
        from django.utils import timezone
        today = timezone.now().date()
        policy = _get_company_policy(employee.company)

        # لو العداد بيتصفر شهريًا
        month = today.month
        year = today.year

        count = LateIncident.objects.filter(
            company=employee.company,
            employee=employee,
            month=month,
            year=year
        ).count() + 1

        incident = LateIncident.objects.create(
            company=employee.company,
            employee=employee,
            attendance=attendance_obj,
            date=today,
            late_minutes=int(late_minutes or 0),
            shift_start_time=getattr(getattr(attendance_obj, "shift", None), "start_time", None),
            actual_checkin_time=getattr(attendance_obj, "check_in_time", None),
            grace_period_used=_get_grace_period_minutes(employee, policy),
            month=month,
            year=year,
            incident_number_in_month=count,
            is_excused=False,
            excuse_reason="",
        )

        _create_late_notification(employee, incident, policy)
        return incident
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# Late Notifications & Actions
# ════════════════════════════════════════════════════════════
@login_required
def late_notifications_list(request):
    """قائمة إشعارات التأخير لـ HR / الإدارة"""
    from attendance.models import LateNotification

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول لهذه الصفحة")
        return redirect("dashboard")

    qs = LateNotification.objects.filter(
        company=request.user.company
    ).select_related("employee").order_by("-created_at")

    status_filter = request.GET.get("status")
    if status_filter == "pending":
        qs = qs.filter(is_acted_upon=False)
    elif status_filter == "done":
        qs = qs.filter(is_acted_upon=True)
    elif status_filter == "unread":
        qs = qs.filter(is_read=False)

    context = {
        "notifications": qs,
        "status_filter": status_filter,
        "page_title": "إشعارات التأخير",
    }
    return render(request, "attendance/late_notifications_list.html", context)


@login_required
def late_notification_detail(request, pk):
    """تفاصيل إشعار التأخير + اتخاذ الإجراء"""
    from attendance.models import LateNotification, DisciplinaryAction
    from employees.models import Deduction
    from django.utils import timezone

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول لهذه الصفحة")
        return redirect("dashboard")

    notif = get_object_or_404(
        LateNotification.objects.select_related("employee"),
        pk=pk,
        company=request.user.company
    )

    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=["is_read"])

    policy = _get_company_policy(request.user.company)

    if request.method == "POST":
        chosen_action = request.POST.get("action_taken", "").strip()
        action_notes = request.POST.get("action_notes", "").strip()

        if not chosen_action:
            messages.error(request, "اختر الإجراء أولاً")
            return redirect("attendance:late_notification_detail", pk=pk)

        # لو الشركة طالبة سبب في حالة override / ignore
        require_reason = False
        if policy and hasattr(policy, "hr_override_reason_required"):
            require_reason = bool(policy.hr_override_reason_required)

        if require_reason and chosen_action == "dismissed" and not action_notes:
            messages.error(request, "سبب تجاهل الإجراء المقترح إجباري")
            return redirect("attendance:late_notification_detail", pk=pk)

        # لو اتاخد إجراء قبل كده
        if notif.is_acted_upon:
            messages.warning(request, "تم اتخاذ إجراء على هذا الإشعار مسبقًا")
            return redirect("attendance:late_notification_detail", pk=pk)

        # إنشاء إجراء تأديبي
        action = DisciplinaryAction.objects.create(
            company=request.user.company,
            employee=notif.employee,
            action_type=chosen_action,
            reason=notif.message,
            related_notification=notif,
            auto_generated=False,
            performed_by=request.user,
            notes=action_notes,
        )

        # لو خصم → أنشئ Deduction
        deduction_amount = None
        if chosen_action in ["quarter_day_deduction", "half_day_deduction", "full_day_deduction"]:
            salary = getattr(notif.employee, "basic_salary", None) or 0
            day_value = 0
            try:
                day_value = float(salary) / 30 if salary else 0
            except Exception:
                day_value = 0

            if chosen_action == "quarter_day_deduction":
                deduction_amount = round(day_value / 4, 2)
                reason_text = "خصم ربع يوم بسبب تكرار التأخير"
            elif chosen_action == "half_day_deduction":
                deduction_amount = round(day_value / 2, 2)
                reason_text = "خصم نصف يوم بسبب تكرار التأخير"
            else:
                deduction_amount = round(day_value, 2)
                reason_text = "خصم يوم كامل بسبب تكرار التأخير"

            Deduction.objects.create(
                company=request.user.company,
                employee=notif.employee,
                deduction_type="penalty",
                amount=deduction_amount,
                date=timezone.now().date(),
                reason=reason_text,
                month=timezone.now().month,
                year=timezone.now().year,
                is_visible_to_employee=True,
                notes=action_notes,
            )

            action.deduction_amount = deduction_amount
            action.deduction_created = True
            action.save(update_fields=["deduction_amount", "deduction_created"])

        # تحديث الإشعار
        notif.is_acted_upon = True
        notif.action_taken = chosen_action
        notif.action_by = request.user
        notif.action_at = timezone.now()
        notif.action_notes = action_notes
        notif.save()

        # إشعار الموظف
        _send_employee_notification_for_action(
            employee=notif.employee,
            action=action,
            sent_by=request.user
        )

        messages.success(request, "تم تسجيل الإجراء بنجاح")
        return redirect("attendance:late_notification_detail", pk=pk)

    context = {
        "notif": notif,
        "page_title": "تفاصيل إشعار التأخير",
    }
    return render(request, "attendance/late_notification_detail.html", context)


@login_required
def my_warnings_view(request):
    """إنذاراتي / إجراءاتي التأديبية للموظف"""
    from attendance.models import DisciplinaryAction
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    current_employee = Employee.all_objects.filter(user=request.user).first()

    if not current_employee:
        messages.error(request, "لم يتم ربط حسابك بملف موظف")
        return redirect("dashboard")

    policy = _get_company_policy(request.user.company)
    can_view = True
    if policy and hasattr(policy, "employee_can_view_warnings"):
        can_view = bool(policy.employee_can_view_warnings)

    if not can_view:
        messages.warning(request, "عرض الإنذارات غير متاح حسب سياسة الشركة")
        return redirect("dashboard")

    actions = DisciplinaryAction.objects.filter(
        company=request.user.company,
        employee=current_employee
    ).order_by("-performed_at")

    context = {
        "actions": actions,
        "page_title": "إنذاراتي وإجراءاتي",
    }
    return render(request, "attendance/my_warnings.html", context)


# ════════════════════════════════════════════════════════════
# Assignment-aware Check-in Helpers
# ════════════════════════════════════════════════════════════

def _get_today_assignment(employee):
    """جلب تكليف اليوم للموظف"""
    from attendance.models import DailyAssignment
    from django.utils import timezone
    today = timezone.now().date()
    return DailyAssignment.objects.filter(
        company=employee.company,
        employee=employee,
        date=today
    ).first()


def _check_assignment_allows_checkin(assignment, policy):
    """
    التحقق: هل التكليف يسمح بـ check-in؟
    Returns: (allowed, message, checkin_mode)
    """
    if not assignment:
        # مفيش تكليف
        mode = "use_default"
        if policy and hasattr(policy, "unplanned_checkin_mode"):
            mode = policy.unplanned_checkin_mode or "use_default"

        if mode == "block":
            return False, "لا يوجد تكليف لك اليوم. تواصل مع مديرك أو HR", "blocked"
        elif mode == "create_exception":
            return True, "سيتم تسجيل حضورك كحالة استثنائية", "exception"
        else:
            return True, "", "default"

    # لو يوم راحة
    if assignment.day_type == "off_day":
        mode = "allow_notify_hr"
        if policy and hasattr(policy, "off_day_checkin_mode"):
            mode = policy.off_day_checkin_mode or "allow_notify_hr"

        if mode == "block":
            return False, "اليوم يوم راحة. لا يمكن تسجيل الحضور", "blocked"
        elif mode == "allow_notify_hr":
            return True, "اليوم يوم راحة. سيتم إشعار HR", "off_notify"
        else:
            return True, "اليوم يوم راحة. سيتم مراجعة الحضور من HR", "off_convert"

    # لو إجازة
    if assignment.day_type == "leave_day":
        mode = "block"
        if policy and hasattr(policy, "leave_day_checkin_mode"):
            mode = policy.leave_day_checkin_mode or "block"

        if mode == "block":
            return False, "عندك إجازة معتمدة اليوم. لا يمكن تسجيل الحضور", "blocked"
        elif mode == "allow_notify_hr":
            return True, "عندك إجازة اليوم. سيتم إشعار HR", "leave_notify"
        else:
            return True, "عندك إجازة اليوم. سيتم مراجعة الحضور من HR", "leave_convert"

    # لو إجازة رسمية
    if assignment.day_type == "holiday":
        return True, "اليوم إجازة رسمية. سيتم تسجيل حضورك كشيفت إضافي", "holiday_extra"

    # لو يوم عمل عادي / مأمورية / تدريب / استدعاء
    return True, "", "normal"


def _get_late_logic_for_assignment(assignment, employee, policy, now):
    """
    تحديد التأخير حسب نوع التكليف
    Returns: (is_late, late_minutes)
    """
    import datetime as dt

    # الأنواع اللي ما فيهاش late
    if not assignment:
        return False, 0

    if assignment.day_type not in ["work_day", "training_day"]:
        return False, 0

    if assignment.work_mode in ["flexible", "field", "remote"]:
        return False, 0

    # fixed / split / mixed → late ينطبق
    shift_start = assignment.start_time
    if not shift_start and assignment.shift:
        shift_start = getattr(assignment.shift, "start_time", None)

    if not shift_start:
        return False, 0

    grace = 0
    if policy and hasattr(policy, "grace_period_minutes"):
        try:
            grace = int(policy.grace_period_minutes or 0)
        except Exception:
            grace = 0

    today = now.date()
    shift_start_dt = dt.datetime.combine(today, shift_start)
    allowed_time = shift_start_dt + dt.timedelta(minutes=grace)

    if now > allowed_time:
        late_mins = int((now - shift_start_dt).total_seconds() / 60)
        return True, late_mins

    return False, 0


def _handle_assignment_checkin(employee, assignment, policy, attendance_obj, now):
    """
    معالجة ما بعد check-in حسب التكليف
    """
    from attendance.models import DailyAssignment

    if not assignment:
        return

    # تحديث حالة التكليف
    if hasattr(assignment, "status"):
        assignment.status = "in_progress"
        assignment.save(update_fields=["status"])

    # لو holiday → convert to extra
    if assignment.day_type == "holiday":
        if not assignment.is_extra_shift:
            assignment.is_extra_shift = True
            assignment.count_as_overtime = True
            assignment.save(update_fields=["is_extra_shift", "count_as_overtime"])


# ════════════════════════════════════════════════════════════
# Schedule Management
# ════════════════════════════════════════════════════════════

@login_required
def schedule_week_view(request):
    """عرض جدول الأسبوع لكل الموظفين"""
    from attendance.models import DailyAssignment
    from employees.models import Employee
    from datetime import timedelta
    from django.utils import timezone

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company
    today = timezone.now().date()

    # نقطة بداية الأسبوع
    week_offset = int(request.GET.get("week", 0))
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

    # بناء أيام الأسبوع
    days = []
    day_names = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    for i in range(7):
        d = week_start + timedelta(days=i)
        days.append({
            "date": d,
            "name": day_names[i],
            "is_today": d == today,
        })

    # الموظفين
    if role == "manager":
        current_emp = Employee.all_objects.filter(user=request.user).first()
        if current_emp:
            employees = Employee.all_objects.filter(
                company=company,
                direct_manager=current_emp,
                status="active"
            ).select_related("department", "job_title")
        else:
            employees = Employee.all_objects.none()
    else:
        employees = Employee.all_objects.filter(
            company=company,
            status="active"
        ).select_related("department", "job_title")

    # التكليفات
    assignments = DailyAssignment.objects.filter(
        company=company,
        date__range=[week_start, week_start + timedelta(days=6)]
    ).select_related("employee")

    # بناء matrix
    assignment_map = {}
    for a in assignments:
        key = f"{a.employee_id}_{a.date}"
        assignment_map[key] = a

    schedule_rows = []
    for emp in employees:
        row = {
            "employee": emp,
            "days": [],
        }
        for day_info in days:
            key = f"{emp.id}_{day_info['date']}"
            assignment = assignment_map.get(key)
            row["days"].append({
                "date": day_info["date"],
                "assignment": assignment,
            })
        schedule_rows.append(row)

    context = {
        "days": days,
        "schedule_rows": schedule_rows,
        "week_start": week_start,
        "week_end": week_start + timedelta(days=6),
        "week_offset": week_offset,
        "prev_week": week_offset - 1,
        "next_week": week_offset + 1,
        "page_title": "جدول العمل الأسبوعي",
    }
    return render(request, "attendance/schedule_week.html", context)


@login_required
def assignment_add(request):
    """إضافة تكليف يومي"""
    from attendance.models import DailyAssignment, Shift
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية")
        return redirect("dashboard")

    company = request.user.company
    employees = Employee.all_objects.filter(company=company, status="active")
    shifts = Shift.objects.filter(company=company)

    if request.method == "POST":
        emp_id = request.POST.get("employee")
        date_str = request.POST.get("date")
        day_type = request.POST.get("day_type", "work_day")
        work_mode = request.POST.get("work_mode", "fixed")

        if not emp_id or not date_str:
            messages.error(request, "الموظف والتاريخ مطلوبين")
        else:
            from datetime import date as dt_date
            emp = get_object_or_404(Employee.all_objects, pk=emp_id, company=company)
            d = dt_date.fromisoformat(date_str)

            existing = DailyAssignment.objects.filter(
                company=company, employee=emp, date=d
            ).first()

            if existing:
                obj = existing
            else:
                obj = DailyAssignment(company=company, employee=emp, date=d)

            obj.day_type = day_type
            obj.work_mode = work_mode
            obj.start_time = request.POST.get("start_time") or None
            obj.end_time = request.POST.get("end_time") or None
            obj.expected_hours = request.POST.get("expected_hours") or None
            obj.segment_2_start = request.POST.get("segment_2_start") or None
            obj.segment_2_end = request.POST.get("segment_2_end") or None
            obj.is_replacement = "is_replacement" in request.POST
            obj.is_extra_shift = "is_extra_shift" in request.POST
            obj.count_as_overtime = "count_as_overtime" in request.POST
            obj.requires_tracking = "requires_tracking" in request.POST
            obj.requires_visits = "requires_visits" in request.POST
            obj.requires_geofence = "requires_geofence" in request.POST
            obj.task_title = request.POST.get("task_title", "")
            obj.location_name = request.POST.get("location_name", "")
            obj.notes = request.POST.get("notes", "")
            obj.approved_by = request.user

            shift_id = request.POST.get("shift")
            if shift_id:
                obj.shift = get_object_or_404(Shift, pk=shift_id, company=company)

            replaces_id = request.POST.get("replaces_employee")
            if replaces_id:
                obj.replaces_employee = get_object_or_404(
                    Employee.all_objects, pk=replaces_id, company=company
                )

            obj.save()

            action = "تحديث" if existing else "إضافة"
            messages.success(request, f"تم {action} التكليف بنجاح")
            return redirect("attendance:schedule_week")

    # Pre-fill من URL params
    pre_employee = request.GET.get("employee", "")
    pre_date = request.GET.get("date", "")

    context = {
        "employees": employees,
        "shifts": shifts,
        "pre_employee": pre_employee,
        "pre_date": pre_date,
        "page_title": "إضافة / تعديل تكليف",
    }
    return render(request, "attendance/assignment_form.html", context)


# ════════════════════════════════════════════════════════════
# Employee Notification Helper
# ════════════════════════════════════════════════════════════
def _send_employee_notification_for_action(employee, action, sent_by=None):
    """
    إرسال إشعار داخلي للموظف بعد اعتماد HR للإجراء
    """
    try:
        from accounts.models import EmployeeNotification

        action_label = ""
        try:
            action_label = action.get_action_type_display()
        except Exception:
            action_label = action.action_type

        # تجاهل / إعفاء → لا نرسل إشعار
        if action.action_type == "dismissed":
            return None

        if action.action_type in ["verbal_warning", "written_warning"]:
            title = "تنبيه بخصوص التأخير"
            message = (
                "عزيزي الموظف،\n"
                "تم تسجيل تأخير عليك، ونرجو عدم تكرار ذلك مرة أخرى "
                "احترامًا لميثاق العمل وسياسات الشركة.\n\n"
                f"الإجراء المتخذ: {action_label}"
            )
            notif_type = "late_warning"
            severity = "warning"
        elif action.action_type in ["quarter_day_deduction", "half_day_deduction", "full_day_deduction"]:
            title = "إشعار خصم بسبب التأخير"
            amount_text = ""
            if action.deduction_amount:
                amount_text = f"\nقيمة الخصم: {action.deduction_amount} ج.م"
            message = (
                "عزيزي الموظف،\n"
                "تم اتخاذ إجراء خصم بسبب تكرار التأخير "
                "وفقًا لسياسة الشركة.\n\n"
                f"الإجراء المتخذ: {action_label}"
                f"{amount_text}"
            )
            notif_type = "deduction_notice"
            severity = "danger"
        else:
            title = "تحديث بخصوص التأخير"
            message = (
                "تم اتخاذ إجراء بخصوص التأخير المسجل عليك.\n\n"
                f"الإجراء المتخذ: {action_label}"
            )
            notif_type = "general_notice"
            severity = "info"

        return EmployeeNotification.objects.create(
            employee=employee,
            title=title,
            message=message,
            notification_type=notif_type,
            severity=severity,
            is_read=False,
            related_action=action,
            sent_by=sent_by,
        )
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# Stealth Tracking Management
# ════════════════════════════════════════════════════════════

@login_required
def stealth_tracking_manage(request):
    """إدارة التتبع الصامت — Patch 49a Fix5"""
    from companies.models import CompanyPolicy
    from employees.models import Employee

    company = getattr(request.user, "company", None)
    if not company:
        try:
            company = request.user.employee.company
        except Exception:
            company = None

    if not company:
        messages.error(request, "لا يمكن تحديد الشركة الحالية.")
        return render(request, "attendance/stealth_manage.html", {
            "policy_enabled": False,
            "field_employees": [],
            "policy": None,
        })

    # اقرأ سياسة الشركة بشكل موحد، ولو فيه duplicates اختار الأخيرة
    policies = CompanyPolicy.objects.filter(company=company).order_by("id")
    policy = policies.last()

    if not policy:
        policy = CompanyPolicy.objects.create(company=company)

    # حذف أي duplicates قديمة
    extras = policies.exclude(id=policy.id)
    if extras.exists():
        extras.delete()

    policy_enabled = bool(getattr(policy, "stealth_tracking_enabled", False))

    # إدارة تفعيل/إيقاف الموظفين
    if request.method == "POST":
        if not policy_enabled:
            messages.warning(request, "ميزة التتبع الصامت غير مفعّلة في سياسات الشركة.")
            return redirect("attendance:stealth_manage")

        emp_id = request.POST.get("employee_id")
        action = request.POST.get("action")

        employee = get_object_or_404(
            Employee,
            id=emp_id,
            company=company,
            is_field_worker=True
        )

        if action == "enable":
            employee.stealth_tracking_enabled = True
            employee.save()
            messages.success(request, f"تم تفعيل التتبع الصامت للموظف {employee.full_name_ar}")
        elif action == "disable":
            employee.stealth_tracking_enabled = False
            employee.save()
            messages.info(request, f"تم إيقاف التتبع الصامت للموظف {employee.full_name_ar}")

        return redirect("attendance:stealth_manage")

    field_employees = Employee.objects.filter(
        company=company,
        status="active",
        is_field_worker=True
    ).select_related("branch", "department").order_by("employee_code")

    context = {
        "policy_enabled": policy_enabled,
        "field_employees": field_employees,
        "policy": policy,
    }
    return render(request, "attendance/stealth_manage.html", context)


@login_required
def stealth_tracking_alerts(request):
    """
    قائمة تنبيهات التتبع الصامت
    """
    from attendance.models import TrackingAlert
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager", "manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company
    alerts = TrackingAlert.objects.filter(company=company).select_related("employee").order_by("-started_at")

    if role == "manager":
        manager_emp = Employee.all_objects.filter(user=request.user).first()
        alerts = alerts.filter(employee__direct_manager=manager_emp)

    status_filter = request.GET.get("status")
    if status_filter:
        alerts = alerts.filter(status=status_filter)

    context = {
        "alerts": alerts,
        "status_filter": status_filter,
        "page_title": "تنبيهات التتبع",
    }
    return render(request, "attendance/stealth_alerts.html", context)


# ════════════════════════════════════════════════════════════
# Stealth Tracking Logic
# ════════════════════════════════════════════════════════════

def _is_stealth_tracking_active_for_employee(employee):
    """
    هل التتبع الصامت مفعّل لهذا الموظف دلوقتي؟
    يتطلب:
    1. الشركة فعّلت الميزة في السياسات
    2. الموظف عليه stealth_tracking_enabled = True
    3. الموظف عامل check-in اليوم وما عملش check-out
    """
    try:
        if not getattr(employee, "stealth_tracking_enabled", False):
            return False

        policy = _get_company_policy(employee.company)
        if not policy or not getattr(policy, "stealth_tracking_enabled", False):
            return False

        from datetime import date as dt_date
        today = dt_date.today()
        today_att = Attendance.objects.filter(
            employee=employee,
            date=today
        ).first()

        if not today_att:
            return False

        has_checkin = bool(getattr(today_att, "check_in_time", None))
        has_checkout = bool(getattr(today_att, "check_out_time", None))

        return has_checkin and not has_checkout
    except Exception:
        return False


def _check_and_create_tracking_alert(employee, lat, lng, address):
    """
    يتحقق من موقع الموظف أثناء العمل
    لو خارج نطاق العمل يسجل TrackingAlert
    """
    try:
        from attendance.models import TrackingAlert
        from django.utils import timezone as tz
        from datetime import timedelta
        from decimal import Decimal

        now = tz.now()
        today = now.date()
        policy = _get_company_policy(employee.company)
        branch = employee.branch

        alert_minutes = 15
        if policy and hasattr(policy, "stealth_tracking_alert_after_minutes"):
            try:
                alert_minutes = int(policy.stealth_tracking_alert_after_minutes or 15)
            except Exception:
                alert_minutes = 15

        is_outside = False
        distance = 0

        if branch and branch.latitude and branch.longitude:
            distance = round(calculate_distance(
                lat, lng,
                float(branch.latitude),
                float(branch.longitude)
            ))
            radius = int(getattr(branch, "check_in_radius", 100) or 100)
            tolerance = int(getattr(policy, "distance_tolerance_meters", 0) or 0) if policy else 0
            is_outside = distance > (radius + tolerance)

        if not is_outside:
            # لو رجع داخل النطاق — نقفل الـ alert المفتوح لو موجود
            open_alert = TrackingAlert.objects.filter(
                company=employee.company,
                employee=employee,
                date=today,
                status="open"
            ).first()
            if open_alert:
                open_alert.status = "resolved"
                open_alert.save(update_fields=["status"])
            return

        # لو خارج النطاق
        open_alert = TrackingAlert.objects.filter(
            company=employee.company,
            employee=employee,
            date=today,
            status="open"
        ).first()

        if not open_alert:
            open_alert = TrackingAlert.objects.create(
                company=employee.company,
                employee=employee,
                date=today,
                started_at=now,
                last_seen_at=now,
                minutes_outside=0,
                last_latitude=Decimal(str(lat)),
                last_longitude=Decimal(str(lng)),
                last_address=address or "",
                status="open",
            )
        else:
            diff = (now - open_alert.started_at).total_seconds() / 60
            open_alert.minutes_outside = int(diff)
            open_alert.last_seen_at = now
            open_alert.last_latitude = Decimal(str(lat))
            open_alert.last_longitude = Decimal(str(lng))
            if address:
                open_alert.last_address = address
            open_alert.save()

        # هل المفروض نبعت تنبيه؟
        if (
            open_alert.minutes_outside >= alert_minutes
            and not (open_alert.notified_manager or open_alert.notified_hr or open_alert.notified_company_admin)
        ):
            _send_stealth_alert_notifications(employee, open_alert, policy)

    except Exception:
        pass


def _send_stealth_alert_notifications(employee, alert, policy):
    """
    بعت تنبيهات لـ المدير / HR / صاحب الشركة
    """
    try:
        from accounts.models import EmployeeNotification, User
        from employees.models import Employee

        title = f"تنبيه تتبع: {employee.full_name_ar}"
        message = (
            f"الموظف {employee.full_name_ar} ({employee.employee_code}) "
            f"خارج نطاق العمل منذ {alert.minutes_outside} دقيقة.\n"
            f"آخر موقع: {alert.last_address or 'غير محدد'}\n"
            f"تاريخ/وقت: {alert.started_at.strftime('%d/%m/%Y %H:%M')}"
        )

        notified = []

        # المدير المباشر
        if policy and getattr(policy, "stealth_tracking_notify_manager", True):
            manager_emp = getattr(employee, "direct_manager", None)
            if manager_emp and getattr(manager_emp, "user", None):
                _create_mgmt_notification(
                    user=manager_emp.user,
                    title=title,
                    message=message
                )
                alert.notified_manager = True
                notified.append("مدير")

        # HR
        if policy and getattr(policy, "stealth_tracking_notify_hr", False):
            hr_users = User.objects.filter(
                company=employee.company,
                role="hr_manager"
            )
            for u in hr_users:
                _create_mgmt_notification(user=u, title=title, message=message)
            alert.notified_hr = True
            notified.append("HR")

        # صاحب الشركة
        if policy and getattr(policy, "stealth_tracking_notify_company_admin", False):
            admin_users = User.objects.filter(
                company=employee.company,
                role__in=["company_admin", "super_admin"]
            )
            for u in admin_users:
                _create_mgmt_notification(user=u, title=title, message=message)
            alert.notified_company_admin = True
            notified.append("صاحب الشركة")

        if notified:
            alert.save(update_fields=["notified_manager", "notified_hr", "notified_company_admin"])

    except Exception:
        pass


def _create_mgmt_notification(user, title, message):
    """إنشاء إشعار لمستخدم إداري"""
    try:
        from employees.models import Employee
        from accounts.models import EmployeeNotification

        mgr_emp = Employee.all_objects.filter(user=user).first()
        if mgr_emp:
            EmployeeNotification.objects.create(
                employee=mgr_emp,
                title=title,
                message=message,
                notification_type="general_notice",
                severity="danger",
                is_read=False,
            )
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# Stealth Tracking API — بتستقبل الموقع الصامت
# ════════════════════════════════════════════════════════════
@login_required
def api_stealth_location(request):
    """
    API endpoint يستقبل الموقع بصمت أثناء ساعات العمل
    الـ JS بتبعته في الخلفية بدون ما الموظف يعرف
    بس لو stealth_tracking مفعّل للموظف
    """
    import json
    from django.http import JsonResponse
    from employees.models import Employee
    from decimal import Decimal

    if request.method != "POST":
        return JsonResponse({"ok": True})

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": True})

    lat = body.get("lat") or body.get("latitude")
    lng = body.get("lng") or body.get("longitude")
    address = body.get("address", "")

    if not lat or not lng:
        return JsonResponse({"ok": True})

    try:
        lat = float(lat)
        lng = float(lng)
    except Exception:
        return JsonResponse({"ok": True})

    employee = Employee.all_objects.filter(user=request.user).first()
    if not employee:
        return JsonResponse({"ok": True})

    if not _is_stealth_tracking_active_for_employee(employee):
        return JsonResponse({"ok": True})

    # حفظ في LocationLog بصمت
    try:
        from attendance.models import LocationLog
        from django.utils import timezone as tz
        LocationLog.objects.create(
            company=employee.company,
            employee=employee,
            timestamp=tz.now(),
            latitude=Decimal(str(lat)),
            longitude=Decimal(str(lng)),
            accuracy=Decimal("15.0"),
            address=address or "",
        )
    except Exception:
        pass

    # فحص النطاق + TrackingAlert
    _check_and_create_tracking_alert(employee, lat, lng, address)

    return JsonResponse({"ok": True})
