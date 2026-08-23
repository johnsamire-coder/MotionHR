from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, time
from decimal import Decimal

from attendance.models import Attendance, DailyAttendanceSummary
from employees.models import EmployeeMovement


def _parse_time_str(time_str, record_date):
    if not time_str:
        return None
    time_str = str(time_str).strip()
    parts = time_str.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s = int(parts[2]) if len(parts) > 2 else 0
    t = time(h, m, s)
    dt = datetime.combine(record_date, t)
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_adjust_attendance(request, attendance_id):
    user = request.user
    allowed_roles = ['super_admin', 'company_admin', 'hr_manager']
    is_authorized = user.role in allowed_roles or getattr(user, 'is_superuser', False)
    if not is_authorized:
        return Response({'success': False, 'message': 'صلاحية غير كافية. تعديل الحضور متاح لـ HR والإدارة فقط'}, status=403)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'success': False, 'message': 'يجب كتابة سبب التعديل بالتفصيل'}, status=400)

    try:
        attendance = Attendance._base_manager.select_related('employee', 'employee__company').get(id=attendance_id)
    except Attendance.DoesNotExist:
        return Response({'success': False, 'message': 'سجل الحضور غير موجود'}, status=404)

    if user.role != 'super_admin' and attendance.employee.company_id != getattr(user, 'company_id', None):
        return Response({'success': False, 'message': 'لا يمكنك تعديل سجلات موظف في شركة أخرى'}, status=403)

    changes = []
    req_check_in = request.data.get('check_in_time')
    req_check_out = request.data.get('check_out_time')
    req_status = request.data.get('status')

    if req_check_in is not None:
        old_in = attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else 'لا يوجد'
        if req_check_in:
            attendance.check_in_time = _parse_time_str(req_check_in, attendance.date)
            new_in = str(req_check_in)
        else:
            attendance.check_in_time = None
            new_in = 'مسح'
        changes.append('وقت الحضور: ' + old_in + ' -> ' + new_in)

    if req_check_out is not None:
        old_out = attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else 'لا يوجد'
        if req_check_out:
            attendance.check_out_time = _parse_time_str(req_check_out, attendance.date)
            new_out = str(req_check_out)
        else:
            attendance.check_out_time = None
            new_out = 'مسح'
        changes.append('وقت الانصراف: ' + old_out + ' -> ' + new_out)

    if req_status and req_status in dict(Attendance.STATUS_CHOICES):
        old_status = attendance.status
        attendance.status = req_status
        changes.append('الحالة: ' + str(old_status) + ' -> ' + str(req_status))

    if attendance.check_in_time and attendance.check_out_time:
        delta = attendance.check_out_time - attendance.check_in_time
        hours = round(Decimal(str(delta.total_seconds() / 3600)), 2)
        attendance.work_hours = max(Decimal('0.00'), hours)
        if not req_status:
            attendance.status = 'present'
    elif attendance.check_in_time:
        if not req_status:
            attendance.status = 'present'

    attendance.is_manually_edited = True
    actor_name = user.get_full_name() or user.username
    audit_msg = 'تعديل بواسطة (' + actor_name + '): ' + ', '.join(changes) + ' | السبب: ' + reason
    stamp = timezone.now().strftime('%Y-%m-%d %H:%M')
    existing_notes = attendance.admin_notes or ''
    attendance.admin_notes = (existing_notes + chr(10) + '[' + stamp + '] ' + audit_msg).strip()
    attendance.save()

    try:
        EmployeeMovement._base_manager.create(
            employee=attendance.employee,
            movement_type='attendance_adjustment',
            description=audit_msg,
            date=attendance.date,
            created_by=user
        )
    except Exception:
        pass

    try:
        DailyAttendanceSummary._base_manager.update_or_create(
            employee=attendance.employee,
            date=attendance.date,
            defaults={
                'status': attendance.status,
                'work_hours': attendance.work_hours or Decimal('0.00'),
            }
        )
    except Exception:
        pass

    return Response({
        'success': True,
        'message': 'تم تعديل سجل الحضور بنجاح',
        'changes': changes,
        'attendance': {
            'id': attendance.id,
            'date': str(attendance.date),
            'check_in_time': attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else None,
            'check_out_time': attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else None,
            'work_hours': float(attendance.work_hours) if attendance.work_hours else 0,
            'status': attendance.status,
            'is_manually_edited': attendance.is_manually_edited,
        }
    })
