# -*- coding: utf-8 -*-
"""
APIs إنهاء الخدمة - Offboarding
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from employees.models import Employee
from accounts.models import User
from accounts.permissions_models import UserRole


def _is_allowed(user, permission_code):
    if user.is_superuser or user.role in ['super_admin', 'company_admin']:
        return True
    from accounts.permissions_models import UserRole, RolePermission, UserPermissionOverride
    override = UserPermissionOverride.objects.filter(
        user=user, permission=permission_code
    ).first()
    if override:
        return override.is_granted
    user_roles = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
    return RolePermission.objects.filter(
        role_id__in=user_roles,
        permission=permission_code
    ).exists()


STATUS_CHOICES = ['resigned', 'terminated', 'suspended', 'retired']
STATUS_LABELS = {
    'resigned': 'مستقيل',
    'terminated': 'مفصول',
    'suspended': 'موقوف',
    'retired': 'متقاعد',
}


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def offboard_employee(request, employee_id):
    """إنهاء خدمة موظف أو مدير"""
    if not _is_allowed(request.user, 'offboarding.execute'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    emp = Employee._base_manager.select_related('user', 'department').filter(
        id=employee_id, company=company
    ).first()

    if not emp:
        return Response({'error': 'الموظف غير موجود'}, status=404)

    if emp.status in STATUS_CHOICES:
        return Response({'error': f'الموظف ده بالفعل حالته {STATUS_LABELS.get(emp.status, emp.status)}'}, status=400)

    new_status = (request.data.get('status') or 'resigned').strip()
    reason = (request.data.get('reason') or '').strip()
    replacement_manager_id = request.data.get('replacement_manager_id')

    if new_status not in STATUS_CHOICES:
        return Response({
            'error': f'حالة غير صحيحة، الحالات المتاحة: {", ".join(STATUS_CHOICES)}'
        }, status=400)

    # لو مدير وعنده موظفين تحته، لازم يختار بديل
    subordinates = Employee._base_manager.filter(
        direct_manager=emp, company=company, status='active'
    )

    if subordinates.exists() and not replacement_manager_id:
        return Response({
            'error': 'الموظف ده مدير وعنده موظفين تحته، لازم تحدد مدير بديل',
            'subordinates_count': subordinates.count(),
            'subordinates': [
                {'id': s.id, 'name': s.full_name_ar or s.full_name_en or f'#{s.id}'}
                for s in subordinates[:10]
            ],
        }, status=400)

    with transaction.atomic():
        # لو فيه بديل، انقل الموظفين التابعين له
        if replacement_manager_id and subordinates.exists():
            replacement = Employee._base_manager.filter(
                id=replacement_manager_id, company=company, status='active'
            ).first()
            if not replacement:
                return Response({'error': 'المدير البديل غير موجود أو غير نشط'}, status=400)
            subordinates.update(direct_manager=replacement)

        # غيّر حالة الموظف
        emp.status = new_status
        emp.save(update_fields=['status'])

        # قفّل حساب المستخدم
        if emp.user:
            emp.user.is_active = False
            emp.user.save(update_fields=['is_active'])

            # وقّف الأدوار والصلاحيات
            UserRole.objects.filter(user=emp.user).delete()

    return Response({
        'success': True,
        'message': f'تم إنهاء خدمة الموظف — الحالة: {STATUS_LABELS.get(new_status, new_status)}',
        'employee_id': emp.id,
        'new_status': new_status,
        'subordinates_transferred': subordinates.count() if replacement_manager_id else 0,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reactivate_employee(request, employee_id):
    """إعادة تفعيل موظف"""
    if not _is_allowed(request.user, 'offboarding.execute'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    emp = Employee._base_manager.select_related('user').filter(
        id=employee_id, company=company
    ).first()

    if not emp:
        return Response({'error': 'الموظف غير موجود'}, status=404)

    with transaction.atomic():
        emp.status = 'active'
        emp.save(update_fields=['status'])

        if emp.user:
            emp.user.is_active = True
            emp.user.save(update_fields=['is_active'])

            # رجّع الدور الافتراضي للقسم لو موجود
            if emp.department and emp.department.default_role:
                UserRole.objects.get_or_create(
                    user=emp.user,
                    role=emp.department.default_role
                )

    return Response({
        'success': True,
        'message': 'تم إعادة تفعيل الموظف',
        'employee_id': emp.id,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def offboarded_employees(request):
    """قايمة الموظفين المنتهية خدمتهم"""
    if not _is_allowed(request.user, 'offboarding.execute'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    emps = Employee._base_manager.filter(
        company=company,
        status__in=STATUS_CHOICES
    ).select_related('user', 'department', 'job_title').order_by('-id')

    data = []
    for emp in emps:
        data.append({
            'id': emp.id,
            'name': emp.full_name_ar or emp.full_name_en or f'#{emp.id}',
            'status': emp.status,
            'status_label': STATUS_LABELS.get(emp.status, emp.status),
            'department': emp.department.name_ar if emp.department else '',
            'job_title': emp.job_title.name_ar if emp.job_title else '',
            'is_account_active': emp.user.is_active if emp.user else False,
        })

    return Response({'employees': data, 'total': len(data)})
