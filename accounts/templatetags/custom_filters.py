from django import template
register = template.Library()

@register.filter(name="split")
def split_filter(value, delimiter="|"):
    if value:
        return str(value).split(delimiter)
    return []

@register.filter(name="getattr")
def getattr_filter(obj, attr):
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

@register.filter(name="get_item")
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.simple_tag(name="unread_notifications_count")
def unread_notifications_count(user):
    """
    عدد الإشعارات غير المقروءة للموظف الحالي
    """
    try:
        if not user or not user.is_authenticated:
            return 0
        from employees.models import Employee
        from accounts.models import EmployeeNotification
        emp = Employee.all_objects.filter(user=user).first()
        if not emp:
            return 0
        return EmployeeNotification.objects.filter(
            employee=emp,
            is_read=False
        ).count()
    except Exception:
        return 0
