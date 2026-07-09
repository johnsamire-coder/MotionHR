"""
============================================================
Patch 09: إصلاح روابط Attendance
============================================================
- تأكيد وجود url للـ monitor
- تصحيح رابط live_map في الـ Dashboard
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. التأكد من وجود url للـ monitor في attendance/urls.py
# ═══════════════════════════════════════════════════════════

def fix_attendance_urls():
    """التأكد من وجود كل الـ URLs المطلوبة"""
    urls_path = BASE_DIR / 'attendance' / 'urls.py'
    
    if not urls_path.exists():
        return False, "ملف attendance/urls.py مش موجود"
    
    content = urls_path.read_text(encoding='utf-8')
    
    # نتأكد إن الـ monitor موجود
    if "name='monitor'" in content and "name='api_monitor'" in content:
        return True, "الـ URLs موجودة بالفعل"
    
    # نستبدل الملف بالكامل بالنسخة الكاملة
    new_content = '''from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # سجلات الحضور
    path('', views.attendance_list, name='list'),
    
    # Check-in/out
    path('check-in/', views.check_in_page, name='check_in'),
    path('api/check-in/', views.api_check_in, name='api_check_in'),
    path('api/check-out/', views.api_check_out, name='api_check_out'),
    
    # زيارات المواقع
    path('visits/', views.visits_list, name='visits'),
    path('visits/add/', views.visit_add, name='visit_add'),
    
    # الخريطة والتتبع
    path('map/', views.live_map, name='live_map'),
    path('api/live-locations/', views.api_live_locations, name='api_live_locations'),
    
    # التتبع المستمر
    path('tracking/', views.tracking_page, name='tracking'),
    path('api/track/', views.api_track_location, name='api_track'),
    path('tracking/employee/<int:employee_id>/', views.employee_tracking_detail, name='tracking_detail'),
    
    # متابعة الموظفين للمدير
    path('monitor/', views.field_employees_monitor, name='monitor'),
    path('api/monitor/', views.api_monitor_data, name='api_monitor'),
]
'''
    
    urls_path.write_text(new_content, encoding='utf-8')
    return True, "تم تحديث attendance/urls.py"


# ═══════════════════════════════════════════════════════════
# 2. إصلاح روابط الـ Dashboard
# ═══════════════════════════════════════════════════════════

def fix_dashboard_map_link():
    """إصلاح رابط الخريطة في الـ Dashboard"""
    template_path = BASE_DIR / 'templates' / 'dashboard' / 'index.html'
    
    if not template_path.exists():
        return False, "ملف dashboard/index.html مش موجود"
    
    content = template_path.read_text(encoding='utf-8')
    
    # نصلح كل الروابط للخريطة
    replacements = [
        ('/attendance/live-map/', '/attendance/map/'),
        ('{% url \'attendance:live-map\' %}', '{% url \'attendance:live_map\' %}'),
    ]
    
    changed = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed = True
    
    if changed:
        template_path.write_text(content, encoding='utf-8')
        return True, "تم إصلاح رابط الخريطة"
    
    return True, "الروابط صحيحة"


# ═══════════════════════════════════════════════════════════
# 3. التأكد من وجود views للـ monitor
# ═══════════════════════════════════════════════════════════

def check_monitor_view():
    """التأكد من وجود view للـ monitor"""
    views_path = BASE_DIR / 'attendance' / 'views.py'
    
    if not views_path.exists():
        return False, "ملف attendance/views.py مش موجود"
    
    content = views_path.read_text(encoding='utf-8')
    
    if 'def field_employees_monitor' in content:
        return True, "view موجود ✅"
    else:
        return False, "⚠️  view مش موجود - محتاج نضيفه"


# ═══════════════════════════════════════════════════════════
# 4. التأكد من وجود template للـ monitor
# ═══════════════════════════════════════════════════════════

def check_monitor_template():
    """التأكد من وجود template للـ monitor"""
    template_path = BASE_DIR / 'templates' / 'attendance' / 'monitor.html'
    
    if template_path.exists():
        return True, "template موجود ✅"
    else:
        return False, "⚠️  template مش موجود - محتاج نضيفه"


# ═══════════════════════════════════════════════════════════
# 5. التأكد من live_map view و template
# ═══════════════════════════════════════════════════════════

def check_live_map():
    """التأكد من live_map"""
    views_path = BASE_DIR / 'attendance' / 'views.py'
    template_path = BASE_DIR / 'templates' / 'attendance' / 'live_map.html'
    
    view_exists = False
    template_exists = template_path.exists()
    
    if views_path.exists():
        content = views_path.read_text(encoding='utf-8')
        view_exists = 'def live_map' in content
    
    if view_exists and template_exists:
        return True, "live_map موجود بالكامل ✅"
    elif view_exists:
        return False, "⚠️  view موجود لكن template ناقص"
    elif template_exists:
        return False, "⚠️  template موجود لكن view ناقص"
    else:
        return False, "⚠️  view و template ناقصين"


def main():
    print("=" * 60)
    print("🔧 Patch 09: إصلاح روابط Attendance")
    print("=" * 60)
    print()
    
    print("📁 فحص الملفات...")
    print("-" * 60)
    
    checks = [
        ('field_employees_monitor view', check_monitor_view),
        ('monitor.html template', check_monitor_template),
        ('live_map (view + template)', check_live_map),
    ]
    
    for name, func in checks:
        try:
            success, message = func()
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("🔧 تطبيق الإصلاحات...")
    print("-" * 60)
    
    fixes = [
        ('attendance/urls.py', fix_attendance_urls),
        ('templates/dashboard/index.html', fix_dashboard_map_link),
    ]
    
    for name, func in fixes:
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
    print("جرب دلوقتي:")
    print("  1. أعد تشغيل السيرفر (Ctrl+C ثم python manage.py runserver)")
    print("  2. روح لـ: http://127.0.0.1:8000/attendance/monitor/")
    print("  3. روح لـ: http://127.0.0.1:8000/attendance/map/")
    print()


if __name__ == '__main__':
    main()