"""
Subscription Template Tags
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def has_feature(context, feature_key):
    """التحقق من ميزة في الـ template"""
    request = context.get('request')
    if not request:
        return False
    
    if hasattr(request.user, 'role') and request.user.role == 'super_admin':
        return True
    
    return feature_key in getattr(request, 'subscription_features', set())


@register.simple_tag(takes_context=True)
def subscription_status(context):
    """جلب حالة الاشتراك"""
    request = context.get('request')
    if not request or not hasattr(request, 'subscription'):
        return None
    return request.subscription


@register.simple_tag(takes_context=True)
def days_remaining(context):
    """الأيام المتبقية"""
    request = context.get('request')
    if not request:
        return 0
    return getattr(request, 'days_remaining', 0)
