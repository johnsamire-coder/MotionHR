from attendance import api_reminders
from attendance import api_employee_profile
from attendance import api_announcements
from attendance import api_attachments
from attendance import api_employee_management
from attendance.api_mobile import mobile_geofence_get, mobile_geofence_set, mobile_fcm_token_register, mobile_fcm_token_delete
from django.urls import path
from .api_employee_management import manager_reset_employee_password, employee_save_location, manager_get_location_report, manager_update_company_info, manager_upload_company_logo, manager_update_employee, manager_company_info, manager_transfer_employee, manager_organization_tree
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
    path('api/mobile/charter/', api_mobile.mobile_charter_get, name='mobile_charter_get'),
    path('api/mobile/charter/accept/', api_mobile.mobile_charter_accept, name='mobile_charter_accept'),
    path('api/mobile/manager/charter/acceptances/', api_mobile.mobile_charter_acceptances, name='mobile_charter_acceptances'),
    path('api/mobile/manager/charter/update/', api_mobile.mobile_charter_update, name='mobile_charter_update'),
    # ─── المرحلة 4.2: الإعلانات ───
    path('api/mobile/announcements/list/', api_announcements.announcements_list),
    path('api/mobile/announcements/mark-read/', api_announcements.announcements_mark_read),
    path('api/mobile/manager/announcements/create/', api_announcements.manager_create_announcement),
    path('api/mobile/manager/announcements/<int:pk>/delete/', api_announcements.manager_delete_announcement),
    path('api/mobile/manager/announcements/<int:pk>/stats/', api_announcements.manager_announcement_stats),

    path('api/mobile/employee/save-location/', employee_save_location),
    path('api/mobile/manager/location-report/', manager_get_location_report),
]

# ═══════════════════════════════════════
# Reports APIs - Batch 1
# ═══════════════════════════════════════
from .api_reports import (
    attendance_monthly_report,
    late_report,
    absence_report,
)

urlpatterns += [
    path('api/mobile/manager/reports/attendance/', attendance_monthly_report, name='report-attendance'),
    path('api/mobile/manager/reports/late/', late_report, name='report-late'),
    path('api/mobile/manager/reports/absence/', absence_report, name='report-absence'),
]

# ═══════════════════════════════════════
# Reports Export APIs - Batch 3
# ═══════════════════════════════════════
from .api_reports import (
    export_report_pdf,
    export_report_excel,
)

urlpatterns += [
    path('api/mobile/manager/reports/export/pdf/', export_report_pdf, name='report-export-pdf'),
    path('api/mobile/manager/reports/export/excel/', export_report_excel, name='report-export-excel'),
]

# ═══════════════════════════════════════

# ═══════════════════════════════════════
# Payroll APIs - Phase 3 (v2)
# ═══════════════════════════════════════
from .api_payroll import (
    payroll_summary,
    payroll_employee_detail,
    payroll_settings,
)

urlpatterns += [
    path('api/mobile/manager/payroll/summary/', payroll_summary, name='payroll-summary'),
    path('api/mobile/manager/payroll/employee/', payroll_employee_detail, name='payroll-employee'),
    path('api/mobile/manager/payroll/settings/', payroll_settings, name='payroll-settings'),

    # ─── المرحلة 7: التذكيرات ───
    path("api/mobile/manager/reminders/trigger/", api_reminders.trigger_reminder),
    path("api/mobile/manager/reminders/settings/", api_reminders.reminder_settings),
    path("api/mobile/employee/profile/", api_employee_profile.my_profile),
    path("api/mobile/employee/documents/", api_employee_profile.my_documents),
    path("api/mobile/employee/movements/", api_employee_profile.my_movements),
    path('api/mobile/employee/summary/', api_employee_profile.my_summary),
    path('api/mobile/manager/employees/', api_employee_profile.manager_employees_list),
    path('api/mobile/manager/employees/<int:emp_id>/profile/', api_employee_profile.manager_employee_profile),
    path('api/mobile/manager/employees/<int:emp_id>/documents/', api_employee_profile.manager_employee_documents),
    path('api/mobile/manager/employees/<int:emp_id>/movements/', api_employee_profile.manager_employee_movements),
    path("api/mobile/attachments/upload/", api_attachments.upload_attachment),
    path("api/mobile/attachments/list/", api_attachments.list_attachments),
    path("api/mobile/attachments/<int:attachment_id>/delete/", api_attachments.delete_attachment),
    path("api/mobile/attachments/<int:attachment_id>/download/", api_attachments.download_attachment),
    path('api/mobile/manager/employees/<int:emp_id>/summary/', api_employee_profile.manager_employee_summary),

    # Phase 8
    path('api/mobile/manager/branches/', api_employee_management.manager_branches),
    path('api/mobile/manager/departments/', api_employee_management.manager_departments),
    path('api/mobile/manager/job-titles/', api_employee_management.manager_job_titles),
    path('api/mobile/manager/employees/simple/', api_employee_management.manager_employees_simple),
    path('api/mobile/manager/employees/create/', api_employee_management.manager_create_employee),

    path('api/mobile/manager/employees/<int:employee_id>/reset-password/', manager_reset_employee_password),
    path('api/mobile/manager/company-info/', manager_company_info),
    path('api/mobile/manager/employees/<int:employee_id>/transfer/', manager_transfer_employee),
    path('api/mobile/manager/organization-tree/', manager_organization_tree),
    path('api/mobile/manager/company-info/update/', manager_update_company_info),
    path('api/mobile/manager/company-info/upload-logo/', manager_upload_company_logo),
]

# ─────────────────────────────────────────────────────────────
# MISSIONS URLs - V1
# ─────────────────────────────────────────────────────────────
from attendance.api_missions import (
    manager_missions_list, manager_create_mission, manager_mission_detail,
    manager_update_mission, manager_cancel_mission, manager_pending_requests,
    manager_approve_request, manager_feedback_dashboard,
    employee_my_missions, employee_respond_mission,
    employee_start_mission, employee_end_mission,
    employee_update_location, employee_upload_attachment,
    employee_request_mission, employee_submit_feedback,
    employee_add_feedback_note, mission_feedback_detail,
    mission_locations_timeline,
)

urlpatterns += [
    # Manager
    path('api/mobile/manager/missions/', manager_missions_list, name='manager_missions_list'),
    path('api/mobile/manager/missions/create/', manager_create_mission, name='manager_create_mission'),
    path('api/mobile/manager/missions/<int:mission_id>/', manager_mission_detail, name='manager_mission_detail'),
    path('api/mobile/manager/missions/<int:mission_id>/update/', manager_update_mission, name='manager_update_mission'),
    path('api/mobile/manager/missions/<int:mission_id>/cancel/', manager_cancel_mission, name='manager_cancel_mission'),
    path('api/mobile/manager/missions/pending-requests/', manager_pending_requests, name='manager_pending_requests'),
    path('api/mobile/manager/missions/requests/<int:request_id>/respond/', manager_approve_request, name='manager_approve_request'),
    path('api/mobile/manager/missions/feedback-dashboard/', manager_feedback_dashboard, name='manager_feedback_dashboard'),

    # Employee
    path('api/mobile/employee/missions/', employee_my_missions, name='employee_my_missions'),
    path('api/mobile/employee/missions/request/', employee_request_mission, name='employee_request_mission'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/respond/', employee_respond_mission, name='employee_respond_mission'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/start/', employee_start_mission, name='employee_start_mission'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/end/', employee_end_mission, name='employee_end_mission'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/update-location/', employee_update_location, name='employee_update_location'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/upload/', employee_upload_attachment, name='employee_upload_attachment'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/locations/', mission_locations_timeline, name='mission_locations_timeline'),

    # Feedback
    path('api/mobile/missions/<int:mission_id>/feedback/', mission_feedback_detail, name='mission_feedback_detail'),
    path('api/mobile/missions/<int:mission_id>/feedback/submit/', employee_submit_feedback, name='employee_submit_feedback'),
    path('api/mobile/missions/<int:mission_id>/feedback/add-note/', employee_add_feedback_note, name='employee_add_feedback_note'),
]

# ─────────────────────────────────────────────────────────────
# MISSIONS Extra URLs - Reassign + Withdraw + Force Cancel
# ─────────────────────────────────────────────────────────────
from attendance.api_missions import (
    manager_reassign_employee, employee_withdraw_request,
    manager_withdraw_requests, manager_respond_withdraw,
    manager_force_cancel_mission,
)

urlpatterns += [
    path('api/mobile/manager/missions/<int:mission_id>/reassign/', manager_reassign_employee, name='manager_reassign_employee'),
    path('api/mobile/manager/missions/<int:mission_id>/force-cancel/', manager_force_cancel_mission, name='manager_force_cancel_mission'),
    path('api/mobile/manager/missions/withdraw-requests/', manager_withdraw_requests, name='manager_withdraw_requests'),
    path('api/mobile/manager/missions/withdraw-requests/<int:assignment_id>/respond/', manager_respond_withdraw, name='manager_respond_withdraw'),
    path('api/mobile/employee/missions/assignments/<int:assignment_id>/withdraw/', employee_withdraw_request, name='employee_withdraw_request'),
]

# ─────────────────────────────────────────────────────────────
# Edit & Cancel Requests/Leaves URLs
# ─────────────────────────────────────────────────────────────
from attendance.api_mobile_requests import (
    mobile_edit_request, mobile_cancel_request,
    mobile_edit_leave, mobile_cancel_leave,
)

urlpatterns += [
    path('api/mobile/my-requests/<int:request_id>/edit/', mobile_edit_request, name='mobile_edit_request'),
    path('api/mobile/my-requests/<int:request_id>/cancel/', mobile_cancel_request, name='mobile_cancel_request'),
    path('api/mobile/my-leaves/<int:leave_id>/edit/', mobile_edit_leave, name='mobile_edit_leave'),
    path('api/mobile/my-leaves/<int:leave_id>/cancel/', mobile_cancel_leave, name='mobile_cancel_leave'),
]

# ─────────────────────────────────────────────────────────────
# Manager/HR: Edit & Cancel Requests/Leaves URLs
# ─────────────────────────────────────────────────────────────
from attendance.api_mobile_requests import (
    manager_edit_request, manager_cancel_request,
    manager_reopen_request, manager_edit_leave,
    manager_cancel_leave,
)

urlpatterns += [
    # Manager/HR - Requests
    path('api/mobile/manager/requests/<int:request_id>/edit/', manager_edit_request, name='manager_edit_request'),
    path('api/mobile/manager/requests/<int:request_id>/cancel/', manager_cancel_request, name='manager_cancel_request'),
    path('api/mobile/manager/requests/<int:request_id>/reopen/', manager_reopen_request, name='manager_reopen_request'),
    # Manager/HR - Leaves
    path('api/mobile/manager/leaves/<int:leave_id>/edit/', manager_edit_leave, name='manager_edit_leave'),
    path('api/mobile/manager/leaves/<int:leave_id>/cancel/', manager_cancel_leave, name='manager_cancel_leave'),
]

# ═══════════════════════════════════════
# Reports APIs - Phase 13 Missing endpoints
# ═══════════════════════════════════════
from .api_reports import (
    requests_report,
    leaves_report,
    work_hours_report,
)

urlpatterns += [
    path('api/mobile/manager/reports/requests/', requests_report, name='report-requests'),
    path('api/mobile/manager/reports/leaves/', leaves_report, name='report-leaves'),
    path('api/mobile/manager/reports/work-hours/', work_hours_report, name='report-work-hours'),
]

# ═══════════════════════════════════════
# Employee Payslip - Self Service
# ═══════════════════════════════════════
from .api_payroll import employee_payslip

urlpatterns += [
    path('api/mobile/employee/payslip/', employee_payslip, name='employee-payslip'),
]

# ═══════════════════════════════════════
# Auto Check-in / Check-out - Phase 14
# ═══════════════════════════════════════
from .api_auto_checkin import auto_check_in, auto_check_out, auto_checkin_status

urlpatterns += [
    path('api/mobile/employee/auto-check-in/', auto_check_in, name='auto-check-in'),
    path('api/mobile/employee/auto-check-out/', auto_check_out, name='auto-check-out'),
    path('api/mobile/employee/auto-checkin-status/', auto_checkin_status, name='auto-checkin-status'),
]

# ═══════════════════════════════════════
# Company Work Policy - Phase 14
# ═══════════════════════════════════════
from .api_company_policy import get_work_policy, save_work_policy

urlpatterns += [
    path('api/mobile/manager/work-policy/', get_work_policy, name='work-policy-get'),
    path('api/mobile/manager/work-policy/save/', save_work_policy, name='work-policy-save'),
]

# ── Shifts Management (Phase 16) ──
from attendance.api_shifts import (
    manager_shifts_list, manager_shift_create, manager_shift_update,
    manager_shift_delete, manager_shift_assign, manager_employee_shifts,
    manager_shift_employees,
)
urlpatterns += [
    path('api/mobile/manager/shifts/', manager_shifts_list),
    path('api/mobile/manager/shifts/create/', manager_shift_create),
    path('api/mobile/manager/shifts/<int:shift_id>/update/', manager_shift_update),
    path('api/mobile/manager/shifts/<int:shift_id>/delete/', manager_shift_delete),
    path('api/mobile/manager/shifts/<int:shift_id>/employees/', manager_shift_employees),
    path('api/mobile/manager/shifts/assign/', manager_shift_assign),
    path('api/mobile/manager/employees/<int:employee_id>/shifts/', manager_employee_shifts),
]

# ══════════════════════════════════════
# Permissions APIs - Sprint 5
# ══════════════════════════════════════
from attendance.api_permissions import (
    list_available_permissions,
    list_roles, create_role, update_role, delete_role,
    assign_role_to_user, remove_role_from_user,
    user_permissions, set_user_override, remove_user_override,
    api_export_permissions,
    company_users_list,
)

urlpatterns += [
    path('api/mobile/manager/permissions/available/', list_available_permissions),
    path('api/mobile/manager/permissions/roles/', list_roles),
    path('api/mobile/manager/permissions/roles/create/', create_role),
    path('api/mobile/manager/permissions/roles/<int:role_id>/update/', update_role),
    path('api/mobile/manager/permissions/roles/<int:role_id>/delete/', delete_role),
    path('api/mobile/manager/permissions/assign-role/', assign_role_to_user),
    path('api/mobile/manager/permissions/remove-role/', remove_role_from_user),
    path('api/mobile/manager/permissions/users/', company_users_list),
    path('api/mobile/manager/permissions/users/<int:user_id>/', user_permissions),
    path('api/mobile/manager/permissions/override/set/', set_user_override),
    path('api/mobile/manager/permissions/override/remove/', remove_user_override),
    path('api/mobile/manager/permissions/export/', api_export_permissions, name='permissions-export'),
]

# ══════════════════════════════════════
# Departments APIs
# ══════════════════════════════════════
from attendance.api_departments import (
    list_departments, add_department, edit_department,
    delete_department, transfer_employees_between_departments,
)

urlpatterns += [
    path('api/mobile/manager/departments/list/', list_departments),
    path('api/mobile/manager/departments/add/', add_department),
    path('api/mobile/manager/departments/<int:dept_id>/edit/', edit_department),
    path('api/mobile/manager/departments/<int:dept_id>/delete/', delete_department),
    path('api/mobile/manager/departments/transfer-employees/', transfer_employees_between_departments),
]

# ══════════════════════════════════════
# Offboarding APIs
# ══════════════════════════════════════
from attendance.api_offboarding import (
    offboard_employee, reactivate_employee, offboarded_employees,
)

urlpatterns += [
    path('api/mobile/manager/offboarding/<int:employee_id>/', offboard_employee),
    path('api/mobile/manager/offboarding/<int:employee_id>/reactivate/', reactivate_employee),
    path('api/mobile/manager/offboarding/list/', offboarded_employees),
]

