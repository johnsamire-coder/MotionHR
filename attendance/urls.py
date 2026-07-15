from attendance.api_mobile import mobile_geofence_get, mobile_geofence_set, mobile_fcm_token_register, mobile_fcm_token_delete
from django.urls import path
from . import views
from . import api_mobile
from . import api_mobile_requests

app_name = 'attendance'

urlpatterns = [
    # سجلات الحضور
    path('check-in/', views.smart_check_in_page, name='check_in'),
    path('', views.attendance_list, name='list'),
    
    # Check-in/out
    path('check-in/', views.check_in_page, name='check_in_old'),
    path('api/check-in/', views.policy_api_check_in, name='api_check_in'),
    path('api/check-out/', views.policy_api_check_out, name='api_check_out'),
    
    # زيارات المواقع
    path('visits/', views.visits_list, name='visits'),
    path('visits/add/', views.field_visit_add_page, name='visit_add'),
    
    # الخريطة والتتبع
    path('map/', views.live_map, name='live_map'),
    path('api/live-locations/', views.api_live_locations, name='api_live_locations'),
    path('api/employee-route/<int:employee_id>/', views.api_employee_route, name='api_employee_route'),
    
    # التتبع المستمر
    path('tracking/', views.tracking_page, name='tracking'),
    path('api/track/', views.api_track_location, name='api_track'),
    path('tracking/employee/<int:employee_id>/', views.employee_tracking_detail, name='tracking_detail'),
    
    # متابعة الموظفين للمدير
    path('monitor/', views.field_employees_monitor, name='monitor'),
    path('api/monitor/', views.api_monitor_data, name='api_monitor'),


    # ── Compatibility Aliases ─────────────────────
    path('', views.attendance_list, name='attendance_list'),
    path('check-in/', views.check_in_page, name='check_in_page_old'),
    path('visits/', views.visits_list, name='visits_list'),
    path('tracking/', views.tracking_page, name='tracking_page'),
    path('tracking/employee/<int:employee_id>/', views.employee_tracking_detail, name='employee_tracking_detail'),
    path('monitor/', views.field_employees_monitor, name='field_employees_monitor'),
    path('api/track/', views.api_track_location, name='api_track_location'),
    path('api/monitor/', views.api_monitor_data, name='api_monitor_data'),

    # Late notifications
    path('late-notifications/', views.late_notifications_list, name='late_notifications'),
    path('late-notifications/<int:pk>/', views.late_notification_detail, name='late_notification_detail'),
    path('my-warnings/', views.my_warnings_view, name='my_warnings'),

    # Schedule
    path('schedule/', views.schedule_week_view, name='schedule_week'),
    path('schedule/assignment/', views.assignment_add, name='assignment_add'),

    # Stealth tracking
    path('stealth-manage/', views.stealth_tracking_manage, name='stealth_manage'),
    path('stealth-alerts/', views.stealth_tracking_alerts, name='stealth_alerts'),

    path('api/stealth-location/', views.api_stealth_location, name='api_stealth_location'),

    path('<int:pk>/override/', views.attendance_override, name='override'),

    # Mobile App APIs
    path('api/mobile/login/', api_mobile.mobile_login, name='mobile_login'),
    path('api/mobile/location/', api_mobile.mobile_send_location, name='mobile_location'),
    path('api/mobile/attendance/', api_mobile.mobile_attendance_action, name='mobile_attendance'),
    path('api/mobile/status/', api_mobile.mobile_attendance_status, name='mobile_attendance_status'),
    path('api/mobile/history/', api_mobile.mobile_attendance_history, name='mobile_attendance_history'),
    path('api/mobile/change-password/', api_mobile.mobile_change_password, name='mobile_change_password'),

    # Leaves & Requests APIs
    path('api/mobile/leave-types/', api_mobile_requests.mobile_leave_types, name='mobile_leave_types'),
    path('api/mobile/leave-request/', api_mobile_requests.mobile_leave_request, name='mobile_leave_request'),
    path('api/mobile/my-leaves/', api_mobile_requests.mobile_my_leaves, name='mobile_my_leaves'),
    path('api/mobile/request-types/', api_mobile_requests.mobile_request_types, name='mobile_request_types'),
    path('api/mobile/submit-request/', api_mobile_requests.mobile_submit_request, name='mobile_submit_request'),
    path('api/mobile/my-requests/', api_mobile_requests.mobile_my_requests, name='mobile_my_requests'),

    # Manager APIs
    path('api/mobile/manager/pending/', api_mobile_requests.mobile_manager_pending, name='mobile_manager_pending'),
    path('api/mobile/manager/action/', api_mobile_requests.mobile_manager_action, name='mobile_manager_action'),
    path('api/mobile/manager/attendance/', api_mobile_requests.mobile_manager_employees_attendance, name='mobile_manager_attendance'),
    path('api/mobile/manager/live-locations/', api_mobile_requests.mobile_manager_live_locations, name='mobile_manager_live_locations'),
    path('api/mobile/manager/route/', api_mobile_requests.mobile_manager_employee_route, name='mobile_manager_employee_route'),
    path('api/mobile/geofence/', mobile_geofence_get, name='mobile_geofence_get'),
    path('api/mobile/geofence/set/', mobile_geofence_set, name='mobile_geofence_set'),
    path('api/mobile/fcm-token/', mobile_fcm_token_register, name='mobile_fcm_token_register'),
    path('api/mobile/fcm-token/delete/', mobile_fcm_token_delete, name='mobile_fcm_token_delete'),
    path('api/mobile/notifications/', api_mobile.mobile_notifications_list, name='mobile_notifications_list'),
    path('api/mobile/notifications/mark-read/', api_mobile.mobile_notifications_mark_read, name='mobile_notifications_mark_read'),
]
