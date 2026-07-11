#!/usr/bin/env python3
"""
Patch 26b: Repair Middleware + Seed Demo Data + Owner Guide
"""

import os
import sys
from datetime import date, datetime, timedelta, time
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 26b: Repair + Seed")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) إصلاح core/middleware.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح core/middleware.py...")

fixed_middleware = '''"""
Middleware للتحكم في Multi-tenant
"""

import threading

_thread_local = threading.local()


def get_current_company():
    return getattr(_thread_local, 'company', None)


def get_current_user():
    return getattr(_thread_local, 'user', None)


def set_current_company(company):
    _thread_local.company = company


def set_current_user(user):
    _thread_local.user = user


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)

            if hasattr(request.user, 'company') and request.user.company:
                set_current_company(request.user.company)
                request.current_company = request.user.company
            else:
                set_current_company(None)
                request.current_company = None
        else:
            set_current_user(None)
            set_current_company(None)
            request.current_company = None

        response = self.get_response(request)

        set_current_user(None)
        set_current_company(None)

        return response


class CurrentEmployeeMiddleware:
    """
    Middleware يضيف employee profile للـ request
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_employee = None

        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from employees.models import Employee
                request.current_employee = Employee.objects.filter(
                    user=request.user
                ).first()
            except Exception:
                pass

        response = self.get_response(request)
        return response


class SubscriptionMiddleware:
    """
    Middleware للتحقق من اشتراك الشركة
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.subscription = None
        request.subscription_features = set()
        request.subscription_valid = False
        request.days_remaining = 0

        if hasattr(request, 'user') and request.user.is_authenticated:
            # Super Admin يشوف كل حاجة
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                request.subscription_valid = True
                request.subscription_features = self._all_features()
            else:
                if hasattr(request.user, 'company') and request.user.company:
                    try:
                        from subscriptions.models import CompanySubscription
                        from django.utils import timezone

                        sub = CompanySubscription.objects.filter(
                            company=request.user.company
                        ).select_related('plan').first()

                        if sub:
                            request.subscription = sub

                            try:
                                request.subscription_valid = sub.is_valid
                            except Exception:
                                request.subscription_valid = (
                                    getattr(sub, 'status', '') in ['active', 'trial']
                                    and getattr(sub, 'end_date', timezone.now().date()) >= timezone.now().date()
                                )

                            try:
                                request.days_remaining = sub.days_remaining
                            except Exception:
                                end_date = getattr(sub, 'end_date', timezone.now().date())
                                if end_date >= timezone.now().date():
                                    request.days_remaining = (end_date - timezone.now().date()).days
                                else:
                                    request.days_remaining = 0

                            try:
                                request.subscription_features = sub.all_features
                            except Exception:
                                request.subscription_features = set()

                    except Exception:
                        pass

        response = self.get_response(request)
        return response

    def _all_features(self):
        try:
            from subscriptions.models import FeatureFlag
            return set(
                FeatureFlag.objects.filter(is_active=True).values_list('key', flat=True)
            )
        except Exception:
            return {
                'employee_management',
                'attendance_tracking',
                'gps_attendance',
                'field_tracking',
                'live_map',
                'location_visits',
                'reports_basic',
                'reports_advanced',
                'excel_export',
                'pdf_export',
                'login_by_employee_code',
                'login_by_phone',
                'leave_management',
                'multi_branch',
                'payroll_basic',
            }
'''
write_file(os.path.join(BASE_DIR, "core", "middleware.py"), fixed_middleware)

# دلوقتي نجهز Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")
import django
django.setup()

# helpers
def model_field_names(model):
    return {f.name for f in model._meta.fields}

def has_field(model, field_name):
    return field_name in model_field_names(model)

def set_if_exists(kwargs, model, field_name, value):
    if has_field(model, field_name):
        kwargs[field_name] = value

def get_choice_key(model, field_name, preferred):
    try:
        field = model._meta.get_field(field_name)
        choices = getattr(field, "choices", None)
        if not choices:
            return preferred[0] if preferred else None
        keys = [c[0] for c in choices]
        for item in preferred:
            if item in keys:
                return item
        return keys[0] if keys else None
    except Exception:
        return preferred[0] if preferred else None

# imports
from django.contrib.auth import get_user_model
from companies.models import Company, Branch, Department
from attendance.models import Shift

User = get_user_model()

try:
    from employees.models import Employee, JobTitle
except Exception:
    Employee = None
    JobTitle = None

try:
    from subscriptions.models import SubscriptionPlan, CompanySubscription
except Exception:
    SubscriptionPlan = None
    CompanySubscription = None

try:
    from leaves.models import LeaveType, LeaveBalance, LeaveRequest
except Exception:
    LeaveType = None
    LeaveBalance = None
    LeaveRequest = None

try:
    from attendance.models import Attendance, LocationLog, LocationCheckIn
except Exception:
    Attendance = None
    LocationLog = None
    LocationCheckIn = None

# ════════════════════════════════════════════════════════════
# 2) بيانات ديمو
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء بيانات ديمو...")

# الشركة
company = Company.objects.filter(name_ar="شركة الاختبار").first()
if not company:
    company = Company.objects.create(
        name_ar="شركة الاختبار",
        name_en="Test Company",
        email="test@company.com",
        phone="01000000000",
        address="القاهرة، مصر",
    )
    print("  ✅ تم إنشاء شركة الاختبار")
else:
    print("  ℹ️  شركة الاختبار موجودة")

# Super Admin
super_admin = User.objects.filter(is_superuser=True).first()
if super_admin:
    if hasattr(super_admin, "company"):
        super_admin.company = company
    if hasattr(super_admin, "role"):
        super_admin.role = "super_admin"
    super_admin.save()
    print(f"  ✅ Super Admin: {super_admin.username}")

# Demo Admin
demo_admin, created = User.objects.get_or_create(
    username="demo_admin",
    defaults={
        "email": "demo@motionhr.local",
        "first_name": "Demo",
        "last_name": "Admin",
        "is_active": True,
        "is_staff": True,
    }
)
demo_admin.set_password("Demo@12345")
if hasattr(demo_admin, "company"):
    demo_admin.company = company
if hasattr(demo_admin, "role"):
    demo_admin.role = "company_admin"
demo_admin.is_staff = True
demo_admin.save()
print("  ✅ Company Admin جاهز")
print("     username: demo_admin")
print("     password: Demo@12345")

# الاشتراك
if SubscriptionPlan and CompanySubscription:
    plan = SubscriptionPlan.objects.filter(name_en="Business").first()
    if not plan:
        plan_kwargs = {}
        set_if_exists(plan_kwargs, SubscriptionPlan, "name_ar", "الأعمال")
        set_if_exists(plan_kwargs, SubscriptionPlan, "name_en", "Business")
        set_if_exists(plan_kwargs, SubscriptionPlan, "tier", get_choice_key(SubscriptionPlan, "tier", ["business", "professional", "starter"]))
        set_if_exists(plan_kwargs, SubscriptionPlan, "description", "خطة ديمو")
        set_if_exists(plan_kwargs, SubscriptionPlan, "price_monthly", Decimal("599"))
        set_if_exists(plan_kwargs, SubscriptionPlan, "price_yearly", Decimal("5999"))
        set_if_exists(plan_kwargs, SubscriptionPlan, "max_employees", 50)
        set_if_exists(plan_kwargs, SubscriptionPlan, "max_branches", 5)
        set_if_exists(plan_kwargs, SubscriptionPlan, "max_departments", 20)
        set_if_exists(plan_kwargs, SubscriptionPlan, "is_trial", False)
        set_if_exists(plan_kwargs, SubscriptionPlan, "trial_days", 14)
        set_if_exists(plan_kwargs, SubscriptionPlan, "color", "#06B6D4")
        set_if_exists(plan_kwargs, SubscriptionPlan, "is_featured", True)
        set_if_exists(plan_kwargs, SubscriptionPlan, "is_active", True)
        set_if_exists(plan_kwargs, SubscriptionPlan, "order", 2)
        plan = SubscriptionPlan.objects.create(**plan_kwargs)
        print("  ✅ تم إنشاء الخطة")
    else:
        print("  ℹ️  الخطة موجودة")

    sub = CompanySubscription.objects.filter(company=company).first()
    if not sub:
        sub_kwargs = {"company": company, "plan": plan}
        set_if_exists(sub_kwargs, CompanySubscription, "start_date", date.today() - timedelta(days=5))
        set_if_exists(sub_kwargs, CompanySubscription, "end_date", date.today() + timedelta(days=365))
        set_if_exists(sub_kwargs, CompanySubscription, "status", get_choice_key(CompanySubscription, "status", ["active", "trial"]))
        set_if_exists(sub_kwargs, CompanySubscription, "billing_cycle", get_choice_key(CompanySubscription, "billing_cycle", ["monthly", "yearly"]))
        set_if_exists(sub_kwargs, CompanySubscription, "is_trial", False)
        set_if_exists(sub_kwargs, CompanySubscription, "grace_period_days", 7)
        set_if_exists(sub_kwargs, CompanySubscription, "price_paid", Decimal("599"))
        set_if_exists(sub_kwargs, CompanySubscription, "discount", Decimal("0"))
        set_if_exists(sub_kwargs, CompanySubscription, "notes", "اشتراك ديمو")
        sub = CompanySubscription.objects.create(**sub_kwargs)
        print("  ✅ تم إنشاء الاشتراك")
    else:
        if hasattr(sub, "status"):
            sub.status = get_choice_key(CompanySubscription, "status", ["active", "trial"]) or "active"
        if hasattr(sub, "start_date"):
            sub.start_date = date.today() - timedelta(days=5)
        if hasattr(sub, "end_date"):
            sub.end_date = date.today() + timedelta(days=365)
        if hasattr(sub, "billing_cycle"):
            sub.billing_cycle = get_choice_key(CompanySubscription, "billing_cycle", ["monthly", "yearly"]) or "monthly"
        if hasattr(sub, "price_paid"):
            sub.price_paid = Decimal("599")
        sub.save()
        print("  ✅ تم تحديث الاشتراك")

# الفروع
branch1 = Branch.objects.filter(company=company, name_ar="المقر الرئيسي").first()
if not branch1:
    branch1 = Branch.objects.create(
        company=company,
        name_ar="المقر الرئيسي",
        name_en="Head Office",
        address="القاهرة",
        phone="01000000001",
        latitude=30.0444,
        longitude=31.2357,
        check_in_radius=500,
        is_main=True,
        is_active=True,
    )
    print("  ✅ تم إنشاء المقر الرئيسي")

branch2 = Branch.objects.filter(company=company, name_ar="فرع الجيزة").first()
if not branch2:
    branch2 = Branch.objects.create(
        company=company,
        name_ar="فرع الجيزة",
        name_en="Giza Branch",
        address="الجيزة",
        phone="01000000002",
        latitude=30.0131,
        longitude=31.2089,
        check_in_radius=400,
        is_main=False,
        is_active=True,
    )
    print("  ✅ تم إنشاء فرع الجيزة")

# الإدارات
hr_dept = Department.objects.filter(company=company, code="HR").first()
if not hr_dept:
    hr_dept = Department.objects.create(company=company, name_ar="الموارد البشرية", name_en="HR", code="HR", is_active=True)

sales_dept = Department.objects.filter(company=company, code="SALES").first()
if not sales_dept:
    sales_dept = Department.objects.create(company=company, name_ar="المبيعات", name_en="Sales", code="SALES", is_active=True)

it_dept = Department.objects.filter(company=company, code="IT").first()
if not it_dept:
    it_dept = Department.objects.create(company=company, name_ar="تقنية المعلومات", name_en="IT", code="IT", is_active=True)

print("  ✅ تم تجهيز الإدارات")

# الشيفت
shift = Shift.objects.filter(company=company, name="شيفت صباحي").first()
if not shift:
    shift = Shift.objects.create(
        company=company,
        name="شيفت صباحي",
        shift_type=get_choice_key(Shift, "shift_type", ["fixed", "flexible"]) or "fixed",
        start_time=time(8, 0),
        end_time=time(17, 0),
        grace_period=15,
        break_duration=60,
        work_sunday=True,
        work_monday=True,
        work_tuesday=True,
        work_wednesday=True,
        work_thursday=True,
        work_friday=False,
        work_saturday=False,
    )
print("  ✅ تم تجهيز الشيفت")

# Job Titles
job_titles = {}
if JobTitle:
    for ar, en in [
        ("مطور برامج", "Software Developer"),
        ("أخصائي موارد بشرية", "HR Specialist"),
        ("مندوب مبيعات", "Sales Rep"),
        ("محاسب", "Accountant"),
    ]:
        jt = JobTitle.objects.filter(company=company, name_ar=ar).first()
        if not jt:
            kwargs = {"company": company}
            set_if_exists(kwargs, JobTitle, "name_ar", ar)
            set_if_exists(kwargs, JobTitle, "name_en", en)
            set_if_exists(kwargs, JobTitle, "is_active", True)
            jt = JobTitle.objects.create(**kwargs)
        job_titles[ar] = jt
    print("  ✅ تم تجهيز المسميات الوظيفية")

# Employees
created_employees = []
if Employee:
    emp_status = get_choice_key(Employee, "status", ["active"]) or "active"
    emp_gender_m = get_choice_key(Employee, "gender", ["male", "m"]) or None
    emp_gender_f = get_choice_key(Employee, "gender", ["female", "f"]) or emp_gender_m
    emp_marital = get_choice_key(Employee, "marital_status", ["single"]) or None
    emp_contract = get_choice_key(Employee, "contract_type", ["permanent", "full_time"]) or None
    emp_religion = get_choice_key(Employee, "religion", ["muslim"]) or None

    demo_employees = [
        ("EMP10001", "أحمد", "محمد", "علي", "Ahmed", "Ali", emp_gender_m, it_dept, branch1, job_titles.get("مطور برامج"), Decimal("12000"), False, "01010000001", "ahmed@demo.local"),
        ("EMP10002", "سارة", "أحمد", "حسن", "Sara", "Hassan", emp_gender_f, hr_dept, branch1, job_titles.get("أخصائي موارد بشرية"), Decimal("9000"), False, "01010000002", "sara@demo.local"),
        ("EMP10003", "محمد", "السيد", "فتحي", "Mohamed", "Fathy", emp_gender_m, sales_dept, branch2, job_titles.get("مندوب مبيعات"), Decimal("7000"), True, "01010000003", "mohamed@demo.local"),
        ("EMP10004", "محمود", "عادل", "جابر", "Mahmoud", "Gaber", emp_gender_m, sales_dept, branch2, job_titles.get("مندوب مبيعات"), Decimal("7200"), True, "01010000004", "mahmoud@demo.local"),
        ("EMP10005", "منة", "طارق", "خالد", "Mena", "Khaled", emp_gender_f, hr_dept, branch1, job_titles.get("محاسب") or job_titles.get("أخصائي موارد بشرية"), Decimal("8500"), False, "01010000005", "mena@demo.local"),
    ]

    for idx, info in enumerate(demo_employees, start=1):
        code, f_ar, m_ar, l_ar, f_en, l_en, gender, dept, branch, title, salary, is_field, phone, email = info

        emp_user = User.objects.filter(username=code.lower()).first()
        if not emp_user:
            emp_user = User.objects.create_user(
                username=code.lower(),
                password="Emp@12345",
                email=email,
                first_name=f_ar,
                last_name=l_ar,
            )

        if hasattr(emp_user, "company"):
            emp_user.company = company
        if hasattr(emp_user, "role"):
            emp_user.role = "employee"
        if hasattr(emp_user, "phone"):
            emp_user.phone = phone
        emp_user.save()

        emp = Employee.objects.filter(company=company, employee_code=code).first()
        if emp:
            created_employees.append(emp)
            continue

        kwargs = {}
        set_if_exists(kwargs, Employee, "company", company)
        set_if_exists(kwargs, Employee, "user", emp_user)
        set_if_exists(kwargs, Employee, "employee_code", code)
        set_if_exists(kwargs, Employee, "first_name_ar", f_ar)
        set_if_exists(kwargs, Employee, "middle_name_ar", m_ar)
        set_if_exists(kwargs, Employee, "last_name_ar", l_ar)
        set_if_exists(kwargs, Employee, "first_name_en", f_en)
        set_if_exists(kwargs, Employee, "last_name_en", l_en)
        set_if_exists(kwargs, Employee, "national_id", f"2990101{idx:07d}")
        set_if_exists(kwargs, Employee, "birth_date", date(1992, min(idx, 12), 10))
        set_if_exists(kwargs, Employee, "gender", gender)
        set_if_exists(kwargs, Employee, "marital_status", emp_marital)
        set_if_exists(kwargs, Employee, "religion", emp_religion)
        set_if_exists(kwargs, Employee, "nationality", "مصري")
        set_if_exists(kwargs, Employee, "email", email)
        set_if_exists(kwargs, Employee, "phone", phone)
        set_if_exists(kwargs, Employee, "address", "القاهرة، مصر")
        set_if_exists(kwargs, Employee, "city", "القاهرة")
        set_if_exists(kwargs, Employee, "hire_date", date.today() - timedelta(days=30 * idx))
        set_if_exists(kwargs, Employee, "contract_type", emp_contract)
        set_if_exists(kwargs, Employee, "branch", branch)
        set_if_exists(kwargs, Employee, "department", dept)
        set_if_exists(kwargs, Employee, "job_title", title)
        set_if_exists(kwargs, Employee, "basic_salary", salary)
        set_if_exists(kwargs, Employee, "has_insurance", False)
        set_if_exists(kwargs, Employee, "emergency_contact_name", "قريب")
        set_if_exists(kwargs, Employee, "emergency_contact_relation", "أخ")
        set_if_exists(kwargs, Employee, "emergency_contact_phone", f"01120000{idx:03d}")
        set_if_exists(kwargs, Employee, "status", emp_status)
        set_if_exists(kwargs, Employee, "notes", "بيانات ديمو")
        set_if_exists(kwargs, Employee, "is_field_worker", is_field)

        emp = Employee.objects.create(**kwargs)
        created_employees.append(emp)

    print(f"  ✅ تم تجهيز {len(created_employees)} موظفين")

# Attendance
if Attendance and created_employees:
    status_present = get_choice_key(Attendance, "status", ["present"]) or "present"
    status_late = get_choice_key(Attendance, "status", ["late", "present"]) or "present"
    status_absent = get_choice_key(Attendance, "status", ["absent", "present"]) or "present"

    count = 0
    for ei, emp in enumerate(created_employees, start=1):
        for day_back in range(1, 6):
            att_date = date.today() - timedelta(days=day_back)
            if Attendance.objects.filter(company=company, employee=emp, date=att_date).exists():
                continue

            st = status_present
            late_m = 0
            ci = time(8, 5)
            co = time(17, 0)
            wh = Decimal("8.0")

            if day_back == 2 and ei % 2 == 0:
                st = status_late
                late_m = 25
                ci = time(8, 25)
                wh = Decimal("7.6")
            elif day_back == 4 and ei == 5:
                st = status_absent
                ci = None
                co = None
                wh = Decimal("0.0")

            kwargs = {"company": company}
            set_if_exists(kwargs, Attendance, "employee", emp)
            set_if_exists(kwargs, Attendance, "date", att_date)
            set_if_exists(kwargs, Attendance, "shift", shift)
            set_if_exists(kwargs, Attendance, "status", st)
            if ci:
                set_if_exists(kwargs, Attendance, "check_in_time", ci)
            if co:
                set_if_exists(kwargs, Attendance, "check_out_time", co)
            set_if_exists(kwargs, Attendance, "work_hours", wh)
            set_if_exists(kwargs, Attendance, "late_minutes", late_m)
            set_if_exists(kwargs, Attendance, "early_leave_minutes", 0)
            set_if_exists(kwargs, Attendance, "overtime_hours", Decimal("0.0"))
            set_if_exists(kwargs, Attendance, "check_in_latitude", Decimal("30.0444"))
            set_if_exists(kwargs, Attendance, "check_in_longitude", Decimal("31.2357"))
            set_if_exists(kwargs, Attendance, "check_in_address", "القاهرة")
            set_if_exists(kwargs, Attendance, "within_range", True)

            try:
                Attendance.objects.create(**kwargs)
                count += 1
            except Exception:
                pass

    print(f"  ✅ تم تجهيز {count} سجل حضور")

# Leaves
if LeaveType and LeaveBalance and LeaveRequest and created_employees:
    annual = LeaveType.objects.filter(company=company, name="إجازة سنوية").first()
    if not annual:
        annual = LeaveType.objects.create(
            company=company,
            name="إجازة سنوية",
            category=get_choice_key(LeaveType, "category", ["annual", "other"]) or "other",
            days_allowed=21,
            is_paid=True,
            requires_approval=True,
            requires_document=False,
            carry_forward=True,
            max_carry_days=7,
            color="#06B6D4",
            is_active=True,
            description="إجازة سنوية مدفوعة",
        )

    sick = LeaveType.objects.filter(company=company, name="إجازة مرضية").first()
    if not sick:
        sick = LeaveType.objects.create(
            company=company,
            name="إجازة مرضية",
            category=get_choice_key(LeaveType, "category", ["sick", "other"]) or "other",
            days_allowed=10,
            is_paid=True,
            requires_approval=True,
            requires_document=True,
            carry_forward=False,
            max_carry_days=0,
            color="#e91e63",
            is_active=True,
            description="إجازة مرضية",
        )

    current_year = date.today().year
    for emp in created_employees:
        LeaveBalance.objects.get_or_create(
            company=company,
            employee=emp,
            leave_type=annual,
            year=current_year,
            defaults={
                "total_days": Decimal("21"),
                "used_days": Decimal("2"),
                "pending_days": Decimal("1"),
            }
        )

    if not LeaveRequest.objects.filter(company=company).exists():
        reqs = [
            (created_employees[0], annual, "pending", date.today() + timedelta(days=3), date.today() + timedelta(days=5), "سفر عائلي"),
            (created_employees[1], sick, "approved", date.today() - timedelta(days=10), date.today() - timedelta(days=9), "نزلة برد"),
            (created_employees[2], annual, "rejected", date.today() + timedelta(days=7), date.today() + timedelta(days=8), "ظروف خاصة"),
        ]
        for emp, lt, st, s, e, reason in reqs:
            lr = LeaveRequest.objects.create(
                company=company,
                employee=emp,
                leave_type=lt,
                start_date=s,
                end_date=e,
                days_count=Decimal((e - s).days + 1),
                reason=reason,
                status=get_choice_key(LeaveRequest, "status", [st, "pending"]) or st,
                notes="بيانات ديمو",
            )
            if st in ["approved", "rejected"] and super_admin:
                lr.reviewed_by = super_admin
                lr.reviewed_at = datetime.now()
                lr.review_notes = "تمت المراجعة"
                lr.save()

    print("  ✅ تم تجهيز الإجازات")

# Field Tracking
if LocationLog and created_employees:
    field_emps = [e for e in created_employees if getattr(e, "is_field_worker", False)]
    for idx, emp in enumerate(field_emps, start=1):
        if not LocationLog.objects.filter(company=company, employee=emp).exists():
            for p in range(3):
                kwargs = {"company": company}
                set_if_exists(kwargs, LocationLog, "employee", emp)
                set_if_exists(kwargs, LocationLog, "timestamp", datetime.now() - timedelta(minutes=10 * p))
                set_if_exists(kwargs, LocationLog, "latitude", Decimal("30.0500") + Decimal(f"0.000{idx+p}"))
                set_if_exists(kwargs, LocationLog, "longitude", Decimal("31.2400") + Decimal(f"0.000{idx+p}"))
                set_if_exists(kwargs, LocationLog, "accuracy", Decimal("10.0"))
                set_if_exists(kwargs, LocationLog, "speed", Decimal("18.5"))
                set_if_exists(kwargs, LocationLog, "battery_level", 80 - p * 5)
                set_if_exists(kwargs, LocationLog, "address", "القاهرة")
                try:
                    LocationLog.objects.create(**kwargs)
                except Exception:
                    pass

if LocationCheckIn and created_employees:
    field_emps = [e for e in created_employees if getattr(e, "is_field_worker", False)]
    visit_type = get_choice_key(LocationCheckIn, "visit_type", ["client_visit", "meeting", "other"])
    visit_status = get_choice_key(LocationCheckIn, "status", ["completed", "arrived", "in_progress"])

    for idx, emp in enumerate(field_emps, start=1):
        if not LocationCheckIn.objects.filter(company=company, employee=emp).exists():
            kwargs = {"company": company}
            set_if_exists(kwargs, LocationCheckIn, "employee", emp)
            set_if_exists(kwargs, LocationCheckIn, "visit_type", visit_type or "client_visit")
            set_if_exists(kwargs, LocationCheckIn, "location_name", f"عميل رقم {idx}")
            set_if_exists(kwargs, LocationCheckIn, "arrival_time", datetime.now() - timedelta(hours=idx))
            set_if_exists(kwargs, LocationCheckIn, "departure_time", datetime.now() - timedelta(minutes=30 * idx))
            set_if_exists(kwargs, LocationCheckIn, "arrival_latitude", Decimal("30.0600"))
            set_if_exists(kwargs, LocationCheckIn, "arrival_longitude", Decimal("31.2500"))
            set_if_exists(kwargs, LocationCheckIn, "departure_latitude", Decimal("30.0610"))
            set_if_exists(kwargs, LocationCheckIn, "departure_longitude", Decimal("31.2510"))
            set_if_exists(kwargs, LocationCheckIn, "purpose", "زيارة عميل")
            set_if_exists(kwargs, LocationCheckIn, "notes", "بيانات ديمو")
            set_if_exists(kwargs, LocationCheckIn, "status", visit_status or "completed")
            try:
                LocationCheckIn.objects.create(**kwargs)
            except Exception:
                pass

print("  ✅ تم تجهيز التتبع الميداني")

# ════════════════════════════════════════════════════════════
# 3) Owner Guide
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء START_HERE_OWNER_GUIDE.md...")

guide_lines = [
    "# START HERE - MotionHR Owner Guide",
    "",
    "## أنا أفتح المشروع منين؟",
    "",
    "### 1) الصفحة العامة",
    "- http://127.0.0.1:8000/",
    "",
    "### 2) تسجيل دخول العميل",
    "- http://127.0.0.1:8000/login/",
    "",
    "### 3) لوحة الأدمن",
    "- http://127.0.0.1:8000/admin/",
    "",
    "### 4) لوحة الاستخدام",
    "- http://127.0.0.1:8000/dashboard/",
    "",
    "## أفتح من الموبايل إزاي؟",
    "1. شغّل السيرفر:",
    "```bash",
    "python manage.py runserver 0.0.0.0:8000",
    "```",
    "2. افتح من الموبايل:",
    "```text",
    "http://192.168.1.45:8000",
    "```",
    "",
    "## أدي العميل إيه؟",
    "- رابط الدخول",
    "- اسم المستخدم",
    "- كلمة المرور",
    "",
    "## بيانات الديمو الحالية",
    "",
    "### Company Admin",
    "- username: demo_admin",
    "- password: Demo@12345",
    "",
    "### Employee",
    "- username: emp10001",
    "- password: Emp@12345",
    "",
    "## أهم صفحات الديمو",
    "- /",
    "- /login/",
    "- /dashboard/",
    "- /employees/",
    "- /attendance/check-in/",
    "- /attendance/map/",
    "- /leaves/",
    "- /reports/",
    "- /subscriptions/my-plan/",
    "",
    "## إنت بتبيع إيه؟",
    "- إدارة الموظفين",
    "- حضور GPS",
    "- تتبع ميداني Live",
    "- إدارة الإجازات",
    "- تقارير الإدارة",
]

create_file(
    os.path.join(BASE_DIR, "START_HERE_OWNER_GUIDE.md"),
    "\\n".join(guide_lines)
)

print("\\n" + "=" * 60)
print("  ✅ Patch 26b اكتمل!")
print("=" * 60)
print("\n" + "=" * 60)
print("  Patch 26b اكتمل!")
print("=" * 60)
print("")
print("بيانات الدخول:")
print("")
print("Company Admin")
print("  username: demo_admin")
print("  password: Demo@12345")
print("")
print("Employee")
print("  username: emp10001")
print("  password: Emp@12345")
print("")
print("الخطوات الجاية:")
print("1) python manage.py check")
print("2) python manage.py runserver 0.0.0.0:8000")
print("3) http://127.0.0.1:8000/login/")
print("4) demo_admin / Demo@12345")
