import requests

BASE = "https://jssolutions-eg.com"
PASSWORD = "Test@1234"

USERS = [
    ("re_admin", "manager", "عقاري - مدير"),
    ("re_hr", "manager", "عقاري - HR"),
    ("re_sales_1", "employee", "عقاري - موظف ميداني حر"),
    ("re_sales_2", "employee", "عقاري - موظف ميداني محدد"),
    ("con_admin", "manager", "مقاولات - مدير"),
    ("con_worker_1", "employee", "مقاولات - عامل شيفت ليلي"),
    ("ph_admin", "manager", "أدوية - مدير"),
    ("ph_rep_1", "employee", "أدوية - مندوب طبي"),
    ("wh_admin", "manager", "مخازن - مدير"),
    ("wh_dispatch", "employee", "مخازن - مندوب توزيع"),
]

MANAGER_ENDPOINTS = [
    ("لوحة التحكم", "/attendance/api/mobile/manager/dashboard/"),
    ("الموظفين", "/attendance/api/mobile/manager/employees/"),
    ("الطلبات المعلقة", "/attendance/api/mobile/manager/pending/"),
    ("الحضور اليوم", "/attendance/api/mobile/manager/attendance/"),
    ("المواقع المباشرة", "/attendance/api/mobile/manager/live-locations/"),
    ("الشيفتات", "/attendance/api/mobile/manager/shifts/"),
    ("مواقع العمل", "/attendance/api/mobile/manager/work-locations/"),
    ("الإعلانات", "/attendance/api/mobile/announcements/list/"),
    ("الإشعارات", "/attendance/api/mobile/notifications/"),
    ("أنواع الطلبات", "/attendance/api/mobile/request-types/"),
    ("سياسة العمل", "/attendance/api/mobile/manager/work-policy/"),
    ("ملخص موظف", "/attendance/api/mobile/manager/employees/{employee_id}/summary/"),
    ("تقرير غياب", "/attendance/api/mobile/manager/reports/absence/"),
    ("تقرير حضور", "/attendance/api/mobile/manager/reports/attendance/"),
]

EMPLOYEE_ENDPOINTS = [
    ("الرئيسية / الحالة", "/attendance/api/mobile/status/"),
    ("ملفي الشخصي", "/attendance/api/mobile/employee/profile/"),
    ("ملخصي", "/attendance/api/mobile/employee/summary/"),
    ("مستنداتي", "/attendance/api/mobile/employee/documents/"),
    ("شيفتي", "/attendance/api/mobile/employee/my-shift/"),
    ("حركاتي", "/attendance/api/mobile/employee/movements/"),
    ("الإشعارات", "/attendance/api/mobile/notifications/"),
    ("الإعلانات", "/attendance/api/mobile/announcements/list/"),
    ("أنواع الطلبات", "/attendance/api/mobile/request-types/"),
    ("طلباتي", "/attendance/api/mobile/my-requests/"),
    ("إجازاتي", "/attendance/api/mobile/my-leaves/"),
    ("رصيد الأذونات", "/attendance/api/mobile/employee/permission-balance/"),
    ("راتبي", "/attendance/api/mobile/employee/payslip/"),
    ("حضور تلقائي حالة", "/attendance/api/mobile/employee/auto-checkin-status/"),
]

def login(username):
    try:
        r = requests.post(
            f"{BASE}/attendance/api/mobile/login/",
            json={"username": username, "password": PASSWORD},
            timeout=20,
        )
        data = r.json()
        if r.status_code == 200 and data.get("success") and data.get("token"):
            return data["token"]
    except Exception:
        pass
    return None

def get_first_employee_id(token):
    try:
        r = requests.get(
            f"{BASE}/attendance/api/mobile/manager/employees/",
            headers={"Authorization": f"Token {token}"},
            timeout=20,
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("employees") or []
            if items:
                return items[0].get("id")
    except Exception:
        pass
    return None

def check(token, path):
    try:
        if "{employee_id}" in path:
            emp_id = get_first_employee_id(token)
            if not emp_id:
                return False, "NO_EMP"
            path = path.replace("{employee_id}", str(emp_id))

        r = requests.get(
            f"{BASE}{path}",
            headers={"Authorization": f"Token {token}"},
            timeout=20,
        )
        return r.status_code == 200, r.status_code
    except Exception:
        return False, "EXC"

total = 0
passed = 0
failed = []

print("=" * 70)
print("MOTIONHR — FULL API HEALTH CHECK V2")
print("=" * 70)

for username, role, label in USERS:
    print(f"\n{'─'*70}")
    print(f"USER: {username} | {label}")
    token = login(username)
    total += 1
    if not token:
        print("  ❌ LOGIN FAILED")
        failed.append((label, "LOGIN", "FAIL"))
        continue

    print("  ✅ LOGIN OK")
    passed += 1
    endpoints = MANAGER_ENDPOINTS if role == "manager" else EMPLOYEE_ENDPOINTS

    for name, path in endpoints:
        total += 1
        ok, code = check(token, path)
        if ok:
            passed += 1
            print(f"  ✅ {name:30s} [{code}]")
        else:
            print(f"  ❌ {name:30s} [{code}]")
            failed.append((label, name, code))

print(f"\n{'='*70}")
print(f"TOTAL: {total} | PASS: {passed} | FAIL: {len(failed)}")
print(f"{'='*70}")

if failed:
    print("\nFAILED ITEMS:")
    for item in failed:
        print(f"  ❌ {item[0]} → {item[1]} [{item[2]}]")
else:
    print("\n✅ ALL CHECKS PASSED — النظام سليم للبيع")
