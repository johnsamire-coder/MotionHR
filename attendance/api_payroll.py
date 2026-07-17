"""
MotionHR - Payroll API (v2 - matches real Attendance model)
"""
from datetime import datetime, date
from calendar import monthrange
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Attendance

User = get_user_model()

DEFAULT_LATE_DEDUCTION_PER_MIN = 1.0
DEFAULT_ABSENCE_DEDUCTION_PER_DAY = 200.0
DEFAULT_OVERTIME_RATE_PER_HOUR = 50.0


def _check_manager(user):
    role = getattr(user, 'role', None)
    return (
        user.is_superuser
        or user.is_staff
        or role in ['company_admin', 'hr_manager', 'manager']
    )


def _get_company_employees(user):
    """جلب موظفي الشركة من موديل Employee"""
    try:
        from employees.models import Employee
    except ImportError:
        return []

    company = getattr(user, 'company', None)
    if company:
        return Employee.objects.filter(company=company)
    return Employee.objects.all()


def _parse_month(request):
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    return year, month


def _calculate_employee_payroll(emp, year, month):
    """حساب راتب موظف واحد من موديل Attendance المحسوب مسبقاً"""
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    attendances = Attendance.objects.filter(
        employee=emp,
        date__gte=first_day,
        date__lte=last_day,
    ).order_by('date')

    # الملخصات
    total_work_hours = float(attendances.aggregate(s=Sum('work_hours'))['s'] or 0)
    total_late_minutes = int(attendances.aggregate(s=Sum('late_minutes'))['s'] or 0)
    total_overtime_hours = float(attendances.aggregate(s=Sum('overtime_hours'))['s'] or 0)

    # عدد الأيام حسب الحالة
    present_days = attendances.filter(status='present').count()
    late_days = attendances.filter(status='late').count()
    absent_days = attendances.filter(status='absent').count()
    on_leave_days = attendances.filter(status='on_leave').count()

    attended_days = present_days + late_days  # الحضور الفعلي = present + late

    # الحسابات المالية
    late_deduction = round(total_late_minutes * DEFAULT_LATE_DEDUCTION_PER_MIN, 2)
    absence_deduction = round(absent_days * DEFAULT_ABSENCE_DEDUCTION_PER_DAY, 2)
    total_deductions = round(late_deduction + absence_deduction, 2)
    overtime_bonus = round(total_overtime_hours * DEFAULT_OVERTIME_RATE_PER_HOUR, 2)

    # الراتب الأساسي من موديل الموظف
    basic_salary = 0
    for field in ['basic_salary', 'salary', 'monthly_salary']:
        val = getattr(emp, field, None)
        if val is not None:
            try:
                basic_salary = float(val)
                break
            except (ValueError, TypeError):
                pass

    net_salary = round(basic_salary - total_deductions + overtime_bonus, 2)

    # اسم الموظف
    emp_name = ''
    for field in ['full_name', 'name', 'first_name']:
        val = getattr(emp, field, None)
        if val:
            emp_name = str(val)
            break
    if not emp_name:
        user_obj = getattr(emp, 'user', None)
        if user_obj:
            emp_name = user_obj.get_full_name() or user_obj.username
        else:
            emp_name = f"Employee #{emp.id}"

    # تفاصيل يومية
    daily_details = []
    for att in attendances:
        daily_details.append({
            'date': att.date.isoformat() if att.date else None,
            'status': att.status,
            'check_in': att.check_in_time.strftime('%H:%M') if att.check_in_time else None,
            'check_out': att.check_out_time.strftime('%H:%M') if att.check_out_time else None,
            'work_hours': float(att.work_hours or 0),
            'late_minutes': int(att.late_minutes or 0),
            'overtime_hours': float(att.overtime_hours or 0),
        })

    return {
        'employee_id': emp.id,
        'employee_name': emp_name,
        'basic_salary': basic_salary,
        'attended_days': attended_days,
        'present_days': present_days,
        'late_days': late_days,
        'absent_days': absent_days,
        'on_leave_days': on_leave_days,
        'total_work_hours': round(total_work_hours, 2),
        'total_late_minutes': total_late_minutes,
        'overtime_hours': round(total_overtime_hours, 2),
        'late_deduction': late_deduction,
        'absence_deduction': absence_deduction,
        'total_deductions': total_deductions,
        'overtime_bonus': overtime_bonus,
        'net_salary': net_salary,
        'daily_details': daily_details,
    }


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_summary(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employees = _get_company_employees(user)

    results = []
    grand_total_salary = 0
    grand_total_deductions = 0
    grand_total_overtime = 0
    grand_total_net = 0

    for emp in employees:
        payroll = _calculate_employee_payroll(emp, year, month)
        results.append({
            'employee_id': payroll['employee_id'],
            'employee_name': payroll['employee_name'],
            'basic_salary': payroll['basic_salary'],
            'attended_days': payroll['attended_days'],
            'absent_days': payroll['absent_days'],
            'late_days': payroll['late_days'],
            'total_work_hours': payroll['total_work_hours'],
            'overtime_hours': payroll['overtime_hours'],
            'total_deductions': payroll['total_deductions'],
            'overtime_bonus': payroll['overtime_bonus'],
            'net_salary': payroll['net_salary'],
        })
        grand_total_salary += payroll['basic_salary']
        grand_total_deductions += payroll['total_deductions']
        grand_total_overtime += payroll['overtime_bonus']
        grand_total_net += payroll['net_salary']

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'grand_total_salary': round(grand_total_salary, 2),
        'grand_total_deductions': round(grand_total_deductions, 2),
        'grand_total_overtime': round(grand_total_overtime, 2),
        'grand_total_net': round(grand_total_net, 2),
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
    employee_id = request.GET.get('employee_id')

    if not employee_id:
        return Response({'error': 'employee_id required'}, status=400)

    try:
        from employees.models import Employee
        emp = Employee.objects.get(id=employee_id)
    except Exception:
        return Response({'error': 'Employee not found'}, status=404)

    payroll = _calculate_employee_payroll(emp, year, month)
    return Response({'year': year, 'month': month, **payroll})


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_settings(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    return Response({
        'late_deduction_per_minute': DEFAULT_LATE_DEDUCTION_PER_MIN,
        'absence_deduction_per_day': DEFAULT_ABSENCE_DEDUCTION_PER_DAY,
        'overtime_rate_per_hour': DEFAULT_OVERTIME_RATE_PER_HOUR,
        'note': 'الحسابات تعتمد على بيانات الحضور المسجلة (work_hours, late_minutes, overtime_hours)',
    })
