"""
Subscription Helper Functions
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def feature_required(feature_key):
    """
    Decorator للـ Views
    يتحقق إن الميزة متاحة في اشتراك الشركة
    
    مثال:
        @feature_required('continuous_tracking')
        def tracking_page(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Super Admin دايماً يوصل
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            
            # التحقق من الاشتراك
            if not getattr(request, 'subscription_valid', False):
                messages.warning(request, 'اشتراكك منتهي. يرجى التجديد للوصول لهذه الميزة')
                return redirect('subscription_upgrade')
            
            # التحقق من الميزة
            if feature_key not in getattr(request, 'subscription_features', set()):
                messages.info(
                    request,
                    f'هذه الميزة غير متاحة في خطتك الحالية. قم بترقية الخطة للاستفادة منها'
                )
                return redirect('subscription_upgrade')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def has_feature(request, feature_key):
    """التحقق من ميزة (للاستخدام في views)"""
    if hasattr(request.user, 'role') and request.user.role == 'super_admin':
        return True
    return feature_key in getattr(request, 'subscription_features', set())


def get_subscription_status(request):
    """جلب حالة الاشتراك"""
    if not hasattr(request, 'subscription') or not request.subscription:
        return {
            'valid': False,
            'status': 'no_subscription',
            'message': 'لا يوجد اشتراك',
        }
    
    sub = request.subscription
    return {
        'valid': sub.is_valid,
        'status': sub.status,
        'plan_name': sub.plan.name_ar,
        'days_remaining': sub.days_remaining,
        'is_trial': sub.is_trial,
        'is_expired': sub.is_expired,
        'is_grace_period': sub.is_in_grace_period,
    }
