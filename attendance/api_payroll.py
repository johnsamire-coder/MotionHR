"""
MotionHR - Payroll API (v4 - Phase 15 Payroll Pro)
"""
from datetime import datetime
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .payroll_rules import calculate_effective_payroll

User = get_user_model()

DEFAULT_SETTINGS = {
    'late_deduction_per_minute': 1.0,
    'absence_deduction_per_day': 200.0,
    'overtime_rate_per_hour': 50.0,
    'insurance_mode': 'none',
    'insurance_fixed_amount': 0.0,
    'insurance_percent': 0.0,
}


def _check_manager(user):
    role = getattr(user, 'role', None)
    return (
        user.is_superuser
        or user.is_staff
        or role in ['company_admin', 'hr_manager', 'manager']
    )


def _get_company_employees(user):
    try:
        from employees.models import Employee
    except ImportError:
        return []
    company = getattr(user, 'company', None)
    if company:
        return Employee.objects.filter(company=company)
    return Employee.objects.all()


def _parse_month(request):
    source = request.GET if request.method == 'GET' else request.data
    try:
        year = int(source.get('year', datetime.now().year))
        month = int(source.get('month', datetime.now().month))
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    return year, month


def _get_lang(request):
    lang = request.GET.get('lang')
    if not lang and hasattr(request, 'data'):
        lang = request.data.get('lang')
    if lang not in ['ar', 'en']:
        lang = 'ar'
    return lang


def _get_payroll_settings(user):
    """
    جيب إعدادات الرواتب من DB أو الافتراضية
    """
    try:
        from .payroll_settings_model import PayrollSettings
        company = getattr(user, 'company', None)
        if company:
            s = PayrollSettings.objects.filter(company=company).first()
            if s:
                return {
                    'late_deduction_per_minute': float(s.late_deduction_per_minute),
                    'absence_deduction_per_day': float(s.absence_deduction_per_day),
                    'overtime_rate_per_hour': float(s.overtime_rate_per_hour),
                    'insurance_mode': getattr(s, 'insurance_mode', 'none'),
                    'insurance_fixed_amount': float(getattr(s, 'insurance_fixed_amount', 0) or 0),
                    'insurance_percent': float(getattr(s, 'insurance_percent', 0) or 0),
                }
    except Exception:
        pass
    return DEFAULT_SETTINGS.copy()


def _serialize_summary_row(payroll):
    return {
        'employee_id': payroll['employee_id'],
        'employee_code': payroll.get('employee_code', ''),
        'employee_name': payroll['employee_name'],
        'branch_name': payroll.get('branch_name', ''),
        'department_name': payroll.get('department_name', ''),
        'job_title_name': payroll.get('job_title_name', ''),
        'currency': payroll.get('currency', 'EGP'),

        'basic_salary': payroll['basic_salary'],
        'allowances_total': payroll.get('allowances_total', 0),
        'overtime_bonus': payroll.get('overtime_bonus', 0),
        'bonuses_total': payroll.get('bonuses_total', 0),
        'gross_salary': payroll.get('gross_salary', 0),

        'late_deduction': payroll.get('late_deduction', 0),
        'absence_deduction': payroll.get('absence_deduction', 0),
        'insurance_deduction': payroll.get('insurance_deduction', 0),
        'installments_total': payroll.get('installments_total', 0),
        'penalties_total': payroll.get('penalties_total', 0),
        'extra_deductions_total': payroll.get('extra_deductions_total', 0),
        'total_deductions': payroll['total_deductions'],

        'net_salary': payroll['net_salary'],

        'total_working_days': payroll['total_working_days'],
        'attended_days': payroll['attended_days'],
        'present_days': payroll.get('present_days', 0),
        'absent_days': payroll['absent_days'],
        'late_days': payroll['late_days'],
        'mission_days': payroll['mission_days'],
        'on_leave_days': payroll['on_leave_days'],
        'total_work_hours': payroll['total_work_hours'],
        'overtime_hours': payroll['overtime_hours'],
        'total_late_minutes': payroll.get('total_late_minutes', 0),
    }


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_summary(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    lang = _get_lang(request)
    employees = _get_company_employees(user)
    settings = _get_payroll_settings(user)

    results = []
    grand_total_salary = 0
    grand_total_allowances = 0
    grand_total_overtime = 0
    grand_total_bonuses = 0
    grand_total_deductions = 0
    grand_total_net = 0

    for emp in employees:
        payroll = calculate_effective_payroll(emp, year, month, settings, lang=lang)
        results.append(_serialize_summary_row(payroll))

        grand_total_salary += payroll['basic_salary']
        grand_total_allowances += payroll.get('allowances_total', 0)
        grand_total_overtime += payroll.get('overtime_bonus', 0)
        grand_total_bonuses += payroll.get('bonuses_total', 0)
        grand_total_deductions += payroll['total_deductions']
        grand_total_net += payroll['net_salary']

    return Response({
        'year': year,
        'month': month,
        'lang': lang,
        'total_employees': len(results),

        'grand_total_salary': round(grand_total_salary, 2),
        'grand_total_allowances': round(grand_total_allowances, 2),
        'grand_total_overtime': round(grand_total_overtime, 2),
        'grand_total_bonuses': round(grand_total_bonuses, 2),
        'grand_total_deductions': round(grand_total_deductions, 2),
        'grand_total_net': round(grand_total_net, 2),

        'payroll_settings': settings,
        'employees': results,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_employee_detail(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    lang = _get_lang(request)
    employee_id = request.GET.get('employee_id')

    if not employee_id:
        return Response({'error': 'employee_id required'}, status=400)

    try:
        from employees.models import Employee
        emp = Employee.objects.get(id=employee_id)
    except Exception:
        return Response({'error': 'Employee not found'}, status=404)

    settings = _get_payroll_settings(user)
    payroll = calculate_effective_payroll(emp, year, month, settings, lang=lang)
    return Response({'year': year, 'month': month, 'lang': lang, **payroll})


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_settings(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    if request.method == 'GET':
        settings = _get_payroll_settings(user)
        return Response(settings)

    try:
        from .payroll_settings_model import PayrollSettings
        company = getattr(user, 'company', None)
        data = request.data

        obj, created = PayrollSettings.objects.get_or_create(
            company=company,
            defaults={
                'late_deduction_per_minute': data.get('late_deduction_per_minute', 1.0),
                'absence_deduction_per_day': data.get('absence_deduction_per_day', 200.0),
                'overtime_rate_per_hour': data.get('overtime_rate_per_hour', 50.0),
                'insurance_mode': data.get('insurance_mode', 'none'),
                'insurance_fixed_amount': data.get('insurance_fixed_amount', 0),
                'insurance_percent': data.get('insurance_percent', 0),
            }
        )
        if not created:
            if 'late_deduction_per_minute' in data:
                obj.late_deduction_per_minute = data['late_deduction_per_minute']
            if 'absence_deduction_per_day' in data:
                obj.absence_deduction_per_day = data['absence_deduction_per_day']
            if 'overtime_rate_per_hour' in data:
                obj.overtime_rate_per_hour = data['overtime_rate_per_hour']
            if 'insurance_mode' in data:
                obj.insurance_mode = data['insurance_mode']
            if 'insurance_fixed_amount' in data:
                obj.insurance_fixed_amount = data['insurance_fixed_amount']
            if 'insurance_percent' in data:
                obj.insurance_percent = data['insurance_percent']
            obj.save()

        return Response({
            'status': 'saved',
            'late_deduction_per_minute': float(obj.late_deduction_per_minute),
            'absence_deduction_per_day': float(obj.absence_deduction_per_day),
            'overtime_rate_per_hour': float(obj.overtime_rate_per_hour),
            'insurance_mode': getattr(obj, 'insurance_mode', 'none'),
            'insurance_fixed_amount': float(getattr(obj, 'insurance_fixed_amount', 0) or 0),
            'insurance_percent': float(getattr(obj, 'insurance_percent', 0) or 0),
        })
    except Exception as e:
        return Response({
            'status': 'saved_default',
            **DEFAULT_SETTINGS,
            'note': str(e),
        })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_payslip(request):
    """
    كشف راتب الموظف لنفسه
    """
    user = request.user
    year, month = _parse_month(request)
    lang = _get_lang(request)

    try:
        from employees.models import Employee
        emp = Employee.objects.get(user=user)
    except Exception:
        return Response({'error': 'Employee not found'}, status=404)

    settings = _get_payroll_settings(user)
    payroll = calculate_effective_payroll(emp, year, month, settings, lang=lang)
    return Response({'year': year, 'month': month, 'lang': lang, **payroll})
