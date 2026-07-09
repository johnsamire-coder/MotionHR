"""
Template Tags للصلاحيات الهرمية
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def can_edit_employee(context, employee):
    """هل المستخدم الحالي يقدر يعدل هذا الموظف؟"""
    from core.permissions import can_user_edit_employee
    request = context.get('request')
    if not request:
        return False
    return can_user_edit_employee(request.user, employee)


@register.simple_tag(takes_context=True)
def can_delete_employee(context, employee):
    """هل يقدر يحذف؟"""
    from core.permissions import can_user_delete_employee
    request = context.get('request')
    if not request:
        return False
    return can_user_delete_employee(request.user, employee)


@register.simple_tag(takes_context=True)
def can_add_employee(context):
    """هل يقدر يضيف موظف جديد؟"""
    from core.permissions import can_user_add_employee
    request = context.get('request')
    if not request:
        return False
    return can_user_add_employee(request.user)


@register.simple_tag(takes_context=True)
def is_admin_hr(context):
    """هل هو Admin أو HR؟"""
    from core.permissions import is_admin_or_hr
    request = context.get('request')
    if not request:
        return False
    return is_admin_or_hr(request.user)
