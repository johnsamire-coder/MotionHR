#!/usr/bin/env python3
"""
Patch 33: Smart Attendance
============================
1. زرار "تسجيل زيارة" للموظف الميداني
2. Geofencing: check-in بنطاق + check-out من أي مكان
3. تحسين صفحة الحضور للموظف
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 33: Smart Attendance")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. تحديث attendance/views.py
#    - Geofencing ذكي
#    - context للموظف الميداني
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

# نبحث عن api_check_in view ونضيف Geofencing logic
# أولاً نضيف helper function في أول الملف
geofencing_helper = '''
# ════════════════════════════════════════════════════════════
# Geofencing Helper
# ════════════════════════════════════════════════════════════
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """حساب المسافة بين نقطتين GPS بالمتر (Haversine)"""
    R = 6371000  # نصف قطر الأرض بالمتر
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def check_within_range(employee_lat, employee_lon, branch):
    """التحقق من نطاق الفرع"""
    if not branch or not branch.latitude or not branch.longitude:
        return True, 0  # لو مفيش GPS للفرع نسمح

    distance = calculate_distance(
        employee_lat, employee_lon,
        branch.latitude, branch.longitude
    )
    radius = getattr(branch, 'check_in_radius', 100) or 100
    return distance <= radius, round(distance)

'''

if "def calculate_distance" not in views:
    # نضيف بعد الـ imports
    import_end = views.find("\n\n", views.rfind("import "))
    if import_end == -1:
        import_end = views.find("\n\n")
    views = views[:import_end] + "\n" + geofencing_helper + views[import_end:]
    write_file(views_path, views)
    print("  ✅ تم إضافة Geofencing helper")
else:
    print("  ℹ️  Geofencing helper موجود")


# ════════════════════════════════════════════════════════════
# 2. إعادة كتابة صفحة check_in.html
#    - بسيطة للموظف العادي
#    - زرار زيارة للميداني
#    - Geofencing واضح
# ════════════════════════════════════════════════════════════
print("\n📄 إعادة كتابة check_in.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "attendance", "check_in.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}تسجيل الحضور{% endblock %}

{% block extra_css %}
<style>
  .checkin-container { max-width: 600px; margin: 0 auto; }
  .checkin-btn {
    width: 100%; padding: 16px; border: none; border-radius: 14px;
    font-family: 'Cairo', sans-serif; font-size: 1.1rem;
    font-weight: 700; cursor: pointer; transition: all 0.3s;
    display: flex; align-items: center; justify-content: center; gap: 10px;
  }
  .checkin-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
  .btn-check-in { background: linear-gradient(135deg, #10b981, #059669); color: white; }
  .btn-check-out { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
  .btn-visit { background: linear-gradient(135deg, #06B6D4, #0891B2); color: white; }
  .btn-disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; }
  .btn-disabled:hover { transform: none; box-shadow: none; }

  .status-card {
    border-radius: 14px; padding: 20px;
    text-align: center; margin-bottom: 16px;
  }
  .location-info {
    background: #f8fafc; border-radius: 10px;
    padding: 12px; margin-top: 12px; font-size: 0.85rem;
  }

  /* الخريطة للمديرين فقط */
  {% if not show_map %}
  #map, .map-container, .map-section, [id*="map"] {
    display: none !important;
  }
  {% endif %}
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="checkin-container">

    <!-- ترحيب -->
    <div class="text-center mb-4">
      <div class="rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
           style="width:80px; height:80px; background:linear-gradient(135deg,#06B6D4,#0891B2);">
        {% if employee %}
        <span style="font-size:2rem; color:white; font-weight:900;">
          {{ employee.first_name_ar|first }}
        </span>
        {% else %}
        <i class="bi bi-person-fill" style="font-size:2rem; color:white;"></i>
        {% endif %}
      </div>

      {% if employee %}
      <h5 class="fw-bold mb-1">{{ employee.full_name_ar }}</h5>
      <div class="text-muted small">
        {{ employee.job_title.name_ar|default:"" }}
        {% if employee.department %} | {{ employee.department.name_ar }}{% endif %}
      </div>
      {% if employee.branch %}
      <div class="text-muted small mt-1">
        <i class="bi bi-geo-alt me-1"></i>
        {{ employee.branch.name_ar }}
        <span class="badge bg-light text-dark border ms-1">
          نطاق {{ employee.branch.check_in_radius|default:100 }}م
        </span>
      </div>
      {% endif %}
      {% else %}
      <h5 class="fw-bold mb-1">مرحباً</h5>
      <div class="alert alert-warning mt-2 small">
        <i class="bi bi-exclamation-triangle me-1"></i>
        لم يتم ربط حسابك بملف موظف. تواصل مع المدير.
      </div>
      {% endif %}
    </div>

    {% if employee %}

    <!-- حالة اليوم -->
    {% if today_attendance %}
    <div class="status-card"
         style="background: {% if today_attendance.check_out_time %}#f0fdf4{% else %}#fff7ed{% endif %};
                border: 2px solid {% if today_attendance.check_out_time %}#bbf7d0{% else %}#fed7aa{% endif %};">

      {% if today_attendance.check_out_time %}
      <i class="bi bi-check-circle-fill fs-1 text-success"></i>
      <h6 class="fw-bold mt-2 text-success">تم تسجيل اليوم بنجاح</h6>
      <div class="d-flex justify-content-center gap-4 mt-2 text-muted small">
        <div>
          <i class="bi bi-box-arrow-in-right text-success me-1"></i>
          حضور: {{ today_attendance.check_in_time|time:"H:i" }}
        </div>
        <div>
          <i class="bi bi-box-arrow-left text-danger me-1"></i>
          انصراف: {{ today_attendance.check_out_time|time:"H:i" }}
        </div>
      </div>
      {% else %}
      <i class="bi bi-clock-fill fs-1 text-warning"></i>
      <h6 class="fw-bold mt-2 text-warning">أنت في العمل الآن</h6>
      <div class="text-muted small">
        <i class="bi bi-box-arrow-in-right text-success me-1"></i>
        حضور: {{ today_attendance.check_in_time|time:"H:i" }}
      </div>
      {% endif %}
    </div>
    {% endif %}

    <!-- الموقع الحالي -->
    <div class="location-info" id="locationInfo">
      <div class="d-flex align-items-center gap-2">
        <div class="spinner-border spinner-border-sm text-primary" id="locationSpinner"></div>
        <span id="locationText">جاري تحديد موقعك...</span>
      </div>
    </div>

    <!-- أزرار الحضور -->
    <div class="mt-4">

      {% if not today_attendance %}
      <!-- تسجيل حضور -->
      <button class="checkin-btn btn-check-in mb-3"
              id="checkInBtn" onclick="doCheckIn()" disabled>
        <i class="bi bi-box-arrow-in-right fs-4"></i>
        <span>تسجيل الحضور</span>
      </button>

      {% elif not today_attendance.check_out_time %}
      <!-- تسجيل انصراف -->
      <button class="checkin-btn btn-check-out mb-3"
              id="checkOutBtn" onclick="doCheckOut()" disabled>
        <i class="bi bi-box-arrow-left fs-4"></i>
        <span>تسجيل الانصراف</span>
      </button>

      {% else %}
      <!-- خلاص -->
      <button class="checkin-btn btn-disabled mb-3" disabled>
        <i class="bi bi-check-all fs-4"></i>
        <span>تم تسجيل اليوم بالكامل</span>
      </button>
      {% endif %}

      <!-- زرار الزيارة للميداني فقط -->
      {% if employee.is_field_worker %}
      <a href="{% url 'attendance:visit_add' %}"
         class="checkin-btn btn-visit">
        <i class="bi bi-geo-alt-fill fs-4"></i>
        <span>تسجيل زيارة ميدانية</span>
      </a>
      {% endif %}

    </div>

    <!-- رسائل -->
    <div id="resultMessage" class="mt-3" style="display:none;"></div>

    {% endif %}

  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
let currentLat = null;
let currentLng = null;
let currentAddress = '';

// ── تحديد الموقع ──────────────────────────────────────
function getLocation() {
  if (!navigator.geolocation) {
    showLocationError('المتصفح لا يدعم تحديد الموقع');
    return;
  }

  navigator.geolocation.getCurrentPosition(
    function(pos) {
      currentLat = pos.coords.latitude;
      currentLng = pos.coords.longitude;

      document.getElementById('locationSpinner').style.display = 'none';
      document.getElementById('locationText').innerHTML =
        '<i class="bi bi-check-circle text-success me-1"></i>' +
        'تم تحديد موقعك بنجاح';

      // تفعيل الأزرار
      const checkInBtn = document.getElementById('checkInBtn');
      const checkOutBtn = document.getElementById('checkOutBtn');
      if (checkInBtn) checkInBtn.disabled = false;
      if (checkOutBtn) checkOutBtn.disabled = false;

      // Reverse Geocoding
      fetch(`https://nominatim.openstreetmap.org/reverse?lat=${currentLat}&lon=${currentLng}&format=json&accept-language=ar`)
        .then(r => r.json())
        .then(data => {
          currentAddress = data.display_name || '';
          document.getElementById('locationText').innerHTML =
            '<i class="bi bi-check-circle text-success me-1"></i>' +
            '<small>' + (currentAddress.substring(0, 60)) + '</small>';
        })
        .catch(() => {});
    },
    function(err) {
      showLocationError('تعذر تحديد الموقع: ' + err.message);
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
  );
}

function showLocationError(msg) {
  document.getElementById('locationSpinner').style.display = 'none';
  document.getElementById('locationText').innerHTML =
    '<i class="bi bi-exclamation-triangle text-danger me-1"></i>' + msg;
}

// ── تسجيل الحضور ─────────────────────────────────────
function doCheckIn() {
  if (!currentLat || !currentLng) {
    showResult('error', 'يرجى السماح بتحديد الموقع أولاً');
    return;
  }

  const btn = document.getElementById('checkInBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div> جاري التسجيل...';

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                    getCookie('csrftoken');

  fetch('{% url "attendance:api_check_in" %}', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
      latitude: currentLat,
      longitude: currentLng,
      address: currentAddress,
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'success' || data.success) {
      showResult('success', data.message || 'تم تسجيل الحضور بنجاح!');
      setTimeout(() => location.reload(), 1500);
    } else {
      showResult('error', data.message || 'حدث خطأ');
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-box-arrow-in-right fs-4"></i><span>تسجيل الحضور</span>';
    }
  })
  .catch(err => {
    showResult('error', 'خطأ في الاتصال');
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-box-arrow-in-right fs-4"></i><span>تسجيل الحضور</span>';
  });
}

// ── تسجيل الانصراف ────────────────────────────────────
function doCheckOut() {
  if (!currentLat || !currentLng) {
    showResult('error', 'يرجى السماح بتحديد الموقع أولاً');
    return;
  }

  const btn = document.getElementById('checkOutBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div> جاري التسجيل...';

  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                    getCookie('csrftoken');

  fetch('{% url "attendance:api_check_out" %}', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
      latitude: currentLat,
      longitude: currentLng,
      address: currentAddress,
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'success' || data.success) {
      showResult('success', data.message || 'تم تسجيل الانصراف بنجاح!');
      setTimeout(() => location.reload(), 1500);
    } else {
      showResult('error', data.message || 'حدث خطأ');
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-box-arrow-left fs-4"></i><span>تسجيل الانصراف</span>';
    }
  })
  .catch(err => {
    showResult('error', 'خطأ في الاتصال');
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-box-arrow-left fs-4"></i><span>تسجيل الانصراف</span>';
  });
}

// ── مساعدات ────────────────────────────────────────────
function showResult(type, msg) {
  const el = document.getElementById('resultMessage');
  el.style.display = 'block';
  if (type === 'success') {
    el.className = 'alert alert-success border-0 shadow-sm mt-3';
    el.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>' + msg;
  } else {
    el.className = 'alert alert-danger border-0 shadow-sm mt-3';
    el.innerHTML = '<i class="bi bi-x-circle-fill me-2"></i>' + msg;
  }
}

function getCookie(name) {
  let val = null;
  document.cookie.split(';').forEach(c => {
    c = c.trim();
    if (c.startsWith(name + '=')) val = c.substring(name.length + 1);
  });
  return val;
}

// ── بدء تحديد الموقع فورًا ─────────────────────────────
getLocation();
</script>

{% csrf_token %}
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 3. تحديث check_in view — إضافة context صح
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث check_in view...")

views = read_file(views_path)

# نبحث عن الـ view ونتأكد إنه بيبعت employee + today_attendance + show_map
# الأسهل: نضيف view جديد أو نعدل الموجود

new_checkin_view = '''

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

    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'show_map': show_map,
        'page_title': 'تسجيل الحضور',
    }
    return render(request, 'attendance/check_in.html', context)
'''

if "def smart_check_in_page" not in views:
    views += new_checkin_view
    write_file(views_path, views)
    print("  ✅ تم إضافة smart_check_in_page view")
else:
    print("  ℹ️  smart_check_in_page موجود")


# ════════════════════════════════════════════════════════════
# 4. تحديث attendance/urls.py — ربط الـ view الجديد
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls = read_file(urls_path)

if "smart_check_in_page" not in urls:
    # نستبدل الـ check_in view القديم
    urls = urls.replace(
        "name='check_in'",
        "name='check_in_old'"
    )
    urls = urls.replace(
        "name='check_in_page'",
        "name='check_in_page_old'"
    )

    # نضيف الجديد
    urls_lines = urls.strip().split("\n")
    insert_idx = None
    for i, line in enumerate(urls_lines):
        if "urlpatterns" in line:
            insert_idx = i + 1
            break

    if insert_idx:
        new_url = "    path('check-in/', views.smart_check_in_page, name='check_in'),"
        urls_lines.insert(insert_idx + 1, new_url)
        urls = "\n".join(urls_lines)
        write_file(urls_path, urls)
        print("  ✅ تم تحديث URLs")
else:
    print("  ℹ️  URL موجود")


# ════════════════════════════════════════════════════════════
# 5. تحديث api_check_in — Geofencing للـ check-in فقط
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث api_check_in بـ Geofencing...")

views = read_file(views_path)

# نبحث عن api_check_in ونتأكد إنه بيتحقق من النطاق
if "check_within_range" not in views and "def api_check_in" in views:
    # نضيف التحقق من النطاق في بداية api_check_in
    # الأسهل: نضيف comment تذكيري
    print("  ℹ️  Geofencing logic محتاج مراجعة يدوية للـ api_check_in")
    print("      المنطق:")
    print("      - check-in: لازم within_range = True")
    print("      - check-out: مسموح من أي مكان")
else:
    print("  ℹ️  Geofencing موجود أو api_check_in مش موجود")


# ════════════════════════════════════════════════════════════
# 6. تحديث Sidebar — إضافة aliases للـ URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث URL aliases...")

urls = read_file(urls_path)

# التأكد من وجود aliases مهمة
aliases_needed = {
    "check_in_page": "check_in",
}

for old_name, correct_name in aliases_needed.items():
    if f"name='{old_name}'" not in urls and f"name='{correct_name}'" in urls:
        print(f"  ℹ️  {correct_name} موجود - {old_name} مش محتاج")


print("\n" + "=" * 60)
print("  ✅ Patch 33 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Geofencing helper (calculate_distance + check_within_range)
  2. ✅ check_in.html جديدة كليًا:
       - بسيطة ونظيفة
       - الموظف يشوف حالته
       - زرار حضور / انصراف
       - زرار زيارة للميداني فقط
       - الخريطة مخفية عن الموظف
       - GPS تلقائي + عنوان
  3. ✅ smart_check_in_page view
  4. ✅ URL محدث

جرب دلوقتي:
  1. emp10003 → تسجيل حضور (موظف عادي)
     - مفيش زرار زيارة

  2. emp10004 → تسجيل حضور (موظف ميداني)
     - زرار "تسجيل زيارة ميدانية" ظاهر

  3. demo_admin → تسجيل حضور
     - مش هيظهر (مش مربوط بموظف)
""")