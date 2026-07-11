from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('<int:pk>/folder/<int:doc_id>/delete/', views.employee_folder_delete, name='folder_delete'),
    path('<int:pk>/folder/upload/', views.employee_folder_upload, name='folder_upload'),
    path('<int:pk>/folder/', views.employee_folder, name='folder'),
    path('<int:pk>/profile/', views.employee_comprehensive_profile, name='comprehensive_profile'),
    path('api/search/', views.employee_search_api, name='search_api'),
    path('api/manager-options/', views.employee_manager_options_api, name='manager_options_api'),
    path('hierarchy/', views.job_hierarchy_manage, name='hierarchy_manage'),

    path('add/', views.employee_add, name='add'),
    path('print/', views.employee_print, name='print_all'),
    path('my-balance/', views.my_balance_view, name='my_balance'),
    path('my-deductions/', views.my_deductions_view, name='my_deductions'),

    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/delete/', views.employee_delete, name='delete'),
    path('<int:pk>/print/', views.employee_print_detail, name='print_detail'),
    path('<int:pk>/credentials/', views.print_credentials_view, name='print_credentials'),
    path('<int:pk>/create-account/', views.create_account_view, name='create_account'),
    path('<int:pk>/deactivate-account/', views.deactivate_account_view, name='deactivate_account'),
    path('<int:pk>/reset-password/', views.reset_password_view, name='reset_password'),
    path('<int:pk>/', views.employee_detail, name='detail'),

    path('', views.employee_list, name='list'),
]


# ═════════════════════════════════════════════════════════════
# Patch 49j-Z — Legacy employee route names (namespaced aliases)
# الغرض: دعم reverse('employees:employee_list') وأسماء legacy داخل namespace
# ═════════════════════════════════════════════════════════════

legacy_employee_urlpatterns = [
    path('', views.employee_list, name='employee_list'),

    path('add/', views.employee_add, name='employee_add'),
    path('add/', views.employee_add, name='employee_create'),
    path('add/', views.employee_add, name='add_employee'),

    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('<int:pk>/', views.employee_detail, name='employee_profile'),
    path('<int:pk>/', views.employee_detail, name='employee_info'),

    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('<int:pk>/edit/', views.employee_edit, name='employee_update'),
    path('<int:pk>/edit/', views.employee_edit, name='edit_employee'),

    path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('<int:pk>/delete/', views.employee_delete, name='delete_employee'),
    path('<int:pk>/delete/', views.employee_delete, name='employee_remove'),
    path('<int:pk>/delete/', views.employee_delete, name='remove_employee'),

    path('print/', views.employee_print, name='employee_print'),
    path('print/', views.employee_print, name='employee_print_all'),
    path('print/', views.employee_print, name='employees_print'),
    path('print/', views.employee_print, name='employees_print_all'),

    path('<int:pk>/print/', views.employee_print_detail, name='employee_print_detail'),
    path('<int:pk>/print/', views.employee_print_detail, name='employee_detail_print'),
    path('<int:pk>/print/', views.employee_print_detail, name='employees_print_detail'),

    path('<int:pk>/credentials/', views.print_credentials_view, name='employee_print_credentials'),
    path('<int:pk>/credentials/', views.print_credentials_view, name='employee_credentials_print'),
    path('<int:pk>/credentials/', views.print_credentials_view, name='print_credentials_view'),

    path('<int:pk>/create-account/', views.create_account_view, name='create_account_view'),
    path('<int:pk>/deactivate-account/', views.deactivate_account_view, name='deactivate_account_view'),
    path('<int:pk>/reset-password/', views.reset_password_view, name='reset_password_view'),

    path('<int:pk>/profile/', views.employee_comprehensive_profile, name='employee_comprehensive_profile'),

    path('<int:pk>/folder/', views.employee_folder, name='employee_folder'),
    path('<int:pk>/folder/upload/', views.employee_folder_upload, name='employee_folder_upload'),
    path('<int:pk>/folder/<int:doc_id>/delete/', views.employee_folder_delete, name='employee_folder_delete'),

    path('my-balance/', views.my_balance_view, name='my_balance_view'),
    path('my-balance/', views.my_balance_view, name='employee_balance'),
    path('my-deductions/', views.my_deductions_view, name='my_deductions_view'),
    path('my-deductions/', views.my_deductions_view, name='employee_deductions'),

    path('api/search/', views.employee_search_api, name='employee_search_api'),
    path('api/manager-options/', views.employee_manager_options_api, name='manager_options_api'),
    path('hierarchy/', views.job_hierarchy_manage, name='hierarchy_manage'),
]

urlpatterns += legacy_employee_urlpatterns

