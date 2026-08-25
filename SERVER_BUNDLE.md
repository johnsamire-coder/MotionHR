# MotionHR — Server Bundle


======================================================================
## FILE: /var/www/motionhr/MASTER_DOCS.md
======================================================================

```

# MotionHR — Master Documentation
# تاريخ الإنشاء: 2026-08-15
# النسخة: 1.0.0 Final

═══════════════════════════════════════════════════════════
1. معلومات المشروع
═══════════════════════════════════════════════════════════

الاسم: MotionHR
النوع: SaaS — نظام HR متكامل للشركات المصرية والعربية
صاحب المشروع: بوب (جون سمير)

الدومين الرئيسي:   https://jssolutions-eg.com       ← Backend / API
دومين الويب:       https://app.jssolutions-eg.com    ← Web App
السيرفر:           Hostinger VPS — Ubuntu 22.04
IP:                194.164.77.164

═══════════════════════════════════════════════════════════
2. Tech Stack
═══════════════════════════════════════════════════════════

Backend:
  - Django + PostgreSQL + Gunicorn + Nginx

Web:
  - Next.js 16 + TypeScript + TailwindCSS + shadcn/ui + Recharts

Mobile:
  - Flutter 3.44.6 (Android + iOS)

═══════════════════════════════════════════════════════════
3. المسارات على السيرفر
═══════════════════════════════════════════════════════════

Backend:  /var/www/motionhr
Web:      /var/www/motionhr_web
venv:     /var/www/motionhr/venv
Backups:  /var/www/motionhr/backups
Fonts:    /var/www/motionhr/core/fonts/

الخطوط:
  /var/www/motionhr/core/fonts/Cairo-Regular.ttf
  /var/www/motionhr/core/fonts/Amiri-Regular.ttf   ← الخط المعتمد للـ PDF

مسارات اللابتوب:
  Web:     C:\MotionHR\web
  Backend: C:\MotionHR\Backend
  Mobile:  C:\MotionHR\Mobile

═══════════════════════════════════════════════════════════
4. GitHub Repositories
═══════════════════════════════════════════════════════════

Web:     johnsamire-coder/MotionHR_Web
Backend: johnsamire-coder/MotionHR
Mobile:  johnsamire-coder/MotionHR_Employee

═══════════════════════════════════════════════════════════
5. Services
═══════════════════════════════════════════════════════════

motionhr.service       # Django Backend
motionhr-web.service   # Next.js Frontend
nginx.service

═══════════════════════════════════════════════════════════
6. هيكل الداتا
═══════════════════════════════════════════════════════════

Company → Branches → Departments → JobTitles → Employees

تحديد المدير:
  - user.role in [manager, hr_manager, company_admin]
  - أو job_title.is_manager = True

═══════════════════════════════════════════════════════════
7. الموديلات (95 موديل)
═══════════════════════════════════════════════════════════

--- accounts ---
User
EmployeeNotification
PushSubscription
FCMDeviceToken
NotificationLog
TrustedDevice

--- companies ---
Company
Branch
Department
CompanyLoginSettings
WorkCharter
CharterAcceptance
CompanyPolicy
NotificationPreference
DepartmentHierarchy
CharterVersion
CharterDigitalSignature
CharterNotificationLog

--- employees ---
JobTitle
Employee
EmployeeDocument
EmployeeMovement
Deduction
JobHierarchyLevel
DepartmentJobTitleRule
EmployeeFolder
ImportLog

--- attendance ---
Shift
AttendanceSession
AttendancePolicy
AttendancePolicyAssignment
LateRule
AbsenceRule
OvertimeRule
NightShiftRule
WeekendWorkRule
LateRepeatPenalty
ShiftAssignment
EmployeeShift
ShiftChangeRequest
ShiftOverride
ShiftRotation
ShiftRotationSlot
ShiftRotationAssignment
Attendance
LocationLog
LocationCheckIn
DailyAttendanceSummary
FlexDayAdjustment
AttendanceActionLog
LateIncident
LateNotification
DisciplinaryRule
DisciplinaryAction
DailyAssignment
TrackingAlert
LocationHistory
PermissionLedger
EmployeeWorkLocation
RouteHistory

--- attendance/company_policy_models ---
CompanyWorkPolicy
PayrollAllowance
PayrollDeduction
CompanyAllowancePolicy
CompanyDeductionPolicy
CompanyBonusPolicy
CompanyInsurancePolicy
CompanyPayrollCyclePolicy
PenaltyRule
BonusRule
AllowanceRule
LeaveRule
ManualEntryBase
ManualPenalty
ManualBonus
ManualAllowance
TaxPolicy
EndOfServicePolicy

--- attendance/policy_models ---
CompanyPolicy
PolicyAcceptance

--- requests_app ---
RequestCategory
RequestType
EmployeeRequest
ApprovalFlow
ApprovalDelegation
PermissionPolicy
PermissionUsage

--- leaves ---
LeavePolicy
LeavePolicyTier
LeavePolicyTypeRule
LeaveBalanceAdjustment
LeaveType
LeaveBalance
LeaveRequest
LeaveRecallRequest

═══════════════════════════════════════════════════════════
8. شاشات الويب (68 صفحة)
═══════════════════════════════════════════════════════════

/hr/dashboard                           ← الداشبورد الرئيسي
/hr/employees                           ← قائمة الموظفين
/hr/employees/[id]                      ← ملف موظف
/hr/employees/import                    ← استيراد الموظفين Excel
/hr/attendance                          ← الحضور والانصراف
/hr/leaves                              ← الإجازات
/hr/requests                            ← الطلبات
/hr/payroll                             ← الرواتب
/hr/payroll-runs                        ← تشغيل المرتبات
/hr/manual-entries                      ← الإدخالات اليدوية
/hr/missions                            ← المهمات
/hr/locations                           ← المواقع المباشرة
/hr/announcements                       ← الإعلانات
/hr/departments                         ← الأقسام
/hr/branches                            ← الفروع
/hr/shifts                              ← الشيفتات
/hr/shifts/exceptions                   ← استثناءات الشيفتات
/hr/shifts/rotations                    ← التناوبات
/hr/job-titles                          ← المسميات الوظيفية
/hr/company                             ← معلومات الشركة
/hr/company-policies                    ← سياسات الشركة
/hr/regulations                         ← اللائحة التنظيمية
/hr/geofence                            ← الجيوفينس
/hr/work-locations                      ← مواقع العمل
/hr/leave-recall                        ← استرداد الإجازة
/hr/flex-shift                          ← الشيفت المرن
/hr/org-chart                           ← الهيكل التنظيمي
/hr/termination                         ← إنهاء الخدمة
/hr/reminders                           ← إعدادات التذكيرات
/hr/devices                             ← الأجهزة المعتمدة ← جديد
/hr/settings                            ← الإعدادات

--- السياسات ---
/hr/policies                            ← مركز السياسات
/hr/policies/allowance                  ← سياسات البدلات
/hr/policies/attendance                 ← سياسات الحضور
/hr/policies/bonus                      ← سياسات المكافآت
/hr/policies/deduction                  ← سياسات الخصومات
/hr/policies/leave                      ← سياسات الإجازات
/hr/policies/work                       ← سياسات العمل

--- الصلاحيات ---
/hr/permissions                         ← مركز الصلاحيات
/hr/permissions/assign                  ← تعيين صلاحيات
/hr/permissions/defaults                ← الصلاحيات الافتراضية
/hr/permissions/exceptions              ← الاستثناءات
/hr/permissions/export                  ← تصدير الصلاحيات
/hr/permissions/roles                   ← الأدوار

--- التقارير (25 تقرير) ---
/hr/reports                             ← مركز التقارير
/hr/reports/absence                     ← تقرير الغياب
/hr/reports/attendance                  ← تقرير الحضور
/hr/reports/bank-transfer               ← تقرير التحويل البنكي
/hr/reports/branch-comparison           ← مقارنة الفروع
/hr/reports/contracts-expiry            ← انتهاء العقود
/hr/reports/daily-attendance            ← الحضور اليومي
/hr/reports/eos                         ← مكافأة نهاية الخدمة
/hr/reports/executive-dashboard         ← لوحة التنفيذيين
/hr/reports/insurance                   ← التأمينات
/hr/reports/late                        ← التأخير
/hr/reports/leaves-basic                ← الإجازات الأساسي
/hr/reports/leaves-enhanced             ← الإجازات المفصل
/hr/reports/loans-advances              ← السلف والقروض
/hr/reports/location-tracking           ← تتبع المواقع
/hr/reports/missions-performance        ← أداء المهمات
/hr/reports/monthly-attendance          ← الحضور الشهري
/hr/reports/payroll                     ← الرواتب
/hr/reports/permissions                 ← الأذونات
/hr/reports/reimbursements              ← المصروفات
/hr/reports/requests                    ← الطلبات
/hr/reports/shifts                      ← الشيفتات
/hr/reports/tax                         ← الضريبة
/hr/reports/turnover                    ← دوران الموظفين
/hr/reports/work-hours                  ← ساعات العمل

═══════════════════════════════════════════════════════════
9. شاشات الموبايل (101 شاشة)
═══════════════════════════════════════════════════════════

--- Root ---
employee_mission_detail_screen.dart
employee_missions_screen.dart
first_launch_language_screen.dart
settings_screen.dart

--- Auth ---
auth/activate_account_screen.dart

--- Common ---
common/hierarchy_tree_screen.dart
common/location_picker_screen.dart

--- Employee Screens ---
employee/announcement_detail_screen.dart
employee/announcements_screen.dart
employee/employee_documents_screen.dart
employee/employee_movements_screen.dart
employee/employee_payslip_screen.dart
employee/employee_profile_screen.dart
employee/employee_summary_screen.dart
employee/field_visits_screen.dart
employee/item_detail_screen.dart
employee/my_shift_screen.dart
employee/my_work_locations_screen.dart
employee/requests_screen.dart

--- Manager Screens ---
manager/attendance_policy_screen.dart
manager/branches_screen.dart
manager/company_edit_screen.dart
manager/company_info_screen.dart
manager/create_announcement_screen.dart
manager/create_employee_screen.dart
manager/create_mission_screen.dart
manager/department_detail_screen.dart
manager/departments_management_screen.dart
manager/employee_permissions_screen.dart
manager/flex_adjustments_screen.dart
manager/import_tools_screen.dart
manager/job_titles_screen.dart
manager/leave_policy_screen.dart
manager/leave_recall_screen.dart
manager/location_report_screen.dart
manager/manager_announcements_screen.dart
manager/manager_employee_detail_screen.dart  ← 7 تبويبات
manager/manager_employees_list_screen.dart
manager/manager_missions_screen.dart
manager/mission_detail_screen.dart
manager/offboarding_screen.dart
manager/official_holidays_screen.dart
manager/organization_tree_screen.dart
manager/payroll_policy_screen.dart
manager/permissions_assign_screen.dart
manager/permissions_export_screen.dart
manager/permissions_hub_screen.dart
manager/permissions_management_screen.dart
manager/permissions_overrides_screen.dart
manager/permissions_roles_screen.dart
manager/policies_hub_screen.dart
manager/reminder_settings_screen.dart
manager/role_detail_screen.dart
manager/trusted_devices_screen.dart         ← جديد
manager/work_locations_approval_screen.dart
manager/work_policy_screen.dart

--- Manager Payroll Screens ---
manager/payroll/allowance_rules_screen.dart
manager/payroll/bonus_rules_screen.dart
manager/payroll/company_policies_screen.dart
manager/payroll/create_edit_allowance_rule_screen.dart
manager/payroll/create_edit_bonus_rule_screen.dart
manager/payroll/create_edit_eos_policy_screen.dart
manager/payroll/create_edit_insurance_policy_screen.dart
manager/payroll/create_edit_leave_rule_screen.dart
manager/payroll/create_edit_payroll_cycle_screen.dart
manager/payroll/create_edit_penalty_rule_screen.dart
manager/payroll/create_edit_tax_policy_screen.dart
manager/payroll/eos_policy_screen.dart
manager/payroll/insurance_policies_screen.dart
manager/payroll/leave_rules_screen.dart
manager/payroll/manual_entries_screen.dart
manager/payroll/payroll_bonus_penalty_screen.dart
manager/payroll/payroll_cycle_screen.dart
manager/payroll/payroll_employee_detail_screen.dart
manager/payroll/payroll_hub_screen.dart
manager/payroll/payroll_payslip_screen.dart
manager/payroll/payroll_run_detail_screen.dart
manager/payroll/payroll_run_screen.dart
manager/payroll/payroll_settings_screen.dart
manager/payroll/payroll_summary_screen.dart
manager/payroll/penalty_rules_screen.dart
manager/payroll/tax_policy_screen.dart

--- Manager Reports Screens ---
manager/reports/absence_report_screen.dart
manager/reports/attendance_report_screen.dart
manager/reports/base_report_screen.dart
manager/reports/branch_comparison_report_screen.dart
manager/reports/daily_attendance_report_screen.dart
manager/reports/late_report_screen.dart
manager/reports/leaves_enhanced_report_screen.dart
manager/reports/leaves_report_screen.dart
manager/reports/payroll_report_screen.dart
manager/reports/permissions_report_screen.dart
manager/reports/reports_hub_screen.dart
manager/reports/requests_report_screen.dart
manager/reports/shifts_report_screen.dart
manager/reports/work_hours_report_screen.dart

--- Manager Shifts Screens ---
manager/shifts/assign_shift_screen.dart
manager/shifts/assignment_detail_screen.dart
manager/shifts/create_edit_shift_screen.dart
manager/shifts/shift_override_screen.dart
manager/shifts/shift_rotation_screen.dart
manager/shifts/shifts_screen.dart

═══════════════════════════════════════════════════════════
10. API Endpoints (299 endpoint)
═══════════════════════════════════════════════════════════

Base URL: https://jssolutions-eg.com

--- Auth ---
POST   /attendance/api/mobile/login/
POST   /attendance/api/mobile/change-password/
POST   /attendance/api/mobile/jwt/token/
POST   /attendance/api/mobile/jwt/refresh/
POST   /attendance/api/mobile/jwt/verify/

--- Device Approval ---
POST   /attendance/api/mobile/device/register/
GET    /attendance/api/mobile/device/status/
GET    /attendance/api/mobile/manager/devices/
POST   /attendance/api/mobile/manager/devices/<id>/action/

--- Employees ---
GET    /attendance/api/mobile/manager/employees/
POST   /attendance/api/mobile/manager/employees/create/
GET    /attendance/api/mobile/manager/employees/<id>/
PUT    /attendance/api/mobile/manager/employees/<id>/update/
POST   /attendance/api/mobile/manager/employees/<id>/toggle-status/
POST   /attendance/api/mobile/manager/employees/<id>/reset-password/
POST   /attendance/api/mobile/manager/employees/<id>/transfer/
DELETE /attendance/api/mobile/manager/employees/<id>/delete/
GET    /attendance/api/mobile/manager/employees/<id>/profile/
GET    /attendance/api/mobile/manager/employees/<id>/summary/
GET    /attendance/api/mobile/manager/employees/<id>/documents/
GET    /attendance/api/mobile/manager/employees/<id>/movements/
GET    /attendance/api/mobile/manager/employees/<id>/attendance/
GET    /attendance/api/mobile/manager/employees/<id>/leaves/
GET    /attendance/api/mobile/manager/employees/<id>/requests/
GET    /attendance/api/mobile/manager/employees/<id>/shifts/
GET    /attendance/api/mobile/manager/employees/<id>/effective-shift/
GET    /attendance/api/mobile/manager/employees/<id>/insurances/
GET    /attendance/api/mobile/manager/employees/<id>/permission-balance/
POST   /attendance/api/mobile/manager/employees/<id>/permission-grant/
POST   /attendance/api/mobile/manager/employees/<id>/permission-rollback/
GET    /attendance/api/mobile/manager/employees/simple/
GET    /attendance/api/mobile/manager/employees/managers/

--- Attendance ---
POST   /attendance/api/mobile/attendance/
GET    /attendance/api/mobile/status/
GET    /attendance/api/mobile/history/
POST   /attendance/api/mobile/employee/auto-check-in/
POST   /attendance/api/mobile/employee/auto-check-out/
GET    /attendance/api/mobile/employee/auto-checkin-status/
GET    /attendance/api/mobile/employee/my-shift/
GET    /attendance/api/mobile/employee/today-sessions/
POST   /attendance/api/mobile/employee/partial-checkout/
POST   /attendance/api/mobile/employee/resume-checkin/
POST   /attendance/api/mobile/employee/save-location/
GET    /attendance/api/mobile/employee/permission-balance/
GET    /attendance/api/mobile/manager/attendance/
GET    /attendance/api/mobile/manager/work-policy/
POST   /attendance/api/mobile/manager/work-policy/save/

--- Shifts ---
GET    /attendance/api/mobile/manager/shifts/
POST   /attendance/api/mobile/manager/shifts/create/
PUT    /attendance/api/mobile/manager/shifts/<id>/update/
DELETE /attendance/api/mobile/manager/shifts/<id>/delete/
GET    /attendance/api/mobile/manager/shifts/<id>/employees/
POST   /attendance/api/mobile/manager/shifts/assign/
GET    /attendance/api/mobile/manager/shifts/assignments/
PUT    /attendance/api/mobile/manager/shifts/assignments/<id>/update/
DELETE /attendance/api/mobile/manager/shifts/assignments/<id>/delete/
POST   /attendance/api/mobile/manager/shifts/override/create/
GET    /attendance/api/mobile/manager/shifts/overrides/
DELETE /attendance/api/mobile/manager/shifts/override/<id>/delete/
GET    /attendance/api/mobile/manager/shifts/change-requests/
POST   /attendance/api/mobile/manager/shifts/change-requests/<id>/action/
GET    /attendance/api/mobile/manager/rotations/
POST   /attendance/api/mobile/manager/rotations/<id>/
PUT    /attendance/api/mobile/manager/rotations/<id>/assign/
GET    /attendance/api/mobile/manager/rotations/<id>/assignments/
DELETE /attendance/api/mobile/manager/rotations/assignments/<id>/delete/
GET    /attendance/api/mobile/my-shift/

--- Leaves ---
GET    /attendance/api/mobile/leave-types/
GET    /attendance/api/mobile/my-leaves/
POST   /attendance/api/mobile/leave-request/
PUT    /attendance/api/mobile/my-leaves/<id>/edit/
DELETE /attendance/api/mobile/my-leaves/<id>/cancel/
GET    /attendance/api/mobile/leave-substitutes/
GET    /attendance/api/mobile/hr/leave-types/
POST   /attendance/api/mobile/hr/create-leave/
GET    /attendance/api/mobile/manager/leave-policy/
POST   /attendance/api/mobile/manager/leave-policy/<id>/approve/
POST   /attendance/api/mobile/manager/leave-policy/apply-to-existing/
GET    /attendance/api/mobile/manager/leave-balance-adjustments/
DELETE /attendance/api/mobile/manager/leaves/<id>/cancel/
PUT    /attendance/api/mobile/manager/leaves/<id>/edit/
POST   /attendance/api/mobile/leave-recall/create/
GET    /attendance/api/mobile/leave-recall/list/
POST   /attendance/api/mobile/leave-recall/<id>/review/

--- Requests ---
GET    /attendance/api/mobile/request-types/
POST   /attendance/api/mobile/submit-request/
GET    /attendance/api/mobile/my-requests/
PUT    /attendance/api/mobile/my-requests/<id>/edit/
DELETE /attendance/api/mobile/my-requests/<id>/cancel/
GET    /attendance/api/mobile/manager/pending/
POST   /attendance/api/mobile/manager/action/
PUT    /attendance/api/mobile/manager/requests/<id>/edit/
POST   /attendance/api/mobile/manager/requests/<id>/cancel/
POST   /attendance/api/mobile/manager/requests/<id>/reopen/
GET    /attendance/api/mobile/manager/substitution-summary/

--- Notifications ---
GET    /attendance/api/mobile/notifications/
POST   /attendance/api/mobile/notifications/mark-read/
POST   /attendance/api/mobile/fcm-token/
DELETE /attendance/api/mobile/fcm-token/delete/

--- Announcements ---
GET    /attendance/api/mobile/announcements/list/
POST   /attendance/api/mobile/announcements/mark-read/
POST   /attendance/api/mobile/manager/announcements/create/
PUT    /attendance/api/mobile/manager/announcements/<id>/update/
DELETE /attendance/api/mobile/manager/announcements/<id>/delete/
GET    /attendance/api/mobile/manager/announcements/<id>/stats/

--- Dashboard ---
GET    /attendance/api/mobile/manager/dashboard/

--- Reports (33 endpoint = 11 تقرير × 3 صيغ) ---
GET    /attendance/api/mobile/manager/reports/attendance/
GET    /attendance/api/mobile/manager/reports/absence/
GET    /attendance/api/mobile/manager/reports/late/
GET    /attendance/api/mobile/manager/reports/daily-attendance/
GET    /attendance/api/mobile/manager/reports/work-hours/
GET    /attendance/api/mobile/manager/reports/leaves/
GET    /attendance/api/mobile/manager/reports/leaves-enhanced/
GET    /attendance/api/mobile/manager/reports/requests/
GET    /attendance/api/mobile/manager/reports/permissions/
GET    /attendance/api/mobile/manager/reports/shifts/
GET    /attendance/api/mobile/manager/reports/location-tracking/
GET    /attendance/api/mobile/manager/reports/payroll/
GET    /attendance/api/mobile/manager/reports/eos/
GET    /attendance/api/mobile/manager/reports/eos/export/
GET    /attendance/api/mobile/manager/reports/eos/export/pdf/
GET    /attendance/api/mobile/manager/reports/reimbursements/
GET    /attendance/api/mobile/manager/reports/reimbursements/export/
GET    /attendance/api/mobile/manager/reports/reimbursements/export/pdf/
GET    /attendance/api/mobile/manager/reports/bank-transfer/
GET    /attendance/api/mobile/manager/reports/bank-transfer/export/
GET    /attendance/api/mobile/manager/reports/bank-transfer/export/pdf/
GET    /attendance/api/mobile/manager/reports/insurance/
GET    /attendance/api/mobile/manager/reports/insurance/export/
GET    /attendance/api/mobile/manager/reports/insurance/export/pdf/
GET    /attendance/api/mobile/manager/reports/tax/
GET    /attendance/api/mobile/manager/reports/tax/export/
GET    /attendance/api/mobile/manager/reports/tax/export/pdf/
GET    /attendance/api/mobile/manager/reports/contracts-expiry/
GET    /attendance/api/mobile/manager/reports/contracts-expiry/export/
GET    /attendance/api/mobile/manager/reports/contracts-expiry/export/pdf/
GET    /attendance/api/mobile/manager/reports/loans-advances/
GET    /attendance/api/mobile/manager/reports/loans-advances/export/
GET    /attendance/api/mobile/manager/reports/loans-advances/export/pdf/
GET    /attendance/api/mobile/manager/reports/missions-performance/
GET    /attendance/api/mobile/manager/reports/missions-performance/export/
GET    /attendance/api/mobile/manager/reports/missions-performance/export/pdf/
GET    /attendance/api/mobile/manager/reports/executive-dashboard/
GET    /attendance/api/mobile/manager/reports/executive-dashboard/export/
GET    /attendance/api/mobile/manager/reports/executive-dashboard/export/pdf/
GET    /attendance/api/mobile/manager/reports/turnover/
GET    /attendance/api/mobile/manager/reports/turnover/export/
GET    /attendance/api/mobile/manager/reports/turnover/export/pdf/
GET    /attendance/api/mobile/manager/reports/branch-comparison/
GET    /attendance/api/mobile/manager/reports/branch-comparison/export/
GET    /attendance/api/mobile/manager/reports/branch-comparison/export/pdf/

--- Missions ---
GET    /attendance/api/mobile/employee/missions/
POST   /attendance/api/mobile/employee/missions/request/
POST   /attendance/api/mobile/employee/missions/assignments/<id>/respond/
POST   /attendance/api/mobile/employee/missions/assignments/<id>/start/
POST   /attendance/api/mobile/employee/missions/assignments/<id>/end/
POST   /attendance/api/mobile/employee/missions/assignments/<id>/update-location/
GET    /attendance/api/mobile/employee/missions/assignments/<id>/locations/
POST   /attendance/api/mobile/employee/missions/assignments/<id>/upload/
POST   /attendance/api/mobile/employee/missions/assignments/<id>/withdraw/
GET    /attendance/api/mobile/manager/missions/
POST   /attendance/api/mobile/manager/missions/create/
GET    /attendance/api/mobile/manager/missions/<id>/
PUT    /attendance/api/mobile/manager/missions/<id>/update/
DELETE /attendance/api/mobile/manager/missions/<id>/cancel/
POST   /attendance/api/mobile/manager/missions/<id>/force-cancel/
POST   /attendance/api/mobile/manager/missions/<id>/reassign/
GET    /attendance/api/mobile/manager/missions/pending-requests/
POST   /attendance/api/mobile/manager/missions/requests/<id>/respond/
GET    /attendance/api/mobile/manager/missions/withdraw-requests/
POST   /attendance/api/mobile/manager/missions/withdraw-requests/<id>/respond/
GET    /attendance/api/mobile/manager/missions/feedback-dashboard/
GET    /attendance/api/mobile/missions/<id>/feedback/
POST   /attendance/api/mobile/missions/<id>/feedback/submit/
POST   /attendance/api/mobile/missions/<id>/feedback/add-note/

--- Field Visits ---
GET    /attendance/api/mobile/field-visits/
POST   /attendance/api/mobile/field-visits/start/
POST   /attendance/api/mobile/field-visits/end/<id>/
GET    /attendance/api/mobile/field-visits/<id>/
GET    /attendance/api/mobile/field-visits/types/

--- Work Locations ---
GET    /attendance/api/mobile/work-locations/
POST   /attendance/api/mobile/work-locations/propose/
GET    /attendance/api/mobile/work-locations/types/
GET    /attendance/api/mobile/work-locations/<id>/
DELETE /attendance/api/mobile/work-locations/<id>/cancel/
GET    /attendance/api/mobile/manager/work-locations/
POST   /attendance/api/mobile/manager/work-locations/<id>/approve/
POST   /attendance/api/mobile/manager/work-locations/<id>/reject/
DELETE /attendance/api/mobile/manager/work-locations/<id>/delete/
POST   /attendance/api/mobile/manager/work-locations/<id>/assign-employees/
GET    /attendance/api/mobile/manager/work-locations/pending/
GET    /attendance/api/mobile/my-work-locations/

--- Geofence ---
GET    /attendance/api/mobile/geofence/
POST   /attendance/api/mobile/geofence/set/
GET    /attendance/api/mobile/manager/geofence/
POST   /attendance/api/mobile/manager/geofence/set/

--- Location ---
POST   /attendance/api/mobile/location/
GET    /attendance/api/mobile/manager/live-locations/
GET    /attendance/api/mobile/manager/location-report/
GET    /attendance/api/mobile/manager/route/

--- Payroll ---
GET    /attendance/api/mobile/employee/payslip/
GET    /attendance/api/mobile/manager/payroll/settings/
GET    /attendance/api/mobile/manager/payroll/summary/
GET    /attendance/api/mobile/manager/payroll/employee/
POST   /attendance/api/mobile/manager/payroll/run/create/
GET    /attendance/api/mobile/manager/payroll/runs/
GET    /attendance/api/mobile/manager/payroll/runs/<id>/
POST   /attendance/api/mobile/manager/payroll/runs/<id>/approve/
GET    /attendance/api/mobile/manager/eos/policies/
POST   /attendance/api/mobile/manager/eos/policies/<id>/
GET    /attendance/api/mobile/manager/eos/calculate/
GET    /attendance/api/mobile/manager/tax/policies/
POST   /attendance/api/mobile/manager/tax/policies/<id>/
POST   /attendance/api/mobile/manager/tax/calculate/

--- Manual Entries ---
GET    /attendance/api/mobile/manager/entries/allowance/
POST   /attendance/api/mobile/manager/entries/allowance/
PUT    /attendance/api/mobile/manager/entries/allowance/<id>/
POST   /attendance/api/mobile/manager/entries/allowance/<id>/approve/
POST   /attendance/api/mobile/manager/entries/allowance/<id>/reject/
GET    /attendance/api/mobile/manager/entries/bonus/
POST   /attendance/api/mobile/manager/entries/bonus/<id>/approve/
POST   /attendance/api/mobile/manager/entries/bonus/<id>/reject/
GET    /attendance/api/mobile/manager/entries/penalty/
POST   /attendance/api/mobile/manager/entries/penalty/<id>/approve/
POST   /attendance/api/mobile/manager/entries/penalty/<id>/reject/
GET    /attendance/api/mobile/manager/entries/summary/

--- Permissions ---
GET    /attendance/api/mobile/permissions/my/
GET    /attendance/api/mobile/manager/permissions/summary/
GET    /attendance/api/mobile/manager/permissions/users/
GET    /attendance/api/mobile/manager/permissions/users/<id>/
GET    /attendance/api/mobile/manager/permissions/available/
GET    /attendance/api/mobile/manager/permissions/roles/
POST   /attendance/api/mobile/manager/permissions/roles/create/
PUT    /attendance/api/mobile/manager/permissions/roles/<id>/update/
DELETE /attendance/api/mobile/manager/permissions/roles/<id>/delete/
POST   /attendance/api/mobile/manager/permissions/assign-role/
POST   /attendance/api/mobile/manager/permissions/remove-role/
GET    /attendance/api/mobile/manager/permissions/defaults/
POST   /attendance/api/mobile/manager/permissions/override/set/
POST   /attendance/api/mobile/manager/permissions/override/bulk/
DELETE /attendance/api/mobile/manager/permissions/override/remove/
GET    /attendance/api/mobile/manager/permissions/export/

--- Company ---
GET    /attendance/api/mobile/manager/company-info/
POST   /attendance/api/mobile/manager/company-info/update/
POST   /attendance/api/mobile/manager/company-info/upload-logo/
GET    /attendance/api/mobile/manager/branches/
GET    /attendance/api/mobile/manager/departments/
POST   /attendance/api/mobile/manager/departments/add/
PUT    /attendance/api/mobile/manager/departments/<id>/edit/
DELETE /attendance/api/mobile/manager/departments/<id>/delete/
GET    /attendance/api/mobile/manager/departments/list/
POST   /attendance/api/mobile/manager/departments/transfer-employees/
GET    /attendance/api/mobile/manager/job-titles/
PUT    /attendance/api/mobile/manager/job-titles/<id>/
GET    /attendance/api/mobile/manager/organization-tree/
GET    /attendance/api/mobile/manager/hierarchy-tree/

--- Charter ---
GET    /attendance/api/mobile/charter/
POST   /attendance/api/mobile/charter/accept/
GET    /attendance/api/mobile/manager/charter/acceptances/
POST   /attendance/api/mobile/manager/charter/update/

--- Policies ---
GET    /attendance/api/mobile/manager/attendance-policy/
POST   /attendance/api/mobile/manager/attendance-policy/<id>/approve/
POST   /attendance/api/mobile/manager/attendance-policy/<id>/assign/
GET    /attendance/api/mobile/manager/allowance-policies/
GET    /attendance/api/mobile/manager/bonus-policies/
GET    /attendance/api/mobile/manager/deduction-policies/
GET    /attendance/api/mobile/manager/insurance-policies/
GET    /attendance/api/mobile/manager/payroll-cycle-policies/
GET    /attendance/api/mobile/manager/leave-policy/
GET    /attendance/api/mobile/manager/official-holidays/

--- Offboarding ---
GET    /attendance/api/mobile/manager/offboarding/list/
GET    /attendance/api/mobile/manager/offboarding/<id>/
POST   /attendance/api/mobile/manager/offboarding/<id>/web/
POST   /attendance/api/mobile/manager/offboarding/<id>/reactivate/

--- Disciplinary ---
GET    /attendance/api/mobile/manager/disciplinary/actions/
POST   /attendance/api/mobile/manager/disciplinary/actions/<id>/review/

--- Flex Adjustments ---
GET    /attendance/api/mobile/manager/flex-adjustments/
POST   /attendance/api/mobile/manager/flex-adjustments/<id>/review/
GET    /attendance/api/mobile/manager/employees/<id>/flex-adjustments/

═══════════════════════════════════════════════════════════
11. سياسة الحضور الذكي
═══════════════════════════════════════════════════════════

Modes:
  1. يدوي
  2. إشعار ذكي
  3. تلقائي

قواعد Check-in:
  - مكتبي خارج النطاق → رفض
  - ميداني حر → أي مكان
  - ميداني محدد → داخل موقع معتمد
  - GPS مقفول → رفض + Alert للمدير

═══════════════════════════════════════════════════════════
12. Device Approval Workflow
═══════════════════════════════════════════════════════════

1. أول جهاز → معتمد تلقائياً + Auto Attendance مفعّل
2. جهاز جديد → pending + إشعار للمدير/HR
3. موافقة المدير → approved + Auto Attendance مفعّل
4. رفض المدير → rejected + Auto Attendance موقوف
5. نفس الجهاز بأكاونت تاني → مرفوض + إشعار نشاط مشبوه للمدير

═══════════════════════════════════════════════════════════
13. نظام الإشعارات
═══════════════════════════════════════════════════════════

Types:
  - reminder_checkin         ← تذكير حضور
  - reminder_checkin_manager ← تذكير للمدير بالغائبين
  - reminder_charter         ← تذكير اللائحة
  - reminder_charter_manager ← تذكير المدير بالغير موافقين
  - shift_coverage_gap       ← فجوة في تغطية الشيفت
  - new_device_approval      ← جهاز جديد ينتظر موافقة
  - suspicious_device_activity ← نشاط مشبوه
  - late_warning             ← تحذير تأخير
  - general_notice           ← إشعار عام
  - request_approved         ← موافقة على طلب
  - request_rejected         ← رفض طلب
  - leave_approved           ← موافقة على إجازة
  - leave_rejected           ← رفض إجازة
  - split_period_start       ← بداية فترة split
  - split_period_missed      ← فوات فترة split
  - work_location_proposed   ← اقتراح موقع عمل
  - device_status_update     ← تحديث حالة الجهاز

═══════════════════════════════════════════════════════════
14. نظام التقارير
═══════════════════════════════════════════════════════════

11 تقرير × 3 صيغ = 33 Endpoint

التقارير:
  1. EOS — مكافأة نهاية الخدمة
  2. Reimbursements — المصروفات
  3. Bank Transfer — التحويل البنكي
  4. Insurance — التأمينات
  5. Tax — الضريبة
  6. Turnover — دوران الموظفين
  7. Branch Comparison — مقارنة الفروع
  8. Contracts Expiry — انتهاء العقود
  9. Loans & Advances — السلف والقروض
  10. Missions Performance — أداء المهمات
  11. Executive Dashboard — لوحة التنفيذيين

تقرير مقارنة الفروع يشمل:
  - عدد الموظفين
  - إجمالي الرواتب
  - متوسط الراتب
  - أعلى راتب
  - أقل راتب
  - أيام الحضور آخر 30 يوم
  - أيام الغياب آخر 30 يوم
  - إجمالي دقائق التأخير
  - إجمالي الأوفر تايم

═══════════════════════════════════════════════════════════
15. نظام الرواتب
═══════════════════════════════════════════════════════════

المحرك: calculate_effective_payroll(emp, year, month, settings)

يحسب لكل موظف:
  - المرتب الأساسي
  - إجمالي البدلات
  - مكافأة الأوفر تايم
  - إجمالي المكافآت
  - بدل ليلي + بدل عطلة
  - إجمالي المرتب
  - خصم التأخير + الغياب + الانصراف المبكر
  - خصم الإجازة بدون مرتب
  - خصم نقص الساعات المرنة
  - خصم التأمين
  - إجمالي الأقساط + الجزاءات + الخصومات
  - صافي المرتب
  - أيام العمل / الحضور / الغياب / التأخير

═══════════════════════════════════════════════════════════
16. نظام الموافقات
═══════════════════════════════════════════════════════════

  - ApprovalFlow: مسار موافقة لكل نوع طلب
  - 3 مستويات + skip
  - unique_together لكل نوع طلب
  - ApprovalDelegation: تفويض أثناء الغياب

ملاحظة:
  scope=team_only موجود في الموديل لكن مش مفعّل في التحقق

═══════════════════════════════════════════════════════════
17. نظام الشيفتات
═══════════════════════════════════════════════════════════

الأنواع:
  - fixed: شيفت ثابت
  - split_fixed: شيفتين في اليوم
  - flexible: شيفت مرن
  - overnight: بعد نص الليل

Overnight Shifts:
  - يدور في يومين
  - يراعي localtime
  - يمنع duplicate attendance

كشف التداخل:
  - _find_same_scope_overlapping_assignment
  - _build_assignment_conflict
  - rotation_coverage_ok
  - missing_day_indexes
  - overlap_day_indexes

═══════════════════════════════════════════════════════════
18. بيانات الاختبار
═══════════════════════════════════════════════════════════

الشركة التجريبية:
  الاسم: موشن التجريبي
  Company ID: 53

الموظفون:
  جون تجريبي (Admin) | admin_john2  | ID: 3584 | Office
  موظف اختباري1      | mwzfemp0011  | ID: 3585 | Office
  موظف اختباري3      | mwzfemp0003  | ID: 3587 | Field Assigned
  موظف اختباري4      | mwzfemp0105  | ID: 3588 | Field Free
  موظف اختباري5      | mwzfemp0201  | ID: 3589 | Field Assigned
  موظف اختباري7      | mwzfemp0005  | ID: 3591 | Office

كلمة المرور الافتراضية: Test@1234
Reset: 12345678

═══════════════════════════════════════════════════════════
19. ملف توثيق الـ API
═══════════════════════════════════════════════════════════

الموقع: /var/www/motionhr/API_DOCS.md
النوع: ملف Markdown ثابت
الأمان: لا يكشف السورس — يوثق الـ endpoints فقط

═══════════════════════════════════════════════════════════
20. الخدمات التلقائية (Cron)
═══════════════════════════════════════════════════════════

python manage.py send_reminders --type checkin       ← 10:00 صباحاً
python manage.py send_reminders --type checkout      ← بعد الشيفت
python manage.py send_reminders --type pending       ← يومياً
python manage.py send_reminders --type charter       ← 9:30 صباحاً
python manage.py send_reminders --type documents     ← placeholder
python manage.py send_reminders --type split_periods ← أثناء الشيفت
python manage.py send_reminders --type shift_coverage ← 8:00 صباحاً ← جديد
python manage.py auto_checkout
python manage.py compute_daily_summaries

═══════════════════════════════════════════════════════════
21. PDF العربي
═══════════════════════════════════════════════════════════

الخط: /var/www/motionhr/core/fonts/Amiri-Regular.ttf
المكتبات: arabic_reshaper + bidi + reportlab Paragraph
المحاذاة: RIGHT
wordWrap: RTL

═══════════════════════════════════════════════════════════
22. Import Excel Template
═══════════════════════════════════════════════════════════

1.  نوع العملية
2.  الاسم الكامل بالعربي
3.  الاسم الكامل بالإنجليزي
4.  الرقم القومي
5.  الموبايل
6.  تاريخ الميلاد
7.  تاريخ التعيين
8.  الفرع
9.  القسم
10. المسمى الوظيفي
11. تصنيف الموظف
12. المرتب الأساسي (اختياري)

═══════════════════════════════════════════════════════════
23. الحالة النهائية — آخر تحديث: 2026-08-15
═══════════════════════════════════════════════════════════

آخر Commits:
  Backend: d2c973c — prevent multi-account on same device
  Web:     225f12d — Trusted Devices web UI + devices API proxy
  Mobile:  02fcc81 — Trusted Devices screen + shift_coverage_gap navigation

الإحصائيات:
  Endpoints: 299
  Web Pages: 68
  Mobile Screens: 101
  Database Models: 95

اللي اتقفل كله:
  ✅ Payroll Engine متكامل
  ✅ Approval Workflow متكامل
  ✅ Shifts System قوي جداً
  ✅ Overnight Shifts مثبتة
  ✅ Branch Comparison Report
  ✅ Device Approval Workflow
  ✅ Multi-account Prevention
  ✅ Trusted Device UI (Web + Mobile)
  ✅ E-T17 Employee Tabs (7 تبويبات)
  ✅ REQ form_schema End-to-End
  ✅ Shift Coverage Gap Alerts
  ✅ Manager Substitution Flow
  ✅ API Documentation (static)
  ✅ Smart Alerts in Dashboard

مؤجل:
  ⏸️ ATT-3 — اختبار ميداني فعلي


```

======================================================================
## FILE: /var/www/motionhr/API_DOCS.md
======================================================================

```
# MotionHR API Documentation
**Version:** 1.0.0
**Base URL:** https://jssolutions-eg.com
**Auth:** Authorization: Token YOUR_TOKEN

---

## 1. Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /attendance/api/mobile/login/ | Login & get token |

Request: {"username": "string", "password": "string"}
Response: {"token": "string", "role": "string", "employee_id": 1}

---

## 2. Employees
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attendance/api/mobile/manager/employees/ | List employees |
| POST | /attendance/api/mobile/manager/employees/create/ | Create employee |
| PUT | /attendance/api/mobile/manager/employees/{id}/update/ | Update employee |
| POST | /attendance/api/mobile/manager/employees/{id}/toggle-status/ | Toggle status |
| POST | /attendance/api/mobile/manager/employees/{id}/reset-password/ | Reset password |

---

## 3. Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /attendance/api/mobile/attendance/ | Check-in / Check-out |
| GET | /attendance/api/mobile/status/ | Current attendance status |
| GET | /attendance/api/mobile/employee/my-shift/ | Get my shift |
| POST | /attendance/api/mobile/employee/auto-check-in/ | Auto check-in |
| POST | /attendance/api/mobile/employee/auto-check-out/ | Auto check-out |

---

## 4. Leaves & Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attendance/api/mobile/request-types/ | List request types |
| POST | /attendance/api/mobile/submit-request/ | Submit request |

---

## 5. Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attendance/api/mobile/notifications/ | List notifications |
| POST | /attendance/api/mobile/notifications/mark-read/ | Mark as read |

---

## 6. Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attendance/api/mobile/manager/reports/branch-comparison/ | Branch comparison |
| GET | /attendance/api/mobile/manager/reports/turnover/ | Turnover report |
| GET | /attendance/api/mobile/manager/reports/payroll/ | Payroll report |
| GET | /attendance/api/mobile/manager/reports/attendance/ | Attendance report |
| GET | /attendance/api/mobile/manager/reports/eos/ | EOS report |
| GET | /attendance/api/mobile/manager/reports/insurance/ | Insurance report |
| GET | /attendance/api/mobile/manager/reports/tax/ | Tax report |
| GET | /attendance/api/mobile/manager/reports/loans-advances/ | Loans & advances |
| GET | /attendance/api/mobile/manager/reports/contracts-expiry/ | Contracts expiry |
| GET | /attendance/api/mobile/manager/reports/missions-performance/ | Missions performance |
| GET | /attendance/api/mobile/manager/reports/executive-dashboard/ | Executive dashboard |

Export: append /export/ for Excel, /export/pdf/ for PDF

---

## 7. Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /attendance/api/mobile/manager/dashboard/ | Manager dashboard |

---

## Notes
- All endpoints require: Authorization: Token YOUR_TOKEN
- Dates format: YYYY-MM-DD
- Default language: Arabic

```

======================================================================
## FILE: /var/www/motionhr_web/src/app/globals.css
======================================================================

```
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

:root {
  --radius: 0.75rem;

  /* MotionHR Brand Colors */
  --brand-primary: oklch(0.19 0.08 280);
  --brand-secondary: oklch(0.35 0.15 285);
  --brand-accent: oklch(0.72 0.18 165);
  --brand-highlight: oklch(0.72 0.18 45);

  /* Base */
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);

  /* Primary uses brand */
  --primary: oklch(0.19 0.08 280);
  --primary-foreground: oklch(0.985 0 0);

  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.985 0 0);

  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.19 0.08 280);

  /* Charts */
  --chart-1: oklch(0.19 0.08 280);
  --chart-2: oklch(0.72 0.18 165);
  --chart-3: oklch(0.72 0.18 45);
  --chart-4: oklch(0.35 0.15 285);
  --chart-5: oklch(0.556 0 0);

  /* Sidebar */
  --sidebar: oklch(0.19 0.08 280);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.72 0.18 165);
  --sidebar-primary-foreground: oklch(0.19 0.08 280);
  --sidebar-accent: oklch(0.25 0.08 280);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(0.25 0.08 280);
  --sidebar-ring: oklch(0.72 0.18 165);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.19 0.02 280);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.19 0.02 280);
  --popover-foreground: oklch(0.985 0 0);

  --primary: oklch(0.72 0.18 165);
  --primary-foreground: oklch(0.19 0.08 280);

  --secondary: oklch(0.25 0.03 280);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.25 0.03 280);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.25 0.03 280);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.396 0.141 25.723);
  --destructive-foreground: oklch(0.985 0 0);

  --border: oklch(0.25 0.03 280);
  --input: oklch(0.25 0.03 280);
  --ring: oklch(0.72 0.18 165);

  --chart-1: oklch(0.72 0.18 165);
  --chart-2: oklch(0.72 0.18 45);
  --chart-3: oklch(0.5 0.15 285);
  --chart-4: oklch(0.35 0.15 285);
  --chart-5: oklch(0.708 0 0);

  --sidebar: oklch(0.145 0.02 280);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.72 0.18 165);
  --sidebar-primary-foreground: oklch(0.19 0.08 280);
  --sidebar-accent: oklch(0.25 0.03 280);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(0.25 0.03 280);
  --sidebar-ring: oklch(0.72 0.18 165);
}

@theme inline {
  --color-brand-primary: var(--brand-primary);
  --color-brand-secondary: var(--brand-secondary);
  --color-brand-accent: var(--brand-accent);
  --color-brand-highlight: var(--brand-highlight);

  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);

  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);

  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}

@layer base {
  * {
    @apply border-border;
  }

  html {
    scroll-behavior: smooth;
  }

  body {
    @apply bg-background text-foreground antialiased;
    font-feature-settings: "cv02", "cv03", "cv04", "cv11";
  }

  /* RTL Support */
  html[dir="rtl"] body {
    font-family: "Cairo", system-ui, -apple-system, sans-serif;
  }
}

@layer utilities {
  .glass {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .glass-dark {
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .gradient-brand {
    background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
  }

  .gradient-accent {
    background: linear-gradient(135deg, var(--brand-accent) 0%, var(--brand-primary) 100%);
  }

  .text-gradient {
    background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}
```

======================================================================
## FILE: /var/www/motionhr_web/src/components/dashboard/sidebar.tsx
======================================================================

```
"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Play,
  LayoutDashboard, Users, Clock, Calendar, FileText,
  DollarSign, MapPin, Settings, Building2, Upload,
  Briefcase, Bell, FileBarChart, Shield, BookOpen, GitBranch, UserMinus, Map, ScrollText, Zap, Smartphone,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDict } from "@/lib/stores/language";

export function Sidebar() {
  const pathname = usePathname();
  const d = useDict();

  const navigation = [
    { key: "dashboard",        href: "/hr/dashboard",        icon: LayoutDashboard },
    { key: "employees",        href: "/hr/employees",         icon: Users },
    { key: "importEmployees",  href: "/hr/employees/import",  icon: Upload },
    { key: "attendance",       href: "/hr/attendance",        icon: Clock },
    { key: "leaves",           href: "/hr/leaves",            icon: Calendar },
    { key: "requests",         href: "/hr/requests",          icon: FileText },
    { key: "payroll",          href: "/hr/payroll",           icon: DollarSign },
    { key: "payrollRuns",     href: "/hr/payroll-runs",     icon: Play },
    { key: "manualEntries",   href: "/hr/manual-entries",  icon: FileText },
    { key: "missions",         href: "/hr/missions",          icon: Briefcase },
    { key: "locations",        href: "/hr/locations",         icon: MapPin },
    { key: "announcements",    href: "/hr/announcements",     icon: Bell },
    { key: "reports",          href: "/hr/reports",           icon: FileBarChart },
    { key: "departments",      href: "/hr/departments",       icon: Building2 },
    { key: "branches",         href: "/hr/branches",          icon: MapPin },
    { key: "shifts",           href: "/hr/shifts",            icon: Clock },
    { key: "jobTitles",        href: "/hr/job-titles",        icon: Briefcase },
    { key: "company",          href: "/hr/company",           icon: Building2 },
    { key: "permissionsTitle",  href: "/hr/permissions",       icon: Shield },
    { key: "policiesTitle",     href: "/hr/policies",          icon: BookOpen },
    { key: "orgChartTitle",     href: "/hr/org-chart",         icon: GitBranch },
    { key: "terminationTitle",  href: "/hr/termination",       icon: UserMinus },
    { key: "workLocationsTitle",href: "/hr/work-locations",    icon: Map },
    { key: "geofenceTitle",     href: "/hr/geofence",          icon: MapPin },
    { key: "companyPoliciesTitle", href: "/hr/company-policies", icon: ScrollText },
    { key: "companyRegulations", href: "/hr/regulations", icon: ScrollText },
    { key: "leaveRecallTitle",  href: "/hr/leave-recall",      icon: Calendar },
    { key: "flexShiftTitle",    href: "/hr/flex-shift",        icon: Zap },
    { key: "dailyReports", href: "/hr/reminders", icon: Bell },
    { key: "trustedDevices",   href: "/hr/devices",           icon: Smartphone },
    { key: "settings",         href: "/hr/settings",          icon: Settings },
  ] as const;

  return (
    <aside className="w-64 h-screen bg-sidebar text-sidebar-foreground flex flex-col fixed right-0 top-0 z-50 border-l border-sidebar-border pointer-events-auto">
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-sidebar-border">
        <Image
          src="/brand/icon/icon-white.png"
          alt="MotionHR"
          width={32} height={32}
          style={{ width: "auto", height: "auto" }}
          priority
        />
        <div className="flex flex-col">
          <span className="font-bold text-sm">MotionHR</span>
          <span className="text-[10px] text-sidebar-foreground/60 -mt-0.5">
            Workforce Platform
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer select-none",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              <span>{d[item.key]}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="text-[10px] text-sidebar-foreground/50 text-center leading-tight">
          <div>{d.designedBy}</div>
          <div className="font-semibold">{d.designedByName}</div>
        </div>
      </div>
    </aside>
  );
}



```

======================================================================
## FILE: /var/www/motionhr/attendance/api_mobile.py
======================================================================

```
from .fcm_logic import notify_managers, notify_employee_checkin, notify_employee_checkout, notify_manager_checkin, notify_manager_checkout, notify_manager_early_leave
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from employees.models import Employee
from attendance.models import Attendance, LocationLog



def reverse_geocode(lat, lng):
    """تحويل الإحداثيات لاسم مكان مقروء (Reverse Geocoding)"""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&accept-language=ar&zoom=16"
        req = urllib.request.Request(url, headers={'User-Agent': 'MotionHR/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get('display_name', '')
    except Exception:
        return ''


def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).first()


def format_time_value(dt):
    if not dt:
        return ''
    try:
        return timezone.localtime(dt).strftime('%I:%M %p')
    except Exception:
        return dt.strftime('%I:%M %p')



def bilingual_message(employee, message_ar, message_en):
    language = getattr(employee, "language", "ar") or "ar"
    return {
        "message": message_en if language == "en" else message_ar,
        "message_ar": message_ar,
        "message_en": message_en,
    }


def get_approved_permission(employee, permission_kind, day):
    from requests_app.models import EmployeeRequest

    return EmployeeRequest._base_manager.select_related(
        "request_type"
    ).filter(
        company=employee.company,
        employee=employee,
        request_type__permission_kind=permission_kind,
        status="approved",
        start_date__lte=day,
        end_date__gte=day,
        duration_hours__gt=0,
        permission_used_at__isnull=True,
    ).order_by("start_date", "id").first()


def consume_permission(permission_request, actual_hours, used_at):
    from decimal import Decimal, ROUND_UP
    from django.db import transaction
    from requests_app.models import EmployeeRequest, PermissionUsage

    hours = Decimal(str(actual_hours))
    requested_hours = permission_request.duration_hours or hours
    hours = min(hours, requested_hours)
    hours = hours.quantize(Decimal("0.1"), rounding=ROUND_UP)

    if hours <= 0:
        return None

    with transaction.atomic():
        locked_request = EmployeeRequest._base_manager.select_for_update().get(
            id=permission_request.id
        )

        if locked_request.permission_used_at:
            return None

        month = timezone.localtime(used_at).strftime("%Y-%m")

        usage, created = PermissionUsage._base_manager.select_for_update().get_or_create(
            company=locked_request.company,
            employee=locked_request.employee,
            month=month,
        )

        usage.used_hours += hours
        usage.used_times += 1
        usage.save(update_fields=["used_hours", "used_times"])

        locked_request.permission_used_at = used_at
        locked_request.actual_used_hours = hours
        locked_request.save(update_fields=[
            "permission_used_at",
            "actual_used_hours",
        ])

    return hours





def _notify_missing_period(employee, period, shift, after_grace=False):
    """
    إشعار الموظف والمدير والـ HR لو الموظف ما حضرش فترة في split_fixed
    after_grace=False → بداية الفترة → للموظف فقط
    after_grace=True  → بعد انتهاء السماحية → للموظف + المدير + HR
    """
    try:
        from accounts.fcm_service import send_notification_to_user, send_notification_to_managers
        from accounts.models import EmployeeNotification

        period_name = period.get('name', 'فترة')
        period_start = period.get('start_str', '')
        period_end = period.get('end_str', '')
        shift_name = shift.name if shift else ''
        emp_name = getattr(employee, 'full_name_ar', '') or str(employee)

        if not after_grace:
            # تذكير للموظف فقط
            title_ar = f'⏰ تذكير: {period_name}'
            body_ar = f'حان وقت {period_name} ({period_start} - {period_end}) من شيفت {shift_name}'
            title_en = f'⏰ Reminder: {period_name}'
            body_en = f'Time for {period_name} ({period_start} - {period_end}) from shift {shift_name}'

            send_notification_to_user(
                user=employee.user,
                title=title_ar,
                body=body_ar,
                title_en=title_en,
                body_en=body_en,
                data={
                    'type': 'period_reminder',
                    'screen': 'attendance',
                    'period_number': str(period.get('period_number', 1)),
                }
            )

            # إشعار داخلي للموظف
            EmployeeNotification.objects.create(
                employee=employee,
                title=title_ar,
                message=body_ar,
                notification_type='general_notice',
                severity='info',
            )

        else:
            # بعد انتهاء السماحية → تصعيد للموظف + المدير + HR
            title_ar = f'🚨 غياب عن {period_name}'
            body_ar = f'الموظف {emp_name} لم يسجل حضور في {period_name} ({period_start} - {period_end}) من شيفت {shift_name}'
            title_en = f'🚨 Missing Period: {period_name}'
            body_en = f'Employee {emp_name} missed {period_name} ({period_start} - {period_end}) from shift {shift_name}'

            # إشعار للموظف
            send_notification_to_user(
                user=employee.user,
                title=f'🚨 لم تسجل حضور في {period_name}',
                body=f'لم تسجل حضور في {period_name} ({period_start} - {period_end})',
                title_en=f'🚨 Missed {period_name}',
                body_en=f'You missed {period_name} ({period_start} - {period_end})',
                data={
                    'type': 'period_missed',
                    'screen': 'attendance',
                    'period_number': str(period.get('period_number', 1)),
                }
            )

            # إشعار داخلي للموظف
            EmployeeNotification.objects.create(
                employee=employee,
                title=f'🚨 غياب عن {period_name}',
                message=f'لم تسجل حضور في {period_name} ({period_start} - {period_end})',
                notification_type='late_warning',
                severity='danger',
            )

            # إشعار للمدير والـ HR
            if employee.company:
                send_notification_to_managers(
                    company=employee.company,
                    title=title_ar,
                    body=body_ar,
                    title_en=title_en,
                    body_en=body_en,
                    data={
                        'type': 'employee_missed_period',
                        'screen': 'manager_attendance',
                        'employee_id': str(employee.id),
                        'period_number': str(period.get('period_number', 1)),
                    }
                )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'notify_missing_period error: {e}')


def get_active_shift(employee, day):
    """
    مصدر موحّد للشيفت الفعلي.
    بنخلّي الحضور يستخدم نفس منطق الشيفتات والمرتبات
    عشان مايبقاش فيه اختلاف بين الحضور وكشف المرتب.

    للشيفت الليلي: لو الوقت الحالي بعد نص الليل (crosses_midnight)
    ممكن الشيفت يكون بدأ يوم فات → نجرب يومين
    """
    from attendance.api_shifts import get_effective_shift
    from datetime import timedelta

    shift, _source = get_effective_shift(employee, day)

    # لو مش لاقيين شيفت ليلي → نجرب يوم فات
    if not shift or not getattr(shift, 'crosses_midnight', False):
        return shift

    # لو الشيفت ليلي وبدايته بعد ظهر اليوم → الشيفت صح
    if shift.start_time and shift.start_time.hour >= 12:
        return shift

    # لو الشيفت ليلي وبدايته قبل الظهر → ممكن يكون الشيفت بتاع امبارح
    yesterday_shift, _ = get_effective_shift(employee, day - timedelta(days=1))
    if yesterday_shift and getattr(yesterday_shift, 'crosses_midnight', False):
        return yesterday_shift

    return shift




def get_shift_periods(shift, day):
    """
    بترجع قائمة الفترات للشيفت
    - split_fixed: بترجع الفترات من schedule_config
    - غيره: بترجع فترة واحدة من start_time و end_time
    """
    from datetime import datetime, timedelta

    if not shift:
        return []

    periods = []

    shift_mode = getattr(shift, 'shift_mode', 'fixed') or 'fixed'

    if shift_mode in ('variable_weekly', 'variable_weekly_flex'):
        # جدول أسبوعي: كل يوم في الأسبوع ليه أوقات مختلفة
        # schedule_config = {"days": {"0": {"start": "09:00", "end": "17:00"}, ...}}
        # 0=الاثنين ... 6=الأحد (Python weekday)
        try:
            config = getattr(shift, 'schedule_config', {}) or {}
            days_config = config.get('days', {})
            day_key = str(day.weekday())  # 0=الاثنين, 6=الأحد
            day_cfg = days_config.get(day_key)

            if day_cfg:
                from datetime import datetime as _dt
                start_str = str(day_cfg.get('start', '09:00'))
                end_str = str(day_cfg.get('end', '17:00'))
                start_parts = start_str.split(':')
                end_parts = end_str.split(':')
                start_dt = _dt.combine(day, __import__('datetime').time(
                    int(start_parts[0]), int(start_parts[1])))
                end_dt = _dt.combine(day, __import__('datetime').time(
                    int(end_parts[0]), int(end_parts[1])))
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                tz = timezone.get_current_timezone()
                periods.append({
                    'period_number': 1,
                    'start': timezone.make_aware(start_dt, tz),
                    'end': timezone.make_aware(end_dt, tz),
                    'start_str': start_str,
                    'end_str': end_str,
                    'name': day_cfg.get('name', 'فترة العمل'),
                })
        except Exception:
            pass

        # fallback لو اليوم مش في الجدول
        if not periods and shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'فترة العمل',
            })

    elif shift_mode == 'variable_daily':
        # جدول يومي: كل تاريخ ليه أوقات مختلفة
        # schedule_config = {"dates": {"2026-07-25": {"start": "08:00", "end": "16:00"}, ...}}
        try:
            config = getattr(shift, 'schedule_config', {}) or {}
            dates_config = config.get('dates', {})
            date_key = day.isoformat()
            date_cfg = dates_config.get(date_key)

            if date_cfg:
                from datetime import datetime as _dt
                start_str = str(date_cfg.get('start', '09:00'))
                end_str = str(date_cfg.get('end', '17:00'))
                start_parts = start_str.split(':')
                end_parts = end_str.split(':')
                start_dt = _dt.combine(day, __import__('datetime').time(
                    int(start_parts[0]), int(start_parts[1])))
                end_dt = _dt.combine(day, __import__('datetime').time(
                    int(end_parts[0]), int(end_parts[1])))
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                tz = timezone.get_current_timezone()
                periods.append({
                    'period_number': 1,
                    'start': timezone.make_aware(start_dt, tz),
                    'end': timezone.make_aware(end_dt, tz),
                    'start_str': start_str,
                    'end_str': end_str,
                    'name': date_cfg.get('name', 'فترة العمل'),
                })
        except Exception:
            pass

        # fallback لو التاريخ مش في الجدول
        if not periods and shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'فترة العمل',
            })

    elif shift_mode == 'split_fixed':
        config = getattr(shift, 'schedule_config', {}) or {}
        raw_periods = config.get('periods', [])

        for i, p in enumerate(raw_periods):
            try:
                start_parts = str(p.get('start', '09:00')).split(':')
                end_parts = str(p.get('end', '17:00')).split(':')

                start_dt = datetime.combine(day,
                    __import__('datetime').time(int(start_parts[0]), int(start_parts[1])))
                end_dt = datetime.combine(day,
                    __import__('datetime').time(int(end_parts[0]), int(end_parts[1])))

                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                tz = timezone.get_current_timezone()
                periods.append({
                    'period_number': i + 1,
                    'start': timezone.make_aware(start_dt, tz),
                    'end': timezone.make_aware(end_dt, tz),
                    'start_str': p.get('start', '09:00'),
                    'end_str': p.get('end', '17:00'),
                    'name': p.get('name', f'فترة {i + 1}'),
                })
            except Exception:
                continue

        # لو schedule_config فاضل → fallback على start/end عادي
        if not periods and shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'فترة 1',
            })
    else:
        # شيفت عادي → فترة واحدة بس
        if shift.start_time and shift.end_time:
            start_dt = datetime.combine(day, shift.start_time)
            end_dt = datetime.combine(day, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            tz = timezone.get_current_timezone()
            periods.append({
                'period_number': 1,
                'start': timezone.make_aware(start_dt, tz),
                'end': timezone.make_aware(end_dt, tz),
                'start_str': shift.start_time.strftime('%I:%M %p'),
                'end_str': shift.end_time.strftime('%I:%M %p'),
                'name': 'الفترة الأساسية',
            })

    return periods


def get_missing_periods(shift, day, employee):
    """
    بترجع الفترات اللي الموظف ما حضرهاش لـ split_fixed
    """

    if not shift or getattr(shift, 'shift_mode', 'fixed') != 'split_fixed':
        return []

    periods = get_shift_periods(shift, day)
    if not periods:
        return []

    attendance = Attendance._base_manager.filter(
        employee=employee, date=day
    ).first()

    if not attendance:
        return periods  # كل الفترات فاتت

    from attendance.models import AttendanceSession

    sessions = AttendanceSession._base_manager.filter(
        attendance=attendance,
        employee=employee,
    ).order_by('session_number')

    missed = []
    now = timezone.now()

    for period in periods:
        # الفترة لو لسه مجيتش ساعتها ما نعدهاش فاتت
        if period['end'] > now:
            continue

        # الفترة فاتت، شوف لو فيه session فيها
        covered = False
        for session in sessions:
            s_in = session.check_in_time
            if s_in and period['start'] <= s_in <= period['end']:
                covered = True
                break

        if not covered:
            missed.append(period)

    return missed


def get_shift_bounds(shift, day):
    """
    بترجع حدود الشيفت (start, end) كـ datetime aware.

    للشيفت الليلي (crosses_midnight):
    - لو start_time بعد 12: الشيفت بيبدأ يوم day وبينتهي يوم day+1
    - لو start_time قبل 12: الشيفت بدأ يوم day-1 وبينتهي يوم day
    """
    from datetime import datetime, timedelta

    if not shift or not shift.start_time or not shift.end_time:
        return None, None

    crosses = getattr(shift, 'crosses_midnight', False)
    start_hour = shift.start_time.hour

    if crosses and start_hour < 12:
        # الشيفت بدأ يوم فات (مثلاً: بدأ 10pm يوم 25، خلص 6am يوم 26)
        shift_day = day - timedelta(days=1)
    else:
        shift_day = day

    start_dt = datetime.combine(shift_day, shift.start_time)
    end_dt = datetime.combine(shift_day, shift.end_time)

    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    current_timezone = timezone.get_current_timezone()
    start_dt = timezone.make_aware(start_dt, current_timezone)
    end_dt = timezone.make_aware(end_dt, current_timezone)

    return start_dt, end_dt


def attendance_to_dict(attendance):
    if not attendance:
        return {
            'date': '',
            'date_display': '',
            'status': '',
            'checked_in': False,
            'check_in_time': '',
            'check_in_latitude': None,
            'check_in_longitude': None,
            'check_in_address': '',
            'checked_out': False,
            'check_out_time': '',
            'check_out_latitude': None,
            'check_out_longitude': None,
            'check_out_address': '',
        }

    return {
        'date': attendance.date.isoformat() if getattr(attendance, 'date', None) else '',
        'date_display': attendance.date.strftime('%d/%m/%Y') if getattr(attendance, 'date', None) else '',
        'status': getattr(attendance, 'status', '') or '',
        'checked_in': bool(getattr(attendance, 'check_in_time', None)),
        'check_in_time': format_time_value(getattr(attendance, 'check_in_time', None)),
        'check_in_latitude': getattr(attendance, 'check_in_latitude', None),
        'check_in_longitude': getattr(attendance, 'check_in_longitude', None),
        'check_in_address': getattr(attendance, 'check_in_address', '') or '',
        'checked_out': bool(getattr(attendance, 'check_out_time', None)),
        'check_out_time': format_time_value(getattr(attendance, 'check_out_time', None)),
        'check_out_latitude': getattr(attendance, 'check_out_latitude', None),
        'check_out_longitude': getattr(attendance, 'check_out_longitude', None),
        'check_out_address': getattr(attendance, 'check_out_address', '') or '',
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({'success': False, 'message': 'اسم المستخدم وكلمة السر مطلوبين'}, status=400)

    user = authenticate(username=username, password=password)

    if not user:
        return Response({'success': False, 'message': 'بيانات الدخول غير صحيحة'}, status=401)

    token, _ = Token.objects.get_or_create(user=user)

    # JWT tokens
    try:
        _refresh = RefreshToken.for_user(user)
        _jwt_access = str(_refresh.access_token)
        _jwt_refresh = str(_refresh)
    except Exception:
        _jwt_access = ''
        _jwt_refresh = ''
    must_change_password = getattr(user, 'must_change_password', False)
    role = getattr(user, 'role', 'employee') or 'employee'
    manager_roles = ['super_admin', 'company_admin', 'hr_manager', 'manager']

    employee = get_employee_for_user(user)

    company_name = ''
    company_obj = getattr(user, 'company', None)
    if employee and getattr(employee, 'company', None):
        company_obj = employee.company

    if company_obj:
        company_name = (
            getattr(company_obj, 'name', '')
            or getattr(company_obj, 'name_ar', '')
            or str(company_obj)
        )

    if not employee and role in manager_roles:
        full_name = user.get_full_name().strip() or user.get_username()
        return Response({
            'success': True,
            'message': 'تم الدخول بنجاح',
            'token': token.key,
            'access': _jwt_access,
            'refresh': _jwt_refresh,
            'must_change_password': must_change_password,
            'role': role,
            'app_mode': 'manager',
            'username': user.get_username(),
            'full_name': full_name,
            'first_name': user.first_name or full_name.split(' ')[0] if full_name else '',
            'gender': 'male',
            'company_name': company_name,
            'employee': {
                'id': None,
                'name': full_name,
                'company': company_name,
                'is_field_worker': False,
                'stealth_tracking_enabled': False,
                'should_track': False,
            }
        })

    if not employee:
        return Response({'success': False, 'message': 'لا يوجد ملف موظف مرتبط بهذا المستخدم'}, status=404)

    is_field_worker = getattr(employee, 'is_field_worker', False)
    stealth_tracking_enabled = getattr(employee, 'stealth_tracking_enabled', False)
    should_track = bool(is_field_worker or stealth_tracking_enabled)

    full_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
    if not full_name:
        full_name = user.get_username()

    app_mode = 'manager' if role in manager_roles else 'employee'

    return Response({
        'success': True,
        'message': 'تم الدخول بنجاح',
        'token': token.key,
        'access': _jwt_access,
        'refresh': _jwt_refresh,
        'must_change_password': must_change_password,
        'role': role,
        'app_mode': app_mode,
        'username': user.get_username(),
        'full_name': full_name,
        'first_name': getattr(employee, 'first_name_ar', '') or user.first_name or full_name.split(' ')[0],
        'gender': getattr(employee, 'gender', 'male') or 'male',
        'company_name': company_name,
        'employee': {
            'id': employee.id,
            'name': full_name,
            'first_name': getattr(employee, 'first_name_ar', ''),
            'gender': getattr(employee, 'gender', 'male'),
            'company': company_name,
            'is_field_worker': is_field_worker,
            'stealth_tracking_enabled': stealth_tracking_enabled,
            'should_track': should_track,
        }
    })




def _create_gps_disabled_alert(employee, source="attendance"):
    try:
        from attendance.models import TrackingAlert
        now = timezone.now()
        today = timezone.localdate()

        note = f"GPS disabled أثناء {source}"

        open_alert = TrackingAlert._base_manager.filter(
            company=employee.company,
            employee=employee,
            date=today,
            status='open'
        ).filter(notes__icontains='GPS').first()

        if open_alert:
            open_alert.last_seen_at = now
            if not getattr(open_alert, 'notes', ''):
                open_alert.notes = note
            open_alert.save(update_fields=['last_seen_at', 'notes'])
        else:
            TrackingAlert._base_manager.create(
                company=employee.company,
                employee=employee,
                date=today,
                started_at=now,
                last_seen_at=now,
                minutes_outside=0,
                last_latitude=None,
                last_longitude=None,
                last_address='',
                status='open',
                notes=note,
            )
    except Exception:
        pass

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_send_location(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    accuracy = request.data.get('accuracy', 0)

    if latitude in [None, ''] or longitude in [None, '']:
        _create_gps_disabled_alert(employee, 'location_ping')
        return Response({'success': False, 'message': 'الموقع الجغرافي غير متاح. يرجى تفعيل GPS والمحاولة مرة أخرى'}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy or 0)
    except Exception:
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)

    address = reverse_geocode(latitude, longitude)
    LocationLog._base_manager.create(
        company=employee.company,
        employee=employee,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        address=address,
        timestamp=timezone.now()
    )

    return Response({
        'success': True,
        'message': 'تم تسجيل الموقع بنجاح',
        'employee_name': f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
    })


def get_current_split_period(shift, now_dt):
    from datetime import timedelta

    if not shift or getattr(shift, 'shift_mode', 'fixed') != 'split_fixed':
        return None

    early_minutes = int(getattr(shift, 'early_checkin_minutes', 0) or 0)
    candidate_days = [
        timezone.localdate(now_dt),
        timezone.localdate(now_dt - timedelta(days=1)),
    ]
    seen_days = set()

    for day in candidate_days:
        if day in seen_days:
            continue
        seen_days.add(day)

        periods = get_shift_periods(shift, day)
        for period in periods:
            allowed_start = period['start'] - timedelta(minutes=early_minutes)
            if allowed_start <= now_dt <= period['end']:
                return period

    return None


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_action(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    action = request.data.get('action', '').strip().lower()
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    accuracy = request.data.get('accuracy', 0)

    if action not in ['check_in', 'check_out']:
        return Response({'success': False, 'message': 'نوع العملية لازم يكون check_in أو check_out'}, status=400)

    if latitude in [None, ''] or longitude in [None, '']:
        _create_gps_disabled_alert(employee, action)
        return Response({'success': False, 'message': 'الموقع الجغرافي غير متاح. يرجى تفعيل GPS والمحاولة مرة أخرى'}, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy or 0)
    except Exception:
        return Response({'success': False, 'message': 'بيانات الموقع غير صحيحة'}, status=400)

    today = timezone.localdate()
    now = timezone.now()

    attendance = Attendance._base_manager.filter(employee=employee, date=today).first()

    # ── حماية الإجازات مع دعم الاستدعاء ──
    from leaves.models import LeaveRequest, LeaveRecallRequest
    has_approved_leave = LeaveRequest._base_manager.filter(
        employee=employee,
        status='approved',
        start_date__lte=today,
        end_date__gte=today,
    ).exists()

    has_approved_recall = False
    if has_approved_leave:
        has_approved_recall = LeaveRecallRequest._base_manager.filter(
            employee=employee,
            recall_date=today,
            status='approved',
        ).exists()

    if has_approved_leave and not has_approved_recall:
        return Response({
            "success": False,
            **bilingual_message(
                employee,
                "أنت في إجازة معتمدة اليوم. لا يمكنك تسجيل الحضور أو الانصراف إلا بعد تواصلك مع الموارد البشرية لعمل طلب استدعاء.",
                "You are on an approved leave today. You cannot record attendance until you contact HR to create a leave recall request."
            ),
            "is_on_leave": True,
            "can_request_recall": True,
        }, status=400)

    # ── تحقق أن الموظف مربوط فعلياً بشيفت (EmployeeShift أو ShiftAssignment) ──
    if action == 'check_in':
        from attendance.models import EmployeeShift as _EmpShift
        from attendance.models import ShiftAssignment as _ShiftAssign
        from django.db.models import Q

        # فحص 1: EmployeeShift (ربط مباشر)
        has_emp_shift = _EmpShift._base_manager.filter(
            employee=employee,
            is_active=True,
        ).exists()

        # فحص 2: ShiftAssignment (ربط بالموظف مباشرة أو بالقسم/الفرع)
        emp_dept_id = getattr(employee, 'department_id', None)
        emp_branch_id = getattr(employee, 'branch_id', None)

        assignment_q = Q(employee=employee)
        if emp_dept_id:
            assignment_q |= Q(assignment_type='department', department_id=emp_dept_id)
        if emp_branch_id:
            assignment_q |= Q(assignment_type='branch', branch_id=emp_branch_id)

        has_shift_assignment = _ShiftAssign._base_manager.filter(
            company=employee.company,
            is_active=True,
        ).filter(assignment_q).exists()

        if not has_emp_shift and not has_shift_assignment:
            return Response({
                'success': False,
                **bilingual_message(
                    employee,
                    'لا يمكن تسجيل الحضور. لم يتم ربطك بأي شيفت حتى الآن. يرجى التواصل مع الموارد البشرية.',
                    'Check-in is not allowed. You are not assigned to any shift yet. Please contact HR.'
                ),
                'no_shift_assigned': True,
            }, status=400)

    active_shift = get_active_shift(employee, today)
    shift_start, shift_end = get_shift_bounds(active_shift, today)
    
    # ═══════════════════════════════════════════════════
    # Worker Type Check - فحص نوع الموظف
    # ═══════════════════════════════════════════════════
    if action == 'check_in':
        worker_type = getattr(employee, 'worker_type', 'office') or 'office'
        company = employee.company
        
        # لو مكتبي - لازم من موقع الشركة
        if worker_type == 'office':
            if company and company.geofence_enabled and company.office_latitude and company.office_longitude:
                from attendance.location_utils import is_within_radius
                radius_check = is_within_radius(
                    latitude, longitude,
                    float(company.office_latitude),
                    float(company.office_longitude),
                    company.geofence_radius or 500,
                )
                if not radius_check['is_within']:
                    return Response({
                        'success': False,
                        **bilingual_message(
                            employee,
                            f'لا يمكن تسجيل الحضور من هنا. الموظف المكتبي يجب أن يبصم من موقع الشركة (أنت على بعد {radius_check["distance_meters"]:.0f} متر).',
                            f'You must check-in from the company location (you are {radius_check["distance_meters"]:.0f}m away).'
                        ),
                        'outside_office': True,
                        'distance_meters': radius_check['distance_meters'],
                    }, status=400)
        
        # لو ميداني محدد - لازم من موقع معتمد
        elif worker_type == 'field_assigned':
            from attendance.models import EmployeeWorkLocation
            from attendance.location_utils import is_within_radius
            from django.db.models import Q
            
            # نجيب المواقع المعتمدة للموظف
            approved_locations = EmployeeWorkLocation._base_manager.filter(
                company=company,
                status='approved',
                is_active=True,
            ).filter(
                Q(employee=employee) |
                Q(is_shared=True, shared_with_branch=None, shared_with_department=None) |
                Q(is_shared=True, shared_with_branch=employee.branch) |
                Q(is_shared=True, shared_with_department=employee.department)
            ).distinct()
            
            # نفحص لو الموظف داخل أي موقع معتمد
            current_location = None
            for loc in approved_locations:
                check = is_within_radius(
                    latitude, longitude,
                    float(loc.latitude), float(loc.longitude),
                    loc.radius or 500,
                )
                if check['is_within']:
                    current_location = loc
                    break
            
            if not current_location:
                # مش داخل أي موقع معتمد
                available_names = [loc.name for loc in approved_locations[:5]]
                return Response({
                    'success': False,
                    **bilingual_message(
                        employee,
                        'الموقع الحالي غير معتمد. المواقع المتاحة: ' + ', '.join(available_names) if available_names else 'لا توجد مواقع معتمدة لك. يرجى اقتراح موقع.',
                        'Current location is not approved.'
                    ),
                    'outside_approved_locations': True,
                    'approved_locations': available_names,
                }, status=400)
        
        # لو ميداني حر - أي مكان مسموح
        # (مفيش فحص للموقع)
    
    

    # ── تحقق من وقت الشيفت (للحضور فقط) ──
    if action == 'check_in' and active_shift:
        attendance_mode = getattr(employee, 'attendance_mode', 'fixed_shift')
        shift_mode = getattr(active_shift, 'shift_mode', 'fixed') or 'fixed'

        # الشيفت المرن والميداني: مسموح أي وقت
        # split_fixed: عنده تحقق خاص أسفل
        skip_time_check = (
            attendance_mode in ('flexible_hours', 'field_worker')
            or shift_mode in ('flex_fixed', 'flex_split', 'split_fixed')
        )

        if not skip_time_check and shift_start and shift_end:
            from datetime import timedelta
            # نقرأ فترة السماح للحضور المبكر من الشيفت نفسه
            early_minutes = int(getattr(active_shift, 'early_checkin_minutes', 30) or 30)
            allowed_from = shift_start - timedelta(minutes=early_minutes)

            if now < allowed_from or now > shift_end:
                shift_start_str = shift_start.strftime('%I:%M %p')
                shift_end_str = shift_end.strftime('%I:%M %p')
                return Response({
                    'success': False,
                    **bilingual_message(
                        employee,
                        f'لا يمكن تسجيل الحضور الآن. الشيفت من {shift_start_str} إلى {shift_end_str} (مسموح الحضور قبل الشيفت بـ {early_minutes} دقيقة).',
                        f'Check-in is not allowed now. Shift is from {shift_start_str} to {shift_end_str} (check-in allowed {early_minutes} minutes before shift starts).'
                    ),
                    'outside_shift_time': True,
                    'shift_start': shift_start_str,
                    'shift_end': shift_end_str,
                }, status=400)

    current_split_period = None
    if action == 'check_in':
        current_split_period = get_current_split_period(active_shift, now)
        if active_shift and getattr(active_shift, 'shift_mode', 'fixed') == 'split_fixed' and not current_split_period:
            periods = get_shift_periods(active_shift, today)
            periods_text = " / ".join(
                [f"{p['name']}: {p['start_str']} - {p['end_str']}" for p in periods]
            ) or "لا توجد فترات معرفة"

            return Response({
                "success": False,
                **bilingual_message(
                    employee,
                    f"لا يمكن تسجيل الحضور الآن. مسموح فقط أثناء فترات الشيفت المحددة: {periods_text}",
                    f"Check-in is not allowed right now. It is only allowed during the configured shift periods: {periods_text}",
                ),
                "outside_allowed_period": True,
                "shift_periods": [
                    {
                        "period_number": p["period_number"],
                        "name": p["name"],
                        "start": p["start_str"],
                        "end": p["end_str"],
                    }
                    for p in periods
                ],
            }, status=400)

    late_minutes = 0
    late_permission = None

    if (
        action == "check_in"
        and shift_start
        and getattr(employee, "attendance_mode", "fixed_shift") != "flexible_hours"
    ):
        from datetime import timedelta

        grace_minutes = int(getattr(active_shift, "grace_period", 0) or 0)
        allowed_start = shift_start + timedelta(minutes=grace_minutes)

        if now > allowed_start:
            late_minutes = int((now - allowed_start).total_seconds() // 60)

            if late_minutes > 0:
                late_permission = get_approved_permission(
                    employee,
                    "late_arrival",
                    today,
                )

    late_permission_covers = bool(
        late_permission
        and float(late_permission.duration_hours or 0) * 60 >= late_minutes
    )

    check_in_status = (
        "present"
        if late_minutes == 0 or late_permission_covers
        else "late"
    )

    check_in_note = ""
    if late_permission_covers:
        check_in_note = "تم استخدام إذن تأخير معتمد"
    elif late_permission and late_minutes > 0:
        check_in_note = "مدة التأخير أكبر من مدة الإذن المعتمد"

    # ═══════════════════════════════════════════════════
    # الكود ده القديم اتنقل للـ Worker Type Check (فوق)
    # اللي بيفحص حسب نوع الموظف (office/field_free/field_assigned)
    # سيبناه Empty عشان لا نكسر التسلسل
    # ═══════════════════════════════════════════════════
    if action == 'check_in':
        pass  # Handled by worker_type check above

    if action == 'check_in':
        if attendance and getattr(attendance, 'check_in_time', None):
            return Response({
                'success': False,
                'message': 'تم تسجيل الحضور اليوم بالفعل',
                'today': attendance_to_dict(attendance)
            }, status=400)

        if not attendance:
            attendance = Attendance._base_manager.create(
                company=employee.company,
                employee=employee,
                date=today,
                check_in_time=now,
                check_in_latitude=latitude,
                check_in_longitude=longitude,
                check_in_address=reverse_geocode(latitude, longitude),
                check_in_within_range=True,
                shift=active_shift,
                late_minutes=late_minutes,
                check_in_notes=check_in_note,
                status=check_in_status,
            )
        else:
            attendance.company = employee.company
            attendance.check_in_time = now
            attendance.check_in_latitude = latitude
            attendance.check_in_longitude = longitude
            attendance.check_in_address = reverse_geocode(latitude, longitude)
            attendance.check_in_within_range = True
            attendance.shift = active_shift
            attendance.late_minutes = late_minutes
            attendance.check_in_notes = check_in_note
            attendance.status = check_in_status
            attendance.save()

        # ── on_mission flag ──
        try:
            from attendance.missions_models import MissionAssignment
            has_mission = MissionAssignment._base_manager.filter(
                employee=employee,
                mission__date=today,
                status='approved',
            ).exists()
            if has_mission:
                attendance.on_mission = True
                attendance.save(update_fields=['on_mission'])
        except Exception:
            pass

        from attendance.models import AttendanceSession

        open_session = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee,
            check_out_time__isnull=True
        ).order_by('-session_number').first()

        if not open_session:
            existing_sessions_count = AttendanceSession._base_manager.filter(
                attendance=attendance,
                employee=employee
            ).count()

            AttendanceSession._base_manager.create(
                company=employee.company,
                attendance=attendance,
                employee=employee,
                session_number=existing_sessions_count + 1,
                check_in_time=now,
                check_in_latitude=latitude,
                check_in_longitude=longitude,
                is_partial=False,
                on_mission=attendance.on_mission,
                notes='Initial check-in session',
            )

        address = reverse_geocode(latitude, longitude)
        LocationLog._base_manager.create(
            company=employee.company,
            employee=employee,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            address=address,
            timestamp=now
        )

        used_permission_hours = None

        if late_permission and late_minutes > 0:
            used_permission_hours = consume_permission(
                late_permission,
                late_minutes / 60,
                now,
            )

        if late_minutes == 0:
            message_ar = "تم تسجيل الحضور بنجاح"
            message_en = "Check-in recorded successfully"
        elif late_permission_covers:
            message_ar = "تم تسجيل الحضور وتطبيق إذن التأخير المعتمد"
            message_en = "Check-in recorded and the approved late-arrival permission was applied"
        elif late_permission:
            message_ar = "تم تسجيل الحضور، لكن مدة التأخير أكبر من مدة الإذن المعتمد"
            message_en = "Check-in recorded, but the delay exceeds the approved permission duration"
        else:
            message_ar = "تم تسجيل الحضور مع احتساب التأخير"
            message_en = "Check-in recorded and the delay was counted"

        response_data = {
            "success": True,
            **bilingual_message(employee, message_ar, message_en),
            "action": "check_in",
            "time": format_time_value(now),
            "late_minutes": late_minutes,
            "permission_applied": bool(used_permission_hours),
            "permission_used_hours": (
                float(used_permission_hours)
                if used_permission_hours
                else 0
            ),
            "today": attendance_to_dict(attendance),
        }

        # Push + Notification center
        try:
            emp_name = request.user.get_full_name() or request.user.username
            notify_employee_checkin(request.user, format_time_value(now), address)
            notify_manager_checkin(employee.company, emp_name, format_time_value(now))
        except Exception as e:
            print(f"Check-in notification error: {e}")

        return Response(response_data)

    from datetime import datetime, timedelta

    early_permission = None
    early_permission_covers = False
    early_leave_minutes = 0

    try:
        today = timezone.localdate()
        shift = get_active_shift(employee, today)

        if shift and shift.start_time and shift.end_time:
            start_dt = datetime.combine(today, shift.start_time)
            end_dt = datetime.combine(today, shift.end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            mode = getattr(employee, 'attendance_mode', 'fixed_shift')
            if mode == 'flexible_hours' and attendance and attendance.check_in_time:
                check_in_local = timezone.localtime(attendance.check_in_time)
                shift_duration = (end_dt - start_dt).total_seconds()
                end_time_aware = check_in_local + timedelta(seconds=shift_duration)
            else:
                end_time_aware = timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt

            now = timezone.now()
            if now < end_time_aware:
                remaining = int((end_time_aware - now).total_seconds())

                early_permission = get_approved_permission(
                    employee,
                    "early_leave",
                    today,
                )

                approved_seconds = (
                    float(early_permission.duration_hours or 0) * 3600
                    if early_permission
                    else 0
                )

                early_permission_covers = bool(
                    early_permission
                    and approved_seconds >= remaining
                )

                if not early_permission_covers:
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60

                    if early_permission:
                        message_ar = (
                            f"مدة الإذن المعتمد لا تغطي الانصراف الحالي. "
                            f"المتبقي {hours} ساعة و{minutes} دقيقة."
                        )
                        message_en = (
                            "The approved permission does not cover "
                            f"the remaining {hours} hours and {minutes} minutes."
                        )
                    else:
                        message_ar = (
                            f"لسه بدري على الانصراف، فاضل "
                            f"{hours} ساعة و{minutes} دقيقة. "
                            "قدم طلب إذن خروج مبكر."
                        )
                        message_en = (
                            f"The shift has not ended. "
                            f"{hours} hours and {minutes} minutes remain. "
                            "Submit an early-leave permission request."
                        )

                    return Response({
                        "success": False,
                        **bilingual_message(employee, message_ar, message_en),
                        "shift_not_ended": True,
                        "remaining_seconds": remaining,
                    }, status=400)

    except Exception as e:
        pass

    if not attendance or not getattr(attendance, 'check_in_time', None):
        return Response({'success': False, 'message': 'لا يمكن تسجيل الانصراف قبل الحضور'}, status=400)

    if getattr(attendance, 'check_out_time', None):
        return Response({
            'success': False,
            'message': 'تم تسجيل الانصراف اليوم بالفعل',
            'today': attendance_to_dict(attendance)
        }, status=400)

    attendance.check_out_time = now
    attendance.check_out_latitude = latitude
    attendance.check_out_longitude = longitude
    attendance.check_out_address = reverse_geocode(latitude, longitude)
    attendance.check_out_within_range = True

    from attendance.models import AttendanceSession

    open_session = AttendanceSession._base_manager.filter(
        attendance=attendance,
        employee=employee,
        check_out_time__isnull=True
    ).order_by('-session_number').first()

    if open_session:
        open_session.check_out_time = now
        open_session.check_out_latitude = latitude
        open_session.check_out_longitude = longitude
        open_session.is_partial = False
        open_session.calculate_worked_minutes()
        open_session.save()
    else:
        existing_sessions_count = AttendanceSession._base_manager.filter(
            attendance=attendance,
            employee=employee
        ).count()

        if existing_sessions_count == 0:
            fallback_session = AttendanceSession._base_manager.create(
                company=employee.company,
                attendance=attendance,
                employee=employee,
                session_number=1,
                check_in_time=attendance.check_in_time,
                check_out_time=now,
                check_in_latitude=attendance.check_in_latitude,
                check_in_longitude=attendance.check_in_longitude,
                check_out_latitude=latitude,
                check_out_longitude=longitude,
                is_partial=False,
                notes='Backfilled from legacy attendance record',
            )
            fallback_session.calculate_worked_minutes()
            fallback_session.save()

    if shift_end and now < shift_end:
        early_leave_minutes = int((shift_end - now).total_seconds() // 60)

    attendance.early_leave_minutes = early_leave_minutes

    if early_permission_covers:
        attendance.check_out_notes = "تم استخدام إذن خروج مبكر معتمد"

    attendance.calculate_work_hours()
    attendance.save()

    # DailyAttendanceSummary: نعبّي الملخص اليومي بعد الانصراف
    try:
        from attendance.models import DailyAttendanceSummary
        DailyAttendanceSummary.compute_for_day(employee, today)
    except Exception as _ds_err:
        import logging
        logging.getLogger(__name__).warning(f'DailyAttendanceSummary checkout error: {_ds_err}')

    # FlexDayAdjustment: لو شيفت مرن → ننشئ/نحدث طلب التعديل
    try:
        from attendance.payroll_rules import _upsert_flex_adjustment
        _flex_shift = getattr(attendance, 'shift', None) or shift
        _flex_hours = float(getattr(attendance, 'work_hours', 0) or 0)
        _upsert_flex_adjustment(employee, attendance, _flex_shift, _flex_hours)
    except Exception as _fx_err:
        import logging
        logging.getLogger(__name__).warning(f'FlexDayAdjustment checkout error: {_fx_err}')

    LocationLog._base_manager.create(
        company=employee.company,
        employee=employee,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        timestamp=now
    )

    used_early_hours = None

    if early_permission and early_leave_minutes > 0:
        used_early_hours = consume_permission(
            early_permission,
            early_leave_minutes / 60,
            now,
        )

    if used_early_hours:
        message_ar = "تم تسجيل الانصراف وتطبيق إذن الخروج المبكر"
        message_en = "Check-out recorded and the approved early-leave permission was applied"
    else:
        message_ar = "تم تسجيل الانصراف بنجاح"
        message_en = "Check-out recorded successfully"

    response_data = {
        "success": True,
        **bilingual_message(employee, message_ar, message_en),
        "action": "check_out",
        "time": format_time_value(now),
        "early_leave_minutes": early_leave_minutes,
        "permission_applied": bool(used_early_hours),
        "permission_used_hours": (
            float(used_early_hours)
            if used_early_hours
            else 0
        ),
        "today": attendance_to_dict(attendance),
    }

    # Push + Notification center
    try:
        emp_name = request.user.get_full_name() or request.user.username
        notify_employee_checkout(request.user, format_time_value(now), hours_worked='')
        if early_leave_minutes > 0:
            notify_manager_early_leave(
                employee.company,
                emp_name,
                format_time_value(now),
                early_leave_minutes,
            )
        else:
            notify_manager_checkout(employee.company, emp_name, format_time_value(now))
    except Exception as e:
        print(f"Check-out notification error: {e}")

    return Response(response_data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_status(request):
    from datetime import datetime, timedelta, time as dt_time
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    today = timezone.localdate()

    # ═══════════════════════════════════════════════════
    # ATT-10b: GPS Detection - يسجل Alert لو GPS مقفول
    # ═══════════════════════════════════════════════════
    try:
        _lat = request.GET.get('latitude')
        _lng = request.GET.get('longitude')
        _has_gps = _lat not in (None, '', 'null') and _lng not in (None, '', 'null')

        from attendance.models import TrackingAlert
        _now = timezone.now()

        _open_alert = TrackingAlert._base_manager.filter(
            company=employee.company,
            employee=employee,
            date=today,
            status='open',
            notes__icontains='GPS'
        ).first()

        if not _has_gps:
            # GPS مقفول - نسجل Alert
            if _open_alert:
                # تحديث Alert الموجود
                _open_alert.last_seen_at = _now
                _open_alert.save(update_fields=['last_seen_at'])
            else:
                # إنشاء Alert جديد
                TrackingAlert._base_manager.create(
                    company=employee.company,
                    employee=employee,
                    date=today,
                    started_at=_now,
                    last_seen_at=_now,
                    minutes_outside=0,
                    last_latitude=None,
                    last_longitude=None,
                    last_address='',
                    status='open',
                    notes='GPS disabled - detected from status ping',
                )
        else:
            # GPS شغال - نقفل أي Alert مفتوح
            if _open_alert:
                _open_alert.status = 'resolved'
                _open_alert.resolved_at = _now
                _open_alert.save(update_fields=['status', 'resolved_at'])
    except Exception:
        pass
    # ═══════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════
    # Validation: worker_type and shift must be set
    # ═══════════════════════════════════════════════════
    worker_type = getattr(employee, 'worker_type', None)
    
    effective_shift = get_active_shift(employee, today)
    has_shift = effective_shift is not None

    
    missing = []
    if not worker_type:
        missing.append('worker_type')
    if not has_shift:
        missing.append('shift')
    
    if missing:
        messages_ar = []
        messages_en = []
        if 'worker_type' in missing:
            messages_ar.append('لم يتم تحديد نوع الموظف (مكتبي / ميداني حر / ميداني محدد)')
            messages_en.append('Worker type not specified (office / field_free / field_assigned)')
        if 'shift' in missing:
            messages_ar.append('لم يتم ربطك بأي شيفت')
            messages_en.append('You are not assigned to any shift')
        
        # Send notification to HR (once per day)
        try:
            _notify_hr_incomplete_data(employee, missing)
        except Exception:
            pass
        
        return Response({
            'success': False,
            'account_incomplete': True,
            'missing': missing,
            'message': ' | '.join(messages_ar),
            'message_en': ' | '.join(messages_en),
            'action_required': 'تواصل مع الموارد البشرية' if getattr(employee, 'language', 'ar') == 'ar' else 'Contact HR',
        }, status=200)
    
    # شيفت بعد نص الليل: نبحث في اليوم الحالي واليوم السابق
    from datetime import timedelta as _td
    attendance = (
        Attendance._base_manager.filter(
            employee=employee,
            date__in=[today, today - _td(days=1)],
            check_in_time__isnull=False,
        ).order_by('-date').first()
        or
        Attendance._base_manager.filter(employee=employee, date=today).first()
    )
    today_dict = attendance_to_dict(attendance)

    # تاريخ الشيفت الفعلي (ممكن يكون امبارح لو شيفت بعد نص الليل)
    att_date = attendance.date if attendance else today

    shift_start_str = ''
    shift_end_str = ''
    shift_name = ''
    shift_end_timestamp = None
    shift_duration_seconds = 0
    remaining_seconds = 0
    can_check_out = False
    has_early_leave = False

    try:
        shift = get_active_shift(employee, att_date)

        if shift:
            shift_name = shift.name
            shift_mode = getattr(shift, 'shift_mode', '') or getattr(shift, 'shift_type', '')
            periods = get_shift_periods(shift, att_date)

            effective_start_dt = None
            effective_end_dt = None

            # لو الشيفت بيرجع فترات فعلية → نعرض أول فترة وآخر فترة
            if periods:
                first_period = periods[0]
                last_period = periods[-1]

                effective_start_dt = first_period.get('start')
                effective_end_dt = last_period.get('end')

                if first_period.get('start_str'):
                    shift_start_str = first_period.get('start_str')
                elif effective_start_dt:
                    local_start = timezone.localtime(effective_start_dt) if timezone.is_aware(effective_start_dt) else effective_start_dt
                    shift_start_str = local_start.strftime('%I:%M %p')

                if last_period.get('end_str'):
                    shift_end_str = last_period.get('end_str')
                elif effective_end_dt:
                    local_end = timezone.localtime(effective_end_dt) if timezone.is_aware(effective_end_dt) else effective_end_dt
                    shift_end_str = local_end.strftime('%I:%M %p')

            # fallback للشيفت العادي
            elif shift.start_time and shift.end_time:
                start_dt = datetime.combine(today, shift.start_time)
                end_dt = datetime.combine(today, shift.end_time)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                tz = timezone.get_current_timezone()
                effective_start_dt = timezone.make_aware(start_dt, tz) if timezone.is_naive(start_dt) else start_dt
                effective_end_dt = timezone.make_aware(end_dt, tz) if timezone.is_naive(end_dt) else end_dt

                shift_start_str = shift.start_time.strftime('%I:%M %p')
                shift_end_str = shift.end_time.strftime('%I:%M %p')

            if effective_start_dt and effective_end_dt:
                shift_duration_seconds = int((effective_end_dt - effective_start_dt).total_seconds())

                if attendance and attendance.check_in_time:
                    check_in_local = timezone.localtime(attendance.check_in_time)
                    mode = getattr(employee, 'attendance_mode', 'fixed_shift')

                    # المرن بدون فترات: نهاية الشيفت = وقت الدخول + المدة
                    if mode == 'flexible_hours' and not periods:
                        end_time_dt = check_in_local + timedelta(seconds=shift_duration_seconds)
                    else:
                        end_time_dt = effective_end_dt

                    shift_end_timestamp = end_time_dt.isoformat()
                    now = timezone.now()
                    remaining = (end_time_dt - now).total_seconds()
                    remaining_seconds = max(0, int(remaining))
                    can_check_out = remaining_seconds <= 0
    except Exception as e:
        pass

    try:
        from requests_app.models import EmployeeRequest, RequestType
        from django.db.models import Q
        early_leave_types = RequestType._base_manager.filter(
            Q(company=employee.company) &
            (Q(name__icontains='خروج مبكر') | Q(name__icontains='إذن انصراف') | Q(name__icontains='اذن انصراف'))
        ).values_list('id', flat=True)
        
        if early_leave_types:
            early_req = EmployeeRequest._base_manager.filter(
                employee=employee,
                request_type__id__in=list(early_leave_types),
                start_date=today,
                status='approved'
            ).order_by('start_time').first()
            
            if early_req:
                has_early_leave = True
                current_time = timezone.localtime(timezone.now()).time()
                
                if early_req.start_time:
                    if current_time >= early_req.start_time:
                        can_check_out = True
                else:
                    can_check_out = True
    except Exception:
        pass

    # بيانات الخروج الجزئي
    allow_partial_checkout = False
    shift_mode = 'fixed'
    sessions_today = 0
    has_open_session = False
    can_partial_checkout = False
    can_resume = False

    periods_data = []
    missing_periods_data = []

    try:
        if shift:
            allow_partial_checkout = getattr(shift, 'allow_partial_checkout', False)
            shift_mode = getattr(shift, 'shift_mode', 'fixed')

            periods = get_shift_periods(shift, today)
            periods_data = [
                {
                    'period_number': p.get('period_number'),
                    'name': p.get('name'),
                    'start': p.get('start_str'),
                    'end': p.get('end_str'),
                }
                for p in periods
            ]

            missing_periods = get_missing_periods(shift, today, employee)
            missing_periods_data = [
                {
                    'period_number': p.get('period_number'),
                    'name': p.get('name'),
                    'start': p.get('start_str'),
                    'end': p.get('end_str'),
                }
                for p in missing_periods
            ]

        if allow_partial_checkout and attendance:
            from attendance.models import AttendanceSession
            sessions = AttendanceSession._base_manager.filter(
                attendance=attendance,
                employee=employee
            ).order_by('session_number')

            sessions_today = sessions.count()
            open_session = sessions.filter(check_out_time__isnull=True).first()
            has_open_session = open_session is not None

            max_sessions = getattr(shift, 'max_sessions_per_day', 2) if shift else 2

            if has_open_session:
                can_partial_checkout = True
                can_resume = False
            elif sessions_today > 0 and sessions_today < max_sessions:
                can_partial_checkout = False
                can_resume = True
    except Exception:
        pass

    response_data = {
        'success': True,
        'date': today.isoformat(),
        'checked_in': today_dict.get('checked_in', False),
        'checked_out': today_dict.get('checked_out', False),
        'check_in_time': today_dict.get('check_in_time', ''),
        'check_out_time': today_dict.get('check_out_time', ''),
        'shift_name': shift_name,
        'shift_start': shift_start_str,
        'shift_end': shift_end_str,
        'shift_end_timestamp': shift_end_timestamp,
        'shift_duration_seconds': shift_duration_seconds,
        'remaining_seconds': remaining_seconds,
        'can_check_out': can_check_out,
        'has_early_leave_permission': has_early_leave,
        'allow_partial_checkout': allow_partial_checkout,
        'shift_mode': shift_mode,
        'shift_periods': periods_data,
        'missing_periods': missing_periods_data,
        'sessions_today': sessions_today,
        'has_open_session': has_open_session,
        'can_partial_checkout': can_partial_checkout,
        'can_resume': can_resume,
        'worker_type': getattr(employee, 'worker_type', 'office') or 'office',
        'current_approved_location': _get_current_approved_location(employee, request),
        'active_field_visit': _get_active_field_visit(employee),
        'today': today_dict,
        'is_late': False,
        'late_minutes': 0,
    }

    # ── حساب التأخير ──────────────────────────────────
    try:
        if attendance and attendance.check_in_time and shift:
            from datetime import datetime, timedelta
            check_in_local = timezone.localtime(attendance.check_in_time)
            periods = get_shift_periods(shift, att_date)

            if periods:
                first_start = periods[0].get('start')
                if first_start:
                    if timezone.is_naive(first_start):
                        tz = timezone.get_current_timezone()
                        first_start = timezone.make_aware(first_start, tz)
                    diff = (check_in_local - timezone.localtime(first_start)).total_seconds()
                    if diff > 0:
                        response_data['is_late'] = True
                        response_data['late_minutes'] = int(diff // 60)
            elif shift.start_time:
                from datetime import datetime
                shift_start_dt = datetime.combine(att_date, shift.start_time)
                tz = timezone.get_current_timezone()
                shift_start_aware = timezone.make_aware(shift_start_dt, tz)
                diff = (check_in_local - shift_start_aware).total_seconds()
                if diff > 0:
                    response_data['is_late'] = True
                    response_data['late_minutes'] = int(diff // 60)
    except Exception:
        pass
    # ──────────────────────────────────────────────────

    return Response(response_data)


def _get_current_approved_location(employee, request):
    try:
        worker_type = getattr(employee, 'worker_type', 'office')
        if worker_type != 'field_assigned':
            return None
        
        try:
            lat = float(request.GET.get('latitude', 0) or 0)
            lng = float(request.GET.get('longitude', 0) or 0)
        except (ValueError, TypeError):
            return None
        
        if lat == 0 or lng == 0:
            return None
        
        from attendance.models import EmployeeWorkLocation
        from attendance.location_utils import is_within_radius
        from django.db.models import Q
        
        locations = EmployeeWorkLocation._base_manager.filter(
            company=employee.company,
            status='approved',
            is_active=True,
        ).filter(
            Q(employee=employee) |
            Q(is_shared=True, shared_with_branch=None, shared_with_department=None) |
            Q(is_shared=True, shared_with_branch=employee.branch) |
            Q(is_shared=True, shared_with_department=employee.department)
        ).distinct()
        
        for loc in locations:
            check = is_within_radius(
                lat, lng,
                float(loc.latitude), float(loc.longitude),
                loc.radius or 500,
            )
            if check['is_within']:
                return {
                    'id': loc.id,
                    'name': loc.name,
                    'type': loc.location_type,
                    'type_display': loc.get_location_type_display(),
                    'distance_meters': check['distance_meters'],
                }
    except Exception:
        pass
    
    return None


def _get_active_field_visit(employee):
    try:
        from attendance.models import LocationCheckIn
        active = LocationCheckIn._base_manager.filter(
            employee=employee,
            status__in=['arrived', 'in_progress'],
        ).first()
        
        if active:
            return {
                'id': active.id,
                'location_name': active.location_name,
                'purpose': active.purpose or '',
                'arrival_time': timezone.localtime(active.arrival_time).strftime('%I:%M %p') if active.arrival_time else None,
            }
    except Exception:
        pass
    
    return None


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_attendance_history(request):
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    records = Attendance._base_manager.filter(employee=employee).order_by('-date')[:30]

    items = [attendance_to_dict(record) for record in records]

    return Response({
        'success': True,
        'count': len(items),
        'items': items
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_change_password(request):
    """تغيير كلمة المرور من تطبيق الموبايل"""
    user = request.user
    current_password = request.data.get('current_password', '').strip()
    new_password = request.data.get('new_password', '').strip()

    if not current_password or not new_password:
        return Response({
            'success': False,
            'message': 'كلمة المرور الحالية والجديدة مطلوبتان'
        }, status=400)

    if len(new_password) < 6:
        return Response({
            'success': False,
            'message': 'كلمة المرور الجديدة لازم تكون 6 أحرف على الأقل'
        }, status=400)

    if not user.check_password(current_password):
        return Response({
            'success': False,
            'message': 'كلمة المرور الحالية غير صحيحة'
        }, status=400)

    if current_password == new_password:
        return Response({
            'success': False,
            'message': 'كلمة المرور الجديدة لازم تختلف عن الحالية'
        }, status=400)

    user.set_password(new_password)
    user.must_change_password = False
    user.save()

    Token.objects.filter(user=user).delete()
    new_token = Token.objects.create(user=user)

    return Response({
        'success': True,
        'message': 'تم تغيير كلمة المرور بنجاح',
        'token': new_token.key,
    })


# ==================== GEOFENCE APIs ====================

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_geofence_get(request):
    """جلب إعدادات النطاق الجغرافي للشركة"""
    user = request.user
    employee = get_employee_for_user(user)

    company = None
    if employee and getattr(employee, 'company', None):
        company = employee.company
    elif hasattr(user, 'company') and user.company:
        company = user.company

    if not company:
        return Response({'success': False, 'message': 'الشركة غير موجودة'}, status=404)

    return Response({
        'success': True,
        'geofence': {
            'latitude': float(company.office_latitude) if company.office_latitude else None,
            'longitude': float(company.office_longitude) if company.office_longitude else None,
            'radius': company.geofence_radius or 100,
            'enabled': company.geofence_enabled,
            'address': company.office_address or '',
        }
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_geofence_set(request):
    """حفظ موقع الشركة من الموبايل (للمدير فقط)"""
    user = request.user
    role = getattr(user, 'role', 'employee') or 'employee'
    manager_roles = ['super_admin', 'company_admin', 'hr_manager', 'manager']

    if role not in manager_roles:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    radius = request.data.get('radius', 100)
    enabled = request.data.get('enabled', True)
    address = request.data.get('address', '')

    if latitude is None or longitude is None:
        return Response({'success': False, 'message': 'الإحداثيات مطلوبة'}, status=400)

    employee = get_employee_for_user(user)
    company = None
    if employee and getattr(employee, 'company', None):
        company = employee.company
    elif hasattr(user, 'company') and user.company:
        company = user.company

    if not company:
        return Response({'success': False, 'message': 'الشركة غير موجودة'}, status=404)

    try:
        company.office_latitude = latitude
        company.office_longitude = longitude
        company.geofence_radius = int(radius)
        company.geofence_enabled = bool(enabled)
        if address:
            company.office_address = address
        company.save()

        return Response({
            'success': True,
            'message': 'تم حفظ موقع الشركة بنجاح',
            'geofence': {
                'latitude': float(company.office_latitude),
                'longitude': float(company.office_longitude),
                'radius': company.geofence_radius,
                'enabled': company.geofence_enabled,
                'address': company.office_address,
            }
        })
    except Exception as e:
        return Response({'success': False, 'message': f'خطأ في الحفظ: {str(e)}'}, status=500)


def calculate_distance(lat1, lng1, lat2, lng2):
    """حساب المسافة بين نقطتين بالمتر"""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    lat1_rad = radians(float(lat1))
    lat2_rad = radians(float(lat2))
    delta_lat = radians(float(lat2) - float(lat1))
    delta_lng = radians(float(lng2) - float(lng1))

    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# ============================================================
# FCM Token Management (Firebase Cloud Messaging)
# ============================================================
from accounts.fcm_models import FCMDeviceToken


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_fcm_token_register(request):
    """حفظ FCM Token للمستخدم — مع refresh تلقائي لو التوكن اتغير"""
    try:
        user = request.user
        fcm_token = request.data.get('fcm_token', '').strip()
        platform = request.data.get('platform', 'android')
        device_info = request.data.get('device_info', '')
        preferred_language = request.data.get('preferred_language', 'ar')

        if not fcm_token:
            return Response({
                'success': False,
                'message': 'FCM token مطلوب'
            }, status=400)

        # تحديث Employee.language عشان تبقى مصدر الحقيقة للإشعارات
        try:
            emp = Employee._base_manager.filter(user=user).first()
            if emp and preferred_language in ('ar', 'en'):
                if emp.language != preferred_language:
                    emp.language = preferred_language
                    emp.save(update_fields=['language'])
        except Exception as _lang_err:
            import logging
            logging.getLogger(__name__).warning(f'Employee.language update error: {_lang_err}')

        # لو نفس التوكن موجود لحد تاني، امسحه
        FCMDeviceToken.objects.filter(fcm_token=fcm_token).exclude(user=user).delete()

        # لو عندنا توكن قديم لنفس الـ user على نفس الجهاز، حدّثه
        # لو التوكن نفسه موجود، update_or_create بالتوكن
        # لو التوكن اتغير (refresh)، شيل القديم وحط الجديد
        existing = FCMDeviceToken.objects.filter(user=user, platform=platform).first()
        if existing and existing.fcm_token != fcm_token:
            existing.fcm_token = fcm_token
            existing.device_info = device_info
            existing.preferred_language = preferred_language
            existing.is_active = True
            existing.save(update_fields=['fcm_token', 'device_info', 'preferred_language', 'is_active'])
            created = False
            token_obj = existing
        else:
            token_obj, created = FCMDeviceToken.objects.update_or_create(
                fcm_token=fcm_token,
                defaults={
                    'user': user,
                    'platform': platform,
                    'device_info': device_info,
                    'preferred_language': preferred_language,
                    'is_active': True,
                }
            )

        return Response({
            'success': True,
            'message': 'تم حفظ التوكن بنجاح' if created else 'تم تحديث التوكن',
            'created': created,
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_fcm_token_delete(request):
    """حذف FCM Token عند تسجيل الخروج"""
    try:
        fcm_token = request.data.get('fcm_token', '').strip()
        if fcm_token:
            FCMDeviceToken.objects.filter(
                user=request.user,
                fcm_token=fcm_token
            ).delete()
        return Response({'success': True, 'message': 'تم حذف التوكن'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)

# ============================================================
# Device Approval Workflow
# ============================================================
from accounts.fcm_models import TrustedDevice

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_device_register(request):
    """تسجيل جهاز جديد — أول جهاز يتعمد تلقائياً، الجهاز الجديد يحتاج موافقة"""
    try:
        from django.utils import timezone as tz
        from accounts.fcm_service import send_notification_to_managers
        from accounts.fcm_models import TrustedDevice

        user = request.user
        device_id = request.data.get('device_id', '').strip()
        device_name = request.data.get('device_name', '').strip()
        platform = request.data.get('platform', 'android')

        if not device_id:
            return Response({'success': False, 'message': 'device_id مطلوب'}, status=400)

        # ─── منع تعدد الحسابات على نفس الجهاز ───
        other_user_device = TrustedDevice._base_manager.filter(
            device_id=device_id
        ).exclude(user=user).first()

        if other_user_device:
            # نبعت إشعار للمديرين إن في نشاط مشبوه
            emp = Employee._base_manager.filter(user=user).first()
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else user.username
            other_emp = Employee._base_manager.filter(user=other_user_device.user).first()
            other_name = f"{getattr(other_emp, 'first_name_ar', '')} {getattr(other_emp, 'last_name_ar', '')}".strip() if other_emp else other_user_device.user.username
            try:
                from accounts.fcm_service import send_notification_to_managers
                send_notification_to_managers(
                    company=getattr(user, 'company', None),
                    title='🚨 نشاط مشبوه — تعدد حسابات',
                    body=f'الجهاز نفسه مسجل باسم {other_name} وحاول الدخول باسم {emp_name}',
                    data={
                        'type': 'suspicious_device_activity',
                        'screen': 'trusted_devices',
                        'device_id': device_id[:20],
                        'user_id': str(user.id),
                    },
                )
            except Exception:
                pass

            return Response({
                'success': False,
                'status': 'suspicious',
                'auto_attendance_enabled': False,
                'message': 'هذا الجهاز مسجل بحساب آخر — تم إبلاغ المدير',
            }, status=403)
        # ─────────────────────────────────────────────

        # هل الجهاز ده موجود قبل كده؟
        existing = TrustedDevice._base_manager.filter(user=user, device_id=device_id).first()
        if existing:
            existing.last_login_at = tz.now()
            existing.save(update_fields=['last_login_at'])
            return Response({
                'success': True,
                'status': existing.status,
                'auto_attendance_enabled': existing.auto_attendance_enabled,
                'message': 'جهاز موجود بالفعل',
                'is_new': False,
            })

        # هل ده أول جهاز للموظف؟
        existing_devices = TrustedDevice._base_manager.filter(user=user)
        is_first = not existing_devices.exists()

        status = 'approved' if is_first else 'pending'
        auto_attendance = is_first

        device = TrustedDevice._base_manager.create(
            user=user,
            device_id=device_id,
            device_name=device_name or f'{platform} device',
            platform=platform,
            status=status,
            is_first_device=is_first,
            auto_attendance_enabled=auto_attendance,
            approved_by=user if is_first else None,
            approved_at=tz.now() if is_first else None,
            last_login_at=tz.now(),
        )

        # لو جهاز جديد مش الأول → نبعت إشعار للمديرين
        if not is_first:
            emp = Employee._base_manager.filter(user=user).first()
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else user.username
            try:
                send_notification_to_managers(
                    company=getattr(user, 'company', None),
                    title=f'🔔 جهاز جديد — {emp_name}',
                    body=f'الموظف {emp_name} دخل من جهاز جديد ويحتاج موافقة. الجهاز: {device_name or device_id[:20]}',
                    data={
                        'type': 'new_device_approval',
                        'screen': 'trusted_devices',
                        'device_id': str(device.id),
                        'user_id': str(user.id),
                    },
                )
            except Exception:
                pass

        return Response({
            'success': True,
            'status': status,
            'auto_attendance_enabled': auto_attendance,
            'is_new': True,
            'is_first_device': is_first,
            'message': 'تم تسجيل الجهاز بنجاح' if is_first else 'طلب تسجيل الجهاز في انتظار موافقة المدير',
        })

    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_device_status(request):
    """حالة الجهاز الحالي"""
    try:
        from accounts.fcm_models import TrustedDevice
        device_id = request.query_params.get('device_id', '').strip()
        if not device_id:
            return Response({'success': False, 'message': 'device_id مطلوب'}, status=400)

        device = TrustedDevice._base_manager.filter(user=request.user, device_id=device_id).first()
        if not device:
            return Response({'success': False, 'status': 'not_registered', 'auto_attendance_enabled': False})

        return Response({
            'success': True,
            'status': device.status,
            'auto_attendance_enabled': device.auto_attendance_enabled,
            'is_first_device': device.is_first_device,
            'device_name': device.device_name,
            'created_at': str(device.created_at)[:10],
        })
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_devices_list(request):
    """قائمة أجهزة الموظفين — للمدير"""
    try:
        from accounts.fcm_models import TrustedDevice
        from attendance.api_reports import _check_manager
        if not _check_manager(request.user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)

        company = getattr(request.user, 'company', None)
        status_filter = request.query_params.get('status', None)

        qs = TrustedDevice._base_manager.filter(
            user__company=company
        ).select_related('user', 'approved_by').order_by('-created_at')

        if status_filter:
            qs = qs.filter(status=status_filter)

        results = []
        for d in qs:
            emp = Employee._base_manager.filter(user=d.user).first()
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() if emp else d.user.username
            results.append({
                'id': d.id,
                'employee_name': emp_name,
                'username': d.user.username,
                'device_name': d.device_name,
                'device_id': d.device_id[:20] + '...' if len(d.device_id) > 20 else d.device_id,
                'platform': d.platform,
                'status': d.status,
                'is_first_device': d.is_first_device,
                'auto_attendance_enabled': d.auto_attendance_enabled,
                'created_at': str(d.created_at)[:16],
                'last_login_at': str(d.last_login_at)[:16] if d.last_login_at else '',
            })

        return Response({'success': True, 'count': len(results), 'results': results})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_device_action(request, device_id):
    """موافقة / رفض / إلغاء جهاز — للمدير"""
    try:
        from accounts.fcm_models import TrustedDevice
        from django.utils import timezone as tz
        from attendance.api_reports import _check_manager
        from accounts.fcm_service import send_notification_to_user

        if not _check_manager(request.user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)

        action = request.data.get('action', '').strip()
        if action not in ('approve', 'reject', 'revoke'):
            return Response({'success': False, 'message': 'action لازم يكون approve / reject / revoke'}, status=400)

        device = TrustedDevice._base_manager.filter(id=device_id).first()
        if not device:
            return Response({'success': False, 'message': 'الجهاز مش موجود'}, status=404)

        if action == 'approve':
            device.status = 'approved'
            device.auto_attendance_enabled = True
            device.approved_by = request.user
            device.approved_at = tz.now()
            msg_ar = 'تم اعتماد جهازك وتفعيل الحضور التلقائي'
            msg_en = 'Your device has been approved and auto attendance is enabled'
        elif action == 'reject':
            device.status = 'rejected'
            device.auto_attendance_enabled = False
            msg_ar = 'تم رفض طلب اعتماد جهازك'
            msg_en = 'Your device registration request has been rejected'
        else:  # revoke
            device.status = 'revoked'
            device.auto_attendance_enabled = False
            msg_ar = 'تم إلغاء صلاحية جهازك'
            msg_en = 'Your device access has been revoked'

        device.save()

        # إشعار الموظف
        try:
            send_notification_to_user(
                user=device.user,
                title='📱 ' + msg_ar,
                body=f'الجهاز: {device.device_name}',
                data={'type': 'device_status_update', 'status': device.status},
                title_en='📱 ' + msg_en,
                body_en=f'Device: {device.device_name}',
            )
        except Exception:
            pass

        return Response({
            'success': True,
            'message': msg_ar,
            'status': device.status,
            'auto_attendance_enabled': device.auto_attendance_enabled,
        })
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)




@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_notifications_list(request):
    """جلب إشعارات المستخدم الحالي"""
    from accounts.fcm_models import NotificationLog

    qs = NotificationLog.objects.filter(user=request.user).order_by('-id')[:50]
    notifications = []
    for n in qs:
        notifications.append({
            'id': n.id,
            'title': n.title,
            'body': n.body,
            'notification_type': n.notification_type,
            'is_read': n.is_read,
            'data': n.data or {},
            'created_at': timezone.localtime(n.created_at).isoformat(),
        })

    unread_count = NotificationLog.objects.filter(user=request.user, is_read=False).count()

    return Response({
        'success': True,
        'unread_count': unread_count,
        'notifications': notifications,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_notifications_mark_read(request):
    """تعليم إشعار كمقروء أو تعليم الكل"""
    from accounts.fcm_models import NotificationLog

    notification_id = request.data.get('id')

    if notification_id:
        updated = NotificationLog.objects.filter(
            user=request.user,
            id=notification_id
        ).update(is_read=True)

        return Response({
            'success': updated > 0,
            'message': 'تم تحديث الإشعار' if updated else 'الإشعار غير موجود'
        }, status=200 if updated else 404)

    updated = NotificationLog.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return Response({
        'success': True,
        'message': 'تم تعليم كل الإشعارات كمقروءة',
        'updated': updated
    })


# ============================================================
#                    Charter / اللائحة
# ============================================================

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_get(request):
    """جلب اللائحة الحالية للموظف أو المدير"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

    charter = WorkCharter.objects.filter(company=company, is_active=True).first()

    if not charter:
        return Response({
            'success': True,
            'has_charter': False,
            'needs_acceptance': False,
            'charter': None,
            'accepted': False,
            'accepted_at': None,
        })

    accepted = False
    accepted_at = None

    if employee:
        acceptance = CharterAcceptance.objects.filter(employee=employee, charter=charter).first()
        if acceptance:
            accepted = True
            accepted_at = acceptance.accepted_at.isoformat() if acceptance.accepted_at else None

    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

    return Response({
        'success': True,
        'has_charter': True,
        'needs_acceptance': charter.is_mandatory and not accepted,
        'charter': {
            'id': charter.id,
            'title': charter.title,
            'introduction': charter.introduction or '',
            'content': charter.content or '',
            'version': charter.version,
            'is_mandatory': charter.is_mandatory,
            'attachment_url': attachment_url,
            'attachment_name': attachment_name,
        },
        'accepted': accepted,
        'accepted_at': accepted_at,
    })

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_accept(request):
    """الموظف يوافق على اللائحة"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    company = getattr(user, 'company', None) or getattr(Employee._base_manager.filter(user=user).first(), 'company', None) or getattr(Employee._base_manager.filter(user=user).first(), 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

    charter = WorkCharter.objects.filter(company=company, is_active=True).first()

    if not charter:
        return Response({'success': False, 'error': 'لا توجد لائحة فعالة'}, status=404)

    employee = Employee._base_manager.filter(user=user).first()

    if not employee:
        return Response({'success': False, 'error': 'لم يتم العثور على الموظف'}, status=404)

    acceptance, created = CharterAcceptance.objects.get_or_create(
        employee=employee,
        charter=charter,
        defaults={
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
        }
    )

    try:
        from accounts.fcm_models import NotificationLog
        emp_name = user.get_full_name() or user.username
        from django.contrib.auth import get_user_model
        User = get_user_model()
        managers = User.objects.filter(is_staff=True, is_active=True)
        for mgr in managers:
            NotificationLog.objects.create(
                user=mgr,
                title='✅ موافقة على اللائحة',
                body=f'الموظف {emp_name} وافق على: {charter.title}',
                notification_type='general',
            )
    except Exception:
        pass

    return Response({
        'success': True,
        'message': 'تم تسجيل موافقتك بنجاح',
        'already_accepted': not created,
        'accepted_at': acceptance.accepted_at.isoformat() if acceptance.accepted_at else None,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_charter_acceptances(request):
    """المدير يشوف مين وافق ومين لسه - للطباعة"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in ['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager']):
        return Response({'success': False, 'error': 'غير مصرح'}, status=403)

    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    if not company:
        return Response({'success': False, 'error': 'لا توجد شركة'}, status=400)

    charter = WorkCharter.objects.filter(company=company, is_active=True).first()
    if not charter:
        return Response({'success': False, 'error': 'لا توجد لائحة'}, status=404)

    all_employees = Employee._base_manager.filter(
        company=company, is_active=True
    ).select_related('user').order_by('user__first_name')

    acceptances = {
        a.employee_id: a
        for a in CharterAcceptance.objects.filter(charter=charter)
    }

    accepted_list = []
    pending_list = []

    for emp in all_employees:
        emp_data = {
            'id': emp.id,
            'name': emp.user.get_full_name() or emp.user.username,
            'username': emp.user.username,
        }
        acc = acceptances.get(emp.id)
        if acc:
            emp_data['accepted_at'] = acc.accepted_at.isoformat() if acc.accepted_at else ''
            emp_data['ip_address'] = str(acc.ip_address) if acc.ip_address else ''
            accepted_list.append(emp_data)
        else:
            pending_list.append(emp_data)

    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

    return Response({
        'success': True,
        'charter_title': charter.title,
        'charter_version': charter.version,
        'charter_content': charter.content or '',
        'attachment_url': attachment_url,
        'attachment_name': attachment_name,
        'print_date': timezone.now().isoformat(),
        'accepted': {'count': len(accepted_list), 'employees': accepted_list},
        'pending': {'count': len(pending_list), 'employees': pending_list},
    })

@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def mobile_charter_update(request):
    """المدير يعدل اللائحة + يرفع ملف مرفق"""
    import os
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in ['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager']):
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    employee = Employee._base_manager.filter(user=user).first()
    company = getattr(user, "company", None) or getattr(employee, "company", None)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    charter = WorkCharter.objects.filter(company=company).first()

    attachment_file = request.FILES.get('attachment')
    remove_attachment = str(request.data.get('remove_attachment', '')).strip().lower() in ['1', 'true', 'yes', 'on']

    if attachment_file:
        ext = os.path.splitext(attachment_file.name.lower())[1]
        allowed = {'.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'}
        if ext not in allowed:
            return Response({
                "success": False,
                "error": "نوع الملف غير مدعوم. المسموح: PDF / Word / PNG / JPG"
            }, status=400)

        max_size = 10 * 1024 * 1024
        if attachment_file.size > max_size:
            return Response({
                "success": False,
                "error": "حجم الملف كبير. الحد الأقصى 10 MB"
            }, status=400)

    if not charter:
        charter = WorkCharter.objects.create(
            company=company,
            title=request.data.get("title", "لائحة الشركة"),
            content=request.data.get("content", ""),
            introduction=request.data.get("introduction", ""),
            is_active=True,
            is_mandatory=True,
            attachment=attachment_file if attachment_file else None,
        )

        attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
        attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

        return Response({
            "success": True,
            "message": "تم إنشاء اللائحة",
            "version": charter.version,
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        })

    content_changed = False
    settings_changed = False

    new_title = request.data.get("title", "").strip()
    if "title" in request.data and not new_title:
        return Response({"success": False, "error": "عنوان اللائحة لا يمكن أن يكون فارغاً"}, status=400)
    new_intro = request.data.get("introduction", "").strip()
    new_content = request.data.get("content", "").strip()

    if new_title and new_title != charter.title:
        charter.title = new_title
        content_changed = True

    if new_intro != (charter.introduction or ''):
        charter.introduction = new_intro
        content_changed = True

    if new_content and new_content != (charter.content or ''):
        charter.content = new_content
        content_changed = True

    if attachment_file:
        charter.attachment = attachment_file
        content_changed = True
    elif remove_attachment and getattr(charter, 'attachment', None):
        try:
            charter.attachment.delete(save=False)
        except Exception:
            pass
        charter.attachment = None
        content_changed = True

    if "is_active" in request.data:
        val = request.data["is_active"]
        new_val = val if isinstance(val, bool) else str(val).lower() == "true"
        if charter.is_active != new_val:
            charter.is_active = new_val
            settings_changed = True

    if "is_mandatory" in request.data:
        val = request.data["is_mandatory"]
        new_val = val if isinstance(val, bool) else str(val).lower() == "true"
        if charter.is_mandatory != new_val:
            charter.is_mandatory = new_val
            settings_changed = True

    charter.save()

    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''

    if content_changed:
        charter.version += 1
        charter.save()
        deleted = CharterAcceptance.objects.filter(charter=charter).delete()

        return Response({
            "success": True,
            "message": f"تم تحديث اللائحة (الإصدار {charter.version}) وتم إعادة طلب الموافقة من جميع الموظفين",
            "version": charter.version,
            "acceptances_reset": deleted[0],
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        })

    if settings_changed:
        return Response({
            "success": True,
            "message": "تم حفظ إعدادات اللائحة",
            "version": charter.version,
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        })

    return Response({
        "success": True,
        "message": "لم يتم إجراء أي تغيير",
        "version": charter.version,
        "attachment_url": attachment_url,
        "attachment_name": attachment_name,
    })


def _notify_hr_incomplete_data(employee, missing):
    """
    Send notification to HR when employee has incomplete data
    (only once per day per employee)
    """
    try:
        from django.core.cache import cache
        cache_key = f'notify_hr_incomplete_{employee.id}_{timezone.localdate()}'
        if cache.get(cache_key):
            return
        cache.set(cache_key, True, 86400)  # 24 hours
        
        from accounts.fcm_service import send_notification_to_managers
        
        emp_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
        
        missing_labels_ar = []
        missing_labels_en = []
        if 'worker_type' in missing:
            missing_labels_ar.append('نوع الموظف')
            missing_labels_en.append('worker type')
        if 'shift' in missing:
            missing_labels_ar.append('الشيفت')
            missing_labels_en.append('shift')
        
        title = 'موظف بيانات ناقصة'
        body = f'[{emp_name}] لم يستطع استخدام التطبيق - ناقص: {", ".join(missing_labels_ar)}'
        
        send_notification_to_managers(
            employee.company,
            title, body,
            data={
                'type': 'employee_incomplete_data',
                'employee_id': str(employee.id),
                'employee_name': emp_name,
                'missing': ','.join(missing),
            },
            title_en='Employee Data Incomplete',
            body_en=f'[{emp_name}] cannot use the app - missing: {", ".join(missing_labels_en)}',
        )
    except Exception:
        pass


```

======================================================================
## FILE: /var/www/motionhr/attendance/api_auto_checkin.py
======================================================================

```
"""
MotionHR - Auto Check-in / Check-out API
Phase 14: تسجيل حضور وانصراف أوتوماتيك - Bilingual AR/EN
"""
import math
from datetime import datetime, date, time
from django.db import models
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Attendance

# ─────────────────────────────────────────
# الرسائل AR/EN
# ─────────────────────────────────────────
MESSAGES = {
    'checked_in': {
        'ar': 'تم تسجيل حضورك تلقائياً ✅',
        'en': 'Attendance recorded automatically ✅',
    },
    'checked_in_late': {
        'ar': 'تم تسجيل حضورك — تأخير {minutes} دقيقة ⚠️',
        'en': 'Checked in — {minutes} minutes late ⚠️',
    },
    'checked_out': {
        'ar': 'تم تسجيل انصرافك تلقائياً ✅',
        'en': 'Check-out recorded automatically ✅',
    },
    'already_checked_in': {
        'ar': 'تم تسجيل الحضور مسبقاً',
        'en': 'Already checked in today',
    },
    'out_of_range': {
        'ar': 'أنت خارج نطاق موقع العمل',
        'en': 'You are outside the work location range',
    },
    'still_inside': {
        'ar': 'لا يزال داخل نطاق موقع العمل',
        'en': 'Still within work location range',
    },
    'no_checkin': {
        'ar': 'لم يتم تسجيل الحضور أو تم تسجيل الانصراف مسبقاً',
        'en': 'No check-in found or already checked out',
    },
    'not_checked_in': {
        'ar': 'لم يتم تسجيل الحضور بعد',
        'en': 'Not checked in yet',
    },
    'employee_not_found': {
        'ar': 'الموظف غير موجود',
        'en': 'Employee not found',
    },
    'invalid_coords': {
        'ar': 'إحداثيات غير صحيحة',
        'en': 'Invalid coordinates',
    },
    'coords_required': {
        'ar': 'يرجى إرسال الإحداثيات',
        'en': 'Latitude and longitude are required',
    },
}


def _msg(key, lang='ar', **kwargs):
    """جيب الرسالة بالغة المطلوبة"""
    lang = lang if lang in ('ar', 'en') else 'ar'
    text = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get('ar', key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def _get_user_lang(user, employee=None):
    """جيب لغة المستخدم من FCMDeviceToken أو Employee"""
    # أولاً من FCMDeviceToken
    try:
        from accounts.fcm_models import FCMDeviceToken
        token = FCMDeviceToken.objects.filter(user=user, is_active=True).first()
        lang = getattr(token, 'preferred_language', None)
        if lang in ('ar', 'en'):
            return lang
    except Exception:
        pass

    # ثانياً من Employee model
    if employee:
        lang = getattr(employee, 'language', None)
        if lang in ('ar', 'en'):
            return lang

    return 'ar'


def _haversine_distance(lat1, lon1, lat2, lon2):
    """المسافة بين نقطتين بالمتر"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_employee(user):
    try:
        from employees.models import Employee
        return Employee._base_manager.filter(user=user).first()
    except Exception:
        return None


def _get_active_geofence(employee):
    try:
        from .models import Geofence
        company = getattr(employee, 'company', None)
        if company:
            return Geofence.objects.filter(company=company, is_active=True).first()
        return Geofence.objects.filter(is_active=True).first()
    except Exception:
        return None


def _get_employee_shift(employee):
    try:
        from attendance.api_mobile import get_active_shift
        from django.utils import timezone
        return get_active_shift(employee, timezone.localdate())
    except Exception:
        return None


def _calculate_late_minutes(shift, check_in_time):
    if not shift:
        return 0
    try:
        from attendance.api_mobile import get_shift_periods
        from django.utils import timezone
        from datetime import timedelta, datetime
        
        today = timezone.localdate()
        now = timezone.now()
        grace = int(getattr(shift, 'grace_period', 15) or 15)
        periods = get_shift_periods(shift, today)
        
        if periods and periods[0].get('start'):
            start_dt = periods[0].get('start')
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
        elif shift.start_time:
            start_dt = datetime.combine(today, shift.start_time)
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
        else:
            return 0
            
        deadline = start_dt + timedelta(minutes=grace)
        diff = (now - deadline).total_seconds()
        
        if diff > 0:
            return int(diff // 60)
    except Exception as e:
        print("Late Calc Error:", e)
    return 0


def _send_auto_checkin_notification(user, employee, lang, check_in_str, late_minutes):
    """FCM notification بعد auto check-in"""
    try:
        from .fcm_logic import send_fcm_notification
        if late_minutes > 0:
            title_ar = 'تسجيل حضور تلقائي ⚠️'
            body_ar = f'تم تسجيل حضورك في {check_in_str} — تأخير {late_minutes} دقيقة'
            title_en = 'Auto Check-in ⚠️'
            body_en = f'Checked in at {check_in_str} — {late_minutes} min late'
        else:
            title_ar = 'تسجيل حضور تلقائي ✅'
            body_ar = f'تم تسجيل حضورك في {check_in_str} بدون تأخير'
            title_en = 'Auto Check-in ✅'
            body_en = f'Checked in at {check_in_str} — on time'

        title = title_en if lang == 'en' else title_ar
        body = body_en if lang == 'en' else body_ar

        send_fcm_notification(
            user, title, body,
            data={'type': 'auto_checkin', 'action': 'checkin'},
            title_en=title_en,
            body_en=body_en,
        )
    except Exception as e:
        print(f'Auto check-in FCM error: {e}')


def _send_auto_checkout_notification(user, employee, lang, check_out_str, work_hours, overtime_hours):
    """FCM notification بعد auto check-out"""
    try:
        from .fcm_logic import send_fcm_notification
        title_ar = 'تسجيل انصراف تلقائي ✅'
        body_ar = f'تم تسجيل انصرافك في {check_out_str} — {work_hours} ساعة عمل'
        title_en = 'Auto Check-out ✅'
        body_en = f'Checked out at {check_out_str} — {work_hours} hours worked'

        if overtime_hours > 0:
            body_ar += f' (أوفرتايم: {overtime_hours} ساعة)'
            body_en += f' (Overtime: {overtime_hours} hrs)'

        title = title_en if lang == 'en' else title_ar
        body = body_en if lang == 'en' else body_ar

        send_fcm_notification(
            user, title, body,
            data={'type': 'auto_checkout', 'action': 'checkout'},
            title_en=title_en,
            body_en=body_en,
        )
    except Exception as e:
        print(f'Auto check-out FCM error: {e}')


# ─────────────────────────────────────────
# API Views
# ─────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def auto_check_in(request):
    """
    تسجيل حضور أوتوماتيك
    Body: { "latitude": ..., "longitude": ... }
    """
    user = request.user
    emp = _get_employee(user)
    lang = _get_user_lang(user, emp)

    if not emp:
        return Response({'error': _msg('employee_not_found', lang)}, status=404)

    # ─── Device Approval Check ───
    device_id = request.data.get('device_id', '').strip()
    if device_id:
        try:
            from accounts.fcm_models import TrustedDevice
            device = TrustedDevice._base_manager.filter(user=user, device_id=device_id).first()
            if device and not device.auto_attendance_enabled:
                return Response({
                    'success': False,
                    'status': 'device_not_approved',
                    'message': 'الجهاز غير معتمد — Auto Attendance متوقف حتى موافقة المدير' if lang == 'ar' else 'Device not approved — Auto Attendance disabled until manager approval',
                }, status=403)
        except Exception:
            pass
    # ─────────────────────────────

    lat = request.data.get('latitude')
    lon = request.data.get('longitude')

    if lat is None or lon is None:
        # ATT-10b: تسجيل GPS Alert للمدير
        try:
            from attendance.models import TrackingAlert
            _today = timezone.localdate()
            _now = timezone.now()
            note = "GPS disabled during auto check-in"

            open_alert = TrackingAlert._base_manager.filter(
                company=emp.company,
                employee=emp,
                date=_today,
                status='open'
            ).filter(notes__icontains='GPS').first()

            if open_alert:
                open_alert.last_seen_at = _now
                open_alert.save(update_fields=['last_seen_at'])
            else:
                TrackingAlert._base_manager.create(
                    company=emp.company,
                    employee=emp,
                    date=_today,
                    started_at=_now,
                    last_seen_at=_now,
                    minutes_outside=0,
                    last_latitude=None,
                    last_longitude=None,
                    last_address='',
                    status='open',
                    notes=note,
                )
        except Exception:
            pass

        return Response({'error': _msg('coords_required', lang)}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return Response({'error': _msg('invalid_coords', lang)}, status=400)

    today = timezone.localdate()
    now = timezone.now()

    # منع الـ Auto Check-in خارج نافذة الشيفت
    shift = _get_employee_shift(emp)
    try:
        from attendance.api_mobile import get_shift_periods
        from attendance.company_policy_models import CompanyWorkPolicy
        from datetime import datetime, timedelta

        policy = CompanyWorkPolicy._base_manager.filter(company=emp.company).first()
        pre_window = int(getattr(policy, 'pre_shift_checkin_window', 15) or 15)

        start_candidates = []
        if shift:
            for base_day in [today - timedelta(days=1), today]:
                periods = get_shift_periods(shift, base_day)
                if periods and periods[0].get('start'):
                    candidate = periods[0].get('start')
                    if timezone.is_naive(candidate):
                        candidate = timezone.make_aware(candidate, timezone.get_current_timezone())
                    start_candidates.append(candidate)

            if not start_candidates and getattr(shift, 'start_time', None):
                candidate = datetime.combine(today, shift.start_time)
                if timezone.is_naive(candidate):
                    candidate = timezone.make_aware(candidate, timezone.get_current_timezone())
                start_candidates.append(candidate)

                shift_end = getattr(shift, 'end_time', None)
                if shift_end and shift_end <= shift.start_time:
                    prev_candidate = datetime.combine(today - timedelta(days=1), shift.start_time)
                    if timezone.is_naive(prev_candidate):
                        prev_candidate = timezone.make_aware(prev_candidate, timezone.get_current_timezone())
                    start_candidates.append(prev_candidate)

        matched_window = None
        nearest_window = None

        for start_dt in sorted(set(start_candidates)):
            allowed_from = start_dt - timedelta(minutes=pre_window)
            allowed_to = start_dt + timedelta(hours=4)

            if nearest_window is None or abs((start_dt - now).total_seconds()) < abs((nearest_window[0] - now).total_seconds()):
                nearest_window = (start_dt, allowed_from, allowed_to)

            if allowed_from <= now <= allowed_to:
                matched_window = (start_dt, allowed_from, allowed_to)
                break

        if start_candidates and matched_window is None:
            start_dt, allowed_from, allowed_to = nearest_window
            return Response({
                'status': 'outside_shift_window',
                'message': 'لا يمكن تسجيل الحضور التلقائي خارج وقت الشيفت',
                'shift_start': timezone.localtime(start_dt).strftime('%I:%M %p'),
                'allowed_from': timezone.localtime(allowed_from).strftime('%I:%M %p'),
                'allowed_to': timezone.localtime(allowed_to).strftime('%I:%M %p'),
            }, status=400)

    except Exception as e:
        print('AUTO WINDOW ERROR:', e)

    # هل عمل check-in النهارده أو امبارح (لشيفتات بعد نص الليل)؟
    from datetime import timedelta
    existing = Attendance._base_manager.filter(
        employee=emp,
        date__in=[today, today - timedelta(days=1)],
        check_in_time__isnull=False,
    ).order_by('-date').first()

    if existing:
        return Response({
            'status': 'already_checked_in',
            'message': _msg('already_checked_in', lang),
            'check_in': timezone.localtime(existing.check_in_time).strftime('%I:%M %p') if existing.check_in_time else None,
        })

    # ═══════════════════════════════════════════════════
    # Worker Type Check - فحص نوع الموظف
    # ═══════════════════════════════════════════════════
    worker_type = getattr(emp, 'worker_type', 'office') or 'office'
    company = emp.company
    
    # لو مكتبي - لازم من موقع الشركة
    if worker_type == 'office':
        if company and company.geofence_enabled and company.office_latitude and company.office_longitude:
            from attendance.location_utils import is_within_radius
            radius_check = is_within_radius(
                lat, lon,
                float(company.office_latitude),
                float(company.office_longitude),
                company.geofence_radius or 500,
            )
            if not radius_check['is_within']:
                return Response({
                    'status': 'out_of_range',
                    'message': f'لا يمكن تسجيل الحضور من هنا. الموظف المكتبي يجب أن يبصم من موقع الشركة (أنت على بعد {radius_check["distance_meters"]:.0f} متر).',
                    'distance_meters': radius_check['distance_meters'],
                }, status=400)
    
    # لو ميداني محدد - لازم من موقع معتمد
    elif worker_type == 'field_assigned':
        from attendance.models import EmployeeWorkLocation
        from attendance.location_utils import is_within_radius
        from django.db.models import Q
        
        approved_locations = EmployeeWorkLocation._base_manager.filter(
            company=company,
            status='approved',
            is_active=True,
        ).filter(
            Q(employee=emp) |
            Q(is_shared=True, shared_with_branch=None, shared_with_department=None) |
            Q(is_shared=True, shared_with_branch=emp.branch) |
            Q(is_shared=True, shared_with_department=emp.department)
        ).distinct()
        
        current_location = None
        for loc in approved_locations:
            check = is_within_radius(
                lat, lon,
                float(loc.latitude), float(loc.longitude),
                loc.radius or 500,
            )
            if check['is_within']:
                current_location = loc
                break
        
        if not current_location:
            available_names = [loc.name for loc in approved_locations[:5]]
            return Response({
                'status': 'outside_approved_locations',
                'message': 'الموقع الحالي غير معتمد. المواقع المتاحة: ' + ', '.join(available_names) if available_names else 'لا توجد مواقع معتمدة لك.',
                'approved_locations': available_names,
            }, status=400)
    
    # لو ميداني حر - أي مكان مسموح (بدون فحص)

    # حساب التأخير
    shift = _get_employee_shift(emp)
    local_now = timezone.localtime(now)
    check_in_time_only = local_now.time().replace(microsecond=0)
    late_minutes = _calculate_late_minutes(shift, check_in_time_only)
    status_val = 'late' if late_minutes > 0 else 'present'
    check_in_str = local_now.strftime('%I:%M %p')

    # إنشاء أو تحديث سجل الحضور (نستخدم now الكامل مش الوقت فقط)
    # شيفت بعد نص الليل: لازم السجل يتربط بيوم بداية الشيفت
    att_date = today
    if shift:
        from attendance.api_mobile import get_shift_periods
        from datetime import timedelta
        local_now_for_att_date = timezone.localtime(now)
        prev_periods = get_shift_periods(shift, today - timedelta(days=1))
        if prev_periods and prev_periods[0].get('start'):
            prev_start = prev_periods[0]['start']
            if timezone.is_naive(prev_start):
                prev_start = timezone.make_aware(prev_start, timezone.get_current_timezone())
            prev_end_estimate = prev_start + timedelta(hours=8)
            if prev_start <= local_now_for_att_date <= prev_end_estimate:
                att_date = today - timedelta(days=1)

    att, created = Attendance._base_manager.get_or_create(
        employee=emp,
        date=att_date,
        defaults={
            'check_in_time': now,
            'status': status_val,
            'late_minutes': late_minutes,
            'check_in_latitude': lat,
            'check_in_longitude': lon,
            'company': emp.company,
        }
    )

    if not created and att.check_in_time is None:
        att.check_in_time = now
        att.status = status_val
        att.late_minutes = late_minutes
        att.check_in_latitude = lat
        att.check_in_longitude = lon
        att.save()

    # FCM notification
    _send_auto_checkin_notification(user, emp, lang, check_in_str, late_minutes)

    # الرسالة
    if late_minutes > 0:
        message = _msg('checked_in_late', lang, minutes=late_minutes)
    else:
        message = _msg('checked_in', lang)

    return Response({
        'status': 'checked_in',
        'message': message,
        'check_in': check_in_str,
        'attendance_status': status_val,
        'late_minutes': late_minutes,
        'auto': True,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def auto_check_out(request):
    """
    تسجيل انصراف أوتوماتيك
    Body: { "latitude": ..., "longitude": ... }
    """
    user = request.user
    emp = _get_employee(user)
    lang = _get_user_lang(user, emp)

    if not emp:
        return Response({'error': _msg('employee_not_found', lang)}, status=404)

    lat = request.data.get('latitude')
    lon = request.data.get('longitude')

    if lat is None or lon is None:
        # ATT-10b: تسجيل GPS Alert للمدير
        try:
            from attendance.models import TrackingAlert
            _today = timezone.localdate()
            _now = timezone.now()
            note = "GPS disabled during auto check-in"

            open_alert = TrackingAlert._base_manager.filter(
                company=emp.company,
                employee=emp,
                date=_today,
                status='open'
            ).filter(notes__icontains='GPS').first()

            if open_alert:
                open_alert.last_seen_at = _now
                open_alert.save(update_fields=['last_seen_at'])
            else:
                TrackingAlert._base_manager.create(
                    company=emp.company,
                    employee=emp,
                    date=_today,
                    started_at=_now,
                    last_seen_at=_now,
                    minutes_outside=0,
                    last_latitude=None,
                    last_longitude=None,
                    last_address='',
                    status='open',
                    notes=note,
                )
        except Exception:
            pass

        return Response({'error': _msg('coords_required', lang)}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return Response({'error': _msg('invalid_coords', lang)}, status=400)

    today = timezone.localdate()
    now = timezone.now()
    from datetime import timedelta

    # لازم يكون عمل check-in الأول
    # بنبحث في اليوم الحالي واليوم السابق (شيفت بعد نص الليل)
    att = Attendance._base_manager.filter(
        employee=emp,
        date__in=[today, today - timedelta(days=1)],
        check_in_time__isnull=False,
        check_out_time__isnull=True,
    ).order_by('-date').first()

    if not att:
        return Response({
            'status': 'no_checkin',
            'message': _msg('no_checkin', lang),
        }, status=400)

    # ═══════════════════════════════════════════════════
    # للانصراف: الميداني الحر والمحدد مسموحلهم من أي مكان
    # المكتبي: فقط لو خرج من نطاق الشركة
    # ═══════════════════════════════════════════════════
    worker_type = getattr(emp, 'worker_type', 'office') or 'office'
    
    if worker_type == 'office':
        company = emp.company
        if company and company.geofence_enabled and company.office_latitude and company.office_longitude:
            from attendance.location_utils import is_within_radius
            radius_check = is_within_radius(
                lat, lon,
                float(company.office_latitude),
                float(company.office_longitude),
                company.geofence_radius or 500,
            )
            # المكتبي - يقدر ينصرف بس لو خرج من نطاق الشركة
            if radius_check['is_within']:
                return Response({
                    'status': 'still_inside',
                    'message': 'ما زلت داخل نطاق الشركة',
                }, status=400)
    
    # الميداني الحر والمحدد: مفيش فحص للانصراف (ممكن من أي مكان)

    # حساب ساعات العمل
    local_now = timezone.localtime(now)
    check_in_local = timezone.localtime(att.check_in_time)
    check_out_dt = local_now.replace(microsecond=0)
    check_in_dt = check_in_local.replace(microsecond=0)
    work_duration = check_out_dt - check_in_dt
    work_hours = round(max(0, work_duration.total_seconds()) / 3600, 2)
    check_out_str = local_now.strftime('%I:%M %p')

    # حساب الأوفرتايم
    shift = _get_employee_shift(emp)
    overtime_hours = 0.0
    if shift and shift.end_time:
        try:
            shift_end = shift.end_time
            if isinstance(shift_end, str):
                h, m = shift_end.split(':')
                shift_end = time(int(h), int(m))
            shift_end_dt = datetime.combine(today, shift_end)
            if check_out_dt > shift_end_dt:
                ot = check_out_dt - shift_end_dt
                overtime_hours = round(ot.total_seconds() / 3600, 2)
        except Exception:
            pass

    att.check_out_time = now
    att.work_hours = work_hours
    att.overtime_hours = overtime_hours
    att.check_out_latitude = lat
    att.check_out_longitude = lon
    att.save()

    # FCM notification
    _send_auto_checkout_notification(
        user, emp, lang, check_out_str,
        work_hours, overtime_hours,
    )

    return Response({
        'status': 'checked_out',
        'message': _msg('checked_out', lang),
        'check_in': timezone.localtime(att.check_in_time).strftime('%I:%M %p'),
        'check_out': check_out_str,
        'work_hours': work_hours,
        'overtime_hours': overtime_hours,
        'auto': True,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def auto_checkin_status(request):
    """حالة الحضور اليوم للموظف"""
    user = request.user
    emp = _get_employee(user)
    lang = _get_user_lang(user, emp)

    if not emp:
        return Response({'error': _msg('employee_not_found', lang)}, status=404)

    today = timezone.localdate()
    from datetime import timedelta

    # شيفت بعد نص الليل: نبحث في اليوم الحالي واليوم السابق
    att = Attendance._base_manager.filter(
        employee=emp,
        date__in=[today, today - timedelta(days=1)],
        check_in_time__isnull=False,
    ).order_by('-date').first()

    if not att:
        return Response({
            'status': 'not_checked_in',
            'message': _msg('not_checked_in', lang),
            'has_check_in': False,
            'has_check_out': False,
            'checked_in': False,
            'checked_out': False,
        })

    return Response({
        'success': True,
        'status': att.status,
        'has_check_in': att.check_in_time is not None,
        'has_check_out': att.check_out_time is not None,
        'checked_in': att.check_in_time is not None,
        'checked_out': att.check_out_time is not None,
        'check_in': timezone.localtime(att.check_in_time).strftime('%I:%M %p') if att.check_in_time else None,
        'check_out': timezone.localtime(att.check_out_time).strftime('%I:%M %p') if att.check_out_time else None,
        'work_hours': float(att.work_hours or 0),
        'late_minutes': int(att.late_minutes or 0),
        'overtime_hours': float(att.overtime_hours or 0),
    })

```

======================================================================
## FILE: /var/www/motionhr/attendance/api_mobile_requests.py
======================================================================

```
"""
APIs للطلبات والإجازات من تطبيق الموبايل
"""
from django.utils import timezone
from django.db.models import Q
from accounts.fcm_service import (
    notify_request_approved,
    notify_request_rejected,
    notify_leave_approved,
    notify_leave_rejected,
    notify_manager_new_request,
    notify_manager_new_leave,
)
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from employees.models import Employee
from leaves.models import LeaveType, LeaveBalance, LeaveRequest
from requests_app.models import RequestCategory, RequestType, EmployeeRequest


def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).select_related('company').first()


ROLE_LABELS_AR = {
    'direct_manager': 'المدير المباشر',
    'department_manager': 'مدير القسم',
    'branch_manager': 'مدير الفرع',
    'hr_manager': 'مدير الموارد البشرية',
    'company_admin': 'صاحب الشركة',
    'skip': '',
}


def get_current_approver_info(req):
    """يرجع معلومات المسؤول الحالي عن الطلب"""
    if req.status != 'pending':
        return None

    try:
        from requests_app.models import ApprovalFlow
        flow = ApprovalFlow._base_manager.filter(
            company=req.company,
            request_type=req.request_type
        ).first()

        if not flow:
            return {
                'step': 1,
                'role': 'direct_manager',
                'role_label': 'المدير المباشر',
                'approver_name': None,
            }

        current_step = req.current_step or 1
        role_field = f'step_{current_step}_role'
        role = getattr(flow, role_field, 'direct_manager')

        if role == 'skip':
            return None

        role_label = ROLE_LABELS_AR.get(role, role)
        approver_name = None

        # نحاول نجيب اسم المدير
        if role == 'direct_manager':
            emp = req.employee
            if emp and emp.direct_manager:
                approver_name = emp.direct_manager.full_name_ar or emp.direct_manager.user.username

        return {
            'step': current_step,
            'role': role,
            'role_label': role_label,
            'approver_name': approver_name,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════
# الإجازات
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_leave_types(request):
    """أنواع الإجازات المتاحة مع الرصيد"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    year = timezone.localdate().year
    leave_types_qs = LeaveType._base_manager.filter(
        company=employee.company, is_active=True
    )
    emp_gender = (getattr(employee, "gender", "") or "").lower()
    if emp_gender == "male":
        leave_types_qs = leave_types_qs.exclude(gender_restriction="female")
    elif emp_gender == "female":
        leave_types_qs = leave_types_qs.exclude(gender_restriction="male")
    leave_types = leave_types_qs.order_by('name')

    result = []
    for lt in leave_types:
        balance = LeaveBalance._base_manager.filter(
            company=employee.company,
            employee=employee,
            leave_type=lt,
            year=year
        ).first()

        result.append({
            'id': lt.id,
            'name': lt.name,
            'name_en': getattr(lt, 'name_en', '') or '',
            'category': lt.category,
            'days_allowed': lt.days_allowed,
            'is_paid': lt.is_paid,
            'requires_document': lt.requires_document,
            'color': lt.color,
            'balance': {
                'total': float(balance.total_days) if balance else 0,
                'used': float(balance.used_days) if balance else 0,
                'pending': float(balance.pending_days) if balance else 0,
                'remaining': float(balance.remaining_days) if balance else 0,
            } if balance else {
                'total': 0, 'used': 0, 'pending': 0, 'remaining': 0,
            }
        })

    return Response({'success': True, 'leave_types': result})


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_leave_substitutes(request):
    """قائمة الموظفين المتاحين كبديل — من نفس الشركة عدا الموظف نفسه"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    # exclude_employee_id → نستثني موظف معين (صاحب الإجازة)
    exclude_id = request.query_params.get('exclude_employee_id')

    from employees.models import Employee
    qs = Employee._base_manager.filter(
        company=employee.company,
        status='active',
    ).exclude(id=employee.id)

    if exclude_id:
        try:
            qs = qs.exclude(id=int(exclude_id))
        except (ValueError, TypeError):
            pass

    qs = qs.order_by('first_name_ar', 'last_name_ar')

    result = []
    for emp in qs:
        full_name = f"{emp.first_name_ar or ''} {emp.last_name_ar or ''}".strip()
        result.append({
            'id': emp.id,
            'name': full_name or emp.user.username,
            'job_title': getattr(getattr(emp, 'job_title', None), 'name', '') or '',
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
        })

    return Response({'success': True, 'substitutes': result, 'count': len(result)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_leave_request(request):
    """تقديم طلب إجازة"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    leave_type_id = request.data.get('leave_type_id')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    reason = request.data.get('reason', '').strip()
    half_day = request.data.get('half_day', False)
    half_day_type = request.data.get('half_day_type', 'morning').strip()
    substitute_employee_id = request.data.get('substitute_employee_id')

    if not all([leave_type_id, start_date, end_date]):
        return Response({
            'success': False,
            'message': 'نوع الإجازة وتاريخ البداية والنهاية مطلوبين'
        }, status=400)

    # REQ-1: السبب اختياري - نحط اسم النوع
    if not reason:
        try:
            _lt = LeaveType._base_manager.get(id=leave_type_id, company=employee.company)
            reason = _lt.name or 'إجازة'
        except Exception:
            reason = 'إجازة'


    try:
        leave_type = LeaveType._base_manager.get(
            id=leave_type_id, company=employee.company, is_active=True
        )
    except LeaveType.DoesNotExist:
        return Response({'success': False, 'message': 'نوع الإجازة غير موجود'}, status=404)

    from datetime import datetime
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response({
            'success': False,
            'message': 'صيغة التاريخ غلط. استخدم YYYY-MM-DD'
        }, status=400)

    if end < start:
        return Response({
            'success': False,
            'message': 'تاريخ النهاية لازم يكون بعد تاريخ البداية'
        }, status=400)

    # فحص التداخل مع إجازات موجودة
    overlap = LeaveRequest._base_manager.filter(
        company=employee.company,
        employee=employee,
        status__in=['pending', 'approved'],
        start_date__lte=end,
        end_date__gte=start,
    ).exists()
    if overlap:
        return Response({
            'success': False,
            'message': 'عندك إجازة موجودة بالفعل في نفس الفترة دي'
        }, status=400)

    # LEV-1: فحص لو الموظف حاضر في نفس الفترة
    from attendance.models import Attendance
    from datetime import timedelta

    conflict_dates = []
    check_date = start
    while check_date <= end:
        att = Attendance._base_manager.filter(
            employee=employee,
            date=check_date,
            check_in_time__isnull=False,
        ).first()
        if att:
            conflict_dates.append(check_date.isoformat())
        check_date += timedelta(days=1)

    if conflict_dates:
        return Response({
            'success': False,
            'message': f'لا يمكن تقديم إجازة - يوجد حضور مسجل في: {", ".join(conflict_dates)}',
            'conflict_dates': conflict_dates,
        }, status=400)


    if half_day and start_date == end_date:
        days_count = 0.5
    else:
        days_count = (end - start).days + 1

    # فحص الرصيد للإجازات المدفوعة فقط
    if leave_type.is_paid:
        year = start.year
        balance = LeaveBalance._base_manager.filter(
            company=employee.company,
            employee=employee,
            leave_type=leave_type,
            year=year,
        ).first()

        remaining = float(balance.remaining_days) if balance else 0
        if days_count > remaining:
            return Response({
                'success': False,
                'message': f'رصيدك من {leave_type.name} غير كافي. المتاح: {remaining} يوم، المطلوب: {days_count} يوم'
            }, status=400)

    _half_day_type_val = half_day_type if half_day and half_day_type in ('morning', 'afternoon') else ''
    _leave_hours = 4.0 if half_day else None

    _leave_notes = ''
    if half_day:
        _half_label = 'صباحي' if half_day_type == 'morning' else 'مسائي'
        _leave_notes = f'نص يوم ({_half_label})'

    # تحديد الموظف البديل لو موجود
    substitute_emp = None
    if substitute_employee_id:
        from employees.models import Employee
        try:
            substitute_emp = Employee._base_manager.get(
                id=substitute_employee_id,
                company=employee.company,
                status='active',
            )
        except Employee.DoesNotExist:
            pass

    leave_request = LeaveRequest._base_manager.create(
        company=employee.company,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        days_count=days_count,
        half_day_type=_half_day_type_val,
        leave_hours=_leave_hours,
        reason=reason,
        notes=_leave_notes if half_day else '',
        status='pending',
        substitute_employee=substitute_emp,
    )

    year = start.year
    balance = LeaveBalance._base_manager.filter(
        company=employee.company,
        employee=employee,
        leave_type=leave_type,
        year=year
    ).first()
    if balance:
        balance.pending_days = float(balance.pending_days) + days_count
        balance.save()

    # إشعار للمدير - طلب إجازة جديد
    try:
        leave_type_name = leave_type.name if leave_type else 'إجازة'
        employee_name = f"{employee.first_name_ar} {employee.last_name_ar}".strip() or employee.user.username
        notify_manager_new_leave(
            company=employee.company,
            employee_name=employee_name,
            leave_type=f"{leave_type_name} من {start} إلى {end} ({days_count} يوم)",
            leave_id=leave_request.id,
        )
    except Exception as e:
        print(f"FCM notification error: {e}")

    return Response({
        'success': True,
        'message': f'تم تقديم طلب الإجازة بنجاح ({days_count} يوم)',
        'request_id': leave_request.id,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_leaves(request):
    """عرض طلبات الإجازات الخاصة بي"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    search = request.query_params.get('search', '').strip()
    status_filter = request.query_params.get('status', '').strip().lower()

    leaves = LeaveRequest._base_manager.filter(
        employee=employee
    ).select_related('leave_type')

    if status_filter:
        leaves = leaves.filter(status=status_filter)

    if search:
        leaves = leaves.filter(
            Q(reason__icontains=search) |
            Q(leave_type__name__icontains=search)
        )

    leaves = leaves.order_by('-created_at')[:30]

    items = []
    for lr in leaves:
        items.append({
            'id': lr.id,
            'leave_type': lr.leave_type.name if lr.leave_type else '',
            'start_date': lr.start_date.strftime('%Y-%m-%d') if lr.start_date else '',
            'end_date': lr.end_date.strftime('%Y-%m-%d') if lr.end_date else '',
            'days_count': float(lr.days_count),
            'reason': lr.reason or '',
            'status': lr.status,
            'status_display': lr.get_status_display(),
            'created_at': lr.created_at.strftime('%Y-%m-%d %H:%M') if lr.created_at else '',
            'review_notes': lr.review_notes or '',
            'current_approver': _get_leave_approver_info(lr) if lr.status == 'pending' else None,
        })

    return Response({'success': True, 'items': items, 'leaves': items})


def _get_leave_approver_info(leave):
    """يرجع معلومات المسؤول عن الموافقة على الإجازة"""
    try:
        approver_name = None
        if leave.employee and leave.employee.direct_manager:
            approver_name = leave.employee.direct_manager.full_name_ar or leave.employee.direct_manager.user.username

        return {
            'step': 1,
            'role': 'direct_manager',
            'role_label': 'المدير المباشر',
            'approver_name': approver_name,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════
# الطلبات (إذن خروج / سلفة / إداري)
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_request_types(request):
    """أنواع الطلبات المتاحة"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    categories = RequestCategory._base_manager.filter(
        company=employee.company, is_active=True
    ).order_by('order', 'id')

    result = []
    for cat in categories:
        types = RequestType._base_manager.filter(
            company=employee.company, category=cat, is_active=True
        ).order_by('order', 'id')

        type_list = []
        for rt in types:
            type_list.append({
                'id': rt.id,
                'name': rt.name,
                'name_en': rt.name_en or '',
                'description': rt.description or '',
                'description_en': rt.description_en or '',
                'permission_kind': rt.permission_kind or 'none',
                'requires_date_range': rt.requires_date_range,
                'requires_amount': rt.requires_amount,
                'requires_document': rt.requires_document,
                'requires_approval': rt.requires_approval,
                'form_schema': rt.form_schema or {},
            })

        result.append({
            'id': cat.id,
            'name': cat.name,
            'name_en': cat.name_en or '',
            'icon': cat.icon,
            'color': cat.color,
            'types': type_list,
        })

    return Response({'success': True, 'categories': result})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_submit_request(request):
    """تقديم طلب (إذن / سلفة / إداري)"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    request_type_id = request.data.get('request_type_id')
    subject = (request.data.get("subject") or request.data.get("title", "")).strip()
    details = (request.data.get("details") or request.data.get("description", "")).strip()
    priority = request.data.get('priority', 'normal').strip()
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    amount = request.data.get('amount')
    permission_date = request.data.get('permission_date')
    permission_time_raw = request.data.get('permission_time')

    if not request_type_id:
        return Response({
            'success': False,
            'message': 'نوع الطلب مطلوب'
        }, status=400)

    try:
        request_type = RequestType._base_manager.get(
            id=request_type_id, company=employee.company, is_active=True
        )
    except RequestType.DoesNotExist:
        return Response({'success': False, 'message': 'نوع الطلب غير موجود'}, status=404)

    # REQ-1: العنوان تلقائي من اسم النوع لو مبعتش
    if not subject:
        subject = request_type.name or 'طلب'

    # التفاصيل اختيارية - لو مبعتش نحط رسالة افتراضية
    if not details:
        details = f'طلب {request_type.name}' if request_type.name else 'طلب'


    is_permission_request = request_type.permission_kind in ['late_arrival', 'early_leave']

    # ── Dynamic Form Data ─────────────────────────────
    form_schema = request_type.form_schema or {}
    schema_fields = form_schema.get('fields', []) if isinstance(form_schema, dict) else []
    raw_form_data = request.data.get('form_data', {})
    if not isinstance(raw_form_data, dict):
        raw_form_data = {}

    dynamic_form_data = {}
    for field in schema_fields:
        if not isinstance(field, dict):
            continue

        key = (field.get('key') or '').strip()
        if not key:
            continue

        value = raw_form_data.get(key, request.data.get(key))
        required = bool(field.get('required', False))
        field_type = (field.get('type') or 'text').strip().lower()

        is_empty = value in [None, '']
        if isinstance(value, str):
            is_empty = value.strip() == ''

        if required and is_empty:
            label_ar = field.get('label_ar') or key
            label_en = field.get('label_en') or key
            language = getattr(employee, 'language', 'ar') or 'ar'
            message_ar = f'حقل "{label_ar}" مطلوب'
            message_en = f'Field "{label_en}" is required'
            return Response({
                'success': False,
                'message': message_en if language == 'en' else message_ar,
                'message_ar': message_ar,
                'message_en': message_en,
                'field': key,
            }, status=400)

        if not is_empty:
            if field_type == 'number':
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    label_ar = field.get('label_ar') or key
                    label_en = field.get('label_en') or key
                    language = getattr(employee, 'language', 'ar') or 'ar'
                    message_ar = f'قيمة "{label_ar}" غير صحيحة'
                    message_en = f'Invalid value for "{label_en}"'
                    return Response({
                        'success': False,
                        'message': message_en if language == 'en' else message_ar,
                        'message_ar': message_ar,
                        'message_en': message_en,
                        'field': key,
                    }, status=400)

        dynamic_form_data[key] = value

    if is_permission_request:
        permission_date = permission_date or start_date

        if not permission_date or not permission_time_raw:
            language = getattr(employee, 'language', 'ar') or 'ar'
            message_ar = 'تاريخ ووقت الإذن مطلوبان'
            message_en = 'Permission date and time are required'
            return Response({
                'success': False,
                'message': message_en if language == 'en' else message_ar,
                'message_ar': message_ar,
                'message_en': message_en,
            }, status=400)

        start_date = permission_date
        end_date = permission_date

    if request_type.requires_amount and not amount:
        return Response({
            'success': False,
            'message': 'المبلغ مطلوب لهذا النوع من الطلبات'
        }, status=400)

    if request_type.requires_date_range and (not start_date or not end_date):
        return Response({
            'success': False,
            'message': 'تاريخ البداية والنهاية مطلوبين لهذا النوع'
        }, status=400)

    # ── فحص سياسة الأذونات (لأنواع الأذون: تأخير / استئذان) ──
    permission_checked = False
    permission_hours = None
    permission_policy = None

    # لو فيه duration_hours في الطلب → معناه إنه إذن
    duration_hours_raw = request.data.get('duration_hours')
    if duration_hours_raw:
        try:
            permission_hours = float(duration_hours_raw)
        except (ValueError, TypeError):
            permission_hours = None

    if permission_hours and permission_hours > 0:
        # نجيب سياسة الأذونات الخاصة بالشركة
        from requests_app.models import PermissionPolicy, PermissionUsage
        try:
            permission_policy = PermissionPolicy._base_manager.get(
                company=employee.company,
                is_active=True
            )
        except PermissionPolicy.DoesNotExist:
            # مفيش سياسة → ممنوع تقديم إذن
            return Response({
                'success': False,
                'message': 'سياسة الأذونات غير مفعلة للشركة. رجاء التواصل مع المدير.'
            }, status=400)

        # نجيب استهلاك الموظف للشهر الحالي
        today = timezone.localdate()
        current_month = today.strftime('%Y-%m')
        usage, _created = PermissionUsage._base_manager.get_or_create(
            company=employee.company,
            employee=employee,
            month=current_month,
        )

        # فحص عدد المرات
        if usage.used_times >= permission_policy.max_times_per_month:
            return Response({
                'success': False,
                'message': f'وصلت للحد الأقصى من عدد مرات الأذونات ({permission_policy.max_times_per_month} مرات/شهر)'
            }, status=400)

        # فحص عدد الساعات (المستهلك + الجديد)
        from decimal import Decimal
        new_total = usage.used_hours + Decimal(str(permission_hours))
        if new_total > permission_policy.max_hours_per_month:
            remaining = permission_policy.max_hours_per_month - usage.used_hours
            return Response({
                'success': False,
                'message': f'الساعات المتبقية ({float(remaining)} ساعة) لا تكفي. الحد الأقصى {float(permission_policy.max_hours_per_month)} ساعة/شهر'
            }, status=400)

        permission_checked = True

    parsed_start = None
    parsed_end = None
    if start_date:
        from datetime import datetime
        try:
            parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_date:
        from datetime import datetime
        try:
            parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            pass

    parsed_permission_time = None
    if permission_time_raw:
        from datetime import datetime
        for time_format in ('%H:%M', '%H:%M:%S'):
            try:
                parsed_permission_time = datetime.strptime(permission_time_raw, time_format).time()
                break
            except ValueError:
                continue

    from datetime import timedelta
    today = timezone.localdate()

    _requires_date = getattr(request_type, 'requires_date_range', False) or is_permission_request

    if _requires_date and parsed_start:
        if parsed_start > today + timedelta(days=90):
            return Response({
                'success': False,
                'message': 'تاريخ البداية لا يمكن أن يكون أكثر من 90 يوم في المستقبل'
            }, status=400)

        if parsed_start < today - timedelta(days=60):
            return Response({
                'success': False,
                'message': 'تاريخ البداية قديم جداً (أكثر من 60 يوم)'
            }, status=400)

    if _requires_date and parsed_end and parsed_start and parsed_end < parsed_start:
        return Response({
            'success': False,
            'message': 'تاريخ النهاية يجب أن يكون بعد تاريخ البداية أو نفسه'
        }, status=400)

    if is_permission_request and request_type.permission_kind == 'early_leave' and parsed_permission_time:
        try:
            from attendance.api_mobile import get_active_shift
            shift = get_active_shift(employee, parsed_start or today)
            if shift and shift.end_time:
                if parsed_permission_time >= shift.end_time:
                    return Response({
                        'success': False,
                        'message': 'لا يمكن طلب انصراف مبكر بعد نهاية الشيفت'
                    }, status=400)
        except Exception:
            pass

    _rt_name = (request_type.name or '').lower() if request_type else ''
    is_expense_request = ('مصروف' in _rt_name or 'expense' in _rt_name or 'reimburs' in _rt_name) and 'بدل' not in _rt_name

    if is_expense_request and parsed_start:
        from attendance.models import Attendance
        att = Attendance._base_manager.filter(
            employee=employee,
            date=parsed_start,
            check_in_time__isnull=False,
        ).first()

        if not att:
            return Response({
                'success': False,
                'message': 'لا يمكن رد المصروفات - لا يوجد حضور مسجل في هذا التاريخ'
            }, status=400)

        if parsed_permission_time is None:
            return Response({
                'success': False,
                'message': 'صيغة الوقت غير صحيحة',
                'message_ar': 'صيغة الوقت غير صحيحة',
                'message_en': 'Invalid time format'
            }, status=400)

    parsed_amount = None
    if amount:
        try:
            parsed_amount = float(amount)
        except ValueError:
            return Response({
                'success': False,
                'message': 'المبلغ غير صحيح'
            }, status=400)

    # REQ-3: Validation للسلفة والقرض
    _rt_name_lower = (request_type.name or '').lower() if request_type else ''
    is_advance_or_loan = any(k in _rt_name_lower for k in ['سلفة', 'قرض', 'advance', 'loan'])

    if is_advance_or_loan:
        if not parsed_amount or parsed_amount <= 0:
            return Response({
                'success': False,
                'message': 'المبلغ مطلوب لطلب السلفة/القرض ويجب أن يكون أكبر من صفر'
            }, status=400)

        # الحد الأقصى = 3 أضعاف الراتب الأساسي
        try:
            basic_salary = float(getattr(employee, 'basic_salary', 0) or 0)
        except Exception:
            basic_salary = 0

        if basic_salary <= 0:
            return Response({
                'success': False,
                'message': 'لا يمكن تقديم طلب سلفة - راتبك الأساسي غير محدد. تواصل مع HR'
            }, status=400)

        max_allowed = basic_salary * 3
        if parsed_amount > max_allowed:
            return Response({
                'success': False,
                'message': f'الحد الأقصى للسلفة {max_allowed:.0f} جنيه (3 أضعاف الراتب). المطلوب: {parsed_amount:.0f}'
            }, status=400)

        # فحص سلفة قائمة
        from django.db.models import Sum
        active_advances = EmployeeRequest._base_manager.filter(
            employee=employee,
            status__in=['pending', 'approved'],
            request_type__name__icontains='سلفة',
        ).exclude(status='rejected')

        active_loans = EmployeeRequest._base_manager.filter(
            employee=employee,
            status__in=['pending', 'approved'],
            request_type__name__icontains='قرض',
        ).exclude(status='rejected')

        total_active = (active_advances.aggregate(total=Sum('amount'))['total'] or 0) +                        (active_loans.aggregate(total=Sum('amount'))['total'] or 0)

        total_active = float(total_active)

        if total_active + parsed_amount > max_allowed:
            remaining = max_allowed - total_active
            return Response({
                'success': False,
                'message': f'لديك سلف/قروض قائمة بمبلغ {total_active:.0f} جنيه. المتبقي المسموح: {remaining:.0f} جنيه'
            }, status=400)


    emp_request = EmployeeRequest._base_manager.create(
        company=employee.company,
        employee=employee,
        request_type=request_type,
        subject=subject,
        details=details,
        form_data=dynamic_form_data,
        priority=priority,
        start_date=parsed_start,
        end_date=parsed_end,
        amount=parsed_amount,
        duration_hours=Decimal(str(permission_hours)) if permission_hours else None,
        permission_time=parsed_permission_time,
        status='pending',
        step_1_status='pending',
    )

    # Permission usage is recorded at actual check-in/check-out after approval.

    # إشعار للمدير - طلب جديد
    try:
        request_type_name = request_type.name if request_type else 'طلب'
        employee_name = f"{employee.first_name_ar} {employee.last_name_ar}".strip() or employee.user.username
        notify_manager_new_request(
            company=employee.company,
            employee_name=employee_name,
            request_type=f"{request_type_name} - {subject}",
            request_id=emp_request.id,
        )
    except Exception as e:
        print(f"FCM notification error: {e}")

    return Response({
        'success': True,
        'message': 'تم تقديم الطلب بنجاح',
        'request_id': emp_request.id,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_requests(request):
    """عرض طلباتي"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    search = request.query_params.get('search', '').strip()
    status_filter = request.query_params.get('status', '').strip().lower()

    requests_list = EmployeeRequest._base_manager.filter(
        employee=employee
    ).select_related('request_type', 'request_type__category')

    if status_filter:
        requests_list = requests_list.filter(status=status_filter)

    if search:
        requests_list = requests_list.filter(
            Q(subject__icontains=search) |
            Q(details__icontains=search) |
            Q(request_type__name__icontains=search) |
            Q(request_type__category__name__icontains=search)
        )

    requests_list = requests_list.order_by('-created_at')[:30]

    items = []
    for req in requests_list:
        items.append({
            'id': req.id,
            'type_name': req.request_type.name if req.request_type else '',
            'category_name': req.request_type.category.name if req.request_type and req.request_type.category else '',
            'subject': req.subject or '',
            'details': req.details or '',
            'priority': req.priority or 'normal',
            'start_date': req.start_date.strftime('%Y-%m-%d') if req.start_date else '',
            'end_date': req.end_date.strftime('%Y-%m-%d') if req.end_date else '',
            'amount': float(req.amount) if req.amount else None,
            'status': req.status,
            'status_display': req.get_status_display(),
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '',
            'review_notes': req.review_notes or '',
            'current_approver': get_current_approver_info(req),
        })

    return Response({'success': True, 'items': items, 'requests': items})


# ═══════════════════════════════════════════════════
# APIs للمدير
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_pending(request):
    """الطلبات المعلقة اللي محتاجة موافقة المدير"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    company = getattr(user, 'company', None)

    pending_leaves = LeaveRequest._base_manager.filter(
        status='pending'
    ).select_related('employee', 'leave_type').order_by('-created_at')

    if company:
        pending_leaves = pending_leaves.filter(company=company)

    # لو البديل مدير مؤقت → يشوف طلبات فريق المدير الغايب كمان
    try:
        from leaves.models import ManagerSubstitution
        from employees.models import Employee as _Emp
        today = timezone.localdate()
        my_emp = _Emp._base_manager.filter(user=user, company=company).first()
        if my_emp:
            active_subs = ManagerSubstitution._base_manager.filter(
                substitute_employee=my_emp,
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
            ).select_related('manager_employee')
            for sub in active_subs:
                mgr_emp = sub.manager_employee
                team_ids = list(
                    _Emp._base_manager.filter(
                        direct_manager=mgr_emp,
                        company=company,
                        status='active',
                    ).values_list('id', flat=True)
                )
                if team_ids:
                    extra_leaves = LeaveRequest._base_manager.filter(
                        status='pending',
                        company=company,
                        employee_id__in=team_ids,
                    ).select_related('employee', 'leave_type')
                    pending_leaves = (pending_leaves | extra_leaves).distinct()
    except Exception:
        pass

    search = request.query_params.get('search', '').strip()
    if search:
        pending_leaves = pending_leaves.filter(
            Q(employee__first_name_ar__icontains=search) |
            Q(employee__last_name_ar__icontains=search) |
            Q(reason__icontains=search) |
            Q(leave_type__name__icontains=search)
        )

    leave_items = []
    for lr in pending_leaves[:50]:
        emp_name = ''
        if lr.employee:
            emp_name = f"{getattr(lr.employee, 'first_name_ar', '')} {getattr(lr.employee, 'last_name_ar', '')}".strip()
        sub_emp = getattr(lr, 'substitute_employee', None)
        sub_name = ''
        sub_id = None
        if sub_emp:
            sub_name = f"{getattr(sub_emp, 'first_name_ar', '')} {getattr(sub_emp, 'last_name_ar', '')}".strip()
            sub_id = sub_emp.id

        leave_items.append({
            'id': lr.id,
            'type': 'leave',
            'employee_name': emp_name,
            'employee_id': lr.employee.id if lr.employee else None,
            'leave_type': lr.leave_type.name if lr.leave_type else '',
            'leave_type_category': lr.leave_type.category if lr.leave_type else '',
            'start_date': lr.start_date.strftime('%Y-%m-%d') if lr.start_date else '',
            'end_date': lr.end_date.strftime('%Y-%m-%d') if lr.end_date else '',
            'days_count': float(lr.days_count),
            'reason': lr.reason or '',
            'status': lr.status,
            'created_at': lr.created_at.strftime('%Y-%m-%d %H:%M') if lr.created_at else '',
            'substitute_employee_id': sub_id,
            'substitute_employee_name': sub_name,
        })

    pending_requests = EmployeeRequest._base_manager.filter(
        status='pending'
    ).select_related('employee', 'request_type', 'request_type__category').order_by('-created_at')

    if company:
        pending_requests = pending_requests.filter(company=company)

    request_items = []
    for req in pending_requests[:50]:
        emp_name = ''
        if req.employee:
            emp_name = f"{getattr(req.employee, 'first_name_ar', '')} {getattr(req.employee, 'last_name_ar', '')}".strip()
        request_items.append({
            'id': req.id,
            'type': 'request',
            'employee_name': emp_name,
            'type_name': req.request_type.name if req.request_type else '',
            'category_name': req.request_type.category.name if req.request_type and req.request_type.category else '',
            'subject': req.subject or '',
            'details': req.details or '',
            'amount': float(req.amount) if req.amount else None,
            'status': req.status,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '',
        })

    return Response({
        'success': True,
        'pending_leaves': leave_items,
        'pending_requests': request_items,
        'total_pending': len(leave_items) + len(request_items),
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_action(request):
    """موافقة أو رفض طلب"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    item_type = request.data.get('type', '').strip()
    item_id = request.data.get('id')
    action = request.data.get('action', '').strip()
    notes = request.data.get('notes', '').strip()

    if not all([item_type, item_id, action]):
        return Response({
            'success': False,
            'message': 'النوع والمعرف والإجراء مطلوبين'
        }, status=400)

    if action not in ['approve', 'reject']:
        return Response({
            'success': False,
            'message': 'الإجراء لازم يكون approve أو reject'
        }, status=400)

    if action == 'reject' and not notes:
        return Response({
            'success': False,
            'message': 'سبب الرفض مطلوب'
        }, status=400)

    try:
        if item_type == 'leave':
            item = LeaveRequest._base_manager.get(id=item_id)

            employee_user = None
            try:
                employee_user = item.employee.user
            except Exception:
                pass

            leave_type_name = ''
            try:
                leave_type_name = item.leave_type.name if hasattr(item, 'leave_type') and item.leave_type else 'إجازة'
            except Exception:
                leave_type_name = 'إجازة'

            if action == 'approve':
                # لو المدير بعت substitute_employee_id مع الاعتماد → نحطه في الطلب
                sub_id = request.data.get('substitute_employee_id')
                if sub_id:
                    try:
                        from employees.models import Employee as _Emp
                        sub_emp = _Emp._base_manager.get(
                            id=sub_id,
                            company=item.employee.company,
                            status='active',
                        )
                        item.substitute_employee = sub_emp
                        item.save(update_fields=['substitute_employee'])
                    except Exception:
                        pass

                leave_category = getattr(getattr(item, 'leave_type', None), 'category', '') or ''
                if leave_category == 'sick' and not getattr(item, 'substitute_employee', None):
                    return Response({
                        'success': False,
                        'message': 'لا يمكن اعتماد الإجازة المرضية بدون تحديد موظف بديل'
                    }, status=400)

                item.approve(user, notes)
                if employee_user:
                    try:
                        notify_leave_approved(
                            user=employee_user,
                            leave_type=leave_type_name,
                            start_date=str(item.start_date) if hasattr(item, 'start_date') else '',
                            end_date=str(item.end_date) if hasattr(item, 'end_date') else '',
                            leave_id=item.id,
                        )
                    except Exception as e:
                        print(f"FCM notification error: {e}")
            else:
                item.reject(user, notes)
                if employee_user:
                    try:
                        notify_leave_rejected(
                            user=employee_user,
                            leave_type=leave_type_name,
                            reason=notes,
                            leave_id=item.id,
                        )
                    except Exception as e:
                        print(f"FCM notification error: {e}")

            # إشعار داخل التطبيق
            try:
                from accounts.fcm_models import NotificationLog
                if employee_user:
                    if action == 'approve':
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='✅ تمت الموافقة على إجازتك',
                            body=f'تمت الموافقة على طلب {leave_type_name}',
                            notification_type='leave_approved',
                        )
                    else:
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='❌ تم رفض طلب إجازتك',
                            body=f'تم رفض طلب {leave_type_name}' + (f' - السبب: {notes}' if notes else ''),
                            notification_type='leave_rejected',
                        )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'تم {"الموافقة على" if action == "approve" else "رفض"} طلب الإجازة',
            })

        elif item_type == 'request':
            item = EmployeeRequest._base_manager.get(id=item_id)

            employee_user = None
            try:
                employee_user = item.employee.user
            except Exception:
                pass

            request_type_name = ''
            request_title = ''
            try:
                request_type_name = item.request_type.name if hasattr(item, 'request_type') and item.request_type else 'طلب'
                request_title = item.subject if hasattr(item, 'subject') else ''
            except Exception:
                request_type_name = 'طلب'

            if action == 'approve':
                item.status = 'approved'
                # لو طلب تعديل حضور → نطبق التعديل تلقائياً
                try:
                    _type_name = (item.request_type.name if item.request_type else '') or ''
                    if 'تعديل سجل حضور' in _type_name or 'Attendance Correction' in _type_name:
                        _form_data = item.form_data or {}
                        _att_date_str = _form_data.get('attendance_date') or (str(item.start_date) if item.start_date else None)
                        _correction_type = _form_data.get('correction_type', 'both')
                        _check_in_str = _form_data.get('correct_check_in')
                        _check_out_str = _form_data.get('correct_check_out')

                        if _att_date_str:
                            from datetime import datetime as _dt, date as _date_cls, time as _time_cls
                            from attendance.models import Attendance, AttendanceActionLog

                            try:
                                _att_date = _date_cls.fromisoformat(_att_date_str)
                                _att = Attendance._base_manager.filter(
                                    employee=item.employee,
                                    date=_att_date,
                                ).first()

                                if _att:
                                    _old_data = {
                                        'check_in_time': str(_att.check_in_time),
                                        'check_out_time': str(_att.check_out_time),
                                    }

                                    _tz_local = _tz.get_current_timezone()

                                    if _check_in_str and _correction_type in ('check_in', 'both', 'full_day'):
                                        try:
                                            _t = _dt.strptime(_check_in_str, '%H:%M').time()
                                            _att.check_in_time = _tz.make_aware(
                                                _dt.combine(_att_date, _t), _tz_local
                                            )
                                        except Exception:
                                            pass

                                    if _check_out_str and _correction_type in ('check_out', 'both', 'full_day'):
                                        try:
                                            _t = _dt.strptime(_check_out_str, '%H:%M').time()
                                            _att.check_out_time = _tz.make_aware(
                                                _dt.combine(_att_date, _t), _tz_local
                                            )
                                        except Exception:
                                            pass

                                    _att.is_manually_edited = True
                                    _att.admin_notes = f'[تعديل بموافقة HR] طلب #{item.id}'
                                    _att.calculate_work_hours()
                                    _att.save()

                                    AttendanceActionLog._base_manager.create(
                                        company=_att.company,
                                        attendance=_att,
                                        action_type='edit',
                                        performed_by=user,
                                        reason=f'تعديل بموافقة HR على طلب #{item.id}',
                                        old_data=_old_data,
                                        new_data={
                                            'check_in_time': str(_att.check_in_time),
                                            'check_out_time': str(_att.check_out_time),
                                        },
                                    )

                                    from attendance.models import DailyAttendanceSummary
                                    DailyAttendanceSummary.compute_for_day(item.employee, _att_date)

                            except Exception as _err:
                                import logging
                                logging.getLogger(__name__).warning(f'attendance correction error: {_err}')
                except Exception as _ce:
                    import logging
                    logging.getLogger(__name__).warning(f'correction hook error: {_ce}')
            else:
                item.status = 'rejected'
            item.reviewed_by = user
            item.reviewed_at = timezone.now()
            item.review_notes = notes
            item.save()

            # لو الطلب إذن تأخير أو انصراف مبكر → خصم من رصيد الأذونات
            if action == 'approve':
                try:
                    _kind = getattr(item.request_type, 'permission_kind', 'none')
                    if _kind in ('late_arrival', 'early_leave'):
                        from attendance.models import PermissionLedger
                        _form_data = item.form_data or {}
                        _duration_hours = float(_form_data.get('duration_hours', 0) or 0)
                        _minutes = int(_duration_hours * 60)
                        _ref_date = item.start_date or timezone.localdate()

                        if _minutes > 0:
                            _kind_label = 'إذن تأخير' if _kind == 'late_arrival' else 'إذن انصراف مبكر'
                            PermissionLedger._base_manager.create(
                                company=item.company,
                                employee=item.employee,
                                entry_type='manual_request',
                                minutes_used=_minutes,
                                count_used=1,
                                reference_date=_ref_date,
                                notes=f'{_kind_label} - طلب #{item.id} - {item.request_type.name}',
                            )
                except Exception as _le:
                    import logging
                    logging.getLogger(__name__).warning(f'PermissionLedger create error: {_le}')

            if employee_user:
                try:
                    if action == 'approve':
                        notify_request_approved(
                            user=employee_user,
                            request_type=request_type_name,
                            request_title=request_title,
                            request_id=item.id,
                        )
                    else:
                        notify_request_rejected(
                            user=employee_user,
                            request_type=request_type_name,
                            request_title=request_title,
                            reason=notes,
                            request_id=item.id,
                        )
                except Exception as e:
                    print(f"FCM notification error: {e}")

            # إشعار داخل التطبيق
            try:
                from accounts.fcm_models import NotificationLog
                if employee_user:
                    if action == 'approve':
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='✅ تمت الموافقة على طلبك',
                            body=f'تمت الموافقة على {request_type_name}: {request_title}',
                            notification_type='request_approved',
                        )
                    else:
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='❌ تم رفض طلبك',
                            body=f'تم رفض {request_type_name}: {request_title}' + (f' - السبب: {notes}' if notes else ''),
                            notification_type='request_rejected',
                        )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'تم {"الموافقة على" if action == "approve" else "رفض"} الطلب',
            })
        else:
            return Response({
                'success': False,
                'message': 'النوع لازم يكون leave أو request'
            }, status=400)

    except (LeaveRequest.DoesNotExist, EmployeeRequest.DoesNotExist):
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': f'حصل خطأ: {str(e)}'}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_employees_attendance(request):
    """سجل حضور الموظفين للمدير"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    from attendance.models import Attendance

    company = getattr(user, 'company', None)
    date_str = request.query_params.get('date')

    if date_str:
        from datetime import datetime
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    records = Attendance._base_manager.filter(
        date=target_date
    ).select_related('employee').order_by('employee__first_name_ar')

    if company:
        records = records.filter(company=company)

    items = []
    for att in records:
        emp_name = ''
        if att.employee:
            emp_name = f"{getattr(att.employee, 'first_name_ar', '')} {getattr(att.employee, 'last_name_ar', '')}".strip()

        def fmt(dt):
            if not dt:
                return ''
            try:
                return timezone.localtime(dt).strftime('%I:%M %p')
            except Exception:
                return str(dt)

        items.append({
            'employee_name': emp_name,
            'employee_code': getattr(att.employee, 'employee_code', '') if att.employee else '',
            'date': att.date.strftime('%Y-%m-%d') if att.date else '',
            'check_in_time': fmt(getattr(att, 'check_in_time', None)),
            'check_out_time': fmt(getattr(att, 'check_out_time', None)),
            'status': getattr(att, 'status', '') or '',
        })

    return Response({
        'success': True,
        'date': target_date.strftime('%Y-%m-%d'),
        'items': items,
        'total': len(items),
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_live_locations(request):
    """مواقع الموظفين اللحظية للخريطة"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    from attendance.models import LocationLog
    from django.db.models import Max

    company = getattr(user, 'company', None)

    employees = Employee._base_manager.filter(status='active')
    if company:
        employees = employees.filter(company=company)

    # فلترة حسب الدور: manager يشوف فريقه فقط
    if role == 'manager':
        try:
            from employees.visibility import get_visible_employees_qs
            visible_ids = list(get_visible_employees_qs(user).values_list('id', flat=True))
            employees = employees.filter(id__in=visible_ids)
        except Exception:
            # fallback: فريق مباشر
            mgr_emp = Employee._base_manager.filter(user=user).first()
            if mgr_emp:
                employees = employees.filter(direct_manager=mgr_emp)
            else:
                employees = employees.none()

    from django.utils import timezone
    from attendance.models import Attendance
    today = timezone.localdate()

    attendance_employee_ids = set(
        Attendance._base_manager.filter(
            employee__in=employees,
            date=today,
        ).exclude(
            check_in_time__isnull=True
        ).values_list('employee_id', flat=True)
    )

    items = []
    for emp in employees:
        has_attendance = emp.id in attendance_employee_ids
        last_log = LocationLog._base_manager.filter(
            employee=emp
        ).order_by('-timestamp').first()

        emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip()
        dept_name = getattr(getattr(emp, 'department', None), 'name_ar', '') or ''

        if not has_attendance:
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'department': dept_name,
                'latitude': None,
                'longitude': None,
                'accuracy': 0,
                'address': '',
                'timestamp': '',
                'status': 'inactive_no_attendance',
                'has_location': False,
                'attendance_registered': False,
                'status_note': 'لم يتم تسجيل حضوره في شيفت اليوم',
            })
            continue

        if last_log:
            log_date = last_log.timestamp.date() if last_log.timestamp else None
            is_online = log_date == today
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'department': dept_name,
                'latitude': float(last_log.latitude),
                'longitude': float(last_log.longitude),
                'accuracy': float(last_log.accuracy) if last_log.accuracy else 0,
                'address': getattr(last_log, 'address', '') or '',
                'timestamp': last_log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_log.timestamp else '',
                'status': 'online' if is_online else 'offline',
                'has_location': True,
                'attendance_registered': True,
                'status_note': '' if is_online else 'آخر موقع مسجل ليس من اليوم',
            })
        else:
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'department': dept_name,
                'latitude': None,
                'longitude': None,
                'accuracy': 0,
                'address': '',
                'timestamp': '',
                'status': 'no_data',
                'has_location': False,
                'attendance_registered': True,
                'status_note': 'تم تسجيل الحضور ولكن لا يوجد موقع مباشر بعد',
            })

    return Response({
        'success': True,
        'items': items,
        'total': len(items),
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_employee_route(request):
    """خط سير موظف معين في يوم معين"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    employee_id = request.query_params.get('employee_id')
    if not employee_id:
        return Response({'success': False, 'message': 'employee_id مطلوب'}, status=400)

    try:
        employee_id = int(employee_id)
    except Exception:
        return Response({'success': False, 'message': 'employee_id غير صحيح'}, status=400)

    company = getattr(user, 'company', None)

    from datetime import datetime
    target_date_str = request.query_params.get('date', '').strip()
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'success': False, 'message': 'صيغة التاريخ لازم تكون YYYY-MM-DD'}, status=400)
    else:
        target_date = timezone.localdate()

    emp_qs = Employee._base_manager.filter(id=employee_id)
    if company:
        emp_qs = emp_qs.filter(company=company)

    employee = emp_qs.first()
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    from attendance.models import LocationLog

    logs = LocationLog._base_manager.filter(
        employee=employee,
        timestamp__date=target_date
    ).order_by('timestamp')[:500]

    emp_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
    if not emp_name:
        emp_name = employee.employee_code or f"Employee #{employee.id}"

    points = []
    for log in logs:
        points.append({
            'latitude': float(log.latitude),
            'longitude': float(log.longitude),
            'accuracy': float(log.accuracy) if log.accuracy else 0,
            'address': getattr(log, 'address', '') or '',
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
        })

    return Response({
        'success': True,
        'employee': {
            'id': employee.id,
            'name': emp_name,
            'employee_code': employee.employee_code or '',
        },
        'date': target_date.strftime('%Y-%m-%d'),
        'points': points,
        'total_points': len(points),
    })


# ─────────────────────────────────────────────────────────────
# تعديل طلب قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_edit_request(request, request_id):
    """الموظف يعدّل طلبه لو لسه pending"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id, employee=employee)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status != 'pending':
        return Response({
            'success': False,
            'message': f'لا يمكن تعديل الطلب — حالته الحالية: {req.get_status_display()}'
        }, status=400)

    d = request.data
    if 'subject' in d:
        req.subject = d['subject']
    if 'details' in d:
        req.details = d['details']
    if 'priority' in d:
        req.priority = d['priority']
    if 'start_date' in d:
        req.start_date = d['start_date'] or None
    if 'end_date' in d:
        req.end_date = d['end_date'] or None
    if 'amount' in d:
        req.amount = d['amount'] or None
    if 'duration_hours' in d:
        req.duration_hours = d['duration_hours'] or None
    req.save()

    return Response({
        'success': True,
        'message': 'تم تعديل الطلب بنجاح',
        'request_id': req.id,
        'status': req.status,
    })


# ─────────────────────────────────────────────────────────────
# إلغاء طلب قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_cancel_request(request, request_id):
    """الموظف يلغي طلبه لو لسه pending أو manager_approved"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id, employee=employee)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    # فحص إمكانية الإلغاء
    if req.status in ('cancelled', 'rejected'):
        return Response({
            'success': False,
            'message': f'لا يمكن إلغاء الطلب — حالته: {req.get_status_display()}'
        }, status=400)

    # لو الطلب معتمد، لازم يكون قبل تاريخ التنفيذ
    if req.status in ('approved', 'hr_approved'):
        _ref_date = req.start_date or timezone.localdate()
        _today = timezone.localdate()
        if _ref_date <= _today:
            return Response({
                'success': False,
                'message': 'لا يمكن إلغاء الإذن بعد تاريخ تنفيذه'
            }, status=400)

    reason = request.data.get('reason', 'إلغاء بواسطة الموظف')
    _was_approved = req.status in ('approved', 'hr_approved')
    req.status = 'cancelled'
    req.review_notes = f'[إلغاء الموظف] {reason}'
    req.save()

    # لو كان معتمد وإذن (تأخير/انصراف مبكر) → نرجع الرصيد
    if _was_approved:
        try:
            _kind = getattr(req.request_type, 'permission_kind', 'none')
            if _kind in ('late_arrival', 'early_leave'):
                from attendance.models import PermissionLedger
                _form_data = req.form_data or {}
                _duration_hours = float(_form_data.get('duration_hours', 0) or 0)
                _minutes = int(_duration_hours * 60)
                _ref_date = req.start_date or timezone.localdate()

                if _minutes > 0:
                    PermissionLedger._base_manager.create(
                        company=req.company,
                        employee=req.employee,
                        entry_type='rollback',
                        minutes_used=-_minutes,
                        count_used=-1,
                        reference_date=_ref_date,
                        notes=f'إلغاء إذن - طلب #{req.id} - {req.request_type.name}',
                    )
        except Exception as _le:
            import logging
            logging.getLogger(__name__).warning(f'PermissionLedger rollback error: {_le}')

    return Response({
        'success': True,
        'message': 'تم إلغاء الطلب بنجاح',
        'request_id': req.id,
    })


# ─────────────────────────────────────────────────────────────
# تعديل إجازة قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_edit_leave(request, leave_id):
    """الموظف يعدّل طلب إجازته لو لسه pending"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id, employee=employee)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status != 'pending':
        return Response({
            'success': False,
            'message': f'لا يمكن تعديل الإجازة — حالتها: {leave.get_status_display()}'
        }, status=400)

    d = request.data
    if 'start_date' in d:
        leave.start_date = d['start_date']
    if 'end_date' in d:
        leave.end_date = d['end_date']
    if 'reason' in d:
        leave.reason = d['reason']
    leave.save()

    return Response({
        'success': True,
        'message': 'تم تعديل طلب الإجازة بنجاح',
        'leave_id': leave.id,
    })


# ─────────────────────────────────────────────────────────────
# إلغاء إجازة قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_cancel_leave(request, leave_id):
    """الموظف يلغي طلب إجازته لو لسه pending"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id, employee=employee)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status in ('approved', 'cancelled', 'rejected'):
        return Response({
            'success': False,
            'message': f'لا يمكن إلغاء الإجازة — حالتها: {leave.get_status_display()}'
        }, status=400)

    leave.status = 'cancelled'
    leave.save()

    return Response({
        'success': True,
        'message': 'تم إلغاء طلب الإجازة بنجاح',
        'leave_id': leave.id,
    })



# ─────────────────────────────────────────────────────────────
# المدير/HR: تعديل أي طلب
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_edit_request(request, request_id):
    """المدير أو HR يعدّل أي طلب في أي مرحلة"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status in ('cancelled',):
        return Response({
            'success': False,
            'message': 'لا يمكن تعديل طلب ملغي'
        }, status=400)

    d = request.data
    if 'subject' in d:
        req.subject = d['subject']
    if 'details' in d:
        req.details = d['details']
    if 'priority' in d:
        req.priority = d['priority']
    if 'start_date' in d:
        req.start_date = d['start_date'] or None
    if 'end_date' in d:
        req.end_date = d['end_date'] or None
    if 'amount' in d:
        req.amount = d['amount'] or None
    if 'duration_hours' in d:
        req.duration_hours = d['duration_hours'] or None
    if 'status' in d and role in ('company_admin', 'hr_manager', 'super_admin'):
        req.status = d['status']
    if 'review_notes' in d:
        req.review_notes = d['review_notes']
    req.save()

    return Response({
        'success': True,
        'message': 'تم تعديل الطلب بنجاح',
        'request_id': req.id,
        'status': req.status,
        'status_display': req.get_status_display(),
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: إلغاء أي طلب
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_cancel_request(request, request_id):
    """المدير أو HR يلغي أي طلب"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status == 'cancelled':
        return Response({'success': False, 'message': 'الطلب ملغي مسبقاً'}, status=400)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'success': False, 'message': 'سبب الإلغاء مطلوب'}, status=400)

    req.status = 'cancelled'
    req.review_notes = f'[إلغاء المدير/HR] {reason}'
    req.save()

    return Response({
        'success': True,
        'message': 'تم إلغاء الطلب بنجاح',
        'request_id': req.id,
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: إعادة فتح طلب مرفوض
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_reopen_request(request, request_id):
    """HR يعيد فتح طلب مرفوض أو ملغي"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح - HR فقط'}, status=403)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status not in ('rejected', 'cancelled'):
        return Response({
            'success': False,
            'message': f'يمكن إعادة الفتح فقط للطلبات المرفوضة أو الملغية — الحالة الحالية: {req.get_status_display()}'
        }, status=400)

    notes = request.data.get('notes', '')
    req.status = 'pending'
    req.current_step = 1
    req.step_1_status = 'pending'
    req.review_notes = f'[إعادة فتح] {notes}'
    req.reviewed_by = None
    req.reviewed_at = None
    req.save()

    return Response({
        'success': True,
        'message': 'تمت إعادة فتح الطلب بنجاح — في انتظار الموافقة من جديد',
        'request_id': req.id,
        'status': req.status,
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: تعديل إجازة
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_edit_leave(request, leave_id):
    """المدير أو HR يعدّل طلب إجازة"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status == 'cancelled':
        return Response({'success': False, 'message': 'لا يمكن تعديل إجازة ملغية'}, status=400)

    d = request.data
    if 'start_date' in d:
        leave.start_date = d['start_date']
    if 'end_date' in d:
        leave.end_date = d['end_date']
    if 'reason' in d:
        leave.reason = d['reason']
    if 'status' in d and role in ('company_admin', 'hr_manager', 'super_admin'):
        new_status = d['status']
        leave_category = getattr(getattr(leave, 'leave_type', None), 'category', '') or ''
        if new_status == 'approved' and leave_category == 'sick' and not (
            d.get('substitute_employee_id') or getattr(leave, 'substitute_employee_id', None)
        ):
            return Response({
                'success': False,
                'message': 'لا يمكن اعتماد الإجازة المرضية بدون تحديد موظف بديل'
            }, status=400)
        leave.status = new_status
    if 'substitute_employee_id' in d:
        from employees.models import Employee
        try:
            sub = Employee._base_manager.get(
                id=d['substitute_employee_id'],
                company=leave.employee.company,
                status='active',
            )
            leave.substitute_employee = sub
        except Employee.DoesNotExist:
            pass
    leave.save()

    return Response({
        'success': True,
        'message': 'تم تعديل طلب الإجازة بنجاح',
        'leave_id': leave.id,
        'status': leave.status,
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: إلغاء إجازة
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_cancel_leave(request, leave_id):
    """المدير أو HR يلغي طلب إجازة"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status == 'cancelled':
        return Response({'success': False, 'message': 'الإجازة ملغية مسبقاً'}, status=400)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'success': False, 'message': 'سبب الإلغاء مطلوب'}, status=400)

    # cancel() بترجع الرصيد تلقائيًا
    leave.cancel()
    if hasattr(leave, 'cancel_reason'):
        leave.cancel_reason = reason
        leave.save(update_fields=['cancel_reason'])

    return Response({
        'success': True,
        'message': 'تم إلغاء طلب الإجازة وإرجاع الرصيد بنجاح',
        'leave_id': leave.id,
    })



# ══════════════════════════════════════════════════════
# LEAVE RECALL APIs
# ══════════════════════════════════════════════════════

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_leave_recall(request):
    """المدير أو صاحب الشركة يطلب استدعاء موظف من إجازته"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    d = request.data
    employee_id = d.get('employee_id')
    recall_date_raw = d.get('recall_date')
    reason = d.get('reason', '').strip()

    if not all([employee_id, recall_date_raw, reason]):
        return Response({'success': False, 'message': 'employee_id و recall_date و reason مطلوبين'}, status=400)

    try:
        from datetime import datetime as dt
        recall_date = dt.strptime(str(recall_date_raw), '%Y-%m-%d').date()
    except ValueError:
        return Response({'success': False, 'message': 'صيغة التاريخ لازم تكون YYYY-MM-DD'}, status=400)

    try:

        company = getattr(request.user, 'company', None)
        employee = Employee._base_manager.get(id=employee_id, company=company)

        leave_request = LeaveRequest._base_manager.filter(
            employee=employee,
            status='approved',
            start_date__lte=recall_date,
            end_date__gte=recall_date,
        ).first()

        if not leave_request:
            return Response({'success': False, 'message': 'الموظف مش في إجازة معتمدة في هذا اليوم'}, status=400)

        if LeaveRecallRequest._base_manager.filter(
            employee=employee,
            recall_date=recall_date,
        ).exists():
            return Response({'success': False, 'message': 'يوجد طلب استدعاء بالفعل لهذا اليوم'}, status=400)

        recall = LeaveRecallRequest._base_manager.create(
            company=company,
            employee=employee,
            leave_request=leave_request,
            recall_date=recall_date,
            reason=reason,
            requested_by=request.user,
            status='pending',
            created_by=request.user,
        )

        # إشعار HR
        try:
            from accounts.fcm_service import send_push_to_role
            emp_name = getattr(employee, 'full_name_ar', str(employee))
            send_push_to_role(
                company=company,
                role='hr_manager',
                title='🔔 طلب استدعاء من إجازة',
                body=f'تم طلب استدعاء {emp_name} من إجازته يوم {recall_date}',
                data={'type': 'leave_recall', 'recall_id': str(recall.id)},
            )
            recall.hr_notified = True
            recall.save(update_fields=['hr_notified'])
        except Exception:
            pass

        # لو صاحب الشركة هو اللي طلب → يعتمد مباشرة
        if role in ('company_admin', 'super_admin'):
            recall.approve(request.user, notes='اعتماد تلقائي من صاحب الشركة')

        return Response({
            'success': True,
            'recall_id': recall.id,
            'status': recall.status,
            'message': 'تم إنشاء طلب الاستدعاء' if recall.status == 'pending' else 'تم الاستدعاء والاعتماد مباشرة ✅',
        }, status=201)

    except Employee.DoesNotExist:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def review_leave_recall(request, recall_id):
    """HR أو صاحب الشركة يوافق أو يرفض طلب الاستدعاء"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح - للـ HR وصاحب الشركة فقط'}, status=403)

    action = request.data.get('action', '').strip().lower()
    notes = request.data.get('notes', '').strip()

    if action not in ('approve', 'reject'):
        return Response({'success': False, 'message': 'action لازم يكون approve أو reject'}, status=400)

    try:
        from leaves.models import LeaveRecallRequest
        company = getattr(request.user, 'company', None)
        recall = LeaveRecallRequest._base_manager.get(id=recall_id, company=company)

        if recall.status != 'pending':
            return Response({'success': False, 'message': f'الطلب حالته {recall.get_status_display()} مش pending'}, status=400)

        if action == 'approve':
            recall.approve(request.user, notes=notes)
            msg = f'تم الموافقة على استدعاء {recall.employee} يوم {recall.recall_date} ✅'
        else:
            recall.reject(request.user, notes=notes)
            msg = f'تم رفض طلب استدعاء {recall.employee} يوم {recall.recall_date}'

        # إشعار المدير اللي طلب
        try:
            from accounts.fcm_service import send_push_to_user
            if recall.requested_by:
                send_push_to_user(
                    user=recall.requested_by,
                    title='✅ استدعاء من إجازة' if action == 'approve' else '❌ رفض استدعاء',
                    body=msg,
                    data={'type': 'leave_recall_reviewed', 'recall_id': str(recall.id)},
                )
        except Exception:
            pass

        return Response({'success': True, 'message': msg, 'status': recall.status})

    except LeaveRecallRequest.DoesNotExist:
        return Response({'success': False, 'message': 'طلب الاستدعاء غير موجود'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_leave_recalls(request):
    """قائمة طلبات الاستدعاء"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        from leaves.models import LeaveRecallRequest
        company = getattr(request.user, 'company', None)
        status_filter = request.GET.get('status')

        qs = LeaveRecallRequest._base_manager.filter(
            company=company,
        ).select_related('employee', 'leave_request', 'requested_by', 'reviewed_by').order_by('-recall_date')

        if status_filter:
            qs = qs.filter(status=status_filter)

        data = []
        for r in qs[:100]:
            data.append({
                'id': r.id,
                'employee_id': r.employee_id,
                'employee_name': getattr(r.employee, 'full_name_ar', str(r.employee)),
                'recall_date': str(r.recall_date),
                'reason': r.reason,
                'status': r.status,
                'status_display': r.get_status_display(),
                'requested_by': r.requested_by.get_full_name() if r.requested_by else '',
                'reviewed_by': r.reviewed_by.get_full_name() if r.reviewed_by else '',
                'reviewed_at': str(r.reviewed_at) if r.reviewed_at else None,
                'review_notes': r.review_notes,
                'balance_restored': r.balance_restored,
                'hr_notified': r.hr_notified,
            })

        return Response({'success': True, 'recalls': data, 'count': len(data)})

    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def hr_create_leave(request):
    """إضافة إجازة من HR/company_admin لأي موظف"""
    from datetime import datetime
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ("company_admin", "hr_manager", "super_admin") and not request.user.is_superuser:
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    company = getattr(request.user, "company", None)
    if not company:
        emp = Employee._base_manager.filter(user=request.user).first()
        if emp:
            company = emp.company
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    employee_id = request.data.get("employee_id")
    leave_type_id = request.data.get("leave_type_id")
    start_date_str = request.data.get("start_date")
    end_date_str = request.data.get("end_date")
    reason = (request.data.get("reason") or "").strip()
    status_val = request.data.get("status", "approved")
    half_day = request.data.get("half_day", False)

    if not all([employee_id, leave_type_id, start_date_str, end_date_str, reason]):
        return Response({"success": False, "error": "الموظف ونوع الإجازة والتواريخ والسبب مطلوبة"}, status=400)

    try:
        employee = Employee._base_manager.get(id=employee_id, company=company)
    except Employee.DoesNotExist:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    try:
        leave_type = LeaveType._base_manager.get(id=leave_type_id, company=company, is_active=True)
    except LeaveType.DoesNotExist:
        return Response({"success": False, "error": "نوع الإجازة غير موجود"}, status=404)

    emp_gender = (getattr(employee, "gender", "") or "").lower()
    lt_restriction = getattr(leave_type, "gender_restriction", "all")
    if lt_restriction == "female" and emp_gender != "female":
        return Response({"success": False, "error": "هذه الإجازة للإناث فقط"}, status=400)
    if lt_restriction == "male" and emp_gender != "male":
        return Response({"success": False, "error": "هذه الإجازة للذكور فقط"}, status=400)

    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"success": False, "error": "صيغة التاريخ غير صحيحة"}, status=400)

    if end < start:
        return Response({"success": False, "error": "تاريخ النهاية قبل البداية"}, status=400)

    days_count = 0.5 if (half_day and start_date_str == end_date_str) else (end - start).days + 1

    if leave_type.is_paid:
        balance = LeaveBalance._base_manager.filter(
            company=company, employee=employee, leave_type=leave_type, year=start.year
        ).first()
        remaining = float(balance.remaining_days) if balance else 0
        if days_count > remaining:
            return Response({"success": False, "error": f"الرصيد غير كافي. المتاح: {remaining} يوم"}, status=400)

    if status_val not in ("pending", "approved"):
        status_val = "approved"

    # إجبار البديل في المرضية عند الإنشاء المباشر كـ approved
    leave_category = getattr(leave_type, 'category', '') or ''
    if status_val == 'approved' and leave_category == 'sick':
        _sub_id = request.data.get('substitute_employee_id')
        if not _sub_id:
            return Response({
                'success': False,
                'error': 'لا يمكن اعتماد الإجازة المرضية بدون تحديد موظف بديل'
            }, status=400)

    # البديل لو بعته المدير أو HR
    substitute_emp = None
    substitute_employee_id = request.data.get('substitute_employee_id')
    if substitute_employee_id:
        from employees.models import Employee as _Emp
        try:
            substitute_emp = _Emp._base_manager.get(
                id=substitute_employee_id,
                company=company,
                status='active',
            )
        except _Emp.DoesNotExist:
            pass

    leave_request = LeaveRequest._base_manager.create(
        company=company,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        days_count=days_count,
        reason=reason,
        status=status_val,
        substitute_employee=substitute_emp,
    )

    if status_val == "approved":
        balance = LeaveBalance._base_manager.filter(
            company=company, employee=employee, leave_type=leave_type, year=start.year
        ).first()
        if balance:
            balance.used_days = float(balance.used_days or 0) + days_count
            balance.save(update_fields=["used_days"])

    return Response({
        "success": True,
        "message": f"تم إضافة الإجازة ({days_count} يوم)",
        "request_id": leave_request.id,
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def hr_leave_types(request):
    """أنواع الإجازات للـ HR/company_admin — بدون حاجة لـ employee profile"""
    try:
        company = getattr(request.user, "company", None)
        if not company:
            from employees.models import Employee
            emp = Employee._base_manager.filter(user=request.user).first()
            if emp:
                company = emp.company

        if not company:
            return Response({"success": False, "message": "لا توجد شركة مرتبطة"}, status=400)

        year = timezone.localdate().year
        leave_types = LeaveType._base_manager.filter(
            company=company, is_active=True
        ).order_by("name")

        result = []
        for lt in leave_types:
            result.append({
                "id": lt.id,
                "name": lt.name,
                "name_en": getattr(lt, "name_en", "") or "",
                "category": lt.category,
                "days_allowed": lt.days_allowed,
                "is_paid": lt.is_paid,
                "requires_document": lt.requires_document,
                "color": lt.color,
            })

        return Response({"success": True, "leave_types": result, "count": len(result)})

    except Exception as e:
        logger.exception("hr_leave_types error")
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_substitution_summary(request):
    """
    GET: ملخص اللي حصل أثناء غياب المدير
    POST: تعليم إن المدير شاف الملخص (summary_viewed=True)
    """
    from leaves.models import ManagerSubstitution, LeaveRequest
    from employees.models import Employee as _Emp
    from requests_app.models import EmployeeRequest
    from attendance.missions_models import Mission

    company = getattr(request.user, 'company', None)
    if not company:
        return Response({'error': 'لا توجد شركة'}, status=400)

    mgr_emp = _Emp._base_manager.filter(user=request.user, company=company).first()
    if not mgr_emp:
        return Response({'error': 'لم يتم العثور على الموظف'}, status=404)

    # POST → عليم إن المدير شاف الملخص
    if request.method == 'POST':
        ManagerSubstitution._base_manager.filter(
            manager_employee=mgr_emp,
            summary_viewed=False,
        ).update(summary_viewed=True)
        return Response({'success': True, 'message': 'تم تعليم الملخص كمُراجَع'})

    # GET → رجّع الملخص
    # نجيب آخر تفويض منتهي للمدير
    last_sub = ManagerSubstitution._base_manager.filter(
        manager_employee=mgr_emp,
    ).order_by('-end_date').first()

    if not last_sub:
        return Response({
            'success': True,
            'has_summary': False,
            'message': 'لا يوجد سجل غياب سابق',
        })

    start = last_sub.start_date
    end = last_sub.end_date
    sub_name = ''
    if last_sub.substitute_employee:
        sub = last_sub.substitute_employee
        sub_name = f"{getattr(sub, 'first_name_ar', '')} {getattr(sub, 'last_name_ar', '')}".strip()

    # جيب فريق المدير
    from employees.visibility import get_visible_employees_qs
    team_qs = _Emp._base_manager.filter(
        direct_manager=mgr_emp,
        company=company,
        status='active',
    )
    team_ids = list(team_qs.values_list('id', flat=True))

    # الطلبات اللي اتحركت أثناء الغياب
    requests_qs = EmployeeRequest._base_manager.filter(
        company=company,
        employee_id__in=team_ids,
        updated_at__date__gte=start,
        updated_at__date__lte=end,
    ).exclude(status='pending').select_related('employee', 'request_type').order_by('-updated_at')

    requests_data = []
    for req in requests_qs[:50]:
        emp_name = f"{getattr(req.employee, 'first_name_ar', '')} {getattr(req.employee, 'last_name_ar', '')}".strip()
        requests_data.append({
            'id': req.id,
            'employee_name': emp_name,
            'type': req.request_type.name if req.request_type else '',
            'subject': req.subject or '',
            'status': req.status,
            'updated_at': req.updated_at.strftime('%Y-%m-%d') if req.updated_at else '',
        })

    # الإجازات اللي اتحركت أثناء الغياب
    leaves_qs = LeaveRequest._base_manager.filter(
        company=company,
        employee_id__in=team_ids,
        updated_at__date__gte=start,
        updated_at__date__lte=end,
    ).exclude(status='pending').select_related('employee', 'leave_type').order_by('-updated_at')

    leaves_data = []
    for lv in leaves_qs[:50]:
        emp_name = f"{getattr(lv.employee, 'first_name_ar', '')} {getattr(lv.employee, 'last_name_ar', '')}".strip()
        leaves_data.append({
            'id': lv.id,
            'employee_name': emp_name,
            'leave_type': lv.leave_type.name if lv.leave_type else '',
            'start_date': str(lv.start_date) if lv.start_date else '',
            'end_date': str(lv.end_date) if lv.end_date else '',
            'status': lv.status,
            'updated_at': lv.updated_at.strftime('%Y-%m-%d') if lv.updated_at else '',
        })

    # المهام أثناء الغياب
    missions_qs = Mission._base_manager.filter(
        company=company,
        assignments__employee_id__in=team_ids,
        created_at__date__gte=start,
        created_at__date__lte=end,
    ).distinct().order_by('-created_at')

    missions_data = []
    for m in missions_qs[:50]:
        missions_data.append({
            'id': m.id,
            'title': m.title or '',
            'status': m.status or '',
            'created_at': m.created_at.strftime('%Y-%m-%d') if m.created_at else '',
        })

    return Response({
        'success': True,
        'has_summary': True,
        'summary_viewed': last_sub.summary_viewed,
        'absence_period': {
            'start': str(start),
            'end': str(end),
            'substitute_name': sub_name,
        },
        'stats': {
            'total_requests': len(requests_data),
            'approved_requests': sum(1 for r in requests_data if r['status'] == 'approved'),
            'rejected_requests': sum(1 for r in requests_data if r['status'] == 'rejected'),
            'total_leaves': len(leaves_data),
            'approved_leaves': sum(1 for l in leaves_data if l['status'] == 'approved'),
            'rejected_leaves': sum(1 for l in leaves_data if l['status'] == 'rejected'),
            'total_missions': len(missions_data),
        },
        'requests': requests_data,
        'leaves': leaves_data,
        'missions': missions_data,
    })


```

======================================================================
## FILE: /var/www/motionhr/attendance/api_reports.py
======================================================================

```
"""
MotionHR - Reports API
Batch 1: Attendance / Late / Absence
"""
from datetime import datetime, timedelta, date
from django.utils import timezone
from calendar import monthrange

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Attendance
from employees.models import Employee


MANAGER_ROLES = ['company_admin', 'hr_manager', 'manager', 'super_admin']


def _check_manager(user):
    role = getattr(user, 'role', None)
    return (
        user.is_superuser
        or user.is_staff
        or role in MANAGER_ROLES
    )


def _get_company_employees(user):
    company = getattr(user, 'company', None)

    qs = Employee._base_manager.all().select_related('user', 'company')

    if company:
        qs = qs.filter(company=company)

    # استبعاد staff
    qs = qs.exclude(user__is_staff=True)

    # ATT-17: استبعاد company_admin و hr_manager لأنهم مش موظفين حقيقيين
    # (مش بيسجلوا حضور وبيظهروا كغائبين)
    qs = qs.exclude(
        user__role__in=['company_admin', 'super_admin']
    )

    # استبعاد الموظفين المنتهية خدمتهم
    qs = qs.exclude(
        status__in=['terminated', 'resigned', 'retired']
    )

    return qs.order_by('id')


FULL_ACCESS_ROLES = ['company_admin', 'hr_manager', 'super_admin']


def _get_manager_scope_employees(user):
    """
    لو المدير العادي → يرجع موظفيه فقط باستخدام _base_manager
    لو HR / company_admin / super_admin → يرجع كل موظفي الشركة
    """
    role = getattr(user, 'role', None)

    # صلاحيات كاملة
    if user.is_superuser or role in FULL_ACCESS_ROLES:
        return _get_company_employees(user)

    try:
        manager_emp = Employee._base_manager.get(user=user)
        company = getattr(user, 'company', None)

        collected_ids = set()
        stack = [manager_emp.id]

        while stack:
            current_id = stack.pop()

            sub_qs = Employee._base_manager.filter(direct_manager_id=current_id)
            if company:
                sub_qs = sub_qs.filter(company=company)

            sub_ids = list(sub_qs.values_list('id', flat=True))
            for sid in sub_ids:
                if sid not in collected_ids:
                    collected_ids.add(sid)
                    stack.append(sid)

        qs = Employee._base_manager.filter(id__in=collected_ids).select_related('user', 'company')
        if company:
            qs = qs.filter(company=company)

        return qs.order_by('id')
    except Exception:
        return _get_company_employees(user)


def _parse_month(request):
    now = datetime.now()
    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        if month < 1 or month > 12:
            raise ValueError
    except (ValueError, TypeError):
        year = now.year
        month = now.month
    return year, month


def _format_time(value):
    if not value:
        return None
    try:
        return value.strftime('%I:%M %p')
    except Exception:
        return str(value)


def _employee_name(emp):
    parts_ar = [
        getattr(emp, 'first_name_ar', '') or '',
        getattr(emp, 'middle_name_ar', '') or '',
        getattr(emp, 'last_name_ar', '') or '',
    ]
    name_ar = ' '.join([p.strip() for p in parts_ar if p and p.strip()]).strip()
    if name_ar:
        return name_ar

    parts_en = [
        getattr(emp, 'first_name_en', '') or '',
        getattr(emp, 'last_name_en', '') or '',
    ]
    name_en = ' '.join([p.strip() for p in parts_en if p and p.strip()]).strip()
    if name_en:
        return name_en

    if getattr(emp, 'user', None):
        return emp.user.get_full_name() or emp.user.username

    return f'Employee #{emp.id}'


def _employee_username(emp):
    if getattr(emp, 'user', None):
        return emp.user.username
    return None


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def attendance_monthly_report(request):
    """
    تقرير الحضور الشهري
    GET params: year, month, employee_id(optional)
    """
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []
    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
        )

        checkins = records.filter(check_in_time__isnull=False).count()
        checkouts = records.filter(check_out_time__isnull=False).count()
        working_days = records.filter(check_in_time__isnull=False).count()

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'username': _employee_username(emp),
            'employee_code': getattr(emp, 'employee_code', None),
            'total_checkins': checkins,
            'total_checkouts': checkouts,
            'working_days': working_days,
            'total_month_days': last_day_num,
        })

    return Response({
        'year': year,
        'month': month,
        'from': first_day.isoformat(),
        'to': last_day.isoformat(),
        'total_employees': len(results),
        'employees': results,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def late_report(request):
    """
    تقرير التأخير
    GET params: year, month, employee_id(optional)
    """
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []

    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by('date')

        late_days = []
        total_late_minutes = 0

        for rec in records:
            minutes_late = int(rec.late_minutes or 0)
            if minutes_late > 0:
                late_days.append({
                    'date': rec.date.isoformat() if rec.date else None,
                    'time': _format_time(rec.check_in_time),
                    'minutes_late': minutes_late,
                })
                total_late_minutes += minutes_late

        if late_days:
            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'username': _employee_username(emp),
                'employee_code': getattr(emp, 'employee_code', None),
                'total_late_days': len(late_days),
                'total_late_minutes': total_late_minutes,
                'total_late_hours': round(total_late_minutes / 60, 2),
                'details': late_days,
            })

    return Response({
        'year': year,
        'month': month,
        'total_employees_with_late': len(results),
        'employees': results,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def absence_report(request):
    """
    تقرير الغياب
    GET params: year, month, employee_id(optional)
    ملاحظة: الجمعة مستبعدة من أيام العمل
    """
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    today = date.today()
    upper_bound = min(last_day, today)

    working_dates = []
    current = first_day
    while current <= upper_bound:
        # الجمعة = 4 في Python
        if current.weekday() != 4:
            working_dates.append(current)
        current += timedelta(days=1)

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []
    for emp in employees:
        attended_dates = set(
            Attendance._base_manager.filter(
                employee=emp,
                date__gte=first_day,
                date__lte=upper_bound,
                check_in_time__isnull=False,
            ).values_list('date', flat=True)
        )

        absent_dates = [d for d in working_dates if d not in attended_dates]

        if absent_dates:
            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'username': _employee_username(emp),
                'employee_code': getattr(emp, 'employee_code', None),
                'total_working_days': len(working_dates),
                'attended_days': len(attended_dates),
                'absent_days': len(absent_dates),
                'absent_dates': [d.isoformat() for d in absent_dates],
            })

    return Response({
        'year': year,
        'month': month,
        'from': first_day.isoformat(),
        'to': upper_bound.isoformat() if upper_bound else None,
        'total_working_days_in_month': len(working_dates),
        'total_employees_with_absence': len(results),
        'employees': results,
    })


# ═══════════════════════════════════════
# 4) تقرير الطلبات
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def requests_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from requests_app.models import EmployeeRequest

    try:
        if 'year' in request.GET:
            int(request.GET.get('year'))
        if 'month' in request.GET:
            month_raw = int(request.GET.get('month'))
            if month_raw < 1 or month_raw > 12:
                return Response({'error': 'الشهر يجب أن يكون من 1 إلى 12'}, status=400)
    except (ValueError, TypeError):
        return Response({'error': 'صيغة year/month غير صحيحة'}, status=400)

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    valid_statuses = {'approved', 'pending', 'rejected'}
    if status_filter and status_filter not in valid_statuses:
        return Response({'error': 'status غير صحيح. القيم المتاحة: approved, pending, rejected'}, status=400)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    reqs = EmployeeRequest._base_manager.filter(
        employee_id__in=emp_ids,
        created_at__date__gte=first_day,
        created_at__date__lte=last_day,
    ).select_related('employee', 'request_type')

    if status_filter:
        reqs = reqs.filter(status=status_filter)

    total = reqs.count()
    approved = reqs.filter(status='approved').count()
    rejected = reqs.filter(status='rejected').count()
    pending = reqs.filter(status='pending').count()

    details = []
    for r in reqs.order_by('-created_at')[:100]:
        emp = r.employee
        details.append({
            'id': r.id,
            'employee_name': _employee_name(emp) if emp else '-',
            'request_type': str(r.request_type) if r.request_type else '-',
            'subject': getattr(r, 'subject', '') or '',
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        })

    return Response({
        'year': year,
        'month': month,
        'total_requests': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'details': details,
    })


# ═══════════════════════════════════════
# 5) تقرير الإجازات
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from leaves.models import LeaveRequest

    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    leaves = LeaveRequest._base_manager.filter(
        employee_id__in=emp_ids,
        start_date__gte=first_day,
        start_date__lte=last_day,
    ).select_related('employee', 'leave_type')

    total = leaves.count()
    approved = leaves.filter(status='approved').count()
    rejected = leaves.filter(status='rejected').count()
    pending = leaves.filter(status='pending').count()

    per_employee = {}
    for lv in leaves.order_by('-start_date'):
        emp = lv.employee
        emp_name = _employee_name(emp) if emp else '-'
        if emp_name not in per_employee:
            per_employee[emp_name] = {
                'employee_id': emp.id if emp else None,
                'total_days': 0,
                'approved_days': 0,
                'leaves': [],
            }

        days = int(lv.days_count or 0)
        if days == 0:
            try:
                days = (lv.end_date - lv.start_date).days + 1
            except Exception:
                days = 1

        per_employee[emp_name]['total_days'] += days
        if lv.status == 'approved':
            per_employee[emp_name]['approved_days'] += days

        per_employee[emp_name]['leaves'].append({
            'id': lv.id,
            'type': str(lv.leave_type) if lv.leave_type else '-',
            'from': lv.start_date.isoformat() if lv.start_date else None,
            'to': lv.end_date.isoformat() if lv.end_date else None,
            'days': days,
            'status': lv.status,
        })

    employees_list = [{'name': k, **v} for k, v in per_employee.items()]

    return Response({
        'year': year,
        'month': month,
        'total_leaves': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'employees': employees_list,
    })


# ═══════════════════════════════════════
# 6) تقرير ساعات العمل الفعلية
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def work_hours_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    results = []

    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by('date')

        total_hours = 0.0
        daily_breakdown = []

        for rec in records:
            hours = float(rec.work_hours or 0)
            if hours > 0:
                total_hours += hours
                daily_breakdown.append({
                    'date': rec.date.isoformat() if rec.date else None,
                    'hours': round(hours, 2),
                    'check_in': _format_time(rec.check_in_time),
                    'check_out': _format_time(rec.check_out_time),
                })

        days_worked = len(daily_breakdown)

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'username': _employee_username(emp),
            'employee_code': getattr(emp, 'employee_code', None),
            'total_hours': round(total_hours, 2),
            'total_days_worked': days_worked,
            'average_hours_per_day': round(total_hours / days_worked, 2) if days_worked else 0,
            'daily_breakdown': daily_breakdown,
        })

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'employees': results,
    })


# ═══════════════════════════════════════
# 7) تصدير PDF
# ═══════════════════════════════════════
from django.http import HttpResponse
from io import BytesIO

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def export_report_pdf(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    report_type = request.GET.get('report_type', 'attendance')
    year, month = _parse_month(request)

    from rest_framework.test import APIRequestFactory, force_authenticate
    factory = APIRequestFactory()
    fake_request = factory.get(f'/test/?year={year}&month={month}')
    force_authenticate(fake_request, user=user)

    view_map = {
        'attendance': attendance_monthly_report,
        'late': late_report,
        'absence': absence_report,
        'requests': requests_report,
        'leaves': leaves_report,
        'work-hours': work_hours_report,
    }

    view_func = view_map.get(report_type)
    if not view_func:
        return Response({'error': 'invalid report_type'}, status=400)

    response_data = view_func(fake_request).data

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(20 * mm, height - 20 * mm, f"MotionHR Report: {report_type.upper()}")

    p.setFont("Helvetica", 10)
    p.drawString(20 * mm, height - 30 * mm, f"Year: {year}  Month: {month}")

    y_pos = height - 45 * mm
    p.setFont("Helvetica", 9)

    employees = response_data.get('employees', [])
    details = response_data.get('details', [])
    items = employees if employees else details

    for item in items[:50]:
        line_parts = []
        name = item.get('employee_name') or item.get('name') or item.get('username') or '-'
        line_parts.append(name)

        if 'working_days' in item:
            line_parts.append(f"Days: {item['working_days']}")
        if 'total_late_days' in item:
            line_parts.append(f"Late: {item['total_late_days']}d")
        if 'absent_days' in item:
            line_parts.append(f"Absent: {item['absent_days']}d")
        if 'total_hours' in item:
            line_parts.append(f"Hours: {item['total_hours']}")
        if 'status' in item:
            line_parts.append(f"Status: {item['status']}")
        if 'subject' in item:
            line_parts.append(item['subject'][:30])

        line = '  |  '.join(line_parts)
        p.drawString(20 * mm, y_pos, line[:120])
        y_pos -= 6 * mm

        if y_pos < 20 * mm:
            p.showPage()
            y_pos = height - 20 * mm

    if not items:
        p.drawString(20 * mm, y_pos, "No data found for this period.")

    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report_type}_{year}_{month}.pdf"'
    return response


# ═══════════════════════════════════════
# 8) تصدير Excel
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def export_report_excel(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from openpyxl import Workbook

    report_type = request.GET.get('report_type', 'attendance')
    year, month = _parse_month(request)

    from rest_framework.test import APIRequestFactory, force_authenticate
    factory = APIRequestFactory()
    fake_request = factory.get(f'/test/?year={year}&month={month}')
    force_authenticate(fake_request, user=user)

    view_map = {
        'attendance': attendance_monthly_report,
        'late': late_report,
        'absence': absence_report,
        'requests': requests_report,
        'leaves': leaves_report,
        'work-hours': work_hours_report,
    }

    view_func = view_map.get(report_type)
    if not view_func:
        return Response({'error': 'invalid report_type'}, status=400)

    response_data = view_func(fake_request).data

    wb = Workbook()
    ws = wb.active
    ws.title = f"{report_type}_{year}_{month}"

    employees = response_data.get('employees', [])
    details = response_data.get('details', [])
    items = employees if employees else details

    if items:
        headers = list(items[0].keys())
        # نشيل الحقول المعقدة
        simple_headers = [h for h in headers if h not in ('details', 'daily_breakdown', 'leaves', 'absent_dates')]
        ws.append(simple_headers)

        for item in items:
            row = []
            for h in simple_headers:
                val = item.get(h, '')
                if isinstance(val, (list, dict)):
                    val = str(val)[:200]
                row.append(val)
            ws.append(row)
    else:
        ws.append(['No data found'])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="report_{report_type}_{year}_{month}.xlsx"'
    return response


# ═══════════════════════════════════════
# Phase 13 Quick Filters Overrides
# requests/leaves/work-hours support filters
# ═══════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def requests_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from requests_app.models import EmployeeRequest

    try:
        if 'year' in request.GET:
            int(request.GET.get('year'))
        if 'month' in request.GET:
            month_raw = int(request.GET.get('month'))
            if month_raw < 1 or month_raw > 12:
                return Response({'error': 'الشهر يجب أن يكون من 1 إلى 12'}, status=400)
    except (ValueError, TypeError):
        return Response({'error': 'صيغة year/month غير صحيحة'}, status=400)

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    employee_id = request.GET.get('employee_id')

    valid_statuses = {'approved', 'pending', 'rejected'}
    if status_filter and status_filter not in valid_statuses:
        return Response({'error': 'status غير صحيح. القيم المتاحة: approved, pending, rejected'}, status=400)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    reqs = EmployeeRequest._base_manager.filter(
        employee_id__in=emp_ids,
        created_at__date__gte=first_day,
        created_at__date__lte=last_day,
    ).select_related('employee', 'request_type')

    if employee_id:
        reqs = reqs.filter(employee_id=employee_id)

    if status_filter:
        reqs = reqs.filter(status=status_filter)

    total = reqs.count()
    approved = reqs.filter(status='approved').count()
    rejected = reqs.filter(status='rejected').count()
    pending = reqs.filter(status='pending').count()

    details = []
    for r in reqs.order_by('-created_at')[:100]:
        emp = r.employee
        details.append({
            'id': r.id,
            'employee_id': emp.id if emp else None,
            'employee_name': _employee_name(emp) if emp else '-',
            'request_type': str(r.request_type) if r.request_type else '-',
            'subject': getattr(r, 'subject', '') or '',
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        })

    return Response({
        'year': year,
        'month': month,
        'employee_id': employee_id,
        'status': status_filter,
        'total_requests': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'details': details,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from leaves.models import LeaveRequest

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    leaves = LeaveRequest._base_manager.filter(
        employee_id__in=emp_ids,
        start_date__gte=first_day,
        start_date__lte=last_day,
    ).select_related('employee', 'leave_type')

    if employee_id:
        leaves = leaves.filter(employee_id=employee_id)

    if status_filter:
        leaves = leaves.filter(status=status_filter)

    total = leaves.count()
    approved = leaves.filter(status='approved').count()
    rejected = leaves.filter(status='rejected').count()
    pending = leaves.filter(status='pending').count()

    per_employee = {}
    for lv in leaves.order_by('-start_date'):
        emp = lv.employee
        emp_name = _employee_name(emp) if emp else '-'
        emp_id = emp.id if emp else None

        if emp_id not in per_employee:
            per_employee[emp_id] = {
                'employee_id': emp_id,
                'name': emp_name,
                'total_days': 0,
                'approved_days': 0,
                'leaves': [],
            }

        days = int(getattr(lv, 'days_count', 0) or 0)
        if days == 0:
            try:
                days = (lv.end_date - lv.start_date).days + 1
            except Exception:
                days = 1

        per_employee[emp_id]['total_days'] += days
        if lv.status == 'approved':
            per_employee[emp_id]['approved_days'] += days

        per_employee[emp_id]['leaves'].append({
            'id': lv.id,
            'type': str(lv.leave_type) if lv.leave_type else '-',
            'from': lv.start_date.isoformat() if lv.start_date else None,
            'to': lv.end_date.isoformat() if lv.end_date else None,
            'days': days,
            'status': lv.status,
        })

    employees_list = list(per_employee.values())

    return Response({
        'year': year,
        'month': month,
        'employee_id': employee_id,
        'status': status_filter,
        'total_leaves': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'employees': employees_list,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def work_hours_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []

    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by('date')

        total_hours = 0.0
        daily_breakdown = []

        for rec in records:
            hours = float(rec.work_hours or 0)
            if hours > 0:
                total_hours += hours
                daily_breakdown.append({
                    'date': rec.date.isoformat() if rec.date else None,
                    'hours': round(hours, 2),
                    'check_in': _format_time(rec.check_in_time),
                    'check_out': _format_time(rec.check_out_time),
                })

        days_worked = len(daily_breakdown)

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'username': _employee_username(emp),
            'employee_code': getattr(emp, 'employee_code', None),
            'total_hours': round(total_hours, 2),
            'total_days_worked': days_worked,
            'average_hours_per_day': round(total_hours / days_worked, 2) if days_worked else 0,
            'daily_breakdown': daily_breakdown,
        })

    return Response({
        'year': year,
        'month': month,
        'employee_id': employee_id,
        'total_employees': len(results),
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.1 تقرير الرواتب الشهري
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def payroll_report(request):
    """تقرير الرواتب الشهري لكل الموظفين"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    try:
        if 'year' in request.GET:
            int(request.GET.get('year'))
        if 'month' in request.GET:
            month_raw = int(request.GET.get('month'))
            if month_raw < 1 or month_raw > 12:
                return Response({'error': 'الشهر يجب أن يكون من 1 إلى 12'}, status=400)
    except (ValueError, TypeError):
        return Response({'error': 'صيغة year/month غير صحيحة'}, status=400)

    year, month = _parse_month(request)
    lang = request.GET.get('lang', 'ar')
    employees = _get_manager_scope_employees(user)

    try:
        from attendance.payroll_rules import calculate_effective_payroll
        from attendance.api_payroll import _get_payroll_settings
    except ImportError:
        return Response({'error': 'payroll module not available'}, status=500)

    settings = _get_payroll_settings(user)

    results = []
    totals = {
        'basic_salary': 0.0,
        'allowances_total': 0.0,
        'overtime_bonus': 0.0,
        'bonuses_total': 0.0,
        'night_allowance': 0.0,
        'weekend_allowance': 0.0,
        'gross_salary': 0.0,
        'late_deduction': 0.0,
        'absence_deduction': 0.0,
        'early_leave_deduction': 0.0,
        'unpaid_leave_deduction': 0.0,
        'flex_shortage_deduction': 0.0,
        'insurance_deduction': 0.0,
        'installments_total': 0.0,
        'penalties_total': 0.0,
        'total_deductions': 0.0,
        'net_salary': 0.0,
    }

    for emp in employees:
        try:
            p = calculate_effective_payroll(emp, year, month, settings, lang=lang)
            row = {
                'employee_id': emp.id,
                'employee_code': getattr(emp, 'employee_code', '') or '',
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'job_title': getattr(getattr(emp, 'job_title', None), 'name_ar', '') or '',
                'currency': p.get('currency', 'EGP'),
                'basic_salary': p.get('basic_salary', 0),
                'allowances_total': p.get('allowances_total', 0),
                'overtime_bonus': p.get('overtime_bonus', 0),
                'bonuses_total': p.get('bonuses_total', 0),
                'night_allowance': p.get('night_allowance', 0),
                'weekend_allowance': p.get('weekend_allowance', 0),
                'gross_salary': p.get('gross_salary', 0),
                'late_deduction': p.get('late_deduction', 0),
                'absence_deduction': p.get('absence_deduction', 0),
                'early_leave_deduction': p.get('early_leave_deduction', 0),
                'unpaid_leave_deduction': p.get('unpaid_leave_deduction', 0),
                'flex_shortage_deduction': p.get('flex_shortage_deduction', 0),
                'insurance_deduction': p.get('insurance_deduction', 0),
                'installments_total': p.get('installments_total', 0),
                'penalties_total': p.get('penalties_total', 0),
                'total_deductions': p.get('total_deductions', 0),
                'net_salary': p.get('net_salary', 0),
                'total_working_days': p.get('total_working_days', 0),
                'attended_days': p.get('attended_days', 0),
                'absent_days': p.get('absent_days', 0),
                'late_days': p.get('late_days', 0),
                'on_leave_days': p.get('on_leave_days', 0),
                'unpaid_leave_days': p.get('unpaid_leave_days', 0),
                'total_late_minutes': p.get('total_late_minutes', 0),
                'policy_name': p.get('policy_name'),
            }
            results.append(row)
            for key in totals:
                totals[key] += float(row.get(key, 0) or 0)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'payroll_report error for {emp}: {e}')

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'totals': {k: round(v, 2) for k, v in totals.items()},
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.3 تقرير الأذونات
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def permissions_report(request):
    """تقرير رصيد الأذونات والحركات"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employees = _get_manager_scope_employees(user)
    company = getattr(user, 'company', None)

    from datetime import date
    first_day = date(year, month, 1)
    import calendar
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    results = []
    for emp in employees:
        try:
            from attendance.models import PermissionLedger
            entries = PermissionLedger._base_manager.filter(
                employee=emp,
                reference_date__gte=first_day,
                reference_date__lte=last_day,
            ).order_by('reference_date')

            total_minutes = 0
            movements = []
            for e in entries:
                total_minutes += int(e.minutes_used or 0)
                movements.append({
                    'date': str(e.reference_date) if e.reference_date else '',
                    'type': e.entry_type,
                    'minutes': e.minutes_used or 0,
                    'notes': e.notes or '',
                })

            from requests_app.models import PermissionPolicy
            policy = PermissionPolicy._base_manager.filter(company=emp.company).first()
            max_hours = float(policy.max_hours_per_month) if policy else 0.0
            max_times = policy.max_times_per_month if policy else 0

            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'max_hours_per_month': max_hours,
                'max_times_per_month': max_times,
                'used_minutes': total_minutes,
                'used_hours': round(total_minutes / 60, 2),
                'movements_count': len(movements),
                'movements': movements,
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'permissions_report error for {emp}: {e}')

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.5 تقرير يومي للحضور
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def daily_attendance_report(request):
    """تقرير حالة الحضور لكل الموظفين في يوم معين"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from datetime import date
    date_str = request.GET.get('date', str(date.today()))
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة (YYYY-MM-DD)'}, status=400)

    employees = _get_manager_scope_employees(user)

    try:
        from attendance.models import DailyAttendanceSummary, Attendance, TrackingAlert
    except ImportError:
        return Response({'error': 'attendance module not available'}, status=500)

    gps_alert_map = {}
    try:
        gps_qs = TrackingAlert._base_manager.filter(date=target_date, status='open')
        requester_company = getattr(user, 'company', None)
        if requester_company:
            gps_qs = gps_qs.filter(company=requester_company)

        for al in gps_qs:
            note = (getattr(al, 'notes', '') or '').lower()
            if 'gps' in note or (getattr(al, 'last_latitude', None) is None and getattr(al, 'last_longitude', None) is None):
                gps_alert_map[al.employee_id] = al
    except Exception:
        gps_alert_map = {}

    results = []
    stats = {
        'present': 0, 'late': 0, 'absent': 0,
        'on_leave': 0, 'weekend': 0, 'mission': 0,
        'no_data': 0, 'gps_disabled': 0,
    }

    for emp in employees:
        summary = DailyAttendanceSummary._base_manager.filter(
            employee=emp, date=target_date
        ).first()

        att = Attendance._base_manager.filter(
            employee=emp, date=target_date
        ).first()

        if summary:
            status = summary.effective_status or summary.status
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': status,
                'check_in': timezone.localtime(att.check_in_time).strftime('%I:%M %p') if att and att.check_in_time else None,
                'check_out': timezone.localtime(att.check_out_time).strftime('%I:%M %p') if att and att.check_out_time else None,
                'work_hours': float(summary.work_hours or 0),
                'late_minutes': summary.late_minutes or 0,
                'early_leave_minutes': summary.early_leave_minutes or 0,
                'overtime_hours': float(summary.overtime_hours or 0),
                'is_night_shift': summary.is_night_shift,
                'is_weekend_work': summary.is_weekend_work,
                'shift_name': summary.shift.name if summary.shift else '',
            }
        elif att and att.check_in_time:
            if getattr(att, 'status', None) in ('late', 'present', 'absent', 'on_leave', 'weekend', 'mission'):
                status = att.status
            elif (att.late_minutes or 0) > 0:
                status = 'late'
            else:
                status = 'present'
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': status,
                'check_in': timezone.localtime(att.check_in_time).strftime('%I:%M %p') if att.check_in_time else None,
                'check_out': timezone.localtime(att.check_out_time).strftime('%I:%M %p') if att and att.check_out_time else None,
                'work_hours': float(att.work_hours or 0),
                'late_minutes': att.late_minutes or 0,
                'early_leave_minutes': att.early_leave_minutes or 0,
                'overtime_hours': float(att.overtime_hours or 0),
                'is_night_shift': False,
                'is_weekend_work': False,
                'shift_name': att.shift.name if att.shift else '',
            }
        else:
            status = 'absent'
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': 'absent',
                'check_in': None,
                'check_out': None,
                'work_hours': 0,
                'late_minutes': 0,
                'early_leave_minutes': 0,
                'overtime_hours': 0,
                'is_night_shift': False,
                'is_weekend_work': False,
                'shift_name': '',
            }

        row['gps_disabled'] = emp.id in gps_alert_map
        row['gps_alert_note'] = getattr(gps_alert_map.get(emp.id), 'notes', '') if emp.id in gps_alert_map else ''

        if row['gps_disabled']:
            stats['gps_disabled'] = stats.get('gps_disabled', 0) + 1

        results.append(row)
        stats[status] = stats.get(status, 0) + 1

    return Response({
        'date': str(target_date),
        'total_employees': len(results),
        'stats': stats,
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.4 تقرير الإجازات المحسّن (مع أرصدة + unpaid + نص يوم)
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report_enhanced(request):
    """تقرير الإجازات الشامل مع الأرصدة"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    employees = _get_manager_scope_employees(user)

    from leaves.models import LeaveRequest, LeaveBalance, LeaveType

    results = []
    for emp in employees:
        leaves = LeaveRequest._base_manager.filter(
            employee=emp,
            start_date__lte=last_day,
            end_date__gte=first_day,
        ).select_related('leave_type').order_by('-start_date')

        leave_items = []
        total_days = 0.0
        unpaid_days = 0.0
        half_day_count = 0

        for lv in leaves:
            days = float(lv.days_count or 1)
            is_unpaid = not getattr(lv.leave_type, 'is_paid', True) if lv.leave_type else False
            is_half = days <= 0.5
            half_type = getattr(lv, 'half_day_type', '') or ''

            if lv.status == 'approved':
                total_days += days
                if is_unpaid:
                    unpaid_days += days
                if is_half:
                    half_day_count += 1

            leave_items.append({
                'id': lv.id,
                'leave_type': lv.leave_type.name if lv.leave_type else '',
                'leave_type_en': getattr(lv.leave_type, 'name_en', '') if lv.leave_type else '',
                'is_paid': not is_unpaid,
                'start_date': str(lv.start_date) if lv.start_date else '',
                'end_date': str(lv.end_date) if lv.end_date else '',
                'days_count': days,
                'is_half_day': is_half,
                'half_day_type': half_type,
                'status': lv.status,
                'reason': lv.reason or '',
            })

        # Filter balances by employee gender (skip leave types restricted to opposite gender)
        emp_gender = (getattr(emp, "gender", "") or "").lower()
        balances_qs = LeaveBalance._base_manager.filter(
            employee=emp,
            year=year,
        ).select_related('leave_type')

        if emp_gender == "male":
            balances_qs = balances_qs.exclude(leave_type__gender_restriction="female")
        elif emp_gender == "female":
            balances_qs = balances_qs.exclude(leave_type__gender_restriction="male")

        balances = balances_qs

        balance_items = []
        for bal in balances:
            balance_items.append({
                'leave_type': bal.leave_type.name if bal.leave_type else '',
                'leave_type_en': getattr(bal.leave_type, 'name_en', '') if bal.leave_type else '',
                'total_days': float(bal.total_days or 0),
                'used_days': float(bal.used_days or 0),
                'pending_days': float(bal.pending_days or 0),
                'remaining_days': float(bal.remaining_days if hasattr(bal, 'remaining_days') else 0),
            })

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'total_approved_days': total_days,
            'unpaid_days': unpaid_days,
            'half_day_count': half_day_count,
            'leaves_count': len(leave_items),
            'leaves': leave_items,
            'balances': balance_items,
        })

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.2 تقرير الشيفتات
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def shifts_report(request):
    """تقرير توزيع الموظفين على الشيفتات"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    employees = _get_manager_scope_employees(user)
    company = getattr(user, 'company', None)

    from attendance.models import Shift, ShiftAssignment, EmployeeShift
    from attendance.api_shifts import get_effective_shift

    today = date.today()
    shift_distribution = {}
    no_shift_employees = []

    for emp in employees:
        try:
            shift, source = get_effective_shift(emp, today)
        except Exception:
            shift = None
            source = 'error'

        if shift:
            shift_id = shift.id
            if shift_id not in shift_distribution:
                shift_distribution[shift_id] = {
                    'shift_id': shift_id,
                    'shift_name': shift.name,
                    'shift_type': shift.shift_type,
                    'shift_mode': getattr(shift, 'shift_mode', ''),
                    'start_time': str(shift.start_time)[:5] if shift.start_time else '',
                    'end_time': str(shift.end_time)[:5] if shift.end_time else '',
                    'crosses_midnight': shift.crosses_midnight,
                    'employees_count': 0,
                    'employees': [],
                }
            shift_distribution[shift_id]['employees_count'] += 1
            shift_distribution[shift_id]['employees'].append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'source': source,
            })
        else:
            no_shift_employees.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            })

    all_shifts = list(shift_distribution.values())
    all_shifts.sort(key=lambda x: x['employees_count'], reverse=True)

    return Response({
        'date': str(today),
        'total_employees': employees.count(),
        'employees_with_shifts': sum(s['employees_count'] for s in all_shifts),
        'employees_without_shifts': len(no_shift_employees),
        'shifts_count': len(all_shifts),
        'shifts': all_shifts,
        'no_shift_employees': no_shift_employees,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def location_tracking_report(request):
    """تقرير تتبع مواقع الموظفين لليوم"""
    from datetime import date, datetime, timedelta
    from django.utils import timezone
    from django.db.models import Min, Max, Count
    from attendance.models import Attendance, LocationLog

    user = request.user
    if not _check_manager(user):
        return Response({'success': False, 'error': 'صلاحية غير كافية'}, status=403)

    date_str = request.GET.get('date', str(date.today()))
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return Response({'success': False, 'error': 'صيغة التاريخ غير صحيحة'}, status=400)

    employees = _get_manager_scope_employees(user)

    results = []
    for emp in employees:
        att = Attendance._base_manager.filter(employee=emp, date=target_date).first()

        checkin_time = att.check_in_time if att and att.check_in_time else None
        checkout_time = att.check_out_time if att and att.check_out_time else None

        # location logs في نطاق الحضور
        logs_qs = LocationLog._base_manager.filter(
            employee=emp,
            timestamp__date=target_date,
        ).order_by('timestamp')

        if checkin_time:
            logs_qs = logs_qs.filter(timestamp__gte=checkin_time)
        if checkout_time:
            logs_qs = logs_qs.filter(timestamp__lte=checkout_time)

        logs = list(logs_qs.values('timestamp', 'latitude', 'longitude', 'address', 'accuracy'))

        first_log = logs[0] if logs else None
        last_log = logs[-1] if logs else None

        emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() or emp.employee_code

        results.append({
            'employee_id': emp.id,
            'employee_code': emp.employee_code or '',
            'employee_name': emp_name,
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'worker_type': getattr(emp, 'worker_type', '') or '',
            'checkin_time': checkin_time.strftime('%H:%M') if checkin_time else '',
            'checkout_time': checkout_time.strftime('%H:%M') if checkout_time else '',
            'has_attendance': bool(att and att.check_in_time),
            'total_logs': len(logs),
            'first_location': {
                'timestamp': first_log['timestamp'].strftime('%H:%M') if first_log else '',
                'lat': float(first_log['latitude']) if first_log else None,
                'lng': float(first_log['longitude']) if first_log else None,
                'address': first_log['address'] if first_log else '',
            } if first_log else None,
            'last_location': {
                'timestamp': last_log['timestamp'].strftime('%H:%M') if last_log else '',
                'lat': float(last_log['latitude']) if last_log else None,
                'lng': float(last_log['longitude']) if last_log else None,
                'address': last_log['address'] if last_log else '',
            } if last_log else None,
            'logs': [
                {
                    'timestamp': log['timestamp'].strftime('%H:%M'),
                    'lat': float(log['latitude']),
                    'lng': float(log['longitude']),
                    'address': log['address'] or '',
                    'accuracy': float(log['accuracy']) if log['accuracy'] else 0,
                }
                for log in logs
            ],
        })

    # stats
    total_emp = len(results)
    with_attendance = sum(1 for r in results if r['has_attendance'])
    tracked = sum(1 for r in results if r['total_logs'] > 0)

    return Response({
        'success': True,
        'date': str(target_date),
        'stats': {
            'total_employees': total_emp,
            'with_attendance': with_attendance,
            'tracked': tracked,
            'not_tracked': total_emp - tracked,
        },
        'employees': results,
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_report(request):
    """تقرير مكافأة نهاية الخدمة"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    as_of_str = request.GET.get('as_of_date', str(timezone.localdate()))
    try:
        as_of_date = date.fromisoformat(as_of_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة (YYYY-MM-DD)'}, status=400)

    employees = (
        _get_manager_scope_employees(user)
        .exclude(user__is_staff=True)
        .exclude(user__role__in=['company_admin', 'super_admin'])
        .exclude(status__in=['terminated', 'resigned', 'retired'])
        .select_related('department', 'branch', 'user')
        .order_by('id')
    )

    results = []
    total_eos_amount = 0.0

    for emp in employees:
        if not emp.hire_date:
            continue

        service_days = (as_of_date - emp.hire_date).days
        if service_days < 0:
            continue

        years_of_service = round(service_days / 365.25, 2)
        basic_salary = round(float(emp.basic_salary or 0), 2)

        if years_of_service <= 5:
            eos_amount = (basic_salary * 0.5) * years_of_service
        else:
            eos_amount = (basic_salary * 0.5 * 5) + (basic_salary * (years_of_service - 5))

        eos_amount = round(eos_amount, 2)
        total_eos_amount += eos_amount

        results.append({
            'employee_id': emp.id,
            'employee_code': emp.employee_code,
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'hire_date': str(emp.hire_date),
            'years_of_service': years_of_service,
            'basic_salary': basic_salary,
            'eos_amount': eos_amount,
        })

    results.sort(key=lambda x: x['eos_amount'], reverse=True)

    return Response({
        'as_of_date': str(as_of_date),
        'summary': {
            'employees_count': len(results),
            'total_eos_amount': round(total_eos_amount, 2),
        },
        'results': results,
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_export_excel(request):
    """تصدير تقرير EOS كـ Excel"""
    from attendance.report_export_helper import export_to_excel
    from datetime import date

    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    as_of_str = request.GET.get('as_of_date', str(timezone.localdate()))
    try:
        as_of_date = date.fromisoformat(as_of_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة'}, status=400)

    employees = (
        _get_manager_scope_employees(user)
        .exclude(user__is_staff=True)
        .exclude(user__role__in=['company_admin', 'super_admin'])
        .exclude(status__in=['terminated', 'resigned', 'retired'])
        .select_related('department', 'branch', 'user')
        .order_by('id')
    )

    rows = []
    for emp in employees:
        if not emp.hire_date:
            continue
        service_days = (as_of_date - emp.hire_date).days
        if service_days < 0:
            continue
        years = round(service_days / 365.25, 2)
        basic = round(float(emp.basic_salary or 0), 2)
        if years <= 5:
            eos = round((basic * 0.5) * years, 2)
        else:
            eos = round((basic * 0.5 * 5) + (basic * (years - 5)), 2)

        rows.append({
            'employee_code': emp.employee_code or '',
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'hire_date': str(emp.hire_date),
            'years_of_service': years,
            'basic_salary': basic,
            'eos_amount': eos,
        })

    rows.sort(key=lambda x: x['eos_amount'], reverse=True)

    columns = [
        ('employee_code',   'الكود',           15),
        ('employee_name',   'اسم الموظف',      25),
        ('department',      'القسم',           20),
        ('branch',          'الفرع',           20),
        ('hire_date',       'تاريخ التعيين',   15),
        ('years_of_service','سنوات الخدمة',    15),
        ('basic_salary',    'الراتب الأساسي',  18),
        ('eos_amount',      'مكافأة نهاية الخدمة', 22),
    ]

    if not rows:
        columns = [('info', 'ملاحظة', 40)]
        rows = [{'info': 'لا توجد بيانات'}]

    return export_to_excel(
        title=f'تقرير مكافأة نهاية الخدمة - {as_of_date}',
        columns=columns,
        rows=rows,
        user=user,
        filename=f'eos_report_{as_of_date}.xlsx',
    )

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_export_pdf(request):
    """تصدير تقرير EOS كـ PDF"""
    from attendance.report_export_helper import export_to_pdf
    from datetime import date

    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    as_of_str = request.GET.get('as_of_date', str(timezone.localdate()))
    try:
        as_of_date = date.fromisoformat(as_of_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة'}, status=400)

    employees = (
        _get_manager_scope_employees(user)
        .exclude(user__is_staff=True)
        .exclude(user__role__in=['company_admin', 'super_admin'])
        .exclude(status__in=['terminated', 'resigned', 'retired'])
        .select_related('department', 'branch', 'user')
        .order_by('id')
    )

    rows = []
    for emp in employees:
        if not emp.hire_date:
            continue
        service_days = (as_of_date - emp.hire_date).days
        if service_days < 0:
            continue
        years = round(service_days / 365.25, 2)
        basic = round(float(emp.basic_salary or 0), 2)
        if years <= 5:
            eos = round((basic * 0.5) * years, 2)
        else:
            eos = round((basic * 0.5 * 5) + (basic * (years - 5)), 2)

        rows.append({
            'employee_code': emp.employee_code or '',
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'hire_date': str(emp.hire_date),
            'years_of_service': years,
            'basic_salary': basic,
            'eos_amount': eos,
        })

    rows.sort(key=lambda x: x['eos_amount'], reverse=True)

    columns = [
        ('employee_code',    'الكود',                15),
        ('employee_name',    'اسم الموظف',           25),
        ('department',       'القسم',                20),
        ('branch',           'الفرع',                20),
        ('hire_date',        'تاريخ التعيين',        15),
        ('years_of_service', 'سنوات الخدمة',         15),
        ('basic_salary',     'الراتب الأساسي',       18),
        ('eos_amount',       'مكافأة نهاية الخدمة',  22),
    ]

    if not rows:
        columns = [('info', 'ملاحظة', 40)]
        rows = [{'info': 'لا توجد بيانات'}]

    return export_to_pdf(
        title=f'تقرير مكافأة نهاية الخدمة - {as_of_date}',
        columns=columns,
        rows=rows,
        user=user,
        filename=f'eos_report_{as_of_date}.pdf',
    )

# ═══════════════════════════════════════════════════
# 10 New Reports + Excel + PDF Exports
# ═══════════════════════════════════════════════════

def _reimbursements_data(user):
    """رد المصروفات"""
    company = getattr(user, 'company', None)
    rows = []
    try:
        from requests_app.models import EmployeeRequest
        reqs = EmployeeRequest._base_manager.filter(
            company=company, request_type__name__icontains='مصروف',
        ).select_related('employee', 'request_type')
        for req in reqs:
            rows.append({
                'employee_name': _employee_name(req.employee),
                'type': req.request_type.name if req.request_type else '',
                'subject': req.subject or '',
                'amount': round(float(req.amount or 0), 2),
                'status': req.status,
                'created_at': str(req.created_at)[:10] if req.created_at else '',
            })
    except Exception:
        pass
    return rows


def _bank_transfer_data(user):
    """كشف تحويلات البنك"""
    from employees.models import Employee
    company = getattr(user, 'company', None)
    rows = []
    emps = Employee._base_manager.filter(
        company=company, status='active', salary_payment_method='bank',
    ).exclude(bank_account__isnull=True).exclude(bank_account='')
    for emp in emps:
        rows.append({
            'employee_code': emp.employee_code,
            'employee_name': _employee_name(emp),
            'bank_name': emp.bank_name or '',
            'account_number': emp.bank_account or '',
            'iban': emp.iban or '',
            'amount': round(float(emp.basic_salary or 0), 2),
        })
    return rows


def _insurance_data(user):
    """التأمينات"""
    from employees.models import Employee
    company = getattr(user, 'company', None)
    rows = []
    insured = Employee._base_manager.filter(company=company, status='active', has_insurance=True)
    for emp in insured:
        base = float(emp.basic_salary or 0)
        ins_base = float(getattr(emp, 'insurance_base_salary', None) or base)
        rows.append({
            'employee_code': emp.employee_code,
            'employee_name': _employee_name(emp),
            'insurance_number': emp.insurance_number or '',
            'basic_salary': round(base, 2),
            'insurance_base': round(ins_base, 2),
            'insurance_amount': round(ins_base * 0.11, 2),
        })
    return rows


def _tax_data(user, year, month):
    """الضرائب"""
    from employees.models import Employee, Deduction
    company = getattr(user, 'company', None)
    rows = []
    for emp in Employee._base_manager.filter(company=company, status='active'):
        taxes = Deduction._base_manager.filter(
            employee=emp, deduction_type='tax', year=year, month=month,
        )
        tax_sum = sum(float(d.amount) for d in taxes)
        if tax_sum > 0:
            rows.append({
                'employee_code': emp.employee_code,
                'employee_name': _employee_name(emp),
                'basic_salary': round(float(emp.basic_salary or 0), 2),
                'tax_amount': round(tax_sum, 2),
            })
    return rows


def _turnover_data(user, year):
    """معدل دوران الموظفين"""
    from employees.models import Employee
    from datetime import date
    company = getattr(user, 'company', None)
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    all_emps = Employee._base_manager.filter(company=company)
    hired = all_emps.filter(hire_date__gte=year_start, hire_date__lte=year_end).count()
    terminated = all_emps.filter(
        status__in=['terminated', 'resigned', 'retired'],
        termination_date__gte=year_start, termination_date__lte=year_end,
    ).count()
    active = all_emps.filter(status='active').count()

    rows = [
        {'metric': f'التعيينات في {year}', 'value': hired},
        {'metric': f'انتهاء الخدمة في {year}', 'value': terminated},
        {'metric': 'الموظفين النشطين حالياً', 'value': active},
        {'metric': 'معدل الدوران %', 'value': round((terminated/max(active,1))*100, 2)},
    ]
    return rows


def _branch_comparison_data(user):
    """مقارنة الفروع والأقسام"""
    from employees.models import Employee
    from companies.models import Branch
    from attendance.models import Attendance
    from django.db.models import Sum, Count, Q
    from datetime import timedelta
    company = getattr(user, 'company', None)
    today = timezone.localdate()
    date_from = today - timedelta(days=30)
    rows = []
    for br in Branch._base_manager.filter(company=company):
        emps = Employee._base_manager.filter(branch=br, status='active')
        emp_ids = list(emps.values_list('id', flat=True))
        salaries = [float(e.basic_salary or 0) for e in emps]

        # بيانات الحضور آخر 30 يوم
        att_qs = Attendance._base_manager.filter(
            employee_id__in=emp_ids,
            date__gte=date_from,
            date__lte=today,
        )
        present_days = att_qs.filter(status__in=['present', 'late']).count()
        absent_days = att_qs.filter(status='absent').count()
        late_minutes = att_qs.aggregate(t=Sum('late_minutes'))['t'] or 0
        overtime_hours = att_qs.aggregate(t=Sum('overtime_hours'))['t'] or 0

        rows.append({
            'branch_name': br.name_ar,
            'employees_count': len(salaries),
            'total_salary': round(sum(salaries), 2),
            'avg_salary': round(sum(salaries)/len(salaries) if salaries else 0, 2),
            'max_salary': round(max(salaries) if salaries else 0, 2),
            'min_salary': round(min(salaries) if salaries else 0, 2),
            'present_days': present_days,
            'absent_days': absent_days,
            'total_late_minutes': int(late_minutes),
            'total_overtime_hours': round(float(overtime_hours), 2),
        })
    return rows


def _contracts_expiry_data(user):
    """العقود المنتهية / قريبة الانتهاء"""
    from employees.models import Employee
    from datetime import timedelta
    company = getattr(user, 'company', None)
    today = timezone.localdate()
    next_90 = today + timedelta(days=90)

    rows = []
    emps = Employee._base_manager.filter(
        company=company, status='active', contract_end_date__isnull=False,
    )
    for emp in emps:
        end = emp.contract_end_date
        if end < today:
            rows.append({
                'employee_name': _employee_name(emp),
                'employee_code': emp.employee_code,
                'contract_end': str(end),
                'status': 'منتهي',
                'days': (today - end).days,
            })
        elif end <= next_90:
            rows.append({
                'employee_name': _employee_name(emp),
                'employee_code': emp.employee_code,
                'contract_end': str(end),
                'status': 'قريب الانتهاء',
                'days': (end - today).days,
            })
    return rows


def _loans_advances_data(user):
    """السلف والقروض"""
    company = getattr(user, 'company', None)
    rows = []
    try:
        from requests_app.models import EmployeeRequest
        from django.db.models import Q
        loans = EmployeeRequest._base_manager.filter(
            company=company, status__in=['approved', 'pending'],
        ).filter(Q(request_type__name__icontains='سلفة') | Q(request_type__name__icontains='قرض'))
        for loan in loans:
            rows.append({
                'employee_name': _employee_name(loan.employee),
                'type': loan.request_type.name if loan.request_type else '',
                'amount': round(float(loan.amount or 0), 2),
                'status': loan.status,
                'created_at': str(loan.created_at)[:10] if loan.created_at else '',
            })
    except Exception:
        pass
    return rows


def _missions_performance_data(user):
    """أداء المهام"""
    employees = _get_manager_scope_employees(user)
    rows = []
    try:
        from attendance.models import MissionAssignment
        for emp in employees:
            assignments = MissionAssignment._base_manager.filter(employee=emp)
            total = assignments.count()
            if total > 0:
                completed = assignments.filter(status='completed').count()
                rows.append({
                    'employee_name': _employee_name(emp),
                    'total_missions': total,
                    'completed': completed,
                    'in_progress': assignments.filter(status='in_progress').count(),
                    'pending': assignments.filter(status='pending').count(),
                    'completion_rate': round((completed/total*100), 2),
                })
    except Exception:
        pass
    return rows


def _executive_dashboard_data(user):
    """التقرير التنفيذي"""
    from employees.models import Employee
    company = getattr(user, 'company', None)
    active = Employee._base_manager.filter(company=company, status='active')
    total_sal = sum(float(e.basic_salary or 0) for e in active)
    rows = [
        {'metric': 'إجمالي الموظفين النشطين', 'value': active.count()},
        {'metric': 'إجمالي الرواتب الشهرية', 'value': round(total_sal, 2)},
        {'metric': 'إجمالي الرواتب السنوية', 'value': round(total_sal * 12, 2)},
        {'metric': 'متوسط الراتب', 'value': round(total_sal/active.count() if active.count() else 0, 2)},
    ]
    return rows


# ═══════════════════════════════════════════════════
# API Views - كل تقرير عنده 3 endpoints: json, excel, pdf
# ═══════════════════════════════════════════════════

def _make_report_views(report_key, data_func, title, columns, needs_year_month=False, needs_year=False):
    """factory لتوليد 3 views (json, excel, pdf) لأي تقرير"""

    def _get_params(request):
        from datetime import date as _d
        if needs_year_month:
            year = int(request.GET.get('year', _d.today().year))
            month = int(request.GET.get('month', _d.today().month))
            return {'year': year, 'month': month}
        if needs_year:
            year = int(request.GET.get('year', _d.today().year))
            return {'year': year}
        return {}

    @api_view(['GET'])
    @authentication_classes([TokenAuthentication, JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def view_json(request):
        user = request.user
        if not _check_manager(user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)
        params = _get_params(request)
        rows = data_func(user, **params) if params else data_func(user)
        return Response({
            'title': title,
            'count': len(rows),
            'results': rows,
        })

    @api_view(['GET'])
    @authentication_classes([TokenAuthentication, JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def view_excel(request):
        from attendance.report_export_helper import export_to_excel
        user = request.user
        if not _check_manager(user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)
        params = _get_params(request)
        rows = data_func(user, **params) if params else data_func(user)
        if not rows:
            rows = [{'info': 'لا توجد بيانات'}]
            cols = [('info', 'ملاحظة', 40)]
        else:
            cols = columns
        return export_to_excel(title=title, columns=cols, rows=rows, user=user, filename=f'{report_key}.xlsx')

    @api_view(['GET'])
    @authentication_classes([TokenAuthentication, JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def view_pdf(request):
        from attendance.report_export_helper import export_to_pdf
        user = request.user
        if not _check_manager(user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)
        params = _get_params(request)
        rows = data_func(user, **params) if params else data_func(user)
        if not rows:
            rows = [{'info': 'لا توجد بيانات'}]
            cols = [('info', 'ملاحظة', 40)]
        else:
            cols = columns
        return export_to_pdf(title=title, columns=cols, rows=rows, user=user, filename=f'{report_key}.pdf')

    return view_json, view_excel, view_pdf


# ═══════════════════════════════════════════════════
# Generate all views
# ═══════════════════════════════════════════════════

reimbursements_report, reimbursements_export_excel, reimbursements_export_pdf = _make_report_views(
    'reimbursements', _reimbursements_data, 'تقرير رد المصروفات',
    [
        ('employee_name', 'اسم الموظف', 25),
        ('type', 'النوع', 20),
        ('subject', 'الموضوع', 30),
        ('amount', 'المبلغ', 15),
        ('status', 'الحالة', 15),
        ('created_at', 'التاريخ', 15),
    ],
)

bank_transfer_report, bank_transfer_export_excel, bank_transfer_export_pdf = _make_report_views(
    'bank_transfer', _bank_transfer_data, 'كشف تحويلات البنك',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('bank_name', 'البنك', 20),
        ('account_number', 'رقم الحساب', 20),
        ('iban', 'IBAN', 25),
        ('amount', 'المبلغ', 15),
    ],
)

insurance_report, insurance_export_excel, insurance_export_pdf = _make_report_views(
    'insurance', _insurance_data, 'تقرير التأمينات',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('insurance_number', 'رقم التأمين', 18),
        ('basic_salary', 'الراتب الأساسي', 15),
        ('insurance_base', 'الأساس التأميني', 18),
        ('insurance_amount', 'مبلغ التأمين', 15),
    ],
)

tax_report, tax_export_excel, tax_export_pdf = _make_report_views(
    'tax', _tax_data, 'تقرير الضرائب',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('basic_salary', 'الراتب الأساسي', 18),
        ('tax_amount', 'مبلغ الضريبة', 18),
    ],
    needs_year_month=True,
)

turnover_report, turnover_export_excel, turnover_export_pdf = _make_report_views(
    'turnover', _turnover_data, 'معدل دوران الموظفين',
    [
        ('metric', 'البند', 40),
        ('value', 'القيمة', 20),
    ],
    needs_year=True,
)

branch_comparison_report, branch_comparison_export_excel, branch_comparison_export_pdf = _make_report_views(
    'branch_comparison', _branch_comparison_data, 'مقارنة الفروع',
    [
        ('branch_name', 'الفرع', 25),
        ('employees_count', 'عدد الموظفين', 15),
        ('total_salary', 'إجمالي الرواتب', 20),
        ('avg_salary', 'متوسط الراتب', 18),
        ('max_salary', 'أعلى راتب', 15),
        ('min_salary', 'أقل راتب', 15),
        ('present_days', 'أيام الحضور 30 يوم', 18),
        ('absent_days', 'أيام الغياب 30 يوم', 18),
        ('total_late_minutes', 'إجمالي دقائق التأخير', 20),
        ('total_overtime_hours', 'إجمالي الأوفر تايم', 18),
    ],
)

contracts_expiry_report, contracts_expiry_export_excel, contracts_expiry_export_pdf = _make_report_views(
    'contracts_expiry', _contracts_expiry_data, 'تقرير العقود المنتهية',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('contract_end', 'تاريخ الانتهاء', 18),
        ('status', 'الحالة', 20),
        ('days', 'عدد الأيام', 15),
    ],
)

loans_advances_report, loans_advances_export_excel, loans_advances_export_pdf = _make_report_views(
    'loans_advances', _loans_advances_data, 'تقرير السلف والقروض',
    [
        ('employee_name', 'اسم الموظف', 25),
        ('type', 'النوع', 20),
        ('amount', 'المبلغ', 15),
        ('status', 'الحالة', 15),
        ('created_at', 'التاريخ', 15),
    ],
)

missions_performance_report, missions_performance_export_excel, missions_performance_export_pdf = _make_report_views(
    'missions_performance', _missions_performance_data, 'تقرير أداء المهام',
    [
        ('employee_name', 'اسم الموظف', 25),
        ('total_missions', 'إجمالي المهام', 18),
        ('completed', 'المكتملة', 15),
        ('in_progress', 'جاري تنفيذها', 18),
        ('pending', 'معلقة', 15),
        ('completion_rate', 'نسبة الإنجاز %', 20),
    ],
)

executive_dashboard_report, executive_dashboard_export_excel, executive_dashboard_export_pdf = _make_report_views(
    'executive_dashboard', _executive_dashboard_data, 'التقرير التنفيذي',
    [
        ('metric', 'البند', 40),
        ('value', 'القيمة', 25),
    ],
)

# ═══════════════════════════════════════════════════
# CEO/HR Unified Dashboard - نبض الشركة
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def unified_dashboard(request):
    """Dashboard شامل - كل ما يحتاجه صاحب الشركة والـ HR"""
    from datetime import date, timedelta
    from employees.models import Employee
    from attendance.models import Attendance
    from django.db.models import Sum, Count, Avg

    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    company = getattr(user, 'company', None)
    if not company:
        return Response({'error': 'لا توجد شركة'}, status=400)

    today = timezone.localdate()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month_end = month_start - timedelta(days=1)

    # ═══ 1) نبض الشركة النهاردة ═══
    all_emps = Employee._base_manager.filter(company=company).exclude(
        user__is_staff=True
    ).exclude(user__role__in=['company_admin', 'super_admin'])

    active_emps = all_emps.filter(status='active')
    total_active = active_emps.count()

    today_att = Attendance._base_manager.filter(
        employee__company=company, date=today,
    )
    present_today = today_att.filter(status='present').count()
    late_today = today_att.filter(status='late').count()
    absent_today = max(0, total_active - today_att.count())
    on_leave_today = today_att.filter(status='on_leave').count()

    attendance_rate = round((present_today + late_today) / max(total_active, 1) * 100, 1)

    # ═══ 2) المالية ═══
    total_monthly_salary = sum(float(e.basic_salary or 0) for e in active_emps)

    # سلف قائمة
    total_active_loans = 0
    active_loans_count = 0
    try:
        from requests_app.models import EmployeeRequest
        from django.db.models import Q
        loans = EmployeeRequest._base_manager.filter(
            company=company, status='approved',
        ).filter(Q(request_type__name__icontains='سلفة') | Q(request_type__name__icontains='قرض'))
        total_active_loans = sum(float(l.amount or 0) for l in loans)
        active_loans_count = loans.count()
    except Exception:
        pass

    # الفرق عن الشهر اللي فات
    last_month_att_count = Attendance._base_manager.filter(
        employee__company=company,
        date__gte=last_month_start, date__lte=last_month_end,
        status='present',
    ).count()
    this_month_att_count = Attendance._base_manager.filter(
        employee__company=company,
        date__gte=month_start, date__lte=today,
        status='present',
    ).count()

    # ═══ 3) القرارات المطلوبة ═══
    pending_requests = 0
    pending_leaves = 0
    try:
        from requests_app.models import EmployeeRequest
        pending_requests = EmployeeRequest._base_manager.filter(
            company=company, status='pending',
        ).count()
    except Exception:
        pass

    try:
        from leaves.models import LeaveRequest
        pending_leaves = LeaveRequest._base_manager.filter(
            company=company, status='pending',
        ).count()
    except Exception:
        pass

    # عقود قربت تنتهي (30 يوم)
    next_30_days = today + timedelta(days=30)
    contracts_expiring = active_emps.filter(
        contract_end_date__isnull=False,
        contract_end_date__gte=today,
        contract_end_date__lte=next_30_days,
    ).count()

    # موظفين في فترة تجربة (خلصت خلال الشهر)
    probation_ending = 0
    for emp in active_emps:
        if emp.hire_date and hasattr(emp, 'probation_months'):
            prob_months = emp.probation_months or 3
            probation_end = emp.hire_date + timedelta(days=prob_months * 30)
            if today <= probation_end <= next_30_days:
                probation_ending += 1

    # ═══ 4) الترند - آخر 30 يوم ═══
    attendance_trend = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        count = Attendance._base_manager.filter(
            employee__company=company, date=d, status='present',
        ).count()
        attendance_trend.append({
            'date': str(d),
            'present': count,
        })

    # ═══ 5) توزيع الموظفين حسب القسم ═══
    from companies.models import Department, Branch
    dept_distribution = []
    for dept in Department._base_manager.filter(company=company):
        count = active_emps.filter(department=dept).count()
        if count > 0:
            dept_distribution.append({
                'name': dept.name_ar,
                'count': count,
            })

    branch_distribution = []
    for br in Branch._base_manager.filter(company=company):
        emps_br = active_emps.filter(branch=br)
        count = emps_br.count()
        salary = sum(float(e.basic_salary or 0) for e in emps_br)
        if count > 0:
            branch_distribution.append({
                'name': br.name_ar,
                'count': count,
                'total_salary': round(salary, 2),
            })

    # ═══ 6) Turnover الشهر ═══
    hired_this_month = all_emps.filter(
        hire_date__gte=month_start, hire_date__lte=today,
    ).count()
    terminated_this_month = all_emps.filter(
        status__in=['terminated', 'resigned', 'retired'],
        termination_date__gte=month_start,
        termination_date__lte=today,
    ).count()

    # ═══ 7) أفضل 5 موظفين (حضور الشهر) ═══
    top_performers = []
    for emp in active_emps[:100]:  # نجيب 100 ونرتب
        emp_att = Attendance._base_manager.filter(
            employee=emp, date__gte=month_start, date__lte=today,
        )
        present = emp_att.filter(status='present').count()
        late = emp_att.filter(status='late').count()
        total_days = (today - month_start).days + 1
        score = (present * 100 + late * 50) / max(total_days, 1)
        top_performers.append({
            'employee_id': emp.id,
            'name': _employee_name(emp),
            'present_days': present,
            'late_days': late,
            'score': round(score, 1),
        })

    top_performers.sort(key=lambda x: x['score'], reverse=True)

    # ═══ 8) موظفين محتاجين متابعة ═══
    need_attention = []
    for emp in active_emps[:100]:
        emp_att = Attendance._base_manager.filter(
            employee=emp, date__gte=month_start, date__lte=today,
        )
        absent = emp_att.filter(status='absent').count()
        late = emp_att.filter(status='late').count()
        if absent >= 3 or late >= 5:
            need_attention.append({
                'employee_id': emp.id,
                'name': _employee_name(emp),
                'absent_days': absent,
                'late_days': late,
            })

    need_attention.sort(key=lambda x: (x['absent_days'] + x['late_days']), reverse=True)

    # ═══ 9) تنبيهات ذكية ═══
    alerts = []

    if contracts_expiring > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'file-warning',
            'title': f'{contracts_expiring} عقد قرب انتهاؤه',
            'action': '/hr/reports/contracts-expiry',
        })

    if pending_requests + pending_leaves > 0:
        alerts.append({
            'type': 'info',
            'icon': 'inbox',
            'title': f'{pending_requests + pending_leaves} طلب معلق ينتظر الموافقة',
            'action': '/hr/requests',
        })

    if active_loans_count > 0:
        alerts.append({
            'type': 'info',
            'icon': 'wallet',
            'title': f'{active_loans_count} سلفة/قرض قائمة ({round(total_active_loans, 0)} جنيه)',
            'action': '/hr/reports/loans-advances',
        })

    if len(need_attention) > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'alert-triangle',
            'title': f'{len(need_attention)} موظف يحتاج متابعة (تأخير/غياب)',
            'action': '/hr/attendance',
        })

    if probation_ending > 0:
        alerts.append({
            'type': 'info',
            'icon': 'user-check',
            'title': f'{probation_ending} موظف تنتهي فترة تجربتهم',
            'action': '/hr/employees',
        })

    return Response({
        'today': str(today),
        'pulse': {
            'total_employees': total_active,
            'present': present_today,
            'late': late_today,
            'absent': absent_today,
            'on_leave': on_leave_today,
            'attendance_rate': attendance_rate,
        },
        'financial': {
            'monthly_salary': round(total_monthly_salary, 2),
            'yearly_salary': round(total_monthly_salary * 12, 2),
            'active_loans_amount': round(total_active_loans, 2),
            'active_loans_count': active_loans_count,
            'this_month_attendance': this_month_att_count,
            'last_month_attendance': last_month_att_count,
            'attendance_change': this_month_att_count - last_month_att_count,
        },
        'decisions': {
            'pending_requests': pending_requests,
            'pending_leaves': pending_leaves,
            'contracts_expiring_30d': contracts_expiring,
            'probation_ending_30d': probation_ending,
        },
        'trend': {
            'attendance_last_30_days': attendance_trend,
        },
        'distribution': {
            'by_department': dept_distribution,
            'by_branch': branch_distribution,
        },
        'turnover': {
            'hired_this_month': hired_this_month,
            'terminated_this_month': terminated_this_month,
        },
        'top_performers': top_performers[:5],
        'need_attention': need_attention[:5],
        'alerts': alerts,
    })


```

======================================================================
## FILE: /var/www/motionhr/attendance/urls.py
======================================================================

```
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

```
