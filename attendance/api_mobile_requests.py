"""
APIs للطلبات والإجازات من تطبيق الموبايل
"""
from django.utils import timezone
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

from employees.models import Employee
from leaves.models import LeaveType, LeaveBalance, LeaveRequest
from requests_app.models import RequestCategory, RequestType, EmployeeRequest


def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).select_related('company').first()


# ═══════════════════════════════════════════════════
# الإجازات
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_leave_types(request):
    """أنواع الإجازات المتاحة مع الرصيد"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    year = timezone.localdate().year
    leave_types = LeaveType._base_manager.filter(
        company=employee.company, is_active=True
    ).order_by('name')

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
@authentication_classes([TokenAuthentication])
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

    days_count = (end - start).days + 1

    leave_request = LeaveRequest._base_manager.create(
        company=employee.company,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        days_count=days_count,
        reason=reason,
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_leaves(request):
    """عرض طلبات الإجازات الخاصة بي"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    leaves = LeaveRequest._base_manager.filter(
        employee=employee
    ).select_related('leave_type').order_by('-created_at')[:30]

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
        })

    return Response({'success': True, 'items': items})


# ═══════════════════════════════════════════════════
# الطلبات (إذن خروج / سلفة / إداري)
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_request_types(request):
    """أنواع الطلبات المتاحة"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    categories = RequestCategory._base_manager.filter(
        company=employee.company, is_active=True
    ).order_by('order')

    result = []
    for cat in categories:
        types = RequestType._base_manager.filter(
            company=employee.company, category=cat, is_active=True
        ).order_by('order')

        type_list = []
        for rt in types:
            type_list.append({
                'id': rt.id,
                'name': rt.name,
                'description': rt.description or '',
                'requires_date_range': rt.requires_date_range,
                'requires_amount': rt.requires_amount,
                'requires_document': rt.requires_document,
            })

        result.append({
            'id': cat.id,
            'name': cat.name,
            'icon': cat.icon,
            'color': cat.color,
            'types': type_list,
        })

    return Response({'success': True, 'categories': result})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_requests(request):
    """عرض طلباتي"""
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)

    requests_list = EmployeeRequest._base_manager.filter(
        employee=employee
    ).select_related('request_type', 'request_type__category').order_by('-created_at')[:30]

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
        })

    return Response({'success': True, 'items': items})


# ═══════════════════════════════════════════════════
# APIs للمدير
# ═══════════════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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
            else:
                item.status = 'rejected'
            item.reviewed_by = user
            item.reviewed_at = timezone.now()
            item.review_notes = notes
            item.save()

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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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

    employees = Employee._base_manager.filter(is_field_worker=True)
    if company:
        employees = employees.filter(company=company)

    items = []
    for emp in employees:
        last_log = LocationLog._base_manager.filter(
            employee=emp
        ).order_by('-timestamp').first()

        if last_log:
            emp_name = f"{getattr(emp, 'first_name_ar', '')} {getattr(emp, 'last_name_ar', '')}".strip()
            items.append({
                'employee_id': emp.id,
                'employee_name': emp_name,
                'employee_code': emp.employee_code or '',
                'latitude': float(last_log.latitude),
                'longitude': float(last_log.longitude),
                'accuracy': float(last_log.accuracy) if last_log.accuracy else 0,
                'address': getattr(last_log, 'address', '') or '',
                'timestamp': last_log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_log.timestamp else '',
            })

    return Response({
        'success': True,
        'items': items,
        'total': len(items),
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
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
