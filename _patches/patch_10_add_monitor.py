"""
============================================================
Patch 10: إضافة صفحة متابعة الميدانيين بالكامل
============================================================
- إضافة view: field_employees_monitor
- إضافة view: api_monitor_data
- إضافة template: monitor.html
- إضافة template: tracking_detail.html
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. Views الجديدة
# ═══════════════════════════════════════════════════════════

MONITOR_VIEWS = '''


@login_required
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
'''


# ═══════════════════════════════════════════════════════════
# 2. Template: monitor.html
# ═══════════════════════════════════════════════════════════

MONITOR_TEMPLATE = '''{% extends 'base/dashboard_base.html' %}

{% block title %}متابعة الموظفين الميدانيين{% endblock %}

{% block page_title %}متابعة الميدانيين 🎯{% endblock %}
{% block page_subtitle %}تابع حركة موظفيك في الوقت الحقيقي{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للرئيسية
    </a>
</div>

<!-- Alert Bar for Notifications -->
<div id="alertBar" class="alert alert-info alert-dismissible fade show" style="display: none;">
    <div class="d-flex align-items-center gap-2">
        <i class="bi bi-bell-fill"></i>
        <span id="alertText"></span>
    </div>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>

<!-- Stats -->
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted mb-1 small">إجمالي الميدانيين</p>
                        <h3 class="fw-bold mb-0" id="totalCount">{{ total_count }}</h3>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(6, 182, 212, 0.1);">
                        <i class="bi bi-people-fill text-primary fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted mb-1 small">متصل الآن</p>
                        <h3 class="fw-bold mb-0 text-success" id="onlineCount">{{ online_count }}</h3>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(16, 185, 129, 0.1);">
                        <i class="bi bi-broadcast text-success fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted mb-1 small">في حركة</p>
                        <h3 class="fw-bold mb-0 text-info" id="movingCount">{{ moving_count }}</h3>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(59, 130, 246, 0.1);">
                        <i class="bi bi-truck text-info fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted mb-1 small">غير متصل</p>
                        <h3 class="fw-bold mb-0 text-secondary" id="offlineCount">{{ offline_count }}</h3>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(148, 163, 184, 0.1);">
                        <i class="bi bi-broadcast-pin text-secondary fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Controls -->
<div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-arrow-repeat text-primary"></i>
                    التحديث التلقائي
                </h6>
                <small class="text-muted">آخر تحديث: <span id="lastUpdate">--</span></small>
            </div>
            <div class="d-flex align-items-center gap-2">
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="autoRefresh" checked>
                    <label class="form-check-label" for="autoRefresh">
                        تحديث كل 30 ثانية
                    </label>
                </div>
                <button class="btn btn-sm btn-primary" onclick="refreshData()">
                    <i class="bi bi-arrow-clockwise"></i>
                    تحديث الآن
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Employees Grid -->
<div class="row g-3" id="employeesGrid">
    {% for data in employees_data %}
    <div class="col-md-6 col-lg-4">
        <div class="card border-0 shadow-sm h-100 employee-monitor-card">
            <div class="card-body">
                
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="d-flex align-items-center gap-2">
                        {% if data.employee.photo %}
                        <img src="{{ data.employee.photo.url }}" 
                             class="rounded-circle" 
                             style="width: 50px; height: 50px; object-fit: cover;">
                        {% else %}
                        <div class="rounded-circle d-flex align-items-center justify-content-center text-white fw-bold" 
                             style="width: 50px; height: 50px; background: linear-gradient(135deg, #06B6D4, #3B82F6);">
                            {{ data.employee.first_name_ar|first }}
                        </div>
                        {% endif %}
                        <div>
                            <div class="fw-bold">{{ data.employee.full_name_ar }}</div>
                            <small class="text-muted">{{ data.employee.job_title.name_ar }}</small>
                        </div>
                    </div>
                    
                    <div>
                        {% if data.connection_status == 'online' %}
                            <span class="badge bg-success">
                                <span class="pulse-dot-small"></span>
                                متصل
                            </span>
                        {% elif data.connection_status == 'idle' %}
                            <span class="badge bg-warning">
                                <i class="bi bi-hourglass-split"></i>
                                خامل
                            </span>
                        {% else %}
                            <span class="badge bg-secondary">
                                <i class="bi bi-broadcast-pin"></i>
                                غير متصل
                            </span>
                        {% endif %}
                    </div>
                </div>
                
                {% if data.is_moving %}
                <div class="alert alert-info py-2 mb-3">
                    <i class="bi bi-truck"></i>
                    <strong>في حركة الآن</strong>
                </div>
                {% endif %}
                
                {% if data.last_location %}
                <div class="mb-3">
                    <small class="text-muted d-block mb-1">
                        <i class="bi bi-geo-alt-fill text-danger"></i>
                        آخر موقع
                    </small>
                    <div class="small">
                        {{ data.last_location.address|default:"جاري تحديد العنوان..."|truncatechars:80 }}
                    </div>
                </div>
                {% else %}
                <div class="mb-3 text-center py-3 bg-light rounded-3">
                    <i class="bi bi-geo-alt-slash text-muted"></i>
                    <small class="text-muted d-block">لم يبدأ التتبع بعد</small>
                </div>
                {% endif %}
                
                <div class="row g-2 mb-3">
                    <div class="col-4 text-center">
                        <div class="p-2 bg-light rounded">
                            <div class="fw-bold text-primary">{{ data.today_points }}</div>
                            <small class="text-muted">نقاط اليوم</small>
                        </div>
                    </div>
                    <div class="col-4 text-center">
                        <div class="p-2 bg-light rounded">
                            <div class="fw-bold text-info">{{ data.total_distance_km }}</div>
                            <small class="text-muted">كم اليوم</small>
                        </div>
                    </div>
                    <div class="col-4 text-center">
                        <div class="p-2 bg-light rounded">
                            {% if data.minutes_since_update is not None %}
                                <div class="fw-bold text-success">{{ data.minutes_since_update }}</div>
                                <small class="text-muted">دقيقة</small>
                            {% else %}
                                <div class="fw-bold text-muted">-</div>
                                <small class="text-muted">لا يوجد</small>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <div class="d-flex gap-2">
                    <a href="tel:{{ data.employee.phone }}" class="btn btn-sm btn-outline-success flex-grow-1">
                        <i class="bi bi-telephone-fill"></i>
                        اتصال
                    </a>
                    <a href="{% url 'attendance:tracking_detail' data.employee.id %}" 
                       class="btn btn-sm btn-primary flex-grow-1">
                        <i class="bi bi-map"></i>
                        المسار
                    </a>
                </div>
                
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-12">
        <div class="card border-0 shadow-sm">
            <div class="card-body text-center py-5">
                <i class="bi bi-people text-muted" style="font-size: 4rem;"></i>
                <h5 class="mt-3 fw-bold">لا يوجد موظفون ميدانيون</h5>
                <p class="text-muted">
                    فعّل خيار "موظف ميداني" في بيانات الموظف لتفعيل التتبع
                </p>
                <a href="{% url 'employees:list' %}" class="btn btn-primary">
                    <i class="bi bi-people-fill"></i>
                    إدارة الموظفين
                </a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% endblock %}

{% block dashboard_css %}
<style>
    .pulse-dot-small {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        display: inline-block;
        animation: pulseSmall 1.5s infinite;
    }
    
    @keyframes pulseSmall {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    
    .employee-monitor-card {
        transition: all 0.3s;
    }
    
    .employee-monitor-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
    }
</style>
{% endblock %}

{% block dashboard_js %}
<script>
    let autoRefreshInterval = null;
    let previousData = {};
    
    async function refreshData() {
        try {
            const response = await fetch('{% url "attendance:api_monitor" %}');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('totalCount').textContent = data.stats.total;
                document.getElementById('onlineCount').textContent = data.stats.online;
                document.getElementById('movingCount').textContent = data.stats.moving;
                document.getElementById('offlineCount').textContent = data.stats.offline;
                document.getElementById('lastUpdate').textContent = data.last_update;
                
                data.employees.forEach(emp => {
                    const prev = previousData[emp.id];
                    
                    if (prev && emp.distance_moved > 100 && !prev.is_moving && emp.is_moving) {
                        showAlert(`🚗 ${emp.name} بدأ يتحرك (${emp.distance_moved} متر)`);
                    }
                    
                    if (prev && prev.is_moving && !emp.is_moving) {
                        showAlert(`⏸️ ${emp.name} توقف عن الحركة`);
                    }
                    
                    if (prev && prev.connection_status === 'offline' && emp.connection_status === 'online') {
                        showAlert(`✅ ${emp.name} أصبح متصل`);
                    }
                });
                
                previousData = {};
                data.employees.forEach(emp => {
                    previousData[emp.id] = emp;
                });
            }
        } catch (error) {
            console.error('Error refreshing:', error);
        }
    }
    
    function showAlert(message) {
        const alertBar = document.getElementById('alertBar');
        const alertText = document.getElementById('alertText');
        alertText.textContent = message;
        alertBar.style.display = 'block';
        
        setTimeout(() => {
            alertBar.style.display = 'none';
        }, 5000);
        
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('MotionHR', { body: message });
        }
    }
    
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    document.getElementById('autoRefresh').addEventListener('change', function() {
        if (this.checked) {
            autoRefreshInterval = setInterval(refreshData, 30000);
        } else {
            clearInterval(autoRefreshInterval);
        }
    });
    
    autoRefreshInterval = setInterval(refreshData, 30000);
    
    {% for data in employees_data %}
    previousData[{{ data.employee.id }}] = {
        is_moving: {% if data.is_moving %}true{% else %}false{% endif %},
        connection_status: '{{ data.connection_status }}',
        distance_moved: 0
    };
    {% endfor %}
</script>
{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 3. Template: tracking_detail.html
# ═══════════════════════════════════════════════════════════

TRACKING_DETAIL_TEMPLATE = '''{% extends 'base/dashboard_base.html' %}

{% block title %}مسار {{ employee.full_name_ar }}{% endblock %}

{% block page_title %}مسار الموظف 🗺️{% endblock %}
{% block page_subtitle %}{{ employee.full_name_ar }}{% endblock %}

{% block dashboard_content %}

<div class="mb-3 d-flex gap-2 flex-wrap">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-primary">
        <i class="bi bi-house-fill"></i>
        الرئيسية
    </a>
    <a href="{% url 'attendance:monitor' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للمتابعة
    </a>
</div>

<div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
        <div class="row align-items-center">
            <div class="col-md-6">
                <div class="d-flex align-items-center gap-3">
                    {% if employee.photo %}
                    <img src="{{ employee.photo.url }}" 
                         class="rounded-circle" 
                         style="width: 60px; height: 60px; object-fit: cover;">
                    {% else %}
                    <div class="rounded-circle d-flex align-items-center justify-content-center text-white fw-bold" 
                         style="width: 60px; height: 60px; background: linear-gradient(135deg, #06B6D4, #3B82F6); font-size: 1.5rem;">
                        {{ employee.first_name_ar|first }}
                    </div>
                    {% endif %}
                    <div>
                        <h5 class="mb-0 fw-bold">{{ employee.full_name_ar }}</h5>
                        <small class="text-muted">
                            {{ employee.job_title.name_ar }} • {{ employee.employee_code }}
                        </small>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <form method="get" class="d-flex gap-2 justify-content-md-end">
                    <input type="date" 
                           name="date" 
                           class="form-control" 
                           value="{{ selected_date|date:'Y-m-d' }}"
                           style="max-width: 200px;">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-calendar-check"></i>
                        عرض
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card border-0 shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-geo-alt-fill text-primary fs-1"></i>
                <h3 class="fw-bold mb-0">{{ total_points }}</h3>
                <small class="text-muted">نقطة مسجلة</small>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card border-0 shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-calendar-day text-info fs-1"></i>
                <h5 class="fw-bold mb-0">{{ selected_date|date:"Y-m-d" }}</h5>
                <small class="text-muted">التاريخ</small>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card border-0 shadow-sm">
            <div class="card-body text-center">
                <i class="bi bi-clock text-success fs-1"></i>
                <h5 class="fw-bold mb-0">
                    {% if locations %}
                        {{ locations.first.timestamp|time:"H:i" }} - {{ locations.last.timestamp|time:"H:i" }}
                    {% else %}
                        --
                    {% endif %}
                </h5>
                <small class="text-muted">فترة النشاط</small>
            </div>
        </div>
    </div>
</div>

<div class="row g-3">
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-map-fill text-danger"></i>
                    الخريطة
                </h6>
            </div>
            <div class="card-body p-0">
                {% if locations %}
                <div id="map" style="height: 500px;"></div>
                {% else %}
                <div class="text-center py-5">
                    <i class="bi bi-map text-muted" style="font-size: 4rem;"></i>
                    <p class="text-muted mt-3">لا توجد بيانات تتبع لهذا اليوم</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-list-ul text-primary"></i>
                    سجل النقاط
                </h6>
            </div>
            <div class="card-body p-0" style="max-height: 500px; overflow-y: auto;">
                {% if locations %}
                <ul class="list-group list-group-flush">
                    {% for loc in locations %}
                    <li class="list-group-item">
                        <div class="d-flex align-items-start gap-2">
                            <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center flex-shrink-0" 
                                 style="width: 30px; height: 30px; font-size: 0.75rem;">
                                {{ forloop.counter }}
                            </div>
                            <div class="flex-grow-1 small">
                                <div class="fw-semibold">{{ loc.timestamp|time:"H:i:s" }}</div>
                                <div class="text-muted">{{ loc.address|default:"جاري تحديد العنوان..."|truncatechars:60 }}</div>
                            </div>
                        </div>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-inbox text-muted fs-1"></i>
                    <p class="text-muted mt-2 small">لا توجد نقاط</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block dashboard_css %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
{% endblock %}

{% block dashboard_js %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
    {% if locations %}
    const map = L.map('map').setView([{{ locations.first.latitude }}, {{ locations.first.longitude }}], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    const points = [];
    
    {% for loc in locations %}
    points.push([{{ loc.latitude }}, {{ loc.longitude }}]);
    
    L.circleMarker([{{ loc.latitude }}, {{ loc.longitude }}], {
        radius: 6,
        fillColor: '#06B6D4',
        color: 'white',
        weight: 2,
        fillOpacity: 0.8
    }).addTo(map).bindPopup(`
        <strong>نقطة {{ forloop.counter }}</strong><br>
        الوقت: {{ loc.timestamp|time:"H:i:s" }}<br>
        {% if loc.address %}{{ loc.address|truncatechars:80 }}{% endif %}
    `);
    {% endfor %}
    
    if (points.length > 1) {
        const polyline = L.polyline(points, { 
            color: '#06B6D4', 
            weight: 4,
            opacity: 0.7
        }).addTo(map);
        
        map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    }
    {% endif %}
</script>
{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def add_views():
    """إضافة views جديدة"""
    views_path = BASE_DIR / 'attendance' / 'views.py'
    
    if not views_path.exists():
        return False, "ملف views.py مش موجود"
    
    content = views_path.read_text(encoding='utf-8')
    
    if 'def field_employees_monitor' in content:
        return True, "الـ views موجودة بالفعل"
    
    with views_path.open('a', encoding='utf-8') as f:
        f.write(MONITOR_VIEWS)
    
    return True, "تم إضافة views"


def create_file(relative_path, content):
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')


def main():
    print("=" * 60)
    print("🔧 Patch 10: إضافة صفحة متابعة الميدانيين")
    print("=" * 60)
    print()
    
    # Views
    print("📝 إضافة Views...")
    print("-" * 60)
    try:
        success, message = add_views()
        icon = "✅" if success else "❌"
        print(f"  {icon} {message}")
    except Exception as e:
        print(f"  ❌ {e}")
    
    # Templates
    print()
    print("📄 إنشاء Templates...")
    print("-" * 60)
    
    templates = [
        ('templates/attendance/monitor.html', MONITOR_TEMPLATE),
        ('templates/attendance/tracking_detail.html', TRACKING_DETAIL_TEMPLATE),
    ]
    
    for path, content in templates:
        try:
            create_file(path, content)
            print(f"  ✅ {path}")
        except Exception as e:
            print(f"  ❌ {path}: {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("دلوقتي:")
    print("  1. أعد تشغيل السيرفر")
    print("  2. روح: http://127.0.0.1:8000/attendance/monitor/")
    print("  3. روح: http://127.0.0.1:8000/attendance/map/")
    print()


if __name__ == '__main__':
    main()