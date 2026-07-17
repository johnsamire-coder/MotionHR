import firebase_admin
from firebase_admin import credentials, messaging
from accounts.fcm_models import FCMDeviceToken, NotificationLog


def send_fcm_notification(user, title, body, data=None):
    key_path = "/var/www/motionhr/firebase-key.json"

    if not firebase_admin._apps:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)

    # سجل الإشعار دائمًا عشان يظهر في شاشة الإشعارات والـ Badge
    try:
        NotificationLog.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=(data or {}).get('type', 'general'),
        )
    except Exception as e:
        print(f"NotificationLog Error: {e}")

    tokens = list(
        FCMDeviceToken.objects.filter(user=user).values_list('fcm_token', flat=True)
    )

    if not tokens:
        return False

    messages = [
        messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            data=data or {}
        )
        for token in tokens
    ]

    try:
        messaging.send_each(messages)
        return True
    except Exception as e:
        print(f"FCM Error: {e}")
        return False


def notify_managers(title, body, data=None, company=None):
    from accounts.models import User

    managers = User.objects.filter(role__in=['super_admin', 'admin', 'company_admin', 'hr_manager', 'manager'], is_active=True)

    if company is not None:
        try:
            managers = managers.filter(company=company)
        except Exception:
            pass

    for manager in managers:
        send_fcm_notification(manager, title, body, data)


def notify_employee_checkin(user, time_str, location=''):
    body = f'تم تسجيل حضورك الساعة {time_str}'
    if location:
        body += f' — {location}'
    send_fcm_notification(user, 'تسجيل الحضور ✅', body, data={
        'type': 'attendance',
        'action': 'checkin'
    })


def notify_employee_checkout(user, time_str, hours_worked=''):
    body = f'تم تسجيل انصرافك الساعة {time_str}'
    if hours_worked:
        body += f' — عدد الساعات: {hours_worked}'
    send_fcm_notification(user, 'تسجيل الانصراف 👋', body, data={
        'type': 'attendance',
        'action': 'checkout'
    })


def notify_manager_checkin(company, employee_name, time_str):
    notify_managers(
        'حضور موظف 📋',
        f'{employee_name} سجّل حضوره الساعة {time_str}',
        data={'type': 'manager_attendance', 'action': 'checkin'},
        company=company
    )


def notify_manager_checkout(company, employee_name, time_str, hours_worked=''):
    body = f'{employee_name} سجّل انصرافه الساعة {time_str}'
    if hours_worked:
        body += f' — {hours_worked} ساعة'
    notify_managers(
        'انصراف موظف 🏁',
        body,
        data={'type': 'manager_attendance', 'action': 'checkout'},
        company=company
    )
