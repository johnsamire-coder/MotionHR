def _sync_policy_assignments(policy, company, assignment_type, branch_ids, department_ids):
    from attendance.models import AttendancePolicyAssignment
    AttendancePolicyAssignment._base_manager.filter(policy=policy).delete()

    if assignment_type == 'branch' and branch_ids:
        for b_id in branch_ids:
            AttendancePolicyAssignment._base_manager.create(
                company=company, policy=policy, assignment_type='branch', branch_id=b_id
            )
    elif assignment_type == 'department' and department_ids:
        for d_id in department_ids:
            AttendancePolicyAssignment._base_manager.create(
                company=company, policy=policy, assignment_type='department', department_id=d_id
            )
    else:
        AttendancePolicyAssignment._base_manager.create(
            company=company, policy=policy, assignment_type='company'
        )


"""
Phase 8: Employee Creation from Manager App
- Manager can create employee user directly from mobile
- Returns credentials for PDF + WhatsApp sharing
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
import logging
import re
from datetime import datetime, date
from employees.visibility import get_visible_employees_qs
from .models import LocationHistory
import random
import string
from core.username_generator import generate_employee_username

logger = logging.getLogger(__name__)

def _generate_username_from_names(first_name_en, last_name_en, company, phone="", national_id=""):
    """توليد يوزر ذكي: اسم + حرفين + آخر 4 من القومي"""
    full_name = f"{first_name_en or ''} {last_name_en or ''}".strip()
    if not full_name:
        full_name = "user"
    nid = national_id or phone or "1234"
    return generate_employee_username(full_name, nid)


User = get_user_model()

MANAGER_ROLES = {"super_admin", "company_admin", "manager", "hr_manager"}


def _check_manager(request):
    role = getattr(request.user, "role", None)
    if role not in MANAGER_ROLES and not request.user.is_superuser and not request.user.is_staff:
        return Response({"success": False, "error": "غير مصرح - يجب أن تكون مدير"}, status=status.HTTP_403_FORBIDDEN)
    return None


def _get_company(request):
    """Get company from user or employee profile"""
    company = getattr(request.user, "company", None)
    if company:
        return company
    try:
        emp = getattr(request.user, "employee_profile", None)
        if emp and getattr(emp, "company", None):
            return emp.company
    except Exception:
        pass
    # Fallback: try via Employee model using _base_manager (multi-tenant safe)
    try:
        from employees.models import Employee
        emp = Employee._base_manager.filter(user=request.user).select_related("company").first()
        if emp and getattr(emp, "company", None):
            return emp.company
    except Exception:
        pass
    return None


def _stringify(value):
    return "" if value is None else str(value)


def _date_string(value):
    return value.isoformat() if value else ""


def _boolish(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "نعم"}


def _int_or_none(value):
    if value in (None, "", "null", "None"):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _employee_display_name(employee):
    if not employee:
        return ""

    for attr in ("full_name_ar", "full_name_en", "full_name"):
        val = getattr(employee, attr, None)
        if val:
            val = str(val).strip()
            if val:
                return val

    parts = [
        getattr(employee, "first_name_ar", "") or "",
        getattr(employee, "middle_name_ar", "") or "",
        getattr(employee, "last_name_ar", "") or "",
    ]
    full_name = " ".join([p for p in parts if p]).strip()
    if full_name:
        return full_name

    user = getattr(employee, "user", None)
    if user:
        full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        if full_name:
            return full_name
        return getattr(user, "username", "") or ""

    return ""


def _serialize_employee_payload(employee):
    branch = getattr(employee, "branch", None)
    department = getattr(employee, "department", None)
    job_title = getattr(employee, "job_title", None)
    direct_manager = getattr(employee, "direct_manager", None)
    user = getattr(employee, "user", None)

    branch_name_ar = getattr(branch, "name_ar", "") or ""
    branch_name_en = getattr(branch, "name_en", "") or ""
    department_name_ar = getattr(department, "name_ar", "") or ""
    department_name_en = getattr(department, "name_en", "") or ""
    job_title_name_ar = (
        getattr(job_title, "name_ar", "")
        or getattr(job_title, "title", "")
        or getattr(job_title, "name", "")
        or ""
    )
    job_title_name_en = (
        getattr(job_title, "name_en", "")
        or getattr(job_title, "title_en", "")
        or ""
    )

    return {
        "id": employee.id,
        "company_id": getattr(employee, "company_id", None),

        "employee_code": getattr(employee, "employee_code", "") or "",
        "username": getattr(user, "username", "") or "",
        "user_role": getattr(user, "role", "") or "",

        "full_name": _employee_display_name(employee),
        "full_name_ar": _employee_display_name(employee),

        "first_name_ar": getattr(employee, "first_name_ar", "") or "",
        "middle_name_ar": getattr(employee, "middle_name_ar", "") or "",
        "last_name_ar": getattr(employee, "last_name_ar", "") or "",
        "first_name_en": getattr(employee, "first_name_en", "") or "",
        "last_name_en": getattr(employee, "last_name_en", "") or "",

        "phone": getattr(employee, "phone", "") or "",
        "phone2": getattr(employee, "phone2", "") or "",
        "email": getattr(employee, "email", "") or "",
        "national_id": getattr(employee, "national_id", "") or "",
        "birth_date": _date_string(getattr(employee, "birth_date", None)),
        "gender": getattr(employee, "gender", "") or "",
        "hire_date": _date_string(getattr(employee, "hire_date", None)),

        "branch_id": getattr(branch, "id", None),
        "branch": branch_name_ar,
        "branch_name_ar": branch_name_ar,
        "branch_name_en": branch_name_en,

        "department_id": getattr(department, "id", None),
        "department": department_name_ar,
        "department_name_ar": department_name_ar,
        "department_name_en": department_name_en,

        "job_title_id": getattr(job_title, "id", None),
        "job_title": job_title_name_ar,
        "job_title_name_ar": job_title_name_ar,
        "job_title_name_en": job_title_name_en,

        "direct_manager_id": getattr(direct_manager, "id", None),
        "direct_manager_name": _employee_display_name(direct_manager),

        "worker_type": getattr(employee, "worker_type", "office") or "office",
        "is_field_worker": bool(getattr(employee, "is_field_worker", False)),

        "basic_salary": float(getattr(employee, "basic_salary", 0) or 0),
        "currency": getattr(employee, "currency", "EGP") or "EGP",
        "salary_payment_method": getattr(employee, "salary_payment_method", "cash") or "cash",
        "bank_name": getattr(employee, "bank_name", "") or "",
        "bank_account": getattr(employee, "bank_account", "") or "",
        "iban": getattr(employee, "iban", "") or "",
        "instapay_phone": getattr(employee, "instapay_phone", "") or "",
        "wallet_phone": getattr(employee, "wallet_phone", "") or "",
        "wallet_provider": getattr(employee, "wallet_provider", "") or "",

        "has_insurance": bool(getattr(employee, "has_insurance", False)),
        "insurance_number": getattr(employee, "insurance_number", "") or "",

        "nationality": getattr(employee, "nationality", "") or "",
        "marital_status": getattr(employee, "marital_status", "single") or "single",
        "religion": getattr(employee, "religion", "") or "",
        "contract_type": getattr(employee, "contract_type", "permanent") or "permanent",
        "contract_end_date": _date_string(getattr(employee, "contract_end_date", None)),

        "address": getattr(employee, "address", "") or "",
        "city": getattr(employee, "city", "") or "",
        "country": str(getattr(employee, "country", "EG") or "EG"),

        "emergency_contact_name": getattr(employee, "emergency_contact_name", "") or "",
        "emergency_contact_relation": getattr(employee, "emergency_contact_relation", "") or "",
        "emergency_contact_phone": getattr(employee, "emergency_contact_phone", "") or "",

        "status": getattr(employee, "status", "") or "",
    }


def _normalize_religion_value(value):
    raw = str(value or "").strip().lower()
    mapping = {
        "": "",
        "muslim": "muslim",
        "مسلم": "muslim",
        "islam": "muslim",
        "christian": "christian",
        "مسيحي": "christian",
        "masihi": "christian",
        "other": "other",
        "أخرى": "other",
        "اخرى": "other",
    }
    if raw in mapping:
        return mapping[raw]
    return None


@api_view(["GET", "POST", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_departments(request, dept_id=None):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)
        from companies.models import Department, Branch

        if request.method == "POST":
            data = request.data
            name_ar = (data.get("name_ar") or "").strip()
            if not name_ar:
                return Response({"success": False, "error": "اسم القسم بالعربي مطلوب"}, status=400)

            branch_id = data.get("branch_id") or data.get("branch")
            branch_obj = None
            if branch_id:
                branch_obj = Branch._base_manager.filter(id=branch_id, company=company).first()

            dept = Department._base_manager.create(
                company=company,
                name_ar=name_ar,
                name_en=(data.get("name_en") or "").strip(),
                code=(data.get("code") or "").strip(),
                description=(data.get("description") or "").strip(),
                branch=branch_obj,
                is_active=True,
            )
            return Response({
                "success": True,
                "message": "تم إنشاء القسم بنجاح",
                "department": {
                    "id": dept.id,
                    "name_ar": dept.name_ar,
                    "name_en": dept.name_en or "",
                    "code": dept.code or "",
                    "branch_id": dept.branch_id,
                    "branch_name": dept.branch.name_ar if dept.branch else None,
                }
            }, status=201)

        elif request.method == "PUT":
            data = request.data
            target_id = dept_id or data.get("id") or request.GET.get("id")
            if not target_id:
                return Response({"success": False, "error": "معرف القسم مطلوب"}, status=400)

            try:
                dept = Department._base_manager.get(id=target_id, company=company)
            except Department.DoesNotExist:
                return Response({"success": False, "error": "القسم غير موجود"}, status=404)

            name_ar = (data.get("name_ar") or "").strip()
            if name_ar:
                dept.name_ar = name_ar
            if "name_en" in data:
                dept.name_en = (data.get("name_en") or "").strip()
            if "code" in data:
                dept.code = (data.get("code") or "").strip()
            if "description" in data:
                dept.description = (data.get("description") or "").strip()

            if "branch_id" in data or "branch" in data:
                b_id = data.get("branch_id") or data.get("branch")
                dept.branch = Branch._base_manager.filter(id=b_id, company=company).first() if b_id else None

            dept.save()
            return Response({
                "success": True,
                "message": "تم تعديل بيانات القسم بنجاح",
                "department": {
                    "id": dept.id,
                    "name_ar": dept.name_ar,
                    "name_en": dept.name_en or "",
                    "code": dept.code or "",
                    "branch_id": dept.branch_id,
                    "branch_name": dept.branch.name_ar if dept.branch else None,
                }
            })

        elif request.method == "DELETE":
            target_id = dept_id or request.data.get("id") or request.GET.get("id")
            if not target_id:
                return Response({"success": False, "error": "معرف القسم مطلوب"}, status=400)

            try:
                dept = Department._base_manager.get(id=target_id, company=company)
            except Department.DoesNotExist:
                return Response({"success": False, "error": "القسم غير موجود"}, status=404)

            from employees.models import Employee
            if Employee._base_manager.filter(department=dept, status="active").exists():
                return Response({"success": False, "error": "لا يمكن حذف هذا القسم لوجود موظفين نشطين مسجلين عليه"}, status=400)

            dept.delete()
            return Response({"success": True, "message": "تم حذف القسم بنجاح"})

        # GET
        branch_filter = request.GET.get("branch_id")
        depts = Department._base_manager.filter(company=company, is_active=True)
        if branch_filter:
            depts = depts.filter(branch_id=branch_filter)

        depts = depts.order_by("name_ar")
        data = [{
            "id": d.id,
            "name_ar": d.name_ar,
            "name_en": d.name_en or "",
            "code": d.code or "",
            "description": d.description or "",
            "branch_id": d.branch_id,
            "branch_name": d.branch.name_ar if d.branch else None,
        } for d in depts]
        return Response({"success": True, "departments": data, "count": len(data)})

    except Exception as e:
        logger.exception("manager_departments error")
        return Response({"success": False, "error": str(e)}, status=500)



@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_job_titles(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)
        from employees.models import JobTitle

        # POST - create new job title
        if request.method == "POST":
            data = request.data
            name_ar = (data.get("name_ar") or "").strip()
            if not name_ar:
                return Response({"success": False, "error": "اسم المسمى مطلوب"}, status=400)

            from companies.models import Branch, Department
            branch_id = data.get("branch_id") or data.get("branch")
            department_id = data.get("department_id") or data.get("department")

            branch_obj = None
            dept_obj = None
            if branch_id:
                branch_obj = Branch._base_manager.filter(id=branch_id, company=company).first()
            if department_id:
                dept_obj = Department._base_manager.filter(id=department_id, company=company).first()

            title = JobTitle._base_manager.create(
                company=company,
                name_ar=name_ar,
                name_en=(data.get("name_en") or "").strip(),
                description=(data.get("description") or "").strip(),
                branch=branch_obj,
                department=dept_obj,
                is_manager=bool(data.get("is_manager", False)),
                is_active=True,
            )
            return Response({
                "success": True,
                "message": "تم إنشاء المسمى الوظيفي بنجاح",
                "job_title": {
                    "id": title.id,
                    "name_ar": title.name_ar,
                    "name_en": title.name_en or "",
                    "branch_id": title.branch_id,
                    "department_id": title.department_id,
                    "is_manager": title.is_manager,
                }
            }, status=201)

        # GET - list job titles with filters
        titles = JobTitle._base_manager.filter(company=company, is_active=True).order_by("name_ar")

        # Optional filters
        branch_filter = request.GET.get("branch_id")
        dept_filter = request.GET.get("department_id")
        if branch_filter:
            titles = titles.filter(branch_id=branch_filter)
        if dept_filter:
            titles = titles.filter(department_id=dept_filter)

        data = [{
            "id": t.id,
            "name_ar": t.name_ar,
            "name_en": t.name_en or "",
            "branch_id": t.branch_id,
            "department_id": t.department_id,
            "is_manager": t.is_manager,
        } for t in titles]
        return Response({"success": True, "job_titles": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_job_titles error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employees_simple(request):
    """List employees with id + name for direct_manager dropdown"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)
        from employees.models import Employee
        # جلب كل الموظفين النشطين
        all_emps = get_visible_employees_qs(request.user).exclude(user=request.user).filter(status="active").select_related("job_title", "user", "department", "branch").order_by("first_name_ar")[:200]
        data = []
        for e in all_emps:
            user_role = getattr(e.user, "role", "employee") if e.user else "employee"
            is_manager = user_role in ("manager", "hr_manager", "company_admin", "super_admin")
            data.append({
                "id": e.id,
                "employee_code": e.employee_code,
                "full_name": getattr(e, "full_name_ar", f"{e.first_name_ar} {e.last_name_ar}"),
                "username": e.user.username if e.user else "",
                "phone": getattr(e, "phone", "") or "",
                "national_id": getattr(e, "national_id", "") or "",
                "job_title": getattr(e.job_title, "name_ar", "") if e.job_title else "",
                "department": getattr(e.department, "name_ar", "") if e.department else "",
                "department_id": e.department_id,
                "branch": getattr(e.branch, "name_ar", "") if e.branch else "",
                "branch_id": e.branch_id,
                "role": user_role,
                "is_manager": is_manager,
            })
        return Response({"success": True, "employees": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_employees_simple error")
        return Response({"success": False, "error": str(e)}, status=500)


def _generate_username(phone, first_name_ar, company_id, last_name_ar="", national_id=""):
    """توليد يوزر ذكي: اسم + حرفين + آخر 4 من القومي"""
    full_name = f"{first_name_ar or ''} {last_name_ar or ''}".strip()
    if not full_name:
        full_name = "user"
    nid = national_id or phone or "1234"
    return generate_employee_username(full_name, nid)


def _generate_password(phone=None):
    """Generate temporary password: Emp@ + 4 random digits + last 2 of phone"""
    suffix = ""
    if phone:
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 4:
            suffix = digits[-4:]
    if not suffix:
        suffix = ''.join(random.choices(string.digits, k=4))
    random_part = ''.join(random.choices(string.digits, k=2))
    return f"Emp@{suffix}{random_part}"



def _make_activation_link(user):
    """توليد رابط تفعيل آمن صالح 48 ساعة"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.conf import settings as django_settings

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    site_url = getattr(django_settings, 'SITE_URL', 'https://motion.jssolutions-eg.com')
    return f"{site_url}/password-reset-confirm/{uid}/{token}/"


def _make_wa_link(clean_phone, first_name_ar, username, activation_link):
    """توليد رابط واتساب بدون كلمة السر"""
    text = (
        f"مرحباً {first_name_ar}%0A"
        f"تم إنشاء حسابك في تطبيق MotionHR%0A%0A"
        f"اسم المستخدم: {username}%0A%0A"
        f"رابط تفعيل حسابك وتعيين كلمة المرور:%0A"
        f"{activation_link}%0A%0A"
        f"الرابط صالح 48 ساعة فقط%0A"
        f"بعد التفعيل حمّل التطبيق من هنا:%0A"
        f"https://jssolutions-eg.com/app/download"
    )
    return f"https://wa.me/{clean_phone}?text={text}"


@api_view(["POST"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_create_employee(request):
    """
    Create new employee user from manager app
    Expected JSON:
    {
        "first_name_ar": "احمد",
        "middle_name_ar": "محمد",
        "last_name_ar": "علي",
        "phone": "01012345678" (required for WhatsApp),
        "national_id": "29501011234567" (14 digits required),
        "birth_date": "1995-01-01" (YYYY-MM-DD),
        "gender": "male" or "female",
        "hire_date": "2026-07-17",
        "branch_id": 1,
        "department_id": 1,
        "job_title_id": 1,
        "basic_salary": 5000,
        "email": "optional",
        "direct_manager_id": optional,
        "username": optional (auto generated if not provided),
        "password": optional (auto generated if not provided),
        "employee_code": optional (auto generated)
    }
    Returns credentials for PDF sharing
    """
    err = _check_manager(request)
    if err:
        return err

    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة بحساب المدير"}, status=400)

        data = request.data

        # ── Required fields validation ──
        required_fields = ["first_name_ar", "last_name_ar", "phone", "national_id", "birth_date", "gender", "hire_date", "branch_id", "department_id", "job_title_id"]
        missing = [f for f in required_fields if not str(data.get(f, "")).strip()]
        if missing:
            return Response({"success": False, "error": f"الحقول المطلوبة ناقصة: {', '.join(missing)}"}, status=400)

        first_name_ar = str(data.get("first_name_ar", "")).strip()
        middle_name_ar = str(data.get("middle_name_ar", "")).strip()
        last_name_ar = str(data.get("last_name_ar", "")).strip()
        phone = str(data.get("phone", "")).strip()
        phone2 = str(data.get("phone2", "")).strip()
        national_id = str(data.get("national_id", "")).strip()
        birth_date_str = str(data.get("birth_date", "")).strip()
        gender = str(data.get("gender", "male")).strip().lower()
        hire_date_str = str(data.get("hire_date", "")).strip()
        email = str(data.get("email", "")).strip()
        basic_salary = data.get("basic_salary", 0)
        branch_id = data.get("branch_id")
        department_id = data.get("department_id")
        job_title_id = data.get("job_title_id")
        direct_manager_id = data.get("direct_manager_id")
        username_input = str(data.get("username", "")).strip()
        password_input = str(data.get("password", "")).strip()
        employee_code_input = ""

        # Optional extra fields
        first_name_en       = str(data.get("first_name_en", "")).strip()
        last_name_en        = str(data.get("last_name_en", "")).strip()
        nationality         = str(data.get("nationality", "")).strip()
        marital_status      = str(data.get("marital_status", "single")).strip()
        religion            = str(data.get("religion", "")).strip()
        contract_type       = str(data.get("contract_type", "permanent")).strip()
        contract_end_date_str = str(data.get("contract_end_date", "")).strip()
        address             = str(data.get("address", "")).strip()
        city                = str(data.get("city", "")).strip()
        country             = str(data.get("country", "EG")).strip()
        bank_name           = str(data.get("bank_name", "")).strip()
        bank_account        = str(data.get("bank_account", "")).strip()
        iban                = str(data.get("iban", "")).strip()
        has_insurance       = bool(data.get("has_insurance", False))
        insurance_number    = str(data.get("insurance_number", "")).strip()
        emergency_contact_name     = str(data.get("emergency_contact_name", "")).strip()
        emergency_contact_relation = str(data.get("emergency_contact_relation", "")).strip()
        emergency_contact_phone    = str(data.get("emergency_contact_phone", "")).strip()
        currency            = str(data.get("currency", "EGP")).strip()
        language            = str(data.get("language", "ar")).strip()

        # Payment method fields
        salary_payment_method      = str(data.get("salary_payment_method", "cash")).strip()
        instapay_phone             = str(data.get("instapay_phone", "")).strip()
        wallet_phone               = str(data.get("wallet_phone", "")).strip()
        wallet_provider            = str(data.get("wallet_provider", "")).strip()

        worker_type = str(data.get("worker_type", "office")).strip()
        if worker_type not in ("office", "field_free", "field_assigned"):
            return Response({"success": False, "error": "قيمة نوع الموظف غير صحيحة"}, status=400)

        # Validation details
        if len(first_name_ar) < 2:
            return Response({"success": False, "error": "الاسم الأول قصير جداً"}, status=400)
        if len(last_name_ar) < 2:
            return Response({"success": False, "error": "الاسم الأخير قصير جداً"}, status=400)

        if len(first_name_en) < 2:
            return Response({"success": False, "error": "الاسم الأول بالإنجليزية إجباري ويجب ألا يقل عن حرفين"}, status=400)

        if len(last_name_en) < 2:
            return Response({"success": False, "error": "الاسم الأخير بالإنجليزية إجباري ويجب ألا يقل عن حرفين"}, status=400)

        # Phone validation Egyptian format (basic)
        clean_phone = re.sub(r'\D', '', phone)
        if len(clean_phone) < 10 or len(clean_phone) > 15:
            return Response({"success": False, "error": "رقم الموبايل غير صحيح (يجب أن يكون 10-15 رقم)"}, status=400)

        # National ID validation
        if not national_id.isdigit() or len(national_id) != 14:
            return Response({"success": False, "error": "الرقم القومي يجب أن يكون 14 رقم"}, status=400)

        if gender not in ["male", "female"]:
            gender = "male"

        # Email optional validation
        if email and "@" not in email:
            return Response({"success": False, "error": "البريد الإلكتروني غير صحيح"}, status=400)

        # Dates parsing
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except Exception:
            return Response({"success": False, "error": "تاريخ الميلاد غير صحيح، استخدم YYYY-MM-DD"}, status=400)

        try:
            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
        except Exception:
            return Response({"success": False, "error": "تاريخ التعيين غير صحيح، استخدم YYYY-MM-DD"}, status=400)

        contract_end_date = None
        if contract_end_date_str:
            try:
                contract_end_date = datetime.strptime(contract_end_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        # Branch / Department / JobTitle belong to company
        from companies.models import Branch, Department
        from employees.models import Employee, JobTitle

        try:
            branch = Branch._base_manager.get(id=branch_id, company=company)
        except Branch.DoesNotExist:
            return Response({"success": False, "error": f"الفرع غير موجود أو لا ينتمي لشركتك (id={branch_id})"}, status=400)

        try:
            department = Department._base_manager.get(id=department_id, company=company)
        except Department.DoesNotExist:
            return Response({"success": False, "error": f"القسم غير موجود أو لا ينتمي لشركتك (id={department_id})"}, status=400)

        try:
            job_title = JobTitle._base_manager.get(id=job_title_id, company=company)
        except JobTitle.DoesNotExist:
            return Response({"success": False, "error": f"المسمى الوظيفي غير موجود (id={job_title_id})"}, status=400)

        direct_manager = None
        if direct_manager_id:
            try:
                direct_manager = Employee._base_manager.get(id=direct_manager_id, company=company)
            except Employee.DoesNotExist:
                return Response({"success": False, "error": "المدير المباشر غير موجود"}, status=400)

        # Check duplicate national_id in company
        if Employee._base_manager.filter(company=company, national_id=national_id).exists():
            return Response({"success": False, "error": "الرقم القومي مسجل لموظف آخر في نفس الشركة"}, status=400)

        # Check duplicate employee_code if provided
        if employee_code_input and Employee._base_manager.filter(company=company, employee_code=employee_code_input).exists():
            return Response({"success": False, "error": "الرقم الوظيفي موجود مسبقاً"}, status=400)

        # Username handling
        if username_input:
            if User._base_manager.filter(username=username_input).exists():
                return Response({"success": False, "error": f"اسم المستخدم '{username_input}' موجود مسبقاً"}, status=400)
            username = username_input
        else:
            username = _generate_username(phone, first_name_ar, company.id)

        # Password handling
        if password_input:
            if len(password_input) < 6:
                return Response({"success": False, "error": "كلمة المرور يجب أن تكون 6 أحرف على الأقل"}, status=400)
            password_plain = password_input
        else:
            password_plain = _generate_password(phone)

        # Basic salary parse
        try:
            basic_salary_val = float(basic_salary) if basic_salary else 0
        except Exception:
            basic_salary_val = 0

        # ── Transaction: Create User + Employee ──
        with transaction.atomic():
            # تحديد الدور بناءً على الدور الافتراضي للقسم
            user_role = "employee"
            if hasattr(department, 'default_role') and department.default_role:
                from accounts.permissions_models import UserRole
                _dept_role = department.default_role
            else:
                _dept_role = None

            # Create User
            user = User._base_manager.create(
                username=username,
                first_name=first_name_ar,
                last_name=last_name_ar,
                email=email if email else "",
                phone=phone,
                role=user_role,
                company=company,
                must_change_password=True,
                is_active=True,
            )
            user.set_password(password_plain)
            user.save()

            # تعيين الدور الافتراضي للقسم تلقائياً
            if _dept_role:
                from accounts.permissions_models import UserRole
                UserRole._base_manager.get_or_create(user=user, role=_dept_role)

            # Create Employee
            employee = Employee._base_manager.create(
                company=company,
                user=user,
                employee_code=employee_code_input if employee_code_input else "",  # auto-generated in save() if empty
                first_name_ar=first_name_ar,
                middle_name_ar=middle_name_ar if middle_name_ar else None,
                last_name_ar=last_name_ar,
                national_id=national_id,
                birth_date=birth_date,
                gender=gender,
                phone=phone,
                phone2=phone2 if phone2 else None,
                email=email if email else None,
                hire_date=hire_date,
                branch=branch,
                department=department,
                job_title=job_title,
                direct_manager=direct_manager,
                worker_type=worker_type,
                basic_salary=basic_salary_val,
                currency=currency if currency else "EGP",
                language=language if language in ("ar", "en") else "ar",
                nationality=nationality if nationality else "مصري",
                marital_status=marital_status if marital_status in ("single","married","divorced","widowed") else "single",
                religion=religion if religion in ("muslim","christian","other") else None,
                contract_type=contract_type if contract_type in ("permanent","temporary","training","freelance","part_time") else "permanent",
                contract_end_date=contract_end_date,
                address=address if address else None,
                city=city if city else None,
                bank_name=bank_name if bank_name else None,
                bank_account=bank_account if bank_account else None,
                iban=iban if iban else None,
                has_insurance=has_insurance,
                insurance_number=insurance_number if insurance_number else None,
                emergency_contact_name=emergency_contact_name if emergency_contact_name else None,
                emergency_contact_relation=emergency_contact_relation if emergency_contact_relation else None,
                emergency_contact_phone=emergency_contact_phone if emergency_contact_phone else None,
                first_name_en=first_name_en if first_name_en else None,
                last_name_en=last_name_en if last_name_en else None,
                country=country if country else "EG",
                salary_payment_method=salary_payment_method if salary_payment_method in ("cash","bank","instapay","wallet") else "cash",
                instapay_phone=instapay_phone if instapay_phone else None,
                wallet_phone=wallet_phone if wallet_phone else None,
                wallet_provider=wallet_provider if wallet_provider else None,
                status="active",
            )

            if hasattr(employee, "is_field_worker"):
                employee.is_field_worker = worker_type in ("field_free", "field_assigned")
                employee.save(update_fields=["is_field_worker"])

        # Prepare response with credentials for PDF
        full_name_ar = f"{first_name_ar} {middle_name_ar + ' ' if middle_name_ar else ''}{last_name_ar}".strip()

        return Response({
            "success": True,
            "message": f"تم إنشاء حساب الموظف {full_name_ar} بنجاح",
            "employee": {
                "id": employee.id,
                "employee_code": employee.employee_code,
                "full_name_ar": full_name_ar,
                "first_name_ar": first_name_ar,
                "last_name_ar": last_name_ar,
                "phone": phone,
                "phone2": phone2,
                "email": email,
                "national_id": national_id,
                "birth_date": str(birth_date),
                "gender": gender,
                "hire_date": str(hire_date),
                "branch": branch.name_ar,
                "branch_id": branch.id,
                "department": department.name_ar,
                "department_id": department.id,
                "job_title": job_title.name_ar,
                "job_title_id": job_title.id,
                "direct_manager": direct_manager.full_name_ar if direct_manager else None,
                "direct_manager_id": direct_manager.id if direct_manager else None,
                "worker_type": getattr(employee, "worker_type", "office"),
                "is_field_worker": bool(getattr(employee, "is_field_worker", False)),
                "basic_salary": float(employee.basic_salary or 0),
                "currency": employee.currency,
                "country": str(getattr(employee, "country", "EG")),
                "salary_payment_method": getattr(employee, "salary_payment_method", "none"),
                "instapay_phone": getattr(employee, "instapay_phone", ""),
                "wallet_phone": getattr(employee, "wallet_phone", ""),
                "wallet_provider": getattr(employee, "wallet_provider", ""),
                "bank_name": getattr(employee, "bank_name", ""),
                "bank_account": getattr(employee, "bank_account", ""),
                "iban": getattr(employee, "iban", ""),
                "has_insurance": getattr(employee, "has_insurance", False),
                "insurance_number": getattr(employee, "insurance_number", ""),
                "emergency_contact_name": getattr(employee, "emergency_contact_name", ""),
                "emergency_contact_phone": getattr(employee, "emergency_contact_phone", ""),
                "emergency_contact_relation": getattr(employee, "emergency_contact_relation", ""),
                "address": getattr(employee, "address", ""),
                "city": getattr(employee, "city", ""),
                "nationality": getattr(employee, "nationality", ""),
                "marital_status": getattr(employee, "marital_status", "single"),
                "first_name_en": getattr(employee, "first_name_en", ""),
                "last_name_en": getattr(employee, "last_name_en", ""),
                "company": company.name_ar,
            },
            "credentials": {
                "username": username,
                "login_url": "https://jssolutions-eg.com",
                "must_change_password": True,
                "activation_link": _make_activation_link(user),
                "expires_hours": 48,
            },
            "whatsapp": {
                "phone": phone,
                "clean_phone": clean_phone,
                "wa_link": _make_wa_link(clean_phone, first_name_ar, username, _make_activation_link(user)),
                "download_link": "https://jssolutions-eg.com/app/download",
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.exception("manager_create_employee error")
        return Response({"success": False, "error": f"خطأ في إنشاء الموظف: {str(e)}"}, status=500)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manager_reset_employee_password(request, employee_id):
    try:
        from employees.models import Employee
        target_employee = Employee._base_manager.select_related("user", "company").filter(id=employee_id).first()
        if not target_employee:
            return Response(
                {"success": False, "error": "الموظف غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )

        requester_company = _get_company(request)

        allowed_groups = {"company_admin", "hr_manager", "super_admin"}
        is_allowed = request.user.is_superuser or (request.user.role in allowed_groups)

        if not is_allowed:
            return Response(
                {"success": False, "error": "غير مصرح لك بإعادة تعيين كلمة المرور"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_superuser:
            if not requester_company:
                return Response(
                    {"success": False, "error": "تعذر تحديد شركة المستخدم الحالي"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if target_employee.company_id != requester_company.id:
                return Response(
                    {"success": False, "error": "لا يمكنك إدارة موظف من شركة أخرى"},
                    status=status.HTTP_403_FORBIDDEN
                )

        if not getattr(target_employee, "user", None):
            return Response(
                {"success": False, "error": "هذا الموظف لا يملك حساب دخول"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # توليد رابط تفعيل جديد بدل إعادة تعيين كلمة السر
        digits = ''.join(random.choices(string.digits, k=6))
        suffix = ''.join(random.choices(string.ascii_uppercase, k=2))
        temp_pass = f"Rx@{digits}{suffix}"
        target_employee.user.set_password(temp_pass)
        target_employee.user.must_change_password = True
        target_employee.user.save()

        full_name = (
            getattr(target_employee, "full_name_ar", "")
            or getattr(target_employee, "full_name_en", "")
            or getattr(target_employee, "full_name", "")
            or target_employee.user.username
        )
        phone = getattr(target_employee, "phone", "") or ""
        clean_phone = ''.join(c for c in phone if c.isdigit())
        first_name_ar = getattr(target_employee, "first_name_ar", "") or full_name
        activation_link = _make_activation_link(target_employee.user)

        return Response({
            "success": True,
            "message": f"تم إرسال رابط تفعيل جديد لـ {full_name}",
            "employee": {
                "id": target_employee.id,
                "employee_code": getattr(target_employee, "employee_code", ""),
                "full_name": full_name,
                "phone": phone,
            },
            "credentials": {
                "username": target_employee.user.username,
                "login_url": "https://jssolutions-eg.com",
                "must_change_password": True,
                "activation_link": activation_link,
                "expires_hours": 48,
            },
            "whatsapp": {
                "phone": phone,
                "clean_phone": clean_phone,
                "wa_link": _make_wa_link(clean_phone, first_name_ar, target_employee.user.username, activation_link),
                "download_link": "https://jssolutions-eg.com/app/download",
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_reset_employee_password error")
        return Response(
            {"success": False, "error": f"خطأ في إعادة تعيين كلمة المرور: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT", "PATCH"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_update_employee(request, employee_id):
    try:
        from companies.models import Branch, Department
        from employees.models import Employee, JobTitle

        target_employee = Employee._base_manager.select_related(
            "user", "company", "branch", "department", "job_title", "direct_manager__user"
        ).filter(id=employee_id).first()

        if not target_employee:
            return Response(
                {"success": False, "error": "الموظف غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )

        requester_company = _get_company(request)

        allowed_groups = {"company_admin", "hr_manager", "super_admin"}
        is_allowed = request.user.is_superuser or (getattr(request.user, "role", None) in allowed_groups)

        if not is_allowed:
            return Response(
                {"success": False, "error": "غير مصرح لك بتعديل بيانات الموظف"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_superuser:
            if not requester_company:
                return Response(
                    {"success": False, "error": "تعذر تحديد شركة المستخدم الحالي"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if target_employee.company_id != requester_company.id:
                return Response(
                    {"success": False, "error": "لا يمكنك تعديل موظف من شركة أخرى"},
                    status=status.HTTP_403_FORBIDDEN
                )

        company = target_employee.company
        data = request.data

        current_branch = getattr(target_employee, "branch", None)
        current_department = getattr(target_employee, "department", None)
        current_job_title = getattr(target_employee, "job_title", None)
        current_direct_manager = getattr(target_employee, "direct_manager", None)

        first_name_ar = str(data.get("first_name_ar", getattr(target_employee, "first_name_ar", "") or "")).strip()
        middle_name_ar = str(data.get("middle_name_ar", getattr(target_employee, "middle_name_ar", "") or "")).strip()
        last_name_ar = str(data.get("last_name_ar", getattr(target_employee, "last_name_ar", "") or "")).strip()
        first_name_en = str(data.get("first_name_en", getattr(target_employee, "first_name_en", "") or "")).strip()
        last_name_en = str(data.get("last_name_en", getattr(target_employee, "last_name_en", "") or "")).strip()

        phone = str(data.get("phone", getattr(target_employee, "phone", "") or "")).strip()
        phone2 = str(data.get("phone2", getattr(target_employee, "phone2", "") or "")).strip()
        email = str(data.get("email", getattr(target_employee, "email", "") or "")).strip()
        national_id = str(data.get("national_id", getattr(target_employee, "national_id", "") or "")).strip()

        birth_date_default = getattr(target_employee, "birth_date", None)
        hire_date_default = getattr(target_employee, "hire_date", None)
        contract_end_date_default = getattr(target_employee, "contract_end_date", None)

        birth_date_str = str(data.get("birth_date", birth_date_default.isoformat() if birth_date_default else "") or "").strip()
        hire_date_str = str(data.get("hire_date", hire_date_default.isoformat() if hire_date_default else "") or "").strip()

        gender = str(data.get("gender", getattr(target_employee, "gender", "male") or "male")).strip().lower()
        marital_status = str(data.get("marital_status", getattr(target_employee, "marital_status", "single") or "single")).strip().lower()
        religion_raw = str(data.get("religion", getattr(target_employee, "religion", "") or "")).strip()
        religion = _normalize_religion_value(religion_raw)

        branch_id = data.get("branch_id", getattr(current_branch, "id", None))
        department_id = data.get("department_id", getattr(current_department, "id", None))
        job_title_id = data.get("job_title_id", getattr(current_job_title, "id", None))
        direct_manager_id = data.get("direct_manager_id", getattr(current_direct_manager, "id", None))

        worker_type = str(data.get("worker_type", getattr(target_employee, "worker_type", "office") or "office")).strip()
        contract_type = str(data.get("contract_type", getattr(target_employee, "contract_type", "permanent") or "permanent")).strip()
        contract_end_date_str = str(data.get("contract_end_date", contract_end_date_default.isoformat() if contract_end_date_default else "") or "").strip()

        basic_salary_raw = data.get("basic_salary", getattr(target_employee, "basic_salary", 0) or 0)
        salary_payment_method = str(
            data.get("salary_payment_method", getattr(target_employee, "salary_payment_method", "cash") or "cash")
        ).strip().lower()

        bank_name = str(data.get("bank_name", getattr(target_employee, "bank_name", "") or "")).strip()
        bank_account = str(data.get("bank_account", getattr(target_employee, "bank_account", "") or "")).strip()
        iban = str(data.get("iban", getattr(target_employee, "iban", "") or "")).strip()
        instapay_phone = str(data.get("instapay_phone", getattr(target_employee, "instapay_phone", "") or "")).strip()
        wallet_phone = str(data.get("wallet_phone", getattr(target_employee, "wallet_phone", "") or "")).strip()
        wallet_provider = str(data.get("wallet_provider", getattr(target_employee, "wallet_provider", "") or "")).strip()

        has_insurance_raw = data.get("has_insurance", getattr(target_employee, "has_insurance", False))
        if isinstance(has_insurance_raw, bool):
            has_insurance = has_insurance_raw
        else:
            has_insurance = str(has_insurance_raw).strip().lower() in {"1", "true", "yes", "on", "نعم"}

        insurance_number = str(data.get("insurance_number", getattr(target_employee, "insurance_number", "") or "")).strip()

        nationality = str(data.get("nationality", getattr(target_employee, "nationality", "") or "")).strip()
        address = str(data.get("address", getattr(target_employee, "address", "") or "")).strip()
        city = str(data.get("city", getattr(target_employee, "city", "") or "")).strip()
        country = str(data.get("country", getattr(target_employee, "country", "EG") or "EG")).strip()
        currency = str(data.get("currency", getattr(target_employee, "currency", "EGP") or "EGP")).strip()
        language = str(data.get("language", getattr(target_employee, "language", "ar") or "ar")).strip()

        if len(first_name_ar) < 2:
            return Response({"success": False, "error": "الاسم الأول قصير جداً"}, status=400)

        if len(last_name_ar) < 2:
            return Response({"success": False, "error": "الاسم الأخير قصير جداً"}, status=400)

        if len(first_name_en) < 2:
            return Response({"success": False, "error": "الاسم الأول بالإنجليزية إجباري ويجب ألا يقل عن حرفين"}, status=400)

        if len(last_name_en) < 2:
            return Response({"success": False, "error": "الاسم الأخير بالإنجليزية إجباري ويجب ألا يقل عن حرفين"}, status=400)

        clean_phone = re.sub(r"\D", "", phone)
        if len(clean_phone) < 10 or len(clean_phone) > 15:
            return Response({"success": False, "error": "رقم الموبايل غير صحيح (يجب أن يكون 10-15 رقم)"}, status=400)

        if not national_id.isdigit() or len(national_id) != 14:
            return Response({"success": False, "error": "الرقم القومي يجب أن يكون 14 رقم"}, status=400)

        if email and "@" not in email:
            return Response({"success": False, "error": "البريد الإلكتروني غير صحيح"}, status=400)

        if gender not in ("male", "female"):
            gender = "male"

        if marital_status not in ("single", "married", "divorced", "widowed"):
            return Response({"success": False, "error": "الحالة الاجتماعية غير صحيحة"}, status=400)

        if religion is None:
            return Response({"success": False, "error": "قيمة الديانة غير صحيحة"}, status=400)

        if worker_type not in ("office", "field_free", "field_assigned"):
            return Response({"success": False, "error": "قيمة نوع الموظف غير صحيحة"}, status=400)

        if contract_type not in ("permanent", "temporary", "training", "freelance", "part_time"):
            return Response({"success": False, "error": "نوع العقد غير صحيح"}, status=400)

        if salary_payment_method not in ("cash", "bank", "instapay", "wallet"):
            return Response({"success": False, "error": "طريقة القبض غير صحيحة"}, status=400)

        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except Exception:
            return Response({"success": False, "error": "تاريخ الميلاد غير صحيح، استخدم YYYY-MM-DD"}, status=400)

        try:
            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
        except Exception:
            return Response({"success": False, "error": "تاريخ التعيين غير صحيح، استخدم YYYY-MM-DD"}, status=400)

        contract_end_date = None
        if contract_end_date_str:
            try:
                contract_end_date = datetime.strptime(contract_end_date_str, "%Y-%m-%d").date()
            except Exception:
                return Response({"success": False, "error": "تاريخ نهاية العقد غير صحيح، استخدم YYYY-MM-DD"}, status=400)

        try:
            basic_salary_val = float(basic_salary_raw) if str(basic_salary_raw).strip() else 0
        except Exception:
            return Response({"success": False, "error": "الراتب الأساسي غير صحيح"}, status=400)

        try:
            branch_id = int(branch_id)
            department_id = int(department_id)
            job_title_id = int(job_title_id)
        except Exception:
            return Response({"success": False, "error": "الفرع والقسم والمسمى الوظيفي مطلوبون"}, status=400)

        try:
            branch = Branch._base_manager.get(id=branch_id, company=company)
        except Branch.DoesNotExist:
            return Response({"success": False, "error": f"الفرع غير موجود أو لا ينتمي لشركتك (id={branch_id})"}, status=400)

        try:
            department = Department._base_manager.get(id=department_id, company=company)
        except Department.DoesNotExist:
            return Response({"success": False, "error": f"القسم غير موجود أو لا ينتمي لشركتك (id={department_id})"}, status=400)

        try:
            job_title = JobTitle._base_manager.get(id=job_title_id, company=company)
        except JobTitle.DoesNotExist:
            return Response({"success": False, "error": f"المسمى الوظيفي غير موجود (id={job_title_id})"}, status=400)

        direct_manager = None
        if direct_manager_id not in (None, "", "null"):
            try:
                direct_manager_id = int(direct_manager_id)
                direct_manager = Employee._base_manager.get(id=direct_manager_id, company=company)
            except Exception:
                return Response({"success": False, "error": "المدير المباشر غير موجود"}, status=400)

            if direct_manager.id == target_employee.id:
                return Response({"success": False, "error": "لا يمكن أن يكون الموظف مديراً مباشراً لنفسه"}, status=400)

        if Employee._base_manager.filter(company=company, national_id=national_id).exclude(id=target_employee.id).exists():
            return Response({"success": False, "error": "الرقم القومي مسجل لموظف آخر في نفس الشركة"}, status=400)

        if Employee._base_manager.filter(company=company, phone=phone).exclude(id=target_employee.id).exists():
            return Response({"success": False, "error": "رقم الموبايل مستخدم بالفعل داخل نفس الشركة"}, status=400)

        with transaction.atomic():
            target_employee.first_name_ar = first_name_ar
            target_employee.middle_name_ar = middle_name_ar or None
            target_employee.last_name_ar = last_name_ar
            target_employee.first_name_en = first_name_en
            target_employee.last_name_en = last_name_en

            target_employee.phone = phone
            if hasattr(target_employee, "phone2"):
                target_employee.phone2 = phone2 or None
            target_employee.email = email or None
            target_employee.national_id = national_id
            target_employee.birth_date = birth_date
            target_employee.gender = gender
            target_employee.hire_date = hire_date

            target_employee.branch = branch
            target_employee.department = department
            target_employee.job_title = job_title
            target_employee.direct_manager = direct_manager

            if hasattr(target_employee, "worker_type"):
                target_employee.worker_type = worker_type
            if hasattr(target_employee, "is_field_worker"):
                target_employee.is_field_worker = worker_type in ("field_free", "field_assigned")

            if hasattr(target_employee, "basic_salary"):
                target_employee.basic_salary = basic_salary_val
            if hasattr(target_employee, "currency"):
                target_employee.currency = currency or "EGP"
            if hasattr(target_employee, "language"):
                target_employee.language = language if language in ("ar", "en") else "ar"

            if hasattr(target_employee, "nationality"):
                target_employee.nationality = nationality or "مصري"
            if hasattr(target_employee, "marital_status"):
                target_employee.marital_status = marital_status
            if hasattr(target_employee, "religion"):
                target_employee.religion = religion or None

            if hasattr(target_employee, "contract_type"):
                target_employee.contract_type = contract_type
            if hasattr(target_employee, "contract_end_date"):
                target_employee.contract_end_date = contract_end_date

            if hasattr(target_employee, "address"):
                target_employee.address = address or None
            if hasattr(target_employee, "city"):
                target_employee.city = city or None
            if hasattr(target_employee, "country"):
                target_employee.country = country or "EG"

            if hasattr(target_employee, "salary_payment_method"):
                target_employee.salary_payment_method = salary_payment_method
            if hasattr(target_employee, "bank_name"):
                target_employee.bank_name = bank_name or None
            if hasattr(target_employee, "bank_account"):
                target_employee.bank_account = bank_account or None
            if hasattr(target_employee, "iban"):
                target_employee.iban = iban or None
            if hasattr(target_employee, "instapay_phone"):
                target_employee.instapay_phone = instapay_phone or None
            if hasattr(target_employee, "wallet_phone"):
                target_employee.wallet_phone = wallet_phone or None
            if hasattr(target_employee, "wallet_provider"):
                target_employee.wallet_provider = wallet_provider or None

            if hasattr(target_employee, "has_insurance"):
                target_employee.has_insurance = has_insurance
            if hasattr(target_employee, "insurance_number"):
                target_employee.insurance_number = insurance_number or None

            target_employee.save()

            if getattr(target_employee, "user", None):
                user = target_employee.user
                if hasattr(user, "first_name"):
                    user.first_name = first_name_ar
                if hasattr(user, "last_name"):
                    user.last_name = last_name_ar
                if hasattr(user, "email"):
                    user.email = email or ""
                if hasattr(user, "phone"):
                    user.phone = phone
                user.save()

        return Response({
            "success": True,
            "message": "تم حفظ التعديلات بنجاح",
            "employee_id": target_employee.id,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_update_employee error")
        return Response(
            {"success": False, "error": f"خطأ في تحديث بيانات الموظف: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_company_info(request):
    """جلب بيانات الشركة الكاملة + اللوجو"""
    try:
        from employees.models import Employee
        requester_employee = Employee._base_manager.select_related("company").filter(user=request.user).first()
        company = getattr(request.user, "company", None)

        if requester_employee and requester_employee.company:
            company = requester_employee.company

        if not company:
            return Response(
                {"success": False, "error": "المستخدم غير مرتبط بشركة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logo_url = ""
        if hasattr(company, "logo") and company.logo:
            try:
                logo_url = request.build_absolute_uri(company.logo.url)
            except Exception:
                logo_url = ""

        branches_count = 0
        departments_count = 0
        employees_count = 0
        try:
            from companies.models import Branch, Department
            branches_count = Branch._base_manager.filter(company=company).count()
            departments_count = Department._base_manager.filter(company=company).count()
            employees_count = Employee._base_manager.filter(company=company).count()
        except Exception:
            pass

        data = {
            "success": True,
            "company": {
                "id": company.id,
                "name_ar": getattr(company, "name_ar", "") or getattr(company, "name", ""),
                "name_en": getattr(company, "name_en", ""),
                "logo_url": logo_url,
                "phone": getattr(company, "phone", ""),
                "email": getattr(company, "email", ""),
                "website": getattr(company, "website", ""),
                "address": getattr(company, "address", ""),
                "commercial_register": getattr(company, "commercial_register", ""),
                "tax_number": getattr(company, "tax_number", ""),
                "industry": getattr(company, "industry", ""),
                "founded_date": str(getattr(company, "founded_date", "") or ""),
                "stats": {
                    "branches": branches_count,
                    "departments": departments_count,
                    "employees": employees_count,
                },
            }
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_company_info error")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return Response(
            {"success": False, "error": f"خطأ: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manager_transfer_employee(request, employee_id):
    from employees.models import Employee
    """نقل موظف: تغيير مدير / إدارة / فرع"""
    try:
        target_employee = Employee._base_manager.select_related("user", "company").filter(id=employee_id).first()
        if not target_employee:
            return Response(
                {"success": False, "error": "الموظف غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )

        requester_employee = Employee._base_manager.select_related("company").filter(user=request.user).first()

        allowed_groups = {"company_admin", "hr_manager", "super_admin"}
        is_allowed = request.user.is_superuser or (request.user.role in allowed_groups)

        if not is_allowed:
            return Response(
                {"success": False, "error": "غير مصرح"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_superuser:
            if not requester_employee or target_employee.company_id != requester_employee.company_id:
                return Response(
                    {"success": False, "error": "لا يمكنك نقل موظف من شركة أخرى"},
                    status=status.HTTP_403_FORBIDDEN
                )

        new_manager_id = request.data.get("new_manager_id")
        new_branch_id = request.data.get("new_branch_id")
        new_department_id = request.data.get("new_department_id")
        new_job_title_id = request.data.get("new_job_title_id")
        transfer_reason = (request.data.get("reason") or "").strip()

        changes = []
        update_fields = []

        if new_manager_id is not None:
            if new_manager_id == 0 or new_manager_id == "":
                if hasattr(target_employee, "direct_manager"):
                    target_employee.direct_manager = None
                    update_fields.append("direct_manager")
                    changes.append("إزالة المدير المباشر")
            else:
                new_mgr = Employee._base_manager.filter(
                    id=new_manager_id,
                    company_id=target_employee.company_id
                ).first()
                if not new_mgr:
                    return Response(
                        {"success": False, "error": "المدير الجديد غير موجود"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if new_mgr.id == target_employee.id:
                    return Response(
                        {"success": False, "error": "لا يمكن أن يكون الموظف مديراً لنفسه"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if hasattr(target_employee, "direct_manager"):
                    old_name = target_employee.direct_manager.full_name_ar if target_employee.direct_manager else "لا يوجد"
                    target_employee.direct_manager = new_mgr
                    update_fields.append("direct_manager")
                    changes.append(f"المدير المباشر: {old_name} → {new_mgr.full_name_ar}")

        if new_branch_id:
            try:
                from attendance.models import Branch
                new_branch = Branch._base_manager.filter(
                    id=new_branch_id,
                    company_id=target_employee.company_id
                ).first()
                if not new_branch:
                    return Response(
                        {"success": False, "error": "الفرع غير موجود"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if hasattr(target_employee, "branch"):
                    old_name = target_employee.branch.name_ar if target_employee.branch else "لا يوجد"
                    target_employee.branch = new_branch
                    update_fields.append("branch")
                    changes.append(f"الفرع: {old_name} → {new_branch.name_ar}")
            except Exception as e:
                pass

        if new_department_id:
            try:
                from attendance.models import Department
                new_dept = Department._base_manager.filter(
                    id=new_department_id,
                    company_id=target_employee.company_id
                ).first()
                if not new_dept:
                    return Response(
                        {"success": False, "error": "الإدارة غير موجودة"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if hasattr(target_employee, "department"):
                    old_name = target_employee.department.name_ar if target_employee.department else "لا يوجد"
                    target_employee.department = new_dept
                    update_fields.append("department")
                    changes.append(f"الإدارة: {old_name} → {new_dept.name_ar}")

                    # تغيير الدور تلقائي لما القسم يتغيّر
                    try:
                        from accounts.permissions_models import UserRole, CustomRole
                        user = target_employee.user
                        if new_dept.default_role:
                            # امسح الأدوار القديمة المرتبطة بأقسام تانية
                            old_dept_roles = CustomRole._base_manager.filter(
                                company=target_employee.company
                            ).values_list('id', flat=True)
                            UserRole._base_manager.filter(
                                user=user,
                                role_id__in=old_dept_roles
                            ).delete()
                            # ضيف الدور الجديد
                            UserRole._base_manager.get_or_create(
                                user=user,
                                role=new_dept.default_role
                            )
                            changes.append(f"الدور: تغيّر تلقائياً لـ {new_dept.default_role.name}")
                    except Exception:
                        pass
            except Exception as e:
                pass

        if new_job_title_id:
            try:
                from attendance.models import JobTitle
                new_jt = JobTitle._base_manager.filter(
                    id=new_job_title_id,
                    company_id=target_employee.company_id
                ).first()
                if not new_jt:
                    return Response(
                        {"success": False, "error": "المسمى الوظيفي غير موجود"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if hasattr(target_employee, "job_title"):
                    old_name = target_employee.job_title.name_ar if target_employee.job_title else "لا يوجد"
                    target_employee.job_title = new_jt
                    update_fields.append("job_title")
                    changes.append(f"المسمى: {old_name} → {new_jt.name_ar}")
            except Exception as e:
                pass

        if not changes:
            return Response(
                {"success": False, "error": "لم يتم اختيار أي تغييرات"},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_employee.save(update_fields=update_fields)

        return Response({
            "success": True,
            "message": f"تم نقل الموظف {target_employee.full_name_ar} بنجاح",
            "changes": changes,
            "reason": transfer_reason,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_transfer_employee error")
        return Response(
            {"success": False, "error": f"خطأ: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_organization_tree(request):
    """الهيكل التنظيمي: فروع > أقسام > مديرون > موظفون"""
    try:
        from employees.models import Employee
        from companies.models import Branch, Department

        company = getattr(request.user, "company", None)
        if not company:
            return Response(
                {"success": False, "error": "المستخدم غير مرتبط بشركة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        employees_qs = Employee._base_manager.filter(
            company=company,
            status="active"
        ).select_related("user", "department", "branch", "job_title", "direct_manager")

        branches_data = []

        for branch in Branch._base_manager.filter(
            company=company,
            is_active=True
        ).order_by("name_ar"):

            branch_employees = employees_qs.filter(branch=branch)
            departments_data = []

            for dept in Department._base_manager.filter(
                company=company,
                is_active=True
            ).order_by("name_ar"):

                dept_employees = branch_employees.filter(department=dept)
                if not dept_employees.exists():
                    continue

                managers_data = []
                manager_ids = set()

                for emp in dept_employees:
                    is_manager_role = getattr(emp.user, "role", "") in [
                        "manager", "company_admin", "hr_manager", "super_admin"
                    ]
                    has_subordinates = dept_employees.filter(
                        direct_manager=emp
                    ).exists()

                    if is_manager_role or has_subordinates:
                        manager_ids.add(emp.id)

                for manager_id in sorted(manager_ids):
                    manager = dept_employees.filter(id=manager_id).first()
                    if not manager:
                        continue

                    subordinates = []
                    for emp in dept_employees.filter(
                        direct_manager=manager
                    ).order_by("first_name_ar", "last_name_ar"):
                        subordinates.append({
                            "id": emp.id,
                            "name": f"{emp.first_name_ar or ''} {emp.last_name_ar or ''}".strip(),
                            "employee_code": emp.employee_code or "",
                            "job_title": manager.job_title.name_ar if False else (
                                emp.job_title.name_ar if emp.job_title else ""
                            ),
                            "status": emp.status or "",
                        })

                    managers_data.append({
                        "id": manager.id,
                        "name": f"{manager.first_name_ar or ''} {manager.last_name_ar or ''}".strip(),
                        "employee_code": manager.employee_code or "",
                        "job_title": manager.job_title.name_ar if manager.job_title else "",
                        "subordinates": subordinates,
                    })

                departments_data.append({
                    "id": dept.id,
                    "name": dept.name_ar,
                    "managers_count": len(managers_data),
                    "employees_count": dept_employees.count(),
                    "managers": managers_data,
                })

            branches_data.append({
                "id": branch.id,
                "name": branch.name_ar,
                "address": branch.address or "",
                "departments_count": len(departments_data),
                "employees_count": branch_employees.count(),
                "departments": departments_data,
            })

        return Response({
            "success": True,
            "company": {
                "id": company.id,
                "name": company.name_ar or company.name_en or "",
                "total_employees": employees_qs.count(),
            },
            "branches": branches_data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_organization_tree error")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_save_location(request):
    """يستقبل موقع الموظف ويخزنه (كل ساعة = 8 نقاط في الشيفت)"""
    try:
        employee = request.user.employee_profile
        company = employee.company

        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        accuracy = request.data.get('accuracy')
        recorded_at_str = request.data.get('recorded_at')
        shift_date_str = request.data.get('shift_date')
        address = request.data.get('address', '')

        if not lat or not lng:
            return Response({'success': False, 'error': 'الإحداثيات مطلوبة'}, status=400)

        shift_date = date.fromisoformat(shift_date_str) if shift_date_str else date.today()

        if recorded_at_str:
            from django.utils.dateparse import parse_datetime
            recorded_at = parse_datetime(recorded_at_str)
            if recorded_at and timezone.is_naive(recorded_at):
                recorded_at = timezone.make_aware(recorded_at)
        else:
            recorded_at = timezone.now()

        # عدد النقاط الحالية في هذا اليوم
        point_index = LocationHistory._base_manager.filter(
            employee=employee,
            shift_date=shift_date
        ).count()

        # حد أقصى 24 نقطة في اليوم
        if point_index >= 24:
            return Response({'success': True, 'message': 'تم الوصول للحد الأقصى من النقاط'})

        loc = LocationHistory._base_manager.create(
            company=employee.company,
            employee=employee,
            latitude=lat,
            longitude=lng,
            accuracy=accuracy,
            recorded_at=recorded_at,
            shift_date=shift_date,
            point_index=point_index,
            address=address,
        )

        from attendance.models import LocationLog
        live_log = LocationLog._base_manager.create(
            company=employee.company,
            employee=employee,
            timestamp=recorded_at,
            latitude=lat,
            longitude=lng,
            accuracy=accuracy if accuracy not in [None, ''] else None,
            speed=request.data.get('speed') or None,
            battery_level=request.data.get('battery_level') or None,
            address=address or '',
        )

        return Response({
            'success': True,
            'message': 'تم حفظ الموقع',
            'point_index': point_index,
            'id': loc.id,
            'live_log_id': live_log.id,
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_get_location_report(request):
    """المدير يشوف تقرير مواقع موظف في يوم معين"""
    try:
        manager_employee = request.user.employee_profile
        company = manager_employee.company

        employee_id = request.GET.get('employee_id')
        shift_date_str = request.GET.get('shift_date')

        if not employee_id or not shift_date_str:
            return Response({'success': False, 'error': 'employee_id و shift_date مطلوبان'}, status=400)

        shift_date = date.fromisoformat(shift_date_str)

        from employees.models import Employee
        try:
            employee = Employee._base_manager.get(id=employee_id, company=company)
        except Employee.DoesNotExist:
            return Response({'success': False, 'error': 'الموظف غير موجود'}, status=404)

        locations = LocationHistory._base_manager.filter(
            employee=employee,
            shift_date=shift_date,
        ).order_by('recorded_at')

        points = []
        for loc in locations:
            points.append({
                'id': loc.id,
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'accuracy': loc.accuracy,
                'recorded_at': loc.recorded_at.strftime('%I:%M %p') if loc.recorded_at else '',
                'point_index': loc.point_index,
                'address': loc.address,
            })

        return Response({
            'success': True,
            'employee': {
                'id': employee.id,
                'name': f"{employee.first_name_ar or ''} {employee.last_name_ar or ''}".strip(),
            },
            'shift_date': shift_date_str,
            'total_points': len(points),
            'points': points,
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ── UPDATE COMPANY INFO ──
@api_view(['PATCH', 'PUT'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_update_company_info(request):
    """تعديل بيانات الشركة (company_admin / super_admin فقط)"""
    try:
        role = getattr(request.user, 'role', '')
        if role not in ['super_admin', 'company_admin']:
            return Response({'success': False, 'error': 'غير مصرح لك بتعديل بيانات الشركة'}, status=403)

        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'success': False, 'error': 'المستخدم غير مرتبط بشركة'}, status=400)

        fields = ['name_ar', 'name_en', 'phone', 'email', 'address', 'website',
                  'commercial_register', 'tax_number', 'office_address']

        updated = []
        for field in fields:
            value = request.data.get(field)
            if value is not None:
                setattr(company, field, value)
                updated.append(field)

        if updated:
            company.save()

        return Response({
            'success': True,
            'message': f'تم تحديث {len(updated)} حقل بنجاح',
            'updated_fields': updated,
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_upload_company_logo(request):
    """رفع لوجو الشركة"""
    try:
        role = getattr(request.user, 'role', '')
        if role not in ['super_admin', 'company_admin']:
            return Response({'success': False, 'error': 'غير مصرح لك'}, status=403)

        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'success': False, 'error': 'المستخدم غير مرتبط بشركة'}, status=400)

        logo_file = request.FILES.get('logo')
        if not logo_file:
            return Response({'success': False, 'error': 'لم يتم إرسال ملف اللوجو'}, status=400)

        allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if logo_file.content_type not in allowed:
            return Response({'success': False, 'error': 'نوع الملف غير مدعوم (JPEG/PNG/GIF/WEBP فقط)'}, status=400)

        if logo_file.size > 5 * 1024 * 1024:
            return Response({'success': False, 'error': 'حجم الملف أكبر من 5MB'}, status=400)

        company.logo = logo_file
        company.save()

        logo_url = ''
        try:
            logo_url = request.build_absolute_uri(company.logo.url)
        except Exception:
            pass

        return Response({
            'success': True,
            'message': 'تم رفع اللوجو بنجاح',
            'logo_url': logo_url,
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)



@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_managers(request):
    err = _check_manager(request)
    if err:
        return err

    try:
        from django.db.models import Q
        from employees.models import Employee

        def _display_name(emp):
            for attr in ("full_name_ar", "full_name_en", "full_name"):
                val = getattr(emp, attr, None)
                if val:
                    val = str(val).strip()
                    if val:
                        return val
            parts = [
                getattr(emp, "first_name_ar", "") or "",
                getattr(emp, "middle_name_ar", "") or "",
                getattr(emp, "last_name_ar", "") or "",
            ]
            name = " ".join([x for x in parts if x]).strip()
            if name:
                return name
            user = getattr(emp, "user", None)
            return getattr(user, "username", "") if user else ""

        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)

        search = (request.GET.get("search") or "").strip()
        exclude_employee_id = request.GET.get("exclude_employee_id") or request.GET.get("employee_id")

        qs = Employee._base_manager.select_related("user", "department", "job_title").filter(company=company)

        try:
            qs = qs.filter(status="active")
        except Exception:
            pass

        # New logic: filter by job_title.is_manager OR user.role
        from django.db.models import Q
        qs = qs.filter(
            Q(user__role__in=["manager", "hr_manager", "company_admin"])
            | Q(job_title__is_manager=True)
        )

        try:
            visible_ids = list(get_visible_employees_qs(request.user).values_list("id", flat=True))
            qs = qs.filter(id__in=visible_ids)
        except Exception:
            pass

        if exclude_employee_id:
            try:
                qs = qs.exclude(id=int(exclude_employee_id))
            except Exception:
                pass

        if search:
            qs = qs.filter(
                Q(first_name_ar__icontains=search) |
                Q(middle_name_ar__icontains=search) |
                Q(last_name_ar__icontains=search) |
                Q(first_name_en__icontains=search) |
                Q(last_name_en__icontains=search) |
                Q(employee_code__icontains=search) |
                Q(user__username__icontains=search)
            )

        results = []
        for emp in qs.order_by("first_name_ar", "middle_name_ar", "last_name_ar", "employee_code")[:500]:
            results.append({
                "id": emp.id,
                "employee_code": getattr(emp, "employee_code", "") or "",
                "full_name": _display_name(emp),
                "department_name_ar": getattr(getattr(emp, "department", None), "name_ar", "") or "",
                "job_title_name_ar": (
                    getattr(getattr(emp, "job_title", None), "name_ar", "")
                    or getattr(getattr(emp, "job_title", None), "title", "")
                    or ""
                ),
                "worker_type": getattr(emp, "worker_type", "office") or "office",
                "user_role": getattr(getattr(emp, "user", None), "role", "") or "",
            })

        return Response({
            "success": True,
            "results": results,
            "count": len(results),
        }, status=200)

    except Exception as e:
        logger.exception("manager_employee_managers error")
        return Response({"success": False, "error": str(e)}, status=500)


# ═══════════════════════════════════════════════════
# Hierarchy Tree — الهيكل الهرمي (حسب direct_manager)
# ═══════════════════════════════════════════════════
@api_view(['GET'])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_hierarchy_tree(request):
    """
    الهيكل الهرمي للشركة (حسب direct_manager)
    
    Returns:
    {
        "root": [
            {
                "id": 1,
                "name": "صاحب الشركة",
                "job_title": "CEO",
                "employee_code": "EMP001",
                "photo": null,
                "children": [
                    {
                        "id": 2,
                        "name": "مدير 1",
                        "children": [ ... ]
                    }
                ]
            }
        ]
    }
    """
    try:
        from employees.models import Employee
        
        company = getattr(request.user, "company", None)
        if not company:
            return Response(
                {"success": False, "error": "المستخدم غير مرتبط بشركة"},
                status=400
            )
        
        # كل الموظفين النشطين
        all_emps = Employee._base_manager.filter(
            company=company,
            status="active"
        ).select_related("user", "job_title", "department", "branch", "direct_manager")
        
        # نبني dict للسرعة
        emp_dict = {e.id: e for e in all_emps}
        
        # نجمع الأبناء لكل مدير
        children_map = {}
        for e in all_emps:
            if e.direct_manager_id:
                children_map.setdefault(e.direct_manager_id, []).append(e)
        
        def serialize(emp):
            children = children_map.get(emp.id, [])
            # ترتيب: المديرين اللي عندهم فريق الأول
            children_sorted = sorted(
                children,
                key=lambda x: (
                    0 if children_map.get(x.id) else 1,
                    x.first_name_ar or ""
                )
            )
            
            job_title_ar = ""
            job_title_en = ""
            try:
                if emp.job_title:
                    job_title_ar = emp.job_title.title or ""
                    job_title_en = getattr(emp.job_title, 'title_en', '') or ""
            except Exception:
                pass
            
            return {
                "id": emp.id,
                "name_ar": f"{emp.first_name_ar or ''} {emp.last_name_ar or ''}".strip(),
                "name_en": f"{emp.first_name_en or ''} {emp.last_name_en or ''}".strip(),
                "employee_code": emp.employee_code or "",
                "job_title_ar": job_title_ar,
                "job_title_en": job_title_en,
                "department": (getattr(emp.department, "name_ar", "") or getattr(emp.department, "name_en", "") or "") if emp.department else "",
                "branch": (getattr(emp.branch, "name_ar", "") or getattr(emp.branch, "name_en", "") or "") if emp.branch else "",
                "photo": None,
                "role": getattr(emp.user, "role", "employee") if emp.user else "employee",
                "team_size": len(children_map.get(emp.id, [])),
                "children": [serialize(c) for c in children_sorted]
            }
        
        # الجذور = اللي مالهمش direct_manager
        roots = [e for e in all_emps if not e.direct_manager_id]
        roots_sorted = sorted(
            roots,
            key=lambda x: (
                0 if children_map.get(x.id) else 1,
                x.first_name_ar or ""
            )
        )
        
        return Response({
            "success": True,
            "company_name": getattr(company, "name_ar", "") or getattr(company, "name_en", "") or str(company),
            "total_employees": all_emps.count(),
            "root": [serialize(r) for r in roots_sorted]
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {"success": False, "error": str(e)},
            status=500
        )


@api_view(["GET"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_employee_detail(request, employee_id):
    err = _check_manager(request)
    if err:
        return err
    try:
        from employees.models import Employee, JobTitle
        from companies.models import Branch, Department

        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)

        employee = Employee._base_manager.select_related(
            "user", "company", "branch", "department", "job_title", "direct_manager__user"
        ).filter(id=employee_id, company=company).first()

        if not employee:
            return Response({"success": False, "error": "الموظف غير موجود"}, status=404)

        branch = getattr(employee, "branch", None)
        dept = getattr(employee, "department", None)
        jt = getattr(employee, "job_title", None)
        dm = getattr(employee, "direct_manager", None)

        def _dn(emp):
            if not emp:
                return ""
            for a in ("full_name_ar", "full_name_en", "full_name"):
                v = getattr(emp, a, None)
                if v and str(v).strip():
                    return str(v).strip()
            parts = [getattr(emp, "first_name_ar", "") or "", getattr(emp, "middle_name_ar", "") or "", getattr(emp, "last_name_ar", "") or ""]
            n = " ".join([x for x in parts if x]).strip()
            if n:
                return n
            u = getattr(emp, "user", None)
            return getattr(u, "username", "") if u else ""

        def _ds(val):
            return val.isoformat() if val else ""

        data = {
            "id": employee.id,
            "employee_code": getattr(employee, "employee_code", "") or "",
            "first_name_ar": getattr(employee, "first_name_ar", "") or "",
            "middle_name_ar": getattr(employee, "middle_name_ar", "") or "",
            "last_name_ar": getattr(employee, "last_name_ar", "") or "",
            "first_name_en": getattr(employee, "first_name_en", "") or "",
            "last_name_en": getattr(employee, "last_name_en", "") or "",
            "full_name_ar": _dn(employee),
            "full_name": _dn(employee),
            "phone": getattr(employee, "phone", "") or "",
            "phone2": getattr(employee, "phone2", "") or "",
            "email": getattr(employee, "email", "") or "",
            "national_id": getattr(employee, "national_id", "") or "",
            "birth_date": _ds(getattr(employee, "birth_date", None)),
            "gender": getattr(employee, "gender", "") or "",
            "marital_status": getattr(employee, "marital_status", "") or "",
            "hire_date": _ds(getattr(employee, "hire_date", None)),
            "address": getattr(employee, "address", "") or "",
            "city": getattr(employee, "city", "") or "",
            "country": str(getattr(employee, "country", "EG") or "EG"),
            "nationality": getattr(employee, "nationality", "") or "",
            "religion": getattr(employee, "religion", "") or "",
            "language": getattr(employee, "language", "ar") or "ar",
            "currency": getattr(employee, "currency", "EGP") or "EGP",

            "branch_id": getattr(branch, "id", None),
            "branch": getattr(branch, "name_ar", "") or "",
            "branch_name_en": getattr(branch, "name_en", "") or "",
            "department_id": getattr(dept, "id", None),
            "department": getattr(dept, "name_ar", "") or "",
            "department_name_en": getattr(dept, "name_en", "") or "",
            "job_title_id": getattr(jt, "id", None),
            "job_title": getattr(jt, "name_ar", "") or getattr(jt, "title", "") or "",
            "job_title_name_en": getattr(jt, "name_en", "") or getattr(jt, "title_en", "") or "",
            "direct_manager_id": getattr(dm, "id", None),
            "direct_manager_name": _dn(dm),

            "worker_type": getattr(employee, "worker_type", "office") or "office",
            "is_field_worker": bool(getattr(employee, "is_field_worker", False)),
            "status": getattr(employee, "status", "") or "",

            "basic_salary": float(getattr(employee, "basic_salary", 0) or 0),
            "salary_payment_method": getattr(employee, "salary_payment_method", "cash") or "cash",
            "bank_name": getattr(employee, "bank_name", "") or "",
            "bank_account": getattr(employee, "bank_account", "") or "",
            "iban": getattr(employee, "iban", "") or "",
            "instapay_phone": getattr(employee, "instapay_phone", "") or "",
            "wallet_phone": getattr(employee, "wallet_phone", "") or "",
            "wallet_provider": getattr(employee, "wallet_provider", "") or "",

            "contract_type": getattr(employee, "contract_type", "permanent") or "permanent",
            "contract_start_date": _ds(getattr(employee, "contract_start_date", None)),
            "contract_end_date": _ds(getattr(employee, "contract_end_date", None)),
            "contract_duration_months": getattr(employee, "contract_duration_months", None),

            "has_insurance": bool(getattr(employee, "has_insurance", False)),
            "insurance_number": getattr(employee, "insurance_number", "") or "",
            "insurance_date": _ds(getattr(employee, "insurance_date", None)),

            "emergency_contact_name": getattr(employee, "emergency_contact_name", "") or "",
            "emergency_contact_relation": getattr(employee, "emergency_contact_relation", "") or "",
            "emergency_contact_phone": getattr(employee, "emergency_contact_phone", "") or "",

            "username": getattr(getattr(employee, "user", None), "username", "") or "",
            "user_role": getattr(getattr(employee, "user", None), "role", "") or "",
        }

        return Response({"success": True, "employee": data}, status=200)

    except Exception as e:
        logger.exception("manager_employee_detail error")
        return Response({"success": False, "error": str(e)}, status=500)



@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_job_title_detail(request, title_id):
    """تعديل / حذف / عرض مسمى وظيفي معين"""
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة"}, status=400)

        from employees.models import JobTitle
        from companies.models import Branch, Department

        title = JobTitle._base_manager.filter(id=title_id, company=company).first()
        if not title:
            return Response({"success": False, "error": "المسمى غير موجود"}, status=404)

        if request.method == "GET":
            return Response({
                "success": True,
                "job_title": {
                    "id": title.id,
                    "name_ar": title.name_ar,
                    "name_en": title.name_en or "",
                    "description": title.description or "",
                    "branch_id": title.branch_id,
                    "department_id": title.department_id,
                    "is_manager": title.is_manager,
                }
            })

        if request.method == "DELETE":
            title.is_active = False
            title.save()
            return Response({"success": True, "message": "تم الحذف"})

        # PUT - update
        data = request.data
        if "name_ar" in data:
            title.name_ar = (data.get("name_ar") or "").strip()
        if "name_en" in data:
            title.name_en = (data.get("name_en") or "").strip()
        if "description" in data:
            title.description = (data.get("description") or "").strip()

        branch_id = data.get("branch_id") or data.get("branch")
        if branch_id is not None:
            title.branch = Branch._base_manager.filter(id=branch_id, company=company).first() if branch_id else None

        department_id = data.get("department_id") or data.get("department")
        if department_id is not None:
            title.department = Department._base_manager.filter(id=department_id, company=company).first() if department_id else None

        if "is_manager" in data:
            title.is_manager = bool(data.get("is_manager"))

        title.save()

        return Response({
            "success": True,
            "message": "تم التحديث",
            "job_title": {
                "id": title.id,
                "name_ar": title.name_ar,
                "name_en": title.name_en or "",
                "branch_id": title.branch_id,
                "department_id": title.department_id,
                "is_manager": title.is_manager,
            }
        })
    except Exception as e:
        logger.exception("manager_job_title_detail error")
        return Response({"success": False, "error": str(e)}, status=500)



@api_view(["GET", "POST", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_branches(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)
        from companies.models import Branch

        if request.method == "POST":
            data = request.data
            name_ar = (data.get("name_ar") or "").strip()
            if not name_ar:
                return Response({"success": False, "error": "اسم الفرع بالعربي مطلوب"}, status=400)

            is_main = bool(data.get("is_main", False))
            if is_main:
                Branch._base_manager.filter(company=company, is_main=True).update(is_main=False)

            branch = Branch._base_manager.create(
                company=company,
                name_ar=name_ar,
                name_en=(data.get("name_en") or "").strip(),
                address=(data.get("address") or "").strip(),
                phone=(data.get("phone") or "").strip(),
                is_active=True,
                is_main=is_main,
            )
            return Response({
                "success": True,
                "message": "تم إنشاء الفرع بنجاح",
                "branch": {
                    "id": branch.id,
                    "name_ar": branch.name_ar,
                    "name_en": branch.name_en or "",
                    "address": branch.address or "",
                    "phone": branch.phone or "",
                    "is_main": branch.is_main,
                }
            }, status=201)

        elif request.method == "PUT":
            data = request.data
            branch_id = data.get("id") or request.GET.get("id")
            if not branch_id:
                return Response({"success": False, "error": "معرف الفرع مطلوب"}, status=400)

            try:
                branch = Branch._base_manager.get(id=branch_id, company=company)
            except Branch.DoesNotExist:
                return Response({"success": False, "error": "الفرع غير موجود"}, status=404)

            name_ar = (data.get("name_ar") or "").strip()
            if name_ar:
                branch.name_ar = name_ar
            if "name_en" in data:
                branch.name_en = (data.get("name_en") or "").strip()
            if "address" in data:
                branch.address = (data.get("address") or "").strip()
            if "phone" in data:
                branch.phone = (data.get("phone") or "").strip()

            if "is_main" in data:
                is_main = bool(data.get("is_main"))
                if is_main:
                    Branch._base_manager.filter(company=company, is_main=True).exclude(id=branch.id).update(is_main=False)
                branch.is_main = is_main

            branch.save()
            return Response({
                "success": True,
                "message": "تم تعديل بيانات الفرع بنجاح",
                "branch": {
                    "id": branch.id,
                    "name_ar": branch.name_ar,
                    "name_en": branch.name_en or "",
                    "address": branch.address or "",
                    "phone": branch.phone or "",
                    "is_main": branch.is_main,
                }
            })

        elif request.method == "DELETE":
            branch_id = request.data.get("id") or request.GET.get("id")
            if not branch_id:
                return Response({"success": False, "error": "معرف الفرع مطلوب"}, status=400)

            try:
                branch = Branch._base_manager.get(id=branch_id, company=company)
            except Branch.DoesNotExist:
                return Response({"success": False, "error": "الفرع غير موجود"}, status=404)

            from employees.models import Employee
            if Employee._base_manager.filter(branch=branch, status="active").exists():
                return Response({"success": False, "error": "لا يمكن حذف هذا الفرع لوجود موظفين نشطين مسجلين عليه"}, status=400)

            branch.delete()
            return Response({"success": True, "message": "تم حذف الفرع بنجاح"})

        # GET
        branches = Branch._base_manager.filter(company=company, is_active=True).order_by("name_ar")
        data = [{
            "id": b.id,
            "name_ar": b.name_ar,
            "name_en": b.name_en or "",
            "address": b.address or "",
            "phone": b.phone or "",
            "is_main": b.is_main
        } for b in branches]
        return Response({"success": True, "branches": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_branches error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET", "POST", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def manager_departments(request, dept_id=None):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)
        from companies.models import Department, Branch

        if request.method == "POST":
            data = request.data
            name_ar = (data.get("name_ar") or "").strip()
            if not name_ar:
                return Response({"success": False, "error": "اسم القسم بالعربي مطلوب"}, status=400)

            branch_id = data.get("branch_id") or data.get("branch")
            branch_obj = None
            if branch_id:
                branch_obj = Branch._base_manager.filter(id=branch_id, company=company).first()

            dept = Department._base_manager.create(
                company=company,
                name_ar=name_ar,
                name_en=(data.get("name_en") or "").strip(),
                code=(data.get("code") or "").strip(),
                description=(data.get("description") or "").strip(),
                branch=branch_obj,
                is_active=True,
            )
            return Response({
                "success": True,
                "message": "تم إنشاء القسم بنجاح",
                "department": {
                    "id": dept.id,
                    "name_ar": dept.name_ar,
                    "name_en": dept.name_en or "",
                    "code": dept.code or "",
                    "branch_id": dept.branch_id,
                    "branch_name": dept.branch.name_ar if dept.branch else None,
                }
            }, status=201)

        elif request.method == "PUT":
            data = request.data
            target_id = dept_id or data.get("id") or request.GET.get("id")
            if not target_id:
                return Response({"success": False, "error": "معرف القسم مطلوب"}, status=400)

            try:
                dept = Department._base_manager.get(id=target_id, company=company)
            except Department.DoesNotExist:
                return Response({"success": False, "error": "القسم غير موجود"}, status=404)

            name_ar = (data.get("name_ar") or "").strip()
            if name_ar:
                dept.name_ar = name_ar
            if "name_en" in data:
                dept.name_en = (data.get("name_en") or "").strip()
            if "code" in data:
                dept.code = (data.get("code") or "").strip()
            if "description" in data:
                dept.description = (data.get("description") or "").strip()

            if "branch_id" in data or "branch" in data:
                b_id = data.get("branch_id") or data.get("branch")
                dept.branch = Branch._base_manager.filter(id=b_id, company=company).first() if b_id else None

            dept.save()
            return Response({
                "success": True,
                "message": "تم تعديل بيانات القسم بنجاح",
                "department": {
                    "id": dept.id,
                    "name_ar": dept.name_ar,
                    "name_en": dept.name_en or "",
                    "code": dept.code or "",
                    "branch_id": dept.branch_id,
                    "branch_name": dept.branch.name_ar if dept.branch else None,
                }
            })

        elif request.method == "DELETE":
            target_id = dept_id or request.data.get("id") or request.GET.get("id")
            if not target_id:
                return Response({"success": False, "error": "معرف القسم مطلوب"}, status=400)

            try:
                dept = Department._base_manager.get(id=target_id, company=company)
            except Department.DoesNotExist:
                return Response({"success": False, "error": "القسم غير موجود"}, status=404)

            from employees.models import Employee
            if Employee._base_manager.filter(department=dept, status="active").exists():
                return Response({"success": False, "error": "لا يمكن حذف هذا القسم لوجود موظفين نشطين مسجلين عليه"}, status=400)

            dept.delete()
            return Response({"success": True, "message": "تم حذف القسم بنجاح"})

        # GET
        branch_filter = request.GET.get("branch_id")
        depts = Department._base_manager.filter(company=company, is_active=True)
        if branch_filter:
            depts = depts.filter(branch_id=branch_filter)

        depts = depts.order_by("name_ar")
        data = [{
            "id": d.id,
            "name_ar": d.name_ar,
            "name_en": d.name_en or "",
            "code": d.code or "",
            "description": d.description or "",
            "branch_id": d.branch_id,
            "branch_name": d.branch.name_ar if d.branch else None,
        } for d in depts]
        return Response({"success": True, "departments": data, "count": len(data)})

    except Exception as e:
        logger.exception("manager_departments error")
        return Response({"success": False, "error": str(e)}, status=500)


