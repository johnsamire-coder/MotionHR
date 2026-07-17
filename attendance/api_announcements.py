"""
API الإعلانات الداخلية - يستخدم CompanyAnnouncement الموجود في accounts
"""
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from accounts.company_announcements import CompanyAnnouncement, CompanyAnnouncementRead
from accounts.fcm_service import send_notification_to_user


def get_employee(user):
    try:
        from employees.models import Employee
        return Employee._base_manager.filter(user=user).first()
    except Exception:
        return None


def get_user_company(user):
    if getattr(user, 'company_id', None):
        return user.company
    emp = get_employee(user)
    return getattr(emp, 'company', None)


def is_manager(user):
    return user.role in ['super_admin', 'company_admin', 'manager', 'hr_manager']


# ─────────────────────────────────────────────
# GET /announcements/list/
# ─────────────────────────────────────────────
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def announcements_list(request):
    user = request.user
    now = timezone.now()
    company = get_user_company(user)

    if not company:
        return Response({
            'announcements': [],
            'unread_count': 0,
            'total': 0,
        })

    qs = CompanyAnnouncement.objects.filter(
        company=company,
        is_active=True,
        publish_at__lte=now,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now)
    ).order_by('-publish_at')

    emp = get_employee(user)
    read_ids = set()
    if emp:
        read_ids = set(
            CompanyAnnouncementRead.objects.filter(
                employee=emp,
                announcement__in=qs
            ).values_list('announcement_id', flat=True)
        )

    result = []
    for a in qs:
        result.append({
            'id': a.id,
            'title': a.title,
            'message': a.message,
            'type': a.announcement_type,
            'type_display': a.get_announcement_type_display(),
            'priority': a.priority,
            'priority_display': a.get_priority_display(),
            'publish_at': a.publish_at.strftime('%Y-%m-%d %H:%M'),
            'expires_at': a.expires_at.strftime('%Y-%m-%d %H:%M') if a.expires_at else None,
            'requires_confirmation': a.requires_confirmation,
            'is_read': a.id in read_ids,
            'total_sent': a.total_sent,
            'total_read': a.total_read,
            'created_by': a.created_by.get_full_name() if a.created_by else '',
        })

    unread_count = sum(1 for r in result if not r['is_read'])

    return Response({
        'announcements': result,
        'unread_count': unread_count,
        'total': len(result),
    })


# ─────────────────────────────────────────────
# POST /announcements/mark-read/
# ─────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def announcements_mark_read(request):
    user = request.user
    company = get_user_company(user)
    emp = get_employee(user)
    if not emp:
        return Response({'error': 'موظف غير موجود'}, status=400)
    if not company:
        return Response({'error': 'شركة المستخدم غير موجودة'}, status=400)

    announcement_id = request.data.get('announcement_id')
    if not announcement_id:
        return Response({'error': 'announcement_id مطلوب'}, status=400)

    try:
        ann = CompanyAnnouncement.objects.get(id=announcement_id, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    _, created = CompanyAnnouncementRead.objects.get_or_create(
        employee=emp,
        announcement=ann,
    )

    if created:
        CompanyAnnouncement.objects.filter(id=ann.id).update(
            total_read=ann.total_read + 1
        )

    return Response({'success': True, 'message': 'تم التسجيل كمقروء'})


# ─────────────────────────────────────────────
# POST /manager/announcements/create/
# ─────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_create_announcement(request):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    data = request.data
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()

    if not title or not message:
        return Response({'error': 'العنوان والمحتوى مطلوبان'}, status=400)

    ann = CompanyAnnouncement.objects.create(
        company=company,
        title=title,
        message=message,
        announcement_type=data.get('type', 'general'),
        priority=data.get('priority', 'medium'),
        target_type=data.get('target_type', 'all'),
        requires_confirmation=data.get('requires_confirmation', False),
        send_push=data.get('send_push', True),
        publish_at=timezone.now(),
        created_by=user,
    )

    # إرسال Push Notification لكل موظف مستهدف
    sent_count = 0
    if ann.send_push:
        try:
            targets = ann.get_target_employees()
            for emp in targets:
                if hasattr(emp, 'user') and emp.user:
                    send_notification_to_user(
                        user=emp.user,
                        title=f"📢 {ann.title}",
                        body=ann.message[:100],
                        data={
                            'type': 'announcement',
                            'announcement_id': str(ann.id),
                        },
                    )
                    sent_count += 1
        except Exception:
            pass

    CompanyAnnouncement.objects.filter(id=ann.id).update(total_sent=sent_count)

    return Response({
        'success': True,
        'message': 'تم نشر الإعلان',
        'announcement_id': ann.id,
        'total_sent': sent_count,
    }, status=201)


# ─────────────────────────────────────────────
# DELETE /manager/announcements/<id>/delete/
# ─────────────────────────────────────────────
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_delete_announcement(request, pk):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    company = get_user_company(user)
    if not company:
        return Response({'error': 'شركة المستخدم غير موجودة'}, status=400)

    try:
        ann = CompanyAnnouncement.objects.get(id=pk, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    ann.delete()
    return Response({'success': True, 'message': 'تم حذف الإعلان'})


# ─────────────────────────────────────────────
# GET /manager/announcements/<id>/stats/
# ─────────────────────────────────────────────
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_announcement_stats(request, pk):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    company = get_user_company(user)
    if not company:
        return Response({'error': 'شركة المستخدم غير موجودة'}, status=400)

    try:
        ann = CompanyAnnouncement.objects.get(id=pk, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    reads = CompanyAnnouncementRead.objects.filter(
        announcement=ann
    ).select_related('employee')

    readers = []
    for r in reads:
        name = ''
        if hasattr(r.employee, 'get_full_name'):
            name = r.employee.get_full_name()
        elif hasattr(r.employee, 'full_name'):
            name = r.employee.full_name
        else:
            name = str(r.employee)
        readers.append({
            'employee_name': name,
            'read_at': r.read_at.strftime('%Y-%m-%d %H:%M'),
        })

    total_sent = ann.total_sent or 0
    total_read = ann.total_read or 0

    return Response({
        'id': ann.id,
        'title': ann.title,
        'total_sent': total_sent,
        'total_read': total_read,
        'read_percentage': round((total_read / total_sent * 100) if total_sent > 0 else 0, 1),
        'readers': readers,
    })