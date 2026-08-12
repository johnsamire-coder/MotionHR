"""
APIs - سياسات دورة الرواتب
"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import CompanyPayrollCyclePolicy


def _check_hr_permission(user):
    role = getattr(user, 'role', None)
    if not (user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager']):
        raise PermissionDenied('غير مسموح')


def _policy_to_dict(policy):
    return {
        'id': policy.id,
        'cycle_type': policy.cycle_type,
        'cycle_type_display': policy.get_cycle_type_display(),
        'cutoff_day': policy.cutoff_day,
        'pay_day': policy.pay_day,
        'weekly_pay_day': policy.weekly_pay_day,
        'weekly_pay_day_display': policy.get_weekly_pay_day_display(),
        'holiday_handling': policy.holiday_handling,
        'holiday_handling_display': policy.get_holiday_handling_display(),
        'default_currency': policy.default_currency,
        'default_currency_display': policy.get_default_currency_display(),
        'proration_method': policy.proration_method,
        'proration_method_display': policy.get_proration_method_display(),
        'working_days_per_month': policy.working_days_per_month,
        'new_employee_handling': policy.new_employee_handling,
        'new_employee_handling_display': policy.get_new_employee_handling_display(),
        'payslip_notify_days_before': policy.payslip_notify_days_before,
        'auto_generate_payroll': policy.auto_generate_payroll,
        'payroll_ref_prefix': policy.payroll_ref_prefix,
        'approval_level': policy.approval_level,
        'approval_level_display': policy.get_approval_level_display(),
        'require_approval_before_pay': policy.require_approval_before_pay,
        'first_approver_role': policy.first_approver_role or '',
        'second_approver_role': policy.second_approver_role or '',
        'third_approver_role': policy.third_approver_role or '',
        'is_active': policy.is_active,
        'start_date': str(policy.start_date),
        'end_date': str(policy.end_date) if policy.end_date else None,
        # Versioning
        'version_number': policy.version_number,
        'previous_version_id': policy.previous_version_id,
        'is_superseded': policy.is_superseded,
        'change_reason': policy.change_reason or '',
        'has_next_versions': policy.next_versions.exists() if hasattr(policy, 'next_versions') else False,
        'created_at': str(policy.created_at),
        'updated_at': str(policy.updated_at),
    }


# ══════════════════════════════════════
# GET (current active) + LIST + CREATE
# ══════════════════════════════════════
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def payroll_cycle_list(request):
    if request.method == 'GET':
        try:
            _check_hr_permission(request.user)
            company = request.user.company

            # لو بيطلب فقط النسخة الحالية النشطة
            active_only = request.GET.get('active_only') in ('true', '1')

            qs = CompanyPayrollCyclePolicy._base_manager.filter(company=company)
            if active_only:
                qs = qs.filter(is_active=True, is_superseded=False)

            qs = qs.order_by('-created_at')
            return JsonResponse({
                'success': True,
                'count': qs.count(),
                'results': [_policy_to_dict(p) for p in qs],
            })
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # POST — إنشاء
    try:
        _check_hr_permission(request.user)
        company = request.user.company
        data = json.loads(request.body.decode('utf-8'))

        start_date = data.get('start_date') or str(date.today())

        policy = CompanyPayrollCyclePolicy._base_manager.create(
            company=company,
            cycle_type=data.get('cycle_type', 'calendar_month'),
            cutoff_day=int(data.get('cutoff_day', 25)),
            pay_day=int(data.get('pay_day', 5)),
            weekly_pay_day=data.get('weekly_pay_day', 'sunday'),
            holiday_handling=data.get('holiday_handling', 'before'),
            default_currency=data.get('default_currency', 'EGP'),
            proration_method=data.get('proration_method', '30_days'),
            working_days_per_month=int(data.get('working_days_per_month', 22)),
            new_employee_handling=data.get('new_employee_handling', 'prorated'),
            payslip_notify_days_before=int(data.get('payslip_notify_days_before', 2)),
            auto_generate_payroll=bool(data.get('auto_generate_payroll', True)),
            payroll_ref_prefix=data.get('payroll_ref_prefix', 'PR'),
            approval_level=data.get('approval_level', 'hr_only'),
            require_approval_before_pay=bool(data.get('require_approval_before_pay', True)),
            first_approver_role=data.get('first_approver_role', 'hr_manager') or 'hr_manager',
            second_approver_role=data.get('second_approver_role', '') or '',
            third_approver_role=data.get('third_approver_role', '') or '',
            is_active=bool(data.get('is_active', True)),
            start_date=start_date,
            end_date=data.get('end_date') or None,
        )

        return JsonResponse({
            'success': True,
            'message': 'تم إنشاء سياسة دورة الرواتب',
            'policy': _policy_to_dict(policy),
        })
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ══════════════════════════════════════
# DETAIL + UPDATE (with Versioning) + DELETE
# ══════════════════════════════════════
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def payroll_cycle_detail(request, policy_id):
    try:
        _check_hr_permission(request.user)
        company = request.user.company

        policy = CompanyPayrollCyclePolicy._base_manager.filter(id=policy_id, company=company).first()
        if not policy:
            return JsonResponse({'success': False, 'error': 'policy not found'}, status=404)

        if request.method == 'GET':
            return JsonResponse({'success': True, 'policy': _policy_to_dict(policy)})

        if request.method == 'DELETE':
            policy.delete()
            return JsonResponse({'success': True, 'message': 'تم حذف السياسة'})

        # PUT / PATCH — Versioning
        data = json.loads(request.body.decode('utf-8'))

        edit_mode = data.get('edit_mode', 'auto')

        core_fields = [
            'cycle_type', 'cutoff_day', 'pay_day', 'weekly_pay_day',
            'holiday_handling', 'default_currency',
            'proration_method', 'working_days_per_month',
            'new_employee_handling',
            'approval_level', 'require_approval_before_pay',
            'first_approver_role', 'second_approver_role', 'third_approver_role',
        ]

        is_core_change = any(f in data for f in core_fields)

        if edit_mode == 'auto':
            edit_mode = 'new_version' if is_core_change else 'metadata_only'

        # ═══ METADATA ONLY ═══
        if edit_mode == 'metadata_only':
            if 'payslip_notify_days_before' in data:
                policy.payslip_notify_days_before = int(data['payslip_notify_days_before'])
            if 'auto_generate_payroll' in data:
                policy.auto_generate_payroll = bool(data['auto_generate_payroll'])
            if 'payroll_ref_prefix' in data:
                policy.payroll_ref_prefix = data['payroll_ref_prefix']
            if 'is_active' in data:
                policy.is_active = bool(data['is_active'])
            if 'end_date' in data:
                policy.end_date = data['end_date'] or None
            if 'change_reason' in data:
                policy.change_reason = (data['change_reason'] or '').strip()

            policy.save()

            return JsonResponse({
                'success': True,
                'message': 'تم التحديث (بدون نسخة جديدة)',
                'edit_mode': 'metadata_only',
                'policy': _policy_to_dict(policy),
            })

        # ═══ NEW VERSION ═══
        from datetime import date as _date, timedelta
        from calendar import monthrange

        today = _date.today()
        if today.month == 12:
            next_month_start = _date(today.year + 1, 1, 1)
        else:
            next_month_start = _date(today.year, today.month + 1, 1)

        last_day = monthrange(today.year, today.month)[1]
        current_month_end = _date(today.year, today.month, last_day)

        # قفل النسخة القديمة
        policy.end_date = current_month_end
        policy.is_superseded = True
        policy.save()

        # إنشاء النسخة الجديدة
        new_policy = CompanyPayrollCyclePolicy._base_manager.create(
            company=company,
            cycle_type=data.get('cycle_type', policy.cycle_type),
            cutoff_day=int(data.get('cutoff_day', policy.cutoff_day)),
            pay_day=int(data.get('pay_day', policy.pay_day)),
            weekly_pay_day=data.get('weekly_pay_day', policy.weekly_pay_day),
            holiday_handling=data.get('holiday_handling', policy.holiday_handling),
            default_currency=data.get('default_currency', policy.default_currency),
            proration_method=data.get('proration_method', policy.proration_method),
            working_days_per_month=int(data.get('working_days_per_month', policy.working_days_per_month)),
            new_employee_handling=data.get('new_employee_handling', policy.new_employee_handling),
            payslip_notify_days_before=int(data.get('payslip_notify_days_before', policy.payslip_notify_days_before)),
            auto_generate_payroll=bool(data.get('auto_generate_payroll', policy.auto_generate_payroll)),
            payroll_ref_prefix=data.get('payroll_ref_prefix', policy.payroll_ref_prefix),
            approval_level=data.get('approval_level', policy.approval_level),
            require_approval_before_pay=bool(data.get('require_approval_before_pay', policy.require_approval_before_pay)),
            first_approver_role=data.get('first_approver_role', policy.first_approver_role) or 'hr_manager',
            second_approver_role=data.get('second_approver_role', policy.second_approver_role) or '',
            third_approver_role=data.get('third_approver_role', policy.third_approver_role) or '',
            is_active=True,
            start_date=next_month_start,
            end_date=None,
            previous_version=policy,
            version_number=policy.version_number + 1,
            change_reason=(data.get('change_reason') or '').strip(),
            is_superseded=False,
        )

        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء النسخة رقم {new_policy.version_number} - سارية من {next_month_start}',
            'edit_mode': 'new_version',
            'old_policy': _policy_to_dict(policy),
            'new_policy': _policy_to_dict(new_policy),
        })

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
