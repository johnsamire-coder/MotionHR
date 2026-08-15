
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

