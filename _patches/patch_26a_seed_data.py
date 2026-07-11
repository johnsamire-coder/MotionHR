#!/usr/bin/env python3
"""
Patch 26a: Seed Data Only
"""

import os
import sys
from datetime import date, datetime, timedelta, time
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


def set_if_exists(kwargs, model, field_name, value):
    names = {f.name for f in model._meta.fields}
    if field_name in names:
        kwargs[field_name] = value


def get_choice_key(model, field_name, preferred_list):
    try:
        field = model._meta.get_field(field_name)
        choices = getattr(field, "choices", None)
        if not choices:
            return preferred_list[0] if preferred_list else None
        keys = [c[0] for c in choices]
        for item in preferred_list:
            if item in keys:
                return item
        return keys[0] if keys else None
    except Exception:
        return preferred_list[0] if preferred_list else None


print("=" * 60)
print("  Patch 26a: Seed Data")
print("=" * 60)

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


# ── الشركة ──
print("\n🏢 الشركة...")
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
    print("  ℹ️  موجودة")

# ── Super Admin ──
super_admin = User.objects.filter(is_superuser=True).first()
if super_admin:
    super_admin.company = company
    if hasattr(super_admin, "role"):
        super_admin.role = "super_admin"
    super_admin.save()
    print(f"  ✅ Super Admin: {super_admin.username}")

# ── Demo Admin ──
print("\n👤 Demo Admin...")
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
print("  ✅ username: demo_admin")
print("  ✅ password: Demo@12345")

# ── الاشتراك ──
print("\n💳 الاشتراك...")
if SubscriptionPlan and CompanySubscription:
    plan = SubscriptionPlan.objects.filter(name_en="Business").first()
    if not plan:
        plan_kwargs = {}
        set_if_exists(plan_kwargs, SubscriptionPlan, "name_ar", "الأعمال")
        set_if_exists(plan_kwargs, SubscriptionPlan, "name_en", "Business")
        set_if_exists(plan_kwargs, SubscriptionPlan, "tier", get_choice_key(SubscriptionPlan, "tier", ["business", "professional", "starter"]))
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
        sub = CompanySubscription.objects.create(**sub_kwargs)
        print("  ✅ تم إنشاء الاشتراك")
    else:
        if hasattr(sub, "status"):
            sub.status = get_choice_key(CompanySubscription, "status", ["active", "trial"]) or "active"
        if hasattr(sub, "start_date"):
            sub.start_date = date.today() - timedelta(days=5)
        if hasattr(sub, "end_date"):
            sub.end_date = date.today() + timedelta(days=365)
        if hasattr(sub, "price_paid"):
            sub.price_paid = Decimal("599")
        sub.save()
        print("  ✅ تم تحديث الاشتراك")

# ── الفروع ──
print("\n🏗️  الفروع...")
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
    print("  ✅ المقر الرئيسي")
else:
    print("  ℹ️  المقر الرئيسي موجود")

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
    print("  ✅ فرع الجيزة")

# ── الإدارات ──
print("\n🏛️  الإدارات...")
hr_dept = Department.objects.filter(company=company, code="HR").first()
if not hr_dept:
    hr_dept = Department.objects.create(
        company=company, name_ar="الموارد البشرية",
        name_en="HR", code="HR", is_active=True,
    )
    print("  ✅ الموارد البشرية")
else:
    print("  ℹ️  HR موجود")

sales_dept = Department.objects.filter(company=company, code="SALES").first()
if not sales_dept:
    sales_dept = Department.objects.create(
        company=company, name_ar="المبيعات",
        name_en="Sales", code="SALES", is_active=True,
    )
    print("  ✅ المبيعات")

it_dept = Department.objects.filter(company=company, code="IT").first()
if not it_dept:
    it_dept = Department.objects.create(
        company=company, name_ar="تقنية المعلومات",
        name_en="IT", code="IT", is_active=True,
    )
    print("  ✅ IT")

# ── الشيفت ──
print("\n⏰ الشيفت...")
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
    print("  ✅ شيفت صباحي")
else:
    print("  ℹ️  موجود")

# ── المسميات الوظيفية ──
print("\n💼 المسميات الوظيفية...")
job_titles = {}
if JobTitle:
    jt_data = [
        ("مطور برامج", "Software Developer"),
        ("أخصائي موارد بشرية", "HR Specialist"),
        ("مندوب مبيعات", "Sales Rep"),
        ("محاسب", "Accountant"),
    ]
    for ar, en in jt_data:
        jt = JobTitle.objects.filter(company=company, name_ar=ar).first()
        if not jt:
            kwargs = {"company": company}
            set_if_exists(kwargs, JobTitle, "name_ar", ar)
            set_if_exists(kwargs, JobTitle, "name_en", en)
            set_if_exists(kwargs, JobTitle, "is_active", True)
            jt = JobTitle.objects.create(**kwargs)
        job_titles[ar] = jt
    print(f"  ✅ {len(job_titles)} مسمى وظيفي")

# ── الموظفون ──
print("\n👥 الموظفون...")
created_employees = []

if Employee:
    emp_status = get_choice_key(Employee, "status", ["active"]) or "active"
    emp_gender_m = get_choice_key(Employee, "gender", ["male", "m"]) or None
    emp_gender_f = get_choice_key(Employee, "gender", ["female", "f"]) or emp_gender_m
    emp_marital = get_choice_key(Employee, "marital_status", ["single"]) or None
    emp_contract = get_choice_key(Employee, "contract_type", ["permanent", "full_time"]) or None
    emp_religion = get_choice_key(Employee, "religion", ["muslim"]) or None

    demo_emps = [
        ("EMP10001", "أحمد", "محمد", "علي", "Ahmed", "Ali",
         emp_gender_m, it_dept, branch1,
         job_titles.get("مطور برامج"), Decimal("12000"), False,
         "01010000001", "ahmed@demo.local"),

        ("EMP10002", "سارة", "أحمد", "حسن", "Sara", "Hassan",
         emp_gender_f, hr_dept, branch1,
         job_titles.get("أخصائي موارد بشرية"), Decimal("9000"), False,
         "01010000002", "sara@demo.local"),

        ("EMP10003", "محمد", "السيد", "فتحي", "Mohamed", "Fathy",
         emp_gender_m, sales_dept, branch2,
         job_titles.get("مندوب مبيعات"), Decimal("7000"), True,
         "01010000003", "mohamed@demo.local"),

        ("EMP10004", "محمود", "عادل", "جابر", "Mahmoud", "Gaber",
         emp_gender_m, sales_dept, branch2,
         job_titles.get("مندوب مبيعات"), Decimal("7200"), True,
         "01010000004", "mahmoud@demo.local"),

        ("EMP10005", "منة", "طارق", "خالد", "Mena", "Khaled",
         emp_gender_f, hr_dept, branch1,
         job_titles.get("محاسب") or job_titles.get("أخصائي موارد بشرية"),
         Decimal("8500"), False,
         "01010000005", "mena@demo.local"),
    ]

    for idx, info in enumerate(demo_emps, start=1):
        (code, far, mar, lar, fen, len_,
         gender, dept, branch, title, salary,
         is_field, phone, email) = info

        # user
        emp_user = User.objects.filter(username=code.lower()).first()
        if not emp_user:
            emp_user = User.objects.create_user(
                username=code.lower(),
                password="Emp@12345",
                email=email,
                first_name=far,
                last_name=lar,
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
            print(f"  ℹ️  {far} موجود")
            continue

        kwargs = {}
        set_if_exists(kwargs, Employee, "company", company)
        set_if_exists(kwargs, Employee, "user", emp_user)
        set_if_exists(kwargs, Employee, "employee_code", code)
        set_if_exists(kwargs, Employee, "first_name_ar", far)
        set_if_exists(kwargs, Employee, "middle_name_ar", mar)
        set_if_exists(kwargs, Employee, "last_name_ar", lar)
        set_if_exists(kwargs, Employee, "first_name_en", fen)
        set_if_exists(kwargs, Employee, "last_name_en", len_)
        set_if_exists(kwargs, Employee, "national_id", f"2990101{idx:07d}")
        set_if_exists(kwargs, Employee, "birth_date", date(1992, idx, 10))
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
        print(f"  ✅ {far} {lar}")

# ── الحضور ──
print("\n📋 الحضور...")
if Attendance and created_employees:
    status_present = get_choice_key(Attendance, "status", ["present"]) or "present"
    status_late    = get_choice_key(Attendance, "status", ["late", "present"]) or "present"
    status_absent  = get_choice_key(Attendance, "status", ["absent"]) or "absent"

    count = 0
    for ei, emp in enumerate(created_employees, 1):
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
            set_if_exists(kwargs, Attendance, "within_range", True)
            set_if_exists(kwargs, Attendance, "check_in_address", "القاهرة")

            try:
                Attendance.objects.create(**kwargs)
                count += 1
            except Exception as e:
                print(f"  ⚠️  {emp}: {e}")

    print(f"  ✅ {count} سجل حضور")

# ── الإجازات ──
print("\n🌴 الإجازات...")
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
        print("  ✅ إجازة سنوية")

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
            description="إجازة مرضية مدفوعة",
        )
        print("  ✅ إجازة مرضية")

    current_year = date.today().year
    for emp in created_employees:
        LeaveBalance.objects.get_or_create(
            company=company,
            employee=emp,
            leave_type=annual,
            year=current_year,
            defaults={
                "total_days": Decimal("21"),
                "used_days":  Decimal("2"),
                "pending_days": Decimal("1"),
            }
        )

    if not LeaveRequest.objects.filter(company=company).exists():
        reqs = [
            (created_employees[0], annual, "pending",
             date.today() + timedelta(days=3),
             date.today() + timedelta(days=5), "سفر عائلي"),
            (created_employees[1], sick, "approved",
             date.today() - timedelta(days=10),
             date.today() - timedelta(days=9), "نزلة برد"),
            (created_employees[2], annual, "rejected",
             date.today() + timedelta(days=7),
             date.today() + timedelta(days=8), "ظروف خاصة"),
        ]
        for emp, lt, st, s, e, reason in reqs:
            status_key = get_choice_key(LeaveRequest, "status", [st, "pending"]) or st
            lr = LeaveRequest.objects.create(
                company=company,
                employee=emp,
                leave_type=lt,
                start_date=s,
                end_date=e,
                days_count=Decimal((e - s).days + 1),
                reason=reason,
                status=status_key,
                notes="بيانات ديمو",
            )
            if st in ["approved", "rejected"] and super_admin:
                lr.reviewed_by = super_admin
                lr.reviewed_at = datetime.now()
                lr.review_notes = "تمت المراجعة"
                lr.save()
        print("  ✅ طلبات إجازة")

# ── التتبع الميداني ──
print("\n📍 التتبع الميداني...")
if LocationLog and created_employees:
    field_emps = [e for e in created_employees if getattr(e, "is_field_worker", False)]
    for idx, emp in enumerate(field_emps, 1):
        if not LocationLog.objects.filter(company=company, employee=emp).exists():
            for p in range(3):
                kwargs = {"company": company}
                set_if_exists(kwargs, LocationLog, "employee", emp)
                set_if_exists(kwargs, LocationLog, "timestamp",
                              datetime.now() - timedelta(minutes=10 * p))
                set_if_exists(kwargs, LocationLog, "latitude",
                              Decimal("30.0500") + Decimal(f"0.000{idx + p}"))
                set_if_exists(kwargs, LocationLog, "longitude",
                              Decimal("31.2400") + Decimal(f"0.000{idx + p}"))
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
    vt = get_choice_key(LocationCheckIn, "visit_type", ["client_visit", "meeting", "other"])
    vs = get_choice_key(LocationCheckIn, "status", ["completed", "arrived"])
    for idx, emp in enumerate(field_emps, 1):
        if not LocationCheckIn.objects.filter(company=company, employee=emp).exists():
            kwargs = {"company": company}
            set_if_exists(kwargs, LocationCheckIn, "employee", emp)
            set_if_exists(kwargs, LocationCheckIn, "visit_type", vt or "client_visit")
            set_if_exists(kwargs, LocationCheckIn, "location_name", f"عميل رقم {idx}")
            set_if_exists(kwargs, LocationCheckIn, "arrival_time",
                          datetime.now() - timedelta(hours=idx))
            set_if_exists(kwargs, LocationCheckIn, "departure_time",
                          datetime.now() - timedelta(minutes=30 * idx))
            set_if_exists(kwargs, LocationCheckIn, "arrival_latitude", Decimal("30.0600"))
            set_if_exists(kwargs, LocationCheckIn, "arrival_longitude", Decimal("31.2500"))
            set_if_exists(kwargs, LocationCheckIn, "departure_latitude", Decimal("30.0610"))
            set_if_exists(kwargs, LocationCheckIn, "departure_longitude", Decimal("31.2510"))
            set_if_exists(kwargs, LocationCheckIn, "purpose", "زيارة عميل")
            set_if_exists(kwargs, LocationCheckIn, "notes", "بيانات ديمو")
            set_if_exists(kwargs, LocationCheckIn, "status", vs or "completed")
            try:
                LocationCheckIn.objects.create(**kwargs)
            except Exception:
                pass

print("  ✅ تتبع ميداني")

print("\n" + "=" * 60)
print("  ✅ Patch 26a اكتمل!")
print("=" * 60)
print("""
بيانات الدخول:

  Company Admin:
    username: demo_admin
    password: Demo@12345

  Employee:
    username: emp10001
    password: Emp@12345

الخطوة الجاية:
  شغّل السيرفر وادخل بـ demo_admin
  python manage.py runserver 0.0.0.0:8000
""")