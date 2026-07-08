"""
Mixins للاستخدام في Views
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class CompanyRequiredMixin(LoginRequiredMixin):
    """
    يتطلب:
    1. المستخدم مسجل دخوله
    2. المستخدم مرتبط بشركة
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Super Admin مش محتاج شركة
        if request.user.role == 'super_admin':
            return super().dispatch(request, *args, **kwargs)
        
        # باقي المستخدمين لازم يكون ليهم شركة
        if not request.user.company:
            raise PermissionDenied('يجب أن تكون مرتبطاً بشركة للوصول لهذه الصفحة')
        
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(LoginRequiredMixin):
    """Super Admin فقط"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.role != 'super_admin':
            raise PermissionDenied('هذه الصفحة للـ Super Admin فقط')
        
        return super().dispatch(request, *args, **kwargs)


class CompanyAdminRequiredMixin(CompanyRequiredMixin):
    """Company Admin أو Super Admin"""
    
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['super_admin', 'company_admin']:
            raise PermissionDenied('هذه الصفحة لمديري الشركات فقط')
        
        return result


class HRManagerRequiredMixin(CompanyRequiredMixin):
    """HR Manager أو أعلى"""
    
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        
        allowed_roles = ['super_admin', 'company_admin', 'hr_manager']
        if request.user.role not in allowed_roles:
            raise PermissionDenied('هذه الصفحة لموارد بشرية فقط')
        
        return result