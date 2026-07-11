from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('charter/signature/<int:signature_id>/print/', views.charter_print_signature, name='charter_print_signature'),
    path('charter/<int:charter_id>/acceptance-status/', views.charter_acceptance_status, name='charter_acceptance_status'),
    path('charter/<int:charter_id>/sign/', views.charter_sign, name='charter_sign'),

    # الشركة
    path('settings/', views.company_settings, name='settings'),

    # ميثاق العمل
    path('charter/', views.charter_view, name='charter'),
    path('charter/accept/', views.charter_accept, name='charter_accept'),
    path('charter/manage/', views.charter_manage, name='charter_manage'),
    path('policies/', views.company_policy_manage, name='policies'),

    # الفروع
    path('branches/', views.branches_list, name='branches_list'),
    path('branches/add/', views.branch_add, name='branch_add'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),

    # الإدارات
    path('departments/', views.departments_list, name='departments_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    # الشيفتات
    path('shifts/', views.shifts_list, name='shifts_list'),
    path('shifts/add/', views.shift_add, name='shift_add'),
    path('shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'),
    path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),

    # Workflow
    path('approval-flows/', views.approval_flows_view, name='approval_flows'),
    path('delegations/', views.delegations_view, name='delegations'),
    path('delegations/add/', views.delegation_add, name='delegation_add'),
    path('delegations/<int:pk>/deactivate/', views.delegation_deactivate, name='delegation_deactivate'),

    path('notification-settings/', views.notification_settings_view, name='notification_settings'),
]
