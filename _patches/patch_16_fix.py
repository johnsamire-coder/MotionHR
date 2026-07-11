#!/usr/bin/env python3
"""
Patch 16-fix: إصلاح motionhr/urls.py
"""

import os, sys, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

print("=" * 60)
print("  Patch 16-fix: إصلاح motionhr/urls.py")
print("=" * 60)

# ── اقرأ urls.py الحالي وأطبعه ──
urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
current = read_file(urls_path)
print("\n📋 محتوى urls.py الحالي:")
print(current)

# ── نكتبه من أول وجديد بشكل صح ──
print("\n🔧 إعادة كتابة urls.py...")

new_urls = """from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from accounts.views import (
    CustomPasswordChangeView,
    smart_login_view,
    smart_logout_view,
)


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


urlpatterns = [

    # ── الرئيسية ──────────────────────────────────────────
    path('', home_redirect, name='home'),

    # ── Admin ─────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── تسجيل الدخول والخروج ──────────────────────────────
    path('login/',  smart_login_view,  name='login'),
    path('logout/', smart_logout_view, name='logout'),

    # ── استعادة كلمة المرور ───────────────────────────────
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
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
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # ── تغيير كلمة المرور ─────────────────────────────────
    path('password-change/',
         CustomPasswordChangeView.as_view(
             template_name='accounts/password_change.html',
         ),
         name='password_change'),

    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html',
         ),
         name='password_change_done'),

    # ── Dashboard ─────────────────────────────────────────
    path('dashboard/', include('accounts.urls_dashboard')),

    # ── Apps ──────────────────────────────────────────────
    path('accounts/',      include('accounts.urls',      namespace='accounts')),
    path('employees/',     include('employees.urls',     namespace='employees')),
    path('attendance/',    include('attendance.urls',    namespace='attendance')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),

]

# ── Media Files (Development) ──────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""

write_file(urls_path, new_urls)

# ── تحقق إن accounts/urls_dashboard.py موجود ──
print("\n🔧 التحقق من dashboard URL...")

dashboard_urls_path = os.path.join(BASE_DIR, 'accounts', 'urls_dashboard.py')

if not os.path.exists(dashboard_urls_path):
    # نبحث في urls.py القديم عن الـ dashboard view
    dashboard_urls = """from django.urls import path
from accounts import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]
"""
    with open(dashboard_urls_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_urls)
    print("  ✅ تم إنشاء urls_dashboard.py")
else:
    print("  ℹ️  urls_dashboard.py موجود")

# ── تحقق إن dashboard_view موجود ──
print("\n🔧 التحقق من dashboard_view...")

accounts_views_path = os.path.join(BASE_DIR, 'accounts', 'views.py')
accounts_views = read_file(accounts_views_path)

if 'def dashboard_view' not in accounts_views and 'def dashboard' not in accounts_views:
    dashboard_view = """

# ─────────────────────────────────────────────
# Dashboard View
# ─────────────────────────────────────────────
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    context = {
        'page_title': 'لوحة التحكم',
    }
    return render(request, 'dashboard/index.html', context)
"""
    with open(accounts_views_path, 'a', encoding='utf-8') as f:
        f.write(dashboard_view)
    print("  ✅ تم إضافة dashboard_view")
else:
    print("  ℹ️  dashboard_view موجود")

    # ── نتحقق من اسمه الحقيقي ──
    import re
    match = re.search(r'def (dashboard\w*)\(', accounts_views)
    if match:
        actual_name = match.group(1)
        if actual_name != 'dashboard_view':
            print(f"  ℹ️  اسم الـ view الحقيقي: {actual_name}")
            # نحدث urls_dashboard.py
            dashboard_urls = f"""from django.urls import path
from accounts import views

urlpatterns = [
    path('', views.{actual_name}, name='dashboard'),
]
"""
            with open(dashboard_urls_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_urls)
            print(f"  ✅ تم تحديث urls_dashboard.py بـ {actual_name}")

print("\n" + "=" * 60)
print("  ✅ Patch 16-fix اكتمل!")
print("=" * 60)
print("""
🚀 شغّل دلوقتي:
  python manage.py migrate
""")