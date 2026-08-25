import json
import requests

BASE = "https://jssolutions-eg.com"
PASSWORD = "Test@1234"

SCENARIOS = [
    ("re_admin", "manager", "realestate"),
    ("re_sales_1", "employee", "realestate"),
    ("con_admin", "manager", "contracting"),
    ("con_worker_1", "employee", "contracting"),
    ("ph_admin", "manager", "pharma"),
    ("ph_rep_1", "employee", "pharma"),
    ("wh_admin", "manager", "warehouse"),
    ("wh_dispatch", "employee", "warehouse"),
]

MANAGER_ENDPOINTS = [
    "/attendance/api/mobile/manager/pending/",
    "/attendance/api/mobile/manager/attendance/",
    "/attendance/api/mobile/manager/live-locations/",
    "/attendance/api/mobile/manager/employees/",
    "/attendance/api/mobile/notifications/",
    "/attendance/api/mobile/announcements/list/",
    "/attendance/api/mobile/request-types/",
]

EMPLOYEE_ENDPOINTS = [
    "/attendance/api/mobile/status/",
    "/attendance/api/mobile/employee/profile/",
    "/attendance/api/mobile/employee/summary/",
    "/attendance/api/mobile/employee/documents/",
    "/attendance/api/mobile/employee/my-shift/",
    "/attendance/api/mobile/notifications/",
    "/attendance/api/mobile/announcements/list/",
    "/attendance/api/mobile/request-types/",
]

def login(username):
    r = requests.post(
        f"{BASE}/attendance/api/mobile/login/",
        json={"username": username, "password": PASSWORD},
        timeout=20,
    )
    ok = False
    token = None
    body = None
    try:
        body = r.json()
        ok = r.status_code == 200 and body.get("success") is True
        token = body.get("token")
    except Exception:
        body = {"raw": r.text[:300]}
    return ok, token, r.status_code, body

def check_endpoint(token, path):
    headers = {"Authorization": f"Token {token}"}
    try:
        r = requests.get(f"{BASE}{path}", headers=headers, timeout=20)
        ctype = r.headers.get("Content-Type", "")
        if r.status_code == 200:
            return True, r.status_code, ctype
        return False, r.status_code, ctype
    except Exception as e:
        return False, "EXC", str(e)

total = 0
passed = 0
failed = []

print("=" * 80)
print("MOTIONHR API HEALTH CHECK")
print("=" * 80)

for username, role, scenario in SCENARIOS:
    print(f"\n### USER: {username} | ROLE: {role} | SCENARIO: {scenario}")
    ok, token, status_code, body = login(username)
    total += 1
    if ok and token:
        passed += 1
        print(f"LOGIN: PASS ({status_code})")
    else:
        failed.append((username, "LOGIN", status_code))
        print(f"LOGIN: FAIL ({status_code}) -> {str(body)[:250]}")
        continue

    endpoints = MANAGER_ENDPOINTS if role == "manager" else EMPLOYEE_ENDPOINTS
    for path in endpoints:
        total += 1
        ok2, sc, extra = check_endpoint(token, path)
        if ok2:
            passed += 1
            print(f"PASS  {path}  [{sc}]")
        else:
            failed.append((username, path, sc))
            print(f"FAIL  {path}  [{sc}]  => {extra}")

print("\n" + "=" * 80)
print(f"TOTAL CHECKS: {total}")
print(f"PASSED: {passed}")
print(f"FAILED: {len(failed)}")
print("=" * 80)

if failed:
    print("FAILED ITEMS:")
    for item in failed:
        print(" -", item)
else:
    print("ALL CHECKS PASSED ✅")
