"""
APIs - سياسات البدلات العامة
GET    /api/attendance/allowance-policies/
POST   /api/attendance/allowance-policies/
GET    /api/attendance/allowance-policies/<id>/
PUT    /api/attendance/allowance-policies/<id>/
DELETE /api/attendance/allowance-policies/<id>/
"""

from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import CompanyAllowancePolicy
from companies.models import Branch, Department
from employees.models import Employee


def _check_hr_permission(user):
    """لازم يكون HR أو أدمن"""
    role = getattr(user, 'role', None)
    if not (
        user.is_superuser
        or user.is_staff
        or role in ['company_admin', 'hr_manager']
    ):
        raise PermissionDenied('مش مسموح')


def _policy_to_dict(policy):
    return {
        'id': policy.id,
        'allowance_type': policy.allowance_type,
        'allowance_type_display': policy.get_allowance_type_display(),
        'name_ar': policy.name_ar,
        'name_en': policy.name_en,
        'amount': float(policy.amount),
        'scope': policy.scope,
        'scope_display': policy.get_scope_display(),
        'branch_id': policy.branch_id,
        'branch_name': policy.branch.name_ar if policy.branch else None,
        'department_id': policy.department_id,
        'department_name': policy.department.name_ar if policy.department else None,
        'specific_employees': list(
            policy.specific_employees.values_list('id', flat=True)
        ),
        'is_monthly': policy.is_monthly,
        'is_active': policy.is_active,
        'start_date': str(policy.start_date),
        'end_date': str(policy.end_date) if policy.end_date else None,
        'created_at': str(policy.created_at),
    }


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def allowance_policies_list(request):
    """GET: قائمة البدلات العامة | POST: إضافة بدل جديد"""

    if request.method == 'GET':
        try:
            _check_hr_permission(request.user)
            company = request.user.company
            policies = CompanyAllowancePolicy._base_manager.filter(
                company=company
            ).order_by('-created_at')
            return JsonResponse({
                'success': True,
                'count': policies.count(),
                'results': [_policy_to_dict(p) for p in policies],
            })
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            _check_hr_permission(request.user)
            data = json.loads(request.body)
            company = request.user.company

            # validation
            required = ['allowance_type', 'name_ar', 'amount', 'scope', 'start_date']
            for field in required:
                if not data.get(field):
                    return JsonResponse(
                        {'success': False, 'error': f'{field} مطلوب'},
                        status=400
                    )

            scope = data['scope']
            branch = None
            department = None

            if scope == 'branch':
                if not data.get('branch_id'):
                    return JsonResponse(
                        {'success': False, 'error': 'branch_id مطلوب لو scope=branch'},
                        status=400
                    )
                branch = Branch.objects.get(id=data['branch_id'], company=company)

            elif scope == 'department':
                if not data.get('department_id'):
                    return JsonResponse(
                        {'success': False, 'error': 'department_id مطلوب لو scope=department'},
                        status=400
                    )
                department = Department.objects.get(id=data['department_id'], company=company)

            policy = CompanyAllowancePolicy._base_manager.create(
                company=company,
                allowance_type=data['allowance_type'],
                name_ar=data['name_ar'],
                name_en=data.get('name_en', ''),
                amount=data['amount'],
                scope=scope,
                branch=branch,
                department=department,
                is_monthly=data.get('is_monthly', True),
                is_active=data.get('is_active', True),
                start_date=date.fromisoformat(data['start_date']),
                end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
            )

            # لو scope=employees نضيف الموظفين المحددين
            if scope == 'employees' and data.get('employee_ids'):
                emps = Employee._base_manager.filter(
                    id__in=data['employee_ids'],
                    company=company,
                )
                policy.specific_employees.set(emps)

            return JsonResponse({
                'success': True,
                'message': 'تم إضافة البدل العام بنجاح',
                'policy': _policy_to_dict(policy),
            }, status=201)

        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def allowance_policy_detail(request, policy_id):
    """GET / PUT / DELETE لبدل محدد"""
    try:
        _check_hr_permission(request.user)
        company = request.user.company
        policy = CompanyAllowancePolicy._base_manager.get(id=policy_id, company=company)
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except CompanyAllowancePolicy.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'مش موجود'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'policy': _policy_to_dict(policy)})

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            company = request.user.company

            if 'allowance_type' in data:
                policy.allowance_type = data['allowance_type']
            if 'name_ar' in data:
                policy.name_ar = data['name_ar']
            if 'name_en' in data:
                policy.name_en = data['name_en']
            if 'amount' in data:
                policy.amount = data['amount']
            if 'is_monthly' in data:
                policy.is_monthly = data['is_monthly']
            if 'is_active' in data:
                policy.is_active = data['is_active']
            if 'start_date' in data:
                policy.start_date = date.fromisoformat(data['start_date'])
            if 'end_date' in data:
                policy.end_date = date.fromisoformat(data['end_date']) if data['end_date'] else None

            if 'scope' in data:
                policy.scope = data['scope']
                policy.branch = None
                policy.department = None
                policy.specific_employees.clear()

                if data['scope'] == 'branch' and data.get('branch_id'):
                    policy.branch = Branch.objects.get(id=data['branch_id'], company=company)
                elif data['scope'] == 'department' and data.get('department_id'):
                    policy.department = Department.objects.get(id=data['department_id'], company=company)
                elif data['scope'] == 'employees' and data.get('employee_ids'):
                    emps = Employee._base_manager.filter(
                        id__in=data['employee_ids'],
                        company=company,
                    )
                    policy.specific_employees.set(emps)

            policy.save()
            return JsonResponse({
                'success': True,
                'message': 'تم التعديل بنجاح',
                'policy': _policy_to_dict(policy),
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        policy.delete()
        return JsonResponse({'success': True, 'message': 'تم الحذف بنجاح'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
