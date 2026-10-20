"""
access.py
مين مسموحله يستخدم السيستم: الحساب الموقوف والشركة الموقوفة.

إيقاف الشركة = Company.is_active = False (مفيش أي بيانات بتتمسح).
السوبر أدمن عمره ما بيتقفل.
"""

ACCOUNT_DISABLED_MSG = 'حسابك موقوف. برجاء التواصل مع إدارة الموارد البشرية.'
ACCOUNT_DISABLED_MSG_EN = 'Your account is disabled. Please contact HR.'
COMPANY_SUSPENDED_MSG = 'اشتراك الشركة متوقف. برجاء التواصل مع إدارة الشركة.'
COMPANY_SUSPENDED_MSG_EN = 'The company subscription is suspended. Please contact your company management.'


def is_super_admin(user):
    return bool(
        user and getattr(user, 'is_authenticated', False)
        and (getattr(user, 'role', '') == 'super_admin' or getattr(user, 'is_superuser', False))
    )


def company_id_for_user(user):
    """شركة المستخدم: من حسابه، ولو مش متسجلة من ملف الموظف بتاعه"""
    cid = getattr(user, 'company_id', None)
    if cid:
        return cid
    from employees.models import Employee
    return Employee._base_manager.filter(user_id=user.pk).values_list('company_id', flat=True).first()


def is_company_suspended(company_id):
    if not company_id:
        return False
    from companies.models import Company
    return Company._base_manager.filter(pk=company_id, is_active=False).exists()


def block_reason(user):
    """
    بترجع (code, رسالة عربي, رسالة إنجليزي) لو المستخدم ممنوع، أو None لو مسموح.
    """
    if not user or not getattr(user, 'pk', None):
        return None
    if is_super_admin(user):
        return None
    if not user.is_active:
        return ('account_disabled', ACCOUNT_DISABLED_MSG, ACCOUNT_DISABLED_MSG_EN)
    if is_company_suspended(company_id_for_user(user)):
        return ('company_suspended', COMPANY_SUSPENDED_MSG, COMPANY_SUSPENDED_MSG_EN)
    return None


def blocked_payload(reason):
    code, msg_ar, msg_en = reason
    # نفس الرسالة في كل المفاتيح اللي الويب والموبايل بيقروا منها
    return {
        'success': False,
        'code': code,
        'message': msg_ar,
        'message_en': msg_en,
        'error': msg_ar,
        'detail': msg_ar,
    }


def notifications_allowed(user):
    """الإشعارات بتقف لموظفين الشركة الموقوفة وبترجع لما تشتغل"""
    try:
        if not user or is_super_admin(user):
            return True
        return not is_company_suspended(company_id_for_user(user))
    except Exception:
        return True
