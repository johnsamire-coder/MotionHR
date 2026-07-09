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


class SubscriptionMiddleware:
    """
    Middleware للتحقق من اشتراك الشركة
    يضيف subscription info للـ request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.subscription = None
        request.subscription_features = set()
        request.subscription_valid = False
        request.days_remaining = 0
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Super Admin عنده كل الصلاحيات
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                request.subscription_valid = True
                request.subscription_features = self._all_features()
            else:
                # جلب اشتراك الشركة
                if hasattr(request.user, 'company') and request.user.company:
                    try:
                        from subscriptions.models import CompanySubscription
                        sub = CompanySubscription.objects.filter(
                            company=request.user.company
                        ).select_related('plan').first()
                        
                        if sub:
                            request.subscription = sub
                            request.subscription_valid = sub.is_valid
                            request.days_remaining = sub.days_remaining
                            if sub.is_valid:
                                request.subscription_features = sub.all_features
                    except Exception:
                        pass
        
        response = self.get_response(request)
        return response
    
    def _all_features(self):
        """كل الميزات المتاحة (للـ Super Admin)"""
        try:
            from subscriptions.models import FeatureFlag
            return set(FeatureFlag.objects.filter(is_active=True).values_list('key', flat=True))
        except Exception:
            return set()
