"""
MotionHR - Reports API
Batch 1: Attendance / Late / Absence
"""
from datetime import datetime, timedelta, date
from django.utils import timezone
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

    # استبعاد staff
    qs = qs.exclude(user__is_staff=True)

    # ATT-17: استبعاد company_admin و hr_manager لأنهم مش موظفين حقيقيين
    # (مش بيسجلوا حضور وبيظهروا كغائبين)
    qs = qs.exclude(
        user__role__in=['company_admin', 'super_admin']
    )

    # استبعاد الموظفين المنتهية خدمتهم
    qs = qs.exclude(
        status__in=['terminated', 'resigned', 'retired']
    )

    return qs.order_by('id')


FULL_ACCESS_ROLES = ['company_admin', 'hr_manager', 'super_admin']


def _get_manager_scope_employees(user):
    """
    لو المدير العادي → يرجع موظفيه فقط باستخدام _base_manager
    لو HR / company_admin / super_admin → يرجع كل موظفي الشركة
    """
    role = getattr(user, 'role', None)

    # صلاحيات كاملة
    if user.is_superuser or role in FULL_ACCESS_ROLES:
        return _get_company_employees(user)

    try:
        manager_emp = Employee._base_manager.get(user=user)
        company = getattr(user, 'company', None)

        collected_ids = set()
        stack = [manager_emp.id]

        while stack:
            current_id = stack.pop()

            sub_qs = Employee._base_manager.filter(direct_manager_id=current_id)
            if company:
                sub_qs = sub_qs.filter(company=company)

            sub_ids = list(sub_qs.values_list('id', flat=True))
            for sid in sub_ids:
                if sid not in collected_ids:
                    collected_ids.add(sid)
                    stack.append(sid)

        qs = Employee._base_manager.filter(id__in=collected_ids).select_related('user', 'company')
        if company:
            qs = qs.filter(company=company)

        return qs.order_by('id')
    except Exception:
        return _get_company_employees(user)


def _get_direct_team_employees(user):
    """
    دايمًا بيرجع الفريق الهرمي (direct_manager) بغض النظر عن الـ role.
    مستخدمة في شاشات "فريقي" اللي المفروض تعرض الفريق المباشر بس،
    حتى لو المستخدم company_admin أو hr_manager.
    """
    try:
        manager_emp = Employee._base_manager.get(user=user)
        company = getattr(user, 'company', None)
        collected_ids = set()
        stack = [manager_emp.id]
        while stack:
            current_id = stack.pop()
            sub_qs = Employee._base_manager.filter(direct_manager_id=current_id)
            if company:
                sub_qs = sub_qs.filter(company=company)
            sub_ids = list(sub_qs.values_list('id', flat=True))
            for sid in sub_ids:
                if sid not in collected_ids:
                    collected_ids.add(sid)
                    stack.append(sid)
        qs = Employee._base_manager.filter(id__in=collected_ids).select_related('user', 'company')
        if company:
            qs = qs.filter(company=company)
        return qs.order_by('id')
    except Exception:
        return Employee._base_manager.none()


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
        # بداية الحساب = تاريخ إضافة الموظف في البرنامج (created_at)
        # لو مش موجود نرجع لـ hire_date ثم أول الشهر
        emp_start = first_day
        created_at = getattr(emp, 'created_at', None)
        if created_at is not None:
            emp_start = max(first_day, created_at.date())
        elif getattr(emp, 'hire_date', None):
            emp_start = max(first_day, emp.hire_date)

        # نهاية الحساب = آخر يوم في النطاق (ومع مراعاة إنهاء الخدمة إن وجد)
        emp_end = upper_bound
        term_date = getattr(emp, 'termination_date', None)
        if term_date:
            emp_end = min(emp_end, term_date)

        # لو الموظف اتضاف بعد نهاية الفترة → مفيش أيام تتحسب
        if emp_start > emp_end:
            continue

        emp_working_dates = [d for d in working_dates if emp_start <= d <= emp_end]

        attended_dates = set(
            Attendance._base_manager.filter(
                employee=emp,
                date__gte=emp_start,
                date__lte=emp_end,
                check_in_time__isnull=False,
            ).values_list('date', flat=True)
        )

        # لا نحتسب اليوم الحالي غياب إلا بعد انتهاء شيفت الموظف
        effective_working_dates = list(emp_working_dates)
        if today in effective_working_dates and today not in attended_dates:
            try:
                from attendance.api_shifts import get_effective_shift
                from django.utils import timezone as dj_tz
                from datetime import datetime as dt, time as dtime

                shift, _src = get_effective_shift(emp, today)
                now_local = dj_tz.localtime()

                if shift and getattr(shift, 'end_time', None):
                    shift_end_dt = dt.combine(today, shift.end_time)
                    # شيفت ليلي يعبر منتصف الليل
                    if getattr(shift, 'crosses_midnight', False):
                        shift_end_dt = dt.combine(today + timedelta(days=1), shift.end_time)

                    # لو لسه الشيفت ما انتهاش → استبعد اليوم من الغياب
                    if now_local.replace(tzinfo=None) < shift_end_dt:
                        effective_working_dates = [d for d in effective_working_dates if d != today]
                else:
                    # مفيش شيفت معروف: استبعد اليوم الحالي حتى نهاية اليوم
                    if now_local.date() == today:
                        effective_working_dates = [d for d in effective_working_dates if d != today]
            except Exception:
                # في أي خطأ: الأمان عدم احتساب اليوم غياب مبكراً
                effective_working_dates = [d for d in effective_working_dates if d != today]

        absent_dates = [d for d in effective_working_dates if d not in attended_dates]
        emp_working_dates = effective_working_dates

        if absent_dates:
            results.append({
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'username': _employee_username(emp),
                'employee_code': getattr(emp, 'employee_code', None),
                'total_working_days': len(emp_working_dates),
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

    try:
        if 'year' in request.GET:
            int(request.GET.get('year'))
        if 'month' in request.GET:
            month_raw = int(request.GET.get('month'))
            if month_raw < 1 or month_raw > 12:
                return Response({'error': 'الشهر يجب أن يكون من 1 إلى 12'}, status=400)
    except (ValueError, TypeError):
        return Response({'error': 'صيغة year/month غير صحيحة'}, status=400)

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    valid_statuses = {'approved', 'pending', 'rejected'}
    if status_filter and status_filter not in valid_statuses:
        return Response({'error': 'status غير صحيح. القيم المتاحة: approved, pending, rejected'}, status=400)

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
        'payroll': payroll_report,
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

    try:
        if 'year' in request.GET:
            int(request.GET.get('year'))
        if 'month' in request.GET:
            month_raw = int(request.GET.get('month'))
            if month_raw < 1 or month_raw > 12:
                return Response({'error': 'الشهر يجب أن يكون من 1 إلى 12'}, status=400)
    except (ValueError, TypeError):
        return Response({'error': 'صيغة year/month غير صحيحة'}, status=400)

    year, month = _parse_month(request)
    status_filter = request.GET.get('status')
    employee_id = request.GET.get('employee_id')

    valid_statuses = {'approved', 'pending', 'rejected'}
    if status_filter and status_filter not in valid_statuses:
        return Response({'error': 'status غير صحيح. القيم المتاحة: approved, pending, rejected'}, status=400)

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

    try:
        if 'year' in request.GET:
            int(request.GET.get('year'))
        if 'month' in request.GET:
            month_raw = int(request.GET.get('month'))
            if month_raw < 1 or month_raw > 12:
                return Response({'error': 'الشهر يجب أن يكون من 1 إلى 12'}, status=400)
    except (ValueError, TypeError):
        return Response({'error': 'صيغة year/month غير صحيحة'}, status=400)

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
        from attendance.models import DailyAttendanceSummary, Attendance, TrackingAlert
    except ImportError:
        return Response({'error': 'attendance module not available'}, status=500)

    gps_alert_map = {}
    try:
        gps_qs = TrackingAlert._base_manager.filter(date=target_date, status='open')
        requester_company = getattr(user, 'company', None)
        if requester_company:
            gps_qs = gps_qs.filter(company=requester_company)

        for al in gps_qs:
            note = (getattr(al, 'notes', '') or '').lower()
            if 'gps' in note or (getattr(al, 'last_latitude', None) is None and getattr(al, 'last_longitude', None) is None):
                gps_alert_map[al.employee_id] = al
    except Exception:
        gps_alert_map = {}

    results = []
    stats = {
        'present': 0, 'late': 0, 'absent': 0,
        'on_leave': 0, 'weekend': 0, 'mission': 0,
        'no_data': 0, 'gps_disabled': 0,
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
                'check_in': timezone.localtime(att.check_in_time).strftime('%I:%M %p') if att and att.check_in_time else None,
                'check_out': timezone.localtime(att.check_out_time).strftime('%I:%M %p') if att and att.check_out_time else None,
                'work_hours': float(summary.work_hours or 0),
                'late_minutes': summary.late_minutes or 0,
                'early_leave_minutes': summary.early_leave_minutes or 0,
                'overtime_hours': float(summary.overtime_hours or 0),
                'is_night_shift': summary.is_night_shift,
                'is_weekend_work': summary.is_weekend_work,
                'shift_name': summary.shift.name if summary.shift else '',
            }
        elif att and att.check_in_time:
            if getattr(att, 'status', None) in ('late', 'present', 'absent', 'on_leave', 'weekend', 'mission'):
                status = att.status
            elif (att.late_minutes or 0) > 0:
                status = 'late'
            else:
                status = 'present'
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': status,
                'check_in': timezone.localtime(att.check_in_time).strftime('%I:%M %p') if att.check_in_time else None,
                'check_out': timezone.localtime(att.check_out_time).strftime('%I:%M %p') if att and att.check_out_time else None,
                'work_hours': float(att.work_hours or 0),
                'late_minutes': att.late_minutes or 0,
                'early_leave_minutes': att.early_leave_minutes or 0,
                'overtime_hours': float(att.overtime_hours or 0),
                'is_night_shift': False,
                'is_weekend_work': False,
                'shift_name': att.shift.name if att.shift else '',
            }
        else:
            # نتأكد إن وقت شيفت الموظف وصل قبل ما نحسبه غائب
            _shift_not_started = False
            try:
                from attendance.api_mobile import get_active_shift
                _shift = get_active_shift(emp, target_date)
                if _shift and getattr(_shift, 'start_time', None) and target_date == timezone.localdate():
                    _now_time = timezone.localtime(timezone.now()).time()
                    if _now_time < _shift.start_time:
                        _shift_not_started = True
            except Exception:
                pass
            if _shift_not_started:
                continue
            status = 'absent'
            row = {
                'employee_id': emp.id,
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
                'status': 'absent',
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

        row['gps_disabled'] = emp.id in gps_alert_map
        row['gps_alert_note'] = getattr(gps_alert_map.get(emp.id), 'notes', '') if emp.id in gps_alert_map else ''

        if row['gps_disabled']:
            stats['gps_disabled'] = stats.get('gps_disabled', 0) + 1

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
                'leave_type_en': getattr(lv.leave_type, 'name_en', '') if lv.leave_type else '',
                'is_paid': not is_unpaid,
                'start_date': str(lv.start_date) if lv.start_date else '',
                'end_date': str(lv.end_date) if lv.end_date else '',
                'days_count': days,
                'is_half_day': is_half,
                'half_day_type': half_type,
                'status': lv.status,
                'reason': lv.reason or '',
            })

        # Filter balances by employee gender (skip leave types restricted to opposite gender)
        emp_gender = (getattr(emp, "gender", "") or "").lower()
        balances_qs = LeaveBalance._base_manager.filter(
            employee=emp,
            year=year,
        ).select_related('leave_type')

        if emp_gender == "male":
            balances_qs = balances_qs.exclude(leave_type__gender_restriction="female")
        elif emp_gender == "female":
            balances_qs = balances_qs.exclude(leave_type__gender_restriction="male")

        balances = balances_qs

        balance_items = []
        for bal in balances:
            balance_items.append({
                'leave_type': bal.leave_type.name if bal.leave_type else '',
                'leave_type_en': getattr(bal.leave_type, 'name_en', '') if bal.leave_type else '',
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


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def location_tracking_report(request):
    """تقرير تتبع مواقع الموظفين لليوم"""
    from datetime import date, datetime, timedelta
    from django.utils import timezone
    from django.db.models import Min, Max, Count
    from attendance.models import Attendance, LocationLog

    user = request.user
    if not _check_manager(user):
        return Response({'success': False, 'error': 'صلاحية غير كافية'}, status=403)

    date_str = request.GET.get('date', str(date.today()))
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return Response({'success': False, 'error': 'صيغة التاريخ غير صحيحة'}, status=400)

    employees = _get_manager_scope_employees(user)

    results = []
    for emp in employees:
        att = Attendance._base_manager.filter(employee=emp, date=target_date).first()

        checkin_time = att.check_in_time if att and att.check_in_time else None
        checkout_time = att.check_out_time if att and att.check_out_time else None

        worker_type = getattr(emp, 'worker_type', 'office') or 'office'
        is_office = worker_type == 'office'

        logs = []

        if is_office:
            # المكتبي: نعرض نقطة الحضور + نقطة الانصراف فقط
            if att and att.check_in_latitude and att.check_in_longitude:
                logs.append({
                    'timestamp': att.check_in_time,
                    'latitude': att.check_in_latitude,
                    'longitude': att.check_in_longitude,
                    'address': getattr(att, 'check_in_address', '') or 'نقطة الحضور',
                    'accuracy': 0,
                })
            if att and att.check_out_latitude and att.check_out_longitude:
                logs.append({
                    'timestamp': att.check_out_time,
                    'latitude': att.check_out_latitude,
                    'longitude': att.check_out_longitude,
                    'address': getattr(att, 'check_out_address', '') or 'نقطة الانصراف',
                    'accuracy': 0,
                })
        else:
            # الميداني: نعرض كل الـ location logs
            logs_qs = LocationLog._base_manager.filter(
                employee=emp,
                timestamp__date=target_date,
            ).order_by('timestamp')

            if checkin_time:
                logs_qs = logs_qs.filter(timestamp__gte=checkin_time)
            if checkout_time:
                logs_qs = logs_qs.filter(timestamp__lte=checkout_time)

            logs = list(logs_qs.values('timestamp', 'latitude', 'longitude', 'address', 'accuracy'))

        first_log = logs[0] if logs else None
        last_log = logs[-1] if logs else None

        emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip() or emp.employee_code

        results.append({
            'employee_id': emp.id,
            'employee_code': emp.employee_code or '',
            'employee_name': emp_name,
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'worker_type': getattr(emp, 'worker_type', '') or '',
            'checkin_time': checkin_time.strftime('%H:%M') if checkin_time else '',
            'checkout_time': checkout_time.strftime('%H:%M') if checkout_time else '',
            'has_attendance': bool(att and att.check_in_time),
            'total_logs': len(logs),
            'first_location': {
                'timestamp': first_log['timestamp'].strftime('%H:%M') if first_log else '',
                'lat': float(first_log['latitude']) if first_log else None,
                'lng': float(first_log['longitude']) if first_log else None,
                'address': first_log['address'] if first_log else '',
            } if first_log else None,
            'last_location': {
                'timestamp': last_log['timestamp'].strftime('%H:%M') if last_log else '',
                'lat': float(last_log['latitude']) if last_log else None,
                'lng': float(last_log['longitude']) if last_log else None,
                'address': last_log['address'] if last_log else '',
            } if last_log else None,
            'logs': [
                {
                    'timestamp': log['timestamp'].strftime('%H:%M'),
                    'lat': float(log['latitude']),
                    'lng': float(log['longitude']),
                    'address': log['address'] or '',
                    'accuracy': float(log['accuracy']) if log['accuracy'] else 0,
                }
                for log in logs
            ],
        })

    # stats
    total_emp = len(results)
    with_attendance = sum(1 for r in results if r['has_attendance'])
    tracked = sum(1 for r in results if r['total_logs'] > 0)

    return Response({
        'success': True,
        'date': str(target_date),
        'stats': {
            'total_employees': total_emp,
            'with_attendance': with_attendance,
            'tracked': tracked,
            'not_tracked': total_emp - tracked,
        },
        'employees': results,
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_report(request):
    """تقرير مكافأة نهاية الخدمة"""
    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    as_of_str = request.GET.get('as_of_date', str(timezone.localdate()))
    try:
        as_of_date = date.fromisoformat(as_of_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة (YYYY-MM-DD)'}, status=400)

    employees = (
        _get_manager_scope_employees(user)
        .exclude(user__is_staff=True)
        .exclude(user__role__in=['company_admin', 'super_admin'])
        .exclude(status__in=['terminated', 'resigned', 'retired'])
        .select_related('department', 'branch', 'user')
        .order_by('id')
    )

    results = []
    total_eos_amount = 0.0

    for emp in employees:
        if not emp.hire_date:
            continue

        service_days = (as_of_date - emp.hire_date).days
        if service_days < 0:
            continue

        years_of_service = round(service_days / 365.25, 2)
        basic_salary = round(float(emp.basic_salary or 0), 2)

        if years_of_service <= 5:
            eos_amount = (basic_salary * 0.5) * years_of_service
        else:
            eos_amount = (basic_salary * 0.5 * 5) + (basic_salary * (years_of_service - 5))

        eos_amount = round(eos_amount, 2)
        total_eos_amount += eos_amount

        results.append({
            'employee_id': emp.id,
            'employee_code': emp.employee_code,
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'hire_date': str(emp.hire_date),
            'years_of_service': years_of_service,
            'basic_salary': basic_salary,
            'eos_amount': eos_amount,
        })

    results.sort(key=lambda x: x['eos_amount'], reverse=True)

    return Response({
        'as_of_date': str(as_of_date),
        'summary': {
            'employees_count': len(results),
            'total_eos_amount': round(total_eos_amount, 2),
        },
        'results': results,
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_export_excel(request):
    """تصدير تقرير EOS كـ Excel"""
    from attendance.report_export_helper import export_to_excel
    from datetime import date

    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    as_of_str = request.GET.get('as_of_date', str(timezone.localdate()))
    try:
        as_of_date = date.fromisoformat(as_of_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة'}, status=400)

    employees = (
        _get_manager_scope_employees(user)
        .exclude(user__is_staff=True)
        .exclude(user__role__in=['company_admin', 'super_admin'])
        .exclude(status__in=['terminated', 'resigned', 'retired'])
        .select_related('department', 'branch', 'user')
        .order_by('id')
    )

    rows = []
    for emp in employees:
        if not emp.hire_date:
            continue
        service_days = (as_of_date - emp.hire_date).days
        if service_days < 0:
            continue
        years = round(service_days / 365.25, 2)
        basic = round(float(emp.basic_salary or 0), 2)
        if years <= 5:
            eos = round((basic * 0.5) * years, 2)
        else:
            eos = round((basic * 0.5 * 5) + (basic * (years - 5)), 2)

        rows.append({
            'employee_code': emp.employee_code or '',
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'hire_date': str(emp.hire_date),
            'years_of_service': years,
            'basic_salary': basic,
            'eos_amount': eos,
        })

    rows.sort(key=lambda x: x['eos_amount'], reverse=True)

    columns = [
        ('employee_code',   'الكود',           15),
        ('employee_name',   'اسم الموظف',      25),
        ('department',      'القسم',           20),
        ('branch',          'الفرع',           20),
        ('hire_date',       'تاريخ التعيين',   15),
        ('years_of_service','سنوات الخدمة',    15),
        ('basic_salary',    'الراتب الأساسي',  18),
        ('eos_amount',      'مكافأة نهاية الخدمة', 22),
    ]

    if not rows:
        columns = [('info', 'ملاحظة', 40)]
        rows = [{'info': 'لا توجد بيانات'}]

    return export_to_excel(
        title=f'تقرير مكافأة نهاية الخدمة - {as_of_date}',
        columns=columns,
        rows=rows,
        user=user,
        filename=f'eos_report_{as_of_date}.xlsx',
    )

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def eos_export_pdf(request):
    """تصدير تقرير EOS كـ PDF"""
    from attendance.report_export_helper import export_to_pdf
    from datetime import date

    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    as_of_str = request.GET.get('as_of_date', str(timezone.localdate()))
    try:
        as_of_date = date.fromisoformat(as_of_str)
    except ValueError:
        return Response({'error': 'صيغة التاريخ غير صحيحة'}, status=400)

    employees = (
        _get_manager_scope_employees(user)
        .exclude(user__is_staff=True)
        .exclude(user__role__in=['company_admin', 'super_admin'])
        .exclude(status__in=['terminated', 'resigned', 'retired'])
        .select_related('department', 'branch', 'user')
        .order_by('id')
    )

    rows = []
    for emp in employees:
        if not emp.hire_date:
            continue
        service_days = (as_of_date - emp.hire_date).days
        if service_days < 0:
            continue
        years = round(service_days / 365.25, 2)
        basic = round(float(emp.basic_salary or 0), 2)
        if years <= 5:
            eos = round((basic * 0.5) * years, 2)
        else:
            eos = round((basic * 0.5 * 5) + (basic * (years - 5)), 2)

        rows.append({
            'employee_code': emp.employee_code or '',
            'employee_name': _employee_name(emp),
            'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
            'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') or '',
            'hire_date': str(emp.hire_date),
            'years_of_service': years,
            'basic_salary': basic,
            'eos_amount': eos,
        })

    rows.sort(key=lambda x: x['eos_amount'], reverse=True)

    columns = [
        ('employee_code',    'الكود',                15),
        ('employee_name',    'اسم الموظف',           25),
        ('department',       'القسم',                20),
        ('branch',           'الفرع',                20),
        ('hire_date',        'تاريخ التعيين',        15),
        ('years_of_service', 'سنوات الخدمة',         15),
        ('basic_salary',     'الراتب الأساسي',       18),
        ('eos_amount',       'مكافأة نهاية الخدمة',  22),
    ]

    if not rows:
        columns = [('info', 'ملاحظة', 40)]
        rows = [{'info': 'لا توجد بيانات'}]

    return export_to_pdf(
        title=f'تقرير مكافأة نهاية الخدمة - {as_of_date}',
        columns=columns,
        rows=rows,
        user=user,
        filename=f'eos_report_{as_of_date}.pdf',
    )

# ═══════════════════════════════════════════════════
# 10 New Reports + Excel + PDF Exports
# ═══════════════════════════════════════════════════

def _reimbursements_data(user):
    """رد المصروفات"""
    company = getattr(user, 'company', None)
    rows = []
    try:
        from requests_app.models import EmployeeRequest
        reqs = EmployeeRequest._base_manager.filter(
            company=company, request_type__name__icontains='مصروف',
        ).select_related('employee', 'request_type')
        for req in reqs:
            rows.append({
                'employee_name': _employee_name(req.employee),
                'type': req.request_type.name if req.request_type else '',
                'subject': req.subject or '',
                'amount': round(float(req.amount or 0), 2),
                'status': req.status,
                'created_at': str(req.created_at)[:10] if req.created_at else '',
            })
    except Exception:
        pass
    return rows


def _bank_transfer_data(user):
    """كشف تحويلات البنك"""
    from employees.models import Employee
    company = getattr(user, 'company', None)
    rows = []
    emps = Employee._base_manager.filter(
        company=company, status='active', salary_payment_method='bank',
    ).exclude(bank_account__isnull=True).exclude(bank_account='')
    for emp in emps:
        rows.append({
            'employee_code': emp.employee_code,
            'employee_name': _employee_name(emp),
            'bank_name': emp.bank_name or '',
            'account_number': emp.bank_account or '',
            'iban': emp.iban or '',
            'amount': round(float(emp.basic_salary or 0), 2),
        })
    return rows


def _insurance_data(user):
    """التأمينات"""
    from employees.models import Employee
    company = getattr(user, 'company', None)
    rows = []
    insured = Employee._base_manager.filter(company=company, status='active', has_insurance=True)
    for emp in insured:
        base = float(emp.basic_salary or 0)
        ins_base = float(getattr(emp, 'insurance_base_salary', None) or base)
        rows.append({
            'employee_code': emp.employee_code,
            'employee_name': _employee_name(emp),
            'insurance_number': emp.insurance_number or '',
            'basic_salary': round(base, 2),
            'insurance_base': round(ins_base, 2),
            'insurance_amount': round(ins_base * 0.11, 2),
        })
    return rows


def _tax_data(user, year, month):
    """الضرائب"""
    from employees.models import Employee, Deduction
    company = getattr(user, 'company', None)
    rows = []
    for emp in Employee._base_manager.filter(company=company, status='active'):
        taxes = Deduction._base_manager.filter(
            employee=emp, deduction_type='tax', year=year, month=month,
        )
        tax_sum = sum(float(d.amount) for d in taxes)
        if tax_sum > 0:
            rows.append({
                'employee_code': emp.employee_code,
                'employee_name': _employee_name(emp),
                'basic_salary': round(float(emp.basic_salary or 0), 2),
                'tax_amount': round(tax_sum, 2),
            })
    return rows


def _turnover_data(user, year):
    """معدل دوران الموظفين"""
    from employees.models import Employee
    from datetime import date
    company = getattr(user, 'company', None)
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    all_emps = Employee._base_manager.filter(company=company)
    hired = all_emps.filter(hire_date__gte=year_start, hire_date__lte=year_end).count()
    terminated = all_emps.filter(
        status__in=['terminated', 'resigned', 'retired'],
        termination_date__gte=year_start, termination_date__lte=year_end,
    ).count()
    active = all_emps.filter(status='active').count()

    rows = [
        {'metric': f'التعيينات في {year}', 'value': hired},
        {'metric': f'انتهاء الخدمة في {year}', 'value': terminated},
        {'metric': 'الموظفين النشطين حالياً', 'value': active},
        {'metric': 'معدل الدوران %', 'value': round((terminated/max(active,1))*100, 2)},
    ]
    return rows


def _branch_comparison_data(user):
    """مقارنة الفروع والأقسام"""
    # حجب التقرير عن المديرين وإتاحته للأدمن والـ HR فقط
    if getattr(user, 'role', None) not in ['company_admin', 'hr_manager', 'super_admin']:
        return []

    from employees.models import Employee
    from companies.models import Branch
    from attendance.models import Attendance
    from django.db.models import Sum, Count, Q
    from datetime import timedelta
    company = getattr(user, 'company', None)
    today = timezone.localdate()
    date_from = today - timedelta(days=30)
    rows = []
    for br in Branch._base_manager.filter(company=company):
        emps = Employee._base_manager.filter(branch=br, status='active')
        emp_ids = list(emps.values_list('id', flat=True))
        salaries = [float(e.basic_salary or 0) for e in emps]

        # بيانات الحضور آخر 30 يوم
        att_qs = Attendance._base_manager.filter(
            employee_id__in=emp_ids,
            date__gte=date_from,
            date__lte=today,
        )
        present_days = att_qs.filter(status__in=['present', 'late']).count()
        absent_days = att_qs.filter(status='absent').count()
        late_minutes = att_qs.aggregate(t=Sum('late_minutes'))['t'] or 0
        overtime_hours = att_qs.aggregate(t=Sum('overtime_hours'))['t'] or 0

        rows.append({
            'branch_name': br.name_ar,
            'employees_count': len(salaries),
            'total_salary': round(sum(salaries), 2),
            'avg_salary': round(sum(salaries)/len(salaries) if salaries else 0, 2),
            'max_salary': round(max(salaries) if salaries else 0, 2),
            'min_salary': round(min(salaries) if salaries else 0, 2),
            'present_days': present_days,
            'absent_days': absent_days,
            'total_late_minutes': int(late_minutes),
            'total_overtime_hours': round(float(overtime_hours), 2),
        })
    return rows


def _contracts_expiry_data(user):
    """العقود المنتهية / قريبة الانتهاء"""
    from employees.models import Employee
    from datetime import timedelta
    company = getattr(user, 'company', None)
    today = timezone.localdate()
    next_90 = today + timedelta(days=90)

    rows = []
    emps = Employee._base_manager.filter(
        company=company, status='active', contract_end_date__isnull=False,
    )
    for emp in emps:
        end = emp.contract_end_date
        if end < today:
            rows.append({
                'employee_name': _employee_name(emp),
                'employee_code': emp.employee_code,
                'contract_end': str(end),
                'status': 'منتهي',
                'days': (today - end).days,
            })
        elif end <= next_90:
            rows.append({
                'employee_name': _employee_name(emp),
                'employee_code': emp.employee_code,
                'contract_end': str(end),
                'status': 'قريب الانتهاء',
                'days': (end - today).days,
            })
    return rows


def _loans_advances_data(user):
    """السلف والقروض"""
    company = getattr(user, 'company', None)
    rows = []
    try:
        from requests_app.models import EmployeeRequest
        from django.db.models import Q
        loans = EmployeeRequest._base_manager.filter(
            company=company, status__in=['approved', 'pending'],
        ).filter(Q(request_type__name__icontains='سلفة') | Q(request_type__name__icontains='قرض'))
        for loan in loans:
            rows.append({
                'employee_name': _employee_name(loan.employee),
                'type': loan.request_type.name if loan.request_type else '',
                'amount': round(float(loan.amount or 0), 2),
                'status': loan.status,
                'created_at': str(loan.created_at)[:10] if loan.created_at else '',
            })
    except Exception:
        pass
    return rows


def _missions_performance_data(user):
    """أداء المهام"""
    employees = _get_manager_scope_employees(user)
    rows = []
    try:
        from attendance.models import MissionAssignment
        for emp in employees:
            assignments = MissionAssignment._base_manager.filter(employee=emp)
            total = assignments.count()
            if total > 0:
                completed = assignments.filter(status='completed').count()
                rows.append({
                    'employee_name': _employee_name(emp),
                    'total_missions': total,
                    'completed': completed,
                    'in_progress': assignments.filter(status='in_progress').count(),
                    'pending': assignments.filter(status='pending').count(),
                    'completion_rate': round((completed/total*100), 2),
                })
    except Exception:
        pass
    return rows


def _executive_dashboard_data(user):
    """التقرير التنفيذي"""
    from employees.models import Employee
    company = getattr(user, 'company', None)
    active = Employee._base_manager.filter(company=company, status='active')
    total_sal = sum(float(e.basic_salary or 0) for e in active)
    rows = [
        {'metric': 'إجمالي الموظفين النشطين', 'value': active.count()},
        {'metric': 'إجمالي الرواتب الشهرية', 'value': round(total_sal, 2)},
        {'metric': 'إجمالي الرواتب السنوية', 'value': round(total_sal * 12, 2)},
        {'metric': 'متوسط الراتب', 'value': round(total_sal/active.count() if active.count() else 0, 2)},
    ]
    return rows


# ═══════════════════════════════════════════════════
# API Views - كل تقرير عنده 3 endpoints: json, excel, pdf
# ═══════════════════════════════════════════════════

def _make_report_views(report_key, data_func, title, columns, needs_year_month=False, needs_year=False):
    """factory لتوليد 3 views (json, excel, pdf) لأي تقرير"""

    def _get_params(request):
        from datetime import date as _d
        if needs_year_month:
            year = int(request.GET.get('year', _d.today().year))
            month = int(request.GET.get('month', _d.today().month))
            return {'year': year, 'month': month}
        if needs_year:
            year = int(request.GET.get('year', _d.today().year))
            return {'year': year}
        return {}

    @api_view(['GET'])
    @authentication_classes([TokenAuthentication, JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def view_json(request):
        user = request.user
        if not _check_manager(user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)
        params = _get_params(request)
        rows = data_func(user, **params) if params else data_func(user)
        return Response({
            'title': title,
            'count': len(rows),
            'results': rows,
        })

    @api_view(['GET'])
    @authentication_classes([TokenAuthentication, JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def view_excel(request):
        from attendance.report_export_helper import export_to_excel
        user = request.user
        if not _check_manager(user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)
        params = _get_params(request)
        rows = data_func(user, **params) if params else data_func(user)
        if not rows:
            rows = [{'info': 'لا توجد بيانات'}]
            cols = [('info', 'ملاحظة', 40)]
        else:
            cols = columns
        return export_to_excel(title=title, columns=cols, rows=rows, user=user, filename=f'{report_key}.xlsx')

    @api_view(['GET'])
    @authentication_classes([TokenAuthentication, JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def view_pdf(request):
        from attendance.report_export_helper import export_to_pdf
        user = request.user
        if not _check_manager(user):
            return Response({'error': 'صلاحية غير كافية'}, status=403)
        params = _get_params(request)
        rows = data_func(user, **params) if params else data_func(user)
        if not rows:
            rows = [{'info': 'لا توجد بيانات'}]
            cols = [('info', 'ملاحظة', 40)]
        else:
            cols = columns
        return export_to_pdf(title=title, columns=cols, rows=rows, user=user, filename=f'{report_key}.pdf')

    return view_json, view_excel, view_pdf


# ═══════════════════════════════════════════════════
# Generate all views
# ═══════════════════════════════════════════════════

def _payroll_data(user, year, month):
    """داتا الرواتب للـ PDF/Excel الاحترافي"""
    from attendance.payroll_rules import calculate_effective_payroll
    from attendance.api_payroll import _get_payroll_settings
    
    employees = _get_manager_scope_employees(user)
    settings = _get_payroll_settings(user)
    lang = 'ar'
    
    rows = []
    for emp in employees:
        try:
            p = calculate_effective_payroll(emp, year, month, settings, lang=lang)
            rows.append({
                'employee_code': getattr(emp, 'employee_code', '') or '',
                'employee_name': _employee_name(emp),
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') or '',
                'basic_salary': round(p.get('basic_salary', 0), 2),
                'allowances_total': round(p.get('allowances_total', 0), 2),
                'bonuses_total': round(p.get('bonuses_total', 0), 2),
                'overtime_bonus': round(p.get('overtime_bonus', 0), 2),
                'gross_salary': round(p.get('gross_salary', 0), 2),
                'late_deduction': round(p.get('late_deduction', 0), 2),
                'absence_deduction': round(p.get('absence_deduction', 0), 2),
                'insurance_deduction': round(p.get('insurance_deduction', 0), 2),
                'total_deductions': round(p.get('total_deductions', 0), 2),
                'net_salary': round(p.get('net_salary', 0), 2),
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'_payroll_data error for {emp}: {e}')
    return rows


payroll_report_json, payroll_export_excel, payroll_export_pdf = _make_report_views(
    'payroll', _payroll_data, 'تقرير المرتبات',
    columns=[
        ('employee_code', 'الكود', 12),
        ('employee_name', 'الموظف', 25),
        ('department', 'القسم', 20),
        ('basic_salary', 'الأساسي', 12),
        ('allowances_total', 'البدلات', 12),
        ('bonuses_total', 'المكافآت', 12),
        ('overtime_bonus', 'الإضافي', 12),
        ('gross_salary', 'الإجمالي', 14),
        ('total_deductions', 'الخصومات', 14),
        ('net_salary', 'الصافي', 14),
    ],
    needs_year_month=True,
)


reimbursements_report, reimbursements_export_excel, reimbursements_export_pdf = _make_report_views(
    'reimbursements', _reimbursements_data, 'تقرير رد المصروفات',
    [
        ('employee_name', 'اسم الموظف', 25),
        ('type', 'النوع', 20),
        ('subject', 'الموضوع', 30),
        ('amount', 'المبلغ', 15),
        ('status', 'الحالة', 15),
        ('created_at', 'التاريخ', 15),
    ],
)

bank_transfer_report, bank_transfer_export_excel, bank_transfer_export_pdf = _make_report_views(
    'bank_transfer', _bank_transfer_data, 'كشف تحويلات البنك',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('bank_name', 'البنك', 20),
        ('account_number', 'رقم الحساب', 20),
        ('iban', 'IBAN', 25),
        ('amount', 'المبلغ', 15),
    ],
)

insurance_report, insurance_export_excel, insurance_export_pdf = _make_report_views(
    'insurance', _insurance_data, 'تقرير التأمينات',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('insurance_number', 'رقم التأمين', 18),
        ('basic_salary', 'الراتب الأساسي', 15),
        ('insurance_base', 'الأساس التأميني', 18),
        ('insurance_amount', 'مبلغ التأمين', 15),
    ],
)

tax_report, tax_export_excel, tax_export_pdf = _make_report_views(
    'tax', _tax_data, 'تقرير الضرائب',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('basic_salary', 'الراتب الأساسي', 18),
        ('tax_amount', 'مبلغ الضريبة', 18),
    ],
    needs_year_month=True,
)

turnover_report, turnover_export_excel, turnover_export_pdf = _make_report_views(
    'turnover', _turnover_data, 'معدل دوران الموظفين',
    [
        ('metric', 'البند', 40),
        ('value', 'القيمة', 20),
    ],
    needs_year=True,
)

branch_comparison_report, branch_comparison_export_excel, branch_comparison_export_pdf = _make_report_views(
    'branch_comparison', _branch_comparison_data, 'مقارنة الفروع',
    [
        ('branch_name', 'الفرع', 25),
        ('employees_count', 'عدد الموظفين', 15),
        ('total_salary', 'إجمالي الرواتب', 20),
        ('avg_salary', 'متوسط الراتب', 18),
        ('max_salary', 'أعلى راتب', 15),
        ('min_salary', 'أقل راتب', 15),
        ('present_days', 'أيام الحضور 30 يوم', 18),
        ('absent_days', 'أيام الغياب 30 يوم', 18),
        ('total_late_minutes', 'إجمالي دقائق التأخير', 20),
        ('total_overtime_hours', 'إجمالي الأوفر تايم', 18),
    ],
)

contracts_expiry_report, contracts_expiry_export_excel, contracts_expiry_export_pdf = _make_report_views(
    'contracts_expiry', _contracts_expiry_data, 'تقرير العقود المنتهية',
    [
        ('employee_code', 'الكود', 15),
        ('employee_name', 'اسم الموظف', 25),
        ('contract_end', 'تاريخ الانتهاء', 18),
        ('status', 'الحالة', 20),
        ('days', 'عدد الأيام', 15),
    ],
)

loans_advances_report, loans_advances_export_excel, loans_advances_export_pdf = _make_report_views(
    'loans_advances', _loans_advances_data, 'تقرير السلف والقروض',
    [
        ('employee_name', 'اسم الموظف', 25),
        ('type', 'النوع', 20),
        ('amount', 'المبلغ', 15),
        ('status', 'الحالة', 15),
        ('created_at', 'التاريخ', 15),
    ],
)

missions_performance_report, missions_performance_export_excel, missions_performance_export_pdf = _make_report_views(
    'missions_performance', _missions_performance_data, 'تقرير أداء المهام',
    [
        ('employee_name', 'اسم الموظف', 25),
        ('total_missions', 'إجمالي المهام', 18),
        ('completed', 'المكتملة', 15),
        ('in_progress', 'جاري تنفيذها', 18),
        ('pending', 'معلقة', 15),
        ('completion_rate', 'نسبة الإنجاز %', 20),
    ],
)

executive_dashboard_report, executive_dashboard_export_excel, executive_dashboard_export_pdf = _make_report_views(
    'executive_dashboard', _executive_dashboard_data, 'التقرير التنفيذي',
    [
        ('metric', 'البند', 40),
        ('value', 'القيمة', 25),
    ],
)

# ═══════════════════════════════════════════════════
# CEO/HR Unified Dashboard - نبض الشركة
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def unified_dashboard(request):
    """Dashboard شامل - كل ما يحتاجه صاحب الشركة والـ HR"""
    from datetime import date, timedelta
    from employees.models import Employee
    from attendance.models import Attendance
    from django.db.models import Sum, Count, Avg

    user = request.user
    if not _check_manager(user):
        return Response({'error': 'صلاحية غير كافية'}, status=403)

    company = getattr(user, 'company', None)
    if not company:
        return Response({'error': 'لا توجد شركة'}, status=400)

    today = timezone.localdate()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month_end = month_start - timedelta(days=1)

    # ═══ 1) نبض الشركة النهاردة ═══
    # استخدم scope المدير (لو HR/admin → كل الشركة، لو manager → فريقه فقط)
    all_emps = _get_manager_scope_employees(user)
    scope_emp_ids = list(all_emps.values_list('id', flat=True))

    active_emps = all_emps.filter(status='active')
    total_active = active_emps.count()

    today_att = Attendance._base_manager.filter(
        employee_id__in=scope_emp_ids, date=today,
    )
    present_today = today_att.filter(status='present').count()
    late_today = today_att.filter(status='late').count()
    absent_today = max(0, total_active - today_att.count())
    on_leave_today = today_att.filter(status='on_leave').count()

    attendance_rate = round((present_today + late_today) / max(total_active, 1) * 100, 1)

    # ═══ 2) المالية ═══
    total_monthly_salary = sum(float(e.basic_salary or 0) for e in active_emps)

    # سلف قائمة
    total_active_loans = 0
    active_loans_count = 0
    try:
        from requests_app.models import EmployeeRequest
        from django.db.models import Q
        loans = EmployeeRequest._base_manager.filter(
            company=company, status='approved',
            employee_id__in=scope_emp_ids,
        ).filter(Q(request_type__name__icontains='سلفة') | Q(request_type__name__icontains='قرض'))
        total_active_loans = sum(float(l.amount or 0) for l in loans)
        active_loans_count = loans.count()
    except Exception:
        pass

    # الفرق عن الشهر اللي فات
    last_month_att_count = Attendance._base_manager.filter(
        employee_id__in=scope_emp_ids,
        date__gte=last_month_start, date__lte=last_month_end,
        status='present',
    ).count()
    this_month_att_count = Attendance._base_manager.filter(
        employee_id__in=scope_emp_ids,
        date__gte=month_start, date__lte=today,
        status='present',
    ).count()

    # ═══ 3) القرارات المطلوبة ═══
    pending_requests = 0
    pending_leaves = 0
    try:
        from requests_app.models import EmployeeRequest
        pending_requests = EmployeeRequest._base_manager.filter(
            company=company, status='pending',
            employee_id__in=scope_emp_ids,
        ).count()
    except Exception:
        pass

    try:
        from leaves.models import LeaveRequest
        pending_leaves = LeaveRequest._base_manager.filter(
            company=company, status='pending',
            employee_id__in=scope_emp_ids,
        ).count()
    except Exception:
        pass

    # عقود قربت تنتهي (30 يوم)
    next_30_days = today + timedelta(days=30)
    contracts_expiring = active_emps.filter(
        contract_end_date__isnull=False,
        contract_end_date__gte=today,
        contract_end_date__lte=next_30_days,
    ).count()

    # موظفين في فترة تجربة (خلصت خلال الشهر)
    probation_ending = 0
    for emp in active_emps:
        if emp.hire_date and hasattr(emp, 'probation_months'):
            prob_months = emp.probation_months or 3
            probation_end = emp.hire_date + timedelta(days=prob_months * 30)
            if today <= probation_end <= next_30_days:
                probation_ending += 1

    # ═══ 4) الترند - آخر 30 يوم ═══
    attendance_trend = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        count = Attendance._base_manager.filter(
            employee_id__in=scope_emp_ids, date=d, status='present',
        ).count()
        attendance_trend.append({
            'date': str(d),
            'present': count,
        })

    # ═══ 5) توزيع الموظفين حسب القسم ═══
    from companies.models import Department, Branch
    dept_distribution = []
    for dept in Department._base_manager.filter(company=company):
        count = active_emps.filter(department=dept).count()
        if count > 0:
            dept_distribution.append({
                'name': dept.name_ar,
                'count': count,
            })

    branch_distribution = []
    for br in Branch._base_manager.filter(company=company):
        emps_br = active_emps.filter(branch=br)
        count = emps_br.count()
        salary = sum(float(e.basic_salary or 0) for e in emps_br)
        if count > 0:
            branch_distribution.append({
                'name': br.name_ar,
                'count': count,
                'total_salary': round(salary, 2),
            })

    # ═══ 6) Turnover الشهر ═══
    hired_this_month = active_emps.filter(
        hire_date__gte=month_start, hire_date__lte=today,
    ).count()
    terminated_this_month = all_emps.filter(
        status__in=['terminated', 'resigned', 'retired'],
        termination_date__gte=month_start,
        termination_date__lte=today,
    ).count()

    # ═══ 7) أفضل 5 موظفين (حضور الشهر) ═══
    top_performers = []
    for emp in active_emps[:100]:  # نجيب 100 ونرتب
        emp_att = Attendance._base_manager.filter(
            employee=emp, date__gte=month_start, date__lte=today,
        )
        present = emp_att.filter(status='present').count()
        late = emp_att.filter(status='late').count()
        total_days = (today - month_start).days + 1
        score = (present * 100 + late * 50) / max(total_days, 1)
        top_performers.append({
            'employee_id': emp.id,
            'name': _employee_name(emp),
            'present_days': present,
            'late_days': late,
            'score': round(score, 1),
        })

    top_performers.sort(key=lambda x: x['score'], reverse=True)

    # ═══ 8) موظفين محتاجين متابعة ═══
    need_attention = []
    for emp in active_emps[:100]:
        emp_att = Attendance._base_manager.filter(
            employee=emp, date__gte=month_start, date__lte=today,
        )
        absent = emp_att.filter(status='absent').count()
        late = emp_att.filter(status='late').count()
        if absent >= 3 or late >= 5:
            need_attention.append({
                'employee_id': emp.id,
                'name': _employee_name(emp),
                'absent_days': absent,
                'late_days': late,
            })

    need_attention.sort(key=lambda x: (x['absent_days'] + x['late_days']), reverse=True)

    # ═══ 9) تنبيهات ذكية ═══
    alerts = []

    if contracts_expiring > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'file-warning',
            'title': f'{contracts_expiring} عقد قرب انتهاؤه',
            'action': '/hr/reports/contracts-expiry',
        })

    if pending_requests + pending_leaves > 0:
        alerts.append({
            'type': 'info',
            'icon': 'inbox',
            'title': f'{pending_requests + pending_leaves} طلب معلق ينتظر الموافقة',
            'action': '/hr/requests',
        })

    if active_loans_count > 0:
        alerts.append({
            'type': 'info',
            'icon': 'wallet',
            'title': f'{active_loans_count} سلفة/قرض قائمة ({round(total_active_loans, 0)} جنيه)',
            'action': '/hr/reports/loans-advances',
        })

    if len(need_attention) > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'alert-triangle',
            'title': f'{len(need_attention)} موظف يحتاج متابعة (تأخير/غياب)',
            'action': '/hr/attendance',
        })

    if probation_ending > 0:
        alerts.append({
            'type': 'info',
            'icon': 'user-check',
            'title': f'{probation_ending} موظف تنتهي فترة تجربتهم',
            'action': '/hr/employees',
        })

    return Response({
        'today': str(today),
        'pulse': {
            'total_employees': total_active,
            'present': present_today,
            'late': late_today,
            'absent': absent_today,
            'on_leave': on_leave_today,
            'attendance_rate': attendance_rate,
        },
        'financial': {
            'monthly_salary': round(total_monthly_salary, 2),
            'yearly_salary': round(total_monthly_salary * 12, 2),
            'active_loans_amount': round(total_active_loans, 2),
            'active_loans_count': active_loans_count,
            'this_month_attendance': this_month_att_count,
            'last_month_attendance': last_month_att_count,
            'attendance_change': this_month_att_count - last_month_att_count,
        },
        'decisions': {
            'pending_requests': pending_requests,
            'pending_leaves': pending_leaves,
            'contracts_expiring_30d': contracts_expiring,
            'probation_ending_30d': probation_ending,
        },
        'trend': {
            'attendance_last_30_days': attendance_trend,
        },
        'distribution': {
            'by_department': dept_distribution,
            'by_branch': branch_distribution,
        },
        'turnover': {
            'hired_this_month': hired_this_month,
            'terminated_this_month': terminated_this_month,
        },
        'top_performers': top_performers[:5],
        'need_attention': need_attention[:5],
        'alerts': alerts,
    })

