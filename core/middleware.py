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

