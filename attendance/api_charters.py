"""
نظام اللوائح المتعددة — لوائح مستهدفة (دور/قسم/فرع) لكل شركة
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import os

MANAGER_ROLES = ['super_admin', 'company_admin', 'hr_manager', 'manager']


def _check_manager(request):
    user = request.user
    role = getattr(user, 'role', '')
    if not (user.is_staff or user.is_superuser or role in MANAGER_ROLES):
        return Response({"success": False, "error": "غير مصرح"}, status=403)
    return None


def _get_employee(user):
    from employees.models import Employee
    return Employee._base_manager.filter(user=user).first()


def _serialize_charter(charter, request):
    attachment_url = request.build_absolute_uri(charter.attachment.url) if getattr(charter, 'attachment', None) else ''
    attachment_name = charter.attachment.name.split('/')[-1] if getattr(charter, 'attachment', None) else ''
    return {
        'id': charter.id,
        'title': charter.title,
        'introduction': charter.introduction or '',
        'content': charter.content or '',
        'version': charter.version,
        'is_active': charter.is_active,
        'is_mandatory': charter.is_mandatory,
        'target_roles': charter.target_roles or [],
        'target_departments': list(charter.target_departments.values_list('id', flat=True)),
        'target_department_names': list(charter.target_departments.values_list('name_ar', flat=True)),
        'target_branches': list(charter.target_branches.values_list('id', flat=True)),
        'target_branch_names': list(charter.target_branches.values_list('name_ar', flat=True)),
        'attachment_url': attachment_url,
        'attachment_name': attachment_name,
        'created_at': charter.created_at.isoformat() if charter.created_at else None,
        'updated_at': charter.updated_at.isoformat() if charter.updated_at else None,
    }


def _charter_applies_to_employee(charter, employee, user):
    """يتأكد هل اللائحة تخص الموظف ده (حسب دوره/قسمه/فرعه)"""
    role = getattr(user, 'role', '') or 'employee'
    target_roles = charter.target_roles or []
    if target_roles and role not in target_roles:
        return False

    dept_ids = set(charter.target_departments.values_list('id', flat=True))
    if dept_ids:
        emp_dept_id = getattr(employee, 'department_id', None) if employee else None
        if emp_dept_id not in dept_ids:
            return False

    branch_ids = set(charter.target_branches.values_list('id', flat=True))
    if branch_ids:
        emp_branch_id = getattr(employee, 'branch_id', None) if employee else None
        if emp_branch_id not in branch_ids:
            return False

    return True


# ═══════════════════════════════════════════
# للمدير: إدارة اللوائح
# ═══════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_charters_list(request):
    """قائمة كل لوائح الشركة"""
    err = _check_manager(request)
    if err:
        return err
    from companies.models import WorkCharter

    user = request.user
    employee = _get_employee(user)
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    charters = WorkCharter._base_manager.filter(company=company).order_by('-created_at')
    data = [_serialize_charter(c, request) for c in charters]
    return Response({"success": True, "charters": data, "count": len(data)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_charters_create(request):
    """إنشاء لائحة جديدة مستهدفة"""
    err = _check_manager(request)
    if err:
        return err
    from companies.models import WorkCharter, Department, Branch
    import json

    user = request.user
    employee = _get_employee(user)
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة"}, status=400)

    title = request.data.get('title', '').strip()
    content = request.data.get('content', '').strip()
    if not title or not content:
        return Response({"success": False, "error": "العنوان والمحتوى مطلوبين"}, status=400)

    attachment_file = request.FILES.get('attachment')
    if attachment_file:
        ext = os.path.splitext(attachment_file.name.lower())[1]
        allowed = {'.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'}
        if ext not in allowed:
            return Response({"success": False, "error": "نوع الملف غير مدعوم. المسموح: PDF / Word / PNG / JPG"}, status=400)
        max_size = 10 * 1024 * 1024
        if attachment_file.size > max_size:
            return Response({"success": False, "error": "حجم الملف كبير. الحد الأقصى 10 MB"}, status=400)

    try:
        target_roles = json.loads(request.data.get('target_roles', '[]') or '[]')
    except (ValueError, TypeError):
        target_roles = []

    try:
        target_dept_ids = json.loads(request.data.get('target_departments', '[]') or '[]')
    except (ValueError, TypeError):
        target_dept_ids = []

    try:
        target_branch_ids = json.loads(request.data.get('target_branches', '[]') or '[]')
    except (ValueError, TypeError):
        target_branch_ids = []

    charter = WorkCharter._base_manager.create(
        company=company,
        title=title,
        content=content,
        introduction=request.data.get('introduction', ''),
        is_active=True,
        is_mandatory=str(request.data.get('is_mandatory', 'true')).lower() in ['1', 'true', 'yes'],
        target_roles=target_roles,
        attachment=attachment_file if attachment_file else None,
    )
    if target_dept_ids:
        charter.target_departments.set(Department.objects.filter(id__in=target_dept_ids, company=company))
    if target_branch_ids:
        charter.target_branches.set(Branch.objects.filter(id__in=target_branch_ids, company=company))

    return Response({"success": True, "message": "تم إنشاء اللائحة", "charter": _serialize_charter(charter, request)})


@api_view(['PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_charters_update(request, charter_id):
    """تعديل لائحة موجودة"""
    err = _check_manager(request)
    if err:
        return err
    from companies.models import WorkCharter, Department, Branch
    import json

    user = request.user
    employee = _get_employee(user)
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    charter = WorkCharter._base_manager.filter(id=charter_id, company=company).first()
    if not charter:
        return Response({"success": False, "error": "اللائحة غير موجودة"}, status=404)

    if 'title' in request.data:
        charter.title = request.data.get('title', charter.title)
    if 'content' in request.data:
        charter.content = request.data.get('content', charter.content)
    if 'introduction' in request.data:
        charter.introduction = request.data.get('introduction', charter.introduction)
    if 'is_mandatory' in request.data:
        charter.is_mandatory = str(request.data.get('is_mandatory')).lower() in ['1', 'true', 'yes']
    if 'is_active' in request.data:
        charter.is_active = str(request.data.get('is_active')).lower() in ['1', 'true', 'yes']

    attachment_file = request.FILES.get('attachment')
    if attachment_file:
        ext = os.path.splitext(attachment_file.name.lower())[1]
        allowed = {'.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'}
        if ext not in allowed:
            return Response({"success": False, "error": "نوع الملف غير مدعوم"}, status=400)
        charter.attachment = attachment_file

    if str(request.data.get('remove_attachment', '')).lower() in ['1', 'true', 'yes']:
        charter.attachment = None

    if 'target_roles' in request.data:
        try:
            charter.target_roles = json.loads(request.data.get('target_roles') or '[]')
        except (ValueError, TypeError):
            pass

    charter.save()

    if 'target_departments' in request.data:
        try:
            dept_ids = json.loads(request.data.get('target_departments') or '[]')
            charter.target_departments.set(Department.objects.filter(id__in=dept_ids, company=company))
        except (ValueError, TypeError):
            pass

    if 'target_branches' in request.data:
        try:
            branch_ids = json.loads(request.data.get('target_branches') or '[]')
            charter.target_branches.set(Branch.objects.filter(id__in=branch_ids, company=company))
        except (ValueError, TypeError):
            pass

    return Response({"success": True, "message": "تم تحديث اللائحة", "charter": _serialize_charter(charter, request)})


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_charters_delete(request, charter_id):
    """حذف لائحة"""
    err = _check_manager(request)
    if err:
        return err
    from companies.models import WorkCharter

    user = request.user
    employee = _get_employee(user)
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)

    charter = WorkCharter._base_manager.filter(id=charter_id, company=company).first()
    if not charter:
        return Response({"success": False, "error": "اللائحة غير موجودة"}, status=404)

    charter.delete()
    return Response({"success": True, "message": "تم حذف اللائحة"})


# ═══════════════════════════════════════════
# للموظف: عرض وقبول اللوائح اللي تخصه
# ═══════════════════════════════════════════

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_charters_list(request):
    """قائمة اللوائح اللي تخص الموظف الحالي + حالة التوقيع لكل واحدة"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    employee = _get_employee(user)
    company = getattr(user, 'company', None) or getattr(employee, 'company', None)
    if not company:
        return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)

    all_charters = WorkCharter._base_manager.filter(company=company, is_active=True)
    my_charters = [c for c in all_charters if _charter_applies_to_employee(c, employee, user)]

    accepted_ids = set()
    if employee:
        accepted_ids = set(
            CharterAcceptance._base_manager.filter(employee=employee, charter__in=my_charters).values_list('charter_id', flat=True)
        )

    data = []
    for c in my_charters:
        item = _serialize_charter(c, request)
        item['accepted'] = c.id in accepted_ids
        item['needs_acceptance'] = c.is_mandatory and c.id not in accepted_ids
        data.append(item)

    return Response({"success": True, "charters": data, "count": len(data)})


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_charter_accept(request, charter_id):
    """الموظف يوقّع على لائحة معينة"""
    from companies.models import WorkCharter, CharterAcceptance

    user = request.user
    employee = _get_employee(user)
    if not employee:
        return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

    charter = WorkCharter._base_manager.filter(id=charter_id, is_active=True).first()
    if not charter:
        return Response({"success": False, "error": "اللائحة غير موجودة"}, status=404)

    if not _charter_applies_to_employee(charter, employee, user):
        return Response({"success": False, "error": "هذه اللائحة لا تخصك"}, status=403)

    existing = CharterAcceptance._base_manager.filter(employee=employee, charter=charter).first()
    if existing:
        return Response({"success": True, "message": "تمت الموافقة مسبقاً"})

    ip = request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    CharterAcceptance._base_manager.create(
        employee=employee,
        charter=charter,
        ip_address=ip if ip else None,
        user_agent=user_agent[:500] if user_agent else '',
    )
    return Response({"success": True, "message": "تم تسجيل الموافقة بنجاح"})
