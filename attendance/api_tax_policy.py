"""APIs - سياسة ضريبة الدخل"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import TaxPolicy
from companies.models import Branch, Department


def _check_hr(user):
    role = getattr(user, 'role', None)
    if not (user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager']):
        raise PermissionDenied('غير مسموح')


def _to_dict(p):
    return {
        'id': p.id,
        'name': p.name,
        'country': p.country,
        'country_display': p.get_country_display(),
        'tax_year': p.tax_year,
        'tax_brackets': p.tax_brackets or [],
        'personal_exemption_single': float(p.personal_exemption_single),
        'personal_exemption_married': float(p.personal_exemption_married),
        'child_exemption': float(p.child_exemption),
        'max_children_exempted': p.max_children_exempted,
        'exempt_social_insurance': p.exempt_social_insurance,
        'exempt_medical_insurance': p.exempt_medical_insurance,
        'additional_exemption': float(p.additional_exemption),
        'calculation_method': p.calculation_method,
        'calculation_method_display': p.get_calculation_method_display(),
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


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def tax_policy_list(request):
    if request.method == 'GET':
        try:
            _check_hr(request.user)
            company = request.user.company
            qs = TaxPolicy._base_manager.filter(company=company).order_by('-created_at')
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

        p = TaxPolicy._base_manager.create(
            company=company,
            name=data.get('name', 'ضريبة الدخل'),
            country=data.get('country', 'EG'),
            tax_year=int(data.get('tax_year', date.today().year)),
            tax_brackets=data.get('tax_brackets', []),
            personal_exemption_single=data.get('personal_exemption_single', 9000),
            personal_exemption_married=data.get('personal_exemption_married', 9000),
            child_exemption=data.get('child_exemption', 0),
            max_children_exempted=int(data.get('max_children_exempted', 3)),
            exempt_social_insurance=bool(data.get('exempt_social_insurance', True)),
            exempt_medical_insurance=bool(data.get('exempt_medical_insurance', True)),
            additional_exemption=data.get('additional_exemption', 0),
            calculation_method=data.get('calculation_method', 'monthly_progressive'),
            scope=scope,
            branch=branch,
            department=department,
            is_active=bool(data.get('is_active', True)),
            start_date=data.get('start_date') or str(date.today()),
            end_date=data.get('end_date') or None,
        )

        return JsonResponse({'success': True, 'message': 'تم إنشاء سياسة الضريبة', 'policy': _to_dict(p)})
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def tax_policy_detail(request, policy_id):
    try:
        _check_hr(request.user)
        company = request.user.company

        p = TaxPolicy._base_manager.filter(id=policy_id, company=company).first()
        if not p:
            return JsonResponse({'success': False, 'error': 'not found'}, status=404)

        if request.method == 'GET':
            return JsonResponse({'success': True, 'policy': _to_dict(p)})

        if request.method == 'DELETE':
            p.delete()
            return JsonResponse({'success': True, 'message': 'تم الحذف'})

        data = json.loads(request.body.decode('utf-8'))
        edit_mode = data.get('edit_mode', 'auto')

        core_fields = ['tax_year', 'tax_brackets', 'personal_exemption_single', 'personal_exemption_married',
                       'child_exemption', 'exempt_social_insurance', 'exempt_medical_insurance',
                       'calculation_method', 'scope', 'branch_id', 'department_id']
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

        # NEW VERSION
        from datetime import date as _date
        from calendar import monthrange
        today = _date.today()
        next_month_start = _date(today.year + 1, 1, 1) if today.month == 12 else _date(today.year, today.month + 1, 1)
        current_month_end = _date(today.year, today.month, monthrange(today.year, today.month)[1])

        p.end_date = current_month_end
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

        new_p = TaxPolicy._base_manager.create(
            company=company,
            name=data.get('name', p.name),
            country=data.get('country', p.country),
            tax_year=int(data.get('tax_year', p.tax_year)),
            tax_brackets=data.get('tax_brackets', p.tax_brackets or []),
            personal_exemption_single=data.get('personal_exemption_single', p.personal_exemption_single),
            personal_exemption_married=data.get('personal_exemption_married', p.personal_exemption_married),
            child_exemption=data.get('child_exemption', p.child_exemption),
            max_children_exempted=int(data.get('max_children_exempted', p.max_children_exempted)),
            exempt_social_insurance=bool(data.get('exempt_social_insurance', p.exempt_social_insurance)),
            exempt_medical_insurance=bool(data.get('exempt_medical_insurance', p.exempt_medical_insurance)),
            additional_exemption=data.get('additional_exemption', p.additional_exemption),
            calculation_method=data.get('calculation_method', p.calculation_method),
            scope=new_scope,
            branch=new_branch,
            department=new_dept,
            is_active=True,
            start_date=next_month_start,
            end_date=None,
            previous_version=p,
            version_number=p.version_number + 1,
            change_reason=(data.get('change_reason') or '').strip(),
            is_superseded=False,
        )

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
def tax_calculate(request):
    """Preview - يحسب الضريبة لدخل معين (للاختبار)"""
    try:
        _check_hr(request.user)
        company = request.user.company
        data = json.loads(request.body.decode('utf-8'))

        policy_id = data.get('policy_id')
        if policy_id:
            p = TaxPolicy._base_manager.filter(id=policy_id, company=company).first()
        else:
            p = TaxPolicy._base_manager.filter(company=company, is_active=True, is_superseded=False).order_by('-created_at').first()

        if not p:
            return JsonResponse({'success': False, 'error': 'no active policy'}, status=404)

        result = p.calculate_annual_tax(
            annual_income=data.get('annual_income', 0),
            marital_status=data.get('marital_status', 'single'),
            children_count=int(data.get('children_count', 0)),
            social_insurance_paid=data.get('social_insurance_paid', 0),
            medical_insurance_paid=data.get('medical_insurance_paid', 0),
            additional_deductions=data.get('additional_deductions', 0),
        )
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
