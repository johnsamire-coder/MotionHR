#!/usr/bin/env python3
"""
Patch 48b: NotificationPreference + Send Push Logic
=====================================================
1) NotificationPreference model
2) send_push_to_user helper
3) ربط Push بـ EmployeeNotification
4) صفحة إعدادات الإشعارات
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


def get_last_migration(app_dir):
    migrations_dir = os.path.join(BASE_DIR, app_dir, "migrations")
    existing = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith(".py") and f != "__init__.py"
    ])
    if existing:
        last = existing[-1].replace(".py", "")
        last_num = int(last.split("_")[0])
        return last, last_num
    return "0001_initial", 1


print("=" * 60)
print("  Patch 48b: NotificationPreference + Send Logic")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) companies/models.py — NotificationPreference
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة NotificationPreference model...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

notif_pref_model = '''

class NotificationPreference(models.Model):
    """إعدادات إشعارات Push لكل دور في الشركة"""

    ROLE_CHOICES = [
        ("employee", "موظف"),
        ("manager", "مدير"),
        ("hr_manager", "مدير HR"),
        ("company_admin", "صاحب الشركة"),
    ]

    NOTIFICATION_TYPES = [
        ("request_approved", "تمت الموافقة على الطلب"),
        ("request_rejected", "تم رفض الطلب"),
        ("new_request_to_approve", "طلب جديد يحتاج موافقة"),
        ("late_warning", "تحذير تأخير"),
        ("late_threshold", "تجاوز حد التأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("stealth_alert", "تنبيه تتبع صامت"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("subscription_expiry", "انتهاء الاشتراك"),
        ("general_notice", "إشعار عام"),
    ]

    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name="الشركة"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="الدور"
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name="نوع الإشعار"
    )
    push_enabled = models.BooleanField(
        default=True,
        verbose_name="إرسال Push"
    )

    class Meta:
        verbose_name = "إعداد إشعار"
        verbose_name_plural = "إعدادات الإشعارات"
        unique_together = [["company", "role", "notification_type"]]

    def __str__(self):
        return f"{self.company} - {self.role} - {self.notification_type}"

    @classmethod
    def is_push_enabled(cls, company, role, notification_type):
        """هل Push مفعّل لهذا الدور وهذا النوع؟"""
        try:
            pref = cls.objects.get(
                company=company,
                role=role,
                notification_type=notification_type
            )
            return pref.push_enabled
        except cls.DoesNotExist:
            return True  # افتراضي: مفعّل
        except Exception:
            return False
'''

if "class NotificationPreference" not in comp_models:
    comp_models += notif_pref_model
    write_file(comp_models_path, comp_models)
    print("  ✅ تم إضافة NotificationPreference")
else:
    print("  ℹ️  NotificationPreference موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

last, num = get_last_migration("companies")
new_num = str(num + 1).zfill(4)

create_file(
    os.path.join(BASE_DIR, "companies", "migrations",
                 f"{new_num}_add_notification_preference.py"),
    f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "{last}"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False)),
                ("role", models.CharField(max_length=20, verbose_name="الدور",
                    choices=[
                        ("employee","موظف"),("manager","مدير"),
                        ("hr_manager","مدير HR"),("company_admin","صاحب الشركة"),
                    ]
                )),
                ("notification_type", models.CharField(max_length=30,
                    verbose_name="نوع الإشعار",
                    choices=[
                        ("request_approved","تمت الموافقة على الطلب"),
                        ("request_rejected","تم رفض الطلب"),
                        ("new_request_to_approve","طلب جديد يحتاج موافقة"),
                        ("late_warning","تحذير تأخير"),
                        ("late_threshold","تجاوز حد التأخير"),
                        ("deduction_notice","إشعار خصم"),
                        ("stealth_alert","تنبيه تتبع صامت"),
                        ("charter_reminder","تذكير بالميثاق"),
                        ("subscription_expiry","انتهاء الاشتراك"),
                        ("general_notice","إشعار عام"),
                    ]
                )),
                ("push_enabled", models.BooleanField(default=True,
                                                      verbose_name="إرسال Push")),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notification_preferences",
                    to="companies.company",
                    verbose_name="الشركة"
                )),
            ],
            options={{
                "verbose_name": "إعداد إشعار",
                "verbose_name_plural": "إعدادات الإشعارات",
            }},
        ),
        migrations.AlterUniqueTogether(
            name="notificationpreference",
            unique_together={{("company", "role", "notification_type")}},
        ),
    ]
'''
)

call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 3) send_push_to_user helper
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء push_helper.py...")

create_file(
    os.path.join(BASE_DIR, "core", "push_helper.py"),
    '''"""
push_helper.py
إرسال Web Push Notifications
"""

from django.conf import settings


def send_push_to_user(user, title, body, url="/dashboard/",
                      notification_type="general_notice"):
    """
    إرسال Push Notification لمستخدم معين
    - يبص على PushSubscription بتاعته
    - يبص على NotificationPreference
    - لو مفعّل يبعت

    في الإنتاج:
    pip install pywebpush
    """
    try:
        from accounts.models import PushSubscription
        from companies.models import NotificationPreference

        subs = PushSubscription.objects.filter(
            user=user,
            is_active=True
        )

        if not subs.exists():
            return 0

        # فحص الـ preference
        role = getattr(user, "role", "employee")
        company = getattr(user, "company", None)

        if company:
            push_allowed = NotificationPreference.is_push_enabled(
                company, role, notification_type
            )
            if not push_allowed:
                return 0

        vapid_public = getattr(settings, "VAPID_PUBLIC_KEY", "")
        vapid_private = getattr(settings, "VAPID_PRIVATE_KEY", "")
        vapid_email = getattr(settings, "VAPID_ADMIN_EMAIL", "")

        if not vapid_public or "Dummy" in vapid_public:
            # Development mode: log only
            print(f"[Push DEV] To: {user.username} | {title} | {body}")
            return 1

        sent = 0
        import json

        try:
            from pywebpush import webpush, WebPushException

            payload = json.dumps({
                "title": title,
                "body": body,
                "url": url,
                "icon": "/static/icons/icon-192x192.png",
                "badge": "/static/icons/icon-72x72.png",
            })

            for sub in subs:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub.endpoint,
                            "keys": {
                                "p256dh": sub.p256dh,
                                "auth": sub.auth,
                            }
                        },
                        data=payload,
                        vapid_private_key=vapid_private,
                        vapid_claims={
                            "sub": f"mailto:{vapid_email}",
                        }
                    )
                    sent += 1
                except WebPushException as e:
                    if "410" in str(e) or "404" in str(e):
                        sub.is_active = False
                        sub.save(update_fields=["is_active"])
                except Exception:
                    pass

        except ImportError:
            # pywebpush مش مثبت
            print(f"[Push] pywebpush not installed. To: {user.username} | {title}")
            sent = 1

        return sent

    except Exception as e:
        print(f"[Push Error] {e}")
        return 0


def send_push_to_company_role(company, role, title, body,
                               url="/dashboard/",
                               notification_type="general_notice"):
    """
    إرسال Push لكل المستخدمين في شركة معينة بدور معين
    """
    try:
        from accounts.models import User

        users = User.objects.filter(
            company=company,
            role=role,
            is_active=True
        )

        total = 0
        for user in users:
            total += send_push_to_user(
                user, title, body, url, notification_type
            )
        return total
    except Exception:
        return 0
'''
)


# ════════════════════════════════════════════════════════════
# 4) ربط Push بـ EmployeeNotification
# ════════════════════════════════════════════════════════════
print("\n🔧 ربط Push بـ EmployeeNotification...")

acc_views_path = os.path.join(BASE_DIR, "accounts", "views.py")
acc_views = read_file(acc_views_path)

# نضيف push في notifications_view لما يتعمل notification جديد
push_trigger = '''

# ════════════════════════════════════════════════════════════
# Push Trigger — بيتشغل لما EmployeeNotification يتنشأ
# ════════════════════════════════════════════════════════════
def trigger_push_for_employee_notification(notification_obj):
    """
    بعد ما EmployeeNotification يتنشأ → ابعت Push
    """
    try:
        from core.push_helper import send_push_to_user
        from employees.models import Employee

        employee = notification_obj.employee
        if not employee.user:
            return

        type_map = {
            "late_warning": "late_warning",
            "deduction_notice": "deduction_notice",
            "request_update": "request_approved",
            "general_notice": "general_notice",
            "policy_reminder": "general_notice",
            "charter_reminder": "charter_reminder",
        }

        notif_type = type_map.get(
            notification_obj.notification_type,
            "general_notice"
        )

        send_push_to_user(
            user=employee.user,
            title=notification_obj.title,
            body=notification_obj.message[:100] if notification_obj.message else "",
            url="/accounts/notifications/",
            notification_type=notif_type,
        )
    except Exception:
        pass
'''

if "trigger_push_for_employee_notification" not in acc_views:
    acc_views += push_trigger
    write_file(acc_views_path, acc_views)
    print("  ✅ تم إضافة Push trigger")
else:
    print("  ℹ️  Push trigger موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 5) ربط trigger بـ EmployeeNotification.save
# ════════════════════════════════════════════════════════════
print("\n🔧 ربط push trigger بـ EmployeeNotification...")

acc_models_path = os.path.join(BASE_DIR, "accounts", "models.py")
acc_models = read_file(acc_models_path)

if "def save" not in acc_models.split("class EmployeeNotification")[1].split("class ")[0]:
    # نضيف override save في EmployeeNotification
    old_meta = '''    class Meta:
        verbose_name = "إشعار موظف"
        verbose_name_plural = "إشعارات الموظفين"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"'''

    new_meta = '''    class Meta:
        verbose_name = "إشعار موظف"
        verbose_name_plural = "إشعارات الموظفين"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            try:
                from accounts.views import trigger_push_for_employee_notification
                trigger_push_for_employee_notification(self)
            except Exception:
                pass'''

    if old_meta in acc_models:
        acc_models = acc_models.replace(old_meta, new_meta)
        write_file(acc_models_path, acc_models)
        print("  ✅ تم ربط Push بـ EmployeeNotification.save")
    else:
        print("  ℹ️  ربط Push — النص مختلف أو موجود بالفعل")
else:
    print("  ℹ️  Push save override موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 6) companies/views.py — notification settings page
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة notification settings view...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

notif_settings_view = '''

# ════════════════════════════════════════════════════════════
# Notification Settings
# ════════════════════════════════════════════════════════════

@login_required
def notification_settings_view(request):
    """إعدادات الإشعارات للشركة"""
    from companies.models import NotificationPreference

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company

    roles = ["employee", "manager", "hr_manager", "company_admin"]
    role_labels = {
        "employee": "موظف",
        "manager": "مدير",
        "hr_manager": "مدير HR",
        "company_admin": "صاحب الشركة",
    }

    notification_types = [
        ("request_approved", "تمت الموافقة على الطلب"),
        ("request_rejected", "تم رفض الطلب"),
        ("new_request_to_approve", "طلب جديد يحتاج موافقة"),
        ("late_warning", "تحذير تأخير"),
        ("late_threshold", "تجاوز حد التأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("stealth_alert", "تنبيه تتبع صامت"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("subscription_expiry", "انتهاء الاشتراك"),
        ("general_notice", "إشعار عام"),
    ]

    # بناء matrix
    prefs_map = {}
    existing = NotificationPreference.objects.filter(company=company)
    for p in existing:
        prefs_map[f"{p.role}_{p.notification_type}"] = p.push_enabled

    if request.method == "POST":
        for r in roles:
            for nt, _ in notification_types:
                key = f"{r}_{nt}"
                is_enabled = key in request.POST
                NotificationPreference.objects.update_or_create(
                    company=company,
                    role=r,
                    notification_type=nt,
                    defaults={"push_enabled": is_enabled}
                )
        messages.success(request, "تم حفظ إعدادات الإشعارات")
        return redirect("companies:notification_settings")

    context = {
        "roles": roles,
        "role_labels": role_labels,
        "notification_types": notification_types,
        "prefs_map": prefs_map,
        "page_title": "إعدادات الإشعارات",
    }
    return render(request, "companies/notification_settings.html", context)
'''

if "def notification_settings_view" not in comp_views:
    comp_views += notif_settings_view
    write_file(comp_views_path, comp_views)
    print("  ✅ تم إضافة notification settings view")
else:
    print("  ℹ️  notification settings view موجود")


# ════════════════════════════════════════════════════════════
# 7) companies/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/urls.py...")

comp_urls_path = os.path.join(BASE_DIR, "companies", "urls.py")
comp_urls = read_file(comp_urls_path)

if "notification-settings" not in comp_urls:
    comp_urls = comp_urls.rstrip()
    if comp_urls.endswith("]"):
        comp_urls = comp_urls[:-1]
        comp_urls += """
    path('notification-settings/', views.notification_settings_view, name='notification_settings'),
]
"""
        write_file(comp_urls_path, comp_urls)
        print("  ✅ تم إضافة URL")
else:
    print("  ℹ️  URL موجود")


# ════════════════════════════════════════════════════════════
# 8) Template
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء notification_settings.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "companies", "notification_settings.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}إعدادات الإشعارات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-bell-fill me-2" style="color:#06B6D4;"></i>
      إعدادات Push Notifications
    </h4>
    <p class="text-muted mb-0">
      حدد مين يوصله إشعار Push لكل نوع حدث
    </p>
  </div>

  <form method="post">
    {% csrf_token %}

    <div class="card border-0 shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead style="background:#f8fafc;">
            <tr>
              <th class="px-4 py-3">نوع الإشعار</th>
              {% for r in roles %}
              <th class="text-center py-3">{{ role_labels|get_item:r }}</th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for nt, nt_label in notification_types %}
            <tr>
              <td class="px-4 fw-semibold small">{{ nt_label }}</td>
              {% for r in roles %}
              <td class="text-center">
                <div class="form-check d-flex justify-content-center">
                  <input class="form-check-input"
                         type="checkbox"
                         name="{{ r }}_{{ nt }}"
                         id="{{ r }}_{{ nt }}"
                         {% with key=r|add:"_"|add:nt %}
                           {% if key in prefs_map %}
                             {% if prefs_map|get_item:key %}checked{% endif %}
                           {% else %}
                             checked
                           {% endif %}
                         {% endwith %}
                         style="width:1.2rem;height:1.2rem;">
                </div>
              </td>
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-4">
      <button type="submit" class="btn text-white px-5"
              style="background:#06B6D4; border-radius:10px;">
        <i class="bi bi-check-lg me-2"></i>
        حفظ الإعدادات
      </button>
    </div>
  </form>

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 9) Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "companies:notification_settings" not in sidebar:
    target = """      <a href="{% url 'companies:approval_flows' %}"
         class="nav-link {% if 'approval-flows' in request.path %}active{% endif %}">
        <i class="bi bi-diagram-2"></i><span>مسارات الموافقة</span>
      </a>"""

    replacement = target + """
      <a href="{% url 'companies:notification_settings' %}"
         class="nav-link {% if 'notification-settings' in request.path %}active{% endif %}">
        <i class="bi bi-bell-fill"></i><span>إعدادات الإشعارات</span>
      </a>"""

    if target in sidebar:
        sidebar = sidebar.replace(target, replacement)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة رابط في الـ Sidebar")
    else:
        print("  ℹ️  لم أجد مكان الإدراج")
else:
    print("  ℹ️  رابط موجود")


# ════════════════════════════════════════════════════════════
# 10) Service Worker update — push handler
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث sw.js...")

sw_path = os.path.join(BASE_DIR, "static", "sw.js")
sw = read_file(sw_path)

if "showNotification" not in sw:
    push_handler = """
// ── Push Handler ─────────────────────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;

  let data = {};
  try {
    data = event.data.json();
  } catch(e) {
    data = { title: 'MotionHR', body: event.data.text() };
  }

  const title = data.title || 'MotionHR';
  const options = {
    body: data.body || '',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    dir: 'rtl',
    lang: 'ar',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/dashboard/' },
    actions: [
      { action: 'open', title: 'فتح' },
      { action: 'close', title: 'إغلاق' },
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'close') return;

  const url = event.notification.data?.url || '/dashboard/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      for (const client of windowClients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
"""
    with open(sw_path, "a", encoding="utf-8") as f:
        f.write(push_handler)
    print("  ✅ تم تحديث sw.js")
else:
    print("  ℹ️  sw.js محدث بالفعل")


# ════════════════════════════════════════════════════════════
# 11) Seed default preferences
# ════════════════════════════════════════════════════════════
print("\n🌱 Seed default preferences...")

from companies.models import Company, NotificationPreference

defaults = [
    # employee
    ("employee", "request_approved", True),
    ("employee", "request_rejected", True),
    ("employee", "late_warning", True),
    ("employee", "deduction_notice", True),
    ("employee", "charter_reminder", True),
    ("employee", "general_notice", True),
    # manager
    ("manager", "new_request_to_approve", True),
    ("manager", "late_threshold", True),
    ("manager", "stealth_alert", True),
    ("manager", "general_notice", True),
    # hr
    ("hr_manager", "new_request_to_approve", True),
    ("hr_manager", "late_threshold", True),
    ("hr_manager", "stealth_alert", True),
    ("hr_manager", "request_approved", True),
    ("hr_manager", "deduction_notice", True),
    ("hr_manager", "general_notice", True),
    # company_admin
    ("company_admin", "subscription_expiry", True),
    ("company_admin", "stealth_alert", True),
    ("company_admin", "general_notice", True),
    ("company_admin", "new_request_to_approve", True),
]

for company in Company.objects.all():
    for role, ntype, enabled in defaults:
        NotificationPreference.objects.get_or_create(
            company=company,
            role=role,
            notification_type=ntype,
            defaults={"push_enabled": enabled}
        )

print("  ✅ تم إنشاء إعدادات افتراضية")

print("\n" + "=" * 60)
print("  ✅ Patch 48b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ NotificationPreference model + Migration
  2. ✅ send_push_to_user helper (core/push_helper.py)
  3. ✅ ربط Push بـ EmployeeNotification.save
  4. ✅ notification_settings_view
  5. ✅ notification_settings.html
  6. ✅ Sidebar link
  7. ✅ sw.js Push handler
  8. ✅ Seed default preferences

في الإنتاج:
  pip install pywebpush
  ولّد VAPID keys حقيقية
  وحدّث settings.py

جرب:
  /companies/notification-settings/
""")#!/usr/bin/env python3
"""
Patch 48b: NotificationPreference + Send Push Logic
=====================================================
1) NotificationPreference model
2) send_push_to_user helper
3) ربط Push بـ EmployeeNotification
4) صفحة إعدادات الإشعارات
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


def get_last_migration(app_dir):
    migrations_dir = os.path.join(BASE_DIR, app_dir, "migrations")
    existing = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith(".py") and f != "__init__.py"
    ])
    if existing:
        last = existing[-1].replace(".py", "")
        last_num = int(last.split("_")[0])
        return last, last_num
    return "0001_initial", 1


print("=" * 60)
print("  Patch 48b: NotificationPreference + Send Logic")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) companies/models.py — NotificationPreference
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة NotificationPreference model...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

notif_pref_model = '''

class NotificationPreference(models.Model):
    """إعدادات إشعارات Push لكل دور في الشركة"""

    ROLE_CHOICES = [
        ("employee", "موظف"),
        ("manager", "مدير"),
        ("hr_manager", "مدير HR"),
        ("company_admin", "صاحب الشركة"),
    ]

    NOTIFICATION_TYPES = [
        ("request_approved", "تمت الموافقة على الطلب"),
        ("request_rejected", "تم رفض الطلب"),
        ("new_request_to_approve", "طلب جديد يحتاج موافقة"),
        ("late_warning", "تحذير تأخير"),
        ("late_threshold", "تجاوز حد التأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("stealth_alert", "تنبيه تتبع صامت"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("subscription_expiry", "انتهاء الاشتراك"),
        ("general_notice", "إشعار عام"),
    ]

    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name="الشركة"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="الدور"
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name="نوع الإشعار"
    )
    push_enabled = models.BooleanField(
        default=True,
        verbose_name="إرسال Push"
    )

    class Meta:
        verbose_name = "إعداد إشعار"
        verbose_name_plural = "إعدادات الإشعارات"
        unique_together = [["company", "role", "notification_type"]]

    def __str__(self):
        return f"{self.company} - {self.role} - {self.notification_type}"

    @classmethod
    def is_push_enabled(cls, company, role, notification_type):
        """هل Push مفعّل لهذا الدور وهذا النوع؟"""
        try:
            pref = cls.objects.get(
                company=company,
                role=role,
                notification_type=notification_type
            )
            return pref.push_enabled
        except cls.DoesNotExist:
            return True  # افتراضي: مفعّل
        except Exception:
            return False
'''

if "class NotificationPreference" not in comp_models:
    comp_models += notif_pref_model
    write_file(comp_models_path, comp_models)
    print("  ✅ تم إضافة NotificationPreference")
else:
    print("  ℹ️  NotificationPreference موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

last, num = get_last_migration("companies")
new_num = str(num + 1).zfill(4)

create_file(
    os.path.join(BASE_DIR, "companies", "migrations",
                 f"{new_num}_add_notification_preference.py"),
    f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "{last}"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False)),
                ("role", models.CharField(max_length=20, verbose_name="الدور",
                    choices=[
                        ("employee","موظف"),("manager","مدير"),
                        ("hr_manager","مدير HR"),("company_admin","صاحب الشركة"),
                    ]
                )),
                ("notification_type", models.CharField(max_length=30,
                    verbose_name="نوع الإشعار",
                    choices=[
                        ("request_approved","تمت الموافقة على الطلب"),
                        ("request_rejected","تم رفض الطلب"),
                        ("new_request_to_approve","طلب جديد يحتاج موافقة"),
                        ("late_warning","تحذير تأخير"),
                        ("late_threshold","تجاوز حد التأخير"),
                        ("deduction_notice","إشعار خصم"),
                        ("stealth_alert","تنبيه تتبع صامت"),
                        ("charter_reminder","تذكير بالميثاق"),
                        ("subscription_expiry","انتهاء الاشتراك"),
                        ("general_notice","إشعار عام"),
                    ]
                )),
                ("push_enabled", models.BooleanField(default=True,
                                                      verbose_name="إرسال Push")),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notification_preferences",
                    to="companies.company",
                    verbose_name="الشركة"
                )),
            ],
            options={{
                "verbose_name": "إعداد إشعار",
                "verbose_name_plural": "إعدادات الإشعارات",
            }},
        ),
        migrations.AlterUniqueTogether(
            name="notificationpreference",
            unique_together={{("company", "role", "notification_type")}},
        ),
    ]
'''
)

call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 3) send_push_to_user helper
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء push_helper.py...")

create_file(
    os.path.join(BASE_DIR, "core", "push_helper.py"),
    '''"""
push_helper.py
إرسال Web Push Notifications
"""

from django.conf import settings


def send_push_to_user(user, title, body, url="/dashboard/",
                      notification_type="general_notice"):
    """
    إرسال Push Notification لمستخدم معين
    - يبص على PushSubscription بتاعته
    - يبص على NotificationPreference
    - لو مفعّل يبعت

    في الإنتاج:
    pip install pywebpush
    """
    try:
        from accounts.models import PushSubscription
        from companies.models import NotificationPreference

        subs = PushSubscription.objects.filter(
            user=user,
            is_active=True
        )

        if not subs.exists():
            return 0

        # فحص الـ preference
        role = getattr(user, "role", "employee")
        company = getattr(user, "company", None)

        if company:
            push_allowed = NotificationPreference.is_push_enabled(
                company, role, notification_type
            )
            if not push_allowed:
                return 0

        vapid_public = getattr(settings, "VAPID_PUBLIC_KEY", "")
        vapid_private = getattr(settings, "VAPID_PRIVATE_KEY", "")
        vapid_email = getattr(settings, "VAPID_ADMIN_EMAIL", "")

        if not vapid_public or "Dummy" in vapid_public:
            # Development mode: log only
            print(f"[Push DEV] To: {user.username} | {title} | {body}")
            return 1

        sent = 0
        import json

        try:
            from pywebpush import webpush, WebPushException

            payload = json.dumps({
                "title": title,
                "body": body,
                "url": url,
                "icon": "/static/icons/icon-192x192.png",
                "badge": "/static/icons/icon-72x72.png",
            })

            for sub in subs:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub.endpoint,
                            "keys": {
                                "p256dh": sub.p256dh,
                                "auth": sub.auth,
                            }
                        },
                        data=payload,
                        vapid_private_key=vapid_private,
                        vapid_claims={
                            "sub": f"mailto:{vapid_email}",
                        }
                    )
                    sent += 1
                except WebPushException as e:
                    if "410" in str(e) or "404" in str(e):
                        sub.is_active = False
                        sub.save(update_fields=["is_active"])
                except Exception:
                    pass

        except ImportError:
            # pywebpush مش مثبت
            print(f"[Push] pywebpush not installed. To: {user.username} | {title}")
            sent = 1

        return sent

    except Exception as e:
        print(f"[Push Error] {e}")
        return 0


def send_push_to_company_role(company, role, title, body,
                               url="/dashboard/",
                               notification_type="general_notice"):
    """
    إرسال Push لكل المستخدمين في شركة معينة بدور معين
    """
    try:
        from accounts.models import User

        users = User.objects.filter(
            company=company,
            role=role,
            is_active=True
        )

        total = 0
        for user in users:
            total += send_push_to_user(
                user, title, body, url, notification_type
            )
        return total
    except Exception:
        return 0
'''
)


# ════════════════════════════════════════════════════════════
# 4) ربط Push بـ EmployeeNotification
# ════════════════════════════════════════════════════════════
print("\n🔧 ربط Push بـ EmployeeNotification...")

acc_views_path = os.path.join(BASE_DIR, "accounts", "views.py")
acc_views = read_file(acc_views_path)

# نضيف push في notifications_view لما يتعمل notification جديد
push_trigger = '''

# ════════════════════════════════════════════════════════════
# Push Trigger — بيتشغل لما EmployeeNotification يتنشأ
# ════════════════════════════════════════════════════════════
def trigger_push_for_employee_notification(notification_obj):
    """
    بعد ما EmployeeNotification يتنشأ → ابعت Push
    """
    try:
        from core.push_helper import send_push_to_user
        from employees.models import Employee

        employee = notification_obj.employee
        if not employee.user:
            return

        type_map = {
            "late_warning": "late_warning",
            "deduction_notice": "deduction_notice",
            "request_update": "request_approved",
            "general_notice": "general_notice",
            "policy_reminder": "general_notice",
            "charter_reminder": "charter_reminder",
        }

        notif_type = type_map.get(
            notification_obj.notification_type,
            "general_notice"
        )

        send_push_to_user(
            user=employee.user,
            title=notification_obj.title,
            body=notification_obj.message[:100] if notification_obj.message else "",
            url="/accounts/notifications/",
            notification_type=notif_type,
        )
    except Exception:
        pass
'''

if "trigger_push_for_employee_notification" not in acc_views:
    acc_views += push_trigger
    write_file(acc_views_path, acc_views)
    print("  ✅ تم إضافة Push trigger")
else:
    print("  ℹ️  Push trigger موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 5) ربط trigger بـ EmployeeNotification.save
# ════════════════════════════════════════════════════════════
print("\n🔧 ربط push trigger بـ EmployeeNotification...")

acc_models_path = os.path.join(BASE_DIR, "accounts", "models.py")
acc_models = read_file(acc_models_path)

if "def save" not in acc_models.split("class EmployeeNotification")[1].split("class ")[0]:
    # نضيف override save في EmployeeNotification
    old_meta = '''    class Meta:
        verbose_name = "إشعار موظف"
        verbose_name_plural = "إشعارات الموظفين"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"'''

    new_meta = '''    class Meta:
        verbose_name = "إشعار موظف"
        verbose_name_plural = "إشعارات الموظفين"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            try:
                from accounts.views import trigger_push_for_employee_notification
                trigger_push_for_employee_notification(self)
            except Exception:
                pass'''

    if old_meta in acc_models:
        acc_models = acc_models.replace(old_meta, new_meta)
        write_file(acc_models_path, acc_models)
        print("  ✅ تم ربط Push بـ EmployeeNotification.save")
    else:
        print("  ℹ️  ربط Push — النص مختلف أو موجود بالفعل")
else:
    print("  ℹ️  Push save override موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 6) companies/views.py — notification settings page
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة notification settings view...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

notif_settings_view = '''

# ════════════════════════════════════════════════════════════
# Notification Settings
# ════════════════════════════════════════════════════════════

@login_required
def notification_settings_view(request):
    """إعدادات الإشعارات للشركة"""
    from companies.models import NotificationPreference

    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية الوصول")
        return redirect("dashboard")

    company = request.user.company

    roles = ["employee", "manager", "hr_manager", "company_admin"]
    role_labels = {
        "employee": "موظف",
        "manager": "مدير",
        "hr_manager": "مدير HR",
        "company_admin": "صاحب الشركة",
    }

    notification_types = [
        ("request_approved", "تمت الموافقة على الطلب"),
        ("request_rejected", "تم رفض الطلب"),
        ("new_request_to_approve", "طلب جديد يحتاج موافقة"),
        ("late_warning", "تحذير تأخير"),
        ("late_threshold", "تجاوز حد التأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("stealth_alert", "تنبيه تتبع صامت"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("subscription_expiry", "انتهاء الاشتراك"),
        ("general_notice", "إشعار عام"),
    ]

    # بناء matrix
    prefs_map = {}
    existing = NotificationPreference.objects.filter(company=company)
    for p in existing:
        prefs_map[f"{p.role}_{p.notification_type}"] = p.push_enabled

    if request.method == "POST":
        for r in roles:
            for nt, _ in notification_types:
                key = f"{r}_{nt}"
                is_enabled = key in request.POST
                NotificationPreference.objects.update_or_create(
                    company=company,
                    role=r,
                    notification_type=nt,
                    defaults={"push_enabled": is_enabled}
                )
        messages.success(request, "تم حفظ إعدادات الإشعارات")
        return redirect("companies:notification_settings")

    context = {
        "roles": roles,
        "role_labels": role_labels,
        "notification_types": notification_types,
        "prefs_map": prefs_map,
        "page_title": "إعدادات الإشعارات",
    }
    return render(request, "companies/notification_settings.html", context)
'''

if "def notification_settings_view" not in comp_views:
    comp_views += notif_settings_view
    write_file(comp_views_path, comp_views)
    print("  ✅ تم إضافة notification settings view")
else:
    print("  ℹ️  notification settings view موجود")


# ════════════════════════════════════════════════════════════
# 7) companies/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/urls.py...")

comp_urls_path = os.path.join(BASE_DIR, "companies", "urls.py")
comp_urls = read_file(comp_urls_path)

if "notification-settings" not in comp_urls:
    comp_urls = comp_urls.rstrip()
    if comp_urls.endswith("]"):
        comp_urls = comp_urls[:-1]
        comp_urls += """
    path('notification-settings/', views.notification_settings_view, name='notification_settings'),
]
"""
        write_file(comp_urls_path, comp_urls)
        print("  ✅ تم إضافة URL")
else:
    print("  ℹ️  URL موجود")


# ════════════════════════════════════════════════════════════
# 8) Template
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء notification_settings.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "companies", "notification_settings.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}إعدادات الإشعارات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="mb-4">
    <h4 class="fw-bold mb-1">
      <i class="bi bi-bell-fill me-2" style="color:#06B6D4;"></i>
      إعدادات Push Notifications
    </h4>
    <p class="text-muted mb-0">
      حدد مين يوصله إشعار Push لكل نوع حدث
    </p>
  </div>

  <form method="post">
    {% csrf_token %}

    <div class="card border-0 shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead style="background:#f8fafc;">
            <tr>
              <th class="px-4 py-3">نوع الإشعار</th>
              {% for r in roles %}
              <th class="text-center py-3">{{ role_labels|get_item:r }}</th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for nt, nt_label in notification_types %}
            <tr>
              <td class="px-4 fw-semibold small">{{ nt_label }}</td>
              {% for r in roles %}
              <td class="text-center">
                <div class="form-check d-flex justify-content-center">
                  <input class="form-check-input"
                         type="checkbox"
                         name="{{ r }}_{{ nt }}"
                         id="{{ r }}_{{ nt }}"
                         {% with key=r|add:"_"|add:nt %}
                           {% if key in prefs_map %}
                             {% if prefs_map|get_item:key %}checked{% endif %}
                           {% else %}
                             checked
                           {% endif %}
                         {% endwith %}
                         style="width:1.2rem;height:1.2rem;">
                </div>
              </td>
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-4">
      <button type="submit" class="btn text-white px-5"
              style="background:#06B6D4; border-radius:10px;">
        <i class="bi bi-check-lg me-2"></i>
        حفظ الإعدادات
      </button>
    </div>
  </form>

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 9) Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "companies:notification_settings" not in sidebar:
    target = """      <a href="{% url 'companies:approval_flows' %}"
         class="nav-link {% if 'approval-flows' in request.path %}active{% endif %}">
        <i class="bi bi-diagram-2"></i><span>مسارات الموافقة</span>
      </a>"""

    replacement = target + """
      <a href="{% url 'companies:notification_settings' %}"
         class="nav-link {% if 'notification-settings' in request.path %}active{% endif %}">
        <i class="bi bi-bell-fill"></i><span>إعدادات الإشعارات</span>
      </a>"""

    if target in sidebar:
        sidebar = sidebar.replace(target, replacement)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة رابط في الـ Sidebar")
    else:
        print("  ℹ️  لم أجد مكان الإدراج")
else:
    print("  ℹ️  رابط موجود")


# ════════════════════════════════════════════════════════════
# 10) Service Worker update — push handler
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث sw.js...")

sw_path = os.path.join(BASE_DIR, "static", "sw.js")
sw = read_file(sw_path)

if "showNotification" not in sw:
    push_handler = """
// ── Push Handler ─────────────────────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;

  let data = {};
  try {
    data = event.data.json();
  } catch(e) {
    data = { title: 'MotionHR', body: event.data.text() };
  }

  const title = data.title || 'MotionHR';
  const options = {
    body: data.body || '',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    dir: 'rtl',
    lang: 'ar',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/dashboard/' },
    actions: [
      { action: 'open', title: 'فتح' },
      { action: 'close', title: 'إغلاق' },
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'close') return;

  const url = event.notification.data?.url || '/dashboard/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      for (const client of windowClients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
"""
    with open(sw_path, "a", encoding="utf-8") as f:
        f.write(push_handler)
    print("  ✅ تم تحديث sw.js")
else:
    print("  ℹ️  sw.js محدث بالفعل")


# ════════════════════════════════════════════════════════════
# 11) Seed default preferences
# ════════════════════════════════════════════════════════════
print("\n🌱 Seed default preferences...")

from companies.models import Company, NotificationPreference

defaults = [
    # employee
    ("employee", "request_approved", True),
    ("employee", "request_rejected", True),
    ("employee", "late_warning", True),
    ("employee", "deduction_notice", True),
    ("employee", "charter_reminder", True),
    ("employee", "general_notice", True),
    # manager
    ("manager", "new_request_to_approve", True),
    ("manager", "late_threshold", True),
    ("manager", "stealth_alert", True),
    ("manager", "general_notice", True),
    # hr
    ("hr_manager", "new_request_to_approve", True),
    ("hr_manager", "late_threshold", True),
    ("hr_manager", "stealth_alert", True),
    ("hr_manager", "request_approved", True),
    ("hr_manager", "deduction_notice", True),
    ("hr_manager", "general_notice", True),
    # company_admin
    ("company_admin", "subscription_expiry", True),
    ("company_admin", "stealth_alert", True),
    ("company_admin", "general_notice", True),
    ("company_admin", "new_request_to_approve", True),
]

for company in Company.objects.all():
    for role, ntype, enabled in defaults:
        NotificationPreference.objects.get_or_create(
            company=company,
            role=role,
            notification_type=ntype,
            defaults={"push_enabled": enabled}
        )

print("  ✅ تم إنشاء إعدادات افتراضية")

print("\n" + "=" * 60)
print("  ✅ Patch 48b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ NotificationPreference model + Migration
  2. ✅ send_push_to_user helper (core/push_helper.py)
  3. ✅ ربط Push بـ EmployeeNotification.save
  4. ✅ notification_settings_view
  5. ✅ notification_settings.html
  6. ✅ Sidebar link
  7. ✅ sw.js Push handler
  8. ✅ Seed default preferences

في الإنتاج:
  pip install pywebpush
  ولّد VAPID keys حقيقية
  وحدّث settings.py

جرب:
  /companies/notification-settings/
""")