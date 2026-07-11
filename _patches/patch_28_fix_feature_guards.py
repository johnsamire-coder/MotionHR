#!/usr/bin/env python3
"""
Patch 28: Fix Feature Guards + Old Redirects
============================================
- إصلاح subscriptions/helpers.py بالكامل
- تحويل كل redirects من /sub-admin/ إلى /subscriptions/
- دعم aliases للـ feature keys القديمة
- fallback demo features للشركات النشطة
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 28: Fix Feature Guards")
print("=" * 60)

helpers_code = '''"""
subscriptions/helpers.py
مساعدات الاشتراكات والـ Feature Guards
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


# ─────────────────────────────────────────────
# Demo / Fallback Features
# ─────────────────────────────────────────────
DEMO_FEATURES = {
    'employee_management',
    'attendance_tracking',
    'gps_attendance',
    'field_tracking',
    'live_map',
    'location_visits',
    'reports_basic',
    'reports_advanced',
    'excel_export',
    'pdf_export',
    'login_by_employee_code',
    'login_by_phone',
    'leave_management',
    'multi_branch',
    'payroll_basic',
}


# ─────────────────────────────────────────────
# Aliases للـ feature keys القديمة
# ─────────────────────────────────────────────
FEATURE_ALIASES = {
    # Employees
    'employees_management': 'employee_management',
    'employee_management': 'employee_management',

    # Attendance
    'attendance': 'attendance_tracking',
    'attendance_management': 'attendance_tracking',
    'attendance_tracking': 'attendance_tracking',
    'gps': 'gps_attendance',
    'gps_tracking': 'gps_attendance',
    'gps_attendance': 'gps_attendance',

    # Field
    'field_employees_tracking': 'field_tracking',
    'field_tracking': 'field_tracking',
    'live_tracking': 'field_tracking',
    'map_live': 'live_map',
    'live_map': 'live_map',
    'visits': 'location_visits',
    'location_visits': 'location_visits',

    # Reports
    'reports': 'reports_basic',
    'reports_basic': 'reports_basic',
    'reports_advanced': 'reports_advanced',

    # Leaves
    'leaves': 'leave_management',
    'leave_management': 'leave_management',

    # Structure
    'branches_management': 'multi_branch',
    'departments_management': 'multi_branch',
    'multi_branch': 'multi_branch',

    # Payroll
    'payroll': 'payroll_basic',
    'payroll_basic': 'payroll_basic',
}


def normalize_feature_key(feature_key):
    """توحيد أسماء المزايا القديمة والجديدة"""
    if not feature_key:
        return feature_key
    return FEATURE_ALIASES.get(feature_key, feature_key)


def get_company_subscription(request):
    """جلب اشتراك الشركة الحالي"""
    try:
        if not request.user.is_authenticated:
            return None
        if not getattr(request.user, 'company', None):
            return None

        from subscriptions.models import CompanySubscription
        return CompanySubscription.objects.filter(
            company=request.user.company
        ).select_related('plan').first()
    except Exception:
        return None


def is_subscription_valid(subscription):
    """التحقق من صلاحية الاشتراك"""
    if not subscription:
        return False

    try:
        return subscription.is_valid
    except Exception:
        today = timezone.now().date()
        status = getattr(subscription, 'status', '')
        end_date = getattr(subscription, 'end_date', today)
        return status in ['active', 'trial'] and end_date >= today


def get_subscription_features(request, subscription=None):
    """
    جلب المزايا المتاحة
    1) من request.subscription_features
    2) من subscription.all_features
    3) fallback demo features لو الاشتراك صالح لكن فاضي
    """
    features = set()

    # من request
    req_features = getattr(request, 'subscription_features', None)
    if req_features:
        features.update(req_features)

    # من subscription
    if subscription:
        try:
            sub_features = subscription.all_features
            if sub_features:
                features.update(sub_features)
        except Exception:
            pass

    # fallback للديمو
    if not features and subscription and is_subscription_valid(subscription):
        features = set(DEMO_FEATURES)

    # normalize
    normalized = {normalize_feature_key(f) for f in features if f}
    return normalized


def has_feature_access(request, feature_key):
    """هل المستخدم عنده الميزة؟"""
    feature_key = normalize_feature_key(feature_key)

    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return False

    # Super Admin يشوف كل حاجة
    if getattr(request.user, 'role', '') == 'super_admin':
        return True

    subscription = get_company_subscription(request)
    if not is_subscription_valid(subscription):
        return False

    features = get_subscription_features(request, subscription)
    return feature_key in features


def redirect_to_upgrade():
    """توجيه موحد لصفحة الترقية / التواصل"""
    return redirect('/subscriptions/contact-sales/')


def redirect_to_feature_locked(feature_key):
    """توجيه موحد لصفحة الميزة المقفولة"""
    feature_key = normalize_feature_key(feature_key)
    return redirect(f'/subscriptions/feature-locked/?feature={feature_key}')


# ─────────────────────────────────────────────
# Decorators
# ─────────────────────────────────────────────
def feature_required(feature_key):
    """
    Decorator للتحقق من ميزة معينة
    """
    feature_key = normalize_feature_key(feature_key)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'يرجى تسجيل الدخول أولاً')
                return redirect('/login/')

            # Super Admin
            if getattr(request.user, 'role', '') == 'super_admin':
                return view_func(request, *args, **kwargs)

            subscription = get_company_subscription(request)

            if not subscription:
                messages.warning(request, 'لا يوجد اشتراك مرتبط بشركتك. تواصل معنا لتفعيل الخدمة')
                return redirect_to_upgrade()

            if not is_subscription_valid(subscription):
                messages.warning(request, 'اشتراكك منتهي. يرجى التجديد للوصول لهذه الميزة')
                return redirect_to_upgrade()

            features = get_subscription_features(request, subscription)

            # خزّنهم على request لو محتاجهم الـ view
            request.subscription = subscription
            request.subscription_valid = True
            request.subscription_features = features

            if feature_key not in features:
                return redirect_to_feature_locked(feature_key)

            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def require_feature(feature_key):
    """Alias"""
    return feature_required(feature_key)


def plan_feature_required(feature_key):
    """Alias"""
    return feature_required(feature_key)


def subscription_required(view_func):
    """
    Decorator للتحقق فقط من وجود اشتراك صالح
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'يرجى تسجيل الدخول أولاً')
            return redirect('/login/')

        if getattr(request.user, 'role', '') == 'super_admin':
            return view_func(request, *args, **kwargs)

        subscription = get_company_subscription(request)

        if not subscription or not is_subscription_valid(subscription):
            messages.warning(request, 'اشتراكك غير صالح أو منتهي')
            return redirect_to_upgrade()

        request.subscription = subscription
        request.subscription_valid = True
        request.subscription_features = get_subscription_features(request, subscription)

        return view_func(request, *args, **kwargs)
    return wrapped


def company_subscription_required(view_func):
    """Alias"""
    return subscription_required(view_func)


def check_feature_access(request, feature_key):
    """Alias function"""
    return has_feature_access(request, feature_key)
'''

write_file(os.path.join(BASE_DIR, "subscriptions", "helpers.py"), helpers_code)

print("\\n" + "=" * 60)
print("  ✅ Patch 28 اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  1. ✅ redirects القديمة /sub-admin/ اتشالت من الكود
  2. ✅ feature-locked بقى يروح /subscriptions/feature-locked/
  3. ✅ aliases للـ feature keys القديمة:
       employees_management -> employee_management
       attendance -> attendance_tracking
       visits -> location_visits
       reports -> reports_basic
       leaves -> leave_management
  4. ✅ fallback demo features للشركة النشطة
  5. ✅ feature guards اتنضفت

جرب دلوقتي:
  - الموظفين
  - تسجيل الحضور
  - سجلات الحضور
  - الخريطة الحية
  - متابعة الميدانيين
  - الزيارات
""")