import os, django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from companies.models import Company, Branch, Department
from employees.models import Employee, JobTitle
from accounts.models import User
from attendance.models import Attendance
from attendance.api_attendance_adjustment import manager_adjust_attendance
from rest_framework.test import APIRequestFactory, force_authenticate

factory = APIRequestFactory()

# 1. تجهيز بيئة الاختبار
company = Company._base_manager.first()
if not company:
    company = Company._base_manager.create(name_ar="شركة تجريبية", is_active=True)

branch, _ = Branch._base_manager.get_or_create(
    company=company,
    name_ar="الفرع الرئيسي",
    defaults={"is_active": True}
)

dept, _ = Department._base_manager.get_or_create(
    company=company,
    branch=branch,
    name_ar="قسم الموارد البشرية",
    defaults={"is_active": True}
)

job_title, _ = JobTitle._base_manager.get_or_create(
    company=company,
    department=dept,
    name_ar="أخصائي HR",
    defaults={"is_active": True}
)

hr_user, _ = User._base_manager.get_or_create(
    username="hr_tester",
    defaults={"role": "hr_manager", "company": company, "email": "hr@test.com"}
)
hr_user.role = "hr_manager"
hr_user.company = company
hr_user.save()

emp_user, _ = User._base_manager.get_or_create(
    username="emp_tester",
    defaults={"role": "employee", "company": company, "email": "emp@test.com"}
)
emp_user.role = "employee"
emp_user.company = company
emp_user.save()

employee, _ = Employee._base_manager.get_or_create(
    company=company,
    employee_code="EMP_TEST_01",
    defaults={
        "first_name_ar": "أحمد",
        "last_name_ar": "علي",
        "branch": branch,
        "department": dept,
        "job_title": job_title,
        "birth_date": date(1995, 5, 15),
        "hire_date": date(2023, 1, 1),
        "basic_salary": Decimal('8000.00'),
        "status": "active",
        "user": emp_user
    }
)

# 2. إنشاء سجل حضور وهمي
test_date = date(2026, 8, 20)
attendance, _ = Attendance._base_manager.get_or_create(
    company=company,
    employee=employee,
    date=test_date,
    defaults={
        "status": "absent",
        "check_in_time": None,
        "check_out_time": None,
        "work_hours": Decimal('0.00')
    }
)
attendance.status = "absent"
attendance.check_in_time = None
attendance.check_out_time = None
attendance.work_hours = Decimal('0.00')
attendance.save()

print(f"Initial Attendance ID {attendance.id}: Status={attendance.status}, Hours={attendance.work_hours}")

# TEST 1: محاولة التعديل من موظف عادي (يجب أن يُرفض 403)
req = factory.post(f'/attendance/api/mobile/manager/attendance/{attendance.id}/adjust/', {
    'check_in_time': '09:00',
    'check_out_time': '17:00',
    'reason': 'تعديل بواسطة موظف'
}, format='json')
force_authenticate(req, user=emp_user)
res1 = manager_adjust_attendance(req, attendance_id=attendance.id)
print(f"\nTEST 1 (Unauthorized User): Status={res1.status_code} -> {res1.data.get('message')}")
assert res1.status_code == 403, "Should return 403 Forbidden"
print("[PASS] Unauthorized access blocked successfully.")

# TEST 2: محاولة التعديل من HR ولكن بدون كتابة سبب (يجب أن يُرفض 400)
req = factory.post(f'/attendance/api/mobile/manager/attendance/{attendance.id}/adjust/', {
    'check_in_time': '09:00',
    'check_out_time': '17:00',
    'reason': ''
}, format='json')
force_authenticate(req, user=hr_user)
res2 = manager_adjust_attendance(req, attendance_id=attendance.id)
print(f"\nTEST 2 (Empty Reason): Status={res2.status_code} -> {res2.data.get('message')}")
assert res2.status_code == 400, "Should return 400 Bad Request"
print("[PASS] Mandatory reason validation enforced successfully.")

# TEST 3: تعديل صحيح بواسطة HR (من 09:00 إلى 17:30 = 8.5 ساعات عمل)
req = factory.post(f'/attendance/api/mobile/manager/attendance/{attendance.id}/adjust/', {
    'check_in_time': '09:00',
    'check_out_time': '17:30',
    'status': 'present',
    'reason': 'تم التأكد من سجل البصمة اليدوية وتعديل الحضور'
}, format='json')
force_authenticate(req, user=hr_user)
res3 = manager_adjust_attendance(req, attendance_id=attendance.id)
print(f"\nTEST 3 (Valid HR Adjustment): Status={res3.status_code} -> {res3.data.get('message')}")
assert res3.status_code == 200, "Should return 200 OK"
assert res3.data['attendance']['work_hours'] == 8.5, f"Expected 8.5 hours, got {res3.data['attendance']['work_hours']}"
assert res3.data['attendance']['status'] == 'present', "Status should be present"
print(f"[PASS] Adjusted Hours: {res3.data['attendance']['work_hours']} hrs | Status: {res3.data['attendance']['status']}")

print("\n" + "="*50)
print(">>> STEP 2 COMPLETED & TESTED 100% <<<")
print("="*50)
