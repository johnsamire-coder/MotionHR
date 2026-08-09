"""
APIs للطلبات والإجازات من تطبيق الموبايل
"""
from django.utils import timezone
from django.db.models import Q
from accounts.fcm_service import (
    notify_request_approved,
    notify_request_rejected,
    notify_leave_approved,
    notify_leave_rejected,
    notify_manager_new_request,
    notify_manager_new_leave,
)
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from employees.models import Employee
from leaves.models import LeaveType, LeaveBalance, LeaveRequest
from requests_app.models import RequestCategory, RequestType, EmployeeRequest


def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).select_related('company').first()


ROLE_LABELS_AR = {
    'direct_manager': 'المدير المباشر',
    'department_manager': 'مدير القسم',
    'branch_manager': 'مدير الفرع',
    'hr_manager': 'مدير الموارد البشرية',
    'company_admin': 'صاحب الشركة',
    'skip': '',
}


def get_current_approver_info(req):
    """يرجع معلومات المسؤول الحالي عن الطلب"""
    if req.status != 'pending':
        return None

    try:
        from requests_app.models import ApprovalFlow
        flow = ApprovalFlow._base_manager.filter(
            company=req.company,
            request_type=req.request_type
        ).first()

        if not flow:
            return {
                'step': 1,
                'role': 'direct_manager',
                'role_label': 'المدير المباشر',
                'approver_name': None,
            }

        current_step = req.current_step or 1
        role_field = f'step_{current_step}_role'
        role = getattr(flow, role_field, 'direct_manager')

        if role == 'skip':
            return None

        role_label = ROLE_LABELS_AR.get(role, role)
        approver_name = None

        # نحاول نجيب اسم المدير
        if role == 'direct_manager':
            emp = req.employee
            if emp and emp.direct_manager:
                approver_name = emp.direct_manager.full_name_ar or emp.direct_manager.user.username

        return {
            'step': current_step,
            'role': role,
            'role_label': role_label,
            'approver_name': approver_name,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════
# الإجازات
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_leave_types(request):
    """أنواع الإجازات المتاحة مع الرصيد"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    year = timezone.localdate().year
    leave_types_qs = LeaveType._base_manager.filter(
        company=employee.company, is_active=True
    )
    emp_gender = (getattr(employee, "gender", "") or "").lower()
    if emp_gender == "male":
        leave_types_qs = leave_types_qs.exclude(gender_restriction="female")
    elif emp_gender == "female":
        leave_types_qs = leave_types_qs.exclude(gender_restriction="male")
    leave_types = leave_types_qs.order_by('name')

    result = []
    for lt in leave_types:
        balance = LeaveBalance._base_manager.filter(
            company=employee.company,
            employee=employee,
            leave_type=lt,
            year=year
        ).first()

        result.append({
            'id': lt.id,
            'name': lt.name,
            'name_en': getattr(lt, 'name_en', '') or '',
            'category': lt.category,
            'days_allowed': lt.days_allowed,
            'is_paid': lt.is_paid,
            'requires_document': lt.requires_document,
            'color': lt.color,
            'balance': {
                'total': float(balance.total_days) if balance else 0,
                'used': float(balance.used_days) if balance else 0,
                'pending': float(balance.pending_days) if balance else 0,
                'remaining': float(balance.remaining_days) if balance else 0,
            } if balance else {
                'total': 0, 'used': 0, 'pending': 0, 'remaining': 0,
            }
        })

    return Response({'success': True, 'leave_types': result})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_leave_request(request):
    """تقديم طلب إجازة"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    leave_type_id = request.data.get('leave_type_id')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    reason = request.data.get('reason', '').strip()
    half_day = request.data.get('half_day', False)
    half_day_type = request.data.get('half_day_type', 'morning').strip()

    if not all([leave_type_id, start_date, end_date, reason]):
        return Response({
            'success': False,
            'message': 'نوع الإجازة وتاريخ البداية والنهاية والسبب مطلوبين'
        }, status=400)

    try:
        leave_type = LeaveType._base_manager.get(
            id=leave_type_id, company=employee.company, is_active=True
        )
    except LeaveType.DoesNotExist:
        return Response({'success': False, 'message': 'نوع الإجازة غير موجود'}, status=404)

    from datetime import datetime
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response({
            'success': False,
            'message': 'صيغة التاريخ غلط. استخدم YYYY-MM-DD'
        }, status=400)

    if end < start:
        return Response({
            'success': False,
            'message': 'تاريخ النهاية لازم يكون بعد تاريخ البداية'
        }, status=400)

    # فحص التداخل مع إجازات موجودة
    overlap = LeaveRequest._base_manager.filter(
        company=employee.company,
        employee=employee,
        status__in=['pending', 'approved'],
        start_date__lte=end,
        end_date__gte=start,
    ).exists()
    if overlap:
        return Response({
            'success': False,
            'message': 'عندك إجازة موجودة بالفعل في نفس الفترة دي'
        }, status=400)

    if half_day and start_date == end_date:
        days_count = 0.5
    else:
        days_count = (end - start).days + 1

    # فحص الرصيد للإجازات المدفوعة فقط
    if leave_type.is_paid:
        year = start.year
        balance = LeaveBalance._base_manager.filter(
            company=employee.company,
            employee=employee,
            leave_type=leave_type,
            year=year,
        ).first()

        remaining = float(balance.remaining_days) if balance else 0
        if days_count > remaining:
            return Response({
                'success': False,
                'message': f'رصيدك من {leave_type.name} غير كافي. المتاح: {remaining} يوم، المطلوب: {days_count} يوم'
            }, status=400)

    _half_day_type_val = half_day_type if half_day and half_day_type in ('morning', 'afternoon') else ''
    _leave_hours = 4.0 if half_day else None

    _leave_notes = ''
    if half_day:
        _half_label = 'صباحي' if half_day_type == 'morning' else 'مسائي'
        _leave_notes = f'نص يوم ({_half_label})'

    leave_request = LeaveRequest._base_manager.create(
        company=employee.company,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        days_count=days_count,
        half_day_type=_half_day_type_val,
        leave_hours=_leave_hours,
        reason=reason,
        notes=_leave_notes if half_day else '',
        status='pending',
    )

    year = start.year
    balance = LeaveBalance._base_manager.filter(
        company=employee.company,
        employee=employee,
        leave_type=leave_type,
        year=year
    ).first()
    if balance:
        balance.pending_days = float(balance.pending_days) + days_count
        balance.save()

    # إشعار للمدير - طلب إجازة جديد
    try:
        leave_type_name = leave_type.name if leave_type else 'إجازة'
        employee_name = f"{employee.first_name_ar} {employee.last_name_ar}".strip() or employee.user.username
        notify_manager_new_leave(
            company=employee.company,
            employee_name=employee_name,
            leave_type=f"{leave_type_name} من {start} إلى {end} ({days_count} يوم)",
            leave_id=leave_request.id,
        )
    except Exception as e:
        print(f"FCM notification error: {e}")

    return Response({
        'success': True,
        'message': f'تم تقديم طلب الإجازة بنجاح ({days_count} يوم)',
        'request_id': leave_request.id,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_leaves(request):
    """عرض طلبات الإجازات الخاصة بي"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    search = request.query_params.get('search', '').strip()
    status_filter = request.query_params.get('status', '').strip().lower()

    leaves = LeaveRequest._base_manager.filter(
        employee=employee
    ).select_related('leave_type')

    if status_filter:
        leaves = leaves.filter(status=status_filter)

    if search:
        leaves = leaves.filter(
            Q(reason__icontains=search) |
            Q(leave_type__name__icontains=search)
        )

    leaves = leaves.order_by('-created_at')[:30]

    items = []
    for lr in leaves:
        items.append({
            'id': lr.id,
            'leave_type': lr.leave_type.name if lr.leave_type else '',
            'start_date': lr.start_date.strftime('%Y-%m-%d') if lr.start_date else '',
            'end_date': lr.end_date.strftime('%Y-%m-%d') if lr.end_date else '',
            'days_count': float(lr.days_count),
            'reason': lr.reason or '',
            'status': lr.status,
            'status_display': lr.get_status_display(),
            'created_at': lr.created_at.strftime('%Y-%m-%d %H:%M') if lr.created_at else '',
            'review_notes': lr.review_notes or '',
            'current_approver': _get_leave_approver_info(lr) if lr.status == 'pending' else None,
        })

    return Response({'success': True, 'items': items, 'leaves': items})


def _get_leave_approver_info(leave):
    """يرجع معلومات المسؤول عن الموافقة على الإجازة"""
    try:
        approver_name = None
        if leave.employee and leave.employee.direct_manager:
            approver_name = leave.employee.direct_manager.full_name_ar or leave.employee.direct_manager.user.username

        return {
            'step': 1,
            'role': 'direct_manager',
            'role_label': 'المدير المباشر',
            'approver_name': approver_name,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════
# الطلبات (إذن خروج / سلفة / إداري)
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_request_types(request):
    """أنواع الطلبات المتاحة"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    categories = RequestCategory._base_manager.filter(
        company=employee.company, is_active=True
    ).order_by('order', 'id')

    result = []
    for cat in categories:
        types = RequestType._base_manager.filter(
            company=employee.company, category=cat, is_active=True
        ).order_by('order', 'id')

        type_list = []
        for rt in types:
            type_list.append({
                'id': rt.id,
                'name': rt.name,
                'name_en': rt.name_en or '',
                'description': rt.description or '',
                'description_en': rt.description_en or '',
                'permission_kind': rt.permission_kind or 'none',
                'requires_date_range': rt.requires_date_range,
                'requires_amount': rt.requires_amount,
                'requires_document': rt.requires_document,
                'requires_approval': rt.requires_approval,
                'form_schema': rt.form_schema or {},
            })

        result.append({
            'id': cat.id,
            'name': cat.name,
            'name_en': cat.name_en or '',
            'icon': cat.icon,
            'color': cat.color,
            'types': type_list,
        })

    return Response({'success': True, 'categories': result})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_submit_request(request):
    """تقديم طلب (إذن / سلفة / إداري)"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    request_type_id = request.data.get('request_type_id')
    subject = (request.data.get("subject") or request.data.get("title", "")).strip()
    details = (request.data.get("details") or request.data.get("description", "")).strip()
    priority = request.data.get('priority', 'normal').strip()
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    amount = request.data.get('amount')
    permission_date = request.data.get('permission_date')
    permission_time_raw = request.data.get('permission_time')

    if not all([request_type_id, subject, details]):
        return Response({
            'success': False,
            'message': 'نوع الطلب والموضوع والتفاصيل مطلوبين'
        }, status=400)

    try:
        request_type = RequestType._base_manager.get(
            id=request_type_id, company=employee.company, is_active=True
        )
    except RequestType.DoesNotExist:
        return Response({'success': False, 'message': 'نوع الطلب غير موجود'}, status=404)

    is_permission_request = request_type.permission_kind in ['late_arrival', 'early_leave']

    # ── Dynamic Form Data ─────────────────────────────
    form_schema = request_type.form_schema or {}
    schema_fields = form_schema.get('fields', []) if isinstance(form_schema, dict) else []
    raw_form_data = request.data.get('form_data', {})
    if not isinstance(raw_form_data, dict):
        raw_form_data = {}

    dynamic_form_data = {}
    for field in schema_fields:
        if not isinstance(field, dict):
            continue

        key = (field.get('key') or '').strip()
        if not key:
            continue

        value = raw_form_data.get(key, request.data.get(key))
        required = bool(field.get('required', False))
        field_type = (field.get('type') or 'text').strip().lower()

        is_empty = value in [None, '']
        if isinstance(value, str):
            is_empty = value.strip() == ''

        if required and is_empty:
            label_ar = field.get('label_ar') or key
            label_en = field.get('label_en') or key
            language = getattr(employee, 'language', 'ar') or 'ar'
            message_ar = f'حقل "{label_ar}" مطلوب'
            message_en = f'Field "{label_en}" is required'
            return Response({
                'success': False,
                'message': message_en if language == 'en' else message_ar,
                'message_ar': message_ar,
                'message_en': message_en,
                'field': key,
            }, status=400)

        if not is_empty:
            if field_type == 'number':
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    label_ar = field.get('label_ar') or key
                    label_en = field.get('label_en') or key
                    language = getattr(employee, 'language', 'ar') or 'ar'
                    message_ar = f'قيمة "{label_ar}" غير صحيحة'
                    message_en = f'Invalid value for "{label_en}"'
                    return Response({
                        'success': False,
                        'message': message_en if language == 'en' else message_ar,
                        'message_ar': message_ar,
                        'message_en': message_en,
                        'field': key,
                    }, status=400)

        dynamic_form_data[key] = value

    if is_permission_request:
        permission_date = permission_date or start_date

        if not permission_date or not permission_time_raw:
            language = getattr(employee, 'language', 'ar') or 'ar'
            message_ar = 'تاريخ ووقت الإذن مطلوبان'
            message_en = 'Permission date and time are required'
            return Response({
                'success': False,
                'message': message_en if language == 'en' else message_ar,
                'message_ar': message_ar,
                'message_en': message_en,
            }, status=400)

        start_date = permission_date
        end_date = permission_date

    if request_type.requires_amount and not amount:
        return Response({
            'success': False,
            'message': 'المبلغ مطلوب لهذا النوع من الطلبات'
        }, status=400)

    if request_type.requires_date_range and (not start_date or not end_date):
        return Response({
            'success': False,
            'message': 'تاريخ البداية والنهاية مطلوبين لهذا النوع'
        }, status=400)

    # ── فحص سياسة الأذونات (لأنواع الأذون: تأخير / استئذان) ──
    permission_checked = False
    permission_hours = None
    permission_policy = None

    # لو فيه duration_hours في الطلب → معناه إنه إذن
    duration_hours_raw = request.data.get('duration_hours')
    if duration_hours_raw:
        try:
            permission_hours = float(duration_hours_raw)
        except (ValueError, TypeError):
            permission_hours = None

    if permission_hours and permission_hours > 0:
        # نجيب سياسة الأذونات الخاصة بالشركة
        from requests_app.models import PermissionPolicy, PermissionUsage
        try:
            permission_policy = PermissionPolicy._base_manager.get(
                company=employee.company,
                is_active=True
            )
        except PermissionPolicy.DoesNotExist:
            # مفيش سياسة → ممنوع تقديم إذن
            return Response({
                'success': False,
                'message': 'سياسة الأذونات غير مفعلة للشركة. رجاء التواصل مع المدير.'
            }, status=400)

        # نجيب استهلاك الموظف للشهر الحالي
        today = timezone.localdate()
        current_month = today.strftime('%Y-%m')
        usage, _created = PermissionUsage._base_manager.get_or_create(
            company=employee.company,
            employee=employee,
            month=current_month,
        )

        # فحص عدد المرات
        if usage.used_times >= permission_policy.max_times_per_month:
            return Response({
                'success': False,
                'message': f'وصلت للحد الأقصى من عدد مرات الأذونات ({permission_policy.max_times_per_month} مرات/شهر)'
            }, status=400)

        # فحص عدد الساعات (المستهلك + الجديد)
        from decimal import Decimal
        new_total = usage.used_hours + Decimal(str(permission_hours))
        if new_total > permission_policy.max_hours_per_month:
            remaining = permission_policy.max_hours_per_month - usage.used_hours
            return Response({
                'success': False,
                'message': f'الساعات المتبقية ({float(remaining)} ساعة) لا تكفي. الحد الأقصى {float(permission_policy.max_hours_per_month)} ساعة/شهر'
            }, status=400)

        permission_checked = True

    parsed_start = None
    parsed_end = None
    if start_date:
        from datetime import datetime
        try:
            parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_date:
        from datetime import datetime
        try:
            parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            pass

    parsed_permission_time = None
    if permission_time_raw:
        from datetime import datetime
        for time_format in ('%H:%M', '%H:%M:%S'):
            try:
                parsed_permission_time = datetime.strptime(permission_time_raw, time_format).time()
                break
            except ValueError:
                continue

        if parsed_permission_time is None:
            return Response({
                'success': False,
                'message': 'صيغة الوقت غير صحيحة',
                'message_ar': 'صيغة الوقت غير صحيحة',
                'message_en': 'Invalid time format'
            }, status=400)

    parsed_amount = None
    if amount:
        try:
            parsed_amount = float(amount)
        except ValueError:
            return Response({
                'success': False,
                'message': 'المبلغ غير صحيح'
            }, status=400)

    emp_request = EmployeeRequest._base_manager.create(
        company=employee.company,
        employee=employee,
        request_type=request_type,
        subject=subject,
        details=details,
        form_data=dynamic_form_data,
        priority=priority,
        start_date=parsed_start,
        end_date=parsed_end,
        amount=parsed_amount,
        duration_hours=Decimal(str(permission_hours)) if permission_hours else None,
        permission_time=parsed_permission_time,
        status='pending',
        step_1_status='pending',
    )

    # Permission usage is recorded at actual check-in/check-out after approval.

    # إشعار للمدير - طلب جديد
    try:
        request_type_name = request_type.name if request_type else 'طلب'
        employee_name = f"{employee.first_name_ar} {employee.last_name_ar}".strip() or employee.user.username
        notify_manager_new_request(
            company=employee.company,
            employee_name=employee_name,
            request_type=f"{request_type_name} - {subject}",
            request_id=emp_request.id,
        )
    except Exception as e:
        print(f"FCM notification error: {e}")

    return Response({
        'success': True,
        'message': 'تم تقديم الطلب بنجاح',
        'request_id': emp_request.id,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_requests(request):
    """عرض طلباتي"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    search = request.query_params.get('search', '').strip()
    status_filter = request.query_params.get('status', '').strip().lower()

    requests_list = EmployeeRequest._base_manager.filter(
        employee=employee
    ).select_related('request_type', 'request_type__category')

    if status_filter:
        requests_list = requests_list.filter(status=status_filter)

    if search:
        requests_list = requests_list.filter(
            Q(subject__icontains=search) |
            Q(details__icontains=search) |
            Q(request_type__name__icontains=search) |
            Q(request_type__category__name__icontains=search)
        )

    requests_list = requests_list.order_by('-created_at')[:30]

    items = []
    for req in requests_list:
        items.append({
            'id': req.id,
            'type_name': req.request_type.name if req.request_type else '',
            'category_name': req.request_type.category.name if req.request_type and req.request_type.category else '',
            'subject': req.subject or '',
            'details': req.details or '',
            'priority': req.priority or 'normal',
            'start_date': req.start_date.strftime('%Y-%m-%d') if req.start_date else '',
            'end_date': req.end_date.strftime('%Y-%m-%d') if req.end_date else '',
            'amount': float(req.amount) if req.amount else None,
            'status': req.status,
            'status_display': req.get_status_display(),
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '',
            'review_notes': req.review_notes or '',
            'current_approver': get_current_approver_info(req),
        })

    return Response({'success': True, 'items': items, 'requests': items})


# ═══════════════════════════════════════════════════
# APIs للمدير
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_pending(request):
    """الطلبات المعلقة اللي محتاجة موافقة المدير"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    company = getattr(user, 'company', None)

    pending_leaves = LeaveRequest._base_manager.filter(
        status='pending'
    ).select_related('employee', 'leave_type').order_by('-created_at')

    if company:
        pending_leaves = pending_leaves.filter(company=company)

    search = request.query_params.get('search', '').strip()
    if search:
        pending_leaves = pending_leaves.filter(
            Q(employee__first_name_ar__icontains=search) |
            Q(employee__last_name_ar__icontains=search) |
            Q(reason__icontains=search) |
            Q(leave_type__name__icontains=search)
        )

    leave_items = []
    for lr in pending_leaves[:50]:
        emp_name = ''
        if lr.employee:
            emp_name = f"{getattr(lr.employee, 'first_name_ar', '')} {getattr(lr.employee, 'last_name_ar', '')}".strip()
        leave_items.append({
            'id': lr.id,
            'type': 'leave',
            'employee_name': emp_name,
            'leave_type': lr.leave_type.name if lr.leave_type else '',
            'start_date': lr.start_date.strftime('%Y-%m-%d') if lr.start_date else '',
            'end_date': lr.end_date.strftime('%Y-%m-%d') if lr.end_date else '',
            'days_count': float(lr.days_count),
            'reason': lr.reason or '',
            'status': lr.status,
            'created_at': lr.created_at.strftime('%Y-%m-%d %H:%M') if lr.created_at else '',
        })

    pending_requests = EmployeeRequest._base_manager.filter(
        status='pending'
    ).select_related('employee', 'request_type', 'request_type__category').order_by('-created_at')

    if company:
        pending_requests = pending_requests.filter(company=company)

    request_items = []
    for req in pending_requests[:50]:
        emp_name = ''
        if req.employee:
            emp_name = f"{getattr(req.employee, 'first_name_ar', '')} {getattr(req.employee, 'last_name_ar', '')}".strip()
        request_items.append({
            'id': req.id,
            'type': 'request',
            'employee_name': emp_name,
            'type_name': req.request_type.name if req.request_type else '',
            'category_name': req.request_type.category.name if req.request_type and req.request_type.category else '',
            'subject': req.subject or '',
            'details': req.details or '',
            'amount': float(req.amount) if req.amount else None,
            'status': req.status,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M') if req.created_at else '',
        })

    return Response({
        'success': True,
        'pending_leaves': leave_items,
        'pending_requests': request_items,
        'total_pending': len(leave_items) + len(request_items),
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_action(request):
    """موافقة أو رفض طلب"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    item_type = request.data.get('type', '').strip()
    item_id = request.data.get('id')
    action = request.data.get('action', '').strip()
    notes = request.data.get('notes', '').strip()

    if not all([item_type, item_id, action]):
        return Response({
            'success': False,
            'message': 'النوع والمعرف والإجراء مطلوبين'
        }, status=400)

    if action not in ['approve', 'reject']:
        return Response({
            'success': False,
            'message': 'الإجراء لازم يكون approve أو reject'
        }, status=400)

    if action == 'reject' and not notes:
        return Response({
            'success': False,
            'message': 'سبب الرفض مطلوب'
        }, status=400)

    try:
        if item_type == 'leave':
            item = LeaveRequest._base_manager.get(id=item_id)

            employee_user = None
            try:
                employee_user = item.employee.user
            except Exception:
                pass

            leave_type_name = ''
            try:
                leave_type_name = item.leave_type.name if hasattr(item, 'leave_type') and item.leave_type else 'إجازة'
            except Exception:
                leave_type_name = 'إجازة'

            if action == 'approve':
                item.approve(user, notes)
                if employee_user:
                    try:
                        notify_leave_approved(
                            user=employee_user,
                            leave_type=leave_type_name,
                            start_date=str(item.start_date) if hasattr(item, 'start_date') else '',
                            end_date=str(item.end_date) if hasattr(item, 'end_date') else '',
                            leave_id=item.id,
                        )
                    except Exception as e:
                        print(f"FCM notification error: {e}")
            else:
                item.reject(user, notes)
                if employee_user:
                    try:
                        notify_leave_rejected(
                            user=employee_user,
                            leave_type=leave_type_name,
                            reason=notes,
                            leave_id=item.id,
                        )
                    except Exception as e:
                        print(f"FCM notification error: {e}")

            # إشعار داخل التطبيق
            try:
                from accounts.fcm_models import NotificationLog
                if employee_user:
                    if action == 'approve':
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='✅ تمت الموافقة على إجازتك',
                            body=f'تمت الموافقة على طلب {leave_type_name}',
                            notification_type='leave_approved',
                        )
                    else:
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='❌ تم رفض طلب إجازتك',
                            body=f'تم رفض طلب {leave_type_name}' + (f' - السبب: {notes}' if notes else ''),
                            notification_type='leave_rejected',
                        )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'تم {"الموافقة على" if action == "approve" else "رفض"} طلب الإجازة',
            })

        elif item_type == 'request':
            item = EmployeeRequest._base_manager.get(id=item_id)

            employee_user = None
            try:
                employee_user = item.employee.user
            except Exception:
                pass

            request_type_name = ''
            request_title = ''
            try:
                request_type_name = item.request_type.name if hasattr(item, 'request_type') and item.request_type else 'طلب'
                request_title = item.subject if hasattr(item, 'subject') else ''
            except Exception:
                request_type_name = 'طلب'

            if action == 'approve':
                item.status = 'approved'
                # لو طلب تعديل حضور → نطبق التعديل تلقائياً
                try:
                    _type_name = (item.request_type.name if item.request_type else '') or ''
                    if 'تعديل سجل حضور' in _type_name or 'Attendance Correction' in _type_name:
                        _form_data = item.form_data or {}
                        _att_date_str = _form_data.get('attendance_date') or (str(item.start_date) if item.start_date else None)
                        _correction_type = _form_data.get('correction_type', 'both')
                        _check_in_str = _form_data.get('correct_check_in')
                        _check_out_str = _form_data.get('correct_check_out')

                        if _att_date_str:
                            from datetime import datetime as _dt, date as _date_cls, time as _time_cls
                            from attendance.models import Attendance, AttendanceActionLog

                            try:
                                _att_date = _date_cls.fromisoformat(_att_date_str)
                                _att = Attendance._base_manager.filter(
                                    employee=item.employee,
                                    date=_att_date,
                                ).first()

                                if _att:
                                    _old_data = {
                                        'check_in_time': str(_att.check_in_time),
                                        'check_out_time': str(_att.check_out_time),
                                    }

                                    _tz_local = _tz.get_current_timezone()

                                    if _check_in_str and _correction_type in ('check_in', 'both', 'full_day'):
                                        try:
                                            _t = _dt.strptime(_check_in_str, '%H:%M').time()
                                            _att.check_in_time = _tz.make_aware(
                                                _dt.combine(_att_date, _t), _tz_local
                                            )
                                        except Exception:
                                            pass

                                    if _check_out_str and _correction_type in ('check_out', 'both', 'full_day'):
                                        try:
                                            _t = _dt.strptime(_check_out_str, '%H:%M').time()
                                            _att.check_out_time = _tz.make_aware(
                                                _dt.combine(_att_date, _t), _tz_local
                                            )
                                        except Exception:
                                            pass

                                    _att.is_manually_edited = True
                                    _att.admin_notes = f'[تعديل بموافقة HR] طلب #{item.id}'
                                    _att.calculate_work_hours()
                                    _att.save()

                                    AttendanceActionLog._base_manager.create(
                                        company=_att.company,
                                        attendance=_att,
                                        action_type='edit',
                                        performed_by=user,
                                        reason=f'تعديل بموافقة HR على طلب #{item.id}',
                                        old_data=_old_data,
                                        new_data={
                                            'check_in_time': str(_att.check_in_time),
                                            'check_out_time': str(_att.check_out_time),
                                        },
                                    )

                                    from attendance.models import DailyAttendanceSummary
                                    DailyAttendanceSummary.compute_for_day(item.employee, _att_date)

                            except Exception as _err:
                                import logging
                                logging.getLogger(__name__).warning(f'attendance correction error: {_err}')
                except Exception as _ce:
                    import logging
                    logging.getLogger(__name__).warning(f'correction hook error: {_ce}')
            else:
                item.status = 'rejected'
            item.reviewed_by = user
            item.reviewed_at = timezone.now()
            item.review_notes = notes
            item.save()

            # لو الطلب إذن تأخير أو انصراف مبكر → خصم من رصيد الأذونات
            if action == 'approve':
                try:
                    _kind = getattr(item.request_type, 'permission_kind', 'none')
                    if _kind in ('late_arrival', 'early_leave'):
                        from attendance.models import PermissionLedger
                        _form_data = item.form_data or {}
                        _duration_hours = float(_form_data.get('duration_hours', 0) or 0)
                        _minutes = int(_duration_hours * 60)
                        _ref_date = item.start_date or timezone.localdate()

                        if _minutes > 0:
                            _kind_label = 'إذن تأخير' if _kind == 'late_arrival' else 'إذن انصراف مبكر'
                            PermissionLedger._base_manager.create(
                                company=item.company,
                                employee=item.employee,
                                entry_type='manual_request',
                                minutes_used=_minutes,
                                count_used=1,
                                reference_date=_ref_date,
                                notes=f'{_kind_label} - طلب #{item.id} - {item.request_type.name}',
                            )
                except Exception as _le:
                    import logging
                    logging.getLogger(__name__).warning(f'PermissionLedger create error: {_le}')

            if employee_user:
                try:
                    if action == 'approve':
                        notify_request_approved(
                            user=employee_user,
                            request_type=request_type_name,
                            request_title=request_title,
                            request_id=item.id,
                        )
                    else:
                        notify_request_rejected(
                            user=employee_user,
                            request_type=request_type_name,
                            request_title=request_title,
                            reason=notes,
                            request_id=item.id,
                        )
                except Exception as e:
                    print(f"FCM notification error: {e}")

            # إشعار داخل التطبيق
            try:
                from accounts.fcm_models import NotificationLog
                if employee_user:
                    if action == 'approve':
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='✅ تمت الموافقة على طلبك',
                            body=f'تمت الموافقة على {request_type_name}: {request_title}',
                            notification_type='request_approved',
                        )
                    else:
                        NotificationLog.objects.create(
                            user=employee_user,
                            title='❌ تم رفض طلبك',
                            body=f'تم رفض {request_type_name}: {request_title}' + (f' - السبب: {notes}' if notes else ''),
                            notification_type='request_rejected',
                        )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'تم {"الموافقة على" if action == "approve" else "رفض"} الطلب',
            })
        else:
            return Response({
                'success': False,
                'message': 'النوع لازم يكون leave أو request'
            }, status=400)

    except (LeaveRequest.DoesNotExist, EmployeeRequest.DoesNotExist):
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': f'حصل خطأ: {str(e)}'}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_employees_attendance(request):
    """سجل حضور الموظفين للمدير"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    from attendance.models import Attendance

    company = getattr(user, 'company', None)
    date_str = request.query_params.get('date')

    if date_str:
        from datetime import datetime
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    records = Attendance._base_manager.filter(
        date=target_date
    ).select_related('employee').order_by('employee__first_name_ar')

    if company:
        records = records.filter(company=company)

    items = []
    for att in records:
        emp_name = ''
        if att.employee:
            emp_name = f"{getattr(att.employee, 'first_name_ar', '')} {getattr(att.employee, 'last_name_ar', '')}".strip()

        def fmt(dt):
            if not dt:
                return ''
            try:
                return timezone.localtime(dt).strftime('%I:%M %p')
            except Exception:
                return str(dt)

        items.append({
            'employee_name': emp_name,
            'employee_code': getattr(att.employee, 'employee_code', '') if att.employee else '',
            'date': att.date.strftime('%Y-%m-%d') if att.date else '',
            'check_in_time': fmt(getattr(att, 'check_in_time', None)),
            'check_out_time': fmt(getattr(att, 'check_out_time', None)),
            'status': getattr(att, 'status', '') or '',
        })

    return Response({
        'success': True,
        'date': target_date.strftime('%Y-%m-%d'),
        'items': items,
        'total': len(items),
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_live_locations(request):
    """مواقع الموظفين اللحظية للخريطة"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    from attendance.models import LocationLog
    from django.db.models import Max

    company = getattr(user, 'company', None)

    employees = Employee._base_manager.filter(status='active')
    if company:
        employees = employees.filter(company=company)

    # فلترة حسب الدور: manager يشوف فريقه فقط
    if role == 'manager':
        try:
            from employees.visibility import get_visible_employees_qs
            visible_ids = list(get_visible_employees_qs(user).values_list('id', flat=True))
            employees = employees.filter(id__in=visible_ids)
        except Exception:
            # fallback: فريق مباشر
            mgr_emp = Employee._base_manager.filter(user=user).first()
            if mgr_emp:
                employees = employees.filter(direct_manager=mgr_emp)
            else:
                employees = employees.none()

    from django.utils import timezone
    from attendance.models import Attendance
    today = timezone.localdate()

    attendance_employee_ids = set(
        Attendance._base_manager.filter(
            employee__in=employees,
            date=today,
        ).exclude(
            check_in_time__isnull=True
        ).values_list('employee_id', flat=True)
    )

    items = []
    for emp in employees:
        has_attendance = emp.id in attendance_employee_ids
        last_log = LocationLog._base_manager.filter(
            employee=emp
        ).order_by('-timestamp').first()

        emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip()
        dept_name = getattr(getattr(emp, 'department', None), 'name_ar', '') or ''

        if not has_attendance:
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'department': dept_name,
                'latitude': None,
                'longitude': None,
                'accuracy': 0,
                'address': '',
                'timestamp': '',
                'status': 'inactive_no_attendance',
                'has_location': False,
                'attendance_registered': False,
                'status_note': 'لم يتم تسجيل حضوره في شيفت اليوم',
            })
            continue

        if last_log:
            log_date = last_log.timestamp.date() if last_log.timestamp else None
            is_online = log_date == today
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'department': dept_name,
                'latitude': float(last_log.latitude),
                'longitude': float(last_log.longitude),
                'accuracy': float(last_log.accuracy) if last_log.accuracy else 0,
                'address': getattr(last_log, 'address', '') or '',
                'timestamp': last_log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_log.timestamp else '',
                'status': 'online' if is_online else 'offline',
                'has_location': True,
                'attendance_registered': True,
                'status_note': '' if is_online else 'آخر موقع مسجل ليس من اليوم',
            })
        else:
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'department': dept_name,
                'latitude': None,
                'longitude': None,
                'accuracy': 0,
                'address': '',
                'timestamp': '',
                'status': 'no_data',
                'has_location': False,
                'attendance_registered': True,
                'status_note': 'تم تسجيل الحضور ولكن لا يوجد موقع مباشر بعد',
            })

    return Response({
        'success': True,
        'items': items,
        'total': len(items),
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_manager_employee_route(request):
    """خط سير موظف معين في يوم معين"""
    user = request.user
    role = getattr(user, 'role', 'employee')

    if role not in ['super_admin', 'company_admin', 'hr_manager', 'manager']:
        return Response({'success': False, 'message': 'ليس لديك صلاحية'}, status=403)

    employee_id = request.query_params.get('employee_id')
    if not employee_id:
        return Response({'success': False, 'message': 'employee_id مطلوب'}, status=400)

    try:
        employee_id = int(employee_id)
    except Exception:
        return Response({'success': False, 'message': 'employee_id غير صحيح'}, status=400)

    company = getattr(user, 'company', None)

    from datetime import datetime
    target_date_str = request.query_params.get('date', '').strip()
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'success': False, 'message': 'صيغة التاريخ لازم تكون YYYY-MM-DD'}, status=400)
    else:
        target_date = timezone.localdate()

    emp_qs = Employee._base_manager.filter(id=employee_id)
    if company:
        emp_qs = emp_qs.filter(company=company)

    employee = emp_qs.first()
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    from attendance.models import LocationLog

    logs = LocationLog._base_manager.filter(
        employee=employee,
        timestamp__date=target_date
    ).order_by('timestamp')[:500]

    emp_name = f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
    if not emp_name:
        emp_name = employee.employee_code or f"Employee #{employee.id}"

    points = []
    for log in logs:
        points.append({
            'latitude': float(log.latitude),
            'longitude': float(log.longitude),
            'accuracy': float(log.accuracy) if log.accuracy else 0,
            'address': getattr(log, 'address', '') or '',
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
        })

    return Response({
        'success': True,
        'employee': {
            'id': employee.id,
            'name': emp_name,
            'employee_code': employee.employee_code or '',
        },
        'date': target_date.strftime('%Y-%m-%d'),
        'points': points,
        'total_points': len(points),
    })


# ─────────────────────────────────────────────────────────────
# تعديل طلب قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_edit_request(request, request_id):
    """الموظف يعدّل طلبه لو لسه pending"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id, employee=employee)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status != 'pending':
        return Response({
            'success': False,
            'message': f'لا يمكن تعديل الطلب — حالته الحالية: {req.get_status_display()}'
        }, status=400)

    d = request.data
    if 'subject' in d:
        req.subject = d['subject']
    if 'details' in d:
        req.details = d['details']
    if 'priority' in d:
        req.priority = d['priority']
    if 'start_date' in d:
        req.start_date = d['start_date'] or None
    if 'end_date' in d:
        req.end_date = d['end_date'] or None
    if 'amount' in d:
        req.amount = d['amount'] or None
    if 'duration_hours' in d:
        req.duration_hours = d['duration_hours'] or None
    req.save()

    return Response({
        'success': True,
        'message': 'تم تعديل الطلب بنجاح',
        'request_id': req.id,
        'status': req.status,
    })


# ─────────────────────────────────────────────────────────────
# إلغاء طلب قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_cancel_request(request, request_id):
    """الموظف يلغي طلبه لو لسه pending أو manager_approved"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id, employee=employee)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    # فحص إمكانية الإلغاء
    if req.status in ('cancelled', 'rejected'):
        return Response({
            'success': False,
            'message': f'لا يمكن إلغاء الطلب — حالته: {req.get_status_display()}'
        }, status=400)

    # لو الطلب معتمد، لازم يكون قبل تاريخ التنفيذ
    if req.status in ('approved', 'hr_approved'):
        _ref_date = req.start_date or timezone.localdate()
        _today = timezone.localdate()
        if _ref_date <= _today:
            return Response({
                'success': False,
                'message': 'لا يمكن إلغاء الإذن بعد تاريخ تنفيذه'
            }, status=400)

    reason = request.data.get('reason', 'إلغاء بواسطة الموظف')
    _was_approved = req.status in ('approved', 'hr_approved')
    req.status = 'cancelled'
    req.review_notes = f'[إلغاء الموظف] {reason}'
    req.save()

    # لو كان معتمد وإذن (تأخير/انصراف مبكر) → نرجع الرصيد
    if _was_approved:
        try:
            _kind = getattr(req.request_type, 'permission_kind', 'none')
            if _kind in ('late_arrival', 'early_leave'):
                from attendance.models import PermissionLedger
                _form_data = req.form_data or {}
                _duration_hours = float(_form_data.get('duration_hours', 0) or 0)
                _minutes = int(_duration_hours * 60)
                _ref_date = req.start_date or timezone.localdate()

                if _minutes > 0:
                    PermissionLedger._base_manager.create(
                        company=req.company,
                        employee=req.employee,
                        entry_type='rollback',
                        minutes_used=-_minutes,
                        count_used=-1,
                        reference_date=_ref_date,
                        notes=f'إلغاء إذن - طلب #{req.id} - {req.request_type.name}',
                    )
        except Exception as _le:
            import logging
            logging.getLogger(__name__).warning(f'PermissionLedger rollback error: {_le}')

    return Response({
        'success': True,
        'message': 'تم إلغاء الطلب بنجاح',
        'request_id': req.id,
    })


# ─────────────────────────────────────────────────────────────
# تعديل إجازة قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_edit_leave(request, leave_id):
    """الموظف يعدّل طلب إجازته لو لسه pending"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id, employee=employee)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status != 'pending':
        return Response({
            'success': False,
            'message': f'لا يمكن تعديل الإجازة — حالتها: {leave.get_status_display()}'
        }, status=400)

    d = request.data
    if 'start_date' in d:
        leave.start_date = d['start_date']
    if 'end_date' in d:
        leave.end_date = d['end_date']
    if 'reason' in d:
        leave.reason = d['reason']
    leave.save()

    return Response({
        'success': True,
        'message': 'تم تعديل طلب الإجازة بنجاح',
        'leave_id': leave.id,
    })


# ─────────────────────────────────────────────────────────────
# إلغاء إجازة قبل الموافقة
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def mobile_cancel_leave(request, leave_id):
    """الموظف يلغي طلب إجازته لو لسه pending"""
    try:
        employee = Employee._base_manager.get(user=request.user)
    except Exception:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id, employee=employee)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status in ('approved', 'cancelled', 'rejected'):
        return Response({
            'success': False,
            'message': f'لا يمكن إلغاء الإجازة — حالتها: {leave.get_status_display()}'
        }, status=400)

    leave.status = 'cancelled'
    leave.save()

    return Response({
        'success': True,
        'message': 'تم إلغاء طلب الإجازة بنجاح',
        'leave_id': leave.id,
    })



# ─────────────────────────────────────────────────────────────
# المدير/HR: تعديل أي طلب
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_edit_request(request, request_id):
    """المدير أو HR يعدّل أي طلب في أي مرحلة"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status in ('cancelled',):
        return Response({
            'success': False,
            'message': 'لا يمكن تعديل طلب ملغي'
        }, status=400)

    d = request.data
    if 'subject' in d:
        req.subject = d['subject']
    if 'details' in d:
        req.details = d['details']
    if 'priority' in d:
        req.priority = d['priority']
    if 'start_date' in d:
        req.start_date = d['start_date'] or None
    if 'end_date' in d:
        req.end_date = d['end_date'] or None
    if 'amount' in d:
        req.amount = d['amount'] or None
    if 'duration_hours' in d:
        req.duration_hours = d['duration_hours'] or None
    if 'status' in d and role in ('company_admin', 'hr_manager', 'super_admin'):
        req.status = d['status']
    if 'review_notes' in d:
        req.review_notes = d['review_notes']
    req.save()

    return Response({
        'success': True,
        'message': 'تم تعديل الطلب بنجاح',
        'request_id': req.id,
        'status': req.status,
        'status_display': req.get_status_display(),
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: إلغاء أي طلب
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_cancel_request(request, request_id):
    """المدير أو HR يلغي أي طلب"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status == 'cancelled':
        return Response({'success': False, 'message': 'الطلب ملغي مسبقاً'}, status=400)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'success': False, 'message': 'سبب الإلغاء مطلوب'}, status=400)

    req.status = 'cancelled'
    req.review_notes = f'[إلغاء المدير/HR] {reason}'
    req.save()

    return Response({
        'success': True,
        'message': 'تم إلغاء الطلب بنجاح',
        'request_id': req.id,
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: إعادة فتح طلب مرفوض
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_reopen_request(request, request_id):
    """HR يعيد فتح طلب مرفوض أو ملغي"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح - HR فقط'}, status=403)

    try:
        req = EmployeeRequest._base_manager.get(id=request_id)
    except EmployeeRequest.DoesNotExist:
        return Response({'success': False, 'message': 'الطلب غير موجود'}, status=404)

    if req.status not in ('rejected', 'cancelled'):
        return Response({
            'success': False,
            'message': f'يمكن إعادة الفتح فقط للطلبات المرفوضة أو الملغية — الحالة الحالية: {req.get_status_display()}'
        }, status=400)

    notes = request.data.get('notes', '')
    req.status = 'pending'
    req.current_step = 1
    req.step_1_status = 'pending'
    req.review_notes = f'[إعادة فتح] {notes}'
    req.reviewed_by = None
    req.reviewed_at = None
    req.save()

    return Response({
        'success': True,
        'message': 'تمت إعادة فتح الطلب بنجاح — في انتظار الموافقة من جديد',
        'request_id': req.id,
        'status': req.status,
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: تعديل إجازة
# ─────────────────────────────────────────────────────────────
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_edit_leave(request, leave_id):
    """المدير أو HR يعدّل طلب إجازة"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status == 'cancelled':
        return Response({'success': False, 'message': 'لا يمكن تعديل إجازة ملغية'}, status=400)

    d = request.data
    if 'start_date' in d:
        leave.start_date = d['start_date']
    if 'end_date' in d:
        leave.end_date = d['end_date']
    if 'reason' in d:
        leave.reason = d['reason']
    if 'status' in d and role in ('company_admin', 'hr_manager', 'super_admin'):
        leave.status = d['status']
    leave.save()

    return Response({
        'success': True,
        'message': 'تم تعديل طلب الإجازة بنجاح',
        'leave_id': leave.id,
        'status': leave.status,
    })


# ─────────────────────────────────────────────────────────────
# المدير/HR: إلغاء إجازة
# ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_cancel_leave(request, leave_id):
    """المدير أو HR يلغي طلب إجازة"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        leave = LeaveRequest._base_manager.get(id=leave_id)
    except Exception:
        return Response({'success': False, 'message': 'طلب الإجازة غير موجود'}, status=404)

    if leave.status == 'cancelled':
        return Response({'success': False, 'message': 'الإجازة ملغية مسبقاً'}, status=400)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'success': False, 'message': 'سبب الإلغاء مطلوب'}, status=400)

    # cancel() بترجع الرصيد تلقائيًا
    leave.cancel()
    if hasattr(leave, 'cancel_reason'):
        leave.cancel_reason = reason
        leave.save(update_fields=['cancel_reason'])

    return Response({
        'success': True,
        'message': 'تم إلغاء طلب الإجازة وإرجاع الرصيد بنجاح',
        'leave_id': leave.id,
    })



# ══════════════════════════════════════════════════════
# LEAVE RECALL APIs
# ══════════════════════════════════════════════════════

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_leave_recall(request):
    """المدير أو صاحب الشركة يطلب استدعاء موظف من إجازته"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    d = request.data
    employee_id = d.get('employee_id')
    recall_date_raw = d.get('recall_date')
    reason = d.get('reason', '').strip()

    if not all([employee_id, recall_date_raw, reason]):
        return Response({'success': False, 'message': 'employee_id و recall_date و reason مطلوبين'}, status=400)

    try:
        from datetime import datetime as dt
        recall_date = dt.strptime(str(recall_date_raw), '%Y-%m-%d').date()
    except ValueError:
        return Response({'success': False, 'message': 'صيغة التاريخ لازم تكون YYYY-MM-DD'}, status=400)

    try:

        company = getattr(request.user, 'company', None)
        employee = Employee._base_manager.get(id=employee_id, company=company)

        leave_request = LeaveRequest._base_manager.filter(
            employee=employee,
            status='approved',
            start_date__lte=recall_date,
            end_date__gte=recall_date,
        ).first()

        if not leave_request:
            return Response({'success': False, 'message': 'الموظف مش في إجازة معتمدة في هذا اليوم'}, status=400)

        if LeaveRecallRequest._base_manager.filter(
            employee=employee,
            recall_date=recall_date,
        ).exists():
            return Response({'success': False, 'message': 'يوجد طلب استدعاء بالفعل لهذا اليوم'}, status=400)

        recall = LeaveRecallRequest._base_manager.create(
            company=company,
            employee=employee,
            leave_request=leave_request,
            recall_date=recall_date,
            reason=reason,
            requested_by=request.user,
            status='pending',
            created_by=request.user,
        )

        # إشعار HR
        try:
            from accounts.fcm_service import send_push_to_role
            emp_name = getattr(employee, 'full_name_ar', str(employee))
            send_push_to_role(
                company=company,
                role='hr_manager',
                title='🔔 طلب استدعاء من إجازة',
                body=f'تم طلب استدعاء {emp_name} من إجازته يوم {recall_date}',
                data={'type': 'leave_recall', 'recall_id': str(recall.id)},
            )
            recall.hr_notified = True
            recall.save(update_fields=['hr_notified'])
        except Exception:
            pass

        # لو صاحب الشركة هو اللي طلب → يعتمد مباشرة
        if role in ('company_admin', 'super_admin'):
            recall.approve(request.user, notes='اعتماد تلقائي من صاحب الشركة')

        return Response({
            'success': True,
            'recall_id': recall.id,
            'status': recall.status,
            'message': 'تم إنشاء طلب الاستدعاء' if recall.status == 'pending' else 'تم الاستدعاء والاعتماد مباشرة ✅',
        }, status=201)

    except Employee.DoesNotExist:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def review_leave_recall(request, recall_id):
    """HR أو صاحب الشركة يوافق أو يرفض طلب الاستدعاء"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح - للـ HR وصاحب الشركة فقط'}, status=403)

    action = request.data.get('action', '').strip().lower()
    notes = request.data.get('notes', '').strip()

    if action not in ('approve', 'reject'):
        return Response({'success': False, 'message': 'action لازم يكون approve أو reject'}, status=400)

    try:
        from leaves.models import LeaveRecallRequest
        company = getattr(request.user, 'company', None)
        recall = LeaveRecallRequest._base_manager.get(id=recall_id, company=company)

        if recall.status != 'pending':
            return Response({'success': False, 'message': f'الطلب حالته {recall.get_status_display()} مش pending'}, status=400)

        if action == 'approve':
            recall.approve(request.user, notes=notes)
            msg = f'تم الموافقة على استدعاء {recall.employee} يوم {recall.recall_date} ✅'
        else:
            recall.reject(request.user, notes=notes)
            msg = f'تم رفض طلب استدعاء {recall.employee} يوم {recall.recall_date}'

        # إشعار المدير اللي طلب
        try:
            from accounts.fcm_service import send_push_to_user
            if recall.requested_by:
                send_push_to_user(
                    user=recall.requested_by,
                    title='✅ استدعاء من إجازة' if action == 'approve' else '❌ رفض استدعاء',
                    body=msg,
                    data={'type': 'leave_recall_reviewed', 'recall_id': str(recall.id)},
                )
        except Exception:
            pass

        return Response({'success': True, 'message': msg, 'status': recall.status})

    except LeaveRecallRequest.DoesNotExist:
        return Response({'success': False, 'message': 'طلب الاستدعاء غير موجود'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_leave_recalls(request):
    """قائمة طلبات الاستدعاء"""
    role = getattr(request.user, 'role', None)
    if role not in ('company_admin', 'hr_manager', 'manager', 'super_admin') and not request.user.is_superuser:
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)

    try:
        from leaves.models import LeaveRecallRequest
        company = getattr(request.user, 'company', None)
        status_filter = request.GET.get('status')

        qs = LeaveRecallRequest._base_manager.filter(
            company=company,
        ).select_related('employee', 'leave_request', 'requested_by', 'reviewed_by').order_by('-recall_date')

        if status_filter:
            qs = qs.filter(status=status_filter)

        data = []
        for r in qs[:100]:
            data.append({
                'id': r.id,
                'employee_id': r.employee_id,
                'employee_name': getattr(r.employee, 'full_name_ar', str(r.employee)),
                'recall_date': str(r.recall_date),
                'reason': r.reason,
                'status': r.status,
                'status_display': r.get_status_display(),
                'requested_by': r.requested_by.get_full_name() if r.requested_by else '',
                'reviewed_by': r.reviewed_by.get_full_name() if r.reviewed_by else '',
                'reviewed_at': str(r.reviewed_at) if r.reviewed_at else None,
                'review_notes': r.review_notes,
                'balance_restored': r.balance_restored,
                'hr_notified': r.hr_notified,
            })

        return Response({'success': True, 'recalls': data, 'count': len(data)})

    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def hr_create_leave(request):
    """إضافة إجازة من HR/company_admin لأي موظف"""
    from datetime import datetime
    from employees.models import Employee

    role = getattr(request.user, "role", "")
    if role not in ("company_admin", "hr_manager", "super_admin") and not request.user.is_superuser:
        return Response({"success": False, "error": "غير مصرح"}, status=403)

    company = getattr(request.user, "company", None)
    if not company:
        emp = Employee._base_manager.filter(user=request.user).first()
        if emp:
            company = emp.company
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    employee_id = request.data.get("employee_id")
    leave_type_id = request.data.get("leave_type_id")
    start_date_str = request.data.get("start_date")
    end_date_str = request.data.get("end_date")
    reason = (request.data.get("reason") or "").strip()
    status_val = request.data.get("status", "approved")
    half_day = request.data.get("half_day", False)

    if not all([employee_id, leave_type_id, start_date_str, end_date_str, reason]):
        return Response({"success": False, "error": "الموظف ونوع الإجازة والتواريخ والسبب مطلوبة"}, status=400)

    try:
        employee = Employee._base_manager.get(id=employee_id, company=company)
    except Employee.DoesNotExist:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    try:
        leave_type = LeaveType._base_manager.get(id=leave_type_id, company=company, is_active=True)
    except LeaveType.DoesNotExist:
        return Response({"success": False, "error": "نوع الإجازة غير موجود"}, status=404)

    emp_gender = (getattr(employee, "gender", "") or "").lower()
    lt_restriction = getattr(leave_type, "gender_restriction", "all")
    if lt_restriction == "female" and emp_gender != "female":
        return Response({"success": False, "error": "هذه الإجازة للإناث فقط"}, status=400)
    if lt_restriction == "male" and emp_gender != "male":
        return Response({"success": False, "error": "هذه الإجازة للذكور فقط"}, status=400)

    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"success": False, "error": "صيغة التاريخ غير صحيحة"}, status=400)

    if end < start:
        return Response({"success": False, "error": "تاريخ النهاية قبل البداية"}, status=400)

    days_count = 0.5 if (half_day and start_date_str == end_date_str) else (end - start).days + 1

    if leave_type.is_paid:
        balance = LeaveBalance._base_manager.filter(
            company=company, employee=employee, leave_type=leave_type, year=start.year
        ).first()
        remaining = float(balance.remaining_days) if balance else 0
        if days_count > remaining:
            return Response({"success": False, "error": f"الرصيد غير كافي. المتاح: {remaining} يوم"}, status=400)

    if status_val not in ("pending", "approved"):
        status_val = "approved"

    leave_request = LeaveRequest._base_manager.create(
        company=company,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        days_count=days_count,
        reason=reason,
        status=status_val,
    )

    if status_val == "approved":
        balance = LeaveBalance._base_manager.filter(
            company=company, employee=employee, leave_type=leave_type, year=start.year
        ).first()
        if balance:
            balance.used_days = float(balance.used_days or 0) + days_count
            balance.save(update_fields=["used_days"])

    return Response({
        "success": True,
        "message": f"تم إضافة الإجازة ({days_count} يوم)",
        "request_id": leave_request.id,
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def hr_leave_types(request):
    """أنواع الإجازات للـ HR/company_admin — بدون حاجة لـ employee profile"""
    try:
        company = getattr(request.user, "company", None)
        if not company:
            from employees.models import Employee
            emp = Employee._base_manager.filter(user=request.user).first()
            if emp:
                company = emp.company

        if not company:
            return Response({"success": False, "message": "لا توجد شركة مرتبطة"}, status=400)

        year = timezone.localdate().year
        leave_types = LeaveType._base_manager.filter(
            company=company, is_active=True
        ).order_by("name")

        result = []
        for lt in leave_types:
            result.append({
                "id": lt.id,
                "name": lt.name,
                "name_en": getattr(lt, "name_en", "") or "",
                "category": lt.category,
                "days_allowed": lt.days_allowed,
                "is_paid": lt.is_paid,
                "requires_document": lt.requires_document,
                "color": lt.color,
            })

        return Response({"success": True, "leave_types": result, "count": len(result)})

    except Exception as e:
        logger.exception("hr_leave_types error")
        return Response({"success": False, "error": str(e)}, status=500)
