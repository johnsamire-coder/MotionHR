#!/usr/bin/env python3
"""
Patch 48a: Push Notification Foundation
========================================
1) VAPID keys generation
2) PushSubscription model
3) subscribe/unsubscribe API
4) JS registration in dashboard_base
5) Migration
"""

import os
import sys
import json
import base64

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
print("  Patch 48a: Push Notification Foundation")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) Generate VAPID Keys (simple approach without pywebpush)
# ════════════════════════════════════════════════════════════
print("\n🔧 VAPID Keys...")

settings_path = os.path.join(BASE_DIR, "motionhr", "settings.py")
settings = read_file(settings_path)

if "VAPID_PUBLIC_KEY" not in settings:
    # نستخدم placeholder keys دلوقتي
    # في الإنتاج هتحتاج تولدهم بـ pywebpush أو web-push
    vapid_block = """
# ─────────────────────────────────────────────
# Web Push VAPID Keys
# ─────────────────────────────────────────────
# في الإنتاج: ولّد مفاتيح حقيقية بـ:
# pip install pywebpush
# python -c "from pywebpush import webpush; from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print(v.public_key); print(v.private_key)"
VAPID_PUBLIC_KEY = "BDummyKeyForDevelopment_ReplaceInProduction_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
VAPID_PRIVATE_KEY = "dummyprivatekey_replace_in_production"
VAPID_ADMIN_EMAIL = "admin@motionhr.com"
"""
    settings += vapid_block
    write_file(settings_path, settings)
    print("  ✅ تم إضافة VAPID Keys (placeholder)")
else:
    print("  ℹ️  VAPID Keys موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) PushSubscription model في accounts/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/models.py...")

models_path = os.path.join(BASE_DIR, "accounts", "models.py")
models_content = read_file(models_path)

push_model = '''

class PushSubscription(models.Model):
    """اشتراك Push Notification لكل جهاز"""

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name="المستخدم"
    )
    endpoint = models.TextField(
        verbose_name="Endpoint URL"
    )
    p256dh = models.TextField(
        verbose_name="P256DH Key"
    )
    auth = models.TextField(
        verbose_name="Auth Key"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="المتصفح"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "اشتراك Push"
        verbose_name_plural = "اشتراكات Push"
        unique_together = [["user", "endpoint"]]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."
'''

if "class PushSubscription" not in models_content:
    models_content += push_model
    write_file(models_path, models_content)
    print("  ✅ تم إضافة PushSubscription model")
else:
    print("  ℹ️  PushSubscription موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3) Manual Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

last, num = get_last_migration("accounts")
new_num = str(num + 1).zfill(4)

create_file(
    os.path.join(BASE_DIR, "accounts", "migrations", f"{new_num}_add_push_subscription.py"),
    f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "{last}"),
    ]

    operations = [
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("endpoint", models.TextField(verbose_name="Endpoint URL")),
                ("p256dh", models.TextField(verbose_name="P256DH Key")),
                ("auth", models.TextField(verbose_name="Auth Key")),
                ("user_agent", models.TextField(blank=True, verbose_name="المتصفح")),
                ("is_active", models.BooleanField(default=True, verbose_name="نشط")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="push_subscriptions",
                    to="accounts.user",
                    verbose_name="المستخدم"
                )),
            ],
            options={{
                "verbose_name": "اشتراك Push",
                "verbose_name_plural": "اشتراكات Push",
            }},
        ),
        migrations.AlterUniqueTogether(
            name="pushsubscription",
            unique_together={{("user", "endpoint")}},
        ),
    ]
'''
)

call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 4) Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 Admin...")

admin_path = os.path.join(BASE_DIR, "accounts", "admin.py")
admin_content = read_file(admin_path)

if "PushSubscription" not in admin_content:
    admin_content += '''

from .models import PushSubscription

@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "created_at"]
    list_filter = ["is_active"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل PushSubscription في Admin")


# ════════════════════════════════════════════════════════════
# 5) Subscribe / Unsubscribe API
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Push API views...")

acc_views_path = os.path.join(BASE_DIR, "accounts", "views.py")
acc_views = read_file(acc_views_path)

push_api = '''

# ════════════════════════════════════════════════════════════
# Push Subscription API
# ════════════════════════════════════════════════════════════

from django.views.decorators.http import require_POST as require_post_method
from django.http import JsonResponse
import json as json_lib


@login_required
@require_post_method
def push_subscribe(request):
    """اشتراك في Push Notifications"""
    try:
        from accounts.models import PushSubscription
        body = json_lib.loads(request.body)
        endpoint = body.get("endpoint", "")
        keys = body.get("keys", {})
        p256dh = keys.get("p256dh", "")
        auth = keys.get("auth", "")

        if not endpoint or not p256dh or not auth:
            return JsonResponse({"ok": False, "message": "بيانات ناقصة"})

        sub, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
                "is_active": True,
            }
        )
        return JsonResponse({"ok": True, "created": created})
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)})


@login_required
@require_post_method
def push_unsubscribe(request):
    """إلغاء اشتراك Push"""
    try:
        from accounts.models import PushSubscription
        body = json_lib.loads(request.body)
        endpoint = body.get("endpoint", "")

        PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).update(is_active=False)

        return JsonResponse({"ok": True})
    except Exception:
        return JsonResponse({"ok": False})
'''

if "def push_subscribe" not in acc_views:
    acc_views += push_api
    write_file(acc_views_path, acc_views)
    print("  ✅ تم إضافة Push API views")
else:
    print("  ℹ️  Push API views موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 6) URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/urls.py...")

urls_path = os.path.join(BASE_DIR, "accounts", "urls.py")
urls_content = read_file(urls_path)

if "push-subscribe" not in urls_content:
    urls_content = urls_content.rstrip()
    if urls_content.endswith("]"):
        urls_content = urls_content[:-1]
        urls_content += """
    path('push-subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push-unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),
]
"""
        write_file(urls_path, urls_content)
        print("  ✅ تم إضافة URLs")
else:
    print("  ℹ️  URLs موجودة")


# ════════════════════════════════════════════════════════════
# 7) JS في dashboard_base.html
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث dashboard_base.html...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "pushSubscribeBtn" not in sidebar:
    push_js = r"""
<!-- Push Notifications -->
<script>
(function() {
  const VAPID_KEY = "{{ VAPID_PUBLIC_KEY|default:'' }}";
  const SUBSCRIBE_URL = "{% url 'accounts:push_subscribe' %}";
  const CSRF = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "{{ csrf_token }}";

  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
  if (!VAPID_KEY || VAPID_KEY.includes("Dummy")) return;

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const raw = window.atob(base64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; ++i) arr[i] = raw.charCodeAt(i);
    return arr;
  }

  async function subscribePush() {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_KEY),
      });

      const subJSON = sub.toJSON();

      await fetch(SUBSCRIBE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF,
        },
        body: JSON.stringify({
          endpoint: subJSON.endpoint,
          keys: subJSON.keys,
        }),
      });

      console.log("[Push] Subscribed successfully");
    } catch (err) {
      console.warn("[Push] Failed:", err);
    }
  }

  // لو الإذن مش granted بعد
  if (Notification.permission === "default") {
    // نسأل بعد 5 ثواني من فتح الصفحة
    setTimeout(() => {
      Notification.requestPermission().then(perm => {
        if (perm === "granted") subscribePush();
      });
    }, 5000);
  } else if (Notification.permission === "granted") {
    subscribePush();
  }
})();
</script>
"""
    if "</body>" in sidebar:
        sidebar = sidebar.replace("</body>", push_js + "\n</body>")
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة Push JS")
    else:
        print("  ⚠️  لم أجد </body>")
else:
    print("  ℹ️  Push JS موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 8) VAPID_PUBLIC_KEY في context
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة VAPID_PUBLIC_KEY في context...")

processor_path = os.path.join(BASE_DIR, "core", "breadcrumb_processor.py")
processor = read_file(processor_path)

if "VAPID_PUBLIC_KEY" not in processor:
    vapid_context = '''

def vapid_key_processor(request):
    """يوفر VAPID_PUBLIC_KEY للـ templates"""
    from django.conf import settings
    return {
        "VAPID_PUBLIC_KEY": getattr(settings, "VAPID_PUBLIC_KEY", ""),
    }
'''
    processor += vapid_context
    write_file(processor_path, processor)
    print("  ✅ تم إضافة vapid_key_processor")

# إضافة في settings
settings = read_file(settings_path)
if "vapid_key_processor" not in settings:
    settings = settings.replace(
        "'core.breadcrumb_processor.breadcrumb_processor',",
        "'core.breadcrumb_processor.breadcrumb_processor',\n                'core.breadcrumb_processor.vapid_key_processor',"
    )
    write_file(settings_path, settings)
    print("  ✅ تم إضافة vapid_key_processor في settings")
else:
    print("  ℹ️  vapid_key_processor موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 48a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ VAPID Keys (placeholder)
  2. ✅ PushSubscription model + Migration
  3. ✅ Admin registration
  4. ✅ subscribe/unsubscribe API
  5. ✅ URLs
  6. ✅ JS registration في dashboard_base
  7. ✅ VAPID_PUBLIC_KEY في context

ملاحظة مهمة:
  حاليًا الـ VAPID keys = placeholder
  في الإنتاج لازم:
  pip install pywebpush py-vapid
  وتولّد مفاتيح حقيقية

الجاي:
  Patch 48b → NotificationPreference + Settings
  Patch 48c → Send Push Logic
""")#!/usr/bin/env python3
"""
Patch 48a: Push Notification Foundation
========================================
1) VAPID keys generation
2) PushSubscription model
3) subscribe/unsubscribe API
4) JS registration in dashboard_base
5) Migration
"""

import os
import sys
import json
import base64

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
print("  Patch 48a: Push Notification Foundation")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) Generate VAPID Keys (simple approach without pywebpush)
# ════════════════════════════════════════════════════════════
print("\n🔧 VAPID Keys...")

settings_path = os.path.join(BASE_DIR, "motionhr", "settings.py")
settings = read_file(settings_path)

if "VAPID_PUBLIC_KEY" not in settings:
    # نستخدم placeholder keys دلوقتي
    # في الإنتاج هتحتاج تولدهم بـ pywebpush أو web-push
    vapid_block = """
# ─────────────────────────────────────────────
# Web Push VAPID Keys
# ─────────────────────────────────────────────
# في الإنتاج: ولّد مفاتيح حقيقية بـ:
# pip install pywebpush
# python -c "from pywebpush import webpush; from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print(v.public_key); print(v.private_key)"
VAPID_PUBLIC_KEY = "BDummyKeyForDevelopment_ReplaceInProduction_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
VAPID_PRIVATE_KEY = "dummyprivatekey_replace_in_production"
VAPID_ADMIN_EMAIL = "admin@motionhr.com"
"""
    settings += vapid_block
    write_file(settings_path, settings)
    print("  ✅ تم إضافة VAPID Keys (placeholder)")
else:
    print("  ℹ️  VAPID Keys موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) PushSubscription model في accounts/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/models.py...")

models_path = os.path.join(BASE_DIR, "accounts", "models.py")
models_content = read_file(models_path)

push_model = '''

class PushSubscription(models.Model):
    """اشتراك Push Notification لكل جهاز"""

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name="المستخدم"
    )
    endpoint = models.TextField(
        verbose_name="Endpoint URL"
    )
    p256dh = models.TextField(
        verbose_name="P256DH Key"
    )
    auth = models.TextField(
        verbose_name="Auth Key"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="المتصفح"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "اشتراك Push"
        verbose_name_plural = "اشتراكات Push"
        unique_together = [["user", "endpoint"]]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."
'''

if "class PushSubscription" not in models_content:
    models_content += push_model
    write_file(models_path, models_content)
    print("  ✅ تم إضافة PushSubscription model")
else:
    print("  ℹ️  PushSubscription موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3) Manual Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

last, num = get_last_migration("accounts")
new_num = str(num + 1).zfill(4)

create_file(
    os.path.join(BASE_DIR, "accounts", "migrations", f"{new_num}_add_push_subscription.py"),
    f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "{last}"),
    ]

    operations = [
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("endpoint", models.TextField(verbose_name="Endpoint URL")),
                ("p256dh", models.TextField(verbose_name="P256DH Key")),
                ("auth", models.TextField(verbose_name="Auth Key")),
                ("user_agent", models.TextField(blank=True, verbose_name="المتصفح")),
                ("is_active", models.BooleanField(default=True, verbose_name="نشط")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="push_subscriptions",
                    to="accounts.user",
                    verbose_name="المستخدم"
                )),
            ],
            options={{
                "verbose_name": "اشتراك Push",
                "verbose_name_plural": "اشتراكات Push",
            }},
        ),
        migrations.AlterUniqueTogether(
            name="pushsubscription",
            unique_together={{("user", "endpoint")}},
        ),
    ]
'''
)

call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 4) Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 Admin...")

admin_path = os.path.join(BASE_DIR, "accounts", "admin.py")
admin_content = read_file(admin_path)

if "PushSubscription" not in admin_content:
    admin_content += '''

from .models import PushSubscription

@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "created_at"]
    list_filter = ["is_active"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل PushSubscription في Admin")


# ════════════════════════════════════════════════════════════
# 5) Subscribe / Unsubscribe API
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Push API views...")

acc_views_path = os.path.join(BASE_DIR, "accounts", "views.py")
acc_views = read_file(acc_views_path)

push_api = '''

# ════════════════════════════════════════════════════════════
# Push Subscription API
# ════════════════════════════════════════════════════════════

from django.views.decorators.http import require_POST as require_post_method
from django.http import JsonResponse
import json as json_lib


@login_required
@require_post_method
def push_subscribe(request):
    """اشتراك في Push Notifications"""
    try:
        from accounts.models import PushSubscription
        body = json_lib.loads(request.body)
        endpoint = body.get("endpoint", "")
        keys = body.get("keys", {})
        p256dh = keys.get("p256dh", "")
        auth = keys.get("auth", "")

        if not endpoint or not p256dh or not auth:
            return JsonResponse({"ok": False, "message": "بيانات ناقصة"})

        sub, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
                "is_active": True,
            }
        )
        return JsonResponse({"ok": True, "created": created})
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)})


@login_required
@require_post_method
def push_unsubscribe(request):
    """إلغاء اشتراك Push"""
    try:
        from accounts.models import PushSubscription
        body = json_lib.loads(request.body)
        endpoint = body.get("endpoint", "")

        PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).update(is_active=False)

        return JsonResponse({"ok": True})
    except Exception:
        return JsonResponse({"ok": False})
'''

if "def push_subscribe" not in acc_views:
    acc_views += push_api
    write_file(acc_views_path, acc_views)
    print("  ✅ تم إضافة Push API views")
else:
    print("  ℹ️  Push API views موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 6) URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/urls.py...")

urls_path = os.path.join(BASE_DIR, "accounts", "urls.py")
urls_content = read_file(urls_path)

if "push-subscribe" not in urls_content:
    urls_content = urls_content.rstrip()
    if urls_content.endswith("]"):
        urls_content = urls_content[:-1]
        urls_content += """
    path('push-subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push-unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),
]
"""
        write_file(urls_path, urls_content)
        print("  ✅ تم إضافة URLs")
else:
    print("  ℹ️  URLs موجودة")


# ════════════════════════════════════════════════════════════
# 7) JS في dashboard_base.html
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث dashboard_base.html...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "pushSubscribeBtn" not in sidebar:
    push_js = r"""
<!-- Push Notifications -->
<script>
(function() {
  const VAPID_KEY = "{{ VAPID_PUBLIC_KEY|default:'' }}";
  const SUBSCRIBE_URL = "{% url 'accounts:push_subscribe' %}";
  const CSRF = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "{{ csrf_token }}";

  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
  if (!VAPID_KEY || VAPID_KEY.includes("Dummy")) return;

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const raw = window.atob(base64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; ++i) arr[i] = raw.charCodeAt(i);
    return arr;
  }

  async function subscribePush() {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_KEY),
      });

      const subJSON = sub.toJSON();

      await fetch(SUBSCRIBE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF,
        },
        body: JSON.stringify({
          endpoint: subJSON.endpoint,
          keys: subJSON.keys,
        }),
      });

      console.log("[Push] Subscribed successfully");
    } catch (err) {
      console.warn("[Push] Failed:", err);
    }
  }

  // لو الإذن مش granted بعد
  if (Notification.permission === "default") {
    // نسأل بعد 5 ثواني من فتح الصفحة
    setTimeout(() => {
      Notification.requestPermission().then(perm => {
        if (perm === "granted") subscribePush();
      });
    }, 5000);
  } else if (Notification.permission === "granted") {
    subscribePush();
  }
})();
</script>
"""
    if "</body>" in sidebar:
        sidebar = sidebar.replace("</body>", push_js + "\n</body>")
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة Push JS")
    else:
        print("  ⚠️  لم أجد </body>")
else:
    print("  ℹ️  Push JS موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 8) VAPID_PUBLIC_KEY في context
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة VAPID_PUBLIC_KEY في context...")

processor_path = os.path.join(BASE_DIR, "core", "breadcrumb_processor.py")
processor = read_file(processor_path)

if "VAPID_PUBLIC_KEY" not in processor:
    vapid_context = '''

def vapid_key_processor(request):
    """يوفر VAPID_PUBLIC_KEY للـ templates"""
    from django.conf import settings
    return {
        "VAPID_PUBLIC_KEY": getattr(settings, "VAPID_PUBLIC_KEY", ""),
    }
'''
    processor += vapid_context
    write_file(processor_path, processor)
    print("  ✅ تم إضافة vapid_key_processor")

# إضافة في settings
settings = read_file(settings_path)
if "vapid_key_processor" not in settings:
    settings = settings.replace(
        "'core.breadcrumb_processor.breadcrumb_processor',",
        "'core.breadcrumb_processor.breadcrumb_processor',\n                'core.breadcrumb_processor.vapid_key_processor',"
    )
    write_file(settings_path, settings)
    print("  ✅ تم إضافة vapid_key_processor في settings")
else:
    print("  ℹ️  vapid_key_processor موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 48a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ VAPID Keys (placeholder)
  2. ✅ PushSubscription model + Migration
  3. ✅ Admin registration
  4. ✅ subscribe/unsubscribe API
  5. ✅ URLs
  6. ✅ JS registration في dashboard_base
  7. ✅ VAPID_PUBLIC_KEY في context

ملاحظة مهمة:
  حاليًا الـ VAPID keys = placeholder
  في الإنتاج لازم:
  pip install pywebpush py-vapid
  وتولّد مفاتيح حقيقية

الجاي:
  Patch 48b → NotificationPreference + Settings
  Patch 48c → Send Push Logic
""")