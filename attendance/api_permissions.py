SOVEREIGN_PERMISSIONS = {'roles.manage', 'company.edit', 'offboarding.execute'}
# -*- coding: utf-8 -*-
"""
APIs إدارة الصلاحيات - للموبايل
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from accounts.permissions_models import (
    CustomRole, RolePermission, UserRole,
    UserPermissionOverride, PERMISSION_CHOICES, SCOPE_CHOICES
)
from accounts.models import User
from employees.models import Employee

# ══════════════════════════════════════
# Helper: تأكد إن المستخدم Company Admin
# ══════════════════════════════════════
def is_company_admin(user):
    return user.is_superuser or user.role in ['super_admin', 'company_admin']


# ══════════════════════════════════════
# 1. قايمة الصلاحيات المتاحة
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_available_permissions(request):
    """كل الصلاحيات الممكنة في النظام"""
    perms = [{'code': code, 'label_ar': label, 'label_en': code} for code, label in PERMISSION_CHOICES]
    scopes = [{'code': code, 'label_ar': label, 'label_en': code} for code, label in SCOPE_CHOICES]
    return Response({'permissions': perms, 'scopes': scopes})


# ══════════════════════════════════════
# 2. الأدوار
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_roles(request):
    """قايمة الأدوار بتاعة الشركة"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    roles = CustomRole.objects.filter(
        company=request.user.company, is_active=True
    ).prefetch_related('permissions')

    data = []
    for role in roles:
        data.append({
            'id': role.id,
            'name': role.name,
            'is_active': role.is_active,
            'permissions': [
                {
                    'code': p.permission,
                    'label_ar': dict(PERMISSION_CHOICES).get(p.permission, p.permission),
                    'scope': p.scope,
                    'scope_label_ar': dict(SCOPE_CHOICES).get(p.scope, p.scope),
                }
                for p in role.permissions.all()
            ],
            'users_count': role.users.count(),
        })
    return Response({'roles': data})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_role(request):
    """إنشاء دور جديد"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    name = (request.data.get('name') or '').strip()
    if not name:
        return Response({'error': 'اسم الدور مطلوب'}, status=400)

    if CustomRole.objects.filter(company=request.user.company, name=name).exists():
        return Response({'error': 'الدور موجود بالفعل'}, status=400)

    role = CustomRole.objects.create(company=request.user.company, name=name)

    permissions = request.data.get('permissions', [])
    for perm in permissions:
        code = perm.get('code')
        scope = perm.get('scope', 'company')
        valid_codes = [p[0] for p in PERMISSION_CHOICES]
        valid_scopes = [s[0] for s in SCOPE_CHOICES]
        if code in valid_codes and scope in valid_scopes:
            if code in SOVEREIGN_PERMISSIONS:
                continue  # منع الصلاحيات السيادية في الأدوار المخصصة
            RolePermission.objects.create(role=role, permission=code, scope=scope)

    return Response({'success': True, 'role_id': role.id, 'message': 'تم إنشاء الدور بنجاح'})


@api_view(['PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_role(request, role_id):
    """تعديل دور"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    role = CustomRole.objects.filter(id=role_id, company=request.user.company).first()
    if not role:
        return Response({'error': 'الدور غير موجود'}, status=404)

    name = (request.data.get('name') or '').strip()
    if name:
        role.name = name
        role.save()

    permissions = request.data.get('permissions')
    if permissions is not None:
        role.permissions.all().delete()
        valid_codes = [p[0] for p in PERMISSION_CHOICES]
        valid_scopes = [s[0] for s in SCOPE_CHOICES]
        for perm in permissions:
            code = perm.get('code')
            scope = perm.get('scope', 'company')
            if code in valid_codes and scope in valid_scopes and code not in SOVEREIGN_PERMISSIONS:
                RolePermission.objects.create(role=role, permission=code, scope=scope)

    return Response({'success': True, 'message': 'تم تحديث الدور'})


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_role(request, role_id):
    """حذف دور"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    role = CustomRole.objects.filter(id=role_id, company=request.user.company).first()
    if not role:
        return Response({'error': 'الدور غير موجود'}, status=404)

    role.is_active = False
    role.save()
    return Response({'success': True, 'message': 'تم حذف الدور'})


# ══════════════════════════════════════
# 3. تعيين دور لموظف
# ══════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def assign_role_to_user(request):
    """تعيين دور لمستخدم"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    user_id = request.data.get('user_id')
    role_id = request.data.get('role_id')

    if not user_id or not role_id:
        return Response({'error': 'user_id و role_id مطلوبين'}, status=400)

    target_user = User.objects.filter(id=user_id, company=request.user.company).first()
    if not target_user:
        return Response({'error': 'المستخدم غير موجود'}, status=404)

    role = CustomRole.objects.filter(id=role_id, company=request.user.company, is_active=True).first()
    if not role:
        return Response({'error': 'الدور غير موجود'}, status=404)

    ur, created = UserRole.objects.get_or_create(user=target_user, role=role)
    msg = 'تم تعيين الدور' if created else 'الدور معيّن بالفعل'
    return Response({'success': True, 'message': msg})


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_role_from_user(request):
    """إلغاء دور من مستخدم"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    user_id = request.data.get('user_id')
    role_id = request.data.get('role_id')

    UserRole.objects.filter(
        user_id=user_id,
        role_id=role_id,
        role__company=request.user.company
    ).delete()

    return Response({'success': True, 'message': 'تم إلغاء الدور'})


# ══════════════════════════════════════
# 4. صلاحيات مستخدم معيّن
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_permissions(request, user_id):
    """كل صلاحيات مستخدم معيّن"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    target_user = User.objects.filter(id=user_id, company=request.user.company).first()
    if not target_user:
        return Response({'error': 'المستخدم غير موجود'}, status=404)

    roles = []
    for ur in target_user.custom_roles.select_related('role').prefetch_related('role__permissions'):
        roles.append({
            'role_id': ur.role.id,
            'role_name': ur.role.name,
            'permissions': [
                {
                    'code': p.permission,
                    'label_ar': dict(PERMISSION_CHOICES).get(p.permission, p.permission),
                    'scope': p.scope,
                    'scope_label_ar': dict(SCOPE_CHOICES).get(p.scope, p.scope),
                }
                for p in ur.role.permissions.all()
            ]
        })

    overrides = []
    for ov in target_user.permission_overrides.all():
        overrides.append({
            'permission': ov.permission,
            'label_ar': dict(PERMISSION_CHOICES).get(ov.permission, ov.permission),
            'scope': ov.scope,
            'is_granted': ov.is_granted,
        })

    return Response({
        'user_id': target_user.id,
        'username': target_user.username,
        'full_name': target_user.get_full_name(),
        'roles': roles,
        'overrides': overrides,
    })


# ══════════════════════════════════════
# 5. استثناءات شخصية
# ══════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_user_override(request):
    """تعيين استثناء شخصي لمستخدم"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    user_id = request.data.get('user_id')
    permission = request.data.get('permission')
    scope = request.data.get('scope', 'company')
    is_granted = request.data.get('is_granted', True)

    valid_codes = [p[0] for p in PERMISSION_CHOICES]
    valid_scopes = [s[0] for s in SCOPE_CHOICES]

    if permission not in valid_codes:
        return Response({'error': 'صلاحية غير صحيحة'}, status=400)
    if is_granted and permission in SOVEREIGN_PERMISSIONS:
        return Response({'error': 'لا يمكن منح الصلاحيات السيادية كاستثناء شخصي'}, status=400)
    if scope not in valid_scopes:
        return Response({'error': 'نطاق غير صحيح'}, status=400)

    target_user = User.objects.filter(id=user_id, company=request.user.company).first()
    if not target_user:
        return Response({'error': 'المستخدم غير موجود'}, status=404)

    ov, created = UserPermissionOverride.objects.update_or_create(
        user=target_user,
        permission=permission,
        defaults={'scope': scope, 'is_granted': is_granted}
    )
    msg = '✅ تم منح الصلاحية' if is_granted else '❌ تم سحب الصلاحية'
    return Response({'success': True, 'message': msg})


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_user_override(request):
    """إزالة استثناء شخصي"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    user_id = request.data.get('user_id')
    permission = request.data.get('permission')

    UserPermissionOverride.objects.filter(
        user_id=user_id,
        user__company=request.user.company,
        permission=permission
    ).delete()

    return Response({'success': True, 'message': 'تم إزالة الاستثناء'})


# ══════════════════════════════════════
# 6. قايمة موظفي الشركة (للتعيين)
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def company_users_list(request):
    """قايمة المستخدمين في الشركة"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    users = User.objects.filter(
        company=request.user.company,
        is_active=True
    ).exclude(is_superuser=True)

    data = []
    for u in users:
        roles = list(u.custom_roles.select_related('role').values_list('role__name', flat=True))
        data.append({
            'id': u.id,
            'username': u.username,
            'full_name': u.get_full_name(),
            'role': u.role,
            'assigned_roles': roles,
        })

    return Response({'users': data})

def api_export_permissions(request):
    """تصدير الصلاحيات للموبايل"""
    from rest_framework.authtoken.models import Token
    from django.http import JsonResponse

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return JsonResponse({'error': 'غير مصرح'}, status=401)

    token_key = auth_header.split(' ')[1]
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        user = token.user
    except Token.DoesNotExist:
        return JsonResponse({'error': 'token غير صالح'}, status=401)

    if not is_company_admin(user):
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    from accounts.permissions_export import (
        export_role_pdf, export_role_excel,
        export_user_pdf, export_user_excel,
        export_company_pdf, export_company_excel
    )
    from accounts.permissions_models import CustomRole
    from django.contrib.auth import get_user_model
    User = get_user_model()

    target_type = request.GET.get('type') # role, user, company
    target_id = request.GET.get('id')
    format_type = request.GET.get('format', 'pdf') # pdf, excel

    company = user.company

    if target_type == 'role':
        role = CustomRole.objects.filter(id=target_id, company=company).first()
        if not role: return JsonResponse({'error': 'role not found'}, status=404)
        return export_role_pdf(role) if format_type == 'pdf' else export_role_excel(role)

    elif target_type == 'user':
        # جرّب User ID أولاً، وإذا لم يوجد جرّب Employee ID
        target_user = User.objects.filter(id=target_id, company=company).first()
        if not target_user:
            from employees.models import Employee
            emp = Employee._base_manager.filter(id=target_id, company=company).first()
            if emp and emp.user_id:
                target_user = User.objects.filter(id=emp.user_id, company=company).first()
        if not target_user:
            return JsonResponse({'error': 'user not found'}, status=404)
        return export_user_pdf(target_user) if format_type == 'pdf' else export_user_excel(target_user)

    elif target_type == 'company':
        return export_company_pdf(company) if format_type == 'pdf' else export_company_excel(company)

    return JsonResponse({'error': 'invalid params'}, status=400)


# ══════════════════════════════════════
# 7. صلاحيات اليوزر الحالي
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_permissions(request):
    """صلاحيات اليوزر الحالي"""
    from accounts.permissions_models import get_user_permissions, PERMISSION_CHOICES
    perms = get_user_permissions(request.user)
    return Response({
        'success': True,
        'role': request.user.role,
        'permissions': [
            {
                'code': code,
                'label_ar': dict(PERMISSION_CHOICES).get(code, code),
                'scope': scope,
            }
            for code, scope in perms.items()
        ],
        'permissions_map': perms,
    })


# ══════════════════════════════════════
# 8. الصلاحيات الافتراضية لكل Role
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def default_role_permissions(request):
    """الصلاحيات الافتراضية لكل Role"""
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    from accounts.permissions_models import DEFAULT_ROLE_PERMISSIONS, PERMISSION_CHOICES

    role = request.query_params.get('role')
    perm_labels = dict(PERMISSION_CHOICES)

    if role and role in DEFAULT_ROLE_PERMISSIONS:
        return Response({
            'success': True,
            'role': role,
            'permissions': [
                {
                    'code': code,
                    'label_ar': perm_labels.get(code, code),
                    'scope': scope,
                }
                for code, scope in DEFAULT_ROLE_PERMISSIONS[role]
            ],
        })

    all_defaults = {}
    for r, perms in DEFAULT_ROLE_PERMISSIONS.items():
        all_defaults[r] = [
            {'code': code, 'label_ar': perm_labels.get(code, code), 'scope': scope}
            for code, scope in perms
        ]

    return Response({'success': True, 'defaults': all_defaults})


# ══════════════════════════════════════
# 9. تعديل صلاحيات Role الأساسي (override)
# ══════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_role_default_override(request):
    """
    تعديل صلاحيات Role أساسي لموظف معين عبر UserPermissionOverride
    target_type: 'user' | 'department' | 'branch'
    target_id: id
    permissions: [{'code': ..., 'scope': ..., 'is_granted': True/False}]
    """
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    target_type = request.data.get('target_type', 'user')
    target_id = request.data.get('target_id')
    permissions = request.data.get('permissions', [])

    if not target_id:
        return Response({'error': 'target_id مطلوب'}, status=400)

    valid_codes = [p[0] for p in PERMISSION_CHOICES]

    if target_type == 'user':
        target_user = User.objects.filter(
            id=target_id, company=request.user.company
        ).first()
        if not target_user:
            return Response({'error': 'المستخدم غير موجود'}, status=404)

        users = [target_user]

    elif target_type == 'department':
        from employees.models import Employee
        emps = Employee._base_manager.filter(
            department_id=target_id,
            company=request.user.company,
        ).select_related('user')
        users = [e.user for e in emps if e.user]

    elif target_type == 'branch':
        from employees.models import Employee
        emps = Employee._base_manager.filter(
            branch_id=target_id,
            company=request.user.company,
        ).select_related('user')
        users = [e.user for e in emps if e.user]

    else:
        return Response({'error': 'target_type غير صحيح'}, status=400)

    updated = 0
    for user in users:
        for perm in permissions:
            code = perm.get('code')
            scope = perm.get('scope', 'company')
            is_granted = perm.get('is_granted', True)

            if code not in valid_codes:
                continue

            UserPermissionOverride.objects.update_or_create(
                user=user,
                permission=code,
                defaults={'scope': scope, 'is_granted': is_granted}
            )
            updated += 1

    return Response({
        'success': True,
        'message': f'تم تحديث {updated} صلاحية لـ {len(users)} مستخدم',
        'users_count': len(users),
        'permissions_count': updated,
    })


# ══════════════════════════════════════
# 10. صلاحيات قسم / فرع كامل
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def target_permissions_summary(request):
    """
    ملخص صلاحيات:
    - موظف معين: ?type=user&id=X
    - قسم: ?type=department&id=X
    - فرع: ?type=branch&id=X
    - role: ?type=role&role=manager
    """
    if not is_company_admin(request.user):
        return Response({'error': 'غير مصرح'}, status=403)

    from accounts.permissions_models import get_user_permissions, PERMISSION_CHOICES, DEFAULT_ROLE_PERMISSIONS

    target_type = request.query_params.get('type', 'user')
    target_id = request.query_params.get('id')
    role_name = request.query_params.get('role')
    perm_labels = dict(PERMISSION_CHOICES)

    if target_type == 'role' and role_name:
        perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        return Response({
            'success': True,
            'type': 'role',
            'role': role_name,
            'permissions': [
                {'code': c, 'label_ar': perm_labels.get(c, c), 'scope': s}
                for c, s in perms
            ],
        })

    if not target_id:
        return Response({'error': 'id مطلوب'}, status=400)

    if target_type == 'user':
        target_user = User.objects.filter(
            id=target_id, company=request.user.company
        ).first()
        if not target_user:
            return Response({'error': 'المستخدم غير موجود'}, status=404)

        perms = get_user_permissions(target_user)
        return Response({
            'success': True,
            'type': 'user',
            'user_id': target_user.id,
            'username': target_user.username,
            'full_name': target_user.get_full_name(),
            'role': target_user.role,
            'permissions': [
                {'code': c, 'label_ar': perm_labels.get(c, c), 'scope': s}
                for c, s in perms.items()
            ],
        })

    elif target_type == 'department':
        from employees.models import Employee
        emps = Employee._base_manager.filter(
            department_id=target_id,
            company=request.user.company,
        ).select_related('user')

        summary = {}
        for emp in emps:
            if emp.user:
                for code, scope in get_user_permissions(emp.user).items():
                    if code not in summary:
                        summary[code] = {'count': 0, 'scope': scope}
                    summary[code]['count'] += 1

        return Response({
            'success': True,
            'type': 'department',
            'department_id': target_id,
            'employees_count': emps.count(),
            'permissions_summary': [
                {
                    'code': c,
                    'label_ar': perm_labels.get(c, c),
                    'scope': v['scope'],
                    'employees_with_perm': v['count'],
                }
                for c, v in summary.items()
            ],
        })

    elif target_type == 'branch':
        from employees.models import Employee
        emps = Employee._base_manager.filter(
            branch_id=target_id,
            company=request.user.company,
        ).select_related('user')

        summary = {}
        for emp in emps:
            if emp.user:
                for code, scope in get_user_permissions(emp.user).items():
                    if code not in summary:
                        summary[code] = {'count': 0, 'scope': scope}
                    summary[code]['count'] += 1

        return Response({
            'success': True,
            'type': 'branch',
            'branch_id': target_id,
            'employees_count': emps.count(),
            'permissions_summary': [
                {
                    'code': c,
                    'label_ar': perm_labels.get(c, c),
                    'scope': v['scope'],
                    'employees_with_perm': v['count'],
                }
                for c, v in summary.items()
            ],
        })

    return Response({'error': 'type غير صحيح'}, status=400)
