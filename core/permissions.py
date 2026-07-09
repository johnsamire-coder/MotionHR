"""
Permissions Helper Functions
دوال مساعدة للصلاحيات الهرمية
"""

from django.db.models import Q


def get_user_employee(user):
    """جلب الـ Employee profile للمستخدم"""
    from employees.models import Employee
    
    if not user or not user.is_authenticated:
        return None
    
    try:
        return Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return None


def get_accessible_employees(user):
    """
    جلب الموظفين اللي المستخدم يقدر يشوفهم حسب دوره
    """
    from employees.models import Employee
    
    if not user or not user.is_authenticated:
        return Employee.objects.none()
    
    # Super Admin و Company Admin و HR Manager يشوفوا الكل
    if user.role in ['super_admin', 'company_admin', 'hr_manager']:
        return Employee.objects.all()
    
    # Manager يشوف نفسه + مرؤوسيه
    if user.role == 'manager':
        my_profile = get_user_employee(user)
        if not my_profile:
            return Employee.objects.none()
        
        ids = my_profile.get_all_subordinates_ids()
        return Employee.objects.filter(id__in=ids)
    
    # Employee يشوف نفسه فقط
    if user.role == 'employee':
        my_profile = get_user_employee(user)
        if not my_profile:
            return Employee.objects.none()
        return Employee.objects.filter(id=my_profile.id)
    
    return Employee.objects.none()


def get_accessible_employee_ids(user):
    """جلب IDs الموظفين اللي يقدر يشوفهم"""
    return list(get_accessible_employees(user).values_list('id', flat=True))


def can_user_edit_employee(user, employee):
    """هل المستخدم يقدر يعدل بيانات موظف معين؟"""
    if not user or not user.is_authenticated:
        return False
    
    # Super Admin و Company Admin و HR Manager يقدروا يعدلوا الكل
    if user.role in ['super_admin', 'company_admin', 'hr_manager']:
        return True
    
    # Manager يقدر يعدل مرؤوسيه بس
    if user.role == 'manager':
        my_profile = get_user_employee(user)
        if my_profile:
            return my_profile.is_manager_of(employee)
    
    # Employee مش يقدر يعدل
    return False


def can_user_delete_employee(user, employee):
    """هل يقدر يحذف؟ - Super Admin و Company Admin بس"""
    if not user or not user.is_authenticated:
        return False
    
    return user.role in ['super_admin', 'company_admin']


def can_user_add_employee(user):
    """هل يقدر يضيف موظف جديد؟"""
    if not user or not user.is_authenticated:
        return False
    
    return user.role in ['super_admin', 'company_admin', 'hr_manager']


def is_admin_or_hr(user):
    """هل هو Admin أو HR؟"""
    if not user or not user.is_authenticated:
        return False
    return user.role in ['super_admin', 'company_admin', 'hr_manager']
