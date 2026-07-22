from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   (request.user.role == 'super_admin' or request.user.is_superuser))

class IsCompanyAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        return request.user.is_superuser or request.user.role in ['super_admin', 'company_admin']

class IsHRManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        return request.user.is_superuser or request.user.role in ['super_admin', 'company_admin', 'hr_manager']

class IsManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        return request.user.is_superuser or request.user.role in ['super_admin', 'company_admin', 'hr_manager', 'manager']
