from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Count, Q


@login_required
def dashboard(request):
    """الصفحة الرئيسية مع إحصائيات حقيقية"""
    from employees.models import Employee
    from attendance.models import Attendance, LocationLog, LocationCheckIn
    from companies.models import Company, Branch, Department
    
    today = date.today()
    now = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # ═══════════════════════════════
    # الإحصائيات الأساسية
    # ═══════════════════════════════
    total_employees = Employee.objects.filter(status='active').count()
    total_branches = Branch.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    field_employees_count = Employee.objects.filter(is_field_worker=True, status='active').count()
    
    # ═══════════════════════════════
    # إحصائيات اليوم
    # ═══════════════════════════════
    today_attendances = Attendance.objects.filter(date=today)
    present_today = today_attendances.filter(status='present').count()
    late_today = today_attendances.filter(status='late').count()
    absent_today = max(0, total_employees - today_attendances.count())
    
    # نسبة الحضور
    attendance_rate = 0
    if total_employees > 0:
        attendance_rate = round((today_attendances.count() / total_employees) * 100, 1)
    
    # ═══════════════════════════════
    # الميدانيين النشطين الآن
    # ═══════════════════════════════
    fifteen_min_ago = now - timedelta(minutes=15)
    active_field_workers = LocationLog.objects.filter(
        timestamp__gte=fifteen_min_ago,
        employee__is_field_worker=True,
        employee__status='active'
    ).values('employee').distinct().count()
    
    # ═══════════════════════════════
    # الزيارات اليوم
    # ═══════════════════════════════
    today_visits = LocationCheckIn.objects.filter(
        arrival_time__date=today
    ).count()
    
    # ═══════════════════════════════
    # آخر النشاطات (10 نشاطات)
    # ═══════════════════════════════
    recent_activities = []
    
    # آخر تسجيلات حضور
    recent_checkins = Attendance.objects.filter(
        check_in_time__isnull=False
    ).select_related('employee').order_by('-check_in_time')[:5]
    
    for att in recent_checkins:
        recent_activities.append({
            'type': 'check_in',
            'icon': 'bi-box-arrow-in-right',
            'color': 'success',
            'employee': att.employee,
            'time': att.check_in_time,
            'message': 'سجل حضوره',
        })
    
    # آخر الزيارات
    recent_visits = LocationCheckIn.objects.select_related('employee').order_by('-arrival_time')[:5]
    for visit in recent_visits:
        recent_activities.append({
            'type': 'visit',
            'icon': 'bi-pin-map-fill',
            'color': 'info',
            'employee': visit.employee,
            'time': visit.arrival_time,
            'message': f'زار {visit.location_name}',
        })
    
    # ترتيب حسب الوقت
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:10]
    
    # ═══════════════════════════════
    # بيانات الرسم البياني - حضور الأسبوع
    # ═══════════════════════════════
    week_chart_labels = []
    week_chart_data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_name = day.strftime('%A')
        # ترجمة أيام الأسبوع
        day_names_ar = {
            'Saturday': 'السبت',
            'Sunday': 'الأحد',
            'Monday': 'الاثنين',
            'Tuesday': 'الثلاثاء',
            'Wednesday': 'الأربعاء',
            'Thursday': 'الخميس',
            'Friday': 'الجمعة',
        }
        week_chart_labels.append(day_names_ar.get(day_name, day_name))
        count = Attendance.objects.filter(date=day, status__in=['present', 'late']).count()
        week_chart_data.append(count)
    
    # ═══════════════════════════════
    # توزيع الموظفين على الأقسام
    # ═══════════════════════════════
    dept_data = Department.objects.annotate(
        emp_count=Count('employees', filter=Q(employees__status='active'))
    ).values('name_ar', 'emp_count')[:6]
    
    dept_labels = [d['name_ar'] for d in dept_data]
    dept_counts = [d['emp_count'] for d in dept_data]
    
    # ═══════════════════════════════
    # توزيع حالات الحضور اليوم
    # ═══════════════════════════════
    status_chart = {
        'labels': ['حاضر', 'متأخر', 'غائب'],
        'data': [present_today, late_today, absent_today],
        'colors': ['#10B981', '#F59E0B', '#EF4444']
    }
    
    # ═══════════════════════════════
    # التنبيهات
    # ═══════════════════════════════
    alerts = []
    
    # موظفين بدون حضور اليوم
    if absent_today > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'bi-exclamation-triangle-fill',
            'title': f'{absent_today} موظف لم يسجل حضور اليوم',
            'link': '/attendance/'
        })
    
    # عقود قربت تنتهي (خلال 30 يوم)
    from datetime import timedelta as td
    expiring_contracts = Employee.objects.filter(
        contract_end_date__isnull=False,
        contract_end_date__lte=today + td(days=30),
        contract_end_date__gte=today,
        status='active'
    ).count()
    
    if expiring_contracts > 0:
        alerts.append({
            'type': 'info',
            'icon': 'bi-file-earmark-text',
            'title': f'{expiring_contracts} عقد سينتهي خلال 30 يوم',
            'link': '/employees/'
        })
    
    # موظفين خارج نطاق الفرع
    outside_range = Attendance.objects.filter(
        date=today,
        check_in_within_range=False
    ).count()
    
    if outside_range > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'bi-geo-alt-fill',
            'title': f'{outside_range} موظف سجل حضور خارج نطاق الفرع',
            'link': '/attendance/'
        })
    
    # ═══════════════════════════════
    # الموظفين الميدانيين للخريطة
    # ═══════════════════════════════
    field_workers_map = []
    field_workers = Employee.objects.filter(
        is_field_worker=True,
        status='active'
    )[:10]
    
    for fw in field_workers:
        last_loc = LocationLog.objects.filter(employee=fw).order_by('-timestamp').first()
        if last_loc:
            field_workers_map.append({
                'name': fw.full_name_ar,
                'lat': float(last_loc.latitude),
                'lng': float(last_loc.longitude),
                'time': last_loc.timestamp.strftime('%H:%M'),
            })
    
    context = {
        # الأرقام
        'total_employees': total_employees,
        'total_branches': total_branches,
        'total_departments': total_departments,
        'field_employees_count': field_employees_count,
        'active_field_workers': active_field_workers,
        
        # اليوم
        'present_today': present_today,
        'late_today': late_today,
        'absent_today': absent_today,
        'attendance_rate': attendance_rate,
        'today_visits': today_visits,
        
        # النشاطات
        'recent_activities': recent_activities,
        
        # الرسوم البيانية
        'week_chart_labels': week_chart_labels,
        'week_chart_data': week_chart_data,
        'dept_labels': dept_labels,
        'dept_counts': dept_counts,
        'status_chart': status_chart,
        
        # التنبيهات
        'alerts': alerts,
        
        # الخريطة
        'field_workers_map': field_workers_map,
    }
    
    return render(request, 'dashboard/index.html', context)
