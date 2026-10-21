"""
اختبارات دفعة 8 (متوسطة):
270 الدخول بالرقم الوظيفي، 333 الدايرة في المديرين، 320 الإعلانات للي سابوا الشركة، 517 تمديد الاشتراك المنتهي،
541 الطلب بيتقرر مرة واحدة، 570 الويب مابيسجلش تنبيه GPS

التشغيل:
  python manage.py test attendance.test_group8_medium --settings=motionhr.settings_test
"""
from datetime import date, timedelta

from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APIClient

from attendance.test_action_scope import ScopeBase

LOGIN = '/attendance/api/mobile/login/'


class EmployeeCodeLoginTests(ScopeBase):
    def login(self, username, password):
        return APIClient().post(LOGIN, {'username': username, 'password': password}, format='json')

    def test_unique_code_logs_in(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(employee_code='ZX900')
        self.other_a.user.set_password('Pass12345')
        self.other_a.user.save()
        self.assertEqual(self.login('ZX900', 'Pass12345').status_code, 200)

    def test_code_shared_between_companies_is_not_guessed(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(employee_code='EMP00001')
        Employee._base_manager.filter(pk=self.emp_b.pk).update(employee_code='EMP00001')
        for e in (self.other_a, self.emp_b):
            e.user.set_password('12345678')
            e.user.save()
        # نفس الكود ونفس الباسورد الافتراضي في شركتين: مايدخلش حساب شركة تانية بالغلط
        self.assertEqual(self.login('EMP00001', '12345678').status_code, 401)


class ManagerCycleTests(ScopeBase):
    def test_cycle_does_not_hang(self):
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.mgr_a.pk).update(direct_manager=self.team_a)   # team_a تحت mgr_a وmgr_a تحت team_a
        self.mgr_a.refresh_from_db()
        subs = self.mgr_a.get_all_subordinates()
        self.assertEqual(sorted(e.id for e in subs), [self.team_a.id])
        self.assertEqual([e.id for e in self.mgr_a.get_manager_chain()], [self.team_a.id])

    def test_transfer_refuses_cycle(self):
        r = self.api(self.hr_a).post(f'/attendance/api/mobile/manager/employees/{self.mgr_a.id}/transfer/',
                                     {'new_manager_id': self.team_a.id}, format='json')
        self.assertEqual(r.status_code, 400)


class AnnouncementTargetsTests(ScopeBase):
    def test_former_employees_not_targeted(self):
        from accounts.company_announcements import CompanyAnnouncement
        from employees.models import Employee
        Employee._base_manager.filter(pk=self.other_a.pk).update(status='terminated')
        ann = CompanyAnnouncement._base_manager.create(company=self.a, title='t', message='m', created_by=self.hr_a.user)
        ids = set(ann.get_target_employees().values_list('id', flat=True))
        self.assertNotIn(self.other_a.id, ids)
        self.assertIn(self.team_a.id, ids)


class ExtendSubscriptionTests(ScopeBase):
    def test_expired_extends_from_today(self):
        from accounts.models import User
        from subscriptions.models import CompanySubscription, SubscriptionPlan
        from subscriptions.views import extend_subscription
        plan = SubscriptionPlan.objects.create(name_ar='أساسي', name_en='Basic', price_monthly=0)
        today = timezone.now().date()
        sub = CompanySubscription.objects.create(company=self.a, plan=plan, start_date=today - timedelta(days=90),
                                                 end_date=today - timedelta(days=30), status='expired')
        root = User.objects.create_user(username='root9', password='x', role='super_admin')
        req = RequestFactory().post('/', {'days': 30, 'price': '150.50'})
        req.user = root
        req._messages = type('M', (), {'add': lambda *a, **k: None})()
        extend_subscription(req, sub.pk)
        sub.refresh_from_db()
        self.assertEqual(sub.end_date, today + timedelta(days=30))
        self.assertEqual(str(sub.price_paid), '150.50')


class RequestDecidedOnceTests(ScopeBase):
    def test_second_decision_refused(self):
        rq = self.req(self.other_a)
        c = self.api(self.hr_a)
        self.assertEqual(c.post('/attendance/api/mobile/manager/action/', {'type': 'request', 'id': rq.id, 'action': 'approve'}, format='json').status_code, 200)
        r = c.post('/attendance/api/mobile/manager/action/', {'type': 'request', 'id': rq.id, 'action': 'reject', 'notes': 'لا'}, format='json')
        self.assertEqual(r.status_code, 409)
        rq.refresh_from_db()
        self.assertEqual(rq.status, 'approved')


class WebStatusNoGpsAlertTests(ScopeBase):
    def test_web_status_call_creates_no_alert(self):
        from attendance.models import TrackingAlert
        self.api(self.team_a).get('/attendance/api/mobile/status/?source=web')
        self.assertFalse(TrackingAlert._base_manager.filter(employee=self.team_a).exists())
