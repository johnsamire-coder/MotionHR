"""
Middleware للتحكم في Multi-tenant
"""

import threading

_thread_local = threading.local()


def get_current_company():
    return getattr(_thread_local, 'company', None)


def get_current_user():
    return getattr(_thread_local, 'user', None)


def set_current_company(company):
    _thread_local.company = company


def set_current_user(user):
    _thread_local.user = user


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
            
            if hasattr(request.user, 'company') and request.user.company:
                set_current_company(request.user.company)
                request.current_company = request.user.company
            else:
                set_current_company(None)
                request.current_company = None
        else:
            set_current_user(None)
            set_current_company(None)
            request.current_company = None
        
        response = self.get_response(request)
        
        set_current_user(None)
        set_current_company(None)
        
        return response

class CurrentEmployeeMiddleware:
    """
    Middleware يضيف employee profile للـ request
    عشان نقدر نستخدمه في الـ views و templates
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.current_employee = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from employees.models import Employee
                request.current_employee = Employee.objects.filter(user=request.user).first()
            except Exception:
                pass
        
        response = self.get_response(request)
        return response
