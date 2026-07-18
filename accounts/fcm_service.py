"""
FCM Notification Service - خدمة إرسال إشعارات Firebase
"""
import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings


# تهيئة Firebase Admin (مرة واحدة بس)
FIREBASE_KEY_PATH = os.path.join(settings.BASE_DIR, 'firebase-key.json')


def init_firebase():
    """تهيئة Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            print(f"❌ Firebase init error: {e}")
            return False
    return True


def _log_notification(user, title, body, data=None):
    """تسجيل الإشعار في قاعدة البيانات"""
    try:
        from accounts.fcm_models import NotificationLog
        notification_type = 'general'
        if isinstance(data, dict) and data.get('type'):
            notification_type = str(data.get('type'))
        NotificationLog.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            data=data or {},
            is_read=False,
        )
        return True
    except Exception as e:
        print(f"❌ Notification log error for {user.username}: {e}")
        return False


def send_notification_to_user(user, title, body, data=None):
    """إرسال إشعار لمستخدم واحد على كل الأجهزة المسجلة"""
    from accounts.fcm_models import FCMDeviceToken

    # سجّل الإشعار في قاعدة البيانات حتى لو مفيش token
    _log_notification(user, title, body, data)

    if not init_firebase():
        return {"success": False, "sent": 0, "failed": 0, "errors": ["Firebase init failed"]}

    tokens = FCMDeviceToken.objects.filter(
        user=user,
        is_active=True
    ).exclude(fcm_token='test123')

    if not tokens.exists():
        return {"success": False, "sent": 0, "failed": 0, "errors": ["No FCM tokens"]}

    sent_count = 0
    failed_count = 0
    errors = []
    invalid_tokens = []

    for token_obj in tokens:
        try:
            data_dict = {}
            if data:
                data_dict = {str(k): str(v) for k, v in data.items()}

            localized_title = title
            localized_body = body
            if getattr(token_obj, 'preferred_language', 'ar') == 'en':
                if title_en:
                    localized_title = title_en
                if body_en:
                    localized_body = body_en

            message = messaging.Message(
                notification=messaging.Notification(
                    title=localized_title,
                    body=localized_body,
                ),
                data=data_dict,
                token=token_obj.fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        default_sound=True,
                        default_vibrate_timings=True,
                    ),
                ),
            )

            response = messaging.send(message)
            sent_count += 1
            print(f"✅ Sent to {user.username}: {response}")

        except messaging.UnregisteredError:
            invalid_tokens.append(token_obj.id)
            failed_count += 1
            errors.append("Invalid token (deleted)")

        except Exception as e:
            failed_count += 1
            errors.append(str(e))
            print(f"❌ Failed to send to {user.username}: {e}")

    if invalid_tokens:
        FCMDeviceToken.objects.filter(id__in=invalid_tokens).delete()

    return {
        "success": sent_count > 0,
        "sent": sent_count,
        "failed": failed_count,
        "errors": errors,
    }


def send_notification_to_managers(company, title, body, data=None):
    """إرسال إشعار لكل المديرين في شركة معينة"""
    from accounts.models import User

    managers = User.objects.filter(
        company=company,
        role__in=['company_admin', 'hr_manager', 'manager', 'super_admin']
    )

    total_sent = 0
    for manager in managers:
        result = send_notification_to_user(manager, title, body, data)
        total_sent += result['sent']

    return {"success": total_sent > 0, "sent": total_sent}


# =========================================
# دوال جاهزة للأحداث المختلفة
# =========================================

def notify_request_approved(user, request_type, request_title='', request_id=None):
    """إشعار موافقة على طلب"""
    data = {
        'type': 'request_approved',
        'request_type': request_type,
        'screen': 'my_requests',
    }
    if request_id:
        data['request_id'] = request_id
    return send_notification_to_user(
        user=user,
        title='✅ تم قبول طلبك',
        body=f'تم الموافقة على {request_type}: {request_title}',
        data=data,
    )


def notify_request_rejected(user, request_type, request_title='', reason='', request_id=None):
    """إشعار رفض طلب"""
    body = f'تم رفض {request_type}: {request_title}'
    if reason:
        body += f'\nالسبب: {reason}'
    data = {
        'type': 'request_rejected',
        'request_type': request_type,
        'screen': 'my_requests',
    }
    if request_id:
        data['request_id'] = request_id
    return send_notification_to_user(
        user=user,
        title='❌ تم رفض طلبك',
        body=body,
        data=data,
    )


def notify_leave_approved(user, leave_type, start_date, end_date, leave_id=None):
    """إشعار موافقة على إجازة"""
    data = {
        'type': 'leave_approved',
        'screen': 'my_leaves',
    }
    if leave_id:
        data['leave_id'] = leave_id
    return send_notification_to_user(
        user=user,
        title='✅ تم قبول إجازتك',
        body=f'تم الموافقة على {leave_type} من {start_date} إلى {end_date}',
        data=data,
    )


def notify_leave_rejected(user, leave_type, reason='', leave_id=None):
    """إشعار رفض إجازة"""
    body = f'تم رفض إجازة {leave_type}'
    if reason:
        body += f'\nالسبب: {reason}'
    data = {
        'type': 'leave_rejected',
        'screen': 'my_leaves',
    }
    if leave_id:
        data['leave_id'] = leave_id
    return send_notification_to_user(
        user=user,
        title='❌ تم رفض إجازتك',
        body=body,
        data=data,
    )


def notify_manager_new_request(company, employee_name, request_type, request_id=None):
    """إشعار للمدير - طلب جديد"""
    data = {
        'type': 'new_request',
        'screen': 'manager_pending',
    }
    if request_id:
        data['request_id'] = request_id
    return send_notification_to_managers(
        company=company,
        title='📩 طلب جديد',
        body=f'الموظف {employee_name} قدم طلب: {request_type}',
        data=data,
    )


def notify_manager_new_leave(company, employee_name, leave_type, leave_id=None):
    """إشعار للمدير - طلب إجازة جديد"""
    data = {
        'type': 'new_leave',
        'screen': 'manager_pending',
    }
    if leave_id:
        data['leave_id'] = leave_id
    return send_notification_to_managers(
        company=company,
        title='📩 طلب إجازة جديد',
        body=f'الموظف {employee_name} قدم طلب إجازة: {leave_type}',
        data=data,
    )


def notify_manager_out_of_geofence(company, employee_name, distance):
    """إشعار للمدير - موظف حاول حضور خارج النطاق"""
    return send_notification_to_managers(
        company=company,
        title='⚠️ محاولة حضور خارج النطاق',
        body=f'الموظف {employee_name} حاول تسجيل حضور من مسافة {distance}م',
        data={'type': 'geofence_violation'}
    )
def notify_employee_checkin(user, time_str, location=''):
    """إشعار للموظف عند تسجيل الحضور"""
    body = f'تم تسجيل حضورك الساعة {time_str}'
    if location:
        body += f' — {location}'
    send_notification_to_user(user, 'تسجيل الحضور ✅', body, data={
        'type': 'attendance',
        'action': 'checkin'
    })

def notify_employee_checkout(user, time_str, hours_worked=''):
    """إشعار للموظف عند تسجيل الانصراف"""
    body = f'تم تسجيل انصرافك الساعة {time_str}'
    if hours_worked:
        body += f' — عدد الساعات: {hours_worked}'
    send_notification_to_user(user, 'تسجيل الانصراف 👋', body, data={
        'type': 'attendance',
        'action': 'checkout'
    })

def notify_manager_checkin(company, employee_name, time_str):
    """إشعار للمدير عند تسجيل حضور موظف"""
    send_notification_to_managers(company, 
        'حضور موظف 📋',
        f'{employee_name} سجّل حضوره الساعة {time_str}',
        data={'type': 'manager_attendance', 'action': 'checkin'}
    )

def notify_manager_checkout(company, employee_name, time_str, hours_worked=''):
    """إشعار للمدير عند تسجيل انصراف موظف"""
    body = f'{employee_name} سجّل انصرافه الساعة {time_str}'
    if hours_worked:
        body += f' — {hours_worked} ساعة'
    send_notification_to_managers(company,
        'انصراف موظف 🏁',
        body,
        data={'type': 'manager_attendance', 'action': 'checkout'}
    )
