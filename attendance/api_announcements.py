"""
API الإعلانات الداخلية - يستخدم CompanyAnnouncement الموجود في accounts
"""
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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

    qs = CompanyAnnouncement._base_manager.filter(
        company=user.company,
        is_active=True,
        publish_at__lte=now,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now)
    ).order_by('-publish_at')

    emp = get_employee(user)
    read_ids = set()
    if emp:
        read_ids = set(
            CompanyAnnouncementRead._base_manager.filter(
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
@authentication_classes([TokenAuthentication, JWTAuthentication])
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
        ann = CompanyAnnouncement._base_manager.get(id=announcement_id, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    _, created = CompanyAnnouncementRead._base_manager.get_or_create(
        employee=emp,
        announcement=ann,
    )

    if created:
        CompanyAnnouncement._base_manager.filter(id=ann.id).update(
            total_read=ann.total_read + 1
        )

    return Response({'success': True, 'message': 'تم التسجيل كمقروء'})


# ─────────────────────────────────────────────
# POST /manager/announcements/create/
# ─────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_create_announcement(request):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    data = request.data
    title = data.get('title', '').strip()
    message = (data.get('message') or data.get('content') or '').strip()

    if not title or not message:
        return Response({'error': 'العنوان والمحتوى مطلوبان'}, status=400)

    ann = CompanyAnnouncement._base_manager.create(
        company=user.company,
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

    CompanyAnnouncement._base_manager.filter(id=ann.id).update(total_sent=sent_count)

    return Response({
        'success': True,
        'message': 'تم نشر الإعلان',
        'announcement_id': ann.id,
        'total_sent': sent_count,
    }, status=201)



# ─────────────────────────────────────────────
# PUT/PATCH /manager/announcements/<id>/update/
# ─────────────────────────────────────────────
@api_view(['PUT', 'PATCH'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_update_announcement(request, pk):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    company = get_user_company(user)
    if not company:
        return Response({'error': 'شركة المستخدم غير موجودة'}, status=400)

    try:
        ann = CompanyAnnouncement._base_manager.get(id=pk, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    data = request.data

    if 'title' in data:
        title = str(data.get('title') or '').strip()
        if not title:
            return Response({'error': 'العنوان مطلوب'}, status=400)
        ann.title = title

    if 'message' in data or 'content' in data:
        ann.message = (data.get('message') or data.get('content') or '').strip()
        message = str(data.get('message') or '').strip()
        if not message:
            return Response({'error': 'المحتوى مطلوب'}, status=400)
        ann.message = message

    if 'type' in data:
        ann.announcement_type = data.get('type') or ann.announcement_type

    if 'priority' in data:
        ann.priority = data.get('priority') or ann.priority

    if 'target_type' in data:
        ann.target_type = data.get('target_type') or ann.target_type

    if 'requires_confirmation' in data:
        ann.requires_confirmation = bool(data.get('requires_confirmation'))

    if 'send_push' in data:
        ann.send_push = bool(data.get('send_push'))

    if 'is_active' in data:
        ann.is_active = bool(data.get('is_active'))

    ann.save()

    # إعادة إرسال الإشعار لو المدير طلب ده
    resend = bool(request.data.get('resend_notification', False))
    resent_count = 0
    if resend:
        try:
            targets = ann.get_target_employees()
            for emp in targets:
                if hasattr(emp, 'user') and emp.user:
                    send_notification_to_user(
                        user=emp.user,
                        title=f"📢 تم تعديل الإعلان: {ann.title}",
                        body=ann.message[:100],
                        data={
                            'type': 'announcement_updated',
                            'announcement_id': str(ann.id),
                        },
                    )
                    resent_count += 1
        except Exception:
            pass

    return Response({
        'success': True,
        'message': 'تم تعديل الإعلان',
        'announcement_id': ann.id,
        'resent_count': resent_count,
    })

# ─────────────────────────────────────────────
# DELETE /manager/announcements/<id>/delete/
# ─────────────────────────────────────────────
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_delete_announcement(request, pk):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    company = get_user_company(user)
    if not company:
        return Response({'error': 'شركة المستخدم غير موجودة'}, status=400)

    try:
        ann = CompanyAnnouncement._base_manager.get(id=pk, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    # إرسال إشعار بالحذف لو المدير طلب ده
    send_deletion_notice = bool(request.data.get('send_deletion_notice', True))
    if send_deletion_notice:
        try:
            targets = ann.get_target_employees()
            for emp in targets:
                if hasattr(emp, 'user') and emp.user:
                    send_notification_to_user(
                        user=emp.user,
                        title=f"🗑️ تم حذف الإعلان: {ann.title}",
                        body="تم حذف هذا الإعلان من قِبل الإدارة",
                        data={
                            'type': 'announcement_deleted',
                            'announcement_id': str(ann.id),
                        },
                    )
        except Exception:
            pass

    ann.delete()
    return Response({'success': True, 'message': 'تم حذف الإعلان'})


# ─────────────────────────────────────────────
# GET /manager/announcements/<id>/stats/
# ─────────────────────────────────────────────
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_announcement_stats(request, pk):
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    company = get_user_company(user)
    if not company:
        return Response({'error': 'شركة المستخدم غير موجودة'}, status=400)

    try:
        ann = CompanyAnnouncement._base_manager.get(id=pk, company=company)
    except CompanyAnnouncement.DoesNotExist:
        return Response({'error': 'الإعلان غير موجود'}, status=404)

    reads = CompanyAnnouncementRead._base_manager.filter(
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


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_list_announcements(request):
    """قائمة الإعلانات اللي أنشأها المدير في شركته"""
    user = request.user
    if not is_manager(user):
        return Response({'error': 'غير مصرح'}, status=403)

    announcements = CompanyAnnouncement._base_manager.filter(
        company=user.company
    ).order_by('-publish_at', '-created_at')

    data = []
    for ann in announcements:
        data.append({
            'id': ann.id,
            'title': ann.title,
            'message': ann.message,
            'announcement_type': ann.announcement_type,
            'announcement_type_display': ann.get_announcement_type_display(),
            'priority': ann.priority,
            'priority_display': ann.get_priority_display(),
            'target_type': ann.target_type,
            'target_type_display': ann.get_target_type_display(),
            'requires_confirmation': ann.requires_confirmation,
            'publish_at': ann.publish_at.isoformat() if ann.publish_at else None,
            'expires_at': ann.expires_at.isoformat() if ann.expires_at else None,
            'is_active': ann.is_active,
            'total_sent': ann.total_sent,
            'total_read': ann.total_read,
            'created_at': ann.created_at.isoformat() if ann.created_at else None,
            'created_by': ann.created_by.get_full_name() if ann.created_by else '',
        })

    return Response({'success': True, 'announcements': data, 'count': len(data)})


def _is_announcement_targeted_to_employee(ann, employee):
    """يتأكد هل الإعلان موجه للموظف ده بناءً على نوع الاستهداف"""
    if employee.id in ann.excluded_employees.values_list('id', flat=True):
        return False

    if ann.target_type == 'all':
        return True
    elif ann.target_type == 'specific':
        return ann.target_employees.filter(id=employee.id).exists()
    elif ann.target_type == 'by_job_title':
        job_title_name = getattr(employee.job_title, 'name_ar', '') if employee.job_title else ''
        targets = [t.strip() for t in (ann.target_job_titles or '').split(',')]
        return job_title_name in targets
    elif ann.target_type == 'by_department':
        return ann.target_departments.filter(id=employee.department_id).exists()
    elif ann.target_type == 'by_branch':
        return ann.target_branches.filter(id=employee.branch_id).exists()
    return False


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_pending_announcements(request):
    """الإعلانات النشطة اللي الموظف لسه ما أكدش قراءتها (لعرضها إجبارياً عند فتح التطبيق)"""
    from employees.models import Employee

    employee = Employee._base_manager.filter(user=request.user).first()
    if not employee:
        return Response({'success': True, 'announcements': [], 'count': 0})

    now = timezone.now()
    active_anns = CompanyAnnouncement._base_manager.filter(
        company=employee.company,
        is_active=True,
        publish_at__lte=now,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now)
    ).order_by('-priority', '-publish_at')

    read_ids = set(
        CompanyAnnouncementRead._base_manager.filter(employee=employee).values_list('announcement_id', flat=True)
    )

    pending = []
    for ann in active_anns:
        if ann.id in read_ids:
            continue
        if not _is_announcement_targeted_to_employee(ann, employee):
            continue
        pending.append({
            'id': ann.id,
            'title': ann.title,
            'message': ann.message,
            'announcement_type': ann.announcement_type,
            'announcement_type_display': ann.get_announcement_type_display(),
            'priority': ann.priority,
            'publish_at': ann.publish_at.isoformat() if ann.publish_at else None,
        })

    return Response({'success': True, 'announcements': pending, 'count': len(pending)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def confirm_announcement_read(request, announcement_id):
    """الموظف يأكد إنه قرأ الإعلان (يمنع ظهوره تاني)"""
    from employees.models import Employee

    employee = Employee._base_manager.filter(user=request.user).first()
    if not employee:
        return Response({'success': False, 'error': 'الموظف غير موجود'}, status=404)

    ann = CompanyAnnouncement._base_manager.filter(id=announcement_id, company=employee.company).first()
    if not ann:
        return Response({'success': False, 'error': 'الإعلان غير موجود'}, status=404)

    CompanyAnnouncementRead._base_manager.get_or_create(employee=employee, announcement=ann)
    ann.total_read = CompanyAnnouncementRead._base_manager.filter(announcement=ann).count()
    ann.save(update_fields=['total_read'])

    return Response({'success': True, 'message': 'تم تأكيد القراءة'})
