"""APIs - سياسة مكافأة نهاية الخدمة"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import EndOfServicePolicy
from companies.models import Branch, Department


def _check_hr(user):
    role = getattr(user, 'role', None)
    if not (user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager']):
        raise PermissionDenied('غير مسموح')


def _to_dict(p):
    return {
        'id': p.id,
        'name': p.name,
        'salary_base_type': p.salary_base_type,
        'salary_base_type_display': p.get_salary_base_type_display(),
        'service_tiers': p.service_tiers or [],
        'min_service_months': p.min_service_months,
        'max_months_cap': float(p.max_months_cap),
        'percent_on_resignation': float(p.percent_on_resignation),
        'percent_on_termination': float(p.percent_on_termination),
        'percent_on_death': float(p.percent_on_death),
        'percent_on_retirement': float(p.percent_on_retirement),
        'percent_on_disability': float(p.percent_on_disability),
        'percent_on_misconduct': float(p.percent_on_misconduct),
        'include_bonuses_in_base': p.include_bonuses_in_base,
        'partial_year_calculation': p.partial_year_calculation,
        'partial_year_calculation_display': p.get_partial_year_calculation_display(),
        'tax_exempted': p.tax_exempted,
        'scope': p.scope,
        'scope_display': p.get_scope_display(),
        'branch_id': p.branch_id,
        'branch_name': p.branch.name_ar if p.branch else None,
        'department_id': p.department_id,
        'department_name': p.department.name_ar if p.department else None,
        'version_number': p.version_number,
        'is_superseded': p.is_superseded,
        'change_reason': p.change_reason or '',
        'is_active': p.is_active,
        'start_date': str(p.start_date),
        'end_date': str(p.end_date) if p.end_date else None,
        'created_at': str(p.created_at),
    }


def _extract_fields(data, defaults=None):
    fields = [
        'name', 'salary_base_type', 'service_tiers',
        'min_service_months', 'max_months_cap',
        'percent_on_resignation', 'percent_on_termination',
        'percent_on_death', 'percent_on_retirement',
        'percent_on_disability', 'percent_on_misconduct',
        'include_bonuses_in_base', 'partial_year_calculation', 'tax_exempted',
    ]
    result = {}
    for f in fields:
        if f in data:
            result[f] = data[f]
        elif defaults and hasattr(defaults, f):
            result[f] = getattr(defaults, f)
    return result


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_policy_list(request):
    if request.method == 'GET':
        try:
            _check_hr(request.user)
            company = request.user.company
            qs = EndOfServicePolicy._base_manager.filter(company=company).order_by('-created_at')
            return JsonResponse({'success': True, 'count': qs.count(), 'results': [_to_dict(p) for p in qs]})
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    try:
        _check_hr(request.user)
        company = request.user.company
        data = json.loads(request.body.decode('utf-8'))

        scope = data.get('scope', 'company')
        branch = Branch._base_manager.filter(id=data.get('branch_id'), company=company).first() if scope == 'branch' else None
        department = Department._base_manager.filter(id=data.get('department_id'), company=company).first() if scope == 'department' else None

        kwargs = {
            'company': company,
            'scope': scope,
            'branch': branch,
            'department': department,
            'is_active': bool(data.get('is_active', True)),
            'start_date': data.get('start_date') or str(date.today()),
            'end_date': data.get('end_date') or None,
        }
        kwargs.update(_extract_fields(data))

        p = EndOfServicePolicy._base_manager.create(**kwargs)
        return JsonResponse({'success': True, 'message': 'تم إنشاء السياسة', 'policy': _to_dict(p)})
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_policy_detail(request, policy_id):
    try:
        _check_hr(request.user)
        company = request.user.company

        p = EndOfServicePolicy._base_manager.filter(id=policy_id, company=company).first()
        if not p:
            return JsonResponse({'success': False, 'error': 'not found'}, status=404)

        if request.method == 'GET':
            return JsonResponse({'success': True, 'policy': _to_dict(p)})

        if request.method == 'DELETE':
            p.delete()
            return JsonResponse({'success': True, 'message': 'تم الحذف'})

        data = json.loads(request.body.decode('utf-8'))
        edit_mode = data.get('edit_mode', 'auto')

        core_fields = ['salary_base_type', 'service_tiers', 'min_service_months',
                       'max_months_cap', 'percent_on_resignation', 'percent_on_termination',
                       'partial_year_calculation', 'scope']
        is_core = any(f in data for f in core_fields)
        if edit_mode == 'auto':
            edit_mode = 'new_version' if is_core else 'metadata_only'

        if edit_mode == 'metadata_only':
            if 'name' in data: p.name = data['name']
            if 'is_active' in data: p.is_active = bool(data['is_active'])
            if 'end_date' in data: p.end_date = data['end_date'] or None
            if 'change_reason' in data: p.change_reason = (data['change_reason'] or '').strip()
            p.save()
            return JsonResponse({'success': True, 'message': 'تم التحديث', 'edit_mode': 'metadata_only', 'policy': _to_dict(p)})

        from datetime import date as _date
        from calendar import monthrange
        today = _date.today()
        next_month = _date(today.year + 1, 1, 1) if today.month == 12 else _date(today.year, today.month + 1, 1)
        current_end = _date(today.year, today.month, monthrange(today.year, today.month)[1])

        p.end_date = current_end
        p.is_superseded = True
        p.save()

        new_scope = data.get('scope', p.scope)
        new_branch = p.branch
        new_dept = p.department
        if new_scope == 'branch':
            bid = data.get('branch_id', p.branch_id)
            new_branch = Branch._base_manager.filter(id=bid, company=company).first() if bid else None
        if new_scope == 'department':
            did = data.get('department_id', p.department_id)
            new_dept = Department._base_manager.filter(id=did, company=company).first() if did else None

        new_kwargs = {
            'company': company,
            'scope': new_scope,
            'branch': new_branch,
            'department': new_dept,
            'is_active': True,
            'start_date': next_month,
            'end_date': None,
            'previous_version': p,
            'version_number': p.version_number + 1,
            'change_reason': (data.get('change_reason') or '').strip(),
            'is_superseded': False,
        }
        new_kwargs.update(_extract_fields(data, defaults=p))

        new_p = EndOfServicePolicy._base_manager.create(**new_kwargs)
        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء النسخة {new_p.version_number}',
            'edit_mode': 'new_version',
            'old_policy': _to_dict(p),
            'new_policy': _to_dict(new_p),
        })

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_calculate(request):
    """يحسب مكافأة نهاية خدمة لموظف/سيناريو معين"""
    try:
        _check_hr(request.user)
        company = request.user.company
        data = json.loads(request.body.decode('utf-8'))

        policy_id = data.get('policy_id')
        if policy_id:
            p = EndOfServicePolicy._base_manager.filter(id=policy_id, company=company).first()
        else:
            p = EndOfServicePolicy._base_manager.filter(company=company, is_active=True, is_superseded=False).order_by('-created_at').first()

        if not p:
            return JsonResponse({'success': False, 'error': 'no active policy'}, status=404)

        result = p.calculate_eos(
            service_years=float(data.get('service_years', 0)),
            monthly_salary=float(data.get('monthly_salary', 0)),
            termination_reason=data.get('termination_reason', 'resignation'),
        )
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
