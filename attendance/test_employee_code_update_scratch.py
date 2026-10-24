from django.test import TestCase
from django.urls import reverse
from datetime import date
from companies.models import Company, Branch, Department
from employees.models import Employee, JobTitle
from accounts.models import User
from rest_framework.authtoken.models import Token


class EmployeeCodeUpdateTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name_ar="شركة اختبار")
        self.user = User.objects.create_superuser(
            username="root_test", password="pass12345", email="root@test.local"
        )
        self.token = Token.objects.create(user=self.user)
        self.branch = Branch.objects.create(company=self.company, name_ar="فرع اختبار")
        self.department = Department.objects.create(company=self.company, branch=self.branch, name_ar="إدارة اختبار")
        self.job_title = JobTitle.objects.create(company=self.company, name_ar="موظف اختبار")
        self.emp = Employee.objects.create(
            company=self.company, first_name_ar="سامح", last_name_ar="محمود", first_name_en="Sameh", last_name_en="Mahmoud",
            phone="01000000001", national_id="29001011234567",
            birth_date=date(1990, 1, 1), hire_date=date(2024, 1, 1), branch=self.branch,
            department=self.department, job_title=self.job_title,
        )
        self.other = Employee.objects.create(
            company=self.company, first_name_ar="أحمد", last_name_ar="علي", first_name_en="Ahmed", last_name_en="Ali",
            phone="01000000002", national_id="29001019876543",
            birth_date=date(1991, 2, 2), hire_date=date(2024, 1, 1), branch=self.branch,
            department=self.department, job_title=self.job_title,
        )

    def _url(self, emp):
        return f"/attendance/api/mobile/manager/employees/{emp.id}/update/"

    def _put(self, emp, payload):
        return self.client.put(
            self._url(emp),
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

    def test_valid_manual_code_is_saved(self):
        resp = self._put(self.emp, {"employee_code": "M-100"})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.employee_code, "M-100")

    def test_duplicate_code_is_rejected(self):
        resp = self._put(self.emp, {"employee_code": self.other.employee_code})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("الرقم الوظيفي", resp.json()["error"])
        self.emp.refresh_from_db()
        self.assertNotEqual(self.emp.employee_code, self.other.employee_code)

    def test_overlong_code_is_rejected(self):
        resp = self._put(self.emp, {"employee_code": "X" * 21})
        self.assertEqual(resp.status_code, 400)
        self.emp.refresh_from_db()
        self.assertNotEqual(self.emp.employee_code, "X" * 21)

    def test_empty_code_keeps_existing(self):
        old = self.emp.employee_code
        resp = self._put(self.emp, {"employee_code": ""})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.employee_code, old)
