"""
MotionHR - Reports API
Batch 1: Attendance / Late / Absence
"""
from datetime import datetime, timedelta, date
from calendar import monthrange

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
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
        return value.strftime('%H:%M')
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
@authentication_classes([TokenAuthentication])
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

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
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

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
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

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
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

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leaves_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    from leaves.models import LeaveRequest

    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def work_hours_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
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

    employees = _get_company_employees(user)
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def work_hours_report(request):
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    year, month = _parse_month(request)
    employee_id = request.GET.get('employee_id')

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    employees = _get_company_employees(user)
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
