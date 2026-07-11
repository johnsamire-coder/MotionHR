"""
Patch 49a Fix4
حل مشكلة إن إعدادات Stealth Tracking في صفحة سياسات الشركة
بتقول "تم الحفظ" لكن بعد الريلود بترجع False.

الحل:
- نضيف Middleware يراقب أي POST على /companies/policies/
- بعد ما الـ view الأصلي يخلص، نثبّت قيم stealth في قاعدة البيانات
- كده حتى لو الـ view القديم مش بيحفظ الحقول الجديدة، القيم تفضل محفوظة
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")

print("=" * 60)
print("Patch 49a Fix4 — Stealth Policy Persist Fix")
print("=" * 60)

# ═════════════════════════════════════════════════════════════
# 1) Append middleware class to core/middleware.py
# ═════════════════════════════════════════════════════════════
middleware_path = "core/middleware.py"
middleware_content = read_file(middleware_path)

if middleware_content is None:
    raise SystemExit("❌ ملف core/middleware.py غير موجود")

class_name = "CompanyPolicyStealthSyncMiddleware"

middleware_class_code = r'''

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
'''

if class_name not in middleware_content:
    middleware_content = middleware_content.rstrip() + "\n" + middleware_class_code + "\n"
    write_file(middleware_path, middleware_content)
    print("✅ تم إضافة Middleware class")
else:
    print("ℹ️ Middleware class موجود بالفعل")


# ═════════════════════════════════════════════════════════════
# 2) Register middleware in settings.py
# ═════════════════════════════════════════════════════════════
settings_path = "motionhr/settings.py"
settings_content = read_file(settings_path)

if settings_content is None:
    raise SystemExit("❌ ملف motionhr/settings.py غير موجود")

middleware_entry = "'core.middleware.CompanyPolicyStealthSyncMiddleware'"

if middleware_entry in settings_content or '"core.middleware.CompanyPolicyStealthSyncMiddleware"' in settings_content:
    print("ℹ️ Middleware مسجل بالفعل في settings.py")
else:
    inserted = False

    candidates = [
        "'django.contrib.auth.middleware.AuthenticationMiddleware',",
        '"django.contrib.auth.middleware.AuthenticationMiddleware",',
        "'accounts.middleware.",
        '"accounts.middleware.',
        "'core.middleware.",
        '"core.middleware.',
    ]

    for marker in candidates:
        if marker in settings_content:
            if "AuthenticationMiddleware" in marker:
                settings_content = settings_content.replace(
                    marker,
                    marker + "\n    'core.middleware.CompanyPolicyStealthSyncMiddleware',",
                    1
                )
                inserted = True
                break

    if not inserted:
        if "MIDDLEWARE = [" in settings_content:
            settings_content = settings_content.replace(
                "MIDDLEWARE = [",
                "MIDDLEWARE = [\n    'core.middleware.CompanyPolicyStealthSyncMiddleware',",
                1
            )
            inserted = True

    write_file(settings_path, settings_content)
    print("✅ تم تسجيل Middleware في settings.py")


print("\n" + "=" * 60)
print("✅ Patch 49a Fix4 اكتمل")
print("=" * 60)
print("""
شغّل بالترتيب:
python manage.py check
python manage.py runserver 0.0.0.0:8000

اختبار بعده:
1) ادخل /companies/policies/
2) فعّل Stealth Tracking
3) اختَر HR + صاحب الشركة
4) احفظ
5) اعمل Refresh
المفروض القيم تفضل محفوظة وماتتلغيش
""")