from django.contrib import admin
from .models import RequestCategory, RequestType, EmployeeRequest

@admin.register(RequestCategory)
class RequestCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]

@admin.register(RequestType)
class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "requires_approval", "is_active"]
    list_filter = ["category", "is_active"]

@admin.register(EmployeeRequest)
class EmployeeRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "request_type", "subject", "status", "created_at"]
    list_filter = ["status", "request_type"]


from .models import ApprovalFlow, ApprovalDelegation

@admin.register(ApprovalFlow)
class ApprovalFlowAdmin(admin.ModelAdmin):
    list_display = ["request_type", "step_1_role", "step_2_role", "step_3_role", "escalation_enabled"]

@admin.register(ApprovalDelegation)
class ApprovalDelegationAdmin(admin.ModelAdmin):
    list_display = ["delegator", "delegate", "start_date", "end_date", "is_active", "scope"]
