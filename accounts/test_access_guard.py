"""
اختبارات مجموعة 1: الحساب الموقوف، إيقاف الشركة، تفعيل الحساب، والموقع القديم.

التشغيل:
  python manage.py test accounts.test_access_guard --settings=motionhr.settings_test
"""
from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from accounts.access import COMPANY_SUSPENDED_MSG, ACCOUNT_DISABLED_MSG
from accounts.activation import ALREADY_ACTIVE_MSG, LOCKED_MSG
from companies.models import Branch, Company, Department
from core.middleware import OLD_SITE_CLOSED_MSG
from employees.models import Employee, JobTitle

User = get_user_model()

LOGIN = '/attendance/api/mobile/login/'
JWT_TOKEN = '/attendance/api/mobile/jwt/token/'
JWT_REFRESH = '/attendance/api/mobile/jwt/refresh/'
SOME_API = '/attendance/api/mobile/status/'
ACTIVATE_APP = '/accounts/api/mobile/activate-account/'
ACTIVATE_WEB = '/attendance/api/mobile/activate-account/'


class AccessBase(TestCase):
    _seq = 0

    def setUp(self):
        cache.clear()
        self.company = Company.objects.create(name_ar='شركة تجريبية', name_en='Test Co')
        self.api = APIClient()

    def make_employee(self, company=None, password='pass1234', status='active', user_company=True, **user_kw):
        AccessBase._seq += 1
        n = AccessBase._seq
        company = company or self.company
        branch = Branch.objects.filter(company=company).first() or Branch.objects.create(company=company, name_ar='الرئيسي', name_en='Main')
        dept = Department.objects.filter(company=company).first() or Department.objects.create(company=company, name_ar='إدارة', name_en='Dept')
        job = JobTitle._base_manager.filter(company=company).first() or JobTitle._base_manager.create(company=company, name_ar='موظف', name_en='Staff')
        user = User.objects.create_user(
            username=f'acc{n}', password=password, role=user_kw.pop('role', 'employee'),
            company=company if user_company else None, **user_kw,
        )
        emp = Employee._base_manager.create(
            user=user, company=company, employee_code=f'A{n}',
            first_name_ar='موظف', last_name_ar=str(n), first_name_en='Emp', last_name_en=str(n),
            national_id=f'2900101{n:07d}', hire_date=date(2020, 1, 1), birth_date=date(1990, 1, 1),
            gender='male', basic_salary=Decimal('5000'), phone=f'010{n:08d}', status=status,
            branch=branch, department=dept, job_title=job,
        )
        return emp

    def login(self, username, password='pass1234'):
        return self.api.post(LOGIN, {'username': username, 'password': password}, format='json')

    def suspend(self, company=None):
        call_command('company_access', (company or self.company).pk, 'suspend', stdout=StringIO())

    def resume(self, company=None):
        call_command('company_access', (company or self.company).pk, 'resume', stdout=StringIO())


class DisabledAccountTests(AccessBase):
    """رقم 17: الحساب الموقوف مايدخلش"""

    def test_disabled_account_gets_clear_message_and_no_token(self):
        emp = self.make_employee()
        emp.user.is_active = False
        emp.user.save()
        r = self.login(emp.user.username)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['code'], 'account_disabled')
        self.assertEqual(r.json()['message'], ACCOUNT_DISABLED_MSG)
        self.assertNotIn('token', r.json())

    def test_disabled_account_wrong_password_looks_like_any_wrong_login(self):
        emp = self.make_employee()
        emp.user.is_active = False
        emp.user.save()
        r = self.login(emp.user.username, 'wrong')
        self.assertEqual(r.status_code, 401)
        self.assertNotIn('code', r.json())

    def test_active_account_logs_in(self):
        emp = self.make_employee()
        r = self.login(emp.user.username)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['token'])

    def test_session_of_disabled_account_is_dropped(self):
        from accounts.login_backend import SmartLoginBackend
        emp = self.make_employee()
        self.assertEqual(SmartLoginBackend().get_user(emp.user.pk), emp.user)
        emp.user.is_active = False
        emp.user.save()
        self.assertIsNone(SmartLoginBackend().get_user(emp.user.pk))

    def test_existing_token_of_disabled_account_gets_message(self):
        emp = self.make_employee()
        token = self.login(emp.user.username).json()['token']
        emp.user.is_active = False
        emp.user.save()
        self.api.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        r = self.api.get(SOME_API)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['code'], 'account_disabled')


class CompanySuspensionTests(AccessBase):
    """إيقاف الشركة: يمنع الدخول، مابيمسحش حاجة، والتشغيل بيرجّع كل حاجة فوراً"""

    def test_login_refused_with_clear_message_then_allowed_after_resume(self):
        emp = self.make_employee()
        self.suspend()
        r = self.login(emp.user.username)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['code'], 'company_suspended')
        self.assertEqual(r.json()['message'], COMPANY_SUSPENDED_MSG)
        self.resume()
        self.assertEqual(self.login(emp.user.username).status_code, 200)

    def test_already_logged_in_is_blocked_and_same_token_works_after_resume(self):
        emp = self.make_employee()
        token = self.login(emp.user.username).json()['token']
        self.api.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        before = self.api.get(SOME_API).status_code
        self.assertEqual(before, 200)

        self.suspend()
        r = self.api.get(SOME_API)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['message'], COMPANY_SUSPENDED_MSG)
        self.assertEqual(r.json()['detail'], COMPANY_SUSPENDED_MSG)

        self.resume()
        self.assertEqual(self.api.get(SOME_API).status_code, before)  # من غير ما يدخل تاني

    def test_jwt_bearer_is_blocked(self):
        emp = self.make_employee()
        access = self.login(emp.user.username).json()['access']
        self.suspend()
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        r = self.api.get(SOME_API)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['code'], 'company_suspended')

    def test_jwt_obtain_and_refresh_refused(self):
        emp = self.make_employee()
        refresh = self.login(emp.user.username).json()['refresh']
        self.suspend()
        r = self.api.post(JWT_TOKEN, {'username': emp.user.username, 'password': 'pass1234'}, format='json')
        self.assertEqual(r.status_code, 403)
        r = self.api.post(JWT_REFRESH, {'refresh': refresh}, format='json')
        self.assertEqual(r.status_code, 403)
        self.resume()
        r = self.api.post(JWT_REFRESH, {'refresh': refresh}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_user_without_company_on_account_uses_employee_company(self):
        emp = self.make_employee(user_company=False)
        self.suspend()
        self.assertEqual(self.login(emp.user.username).json().get('code'), 'company_suspended')

    def test_other_company_not_affected(self):
        other = Company.objects.create(name_ar='شركة تانية', name_en='Other')
        emp_other = self.make_employee(company=other)
        self.suspend()
        self.assertEqual(self.login(emp_other.user.username).status_code, 200)

    def test_super_admin_never_blocked(self):
        admin = User.objects.create_user(username='root1', password='pass1234', role='super_admin', company=self.company)
        self.suspend()
        r = self.login('root1')
        self.assertNotEqual(r.status_code, 403)
        self.api.credentials(HTTP_AUTHORIZATION=f'Token {r.json()["token"]}')
        self.assertNotEqual(self.api.get(SOME_API).status_code, 401)
        self.assertTrue(admin.is_active)

    def test_suspend_keeps_all_data(self):
        emp = self.make_employee()
        users_before = User.objects.count()
        emps_before = Employee._base_manager.count()
        self.suspend()
        self.assertEqual(User.objects.count(), users_before)
        self.assertEqual(Employee._base_manager.count(), emps_before)
        emp.refresh_from_db()
        emp.user.refresh_from_db()
        self.assertEqual(emp.status, 'active')
        self.assertTrue(emp.user.is_active)
        self.company.refresh_from_db()
        self.assertFalse(self.company.is_active)

    def test_notifications_stop_and_come_back(self):
        from accounts.fcm_service import send_notification_to_user
        from core.push_helper import send_push_to_user
        emp = self.make_employee()
        self.suspend()
        self.assertEqual(send_notification_to_user(emp.user, 'ت', 'ب')['errors'], ['Company suspended'])
        self.assertEqual(send_push_to_user(emp.user, 'ت', 'ب'), 0)
        self.resume()
        self.assertNotEqual(send_notification_to_user(emp.user, 'ت', 'ب')['errors'], ['Company suspended'])


class CompanyAccessCommandTests(AccessBase):
    def test_reactivate_accounts_only_when_suspended_and_only_active_employees(self):
        working = [self.make_employee() for _ in range(3)]
        left = self.make_employee(status='terminated')
        for e in working + [left]:
            e.user.is_active = False
            e.user.save()

        with self.assertRaises(CommandError):
            call_command('company_access', self.company.pk, 'reactivate-accounts', stdout=StringIO())

        self.suspend()
        out = StringIO()
        call_command('company_access', self.company.pk, 'reactivate-accounts', stdout=out)
        self.assertIn('رجّعت 3 حساب', out.getvalue())
        for e in working:
            e.user.refresh_from_db()
            self.assertTrue(e.user.is_active)
        left.user.refresh_from_db()
        self.assertFalse(left.user.is_active)

        # لسه موقوفة: مايقدروش يدخلوا لحد التشغيل
        self.assertEqual(self.login(working[0].user.username).json()['code'], 'company_suspended')
        self.resume()
        self.assertEqual(self.login(working[0].user.username).status_code, 200)

    def test_unknown_company(self):
        with self.assertRaises(CommandError):
            call_command('company_access', 999999, 'status', stdout=StringIO())

    def test_admin_buttons(self):
        User.objects.create_superuser(username='boss', password='pass1234', email='b@x.com', role='super_admin')
        self.client.login(username='boss', password='pass1234')
        url = '/admin/companies/company/'
        self.client.post(url, {'action': 'suspend_companies', '_selected_action': [self.company.pk]})
        self.company.refresh_from_db()
        self.assertFalse(self.company.is_active)
        self.client.post(url, {'action': 'resume_companies', '_selected_action': [self.company.pk]})
        self.company.refresh_from_db()
        self.assertTrue(self.company.is_active)


class ActivationTests(AccessBase):
    """11 و26: تفعيل الحساب مايبقاش طريقة للاستيلاء على حساب حد"""

    def new_employee(self, **kw):
        emp = self.make_employee(**kw)
        emp.user.must_change_password = True
        emp.user.save()
        return emp

    def post(self, url, emp, suffix=None, password=None, phone=None):
        data = {'phone': phone or emp.phone, 'national_id_suffix': suffix or emp.national_id[-4:]}
        if password:
            data['new_password'] = password
        return self.api.post(url, data, format='json')

    def test_new_account_activates_on_both_links(self):
        for url in (ACTIVATE_APP, ACTIVATE_WEB):
            emp = self.new_employee()
            r = self.post(url, emp)
            self.assertEqual(r.status_code, 200, url)
            self.assertEqual(r.json()['username'], emp.user.username)
            r = self.post(url, emp, password='newpass99')
            self.assertEqual(r.status_code, 200, url)
            emp.user.refresh_from_db()
            self.assertFalse(emp.user.must_change_password)
            self.assertEqual(self.login(emp.user.username, 'newpass99').status_code, 200)

    def test_already_active_account_cannot_be_taken_over(self):
        for url in (ACTIVATE_APP, ACTIVATE_WEB):
            emp = self.make_employee(role='company_admin')  # صاحب الشركة، متفعّل من زمان
            r = self.post(url, emp, password='hacked999')
            self.assertEqual(r.status_code, 400, url)
            self.assertEqual(r.json()['message'], ALREADY_ACTIVE_MSG)
            self.assertEqual(self.login(emp.user.username).status_code, 200)

    def test_needs_exactly_four_digits_and_full_phone(self):
        emp = self.new_employee()
        self.assertEqual(self.post(ACTIVATE_APP, emp, suffix=emp.national_id[-1:]).status_code, 400)
        self.assertEqual(self.post(ACTIVATE_APP, emp, phone=emp.phone[-7:]).status_code, 400)

    def test_does_not_reactivate_disabled_account(self):
        emp = self.new_employee()
        emp.user.is_active = False
        emp.user.save()
        r = self.post(ACTIVATE_APP, emp, password='newpass99')
        self.assertEqual(r.status_code, 403)
        emp.user.refresh_from_db()
        self.assertFalse(emp.user.is_active)
        self.assertFalse(emp.user.check_password('newpass99'))

    def test_refused_for_suspended_company(self):
        emp = self.new_employee()
        self.suspend()
        r = self.post(ACTIVATE_WEB, emp, password='newpass99')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['code'], 'company_suspended')

    def test_two_employees_same_data_refused(self):
        a = self.new_employee()
        b = self.new_employee()
        b.phone, b.national_id = a.phone, '2999999' + a.national_id[-7:]
        b.save()
        self.assertEqual(self.post(ACTIVATE_APP, a).status_code, 400)

    def test_locked_after_five_wrong_tries(self):
        emp = self.new_employee()
        for _ in range(5):
            self.assertEqual(self.post(ACTIVATE_APP, emp, suffix='0000').status_code, 400)
        r = self.post(ACTIVATE_APP, emp)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.json()['message'], LOCKED_MSG)


class OldSiteTests(AccessBase):
    """مجموعة 5: صفحات الموقع القديم للسوبر أدمن بس"""

    def test_employee_cannot_login_to_old_site(self):
        emp = self.make_employee(role='company_admin')
        r = self.client.post('/login/', {'username': emp.user.username, 'password': 'pass1234'})
        self.assertContains(r, 'للإدارة بس')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_existing_session_sees_closed_page(self):
        emp = self.make_employee(role='hr_manager')
        self.client.force_login(emp.user, backend='accounts.login_backend.SmartLoginBackend')
        for url in ('/dashboard/', '/companies/', '/leaves/', '/subscriptions/'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 403, url)
            self.assertContains(r, 'للإدارة بس', status_code=403)

    def test_old_site_api_links_closed_for_session(self):
        emp = self.make_employee(role='manager')
        self.client.force_login(emp.user, backend='accounts.login_backend.SmartLoginBackend')
        for url in ('/attendance/api/employee-route/1/', '/attendance/api/monitor/', '/employees/api/search/?q=a'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 403, url)

    def test_token_requests_not_affected_by_old_site_lock(self):
        emp = self.make_employee()
        token = self.login(emp.user.username).json()['token']
        self.client.force_login(emp.user, backend='accounts.login_backend.SmartLoginBackend')
        r = self.client.get(SOME_API, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(r.status_code, 200)

    def test_open_pages_still_open(self):
        emp = self.make_employee()
        self.client.force_login(emp.user, backend='accounts.login_backend.SmartLoginBackend')
        r = self.client.get('/subscriptions/contact-sales/')
        self.assertNotContains(r, 'للإدارة بس', status_code=r.status_code)

    def test_super_admin_can_login(self):
        User.objects.create_user(username='root2', password='pass1234', role='super_admin')
        r = self.client.post('/login/', {'username': 'root2', 'password': 'pass1234'})
        self.assertEqual(r.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_api_not_affected_by_old_site_lock(self):
        emp = self.make_employee()
        self.assertEqual(self.login(emp.user.username).status_code, 200)

    def test_second_subscriptions_dashboard_needs_super_admin(self):
        from subscriptions.views import admin_dashboard
        emp = self.make_employee(role='company_admin')
        request = RequestFactory().get('/subscriptions/')
        request.user = emp.user
        r = admin_dashboard(request)
        self.assertEqual(r.status_code, 302)
