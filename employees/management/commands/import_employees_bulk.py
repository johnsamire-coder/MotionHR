"""
Management Command: import_employees_bulk - Version 2
خريطة الأعمدة متطابقة مع generate_employee_template v2
"""
import os
import random
import string
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from openpyxl import load_workbook

from accounts.models import User
from employees.models import Employee, JobTitle
from companies.models import Branch, Department
from leaves.models import LeaveType, LeaveBalance
from leaves.signals import _get_entitlement_days
from employees.account_utils import send_mail
from django.conf import settings


# ═══════════════════════════════════════════════════════
# خريطة الأعمدة الثابتة — index يبدأ من 0
# ═══════════════════════════════════════════════════════
C = {
    "operation_type": 0,
    "employee_code": 1,
    "temporary_password": 2,
    "first_name_ar": 3,
    "middle_name_ar": 4,
    "last_name_ar": 5,
    "first_name_en": 6,
    "last_name_en": 7,
    "national_id": 8,
    "passport_number": 9,
    "birth_date": 10,
    "gender": 11,
    "marital_status": 12,
    "religion": 13,
    "nationality": 14,
    "language": 15,
    "country_code": 16,
    "phone": 17,
    "phone2": 18,
    "email": 19,
    "address": 20,
    "city": 21,
    "emergency_contact_name": 22,
    "emergency_contact_relation": 23,
    "emergency_contact_phone": 24,
    "branch_name": 25,
    "department_name": 26,
    "job_title_name": 27,
    "direct_manager_department": 28,
    "direct_manager_name": 29,
    "hire_date": 30,
    "attendance_mode": 31,
    "status": 32,
    "contract_type": 33,
    "contract_start_date": 34,
    "contract_end_date": 35,
    "contract_duration_months": 36,
    "probation_months": 37,
    "has_insurance": 38,
    "insurance_number": 39,
    "basic_salary": 40,
    "currency": 41,
    "salary_payment_method": 42,
    "bank_name": 43,
    "bank_account": 44,
    "bank_account_holder_name": 45,
    "iban": 46,
    "instapay_transfer_id": 47,
    "wallet_transfer_number": 48,
    "wallet_provider": 49,
    "annual_entitled": 50,
    "annual_used_before_system": 51,
    "annual_carry_forward": 52,
    "sick_entitled": 53,
    "sick_used_before_system": 54,
    "sick_carry_forward": 55,
    "emergency_entitled": 56,
    "emergency_used_before_system": 57,
    "emergency_carry_forward": 58,
    "maternity_entitled": 59,
    "maternity_used_before_system": 60,
    "maternity_carry_forward": 61,
    "paternity_entitled": 62,
    "paternity_used_before_system": 63,
    "paternity_carry_forward": 64,
    "unpaid_entitled": 65,
    "unpaid_used_before_system": 66,
    "unpaid_carry_forward": 67,
}

LEAVE_COLS = {
    "annual":    ("annual_entitled",    "annual_used_before_system",    "annual_carry_forward"),
    "sick":      ("sick_entitled",      "sick_used_before_system",      "sick_carry_forward"),
    "emergency": ("emergency_entitled", "emergency_used_before_system", "emergency_carry_forward"),
    "maternity": ("maternity_entitled", "maternity_used_before_system", "maternity_carry_forward"),
    "paternity": ("paternity_entitled", "paternity_used_before_system", "paternity_carry_forward"),
    "unpaid":    ("unpaid_entitled",    "unpaid_used_before_system",    "unpaid_carry_forward"),
}


def _str(row, key):
    val = row[C[key]]
    return str(val).strip() if val is not None else ""


def _dec(row, key):
    val = row[C[key]]
    if val is None or str(val).strip() == "":
        return Decimal("0")
    try:
        return Decimal(str(val).strip())
    except InvalidOperation:
        return Decimal("0")


def _int(row, key, default=0):
    val = row[C[key]]
    if val is None or str(val).strip() == "":
        return default
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def _date(row, key):
    val = row[C[key]]
    if val is None:
        return None
    if hasattr(val, "date"):
        return val.date()
    from datetime import date
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


class Command(BaseCommand):
    help = "استيراد الموظفين من ملف Excel - v2"

    def add_arguments(self, parser):
        parser.add_argument("--file",        type=str, required=True)
        parser.add_argument("--send-emails", action="store_true")
        parser.add_argument("--company-id",  type=int, default=None)

    def generate_random_password(self, length=8):
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def _make_activation_link(self, user):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        site  = getattr(settings, "SITE_URL", "https://motion.jssolutions-eg.com")
        return f"{site}/password-reset-confirm/{uid}/{token}/"

    def handle(self, *args, **options):
        file_path  = options["file"]
        send_emails = options["send_emails"]

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"الملف غير موجود: {file_path}"))
            return

        try:
            wb = load_workbook(file_path, data_only=True)
            ws = wb["الموظفين"]
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطأ في قراءة ملف الإكسيل: {e}"))
            return

        from companies.models import Company
        if options["company_id"]:
            company = Company.objects.filter(id=options["company_id"]).first()
        else:
            company = Company.objects.first()

        if not company:
            self.stdout.write(self.style.ERROR("لا توجد شركة مسجلة في النظام!"))
            return

        leave_types_map = {
            lt.category: lt
            for lt in LeaveType.objects.filter(company=company, is_active=True)
        }

        # تخطي أول 3 صفوف (section header + labels + keys)
        rows = list(ws.iter_rows(min_row=4, values_only=True))

        success_count = 0
        update_count  = 0
        error_count   = 0
        errors        = []

        for idx, row in enumerate(rows, start=4):
            if not row or not row[C["operation_type"]]:
                continue

            op_type  = _str(row, "operation_type").lower()
            emp_code = _str(row, "employee_code")
            nat_id   = _str(row, "national_id")

            row_errors = self._validate_row(row, op_type, idx)
            if row_errors:
                for e in row_errors:
                    self.stdout.write(self.style.WARNING(e))
                    errors.append(e)
                error_count += 1
                continue

            try:
                with transaction.atomic():
                    if op_type == "new":
                        result = self._create_employee(
                            row, company, leave_types_map,
                            send_emails, idx
                        )
                        if result:
                            success_count += 1
                        else:
                            error_count += 1

                    elif op_type == "update":
                        result = self._update_employee(row, company, emp_code, nat_id, idx)
                        if result:
                            update_count += 1
                        else:
                            error_count += 1
                    else:
                        msg = f"صف {idx}: نوع العملية غير معروف: {op_type}"
                        self.stdout.write(self.style.WARNING(msg))
                        errors.append(msg)
                        error_count += 1

            except Exception as e:
                msg = f"صف {idx}: فشل الاستيراد - {e}"
                self.stdout.write(self.style.ERROR(msg))
                errors.append(msg)
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"تم الانتهاء! جديد: {success_count} | تحديث: {update_count} | أخطاء: {error_count}"
        ))
        if errors:
            self.stdout.write(self.style.WARNING("\nتفاصيل الأخطاء:"))
            for e in errors:
                self.stdout.write(f"  - {e}")

    # ─────────────────────────────────────────
    def _validate_row(self, row, op_type, idx):
        errors = []
        prefix = f"صف {idx}"

        if op_type == "new":
            required = [
                "first_name_ar", "last_name_ar",
                "national_id", "phone",
                "hire_date", "branch_name",
                "department_name", "job_title_name",
                "salary_payment_method",
            ]
            for field in required:
                if not _str(row, field):
                    errors.append(f"{prefix}: الحقل [{field}] إجباري للموظف الجديد")

            # التأمين
            has_ins = _str(row, "has_insurance")
            ins_num = _str(row, "insurance_number")
            if has_ins == "نعم" and not ins_num:
                errors.append(f"{prefix}: رقم التأمين إجباري لأن [مؤمن عليه = نعم]")

            # العقد
            contract_type = _str(row, "contract_type")
            if contract_type in ("temporary", "training", "consultant"):
                if not _str(row, "contract_start_date"):
                    errors.append(f"{prefix}: بداية العقد إجبارية لنوع العقد [{contract_type}]")
                if not _str(row, "contract_end_date") and not _int(row, "contract_duration_months"):
                    errors.append(f"{prefix}: نهاية العقد أو مدة العقد إجبارية لنوع العقد [{contract_type}]")

            # طريقة القبض
            pay_method = _str(row, "salary_payment_method")
            if pay_method == "bank":
                if not _str(row, "bank_name"):
                    errors.append(f"{prefix}: اسم البنك إجباري لطريقة القبض [bank]")
                if not _str(row, "bank_account"):
                    errors.append(f"{prefix}: رقم الحساب إجباري لطريقة القبض [bank]")
                if not _str(row, "bank_account_holder_name"):
                    errors.append(f"{prefix}: اسم صاحب الحساب إجباري لطريقة القبض [bank]")
            elif pay_method == "instapay":
                if not _str(row, "instapay_transfer_id"):
                    errors.append(f"{prefix}: رقم إنستا باي إجباري لطريقة القبض [instapay]")
            elif pay_method == "wallet":
                if not _str(row, "wallet_transfer_number"):
                    errors.append(f"{prefix}: رقم المحفظة إجباري لطريقة القبض [wallet]")
                if not _str(row, "wallet_provider"):
                    errors.append(f"{prefix}: مزود المحفظة إجباري لطريقة القبض [wallet]")

        elif op_type == "update":
            if not _str(row, "employee_code") and not _str(row, "national_id"):
                errors.append(f"{prefix}: كود الموظف أو الرقم القومي مطلوب للتحديث")

        return errors

    # ─────────────────────────────────────────
    def _resolve_manager(self, company, manager_name, manager_department=None):
        if not manager_name:
            return None

        employees = Employee._base_manager.filter(company=company).select_related("department")

        full_matches = [
            e for e in employees
            if f"{e.first_name_ar} {e.last_name_ar}".strip() == manager_name
        ]

        if manager_department:
            full_matches = [
                e for e in full_matches
                if getattr(e.department, "name_ar", None) == manager_department
            ]

        if len(full_matches) == 1:
            return full_matches[0]

        if len(full_matches) > 1:
            if manager_department:
                raise ValueError(
                    f"اسم المدير [{manager_name}] متكرر داخل القسم [{manager_department}] — يرجى المراجعة"
                )
            raise ValueError(
                f"اسم المدير [{manager_name}] متكرر — اكتب قسم المدير المباشر لتحديده"
            )

        if manager_department:
            raise ValueError(
                f"لم يتم العثور على مدير باسم [{manager_name}] داخل القسم [{manager_department}]"
            )

        raise ValueError(f"لم يتم العثور على مدير باسم [{manager_name}]")
        matches = Employee._base_manager.filter(
            company=company,
            first_name_ar__icontains=manager_name.split()[0] if manager_name.split() else manager_name,
        )
        full_matches = [
            e for e in matches
            if f"{e.first_name_ar} {e.last_name_ar}".strip() == manager_name
        ]
        if len(full_matches) == 1:
            return full_matches[0]
        elif len(full_matches) > 1:
            raise ValueError(f"اسم المدير [{manager_name}] متكرر — يرجى التوضيح بكود الموظف")
        return None

    # ─────────────────────────────────────────
    def _create_employee(self, row, company, leave_types_map, send_emails, idx):
        fname_ar  = _str(row, "first_name_ar")
        lname_ar  = _str(row, "last_name_ar")
        nat_id    = _str(row, "national_id")
        phone     = _str(row, "phone")
        email     = _str(row, "email") or None
        emp_code  = _str(row, "employee_code")
        temp_pass = _str(row, "temporary_password") or self.generate_random_password()

        hire_date = _date(row, "hire_date")

        branch_name = _str(row, "branch_name")
        dept_name   = _str(row, "department_name")
        job_name    = _str(row, "job_title_name")

        created_defs = []

        branch, branch_created = Branch.objects.get_or_create(
            company=company,
            name_ar=branch_name,
        )
        if branch_created:
            created_defs.append(f"صف {idx}: تم إنشاء فرع جديد [{branch_name}]")

        dept, dept_created = Department.objects.get_or_create(
            company=company,
            branch=branch,
            name_ar=dept_name,
        )
        if dept_created:
            created_defs.append(f"صف {idx}: تم إنشاء قسم جديد [{dept_name}] داخل الفرع [{branch_name}]")

        job, job_created = JobTitle.objects.get_or_create(
            company=company,
            department=dept,
            name_ar=job_name,
        )
        if job_created:
            created_defs.append(f"صف {idx}: تم إنشاء مسمى وظيفي جديد [{job_name}] داخل القسم [{dept_name}]")

        manager = self._resolve_manager(company, _str(row, "direct_manager_name"), _str(row, "direct_manager_department"))

        contract_type = _str(row, "contract_type") or "permanent"
        contract_start = _date(row, "contract_start_date") or hire_date
        contract_end   = _date(row, "contract_end_date")
        duration_months = _int(row, "contract_duration_months")

        # حساب نهاية العقد تلقائي لو مش موجودة
        if not contract_end and duration_months and contract_start:
            from dateutil.relativedelta import relativedelta
            contract_end = contract_start + relativedelta(months=duration_months)

        has_insurance = _str(row, "has_insurance") == "نعم"
        gender_val = _str(row, "gender")

        att_mode = _str(row, "attendance_mode") or "fixed_shift"
        status   = _str(row, "status") or "active"

        username = f"emp{nat_id[-6:]}{random.randint(10, 99)}"
        user = User.objects.create_user(
            username=username,
            password=temp_pass,
            email=email or "",
            first_name=fname_ar,
            last_name=lname_ar,
            company=company,
            role="employee",
        )

        emp = Employee.objects.create(
            company=company,
            user=user,
            employee_code=emp_code or f"EMP{user.id}",
            first_name_ar=fname_ar,
            middle_name_ar=_str(row, "middle_name_ar"),
            last_name_ar=lname_ar,
            first_name_en=_str(row, "first_name_en"),
            last_name_en=_str(row, "last_name_en"),
            national_id=nat_id,
            passport_number=_str(row, "passport_number") or None,
            birth_date=_date(row, "birth_date"),
            gender="female" if gender_val in ("female", "أنثى") else "male",
            marital_status=_str(row, "marital_status") or None,
            religion=_str(row, "religion") or None,
            nationality=_str(row, "nationality") or "مصري",
            language="en" if _str(row, "language") == "en" else "ar",
            phone=phone,
            phone2=_str(row, "phone2") or None,
            email=email,
            address=_str(row, "address") or None,
            city=_str(row, "city") or None,
            emergency_contact_name=_str(row, "emergency_contact_name") or None,
            emergency_contact_relation=_str(row, "emergency_contact_relation") or None,
            emergency_contact_phone=_str(row, "emergency_contact_phone") or None,
            branch=branch,
            department=dept,
            job_title=job,
            direct_manager=manager,
            hire_date=hire_date,
            attendance_mode=att_mode,
            status=status,
            contract_type=contract_type,
            contract_start_date=contract_start,
            contract_end_date=contract_end,
            contract_duration_months=duration_months or None,
            probation_months=_int(row, "probation_months", 3),
            has_insurance=has_insurance,
            insurance_number=_str(row, "insurance_number") or None,
            basic_salary=_dec(row, "basic_salary") or None,
            currency=_str(row, "currency") or "EGP",
            salary_payment_method=_str(row, "salary_payment_method") or "cash",
            bank_name=_str(row, "bank_name") or None,
            bank_account=_str(row, "bank_account") or None,
            bank_account_holder_name=_str(row, "bank_account_holder_name") or None,
            iban=_str(row, "iban") or None,
            instapay_phone=_str(row, "instapay_transfer_id") or None,
            wallet_phone=_str(row, "wallet_transfer_number") or None,
            wallet_provider=_str(row, "wallet_provider") or None,
        )

        # أرصدة الإجازات
        year = timezone.now().year
        for cat, (ent_key, used_key, carry_key) in LEAVE_COLS.items():
            lt = leave_types_map.get(cat)
            if not lt:
                continue
            entitled = _dec(row, ent_key)
            used     = _dec(row, used_key)
            carry    = _dec(row, carry_key)
            if entitled == 0:
                entitled = Decimal(str(_get_entitlement_days(company, emp, lt, year)))
            LeaveBalance._base_manager.create(
                company=company,
                employee=emp,
                leave_type=lt,
                year=year,
                total_days=entitled + carry,
                used_days=used,
                pending_days=0,
            )

        for msg in created_defs:
            self.stdout.write(self.style.SUCCESS(msg))

        self.stdout.write(self.style.SUCCESS(f"صف {idx}: تم إنشاء الموظف [{fname_ar} {lname_ar}] بنجاح"))

        # إرسال الإيميل
        if send_emails and email:
            try:
                act_link = self._make_activation_link(user)
                msg = (
                    f"مرحباً {fname_ar}،\n"
                    f"تم إنشاء حسابك في MotionHR.\n"
                    f"اسم المستخدم: {username}\n"
                    f"كلمة المرور المؤقتة: {temp_pass}\n"
                    f"رابط التفعيل (صالح 48 ساعة): {act_link}"
                )
                send_mail(
                    "مرحباً بك في MotionHR",
                    msg,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,
                )
            except Exception:
                pass

        return True

    # ─────────────────────────────────────────
    def _update_employee(self, row, company, emp_code, nat_id, idx):
        emp = None
        if emp_code:
            emp = Employee._base_manager.filter(employee_code=emp_code, company=company).first()
        if not emp and nat_id:
            emp = Employee._base_manager.filter(national_id=nat_id, company=company).first()

        if not emp:
            msg = f"صف {idx}: لم يتم العثور على الموظف (كود: {emp_code} | رقم قومي: {nat_id})"
            self.stdout.write(self.style.WARNING(msg))
            return False

        # تحديث الحقول اللي موجودة في الصف
        salary = _dec(row, "basic_salary")
        if salary:
            emp.basic_salary = salary

        contract_type = _str(row, "contract_type")
        if contract_type:
            emp.contract_type = contract_type

        status = _str(row, "status")
        if status:
            emp.status = status

        att_mode = _str(row, "attendance_mode")
        if att_mode:
            emp.attendance_mode = att_mode

        contract_start = _date(row, "contract_start_date")
        if contract_start:
            emp.contract_start_date = contract_start

        contract_end = _date(row, "contract_end_date")
        if contract_end:
            emp.contract_end_date = contract_end

        duration = _int(row, "contract_duration_months")
        if duration:
            emp.contract_duration_months = duration

        probation = _int(row, "probation_months")
        if probation:
            emp.probation_months = probation

        pay_method = _str(row, "salary_payment_method")
        if pay_method:
            emp.salary_payment_method = pay_method

        manager = self._resolve_manager(company, _str(row, "direct_manager_name"), _str(row, "direct_manager_department"))
        if manager:
            emp.direct_manager = manager

        emp.save()
        self.stdout.write(self.style.SUCCESS(f"صف {idx}: تم تحديث الموظف [{emp.first_name_ar} {emp.last_name_ar}]"))
        return True