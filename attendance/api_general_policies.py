"""
APIs - سياسات الخصومات والمكافآت العامة
Deduction Policies:
  GET/POST   /api/mobile/manager/deduction-policies/
  GET/PUT/DELETE /api/mobile/manager/deduction-policies/<id>/

Bonus Policies:
  GET/POST   /api/mobile/manager/bonus-policies/
  GET/PUT/DELETE /api/mobile/manager/bonus-policies/<id>/
"""

from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import CompanyDeductionPolicy, CompanyBonusPolicy
from companies.models import Branch, Department
from employees.models import Employee


def _check_hr(user):
    role = getattr(user, 'role', None)
    if not (
        user.is_superuser
        or user.is_staff
        or role in ['company_admin', 'hr_manager']
    ):
        raise PermissionDenied('مش مسموح')


def _parse_date(val):
    return date.fromisoformat(val) if val else None


def _set_scope(policy, data, company):
    scope = data.get('scope', policy.scope)
    policy.scope = scope
    policy.branch = None
    policy.department = None
    policy.specific_employees.clear()

    if scope == 'branch' and data.get('branch_id'):
        policy.branch = Branch.objects.get(id=data['branch_id'], company=company)
    elif scope == 'department' and data.get('department_id'):
        policy.department = Department.objects.get(id=data['department_id'], company=company)
    elif scope == 'employees' and data.get('employee_ids'):
        emps = Employee._base_manager.filter(id__in=data['employee_ids'], company=company)
        policy.specific_employees.set(emps)


# ══════════════════════════════════════════════
# Deduction Policies
# ══════════════════════════════════════════════

def _deduction_to_dict(p):
    return {
        'id': p.id,
        'deduction_type': p.deduction_type,
        'deduction_type_display': p.get_deduction_type_display(),
        'name_ar': p.name_ar,
        'name_en': p.name_en,
        'amount': float(p.amount),
        'scope': p.scope,
        'scope_display': p.get_scope_display(),
        'branch_id': p.branch_id,
        'branch_name': p.branch.name_ar if p.branch else None,
        'department_id': p.department_id,
        'department_name': p.department.name_ar if p.department else None,
        'specific_employees': list(p.specific_employees.values_list('id', flat=True)),
        'is_monthly': p.is_monthly,
        'is_active': p.is_active,
        'start_date': str(p.start_date),
        'end_date': str(p.end_date) if p.end_date else None,
        'notes': p.notes,
        'created_at': str(p.created_at),
    }


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def deduction_policies_list(request):
    try:
        _check_hr(request.user)
        company = request.user.company

        if request.method == 'GET':
            qs = CompanyDeductionPolicy._base_manager.filter(company=company).order_by('-created_at')
            return JsonResponse({'success': True, 'count': qs.count(), 'results': [_deduction_to_dict(p) for p in qs]})

        elif request.method == 'POST':
            data = json.loads(request.body)
            for f in ['deduction_type', 'name_ar', 'amount', 'scope', 'start_date']:
                if not data.get(f):
                    return JsonResponse({'success': False, 'error': f'{f} مطلوب'}, status=400)

            policy = CompanyDeductionPolicy(
                company=company,
                deduction_type=data['deduction_type'],
                name_ar=data['name_ar'],
                name_en=data.get('name_en', ''),
                amount=data['amount'],
                is_monthly=data.get('is_monthly', True),
                is_active=data.get('is_active', True),
                start_date=_parse_date(data['start_date']),
                end_date=_parse_date(data.get('end_date')),
                notes=data.get('notes', ''),
                scope=data.get('scope', 'company'),
            )
            policy.save()
            _set_scope(policy, data, company)
            policy.save()
            return JsonResponse({'success': True, 'message': 'تم إضافة الخصم العام', 'policy': _deduction_to_dict(policy)}, status=201)

        return JsonResponse({'error': 'Method not allowed'}, status=405)

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def deduction_policy_detail(request, policy_id):
    try:
        _check_hr(request.user)
        company = request.user.company
        policy = CompanyDeductionPolicy._base_manager.get(id=policy_id, company=company)
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except CompanyDeductionPolicy.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'مش موجود'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'policy': _deduction_to_dict(policy)})

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            for f in ['deduction_type', 'name_ar', 'name_en', 'amount', 'is_monthly', 'is_active', 'notes']:
                if f in data:
                    setattr(policy, f, data[f])
            if 'start_date' in data:
                policy.start_date = _parse_date(data['start_date'])
            if 'end_date' in data:
                policy.end_date = _parse_date(data.get('end_date'))
            if 'scope' in data:
                _set_scope(policy, data, request.user.company)
            policy.save()
            return JsonResponse({'success': True, 'message': 'تم التعديل', 'policy': _deduction_to_dict(policy)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        policy.delete()
        return JsonResponse({'success': True, 'message': 'تم الحذف'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ══════════════════════════════════════════════
# Bonus Policies
# ══════════════════════════════════════════════

def _bonus_to_dict(p):
    return {
        'id': p.id,
        'bonus_type': p.bonus_type,
        'bonus_type_display': p.get_bonus_type_display(),
        'name_ar': p.name_ar,
        'name_en': p.name_en,
        'amount': float(p.amount),
        'scope': p.scope,
        'scope_display': p.get_scope_display(),
        'branch_id': p.branch_id,
        'branch_name': p.branch.name_ar if p.branch else None,
        'department_id': p.department_id,
        'department_name': p.department.name_ar if p.department else None,
        'specific_employees': list(p.specific_employees.values_list('id', flat=True)),
        'is_monthly': p.is_monthly,
        'is_active': p.is_active,
        'start_date': str(p.start_date),
        'end_date': str(p.end_date) if p.end_date else None,
        'notes': p.notes,
        'created_at': str(p.created_at),
    }


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def bonus_policies_list(request):
    try:
        _check_hr(request.user)
        company = request.user.company

        if request.method == 'GET':
            qs = CompanyBonusPolicy._base_manager.filter(company=company).order_by('-created_at')
            return JsonResponse({'success': True, 'count': qs.count(), 'results': [_bonus_to_dict(p) for p in qs]})

        elif request.method == 'POST':
            data = json.loads(request.body)
            for f in ['bonus_type', 'name_ar', 'amount', 'scope', 'start_date']:
                if not data.get(f):
                    return JsonResponse({'success': False, 'error': f'{f} مطلوب'}, status=400)

            policy = CompanyBonusPolicy(
                company=company,
                bonus_type=data['bonus_type'],
                name_ar=data['name_ar'],
                name_en=data.get('name_en', ''),
                amount=data['amount'],
                is_monthly=data.get('is_monthly', True),
                is_active=data.get('is_active', True),
                start_date=_parse_date(data['start_date']),
                end_date=_parse_date(data.get('end_date')),
                notes=data.get('notes', ''),
                scope=data.get('scope', 'company'),
            )
            policy.save()
            _set_scope(policy, data, company)
            policy.save()
            return JsonResponse({'success': True, 'message': 'تم إضافة المكافأة العامة', 'policy': _bonus_to_dict(policy)}, status=201)

        return JsonResponse({'error': 'Method not allowed'}, status=405)

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def bonus_policy_detail(request, policy_id):
    try:
        _check_hr(request.user)
        company = request.user.company
        policy = CompanyBonusPolicy._base_manager.get(id=policy_id, company=company)
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except CompanyBonusPolicy.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'مش موجود'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'policy': _bonus_to_dict(policy)})

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            for f in ['bonus_type', 'name_ar', 'name_en', 'amount', 'is_monthly', 'is_active', 'notes']:
                if f in data:
                    setattr(policy, f, data[f])
            if 'start_date' in data:
                policy.start_date = _parse_date(data['start_date'])
            if 'end_date' in data:
                policy.end_date = _parse_date(data.get('end_date'))
            if 'scope' in data:
                _set_scope(policy, data, request.user.company)
            policy.save()
            return JsonResponse({'success': True, 'message': 'تم التعديل', 'policy': _bonus_to_dict(policy)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        policy.delete()
        return JsonResponse({'success': True, 'message': 'تم الحذف'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
