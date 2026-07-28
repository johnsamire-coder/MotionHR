"""
Work Locations APIs
──────────────────────────────
نظام المواقع المتعددة للموظفين (Multi-Site)
- الموظف يقترح موقع جديد
- المدير/HR يوافق أو يرفض
- الموظف يقدر يبصم من المواقع المعتمدة
"""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication

from attendance.models import EmployeeWorkLocation
from employees.models import Employee


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════
def get_employee_for_user(user):
    return Employee._base_manager.filter(user=user).first()


def reverse_geocode_safe(lat, lng):
    try:
        from attendance.api_mobile import reverse_geocode
        return reverse_geocode(lat, lng)
    except Exception:
        return ''


def work_location_to_dict(loc):
    """تحويل موقع العمل لـ dict"""
    return {
        'id': loc.id,
        'name': loc.name,
        'description': loc.description or '',
        'location_type': loc.location_type,
        'location_type_display': loc.get_location_type_display(),
        'latitude': float(loc.latitude) if loc.latitude else None,
        'longitude': float(loc.longitude) if loc.longitude else None,
        'radius': loc.radius,
        'address': loc.address or '',
        'city': loc.city or '',
        
        'project_code': loc.project_code or '',
        'client_name': loc.client_name or '',
        'contact_person': loc.contact_person or '',
        'contact_phone': loc.contact_phone or '',
        
        'is_shared': loc.is_shared,
        'requires_checkin_photo': loc.requires_checkin_photo,
        
        'valid_from': loc.valid_from.isoformat() if loc.valid_from else None,
        'valid_until': loc.valid_until.isoformat() if loc.valid_until else None,
        
        'status': loc.status,
        'status_display': loc.get_status_display(),
        
        'proposed_at': loc.proposed_at.isoformat() if loc.proposed_at else None,
        'approved_at': loc.approved_at.isoformat() if loc.approved_at else None,
        'approved_by_name': (
            loc.approved_by.get_full_name() 
            if loc.approved_by else None
        ),
        'rejection_reason': loc.rejection_reason or '',
        
        'is_active': loc.is_active,
        'color_code': loc.color_code,
        'icon': loc.icon,
        'priority': loc.priority,
        
        'total_visits_count': loc.total_visits_count,
        'last_visited_at': loc.last_visited_at.isoformat() if loc.last_visited_at else None,
    }


# ═══════════════════════════════════════════════════
# API 1: اقتراح موقع جديد (Employee)
# ═══════════════════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def propose_work_location(request):
    """
    POST /attendance/api/mobile/work-locations/propose/
    
    Body:
    {
        "name": "موقع مشروع الجيزة",
        "description": "الوصف",
        "location_type": "project",
        "latitude": 30.05,
        "longitude": 31.24,
        "radius": 500,
        "project_code": "PRJ-2026-001",
        "client_name": "شركة العميل",
        "contact_person": "أحمد",
        "contact_phone": "01000000000",
        "valid_from": "2026-01-01",
        "valid_until": "2026-12-31",
        "notes": "ملاحظات"
    }
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    # نتحقق من الحقول الإجبارية
    name = request.data.get('name', '').strip()
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    
    if not name:
        return Response({'success': False, 'message': 'اسم الموقع مطلوب'}, status=400)
    if latitude in [None, ''] or longitude in [None, '']:
        return Response({'success': False, 'message': 'الإحداثيات مطلوبة'}, status=400)
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        return Response({'success': False, 'message': 'إحداثيات غير صحيحة'}, status=400)
    
    # نتحقق من نوع الموقع
    location_type = request.data.get('location_type', 'project')
    valid_types = [c[0] for c in EmployeeWorkLocation.LOCATION_TYPE_CHOICES]
    if location_type not in valid_types:
        location_type = 'project'
    
    # radius
    try:
        radius = int(request.data.get('radius') or 500)
    except (ValueError, TypeError):
        radius = 500
    
    # dates
    from datetime import datetime
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    # جيب اسم الموقع من reverse geocode
    address = reverse_geocode_safe(latitude, longitude)
    
    # ننشئ الموقع
    location = EmployeeWorkLocation._base_manager.create(
        company=employee.company,
        employee=employee,
        name=name,
        description=request.data.get('description', '').strip(),
        location_type=location_type,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        address=address,
        city=request.data.get('city', '').strip() or None,
        project_code=request.data.get('project_code', '').strip() or None,
        client_name=request.data.get('client_name', '').strip() or None,
        contact_person=request.data.get('contact_person', '').strip() or None,
        contact_phone=request.data.get('contact_phone', '').strip() or None,
        valid_from=parse_date(request.data.get('valid_from')),
        valid_until=parse_date(request.data.get('valid_until')),
        notes=request.data.get('notes', '').strip() or None,
        status='pending',
        proposed_by=request.user,
    )
    
    # TODO: إشعار للمدير/HR
    
    return Response({
        'success': True,
        'message': 'تم اقتراح الموقع بنجاح. في انتظار موافقة المدير.',
        'location': work_location_to_dict(location),
    }, status=201)


# ═══════════════════════════════════════════════════
# API 2: قائمة مواقعي
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_work_locations(request):
    """
    GET /attendance/api/mobile/work-locations/
    
    Query params:
    - filter: 'all' | 'approved' | 'pending' | 'rejected'
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    filter_type = request.GET.get('filter', 'all').lower()
    
    from django.db.models import Q
    
    # المواقع الخاصة بالموظف + المشتركة اللي متاحة له
    qs = EmployeeWorkLocation._base_manager.filter(
        company=employee.company,
    ).filter(
        Q(employee=employee) |  # مواقعي الخاصة
        Q(is_shared=True, shared_with_branch=None, shared_with_department=None) |  # مشترك لكل الشركة
        Q(is_shared=True, shared_with_branch=employee.branch) |  # مشترك مع فرعي
        Q(is_shared=True, shared_with_department=employee.department)  # مشترك مع قسمي
    ).distinct().order_by('-priority', '-created_at')
    
    if filter_type == 'approved':
        qs = qs.filter(status='approved', is_active=True)
    elif filter_type == 'pending':
        qs = qs.filter(status='pending')
    elif filter_type == 'rejected':
        qs = qs.filter(status='rejected')
    
    locations = list(qs[:100])
    
    return Response({
        'success': True,
        'count': len(locations),
        'locations': [work_location_to_dict(l) for l in locations],
    })


# ═══════════════════════════════════════════════════
# API 3: تفاصيل موقع
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def work_location_detail(request, location_id):
    """
    GET /attendance/api/mobile/work-locations/<id>/
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    location = EmployeeWorkLocation._base_manager.filter(
        id=location_id,
        company=employee.company,
    ).first()
    
    if not location:
        return Response({'success': False, 'message': 'الموقع غير موجود'}, status=404)
    
    return Response({
        'success': True,
        'location': work_location_to_dict(location),
    })


# ═══════════════════════════════════════════════════
# API 4: إلغاء طلب معلق (الموظف)
# ═══════════════════════════════════════════════════
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def cancel_pending_location(request, location_id):
    """
    DELETE /attendance/api/mobile/work-locations/<id>/cancel/
    الموظف يقدر يلغي طلبه المعلق فقط
    """
    employee = get_employee_for_user(request.user)
    if not employee:
        return Response({'success': False, 'message': 'الموظف غير موجود'}, status=404)
    
    location = EmployeeWorkLocation._base_manager.filter(
        id=location_id,
        employee=employee,
    ).first()
    
    if not location:
        return Response({'success': False, 'message': 'الموقع غير موجود'}, status=404)
    
    if location.status != 'pending':
        return Response({
            'success': False,
            'message': f'يمكن إلغاء الطلبات المعلقة فقط. الحالة الحالية: {location.get_status_display()}',
        }, status=400)
    
    location.delete()
    
    return Response({
        'success': True,
        'message': 'تم إلغاء الطلب بنجاح',
    })


# ═══════════════════════════════════════════════════
# API 5: أنواع المواقع المتاحة
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def work_location_types(request):
    """
    GET /attendance/api/mobile/work-locations/types/
    """
    types = [
        {'value': c[0], 'label': c[1]}
        for c in EmployeeWorkLocation.LOCATION_TYPE_CHOICES
    ]
    return Response({'success': True, 'types': types})


# ═══════════════════════════════════════════════════
# ═══════════════════════════════════════════════════
# Manager/HR APIs
# ═══════════════════════════════════════════════════
# ═══════════════════════════════════════════════════

def _is_manager_or_hr(user):
    return getattr(user, 'role', '') in ('company_admin', 'hr_manager', 'manager', 'super_admin')


# ═══════════════════════════════════════════════════
# API 6: قائمة الطلبات المعلقة (Manager/HR)
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_pending_locations(request):
    """
    GET /attendance/api/mobile/manager/work-locations/pending/
    """
    if not _is_manager_or_hr(request.user):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    
    company = request.user.company
    if not company:
        return Response({'success': False, 'message': 'لا توجد شركة مرتبطة'}, status=400)
    
    qs = EmployeeWorkLocation._base_manager.filter(
        company=company,
        status='pending',
    ).select_related('employee', 'proposed_by').order_by('-proposed_at')
    
    locations = list(qs[:100])
    
    data = []
    for loc in locations:
        item = work_location_to_dict(loc)
        item['employee_name'] = (
            f"{loc.employee.first_name_ar} {loc.employee.last_name_ar}"
            if loc.employee else 'غير محدد'
        )
        item['proposed_by_name'] = (
            loc.proposed_by.get_full_name() if loc.proposed_by else 'غير معروف'
        )
        data.append(item)
    
    return Response({
        'success': True,
        'count': len(data),
        'locations': data,
    })


# ═══════════════════════════════════════════════════
# API 7: كل مواقع الشركة (Manager/HR)
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_all_locations(request):
    """
    GET /attendance/api/mobile/manager/work-locations/
    
    Query params:
    - filter: 'all' | 'approved' | 'pending' | 'rejected' | 'expired'
    - employee_id: filter بموظف معين
    """
    if not _is_manager_or_hr(request.user):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    
    company = request.user.company
    if not company:
        return Response({'success': False, 'message': 'لا توجد شركة مرتبطة'}, status=400)
    
    qs = EmployeeWorkLocation._base_manager.filter(
        company=company,
    ).select_related('employee', 'proposed_by', 'approved_by').order_by('-created_at')
    
    filter_type = request.GET.get('filter', 'all').lower()
    if filter_type in ('approved', 'pending', 'rejected', 'expired', 'suspended'):
        qs = qs.filter(status=filter_type)
    
    employee_id = request.GET.get('employee_id')
    if employee_id:
        try:
            qs = qs.filter(employee_id=int(employee_id))
        except (ValueError, TypeError):
            pass
    
    locations = list(qs[:200])
    
    data = []
    for loc in locations:
        item = work_location_to_dict(loc)
        item['employee_name'] = (
            f"{loc.employee.first_name_ar} {loc.employee.last_name_ar}"
            if loc.employee else 'مشترك'
        )
        data.append(item)
    
    return Response({
        'success': True,
        'count': len(data),
        'locations': data,
    })


# ═══════════════════════════════════════════════════
# API 8: الموافقة على موقع (Manager/HR)
# ═══════════════════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def approve_work_location(request, location_id):
    """
    POST /attendance/api/mobile/manager/work-locations/<id>/approve/
    
    Body:
    {
        "notes": "ملاحظات الموافقة"  // اختياري
    }
    """
    if not _is_manager_or_hr(request.user):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    
    location = EmployeeWorkLocation._base_manager.filter(
        id=location_id,
        company=request.user.company,
    ).first()
    
    if not location:
        return Response({'success': False, 'message': 'الموقع غير موجود'}, status=404)
    
    if location.status != 'pending':
        return Response({
            'success': False,
            'message': f'الموقع بحالة {location.get_status_display()}، لا يمكن الموافقة عليه',
        }, status=400)
    
    location.status = 'approved'
    location.approved_by = request.user
    location.approved_at = timezone.now()
    location.approval_notes = request.data.get('notes', '').strip() or None
    location.save()
    
    # TODO: إشعار للموظف
    
    return Response({
        'success': True,
        'message': 'تم اعتماد الموقع بنجاح',
        'location': work_location_to_dict(location),
    })


# ═══════════════════════════════════════════════════
# API 9: رفض موقع (Manager/HR)
# ═══════════════════════════════════════════════════
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reject_work_location(request, location_id):
    """
    POST /attendance/api/mobile/manager/work-locations/<id>/reject/
    
    Body:
    {
        "reason": "سبب الرفض"  // إجباري
    }
    """
    if not _is_manager_or_hr(request.user):
        return Response({'success': False, 'message': 'غير مصرح'}, status=403)
    
    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'success': False, 'message': 'سبب الرفض مطلوب'}, status=400)
    
    location = EmployeeWorkLocation._base_manager.filter(
        id=location_id,
        company=request.user.company,
    ).first()
    
    if not location:
        return Response({'success': False, 'message': 'الموقع غير موجود'}, status=404)
    
    if location.status != 'pending':
        return Response({
            'success': False,
            'message': f'الموقع بحالة {location.get_status_display()}، لا يمكن رفضه',
        }, status=400)
    
    location.status = 'rejected'
    location.approved_by = request.user
    location.approved_at = timezone.now()
    location.rejection_reason = reason
    location.save()
    
    # TODO: إشعار للموظف
    
    return Response({
        'success': True,
        'message': 'تم رفض الموقع',
        'location': work_location_to_dict(location),
    })
