import os
import django
from datetime import date, time
from decimal import Decimal
from django.apps import apps
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

TEMPLATE_COMPANY_ID = 24
DEFAULT_PASSWORD = 'Test@1234'

def find_model(*names):
    all_models = list(apps.get_models())
    for name in names:
        for m in all_models:
            if m.__name__.lower() == name.lower():
                return m
    return None

def mgr(model):
    return getattr(model, '_base_manager', model.objects)

def concrete_fields(model):
    return {f.name for f in model._meta.fields}

def clean_data(model, data):
    allowed = concrete_fields(model)
    return {k: v for k, v in data.items() if k in allowed and v is not None}

def upsert(model, lookup=None, data=None):
    lookup = clean_data(model, lookup or {})
    data = clean_data(model, data or {})
    obj = mgr(model).filter(**lookup).first() if lookup else None
    if obj:
        changed = False
        for k, v in data.items():
            if getattr(obj, k, None) != v:
                setattr(obj, k, v)
                changed = True
        if changed:
            obj.save()
        return obj
    return mgr(model).create(**{**lookup, **data})

Company = find_model('Company')
Branch = find_model('Branch')
Department = find_model('Department')
JobTitle = find_model('JobTitle')
Shift = find_model('Shift', 'WorkShift')
Employee = find_model('Employee')
EmployeeShift = find_model('EmployeeShift')
RequestCategory = find_model('RequestCategory')
RequestType = find_model('RequestType')
LeaveType = find_model('LeaveType')

User = get_user_model()

if not all([Company, Branch, Department, JobTitle, Shift, Employee, RequestCategory, RequestType, LeaveType]):
    raise SystemExit('بعض الموديلات الأساسية غير موجودة')

template_company = mgr(Company).filter(id=TEMPLATE_COMPANY_ID).first()
if not template_company:
    raise SystemExit(f'شركة التمبليت {TEMPLATE_COMPANY_ID} غير موجودة')

def ensure_user(username, email, password, role, company=None, is_superuser=False):
    user = User._base_manager.filter(username=username).first()
    if not user:
        if is_superuser:
            user = User.objects.create_superuser(username=username, email=email, password=password)
        else:
            user = User.objects.create_user(username=username, email=email, password=password)

    changed = False
    updates = {
        'email': email,
        'role': role,
        'company': company,
        'is_active': True,
    }
    for field, value in updates.items():
        if hasattr(user, field) and getattr(user, field, None) != value:
            setattr(user, field, value)
            changed = True
    if changed:
        user.save()
    return user

def clone_template_data(company):
    category_map = {}

    for cat in mgr(RequestCategory).filter(company_id=TEMPLATE_COMPANY_ID):
        new_cat = upsert(
            RequestCategory,
            lookup={'company': company, 'name': cat.name},
            data={
                'company': company,
                'name': cat.name,
                'name_en': getattr(cat, 'name_en', None),
                'icon': getattr(cat, 'icon', None),
                'color': getattr(cat, 'color', None),
                'is_active': getattr(cat, 'is_active', True),
            },
        )
        category_map[cat.id] = new_cat

    for rt in mgr(RequestType).filter(company_id=TEMPLATE_COMPANY_ID).select_related('category'):
        new_cat = category_map.get(getattr(rt, 'category_id', None))
        upsert(
            RequestType,
            lookup={'company': company, 'name': rt.name},
            data={
                'company': company,
                'category': new_cat,
                'name': rt.name,
                'name_en': getattr(rt, 'name_en', None),
                'description': getattr(rt, 'description', None),
                'description_en': getattr(rt, 'description_en', None),
                'permission_kind': getattr(rt, 'permission_kind', None),
                'requires_date_range': getattr(rt, 'requires_date_range', False),
                'requires_amount': getattr(rt, 'requires_amount', False),
                'requires_document': getattr(rt, 'requires_document', False),
                'requires_approval': getattr(rt, 'requires_approval', True),
                'form_schema': getattr(rt, 'form_schema', None),
                'is_active': getattr(rt, 'is_active', True),
            },
        )

    for lt in mgr(LeaveType).filter(company_id=TEMPLATE_COMPANY_ID):
        upsert(
            LeaveType,
            lookup={'company': company, 'name': lt.name},
            data={
                'company': company,
                'name': lt.name,
                'name_en': getattr(lt, 'name_en', None),
                'code': getattr(lt, 'code', None),
                'days_allowed': getattr(lt, 'days_allowed', None),
                'is_paid': getattr(lt, 'is_paid', True),
                'requires_approval': getattr(lt, 'requires_approval', True),
                'requires_attachment': getattr(lt, 'requires_attachment', False),
                'gender_specific': getattr(lt, 'gender_specific', None),
                'is_active': getattr(lt, 'is_active', True),
            },
        )

def make_company(name_ar, name_en, phone, lat, lon, radius=500):
    return upsert(
        Company,
        lookup={'name_ar': name_ar},
        data={
            'name_ar': name_ar,
            'name_en': name_en,
            'email': f"info@{name_en.lower().replace(' ', '')}.com",
            'phone': phone,
            'is_active': True,
            'office_address': f'Main office - {name_ar}',
            'office_latitude': Decimal(str(lat)),
            'office_longitude': Decimal(str(lon)),
            'geofence_enabled': True,
            'geofence_radius': radius,
        },
    )

def make_branch(company, name_ar, name_en):
    return upsert(
        Branch,
        lookup={'company': company, 'name_ar': name_ar},
        data={'company': company, 'name_ar': name_ar, 'name_en': name_en, 'is_active': True},
    )

def make_department(company, name_ar, name_en):
    return upsert(
        Department,
        lookup={'company': company, 'name_ar': name_ar},
        data={'company': company, 'name_ar': name_ar, 'name_en': name_en, 'is_active': True},
    )

def make_job_title(company, name_ar, name_en, is_manager=False):
    return upsert(
        JobTitle,
        lookup={'company': company, 'name_ar': name_ar},
        data={'company': company, 'name_ar': name_ar, 'name_en': name_en, 'is_manager': is_manager, 'is_active': True},
    )

def make_shift(company, name, start_h, start_m, end_h, end_m, crosses_midnight=False, is_default=False):
    if is_default:
        mgr(Shift).filter(company=company, is_default=True).update(is_default=False)

    return upsert(
        Shift,
        lookup={'company': company, 'name': name},
        data={
            'company': company,
            'name': name,
            'start_time': time(start_h, start_m),
            'end_time': time(end_h, end_m),
            'crosses_midnight': crosses_midnight,
            'grace_period': 15,
            'early_checkin_minutes': 30,
            'break_duration': 60,
            'is_default': is_default,
            'is_active': True,
            'work_sunday': True,
            'work_monday': True,
            'work_tuesday': True,
            'work_wednesday': True,
            'work_thursday': True,
            'work_friday': False,
            'work_saturday': False,
        },
    )

employee_counter = 1
def next_codes():
    global employee_counter
    code = f'AUTO{employee_counter:04d}'
    phone = f'0101000{employee_counter:04d}'[-11:]
    national = f'2910101{employee_counter:06d}'[-14:]
    employee_counter += 1
    return code, phone, national

def make_employee(company, user, first_ar, last_ar, first_en, last_en, branch, department, job_title, salary, worker_type='office', status='active'):
    code, phone, national = next_codes()
    emp = upsert(
        Employee,
        lookup={'user': user},
        data={
            'company': company,
            'user': user,
            'employee_code': code,
            'first_name_ar': first_ar,
            'last_name_ar': last_ar,
            'first_name_en': first_en,
            'last_name_en': last_en,
            'national_id': national,
            'birth_date': date(1991, 1, 10),
            'gender': 'male',
            'language': 'ar',
            'marital_status': 'single',
            'nationality': 'مصري',
            'email': user.email,
            'phone': phone,
            'hire_date': date.today(),
            'contract_type': 'permanent',
            'branch': branch,
            'department': department,
            'job_title': job_title,
            'basic_salary': Decimal(str(salary)),
            'status': status,
            'worker_type': worker_type,
        },
    )
    return emp

def assign_shift(company, employee, shift):
    if not EmployeeShift or not shift:
        return
    upsert(
        EmployeeShift,
        lookup={'employee': employee, 'shift': shift, 'start_date': date.today()},
        data={
            'company': company,
            'employee': employee,
            'shift': shift,
            'assignment_type': 'employee',
            'start_date': date.today(),
            'is_active': True,
            'priority': 1,
        },
    )

SCENARIOS = [
    {
        'slug': 'realestate',
        'company_ar': 'شركة المدار العقارية',
        'company_en': 'Orbit Real Estate',
        'phone': '01050000001',
        'lat': 30.0444, 'lon': 31.2357,
        'branches': [('المقر الرئيسي', 'HQ'), ('فرع المبيعات', 'Sales Branch')],
        'departments': [('المبيعات', 'Sales'), ('الموارد البشرية', 'HR'), ('الحسابات', 'Finance'), ('المشروعات', 'Projects')],
        'job_titles': [('صاحب الشركة', 'Owner', True), ('مدير الموارد البشرية', 'HR Manager', True), ('مدير الحسابات', 'Finance Manager', True), ('مدير مبيعات', 'Sales Manager', True), ('مندوب مبيعات', 'Sales Rep', False)],
        'shifts': [('الشيفت الصباحي', 9, 0, 17, 0, False, True), ('شيفت المبيعات الميداني', 10, 0, 18, 0, False, False)],
        'users': [
            ('re_admin', 'company_admin', 'جون', 'العقاري', 'John', 'Realty', 'صاحب الشركة', 'المبيعات', 'المقر الرئيسي', 35000, 'office', 'الشيفت الصباحي'),
            ('re_hr', 'hr_manager', 'منى', 'الموارد', 'Mona', 'HR', 'مدير الموارد البشرية', 'الموارد البشرية', 'المقر الرئيسي', 18000, 'office', 'الشيفت الصباحي'),
            ('re_fin', 'manager', 'أحمد', 'الحسابات', 'Ahmed', 'Finance', 'مدير الحسابات', 'الحسابات', 'المقر الرئيسي', 22000, 'office', 'الشيفت الصباحي'),
            ('re_sales_mgr', 'manager', 'سارة', 'المبيعات', 'Sara', 'Sales', 'مدير مبيعات', 'المبيعات', 'فرع المبيعات', 20000, 'office', 'الشيفت الصباحي'),
            ('re_sales_1', 'employee', 'محمود', 'مندوب', 'Mahmoud', 'Rep', 'مندوب مبيعات', 'المبيعات', 'فرع المبيعات', 9000, 'field_free', 'شيفت المبيعات الميداني'),
            ('re_sales_2', 'employee', 'يوسف', 'مندوب', 'Youssef', 'Rep', 'مندوب مبيعات', 'المبيعات', 'فرع المبيعات', 9000, 'field_assigned', 'شيفت المبيعات الميداني'),
        ],
    },
    {
        'slug': 'contracting',
        'company_ar': 'شركة البنيان للمقاولات',
        'company_en': 'Bunyan Contracting',
        'phone': '01050000002',
        'lat': 30.0131, 'lon': 31.2089,
        'branches': [('المقر الرئيسي', 'HQ'), ('موقع مشروع 1', 'Project 1'), ('المخزن المركزي', 'Central Store')],
        'departments': [('العمليات', 'Operations'), ('الهندسة', 'Engineering'), ('الموارد البشرية', 'HR'), ('الحسابات', 'Finance'), ('المخازن', 'Stores')],
        'job_titles': [('صاحب الشركة', 'Owner', True), ('مدير موقع', 'Site Manager', True), ('مهندس موقع', 'Site Engineer', True), ('أمين مخزن', 'Store Keeper', False), ('عامل', 'Worker', False)],
        'shifts': [('شيفت نهاري', 8, 0, 16, 0, False, True), ('شيفت ليلي', 20, 0, 4, 0, True, False)],
        'users': [
            ('con_admin', 'company_admin', 'وليد', 'البنيان', 'Walid', 'Bunyan', 'صاحب الشركة', 'العمليات', 'المقر الرئيسي', 40000, 'office', 'شيفت نهاري'),
            ('con_hr', 'hr_manager', 'هالة', 'الموارد', 'Hala', 'HR', 'مدير موقع', 'الموارد البشرية', 'المقر الرئيسي', 17000, 'office', 'شيفت نهاري'),
            ('con_fin', 'manager', 'رامي', 'الحسابات', 'Ramy', 'Finance', 'مدير موقع', 'الحسابات', 'المقر الرئيسي', 20000, 'office', 'شيفت نهاري'),
            ('con_eng_1', 'manager', 'خالد', 'المهندس', 'Khaled', 'Engineer', 'مهندس موقع', 'الهندسة', 'موقع مشروع 1', 16000, 'field_assigned', 'شيفت نهاري'),
            ('con_store', 'employee', 'سامي', 'المخزن', 'Samy', 'Store', 'أمين مخزن', 'المخازن', 'المخزن المركزي', 8500, 'office', 'شيفت نهاري'),
            ('con_worker_1', 'employee', 'حسن', 'عامل', 'Hassan', 'Worker', 'عامل', 'العمليات', 'موقع مشروع 1', 6000, 'field_assigned', 'شيفت ليلي'),
            ('con_worker_2', 'employee', 'علي', 'عامل', 'Ali', 'Worker', 'عامل', 'العمليات', 'موقع مشروع 1', 6000, 'field_assigned', 'شيفت ليلي'),
        ],
    },
    {
        'slug': 'pharma',
        'company_ar': 'شركة الشفاء للأدوية',
        'company_en': 'Shifa Pharma',
        'phone': '01050000003',
        'lat': 30.0626, 'lon': 31.2497,
        'branches': [('المقر الرئيسي', 'HQ'), ('مخزن التوزيع', 'Distribution Store')],
        'departments': [('المبيعات', 'Sales'), ('التوزيع', 'Distribution'), ('الموارد البشرية', 'HR'), ('الحسابات', 'Finance'), ('المخازن', 'Stores')],
        'job_titles': [('صاحب الشركة', 'Owner', True), ('مدير الموارد البشرية', 'HR Manager', True), ('مدير الحسابات', 'Finance Manager', True), ('مندوب طبي', 'Medical Rep', False), ('أمين مخزن', 'Store Keeper', False)],
        'shifts': [('شيفت إداري', 9, 0, 17, 0, False, True), ('شيفت ميداني', 8, 0, 16, 0, False, False)],
        'users': [
            ('ph_admin', 'company_admin', 'مازن', 'الشفاء', 'Mazen', 'Shifa', 'صاحب الشركة', 'المبيعات', 'المقر الرئيسي', 38000, 'office', 'شيفت إداري'),
            ('ph_hr', 'hr_manager', 'ريم', 'الموارد', 'Reem', 'HR', 'مدير الموارد البشرية', 'الموارد البشرية', 'المقر الرئيسي', 18000, 'office', 'شيفت إداري'),
            ('ph_fin', 'manager', 'ياسر', 'الحسابات', 'Yasser', 'Finance', 'مدير الحسابات', 'الحسابات', 'المقر الرئيسي', 21000, 'office', 'شيفت إداري'),
            ('ph_rep_1', 'employee', 'مينا', 'مندوب', 'Mina', 'Rep', 'مندوب طبي', 'المبيعات', 'المقر الرئيسي', 9500, 'field_free', 'شيفت ميداني'),
            ('ph_rep_2', 'employee', 'طارق', 'مندوب', 'Tarek', 'Rep', 'مندوب طبي', 'المبيعات', 'المقر الرئيسي', 9500, 'field_assigned', 'شيفت ميداني'),
            ('ph_store', 'employee', 'نبيل', 'المخزن', 'Nabil', 'Store', 'أمين مخزن', 'المخازن', 'مخزن التوزيع', 8500, 'office', 'شيفت إداري'),
        ],
    },
    {
        'slug': 'warehouse',
        'company_ar': 'شركة السهم للمخازن والتوزيع',
        'company_en': 'Sahm Warehousing',
        'phone': '01050000004',
        'lat': 30.1200, 'lon': 31.3300,
        'branches': [('المخزن الرئيسي', 'Main Warehouse')],
        'departments': [('المخازن', 'Warehouse'), ('التوزيع', 'Dispatch'), ('الموارد البشرية', 'HR'), ('الحسابات', 'Finance')],
        'job_titles': [('صاحب الشركة', 'Owner', True), ('مدير وردية', 'Shift Manager', True), ('أمين مخزن', 'Store Keeper', False), ('مندوب توزيع', 'Dispatcher', False)],
        'shifts': [('شيفت صباحي', 8, 0, 16, 0, False, True), ('شيفت مسائي', 16, 0, 0, 0, True, False), ('شيفت ليلي', 0, 0, 8, 0, False, False)],
        'users': [
            ('wh_admin', 'company_admin', 'حازم', 'السهم', 'Hazem', 'Sahm', 'صاحب الشركة', 'المخازن', 'المخزن الرئيسي', 32000, 'office', 'شيفت صباحي'),
            ('wh_hr', 'hr_manager', 'دينا', 'الموارد', 'Dina', 'HR', 'مدير وردية', 'الموارد البشرية', 'المخزن الرئيسي', 16500, 'office', 'شيفت صباحي'),
            ('wh_fin', 'manager', 'شريف', 'الحسابات', 'Sherif', 'Finance', 'مدير وردية', 'الحسابات', 'المخزن الرئيسي', 19000, 'office', 'شيفت صباحي'),
            ('wh_keeper', 'employee', 'باسم', 'المخزن', 'Bassem', 'Store', 'أمين مخزن', 'المخازن', 'المخزن الرئيسي', 8000, 'office', 'شيفت مسائي'),
            ('wh_dispatch', 'employee', 'كريم', 'التوزيع', 'Karim', 'Dispatch', 'مندوب توزيع', 'التوزيع', 'المخزن الرئيسي', 7800, 'field_assigned', 'شيفت ليلي'),
        ],
    },
]

created_companies = []

for cfg in SCENARIOS:
    company = make_company(cfg['company_ar'], cfg['company_en'], cfg['phone'], cfg['lat'], cfg['lon'])
    clone_template_data(company)

    branches = {x[0]: make_branch(company, x[0], x[1]) for x in cfg['branches']}
    departments = {x[0]: make_department(company, x[0], x[1]) for x in cfg['departments']}
    job_titles = {x[0]: make_job_title(company, x[0], x[1], x[2]) for x in cfg['job_titles']}
    shifts = {x[0]: make_shift(company, *x) for x in cfg['shifts']}

    for username, role, first_ar, last_ar, first_en, last_en, title_ar, dept_ar, branch_ar, salary, worker_type, shift_name in cfg['users']:
        email = f'{username}@motionhr.local'
        user = ensure_user(username, email, DEFAULT_PASSWORD, role, company=company)
        emp = make_employee(
            company=company,
            user=user,
            first_ar=first_ar,
            last_ar=last_ar,
            first_en=first_en,
            last_en=last_en,
            branch=branches[branch_ar],
            department=departments[dept_ar],
            job_title=job_titles[title_ar],
            salary=salary,
            worker_type=worker_type,
        )
        assign_shift(company, emp, shifts.get(shift_name))

    created_companies.append((company.id, company.name_ar))

print('=== DONE ===')
print('PASSWORD =', DEFAULT_PASSWORD)
for cid, name in created_companies:
    print('COMPANY:', cid, name)
print('USERS:')
for cfg in SCENARIOS:
    for username, *_rest in cfg['users']:
        print(' -', username, '/', DEFAULT_PASSWORD)
