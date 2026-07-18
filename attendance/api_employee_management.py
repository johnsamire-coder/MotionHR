"""
Phase 8: Employee Creation from Manager App
- Manager can create employee user directly from mobile
- Returns credentials for PDF + WhatsApp sharing
"""
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
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

logger = logging.getLogger(__name__)

def _generate_username_from_names(first_name_en, last_name_en, company, phone=""):
    """توليد يوزر من الاسم الإنجليزي + فحص التكرار"""
    from django.contrib.auth.models import User
    import re

    first = re.sub(r'[^a-z]', '', (first_name_en or '').lower().strip())
    last = re.sub(r'[^a-z]', '', (last_name_en or '').lower().strip())

    if first and last:
        base = f"{first}{last}"
    elif first:
        base = first
    else:
        clean_phone = ''.join(ch for ch in (phone or '') if ch.isdigit())
        base = f"emp{clean_phone[-7:]}" if clean_phone else "emp1"

    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
        if counter > 999:
            import random
            username = f"{base}{random.randint(1000, 9999)}"
            break

    return username


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
    # Fallback: try via Employee model
    try:
        from employees.models import Employee
        emp = Employee.objects.filter(user=request.user).first()
        if emp and emp.company:
            return emp.company
    except Exception:
        pass
    return None


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
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
        branches = Branch.objects.filter(company=company, is_active=True).order_by("name_ar")
        data = [{"id": b.id, "name_ar": b.name_ar, "name_en": b.name_en or "", "is_main": b.is_main} for b in branches]
        return Response({"success": True, "branches": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_branches error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_departments(request):
    err = _check_manager(request)
    if err:
        return err
    try:
        company = _get_company(request)
        if not company:
            return Response({"success": False, "error": "لا توجد شركة مرتبطة"}, status=400)
        from companies.models import Department
        depts = Department.objects.filter(company=company, is_active=True).order_by("name_ar")
        data = [{"id": d.id, "name_ar": d.name_ar, "name_en": d.name_en or "", "code": d.code or ""} for d in depts]
        return Response({"success": True, "departments": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_departments error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
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
        titles = JobTitle._base_manager.filter(company=company, is_active=True).order_by("name_ar")
        data = [{"id": t.id, "name_ar": t.name_ar, "name_en": t.name_en or ""} for t in titles]
        return Response({"success": True, "job_titles": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_job_titles error")
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
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
        emps = get_visible_employees_qs(request.user).exclude(user=request.user).filter(status="active").select_related("job_title").order_by("first_name_ar")[:200]
        data = []
        for e in emps:
            data.append({
                "id": e.id,
                "employee_code": e.employee_code,
                "full_name": getattr(e, "full_name_ar", f"{e.first_name_ar} {e.last_name_ar}"),
                "job_title": getattr(e.job_title, "name_ar", "") if e.job_title else "",
            })
        return Response({"success": True, "employees": data, "count": len(data)})
    except Exception as e:
        logger.exception("manager_employees_simple error")
        return Response({"success": False, "error": str(e)}, status=500)


def _generate_username(phone, first_name_ar, company_id):
    """Generate unique username"""
    base = None
    # Try phone as username if not exists
    if phone:
        clean_phone = re.sub(r'\D', '', phone)
        if clean_phone:
            base = f"emp{clean_phone[-7:]}"
    if not base:
        # Fallback random
        base = f"emp{random.randint(10000, 99999)}"
    
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
        if counter > 100:
            username = f"emp{random.randint(100000, 999999)}"
            break
    return username


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


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
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
        employee_code_input = str(data.get("employee_code", "")).strip()

        # Validation details
        if len(first_name_ar) < 2:
            return Response({"success": False, "error": "الاسم الأول قصير جداً"}, status=400)
        if len(last_name_ar) < 2:
            return Response({"success": False, "error": "الاسم الأخير قصير جداً"}, status=400)

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

        # Branch / Department / JobTitle belong to company
        from companies.models import Branch, Department
        from employees.models import Employee, JobTitle

        try:
            branch = Branch.objects.get(id=branch_id, company=company)
        except Branch.DoesNotExist:
            return Response({"success": False, "error": f"الفرع غير موجود أو لا ينتمي لشركتك (id={branch_id})"}, status=400)

        try:
            department = Department.objects.get(id=department_id, company=company)
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
        if Employee.objects.filter(company=company, national_id=national_id).exists():
            return Response({"success": False, "error": "الرقم القومي مسجل لموظف آخر في نفس الشركة"}, status=400)

        # Check duplicate employee_code if provided
        if employee_code_input and Employee.objects.filter(company=company, employee_code=employee_code_input).exists():
            return Response({"success": False, "error": "الرقم الوظيفي موجود مسبقاً"}, status=400)

        # Username handling
        if username_input:
            if User.objects.filter(username=username_input).exists():
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
            # Create User
            user = User.objects.create(
                username=username,
                first_name=first_name_ar,
                last_name=last_name_ar,
                email=email if email else "",
                phone=phone,
                role="employee",
                company=company,
                must_change_password=True,
                is_active=True,
            )
            user.set_password(password_plain)
            user.save()

            # Create Employee
            employee = Employee.objects.create(
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
                basic_salary=basic_salary_val,
                status="active",
            )

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
                "basic_salary": float(employee.basic_salary or 0),
                "currency": employee.currency,
                "company": company.name_ar,
            },
            "credentials": {
                "username": username,
                "password": password_plain,
                "login_url": "https://jssolutions-eg.com",
                "must_change_password": True,
            },
            "whatsapp": {
                "phone": phone,
                "clean_phone": clean_phone,
                "wa_link": f"https://wa.me/{clean_phone}?text=" + 
                    f"مرحباً {first_name_ar}%0A"
                    f"تم إنشاء حسابك في تطبيق MotionHR%0A%0A"
                    f"اسم المستخدم: {username}%0A"
                    f"كلمة المرور: {password_plain}%0A%0A"
                    f"حمّل التطبيق من هنا:%0A"
                    f"https://jssolutions-eg.com/app/download%0A%0A"
                    f"⚠️ يرجى تغيير كلمة المرور عند أول دخول",
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
        target_employee = Employee.objects.select_related("user", "company").filter(id=employee_id).first()
        if not target_employee:
            return Response(
                {"success": False, "error": "الموظف غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )

        requester_employee = Employee.objects.select_related("company").filter(user=request.user).first()

        allowed_groups = {"company_admin", "manager", "hr_manager", "super_admin"}
        user_groups = set(request.user.groups.values_list("name", flat=True))
        is_allowed = request.user.is_superuser or bool(user_groups.intersection(allowed_groups))

        if not is_allowed:
            return Response(
                {"success": False, "error": "غير مصرح لك بإعادة تعيين كلمة المرور"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_superuser:
            if not requester_employee or not requester_employee.company_id:
                return Response(
                    {"success": False, "error": "تعذر تحديد شركة المستخدم الحالي"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if target_employee.company_id != requester_employee.company_id:
                return Response(
                    {"success": False, "error": "لا يمكنك إدارة موظف من شركة أخرى"},
                    status=status.HTTP_403_FORBIDDEN
                )

        if not getattr(target_employee, "user", None):
            return Response(
                {"success": False, "error": "هذا الموظف لا يملك حساب دخول"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_password = (request.data.get("new_password") or "").strip()

        if not new_password:
            import random
            import string
            digits = ''.join(random.choices(string.digits, k=4))
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
            new_password = f"Emp@{digits}{suffix}"

        if len(new_password) < 6:
            return Response(
                {"success": False, "error": "كلمة المرور يجب أن تكون 6 أحرف على الأقل"},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_employee.user.set_password(new_password)
        target_employee.user.save()

        if hasattr(target_employee, "must_change_password"):
            target_employee.must_change_password = True
            target_employee.save(update_fields=["must_change_password"])

        full_name = (
            getattr(target_employee, "full_name_ar", "")
            or getattr(target_employee, "full_name_en", "")
            or getattr(target_employee, "full_name", "")
            or target_employee.user.username
        )

        return Response({
            "success": True,
            "message": f"تم إعادة تعيين كلمة مرور {full_name} بنجاح",
            "employee": {
                "id": target_employee.id,
                "employee_code": getattr(target_employee, "employee_code", ""),
                "full_name": full_name,
                "phone": getattr(target_employee, "phone", ""),
            },
            "credentials": {
                "username": target_employee.user.username,
                "password": new_password,
                "must_change_password": True,
                "login_url": "https://jssolutions-eg.com",
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_reset_employee_password error")
        return Response(
            {"success": False, "error": f"خطأ في إعادة تعيين كلمة المرور: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def manager_update_employee(request, employee_id):
    try:
        target_employee = Employee.objects.select_related("user", "company").filter(id=employee_id).first()
        if not target_employee:
            return Response(
                {"success": False, "error": "الموظف غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )

        requester_employee = Employee.objects.select_related("company").filter(user=request.user).first()

        allowed_groups = {"company_admin", "manager", "hr_manager", "super_admin"}
        user_groups = set(request.user.groups.values_list("name", flat=True))
        is_allowed = request.user.is_superuser or bool(user_groups.intersection(allowed_groups))

        if not is_allowed:
            return Response(
                {"success": False, "error": "غير مصرح لك بتعديل بيانات الموظف"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_superuser:
            if not requester_employee or not requester_employee.company_id:
                return Response(
                    {"success": False, "error": "تعذر تحديد شركة المستخدم الحالي"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if target_employee.company_id != requester_employee.company_id:
                return Response(
                    {"success": False, "error": "لا يمكنك تعديل موظف من شركة أخرى"},
                    status=status.HTTP_403_FORBIDDEN
                )

        phone = (request.data.get("phone") or "").strip()
        email = (request.data.get("email") or "").strip()
        address = (request.data.get("address") or "").strip()
        bank_name = (request.data.get("bank_name") or "").strip()
        bank_account = (request.data.get("bank_account") or "").strip()
        iban = (request.data.get("iban") or "").strip()

        if phone:
            clean_phone = ''.join(ch for ch in phone if ch.isdigit())
            if len(clean_phone) < 10 or len(clean_phone) > 15:
                return Response(
                    {"success": False, "error": "رقم الموبايل يجب أن يكون من 10 إلى 15 رقم"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            phone_conflict = Employee.objects.filter(
                company_id=target_employee.company_id,
                phone=phone
            ).exclude(id=target_employee.id).exists()

            if phone_conflict:
                return Response(
                    {"success": False, "error": "رقم الموبايل مستخدم بالفعل داخل نفس الشركة"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        update_fields = []

        if hasattr(target_employee, "phone"):
            target_employee.phone = phone
            update_fields.append("phone")

        if hasattr(target_employee, "email"):
            target_employee.email = email
            update_fields.append("email")

        if hasattr(target_employee, "address"):
            target_employee.address = address
            update_fields.append("address")

        if hasattr(target_employee, "bank_name"):
            target_employee.bank_name = bank_name
            update_fields.append("bank_name")

        if hasattr(target_employee, "bank_account"):
            target_employee.bank_account = bank_account
            update_fields.append("bank_account")

        if hasattr(target_employee, "iban"):
            target_employee.iban = iban
            update_fields.append("iban")

        if update_fields:
            target_employee.save(update_fields=update_fields)

        if getattr(target_employee, "user", None) and hasattr(target_employee.user, "email"):
            target_employee.user.email = email
            target_employee.user.save(update_fields=["email"])

        full_name = (
            getattr(target_employee, "full_name_ar", "")
            or getattr(target_employee, "full_name_en", "")
            or getattr(target_employee, "full_name", "")
            or target_employee.user.username
        )

        return Response({
            "success": True,
            "message": f"تم تحديث بيانات {full_name} بنجاح",
            "employee": {
                "id": target_employee.id,
                "employee_code": getattr(target_employee, "employee_code", ""),
                "full_name": full_name,
                "phone": getattr(target_employee, "phone", ""),
                "email": getattr(target_employee, "email", ""),
                "address": getattr(target_employee, "address", ""),
                "bank_name": getattr(target_employee, "bank_name", ""),
                "bank_account": getattr(target_employee, "bank_account", ""),
                "iban": getattr(target_employee, "iban", ""),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("manager_update_employee error")
        return Response(
            {"success": False, "error": f"خطأ في تحديث بيانات الموظف: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manager_company_info(request):
    """جلب بيانات الشركة الكاملة + اللوجو"""
    try:
        from employees.models import Employee
        requester_employee = Employee.objects.select_related("company").filter(user=request.user).first()
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
            branches_count = Branch.objects.filter(company=company).count()
            departments_count = Department.objects.filter(company=company).count()
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
    """نقل موظف: تغيير مدير / إدارة / فرع"""
    try:
        target_employee = Employee.objects.select_related("user", "company").filter(id=employee_id).first()
        if not target_employee:
            return Response(
                {"success": False, "error": "الموظف غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )

        requester_employee = Employee.objects.select_related("company").filter(user=request.user).first()

        allowed_groups = {"company_admin", "manager", "hr_manager", "super_admin"}
        user_groups = set(request.user.groups.values_list("name", flat=True))
        is_allowed = request.user.is_superuser or bool(user_groups.intersection(allowed_groups))

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
                new_mgr = Employee.objects.filter(
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
                new_branch = Branch.objects.filter(
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
                new_dept = Department.objects.filter(
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
            except Exception as e:
                pass

        if new_job_title_id:
            try:
                from attendance.models import JobTitle
                new_jt = JobTitle.objects.filter(
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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
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
        point_index = LocationHistory.objects.filter(
            employee=employee,
            shift_date=shift_date
        ).count()

        # حد أقصى 24 نقطة في اليوم
        if point_index >= 24:
            return Response({'success': True, 'message': 'تم الوصول للحد الأقصى من النقاط'})

        loc = LocationHistory.objects.create(
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
@authentication_classes([TokenAuthentication])
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
                'recorded_at': loc.recorded_at.strftime('%H:%M') if loc.recorded_at else '',
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
