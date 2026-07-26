"""
MotionHR - Payroll API (v4 - Phase 15 Payroll Pro)
"""
from datetime import datetime
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

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
    """
    الوصول للمرتبات مقصور على:
    - super_admin (is_superuser / is_staff)
    - company_admin (صاحب الشركة)
    - hr_manager (مدير الموارد البشرية)

    المدير العادي (manager) ممنوع من الوصول للمرتبات لأسباب أمان.
    """
    role = getattr(user, 'role', None)
    return (
        user.is_superuser
        or user.is_staff
        or role in ['company_admin', 'hr_manager']
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
        'night_allowance': payroll.get('night_allowance', 0),
        'weekend_allowance': payroll.get('weekend_allowance', 0),
        'gross_salary': payroll.get('gross_salary', 0),
        'policy_name': payroll.get('policy_name'),

        'flex_shortage_deduction': payroll.get('flex_shortage_deduction', 0),
        'early_leave_deduction': payroll.get('early_leave_deduction', 0),
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
        'total_early_leave_minutes': payroll.get('total_early_leave_minutes', 0),
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
        try:
            from accounts.models import User
            company = getattr(user, 'company', None)
            if company:
                settings['payroll_cycle_type'] = getattr(company, 'payroll_cycle_type', 'calendar_month') or 'calendar_month'
                settings['payroll_cutoff_day'] = getattr(company, 'payroll_cutoff_day', 1) or 1
                settings['payroll_pay_day'] = getattr(company, 'payroll_pay_day', 1) or 1
                settings['payroll_pay_month_offset'] = getattr(company, 'payroll_pay_month_offset', 'same_month') or 'same_month'
                settings['payroll_period_label_mode'] = getattr(company, 'payroll_period_label_mode', 'cutoff_month') or 'cutoff_month'
        except Exception:
            pass
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

        try:
            company = getattr(user, 'company', None)
            if company:
                if 'payroll_cycle_type' in data:
                    company.payroll_cycle_type = data['payroll_cycle_type']
                if 'payroll_cutoff_day' in data:
                    val = int(data['payroll_cutoff_day'])
                    company.payroll_cutoff_day = max(1, min(val, 28))
                if 'payroll_pay_day' in data:
                    val = int(data['payroll_pay_day'])
                    company.payroll_pay_day = max(1, min(val, 31))
                if 'payroll_pay_month_offset' in data:
                    company.payroll_pay_month_offset = data['payroll_pay_month_offset']
                if 'payroll_period_label_mode' in data:
                    company.payroll_period_label_mode = data['payroll_period_label_mode']
                company.save(update_fields=[
                    'payroll_cycle_type', 'payroll_cutoff_day',
                    'payroll_pay_day', 'payroll_pay_month_offset',
                    'payroll_period_label_mode'
                ])
        except Exception as cycle_err:
            import logging
            logging.getLogger(__name__).warning(f'payroll cycle save error: {cycle_err}')

        company = getattr(user, 'company', None)
        return Response({
            'status': 'saved',
            'late_deduction_per_minute': float(obj.late_deduction_per_minute),
            'absence_deduction_per_day': float(obj.absence_deduction_per_day),
            'overtime_rate_per_hour': float(obj.overtime_rate_per_hour),
            'insurance_mode': getattr(obj, 'insurance_mode', 'none'),
            'insurance_fixed_amount': float(getattr(obj, 'insurance_fixed_amount', 0) or 0),
            'insurance_percent': float(getattr(obj, 'insurance_percent', 0) or 0),
            'payroll_cycle_type': getattr(company, 'payroll_cycle_type', 'calendar_month') if company else 'calendar_month',
            'payroll_cutoff_day': getattr(company, 'payroll_cutoff_day', 1) if company else 1,
            'payroll_pay_day': getattr(company, 'payroll_pay_day', 1) if company else 1,
            'payroll_pay_month_offset': getattr(company, 'payroll_pay_month_offset', 'same_month') if company else 'same_month',
            'payroll_period_label_mode': getattr(company, 'payroll_period_label_mode', 'cutoff_month') if company else 'cutoff_month',
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
    يدعم إرجاع JSON أو ملف PDF
    """
    user = request.user
    year, month = _parse_month(request)
    lang = _get_lang(request)
    req_format = request.GET.get('format', 'json')

    try:
        from employees.models import Employee
        emp = Employee._base_manager.get(user=user)
    except Exception:
        return Response({'error': 'Employee not found'}, status=404)

    settings = _get_payroll_settings(user)
    payroll = calculate_effective_payroll(emp, year, month, settings, lang=lang)

    if req_format == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from io import BytesIO

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            # عنوان الكشف
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width/2.0, height - 20*mm, f"Payslip - {month}/{year}")

            # بيانات الموظف
            p.setFont("Helvetica", 12)
            p.drawString(20*mm, height - 40*mm, f"Employee: {emp.first_name_en or emp.first_name_ar} {emp.last_name_en or emp.last_name_ar}")
            p.drawString(20*mm, height - 48*mm, f"Department: {emp.department.name_en if emp.department else 'N/A'}")

            # تفاصيل المرتب (مبسط للسرعة والأمان كنسخة أولى)
            p.drawString(20*mm, height - 60*mm, "--------------------------------------------------")
            p.drawString(20*mm, height - 70*mm, f"Basic Salary: {payroll.get('basic_salary', 0)}")
            p.drawString(20*mm, height - 78*mm, f"Total Allowances: + {payroll.get('total_allowances', 0)}")
            p.drawString(20*mm, height - 86*mm, f"Total Deductions: - {payroll.get('total_deductions', 0)}")
            
            p.setFont("Helvetica-Bold", 14)
            p.drawString(20*mm, height - 100*mm, f"Net Salary: {payroll.get('net_salary', 0)}")

            p.showPage()
            p.save()

            pdf_bytes = buffer.getvalue()
            buffer.close()

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payslip_{year}_{month}.pdf"'
            return response
        except Exception as e:
            return Response({'error': f'PDF generation failed: {str(e)}'}, status=500)

    return Response({'year': year, 'month': month, 'lang': lang, **payroll})


# ══════════════════════════════════════════════
# PAYROLL RUN APIs
# ══════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_runs_list(request):
    """قائمة تشغيلات المرتبات السابقة"""
    user = request.user
    if not _check_manager(user):
        return Response({'success': False, 'error': 'صلاحية غير كافية'}, status=403)

    try:
        from attendance.payroll_pro_models import PayrollRun
        company = getattr(user, 'company', None)
        if not company:
            return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

        runs = PayrollRun._base_manager.filter(
            company=company
        ).select_related('approved_by').order_by('-year', '-month')[:24]

        data = []
        for r in runs:
            data.append({
                'id': r.id,
                'year': r.year,
                'month': r.month,
                'status': r.status,
                'status_label': {
                    'draft': 'مسودة',
                    'approved': 'معتمد',
                    'locked': 'مقفول',
                }.get(r.status, r.status),
                'total_employees': r.lines.count(),
                'approved_by': r.approved_by.get_full_name() if r.approved_by else None,
                'approved_at': str(r.approved_at)[:16] if r.approved_at else None,
                'created_at': str(r.created_at)[:16] if r.created_at else None,
                'notes': r.notes or '',
            })

        return Response({'success': True, 'runs': data, 'count': len(data)})

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('payroll_runs_list error')
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_run_create(request):
    """
    تشغيل المرتبات لشهر معين
    بيحسب مرتب كل موظف ويحفظه في PayrollLine
    """
    user = request.user
    if not _check_manager(user):
        return Response({'success': False, 'error': 'صلاحية غير كافية'}, status=403)

    try:
        from attendance.payroll_pro_models import PayrollRun, PayrollLine
        from employees.models import Employee

        company = getattr(user, 'company', None)
        if not company:
            return Response({'success': False, 'error': 'لا توجد شركة مرتبطة'}, status=400)

        data = request.data
        year = int(data.get('year', datetime.now().year))
        month = int(data.get('month', datetime.now().month))
        notes = data.get('notes', '')
        lang = data.get('lang', 'ar')

        if month < 1 or month > 12:
            return Response({'success': False, 'error': 'شهر غير صحيح'}, status=400)

        # لو فيه run موجود لنفس الشهر وحالته draft → نمسحه ونعيد الحساب
        existing = PayrollRun._base_manager.filter(
            company=company, year=year, month=month
        ).first()

        if existing and existing.status in ('approved', 'locked'):
            return Response({
                'success': False,
                'error': f'يوجد تشغيل معتمد/مقفول لهذا الشهر (ID: {existing.id}). لا يمكن إعادة التشغيل.'
            }, status=400)

        if existing:
            existing.lines.all().delete()
            run = existing
            run.notes = notes
            run.status = 'draft'
            run.save()
        else:
            run = PayrollRun._base_manager.create(
                company=company,
                year=year,
                month=month,
                status='draft',
                notes=notes,
                created_by=user,
            )

        settings = _get_payroll_settings(user)
        employees = Employee._base_manager.filter(
            company=company,
            status='active'
        ).select_related('user', 'branch', 'department', 'job_title')

        results = []
        errors = []
        grand_net = 0.0

        for emp in employees:
            try:
                payroll = calculate_effective_payroll(emp, year, month, settings, lang=lang)

                PayrollLine._base_manager.create(
                    company=company,
                    payroll_run=run,
                    employee=emp,
                    basic_salary=payroll.get('basic_salary', 0),
                    allowances_total=payroll.get('allowances_total', 0),
                    overtime_total=payroll.get('overtime_bonus', 0),
                    bonuses_total=payroll.get('bonuses_total', 0),
                    gross_salary=payroll.get('gross_salary', 0),
                    late_deduction=payroll.get('late_deduction', 0),
                    absence_deduction=payroll.get('absence_deduction', 0),
                    insurance_deduction=payroll.get('insurance_deduction', 0),
                    installments_total=payroll.get('installments_total', 0),
                    penalties_total=payroll.get('penalties_total', 0),
                    extra_deductions_total=payroll.get('extra_deductions_total', 0),
                    total_deductions=payroll.get('total_deductions', 0),
                    net_salary=payroll.get('net_salary', 0),
                    working_days=payroll.get('total_working_days', 0),
                    attended_days=payroll.get('attended_days', 0),
                    absent_days=payroll.get('absent_days', 0),
                    late_days=payroll.get('late_days', 0),
                    mission_days=payroll.get('mission_days', 0),
                    on_leave_days=payroll.get('on_leave_days', 0),
                    overtime_hours=payroll.get('overtime_hours', 0),
                    late_minutes=payroll.get('total_late_minutes', 0),
                    currency=payroll.get('currency', 'EGP'),
                    created_by=user,
                )

                grand_net += float(payroll.get('net_salary', 0))
                results.append({
                    'employee_id': emp.id,
                    'employee_name': payroll.get('employee_name', ''),
                    'net_salary': payroll.get('net_salary', 0),
                    'currency': payroll.get('currency', 'EGP'),
                })

            except Exception as emp_err:
                errors.append({
                    'employee_id': emp.id,
                    'employee_name': getattr(emp, 'full_name_ar', str(emp)),
                    'error': str(emp_err),
                })

        return Response({
            'success': True,
            'run_id': run.id,
            'year': year,
            'month': month,
            'status': 'draft',
            'total_employees': len(results),
            'grand_net': round(grand_net, 2),
            'errors_count': len(errors),
            'errors': errors,
            'message': f'تم حساب مرتبات {len(results)} موظف بنجاح',
        })

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('payroll_run_create error')
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_run_approve(request, run_id):
    """اعتماد تشغيل المرتبات — صاحب الشركة وHR فقط"""
    user = request.user
    if not _check_manager(user):
        return Response({'success': False, 'error': 'صلاحية غير كافية'}, status=403)

    try:
        from attendance.payroll_pro_models import PayrollRun
        from django.utils import timezone

        company = getattr(user, 'company', None)

        try:
            run = PayrollRun._base_manager.get(id=run_id, company=company)
        except PayrollRun.DoesNotExist:
            return Response({'success': False, 'error': 'التشغيل غير موجود'}, status=404)

        if run.status == 'locked':
            return Response({'success': False, 'error': 'التشغيل مقفول ولا يمكن تعديله'}, status=400)

        if run.status == 'approved':
            return Response({'success': False, 'error': 'التشغيل معتمد مسبقاً'}, status=400)

        run.status = 'approved'
        run.approved_by = user
        run.approved_at = timezone.now()
        run.save()

        return Response({
            'success': True,
            'message': f'تم اعتماد مرتبات {run.month}/{run.year} بنجاح',
            'run_id': run.id,
            'approved_by': user.get_full_name() or user.username,
        })

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('payroll_run_approve error')
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def payroll_run_detail(request, run_id):
    """تفاصيل تشغيل مرتبات محدد"""
    user = request.user
    if not _check_manager(user):
        return Response({'success': False, 'error': 'صلاحية غير كافية'}, status=403)

    try:
        from attendance.payroll_pro_models import PayrollRun

        company = getattr(user, 'company', None)

        try:
            run = PayrollRun._base_manager.get(id=run_id, company=company)
        except PayrollRun.DoesNotExist:
            return Response({'success': False, 'error': 'التشغيل غير موجود'}, status=404)

        lines = run.lines.select_related('employee').all()
        lines_data = []
        grand_net = 0.0

        for line in lines:
            emp = line.employee
            grand_net += float(line.net_salary or 0)
            lines_data.append({
                'employee_id': emp.id if emp else None,
                'employee_name': getattr(emp, 'full_name_ar', '') if emp else '',
                'employee_code': getattr(emp, 'employee_code', '') if emp else '',
                'branch': getattr(getattr(emp, 'branch', None), 'name_ar', '') if emp else '',
                'department': getattr(getattr(emp, 'department', None), 'name_ar', '') if emp else '',
                'basic_salary': float(line.basic_salary or 0),
                'allowances_total': float(line.allowances_total or 0),
                'overtime_total': float(line.overtime_total or 0),
                'bonuses_total': float(line.bonuses_total or 0),
                'gross_salary': float(line.gross_salary or 0),
                'late_deduction': float(line.late_deduction or 0),
                'absence_deduction': float(line.absence_deduction or 0),
                'insurance_deduction': float(line.insurance_deduction or 0),
                'installments_total': float(line.installments_total or 0),
                'penalties_total': float(line.penalties_total or 0),
                'extra_deductions_total': float(line.extra_deductions_total or 0),
                'total_deductions': float(line.total_deductions or 0),
                'net_salary': float(line.net_salary or 0),
                'currency': line.currency or 'EGP',
                'working_days': line.working_days or 0,
                'attended_days': line.attended_days or 0,
                'absent_days': line.absent_days or 0,
                'late_days': line.late_days or 0,
                'late_minutes': line.late_minutes or 0,
                'overtime_hours': float(line.overtime_hours or 0),
            })

        return Response({
            'success': True,
            'run_id': run.id,
            'year': run.year,
            'month': run.month,
            'status': run.status,
            'status_label': {'draft': 'مسودة', 'approved': 'معتمد', 'locked': 'مقفول'}.get(run.status, run.status),
            'total_employees': len(lines_data),
            'grand_net': round(grand_net, 2),
            'approved_by': run.approved_by.get_full_name() if run.approved_by else None,
            'approved_at': str(run.approved_at)[:16] if run.approved_at else None,
            'notes': run.notes or '',
            'lines': lines_data,
        })

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('payroll_run_detail error')
        return Response({'success': False, 'error': str(e)}, status=500)
