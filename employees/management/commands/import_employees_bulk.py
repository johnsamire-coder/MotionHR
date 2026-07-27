"""
Management Command: import_employees_bulk
استيراد الموظفين من شيت Excel (مع دعم توليد أرصدة الإجازات وإرسال الإيميلات).
"""
import os
import random
import string
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from openpyxl import load_workbook

# App Imports
from accounts.models import User
from employees.models import Employee, JobTitle
from companies.models import Branch, Department
from leaves.models import LeaveType, LeaveBalance
from leaves.signals import _get_entitlement_days  # عشان نحسب الرصيد من السياسة
from employees.account_utils import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'استيراد الموظفين من ملف Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='مسار ملف الـ Excel'
        )
        parser.add_argument(
            '--send-emails',
            action='store_true',
            help='إرسال إيميلات التفعيل للموظفين الجدد (إذا توافر الإيميل)'
        )

    def generate_random_password(self, length=8):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _make_activation_link(self, user):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        site_url = getattr(settings, 'SITE_URL', 'https://motion.jssolutions-eg.com')
        return f"{site_url}/password-reset-confirm/{uid}/{token}/"

    def handle(self, *args, **options):
        file_path = options['file']
        send_emails = options['send_emails']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"الملف غير موجود: {file_path}"))
            return

        try:
            wb = load_workbook(file_path)
            ws = wb['الموظفين']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطأ في قراءة ملف الإكسيل: {e}"))
            return

        # افتراض الشركة الأولى (لأن الـ Command بيشتغل على مستوى السيرفر)
        from companies.models import Company
        company = Company.objects.first()
        if not company:
            self.stdout.write(self.style.ERROR("لا توجد شركة مسجلة في النظام!"))
            return

        # قاموس لحفظ الأنواع والأرصدة
        leave_types_map = {lt.category: lt for lt in LeaveType.objects.filter(company=company, is_active=True)}
        
        # تخطي أول 3 صفوف (العناوين)
        rows = list(ws.iter_rows(min_row=4, values_only=True))
        
        success_count = 0
        update_count = 0
        error_count = 0

        for idx, row in enumerate(rows, start=4):
            # التأكد إن الصف مش فاضي
            if not row[0]: 
                continue

            op_type = str(row[0]).strip().lower()
            emp_code = str(row[1]).strip() if row[1] else None
            temp_pass = str(row[2]).strip() if row[2] else self.generate_random_password()

            # استخراج الحقول الإلزامية
            fname_ar = row[3]
            lname_ar = row[5]
            fname_en = row[6]
            lname_en = row[7]
            national_id = str(row[8]).strip() if row[8] else None
            birth_date = row[10]
            gender = str(row[11]).strip().lower() if row[11] else 'male'
            
            phone = str(row[17]).strip() if row[17] else None
            email = str(row[19]).strip() if row[19] else None
            
            branch_name = row[25]
            dept_name = row[26]
            job_name = row[27]
            hire_date = row[29]
            att_mode = str(row[30]).strip() if row[30] else 'fixed_shift'
            contract_type = str(row[31]).strip() if row[31] else 'permanent'
            
            # فلترة وتحقق سريع
            if op_type == 'new' and not (fname_ar and lname_ar and national_id and phone and hire_date and branch_name and dept_name and job_name):
                self.stdout.write(self.style.WARNING(f"صف {idx}: بيانات إلزامية ناقصة للموظف الجديد. تم التخطي."))
                error_count += 1
                continue

            try:
                with transaction.atomic():
                    # البحث عن الفرع والقسم والمسمى
                    branch, _ = Branch.objects.get_or_create(company=company, name_ar=branch_name)
                    dept, _ = Department.objects.get_or_create(company=company, branch=branch, name_ar=dept_name)
                    job, _ = JobTitle.objects.get_or_create(company=company, department=dept, name_ar=job_name)

                    if op_type == 'new':
                        # 1. كريت User
                        username = f"emp{national_id[-6:]}{random.randint(10,99)}"
                        user = User.objects.create_user(
                            username=username,
                            password=temp_pass,
                            email=email or "",
                            first_name=fname_ar,
                            last_name=lname_ar,
                            company=company,
                            role='employee'
                        )

                        # 2. كريت Employee
                        emp = Employee.objects.create(
                            company=company,
                            user=user,
                            employee_code=emp_code or f"EMP{user.id}",
                            first_name_ar=fname_ar,
                            middle_name_ar=row[4],
                            last_name_ar=lname_ar,
                            first_name_en=fname_en,
                            last_name_en=lname_en,
                            national_id=national_id,
                            passport_number=row[9],
                            birth_date=birth_date,
                            gender='female' if gender == 'أنثى' else 'male',
                            marital_status=row[12],
                            religion=row[13],
                            nationality=row[14] or 'مصري',
                            language='en' if row[15] == 'en' else 'ar',
                            phone=phone,
                            phone2=row[18],
                            email=email,
                            address=row[20],
                            city=row[21],
                            emergency_contact_name=row[22],
                            emergency_contact_relation=row[23],
                            emergency_contact_phone=row[24],
                            branch=branch,
                            department=dept,
                            job_title=job,
                            hire_date=hire_date,
                            attendance_mode=att_mode,
                            contract_type=contract_type,
                            contract_start_date=row[32] or hire_date,
                            contract_end_date=row[33],
                            contract_duration_months=row[34],
                            probation_months=row[35] or 3,
                            has_insurance=True if row[36] == 'نعم' else False,
                            insurance_number=row[37],
                            basic_salary=row[38],
                            currency=row[39] or 'EGP',
                            salary_payment_method=row[40] or 'cash',
                            bank_name=row[41],
                            bank_account=row[42],
                            iban=row[44],
                            instapay_phone=row[45],
                            wallet_phone=row[46],
                            wallet_provider=row[47]
                        )
                        
                        # 3. إعداد الأرصدة الافتتاحية
                        year = timezone.now().year
                        
                        # Mapping بين الإكسيل والـ Categories
                        leave_cols = {
                            'annual': (47, 48, 49),
                            'sick': (50, 51, 52),
                            'emergency': (53, 54, 55),
                            'maternity': (56, 57, 58),
                            'paternity': (59, 60, 61),
                            'unpaid': (62, 63, 64)
                        }

                        for cat, (ent_col, used_col, carry_col) in leave_cols.items():
                            lt = leave_types_map.get(cat)
                            if not lt: continue
                            
                            entitled = Decimal(str(row[ent_col] or 0))
                            used = Decimal(str(row[used_col] or 0))
                            carry = Decimal(str(row[carry_col] or 0))

                            # لو مسجلش استحقاق في الإكسيل، نحسبه من السياسة
                            if entitled == 0:
                                entitled = Decimal(str(_get_entitlement_days(company, emp, lt, year)))

                            # إنشاء الرصيد
                            LeaveBalance._base_manager.create(
                                company=company,
                                employee=emp,
                                leave_type=lt,
                                year=year,
                                total_days=entitled + carry,
                                used_days=used,
                                pending_days=0
                            )

                        success_count += 1

                        # 4. إرسال الإيميل (اختياري)
                        if send_emails and email:
                            act_link = self._make_activation_link(user)
                            msg = f"""مرحباً {fname_ar}،
تم إنشاء حسابك في MotionHR.
اسم المستخدم: {username}
كلمة المرور المؤقتة: {temp_pass}
رابط التفعيل (صالح 48 ساعة): {act_link}"""
                            try:
                                send_mail(
                                    'مرحباً بك في MotionHR',
                                    msg,
                                    settings.DEFAULT_FROM_EMAIL,
                                    [email],
                                    fail_silently=True
                                )
                            except Exception:
                                pass

                    elif op_type == 'update':
                        # تحديث بيانات الموظف الحالي
                        emp = Employee._base_manager.filter(employee_code=emp_code, company=company).first()
                        if not emp:
                            emp = Employee._base_manager.filter(national_id=national_id, company=company).first()
                        
                        if emp:
                            # تحديث الحقول الأساسية كمثال
                            if basic_salary: emp.basic_salary = basic_salary
                            if contract_type: emp.contract_type = contract_type
                            emp.save()
                            update_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"صف {idx}: لم يتم العثور على الموظف للتحديث."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"صف {idx}: فشل الاستيراد - {e}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f"تم الانتهاء! جديد: {success_count} | تحديث: {update_count} | أخطاء: {error_count}"))

