#!/usr/bin/env python3
"""
Patch 36: Smart Geofencing
============================
1. Check-in: لازم يكون في نطاق الفرع
2. Check-out: من أي مكان
3. رسائل واضحة للموظف
4. تسجيل المسافة في سجل الحضور
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


print("=" * 60)
print("  Patch 36: Smart Geofencing")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إعادة كتابة api_check_in و api_check_out
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

# نتأكد إن calculate_distance موجود
if "def calculate_distance" not in views:
    geo_helper = '''
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """حساب المسافة بين نقطتين GPS بالمتر (Haversine)"""
    R = 6371000
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

'''
    # نضيف بعد الـ imports
    first_def = views.find("\ndef ")
    if first_def == -1:
        first_def = views.find("\nclass ")
    if first_def == -1:
        first_def = len(views)
    views = views[:first_def] + "\n" + geo_helper + views[first_def:]
    print("  ✅ تم إضافة calculate_distance")


# ════════════════════════════════════════════════════════════
# 2. إضافة Smart API views
# ════════════════════════════════════════════════════════════

smart_api = '''

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
'''

if "def smart_api_check_in" not in views:
    views += smart_api
    write_file(views_path, views)
    print("  ✅ تم إضافة Smart API views")
else:
    print("  ℹ️  Smart API views موجودة")


# ════════════════════════════════════════════════════════════
# 3. تحديث URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls = read_file(urls_path)

if "smart_api_check_in" not in urls:
    # نستبدل الـ api URLs القديمة أو نضيف الجديدة
    old_api_in = "path('api/check-in/', views.api_check_in, name='api_check_in'),"
    new_api_in = "path('api/check-in/', views.smart_api_check_in, name='api_check_in'),"

    old_api_out = "path('api/check-out/', views.api_check_out, name='api_check_out'),"
    new_api_out = "path('api/check-out/', views.smart_api_check_out, name='api_check_out'),"

    if old_api_in in urls:
        urls = urls.replace(old_api_in, new_api_in)
    if old_api_out in urls:
        urls = urls.replace(old_api_out, new_api_out)

    write_file(urls_path, urls)
    print("  ✅ تم تحديث URLs")
else:
    print("  ℹ️  URLs محدثة")


# ════════════════════════════════════════════════════════════
# 4. تحديث check_in.html — رسائل Geofencing
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث check_in.html...")

checkin_path = os.path.join(BASE_DIR, "templates", "attendance", "check_in.html")
checkin = read_file(checkin_path)

# نتأكد إن الصفحة بتستخدم الـ API URLs الصح
checkin = checkin.replace(
    "{% url 'attendance:api_check_in' %}",
    "{% url 'attendance:api_check_in' %}"
)
checkin = checkin.replace(
    "{% url 'attendance:api_check_out' %}",
    "{% url 'attendance:api_check_out' %}"
)

# إضافة معلومة النطاق للموظف
if "geofencing-info" not in checkin:
    geo_info = """
      <!-- معلومة النطاق -->
      {% if employee.branch and employee.branch.check_in_radius %}
      <div class="location-info mt-2" id="geofencing-info"
           style="background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:10px;">
        <div class="d-flex align-items-center gap-2">
          <i class="bi bi-shield-check text-warning"></i>
          <small class="text-muted">
            تسجيل الحضور متاح فقط في نطاق
            <strong>{{ employee.branch.check_in_radius }} متر</strong>
            من {{ employee.branch.name_ar }}.
            <br>
            تسجيل الانصراف متاح من أي مكان.
          </small>
        </div>
      </div>
      {% endif %}
"""
    # نضيف بعد location-info الأصلي
    if 'id="locationInfo"' in checkin:
        loc_end = checkin.find("</div>", checkin.find('id="locationInfo"'))
        if loc_end != -1:
            checkin = checkin[:loc_end + 6] + geo_info + checkin[loc_end + 6:]
            write_file(checkin_path, checkin)
            print("  ✅ تم إضافة معلومة النطاق")
    else:
        print("  ℹ️  locationInfo مش موجود - مش محتاج تعديل")
else:
    print("  ℹ️  geofencing-info موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 36 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ smart_api_check_in — مع Geofencing
       - لو الموظف خارج النطاق: يترفض + رسالة بالمسافة
       - لو جوه النطاق: يتسجل + رسالة بالمسافة
  2. ✅ smart_api_check_out — بدون Geofencing
       - من أي مكان
       - بيحسب ساعات العمل تلقائي
  3. ✅ URLs محدثة
  4. ✅ رسالة واضحة للموظف عن النطاق المسموح
  5. ✅ حساب التأخير مع grace_period

جرب دلوقتي:
  emp10003 → تسجيل حضور
  - لو في نطاق الفرع: يتسجل ✅
  - لو برا النطاق: يترفض مع المسافة ❌

  emp10003 → تسجيل انصراف
  - من أي مكان ✅
""")