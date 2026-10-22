"""
Middleware للتحكم في Multi-tenant
"""

import threading

_thread_local = threading.local()


def get_current_company():
    return getattr(_thread_local, 'company', None)


def get_current_user():
    return getattr(_thread_local, 'user', None)


def set_current_company(company):
    _thread_local.company = company


def set_current_user(user):
    _thread_local.user = user


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)

            if hasattr(request.user, 'company') and request.user.company:
                set_current_company(request.user.company)
                request.current_company = request.user.company
            else:
                set_current_company(None)
                request.current_company = None
        else:
            set_current_user(None)
            set_current_company(None)
            request.current_company = None

        response = self.get_response(request)

        set_current_user(None)
        set_current_company(None)

        return response


class CurrentEmployeeMiddleware:
    """
    Middleware يضيف employee profile للـ request
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_employee = None

        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from employees.models import Employee
                request.current_employee = Employee.all_objects.filter(
                    user=request.user
                ).select_related("job_title", "department", "branch").first()
            except Exception:
                pass

        response = self.get_response(request)
        return response


class SubscriptionMiddleware:
    """
    Middleware للتحقق من اشتراك الشركة
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.subscription = None
        request.subscription_features = set()
        request.subscription_valid = False
        request.days_remaining = 0

        if hasattr(request, 'user') and request.user.is_authenticated:
            # Super Admin يشوف كل حاجة
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                request.subscription_valid = True
                request.subscription_features = self._all_features()
            else:
                if hasattr(request.user, 'company') and request.user.company:
                    try:
                        from subscriptions.models import CompanySubscription
                        from django.utils import timezone

                        sub = CompanySubscription.objects.filter(
                            company=request.user.company
                        ).select_related('plan').first()

                        if sub:
                            request.subscription = sub

                            try:
                                request.subscription_valid = sub.is_valid
                            except Exception:
                                request.subscription_valid = (
                                    getattr(sub, 'status', '') in ['active', 'trial']
                                    and getattr(sub, 'end_date', timezone.now().date()) >= timezone.now().date()
                                )

                            try:
                                request.days_remaining = sub.days_remaining
                            except Exception:
                                end_date = getattr(sub, 'end_date', timezone.now().date())
                                if end_date >= timezone.now().date():
                                    request.days_remaining = (end_date - timezone.now().date()).days
                                else:
                                    request.days_remaining = 0

                            try:
                                request.subscription_features = sub.all_features
                            except Exception:
                                request.subscription_features = set()

                    except Exception:
                        pass

        response = self.get_response(request)
        return response

    def _all_features(self):
        try:
            from subscriptions.models import FeatureFlag
            return set(
                FeatureFlag.objects.filter(is_active=True).values_list('key', flat=True)
            )
        except Exception:
            return {
                'employee_management',
                'attendance_tracking',
                'gps_attendance',
                'field_tracking',
                'live_map',
                'location_visits',
                'reports_basic',
                'reports_advanced',
                'excel_export',
                'pdf_export',
                'login_by_employee_code',
                'login_by_phone',
                'leave_management',
                'multi_branch',
                'payroll_basic',
            }


class CharterMiddleware:
    """
    لو الميثاق إجباري والموظف ما وافقش
    يتحول لصفحة الميثاق تلقائيًا
    """

    EXEMPT_URLS = [
        '/login/',
        '/logout/',
        '/admin/',
        '/password-change/',
        '/password-reset/',
        '/companies/charter/',
        '/static/',
        '/media/',
        '/manifest.json',
        '/sw.js',
        '/offline/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role == 'employee'
            and hasattr(request.user, 'company')
            and request.user.company
            and not request.user.is_superuser
        ):
            path = request.path_info
            exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)

            if not exempt:
                try:
                    from companies.models import WorkCharter, CharterAcceptance
                    from employees.models import Employee

                    charter = WorkCharter.objects.filter(
                        company=request.user.company,
                        is_active=True,
                        is_mandatory=True,
                    ).first()

                    if charter:
                        employee = Employee.objects.filter(
                            user=request.user
                        ).first()

                        if employee:
                            accepted = CharterAcceptance.objects.filter(
                                employee=employee,
                                charter=charter,
                            ).exists()

                            if not accepted:
                                from django.shortcuts import redirect
                                return redirect('/companies/charter/')
                except Exception:
                    pass

        return self.get_response(request)


# ═════════════════════════════════════════════════════════════
# Patch 49a Fix4 — CompanyPolicy Stealth Sync Middleware
# ═════════════════════════════════════════════════════════════
class CompanyPolicyStealthSyncMiddleware:
    """
    يثبّت حفظ حقول التتبع الصامت بعد POST على /companies/policies/
    حتى لو الـ view القديم لا يحفظها بشكل صحيح.
    """

    POLICY_PATHS = {"/companies/policies", "/companies/policies/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def _get_first_value(self, post_data, keys):
        for key in keys:
            if key in post_data:
                return post_data.get(key)
        return None

    def _is_checked(self, post_data, keys):
        """
        checkbox considered True if any alias exists and value is truthy
        """
        truthy = {"1", "true", "True", "on", "yes", "y"}
        for key in keys:
            if key in post_data:
                return str(post_data.get(key)).strip() in truthy or post_data.get(key) == "on"
        return False

    def __call__(self, request):
        response = self.get_response(request)

        try:
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return response

            current_path = request.path.rstrip("/")
            if request.method != "POST":
                return response

            if current_path != "/companies/policies":
                return response

            company = getattr(user, "company", None)
            if not company:
                return response

            from companies.models import CompanyPolicy

            policy, _ = CompanyPolicy.objects.get_or_create(company=company)

            # ── aliases لاحتمالات اختلاف أسماء الحقول في التمبلت ──
            stealth_enabled_keys = [
                "stealth_tracking_enabled",
                "enable_stealth_tracking",
                "stealth_enabled",
            ]
            notify_manager_keys = [
                "stealth_tracking_notify_manager",
                "notify_manager",
                "stealth_notify_manager",
            ]
            notify_hr_keys = [
                "stealth_tracking_notify_hr",
                "notify_hr",
                "stealth_notify_hr",
            ]
            notify_company_admin_keys = [
                "stealth_tracking_notify_company_admin",
                "notify_company_admin",
                "stealth_notify_company_admin",
                "notify_owner",
            ]
            requires_charter_keys = [
                "stealth_tracking_requires_charter_clause",
                "requires_charter_clause",
                "stealth_requires_charter_clause",
            ]
            minutes_keys = [
                "stealth_tracking_alert_after_minutes",
                "stealth_alert_after_minutes",
                "alert_after_minutes",
            ]

            # نعتبر إن صفحة stealth موجودة طالما أي مفتاح من دول في POST
            any_stealth_posted = any(
                key in request.POST for key in (
                    stealth_enabled_keys
                    + notify_manager_keys
                    + notify_hr_keys
                    + notify_company_admin_keys
                    + requires_charter_keys
                    + minutes_keys
                )
            )

            # حتى لو مفيش checkbox checked، طالما الصفحة اتبعت وحقول الدقائق موجودة
            # أو تم فتح سياسات الشركة POST، هنثبّت القيم الحالية من POST.
            if any_stealth_posted or current_path == "/companies/policies":
                policy.stealth_tracking_enabled = self._is_checked(request.POST, stealth_enabled_keys)
                policy.stealth_tracking_notify_manager = self._is_checked(request.POST, notify_manager_keys)
                policy.stealth_tracking_notify_hr = self._is_checked(request.POST, notify_hr_keys)
                policy.stealth_tracking_notify_company_admin = self._is_checked(request.POST, notify_company_admin_keys)
                policy.stealth_tracking_requires_charter_clause = self._is_checked(request.POST, requires_charter_keys)

                minutes_raw = self._get_first_value(request.POST, minutes_keys)
                if minutes_raw not in [None, ""]:
                    try:
                        minutes_val = int(str(minutes_raw).strip())
                        if minutes_val < 1:
                            minutes_val = 1
                        if minutes_val > 1440:
                            minutes_val = 1440
                        policy.stealth_tracking_alert_after_minutes = minutes_val
                    except Exception:
                        pass

                policy.save()

        except Exception as e:
            # ما نكسرش الصفحة لو حصل أي خطأ
            print(f"[Patch 49a Fix4] Middleware warning: {e}")

        return response


# ═════════════════════════════════════════════════════════════
# Patch 49a Fix5 — CompanyPolicyStealthFinalSyncMiddleware
# ═════════════════════════════════════════════════════════════
class CompanyPolicyStealthFinalSyncMiddleware:
    """
    يثبت حفظ حقول التتبع الصامت بعد POST على /companies/policies/
    ويضمن أن الشركة لها CompanyPolicy واحدة فقط.
    """

    POLICY_PATHS = {"/companies/policies", "/companies/policies/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def _bool_value(self, post_data, aliases):
        truthy = {"1", "true", "True", "on", "yes", "y"}
        for key in aliases:
            if key in post_data:
                val = str(post_data.get(key)).strip()
                return val in truthy or val == "on"
        return False

    def _first_value(self, post_data, aliases):
        for key in aliases:
            if key in post_data:
                return post_data.get(key)
        return None

    def __call__(self, request):
        response = self.get_response(request)

        try:
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return response

            current_path = request.path.rstrip("/")
            if request.method != "POST":
                return response

            if current_path != "/companies/policies":
                return response

            company = getattr(user, "company", None)
            if not company:
                try:
                    company = user.employee.company
                except Exception:
                    company = None

            if not company:
                return response

            from companies.models import CompanyPolicy

            policies = CompanyPolicy.objects.filter(company=company).order_by("id")
            policy = policies.last()
            if not policy:
                policy = CompanyPolicy.objects.create(company=company)

            # aliases لاحتمالات اختلاف أسماء الحقول في الفورم
            enabled_keys = [
                "stealth_tracking_enabled",
                "enable_stealth_tracking",
                "stealth_enabled",
            ]
            notify_manager_keys = [
                "stealth_tracking_notify_manager",
                "notify_manager",
                "stealth_notify_manager",
            ]
            notify_hr_keys = [
                "stealth_tracking_notify_hr",
                "notify_hr",
                "stealth_notify_hr",
            ]
            notify_company_admin_keys = [
                "stealth_tracking_notify_company_admin",
                "notify_company_admin",
                "stealth_notify_company_admin",
                "notify_owner",
            ]
            requires_charter_keys = [
                "stealth_tracking_requires_charter_clause",
                "requires_charter_clause",
                "stealth_requires_charter_clause",
            ]
            minutes_keys = [
                "stealth_tracking_alert_after_minutes",
                "stealth_alert_after_minutes",
                "alert_after_minutes",
            ]

            # لو الحقول موجودة في POST نحدثها
            posted_any_stealth = any(
                key in request.POST for key in (
                    enabled_keys
                    + notify_manager_keys
                    + notify_hr_keys
                    + notify_company_admin_keys
                    + requires_charter_keys
                    + minutes_keys
                )
            )

            if posted_any_stealth:
                policy.stealth_tracking_enabled = self._bool_value(request.POST, enabled_keys)
                policy.stealth_tracking_notify_manager = self._bool_value(request.POST, notify_manager_keys)
                policy.stealth_tracking_notify_hr = self._bool_value(request.POST, notify_hr_keys)
                policy.stealth_tracking_notify_company_admin = self._bool_value(request.POST, notify_company_admin_keys)
                policy.stealth_tracking_requires_charter_clause = self._bool_value(request.POST, requires_charter_keys)

                minutes_raw = self._first_value(request.POST, minutes_keys)
                if minutes_raw not in (None, ""):
                    try:
                        minutes_val = int(str(minutes_raw).strip())
                        if minutes_val < 1:
                            minutes_val = 1
                        if minutes_val > 1440:
                            minutes_val = 1440
                        policy.stealth_tracking_alert_after_minutes = minutes_val
                    except Exception:
                        pass

                policy.save()

                # حذف أي duplicate بعد الحفظ
                extra_policies = CompanyPolicy.objects.filter(company=company).exclude(id=policy.id)
                if extra_policies.exists():
                    extra_policies.delete()

        except Exception as e:
            print(f"[Patch 49a Fix5] Middleware warning: {e}")

        return response



# ═════════════════════════════════════════════════════════════
# حماية الدخول: الحساب الموقوف، الشركة الموقوفة، والموقع القديم
# ═════════════════════════════════════════════════════════════

_BLOCK_PAGE = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>MotionHR</title>
<style>body{{font-family:Tahoma,Arial,sans-serif;background:#f4f6fa;color:#1f2937;margin:0;
display:flex;min-height:100vh;align-items:center;justify-content:center;padding:16px}}
.box{{background:#fff;border-radius:12px;padding:32px;max-width:480px;text-align:center;
box-shadow:0 2px 12px rgba(0,0,0,.08)}}h1{{font-size:20px;margin:0 0 12px}}p{{line-height:1.8}}
button{{margin-top:16px;padding:8px 20px;border:0;border-radius:8px;background:#1d4ed8;color:#fff;cursor:pointer}}
</style></head><body><div class="box"><h1>{title}</h1><p>{message}</p>
<form method="post" action="/logout/"><input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
<button type="submit">تسجيل الخروج</button></form></div></body></html>"""

OLD_SITE_CLOSED_MSG = (
    'صفحات الموقع القديم بقت للإدارة بس. '
    'من فضلك استخدم موقع الويب app.jssolutions-eg.com أو تطبيق الموبايل.'
)


def _block_page(request, title, message):
    from django.http import HttpResponse
    from django.middleware.csrf import get_token
    from django.utils.html import escape
    html = _BLOCK_PAGE.format(title=escape(title), message=escape(message), csrf=get_token(request))
    return HttpResponse(html, status=403)


def _user_from_auth_header(request):
    """المستخدم صاحب التوكن (Token أو Bearer) حتى لو حسابه موقوف — من غير ما نرفض الطلب هنا"""
    header = request.META.get('HTTP_AUTHORIZATION', '')
    parts = header.split()
    if len(parts) != 2:
        return None
    kind, key = parts
    try:
        if kind == 'Token':
            from rest_framework.authtoken.models import Token
            tok = Token._base_manager.select_related('user').filter(key=key).first()
            return tok.user if tok else None
        if kind == 'Bearer':
            from django.contrib.auth import get_user_model
            from rest_framework_simplejwt.authentication import JWTAuthentication
            from rest_framework_simplejwt.settings import api_settings
            validated = JWTAuthentication().get_validated_token(key.encode())
            uid = validated.get(api_settings.USER_ID_CLAIM)
            return get_user_model()._base_manager.filter(**{api_settings.USER_ID_FIELD: uid}).first()
    except Exception:
        return None
    return None


class AccessGuardMiddleware:
    """
    1) أي طلب من حساب موقوف أو من شركة موقوفة بيترفض برسالة واضحة
       (الـ API بـ 401 عشان الويب يرجّعه لصفحة الدخول، والصفحات بصفحة رسالة).
    2) صفحات الموقع القديم (Django) بقت للسوبر أدمن بس — أي طلب بجلسة الموقع القديم
       من غير توكن على مساراته (حتى اللي فيها api) بيتقفل على غير السوبر أدمن.
    """

    OLD_SITE_PREFIXES = (
        '/dashboard/', '/search/', '/accounts/', '/employees/', '/attendance/',
        '/subscriptions/', '/companies/', '/leaves/', '/requests/', '/reports/',
        '/announcements/', '/password-change/',
    )
    OLD_SITE_OPEN = ('/subscriptions/contact-sales',)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith(('/static/', '/media/')) or path.endswith('/logout/'):
            return self.get_response(request)

        from accounts.access import block_reason, blocked_payload, is_super_admin

        is_api = '/api/' in path
        session_user = getattr(request, 'user', None)
        if not (session_user and session_user.is_authenticated):
            session_user = None

        user = session_user
        if user is None and request.META.get('HTTP_AUTHORIZATION'):
            user = _user_from_auth_header(request)

        if user is not None:
            reason = block_reason(user)
            if reason:
                if is_api or session_user is None:
                    from django.http import JsonResponse
                    return JsonResponse(blocked_payload(reason), status=401,
                                        json_dumps_params={'ensure_ascii': False})
                if path not in ('/login/',):
                    return _block_page(request, 'مش متاح', reason[1])

        # الويب الجديد والموبايل بيبعتوا توكن؛ الطلب اللي من غير توكن جاي من صفحات الموقع القديم
        # (حتى لو في رابطه api زي attendance/api/employee-route)
        if (session_user is not None and not request.META.get('HTTP_AUTHORIZATION')
                and path.startswith(self.OLD_SITE_PREFIXES)
                and not path.startswith(self.OLD_SITE_OPEN)
                and not is_super_admin(session_user)):
            return _block_page(request, 'الصفحة دي مقفولة', OLD_SITE_CLOSED_MSG)

        return self.get_response(request)
