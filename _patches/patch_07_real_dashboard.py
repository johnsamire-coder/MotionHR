"""
============================================================
Patch 07: Dashboard حقيقي
============================================================
- الأرقام الحقيقية
- رسوم بيانية (Chart.js)
- آخر النشاطات
- خريطة مصغرة
- التنبيهات المهمة
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. View الجديد للـ Dashboard
# ═══════════════════════════════════════════════════════════

NEW_DASHBOARD_VIEW = '''from django.shortcuts import render
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
'''


# ═══════════════════════════════════════════════════════════
# 2. Template الجديد للـ Dashboard
# ═══════════════════════════════════════════════════════════

NEW_DASHBOARD_TEMPLATE = '''{% extends 'base/dashboard_base.html' %}

{% block title %}لوحة التحكم{% endblock %}

{% block page_title %}لوحة التحكم{% endblock %}
{% block page_subtitle %}نظرة عامة على النظام{% endblock %}

{% block dashboard_content %}

<!-- Welcome Section -->
<div class="card border-0 shadow-sm mb-4" 
     style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%);">
    <div class="card-body p-4 text-white">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h3 class="fw-bold mb-2">
                    أهلاً بك، {{ user.get_full_name|default:user.username }} 👋
                </h3>
                <p class="mb-0 opacity-75">
                    {% now "l، d F Y" %} - نتمنى لك يوماً مثمراً
                </p>
            </div>
            <div class="col-md-4 text-md-end mt-3 mt-md-0">
                <div class="d-inline-flex align-items-center bg-white bg-opacity-10 rounded-3 px-3 py-2">
                    <i class="bi bi-clock ms-2"></i>
                    <span id="currentTime" class="fw-semibold"></span>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Alerts -->
{% if alerts %}
<div class="row g-2 mb-4">
    {% for alert in alerts %}
    <div class="col-md-4">
        <a href="{{ alert.link }}" class="text-decoration-none">
            <div class="alert alert-{{ alert.type }} mb-0 d-flex align-items-center gap-2">
                <i class="{{ alert.icon }} fs-5"></i>
                <div class="flex-grow-1">{{ alert.title }}</div>
                <i class="bi bi-arrow-left"></i>
            </div>
        </a>
    </div>
    {% endfor %}
</div>
{% endif %}

<!-- Stats Cards -->
<div class="row g-3 mb-4">
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">إجمالي الموظفين</p>
                        <h3 class="fw-bold mb-0">{{ total_employees }}</h3>
                        <small class="text-muted">
                            <i class="bi bi-building"></i>
                            {{ total_branches }} فرع، {{ total_departments }} إدارة
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(6, 182, 212, 0.1);">
                        <i class="bi bi-people-fill text-primary fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">الحاضرون اليوم</p>
                        <h3 class="fw-bold mb-0 text-success">{{ present_today }}</h3>
                        <small class="text-muted">
                            نسبة الحضور: {{ attendance_rate }}%
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(16, 185, 129, 0.1);">
                        <i class="bi bi-check-circle-fill text-success fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">ميدانيون نشطون</p>
                        <h3 class="fw-bold mb-0 text-info">{{ active_field_workers }}</h3>
                        <small class="text-info">
                            <i class="bi bi-broadcast"></i>
                            من {{ field_employees_count }} ميداني
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(59, 130, 246, 0.1);">
                        <i class="bi bi-geo-alt-fill text-info fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">زيارات اليوم</p>
                        <h3 class="fw-bold mb-0 text-warning">{{ today_visits }}</h3>
                        <small class="text-muted">
                            <i class="bi bi-pin-map"></i>
                            زيارات ميدانية
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(245, 158, 11, 0.1);">
                        <i class="bi bi-pin-map-fill text-warning fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
</div>

<!-- Quick Actions -->
<div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
        <h6 class="fw-bold mb-3">
            <i class="bi bi-lightning-charge-fill text-warning"></i>
            إجراءات سريعة
        </h6>
        
        <div class="row g-3">
            <div class="col-md-3 col-6">
                <a href="/employees/add/" class="text-decoration-none">
                    <div class="border rounded-3 p-3 text-center h-100 hover-lift">
                        <i class="bi bi-person-plus-fill text-primary" style="font-size: 2rem;"></i>
                        <p class="mb-0 mt-2 fw-semibold text-dark">إضافة موظف</p>
                    </div>
                </a>
            </div>
            
            <div class="col-md-3 col-6">
                <a href="/attendance/check-in/" class="text-decoration-none">
                    <div class="border rounded-3 p-3 text-center h-100 hover-lift">
                        <i class="bi bi-clock-fill text-success" style="font-size: 2rem;"></i>
                        <p class="mb-0 mt-2 fw-semibold text-dark">تسجيل حضور</p>
                    </div>
                </a>
            </div>
            
            <div class="col-md-3 col-6">
                <a href="/attendance/monitor/" class="text-decoration-none">
                    <div class="border rounded-3 p-3 text-center h-100 hover-lift">
                        <i class="bi bi-broadcast text-info" style="font-size: 2rem;"></i>
                        <p class="mb-0 mt-2 fw-semibold text-dark">متابعة الميدانيين</p>
                    </div>
                </a>
            </div>
            
            <div class="col-md-3 col-6">
                <a href="/attendance/live-map/" class="text-decoration-none">
                    <div class="border rounded-3 p-3 text-center h-100 hover-lift">
                        <i class="bi bi-map-fill text-warning" style="font-size: 2rem;"></i>
                        <p class="mb-0 mt-2 fw-semibold text-dark">الخريطة الحية</p>
                    </div>
                </a>
            </div>
        </div>
        
    </div>
</div>

<!-- Charts Row -->
<div class="row g-3 mb-4">
    
    <!-- Week Attendance Chart -->
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-graph-up text-primary"></i>
                    الحضور خلال الأسبوع
                </h6>
                <canvas id="weekChart" style="max-height: 300px;"></canvas>
            </div>
        </div>
    </div>
    
    <!-- Status Chart -->
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-pie-chart-fill text-info"></i>
                    حالة الحضور اليوم
                </h6>
                <canvas id="statusChart" style="max-height: 300px;"></canvas>
            </div>
        </div>
    </div>
    
</div>

<!-- Departments + Recent Activities -->
<div class="row g-3">
    
    <!-- Departments Chart -->
    <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-diagram-3-fill text-warning"></i>
                    توزيع الموظفين على الإدارات
                </h6>
                {% if dept_labels %}
                <canvas id="deptChart" style="max-height: 300px;"></canvas>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
                    <p class="text-muted mt-2">لا توجد إدارات</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Recent Activities -->
    <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="fw-bold mb-0">
                        <i class="bi bi-activity text-success"></i>
                        آخر النشاطات
                    </h6>
                    <a href="/attendance/" class="text-decoration-none small">عرض الكل</a>
                </div>
                
                {% if recent_activities %}
                <div style="max-height: 300px; overflow-y: auto;">
                    {% for activity in recent_activities %}
                    <div class="d-flex align-items-start gap-2 mb-3 pb-3 border-bottom">
                        <div class="rounded-circle d-flex align-items-center justify-content-center bg-{{ activity.color }} bg-opacity-10 flex-shrink-0" 
                             style="width: 40px; height: 40px;">
                            <i class="{{ activity.icon }} text-{{ activity.color }}"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="fw-semibold small">{{ activity.employee.full_name_ar }}</div>
                            <div class="text-muted small">{{ activity.message }}</div>
                            <small class="text-muted">
                                <i class="bi bi-clock"></i>
                                {{ activity.time|date:"H:i" }}
                            </small>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
                    <p class="text-muted mt-2">لا يوجد نشاط حديث</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
</div>

<!-- Field Workers Map -->
{% if field_workers_map %}
<div class="row g-3 mt-1">
    <div class="col-12">
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="fw-bold mb-0">
                        <i class="bi bi-geo-alt-fill text-danger"></i>
                        الموظفون الميدانيون
                        <span class="badge bg-danger ms-2">
                            <i class="bi bi-circle-fill" style="font-size: 0.5rem;"></i>
                            Live
                        </span>
                    </h6>
                    <a href="/attendance/live-map/" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-arrows-fullscreen"></i>
                        الخريطة الكاملة
                    </a>
                </div>
                <div id="miniMap" style="height: 400px; border-radius: 10px;"></div>
            </div>
        </div>
    </div>
</div>
{% endif %}

{% endblock %}

{% block dashboard_css %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
    .hover-lift {
        transition: all 0.2s;
        cursor: pointer;
    }
    .hover-lift:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #06B6D4 !important;
    }
</style>
{% endblock %}

{% block dashboard_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
    // Time
    function updateTime() {
        const now = new Date();
        const time = now.toLocaleTimeString('ar-EG', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        document.getElementById('currentTime').textContent = time;
    }
    updateTime();
    setInterval(updateTime, 60000);
    
    // Chart.js defaults
    Chart.defaults.font.family = 'Cairo';
    Chart.defaults.font.size = 13;
    
    // Week Chart
    const weekCtx = document.getElementById('weekChart');
    if (weekCtx) {
        new Chart(weekCtx, {
            type: 'line',
            data: {
                labels: {{ week_chart_labels|safe }},
                datasets: [{
                    label: 'عدد الحاضرين',
                    data: {{ week_chart_data|safe }},
                    borderColor: '#06B6D4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#06B6D4',
                    pointRadius: 5,
                    pointHoverRadius: 7,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Status Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: {{ status_chart.labels|safe }},
                datasets: [{
                    data: {{ status_chart.data|safe }},
                    backgroundColor: {{ status_chart.colors|safe }},
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 15 }
                    }
                },
                cutout: '65%'
            }
        });
    }
    
    // Departments Chart
    const deptCtx = document.getElementById('deptChart');
    if (deptCtx) {
        new Chart(deptCtx, {
            type: 'bar',
            data: {
                labels: {{ dept_labels|safe }},
                datasets: [{
                    label: 'عدد الموظفين',
                    data: {{ dept_counts|safe }},
                    backgroundColor: [
                        '#06B6D4', '#3B82F6', '#8B5CF6', 
                        '#10B981', '#F59E0B', '#EF4444'
                    ],
                    borderRadius: 8,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Mini Map
    {% if field_workers_map %}
    const miniMap = L.map('miniMap').setView([30.0444, 31.2357], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(miniMap);
    
    const workers = {{ field_workers_map|safe }};
    const bounds = [];
    
    workers.forEach(w => {
        L.marker([w.lat, w.lng])
            .addTo(miniMap)
            .bindPopup(`<strong>${w.name}</strong><br><small>آخر تحديث: ${w.time}</small>`);
        bounds.push([w.lat, w.lng]);
    });
    
    if (bounds.length > 0) {
        miniMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
    {% endif %}
</script>
{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def update_dashboard_view():
    """تحديث view الـ dashboard"""
    views_path = BASE_DIR / 'accounts' / 'views.py'
    
    if not views_path.exists():
        return False, "ملف accounts/views.py مش موجود"
    
    # نستبدل الملف بالكامل بالكود الجديد
    views_path.write_text(NEW_DASHBOARD_VIEW, encoding='utf-8')
    
    return True, "تم تحديث dashboard view"


def update_dashboard_template():
    """تحديث template الـ dashboard"""
    template_path = BASE_DIR / 'templates' / 'dashboard' / 'index.html'
    
    if not template_path.exists():
        return False, "ملف dashboard/index.html مش موجود"
    
    template_path.write_text(NEW_DASHBOARD_TEMPLATE, encoding='utf-8')
    
    return True, "تم تحديث dashboard template"


def main():
    print("=" * 60)
    print("🚀 Patch 07: Dashboard حقيقي")
    print("=" * 60)
    print()
    
    updates = [
        ('accounts/views.py', update_dashboard_view),
        ('templates/dashboard/index.html', update_dashboard_template),
    ]
    
    for name, func in updates:
        try:
            success, message = func()
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("دلوقتي:")
    print("  1. شغل السيرفر: python manage.py runserver 0.0.0.0:8000")
    print("  2. روح للـ Dashboard: http://127.0.0.1:8000/dashboard/")
    print("  3. هتشوف:")
    print("     ✅ أرقام حقيقية")
    print("     ✅ 3 رسوم بيانية")
    print("     ✅ آخر النشاطات")
    print("     ✅ خريطة مصغرة للميدانيين")
    print("     ✅ تنبيهات مهمة")
    print()


if __name__ == '__main__':
    main()