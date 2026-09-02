"""
APIs - الإدخالات اليدوية (جزاءات / مكافآت / بدلات)
Workflow: طلب → موافقة CEO → إبلاغ HR → تطبيق في المرتب
"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import json
from datetime import date

from .company_policy_models import ManualPenalty, ManualBonus, ManualAllowance
from employees.models import Employee
from accounts.fcm_service import (
    notify_manual_entry_approved,
    notify_manual_entry_rejected,
    notify_hr_manual_entry_approved,
)


# ═══════════════════════════════════════════════════════════════
# Permissions
# ═══════════════════════════════════════════════════════════════
def _is_ceo(user):
    """Company Admin = CEO"""
    role = getattr(user, 'role', None)
    return user.is_superuser or role == 'company_admin'


def _is_hr(user):
    role = getattr(user, 'role', None)
    return user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager']


def _is_manager(user):
    """المدير المباشر أو أعلى"""
    role = getattr(user, 'role', None)
    return user.is_superuser or user.is_staff or role in ['company_admin', 'hr_manager', 'manager']


def _get_user_employee(user):
    """يجيب Employee record للـ user"""
    try:
        return Employee._base_manager.filter(user_id=user.id).first()
    except Exception:
        return None


def _can_manage_employee(user, employee):
    """
    يتحقق إن الـ user يقدر يطلب لـ employee ده:
    - CEO / HR: أي موظف
    - Manager: فقط الموظفين اللي direct_manager بتاعهم
    """
    if _is_ceo(user) or _is_hr(user):
        return True

    manager_emp = _get_user_employee(user)
    if not manager_emp:
        return False

    return getattr(employee, 'direct_manager_id', None) == manager_emp.id


# ═══════════════════════════════════════════════════════════════
# Serializer
# ═══════════════════════════════════════════════════════════════
def _entry_to_dict(entry):
    return {
        'id': entry.id,
        'entry_type': entry.__class__.__name__.replace('Manual', '').lower(),
        'category': entry.category,
        'category_display': entry.get_category_display(),

        # Employee
        'employee_id': entry.employee_id,
        'employee_name': f'{entry.employee.first_name_ar or ""} {entry.employee.last_name_ar or ""}'.strip() or entry.employee.employee_code,
        'employee_code': entry.employee.employee_code,

        # Amount
        'amount_type': entry.amount_type,
        'amount_type_display': entry.get_amount_type_display(),
        'amount_value': float(entry.amount_value),

        # Reason
        'reason': entry.reason,
        'attachment_url': entry.attachment.url if entry.attachment else None,

        # Target
        'target_year': entry.target_year,
        'target_month': entry.target_month,

        # Workflow
        'status': entry.status,
        'status_display': entry.get_status_display(),

        # Requester
        'requested_by_id': entry.requested_by_id,
        'requested_by_name': f'{entry.requested_by.first_name} {entry.requested_by.last_name}'.strip() if entry.requested_by else '',
        'requested_at': str(entry.requested_at),

        # Approval
        'approved_by_id': entry.approved_by_id,
        'approved_by_name': f'{entry.approved_by.first_name} {entry.approved_by.last_name}'.strip() if entry.approved_by else '',
        'approved_at': str(entry.approved_at) if entry.approved_at else None,
        'approval_notes': entry.approval_notes or '',

        # Rejection
        'rejected_by_id': entry.rejected_by_id,
        'rejected_by_name': f'{entry.rejected_by.first_name} {entry.rejected_by.last_name}'.strip() if entry.rejected_by else '',
        'rejected_at': str(entry.rejected_at) if entry.rejected_at else None,
        'rejection_reason': entry.rejection_reason or '',

        # HR
        'hr_notified': entry.hr_notified,
        'hr_notified_at': str(entry.hr_notified_at) if entry.hr_notified_at else None,

        # Application
        'applied_in_payroll': entry.applied_in_payroll,
        'applied_at': str(entry.applied_at) if entry.applied_at else None,

        'created_at': str(entry.created_at),
        'updated_at': str(entry.updated_at),
    }


# ═══════════════════════════════════════════════════════════════
# Generic Handlers
# ═══════════════════════════════════════════════════════════════
def _handle_list_create(request, ModelClass):
    company = request.user.company

    if request.method == 'GET':
        try:
            qs = ModelClass._base_manager.filter(company=company).select_related(
                'employee', 'requested_by', 'approved_by', 'rejected_by'
            )

            # فلترات
            status_filter = request.GET.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)

            year = request.GET.get('year')
            month = request.GET.get('month')
            if year:
                qs = qs.filter(target_year=int(year))
            if month:
                qs = qs.filter(target_month=int(month))

            employee_id = request.GET.get('employee_id')
            if employee_id:
                qs = qs.filter(employee_id=int(employee_id))

            # الصلاحيات: المدير يشوف فقط فريقه، HR/CEO يشوفوا الكل
            role = getattr(request.user, 'role', None)
            if role == 'manager' and not _is_ceo(request.user) and not _is_hr(request.user):
                manager_emp = _get_user_employee(request.user)
                if manager_emp:
                    qs = qs.filter(employee__direct_manager_id=manager_emp.id)
                else:
                    qs = qs.none()

            qs = qs.order_by('-created_at')
            return JsonResponse({
                'success': True,
                'count': qs.count(),
                'results': [_entry_to_dict(e) for e in qs],
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # POST — إنشاء
    try:
        if not _is_manager(request.user):
            return JsonResponse({'success': False, 'error': 'غير مسموح - فقط المدراء'}, status=403)

        data = json.loads(request.body.decode('utf-8'))

        employee_id = data.get('employee_id')
        if not employee_id:
            return JsonResponse({'success': False, 'error': 'employee_id مطلوب'}, status=400)

        employee = Employee._base_manager.filter(id=employee_id, company=company).first()
        if not employee:
            return JsonResponse({'success': False, 'error': 'الموظف غير موجود'}, status=404)

        # التحقق من صلاحية المدير
        if not _can_manage_employee(request.user, employee):
            return JsonResponse({
                'success': False,
                'error': 'مش مصرح لك تطلب للموظف ده (مش تابع لفريقك)',
            }, status=403)

        # لو صاحب الشركة نفسه هو اللي بيضيف، يتعتمد فوراً من غير موافقة إضافية
        _auto_approve = _is_ceo(request.user)
        entry = ModelClass._base_manager.create(
            company=company,
            employee=employee,
            requested_by=request.user,
            category=data.get('category', 'other'),
            amount_type=data.get('amount_type', 'fixed'),
            amount_value=data.get('amount_value', 0),
            reason=data.get('reason', ''),
            target_year=int(data.get('target_year', date.today().year)),
            target_month=int(data.get('target_month', date.today().month)),
            status='approved' if _auto_approve else 'pending',
        )
        if _auto_approve:
            entry.approved_by = request.user
            entry.approved_at = timezone.now()
            entry.save()

        return JsonResponse({
            'success': True,
            'message': 'تم الاعتماد فوراً' if _auto_approve else 'تم تقديم الطلب، بانتظار موافقة الإدارة',
            'entry': _entry_to_dict(entry),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _handle_detail_and_actions(request, entry_id, ModelClass):
    company = request.user.company

    entry = ModelClass._base_manager.filter(id=entry_id, company=company).first()
    if not entry:
        return JsonResponse({'success': False, 'error': 'not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'entry': _entry_to_dict(entry)})

    if request.method == 'DELETE':
        # فقط الطالب أو CEO يقدر يحذف (وفقط لو pending)
        if entry.status != 'pending':
            return JsonResponse({'success': False, 'error': 'لا يمكن حذف طلب معتمد أو مطبق'}, status=400)
        if request.user.id != entry.requested_by_id and not _is_ceo(request.user):
            return JsonResponse({'success': False, 'error': 'غير مسموح'}, status=403)
        entry.delete()
        return JsonResponse({'success': True, 'message': 'تم الحذف'})

    # PUT / PATCH — تعديل (فقط لو pending والطالب نفسه)
    data = json.loads(request.body.decode('utf-8'))

    if entry.status != 'pending':
        return JsonResponse({'success': False, 'error': 'لا يمكن تعديل طلب معتمد'}, status=400)

    if request.user.id != entry.requested_by_id and not _is_ceo(request.user):
        return JsonResponse({'success': False, 'error': 'غير مسموح'}, status=403)

    if 'category' in data: entry.category = data['category']
    if 'amount_type' in data: entry.amount_type = data['amount_type']
    if 'amount_value' in data: entry.amount_value = data['amount_value']
    if 'reason' in data: entry.reason = data['reason']
    if 'target_year' in data: entry.target_year = int(data['target_year'])
    if 'target_month' in data: entry.target_month = int(data['target_month'])
    entry.save()

    return JsonResponse({
        'success': True,
        'message': 'تم التحديث',
        'entry': _entry_to_dict(entry),
    })


# ═══════════════════════════════════════════════════════════════
# Approval Actions
# ═══════════════════════════════════════════════════════════════
def _handle_approve(request, entry_id, ModelClass):
    """CEO يوافق على الطلب"""
    company = request.user.company

    if not _is_ceo(request.user):
        return JsonResponse({'success': False, 'error': 'فقط مدير الشركة يقدر يعتمد'}, status=403)

    entry = ModelClass._base_manager.filter(id=entry_id, company=company).first()
    if not entry:
        return JsonResponse({'success': False, 'error': 'not found'}, status=404)

    if entry.status != 'pending':
        return JsonResponse({'success': False, 'error': 'الطلب ليس pending'}, status=400)

    data = json.loads(request.body.decode('utf-8')) if request.body else {}

    entry.status = 'approved'
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.approval_notes = data.get('notes', '').strip()

    # HR notification تلقائي
    entry.hr_notified = True
    entry.hr_notified_at = timezone.now()

    entry.save()

    # إشعار الموظف المستهدف + المدير الطالب + HR
    try:
        emp_name = f'{entry.employee.first_name_ar or ""} {entry.employee.last_name_ar or ""}'.strip() or entry.employee.employee_code
        notify_manual_entry_approved(
            user=entry.employee.user if entry.employee else None,
            category_display=entry.get_category_display(),
            amount_value=float(entry.amount_value),
            employee_name=emp_name,
            requester_user=entry.requested_by,
        )
        notify_hr_manual_entry_approved(
            company=company,
            category_display=entry.get_category_display(),
            employee_name=emp_name,
            amount_value=float(entry.amount_value),
        )
    except Exception as e:
        print(f"Manual entry notification error: {e}")

    return JsonResponse({
        'success': True,
        'message': 'تم اعتماد الطلب. HR تم إبلاغهم تلقائياً',
        'entry': _entry_to_dict(entry),
    })


def _handle_reject(request, entry_id, ModelClass):
    """CEO يرفض الطلب"""
    company = request.user.company

    if not _is_ceo(request.user):
        return JsonResponse({'success': False, 'error': 'فقط مدير الشركة يقدر يرفض'}, status=403)

    entry = ModelClass._base_manager.filter(id=entry_id, company=company).first()
    if not entry:
        return JsonResponse({'success': False, 'error': 'not found'}, status=404)

    if entry.status != 'pending':
        return JsonResponse({'success': False, 'error': 'الطلب ليس pending'}, status=400)

    data = json.loads(request.body.decode('utf-8'))
    reason = data.get('reason', '').strip()
    if not reason:
        return JsonResponse({'success': False, 'error': 'سبب الرفض مطلوب'}, status=400)

    entry.status = 'rejected'
    entry.rejected_by = request.user
    entry.rejected_at = timezone.now()
    entry.rejection_reason = reason
    entry.save()

    # إشعار الموظف المستهدف + المدير الطالب
    try:
        emp_name = f'{entry.employee.first_name_ar or ""} {entry.employee.last_name_ar or ""}'.strip() or entry.employee.employee_code
        notify_manual_entry_rejected(
            user=entry.employee.user if entry.employee else None,
            category_display=entry.get_category_display(),
            reason=reason,
            employee_name=emp_name,
            requester_user=entry.requested_by,
        )
    except Exception as e:
        print(f"Manual entry notification error: {e}")

    return JsonResponse({
        'success': True,
        'message': 'تم رفض الطلب',
        'entry': _entry_to_dict(entry),
    })


# ═══════════════════════════════════════════════════════════════
# Endpoints for each Model
# ═══════════════════════════════════════════════════════════════

# --- PENALTIES ---
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_penalty_list(request):
    return _handle_list_create(request, ManualPenalty)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_penalty_detail(request, entry_id):
    return _handle_detail_and_actions(request, entry_id, ManualPenalty)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_penalty_approve(request, entry_id):
    return _handle_approve(request, entry_id, ManualPenalty)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_penalty_reject(request, entry_id):
    return _handle_reject(request, entry_id, ManualPenalty)


# --- BONUSES ---
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_bonus_list(request):
    return _handle_list_create(request, ManualBonus)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_bonus_detail(request, entry_id):
    return _handle_detail_and_actions(request, entry_id, ManualBonus)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_bonus_approve(request, entry_id):
    return _handle_approve(request, entry_id, ManualBonus)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_bonus_reject(request, entry_id):
    return _handle_reject(request, entry_id, ManualBonus)


# --- ALLOWANCES ---
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_allowance_list(request):
    return _handle_list_create(request, ManualAllowance)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_allowance_detail(request, entry_id):
    return _handle_detail_and_actions(request, entry_id, ManualAllowance)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_allowance_approve(request, entry_id):
    return _handle_approve(request, entry_id, ManualAllowance)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_allowance_reject(request, entry_id):
    return _handle_reject(request, entry_id, ManualAllowance)


# ═══════════════════════════════════════════════════════════════
# Summary endpoint — للـ HR/CEO/Manager
# ═══════════════════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manual_entries_summary(request):
    """ملخص الطلبات المعلقة + الإحصائيات"""
    company = request.user.company

    def count_pending(ModelClass):
        return ModelClass._base_manager.filter(company=company, status='pending').count()

    def count_this_month(ModelClass, status):
        today = date.today()
        return ModelClass._base_manager.filter(
            company=company,
            status=status,
            target_year=today.year,
            target_month=today.month,
        ).count()

    return JsonResponse({
        'success': True,
        'pending': {
            'penalties': count_pending(ManualPenalty),
            'bonuses': count_pending(ManualBonus),
            'allowances': count_pending(ManualAllowance),
        },
        'this_month': {
            'approved_penalties': count_this_month(ManualPenalty, 'approved'),
            'approved_bonuses': count_this_month(ManualBonus, 'approved'),
            'approved_allowances': count_this_month(ManualAllowance, 'approved'),
        },
        'user_role': getattr(request.user, 'role', ''),
        'is_ceo': _is_ceo(request.user),
        'is_hr': _is_hr(request.user),
    })
