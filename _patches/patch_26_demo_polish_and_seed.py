#!/usr/bin/env python3
"""
Patch 26: Demo Polish + Seed Data + Owner Guide
================================================
1) تحسين تجربة الديمو
2) Navbar واضح في صفحات البيع
3) إصلاح/تثبيت التاريخ البسيط
4) إنشاء بيانات ديمو حقيقية
5) إنشاء Company Admin للتجربة
6) إنشاء ملف START_HERE_OWNER_GUIDE.md
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


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


def append_file(path, content):
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")


def field_names(model):
    return {f.name for f in model._meta.fields}


def has_field(model, field_name):
    return field_name in field_names(model)


def set_if_exists(kwargs, model, field_name, value):
    if has_field(model, field_name):
        kwargs[field_name] = value


def get_choice_key(model, field_name, preferred_list):
    """
    يرجع أول choice مناسب من preferred_list
    ولو مش موجود يرجع أول choice متاح
    """
    try:
        field = model._meta.get_field(field_name)
    except Exception:
        return None

    choices = getattr(field, "choices", None)
    if not choices:
        return preferred_list[0] if preferred_list else None

    keys = [c[0] for c in choices]
    for item in preferred_list:
        if item in keys:
            return item

    return keys[0] if keys else None


print("=" * 60)
print("  Patch 26: Demo Polish + Seed Data")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) إصلاح/تحسين Navbar في صفحات الـ Landing
# ════════════════════════════════════════════════════════════
print("\n🔧 تحسين صفحات الـ Landing...")

pricing_path = os.path.join(BASE_DIR, "templates", "landing", "pricing.html")
about_path   = os.path.join(BASE_DIR, "templates", "landing", "about.html")
contact_path = os.path.join(BASE_DIR, "templates", "landing", "contact.html")

if os.path.exists(pricing_path):
    pricing = read_file(pricing_path)
    pricing = pricing.replace(
        """<div class="d-flex gap-2">
        <a href="{% url 'landing:home' %}"
           class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
        <a href="{% url 'landing:contact' %}"
           class="btn btn-sm rounded-pill text-white"
           style="background:#06B6D4;">اطلب عرضاً</a>
      </div>""",
        """<div class="d-flex gap-2 align-items-center">
        <a href="{% url 'landing:home' %}"
           class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>

        {% if request.user.is_authenticated %}
          <a href="{% url 'dashboard' %}"
             class="btn btn-sm rounded-pill text-white"
             style="background:#06B6D4;">لوحة التحكم</a>
          <form method="post" action="{% url 'logout' %}" class="m-0">
            {% csrf_token %}
            <button type="submit"
                    class="btn btn-sm btn-outline-light rounded-pill">
              تسجيل الخروج
            </button>
          </form>
        {% else %}
          <a href="{% url 'login' %}"
             class="btn btn-sm btn-outline-light rounded-pill">تسجيل الدخول</a>
          <a href="{% url 'landing:contact' %}"
             class="btn btn-sm rounded-pill text-white"
             style="background:#06B6D4;">اطلب عرضاً</a>
        {% endif %}
      </div>"""
    )
    write_file(pricing_path, pricing)

if os.path.exists(about_path):
    about = read_file(about_path)
    about = about.replace(
        """<div class="d-flex gap-2">
        <a href="{% url 'landing:home' %}" class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
        <a href="{% url 'landing:contact' %}" class="btn btn-sm rounded-pill text-white" style="background:#06B6D4;">تواصل معنا</a>
      </div>""",
        """<div class="d-flex gap-2 align-items-center">
        <a href="{% url 'landing:home' %}" class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>

        {% if request.user.is_authenticated %}
          <a href="{% url 'dashboard' %}" class="btn btn-sm rounded-pill text-white" style="background:#06B6D4;">لوحة التحكم</a>
          <form method="post" action="{% url 'logout' %}" class="m-0">
            {% csrf_token %}
            <button type="submit" class="btn btn-sm btn-outline-light rounded-pill">تسجيل الخروج</button>
          </form>
        {% else %}
          <a href="{% url 'login' %}" class="btn btn-sm btn-outline-light rounded-pill">تسجيل الدخول</a>
          <a href="{% url 'landing:contact' %}" class="btn btn-sm rounded-pill text-white" style="background:#06B6D4;">تواصل معنا</a>
        {% endif %}
      </div>"""
    )
    write_file(about_path, about)

if os.path.exists(contact_path):
    contact = read_file(contact_path)
    contact = contact.replace(
        """<div class="d-flex align-items-center justify-content-between">
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">
        MotionHR
      </a>
      <a href="{% url 'landing:home' %}"
         class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
    </div>""",
        """<div class="d-flex align-items-center justify-content-between">
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">
        MotionHR
      </a>

      <div class="d-flex gap-2 align-items-center">
        <a href="{% url 'landing:home' %}"
           class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>

        {% if request.user.is_authenticated %}
          <a href="{% url 'dashboard' %}"
             class="btn btn-sm rounded-pill text-white"
             style="background:#06B6D4;">لوحة التحكم</a>
          <form method="post" action="{% url 'logout' %}" class="m-0">
            {% csrf_token %}
            <button type="submit"
                    class="btn btn-sm btn-outline-light rounded-pill">
              تسجيل الخروج
            </button>
          </form>
        {% else %}
          <a href="{% url 'login' %}"
             class="btn btn-sm btn-outline-light rounded-pill">تسجيل الدخول</a>
        {% endif %}
      </div>
    </div>"""
    )
    write_file(contact_path, contact)

# ════════════════════════════════════════════════════════════
# 2) تثبيت عرض التاريخ في الـ Dashboard
# ════════════════════════════════════════════════════════════
print("\n🔧 تثبيت عرض التاريخ في الـ Dashboard...")

dashboard_path = os.path.join(BASE_DIR, "templates", "dashboard", "index.html")
if os.path.exists(dashboard_path):
    dashboard = read_file(dashboard_path)
    dashboard = dashboard.replace(
        '{{ today|date:"l، d MMMM Y" }}',
        '{{ today|date:"d/m/Y" }}'
    )
    dashboard = dashboard.replace(
        "{{ today|date:'l، d MMMM Y' }}",
        "{{ today|date:'d/m/Y' }}"
    )
    write_file(dashboard_path, dashboard)

# ════════════════════════════════════════════════════════════
# 3) تحسين CompanySubscription.all_features للديمو
# ════════════════════════════════════════════════════════════
print("\n🔧 تحسين صلاحيات الاشتراك للديمو...")

subs_models_path = os.path.join(BASE_DIR, "subscriptions", "models.py")
if os.path.exists(subs_models_path):
    subs_models = read_file(subs_models_path)
    old_text = """    @property
    def all_features(self):
        \"\"\"كل ميزات الخطة\"\"\"
        return set()
"""
    new_text = """    @property
    def all_features(self):
        \"\"\"كل ميزات الخطة - وضع ديمو مبسط\"\"\"
        demo_features = {
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
        try:
            from subscriptions.models import FeatureFlag
            keys = set(
                FeatureFlag.objects.filter(is_active=True).values_list('key', flat=True)
            )
            return keys or demo_features
        except Exception:
            return demo_features
"""
    if old_text in subs_models:
        subs_models = subs_models.replace(old_text, new_text)
        write_file(subs_models_path, subs_models)
        print("  ✅ تم تحسين all_features")
    else:
        print("  ℹ️  all_features تم تعديلها قبل كده أو النص مختلف")

# ════════════════════════════════════════════════════════════
# 4) Seed Data
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء بيانات ديمو...")

from django.contrib.auth import get_user_model
from companies.models import Company, Branch, Department
from attendance.models import Shift

User = get_user_model()

# imports اختيارية
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

# ── الشركة ───────────────────────────────────────────────
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

# ── ربط السوبر أدمن بالشركة ──────────────────────────────
super_admin = User.objects.filter(is_superuser=True).first()
if super_admin:
    if getattr(super_admin, "company", None) != company:
        super_admin.company = company
    if hasattr(super_admin, "role"):
        super_admin.role = "super_admin"
    super_admin.save()
    print(f"  ✅ Super Admin: {super_admin.username}")

# ── Company Admin فعلي للتجربة ───────────────────────────
demo_admin, created = User.objects.get_or_create(
    username="demo_admin",
    defaults={
        "email": "demo@motionhr.local",
        "first_name": "Demo",
        "last_name": "Admin",
        "is_active": True,
    }
)
demo_admin.set_password("Demo@12345")
if hasattr(demo_admin, "company"):
    demo_admin.company = company
if hasattr(demo_admin, "role"):
    demo_admin.role = "company_admin"
demo_admin.is_staff = True
demo_admin.save()
print("  ✅ تم تجهيز Company Admin:")
print("     username: demo_admin")
print("     password: Demo@12345")

# ── الخطة والاشتراك ──────────────────────────────────────
if SubscriptionPlan and CompanySubscription:
    tier_value = get_choice_key(SubscriptionPlan, "tier", ["business", "professional", "starter", "enterprise"])
    plan = SubscriptionPlan.objects.filter(name_en="Business").first()
    if not plan:
        plan_kwargs = {}
        set_if_exists(plan_kwargs, SubscriptionPlan, "name_ar", "الأعمال")
        set_if_exists(plan_kwargs, SubscriptionPlan, "name_en", "Business")
        set_if_exists(plan_kwargs, SubscriptionPlan, "tier", tier_value or "business")
        set_if_exists(plan_kwargs, SubscriptionPlan, "description", "خطة ديمو للأعمال")
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
        print("  ✅ تم إنشاء SubscriptionPlan")
    else:
        print("  ℹ️  SubscriptionPlan موجودة")

    sub = CompanySubscription.objects.filter(company=company).first()
    if not sub:
        sub_kwargs = {"company": company, "plan": plan}
        set_if_exists(sub_kwargs, CompanySubscription, "start_date", date.today() - timedelta(days=5))
        set_if_exists(sub_kwargs, CompanySubscription, "end_date", date.today() + timedelta(days=365))
        set_if_exists(sub_kwargs, CompanySubscription, "status", get_choice_key(CompanySubscription, "status", ["active", "trial"]) or "active")
        set_if_exists(sub_kwargs, CompanySubscription, "billing_cycle", get_choice_key(CompanySubscription, "billing_cycle", ["monthly", "yearly"]) or "monthly")
        set_if_exists(sub_kwargs, CompanySubscription, "is_trial", False)
        set_if_exists(sub_kwargs, CompanySubscription, "grace_period_days", 7)
        set_if_exists(sub_kwargs, CompanySubscription, "price_paid", Decimal("599"))
        set_if_exists(sub_kwargs, CompanySubscription, "discount", Decimal("0"))
        set_if_exists(sub_kwargs, CompanySubscription, "notes", "اشتراك ديمو")
        sub = CompanySubscription.objects.create(**sub_kwargs)
        print("  ✅ تم إنشاء الاشتراك")
    else:
        # تحديثه عشان يبقى صالح
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
        print("  ✅ تم تحديث الاشتراك ليكون صالح")

# ── الفروع ────────────────────────────────────────────────
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
    print("  ✅ تم إنشاء الفرع الرئيسي")
else:
    print("  ℹ️  الفرع الرئيسي موجود")

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

# ── الإدارات ──────────────────────────────────────────────
hr_dept = Department.objects.filter(company=company, name_ar="الموارد البشرية").first()
if not hr_dept:
    hr_dept = Department.objects.create(
        company=company,
        name_ar="الموارد البشرية",
        name_en="Human Resources",
        code="HR",
        is_active=True,
    )
    print("  ✅ تم إنشاء إدارة الموارد البشرية")

sales_dept = Department.objects.filter(company=company, name_ar="المبيعات").first()
if not sales_dept:
    sales_dept = Department.objects.create(
        company=company,
        name_ar="المبيعات",
        name_en="Sales",
        code="SALES",
        is_active=True,
    )
    print("  ✅ تم إنشاء إدارة المبيعات")

it_dept = Department.objects.filter(company=company, name_ar="تقنية المعلومات").first()
if not it_dept:
    it_dept = Department.objects.create(
        company=company,
        name_ar="تقنية المعلومات",
        name_en="IT",
        code="IT",
        is_active=True,
    )
    print("  ✅ تم إنشاء إدارة تقنية المعلومات")

# ── الشيفت ────────────────────────────────────────────────
shift = Shift.objects.filter(company=company, name="شيفت صباحي").first()
if not shift:
    shift = Shift.objects.create(
        company=company,
        name="شيفت صباحي",
        shift_type=get_choice_key(Shift, "shift_type", ["fixed", "flexible", "rotating"]) or "fixed",
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
    print("  ✅ تم إنشاء الشيفت الصباحي")
else:
    print("  ℹ️  الشيفت الصباحي موجود")

# ── المسميات الوظيفية ────────────────────────────────────
job_titles = {}
if JobTitle:
    jt_data = [
        ("أخصائي موارد بشرية", "HR Specialist"),
        ("مندوب مبيعات", "Sales Representative"),
        ("مطور برامج", "Software Developer"),
        ("محاسب", "Accountant"),
        ("فني صيانة", "Maintenance Technician"),
    ]
    for ar, en in jt_data:
        jt = JobTitle.objects.filter(company=company, name_ar=ar).first()
        if not jt:
            kwargs = {"company": company}
            set_if_exists(kwargs, JobTitle, "name_ar", ar)
            set_if_exists(kwargs, JobTitle, "name_en", en)
            set_if_exists(kwargs, JobTitle, "description", ar)
            set_if_exists(kwargs, JobTitle, "is_active", True)
            jt = JobTitle.objects.create(**kwargs)
        job_titles[ar] = jt
    print("  ✅ تم تجهيز المسميات الوظيفية")

# ── الموظفون ─────────────────────────────────────────────
created_employees = []
if Employee:
    emp_status_active = get_choice_key(Employee, "status", ["active", "on_leave", "suspended"]) or "active"
    emp_gender_male   = get_choice_key(Employee, "gender", ["male", "m", "ذكر"]) or None
    emp_gender_female = get_choice_key(Employee, "gender", ["female", "f", "أنثى"]) or emp_gender_male
    emp_marital       = get_choice_key(Employee, "marital_status", ["single", "أعزب", "single_male"]) or None
    emp_contract      = get_choice_key(Employee, "contract_type", ["permanent", "full_time", "fixed"]) or None
    emp_religion      = get_choice_key(Employee, "religion", ["muslim", "christian"]) or None

    demo_employees = [
        {
            "code": "EMP10001",
            "first_ar": "أحمد",
            "middle_ar": "محمد",
            "last_ar": "علي",
            "first_en": "Ahmed",
            "last_en": "Ali",
            "gender": emp_gender_male,
            "dept": it_dept,
            "branch": branch1,
            "title": job_titles.get("مطور برامج"),
            "salary": Decimal("12000"),
            "field": False,
            "phone": "01010000001",
            "email": "ahmed@demo.local",
        },
        {
            "code": "EMP10002",
            "first_ar": "سارة",
            "middle_ar": "أحمد",
            "last_ar": "حسن",
            "first_en": "Sara",
            "last_en": "Hassan",
            "gender": emp_gender_female,
            "dept": hr_dept,
            "branch": branch1,
            "title": job_titles.get("أخصائي موارد بشرية"),
            "salary": Decimal("9000"),
            "field": False,
            "phone": "01010000002",
            "email": "sara@demo.local",
        },
        {
            "code": "EMP10003",
            "first_ar": "محمد",
            "middle_ar": "السيد",
            "last_ar": "فتحي",
            "first_en": "Mohamed",
            "last_en": "Fathy",
            "gender": emp_gender_male,
            "dept": sales_dept,
            "branch": branch2,
            "title": job_titles.get("مندوب مبيعات"),
            "salary": Decimal("7000"),
            "field": True,
            "phone": "01010000003",
            "email": "mohamed@demo.local",
        },
        {
            "code": "EMP10004",
            "first_ar": "محمود",
            "middle_ar": "عادل",
            "last_ar": "جابر",
            "first_en": "Mahmoud",
            "last_en": "Gaber",
            "gender": emp_gender_male,
            "dept": sales_dept,
            "branch": branch2,
            "title": job_titles.get("مندوب مبيعات"),
            "salary": Decimal("7200"),
            "field": True,
            "phone": "01010000004",
            "email": "mahmoud@demo.local",
        },
        {
            "code": "EMP10005",
            "first_ar": "منة",
            "middle_ar": "طارق",
            "last_ar": "خالد",
            "first_en": "Mena",
            "last_en": "Khaled",
            "gender": emp_gender_female,
            "dept": hr_dept,
            "branch": branch1,
            "title": job_titles.get("محاسب") or job_titles.get("أخصائي موارد بشرية"),
            "salary": Decimal("8500"),
            "field": False,
            "phone": "01010000005",
            "email": "mena@demo.local",
        },
    ]

    for idx, info in enumerate(demo_employees, start=1):
        # user للموظف
        emp_user = User.objects.filter(username=info["code"].lower()).first()
        if not emp_user:
            emp_user = User.objects.create_user(
                username=info["code"].lower(),
                password="Emp@12345",
                email=info["email"],
                first_name=info["first_ar"],
                last_name=info["last_ar"],
            )
        if hasattr(emp_user, "company"):
            emp_user.company = company
        if hasattr(emp_user, "role"):
            emp_user.role = "employee"
        if hasattr(emp_user, "phone"):
            emp_user.phone = info["phone"]
        emp_user.save()

        employee = Employee.objects.filter(company=company, employee_code=info["code"]).first()
        if employee:
            created_employees.append(employee)
            continue

        kwargs = {}
        set_if_exists(kwargs, Employee, "company", company)
        set_if_exists(kwargs, Employee, "user", emp_user)
        set_if_exists(kwargs, Employee, "employee_code", info["code"])
        set_if_exists(kwargs, Employee, "first_name_ar", info["first_ar"])
        set_if_exists(kwargs, Employee, "middle_name_ar", info["middle_ar"])
        set_if_exists(kwargs, Employee, "last_name_ar", info["last_ar"])
        set_if_exists(kwargs, Employee, "first_name_en", info["first_en"])
        set_if_exists(kwargs, Employee, "last_name_en", info["last_en"])
        set_if_exists(kwargs, Employee, "national_id", f"2990101{idx:07d}")
        set_if_exists(kwargs, Employee, "birth_date", date(1995, 1, min(idx, 28)))
        set_if_exists(kwargs, Employee, "gender", info["gender"])
        set_if_exists(kwargs, Employee, "marital_status", emp_marital)
        set_if_exists(kwargs, Employee, "religion", emp_religion)
        set_if_exists(kwargs, Employee, "nationality", "مصري")
        set_if_exists(kwargs, Employee, "email", info["email"])
        set_if_exists(kwargs, Employee, "phone", info["phone"])
        set_if_exists(kwargs, Employee, "phone2", "")
        set_if_exists(kwargs, Employee, "address", "القاهرة، مصر")
        set_if_exists(kwargs, Employee, "city", "القاهرة")
        set_if_exists(kwargs, Employee, "hire_date", date.today() - timedelta(days=30 * idx))
        set_if_exists(kwargs, Employee, "contract_type", emp_contract)
        set_if_exists(kwargs, Employee, "branch", info["branch"])
        set_if_exists(kwargs, Employee, "department", info["dept"])
        set_if_exists(kwargs, Employee, "job_title", info["title"])
        set_if_exists(kwargs, Employee, "basic_salary", info["salary"])
        set_if_exists(kwargs, Employee, "bank_name", "البنك الأهلي")
        set_if_exists(kwargs, Employee, "bank_account", f"100200300{idx}")
        set_if_exists(kwargs, Employee, "iban", f"EG{idx:02d}123456789012345678901")
        set_if_exists(kwargs, Employee, "has_insurance", False)
        set_if_exists(kwargs, Employee, "emergency_contact_name", "أحد الأقارب")
        set_if_exists(kwargs, Employee, "emergency_contact_relation", "أخ")
        set_if_exists(kwargs, Employee, "emergency_contact_phone", f"0112000000{idx}")
        set_if_exists(kwargs, Employee, "status", emp_status_active)
        set_if_exists(kwargs, Employee, "notes", "بيانات ديمو")
        set_if_exists(kwargs, Employee, "is_field_worker", info["field"])

        employee = Employee.objects.create(**kwargs)
        created_employees.append(employee)

    print(f"  ✅ تم تجهيز {len(created_employees)} موظفين ديمو")
    print("     بيانات دخول أي موظف:")
    print("     username: emp10001")
    print("     password: Emp@12345")

# ── الحضور ───────────────────────────────────────────────
if Attendance and created_employees:
    attendance_status_present = get_choice_key(Attendance, "status", ["present", "late", "absent"]) or "present"
    attendance_status_late    = get_choice_key(Attendance, "status", ["late", "present", "absent"]) or attendance_status_present
    attendance_status_absent  = get_choice_key(Attendance, "status", ["absent", "late", "present"]) or attendance_status_present

    for emp_index, emp in enumerate(created_employees, start=1):
        for day_back in range(1, 6):
            att_date = date.today() - timedelta(days=day_back)
            obj = Attendance.objects.filter(company=company, employee=emp, date=att_date).first()
            if obj:
                continue

            status = attendance_status_present
            late_minutes = 0
            check_in_t = time(8, 5)
            check_out_t = time(17, 0)
            work_hours = Decimal("8.0")

            if day_back == 2 and emp_index % 2 == 0:
                status = attendance_status_late
                late_minutes = 25
                check_in_t = time(8, 25)
                work_hours = Decimal("7.6")
            elif day_back == 4 and emp_index == 5:
                status = attendance_status_absent
                check_in_t = None
                check_out_t = None
                work_hours = Decimal("0.0")

            kwargs = {"company": company}
            set_if_exists(kwargs, Attendance, "employee", emp)
            set_if_exists(kwargs, Attendance, "date", att_date)
            set_if_exists(kwargs, Attendance, "shift", shift)
            set_if_exists(kwargs, Attendance, "status", status)
            if check_in_t:
                set_if_exists(kwargs, Attendance, "check_in_time", check_in_t)
            if check_out_t:
                set_if_exists(kwargs, Attendance, "check_out_time", check_out_t)
            set_if_exists(kwargs, Attendance, "work_hours", work_hours)
            set_if_exists(kwargs, Attendance, "late_minutes", late_minutes)
            set_if_exists(kwargs, Attendance, "early_leave_minutes", 0)
            set_if_exists(kwargs, Attendance, "overtime_hours", Decimal("0.0"))
            set_if_exists(kwargs, Attendance, "check_in_latitude", Decimal("30.0444"))
            set_if_exists(kwargs, Attendance, "check_in_longitude", Decimal("31.2357"))
            set_if_exists(kwargs, Attendance, "check_out_latitude", Decimal("30.0444"))
            set_if_exists(kwargs, Attendance, "check_out_longitude", Decimal("31.2357"))
            set_if_exists(kwargs, Attendance, "within_range", True)
            set_if_exists(kwargs, Attendance, "check_in_address", "القاهرة")
            set_if_exists(kwargs, Attendance, "check_out_address", "القاهرة")

            try:
                Attendance.objects.create(**kwargs)
            except Exception as e:
                print(f"  ⚠️  تعذر إنشاء حضور للموظف {getattr(emp, 'employee_code', emp.pk)}: {e}")

    print("  ✅ تم تجهيز سجلات حضور ديمو")

# ── الإجازات ─────────────────────────────────────────────
if LeaveType and LeaveBalance and LeaveRequest and created_employees:
    annual = LeaveType.objects.filter(company=company, name="إجازة سنوية").first()
    if not annual:
        annual = LeaveType.objects.create(
            company=company,
            name="إجازة سنوية",
            category=get_choice_key(LeaveType, "category", ["annual", "other"]) or "annual",
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
        bal, _ = LeaveBalance.objects.get_or_create(
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
        if bal.total_days == 0:
            bal.total_days = Decimal("21")
            bal.save()

    # طلبات إجازة
    if not LeaveRequest.objects.filter(company=company).exists():
        sample_reqs = [
            (created_employees[0], annual, "pending",  date.today() + timedelta(days=3), date.today() + timedelta(days=5), "سفر عائلي"),
            (created_employees[1], sick,   "approved", date.today() - timedelta(days=10), date.today() - timedelta(days=9), "نزلة برد"),
            (created_employees[2], annual, "rejected", date.today() + timedelta(days=7), date.today() + timedelta(days=8), "ظروف خاصة"),
        ]

        for emp, lt, status, start_d, end_d, reason in sample_reqs:
            kwargs = {
                "company": company,
                "employee": emp,
                "leave_type": lt,
                "start_date": start_d,
                "end_date": end_d,
                "days_count": Decimal((end_d - start_d).days + 1),
                "reason": reason,
                "status": get_choice_key(LeaveRequest, "status", [status, "pending", "approved", "rejected"]) or status,
                "notes": "بيانات ديمو",
            }
            lr = LeaveRequest.objects.create(**kwargs)
            if status in ["approved", "rejected"] and super_admin:
                lr.reviewed_by = super_admin
                lr.reviewed_at = datetime.now()
                lr.review_notes = "تمت المعالجة"
                lr.save()

    print("  ✅ تم تجهيز أنواع وطلبات الإجازات")

# ── التتبع الميداني ──────────────────────────────────────
if created_employees and LocationLog:
    field_emps = [e for e in created_employees if getattr(e, "is_field_worker", False)]
    for idx, emp in enumerate(field_emps, start=1):
        if not LocationLog.objects.filter(company=company, employee=emp).exists():
            for p in range(3):
                kwargs = {"company": company}
                set_if_exists(kwargs, LocationLog, "employee", emp)
                set_if_exists(kwargs, LocationLog, "timestamp", datetime.now() - timedelta(minutes=10 * p))
                set_if_exists(kwargs, LocationLog, "latitude", Decimal("30.0500") + Decimal(f"0.00{idx+p}"))
                set_if_exists(kwargs, LocationLog, "longitude", Decimal("31.2400") + Decimal(f"0.00{idx+p}"))
                set_if_exists(kwargs, LocationLog, "accuracy", Decimal("10.0"))
                set_if_exists(kwargs, LocationLog, "speed", Decimal("18.5"))
                set_if_exists(kwargs, LocationLog, "battery_level", 80 - p * 5)
                set_if_exists(kwargs, LocationLog, "address", "القاهرة")
                try:
                    LocationLog.objects.create(**kwargs)
                except Exception:
                    pass
    print("  ✅ تم تجهيز نقاط تتبع ميداني")

if created_employees and LocationCheckIn:
    field_emps = [e for e in created_employees if getattr(e, "is_field_worker", False)]
    visit_type_choice = get_choice_key(LocationCheckIn, "visit_type", ["client_visit", "meeting", "other"])
    visit_status_choice = get_choice_key(LocationCheckIn, "status", ["completed", "arrived", "in_progress"])

    for idx, emp in enumerate(field_emps, start=1):
        if not LocationCheckIn.objects.filter(company=company, employee=emp).exists():
            kwargs = {"company": company}
            set_if_exists(kwargs, LocationCheckIn, "employee", emp)
            set_if_exists(kwargs, LocationCheckIn, "visit_type", visit_type_choice or "client_visit")
            set_if_exists(kwargs, LocationCheckIn, "location_name", f"عميل رقم {idx}")
            set_if_exists(kwargs, LocationCheckIn, "arrival_time", datetime.now() - timedelta(hours=idx))
            set_if_exists(kwargs, LocationCheckIn, "departure_time", datetime.now() - timedelta(hours=idx-1) if idx > 0 else datetime.now())
            set_if_exists(kwargs, LocationCheckIn, "arrival_latitude", Decimal("30.0600"))
            set_if_exists(kwargs, LocationCheckIn, "arrival_longitude", Decimal("31.2500"))
            set_if_exists(kwargs, LocationCheckIn, "departure_latitude", Decimal("30.0610"))
            set_if_exists(kwargs, LocationCheckIn, "departure_longitude", Decimal("31.2510"))
            set_if_exists(kwargs, LocationCheckIn, "address", "القاهرة")
            set_if_exists(kwargs, LocationCheckIn, "purpose", "زيارة عميل")
            set_if_exists(kwargs, LocationCheckIn, "notes", "بيانات ديمو")
            set_if_exists(kwargs, LocationCheckIn, "status", visit_status_choice or "completed")
            try:
                LocationCheckIn.objects.create(**kwargs)
            except Exception:
                pass
    print("  ✅ تم تجهيز زيارات ميدانية")

# ════════════════════════════════════════════════════════════
# 5) ملف شرح سريع لصاحب المشروع
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء ملف START_HERE_OWNER_GUIDE.md...")

guide = """# START HERE - MotionHR Owner Guide

## 1) أنا أفتح المشروع منين؟

### أ) الصفحة العامة (البيع)
- http://127.0.0.1:8000/
- دي صفحة تسويقية للعميل قبل تسجيل الدخول

### ب) صفحة دخول العميل
- http://127.0.0.1:8000/login/

### ج) لوحة الإدارة الكبيرة
- http://127.0.0.1:8000/admin/

### د) لوحة الاستخدام الفعلي
- http://127.0.0.1:8000/dashboard/

---

## 2) أفتح من الموبايل إزاي؟
1. شغل السيرفر:
```bash
python manage.py runserver 0.0.0.0:8000