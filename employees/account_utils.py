"""
account_utils.py
أدوات إنشاء وإدارة حسابات الموظفين
"""

import random
import string
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

User = get_user_model()


def generate_password(length=10):
    """
    توليد كلمة سر آمنة
    - حروف كبيرة + صغيرة + أرقام + رموز
    """
    chars = (
        string.ascii_uppercase +   # A-Z
        string.ascii_lowercase +   # a-z
        string.digits +            # 0-9
        "@#$%"                     # رموز بسيطة
    )
    # نضمن وجود كل نوع
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("@#$%"),
    ]
    # باقي الطول عشوائي
    password += random.choices(chars, k=length - 4)
    random.shuffle(password)
    return "".join(password)


def generate_username(employee):
    """
    توليد username من employee_code
    مثال: EMP00001
    """
    return employee.employee_code.lower()


def create_employee_account(employee, created_by=None, send_email=True):
    """
    إنشاء حساب مستخدم للموظف

    Returns:
        dict: {
            'success': bool,
            'user': User or None,
            'password': str,
            'message': str,
            'email_sent': bool,
        }
    """
    result = {
        'success':    False,
        'user':       None,
        'password':   '',
        'message':    '',
        'email_sent': False,
    }

    # تحقق لو عنده حساب بالفعل
    if employee.user:
        result['message'] = 'الموظف عنده حساب بالفعل'
        return result

    try:
        username = generate_username(employee)
        password = generate_password()

        # تحقق إن الـ username مش مكرر
        if User.objects.filter(username=username).exists():
            username = f"{username}_{employee.pk}"

        # إنشاء الـ User
        user = User.objects.create_user(
            username=username,
            password=password,
            email=employee.email or '',
            first_name=employee.first_name_ar or '',
            last_name=employee.last_name_ar or '',
            phone=employee.phone or '',
            role='employee',
            company=employee.company,
            must_change_password=True,  # إجباري تغيير أول دخول
        )

        # ربط الـ User بالموظف
        employee.user = user
        employee.save(update_fields=['user'])

        result['success']  = True
        result['user']     = user
        result['password'] = password
        result['message']  = 'تم إنشاء الحساب بنجاح'

        # إرسال إيميل لو فيه إيميل
        if send_email and employee.email:
            try:
                _send_welcome_email(employee, user, password)
                result['email_sent'] = True
            except Exception as e:
                result['email_sent'] = False
                result['message'] += f' (فشل إرسال الإيميل: {e})'

    except Exception as e:
        result['message'] = f'خطأ في إنشاء الحساب: {e}'

    return result


def reset_employee_password(employee, reset_by=None):
    """
    إعادة تعيين كلمة مرور الموظف من المدير

    Returns:
        dict: {
            'success': bool,
            'password': str,
            'message': str,
            'email_sent': bool,
        }
    """
    result = {
        'success':    False,
        'password':   '',
        'message':    '',
        'email_sent': False,
    }

    if not employee.user:
        result['message'] = 'الموظف مالوش حساب'
        return result

    try:
        new_password = generate_password()
        employee.user.set_password(new_password)
        employee.user.must_change_password = True  # إجباري تغيير
        employee.user.save()

        result['success']  = True
        result['password'] = new_password
        result['message']  = 'تم إعادة تعيين كلمة المرور بنجاح'

        # إرسال إيميل لو فيه إيميل
        if employee.email:
            try:
                _send_password_reset_email(employee, new_password)
                result['email_sent'] = True
            except Exception as e:
                result['email_sent'] = False

    except Exception as e:
        result['message'] = f'خطأ: {e}'

    return result


def _send_welcome_email(employee, user, password):
    """إرسال إيميل ترحيبي للموظف الجديد"""
    subject = f'مرحباً بك في {employee.company.name_ar} - بيانات دخولك'
    
    login_url = getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/login/'
    
    message = f"""
مرحباً {employee.full_name_ar}،

تم إنشاء حسابك في نظام MotionHR لإدارة الموارد البشرية.

بيانات تسجيل الدخول:
━━━━━━━━━━━━━━━━━━━━
اسم المستخدم: {user.username}
كلمة المرور:  {password}
رابط الدخول:  {login_url}
━━━━━━━━━━━━━━━━━━━━

⚠️ ملاحظة مهمة:
يرجى تغيير كلمة المرور فور تسجيل دخولك الأول.

لا تشارك بيانات دخولك مع أي شخص.

مع تحيات،
فريق {employee.company.name_ar}
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[employee.email],
        fail_silently=False,
    )


def _send_password_reset_email(employee, new_password):
    """إرسال إيميل إعادة تعيين كلمة المرور"""
    subject = f'إعادة تعيين كلمة المرور - {employee.company.name_ar}'
    
    login_url = getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/login/'
    
    message = f"""
مرحباً {employee.full_name_ar}،

تم إعادة تعيين كلمة مرور حسابك.

بيانات تسجيل الدخول الجديدة:
━━━━━━━━━━━━━━━━━━━━
اسم المستخدم: {employee.user.username}
كلمة المرور:  {new_password}
رابط الدخول:  {login_url}
━━━━━━━━━━━━━━━━━━━━

⚠️ يرجى تغيير كلمة المرور فور تسجيل دخولك.

مع تحيات،
فريق {employee.company.name_ar}
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[employee.email],
        fail_silently=False,
    )
