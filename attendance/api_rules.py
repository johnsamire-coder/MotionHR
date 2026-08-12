"""
APIs موحدة - قواعد الجزاءات + المكافآت + البدلات
كل واحدة بتدعم Tiers + Scoping + Versioning
"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import PenaltyRule, BonusRule, AllowanceRule
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


# ═══════════════════════════════════════════════════════════════
# Base Serializer + Handler
# ═══════════════════════════════════════════════════════════════
def _base_rule_dict(rule, type_field_name):
    return {
        'id': rule.id,
        'name': rule.name,
        type_field_name: getattr(rule, type_field_name, ''),
        f'{type_field_name}_display': getattr(rule, f'get_{type_field_name}_display')() if hasattr(rule, f'get_{type_field_name}_display') else '',
        'tiers': rule.tiers or [],
        'scope': rule.scope,
        'scope_display': rule.get_scope_display(),
        'branch_id': rule.branch_id,
        'branch_name': rule.branch.name_ar if rule.branch else None,
        'department_id': rule.department_id,
        'department_name': rule.department.name_ar if rule.department else None,
        'specific_employees': _m2m_read_ids(rule),
        'version_number': rule.version_number,
        'previous_version_id': rule.previous_version_id,
        'is_superseded': rule.is_superseded,
        'change_reason': rule.change_reason or '',
        'has_next_versions': rule.next_versions.exists() if hasattr(rule, 'next_versions') else False,
        'is_active': rule.is_active,
        'start_date': str(rule.start_date),
        'end_date': str(rule.end_date) if rule.end_date else None,
        'created_at': str(rule.created_at),
        'updated_at': str(rule.updated_at),
    }


def _penalty_to_dict(rule):
    d = _base_rule_dict(rule, 'penalty_type')
    d.update({
        'grace_amount': rule.grace_amount,
        'warnings_enabled': rule.warnings_enabled,
        'first_warning_after': rule.first_warning_after,
        'second_warning_after': rule.second_warning_after,
        'termination_after': rule.termination_after,
    })
    return d


def _bonus_to_dict(rule):
    d = _base_rule_dict(rule, 'bonus_type')
    d.update({
        'max_per_day': float(rule.max_per_day),
        'max_per_month': float(rule.max_per_month),
        'requires_approval': rule.requires_approval,
    })
    return d


def _allowance_to_dict(rule):
    d = _base_rule_dict(rule, 'allowance_type')
    d.update({
        'calculation_type': rule.calculation_type,
        'fixed_amount': float(rule.fixed_amount),
        'min_work_hours_per_day': rule.min_work_hours_per_day,
    })
    return d


# ═══════════════════════════════════════════════════════════════
# Generic Handlers
# ═══════════════════════════════════════════════════════════════
def _handle_list_create(request, ModelClass, to_dict_func, extra_create_fields=None):
    if request.method == 'GET':
        try:
            _check_hr_permission(request.user)
            company = request.user.company
            active_only = request.GET.get('active_only') in ('true', '1')
            qs = ModelClass._base_manager.filter(company=company)
            if active_only:
                qs = qs.filter(is_active=True, is_superseded=False)
            qs = qs.order_by('-created_at')
            return JsonResponse({
                'success': True,
                'count': qs.count(),
                'results': [to_dict_func(r) for r in qs],
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

        base_kwargs = {
            'company': company,
            'name': data.get('name', ''),
            'tiers': data.get('tiers', []),
            'scope': scope,
            'branch': branch,
            'department': department,
            'is_active': bool(data.get('is_active', True)),
            'start_date': data.get('start_date') or str(date.today()),
            'end_date': data.get('end_date') or None,
        }

        # الحقول الإضافية لكل نوع
        if extra_create_fields:
            base_kwargs.update(extra_create_fields(data))

        rule = ModelClass._base_manager.create(**base_kwargs)

        if scope == 'employees':
            _m2m_set_ids(rule, company, data.get('specific_employees', []))

        return JsonResponse({
            'success': True,
            'message': 'تم إنشاء القاعدة',
            'rule': to_dict_func(rule),
        })
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _handle_detail(request, rule_id, ModelClass, to_dict_func, core_fields, extra_update_fn=None):
    try:
        _check_hr_permission(request.user)
        company = request.user.company

        rule = ModelClass._base_manager.filter(id=rule_id, company=company).first()
        if not rule:
            return JsonResponse({'success': False, 'error': 'not found'}, status=404)

        if request.method == 'GET':
            return JsonResponse({'success': True, 'rule': to_dict_func(rule)})

        if request.method == 'DELETE':
            rule.delete()
            return JsonResponse({'success': True, 'message': 'تم الحذف'})

        data = json.loads(request.body.decode('utf-8'))
        edit_mode = data.get('edit_mode', 'auto')
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
                'message': 'تم التحديث (بدون نسخة جديدة)',
                'edit_mode': 'metadata_only',
                'rule': to_dict_func(rule),
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

        # نجهز kwargs بناءً على الـ ModelClass
        new_kwargs = {
            'company': company,
            'name': data.get('name', rule.name),
            'tiers': data.get('tiers', rule.tiers or []),
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

        # نسخ حقل النوع (penalty_type / bonus_type / allowance_type)
        for type_field in ('penalty_type', 'bonus_type', 'allowance_type'):
            if hasattr(rule, type_field):
                new_kwargs[type_field] = data.get(type_field, getattr(rule, type_field))

        # حقول إضافية لكل نوع
        if extra_update_fn:
            new_kwargs.update(extra_update_fn(data, rule))

        new_rule = ModelClass._base_manager.create(**new_kwargs)

        if new_scope == 'employees':
            emp_ids = data.get('specific_employees', _m2m_read_ids(rule))
            _m2m_set_ids(new_rule, company, emp_ids)

        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء النسخة رقم {new_rule.version_number} - سارية من {next_month_start}',
            'edit_mode': 'new_version',
            'old_rule': to_dict_func(rule),
            'new_rule': to_dict_func(new_rule),
        })

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════
# PENALTY RULES
# ═══════════════════════════════════════════════════════════════
def _penalty_extra_create(data):
    return {
        'penalty_type': data.get('penalty_type', 'late_arrival'),
        'grace_amount': int(data.get('grace_amount', 0)),
        'warnings_enabled': bool(data.get('warnings_enabled', False)),
        'first_warning_after': int(data.get('first_warning_after', 3)),
        'second_warning_after': int(data.get('second_warning_after', 5)),
        'termination_after': int(data.get('termination_after', 10)),
    }

def _penalty_extra_update(data, rule):
    return {
        'grace_amount': int(data.get('grace_amount', rule.grace_amount)),
        'warnings_enabled': bool(data.get('warnings_enabled', rule.warnings_enabled)),
        'first_warning_after': int(data.get('first_warning_after', rule.first_warning_after)),
        'second_warning_after': int(data.get('second_warning_after', rule.second_warning_after)),
        'termination_after': int(data.get('termination_after', rule.termination_after)),
    }


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def penalty_list(request):
    return _handle_list_create(request, PenaltyRule, _penalty_to_dict, _penalty_extra_create)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def penalty_detail(request, rule_id):
    core = ['penalty_type', 'tiers', 'grace_amount', 'scope', 'branch_id', 'department_id', 'specific_employees']
    return _handle_detail(request, rule_id, PenaltyRule, _penalty_to_dict, core, _penalty_extra_update)


# ═══════════════════════════════════════════════════════════════
# BONUS RULES
# ═══════════════════════════════════════════════════════════════
def _bonus_extra_create(data):
    return {
        'bonus_type': data.get('bonus_type', 'overtime'),
        'max_per_day': data.get('max_per_day', 0),
        'max_per_month': data.get('max_per_month', 0),
        'requires_approval': bool(data.get('requires_approval', False)),
    }

def _bonus_extra_update(data, rule):
    return {
        'max_per_day': data.get('max_per_day', rule.max_per_day),
        'max_per_month': data.get('max_per_month', rule.max_per_month),
        'requires_approval': bool(data.get('requires_approval', rule.requires_approval)),
    }


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def bonus_list(request):
    return _handle_list_create(request, BonusRule, _bonus_to_dict, _bonus_extra_create)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def bonus_detail(request, rule_id):
    core = ['bonus_type', 'tiers', 'max_per_day', 'max_per_month', 'scope', 'branch_id', 'department_id', 'specific_employees']
    return _handle_detail(request, rule_id, BonusRule, _bonus_to_dict, core, _bonus_extra_update)


# ═══════════════════════════════════════════════════════════════
# ALLOWANCE RULES
# ═══════════════════════════════════════════════════════════════
def _allowance_extra_create(data):
    return {
        'allowance_type': data.get('allowance_type', 'field_work'),
        'calculation_type': data.get('calculation_type', 'fixed_monthly'),
        'fixed_amount': data.get('fixed_amount', 0),
        'min_work_hours_per_day': int(data.get('min_work_hours_per_day', 0)),
    }

def _allowance_extra_update(data, rule):
    return {
        'calculation_type': data.get('calculation_type', rule.calculation_type),
        'fixed_amount': data.get('fixed_amount', rule.fixed_amount),
        'min_work_hours_per_day': int(data.get('min_work_hours_per_day', rule.min_work_hours_per_day)),
    }


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def allowance_list(request):
    return _handle_list_create(request, AllowanceRule, _allowance_to_dict, _allowance_extra_create)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def allowance_detail(request, rule_id):
    core = ['allowance_type', 'calculation_type', 'fixed_amount', 'tiers', 'scope', 'branch_id', 'department_id', 'specific_employees']
    return _handle_detail(request, rule_id, AllowanceRule, _allowance_to_dict, core, _allowance_extra_update)
