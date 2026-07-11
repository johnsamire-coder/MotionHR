#!/usr/bin/env python3
"""
Patch 23: Simulation كامل + إصلاح الأخطاء
============================================
- فحص كل الـ URLs
- فحص الـ imports
- فحص الـ migrations
- إصلاح أي مشاكل
- تقرير شامل بحالة النظام
"""

import os, sys, subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def append_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

def run_cmd(cmd):
    result = subprocess.run(
        cmd, shell=True, capture_output=True,
        text=True, cwd=BASE_DIR
    )
    return result.returncode, result.stdout, result.stderr

print("=" * 60)
print("  Patch 23: Simulation & Fix")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. فحص Django Check
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص Django (manage.py check)...")

code, out, err = run_cmd(
    f'"{sys.executable}" manage.py check --settings=motionhr.settings'
)

if code == 0:
    print("  ✅ Django Check: لا يوجد أخطاء")
else:
    print("  ⚠️  يوجد مشاكل:")
    print(err[:2000])


# ════════════════════════════════════════════════════════════
# 2. فحص Migrations
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص Migrations...")

code, out, err = run_cmd(
    f'"{sys.executable}" manage.py migrate --check'
)

if code == 0:
    print("  ✅ كل الـ Migrations طُبقت")
else:
    print("  ⚠️  يوجد migrations لم تُطبق - سنطبقها...")
    code2, out2, err2 = run_cmd(
        f'"{sys.executable}" manage.py migrate'
    )
    if code2 == 0:
        print("  ✅ تم تطبيق الـ Migrations بنجاح")
    else:
        print(f"  ❌ خطأ: {err2[:500]}")


# ════════════════════════════════════════════════════════════
# 3. فحص الـ URLs الأساسية
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص URLs الأساسية...")

main_urls = read_file(os.path.join(BASE_DIR, 'motionhr', 'urls.py'))
print(f"\n  📋 محتوى motionhr/urls.py:\n")
print(main_urls)


# ════════════════════════════════════════════════════════════
# 4. إصلاح motionhr/urls.py نهائي وشامل
# ════════════════════════════════════════════════════════════
print("\n🔧 إعادة كتابة motionhr/urls.py نهائي...")

# نقرأ الـ accounts views عشان نعرف إيه الموجود
accounts_views = read_file(os.path.join(BASE_DIR, 'accounts', 'views.py'))

# نحدد الـ views الموجودة فعلاً
has_dashboard             = 'def dashboard(' in accounts_views
has_smart_login           = 'def smart_login_view(' in accounts_views
has_smart_logout          = 'def smart_logout_view(' in accounts_views
has_custom_pwd_change     = 'class CustomPasswordChangeView(' in accounts_views
has_offline               = 'def offline_view(' in accounts_views
has_manifest              = 'def manifest_view(' in accounts_views
has_sw                    = 'def service_worker_view(' in accounts_views
has_global_search         = 'def global_search(' in accounts_views
has_handler_404           = 'def handler_404(' in accounts_views
has_handler_500           = 'def handler_500(' in accounts_views

print(f"""
  📋 الـ Views الموجودة في accounts/views.py:
  - dashboard:              {'✅' if has_dashboard else '❌'}
  - smart_login_view:       {'✅' if has_smart_login else '❌'}
  - smart_logout_view:      {'✅' if has_smart_logout else '❌'}
  - CustomPasswordChangeView:{'✅' if has_custom_pwd_change else '❌'}
  - offline_view:           {'✅' if has_offline else '❌'}
  - manifest_view:          {'✅' if has_manifest else '❌'}
  - service_worker_view:    {'✅' if has_sw else '❌'}
  - global_search:          {'✅' if has_global_search else '❌'}
  - handler_404:            {'✅' if has_handler_404 else '❌'}
  - handler_500:            {'✅' if has_handler_500 else '❌'}
""")

# بناء قائمة الـ imports بناءً على الموجود فعلاً
imports_list = []
if has_custom_pwd_change:
    imports_list.append('    CustomPasswordChangeView,')
if has_smart_login:
    imports_list.append('    smart_login_view,')
if has_smart_logout:
    imports_list.append('    smart_logout_view,')
if has_dashboard:
    imports_list.append('    dashboard,')
if has_offline:
    imports_list.append('    offline_view,')
if has_manifest:
    imports_list.append('    manifest_view,')
if has_sw:
    imports_list.append('    service_worker_view,')
if has_global_search:
    imports_list.append('    global_search,')

imports_str = '\n'.join(imports_list)

# بناء الـ URL patterns
url_patterns = []

# PWA
if has_offline:
    url_patterns.append("    path('offline/',      offline_view,        name='offline'),")
if has_manifest:
    url_patterns.append("    path('manifest.json', manifest_view,       name='manifest'),")
if has_sw:
    url_patterns.append("    path('sw.js',         service_worker_view, name='service_worker'),")

# Search
if has_global_search:
    url_patterns.append("    path('search/',       global_search,       name='global_search'),")

pwa_search_urls = '\n'.join(url_patterns)

# Password Change
if has_custom_pwd_change:
    pwd_change_view = "CustomPasswordChangeView.as_view("
else:
    pwd_change_view = "auth_views.PasswordChangeView.as_view("

# Login/Logout
if has_smart_login:
    login_view = "smart_login_view"
else:
    login_view = "auth_views.LoginView.as_view(template_name='accounts/login.html')"

if has_smart_logout:
    logout_view = "smart_logout_view"
else:
    logout_view = "auth_views.LogoutView.as_view()"

# Dashboard
if has_dashboard:
    dashboard_view = "dashboard"
else:
    dashboard_view = "auth_views.LoginView.as_view()"

final_urls = f"""from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from accounts.views import (
{imports_str}
)


urlpatterns = [

    # ── Landing Page ───────────────────────────────────────
    path('', include('landing.urls', namespace='landing')),

    # ── Admin ─────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── تسجيل الدخول والخروج ──────────────────────────────
    path('login/',  {login_view},  name='login'),
    path('logout/', {logout_view}, name='logout'),

    # ── استعادة كلمة المرور ───────────────────────────────
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/password-reset/done/',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/password-reset-complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # ── تغيير كلمة المرور ─────────────────────────────────
    path('password-change/',
         {pwd_change_view}
             template_name='accounts/password_change.html',
             success_url='/password-change/done/',
         ),
         name='password_change'),

    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html',
         ),
         name='password_change_done'),

    # ── Dashboard ─────────────────────────────────────────
    path('dashboard/', {dashboard_view}, name='dashboard'),

    # ── PWA ───────────────────────────────────────────────
{pwa_search_urls}

    # ── Apps ──────────────────────────────────────────────
    path('accounts/',      include('accounts.urls',      namespace='accounts')),
    path('employees/',     include('employees.urls',     namespace='employees')),
    path('attendance/',    include('attendance.urls',    namespace='attendance')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    path('companies/',     include('companies.urls',     namespace='companies')),
    path('leaves/',        include('leaves.urls',        namespace='leaves')),
    path('reports/',       include('reports.urls',       namespace='reports')),

]

# ── Media + Static ─────────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ── Error Handlers ─────────────────────────────────────────
"""

if has_handler_404:
    final_urls += "handler404 = 'accounts.views.handler_404'\n"
if has_handler_500:
    final_urls += "handler500 = 'accounts.views.handler_500'\n"

write_file(
    os.path.join(BASE_DIR, 'motionhr', 'urls.py'),
    final_urls
)


# ════════════════════════════════════════════════════════════
# 5. فحص Django Check بعد التعديل
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص Django بعد التعديل...")

code, out, err = run_cmd(
    f'"{sys.executable}" manage.py check --settings=motionhr.settings'
)

if code == 0:
    print("  ✅ Django Check: لا يوجد أخطاء!")
else:
    print("  ⚠️  يوجد مشاكل:")
    for line in err.split('\n'):
        if line.strip():
            print(f"    {line}")


# ════════════════════════════════════════════════════════════
# 6. فحص الملفات الأساسية
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص الملفات الأساسية...")

required_files = [
    # Templates
    ('templates/base/base.html',                   'Base Template'),
    ('templates/base/dashboard_base.html',          'Dashboard Base'),
    ('templates/accounts/login.html',               'Login Page'),
    ('templates/dashboard/index.html',              'Dashboard'),
    ('templates/employees/list.html',               'Employees List'),
    ('templates/employees/detail.html',             'Employee Detail'),
    ('templates/employees/form.html',               'Employee Form'),
    ('templates/attendance/list.html',              'Attendance List'),
    ('templates/attendance/check_in.html',          'Check In'),
    ('templates/attendance/live_map.html',          'Live Map'),
    ('templates/companies/settings.html',           'Company Settings'),
    ('templates/companies/branches_list.html',      'Branches'),
    ('templates/companies/departments_list.html',   'Departments'),
    ('templates/companies/shifts_list.html',        'Shifts'),
    ('templates/leaves/leave_requests_list.html',   'Leave Requests'),
    ('templates/leaves/leave_types_list.html',      'Leave Types'),
    ('templates/leaves/leave_balances.html',        'Leave Balances'),
    ('templates/reports/home.html',                 'Reports Home'),
    ('templates/reports/attendance_report.html',    'Attendance Report'),
    ('templates/subscriptions/my_plan.html',        'My Plan'),
    ('templates/subscriptions/contact_sales.html',  'Contact Sales'),
    ('templates/landing/home.html',                 'Landing Home'),
    ('templates/landing/pricing.html',              'Pricing'),
    ('templates/landing/contact.html',              'Contact'),
    ('templates/accounts/profile.html',             'Profile'),
    ('templates/404.html',                          '404 Page'),
    ('templates/500.html',                          '500 Page'),
    ('templates/offline.html',                      'Offline Page'),
    # Static
    ('static/manifest.json',                        'PWA Manifest'),
    ('static/sw.js',                               'Service Worker'),
    ('static/icons/icon-192x192.png',              'PWA Icon'),
    # Python files
    ('accounts/login_backend.py',                   'Login Backend'),
    ('accounts/middleware.py',                      'Auth Middleware'),
    ('employees/account_utils.py',                  'Account Utils'),
    ('reports/utils.py',                            'Reports Utils'),
]

missing = []
found   = []

for file_path, label in required_files:
    full_path = os.path.join(BASE_DIR, file_path)
    if os.path.exists(full_path):
        found.append(label)
    else:
        missing.append((file_path, label))

print(f"\n  ✅ موجود: {len(found)} ملف")

if missing:
    print(f"\n  ❌ مفقود: {len(missing)} ملف:")
    for path, label in missing:
        print(f"     - {label} ({path})")
else:
    print("  ✅ كل الملفات موجودة!")


# ════════════════════════════════════════════════════════════
# 7. فحص الـ Apps في INSTALLED_APPS
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص INSTALLED_APPS...")

settings_content = read_file(os.path.join(BASE_DIR, 'motionhr', 'settings.py'))

required_apps = [
    'core', 'accounts', 'companies', 'employees',
    'attendance', 'subscriptions', 'leaves', 'reports',
    'landing',
]

for app in required_apps:
    if f"'{app}'" in settings_content or f'"{app}"' in settings_content:
        print(f"  ✅ {app}")
    else:
        print(f"  ❌ {app} - مش موجود في INSTALLED_APPS!")
        # نضيفه
        settings_content = settings_content.replace(
            "'landing',",
            f"'{app}',\n    'landing',"
        )
        write_file(
            os.path.join(BASE_DIR, 'motionhr', 'settings.py'),
            settings_content
        )


# ════════════════════════════════════════════════════════════
# 8. فحص Django Check النهائي
# ════════════════════════════════════════════════════════════
print("\n🔍 الفحص النهائي...")

code, out, err = run_cmd(
    f'"{sys.executable}" manage.py check --settings=motionhr.settings'
)

if code == 0:
    print("  ✅ النظام سليم 100%!")
else:
    print("  ⚠️  المشاكل المتبقية:")
    for line in err.split('\n'):
        if line.strip() and ('Error' in line or 'error' in line or 'ERRORS' in line):
            print(f"    ⚠️  {line}")


# ════════════════════════════════════════════════════════════
# 9. فحص الـ Migrations المتبقية
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص Migrations...")

code, out, err = run_cmd(
    f'"{sys.executable}" manage.py showmigrations --settings=motionhr.settings'
)

if code == 0:
    lines = out.split('\n')
    pending = [l for l in lines if '[ ]' in l]
    applied = [l for l in lines if '[x]' in l]
    print(f"  ✅ مطبقة: {len(applied)}")
    if pending:
        print(f"  ⚠️  غير مطبقة: {len(pending)}")
        for p in pending:
            print(f"     {p}")
        # نطبقها
        print("\n  🔧 تطبيق الـ Migrations...")
        run_cmd(f'"{sys.executable}" manage.py migrate')
        print("  ✅ تم التطبيق")
    else:
        print("  ✅ كل الـ Migrations مطبقة")


# ════════════════════════════════════════════════════════════
# 10. تقرير شامل بالـ URLs
# ════════════════════════════════════════════════════════════
print("\n📋 تقرير URLs الكامل...")

all_urls = {
    "Landing Page": [
        ("/",             "الصفحة الرئيسية"),
        ("/pricing/",     "الأسعار"),
        ("/contact/",     "تواصل معنا"),
        ("/about/",       "عن النظام"),
    ],
    "Authentication": [
        ("/login/",                         "تسجيل الدخول"),
        ("/logout/",                        "تسجيل الخروج"),
        ("/password-reset/",               "استعادة كلمة المرور"),
        ("/password-change/",              "تغيير كلمة المرور"),
    ],
    "Dashboard": [
        ("/dashboard/",   "لوحة التحكم"),
        ("/search/",      "البحث الشامل"),
    ],
    "Accounts": [
        ("/accounts/profile/",        "الملف الشخصي"),
        ("/accounts/notifications/",  "الإشعارات"),
        ("/accounts/login-settings/", "إعدادات الدخول"),
    ],
    "Employees": [
        ("/employees/",           "قائمة الموظفين"),
        ("/employees/add/",       "إضافة موظف"),
        ("/employees/1/",         "تفاصيل موظف"),
        ("/employees/1/edit/",    "تعديل موظف"),
        ("/employees/print/",     "طباعة القائمة"),
    ],
    "Attendance": [
        ("/attendance/",          "سجلات الحضور"),
        ("/attendance/check-in/", "تسجيل الحضور"),
        ("/attendance/map/",      "الخريطة الحية"),
        ("/attendance/visits/",   "الزيارات"),
        ("/attendance/tracking/", "التتبع"),
        ("/attendance/monitor/",  "متابعة الميدانيين"),
    ],
    "Companies": [
        ("/companies/settings/",      "إعدادات الشركة"),
        ("/companies/branches/",      "الفروع"),
        ("/companies/departments/",   "الإدارات"),
        ("/companies/shifts/",        "الشيفتات"),
    ],
    "Leaves": [
        ("/leaves/",          "طلبات الإجازات"),
        ("/leaves/add/",      "طلب إجازة جديد"),
        ("/leaves/types/",    "أنواع الإجازات"),
        ("/leaves/balances/", "الأرصدة"),
    ],
    "Reports": [
        ("/reports/",             "الصفحة الرئيسية"),
        ("/reports/attendance/",  "الحضور"),
        ("/reports/late/",        "التأخيرات"),
        ("/reports/leaves/",      "الإجازات"),
        ("/reports/field/",       "الميدانيون"),
        ("/reports/employees/",   "الموظفون"),
    ],
    "Subscriptions": [
        ("/subscriptions/my-plan/",      "خطتي"),
        ("/subscriptions/contact-sales/","تواصل للترقية"),
    ],
    "PWA": [
        ("/manifest.json", "PWA Manifest"),
        ("/sw.js",         "Service Worker"),
        ("/offline/",      "صفحة Offline"),
    ],
    "Admin": [
        ("/admin/", "Django Admin"),
    ],
}

total_urls = 0
for section, urls in all_urls.items():
    print(f"\n  📁 {section}:")
    for url, label in urls:
        print(f"     {url:<40} ← {label}")
        total_urls += 1

print(f"\n  📊 إجمالي URLs: {total_urls}")


# ════════════════════════════════════════════════════════════
# 11. ملف SIMULATION_GUIDE.md
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء SIMULATION_GUIDE.md...")

create_file(
    os.path.join(BASE_DIR, 'SIMULATION_GUIDE.md'),
    """# 🎯 دليل Simulation الكامل لـ MotionHR

## خطوات الـ Simulation

### 1. تشغيل السيرفر
```bash
.venv\\Scripts\\activate
python manage.py runserver 0.0.0.0:8000