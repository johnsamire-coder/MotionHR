import pathlib, re

BASE = pathlib.Path('.')

print("=== 1. Checking LeaveType in leaves/models.py ===")
lt_content = (BASE / 'leaves/models.py').read_text(encoding='utf-8')
print("require_reason exists:", "require_reason" in lt_content)
print("is_excused_absence exists:", "is_excused_absence" in lt_content)

print("\n=== 2. Checking Leave Request endpoint in attendance/api_mobile_requests.py ===")
req_file = BASE / 'attendance/api_mobile_requests.py'
if req_file.exists():
    content = req_file.read_text(encoding='utf-8')
    match = re.search(r'def mobile_leave_request\(.*?\):.*?(?=\ndef |\Z)', content, re.DOTALL)
    if match:
        lines = match.group(0).splitlines()[:40]
        print("Found mobile_leave_request (first 40 lines):")
        print("\n".join(lines))
    else:
        print("mobile_leave_request not found by regex")
else:
    print("attendance/api_mobile_requests.py NOT FOUND")
