from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from employees import views as employee_views
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import (
    CustomPasswordChangeView,
    smart_login_view,
    smart_logout_view,
    dashboard,
    offline_view,
    manifest_view,
    service_worker_view,
    global_search,
)


urlpatterns = [
    path('announcements/', include('accounts.announcement_urls')),

    # Landing Page
    path('', include('landing.urls', namespace='landing')),

    # Admin
    path('admin/', admin.site.urls),

    # Auth
    path('login/',  smart_login_view,  name='login'),
    path('logout/', smart_logout_view, name='logout'),

    # Password Reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/password-reset/done/',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/password-reset-complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # Password Change
    path('password-change/',
         CustomPasswordChangeView.as_view(
             template_name='accounts/password_change.html',
             success_url='/password-change/done/',
         ),
         name='password_change'),

    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html',
         ),
         name='password_change_done'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Search
    path('search/', global_search, name='global_search'),

    # PWA
    path('offline/',      offline_view,        name='offline'),
    path('manifest.json', manifest_view,       name='manifest'),
    path('sw.js',         service_worker_view, name='service_worker'),

    # Apps
    path('accounts/',      include('accounts.urls',      namespace='accounts')),
    path('employees/',     include('employees.urls',     namespace='employees')),
    path('attendance/',    include('attendance.urls',    namespace='attendance')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    path('companies/',     include('companies.urls',     namespace='companies')),
    path('leaves/',        include('leaves.urls',        namespace='leaves')),
    path('requests/',    include('requests_app.urls', namespace='requests_app')),
    path('reports/',       include('reports.urls',       namespace='reports')),

]

# Media + Static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error Handlers
handler404 = 'accounts.views.handler_404'
handler500 = 'accounts.views.handler_500'


# ═════════════════════════════════════════════════════════════
# Patch 49j-Hooks Fix2 — Global Legacy Employee URL Aliases
# الغرض: دعم reverse بالأسماء القديمة غير الـ namespaced
# ═════════════════════════════════════════════════════════════

legacy_employee_urlpatterns = [
    # القائمة
    path('employees/', employee_views.employee_list, name='employee_list'),

    # إضافة
    path('employees/add/', employee_views.employee_add, name='employee_add'),
    path('employees/add/', employee_views.employee_add, name='employee_create'),
    path('employees/add/', employee_views.employee_add, name='add_employee'),

    # التفاصيل
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_profile'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_info'),

    # تعديل
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_update'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='edit_employee'),

    # حذف
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='delete_employee'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_remove'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='remove_employee'),

    # طباعة
    path('employees/print/', employee_views.employee_print, name='employee_print'),
    path('employees/print/', employee_views.employee_print, name='employee_print_all'),
    path('employees/print/', employee_views.employee_print, name='employees_print'),
    path('employees/print/', employee_views.employee_print, name='employees_print_all'),

    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employee_print_detail'),
    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employee_detail_print'),
    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employees_print_detail'),

    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='employee_print_credentials'),
    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='employee_credentials_print'),
    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='print_credentials_view'),

    # حسابات
    path('employees/<int:pk>/create-account/', employee_views.create_account_view, name='create_account_view'),
    path('employees/<int:pk>/deactivate-account/', employee_views.deactivate_account_view, name='deactivate_account_view'),
    path('employees/<int:pk>/reset-password/', employee_views.reset_password_view, name='reset_password_view'),

    # الملف الشامل
    path('employees/<int:pk>/profile/', employee_views.employee_comprehensive_profile, name='employee_comprehensive_profile'),

    # المستندات
    path('employees/<int:pk>/folder/', employee_views.employee_folder, name='employee_folder'),
    path('employees/<int:pk>/folder/upload/', employee_views.employee_folder_upload, name='employee_folder_upload'),
    path('employees/<int:pk>/folder/<int:doc_id>/delete/', employee_views.employee_folder_delete, name='employee_folder_delete'),

    # Self-service
    path('employees/my-balance/', employee_views.my_balance_view, name='my_balance_view'),
    path('employees/my-balance/', employee_views.my_balance_view, name='employee_balance'),
    path('employees/my-deductions/', employee_views.my_deductions_view, name='my_deductions_view'),
    path('employees/my-deductions/', employee_views.my_deductions_view, name='employee_deductions'),

    # APIs / hierarchy
    path('employees/api/search/', employee_views.employee_search_api, name='employee_search_api'),
    path('employees/api/manager-options/', employee_views.employee_manager_options_api, name='manager_options_api'),
    path('employees/hierarchy/', employee_views.job_hierarchy_manage, name='hierarchy_manage'),
]

urlpatterns += legacy_employee_urlpatterns


# ═════════════════════════════════════════════════════════════
# Patch 49j-Z — Global legacy employee route names
# الغرض: دعم reverse('employee_list') وأسماء legacy غير namespaced
# ═════════════════════════════════════════════════════════════

legacy_global_employee_urlpatterns = [
    path('employees/', employee_views.employee_list, name='employee_list'),

    path('employees/add/', employee_views.employee_add, name='employee_add'),
    path('employees/add/', employee_views.employee_add, name='employee_create'),
    path('employees/add/', employee_views.employee_add, name='add_employee'),

    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_profile'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_info'),

    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_update'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='edit_employee'),

    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='delete_employee'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_remove'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='remove_employee'),

    path('employees/print/', employee_views.employee_print, name='employee_print'),
    path('employees/<int:pk>/print/', employee_views.employee_print_detail, name='employee_print_detail'),
    path('employees/<int:pk>/credentials/', employee_views.print_credentials_view, name='print_credentials_view'),

    path('employees/<int:pk>/profile/', employee_views.employee_comprehensive_profile, name='employee_comprehensive_profile'),

    path('employees/<int:pk>/create-account/', employee_views.create_account_view, name='create_account_view'),
    path('employees/<int:pk>/deactivate-account/', employee_views.deactivate_account_view, name='deactivate_account_view'),
    path('employees/<int:pk>/reset-password/', employee_views.reset_password_view, name='reset_password_view'),

    path('employees/my-balance/', employee_views.my_balance_view, name='my_balance_view'),
    path('employees/my-deductions/', employee_views.my_deductions_view, name='my_deductions_view'),

    path('employees/api/search/', employee_views.employee_search_api, name='employee_search_api'),
]

urlpatterns += legacy_global_employee_urlpatterns

