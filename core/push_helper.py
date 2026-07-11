"""
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
