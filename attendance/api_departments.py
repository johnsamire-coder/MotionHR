# -*- coding: utf-8 -*-
"""
APIs إدارة الأقسام - للموبايل
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from companies.models import Department
from employees.models import Employee
from accounts.models import User
from accounts.permissions_models import UserRole


def _is_allowed(user, permission_code):
    """تحقق إن المستخدم عنده صلاحية معينة"""
    if user.is_superuser or user.role in ['super_admin', 'company_admin']:
        return True
    # شيك على الصلاحيات المخصصة
    from accounts.permissions_models import UserRole, RolePermission, UserPermissionOverride
    # شيك استثناء شخصي
    override = UserPermissionOverride.objects.filter(
        user=user, permission=permission_code
    ).first()
    if override:
        return override.is_granted
    # شيك أدوار
    user_roles = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
    return RolePermission.objects.filter(
        role_id__in=user_roles,
        permission=permission_code
    ).exists()


# ══════════════════════════════════════
# 1. قايمة الأقسام
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_departments(request):
    if not _is_allowed(request.user, 'departments.view'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    if not company:
        return Response({'error': 'مفيش شركة مرتبطة بحسابك'}, status=400)

    depts = Department.objects.filter(company=company, is_active=True).order_by('name_ar')
    data = []
    for d in depts:
        employees_count = Employee._base_manager.filter(department=d, status='active').count()
        data.append({
            'id': d.id,
            'name_ar': d.name_ar,
            'name_en': d.name_en or '',
            'code': d.code or '',
            'employees_count': employees_count,
            'default_role': {
                'id': d.default_role.id,
                'name': d.default_role.name,
            } if d.default_role else None,
            'parent_id': d.parent_id,
        })
    return Response({'departments': data})


# ══════════════════════════════════════
# 2. إضافة قسم جديد
# ══════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_department(request):
    if not _is_allowed(request.user, 'departments.add'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    if not company:
        return Response({'error': 'مفيش شركة مرتبطة بحسابك'}, status=400)

    name_ar = (request.data.get('name_ar') or '').strip()
    name_en = (request.data.get('name_en') or '').strip()
    code = (request.data.get('code') or '').strip()
    parent_id = request.data.get('parent_id')
    default_role_id = request.data.get('default_role_id')

    if not name_ar:
        return Response({'error': 'اسم القسم بالعربي مطلوب'}, status=400)

    if Department.objects.filter(company=company, name_ar=name_ar, is_active=True).exists():
        return Response({'error': 'القسم موجود بالفعل'}, status=400)

    parent = None
    if parent_id:
        parent = Department.objects.filter(id=parent_id, company=company).first()

    from accounts.permissions_models import CustomRole
    default_role = None
    if default_role_id:
        default_role = CustomRole.objects.filter(id=default_role_id, company=company).first()

    dept = Department.objects.create(
        company=company,
        name_ar=name_ar,
        name_en=name_en or None,
        code=code or None,
        parent=parent,
        default_role=default_role,
        is_active=True,
    )

    return Response({
        'success': True,
        'message': f'تم إنشاء قسم {name_ar}',
        'department_id': dept.id,
    })


# ══════════════════════════════════════
# 3. تعديل قسم
# ══════════════════════════════════════
@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def edit_department(request, dept_id):
    if not _is_allowed(request.user, 'departments.edit'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    dept = Department.objects.filter(id=dept_id, company=company, is_active=True).first()
    if not dept:
        return Response({'error': 'القسم غير موجود'}, status=404)

    name_ar = (request.data.get('name_ar') or '').strip()
    name_en = (request.data.get('name_en') or '').strip()
    code = (request.data.get('code') or '').strip()
    default_role_id = request.data.get('default_role_id')

    if name_ar:
        dept.name_ar = name_ar
    if name_en:
        dept.name_en = name_en
    if code:
        dept.code = code

    if default_role_id is not None:
        from accounts.permissions_models import CustomRole
        if default_role_id == 0 or default_role_id == '':
            dept.default_role = None
        else:
            role = CustomRole.objects.filter(id=default_role_id, company=company).first()
            if role:
                dept.default_role = role

    dept.save()
    return Response({'success': True, 'message': 'تم تعديل القسم'})


# ══════════════════════════════════════
# 4. حذف قسم (مع نقل الموظفين)
# ══════════════════════════════════════
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_department(request, dept_id):
    if not _is_allowed(request.user, 'departments.delete'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    dept = Department.objects.filter(id=dept_id, company=company, is_active=True).first()
    if not dept:
        return Response({'error': 'القسم غير موجود'}, status=404)

    transfer_to_id = request.data.get('transfer_to_department_id')
    employees = Employee._base_manager.filter(department=dept, status='active')

    if employees.exists() and not transfer_to_id:
        return Response({
            'error': 'القسم فيه موظفين، لازم تحدد قسم بديل لنقلهم',
            'employees_count': employees.count(),
        }, status=400)

    with transaction.atomic():
        if transfer_to_id and employees.exists():
            new_dept = Department.objects.filter(
                id=transfer_to_id, company=company, is_active=True
            ).first()
            if not new_dept:
                return Response({'error': 'القسم البديل غير موجود'}, status=400)

            for emp in employees:
                emp.department = new_dept
                emp.save(update_fields=['department'])

                # تغيير الدور تلقائي
                if new_dept.default_role and emp.user:
                    old_roles = UserRole.objects.filter(user=emp.user)
                    old_roles.delete()
                    UserRole.objects.get_or_create(user=emp.user, role=new_dept.default_role)

        dept.is_active = False
        dept.save(update_fields=['is_active'])

    return Response({
        'success': True,
        'message': f'تم حذف القسم وتم نقل {employees.count()} موظف',
    })


# ══════════════════════════════════════
# 5. نقل موظفين من قسم لقسم
# ══════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transfer_employees_between_departments(request):
    if not _is_allowed(request.user, 'departments.transfer_employees'):
        return Response({'error': 'غير مصرح'}, status=403)

    company = request.user.company
    employee_ids = request.data.get('employee_ids', [])
    to_dept_id = request.data.get('to_department_id')

    if not employee_ids:
        return Response({'error': 'لازم تحدد موظف واحد على الأقل'}, status=400)
    if not to_dept_id:
        return Response({'error': 'لازم تحدد القسم الجديد'}, status=400)

    new_dept = Department.objects.filter(id=to_dept_id, company=company, is_active=True).first()
    if not new_dept:
        return Response({'error': 'القسم غير موجود'}, status=404)

    success = 0
    with transaction.atomic():
        for emp_id in employee_ids:
            emp = Employee._base_manager.filter(id=emp_id, company=company).first()
            if not emp:
                continue
            emp.department = new_dept
            emp.save(update_fields=['department'])
            success += 1

            # تغيير الدور تلقائي
            if new_dept.default_role and emp.user:
                UserRole.objects.filter(user=emp.user).delete()
                UserRole.objects.get_or_create(user=emp.user, role=new_dept.default_role)

    return Response({
        'success': True,
        'message': f'تم نقل {success} موظف لقسم {new_dept.name_ar}',
    })
