"""
اختبارات سجل التعديلات
  python manage.py test audit --settings=motionhr.settings_test
"""
from decimal import Decimal
from unittest import mock

from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient

from attendance.test_action_scope import ScopeBase
from audit.models import AuditLog

M = '/attendance/api/mobile/'


class AuditCaptureTests(ScopeBase):
    def edit_employee(self, who, emp, **changes):
        from attendance.api_employee_profile import _serialize_employee_full
        from employees.models import Employee
        e = Employee._base_manager.get(pk=emp.pk)
        p = _serialize_employee_full(e)
        body = {
            'first_name_ar': p['first_name_ar'], 'last_name_ar': 'أحمد', 'first_name_en': 'Emp', 'last_name_en': 'Test',
            'phone': e.phone, 'national_id': e.national_id, 'birth_date': '1990-01-01', 'hire_date': '2020-01-01',
            'branch_id': e.branch_id, 'department_id': e.department_id, 'job_title_id': e.job_title_id,
            'basic_salary': str(e.basic_salary), 'gender': 'male', 'contract_type': 'permanent',
        }
        body.update(changes)
        return self.api(who).put(f'{M}manager/employees/{e.id}/update/', body, format='json')

    def test_salary_change_logged_with_before_after_and_user(self):
        r = self.edit_employee(self.hr_a, self.team_a, basic_salary='6500')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        log = AuditLog.objects.filter(model='employees.Employee', employee_id=self.team_a.id, action='update').first()
        self.assertIsNotNone(log)
        sal = [c for c in log.changes if c['field'] == 'basic_salary']
        self.assertEqual((sal[0]['old'], sal[0]['new']), ('5000', '6500'))
        self.assertEqual(log.username, self.hr_a.user.username)
        self.assertEqual(log.company_id, self.a.id)
        self.assertEqual(log.source, 'web')

    def test_name_and_phone_change_logged(self):
        self.edit_employee(self.hr_a, self.team_a, first_name_ar='محمود', phone='01099998888')
        log = AuditLog.objects.filter(model='employees.Employee', employee_id=self.team_a.id, action='update').first()
        fields = {c['field']: c for c in log.changes}
        self.assertEqual(fields['first_name_ar']['new'], 'محمود')
        self.assertEqual(fields['phone']['new'], '01099998888')

    def test_leave_approval_logged(self):
        lv = self.leave(self.team_a)
        self.act(self.mgr_a, 'leave', lv)
        log = AuditLog.objects.filter(model='leaves.LeaveRequest', object_id=str(lv.id)).order_by('-id').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.username, self.mgr_a.user.username)
        self.assertIn('الحالة', [c['label'] for c in log.changes])
        self.assertEqual(log.employee_id, self.team_a.id)

    def test_request_decision_logged(self):
        rq = self.req(self.other_a)
        self.act(self.hr_a, 'request', rq)
        logs = AuditLog.objects.filter(model='requests_app.EmployeeRequest', object_id=str(rq.id))
        self.assertTrue(any(c.get('field') == 'status' for l in logs for c in l.changes))

    def test_login_logged(self):
        self.other_a.user.set_password('Pass12345')
        self.other_a.user.save()
        APIClient().post(f'{M}login/', {'username': self.other_a.user.username, 'password': 'Pass12345'}, format='json')
        self.assertTrue(AuditLog.objects.filter(action='login', user_id=self.other_a.user_id).exists())

    def test_password_value_never_stored(self):
        self.other_a.user.set_password('NewSecret999')
        self.other_a.user.save()
        log = AuditLog.objects.filter(model='accounts.User', object_id=str(self.other_a.user_id), action='update').first()
        pw = [c for c in log.changes if c['field'] == 'password'][0]
        self.assertEqual((pw['old'], pw['new']), ('***', 'اتغيرت'))
        self.assertNotIn('NewSecret999', str(log.changes))

    def test_audit_failure_never_breaks_saving(self):
        from employees.models import Employee
        with mock.patch.object(AuditLog.objects, 'create', side_effect=Exception('table missing')):
            with transaction.atomic():
                e = Employee._base_manager.get(pk=self.team_a.pk)
                e.basic_salary = Decimal('7000')
                e.save()
        self.assertEqual(Employee._base_manager.get(pk=self.team_a.pk).basic_salary, Decimal('7000'))


class AuditReportTests(ScopeBase):
    def setUp(self):
        super().setUp()
        from employees.models import Employee, EmployeeMovement
        e = Employee._base_manager.get(pk=self.team_a.pk)
        e.phone = '01011112222'
        e.save()
        b = Employee._base_manager.get(pk=self.emp_b.pk)
        b.phone = '01033334444'
        b.save()
        EmployeeMovement._base_manager.create(company=self.a, employee=self.team_a, movement_type='salary_change',
                                              movement_date=timezone.localdate(), old_value='4000', new_value='5000',
                                              reason='تعديل من قبل')

    def test_owner_sees_company_log_only(self):
        r = self.api(self.owner_a).get('/audit/api/logs/')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        emps = {l['employee_id'] for l in r.data['logs']}
        self.assertIn(self.team_a.id, emps)
        self.assertNotIn(self.emp_b.id, emps)

    def test_hr_and_manager_cannot_see_whole_log(self):
        self.assertEqual(self.api(self.hr_a).get('/audit/api/logs/').status_code, 403)
        self.assertEqual(self.api(self.mgr_a).get('/audit/api/logs/').status_code, 403)

    def test_employee_history_has_new_and_legacy(self):
        r = self.api(self.hr_a).get(f'/audit/api/employee/{self.team_a.id}/')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        labels = [c['label'] for h in r.data['history'] for c in h['changes']]
        self.assertTrue(any('موبايل' in l or 'phone' in l.lower() or 'هاتف' in l for l in labels), labels)
        self.assertTrue(any(h.get('legacy') for h in r.data['history']))
        self.assertEqual(self.api(self.hr_a).get(f'/audit/api/employee/{self.emp_b.id}/').status_code, 404)

    def test_excel_exports(self):
        r = self.api(self.owner_a).get('/audit/api/logs/?export=xlsx')
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheet', r['Content-Type'])
        r = self.api(self.hr_a).get(f'/audit/api/employee/{self.team_a.id}/?export=xlsx')
        self.assertEqual(r.status_code, 200)
