"""
activation.py
تفعيل حساب الموظف لأول مرة (رقم الموبايل + آخر 4 أرقام من القومي).
نسخة واحدة آمنة بيستخدمها رابط الموبايل ورابط الويب.

- مسموح بس للحساب اللي لسه ماتفعّلش (عليه "لازم يغيّر كلمة السر").
- الموبايل لازم يتطابق كله، و4 أرقام بالظبط من القومي، وموظف واحد بس.
- مابيرجّعش حساب موقوف، ومابيشتغلش لشركة موقوفة.
- بعد 5 محاولات غلط من نفس الجهاز أو لنفس الرقم يتقفل ربع ساعة.
"""
import re

from django.core.cache import cache
from rest_framework.response import Response

from .access import block_reason, blocked_payload

MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60

NOT_MATCHED_MSG = 'بيانات غير مطابقة. تأكد من إدخال البيانات المسجلة بالشركة'
ALREADY_ACTIVE_MSG = 'حسابك متفعّل قبل كده. لو نسيت كلمة السر تواصل مع إدارة الموارد البشرية.'
LOCKED_MSG = 'محاولات كتير غلط. حاول تاني بعد ربع ساعة.'


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[0].strip() if forwarded else '') or request.META.get('REMOTE_ADDR', '') or '-'


def _keys(request, phone):
    return [f'activate_fail:ip:{_client_ip(request)}', f'activate_fail:phone:{phone}']


def _is_locked(keys):
    return any((cache.get(k) or 0) >= MAX_FAILURES for k in keys)


def _fail(keys, message, status=400):
    for k in keys:
        try:
            cache.add(k, 0, LOCK_SECONDS)
            cache.incr(k)
        except ValueError:
            cache.set(k, 1, LOCK_SECONDS)
    return Response({'success': False, 'message': message}, status=status)


def activate_account_response(request):
    from employees.models import Employee

    data = request.data
    phone = re.sub(r'\D', '', str(data.get('phone', '') or ''))
    suffix = str(data.get('national_id_suffix', '') or '').strip()
    new_password = str(data.get('new_password', '') or '').strip()

    if not phone or not suffix:
        return Response({'success': False, 'message': 'رقم الموبايل وآخر 4 أرقام من الرقم القومي مطلوبين'}, status=400)
    if len(suffix) != 4 or not suffix.isdigit():
        return Response({'success': False, 'message': 'آخر 4 أرقام من الرقم القومي غير صحيحة'}, status=400)
    if len(phone) < 10:
        return Response({'success': False, 'message': 'رقم الموبايل غير صحيح'}, status=400)

    phone10 = phone[-10:]
    keys = _keys(request, phone10)
    if _is_locked(keys):
        return Response({'success': False, 'message': LOCKED_MSG}, status=429)

    candidates = [
        e for e in Employee._base_manager.filter(
            phone__endswith=phone10,
            national_id__endswith=suffix,
            status='active',
        ).select_related('user')
        # الرقم كله لازم يطابق (مش آخره بس)
        if re.sub(r'\D', '', e.phone or '')[-10:] == phone10
    ]
    if len(candidates) != 1 or not candidates[0].user:
        return _fail(keys, NOT_MATCHED_MSG)

    emp = candidates[0]
    user = emp.user

    reason = block_reason(user)
    if reason:
        return Response(blocked_payload(reason), status=403)
    if not getattr(user, 'must_change_password', False):
        return _fail(keys, ALREADY_ACTIVE_MSG)

    if not new_password:
        # خطوة 1: التحقق بس
        return Response({
            'success': True,
            'message': f'أهلاً {emp.first_name_ar or ""}. يرجى تعيين كلمة سر جديدة لحسابك'.replace('  ', ' '),
            'username': user.username,
        })

    if len(new_password) < 8:
        return Response({'success': False, 'message': 'كلمة السر يجب أن تكون 8 رموز على الأقل'}, status=400)

    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=['password', 'must_change_password'])
    from rest_framework.authtoken.models import Token
    Token._base_manager.filter(user=user).delete()
    for k in keys:
        cache.delete(k)

    return Response({
        'success': True,
        'message': 'تم تفعيل حسابك بنجاح. يمكنك الآن تسجيل الدخول',
        'username': user.username,
    })
