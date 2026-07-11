#!/usr/bin/env python3
"""
Patch 14c-fix2: إصلاح subscriptions/urls.py
الباتش السابق مسح URLs مهمة - هنرجعها + نضيف my_plan
"""

import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

print("=" * 60)
print("  Patch 14c-fix2: إصلاح subscriptions/urls.py")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إعادة كتابة subscriptions/urls.py بشكل صح وكامل
# ════════════════════════════════════════════════════════════
print("\n🔧 إعادة كتابة subscriptions/urls.py...")

urls_content = """from django.urls import path
from . import views
from .views import contact_sales_view

app_name = 'subscriptions'

urlpatterns = [

    # ── Admin Dashboard ──────────────────────────────────
    path('', views.admin_dashboard, name='admin_dashboard'),

    # ── Plans ────────────────────────────────────────────
    path('plans/', views.plans_list, name='plans_list'),

    # ── Subscriptions (Admin) ────────────────────────────
    path('subscriptions/',
         views.subscriptions_list, name='subscriptions_list'),
    path('subscriptions/create/',
         views.create_subscription, name='create'),
    path('subscriptions/<int:pk>/',
         views.subscription_detail, name='detail'),
    path('subscriptions/<int:pk>/upgrade/',
         views.upgrade_subscription, name='upgrade'),
    path('subscriptions/<int:pk>/extend/',
         views.extend_subscription, name='extend'),
    path('subscriptions/<int:pk>/cancel/',
         views.cancel_subscription, name='cancel'),
    path('subscriptions/<int:pk>/activate/',
         views.activate_subscription, name='activate'),

    # ── Client Side ──────────────────────────────────────
    path('my-subscription/',
         views.my_subscription, name='my_subscription'),
    path('my-plan/',
         views.my_plan_view, name='my_plan'),
    path('upgrade/',
         views.upgrade_plan, name='upgrade_plan'),
    path('feature-locked/',
         views.feature_locked, name='feature_locked'),
    path('contact-sales/',
         contact_sales_view, name='contact_sales'),
]
"""

write_file(
    os.path.join(BASE_DIR, 'subscriptions', 'urls.py'),
    urls_content
)


# ════════════════════════════════════════════════════════════
# 2. التحقق إن upgrade_plan و feature_locked موجودين في views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 التحقق من views.py...")

views_path = os.path.join(BASE_DIR, 'subscriptions', 'views.py')
views_content = read_file(views_path)

missing_views = []

if 'def upgrade_plan' not in views_content:
    missing_views.append('upgrade_plan')

if 'def feature_locked' not in views_content:
    missing_views.append('feature_locked')

if 'def my_subscription' not in views_content:
    missing_views.append('my_subscription')

if missing_views:
    print(f"  ⚠️  Views ناقصة: {missing_views}")
    print("  ➕ سنضيفها...")

    extra_views = ""

    if 'upgrade_plan' in missing_views:
        extra_views += '''

# ─────────────────────────────────────────────
# صفحة ترقية الخطة
# ─────────────────────────────────────────────
@login_required
def upgrade_plan(request):
    """إعادة توجيه لصفحة التواصل"""
    return redirect('subscriptions:contact_sales')
'''

    if 'feature_locked' in missing_views:
        extra_views += '''

# ─────────────────────────────────────────────
# صفحة الميزة المقفولة
# ─────────────────────────────────────────────
@login_required
def feature_locked(request):
    """صفحة الميزة غير المتاحة في الخطة الحالية"""
    context = {
        'feature_name':   request.GET.get('feature', ''),
        'required_plan':  request.GET.get('plan', ''),
        'page_title':     'ميزة غير متاحة',
    }
    return render(request, 'subscriptions/feature_unavailable.html', context)
'''

    if 'my_subscription' in missing_views:
        extra_views += '''

# ─────────────────────────────────────────────
# my_subscription (redirect لـ my_plan)
# ─────────────────────────────────────────────
@login_required
def my_subscription(request):
    """إعادة توجيه لصفحة خطتي"""
    return redirect('subscriptions:my_plan')
'''

    if extra_views:
        # تأكد إن redirect موجود في imports
        if 'from django.shortcuts import' in views_content:
            if 'redirect' not in views_content.split('from django.shortcuts import')[1].split('\n')[0]:
                views_content = views_content.replace(
                    'from django.shortcuts import render',
                    'from django.shortcuts import render, redirect'
                )
                with open(views_path, 'w', encoding='utf-8') as f:
                    f.write(views_content)
                print("  ✅ تم إضافة redirect للـ imports")

        with open(views_path, 'a', encoding='utf-8') as f:
            f.write(extra_views)
        print(f"  ✅ تم إضافة: {missing_views}")
else:
    print("  ✅ كل الـ views موجودة")


# ════════════════════════════════════════════════════════════
# 3. التحقق من الـ Sidebar - إزالة الـ duplicate لو موجود
# ════════════════════════════════════════════════════════════
print("\n🔧 التحقق من الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
sidebar_content = read_file(sidebar_path)

# عد مرات ظهور contact_sales في الـ sidebar
count = sidebar_content.count('contact_sales')
if count > 1:
    print(f"  ⚠️  رابط التواصل مكرر {count} مرة - سنحذف التكرار")
    # امسح المرة الأولى وسيب الأخيرة
    idx = sidebar_content.find('contact_sales')
    # ابحث عن بداية الـ <li> اللي فيها الرابط
    li_start = sidebar_content.rfind('<li', 0, idx)
    li_end = sidebar_content.find('</li>', idx) + 5
    duplicate_block = sidebar_content[li_start:li_end]
    # امسح أول occurrence بس
    sidebar_content = sidebar_content.replace(duplicate_block, '', 1)
    write_file(sidebar_path, sidebar_content)
elif count == 1:
    print("  ✅ رابط التواصل موجود مرة واحدة - تمام")
else:
    print("  ⚠️  رابط التواصل مش موجود في الـ Sidebar")


# ════════════════════════════════════════════════════════════
# 4. إضافة رابط "خطتي" في الـ Sidebar لو مش موجود
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة رابط 'خطتي' في الـ Sidebar...")

sidebar_content = read_file(sidebar_path)

if 'my_plan' not in sidebar_content:
    my_plan_link = """
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'subscriptions:my_plan' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px; font-size:0.85rem;">
                    <i class="bi bi-star"></i>
                    <span>خطتي</span>
                  </a>
                </li>"""

    # نضيفه قبل رابط التواصل
    if 'contact_sales' in sidebar_content:
        contact_idx = sidebar_content.find("{% url 'subscriptions:contact_sales' %}")
        li_start = sidebar_content.rfind('<li', 0, contact_idx)
        old_block = sidebar_content[li_start:]
        sidebar_content = sidebar_content[:li_start] + my_plan_link + '\n' + sidebar_content[li_start:]
        write_file(sidebar_path, sidebar_content)
        print("  ✅ تم إضافة رابط 'خطتي' في الـ Sidebar")
    else:
        print("  ⚠️  مش لاقي مكان مناسب لرابط 'خطتي'")
else:
    print("  ℹ️  رابط 'خطتي' موجود بالفعل")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 14c-fix2 اكتمل!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1. ✅ subscriptions/urls.py - كامل ومرتب
  2. ✅ views ناقصة اتضافت (upgrade_plan, feature_locked, my_subscription)
  3. ✅ Sidebar - خطتي + تواصل معنا

🔗 الروابط المتاحة:
  /subscriptions/              ← Admin Dashboard
  /subscriptions/plans/        ← الخطط
  /subscriptions/my-plan/      ← خطتي
  /subscriptions/contact-sales/← تواصل معنا
  /subscriptions/feature-locked/← ميزة مقفولة

🚀 شغّل السيرفر وتأكد من:
  1. /subscriptions/my-plan/
  2. /subscriptions/contact-sales/
  3. رابط "خطتي" في الـ Sidebar
""")