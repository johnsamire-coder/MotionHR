"""APIs - قواعد الإجازات الشاملة"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import LeaveRule
from companies.models import Branch, Department
from employees.models import Employee


def _check_hr_permission(user):
    role = getattr(user, 'role', None)
    if not (user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager']):
        raise PermissionDenied('غير مسموح')


def _m2m_read_ids(rule):
    try:
        through = rule.specific_employees.through
        src_fk = emp_fk = None
        for f in through._meta.fields:
            rm = getattr(getattr(f, 'remote_field', None), 'model', None)
            if rm == rule.__class__:
                src_fk = f.attname
            elif getattr(getattr(rm, '_meta', None), 'label_lower', '') == 'employees.employee':
                emp_fk = f.attname
        if not src_fk or not emp_fk:
            return []
        return list(through._base_manager.filter(**{src_fk: rule.id}).values_list(emp_fk, flat=True))
    except Exception:
        return []


def _m2m_set_ids(rule, company, employee_ids):
    try:
        ids = [int(x) for x in (employee_ids or []) if str(x).isdigit()]
        valid = list(Employee._base_manager.filter(company=company, id__in=ids).values_list('id', flat=True))
        through = rule.specific_employees.through
        src_fk = emp_fk = None
        for f in through._meta.fields:
            rm = getattr(getattr(f, 'remote_field', None), 'model', None)
            if rm == rule.__class__:
                src_fk = f.attname
            elif getattr(getattr(rm, '_meta', None), 'label_lower', '') == 'employees.employee':
                emp_fk = f.attname
        if not src_fk or not emp_fk:
            return
        through._base_manager.filter(**{src_fk: rule.id}).delete()
        rows = [through(**{src_fk: rule.id, emp_fk: eid}) for eid in valid]
        if rows:
            through._base_manager.bulk_create(rows, ignore_conflicts=True)
    except Exception:
        pass


def _rule_to_dict(rule):
    return {
        'id': rule.id,
        'name': rule.name,
        # Annual
        'annual_leave_enabled': rule.annual_leave_enabled,
        'annual_leave_days': rule.annual_leave_days,
        'annual_earn_start': rule.annual_earn_start,
        'annual_earn_start_display': rule.get_annual_earn_start_display(),
        'annual_carry_over': rule.annual_carry_over,
        'annual_max_carry_over': rule.annual_max_carry_over,
        'annual_cash_out_allowed': rule.annual_cash_out_allowed,
        'annual_min_notice_days': rule.annual_min_notice_days,
        'annual_max_consecutive_days': rule.annual_max_consecutive_days,
        # Sick
        'sick_leave_enabled': rule.sick_leave_enabled,
        'sick_leave_max_days': rule.sick_leave_max_days,
        'sick_requires_certificate_after': rule.sick_requires_certificate_after,
        'sick_paid_percentage': float(rule.sick_paid_percentage),
        # Emergency
        'emergency_leave_enabled': rule.emergency_leave_enabled,
        'emergency_max_days': rule.emergency_max_days,
        'emergency_max_per_month': rule.emergency_max_per_month,
        'emergency_min_notice_hours': rule.emergency_min_notice_hours,
        'emergency_requires_reason': rule.emergency_requires_reason,
        'emergency_deducted_from_annual': rule.emergency_deducted_from_annual,
        # Maternity
        'maternity_enabled': rule.maternity_enabled,
        'maternity_days': rule.maternity_days,
        'maternity_paid': rule.maternity_paid,
        'maternity_paid_percentage': float(rule.maternity_paid_percentage),
        'maternity_extension_days': rule.maternity_extension_days,
        'maternity_max_times': rule.maternity_max_times,
        # Paternity
        'paternity_enabled': rule.paternity_enabled,
        'paternity_days': rule.paternity_days,
        'paternity_paid': rule.paternity_paid,
        # Unpaid
        'unpaid_leave_enabled': rule.unpaid_leave_enabled,
        'unpaid_deduction_type': rule.unpaid_deduction_type,
        'unpaid_deduction_type_display': rule.get_unpaid_deduction_type_display(),
        'unpaid_custom_amount': float(rule.unpaid_custom_amount),
        'max_unpaid_days_per_year': rule.max_unpaid_days_per_year,
        'unpaid_requires_approval': rule.unpaid_requires_approval,
        # Hajj
        'hajj_enabled': rule.hajj_enabled,
        'hajj_days': rule.hajj_days,
        'hajj_paid': rule.hajj_paid,
        'hajj_once_in_lifetime': rule.hajj_once_in_lifetime,
        'hajj_min_service_years': rule.hajj_min_service_years,
        # Bereavement
        'bereavement_enabled': rule.bereavement_enabled,
        'bereavement_days_first_degree': rule.bereavement_days_first_degree,
        'bereavement_days_second_degree': rule.bereavement_days_second_degree,
        # Marriage
        'marriage_enabled': rule.marriage_enabled,
        'marriage_days': rule.marriage_days,
        'marriage_once_in_lifetime': rule.marriage_once_in_lifetime,
        # Scope
        'scope': rule.scope,
        'scope_display': rule.get_scope_display(),
        'branch_id': rule.branch_id,
        'branch_name': rule.branch.name_ar if rule.branch else None,
        'department_id': rule.department_id,
        'department_name': rule.department.name_ar if rule.department else None,
        'specific_employees': _m2m_read_ids(rule),
        # Versioning
        'version_number': rule.version_number,
        'previous_version_id': rule.previous_version_id,
        'is_superseded': rule.is_superseded,
        'change_reason': rule.change_reason or '',
        'has_next_versions': rule.next_versions.exists() if hasattr(rule, 'next_versions') else False,
        # Metadata
        'is_active': rule.is_active,
        'start_date': str(rule.start_date),
        'end_date': str(rule.end_date) if rule.end_date else None,
        'created_at': str(rule.created_at),
        'updated_at': str(rule.updated_at),
    }


def _extract_fields(data, defaults=None):
    """يجمع كل الحقول من data لتمريرها للـ Model"""
    fields = [
        'annual_leave_enabled', 'annual_leave_days', 'annual_earn_start',
        'annual_carry_over', 'annual_max_carry_over', 'annual_cash_out_allowed',
        'annual_min_notice_days', 'annual_max_consecutive_days',
        'sick_leave_enabled', 'sick_leave_max_days', 'sick_requires_certificate_after', 'sick_paid_percentage',
        'emergency_leave_enabled', 'emergency_max_days', 'emergency_max_per_month',
        'emergency_min_notice_hours', 'emergency_requires_reason', 'emergency_deducted_from_annual',
        'maternity_enabled', 'maternity_days', 'maternity_paid', 'maternity_paid_percentage',
        'maternity_extension_days', 'maternity_max_times',
        'paternity_enabled', 'paternity_days', 'paternity_paid',
        'unpaid_leave_enabled', 'unpaid_deduction_type', 'unpaid_custom_amount',
        'max_unpaid_days_per_year', 'unpaid_requires_approval',
        'hajj_enabled', 'hajj_days', 'hajj_paid', 'hajj_once_in_lifetime', 'hajj_min_service_years',
        'bereavement_enabled', 'bereavement_days_first_degree', 'bereavement_days_second_degree',
        'marriage_enabled', 'marriage_days', 'marriage_once_in_lifetime',
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
def leave_rule_list(request):
    if request.method == 'GET':
        try:
            _check_hr_permission(request.user)
            company = request.user.company
            active_only = request.GET.get('active_only') in ('true', '1')
            qs = LeaveRule._base_manager.filter(company=company)
            if active_only:
                qs = qs.filter(is_active=True, is_superseded=False)
            qs = qs.order_by('-created_at')
            return JsonResponse({
                'success': True,
                'count': qs.count(),
                'results': [_rule_to_dict(r) for r in qs],
            })
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # POST
    try:
        _check_hr_permission(request.user)
        company = request.user.company
        data = json.loads(request.body.decode('utf-8'))

        scope = data.get('scope', 'company')
        branch = None
        department = None
        if scope == 'branch' and data.get('branch_id'):
            branch = Branch._base_manager.filter(id=data['branch_id'], company=company).first()
        if scope == 'department' and data.get('department_id'):
            department = Department._base_manager.filter(id=data['department_id'], company=company).first()

        kwargs = {
            'company': company,
            'name': data.get('name', 'قواعد الإجازات الافتراضية'),
            'scope': scope,
            'branch': branch,
            'department': department,
            'is_active': bool(data.get('is_active', True)),
            'start_date': data.get('start_date') or str(date.today()),
            'end_date': data.get('end_date') or None,
        }
        kwargs.update(_extract_fields(data))

        rule = LeaveRule._base_manager.create(**kwargs)

        if scope == 'employees':
            _m2m_set_ids(rule, company, data.get('specific_employees', []))

        return JsonResponse({
            'success': True,
            'message': 'تم إنشاء قواعد الإجازات',
            'rule': _rule_to_dict(rule),
        })
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leave_rule_detail(request, rule_id):
    try:
        _check_hr_permission(request.user)
        company = request.user.company

        rule = LeaveRule._base_manager.filter(id=rule_id, company=company).first()
        if not rule:
            return JsonResponse({'success': False, 'error': 'not found'}, status=404)

        if request.method == 'GET':
            return JsonResponse({'success': True, 'rule': _rule_to_dict(rule)})

        if request.method == 'DELETE':
            rule.delete()
            return JsonResponse({'success': True, 'message': 'تم الحذف'})

        data = json.loads(request.body.decode('utf-8'))
        edit_mode = data.get('edit_mode', 'auto')

        # الحقول الجوهرية (لو تغيرت = نسخة جديدة)
        core_fields = ['annual_leave_days', 'sick_leave_max_days', 'maternity_days', 'paternity_days',
                       'unpaid_deduction_type', 'emergency_max_days', 'scope']
        is_core_change = any(f in data for f in core_fields)
        if edit_mode == 'auto':
            edit_mode = 'new_version' if is_core_change else 'metadata_only'

        if edit_mode == 'metadata_only':
            if 'name' in data: rule.name = data['name']
            if 'is_active' in data: rule.is_active = bool(data['is_active'])
            if 'end_date' in data: rule.end_date = data['end_date'] or None
            if 'change_reason' in data: rule.change_reason = (data['change_reason'] or '').strip()
            rule.save()
            return JsonResponse({
                'success': True,
                'message': 'تم التحديث',
                'edit_mode': 'metadata_only',
                'rule': _rule_to_dict(rule),
            })

        # NEW VERSION
        from datetime import date as _date
        from calendar import monthrange
        today = _date.today()
        if today.month == 12:
            next_month_start = _date(today.year + 1, 1, 1)
        else:
            next_month_start = _date(today.year, today.month + 1, 1)
        last_day = monthrange(today.year, today.month)[1]
        current_month_end = _date(today.year, today.month, last_day)

        rule.end_date = current_month_end
        rule.is_superseded = True
        rule.save()

        new_scope = data.get('scope', rule.scope)
        new_branch = rule.branch
        new_dept = rule.department
        if new_scope == 'branch':
            bid = data.get('branch_id', rule.branch_id)
            new_branch = Branch._base_manager.filter(id=bid, company=company).first() if bid else None
        if new_scope == 'department':
            did = data.get('department_id', rule.department_id)
            new_dept = Department._base_manager.filter(id=did, company=company).first() if did else None

        new_kwargs = {
            'company': company,
            'name': data.get('name', rule.name),
            'scope': new_scope,
            'branch': new_branch,
            'department': new_dept,
            'is_active': True,
            'start_date': next_month_start,
            'end_date': None,
            'previous_version': rule,
            'version_number': rule.version_number + 1,
            'change_reason': (data.get('change_reason') or '').strip(),
            'is_superseded': False,
        }
        new_kwargs.update(_extract_fields(data, defaults=rule))

        new_rule = LeaveRule._base_manager.create(**new_kwargs)

        if new_scope == 'employees':
            emp_ids = data.get('specific_employees', _m2m_read_ids(rule))
            _m2m_set_ids(new_rule, company, emp_ids)

        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء النسخة رقم {new_rule.version_number} - سارية من {next_month_start}',
            'edit_mode': 'new_version',
            'old_rule': _rule_to_dict(rule),
            'new_rule': _rule_to_dict(new_rule),
        })

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
