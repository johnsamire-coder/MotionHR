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
