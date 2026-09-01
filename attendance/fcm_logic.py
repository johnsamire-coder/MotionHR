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

def notify_managers(title, body, data=None, company=None, title_en=None, body_en=None, employee=None):
    """Wrapper على الخدمة المركزية للمديرين (HR + Admins + المدير المباشر فقط)"""
    try:
        from accounts.fcm_service import send_notification_to_managers
        return send_notification_to_managers(
            company=company,
            title=title,
            body=body,
            data=data,
            title_en=title_en,
            body_en=body_en,
            employee=employee,
        )
    except Exception as e:
        print(f"Notify managers error: {e}")
        return {"success": False, "sent": 0}

ar_emp_checkin_title = 'تم تسجيل الحضور ✅'
ar_emp_checkin_body = 'تم تسجيل حضورك الساعة'
ar_emp_checkout_title = 'تم تسجيل الانصراف ✅'
ar_emp_checkout_body = 'تم تسجيل انصرافك الساعة'

ar_mgr_checkin_title = 'حضور موظف ✅'
ar_mgr_checkin_body = 'سجل حضور الساعة'
ar_mgr_checkout_title = 'انصراف موظف ✅'
ar_mgr_checkout_body = 'سجل انصراف الساعة'
ar_mgr_early_title = 'انصراف مبكر ⏰'
ar_mgr_early_body = 'انصرف مبكرًا قبل الميعاد بـ'

# ========================
# إشعارات الحضور والانصراف
# ========================
def notify_employee_checkin(user, time_str, location=''):
    lang = getattr(FCMDeviceToken.objects.filter(user=user).first(), 'preferred_language', 'ar')
    if lang == 'en':
        body = f'Your check-in was recorded at {time_str}'
        if location:
            body += f' • {location}'
        send_fcm_notification(
            user,
            'Check-in recorded ✅',
            body,
            data={'type': 'attendance', 'action': 'checkin'},
            title_en='Check-in recorded ✅',
            body_en=body
        )
    else:
        body = f'{ar_emp_checkin_body} {time_str}'
        if location:
            body += f' • {location}'
        send_fcm_notification(
            user,
            ar_emp_checkin_title,
            body,
            data={'type': 'attendance', 'action': 'checkin'},
            title_en='Check-in recorded ✅',
            body_en=f'Your check-in was recorded at {time_str}'
        )


def notify_employee_checkout(user, time_str, hours_worked=''):
    lang = getattr(FCMDeviceToken.objects.filter(user=user).first(), 'preferred_language', 'ar')
    if lang == 'en':
        body = f'Your check-out was recorded at {time_str}'
        if hours_worked:
            body += f' • Worked hours: {hours_worked}'
        send_fcm_notification(
            user,
            'Check-out recorded ✅',
            body,
            data={'type': 'attendance', 'action': 'checkout'},
            title_en='Check-out recorded ✅',
            body_en=body
        )
    else:
        body = f'{ar_emp_checkout_body} {time_str}'
        if hours_worked:
            body += f' • عدد ساعات العمل: {hours_worked}'
        send_fcm_notification(
            user,
            ar_emp_checkout_title,
            body,
            data={'type': 'attendance', 'action': 'checkout'},
            title_en='Check-out recorded ✅',
            body_en=f'Your check-out was recorded at {time_str}'
        )


def notify_manager_checkin(company, employee_name, time_str, employee=None):
    body = f'{employee_name} {ar_mgr_checkin_body} {time_str}'
    body_en = f'{employee_name} checked in at {time_str}'
    notify_managers(
        ar_mgr_checkin_title,
        body,
        data={'type': 'manager_attendance', 'action': 'checkin'},
        company=company,
        title_en='Employee Check-in ✅',
        body_en=body_en,
        employee=employee,
    )


def notify_manager_checkout(company, employee_name, time_str, hours_worked='', employee=None):
    body = f'{employee_name} {ar_mgr_checkout_body} {time_str}'
    body_en = f'{employee_name} checked out at {time_str}'
    if hours_worked:
        body += f' • ساعات العمل: {hours_worked}'
        body_en += f' • Worked hours: {hours_worked}'
    notify_managers(
        ar_mgr_checkout_title,
        body,
        data={'type': 'manager_attendance', 'action': 'checkout'},
        company=company,
        title_en='Employee Check-out ✅',
        body_en=body_en,
        employee=employee,
    )


def notify_manager_early_leave(company, employee_name, time_str, early_minutes, hours_worked='', employee=None):
    """إشعار المدير إن الموظف انصرف مبكرًا"""
    early_h = early_minutes // 60
    early_m = early_minutes % 60

    if early_h > 0:
        duration_ar = f'{early_h} ساعة {early_m} دقيقة' if early_m > 0 else f'{early_h} ساعة'
        duration_en = f'{early_h}h {early_m}m early' if early_m > 0 else f'{early_h}h early'
    else:
        duration_ar = f'{early_m} دقيقة'
        duration_en = f'{early_m}m early'

    body = f'{employee_name} انصرف مبكرًا قبل الميعاد بـ {duration_ar} الساعة {time_str}'
    body_en = f'{employee_name} left early by {duration_en} at {time_str}'

    if hours_worked:
        body += f' • ساعات العمل: {hours_worked}'
        body_en += f' • Worked hours: {hours_worked}'

    notify_managers(
        'انصراف مبكر ⏰',
        body,
        data={'type': 'manager_attendance', 'action': 'early_leave'},
        company=company,
        title_en='Early Leave ⏰',
        body_en=body_en,
        employee=employee,
    )


# ========================
# إشعارات الزيارات الميدانية
# ========================

def notify_employee_visit_start(user, location_name, time_str):
    send_fcm_notification(
        user,
        'تم بدء الزيارة 📍',
        f'بدأت زيارتك لـ {location_name} الساعة {time_str}',
        data={'type': 'field_visit', 'action': 'start'},
        title_en='Visit Started 📍',
        body_en=f'Your visit to {location_name} started at {time_str}',
    )


def notify_employee_visit_end(user, location_name, time_str, duration_str):
    send_fcm_notification(
        user,
        'تم إنهاء الزيارة ✅',
        f'انتهت زيارتك لـ {location_name} الساعة {time_str} • مدة الزيارة: {duration_str}',
        data={'type': 'field_visit', 'action': 'end'},
        title_en='Visit Ended ✅',
        body_en=f'Your visit to {location_name} ended at {time_str} • Duration: {duration_str}',
    )


def notify_manager_visit_start(company, employee_name, location_name, time_str, employee=None):
    notify_managers(
        'زيارة ميدانية بدأت 📍',
        f'{employee_name} بدأ زيارة لـ {location_name} الساعة {time_str}',
        data={'type': 'field_visit', 'action': 'start'},
        company=company,
        title_en='Field Visit Started 📍',
        body_en=f'{employee_name} started a visit to {location_name} at {time_str}',
        employee=employee,
    )


def notify_manager_visit_end(company, employee_name, location_name, time_str, duration_str, duration_en='', employee=None):
    notify_managers(
        'زيارة ميدانية انتهت ✅',
        f'{employee_name} أنهى زيارة {location_name} الساعة {time_str} • مدة: {duration_str}',
        data={'type': 'field_visit', 'action': 'end'},
        company=company,
        title_en='Field Visit Ended ✅',
        body_en=f'{employee_name} ended visit to {location_name} at {time_str} • Duration: {duration_en or duration_str}',
        employee=employee,
    )

