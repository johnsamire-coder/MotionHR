import firebase_admin
from firebase_admin import credentials, messaging
from accounts.fcm_models import FCMDeviceToken, NotificationLog

def send_fcm_notification(user, title, body, data=None, title_en=None, body_en=None):
    """Wrapper على الخدمة المركزية عشان اللغة تبقى من Employee.language"""
    try:
        from accounts.fcm_service import send_notification_to_user
        result = send_notification_to_user(
            user=user,
            title=title,
            body=body,
            data=data,
            title_en=title_en,
            body_en=body_en,
        )
        return bool(result.get('success'))
    except Exception as e:
        print(f"FCM Error: {e}")
        return False

def notify_managers(title, body, data=None, company=None, title_en=None, body_en=None):
    """Wrapper على الخدمة المركزية للمديرين"""
    try:
        from accounts.fcm_service import send_notification_to_managers
        return send_notification_to_managers(
            company=company,
            title=title,
            body=body,
            data=data,
            title_en=title_en,
            body_en=body_en,
        )
    except Exception as e:
        print(f"Notify managers error: {e}")
        return {"success": False, "sent": 0}

# ========================
# إشعارات الحضور والانصراف
# ========================
def notify_employee_checkin(user, time_str, location=''):
    lang = getattr(FCMDeviceToken.objects.filter(user=user).first(), 'preferred_language', 'ar')
    if lang == 'en':
        body = f'Check-in recorded at {time_str}'
        if location:
            body += f' — {location}'
        send_fcm_notification(
            user,
            'Check-in ✅',
            body,
            data={'type': 'attendance', 'action': 'checkin'},
            title_en='Check-in ✅',
            body_en=body
        )
    else:
        body = f'تم تسجيل حضورك الساعة {time_str}'
        if location:
            body += f' — {location}'
        send_fcm_notification(
            user,
            'تسجيل الحضور ✅',
            body,
            data={'type': 'attendance', 'action': 'checkin'},
            title_en='Check-in ✅',
            body_en=f'Check-in recorded at {time_str}'
        )

def notify_employee_checkout(user, time_str, hours_worked=''):
    lang = getattr(FCMDeviceToken.objects.filter(user=user).first(), 'preferred_language', 'ar')
    if lang == 'en':
        body = f'Check-out recorded at {time_str}'
        if hours_worked:
            body += f' — Hours worked: {hours_worked}'
        send_fcm_notification(
            user,
            'Check-out 👋',
            body,
            data={'type': 'attendance', 'action': 'checkout'},
            title_en='Check-out 👋',
            body_en=body
        )
    else:
        body = f'تم تسجيل انصرافك الساعة {time_str}'
        if hours_worked:
            body += f' — عدد الساعات: {hours_worked}'
        send_fcm_notification(
            user,
            'تسجيل الانصراف 👋',
            body,
            data={'type': 'attendance', 'action': 'checkout'},
            title_en='Check-out 👋',
            body_en=f'Check-out recorded at {time_str}'
        )

def notify_manager_checkin(company, employee_name, time_str):
    # افتراض إن المديرين في الشركة العربية
    body = f'{employee_name} سجّل حضوره الساعة {time_str}'
    body_en = f'{employee_name} checked in at {time_str}'
    notify_managers(
        'حضور موظف 📋',
        body,
        data={'type': 'manager_attendance', 'action': 'checkin'},
        company=company,
        title_en='Employee Check-in 📋',
        body_en=body_en
    )

def notify_manager_checkout(company, employee_name, time_str, hours_worked=''):
    body = f'{employee_name} سجّل انصرافه الساعة {time_str}'
    body_en = f'{employee_name} checked out at {time_str}'
    if hours_worked:
        body += f' — {hours_worked} ساعة'
        body_en += f' — {hours_worked} hours'
    notify_managers(
        'انصراف موظف 🏁',
        body,
        data={'type': 'manager_attendance', 'action': 'checkout'},
        company=company,
        title_en='Employee Check-out 🏁',
        body_en=body_en
    )


def notify_manager_early_leave(company, employee_name, time_str, early_minutes, hours_worked=''):
    """إشعار المدير لما موظف ينصرف مبكر"""
    early_h = early_minutes // 60
    early_m = early_minutes % 60

    if early_h > 0:
        duration_ar = f'{early_h} ساعة {early_m} دقيقة' if early_m > 0 else f'{early_h} ساعة'
        duration_en = f'{early_h}h {early_m}m early' if early_m > 0 else f'{early_h}h early'
    else:
        duration_ar = f'{early_m} دقيقة'
        duration_en = f'{early_m}m early'

    body = f'{employee_name} انصرف مبكراً بـ {duration_ar} الساعة {time_str}'
    body_en = f'{employee_name} left {duration_en} at {time_str}'

    if hours_worked:
        body += f' — عمل {hours_worked} ساعة'
        body_en += f' — worked {hours_worked} hours'

    notify_managers(
        'انصراف مبكر ⚠️',
        body,
        data={'type': 'manager_attendance', 'action': 'early_leave'},
        company=company,
        title_en='Early Leave ⚠️',
        body_en=body_en,
    )
