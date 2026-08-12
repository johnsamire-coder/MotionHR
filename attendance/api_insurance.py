"""
APIs - سياسات التأمين (اجتماعي + طبي)
"""

from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import CompanyInsurancePolicy
from companies.models import Branch, Department
from employees.models import Employee


def _check_hr_permission(user):
    role = getattr(user, 'role', None)
    if not (user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager']):
        raise PermissionDenied('غير مسموح')


# ── M2M helpers ────────────────────────────────────────────
def _m2m_read_ids(policy):
    try:
        through = policy.specific_employees.through
        src_fk = emp_fk = None
        for f in through._meta.fields:
            rm = getattr(getattr(f, 'remote_field', None), 'model', None)
            if rm == policy.__class__:
                src_fk = f.attname
            elif getattr(getattr(rm, '_meta', None), 'label_lower', '') == 'employees.employee':
                emp_fk = f.attname
        if not src_fk or not emp_fk:
            return []
        return list(through._base_manager.filter(**{src_fk: policy.id}).values_list(emp_fk, flat=True))
    except Exception:
        return []


def _m2m_set_ids(policy, company, employee_ids):
    try:
        ids = [int(x) for x in (employee_ids or []) if str(x).isdigit()]
        valid = list(Employee._base_manager.filter(company=company, id__in=ids).values_list('id', flat=True))
        through = policy.specific_employees.through
        src_fk = emp_fk = None
        for f in through._meta.fields:
            rm = getattr(getattr(f, 'remote_field', None), 'model', None)
            if rm == policy.__class__:
                src_fk = f.attname
            elif getattr(getattr(rm, '_meta', None), 'label_lower', '') == 'employees.employee':
                emp_fk = f.attname
        if not src_fk or not emp_fk:
            return
        through._base_manager.filter(**{src_fk: policy.id}).delete()
        rows = [through(**{src_fk: policy.id, emp_fk: eid}) for eid in valid]
        if rows:
            through._base_manager.bulk_create(rows, ignore_conflicts=True)
    except Exception:
        pass


def _policy_to_dict(policy):
    return {
        'id': policy.id,
        'insurance_type': policy.insurance_type,
        'insurance_type_display': policy.get_insurance_type_display(),
        'name_ar': policy.name_ar,
        'name_en': policy.name_en,
        'company_share_type': policy.company_share_type,
        'company_share_type_display': policy.get_company_share_type_display(),
        'company_share_value': float(policy.company_share_value),
        'employee_share_type': policy.employee_share_type,
        'employee_share_type_display': policy.get_employee_share_type_display(),
        'employee_share_value': float(policy.employee_share_value),
        'calculation_base': policy.calculation_base,
        'calculation_base_display': policy.get_calculation_base_display(),
        'min_insured_salary': float(policy.min_insured_salary) if policy.min_insured_salary else None,
        'max_insured_salary': float(policy.max_insured_salary) if policy.max_insured_salary else None,
        'scope': policy.scope,
        'scope_display': policy.get_scope_display(),
        'branch_id': policy.branch_id,
        'branch_name': policy.branch.name_ar if policy.branch else None,
        'department_id': policy.department_id,
        'department_name': policy.department.name_ar if policy.department else None,
        'specific_employees': _m2m_read_ids(policy),
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
# LIST + CREATE
# ══════════════════════════════════════
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def insurance_policies_list(request):
    if request.method == 'GET':
        try:
            _check_hr_permission(request.user)
            company = request.user.company

            # فلاتر اختيارية
            insurance_type = request.GET.get('type')
            is_active = request.GET.get('active')

            qs = CompanyInsurancePolicy._base_manager.filter(company=company)
            if insurance_type in ('social', 'medical'):
                qs = qs.filter(insurance_type=insurance_type)
            if is_active in ('true', '1'):
                qs = qs.filter(is_active=True)
            elif is_active in ('false', '0'):
                qs = qs.filter(is_active=False)

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

        # التحقق من الحقول الإلزامية
        insurance_type = data.get('insurance_type')
        if insurance_type not in ('social', 'medical'):
            return JsonResponse({'success': False, 'error': 'insurance_type must be social or medical'}, status=400)

        name_ar = (data.get('name_ar') or '').strip()
        if not name_ar:
            return JsonResponse({'success': False, 'error': 'name_ar is required'}, status=400)

        start_date = data.get('start_date') or str(date.today())

        # scope validation
        scope = data.get('scope', 'company')
        branch_id = data.get('branch_id')
        department_id = data.get('department_id')

        branch = None
        department = None
        if scope == 'branch' and branch_id:
            branch = Branch._base_manager.filter(id=branch_id, company=company).first()
        if scope == 'department' and department_id:
            department = Department._base_manager.filter(id=department_id, company=company).first()

        policy = CompanyInsurancePolicy._base_manager.create(
            company=company,
            insurance_type=insurance_type,
            name_ar=name_ar,
            name_en=(data.get('name_en') or '').strip(),
            company_share_type=data.get('company_share_type', 'percent'),
            company_share_value=data.get('company_share_value', 0),
            employee_share_type=data.get('employee_share_type', 'percent'),
            employee_share_value=data.get('employee_share_value', 0),
            calculation_base=data.get('calculation_base', 'basic'),
            min_insured_salary=data.get('min_insured_salary') or None,
            max_insured_salary=data.get('max_insured_salary') or None,
            scope=scope,
            branch=branch,
            department=department,
            is_active=bool(data.get('is_active', True)),
            start_date=start_date,
            end_date=data.get('end_date') or None,
        )

        # موظفين محددين
        if scope == 'employees':
            _m2m_set_ids(policy, company, data.get('specific_employees', []))

        return JsonResponse({
            'success': True,
            'message': 'تم إنشاء سياسة التأمين',
            'policy': _policy_to_dict(policy),
        })
    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ══════════════════════════════════════
# DETAIL + UPDATE + DELETE
# ══════════════════════════════════════
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def insurance_policy_detail(request, policy_id):
    try:
        _check_hr_permission(request.user)
        company = request.user.company

        policy = CompanyInsurancePolicy._base_manager.filter(id=policy_id, company=company).first()
        if not policy:
            return JsonResponse({'success': False, 'error': 'policy not found'}, status=404)

        if request.method == 'GET':
            return JsonResponse({'success': True, 'policy': _policy_to_dict(policy)})

        if request.method == 'DELETE':
            policy.delete()
            return JsonResponse({'success': True, 'message': 'تم حذف السياسة'})

        # PUT / PATCH — نعمل نسخة جديدة (Versioning)
        data = json.loads(request.body.decode('utf-8'))

        # مود التعديل:
        # - metadata_only: فقط تعديل معلومات (اسم، تاريخ نهاية، تفعيل/تعطيل)
        # - new_version: تعديل جوهري (نسب أو قيم) => نسخة جديدة
        edit_mode = data.get('edit_mode', 'auto')

        # الحقول اللي تعتبر "جوهرية" (لو اتغيرت => نسخة جديدة)
        core_fields = [
            'company_share_type', 'company_share_value',
            'employee_share_type', 'employee_share_value',
            'calculation_base',
            'min_insured_salary', 'max_insured_salary',
            'scope', 'branch_id', 'department_id', 'specific_employees',
        ]

        # نشوف هل فيه تغيير في حقل جوهري
        is_core_change = False
        for f in core_fields:
            if f in data:
                is_core_change = True
                break

        # نحدد المود تلقائياً
        if edit_mode == 'auto':
            edit_mode = 'new_version' if is_core_change else 'metadata_only'

        # ═══════ MODE 1: METADATA ONLY ═══════
        # (تعديل الاسم أو تعطيل/تفعيل فقط - بدون نسخة جديدة)
        if edit_mode == 'metadata_only':
            if 'name_ar' in data:
                policy.name_ar = (data['name_ar'] or '').strip()
            if 'name_en' in data:
                policy.name_en = (data['name_en'] or '').strip()
            if 'change_reason' in data:
                policy.change_reason = (data['change_reason'] or '').strip()
            if 'is_active' in data:
                policy.is_active = bool(data['is_active'])
            if 'end_date' in data:
                policy.end_date = data['end_date'] or None

            policy.save()

            return JsonResponse({
                'success': True,
                'message': 'تم التحديث (بدون نسخة جديدة)',
                'edit_mode': 'metadata_only',
                'policy': _policy_to_dict(policy),
            })

        # ═══════ MODE 2: NEW VERSION ═══════
        # تعديل جوهري => نسخة جديدة تبدأ من أول الشهر التالي
        from datetime import date, timedelta
        from calendar import monthrange

        today = date.today()
        # أول يوم في الشهر التالي
        if today.month == 12:
            next_month_start = date(today.year + 1, 1, 1)
        else:
            next_month_start = date(today.year, today.month + 1, 1)

        # آخر يوم في الشهر الحالي
        last_day = monthrange(today.year, today.month)[1]
        current_month_end = date(today.year, today.month, last_day)

        # ─── قفل النسخة القديمة ───
        policy.end_date = current_month_end
        policy.is_superseded = True
        policy.save()

        # ─── إنشاء النسخة الجديدة ───
        new_policy_data = {
            'company': company,
            'insurance_type': data.get('insurance_type', policy.insurance_type),
            'name_ar': (data.get('name_ar') or policy.name_ar).strip(),
            'name_en': (data.get('name_en') or policy.name_en).strip(),
            'company_share_type': data.get('company_share_type', policy.company_share_type),
            'company_share_value': data.get('company_share_value', policy.company_share_value) or 0,
            'employee_share_type': data.get('employee_share_type', policy.employee_share_type),
            'employee_share_value': data.get('employee_share_value', policy.employee_share_value) or 0,
            'calculation_base': data.get('calculation_base', policy.calculation_base),
            'min_insured_salary': data.get('min_insured_salary', policy.min_insured_salary) or None,
            'max_insured_salary': data.get('max_insured_salary', policy.max_insured_salary) or None,
            'scope': data.get('scope', policy.scope),
            'is_active': True,
            'start_date': next_month_start,
            'end_date': None,
            # ─── Versioning ───
            'previous_version': policy,
            'version_number': policy.version_number + 1,
            'change_reason': (data.get('change_reason') or '').strip(),
            'is_superseded': False,
        }

        # scope-related fields
        scope = new_policy_data['scope']
        if scope == 'branch':
            branch_id = data.get('branch_id', policy.branch_id)
            new_policy_data['branch'] = Branch._base_manager.filter(id=branch_id, company=company).first() if branch_id else None
        if scope == 'department':
            dept_id = data.get('department_id', policy.department_id)
            new_policy_data['department'] = Department._base_manager.filter(id=dept_id, company=company).first() if dept_id else None

        new_policy = CompanyInsurancePolicy._base_manager.create(**new_policy_data)

        # الموظفين المحددين
        if scope == 'employees':
            emp_ids = data.get('specific_employees', _m2m_read_ids(policy))
            _m2m_set_ids(new_policy, company, emp_ids)

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


# ══════════════════════════════════════
# HELPER — تجميع تأمينات موظف معين (للاستخدام في payroll)
# ══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_insurances(request, employee_id):
    """
    يرجع تأمينات موظف معين (اجتماعي + طبي مع الحساب)
    مفيد للـ payslip
    """
    try:
        _check_hr_permission(request.user)
        company = request.user.company

        employee = Employee._base_manager.filter(id=employee_id, company=company).first()
        if not employee:
            return JsonResponse({'success': False, 'error': 'employee not found'}, status=404)

        basic_salary = float(getattr(employee, 'basic_salary', 0) or 0)
        custom_insurance_salary = float(getattr(employee, 'insurance_base_salary', 0) or 0) if getattr(employee, 'insurance_base_salary', None) else None

        # نجيب التاريخ المطلوب (افتراضي: النهاردة)
        from datetime import date as _date
        target_date_str = request.GET.get('date')
        try:
            target_date = _date.fromisoformat(target_date_str) if target_date_str else _date.today()
        except Exception:
            target_date = _date.today()

        # نجيب السياسات السارية في التاريخ ده
        from django.db.models import Q
        policies = CompanyInsurancePolicy._base_manager.filter(
            company=company,
            is_active=True,
            start_date__lte=target_date,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=target_date)
        )

        social = {'has_policy': False}
        medical = {'has_policy': False}

        for policy in policies:
            if not policy.applies_to_employee(employee):
                continue

            # هنبعت الـ employee object، الدالة هتقرر تستخدم أي مبلغ
            calc = policy.calculate_deduction(employee)
            info = {
                'has_policy': True,
                'policy_id': policy.id,
                'policy_name': policy.name_ar,
                'calculation_base': calc.get('calculation_base', 'basic'),
                'base_amount_used': str(calc.get('base_salary', 0)),
                'insured_salary': str(calc['insured_salary']),
                'company_share': str(calc['company_share']),
                'employee_share': str(calc['employee_share']),
            }

            if policy.insurance_type == 'social':
                social = info
            elif policy.insurance_type == 'medical':
                medical = info

        def _get(d, k):
            try:
                return float(d.get(k, 0)) if d.get('has_policy') else 0
            except Exception:
                return 0

        return JsonResponse({
            'success': True,
            'employee_id': employee.id,
            'target_date': str(target_date),
            'employee_info': {
                'basic_salary': basic_salary,
                'insurance_base_salary': custom_insurance_salary,
            },
            'social': social,
            'medical': medical,
            'total_employee_deduction': round(_get(social, 'employee_share') + _get(medical, 'employee_share'), 2),
            'total_company_contribution': round(_get(social, 'company_share') + _get(medical, 'company_share'), 2),
        })

    except PermissionDenied as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
