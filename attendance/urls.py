from .api_attendance_adjustment import manager_adjust_attendance
from attendance import api_reminders
from attendance import api_employee_profile
from attendance import api_announcements
from attendance import api_attachments
from attendance import api_employee_management
from attendance.api_mobile import mobile_geofence_get, mobile_geofence_set, mobile_fcm_token_register, mobile_fcm_token_delete, mobile_device_register, mobile_device_status, manager_devices_list, manager_device_action
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .api_employee_management import manager_reset_employee_password, employee_save_location, manager_get_location_report, manager_update_company_info, manager_upload_company_logo, manager_update_employee, manager_company_info, manager_transfer_employee, manager_organization_tree, manager_hierarchy_tree
from . import views
from .api_field_visits import (
    field_visit_start,
    field_visit_end,
    field_visits_list,
    field_visit_detail,
    field_visit_types,
)
from .api_work_locations import (
    manager_delete_location,
    manager_assign_employees_to_location,
    hr_pending_locations,
    propose_work_location,
    my_work_locations,
    work_location_detail,
    cancel_pending_location,
    work_location_types,
    manager_pending_locations,
    manager_all_locations,
    approve_work_location,
    reject_work_location,
)
from . import api_mobile
from . import api_mobile_requests
from .api_company_allowance_policy import allowance_policies_list, allowance_policy_detail
from .api_insurance import insurance_policies_list, insurance_policy_detail, employee_insurances
from .api_payroll_cycle import payroll_cycle_list, payroll_cycle_detail
from .api_rules import penalty_list, penalty_detail, bonus_list, bonus_detail, allowance_list, allowance_detail
from .api_leave_rule import leave_rule_list, leave_rule_detail
from .api_tax_policy import tax_policy_list, tax_policy_detail, tax_calculate
from .api_eos_policy import eos_policy_list, eos_policy_detail, eos_calculate
from .api_manual_entries import (
    manual_penalty_list, manual_penalty_detail, manual_penalty_approve, manual_penalty_reject,
    manual_bonus_list, manual_bonus_detail, manual_bonus_approve, manual_bonus_reject,
    manual_allowance_list, manual_allowance_detail, manual_allowance_approve, manual_allowance_reject,
    manual_entries_summary,
)
from .api_general_policies import deduction_policies_list, deduction_policy_detail, bonus_policies_list, bonus_policy_detail

app_name = 'attendance'

urlpatterns = [
    path('api/mobile/manager/attendance/<int:attendance_id>/adjust/', manager_adjust_attendance, name='manager_adjust_attendance'),

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
    path('api/mobile/jwt/token/', TokenObtainPairView.as_view(), name='mobile_jwt_token'),
    path('api/mobile/jwt/refresh/', TokenRefreshView.as_view(), name='mobile_jwt_refresh'),
    path('api/mobile/jwt/verify/', TokenVerifyView.as_view(), name='mobile_jwt_verify'),
    path('api/mobile/location/', api_mobile.mobile_send_location, name='mobile_location'),
    path('api/mobile/attendance/', api_mobile.mobile_attendance_action, name='mobile_attendance'),
    path('api/mobile/status/', api_mobile.mobile_attendance_status, name='mobile_attendance_status'),
    path('api/mobile/history/', api_mobile.mobile_attendance_history, name='mobile_attendance_history'),
    path('api/mobile/change-password/', api_mobile.mobile_change_password, name='mobile_change_password'),

    # Leaves & Requests APIs
    path('api/mobile/leave-types/', api_mobile_requests.mobile_leave_types, name='mobile_leave_types'),
    path('api/mobile/leave-substitutes/', api_mobile_requests.mobile_leave_substitutes, name='mobile_leave_substitutes'),
    path('api/mobile/manager/substitution-summary/', api_mobile_requests.manager_substitution_summary, name='manager_substitution_summary'),
    path('api/mobile/hr/leave-types/', api_mobile_requests.hr_leave_types, name='hr_leave_types'),
    path('api/mobile/hr/create-leave/', api_mobile_requests.hr_create_leave, name='hr_create_leave'),
    path('api/mobile/leave-request/', api_mobile_requests.mobile_leave_request, name='mobile_leave_request'),
    path('api/mobile/leave-recall/create/', api_mobile_requests.create_leave_recall, name='create_leave_recall'),
    path('api/mobile/leave-recall/<int:recall_id>/review/', api_mobile_requests.review_leave_recall, name='review_leave_recall'),
    path('api/mobile/leave-recall/list/', api_mobile_requests.list_leave_recalls, name='list_leave_recalls'),
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
    path('api/mobile/manager/geofence/', mobile_geofence_get, name='mobile_manager_geofence_get'),
    path('api/mobile/manager/geofence/set/', mobile_geofence_set, name='mobile_manager_geofence_set'),
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
    path('api/mobile/manager/announcements/<int:pk>/update/', api_announcements.manager_update_announcement),
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
from .api_disciplinary import (
    disciplinary_rules, disciplinary_rule_detail,
    disciplinary_actions, disciplinary_action_review,
)

from leaves.api_official_holidays import (
    official_holiday_list_create,
    official_holiday_detail,
)
from leaves.api_leave_policy import (
    leave_policy_list_create, leave_policy_detail,
    leave_policy_approve, leave_balance_adjustments,
    apply_leave_policy_to_existing_employees,
)

from .api_attendance_policy import (
    policy_list_create, policy_detail, policy_approve, policy_assign,
)

from .api_payroll import (
    payroll_summary,
    payroll_employee_detail,
    payroll_settings,
    payroll_runs_list,
    payroll_run_create,
    payroll_run_approve,
    payroll_run_detail,
)

urlpatterns += [
    path('api/mobile/manager/attendance-policy/', policy_list_create),
    path('api/mobile/manager/attendance-policy/<int:policy_id>/', policy_detail),
    path('api/mobile/manager/attendance-policy/<int:policy_id>/approve/', policy_approve),
    path('api/mobile/manager/attendance-policy/<int:policy_id>/assign/', policy_assign),

    # Leave Policy
    path('api/mobile/manager/leave-policy/', leave_policy_list_create),
    path('api/mobile/manager/leave-policy/<int:policy_id>/', leave_policy_detail),
    path('api/mobile/manager/leave-policy/<int:policy_id>/approve/', leave_policy_approve),
    path('api/mobile/manager/leave-balance-adjustments/', leave_balance_adjustments),
    path('api/mobile/manager/leave-policy/apply-to-existing/', apply_leave_policy_to_existing_employees),

    # Disciplinary
    path('api/mobile/manager/disciplinary/actions/', disciplinary_actions),
    path('api/mobile/manager/disciplinary/actions/<int:action_id>/review/', disciplinary_action_review),
    path('api/mobile/manager/attendance-policy/<int:policy_id>/disciplinary-rules/', disciplinary_rules),
    path('api/mobile/manager/attendance-policy/<int:policy_id>/disciplinary-rules/<int:rule_id>/', disciplinary_rule_detail),

    path('api/mobile/manager/payroll/summary/', payroll_summary, name='payroll-summary'),
    path('api/mobile/manager/payroll/employee/', payroll_employee_detail, name='payroll-employee'),
    path('api/mobile/manager/payroll/settings/', payroll_settings, name='payroll-settings'),
    path('api/mobile/manager/payroll/runs/', payroll_runs_list, name='payroll-runs-list'),
    path('api/mobile/manager/payroll/run/create/', payroll_run_create, name='payroll-run-create'),
    path('api/mobile/manager/payroll/runs/<int:run_id>/', payroll_run_detail, name='payroll-run-detail'),
    path('api/mobile/manager/payroll/runs/<int:run_id>/approve/', payroll_run_approve, name='payroll-run-approve'),

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
    path('api/mobile/manager/employees/<int:emp_id>/attendance/', api_employee_profile.manager_employee_attendance),
    path('api/mobile/manager/employees/<int:emp_id>/leaves/', api_employee_profile.manager_employee_leaves),
    path('api/mobile/manager/employees/<int:emp_id>/requests/', api_employee_profile.manager_employee_requests),

    # Phase 8
    path('api/mobile/manager/branches/', api_employee_management.manager_branches),
    path('api/mobile/manager/departments/', api_employee_management.manager_departments),
    path('api/mobile/manager/job-titles/', api_employee_management.manager_job_titles),
    path('api/mobile/manager/job-titles/<int:title_id>/', api_employee_management.manager_job_title_detail),
    path('api/mobile/manager/employees/simple/', api_employee_management.manager_employees_simple),
    path('api/mobile/manager/employees/create/', api_employee_management.manager_create_employee),
    path('api/mobile/manager/employees/managers/', api_employee_management.manager_employee_managers),
    path('api/mobile/manager/employees/<int:employee_id>/', api_employee_management.manager_employee_detail),
    path('api/mobile/manager/employees/<int:employee_id>/update/', manager_update_employee),

    path('api/mobile/manager/employees/<int:employee_id>/reset-password/', manager_reset_employee_password),
    path('api/mobile/manager/company-info/', manager_company_info),
    path('api/mobile/manager/employees/<int:employee_id>/transfer/', manager_transfer_employee),
    path('api/mobile/manager/organization-tree/', manager_organization_tree),
    path('api/mobile/manager/hierarchy-tree/', manager_hierarchy_tree),
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
    manager_shift_employees, my_shift, shift_change_requests_list,
    shift_change_request_action, shift_override_create, shift_override_delete, shift_override_list,
    employee_effective_shift, partial_checkout, resume_checkin, today_sessions,
    manager_shift_assignments_list, manager_shift_assignment_update,
    manager_shift_assignment_delete,
    rotation_list_create, rotation_detail, rotation_assign, rotation_assignments_list, rotation_assignment_delete,
)
urlpatterns += [
    path('api/mobile/manager/shifts/', manager_shifts_list),
    path('api/mobile/manager/shifts/create/', manager_shift_create),
    path('api/mobile/manager/shifts/<int:shift_id>/update/', manager_shift_update),
    path('api/mobile/manager/shifts/<int:shift_id>/delete/', manager_shift_delete),
    path('api/mobile/manager/shifts/<int:shift_id>/employees/', manager_shift_employees),
    path('api/mobile/manager/shifts/assign/', manager_shift_assign),
    path('api/mobile/manager/shifts/assignments/', manager_shift_assignments_list),
    path('api/mobile/manager/shifts/assignments/<int:assignment_id>/update/', manager_shift_assignment_update),
    path('api/mobile/manager/shifts/assignments/<int:assignment_id>/delete/', manager_shift_assignment_delete),
    path('api/mobile/manager/employees/<int:employee_id>/shifts/', manager_employee_shifts),
    path('api/mobile/manager/employees/<int:employee_id>/effective-shift/', employee_effective_shift),
    path('api/mobile/manager/shifts/change-requests/', shift_change_requests_list),
    path('api/mobile/manager/shifts/change-requests/<int:request_id>/action/', shift_change_request_action),
    path('api/mobile/manager/shifts/overrides/', shift_override_list),
    path('api/mobile/manager/rotations/', rotation_list_create),
    path('api/mobile/manager/rotations/<int:rotation_id>/', rotation_detail),
    path('api/mobile/manager/rotations/<int:rotation_id>/assign/', rotation_assign),
    path('api/mobile/manager/rotations/<int:rotation_id>/assignments/', rotation_assignments_list),
    path('api/mobile/manager/rotations/assignments/<int:assignment_id>/delete/', rotation_assignment_delete),
    path('api/mobile/manager/shifts/override/create/', shift_override_create),
    path('api/mobile/manager/shifts/override/<int:override_id>/delete/', shift_override_delete),
    path('api/mobile/my-shift/', my_shift),
    path('api/mobile/employee/my-shift/', my_shift),
    path('api/mobile/employee/partial-checkout/', partial_checkout),
    path('api/mobile/employee/resume-checkin/', resume_checkin),
    path('api/mobile/employee/today-sessions/', today_sessions),
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
    my_permissions,
    default_role_permissions,
    set_role_default_override,
    target_permissions_summary,
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
    path('api/mobile/permissions/my/', my_permissions),
    path('api/mobile/manager/permissions/defaults/', default_role_permissions),
    path('api/mobile/manager/permissions/override/bulk/', set_role_default_override),
    path('api/mobile/manager/permissions/summary/', target_permissions_summary),
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
    toggle_employee_status, delete_employee_api, offboard_employee_web,
)

urlpatterns += [
    path('api/mobile/manager/offboarding/<int:employee_id>/', offboard_employee),
    path('api/mobile/manager/offboarding/<int:employee_id>/reactivate/', reactivate_employee),
    path('api/mobile/manager/offboarding/list/', offboarded_employees),
    path('api/mobile/manager/employees/<int:employee_id>/toggle-status/', toggle_employee_status),
    path('api/mobile/manager/employees/<int:employee_id>/delete/', delete_employee_api),
    path('api/mobile/manager/offboarding/<int:employee_id>/web/', offboard_employee_web),
]



# ══════════════════════════════════════
# Permission Balance APIs
# ══════════════════════════════════════
from attendance.api_permissions_balance import (
    my_permission_balance,
    employee_permission_balance,
    grant_extra_permission,
    rollback_late,
)

urlpatterns += [
    path('api/mobile/employee/permission-balance/', my_permission_balance),
    path('api/mobile/manager/employees/<int:employee_id>/permission-balance/', employee_permission_balance),
    path('api/mobile/manager/employees/<int:employee_id>/permission-grant/', grant_extra_permission),
    path('api/mobile/manager/employees/<int:employee_id>/permission-rollback/', rollback_late),
]

from .api_shifts import (
    flex_adjustments_list,
    flex_adjustment_review,
    employee_flex_adjustments,
)

urlpatterns += [
    path('api/mobile/manager/flex-adjustments/', flex_adjustments_list, name='flex-adjustments-list'),
    path('api/mobile/manager/flex-adjustments/<int:adjustment_id>/review/', flex_adjustment_review, name='flex-adjustment-review'),
    path('api/mobile/manager/employees/<int:emp_id>/flex-adjustments/', employee_flex_adjustments, name='employee-flex-adjustments'),
]

from .api_reports import (
    payroll_report,
    permissions_report,
    daily_attendance_report,
    eos_report,
    eos_export_excel,
    eos_export_pdf,
    reimbursements_report, reimbursements_export_excel, reimbursements_export_pdf,
    bank_transfer_report, bank_transfer_export_excel, bank_transfer_export_pdf,
    insurance_report, insurance_export_excel, insurance_export_pdf,
    tax_report, tax_export_excel, tax_export_pdf,
    turnover_report, turnover_export_excel, turnover_export_pdf,
    branch_comparison_report, branch_comparison_export_excel, branch_comparison_export_pdf,
    contracts_expiry_report, contracts_expiry_export_excel, contracts_expiry_export_pdf,
    loans_advances_report, loans_advances_export_excel, loans_advances_export_pdf,
    missions_performance_report, missions_performance_export_excel, missions_performance_export_pdf,
    executive_dashboard_report, executive_dashboard_export_excel, executive_dashboard_export_pdf,
    unified_dashboard,
)

urlpatterns += [
    path('api/mobile/manager/reports/payroll/', payroll_report, name='reports-payroll'),
    path('api/mobile/manager/reports/permissions/', permissions_report, name='reports-permissions'),
    path('api/mobile/manager/reports/daily-attendance/', daily_attendance_report, name='reports-daily-attendance'),
    path('api/mobile/manager/reports/eos/', eos_report, name='reports-eos'),
    path('api/mobile/manager/reports/eos/export/', eos_export_excel, name='reports-eos-export'),
    path('api/mobile/manager/reports/eos/export/pdf/', eos_export_pdf, name='reports-eos-export-pdf'),

    # Reimbursements
    path('api/mobile/manager/reports/reimbursements/', reimbursements_report),
    path('api/mobile/manager/reports/reimbursements/export/', reimbursements_export_excel),
    path('api/mobile/manager/reports/reimbursements/export/pdf/', reimbursements_export_pdf),

    # Bank Transfer
    path('api/mobile/manager/reports/bank-transfer/', bank_transfer_report),
    path('api/mobile/manager/reports/bank-transfer/export/', bank_transfer_export_excel),
    path('api/mobile/manager/reports/bank-transfer/export/pdf/', bank_transfer_export_pdf),

    # Insurance
    path('api/mobile/manager/reports/insurance/', insurance_report),
    path('api/mobile/manager/reports/insurance/export/', insurance_export_excel),
    path('api/mobile/manager/reports/insurance/export/pdf/', insurance_export_pdf),

    # Tax
    path('api/mobile/manager/reports/tax/', tax_report),
    path('api/mobile/manager/reports/tax/export/', tax_export_excel),
    path('api/mobile/manager/reports/tax/export/pdf/', tax_export_pdf),

    # Turnover
    path('api/mobile/manager/reports/turnover/', turnover_report),
    path('api/mobile/manager/reports/turnover/export/', turnover_export_excel),
    path('api/mobile/manager/reports/turnover/export/pdf/', turnover_export_pdf),

    # Branch Comparison
    path('api/mobile/manager/reports/branch-comparison/', branch_comparison_report),
    path('api/mobile/manager/reports/branch-comparison/export/', branch_comparison_export_excel),
    path('api/mobile/manager/reports/branch-comparison/export/pdf/', branch_comparison_export_pdf),

    # Contracts Expiry
    path('api/mobile/manager/reports/contracts-expiry/', contracts_expiry_report),
    path('api/mobile/manager/reports/contracts-expiry/export/', contracts_expiry_export_excel),
    path('api/mobile/manager/reports/contracts-expiry/export/pdf/', contracts_expiry_export_pdf),

    # Loans & Advances
    path('api/mobile/manager/reports/loans-advances/', loans_advances_report),
    path('api/mobile/manager/reports/loans-advances/export/', loans_advances_export_excel),
    path('api/mobile/manager/reports/loans-advances/export/pdf/', loans_advances_export_pdf),

    # Missions Performance
    path('api/mobile/manager/reports/missions-performance/', missions_performance_report),
    path('api/mobile/manager/reports/missions-performance/export/', missions_performance_export_excel),
    path('api/mobile/manager/reports/missions-performance/export/pdf/', missions_performance_export_pdf),

    # Executive Dashboard
    path('api/mobile/manager/reports/executive-dashboard/', executive_dashboard_report),
    path('api/mobile/manager/reports/executive-dashboard/export/', executive_dashboard_export_excel),
    path('api/mobile/manager/reports/executive-dashboard/export/pdf/', executive_dashboard_export_pdf),
]

from .api_reports import (
    leaves_report_enhanced,
    shifts_report,
    location_tracking_report,
)

urlpatterns += [
    path('api/mobile/manager/reports/leaves-enhanced/', leaves_report_enhanced, name='reports-leaves-enhanced'),
    path('api/mobile/manager/reports/shifts/', shifts_report, name='reports-shifts'),
    path('api/mobile/manager/reports/location-tracking/', location_tracking_report, name='location-tracking-report'),

    # ═══════════════════════════════════════════════════
    # Field Visits Mobile APIs (زيارات ميدانية بدون موافقات)
    # ═══════════════════════════════════════════════════
    path('api/mobile/field-visits/', field_visits_list, name='field_visits_list'),
    path('api/mobile/field-visits/types/', field_visit_types, name='field_visit_types'),
    path('api/mobile/field-visits/start/', field_visit_start, name='field_visit_start'),
    path('api/mobile/field-visits/<int:visit_id>/', field_visit_detail, name='field_visit_detail'),
    path('api/mobile/field-visits/end/<int:visit_id>/', field_visit_end, name='field_visit_end'),


    # ═══════════════════════════════════════════════════
    # Work Locations APIs (Multi-Site System)
    # ═══════════════════════════════════════════════════
    # Employee endpoints
    path('api/mobile/work-locations/', my_work_locations, name='my_work_locations'),
    path('api/mobile/work-locations/types/', work_location_types, name='work_location_types'),
    path('api/mobile/work-locations/propose/', propose_work_location, name='propose_work_location'),
    path('api/mobile/work-locations/<int:location_id>/', work_location_detail, name='work_location_detail'),
    path('api/mobile/work-locations/<int:location_id>/cancel/', cancel_pending_location, name='cancel_pending_location'),
    
    # Manager/HR endpoints
    path('api/mobile/manager/work-locations/', manager_all_locations, name='manager_all_locations'),
    path('api/mobile/manager/work-locations/pending/', manager_pending_locations, name='manager_pending_locations'),
    path('api/mobile/manager/work-locations/<int:location_id>/approve/', approve_work_location, name='approve_work_location'),
    path('api/mobile/manager/work-locations/<int:location_id>/reject/', reject_work_location, name='reject_work_location'),
    path('api/mobile/manager/work-locations/<int:location_id>/delete/', manager_delete_location),
    path('api/mobile/manager/work-locations/<int:location_id>/assign-employees/', manager_assign_employees_to_location),
    # ═══════════════════════════════════════════════════
    # Company Allowance Policies (بدلات عامة)
    # ═══════════════════════════════════════════════════
    path('api/mobile/manager/allowance-policies/', allowance_policies_list, name='allowance_policies_list'),
    path('api/mobile/manager/allowance-policies/<int:policy_id>/', allowance_policy_detail, name='allowance_policy_detail'),

    # Insurance Policies (Social + Medical)
    path('api/mobile/manager/insurance-policies/', insurance_policies_list, name='insurance_policies_list'),
    path('api/mobile/manager/insurance-policies/<int:policy_id>/', insurance_policy_detail, name='insurance_policy_detail'),
    path('api/mobile/manager/employees/<int:employee_id>/insurances/', employee_insurances, name='employee_insurances'),

    # Payroll Cycle Policies
    path('api/mobile/manager/payroll-cycle-policies/', payroll_cycle_list, name='payroll_cycle_list'),
    path('api/mobile/manager/payroll-cycle-policies/<int:policy_id>/', payroll_cycle_detail, name='payroll_cycle_detail'),
    # Rules (Penalty + Bonus + Allowance) - New with Tiers
    path('api/mobile/manager/rules/penalty/', penalty_list, name='penalty_list'),
    path('api/mobile/manager/rules/penalty/<int:rule_id>/', penalty_detail, name='penalty_detail'),
    path('api/mobile/manager/rules/bonus/', bonus_list, name='bonus_list'),
    path('api/mobile/manager/rules/bonus/<int:rule_id>/', bonus_detail, name='bonus_detail'),
    path('api/mobile/manager/rules/allowance/', allowance_list, name='allowance_list'),
    path('api/mobile/manager/rules/allowance/<int:rule_id>/', allowance_detail, name='allowance_detail'),
    # Leave Rules
    path('api/mobile/manager/rules/leave/', leave_rule_list, name='leave_rule_list'),
    path('api/mobile/manager/rules/leave/<int:rule_id>/', leave_rule_detail, name='leave_rule_detail'),
    # Manual Entries
    path('api/mobile/manager/entries/summary/', manual_entries_summary, name='manual_entries_summary'),
    path('api/mobile/manager/entries/penalty/', manual_penalty_list, name='manual_penalty_list'),
    path('api/mobile/manager/entries/penalty/<int:entry_id>/', manual_penalty_detail, name='manual_penalty_detail'),
    path('api/mobile/manager/entries/penalty/<int:entry_id>/approve/', manual_penalty_approve, name='manual_penalty_approve'),
    path('api/mobile/manager/entries/penalty/<int:entry_id>/reject/', manual_penalty_reject, name='manual_penalty_reject'),
    path('api/mobile/manager/entries/bonus/', manual_bonus_list, name='manual_bonus_list'),
    path('api/mobile/manager/entries/bonus/<int:entry_id>/', manual_bonus_detail, name='manual_bonus_detail'),
    path('api/mobile/manager/entries/bonus/<int:entry_id>/approve/', manual_bonus_approve, name='manual_bonus_approve'),
    path('api/mobile/manager/entries/bonus/<int:entry_id>/reject/', manual_bonus_reject, name='manual_bonus_reject'),
    path('api/mobile/manager/entries/allowance/', manual_allowance_list, name='manual_allowance_list'),
    path('api/mobile/manager/entries/allowance/<int:entry_id>/', manual_allowance_detail, name='manual_allowance_detail'),
    path('api/mobile/manager/entries/allowance/<int:entry_id>/approve/', manual_allowance_approve, name='manual_allowance_approve'),
    path('api/mobile/manager/entries/allowance/<int:entry_id>/reject/', manual_allowance_reject, name='manual_allowance_reject'),
    # Tax Policy
    path('api/mobile/manager/tax/policies/', tax_policy_list, name='tax_policy_list'),
    path('api/mobile/manager/tax/policies/<int:policy_id>/', tax_policy_detail, name='tax_policy_detail'),
    path('api/mobile/manager/tax/calculate/', tax_calculate, name='tax_calculate'),
    # End of Service Policy
    path('api/mobile/manager/eos/policies/', eos_policy_list, name='eos_policy_list'),
    path('api/mobile/manager/eos/policies/<int:policy_id>/', eos_policy_detail, name='eos_policy_detail'),
    path('api/mobile/manager/eos/calculate/', eos_calculate, name='eos_calculate'),






    # ═══════════════════════════════════════════════════
    # General Deduction Policies (خصومات عامة)
    # ═══════════════════════════════════════════════════
    path('api/mobile/manager/deduction-policies/', deduction_policies_list, name='deduction_policies_list'),
    path('api/mobile/manager/deduction-policies/<int:policy_id>/', deduction_policy_detail, name='deduction_policy_detail'),

    # ═══════════════════════════════════════════════════
    # General Bonus Policies (مكافآت عامة)
    # ═══════════════════════════════════════════════════
    path('api/mobile/manager/bonus-policies/', bonus_policies_list, name='bonus_policies_list'),
    path('api/mobile/manager/bonus-policies/<int:policy_id>/', bonus_policy_detail, name='bonus_policy_detail'),

    # ═══════════════════════════════════════════════════
    # Official Holidays (الإجازات الرسمية)
    # ═══════════════════════════════════════════════════
    path('api/mobile/manager/official-holidays/', official_holiday_list_create, name='official_holiday_list_create'),
    path('api/mobile/manager/official-holidays/<int:holiday_id>/', official_holiday_detail, name='official_holiday_detail'),
    path('api/mobile/manager/dashboard/', unified_dashboard, name='unified-dashboard'),

    # ═══════════════════════════════════════════════════
    # Device Approval Workflow
    # ═══════════════════════════════════════════════════
    path('api/mobile/device/register/', mobile_device_register, name='mobile_device_register'),
    path('api/mobile/device/status/', mobile_device_status, name='mobile_device_status'),
    path('api/mobile/manager/devices/', manager_devices_list, name='manager_devices_list'),
    path('api/mobile/manager/devices/<int:device_id>/action/', manager_device_action, name='manager_device_action'),
]
