"""
MotionHR - Reports API
Batch 1: Attendance / Late / Absence
"""
from datetime import datetime, timedelta, date
from calendar import monthrange

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Attendance
from employees.models import Employee


MANAGER_ROLES = ['company_admin', 'hr_manager', 'manager', 'super_admin']


def _check_manager(user):
    role = getattr(user, 'role', None)
    return (
        user.is_superuser
        or user.is_staff
        or role in MANAGER_ROLES
    )


def _get_company_employees(user):
    company = getattr(user, 'company', None)

    qs = Employee._base_manager.all().select_related('user', 'company')

    if company:
        qs = qs.filter(company=company)

    return qs.order_by('id')


FULL_ACCESS_ROLES = ['company_admin', 'hr_manager', 'super_admin']


def _get_manager_scope_employees(user):
    """
    لو المدير العادي → يرجع موظفيه (subordinates) بس
    لو HR / company_admin / super_admin → يرجع كل موظفي الشركة
    """
    role = getattr(user, 'role', None)

    # لو صلاحيات كاملة → كل الشركة
    if user.is_superuser or user.is_staff or role in FULL_ACCESS_ROLES:
        return _get_company_employees(user)

    # لو مدير عادي → موظفيه بس
    try:
        manager_emp = Employee._base_manager.get(user=user)
        all_sub_ids = manager_emp.get_all_subordinates_ids()
        company = getattr(user, 'company', None)
        qs = Employee._base_manager.filter(
            id__in=all_sub_ids
        ).select_related('user', 'company')
        if company:
            qs = qs.filter(company=company)
        return qs.order_by('id')
    except Exception:
        return _get_company_employees(user)


def _parse_month(request):
    now = datetime.now()
    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        if month < 1 or month > 12:
            raise ValueError
    except (ValueError, TypeError):
        year = now.year
        month = now.month
    return year, month


def _format_time(value):
    if not value:
        return None
    try:
        return value.strftime('%I:%M %p')
    except Exception:
        return str(value)


def _employee_name(emp):
    parts_ar = [
        getattr(emp, 'first_name_ar', '') or '',
        getattr(emp, 'middle_name_ar', '') or '',
        getattr(emp, 'last_name_ar', '') or '',
    ]
    name_ar = ' '.join([p.strip() for p in parts_ar if p and p.strip()]).strip()
    if name_ar:
        return name_ar

    parts_en = [
        getattr(emp, 'first_name_en', '') or '',
        getattr(emp, 'last_name_en', '') or '',
    ]
    name_en = ' '.join([p.strip() for p in parts_en if p and p.strip()]).strip()
    if name_en:
        return name_en

    if getattr(emp, 'user', None):
        return emp.user.get_full_name() or emp.user.username

    return f'Employee #{emp.id}'


def _employee_username(emp):
    if getattr(emp, 'user', None):
        return emp.user.username
    return None


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def attendance_monthly_report(request):
    """
    تقرير الحضور الشهري
    GET params: year, month, employee_id(optional)
    """
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []
    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
        )

        checkins = records.filter(check_in_time__isnull=False).count()
        checkouts = records.filter(check_out_time__isnull=False).count()
        working_days = records.filter(check_in_time__isnull=False).count()

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'username': _employee_username(emp),
            'employee_code': getattr(emp, 'employee_code', None),
            'total_checkins': checkins,
            'total_checkouts': checkouts,
            'working_days': working_days,
            'total_month_days': last_day_num,
        })

    return Response({
        'year': year,
        'month': month,
        'from': first_day.isoformat(),
        'to': last_day.isoformat(),
        'total_employees': len(results),
        'employees': results,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def late_report(request):
    """
    تقرير التأخير
    GET params: year, month, employee_id(optional)
    """
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []

    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by('date')

        late_days = []
        total_late_minutes = 0

        for rec in records:
            minutes_late = int(rec.late_minutes or 0)
            if minutes_late > 0:
                late_days.append({
                    'date': rec.date.isoformat() if rec.date else None,
                    'time': _format_time(rec.check_in_time),
                    'minutes_late': minutes_late,
                })
                total_late_minutes += minutes_late

        if late_days:
            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'username': _employee_username(emp),
                'employee_code': getattr(emp, 'employee_code', None),
                'total_late_days': len(late_days),
                'total_late_minutes': total_late_minutes,
                'total_late_hours': round(total_late_minutes / 60, 2),
                'details': late_days,
            })

    return Response({
        'year': year,
        'month': month,
        'total_employees_with_late': len(results),
        'employees': results,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def absence_report(request):
    """
    تقرير الغياب
    GET params: year, month, employee_id(optional)
    ملاحظة: الجمعة مستبعدة من أيام العمل
    """
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    today = date.today()
    upper_bound = min(last_day, today)

    working_dates = []
    current = first_day
    while current <= upper_bound:
        # الجمعة = 4 في Python
        if current.weekday() != 4:
            working_dates.append(current)
        current += timedelta(days=1)

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []
    for emp in employees:
        attended_dates = set(
            Attendance._base_manager.filter(
                employee=emp,
                date__gte=first_day,
                date__lte=upper_bound,
                check_in_time__isnull=False,
            ).values_list('date', flat=True)
        )

        absent_dates = [d for d in working_dates if d not in attended_dates]

        if absent_dates:
            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'username': _employee_username(emp),
                'employee_code': getattr(emp, 'employee_code', None),
                'total_working_days': len(working_dates),
                'attended_days': len(attended_dates),
                'absent_days': len(absent_dates),
                'absent_dates': [d.isoformat() for d in absent_dates],
            })

    return Response({
        'year': year,
        'month': month,
        'from': first_day.isoformat(),
        'to': upper_bound.isoformat() if upper_bound else None,
        'total_working_days_in_month': len(working_dates),
        'total_employees_with_absence': len(results),
        'employees': results,
    })


# ═══════════════════════════════════════
# 4) تقرير الطلبات
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def requests_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from requests_app.models import EmployeeRequest

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    reqs = EmployeeRequest._base_manager.filter(
        employee_id__in=emp_ids,
        created_at__date__gte=first_day,
        created_at__date__lte=last_day,
    ).select_related('employee', 'request_type')

    if status_filter:
        reqs = reqs.filter(status=status_filter)

    total = reqs.count()
    approved = reqs.filter(status='approved').count()
    rejected = reqs.filter(status='rejected').count()
    pending = reqs.filter(status='pending').count()

    details = []
    for r in reqs.order_by('-created_at')[:100]:
        emp = r.employee
        details.append({
            'id': r.id,
            'employee_name': _employee_name(emp) if emp else '-',
            'request_type': str(r.request_type) if r.request_type else '-',
            'subject': getattr(r, 'subject', '') or '',
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        })

    return Response({
        'year': year,
        'month': month,
        'total_requests': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'details': details,
    })


# ═══════════════════════════════════════
# 5) تقرير الإجازات
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from leaves.models import LeaveRequest

    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    leaves = LeaveRequest._base_manager.filter(
        employee_id__in=emp_ids,
        start_date__gte=first_day,
        start_date__lte=last_day,
    ).select_related('employee', 'leave_type')

    total = leaves.count()
    approved = leaves.filter(status='approved').count()
    rejected = leaves.filter(status='rejected').count()
    pending = leaves.filter(status='pending').count()

    per_employee = {}
    for lv in leaves.order_by('-start_date'):
        emp = lv.employee
        emp_name = _employee_name(emp) if emp else '-'
        if emp_name not in per_employee:
            per_employee[emp_name] = {
                'employee_id': emp.id if emp else None,
                'total_days': 0,
                'approved_days': 0,
                'leaves': [],
            }

        days = int(lv.days_count or 0)
        if days == 0:
            try:
                days = (lv.end_date - lv.start_date).days + 1
            except Exception:
                days = 1

        per_employee[emp_name]['total_days'] += days
        if lv.status == 'approved':
            per_employee[emp_name]['approved_days'] += days

        per_employee[emp_name]['leaves'].append({
            'id': lv.id,
            'type': str(lv.leave_type) if lv.leave_type else '-',
            'from': lv.start_date.isoformat() if lv.start_date else None,
            'to': lv.end_date.isoformat() if lv.end_date else None,
            'days': days,
            'status': lv.status,
        })

    employees_list = [{'name': k, **v} for k, v in per_employee.items()]

    return Response({
        'year': year,
        'month': month,
        'total_leaves': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'employees': employees_list,
    })


# ═══════════════════════════════════════
# 6) تقرير ساعات العمل الفعلية
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def work_hours_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    results = []

    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by('date')

        total_hours = 0.0
        daily_breakdown = []

        for rec in records:
            hours = float(rec.work_hours or 0)
            if hours > 0:
                total_hours += hours
                daily_breakdown.append({
                    'date': rec.date.isoformat() if rec.date else None,
                    'hours': round(hours, 2),
                    'check_in': _format_time(rec.check_in_time),
                    'check_out': _format_time(rec.check_out_time),
                })

        days_worked = len(daily_breakdown)

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'username': _employee_username(emp),
            'employee_code': getattr(emp, 'employee_code', None),
            'total_hours': round(total_hours, 2),
            'total_days_worked': days_worked,
            'average_hours_per_day': round(total_hours / days_worked, 2) if days_worked else 0,
            'daily_breakdown': daily_breakdown,
        })

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'employees': results,
    })


# ═══════════════════════════════════════
# 7) تصدير PDF
# ═══════════════════════════════════════
from django.http import HttpResponse
from io import BytesIO

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def export_report_pdf(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    report_type = request.GET.get('report_type', 'attendance')
    year, month = _parse_month(request)

    from rest_framework.test import APIRequestFactory, force_authenticate
    factory = APIRequestFactory()
    fake_request = factory.get(f'/test/?year={year}&month={month}')
    force_authenticate(fake_request, user=user)

    view_map = {
        'attendance': attendance_monthly_report,
        'late': late_report,
        'absence': absence_report,
        'requests': requests_report,
        'leaves': leaves_report,
        'work-hours': work_hours_report,
    }

    view_func = view_map.get(report_type)
    if not view_func:
        return Response({'error': 'invalid report_type'}, status=400)

    response_data = view_func(fake_request).data

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(20 * mm, height - 20 * mm, f"MotionHR Report: {report_type.upper()}")

    p.setFont("Helvetica", 10)
    p.drawString(20 * mm, height - 30 * mm, f"Year: {year}  Month: {month}")

    y_pos = height - 45 * mm
    p.setFont("Helvetica", 9)

    employees = response_data.get('employees', [])
    details = response_data.get('details', [])
    items = employees if employees else details

    for item in items[:50]:
        line_parts = []
        name = item.get('employee_name') or item.get('name') or item.get('username') or '-'
        line_parts.append(name)

        if 'working_days' in item:
            line_parts.append(f"Days: {item['working_days']}")
        if 'total_late_days' in item:
            line_parts.append(f"Late: {item['total_late_days']}d")
        if 'absent_days' in item:
            line_parts.append(f"Absent: {item['absent_days']}d")
        if 'total_hours' in item:
            line_parts.append(f"Hours: {item['total_hours']}")
        if 'status' in item:
            line_parts.append(f"Status: {item['status']}")
        if 'subject' in item:
            line_parts.append(item['subject'][:30])

        line = '  |  '.join(line_parts)
        p.drawString(20 * mm, y_pos, line[:120])
        y_pos -= 6 * mm

        if y_pos < 20 * mm:
            p.showPage()
            y_pos = height - 20 * mm

    if not items:
        p.drawString(20 * mm, y_pos, "No data found for this period.")

    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report_type}_{year}_{month}.pdf"'
    return response


# ═══════════════════════════════════════
# 8) تصدير Excel
# ═══════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def export_report_excel(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from openpyxl import Workbook

    report_type = request.GET.get('report_type', 'attendance')
    year, month = _parse_month(request)

    from rest_framework.test import APIRequestFactory, force_authenticate
    factory = APIRequestFactory()
    fake_request = factory.get(f'/test/?year={year}&month={month}')
    force_authenticate(fake_request, user=user)

    view_map = {
        'attendance': attendance_monthly_report,
        'late': late_report,
        'absence': absence_report,
        'requests': requests_report,
        'leaves': leaves_report,
        'work-hours': work_hours_report,
    }

    view_func = view_map.get(report_type)
    if not view_func:
        return Response({'error': 'invalid report_type'}, status=400)

    response_data = view_func(fake_request).data

    wb = Workbook()
    ws = wb.active
    ws.title = f"{report_type}_{year}_{month}"

    employees = response_data.get('employees', [])
    details = response_data.get('details', [])
    items = employees if employees else details

    if items:
        headers = list(items[0].keys())
        # نشيل الحقول المعقدة
        simple_headers = [h for h in headers if h not in ('details', 'daily_breakdown', 'leaves', 'absent_dates')]
        ws.append(simple_headers)

        for item in items:
            row = []
            for h in simple_headers:
                val = item.get(h, '')
                if isinstance(val, (list, dict)):
                    val = str(val)[:200]
                row.append(val)
            ws.append(row)
    else:
        ws.append(['No data found'])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="report_{report_type}_{year}_{month}.xlsx"'
    return response


# ═══════════════════════════════════════
# Phase 13 Quick Filters Overrides
# requests/leaves/work-hours support filters
# ═══════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def requests_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from requests_app.models import EmployeeRequest

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    reqs = EmployeeRequest._base_manager.filter(
        employee_id__in=emp_ids,
        created_at__date__gte=first_day,
        created_at__date__lte=last_day,
    ).select_related('employee', 'request_type')

    if employee_id:
        reqs = reqs.filter(employee_id=employee_id)

    if status_filter:
        reqs = reqs.filter(status=status_filter)

    total = reqs.count()
    approved = reqs.filter(status='approved').count()
    rejected = reqs.filter(status='rejected').count()
    pending = reqs.filter(status='pending').count()

    details = []
    for r in reqs.order_by('-created_at')[:100]:
        emp = r.employee
        details.append({
            'id': r.id,
            'employee_id': emp.id if emp else None,
            'employee_name': _employee_name(emp) if emp else '-',
            'request_type': str(r.request_type) if r.request_type else '-',
            'subject': getattr(r, 'subject', '') or '',
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        })

    return Response({
        'year': year,
        'month': month,
        'employee_id': employee_id,
        'status': status_filter,
        'total_requests': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'details': details,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from leaves.models import LeaveRequest

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    emp_ids = list(employees.values_list('id', flat=True))

    leaves = LeaveRequest._base_manager.filter(
        employee_id__in=emp_ids,
        start_date__gte=first_day,
        start_date__lte=last_day,
    ).select_related('employee', 'leave_type')

    if employee_id:
        leaves = leaves.filter(employee_id=employee_id)

    if status_filter:
        leaves = leaves.filter(status=status_filter)

    total = leaves.count()
    approved = leaves.filter(status='approved').count()
    rejected = leaves.filter(status='rejected').count()
    pending = leaves.filter(status='pending').count()

    per_employee = {}
    for lv in leaves.order_by('-start_date'):
        emp = lv.employee
        emp_name = _employee_name(emp) if emp else '-'
        emp_id = emp.id if emp else None

        if emp_id not in per_employee:
            per_employee[emp_id] = {
                'employee_id': emp_id,
                'name': emp_name,
                'total_days': 0,
                'approved_days': 0,
                'leaves': [],
            }

        days = int(getattr(lv, 'days_count', 0) or 0)
        if days == 0:
            try:
                days = (lv.end_date - lv.start_date).days + 1
            except Exception:
                days = 1

        per_employee[emp_id]['total_days'] += days
        if lv.status == 'approved':
            per_employee[emp_id]['approved_days'] += days

        per_employee[emp_id]['leaves'].append({
            'id': lv.id,
            'type': str(lv.leave_type) if lv.leave_type else '-',
            'from': lv.start_date.isoformat() if lv.start_date else None,
            'to': lv.end_date.isoformat() if lv.end_date else None,
            'days': days,
            'status': lv.status,
        })

    employees_list = list(per_employee.values())

    return Response({
        'year': year,
        'month': month,
        'employee_id': employee_id,
        'status': status_filter,
        'total_leaves': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'employees': employees_list,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def work_hours_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_manager_scope_employees(user)
    if employee_id:
        employees = employees.filter(id=employee_id)

    results = []

    for emp in employees:
        records = Attendance._base_manager.filter(
            employee=emp,
            date__gte=first_day,
            date__lte=last_day,
            check_in_time__isnull=False,
        ).order_by('date')

        total_hours = 0.0
        daily_breakdown = []

        for rec in records:
            hours = float(rec.work_hours or 0)
            if hours > 0:
                total_hours += hours
                daily_breakdown.append({
                    'date': rec.date.isoformat() if rec.date else None,
                    'hours': round(hours, 2),
                    'check_in': _format_time(rec.check_in_time),
                    'check_out': _format_time(rec.check_out_time),
                })

        days_worked = len(daily_breakdown)

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'username': _employee_username(emp),
            'employee_code': getattr(emp, 'employee_code', None),
            'total_hours': round(total_hours, 2),
            'total_days_worked': days_worked,
            'average_hours_per_day': round(total_hours / days_worked, 2) if days_worked else 0,
            'daily_breakdown': daily_breakdown,
        })

    return Response({
        'year': year,
        'month': month,
        'employee_id': employee_id,
        'total_employees': len(results),
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.1 تقرير الرواتب الشهري
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def payroll_report(request):
    """تقرير الرواتب الشهري لكل الموظفين"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    lang = request.GET.get('lang', 'ar')
    employees = _get_manager_scope_employees(user)

    try:
        from attendance.payroll_rules import calculate_effective_payroll
        from attendance.api_payroll import _get_payroll_settings
    except ImportError:
        return Response({'error': 'payroll module not available'}, status=500)

    settings = _get_payroll_settings(user)

    results = []
    totals = {
        'basic_salary': 0.0,
        'allowances_total': 0.0,
        'overtime_bonus': 0.0,
        'bonuses_total': 0.0,
        'night_allowance': 0.0,
        'weekend_allowance': 0.0,
        'gross_salary': 0.0,
        'late_deduction': 0.0,
        'absence_deduction': 0.0,
        'early_leave_deduction': 0.0,
        'unpaid_leave_deduction': 0.0,
        'flex_shortage_deduction': 0.0,
        'insurance_deduction': 0.0,
        'installments_total': 0.0,
        'penalties_total': 0.0,
        'total_deductions': 0.0,
        'net_salary': 0.0,
    }

    for emp in employees:
        try:
            p = calculate_effective_payroll(emp, year, month, settings, lang=lang)
            row = {
                'employee_id': emp.id,
                'employee_code': getattr(emp, 'employee_code', '') or '',
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'job_title': getattr(getattr(emp, 'job_title', None), 'name_ar', '') or '',
                'currency': p.get('currency', 'EGP'),
                'basic_salary': p.get('basic_salary', 0),
                'allowances_total': p.get('allowances_total', 0),
                'overtime_bonus': p.get('overtime_bonus', 0),
                'bonuses_total': p.get('bonuses_total', 0),
                'night_allowance': p.get('night_allowance', 0),
                'weekend_allowance': p.get('weekend_allowance', 0),
                'gross_salary': p.get('gross_salary', 0),
                'late_deduction': p.get('late_deduction', 0),
                'absence_deduction': p.get('absence_deduction', 0),
                'early_leave_deduction': p.get('early_leave_deduction', 0),
                'unpaid_leave_deduction': p.get('unpaid_leave_deduction', 0),
                'flex_shortage_deduction': p.get('flex_shortage_deduction', 0),
                'insurance_deduction': p.get('insurance_deduction', 0),
                'installments_total': p.get('installments_total', 0),
                'penalties_total': p.get('penalties_total', 0),
                'total_deductions': p.get('total_deductions', 0),
                'net_salary': p.get('net_salary', 0),
                'total_working_days': p.get('total_working_days', 0),
                'attended_days': p.get('attended_days', 0),
                'absent_days': p.get('absent_days', 0),
                'late_days': p.get('late_days', 0),
                'on_leave_days': p.get('on_leave_days', 0),
                'unpaid_leave_days': p.get('unpaid_leave_days', 0),
                'total_late_minutes': p.get('total_late_minutes', 0),
                'policy_name': p.get('policy_name'),
            }
            results.append(row)
            for key in totals:
                totals[key] += float(row.get(key, 0) or 0)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'payroll_report error for {emp}: {e}')

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'totals': {k: round(v, 2) for k, v in totals.items()},
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.3 تقرير الأذونات
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def permissions_report(request):
    """تقرير رصيد الأذونات والحركات"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employees = _get_manager_scope_employees(user)
    company = getattr(user, 'company', None)

    from datetime import date
    first_day = date(year, month, 1)
    import calendar
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    results = []
    for emp in employees:
        try:
            from attendance.models import PermissionLedger
            entries = PermissionLedger._base_manager.filter(
                employee=emp,
                reference_date__gte=first_day,
                reference_date__lte=last_day,
            ).order_by('reference_date')

            total_minutes = 0
            movements = []
            for e in entries:
                total_minutes += int(e.minutes_used or 0)
                movements.append({
                    'date': str(e.reference_date) if e.reference_date else '',
                    'type': e.entry_type,
                    'minutes': e.minutes_used or 0,
                    'notes': e.notes or '',
                })

            from requests_app.models import PermissionPolicy
            policy = PermissionPolicy._base_manager.filter(company=emp.company).first()
            max_hours = float(policy.max_hours_per_month) if policy else 0.0
            max_times = policy.max_times_per_month if policy else 0

            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'max_hours_per_month': max_hours,
                'max_times_per_month': max_times,
                'used_minutes': total_minutes,
                'used_hours': round(total_minutes / 60, 2),
                'movements_count': len(movements),
                'movements': movements,
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'permissions_report error for {emp}: {e}')

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.5 تقرير يومي للحضور
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def daily_attendance_report(request):
    """تقرير حالة الحضور لكل الموظفين في يوم معين"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from datetime import date
    date_str = request.GET.get('date', str(date.today()))
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة (YYYY-MM-DD)'}, status=400)

    employees = _get_manager_scope_employees(user)

    try:
        from attendance.models import DailyAttendanceSummary, Attendance
    except ImportError:
        return Response({'error': 'attendance module not available'}, status=500)

    results = []
    stats = {
        'present': 0, 'late': 0, 'absent': 0,
        'on_leave': 0, 'weekend': 0, 'mission': 0,
        'no_data': 0,
    }

    for emp in employees:
        summary = DailyAttendanceSummary._base_manager.filter(
            employee=emp, date=target_date
        ).first()

        att = Attendance._base_manager.filter(
            employee=emp, date=target_date
        ).first()

        if summary:
            status = summary.effective_status or summary.status
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': status,
                'check_in': att.check_in_time.strftime('%I:%M %p') if att and att.check_in_time else None,
                'check_out': att.check_out_time.strftime('%I:%M %p') if att and att.check_out_time else None,
                'work_hours': float(summary.work_hours or 0),
                'late_minutes': summary.late_minutes or 0,
                'early_leave_minutes': summary.early_leave_minutes or 0,
                'overtime_hours': float(summary.overtime_hours or 0),
                'is_night_shift': summary.is_night_shift,
                'is_weekend_work': summary.is_weekend_work,
                'shift_name': summary.shift.name if summary.shift else '',
            }
        elif att and att.check_in_time:
            status = 'present'
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': status,
                'check_in': att.check_in_time.strftime('%I:%M %p') if att.check_in_time else None,
                'check_out': att.check_out_time.strftime('%I:%M %p') if att and att.check_out_time else None,
                'work_hours': float(att.work_hours or 0),
                'late_minutes': att.late_minutes or 0,
                'early_leave_minutes': att.early_leave_minutes or 0,
                'overtime_hours': float(att.overtime_hours or 0),
                'is_night_shift': False,
                'is_weekend_work': False,
                'shift_name': att.shift.name if att.shift else '',
            }
        else:
            status = 'no_data'
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': 'no_data',
                'check_in': None,
                'check_out': None,
                'work_hours': 0,
                'late_minutes': 0,
                'early_leave_minutes': 0,
                'overtime_hours': 0,
                'is_night_shift': False,
                'is_weekend_work': False,
                'shift_name': '',
            }

        results.append(row)
        stats[status] = stats.get(status, 0) + 1

    return Response({
        'date': str(target_date),
        'total_employees': len(results),
        'stats': stats,
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.4 تقرير الإجازات المحسّن (مع أرصدة + unpaid + نص يوم)
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report_enhanced(request):
    """تقرير الإجازات الشامل مع الأرصدة"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    employees = _get_manager_scope_employees(user)

    from leaves.models import LeaveRequest, LeaveBalance, LeaveType

    results = []
    for emp in employees:
        leaves = LeaveRequest._base_manager.filter(
            employee=emp,
            start_date__lte=last_day,
            end_date__gte=first_day,
        ).select_related('leave_type').order_by('-start_date')

        leave_items = []
        total_days = 0.0
        unpaid_days = 0.0
        half_day_count = 0

        for lv in leaves:
            days = float(lv.days_count or 1)
            is_unpaid = not getattr(lv.leave_type, 'is_paid', True) if lv.leave_type else False
            is_half = days <= 0.5
            half_type = getattr(lv, 'half_day_type', '') or ''

            if lv.status == 'approved':
                total_days += days
                if is_unpaid:
                    unpaid_days += days
                if is_half:
                    half_day_count += 1

            leave_items.append({
                'id': lv.id,
                'leave_type': lv.leave_type.name if lv.leave_type else '',
                'is_paid': not is_unpaid,
                'start_date': str(lv.start_date) if lv.start_date else '',
                'end_date': str(lv.end_date) if lv.end_date else '',
                'days_count': days,
                'is_half_day': is_half,
                'half_day_type': half_type,
                'status': lv.status,
                'reason': lv.reason or '',
            })

        balances = LeaveBalance._base_manager.filter(
            employee=emp,
            year=year,
        ).select_related('leave_type')

        balance_items = []
        for bal in balances:
            balance_items.append({
                'leave_type': bal.leave_type.name if bal.leave_type else '',
                'total_days': float(bal.total_days or 0),
                'used_days': float(bal.used_days or 0),
                'pending_days': float(bal.pending_days or 0),
                'remaining_days': float(bal.remaining_days if hasattr(bal, 'remaining_days') else 0),
            })

        results.append({
            'employee_id': emp.id,
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'total_approved_days': total_days,
            'unpaid_days': unpaid_days,
            'half_day_count': half_day_count,
            'leaves_count': len(leave_items),
            'leaves': leave_items,
            'balances': balance_items,
        })

    return Response({
        'year': year,
        'month': month,
        'total_employees': len(results),
        'employees': results,
    })


# ══════════════════════════════════════════════════════════════════
# 5.2 تقرير الشيفتات
# ══════════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def shifts_report(request):
    """تقرير توزيع الموظفين على الشيفتات"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    employees = _get_manager_scope_employees(user)
    company = getattr(user, 'company', None)

    from attendance.models import Shift, ShiftAssignment, EmployeeShift
    from attendance.api_shifts import get_effective_shift

    today = date.today()
    shift_distribution = {}
    no_shift_employees = []

    for emp in employees:
        try:
            shift, source = get_effective_shift(emp, today)
        except Exception:
            shift = None
            source = 'error'

        if shift:
            shift_id = shift.id
            if shift_id not in shift_distribution:
                shift_distribution[shift_id] = {
                    'shift_id': shift_id,
                    'shift_name': shift.name,
                    'shift_type': shift.shift_type,
                    'shift_mode': getattr(shift, 'shift_mode', ''),
                    'start_time': str(shift.start_time)[:5] if shift.start_time else '',
                    'end_time': str(shift.end_time)[:5] if shift.end_time else '',
                    'crosses_midnight': shift.crosses_midnight,
                    'employees_count': 0,
                    'employees': [],
                }
            shift_distribution[shift_id]['employees_count'] += 1
            shift_distribution[shift_id]['employees'].append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'source': source,
            })
        else:
            no_shift_employees.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            })

    all_shifts = list(shift_distribution.values())
    all_shifts.sort(key=lambda x: x['employees_count'], reverse=True)

    return Response({
        'date': str(today),
        'total_employees': employees.count(),
        'employees_with_shifts': sum(s['employees_count'] for s in all_shifts),
        'employees_without_shifts': len(no_shift_employees),
        'shifts_count': len(all_shifts),
        'shifts': all_shifts,
        'no_shift_employees': no_shift_employees,
    })
