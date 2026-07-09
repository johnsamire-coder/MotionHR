# ════════════════════════════════════════════════════════════
# 📘 MotionHR - Handout الكامل والشامل
# ════════════════════════════════════════════════════════════
# آخر تحديث: يوليو 2025
# هذا الملف يحتوي على كل تفاصيل المشروع من الصفر
# لو فتحت شات جديد - ابعت الملف ده وقول "كمل من هنا"
# ════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
# 📌 القسم 1: رؤية المشروع
# ═══════════════════════════════════════════════════════════

## اسم المنتج: MotionHR
## الشعار: HR in Motion – إدارة بسلاسة
## اللغة: عربي RTL + إنجليزي
## اللون الأساسي: أزرق مخضر (#06B6D4)
## التصميم: عصري Modern وبسيط
## الخط: Cairo (Google Fonts)

## الوصف
نظام إدارة موارد بشرية عصري وذكي
مصمم للشركات الصغيرة والمتوسطة (10-100 موظف)
في مصر والعالم العربي
يتميز بتتبع الموظفين الميدانيين في الوقت الفعلي

## العميل المستهدف
- شركات 10-100 موظف
- مصر أولاً ثم العالم العربي
- كل الأنشطة (عام)
- المشتري: صاحب شركة / HR Manager / Admin / IT
- أول عميل: الشركة اللي شغال فيها المطور

## الميزة التنافسية الأهم
GPS Live Tracking للموظفين الميدانيين
- مفيش حد في السوق المصري عامل كده بشكل احترافي
- تتبع مستمر + خرائط + زيارات + تنبيهات

## نموذج البيع
- اشتراك شهري / سنوي (SaaS)
- ترخيص دائم (مرة واحدة)
- تثبيت على سيرفرنا أو سيرفر العميل
- Multi-tenant (كل شركة ببياناتها)
- White Label لاحقاً

## التسعير المقترح
| الباقة | الموظفين | شهري | سنوي |
|--------|----------|------|------|
| Starter | حتى 15 | 299 ج.م | 2,999 ج.م |
| Business | حتى 50 | 599 ج.م | 5,999 ج.م |
| Professional | حتى 100 | 999 ج.م | 9,999 ج.م |
| Enterprise | 100+ | حسب الطلب | حسب الطلب |

### إضافات مدفوعة
| الإضافة | السعر |
|---------|-------|
| التتبع الميداني | +200 ج.م/شهر |
| Payroll متقدم | +300 ج.م/شهر |
| تثبيت سيرفر العميل | 5,000 ج.م (مرة) |
| إعداد وتدريب | 2,000 ج.م (مرة) |
| White Label | 10,000 ج.م |


# ═══════════════════════════════════════════════════════════
# 📌 القسم 2: التقنيات المستخدمة
# ═══════════════════════════════════════════════════════════

## التقنية الأساسية
- Python 3.14
- Django 6.0.7
- SQLite (للتطوير) → PostgreSQL (للإنتاج)
- HTML / CSS / JavaScript
- Bootstrap 5.3 RTL
- Bootstrap Icons
- Google Fonts (Cairo)
- Leaflet.js (خرائط تفاعلية)
- OpenStreetMap (الخرائط)
- Nominatim API (Reverse Geocoding)
- Git (إدارة الكود)
- VS Code (محرر الكود)

## مكتبات Python
- Django 6.0.7
- Pillow (للصور)
- WeasyPrint (PDF) - مؤجل حتى Deployment
- python-dotenv (لاحقاً)

## بيئة العمل
- نظام التشغيل: Windows
- Python: 3.14 64-bit
- البيئة الافتراضية: .venv
- IP الكمبيوتر: 192.168.1.45
- الوصول من الموبايل: http://192.168.1.45:8000

## طريقة العمل الجديدة (Patches)
- مجلد _patches/ لكل التعديلات
- كل مجموعة تعديلات في ملف Python واحد
- التشغيل: python _patches/patch_XX_name.py
- السكريبت يعمل كل حاجة أوتوماتيك (ملفات + تعديلات)


# ═══════════════════════════════════════════════════════════
# 📌 القسم 3: هيكل المشروع
# ═══════════════════════════════════════════════════════════

MotionHR/
├── .venv/                    # البيئة الافتراضية
├── .git/                     # Git repository
├── .gitignore                # ملفات مستبعدة من Git
├── manage.py                 # أداة إدارة Django
├── requirements.txt          # المكتبات المطلوبة
├── db.sqlite3                # قاعدة البيانات (تطوير)
│
├── _patches/                 # سكريبتات التعديلات
│   ├── patch_01_password_reset.py
│   └── patch_02_employees.py
│
├── motionhr/                 # المشروع الرئيسي (settings)
│   ├── __init__.py
│   ├── settings.py           # الإعدادات
│   ├── urls.py               # الروابط الرئيسية
│   ├── asgi.py
│   └── wsgi.py
│
├── core/                     # النواة الأساسية (Multi-tenant)
│   ├── __init__.py
│   ├── apps.py               # verbose_name = 'النواة الأساسية'
│   ├── middleware.py          # TenantMiddleware
│   ├── models.py             # TenantModel, TimeStampedModel, TenantManager
│   ├── mixins.py             # CompanyRequired, SuperAdmin, HR, Manager Mixins
│   ├── admin.py
│   ├── tests.py
│   └── views.py
│
├── accounts/                 # المستخدمين والصلاحيات
│   ├── __init__.py
│   ├── apps.py               # verbose_name = 'الحسابات والمستخدمون'
│   ├── models.py             # Custom User Model (phone, role, company, avatar)
│   ├── admin.py              # CustomUserAdmin with fieldsets
│   ├── views.py              # dashboard view
│   ├── tests.py
│   └── migrations/
│
├── companies/                # الشركات والفروع
│   ├── __init__.py
│   ├── apps.py               # verbose_name = 'الشركات والفروع'
│   ├── models.py             # Company, Branch (GPS), Department (شجري)
│   ├── admin.py              # CompanyAdmin, BranchAdmin, DepartmentAdmin
│   ├── tests.py
│   └── migrations/
│
├── employees/                # الموظفين
│   ├── __init__.py
│   ├── apps.py               # verbose_name = 'الموظفون'
│   ├── models.py             # Employee (30+ حقل), JobTitle, EmployeeDocument, EmployeeMovement
│   ├── admin.py              # EmployeeAdmin with inlines
│   ├── views.py              # CRUD + export + print
│   ├── forms.py              # EmployeeForm with validation
│   ├── urls.py               # app_name = 'employees'
│   ├── tests.py
│   └── migrations/
│
├── attendance/               # الحضور والتتبع
│   ├── __init__.py
│   ├── apps.py               # verbose_name = 'الحضور والتتبع'
│   ├── models.py             # Shift, EmployeeShift, Attendance, LocationLog, LocationCheckIn
│   ├── admin.py              # كل الـ models مسجلة
│   ├── views.py              # check_in, check_out, tracking, monitor, visits, live_map, APIs
│   ├── urls.py               # app_name = 'attendance'
│   ├── tests.py
│   └── migrations/
│
├── templates/                # صفحات HTML
│   ├── base/
│   │   ├── base.html             # Base template (Bootstrap 5 RTL + Cairo font)
│   │   └── dashboard_base.html   # Dashboard layout (Sidebar + Header + Content)
│   ├── accounts/
│   │   ├── login.html                    # صفحة تسجيل الدخول
│   │   ├── password_reset.html           # نسيت كلمة المرور
│   │   ├── password_reset_done.html      # تم الإرسال
│   │   ├── password_reset_confirm.html   # كلمة مرور جديدة
│   │   ├── password_reset_complete.html  # تم بنجاح
│   │   ├── password_reset_email.html     # قالب البريد
│   │   ├── password_reset_subject.txt    # عنوان البريد
│   │   ├── password_change.html          # تغيير كلمة المرور
│   │   └── password_change_done.html     # تم بنجاح
│   ├── dashboard/
│   │   └── index.html            # الصفحة الرئيسية (Dashboard)
│   ├── employees/
│   │   ├── list.html             # قائمة الموظفين
│   │   ├── detail.html           # تفاصيل الموظف (Tabs)
│   │   ├── form.html             # إضافة/تعديل موظف (5 خطوات)
│   │   ├── delete_confirm.html   # تأكيد الحذف
│   │   ├── print_list.html       # طباعة قائمة الموظفين
│   │   └── print_detail.html     # طباعة بطاقة موظف
│   └── attendance/
│       ├── list.html             # سجلات الحضور
│       ├── check_in.html         # تسجيل حضور/انصراف بالـ GPS
│       ├── live_map.html         # خريطة الموظفين الميدانيين Live
│       ├── tracking.html         # التتبع المستمر للموظف
│       ├── tracking_detail.html  # مسار موظف معين
│       ├── monitor.html          # متابعة الميدانيين (للمدير)
│       ├── visits.html           # قائمة الزيارات
│       └── visit_form.html       # تسجيل زيارة جديدة
│
├── static/                   # ملفات ثابتة (CSS, JS, Images)
└── media/                    # ملفات مرفوعة (صور, مستندات)


# ═══════════════════════════════════════════════════════════
# 📌 القسم 4: إعدادات المشروع (settings.py)
# ═══════════════════════════════════════════════════════════

## INSTALLED_APPS
- django.contrib.admin
- django.contrib.auth
- django.contrib.contenttypes
- django.contrib.sessions
- django.contrib.messages
- django.contrib.staticfiles
- core
- accounts
- companies
- employees
- attendance

## MIDDLEWARE
- SecurityMiddleware
- SessionMiddleware
- CommonMiddleware
- CsrfViewMiddleware
- AuthenticationMiddleware
- MessageMiddleware
- XFrameOptionsMiddleware
- core.middleware.TenantMiddleware ← مخصص

## إعدادات مخصصة
- AUTH_USER_MODEL = 'accounts.User'
- LANGUAGE_CODE = 'ar'
- TIME_ZONE = 'Africa/Cairo'
- LANGUAGE_BIDI = True
- LOGIN_URL = '/login/'
- LOGIN_REDIRECT_URL = '/dashboard/'
- LOGOUT_REDIRECT_URL = '/login/'
- ALLOWED_HOSTS = ['*']
- EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
- DEFAULT_FROM_EMAIL = 'MotionHR <noreply@motionhr.com>'
- STATIC_URL = 'static/'
- STATICFILES_DIRS = [BASE_DIR / 'static']
- MEDIA_URL = '/media/'
- MEDIA_ROOT = BASE_DIR / 'media'


# ═══════════════════════════════════════════════════════════
# 📌 القسم 5: الـ Models تفصيلياً
# ═══════════════════════════════════════════════════════════

## core/models.py
### TenantManager
- يفلتر البيانات أوتوماتيك حسب الشركة الحالية
- Super Admin يشوف كل حاجة
- باقي المستخدمين يشوفوا شركتهم فقط

### AllObjectsManager
- يرجع كل البيانات بدون فلترة
- للاستخدام في الحالات الخاصة

### TimeStampedModel (abstract)
- created_at (auto_now_add)
- updated_at (auto_now)
- created_by (ForeignKey User)
- updated_by (ForeignKey User)
- يحفظ تلقائياً مين عمل إيه

### TenantModel (abstract, يرث TimeStampedModel)
- company (ForeignKey Company)
- objects = TenantManager()
- all_objects = AllObjectsManager()
- يحدد الشركة تلقائياً من المستخدم

## accounts/models.py
### User (يرث AbstractUser)
- phone (CharField)
- role (CharField: super_admin, company_admin, hr_manager, manager, employee)
- company (ForeignKey Company)
- avatar (ImageField)

## companies/models.py
### Company
- name_ar, name_en, logo
- commercial_register, tax_number
- email, phone, address, website
- is_active, created_at, updated_at

### Branch
- company (FK), name_ar, name_en
- address, phone
- latitude, longitude ← GPS
- check_in_radius (default=100 متر) ← Geofencing
- is_main, is_active

### Department
- company (FK)
- parent (self FK) ← هيكل شجري
- name_ar, name_en, code, description
- is_active

## employees/models.py
### JobTitle (يرث TenantModel)
- name_ar, name_en, description, is_active

### Employee (يرث TenantModel)
- user (OneToOne → User)
- employee_code (يتولد أوتوماتيك EMP00001)
- البيانات الشخصية: first_name_ar, middle_name_ar, last_name_ar, first_name_en, last_name_en
- national_id (14 رقم), birth_date, gender, marital_status, religion, nationality
- photo (ImageField)
- بيانات التواصل: email, phone, phone2, address, city
- بيانات التعيين: hire_date, contract_type, contract_end_date
- branch (FK), department (FK), job_title (FK), direct_manager (self FK)
- basic_salary (DecimalField)
- بيانات بنكية: bank_name, bank_account, iban
- تأمينات: insurance_number, insurance_date, has_insurance
- طوارئ: emergency_contact_name, emergency_contact_relation, emergency_contact_phone
- status (active, on_leave, suspended, resigned, terminated, retired)
- termination_date, termination_reason, notes
- is_field_worker ← للتتبع الميداني
- Properties: full_name_ar, full_name_en, age, years_of_service
- unique_together: [company, employee_code], [company, national_id]

### EmployeeDocument (يرث TenantModel)
- employee (FK)
- document_type (national_id, passport, contract, certificate, cv, medical, license, insurance, other)
- title, file (FileField), issue_date, expiry_date, notes

### EmployeeMovement (يرث TenantModel)
- employee (FK)
- movement_type (promotion, transfer, salary_change, etc.)
- movement_date, old_value, new_value, reason, document (FileField)

## attendance/models.py
### Shift (يرث TenantModel)
- name, shift_type (fixed, flexible, rotating)
- start_time, end_time
- grace_period (default=15 دقيقة)
- work_sunday → work_saturday (BooleanFields)
- break_duration (default=60 دقيقة)
- Property: work_hours

### EmployeeShift (يرث TenantModel)
- employee (FK), shift (FK)
- start_date, end_date, is_active

### Attendance (يرث TenantModel)
- employee (FK), date, shift (FK)
- check_in: time, latitude, longitude, address, within_range, notes
- check_out: time, latitude, longitude, address, within_range, notes
- الحسابات: work_hours, late_minutes, early_leave_minutes, overtime_hours
- status (present, absent, late, early_leave, on_leave, holiday, weekend)
- is_manually_edited, admin_notes
- Methods: calculate_work_hours(), calculate_late_minutes()
- unique_together: [employee, date]

### LocationLog (يرث TenantModel) ← التتبع المستمر
- employee (FK), timestamp
- latitude, longitude, accuracy, speed
- battery_level, address
- Index: [employee, -timestamp]

### LocationCheckIn (يرث TenantModel) ← زيارات المواقع
- employee (FK)
- visit_type (client_visit, supplier_visit, site_inspection, maintenance, delivery, meeting, purchase, other)
- location_name
- arrival: time, latitude, longitude, address
- departure: time, latitude, longitude
- purpose, notes, photo
- status (arrived, in_progress, completed, cancelled)
- Property: duration_minutes


# ═══════════════════════════════════════════════════════════
# 📌 القسم 6: الـ URLs
# ═══════════════════════════════════════════════════════════

## motionhr/urls.py (الرئيسي)
/ → home_redirect (dashboard أو login)
/admin/ → Django Admin
/login/ → تسجيل الدخول
/logout/ → تسجيل الخروج
/password-reset/ → نسيت كلمة المرور
/password-reset/done/ → تم الإرسال
/password-reset-confirm/<uidb64>/<token>/ → كلمة مرور جديدة
/password-reset-complete/ → تم بنجاح
/password-change/ → تغيير كلمة المرور
/password-change/done/ → تم بنجاح
/dashboard/ → الصفحة الرئيسية
/employees/ → include employees.urls
/attendance/ → include attendance.urls

## employees/urls.py (app_name = 'employees')
/ → employee_list (قائمة)
/add/ → employee_add (إضافة)
/<pk>/ → employee_detail (تفاصيل)
/<pk>/edit/ → employee_edit (تعديل)
/<pk>/delete/ → employee_delete (حذف)
/print/ → employee_print (طباعة قائمة)
/<pk>/print/ → employee_print_detail (طباعة بطاقة)

## attendance/urls.py (app_name = 'attendance')
/ → attendance_list (سجلات الحضور)
/check-in/ → check_in_page (صفحة تسجيل الحضور)
/api/check-in/ → api_check_in (API حضور)
/api/check-out/ → api_check_out (API انصراف)
/visits/ → visits_list (قائمة الزيارات)
/visits/add/ → visit_add (تسجيل زيارة)
/map/ → live_map (الخريطة الحية)
/api/live-locations/ → api_live_locations (API مواقع)
/tracking/ → tracking_page (التتبع المستمر)
/api/track/ → api_track_location (API تتبع)
/tracking/employee/<id>/ → employee_tracking_detail (مسار موظف)
/monitor/ → field_employees_monitor (متابعة الميدانيين)
/api/monitor/ → api_monitor_data (API متابعة)


# ═══════════════════════════════════════════════════════════
# 📌 القسم 7: الميزات المكتملة تفصيلياً
# ═══════════════════════════════════════════════════════════

## ✅ Multi-tenant System
- كل شركة تشوف بياناتها فقط
- Super Admin يشوف كل حاجة
- TenantMiddleware يحدد الشركة من المستخدم المسجل
- TenantManager يفلتر القويريات أوتوماتيك
- الحماية على مستوى الـ Model مش بس الـ View

## ✅ نظام الحضور GPS
- Check-in بالـ GPS من المتصفح (geolocation API)
- Reverse Geocoding (اسم الشارع والحي والمدينة)
- خريطة تفاعلية Leaflet على الصفحة
- حساب المسافة من الفرع (Haversine Formula)
- Geofencing (التحقق من نطاق الفرع)
- حساب التأخير أوتوماتيك مع فترة سماح
- حساب ساعات العمل

## ✅ التتبع المستمر (Live Tracking)
- إرسال الموقع كل دقيقتين أوتوماتيك
- عرض المسار على الخريطة (Polyline)
- حفظ Battery Level
- localStorage لاستمرار التتبع
- يعمل في الخلفية

## ✅ متابعة الموظفين الميدانيين
- كارتات لكل موظف ميداني
- حالة الاتصال (متصل/خامل/غير متصل)
- حالة الحركة (متحرك/ثابت)
- المسافة المقطوعة اليوم (كم)
- نقاط التتبع اليوم
- تنبيهات لما حد يتحرك أو يقف
- Notifications API للمتصفح
- تحديث تلقائي كل 30 ثانية
- زرار "المسار" لعرض مسار الموظف بالتفصيل

## ✅ خريطة الموظفين الميدانيين Live
- خريطة Leaflet كاملة
- Custom Markers (دائرية بأول حرف من الاسم)
- Popup بتفاصيل الموظف
- قائمة جانبية بالأسماء
- ضغط على الاسم → Focus على الخريطة
- Auto-zoom على كل الماركرات
- تحديث تلقائي

## ✅ زيارات المواقع (Location Check-ins)
- فورم تسجيل زيارة
- GPS + اسم المكان + خريطة
- أنواع زيارات (عميل، مورد، صيانة، شراء...)
- قائمة الزيارات مع الفلترة

## ✅ نظام الموظفين
- فورم 5 خطوات (Multi-step wizard)
- بحث وفلترة (اسم، رقم وظيفي، قومي، موبايل)
- تصدير Excel (بالعربي)
- صفحة طباعة قائمة الموظفين
- صفحة طباعة بطاقة موظف (بالتوقيعات)
- صفحة تفاصيل بالتابات (شخصي، تعيين، مالي، مستندات)

## ✅ Frontend احترافي
- Sidebar جانبية داكنة أنيقة
- Header علوي مع User Dropdown
- Responsive Design (يشتغل موبايل)
- خط Cairo العربي
- Bootstrap Icons
- Hover Effects
- Loading Spinners
- Messages/Alerts

## ✅ Password Management
- نسيت كلمة المرور (عبر البريد)
- تغيير كلمة المرور (للمسجل)
- صفحات احترافية لكل خطوة
- Email في التيرمنال (للتطوير)


# ═══════════════════════════════════════════════════════════
# 📌 القسم 8: قرارات التصميم المهمة
# ═══════════════════════════════════════════════════════════

| # | القرار | السبب |
|---|--------|-------|
| 1 | Web App Responsive | كود واحد، أسهل وأرخص |
| 2 | Django كـ Backend | Python، شامل، مجاني، مناسب للمبتدئين |
| 3 | SQLite للتطوير | مش محتاج تثبيت، بعدين PostgreSQL |
| 4 | Bootstrap 5 RTL | تصميم جاهز عربي، Responsive |
| 5 | البداية بدون Offline | المزامنة معقدة، نأجلها |
| 6 | Multi-tenant من البداية | أساسي لأن كل شركة ببياناتها |
| 7 | الحضور بـ GPS | ميزة تنافسية أساسية |
| 8 | Leaflet بدل Google Maps | مجاني 100% بدون API Key |
| 9 | Nominatim Geocoding | مجاني بدون حدود |
| 10 | MVP أولاً | نبيع بسرعة ونكمل تدريجياً |
| 11 | Patches نظام | أسرع في التطوير، ملف واحد يعمل كل حاجة |
| 12 | Email Console للتطوير | مش محتاج إعداد Gmail دلوقتي |
| 13 | Custom User Model من البداية | لو اتعمل بعدين = مشكلة كبيرة |
| 14 | TenantModel Abstract | كل Model يرث منه = محمي أوتوماتيك |
| 15 | company=employee.company | لازم نحدد الشركة عند إنشاء سجل حضور |


# ═══════════════════════════════════════════════════════════
# 📌 القسم 9: الأوامر المهمة
# ═══════════════════════════════════════════════════════════

## البيئة الافتراضية
.venv\Scripts\activate          # تفعيل
deactivate                       # إلغاء

## Django
python manage.py runserver 0.0.0.0:8000  # تشغيل (يسمح للموبايل)
python manage.py runserver               # تشغيل (محلي فقط)
python manage.py makemigrations          # إنشاء migrations
python manage.py migrate                 # تطبيق migrations
python manage.py createsuperuser         # إنشاء admin
python manage.py startapp <name>         # إنشاء app جديد
python manage.py check                   # فحص الأخطاء

## Git
git add .
git commit -m "رسالة التعديل"
git status
git log --oneline

## Patches
python _patches/patch_01_password_reset.py
python _patches/patch_02_employees.py

## الوصول
http://127.0.0.1:8000/            # من الكمبيوتر
http://192.168.1.45:8000/         # من الموبايل
http://127.0.0.1:8000/admin/      # لوحة الإدارة


# ═══════════════════════════════════════════════════════════
# 📌 القسم 10: سجل الأخطاء والحلول
# ═══════════════════════════════════════════════════════════

| # | المشكلة | الحل |
|---|---------|------|
| 1 | django-admin not recognized | استخدم: python -m django startproject |
| 2 | Pillow not installed | pip install Pillow |
| 3 | InconsistentMigrationHistory | امسح db.sqlite3 + migrations واعمل من أول |
| 4 | ModuleNotFoundError: accounts | شيل accounts من INSTALLED_APPS مؤقتاً ثم أنشئها |
| 5 | AUTH_USER_MODEL not installed | تأكد إن models.py فيه User class |
| 6 | true بدل True | Python: True, False, None بحرف كبير |
| 7 | NOT NULL company_id | لازم نحدد company=employee.company عند إنشاء Attendance |
| 8 | Logout GET Method Not Allowed | استخدم form method="post" بدل <a href> |
| 9 | staticfiles.W004 directory not exist | أنشئ فولدر static/ |
| 10 | Custom User Model بعد migrate | لازم Custom User Model يتعمل قبل أول migrate |
| 11 | IndentationError | التأكد من المسافات في Python |
| 12 | PowerShell Execution Policy | استخدم Command Prompt بدل PowerShell |
| 13 | VS Code JavaScript warnings | تجاهلها - Django template tags مش JavaScript |


# ═══════════════════════════════════════════════════════════
# 📌 القسم 11: الدروس المستفادة
# ═══════════════════════════════════════════════════════════

1. Custom User Model لازم قبل أول migrate أبداً
2. عند مسح App لازم نشيلها من INSTALLED_APPS الأول
3. __pycache__ و db.sqlite3 لازم يتمسحوا عند الـ reset
4. admin.py محتاج تسجيل الـ models عشان تظهر في Admin
5. company_id لازم يتحدد في كل TenantModel عند الإنشاء
6. Logout في Django الجديد لازم POST مش GET
7. ALLOWED_HOSTS = ['*'] عشان الموبايل يوصل
8. 0.0.0.0:8000 عشان يشتغل من أي جهاز في الشبكة
9. blank=True في Model لو عايز الفورم يقبله فاضي
10. select_related() لتحسين الأداء في queries


# ═══════════════════════════════════════════════════════════
# 📌 القسم 12: حالة الإنجاز التفصيلية
# ═══════════════════════════════════════════════════════════

## ✅ مكتمل 100%
- [x] البنية التحتية (Django + Git + Multi-tenant)
- [x] نظام الشركات (Company + Branch + Department)
- [x] Frontend Base (Login + Dashboard + Sidebar)
- [x] Responsive Design
- [x] Password Reset + Change

## ✅ مكتمل 85-95%
- [x] نظام المستخدمين (90%)
  - ⏳ ملف شخصي
  - ⏳ إعدادات
- [x] نظام الموظفين (85%)
  - ⏳ PDF Export (WeasyPrint على Windows)
  - ✅ طباعة
  - ⏳ صفحة تعديل مستقلة
- [x] نظام الحضور والتتبع (95%)
  - ⏳ Push Notifications حقيقية
  - ⏳ تنبيه خروج من نطاق محدد

## ⏳ لم يبدأ بعد
- [ ] نظام الإجازات (LeaveType, LeaveBalance, LeaveRequest, Workflow)
- [ ] نظام الطلبات (Loan, Letter, Overtime, DataChange)
- [ ] صفحات الشركات والفروع (Frontend)
- [ ] صفحة الشيفتات (Frontend)
- [ ] Dashboard حقيقي (Charts + أرقام حقيقية)
- [ ] التقارير الكاملة (حضور، تأخيرات، أوفر تايم)
- [ ] PWA (Manifest, Service Worker, Icons)
- [ ] Landing Page
- [ ] Onboarding Wizard
- [ ] صفحات إضافية (Profile, Settings, 404, Search)
- [ ] نظام المرتبات (Payroll)
- [ ] نظام التوظيف (Recruitment)
- [ ] تقييم الأداء
- [ ] التدريب
- [ ] API (Django REST Framework)


# ═══════════════════════════════════════════════════════════
# 📌 القسم 13: خطة العمل المتبقية (بالترتيب)
# ═══════════════════════════════════════════════════════════

## المجموعة المكتملة
- [x] المجموعة 1: Reset/Change Password ✅
- [x] المجموعة 2: الموظفين (PDF/Print) ✅ (جزئياً)

## المجموعات التالية بالترتيب
- [ ] المجموعة 3: التنبيهات (Push + خارج النطاق)
- [ ] المجموعة 4: صفحات الشركات والفروع والإدارات (Frontend)
- [ ] المجموعة 5: الشيفتات (Frontend)
- [ ] المجموعة 6: Dashboard حقيقي (Charts + أرقام)
- [ ] المجموعة 7: PWA (تطبيق موبايل)
- [ ] المجموعة 8: Landing Page
- [ ] المجموعة 9: Onboarding Wizard
- [ ] المجموعة 10: صفحات إضافية (Profile, Settings, 404, Search)

## بعد الـ MVP
- [ ] المجموعة 11: نظام الإجازات
- [ ] المجموعة 12: التقارير الكاملة
- [ ] المجموعة 13: نظام المرتبات
- [ ] المجموعة 14: التوظيف والأداء والتدريب
- [ ] المجموعة 15: API + React Native


# ═══════════════════════════════════════════════════════════
# 📌 القسم 14: حاجات مؤجلة لمرحلة النشر (Deployment)
# ═══════════════════════════════════════════════════════════

## 1. إعدادات البريد الإلكتروني الحقيقي
- [ ] إعداد Gmail/SendGrid/AWS SES
- [ ] تغيير EMAIL_BACKEND في settings.py
- [ ] اختبار إرسال البريد فعلاً
- [ ] Domain للـ From Email

## 2. إعدادات الأمان
- [ ] DEBUG = False
- [ ] SECRET_KEY في متغير بيئة (.env)
- [ ] ALLOWED_HOSTS محدد
- [ ] HTTPS/SSL
- [ ] CSRF Settings
- [ ] Secure Cookies

## 3. قاعدة البيانات
- [ ] PostgreSQL بدل SQLite
- [ ] Backup تلقائي
- [ ] Database Optimization

## 4. الأداء
- [ ] Redis للـ Cache
- [ ] CDN للملفات الثابتة
- [ ] Compress للصور
- [ ] Gunicorn/uWSGI
- [ ] Nginx

## 5. الاستضافة
- [ ] Railway / Render / VPS
- [ ] Domain (motionhr.com)
- [ ] SSL Certificate
- [ ] DNS Setup


# ═══════════════════════════════════════════════════════════
# 📌 القسم 15: Git Commits History
# ═══════════════════════════════════════════════════════════

1. "Initial Django project setup"
2. "Add Custom User Model with phone and role fields"
3. "Add Companies, Branches, Departments + link Users to Company"
4. "Add core app with Multi-tenant Middleware and Base Models"
5. "Add Employees app with Employee, JobTitle, Documents, Movements"
6. "Add Attendance app: Shifts, Attendance, Location Tracking, Check-ins"
7. "Add responsive support + Dashboard works on mobile"
8. "Add Frontend Base: Login page + Dashboard + Bootstrap 5 RTL"
9. "Add professional Dashboard Layout with Sidebar and Header"
10. "Add Employees pages: List, Detail, Delete with search and filters"
11. "Add professional Employee Add/Edit form with 5-step wizard"
12. "Fix Employee List: better stats card + working Excel export"
13. "Update sidebar with attendance links + fix all navigation"
14. "Complete GPS attendance system with map, address, distance calculation"
15. "Add Attendance system: Check-in/out with GPS + Live tracking base"
16. "Add Live Map + Visits with GPS tracking"
17. "Add Live Tracking system with continuous location updates"
18. "Add employee info card at top of tracking page"
19. "Add Field Employees Monitor with alerts + Employee Path Detail"
20. "Complete Live Tracking system - MotionHR MVP core is READY!"
21. "Patch 01: Password Reset + Change Password"
22. "Patch 02: Add Print pages + PDF export for Employees"


# ═══════════════════════════════════════════════════════════
# 📌 القسم 16: إرشادات لشات جديد
# ═══════════════════════════════════════════════════════════

## لو فتحت شات جديد:
1. ابعت هذا الملف كامل
2. اكتب: "أنا بعمل مشروع MotionHR، ده الـ Handout، كمل معايا من آخر خطوة"
3. حدد آخر مجموعة خلصتها
4. لو في كود معين محتاج تكمله ابعته برضو

## معلومات عن المطور:
- مبتدئ في Python (بيتعلم مع المشروع)
- بيشتغل على Windows
- الشرح بالعامية المصرية
- خطوة خطوة جدًا مع شرح مبسط
- بيئة العمل: VS Code
- يفضل Scripts أوتوماتيكية (مجلد _patches/)
- مش يحب نسخ ولصق كتير

## القاعدة الذهبية:
- أي تعديل جديد = ملف Script في _patches/
- السكريبت يعمل كل حاجة لوحده
- متقولش "افتح وحط وغير" - اعمل باتش!


# ═══════════════════════════════════════════════════════════
# نهاية الـ Handout - يتم التحديث مع كل خطوة جديدة
# ═══════════════════════════════════════════════════════════