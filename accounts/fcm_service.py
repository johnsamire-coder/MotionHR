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
        NotificationLog._base_manager.create(
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


def _get_user_lang(user):
    """
    جلب لغة المستخدم.
    الأولوية: Employee.language → FCMDeviceToken.preferred_language → ar
    """
    try:
        from employees.models import Employee
        emp = Employee._base_manager.filter(user=user).first()
        if emp and getattr(emp, 'language', None):
            return emp.language
    except Exception:
        pass
    try:
        from accounts.fcm_models import FCMDeviceToken
        token = FCMDeviceToken.objects.filter(user=user, is_active=True).first()
        return getattr(token, 'preferred_language', 'ar') or 'ar'
    except Exception:
        pass
    return 'ar'


def send_notification_to_user(user, title, body, data=None, title_en=None, body_en=None):
    """إرسال إشعار لمستخدم واحد على كل الأجهزة المسجلة"""
    from accounts.fcm_models import FCMDeviceToken

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

            # لغة الإشعار = Employee.language (أولوية) أو preferred_language
            _user_lang = _get_user_lang(token_obj.user)
            if _user_lang == 'en':
                if title_en is not None:
                    localized_title = title_en
                if body_en is not None:
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


def send_notification_to_managers(company, title, body, data=None, title_en=None, body_en=None):
    """إرسال إشعار لكل المديرين في شركة معينة"""
    from accounts.models import User

    managers = User.objects.filter(
        company=company,
        role__in=['company_admin', 'hr_manager', 'manager', 'super_admin']
    )

    total_sent = 0
    for manager in managers:
        result = send_notification_to_user(
            manager, title, body, data,
            title_en=title_en, body_en=body_en
        )
        total_sent += result['sent']

    return {"success": total_sent > 0, "sent": total_sent}


# =========================================
# دوال جاهزة للأحداث المختلفة
# =========================================

def notify_request_approved(user, request_type, request_title='', request_id=None):
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
        body=f'تمت الموافقة على {request_type}: {request_title}',
        data=data,
        title_en='✅ Your request was approved',
        body_en=f'Your {request_type} request was approved: {request_title}',
    )


def notify_request_rejected(user, request_type, request_title='', reason='', request_id=None):
    body_ar = f'تم رفض {request_type}: {request_title}'
    body_en = f'Your {request_type} request was rejected: {request_title}'
    if reason:
        body_ar += f'\nالسبب: {reason}'
        body_en += f'\nReason: {reason}'

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
        body=body_ar,
        data=data,
        title_en='❌ Your request was rejected',
        body_en=body_en,
    )


def notify_leave_approved(user, leave_type, start_date, end_date, leave_id=None):
    data = {
        'type': 'leave_approved',
        'screen': 'my_leaves',
    }
    if leave_id:
        data['leave_id'] = leave_id

    return send_notification_to_user(
        user=user,
        title='✅ تم قبول إجازتك',
        body=f'تمت الموافقة على {leave_type} من {start_date} إلى {end_date}',
        data=data,
        title_en='✅ Your leave was approved',
        body_en=f'Your {leave_type} leave from {start_date} to {end_date} was approved',
    )


def notify_leave_rejected(user, leave_type, reason='', leave_id=None):
    body_ar = f'تم رفض إجازة {leave_type}'
    body_en = f'Your {leave_type} leave request was rejected'
    if reason:
        body_ar += f'\nالسبب: {reason}'
        body_en += f'\nReason: {reason}'

    data = {
        'type': 'leave_rejected',
        'screen': 'my_leaves',
    }
    if leave_id:
        data['leave_id'] = leave_id

    return send_notification_to_user(
        user=user,
        title='❌ تم رفض إجازتك',
        body=body_ar,
        data=data,
        title_en='❌ Your leave was rejected',
        body_en=body_en,
    )


def notify_manager_new_request(company, employee_name, request_type, request_id=None):
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
        title_en='📩 New Request',
        body_en=f'Employee {employee_name} submitted a request: {request_type}',
    )


def notify_manager_new_leave(company, employee_name, leave_type, leave_id=None):
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
        title_en='📩 New Leave Request',
        body_en=f'Employee {employee_name} submitted a leave request: {leave_type}',
    )


def notify_manager_out_of_geofence(company, employee_name, distance):
    return send_notification_to_managers(
        company=company,
        title='⚠️ محاولة حضور خارج النطاق',
        body=f'الموظف {employee_name} حاول تسجيل حضور من مسافة {distance}م',
        data={'type': 'geofence_violation'},
        title_en='⚠️ Out of Geofence Attempt',
        body_en=f'Employee {employee_name} tried to check in from {distance}m away',
    )


def notify_employee_checkin(user, time_str, location=''):
    body_ar = f'تم تسجيل حضورك الساعة {time_str}'
    body_en = f'Check-in recorded at {time_str}'
    if location:
        body_ar += f' — {location}'
        body_en += f' — {location}'

    send_notification_to_user(
        user=user,
        title='تسجيل الحضور ✅',
        body=body_ar,
        data={'type': 'attendance', 'action': 'checkin'},
        title_en='Check-in ✅',
        body_en=body_en,
    )


def notify_employee_checkout(user, time_str, hours_worked=''):
    body_ar = f'تم تسجيل انصرافك الساعة {time_str}'
    body_en = f'Check-out recorded at {time_str}'
    if hours_worked:
        body_ar += f' — عدد الساعات: {hours_worked}'
        body_en += f' — Hours worked: {hours_worked}'

    send_notification_to_user(
        user=user,
        title='تسجيل الانصراف 👋',
        body=body_ar,
        data={'type': 'attendance', 'action': 'checkout'},
        title_en='Check-out 👋',
        body_en=body_en,
    )


def notify_manager_checkin(company, employee_name, time_str):
    send_notification_to_managers(
        company=company,
        title='حضور موظف 📋',
        body=f'{employee_name} سجّل حضوره الساعة {time_str}',
        data={'type': 'manager_attendance', 'action': 'checkin'},
        title_en='Employee Check-in 📋',
        body_en=f'{employee_name} checked in at {time_str}',
    )


def notify_manager_checkout(company, employee_name, time_str, hours_worked=''):
    body_ar = f'{employee_name} سجّل انصرافه الساعة {time_str}'
    body_en = f'{employee_name} checked out at {time_str}'
    if hours_worked:
        body_ar += f' — {hours_worked} ساعة'
        body_en += f' — {hours_worked} hours'

    send_notification_to_managers(
        company=company,
        title='انصراف موظف 🏁',
        body=body_ar,
        data={'type': 'manager_attendance', 'action': 'checkout'},
        title_en='Employee Check-out 🏁',
        body_en=body_en,
    )


# ═══════════════════════════════════════════════════
# Field Visits & Multi-Site Notifications
# ═══════════════════════════════════════════════════

def notify_visit_auto_closed(user, previous_visit_name, auto_checkout_time,
                             travel_minutes, distance_km, company=None):
    """
    إشعار للموظف إن السيستم قفل زيارته السابقة تلقائياً
    """
    title = "تم إنهاء زيارتك السابقة تلقائياً"
    body = (
        f"تم إنهاء زيارتك في [{previous_visit_name}] الساعة {auto_checkout_time}. "
        f"المسافة {distance_km} كم، وقت التنقل المتوقع {travel_minutes} دقيقة."
    )
    
    send_notification_to_user(
        user, title, body,
        data={
            'type': 'visit_auto_closed',
            'previous_visit_name': previous_visit_name,
            'auto_checkout_time': auto_checkout_time,
            'travel_minutes': str(travel_minutes),
            'distance_km': str(distance_km),
        },
        title_en="Previous Visit Auto-Closed",
        body_en=f"Your visit at [{previous_visit_name}] was closed at {auto_checkout_time}. Distance {distance_km}km, estimated travel {travel_minutes} min.",
    )
    
    # إشعار للمدير أيضاً
    if company:
        emp_name = user.get_full_name() or user.username
        mgr_title = "إغلاق تلقائي لزيارة موظف"
        mgr_body = (
            f"[{emp_name}] تم إغلاق زيارته في [{previous_visit_name}] "
            f"الساعة {auto_checkout_time} تلقائياً (تنقل {travel_minutes} دقيقة)."
        )
        send_notification_to_managers(
            company, mgr_title, mgr_body,
            data={
                'type': 'visit_auto_closed',
                'employee_name': emp_name,
                'previous_visit_name': previous_visit_name,
            },
            title_en="Employee Visit Auto-Closed",
            body_en=f"[{emp_name}] visit at [{previous_visit_name}] was auto-closed at {auto_checkout_time}.",
        )


def notify_fraud_attempt(user, previous_visit_name, reason, company=None):
    """
    تنبيه للمدير + HR إن الموظف حاول يعمل استهبال
    """
    emp_name = user.get_full_name() or user.username
    
    # إشعار عاجل للمدير و HR
    if company:
        title = "🚨 تنبيه: محاولة تسجيل بصمة غير منطقية"
        body = (
            f"[{emp_name}] حاول تسجيل زيارة جديدة قبل إنهاء [{previous_visit_name}]. "
            f"السبب: {reason[:100]}"
        )
        send_notification_to_managers(
            company, title, body,
            data={
                'type': 'fraud_attempt',
                'severity': 'high',
                'employee_name': emp_name,
                'previous_visit_name': previous_visit_name,
                'reason': reason,
            },
            title_en="🚨 Alert: Suspicious Check-in Attempt",
            body_en=f"[{emp_name}] attempted a check-in that appears fraudulent. Reason: {reason[:100]}",
        )


def notify_work_location_proposed(company, employee_name, location_name):
    """
    إشعار للمدير/HR إن الموظف اقترح موقع جديد
    """
    title = "اقتراح موقع عمل جديد"
    body = f"[{employee_name}] اقترح موقع عمل جديد: [{location_name}]. يحتاج مراجعة واعتماد."
    
    send_notification_to_managers(
        company, title, body,
        data={
            'type': 'work_location_proposed',
            'employee_name': employee_name,
            'location_name': location_name,
        },
        title_en="New Work Location Proposed",
        body_en=f"[{employee_name}] proposed a new work location: [{location_name}]. Requires review.",
    )


def notify_work_location_approved(user, location_name, approved_by_name=''):
    """
    إشعار للموظف إن موقعه اتوافق عليه
    """
    title = "✅ تم اعتماد موقع العمل"
    body = f"تم اعتماد الموقع [{location_name}]. تقدر تبصم منه الآن."
    if approved_by_name:
        body += f" (تم الاعتماد بواسطة {approved_by_name})"
    
    send_notification_to_user(
        user, title, body,
        data={
            'type': 'work_location_approved',
            'location_name': location_name,
        },
        title_en="✅ Work Location Approved",
        body_en=f"Location [{location_name}] has been approved. You can check-in from there now.",
    )


def notify_work_location_rejected(user, location_name, reason=''):
    """
    إشعار للموظف إن موقعه اترفض
    """
    title = "❌ تم رفض موقع العمل"
    body = f"تم رفض الموقع [{location_name}]"
    if reason:
        body += f". السبب: {reason}"
    
    send_notification_to_user(
        user, title, body,
        data={
            'type': 'work_location_rejected',
            'location_name': location_name,
            'reason': reason,
        },
        title_en="❌ Work Location Rejected",
        body_en=f"Location [{location_name}] has been rejected. Reason: {reason}",
    )

