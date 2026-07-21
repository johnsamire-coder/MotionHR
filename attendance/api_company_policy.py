"""
MotionHR - Company Work Policy API
Phase 14: إعدادات أيام العمل لكل شركة - Bilingual AR/EN
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def _check_manager(user):
    role = getattr(user, 'role', None)
    return (
        user.is_superuser
        or user.is_staff
        or role in ['company_admin', 'hr_manager', 'manager']
    )


def _get_lang(user):
    try:
        from accounts.fcm_models import FCMDeviceToken
        token = FCMDeviceToken.objects.filter(user=user, is_active=True).first()
        lang = getattr(token, 'preferred_language', 'ar')
        return lang if lang in ('ar', 'en') else 'ar'
    except Exception:
        return 'ar'


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_work_policy(request):
    user = request.user
    lang = _get_lang(user)

    if not _check_manager(user):
        msg = 'Insufficient permissions' if lang == 'en' else 'صلاحية غير كافية'
        return Response({'error': msg}, status=403)

    company = getattr(user, 'company', None)

    try:
        from .company_policy_models import CompanyWorkPolicy
        policy = CompanyWorkPolicy.objects.filter(company=company).first()
    except Exception:
        policy = None

    if policy:
        data = {
            'work_sunday': policy.work_sunday,
            'work_monday': policy.work_monday,
            'work_tuesday': policy.work_tuesday,
            'work_wednesday': policy.work_wednesday,
            'work_thursday': policy.work_thursday,
            'work_friday': policy.work_friday,
            'work_saturday': policy.work_saturday,
            'is_24_7': policy.is_24_7,
        }
    else:
        # افتراضي: أحد → خميس + سبت، جمعة إجازة
        data = {
            'work_sunday': True,
            'work_monday': True,
            'work_tuesday': True,
            'work_wednesday': True,
            'work_thursday': True,
            'work_friday': False,
            'work_saturday': True,
            'is_24_7': False,
        }

    data['source'] = 'database' if policy else 'default'
    return Response(data)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_work_policy(request):
    user = request.user
    lang = _get_lang(user)

    if not _check_manager(user):
        msg = 'Insufficient permissions' if lang == 'en' else 'صلاحية غير كافية'
        return Response({'error': msg}, status=403)

    company = getattr(user, 'company', None)
    d = request.data

    try:
        from .company_policy_models import CompanyWorkPolicy
        policy, created = CompanyWorkPolicy.objects.get_or_create(
            company=company,
            defaults={
                'work_sunday': d.get('work_sunday', True),
                'work_monday': d.get('work_monday', True),
                'work_tuesday': d.get('work_tuesday', True),
                'work_wednesday': d.get('work_wednesday', True),
                'work_thursday': d.get('work_thursday', True),
                'work_friday': d.get('work_friday', False),
                'work_saturday': d.get('work_saturday', True),
                'is_24_7': d.get('is_24_7', False),
            }
        )

        if not created:
            for field in ['work_sunday', 'work_monday', 'work_tuesday',
                          'work_wednesday', 'work_thursday', 'work_friday',
                          'work_saturday', 'is_24_7']:
                if field in d:
                    setattr(policy, field, d[field])
            policy.save()

        msg = 'Work policy saved successfully' if lang == 'en' else 'تم حفظ سياسة العمل بنجاح'
        return Response({
            'status': 'saved',
            'message': msg,
            'work_sunday': policy.work_sunday,
            'work_monday': policy.work_monday,
            'work_tuesday': policy.work_tuesday,
            'work_wednesday': policy.work_wednesday,
            'work_thursday': policy.work_thursday,
            'work_friday': policy.work_friday,
            'work_saturday': policy.work_saturday,
            'is_24_7': policy.is_24_7,
        })

    except Exception as e:
        msg = f'Error: {e}' if lang == 'en' else f'خطأ: {e}'
        return Response({'error': msg}, status=500)
