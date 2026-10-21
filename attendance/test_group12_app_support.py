"""
اختبارات دفعة 12 (السيرفر مع إصدار التطبيق 1.5):
171 تعديل بيانات الموظف من الموبايل، 183 الإجازة الرسمية لفرع أو إدارة

التشغيل:
  python manage.py test attendance.test_group12_app_support --settings=motionhr.settings_test
"""
from datetime import date

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/'


class EmployeeEditFromAppTests(ScopeBase):
    def test_profile_returns_fields_edit_screen_needs(self):
        from attendance.api_employee_profile import _serialize_employee_full
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(has_insurance=True, salary_payment_method='bank')
        e = Employee._base_manager.get(pk=self.team_a.pk)
        d = _serialize_employee_full(e)
        self.assertEqual((d['has_insurance'], d['salary_payment_method']), (True, 'bank'))
        self.assertEqual(d['first_name_en'], 'E')
        self.assertEqual(d['branch_id'], e.branch_id)

    def test_arabic_labels_saved_as_codes_and_insurance_kept(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.team_a.pk).update(
            has_insurance=True, salary_payment_method='bank', gender='female',
            marital_status='married', contract_type='training', first_name_en='Mona', last_name_en='Ali', last_name_ar='أحمد')
        e = Employee._base_manager.get(pk=self.team_a.pk)
        from attendance.api_employee_profile import _serialize_employee_full
        p = _serialize_employee_full(e)
        # نفس اللي شاشة الموبايل بتبعته: القيم زي ما رجعت من الملف (النوع بالعربي)
        body = {
            'first_name_ar': p['first_name_ar'], 'last_name_ar': p['last_name_ar'],
            'first_name_en': p['first_name_en'], 'last_name_en': p['last_name_en'],
            'phone': e.phone, 'national_id': e.national_id, 'birth_date': '1990-01-01', 'hire_date': '2020-01-01',
            'gender': p['gender'], 'marital_status': p['marital_status'], 'contract_type': p['contract_type'],
            'branch_id': p['branch_id'], 'department_id': p['department_id'], 'job_title_id': p['job_title_id'],
            'basic_salary': '5000', 'salary_payment_method': p['salary_payment_method'],
            'has_insurance': p['has_insurance'], 'worker_type': p['worker_type'],
        }
        self.assertEqual(p['gender'], 'أنثى')
        r = self.api(self.hr_a).put(f'{M}manager/employees/{e.id}/update/', body, format='json')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        e.refresh_from_db()
        self.assertEqual((e.gender, e.marital_status, e.contract_type), ('female', 'married', 'training'))
        self.assertEqual((e.has_insurance, e.salary_payment_method), (True, 'bank'))


class OfficialHolidayScopeTests(ScopeBase):
    def post(self, rules):
        return self.api(self.hr_a).post(f'{M}manager/official-holidays/', {
            'name': 'عيد', 'start_date': '2026-11-05', 'end_date': '2026-11-05', 'rules': rules,
            'send_notification': False,
        }, format='json')

    def test_branch_rule_without_branch_refused(self):
        from leaves.official_holiday_models import OfficialHoliday
        r = self.post([{'scope': 'branch', 'treatment': 'paid_leave'}])
        self.assertEqual(r.status_code, 400, getattr(r, 'data', None))
        self.assertFalse(OfficialHoliday._base_manager.filter(company=self.a, name='عيد').exists())

    def test_branch_rule_applies_to_branch(self):
        from leaves.official_holiday_models import OfficialHolidayRule
        r = self.post([{'scope': 'branch', 'branch_id': self.team_a.branch_id, 'treatment': 'paid_leave'}])
        self.assertIn(r.status_code, (200, 201), getattr(r, 'data', None))
        rule = OfficialHolidayRule._base_manager.get(holiday__name='عيد')
        self.assertEqual(rule.branch_id, self.team_a.branch_id)

    def test_employee_ids_returned_for_edit(self):
        r = self.post([{'scope': 'employees', 'employee_ids': [self.team_a.id], 'treatment': 'paid_leave'}])
        self.assertIn(r.status_code, (200, 201), getattr(r, 'data', None))
        from leaves.api_official_holidays import _rule_data
        from leaves.official_holiday_models import OfficialHolidayRule
        rule = OfficialHolidayRule._base_manager.get(holiday__name='عيد')
        self.assertEqual(_rule_data(rule)['employee_ids'], [self.team_a.id])
