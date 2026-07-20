# ============================================================
# MISSIONS APIs - MotionHR V1
# ============================================================

from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from attendance.missions_models import (
    Mission, MissionAssignment, MissionLocation,
    MissionAttachment, MissionRequest, MissionClient,
    MissionFeedback, MissionFeedbackAddendum, MissionFollowup
)
from employees.models import Employee


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def get_employee(user):
    try:
        return Employee._base_manager.filter(user=user).first()
    except Exception:
        return None


def get_company(user):
    company = getattr(user, 'company', None)
    if company:
        return company

    try:
        emp = getattr(user, 'employee_profile', None)
        if emp and getattr(emp, 'company', None):
            return emp.company
    except Exception:
        pass

    emp = get_employee(user)
    if emp and getattr(emp, 'company', None):
        return emp.company

    return None


def is_manager_or_hr(user):
    role = getattr(user, 'role', None)
    return role in ('company_admin', 'hr_manager', 'manager', 'super_admin') or user.is_superuser or user.is_staff


def serialize_mission(mission, employee=None):
    assignments = mission.assignments.select_related('employee').all()
    assignment_data = []
    my_assignment = None

    for a in assignments:
        emp = a.employee
        name = f"{emp.first_name_ar} {emp.last_name_ar}"
        assignment_data.append({
            'id': a.id,
            'employee_id': emp.id,
            'employee_name': name,
            'role': a.role_in_mission,
            'role_display': a.get_role_in_mission_display(),
            'is_lead': a.is_lead,
            'status': a.status,
            'status_display': a.get_status_display(),
            'started_at': a.started_at.isoformat() if a.started_at else None,
            'ended_at': a.ended_at.isoformat() if a.ended_at else None,
        })
        if employee and emp.id == employee.id:
            my_assignment = a

    client_info = None
    try:
        c = mission.client_info
        client_info = {
            'client_name': c.client_name,
            'company_name': c.company_name,
            'position': c.position,
            'phone': c.phone,
            'email': c.email,
            'actual_address': c.actual_address,
        }
    except Exception:
        pass

    has_feedback = False
    try:
        mission.feedback
        has_feedback = True
    except Exception:
        pass

    data = {
        'id': mission.id,
        'title': mission.title,
        'description': mission.description,
        'priority': mission.priority,
        'priority_display': mission.get_priority_display(),
        'status': mission.status,
        'status_display': mission.get_status_display(),
        'source': mission.source,
        'planned_start_time': mission.planned_start_time.isoformat(),
        'planned_end_time': mission.planned_end_time.isoformat(),
        'location_name': mission.location_name,
        'location_lat': str(mission.location_lat) if mission.location_lat else None,
        'location_lng': str(mission.location_lng) if mission.location_lng else None,
        'client_name': mission.client_name,
        'client_phone': mission.client_phone,
        'created_at': mission.created_at.isoformat(),
        'assignments': assignment_data,
        'client_info': client_info,
        'has_feedback': has_feedback,
    }

    if my_assignment:
        data['my_assignment'] = {
            'id': my_assignment.id,
            'status': my_assignment.status,
            'status_display': my_assignment.get_status_display(),
            'is_lead': my_assignment.is_lead,
            'role': my_assignment.role_in_mission,
            'started_at': my_assignment.started_at.isoformat() if my_assignment.started_at else None,
            'ended_at': my_assignment.ended_at.isoformat() if my_assignment.ended_at else None,
        }

    return data


# ─────────────────────────────────────────────────────────────
# MANAGER APIs
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_missions_list(request):
    """قائمة المهمات للمدير"""
    company = get_company(request.user)
    if not company:
        return Response({'error': 'لم يتم العثور على بيانات الشركة'}, status=400)

    missions = Mission.objects.filter(company=company).prefetch_related('assignments__employee')

    # فلتر الحالة
    status_filter = request.GET.get('status')
    if status_filter:
        missions = missions.filter(status=status_filter)

    # فلتر الأولوية
    priority_filter = request.GET.get('priority')
    if priority_filter:
        missions = missions.filter(priority=priority_filter)

    # فلتر التاريخ
    date_filter = request.GET.get('date')
    if date_filter:
        missions = missions.filter(planned_start_time__date=date_filter)

    data = [serialize_mission(m) for m in missions]
    data.sort(key=lambda x: x.get('planned_start_time') or '', reverse=True)
    return Response({'missions': data, 'count': len(data)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_create_mission(request):
    """إنشاء مهمة جديدة"""
    company = get_company(request.user)
    if not company:
        return Response({'error': 'لم يتم العثور على بيانات الشركة'}, status=400)

    d = request.data

    # التحقق من الحقول المطلوبة
    required = ['title', 'planned_start_time', 'planned_end_time']
    for field in required:
        if not d.get(field):
            return Response({'error': f'الحقل {field} مطلوب'}, status=400)

    mission = Mission.objects.create(
        company=company,
        created_by=request.user,
        source='manager',
        status='approved',
        title=d['title'],
        description=d.get('description', ''),
        priority=d.get('priority', 'normal'),
        planned_start_time=d['planned_start_time'],
        planned_end_time=d['planned_end_time'],
        location_name=d.get('location_name', ''),
        location_lat=d.get('location_lat') or None,
        location_lng=d.get('location_lng') or None,
        client_name=d.get('client_name', ''),
        client_phone=d.get('client_phone', ''),
    )

    # إضافة بيانات العميل التفصيلية
    if any(d.get(f) for f in ['client_company', 'client_position', 'client_email', 'client_address']):
        MissionClient.objects.create(
            mission=mission,
            client_name=d.get('client_name', ''),
            company_name=d.get('client_company', ''),
            position=d.get('client_position', ''),
            phone=d.get('client_phone', ''),
            email=d.get('client_email', ''),
            actual_address=d.get('client_address', ''),
        )

    # تعيين الموظفين
    assignees = d.get('assignees', [])
    for i, assignee in enumerate(assignees):
        emp_id = assignee.get('employee_id')
        role = assignee.get('role', 'lead')
        is_lead = assignee.get('is_lead', i == 0)
        try:
            emp = Employee.objects.get(id=emp_id, company=company)
            MissionAssignment.objects.create(
                mission=mission,
                employee=emp,
                role_in_mission=role,
                is_lead=is_lead,
                status='pending',
                company=company,
            )
        except Employee.DoesNotExist:
            pass

    return Response({
        'success': True,
        'message': 'تم إنشاء المهمة بنجاح',
        'mission': serialize_mission(mission)
    }, status=201)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_mission_detail(request, mission_id):
    """تفاصيل مهمة للمدير"""
    company = get_company(request.user)
    try:
        mission = Mission.objects.get(id=mission_id, company=company)
    except Mission.DoesNotExist:
        return Response({'error': 'المهمة غير موجودة'}, status=404)

    return Response({'mission': serialize_mission(mission)})


@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_update_mission(request, mission_id):
    """تعديل مهمة"""
    company = get_company(request.user)
    try:
        mission = Mission.objects.get(id=mission_id, company=company)
    except Mission.DoesNotExist:
        return Response({'error': 'المهمة غير موجودة'}, status=404)

    if mission.status in ('in_progress', 'completed'):
        return Response({'error': 'لا يمكن تعديل مهمة جارية أو مكتملة'}, status=400)

    d = request.data
    for field in ['title', 'description', 'priority', 'planned_start_time',
                  'planned_end_time', 'location_name', 'location_lat',
                  'location_lng', 'client_name', 'client_phone', 'status']:
        if field in d:
            setattr(mission, field, d[field])
    mission.save()

    return Response({
        'success': True,
        'message': 'تم تحديث المهمة',
        'mission': serialize_mission(mission)
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_cancel_mission(request, mission_id):
    """إلغاء مهمة"""
    company = get_company(request.user)
    try:
        mission = Mission.objects.get(id=mission_id, company=company)
    except Mission.DoesNotExist:
        return Response({'error': 'المهمة غير موجودة'}, status=404)

    if mission.status == 'in_progress':
        return Response({'error': 'لا يمكن إلغاء مهمة جارية'}, status=400)

    mission.status = 'cancelled'
    mission.save()
    return Response({'success': True, 'message': 'تم إلغاء المهمة'})


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_pending_requests(request):
    """طلبات المهمات من الموظفين في انتظار الموافقة"""
    company = get_company(request.user)
    requests_qs = MissionRequest.objects.filter(
        mission__company=company,
        manager_approval='pending'
    ).select_related('mission', 'requested_by')

    data = []
    for req in requests_qs:
        emp = req.requested_by
        data.append({
            'request_id': req.id,
            'mission_id': req.mission.id if req.mission else None,
            'mission_title': req.mission.title if req.mission else '',
            'requested_by': f"{emp.first_name_ar} {emp.last_name_ar}",
            'employee_id': emp.id,
            'planned_start': req.mission.planned_start_time.isoformat() if req.mission else None,
            'created_at': req.created_at.isoformat(),
        })

    return Response({'requests': data, 'count': len(data)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_approve_request(request, request_id):
    """موافقة/رفض طلب مهمة من موظف"""
    company = get_company(request.user)
    try:
        req = MissionRequest.objects.get(id=request_id, mission__company=company)
    except MissionRequest.DoesNotExist:
        return Response({'error': 'الطلب غير موجود'}, status=404)

    action = request.data.get('action')  # 'approve' or 'reject'
    notes = request.data.get('notes', '')

    if action == 'approve':
        req.manager_approval = 'approved'
        req.final_status = 'approved'
        if req.mission:
            req.mission.status = 'approved'
            req.mission.save()
            # تعيين الموظف الطالب على المهمة
            emp = req.requested_by
            MissionAssignment.objects.get_or_create(
                mission=req.mission,
                employee=emp,
                defaults={
                    'role_in_mission': 'lead',
                    'is_lead': True,
                    'status': 'accepted',
                    'company': company,
                }
            )
        msg = 'تمت الموافقة على الطلب'
    elif action == 'reject':
        req.manager_approval = 'rejected'
        req.final_status = 'rejected'
        if req.mission:
            req.mission.status = 'cancelled'
            req.mission.save()
        msg = 'تم رفض الطلب'
    else:
        return Response({'error': 'action يجب أن يكون approve أو reject'}, status=400)

    req.manager_notes = notes
    req.manager_responded_at = timezone.now()
    req.save()

    return Response({'success': True, 'message': msg})


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_feedback_dashboard(request):
    """داشبورد الفيدباك للمدير"""
    company = get_company(request.user)
    feedbacks = MissionFeedback.objects.filter(
        mission__company=company
    ).select_related('mission', 'written_by')

    total = feedbacks.count()
    very_interested = feedbacks.filter(client_status='very_interested').count()
    interested = feedbacks.filter(client_status='interested').count()
    contracts_signed = feedbacks.filter(contract_signed=True).count()
    needs_followup = feedbacks.filter(needs_followup=True).count()

    total_deal_value = sum(
        f.deal_value for f in feedbacks.filter(contract_signed=True) if f.deal_value
    )

    upcoming_followups = MissionFollowup.objects.filter(
        original_mission__company=company,
        status__in=('pending', 'scheduled'),
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date')[:10]

    followups_data = []
    for f in upcoming_followups:
        followups_data.append({
            'id': f.id,
            'mission_title': f.original_mission.title,
            'scheduled_date': f.scheduled_date.isoformat(),
            'assigned_to': f"{f.assigned_to.first_name_ar} {f.assigned_to.last_name_ar}" if f.assigned_to else '',
            'status': f.status,
            'notes': f.notes,
        })

    recent_feedbacks = []
    for fb in feedbacks.order_by('-written_at')[:10]:
        recent_feedbacks.append({
            'id': fb.id,
            'mission_title': fb.mission.title,
            'client_status': fb.client_status,
            'client_status_display': fb.get_client_status_display(),
            'interest_rating': fb.interest_rating,
            'deal_probability': fb.deal_probability,
            'contract_signed': fb.contract_signed,
            'deal_value': str(fb.deal_value) if fb.deal_value else None,
            'needs_followup': fb.needs_followup,
            'followup_date': fb.followup_date.isoformat() if fb.followup_date else None,
            'written_at': fb.written_at.isoformat(),
        })

    return Response({
        'summary': {
            'total_feedbacks': total,
            'very_interested': very_interested,
            'interested': interested,
            'contracts_signed': contracts_signed,
            'needs_followup': needs_followup,
            'total_deal_value': str(total_deal_value),
        },
        'upcoming_followups': followups_data,
        'recent_feedbacks': recent_feedbacks,
    })


# ─────────────────────────────────────────────────────────────
# EMPLOYEE APIs
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_my_missions(request):
    """مهماتي - للموظف"""
    employee = get_employee(request.user)
    if not employee:
        return Response({'error': 'لم يتم العثور على بيانات الموظف'}, status=400)

    assignments = MissionAssignment.objects.filter(
        employee=employee
    ).select_related('mission').exclude(status='rejected')

    filter_type = request.GET.get('filter', 'all')
    today = timezone.now().date()

    if filter_type == 'today':
        assignments = assignments.filter(mission__planned_start_time__date=today)
    elif filter_type == 'upcoming':
        assignments = assignments.filter(
            mission__planned_start_time__date__gt=today,
            status__in=('pending', 'accepted')
        )
    elif filter_type == 'active':
        assignments = assignments.filter(status='in_progress')
    elif filter_type == 'completed':
        assignments = assignments.filter(status='completed')

    data = []
    for a in assignments.order_by('-mission__planned_start_time'):
        m = a.mission
        data.append({
            'assignment_id': a.id,
            'mission_id': m.id,
            'title': m.title,
            'description': m.description,
            'priority': m.priority,
            'priority_display': m.get_priority_display(),
            'status': a.status,
            'status_display': a.get_status_display(),
            'mission_status': m.status,
            'is_lead': a.is_lead,
            'role': a.role_in_mission,
            'role_display': a.get_role_in_mission_display(),
            'planned_start_time': m.planned_start_time.isoformat(),
            'planned_end_time': m.planned_end_time.isoformat(),
            'location_name': m.location_name,
            'location_lat': str(m.location_lat) if m.location_lat else None,
            'location_lng': str(m.location_lng) if m.location_lng else None,
            'client_name': m.client_name,
            'client_phone': m.client_phone,
            'started_at': a.started_at.isoformat() if a.started_at else None,
            'ended_at': a.ended_at.isoformat() if a.ended_at else None,
        })

    return Response({'missions': data, 'count': len(data)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_respond_mission(request, assignment_id):
    """قبول أو رفض مهمة"""
    employee = get_employee(request.user)
    try:
        assignment = MissionAssignment.objects.get(id=assignment_id, employee=employee)
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'التعيين غير موجود'}, status=404)

    if assignment.status != 'pending':
        return Response({'error': 'تم الرد على هذه المهمة مسبقاً'}, status=400)

    action = request.data.get('action')
    if action == 'accept':
        assignment.status = 'accepted'
        msg = 'تم قبول المهمة'
    elif action == 'reject':
        assignment.status = 'rejected'
        assignment.rejection_reason = request.data.get('reason', '')
        msg = 'تم رفض المهمة'
    else:
        return Response({'error': 'action يجب أن يكون accept أو reject'}, status=400)

    assignment.responded_at = timezone.now()
    assignment.save()

    return Response({'success': True, 'message': msg})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_start_mission(request, assignment_id):
    """بدء المهمة + Auto Attendance"""
    employee = get_employee(request.user)
    try:
        assignment = MissionAssignment.objects.get(
            id=assignment_id, employee=employee, status='accepted'
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'التعيين غير موجود أو غير مقبول'}, status=404)

    if assignment.started_at:
        return Response({'error': 'المهمة بدأت مسبقاً'}, status=400)

    lat = request.data.get('lat')
    lng = request.data.get('lng')

    now = timezone.now()
    assignment.status = 'in_progress'
    assignment.started_at = now
    if lat:
        assignment.start_lat = lat
    if lng:
        assignment.start_lng = lng
    assignment.save()

    # تحديث حالة المهمة
    assignment.mission.status = 'in_progress'
    assignment.mission.save()

    # تسجيل موقع البداية
    if lat and lng:
        MissionLocation.objects.create(
            assignment=assignment,
            lat=lat,
            lng=lng,
            location_label='موقع بداية المهمة',
            added_by_employee=True,
        )

    # Auto Attendance: لو مفيش check-in النهارده
    auto_checkin_done = False
    try:
        from attendance.models import Attendance
        today = now.date()
        existing = Attendance.objects.filter(
            employee=employee,
            date=today
        ).first()

        if not existing:
            Attendance.objects.create(
                employee=employee,
                company=employee.company,
                date=today,
                check_in_time=now.time(),
                status='present',
                notes=f'حضور تلقائي - مهمة: {assignment.mission.title}',
            )
            auto_checkin_done = True
    except Exception as e:
        pass

    return Response({
        'success': True,
        'message': 'تم بدء المهمة',
        'auto_checkin': auto_checkin_done,
        'started_at': assignment.started_at.isoformat(),
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_end_mission(request, assignment_id):
    """إنهاء المهمة"""
    employee = get_employee(request.user)
    try:
        assignment = MissionAssignment.objects.get(
            id=assignment_id, employee=employee, status='in_progress'
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'لا توجد مهمة جارية بهذا المعرف'}, status=404)

    lat = request.data.get('lat')
    lng = request.data.get('lng')
    notes = request.data.get('notes', '')

    now = timezone.now()
    assignment.status = 'completed'
    assignment.ended_at = now
    if lat:
        assignment.end_lat = lat
    if lng:
        assignment.end_lng = lng
    assignment.save()

    # تحقق لو كل المشاركين خلصوا → المهمة مكتملة
    mission = assignment.mission
    all_done = not mission.assignments.exclude(
        status__in=('completed', 'rejected')
    ).exists()
    if all_done:
        mission.status = 'completed'
        mission.save()

    # تسجيل موقع النهاية
    if lat and lng:
        MissionLocation.objects.create(
            assignment=assignment,
            lat=lat,
            lng=lng,
            location_label='موقع نهاية المهمة',
            added_by_employee=True,
        )

    return Response({
        'success': True,
        'message': 'تم إنهاء المهمة',
        'ended_at': assignment.ended_at.isoformat(),
        'mission_completed': mission.status == 'completed',
        'feedback_required': assignment.is_lead,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_update_location(request, assignment_id):
    """تحديث الموقع أثناء المهمة (لو تحرك مع العميل)"""
    employee = get_employee(request.user)
    try:
        assignment = MissionAssignment.objects.get(
            id=assignment_id, employee=employee, status='in_progress'
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'لا توجد مهمة جارية'}, status=404)

    lat = request.data.get('lat')
    lng = request.data.get('lng')
    label = request.data.get('label', 'موقع جديد')

    if not lat or not lng:
        return Response({'error': 'lat و lng مطلوبان'}, status=400)

    loc = MissionLocation.objects.create(
        assignment=assignment,
        lat=lat,
        lng=lng,
        location_label=label,
        added_by_employee=True,
    )

    return Response({
        'success': True,
        'message': 'تم تحديث الموقع',
        'location': {
            'id': loc.id,
            'lat': str(loc.lat),
            'lng': str(loc.lng),
            'label': loc.location_label,
            'recorded_at': loc.recorded_at.isoformat(),
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def employee_upload_attachment(request, assignment_id):
    """رفع صور إثبات للمهمة"""
    employee = get_employee(request.user)
    try:
        assignment = MissionAssignment.objects.get(
            id=assignment_id, employee=employee
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'التعيين غير موجود'}, status=404)

    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'لم يتم إرسال ملف'}, status=400)

    caption = request.data.get('caption', '')
    attachment = MissionAttachment.objects.create(
        assignment=assignment,
        file=file,
        caption=caption,
    )

    return Response({
        'success': True,
        'message': 'تم رفع المرفق',
        'attachment': {
            'id': attachment.id,
            'url': request.build_absolute_uri(attachment.file.url),
            'caption': attachment.caption,
            'uploaded_at': attachment.uploaded_at.isoformat(),
        }
    }, status=201)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_request_mission(request):
    """الموظف يطلب مهمة (رتب مع العميل مباشرة)"""
    employee = get_employee(request.user)
    if not employee:
        return Response({'error': 'لم يتم العثور على بيانات الموظف'}, status=400)

    d = request.data
    required = ['title', 'planned_start_time', 'planned_end_time']
    for field in required:
        if not d.get(field):
            return Response({'error': f'الحقل {field} مطلوب'}, status=400)

    # إنشاء المهمة بحالة pending_approval
    mission = Mission.objects.create(
        company=employee.company,
        created_by=request.user,
        source='employee_request',
        status='pending_approval',
        title=d['title'],
        description=d.get('description', ''),
        priority=d.get('priority', 'normal'),
        planned_start_time=d['planned_start_time'],
        planned_end_time=d['planned_end_time'],
        location_name=d.get('location_name', ''),
        location_lat=d.get('location_lat') or None,
        location_lng=d.get('location_lng') or None,
        client_name=d.get('client_name', ''),
        client_phone=d.get('client_phone', ''),
    )

    # إنشاء طلب للموافقة
    MissionRequest.objects.create(
        mission=mission,
        requested_by=employee,
        manager_approval='pending',
        final_status='pending',
    )

    return Response({
        'success': True,
        'message': 'تم إرسال طلب المهمة للمدير. انتظر الموافقة.',
        'mission_id': mission.id,
    }, status=201)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_submit_feedback(request, mission_id):
    """كتابة فيدباك بعد المهمة"""
    employee = get_employee(request.user)
    try:
        mission = Mission.objects.get(id=mission_id, company=employee.company)
        assignment = MissionAssignment.objects.get(
            mission=mission, employee=employee, is_lead=True
        )
    except (Mission.DoesNotExist, MissionAssignment.DoesNotExist):
        return Response({'error': 'المهمة غير موجودة أو لا يحق لك كتابة الفيدباك'}, status=404)

    if assignment.status != 'completed':
        return Response({'error': 'يجب إنهاء المهمة أولاً قبل كتابة الفيدباك'}, status=400)

    # لو فيه فيدباك موجود → تحديثه
    feedback, created = MissionFeedback.objects.get_or_create(
        mission=mission,
        defaults={'written_by': employee}
    )

    d = request.data
    feedback.interest_rating = d.get('interest_rating', feedback.interest_rating)
    feedback.deal_probability = d.get('deal_probability', feedback.deal_probability)
    feedback.client_status = d.get('client_status', feedback.client_status)
    feedback.client_needs = d.get('client_needs', feedback.client_needs)
    feedback.estimated_budget = d.get('estimated_budget') or feedback.estimated_budget
    feedback.expected_decision_date = d.get('expected_decision_date') or feedback.expected_decision_date
    feedback.interested_in = d.get('interested_in', feedback.interested_in)
    feedback.needs_followup = d.get('needs_followup', feedback.needs_followup)
    feedback.followup_date = d.get('followup_date') or feedback.followup_date
    feedback.preferred_contact = d.get('preferred_contact', feedback.preferred_contact)
    feedback.followup_notes = d.get('followup_notes', feedback.followup_notes)
    feedback.contract_signed = d.get('contract_signed', feedback.contract_signed)
    feedback.deal_value = d.get('deal_value') or feedback.deal_value
    feedback.internal_notes = d.get('internal_notes', feedback.internal_notes)
    feedback.warnings = d.get('warnings', feedback.warnings)

    # تعيين مسؤول المتابعة
    followup_owner_id = d.get('followup_owner_id')
    if followup_owner_id:
        try:
            feedback.followup_owner = Employee.objects.get(id=followup_owner_id)
        except Employee.DoesNotExist:
            pass

    feedback.save()

    # إنشاء متابعة لو مطلوب
    if feedback.needs_followup and feedback.followup_date:
        MissionFollowup.objects.get_or_create(
            original_mission=mission,
            defaults={
                'scheduled_date': feedback.followup_date,
                'assigned_to': feedback.followup_owner or employee,
                'status': 'scheduled',
                'notes': feedback.followup_notes,
            }
        )

    return Response({
        'success': True,
        'message': 'تم حفظ الفيدباك بنجاح',
        'created': created,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_add_feedback_note(request, mission_id):
    """مشارك آخر يضيف ملاحظة على الفيدباك"""
    employee = get_employee(request.user)
    try:
        mission = Mission.objects.get(id=mission_id, company=employee.company)
        feedback = mission.feedback
        # تأكد أنه مشارك في المهمة
        MissionAssignment.objects.get(mission=mission, employee=employee)
    except (Mission.DoesNotExist, MissionFeedback.DoesNotExist, MissionAssignment.DoesNotExist):
        return Response({'error': 'غير مصرح لك بإضافة ملاحظة'}, status=403)

    note = request.data.get('note', '').strip()
    if not note:
        return Response({'error': 'الملاحظة مطلوبة'}, status=400)

    addendum = MissionFeedbackAddendum.objects.create(
        feedback=feedback,
        added_by=employee,
        note=note,
    )

    return Response({
        'success': True,
        'message': 'تمت إضافة الملاحظة',
        'addendum': {
            'id': addendum.id,
            'note': addendum.note,
            'added_at': addendum.added_at.isoformat(),
        }
    }, status=201)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mission_feedback_detail(request, mission_id):
    """عرض الفيدباك الكامل لمهمة"""
    employee = get_employee(request.user)
    try:
        mission = Mission.objects.get(id=mission_id, company=employee.company)
        feedback = mission.feedback
    except (Mission.DoesNotExist, MissionFeedback.DoesNotExist):
        return Response({'error': 'الفيدباك غير موجود'}, status=404)

    addenda = []
    for a in feedback.addenda.select_related('added_by').all():
        addenda.append({
            'id': a.id,
            'added_by': f"{a.added_by.first_name_ar} {a.added_by.last_name_ar}",
            'note': a.note,
            'added_at': a.added_at.isoformat(),
        })

    data = {
        'id': feedback.id,
        'written_by': f"{feedback.written_by.first_name_ar} {feedback.written_by.last_name_ar}" if feedback.written_by else '',
        'written_at': feedback.written_at.isoformat(),
        'interest_rating': feedback.interest_rating,
        'deal_probability': feedback.deal_probability,
        'client_status': feedback.client_status,
        'client_status_display': feedback.get_client_status_display(),
        'client_needs': feedback.client_needs,
        'estimated_budget': str(feedback.estimated_budget) if feedback.estimated_budget else None,
        'expected_decision_date': feedback.expected_decision_date.isoformat() if feedback.expected_decision_date else None,
        'interested_in': feedback.interested_in,
        'needs_followup': feedback.needs_followup,
        'followup_date': feedback.followup_date.isoformat() if feedback.followup_date else None,
        'preferred_contact': feedback.preferred_contact,
        'preferred_contact_display': feedback.get_preferred_contact_display(),
        'followup_owner': f"{feedback.followup_owner.first_name_ar} {feedback.followup_owner.last_name_ar}" if feedback.followup_owner else '',
        'followup_notes': feedback.followup_notes,
        'contract_signed': feedback.contract_signed,
        'deal_value': str(feedback.deal_value) if feedback.deal_value else None,
        'internal_notes': feedback.internal_notes,
        'warnings': feedback.warnings,
        'addenda': addenda,
    }

    return Response({'feedback': data})


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mission_locations_timeline(request, assignment_id):
    """Timeline الحركة لتعيين معين"""
    employee = get_employee(request.user)
    try:
        assignment = MissionAssignment.objects.get(id=assignment_id)
        # المدير أو الموظف نفسه
        if assignment.employee != employee and not is_manager_or_hr(request.user):
            return Response({'error': 'غير مصرح'}, status=403)
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'التعيين غير موجود'}, status=404)

    locations = assignment.locations.all()
    data = [{
        'id': loc.id,
        'lat': str(loc.lat),
        'lng': str(loc.lng),
        'label': loc.location_label,
        'recorded_at': loc.recorded_at.isoformat(),
    } for loc in locations]

    return Response({'locations': data, 'count': len(data)})



# ─────────────────────────────────────────────────────────────
# MANAGER: إعادة تعيين موظف على مهمة (استبدال)
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_reassign_employee(request, mission_id):
    """
    المدير/HR يستبدل موظف على مهمة بموظف آخر
    حتى لو الموظف الأول قبل المهمة
    Body: { old_employee_id, new_employee_id, role, is_lead }
    """
    company = get_company(request.user)
    if not company:
        return Response({'error': 'لم يتم العثور على بيانات الشركة'}, status=400)

    try:
        mission = Mission.objects.get(id=mission_id, company=company)
    except Mission.DoesNotExist:
        return Response({'error': 'المهمة غير موجودة'}, status=404)

    if mission.status == 'completed':
        return Response({'error': 'لا يمكن تعديل مهمة مكتملة'}, status=400)

    old_emp_id = request.data.get('old_employee_id')
    new_emp_id = request.data.get('new_employee_id')
    reason = request.data.get('reason', '')

    if not old_emp_id or not new_emp_id:
        return Response({'error': 'old_employee_id و new_employee_id مطلوبان'}, status=400)

    # جيب التعيين القديم
    try:
        old_assignment = MissionAssignment.objects.get(
            mission=mission, employee__id=old_emp_id
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'الموظف القديم غير مُعيَّن على هذه المهمة'}, status=404)

    # لو الموظف القديم بدأ المهمة فعلاً → لا يمكن الاستبدال
    if old_assignment.status == 'in_progress':
        return Response({'error': 'لا يمكن استبدال موظف بدأ المهمة بالفعل. أنهِ مهمته أولاً.'}, status=400)

    # جيب الموظف الجديد
    try:
        new_emp = Employee.objects.get(id=new_emp_id, company=company)
    except Employee.DoesNotExist:
        return Response({'error': 'الموظف الجديد غير موجود'}, status=404)

    # حفظ بيانات التعيين القديم
    role = old_assignment.role_in_mission
    is_lead = old_assignment.is_lead

    # احذف التعيين القديم
    old_assignment.delete()

    # أنشئ تعيين جديد للموظف الجديد
    new_assignment, created = MissionAssignment.objects.get_or_create(
        mission=mission,
        employee=new_emp,
        defaults={
            'role_in_mission': role,
            'is_lead': is_lead,
            'status': 'pending',
            'company': company,
        }
    )
    if not created:
        return Response({'error': 'الموظف الجديد مُعيَّن على هذه المهمة مسبقاً'}, status=400)

    return Response({
        'success': True,
        'message': f'تم استبدال الموظف بنجاح',
        'new_assignment': {
            'id': new_assignment.id,
            'employee': f"{new_emp.first_name_ar} {new_emp.last_name_ar}",
            'role': new_assignment.role_in_mission,
            'is_lead': new_assignment.is_lead,
            'status': new_assignment.status,
        }
    })


# ─────────────────────────────────────────────────────────────
# EMPLOYEE: طلب الانسحاب من مهمة (حصل ظرف)
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def employee_withdraw_request(request, assignment_id):
    """
    الموظف يطلب الانسحاب من مهمة قبلها
    المدير يشوف الطلب ويوافق أو يرفض
    Body: { reason }
    """
    employee = get_employee(request.user)
    if not employee:
        return Response({'error': 'لم يتم العثور على بيانات الموظف'}, status=400)

    try:
        assignment = MissionAssignment.objects.get(
            id=assignment_id, employee=employee
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'التعيين غير موجود'}, status=404)

    if assignment.status == 'in_progress':
        return Response({'error': 'لا يمكن الانسحاب من مهمة جارية. أنهِ المهمة أولاً.'}, status=400)

    if assignment.status == 'completed':
        return Response({'error': 'المهمة مكتملة بالفعل'}, status=400)

    if assignment.status == 'rejected':
        return Response({'error': 'أنت رفضت هذه المهمة مسبقاً'}, status=400)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'سبب الانسحاب مطلوب'}, status=400)

    # احفظ طلب الانسحاب في rejection_reason مع flag خاص
    assignment.rejection_reason = f'[WITHDRAW_REQUEST] {reason}'
    assignment.save()

    return Response({
        'success': True,
        'message': 'تم إرسال طلب الانسحاب للمدير. انتظر الموافقة.',
        'assignment_id': assignment.id,
        'mission_title': assignment.mission.title,
    })


# ─────────────────────────────────────────────────────────────
# MANAGER: قائمة طلبات الانسحاب
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_withdraw_requests(request):
    """قائمة طلبات الانسحاب من المهمات"""
    company = get_company(request.user)
    if not company:
        return Response({'error': 'لم يتم العثور على بيانات الشركة'}, status=400)

    assignments = MissionAssignment.objects.filter(
        mission__company=company,
        rejection_reason__startswith='[WITHDRAW_REQUEST]'
    ).exclude(status='rejected').select_related('mission', 'employee')

    data = []
    for a in assignments:
        emp = a.employee
        reason = a.rejection_reason.replace('[WITHDRAW_REQUEST] ', '')
        data.append({
            'assignment_id': a.id,
            'mission_id': a.mission.id,
            'mission_title': a.mission.title,
            'employee_id': emp.id,
            'employee_name': f"{emp.first_name_ar} {emp.last_name_ar}",
            'reason': reason,
            'current_status': a.status,
            'planned_start': a.mission.planned_start_time.isoformat(),
        })

    return Response({'withdraw_requests': data, 'count': len(data)})


# ─────────────────────────────────────────────────────────────
# MANAGER: الموافقة على طلب الانسحاب
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_respond_withdraw(request, assignment_id):
    """
    المدير يوافق أو يرفض طلب انسحاب موظف
    Body: { action: 'approve'/'reject', notes }
    """
    company = get_company(request.user)
    if not company:
        return Response({'error': 'لم يتم العثور على بيانات الشركة'}, status=400)

    try:
        assignment = MissionAssignment.objects.get(
            id=assignment_id,
            mission__company=company,
            rejection_reason__startswith='[WITHDRAW_REQUEST]'
        )
    except MissionAssignment.DoesNotExist:
        return Response({'error': 'طلب الانسحاب غير موجود'}, status=404)

    action = request.data.get('action')

    if action == 'approve':
        assignment.status = 'rejected'
        assignment.responded_at = timezone.now()
        assignment.save()
        msg = 'تمت الموافقة على طلب الانسحاب. تم إزالة الموظف من المهمة.'
    elif action == 'reject':
        assignment.rejection_reason = ''
        assignment.save()
        msg = 'تم رفض طلب الانسحاب. الموظف لا يزال مُعيَّناً على المهمة.'
    else:
        return Response({'error': 'action يجب أن يكون approve أو reject'}, status=400)

    return Response({'success': True, 'message': msg})


# ─────────────────────────────────────────────────────────────
# MANAGER/HR: إلغاء مهمة حتى لو جارية (صلاحية خاصة)
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_force_cancel_mission(request, mission_id):
    """
    المدير أو HR يلغي مهمة حتى لو كانت جارية
    Body: { reason }
    """
    company = get_company(request.user)
    if not company:
        return Response({'error': 'لم يتم العثور على بيانات الشركة'}, status=400)

    if not is_manager_or_hr(request.user):
        return Response({'error': 'غير مصرح. يجب أن تكون مدير أو HR'}, status=403)

    try:
        mission = Mission.objects.get(id=mission_id, company=company)
    except Mission.DoesNotExist:
        return Response({'error': 'المهمة غير موجودة'}, status=404)

    if mission.status == 'completed':
        return Response({'error': 'لا يمكن إلغاء مهمة مكتملة'}, status=400)

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'سبب الإلغاء مطلوب'}, status=400)

    old_status = mission.status
    mission.status = 'cancelled'
    mission.save()

    # إلغاء كل التعيينات النشطة
    cancelled_count = 0
    for assignment in mission.assignments.filter(
        status__in=('pending', 'accepted', 'in_progress')
    ):
        assignment.status = 'rejected'
        assignment.rejection_reason = f'[FORCE_CANCEL] {reason}'
        assignment.save()
        cancelled_count += 1

    return Response({
        'success': True,
        'message': f'تم إلغاء المهمة بنجاح',
        'mission_id': mission_id,
        'previous_status': old_status,
        'affected_assignments': cancelled_count,
        'reason': reason,
    })

