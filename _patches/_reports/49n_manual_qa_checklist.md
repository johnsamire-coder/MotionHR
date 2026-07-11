# Manual QA Checklist — MotionHR

استخدم هذه القائمة للتجربة اليدوية بجانب الفحص الآلي.

## 1) قواعد التنفيذ

- افتح كل رابط وسجّل هل الصفحة منطقية أم لا.
- جرّب كل زرار ظاهر في الصفحة (عرض / حفظ / رجوع / طباعة / تصدير).
- أي Route حالته `SKIPPED` أو `REDIRECT` أو `FORBIDDEN` يحتاج مراجعة يدوية.
- علّم كل بند بـ ✅ أو ❌ أثناء الاختبار.

## 2) بيانات المستخدمين المتاحة

- **anonymous**: غير متوفر
- **super_admin**: `john`
- **company_admin**: `demo_admin`
- **hr_manager**: `hr_manager`
- **manager**: `manager1`
- **employee**: `John`
- **field_employee**: غير متوفر

## اختبار Role: super_admin

### أ) فحص عام
- [ ] تسجيل الدخول
- [ ] فتح Dashboard
- [ ] فتح البروفايل
- [ ] فتح تغيير كلمة المرور (إن وجدت)
- [ ] تسجيل الخروج

### ب) الصفحات التي فتحت آليًا بنجاح

- [ ] `/about/` — (landing:about)
- [ ] `/accounts/login-settings/` — (accounts:login_settings)
- [ ] `/accounts/notifications/` — (accounts:notifications)
- [ ] `/accounts/notifications/send/` — (accounts:send_employee_notification)
- [ ] `/accounts/profile/` — (accounts:profile)
- [ ] `/attendance/` — (attendance:list)
- [ ] `/attendance/` — (attendance:attendance_list)
- [ ] `/attendance/api/live-locations/` — (attendance:api_live_locations)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor_data)
- [ ] `/attendance/api/stealth-location/` — (attendance:api_stealth_location)
- [ ] `/attendance/check-in/` — (attendance:check_in_old)
- [ ] `/attendance/check-in/` — (attendance:check_in_page_old)
- [ ] `/attendance/check-in/` — (attendance:check_in)
- [ ] `/attendance/late-notifications/` — (attendance:late_notifications)
- [ ] `/attendance/map/` — (attendance:live_map)
- [ ] `/attendance/monitor/` — (attendance:field_employees_monitor)
- [ ] `/attendance/monitor/` — (attendance:monitor)
- [ ] `/attendance/my-warnings/` — (attendance:my_warnings)
- [ ] `/attendance/schedule/` — (attendance:schedule_week)
- [ ] `/attendance/schedule/assignment/` — (attendance:assignment_add)
- [ ] `/attendance/stealth-alerts/` — (attendance:stealth_alerts)
- [ ] `/attendance/stealth-manage/` — (attendance:stealth_manage)
- [ ] `/attendance/tracking/` — (attendance:tracking_page)
- [ ] `/attendance/tracking/` — (attendance:tracking)
- [ ] `/attendance/visits/` — (attendance:visits)
- [ ] `/attendance/visits/` — (attendance:visits_list)
- [ ] `/attendance/visits/add/` — (attendance:visit_add)
- [ ] `/companies/approval-flows/` — (companies:approval_flows)
- [ ] `/companies/branches/` — (companies:branches_list)
- [ ] `/companies/branches/1/edit/` — (companies:branch_edit)
- [ ] `/companies/branches/add/` — (companies:branch_add)
- [ ] `/companies/charter/` — (companies:charter)
- [ ] `/companies/charter/1/sign/` — (companies:charter_sign)
- [ ] `/companies/charter/manage/` — (companies:charter_manage)
- [ ] `/companies/delegations/` — (companies:delegations)
- [ ] `/companies/delegations/add/` — (companies:delegation_add)
- [ ] `/companies/departments/1/edit/` — (companies:department_edit)
- [ ] `/companies/departments/add/` — (companies:department_add)
- [ ] `/companies/notification-settings/` — (companies:notification_settings)
- [ ] `/companies/policies/` — (companies:policies)
- [ ] `/companies/settings/` — (companies:settings)
- [ ] `/companies/shifts/` — (companies:shifts_list)
- [ ] `/companies/shifts/add/` — (companies:shift_add)
- [ ] `/contact/` — (landing:contact)
- [ ] `/dashboard/` — (dashboard)
- [ ] `/employees/` — (employee_list)
- [ ] `/employees/` — (employees:employee_list)
- [ ] `/employees/` — (employees:list)
- [ ] `/employees/add/` — (employees:employee_add)
- [ ] `/employees/add/` — (employee_create)
- [ ] `/employees/add/` — (employee_add)
- [ ] `/employees/add/` — (add_employee)
- [ ] `/employees/add/` — (employees:add_employee)
- [ ] `/employees/add/` — (employees:employee_create)
- [ ] `/employees/add/` — (employees:add)
- [ ] `/employees/api/manager-options/` — (manager_options_api)
- [ ] `/employees/api/manager-options/` — (employees:manager_options_api)
- [ ] `/employees/api/search/` — (employees:search_api)
- [ ] `/employees/api/search/` — (employees:employee_search_api)
- [ ] `/employees/api/search/` — (employee_search_api)
- [ ] `/employees/hierarchy/` — (hierarchy_manage)
- [ ] `/employees/hierarchy/` — (employees:hierarchy_manage)
- [ ] `/employees/my-balance/` — (employee_balance)
- [ ] `/employees/my-balance/` — (employees:my_balance)
- [ ] `/employees/my-balance/` — (employees:my_balance_view)
- [ ] `/employees/my-balance/` — (employees:employee_balance)
- [ ] `/employees/my-balance/` — (my_balance_view)
- [ ] `/employees/my-deductions/` — (employees:my_deductions_view)
- [ ] `/employees/my-deductions/` — (employee_deductions)
- [ ] `/employees/my-deductions/` — (employees:my_deductions)
- [ ] `/employees/my-deductions/` — (my_deductions_view)
- [ ] `/employees/my-deductions/` — (employees:employee_deductions)
- [ ] `/employees/print/` — (employees_print_all)
- [ ] `/employees/print/` — (employees_print)
- [ ] `/employees/print/` — (employees:print_all)
- [ ] `/employees/print/` — (employees:employees_print_all)
- [ ] `/employees/print/` — (employee_print)
- [ ] `/employees/print/` — (employee_print_all)
- [ ] `/employees/print/` — (employees:employee_print)
- [ ] `/employees/print/` — (employees:employees_print)
- [ ] `/employees/print/` — (employees:employee_print_all)
- [ ] `/free-trial/` — (landing:free_trial)
- [ ] `/leaves/` — (leaves:leave_requests_list)
- [ ] `/leaves/add/` — (leaves:leave_request_add)
- [ ] `/leaves/balances/` — (leaves:leave_balances)
- [ ] `/leaves/types/` — (leaves:leave_types_list)
- [ ] `/leaves/types/add/` — (leaves:leave_type_add)
- [ ] `/manifest.json` — (manifest)
- [ ] `/offline/` — (offline)
- [ ] `/password-change/` — (password_change)
- [ ] `/password-change/done/` — (password_change_done)
- [ ] `/password-reset-complete/` — (password_reset_complete)
- [ ] `/password-reset/` — (password_reset)
- [ ] `/password-reset/done/` — (password_reset_done)
- [ ] `/pricing/` — (landing:pricing)
- [ ] `/reports/` — (reports:home)
- [ ] `/reports/attendance/` — (reports:attendance)
- [ ] `/reports/field/` — (reports:field)
- [ ] `/requests/` — (requests_app:list)
- [ ] `/requests/add/` — (requests_app:add)
- [ ] `/search/` — (global_search)
- [ ] `/subscriptions/contact-sales/` — (subscriptions:contact_sales)
- [ ] `/subscriptions/feature-locked/` — (subscriptions:feature_locked)
- [ ] `/subscriptions/my-plan/` — (subscriptions:my_plan)
- [ ] `/subscriptions/my-subscription/` — (subscriptions:my_subscription)
- [ ] `/subscriptions/plans/` — (subscriptions:plans_list)
- [ ] `/subscriptions/subscriptions/` — (subscriptions:subscriptions_list)
- [ ] `/subscriptions/subscriptions/1/` — (subscriptions:detail)
- [ ] `/subscriptions/subscriptions/create/` — (subscriptions:create)
- [ ] `/subscriptions/upgrade/` — (subscriptions:upgrade_plan)
- [ ] `/subscriptions/upgrade/module/payroll/` — (subscriptions:upsell)
- [ ] `/sw.js` — (service_worker)

### ج) صفحات تحتاج مراجعة خاصة

- [ ] `/companies/charter/1/acceptance-status/` — (companies:charter_acceptance_status) — **FORBIDDEN**
- [ ] `/companies/departments/` — (companies:departments_list) — **FORBIDDEN**
- [ ] `/` — (landing:home) — **REDIRECT**
- [ ] `/accounts/profile/update/` — (accounts:profile_update) — **REDIRECT**
- [ ] `/companies/charter/accept/` — (companies:charter_accept) — **REDIRECT**
- [ ] `/free-trial/success/` — (landing:free_trial_success) — **REDIRECT**
- [ ] `/login/` — (login) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/activate/` — (subscriptions:activate) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/cancel/` — (subscriptions:cancel) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/extend/` — (subscriptions:extend) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/upgrade/` — (subscriptions:upgrade) — **REDIRECT**
- [ ] `/companies/branches/1/delete/` — (companies:branch_delete) — **SKIPPED**
- [ ] `/companies/delegations/1/deactivate/` — (companies:delegation_deactivate) — **SKIPPED**
- [ ] `/companies/departments/1/delete/` — (companies:department_delete) — **SKIPPED**
- [ ] `/companies/shifts/1/delete/` — (companies:shift_delete) — **SKIPPED**
- [ ] `/logout/` — (logout) — **SKIPPED**

### د) سيناريوهات مهمة لهذا الدور

- [ ] مراجعة Admin / الشاشات الإدارية
- [ ] التحقق من أن كل التطبيقات ظاهرة وتفتح

## اختبار Role: company_admin

### أ) فحص عام
- [ ] تسجيل الدخول
- [ ] فتح Dashboard
- [ ] فتح البروفايل
- [ ] فتح تغيير كلمة المرور (إن وجدت)
- [ ] تسجيل الخروج

### ب) الصفحات التي فتحت آليًا بنجاح

- [ ] `/about/` — (landing:about)
- [ ] `/accounts/login-settings/` — (accounts:login_settings)
- [ ] `/accounts/notifications/` — (accounts:notifications)
- [ ] `/accounts/notifications/send/` — (accounts:send_employee_notification)
- [ ] `/accounts/profile/` — (accounts:profile)
- [ ] `/attendance/` — (attendance:list)
- [ ] `/attendance/` — (attendance:attendance_list)
- [ ] `/attendance/api/live-locations/` — (attendance:api_live_locations)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor_data)
- [ ] `/attendance/api/stealth-location/` — (attendance:api_stealth_location)
- [ ] `/attendance/check-in/` — (attendance:check_in_old)
- [ ] `/attendance/check-in/` — (attendance:check_in_page_old)
- [ ] `/attendance/check-in/` — (attendance:check_in)
- [ ] `/attendance/late-notifications/` — (attendance:late_notifications)
- [ ] `/attendance/map/` — (attendance:live_map)
- [ ] `/attendance/monitor/` — (attendance:field_employees_monitor)
- [ ] `/attendance/monitor/` — (attendance:monitor)
- [ ] `/attendance/schedule/` — (attendance:schedule_week)
- [ ] `/attendance/schedule/assignment/` — (attendance:assignment_add)
- [ ] `/attendance/stealth-alerts/` — (attendance:stealth_alerts)
- [ ] `/attendance/stealth-manage/` — (attendance:stealth_manage)
- [ ] `/attendance/tracking/` — (attendance:tracking_page)
- [ ] `/attendance/tracking/` — (attendance:tracking)
- [ ] `/attendance/visits/` — (attendance:visits)
- [ ] `/attendance/visits/` — (attendance:visits_list)
- [ ] `/attendance/visits/add/` — (attendance:visit_add)
- [ ] `/companies/approval-flows/` — (companies:approval_flows)
- [ ] `/companies/branches/` — (companies:branches_list)
- [ ] `/companies/branches/1/edit/` — (companies:branch_edit)
- [ ] `/companies/branches/add/` — (companies:branch_add)
- [ ] `/companies/charter/` — (companies:charter)
- [ ] `/companies/charter/1/acceptance-status/` — (companies:charter_acceptance_status)
- [ ] `/companies/charter/manage/` — (companies:charter_manage)
- [ ] `/companies/delegations/` — (companies:delegations)
- [ ] `/companies/delegations/add/` — (companies:delegation_add)
- [ ] `/companies/departments/` — (companies:departments_list)
- [ ] `/companies/departments/1/edit/` — (companies:department_edit)
- [ ] `/companies/departments/add/` — (companies:department_add)
- [ ] `/companies/notification-settings/` — (companies:notification_settings)
- [ ] `/companies/policies/` — (companies:policies)
- [ ] `/companies/settings/` — (companies:settings)
- [ ] `/companies/shifts/` — (companies:shifts_list)
- [ ] `/companies/shifts/add/` — (companies:shift_add)
- [ ] `/contact/` — (landing:contact)
- [ ] `/dashboard/` — (dashboard)
- [ ] `/employees/` — (employee_list)
- [ ] `/employees/` — (employees:employee_list)
- [ ] `/employees/` — (employees:list)
- [ ] `/employees/add/` — (employees:employee_add)
- [ ] `/employees/add/` — (employee_create)
- [ ] `/employees/add/` — (employee_add)
- [ ] `/employees/add/` — (add_employee)
- [ ] `/employees/add/` — (employees:add_employee)
- [ ] `/employees/add/` — (employees:employee_create)
- [ ] `/employees/add/` — (employees:add)
- [ ] `/employees/api/manager-options/` — (manager_options_api)
- [ ] `/employees/api/manager-options/` — (employees:manager_options_api)
- [ ] `/employees/api/search/` — (employees:search_api)
- [ ] `/employees/api/search/` — (employees:employee_search_api)
- [ ] `/employees/api/search/` — (employee_search_api)
- [ ] `/employees/hierarchy/` — (hierarchy_manage)
- [ ] `/employees/hierarchy/` — (employees:hierarchy_manage)
- [ ] `/employees/print/` — (employees_print_all)
- [ ] `/employees/print/` — (employees_print)
- [ ] `/employees/print/` — (employees:print_all)
- [ ] `/employees/print/` — (employees:employees_print_all)
- [ ] `/employees/print/` — (employee_print)
- [ ] `/employees/print/` — (employee_print_all)
- [ ] `/employees/print/` — (employees:employee_print)
- [ ] `/employees/print/` — (employees:employees_print)
- [ ] `/employees/print/` — (employees:employee_print_all)
- [ ] `/free-trial/` — (landing:free_trial)
- [ ] `/leaves/` — (leaves:leave_requests_list)
- [ ] `/leaves/add/` — (leaves:leave_request_add)
- [ ] `/leaves/balances/` — (leaves:leave_balances)
- [ ] `/leaves/types/` — (leaves:leave_types_list)
- [ ] `/leaves/types/add/` — (leaves:leave_type_add)
- [ ] `/manifest.json` — (manifest)
- [ ] `/offline/` — (offline)
- [ ] `/password-change/` — (password_change)
- [ ] `/password-change/done/` — (password_change_done)
- [ ] `/password-reset-complete/` — (password_reset_complete)
- [ ] `/password-reset/` — (password_reset)
- [ ] `/password-reset/done/` — (password_reset_done)
- [ ] `/pricing/` — (landing:pricing)
- [ ] `/reports/` — (reports:home)
- [ ] `/reports/attendance/` — (reports:attendance)
- [ ] `/reports/field/` — (reports:field)
- [ ] `/requests/` — (requests_app:list)
- [ ] `/requests/add/` — (requests_app:add)
- [ ] `/search/` — (global_search)
- [ ] `/subscriptions/contact-sales/` — (subscriptions:contact_sales)
- [ ] `/subscriptions/feature-locked/` — (subscriptions:feature_locked)
- [ ] `/subscriptions/my-plan/` — (subscriptions:my_plan)
- [ ] `/subscriptions/my-subscription/` — (subscriptions:my_subscription)
- [ ] `/subscriptions/upgrade/` — (subscriptions:upgrade_plan)
- [ ] `/subscriptions/upgrade/module/payroll/` — (subscriptions:upsell)
- [ ] `/sw.js` — (service_worker)

### ج) صفحات تحتاج مراجعة خاصة

- [ ] `/` — (landing:home) — **REDIRECT**
- [ ] `/accounts/profile/update/` — (accounts:profile_update) — **REDIRECT**
- [ ] `/attendance/my-warnings/` — (attendance:my_warnings) — **REDIRECT**
- [ ] `/companies/charter/1/sign/` — (companies:charter_sign) — **REDIRECT**
- [ ] `/companies/charter/accept/` — (companies:charter_accept) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employees:employee_balance) — **REDIRECT**
- [ ] `/employees/my-balance/` — (my_balance_view) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employee_balance) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employees:my_balance) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employees:my_balance_view) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employee_deductions) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (my_deductions_view) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employees:my_deductions) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employees:my_deductions_view) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employees:employee_deductions) — **REDIRECT**
- [ ] `/free-trial/success/` — (landing:free_trial_success) — **REDIRECT**
- [ ] `/login/` — (login) — **REDIRECT**
- [ ] `/subscriptions/` — (subscriptions:admin_dashboard) — **REDIRECT**
- [ ] `/subscriptions/plans/` — (subscriptions:plans_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/` — (subscriptions:subscriptions_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/` — (subscriptions:detail) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/activate/` — (subscriptions:activate) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/cancel/` — (subscriptions:cancel) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/extend/` — (subscriptions:extend) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/upgrade/` — (subscriptions:upgrade) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/create/` — (subscriptions:create) — **REDIRECT**
- [ ] `/companies/branches/1/delete/` — (companies:branch_delete) — **SKIPPED**
- [ ] `/companies/delegations/1/deactivate/` — (companies:delegation_deactivate) — **SKIPPED**
- [ ] `/companies/departments/1/delete/` — (companies:department_delete) — **SKIPPED**
- [ ] `/companies/shifts/1/delete/` — (companies:shift_delete) — **SKIPPED**
- [ ] `/logout/` — (logout) — **SKIPPED**

### د) سيناريوهات مهمة لهذا الدور

- [ ] إعداد الشركة والفروع والإدارات
- [ ] تجربة صفحة الهيكل الوظيفي
- [ ] إضافة موظف جديد
- [ ] فتح ملف المستندات لموظف
- [ ] تجربة الحضور / الخريطة / التتبع
- [ ] تجربة الإجازات والطلبات
- [ ] فتح كل التقارير والتصدير
- [ ] تجربة صفحات الـ Add-ons / Upsell

## اختبار Role: hr_manager

### أ) فحص عام
- [ ] تسجيل الدخول
- [ ] فتح Dashboard
- [ ] فتح البروفايل
- [ ] فتح تغيير كلمة المرور (إن وجدت)
- [ ] تسجيل الخروج

### ب) الصفحات التي فتحت آليًا بنجاح

- [ ] `/about/` — (landing:about)
- [ ] `/accounts/login-settings/` — (accounts:login_settings)
- [ ] `/accounts/notifications/` — (accounts:notifications)
- [ ] `/accounts/notifications/send/` — (accounts:send_employee_notification)
- [ ] `/accounts/profile/` — (accounts:profile)
- [ ] `/attendance/` — (attendance:list)
- [ ] `/attendance/` — (attendance:attendance_list)
- [ ] `/attendance/api/live-locations/` — (attendance:api_live_locations)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor_data)
- [ ] `/attendance/api/stealth-location/` — (attendance:api_stealth_location)
- [ ] `/attendance/check-in/` — (attendance:check_in_old)
- [ ] `/attendance/check-in/` — (attendance:check_in_page_old)
- [ ] `/attendance/check-in/` — (attendance:check_in)
- [ ] `/attendance/late-notifications/` — (attendance:late_notifications)
- [ ] `/attendance/map/` — (attendance:live_map)
- [ ] `/attendance/monitor/` — (attendance:field_employees_monitor)
- [ ] `/attendance/monitor/` — (attendance:monitor)
- [ ] `/attendance/my-warnings/` — (attendance:my_warnings)
- [ ] `/attendance/schedule/` — (attendance:schedule_week)
- [ ] `/attendance/schedule/assignment/` — (attendance:assignment_add)
- [ ] `/attendance/stealth-alerts/` — (attendance:stealth_alerts)
- [ ] `/attendance/stealth-manage/` — (attendance:stealth_manage)
- [ ] `/attendance/tracking/` — (attendance:tracking_page)
- [ ] `/attendance/tracking/` — (attendance:tracking)
- [ ] `/attendance/visits/` — (attendance:visits)
- [ ] `/attendance/visits/` — (attendance:visits_list)
- [ ] `/attendance/visits/add/` — (attendance:visit_add)
- [ ] `/companies/approval-flows/` — (companies:approval_flows)
- [ ] `/companies/branches/` — (companies:branches_list)
- [ ] `/companies/branches/1/edit/` — (companies:branch_edit)
- [ ] `/companies/branches/add/` — (companies:branch_add)
- [ ] `/companies/charter/` — (companies:charter)
- [ ] `/companies/charter/1/acceptance-status/` — (companies:charter_acceptance_status)
- [ ] `/companies/charter/1/sign/` — (companies:charter_sign)
- [ ] `/companies/charter/manage/` — (companies:charter_manage)
- [ ] `/companies/delegations/` — (companies:delegations)
- [ ] `/companies/delegations/add/` — (companies:delegation_add)
- [ ] `/companies/departments/` — (companies:departments_list)
- [ ] `/companies/departments/1/edit/` — (companies:department_edit)
- [ ] `/companies/departments/add/` — (companies:department_add)
- [ ] `/companies/notification-settings/` — (companies:notification_settings)
- [ ] `/companies/policies/` — (companies:policies)
- [ ] `/companies/settings/` — (companies:settings)
- [ ] `/companies/shifts/` — (companies:shifts_list)
- [ ] `/companies/shifts/add/` — (companies:shift_add)
- [ ] `/contact/` — (landing:contact)
- [ ] `/dashboard/` — (dashboard)
- [ ] `/employees/` — (employee_list)
- [ ] `/employees/` — (employees:employee_list)
- [ ] `/employees/` — (employees:list)
- [ ] `/employees/add/` — (employees:employee_add)
- [ ] `/employees/add/` — (employee_create)
- [ ] `/employees/add/` — (employee_add)
- [ ] `/employees/add/` — (add_employee)
- [ ] `/employees/add/` — (employees:add_employee)
- [ ] `/employees/add/` — (employees:employee_create)
- [ ] `/employees/add/` — (employees:add)
- [ ] `/employees/api/manager-options/` — (manager_options_api)
- [ ] `/employees/api/manager-options/` — (employees:manager_options_api)
- [ ] `/employees/api/search/` — (employees:search_api)
- [ ] `/employees/api/search/` — (employees:employee_search_api)
- [ ] `/employees/api/search/` — (employee_search_api)
- [ ] `/employees/hierarchy/` — (hierarchy_manage)
- [ ] `/employees/hierarchy/` — (employees:hierarchy_manage)
- [ ] `/employees/my-balance/` — (employee_balance)
- [ ] `/employees/my-balance/` — (employees:my_balance)
- [ ] `/employees/my-balance/` — (employees:my_balance_view)
- [ ] `/employees/my-balance/` — (employees:employee_balance)
- [ ] `/employees/my-balance/` — (my_balance_view)
- [ ] `/employees/my-deductions/` — (employees:my_deductions_view)
- [ ] `/employees/my-deductions/` — (employee_deductions)
- [ ] `/employees/my-deductions/` — (employees:my_deductions)
- [ ] `/employees/my-deductions/` — (my_deductions_view)
- [ ] `/employees/my-deductions/` — (employees:employee_deductions)
- [ ] `/employees/print/` — (employees_print_all)
- [ ] `/employees/print/` — (employees_print)
- [ ] `/employees/print/` — (employees:print_all)
- [ ] `/employees/print/` — (employees:employees_print_all)
- [ ] `/employees/print/` — (employee_print)
- [ ] `/employees/print/` — (employee_print_all)
- [ ] `/employees/print/` — (employees:employee_print)
- [ ] `/employees/print/` — (employees:employees_print)
- [ ] `/employees/print/` — (employees:employee_print_all)
- [ ] `/free-trial/` — (landing:free_trial)
- [ ] `/leaves/` — (leaves:leave_requests_list)
- [ ] `/leaves/add/` — (leaves:leave_request_add)
- [ ] `/leaves/balances/` — (leaves:leave_balances)
- [ ] `/leaves/types/` — (leaves:leave_types_list)
- [ ] `/leaves/types/add/` — (leaves:leave_type_add)
- [ ] `/manifest.json` — (manifest)
- [ ] `/offline/` — (offline)
- [ ] `/password-change/` — (password_change)
- [ ] `/password-change/done/` — (password_change_done)
- [ ] `/password-reset-complete/` — (password_reset_complete)
- [ ] `/password-reset/` — (password_reset)
- [ ] `/password-reset/done/` — (password_reset_done)
- [ ] `/pricing/` — (landing:pricing)
- [ ] `/reports/` — (reports:home)
- [ ] `/reports/attendance/` — (reports:attendance)
- [ ] `/reports/field/` — (reports:field)
- [ ] `/requests/` — (requests_app:list)
- [ ] `/requests/add/` — (requests_app:add)
- [ ] `/search/` — (global_search)
- [ ] `/subscriptions/contact-sales/` — (subscriptions:contact_sales)
- [ ] `/subscriptions/feature-locked/` — (subscriptions:feature_locked)
- [ ] `/subscriptions/my-plan/` — (subscriptions:my_plan)
- [ ] `/subscriptions/my-subscription/` — (subscriptions:my_subscription)
- [ ] `/subscriptions/upgrade/` — (subscriptions:upgrade_plan)
- [ ] `/subscriptions/upgrade/module/payroll/` — (subscriptions:upsell)
- [ ] `/sw.js` — (service_worker)

### ج) صفحات تحتاج مراجعة خاصة

- [ ] `/` — (landing:home) — **REDIRECT**
- [ ] `/accounts/profile/update/` — (accounts:profile_update) — **REDIRECT**
- [ ] `/companies/charter/accept/` — (companies:charter_accept) — **REDIRECT**
- [ ] `/free-trial/success/` — (landing:free_trial_success) — **REDIRECT**
- [ ] `/login/` — (login) — **REDIRECT**
- [ ] `/subscriptions/` — (subscriptions:admin_dashboard) — **REDIRECT**
- [ ] `/subscriptions/plans/` — (subscriptions:plans_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/` — (subscriptions:subscriptions_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/` — (subscriptions:detail) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/activate/` — (subscriptions:activate) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/cancel/` — (subscriptions:cancel) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/extend/` — (subscriptions:extend) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/upgrade/` — (subscriptions:upgrade) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/create/` — (subscriptions:create) — **REDIRECT**
- [ ] `/companies/branches/1/delete/` — (companies:branch_delete) — **SKIPPED**
- [ ] `/companies/delegations/1/deactivate/` — (companies:delegation_deactivate) — **SKIPPED**
- [ ] `/companies/departments/1/delete/` — (companies:department_delete) — **SKIPPED**
- [ ] `/companies/shifts/1/delete/` — (companies:shift_delete) — **SKIPPED**
- [ ] `/logout/` — (logout) — **SKIPPED**

### د) سيناريوهات مهمة لهذا الدور

- [ ] إضافة / تعديل موظف
- [ ] مراجعة الحضور
- [ ] مراجعة الإجازات
- [ ] مراجعة الطلبات
- [ ] فتح ملف شامل لموظف
- [ ] رفع مستندات موظف

## اختبار Role: manager

### أ) فحص عام
- [ ] تسجيل الدخول
- [ ] فتح Dashboard
- [ ] فتح البروفايل
- [ ] فتح تغيير كلمة المرور (إن وجدت)
- [ ] تسجيل الخروج

### ب) الصفحات التي فتحت آليًا بنجاح

- [ ] `/about/` — (landing:about)
- [ ] `/accounts/login-settings/` — (accounts:login_settings)
- [ ] `/accounts/notifications/` — (accounts:notifications)
- [ ] `/accounts/profile/` — (accounts:profile)
- [ ] `/attendance/` — (attendance:list)
- [ ] `/attendance/` — (attendance:attendance_list)
- [ ] `/attendance/api/live-locations/` — (attendance:api_live_locations)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor_data)
- [ ] `/attendance/api/stealth-location/` — (attendance:api_stealth_location)
- [ ] `/attendance/check-in/` — (attendance:check_in_old)
- [ ] `/attendance/check-in/` — (attendance:check_in_page_old)
- [ ] `/attendance/check-in/` — (attendance:check_in)
- [ ] `/attendance/late-notifications/` — (attendance:late_notifications)
- [ ] `/attendance/map/` — (attendance:live_map)
- [ ] `/attendance/monitor/` — (attendance:field_employees_monitor)
- [ ] `/attendance/monitor/` — (attendance:monitor)
- [ ] `/attendance/my-warnings/` — (attendance:my_warnings)
- [ ] `/attendance/schedule/` — (attendance:schedule_week)
- [ ] `/attendance/schedule/assignment/` — (attendance:assignment_add)
- [ ] `/attendance/stealth-alerts/` — (attendance:stealth_alerts)
- [ ] `/attendance/stealth-manage/` — (attendance:stealth_manage)
- [ ] `/attendance/tracking/` — (attendance:tracking_page)
- [ ] `/attendance/tracking/` — (attendance:tracking)
- [ ] `/attendance/visits/` — (attendance:visits)
- [ ] `/attendance/visits/` — (attendance:visits_list)
- [ ] `/attendance/visits/add/` — (attendance:visit_add)
- [ ] `/companies/branches/` — (companies:branches_list)
- [ ] `/companies/branches/1/edit/` — (companies:branch_edit)
- [ ] `/companies/branches/add/` — (companies:branch_add)
- [ ] `/companies/charter/` — (companies:charter)
- [ ] `/companies/charter/1/sign/` — (companies:charter_sign)
- [ ] `/companies/charter/manage/` — (companies:charter_manage)
- [ ] `/companies/delegations/` — (companies:delegations)
- [ ] `/companies/delegations/add/` — (companies:delegation_add)
- [ ] `/companies/departments/` — (companies:departments_list)
- [ ] `/companies/departments/1/edit/` — (companies:department_edit)
- [ ] `/companies/departments/add/` — (companies:department_add)
- [ ] `/companies/policies/` — (companies:policies)
- [ ] `/companies/settings/` — (companies:settings)
- [ ] `/companies/shifts/` — (companies:shifts_list)
- [ ] `/companies/shifts/add/` — (companies:shift_add)
- [ ] `/contact/` — (landing:contact)
- [ ] `/dashboard/` — (dashboard)
- [ ] `/employees/` — (employee_list)
- [ ] `/employees/` — (employees:employee_list)
- [ ] `/employees/` — (employees:list)
- [ ] `/employees/api/manager-options/` — (manager_options_api)
- [ ] `/employees/api/manager-options/` — (employees:manager_options_api)
- [ ] `/employees/api/search/` — (employees:search_api)
- [ ] `/employees/api/search/` — (employees:employee_search_api)
- [ ] `/employees/api/search/` — (employee_search_api)
- [ ] `/employees/my-balance/` — (employee_balance)
- [ ] `/employees/my-balance/` — (employees:my_balance)
- [ ] `/employees/my-balance/` — (employees:my_balance_view)
- [ ] `/employees/my-balance/` — (employees:employee_balance)
- [ ] `/employees/my-balance/` — (my_balance_view)
- [ ] `/employees/my-deductions/` — (employees:my_deductions_view)
- [ ] `/employees/my-deductions/` — (employee_deductions)
- [ ] `/employees/my-deductions/` — (employees:my_deductions)
- [ ] `/employees/my-deductions/` — (my_deductions_view)
- [ ] `/employees/my-deductions/` — (employees:employee_deductions)
- [ ] `/employees/print/` — (employees_print_all)
- [ ] `/employees/print/` — (employees_print)
- [ ] `/employees/print/` — (employees:print_all)
- [ ] `/employees/print/` — (employees:employees_print_all)
- [ ] `/employees/print/` — (employee_print)
- [ ] `/employees/print/` — (employee_print_all)
- [ ] `/employees/print/` — (employees:employee_print)
- [ ] `/employees/print/` — (employees:employees_print)
- [ ] `/employees/print/` — (employees:employee_print_all)
- [ ] `/free-trial/` — (landing:free_trial)
- [ ] `/leaves/` — (leaves:leave_requests_list)
- [ ] `/leaves/add/` — (leaves:leave_request_add)
- [ ] `/leaves/balances/` — (leaves:leave_balances)
- [ ] `/leaves/types/` — (leaves:leave_types_list)
- [ ] `/leaves/types/add/` — (leaves:leave_type_add)
- [ ] `/manifest.json` — (manifest)
- [ ] `/offline/` — (offline)
- [ ] `/password-change/` — (password_change)
- [ ] `/password-change/done/` — (password_change_done)
- [ ] `/password-reset-complete/` — (password_reset_complete)
- [ ] `/password-reset/` — (password_reset)
- [ ] `/password-reset/done/` — (password_reset_done)
- [ ] `/pricing/` — (landing:pricing)
- [ ] `/reports/` — (reports:home)
- [ ] `/reports/attendance/` — (reports:attendance)
- [ ] `/reports/field/` — (reports:field)
- [ ] `/requests/` — (requests_app:list)
- [ ] `/requests/add/` — (requests_app:add)
- [ ] `/search/` — (global_search)
- [ ] `/subscriptions/contact-sales/` — (subscriptions:contact_sales)
- [ ] `/subscriptions/feature-locked/` — (subscriptions:feature_locked)
- [ ] `/subscriptions/my-plan/` — (subscriptions:my_plan)
- [ ] `/subscriptions/my-subscription/` — (subscriptions:my_subscription)
- [ ] `/subscriptions/upgrade/` — (subscriptions:upgrade_plan)
- [ ] `/subscriptions/upgrade/module/payroll/` — (subscriptions:upsell)
- [ ] `/sw.js` — (service_worker)

### ج) صفحات تحتاج مراجعة خاصة

- [ ] `/companies/charter/1/acceptance-status/` — (companies:charter_acceptance_status) — **FORBIDDEN**
- [ ] `/employees/add/` — (employee_create) — **FORBIDDEN**
- [ ] `/employees/add/` — (add_employee) — **FORBIDDEN**
- [ ] `/employees/add/` — (employees:employee_add) — **FORBIDDEN**
- [ ] `/employees/add/` — (employees:add_employee) — **FORBIDDEN**
- [ ] `/employees/add/` — (employees:add) — **FORBIDDEN**
- [ ] `/employees/add/` — (employee_add) — **FORBIDDEN**
- [ ] `/employees/add/` — (employees:employee_create) — **FORBIDDEN**
- [ ] `/employees/hierarchy/` — (employees:hierarchy_manage) — **FORBIDDEN**
- [ ] `/employees/hierarchy/` — (hierarchy_manage) — **FORBIDDEN**
- [ ] `/` — (landing:home) — **REDIRECT**
- [ ] `/accounts/notifications/send/` — (accounts:send_employee_notification) — **REDIRECT**
- [ ] `/accounts/profile/update/` — (accounts:profile_update) — **REDIRECT**
- [ ] `/companies/approval-flows/` — (companies:approval_flows) — **REDIRECT**
- [ ] `/companies/charter/accept/` — (companies:charter_accept) — **REDIRECT**
- [ ] `/companies/notification-settings/` — (companies:notification_settings) — **REDIRECT**
- [ ] `/free-trial/success/` — (landing:free_trial_success) — **REDIRECT**
- [ ] `/login/` — (login) — **REDIRECT**
- [ ] `/subscriptions/` — (subscriptions:admin_dashboard) — **REDIRECT**
- [ ] `/subscriptions/plans/` — (subscriptions:plans_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/` — (subscriptions:subscriptions_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/` — (subscriptions:detail) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/activate/` — (subscriptions:activate) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/cancel/` — (subscriptions:cancel) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/extend/` — (subscriptions:extend) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/upgrade/` — (subscriptions:upgrade) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/create/` — (subscriptions:create) — **REDIRECT**
- [ ] `/companies/branches/1/delete/` — (companies:branch_delete) — **SKIPPED**
- [ ] `/companies/delegations/1/deactivate/` — (companies:delegation_deactivate) — **SKIPPED**
- [ ] `/companies/departments/1/delete/` — (companies:department_delete) — **SKIPPED**
- [ ] `/companies/shifts/1/delete/` — (companies:shift_delete) — **SKIPPED**
- [ ] `/logout/` — (logout) — **SKIPPED**

### د) سيناريوهات مهمة لهذا الدور

- [ ] مراجعة فريقه فقط
- [ ] الموافقة على الطلبات
- [ ] مراجعة الحضور الخاص بفريقه
- [ ] متابعة الموظفين الميدانيين إن وُجد

## اختبار Role: employee

### أ) فحص عام
- [ ] تسجيل الدخول
- [ ] فتح Dashboard
- [ ] فتح البروفايل
- [ ] فتح تغيير كلمة المرور (إن وجدت)
- [ ] تسجيل الخروج

### ب) الصفحات التي فتحت آليًا بنجاح

- [ ] `/about/` — (landing:about)
- [ ] `/accounts/notifications/` — (accounts:notifications)
- [ ] `/accounts/profile/` — (accounts:profile)
- [ ] `/attendance/api/live-locations/` — (attendance:api_live_locations)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor_data)
- [ ] `/attendance/api/monitor/` — (attendance:api_monitor)
- [ ] `/attendance/api/stealth-location/` — (attendance:api_stealth_location)
- [ ] `/attendance/check-in/` — (attendance:check_in_old)
- [ ] `/attendance/check-in/` — (attendance:check_in)
- [ ] `/attendance/check-in/` — (attendance:check_in_page_old)
- [ ] `/attendance/stealth-manage/` — (attendance:stealth_manage)
- [ ] `/companies/branches/` — (companies:branches_list)
- [ ] `/companies/branches/add/` — (companies:branch_add)
- [ ] `/companies/charter/` — (companies:charter)
- [ ] `/companies/charter/manage/` — (companies:charter_manage)
- [ ] `/companies/delegations/` — (companies:delegations)
- [ ] `/companies/delegations/add/` — (companies:delegation_add)
- [ ] `/companies/departments/add/` — (companies:department_add)
- [ ] `/companies/shifts/` — (companies:shifts_list)
- [ ] `/companies/shifts/add/` — (companies:shift_add)
- [ ] `/contact/` — (landing:contact)
- [ ] `/dashboard/` — (dashboard)
- [ ] `/free-trial/` — (landing:free_trial)
- [ ] `/leaves/` — (leaves:leave_requests_list)
- [ ] `/leaves/add/` — (leaves:leave_request_add)
- [ ] `/leaves/balances/` — (leaves:leave_balances)
- [ ] `/leaves/types/` — (leaves:leave_types_list)
- [ ] `/leaves/types/add/` — (leaves:leave_type_add)
- [ ] `/manifest.json` — (manifest)
- [ ] `/offline/` — (offline)
- [ ] `/password-change/` — (password_change)
- [ ] `/password-change/done/` — (password_change_done)
- [ ] `/password-reset-complete/` — (password_reset_complete)
- [ ] `/password-reset/` — (password_reset)
- [ ] `/password-reset/done/` — (password_reset_done)
- [ ] `/pricing/` — (landing:pricing)
- [ ] `/reports/` — (reports:home)
- [ ] `/reports/field/` — (reports:field)
- [ ] `/requests/` — (requests_app:list)
- [ ] `/requests/add/` — (requests_app:add)
- [ ] `/search/` — (global_search)
- [ ] `/subscriptions/contact-sales/` — (subscriptions:contact_sales)
- [ ] `/subscriptions/feature-locked/` — (subscriptions:feature_locked)
- [ ] `/subscriptions/my-plan/` — (subscriptions:my_plan)
- [ ] `/subscriptions/my-subscription/` — (subscriptions:my_subscription)
- [ ] `/subscriptions/upgrade/` — (subscriptions:upgrade_plan)
- [ ] `/subscriptions/upgrade/module/payroll/` — (subscriptions:upsell)
- [ ] `/sw.js` — (service_worker)

### ج) صفحات تحتاج مراجعة خاصة

- [ ] `/companies/charter/1/acceptance-status/` — (companies:charter_acceptance_status) — **FORBIDDEN**
- [ ] `/companies/departments/` — (companies:departments_list) — **FORBIDDEN**
- [ ] `/` — (landing:home) — **REDIRECT**
- [ ] `/accounts/login-settings/` — (accounts:login_settings) — **REDIRECT**
- [ ] `/accounts/notifications/send/` — (accounts:send_employee_notification) — **REDIRECT**
- [ ] `/accounts/profile/update/` — (accounts:profile_update) — **REDIRECT**
- [ ] `/attendance/` — (attendance:list) — **REDIRECT**
- [ ] `/attendance/` — (attendance:attendance_list) — **REDIRECT**
- [ ] `/attendance/late-notifications/` — (attendance:late_notifications) — **REDIRECT**
- [ ] `/attendance/map/` — (attendance:live_map) — **REDIRECT**
- [ ] `/attendance/monitor/` — (attendance:field_employees_monitor) — **REDIRECT**
- [ ] `/attendance/monitor/` — (attendance:monitor) — **REDIRECT**
- [ ] `/attendance/my-warnings/` — (attendance:my_warnings) — **REDIRECT**
- [ ] `/attendance/schedule/` — (attendance:schedule_week) — **REDIRECT**
- [ ] `/attendance/schedule/assignment/` — (attendance:assignment_add) — **REDIRECT**
- [ ] `/attendance/stealth-alerts/` — (attendance:stealth_alerts) — **REDIRECT**
- [ ] `/attendance/tracking/` — (attendance:tracking_page) — **REDIRECT**
- [ ] `/attendance/tracking/` — (attendance:tracking) — **REDIRECT**
- [ ] `/attendance/visits/` — (attendance:visits) — **REDIRECT**
- [ ] `/attendance/visits/` — (attendance:visits_list) — **REDIRECT**
- [ ] `/attendance/visits/add/` — (attendance:visit_add) — **REDIRECT**
- [ ] `/companies/approval-flows/` — (companies:approval_flows) — **REDIRECT**
- [ ] `/companies/charter/1/sign/` — (companies:charter_sign) — **REDIRECT**
- [ ] `/companies/charter/accept/` — (companies:charter_accept) — **REDIRECT**
- [ ] `/companies/notification-settings/` — (companies:notification_settings) — **REDIRECT**
- [ ] `/companies/policies/` — (companies:policies) — **REDIRECT**
- [ ] `/companies/settings/` — (companies:settings) — **REDIRECT**
- [ ] `/employees/` — (employees:employee_list) — **REDIRECT**
- [ ] `/employees/` — (employees:list) — **REDIRECT**
- [ ] `/employees/` — (employee_list) — **REDIRECT**
- [ ] `/employees/add/` — (employees:add_employee) — **REDIRECT**
- [ ] `/employees/add/` — (employees:employee_create) — **REDIRECT**
- [ ] `/employees/add/` — (employee_create) — **REDIRECT**
- [ ] `/employees/add/` — (employees:add) — **REDIRECT**
- [ ] `/employees/add/` — (employee_add) — **REDIRECT**
- [ ] `/employees/add/` — (add_employee) — **REDIRECT**
- [ ] `/employees/add/` — (employees:employee_add) — **REDIRECT**
- [ ] `/employees/api/manager-options/` — (employees:manager_options_api) — **REDIRECT**
- [ ] `/employees/api/manager-options/` — (manager_options_api) — **REDIRECT**
- [ ] `/employees/api/search/` — (employees:employee_search_api) — **REDIRECT**
- [ ] `/employees/api/search/` — (employee_search_api) — **REDIRECT**
- [ ] `/employees/api/search/` — (employees:search_api) — **REDIRECT**
- [ ] `/employees/hierarchy/` — (hierarchy_manage) — **REDIRECT**
- [ ] `/employees/hierarchy/` — (employees:hierarchy_manage) — **REDIRECT**
- [ ] `/employees/my-balance/` — (my_balance_view) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employee_balance) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employees:employee_balance) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employees:my_balance) — **REDIRECT**
- [ ] `/employees/my-balance/` — (employees:my_balance_view) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (my_deductions_view) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employees:employee_deductions) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employee_deductions) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employees:my_deductions) — **REDIRECT**
- [ ] `/employees/my-deductions/` — (employees:my_deductions_view) — **REDIRECT**
- [ ] `/employees/print/` — (employees_print_all) — **REDIRECT**
- [ ] `/employees/print/` — (employees:employees_print_all) — **REDIRECT**
- [ ] `/employees/print/` — (employees:employee_print) — **REDIRECT**
- [ ] `/employees/print/` — (employees:employee_print_all) — **REDIRECT**
- [ ] `/employees/print/` — (employees:employees_print) — **REDIRECT**
- [ ] `/employees/print/` — (employee_print) — **REDIRECT**
- [ ] `/employees/print/` — (employee_print_all) — **REDIRECT**
- [ ] `/employees/print/` — (employees_print) — **REDIRECT**
- [ ] `/employees/print/` — (employees:print_all) — **REDIRECT**
- [ ] `/free-trial/success/` — (landing:free_trial_success) — **REDIRECT**
- [ ] `/login/` — (login) — **REDIRECT**
- [ ] `/subscriptions/` — (subscriptions:admin_dashboard) — **REDIRECT**
- [ ] `/subscriptions/plans/` — (subscriptions:plans_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/` — (subscriptions:subscriptions_list) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/` — (subscriptions:detail) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/activate/` — (subscriptions:activate) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/cancel/` — (subscriptions:cancel) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/extend/` — (subscriptions:extend) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/1/upgrade/` — (subscriptions:upgrade) — **REDIRECT**
- [ ] `/subscriptions/subscriptions/create/` — (subscriptions:create) — **REDIRECT**
- [ ] `/companies/branches/1/delete/` — (companies:branch_delete) — **SKIPPED**
- [ ] `/companies/delegations/1/deactivate/` — (companies:delegation_deactivate) — **SKIPPED**
- [ ] `/companies/departments/1/delete/` — (companies:department_delete) — **SKIPPED**
- [ ] `/companies/shifts/1/delete/` — (companies:shift_delete) — **SKIPPED**
- [ ] `/logout/` — (logout) — **SKIPPED**

### د) سيناريوهات مهمة لهذا الدور

- [ ] تسجيل حضور/انصراف
- [ ] تقديم طلب جديد
- [ ] تقديم طلب إجازة
- [ ] رؤية رصيد الإجازات
- [ ] مراجعة إشعاراته

## اختبار Role: field_employee

- لا يوجد مستخدم متاح لهذا الدور حاليًا.

## 3) سيناريوهات شاملة مشتركة

- [ ] Landing page تعمل
- [ ] Pricing page تعمل
- [ ] Free Trial page تعمل
- [ ] التسجيل في Free Trial يعمل
- [ ] صفحة success بعد التجربة تعمل
- [ ] الدخول ببيانات التجربة يعمل
- [ ] لا توجد صفحات 500 أثناء السيناريو الرئيسي
- [ ] التصدير Excel يعمل
- [ ] التصدير PDF يعمل
- [ ] الطباعة تعمل
