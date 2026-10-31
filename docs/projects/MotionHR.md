# MotionHR: الوثيقة الشاملة

> نظام موارد بشرية متكامل بنظام اشتراكات (SaaS) للشركات المصرية والعربية: الموظفين، والحضور بالـ GPS والبصمة، والتتبع الميداني، والشيفتات، والإجازات، والطلبات، والمهمات، والمرتبات، والسياسات، والتقارير.
> المشروع 3 مستودعات:
> - **الباك إند (السيرفر):** `johnsamire-coder/MotionHR` (المستودع ده). آخر نسخة: `eed7d8e` (خصم بعدد الساعات في جزاءات التأخير والغياب والخروج المبكر).
> - **الويب:** `johnsamire-coder/MotionHR_Web`. آخر نسخة: `87682c1`.
> - **الموبايل:** `johnsamire-coder/MotionHR_Employee` (تطبيق الموظف والمدير، إصدار 1.5.0). آخر نسخة: `b8b796e`.
>
> الوثيقة دي اتعملت من قراية الكود في التلات مستودعات يوم 31 أكتوبر 2026، ومعاها `MASTER_DOCS.md` و `API_DOCS.md`.

---

## الفهرس

1. [نظرة عامة](#1-نظرة-عامة)
2. [طريقة البناء (التقنيات)](#2-طريقة-البناء-التقنيات)
3. [العناوين والسيرفر](#3-العناوين-والسيرفر)
4. [هيكل الباك إند](#4-هيكل-الباك-إند)
5. [هيكل الويب والموبايل](#5-هيكل-الويب-والموبايل)
6. [هيكل البيانات وتعدد الشركات](#6-هيكل-البيانات-وتعدد-الشركات)
7. [الأدوار والصلاحيات](#7-الأدوار-والصلاحيات)
8. [شاشات الويب والتبويبات والزراير](#8-شاشات-الويب-والتبويبات-والزراير)
9. [شاشات الموبايل](#9-شاشات-الموبايل)
10. [الموديلات (قاعدة البيانات)](#10-الموديلات-قاعدة-البيانات)
11. [الـ API (الربط)](#11-الـ-api-الربط)
12. [الأنظمة الأساسية بالتفصيل](#12-الأنظمة-الأساسية-بالتفصيل)
13. [التقارير](#13-التقارير)
14. [الخدمات التلقائية (Cron)](#14-الخدمات-التلقائية-cron)
15. [أوامر الإدارة (Management Commands)](#15-أوامر-الإدارة-management-commands)
16. [التنصيب والتشغيل](#16-التنصيب-والتشغيل)
17. [طريقة التحديث والنشر](#17-طريقة-التحديث-والنشر)
18. [الاختبارات](#18-الاختبارات)
19. [سجل آخر الشغل](#19-سجل-آخر-الشغل)
20. [ملاحظات وتحذيرات](#20-ملاحظات-وتحذيرات)

---

## 1. نظرة عامة

| الحاجة | القيمة |
| --- | --- |
| الاسم | MotionHR — الشعار: HR in Motion – إدارة بسلاسة |
| النوع | SaaS، كل شركة مشتركة ليها بياناتها لوحدها |
| صاحب المشروع | جون سمير |
| اللغة | عربي (RTL) وإنجليزي |
| الهوية | خط Cairo، واللون الأساسي أزرق مخضر، والموبايل بنفسجي (`#4A148C`) |
| الميزة الأهم | حضور بالـ GPS ونطاق جغرافي، وتتبع ميداني مباشر، واعتماد الأجهزة، ومحرك مرتبات مربوط بالسياسات |

| الحاجة | الرقم |
| --- | --- |
| الموديلات | حوالي 130 موديل |
| روابط الـ API | حوالي 300 رابط (منهم 396 مسار في `attendance/urls.py` لوحده) |
| شاشات الويب | 108 صفحة (HR + مدير + موظف) |
| شاشات الموبايل | حوالي 103 شاشة |
| التقارير | 25 تقرير |

---

## 2. طريقة البناء (التقنيات)

| الطبقة | التقنية |
| --- | --- |
| الباك إند | Django 5 + Django REST Framework + SimpleJWT + Token Auth + django-cors-headers + django-countries |
| القاعدة | PostgreSQL على السيرفر (SQLite للتطوير المحلي، والاختيار من `DB_ENGINE`) |
| التشغيل | Gunicorn + Nginx على Ubuntu 22.04 |
| الإشعارات | Firebase Cloud Messaging (FCM) + Web Push |
| PDF العربي | reportlab + arabic_reshaper + python-bidi، بخط Amiri |
| الويب | Next.js 16 + React 19 + TypeScript + Tailwind 4 + shadcn/ui + React Query + Zustand + react-hook-form + zod + Recharts + Leaflet (خرايط) + jsPDF + ExcelJS |
| الموبايل | Flutter (Android + iOS): geolocator، flutter_map، flutter_background_service (تتبع في الخلفية)، firebase_messaging، local_auth (بصمة الوش/الصباع)، flutter_udid (بصمة الجهاز)، sqflite، pdf، excel، fl_chart |
| أجهزة البصمة | ZKTeco بنظام ADMS (`/iclock/...`) + أداة شبكة محلية بـ Python |
| المنطقة الزمنية واللغة | `Africa/Cairo`، والافتراضي `ar` |

---

## 3. العناوين والسيرفر

| الحاجة | القيمة |
| --- | --- |
| الباك إند / API | https://jssolutions-eg.com |
| تطبيق الويب | https://app.jssolutions-eg.com |
| السيرفر | Hostinger VPS — Ubuntu 22.04 — `194.164.77.164` (نفس سيرفر Motion POS) |
| مكان الباك إند | `/var/www/motionhr` (والبيئة `/var/www/motionhr/venv`) |
| مكان الويب | `/var/www/motionhr_web` |
| النسخ الاحتياطي | `/var/www/motionhr/backups` و `/var/backups/motionhr_*` |
| الخطوط | `/var/www/motionhr/core/fonts/` (Cairo و Amiri) |
| الخدمات | `motionhr.service` (Django)، و`motionhr-web.service` (Next.js)، و`nginx.service` |
| القاعدة | PostgreSQL على بورت 5432 (Motion POS على 5433 منفصل) |
| جهاز التطوير | `C:\MotionHR\Backend`، `C:\MotionHR\web`، `C:\MotionHR\Mobile` |

---

## 4. هيكل الباك إند

```
MotionHR/
├── manage.py, requirements.txt
├── motionhr/            ← settings.py, urls.py (الرئيسي), wsgi.py
├── core/                ← TenantModel الأساسي، الخطوط، قوالب الشركة، أمان التصدير، breadcrumb
├── accounts/            ← المستخدم، الدخول (بالاسم أو كود الموظف)، JWT، التفعيل، الصلاحيات والأدوار، FCM، الإعلانات، الأجهزة المعتمدة
├── companies/           ← الشركة، الفروع، الأقسام، اللائحة (Charter) وتوقيعها، إعدادات الدخول، تفضيلات الإشعارات
├── employees/           ← الموظف، المسميات، المستندات، الحركات، الخصومات، الاستيراد من Excel، التصدير
├── attendance/          ← أكبر تطبيق: الحضور، والشيفتات، والسياسات، والمرتبات، والمهمات، والزيارات، ومواقع العمل، والتذكيرات (+ ملفات api_*.py)
├── leaves/              ← الإجازات، والأرصدة، والسياسات، واسترداد الإجازة، والبديل
├── requests_app/        ← الطلبات العامة، ومسارات الموافقة، والتفويض، والأذونات
├── reports/             ← التقارير
├── subscriptions/       ← الباقات والاشتراكات والمزايا
├── audit/               ← سجل التعديلات (مين عمل إيه وإمتى)
├── biometric/           ← أجهزة البصمة ZKTeco
├── landing/             ← الصفحة العامة
├── templates/, static/  ← قوالب Django القديمة (لوحة الويب القديمة)
├── _deploy/             ← سكريبتات النشر (policies_hub, hours_penalty, employee_code, biometric) + nginx + gunicorn
├── _patches/            ← تعديلات قديمة
├── backups/             ← نسخ قديمة من ملفات
├── .github/workflows/api_test.yml  ← اختبار API تلقائي (Newman)
├── API_DOCS.md, MASTER_DOCS.md, MotionHR_Handout.md, PROJECT_VISUAL_GUIDE.md, SIMULATION_GUIDE.md, START_HERE_OWNER_GUIDE.md
└── سكريبتات فحص (api_health_check*.py, deep_scan.py, full_business_test.py, seed_business_scenarios.py …)
```

**ملفات الـ API جوه `attendance/`:** `api_mobile.py` (كل روابط الموبايل)، `api_employee_management.py`، `api_employee_profile.py`، `api_shifts.py`، `api_attendance_policy.py`، `api_attendance_adjustment.py`، `api_auto_checkin.py`، `api_payroll.py`، `api_payroll_cycle.py`، `api_manual_entries.py`، `api_missions.py`، `api_field_visits.py`، `api_field_visits_report.py`، `api_work_locations*.py`، `api_departments.py`، `api_permissions*.py`، `api_company_policy.py`، `api_company_allowance_policy.py`، `api_general_policies.py`، `api_leave_rule.py`، `api_tax_policy.py`، `api_insurance.py`، `api_eos_policy.py`، `api_rules.py`، `api_disciplinary.py`، `api_offboarding.py`، `api_charters.py`، `api_announcements.py`، `api_attachments.py`، `api_reminders.py`، `api_reports.py`.
**محركات الحساب:** `payroll_rules.py` (جزاءات ومكافآت السياسات)، `mission_days.py`، `location_utils.py` (المسافات والنطاق)، `reminders.py`، `fcm_logic.py`، `action_scope.py` (نطاق صلاحية المدير)، `report_export_helper.py`.

---

## 5. هيكل الويب والموبايل

### الويب (`MotionHR_Web`)
```
src/
├── app/
│   ├── page.tsx (الصفحة الرئيسية), login, signup, change-password
│   ├── hr/        ← لوحة الموارد البشرية وصاحب الشركة (70 صفحة)
│   ├── manager/   ← لوحة المدير المباشر (21 صفحة)
│   ├── employee/  ← لوحة الموظف (13 صفحة)
│   └── api/       ← وسطاء (proxy) للمستندات وسجل التعديلات
├── components/ (analytics, auth, dashboard [sidebar, manager-sidebar, employee-sidebar, header], employees, hr, maps, onboarding, reports, ui)
└── lib/ (api/client.ts + endpoints, stores [اللغة…], hooks, schemas, utils, audit-proxy, documents-proxy)
```
- عنوان الـ API من `NEXT_PUBLIC_API_BASE`.
- التشغيل: `npm run dev` (تطوير) / `npm run build && npm start`.

### الموبايل (`MotionHR_Employee`)
```
lib/
├── main.dart, background_service.dart (التتبع في الخلفية), firebase_options.dart
├── l10n/ (app_ar.arb, app_en.arb)
├── services/ (api_client.dart, api_service.dart, …)
├── widgets/
└── screens/
    ├── auth/        ← تفعيل الحساب
    ├── common/      ← شجرة الهيكل، واختيار مكان على الخريطة
    ├── employee/    ← شاشات الموظف
    └── manager/     ← شاشات المدير (+ payroll/, reports/, shifts/)
```
- الإصدار `1.5.0+8`، وأقل أندرويد 21.
- البناء: `flutter pub get` ثم `flutter build apk` أو `flutter build ios`.

---

## 6. هيكل البيانات وتعدد الشركات

```
Company (الشركة)
  └── Branches (الفروع)
       └── Departments (الأقسام، بهيكل شجري)
            └── JobTitles (المسميات، ومستويات وظيفية)
                 └── Employees (الموظفين)
```

- كل موديل شركة بيورث `TenantModel` (فيه `company` + تواريخ الإنشاء والتعديل) ومعاه `TenantManager` اللي بيفلتر بالشركة لوحده، و`AllObjectsManager` للكل.
- **مين المدير:** `user.role` واحد من (`manager`, `hr_manager`, `company_admin`) أو `job_title.is_manager = True`.
- **نطاق المدير:** المدير والـ HR بيتعاملوا مع الموظفين اللي في نطاقهم بس، ومفيش حد يوافق على طلب نفسه (إلا صاحب الشركة).
- الشركة الموقوفة والحساب المعطّل بيتمنعوا من الدخول، ورسالة الإيقاف واضحة.

---

## 7. الأدوار والصلاحيات

### الأدوار الأساسية (`User.ROLE_CHOICES`)
| الدور | الاسم | اللوحة |
| --- | --- | --- |
| `super_admin` | سوبر أدمن (صاحب المنتج) | لوحة Django + كل الشركات + الموقع القديم |
| `company_admin` | مدير الشركة (المالك) | `/hr/*` كاملة |
| `hr_manager` | مدير الموارد البشرية | `/hr/*` |
| `manager` | مدير مباشر | `/manager/*` (فريقه) |
| `employee` | موظف | `/employee/*` + تطبيق الموبايل |

### الصلاحيات التفصيلية (`accounts/permissions_models.py`)
- `CustomRole` أدوار مخصصة (مثلاً "مدير مهندسين")، و`RolePermission` صلاحيات الدور، و`UserRole` ربط المستخدم بالدور، و`UserPermissionOverride` استثناء لموظف معيّن.
- **نطاق الصلاحية:** الشركة · قسمه · فريقه · الموظف نفسه.
- شاشات: **مركز الصلاحيات** ← الأدوار · تعيين صلاحيات · الصلاحيات الافتراضية · الاستثناءات · تصدير الصلاحيات.
- الأدوار النظامية ماتتمسحش، وإدارة الأدوار لصاحب الشركة بس.

---

## 8. شاشات الويب والتبويبات والزراير

### 8.1 الصفحات العامة
| الرابط | الشاشة |
| --- | --- |
| `/` | الصفحة الرئيسية (تعريف بالمنتج والباقات) |
| `/signup` | تسجيل شركة جديدة (فترة تجريبية) |
| `/login` | الدخول (بالاسم أو كود الموظف) |
| `/change-password` | تغيير كلمة المرور |

### 8.2 لوحة الموارد البشرية (`/hr/*`) — القايمة الجانبية بالترتيب
| الرابط | الشاشة | أهم المحتوى والزراير |
| --- | --- | --- |
| `/hr/dashboard` | لوحة المعلومات التنفيذية | الطلبات المعلقة، والإجازات المعلقة، و**نبض الشركة النهاردة** (الإجمالي، حاضر، متأخر، غايب، في إجازة)، والرواتب الشهرية، والسلف النشطة، ومعدل الحضور، وحالات تحتاج متابعة، واختصارات |
| `/hr/employees` | الموظفين | بحث وفلاتر، والحالات (نشط، في إجازة، موقوف، مستقيل، منتهي الخدمة)، و**تصدير Excel** و**تصدير PDF**، وصفحات |
| `/hr/employees/[id]` | ملف الموظف | **التبويبات:** بيانات شخصية · بيانات وظيفية · الراتب · العقد · الحضور · الإجازات · الطلبات · ملف الموظف (المستندات) · بيانات الدخول. **الزراير:** تعديل · حفظ · إلغاء · سجل التعديلات · إعادة كلمة المرور · إيقاف/تفعيل · إنهاء الخدمة (تاريخ وسبب) · حذف نهائي. طريقة الصرف: كاش/بنك/إنستاباي/محفظة. نوع العمل: مكتبي/ميداني حر/ميداني محدد. نوع العقد: دائم/مؤقت/تدريب/عمل حر/دوام جزئي. **كود الموظف** بيتكتب بالإيد |
| `/hr/employees/import` | استيراد الموظفين | قالب Excel (نوع العملية، والاسم عربي وإنجليزي، والرقم القومي، والموبايل، والميلاد، والتعيين، والفرع، والقسم، والمسمى، والتصنيف، والمرتب) + رفع + سجل الاستيراد |
| `/hr/attendance` | الحضور والانصراف | تقرير الحضور اليومي، و**تعديل** سجل (الحضور، والانصراف، والحالة: حاضر/متأخر/غائب/انصراف مبكر/إجازة/مأمورية، و**سبب التعديل إجباري**)، وتصدير PDF |
| `/hr/leaves` | الإجازات | كروت (الإجمالي، المقبولة، المعلقة، المرفوضة)، وبحث، و**موافقة** / **رفض** (بسبب)، و**إضافة إجازة**، وتصدير |
| `/hr/requests` | الطلبات | القايمة، والتفاصيل، و**قبول** / **رفض** بسبب، وتصدير |
| `/hr/payroll` | الرواتب | السنة والشهر والفرع والقسم وبحث. أعمدة: الأساسي، البدلات، الإضافي، خصم تأخير، غياب، جزاء، سلفة، الصافي. **التفاصيل** لكل موظف، و**إضافة استحقاق / استقطاع يدوي** (خصم / مكافأة / بدل)، وتصدير |
| `/hr/payroll-runs` | تشغيل المرتبات | **تشغيل مسير رواتب جديد** (السنة، الشهر، ملاحظات) ← **حساب وإنشاء المسير** ← مراجعة ← **اعتماد وإغلاق المسير** أو **إلغاء المسودة**. الحالات: مسودة/معتمد. تصدير Excel وطباعة PDF |
| `/hr/manual-entries` | الإدخالات اليدوية | جزاءات · مكافآت · بدلات (معلقة/معتمدة/مرفوضة) + **السلف والأقساط** (إضافة سلفة: المبلغ، والقسط، وبداية الخصم). **اعتماد** / **رفض** بسبب |
| `/hr/missions` | المهمات | إنشاء مهمة (العنوان، والوصف، والأولوية: منخفضة/عادية/عالية/عاجلة، والوقت، والمكان على الخريطة، والعميل، والموظفين). الحالات: انتظار، معيّنة، موافق عليها، نشطة، جارية، مكتملة، ملغاة. **داشبورد الفيدباك** (قيمة الصفقات، مهتم جداً، مهتم، عقود موقّعة، تحتاج متابعة). طلبات المهمات (قبول/رفض). تصدير |
| `/hr/locations` | المواقع المباشرة | خريطة الموظفين الميدانيين لايف ومساراتهم |
| `/hr/announcements` | الإعلانات | إنشاء وتعديل إعلان واستهداف (الكل/فرع/قسم/موظفين) ومرفقات |
| `/hr/reports` | مركز التقارير | 25 تقرير (القسم 13) |
| `/hr/audit` | سجل التعديلات | مين عمل إيه وإمتى، وتاريخ كل موظف |
| `/hr/biometric` | أجهزة البصمة | **التبويبات:** الأجهزة · ربط الأرقام بالموظفين · رفع ملف بصمات · التقرير والمقارنة. تسجيل جهاز (الرقم التسلسلي SN، والاسم، والفرع)، وحالة الاتصال، وتشغيل/إيقاف، وتصدير Excel للمقارنة ولكل البصمات |
| `/hr/departments` | الأقسام | إضافة وتعديل وحذف، ومدير القسم، والهيكل |
| `/hr/branches` | الفروع | إضافة وتعديل، والموقع |
| `/hr/shifts` | الشيفتات | **إضافة شيفت جديد** (الاسم، والنوع: صباحي/مسائي/ليلي/مرن/ثابت، والساعات، والحضور والانصراف، والسماح، والحضور المبكر، والانصراف المتأخر) · **جعله افتراضي** · **تخصيص** لفرع/قسم/موظف من تاريخ · إلغاء التعيين · تعديل · حذف. (+ `/hr/shifts/exceptions` الاستثناءات، و `/hr/shifts/rotations` التناوب) |
| `/hr/job-titles` | المسميات الوظيفية | إضافة وتعديل، ومدير ولا لأ، والمستوى |
| `/hr/company` | معلومات الشركة | البيانات، ورفع اللوجو (PNG/JPG حد أقصى 2 ميجا) |
| `/hr/permissions` | الصلاحيات | (القسم 7) |
| `/hr/policies` | مركز السياسات | **سياسات الحضور والانصراف** (التأخير، الغياب، الانصراف المبكر ونسيان البصمة، الأوفر تايم، أقل مدة والمعامل والحدود، الشيفت الليلي والعمل في يوم الراحة) · **دورة حساب المرتبات (Cut-off)** · **العطلات الرسمية** · **قواعد الحضور والمرتبات** · **سياسات وتدرج الإجازات** · **البدلات** · **التأمينات** · **الضرايب** (شرايح وإعفاء) · **مكافأة نهاية الخدمة**. الحالات: مسودة/معتمدة/مؤرشفة + زرار **اعتماد**. صفحات فرعية: `allowance`, `attendance`, `bonus`, `deduction`, `leave`, `work` |
| `/hr/policies/work` | سياسة العمل | أيام العمل والراحة، وطريقة تسجيل الحضور (يدوي فقط / إشعار ذكي / تسجيل تلقائي)، وشغل 24 ساعة 7 أيام |
| `/hr/org-chart` | الهيكل التنظيمي | شجرة |
| `/hr/termination` | إنهاء الخدمة | إجراءات الإنهاء والتسليم |
| `/hr/work-locations` | مواقع العمل | الأنواع (مكتب، فرع، عن بُعد، ميداني، مستودع، أخرى)، والمكان من الخريطة، والنطاق بالمتر. **التعيين:** موظفين محددين / قسم / فرع / الشركة كلها. **قبول واعتماد** أو **رفض** المواقع اللي الموظفين اقترحوها |
| `/hr/geofence` | النطاق الجغرافي | خريطة ورسم النطاق |
| `/hr/regulations` | اللائحة التنظيمية | إصدارات اللائحة، والتوقيع الرقمي، ومين وافق |
| `/hr/leave-recall` | استرداد الإجازة | استدعاء موظف من إجازته |
| `/hr/flex-shift` | الشيفت المرن | تظبيط أيام المرن |
| `/hr/reminders` | التذكيرات | إعدادات التذكير اليومي |
| `/hr/devices` | الأجهزة المعتمدة | الجهاز، والمنصة، والمعرّف، وآخر دخول، وأول جهاز، والحضور التلقائي. **موافقة** · **رفض** · **إلغاء الجهاز** |
| `/hr/settings` | الإعدادات | إعدادات الشركة العامة والدخول |

### 8.3 لوحة المدير (`/manager/*`)
القايمة: **الرئيسية** · **فريقي** · **الحضور** · **المهمات** · **المواقع** · **الطلبات** · **التقارير**.
- الرئيسية: الغايب النهاردة، والمتأخر، والمهمات، والإجازات المعلقة، والطلبات المعلقة (**مراجعة**)، والبديل.
- صفحات المدير الشخصية: حضوري، وزياراتي الميدانية، وإجازاتي، ومهماتي، وقسيمة مرتبي، وأذوناتي، وملفي، وطلباتي، والإشعارات، والهيكل، واللائحة، وملخص البدائل (`substitution-summary`)، وتقرير الزيارات الميدانية.

### 8.4 لوحة الموظف (`/employee/*`)
القايمة: **الرئيسية** · **الحضور** · **الإجازات** · **الطلبات** · **الأذونات** · **المهمات** · **الزيارات الميدانية** · **قسيمة المرتب** · **الإعلانات** · **الإشعارات** · **اللائحة** · **الهيكل** · **ملفي**.
- الرئيسية: **تسجيل الحضور** · **خروج مؤقت** · **استئناف العمل** · **تسجيل الانصراف**، ووقت الحضور والانصراف، واختصارات (إجازاتي، طلباتي، مهماتي، حضوري).
- الحضور: تسجيل الحضور والانصراف، و**بدء زيارة ميدانية** (النوع والغرض) و**إنهاء الزيارة**، وزيارات اليوم، وإجمالي التأخير وساعات الشغل، وسجل الحضور.

---

## 9. شاشات الموبايل

تطبيق واحد للموظف والمدير (الشاشات بتظهر حسب الدور):

| المجموعة | الشاشات |
| --- | --- |
| البداية | اختيار اللغة أول مرة، وتفعيل الحساب، والدخول، والإعدادات |
| الموظف | الملخص، والملف الشخصي، والمستندات، والحركات، وقسيمة المرتب، والإعلانات وتفاصيلها، والطلبات، والزيارات الميدانية، وشيفتي، ومواقع عملي، والمهمات وتفاصيلها |
| المدير | قايمة الموظفين وملف الموظف (**7 تبويبات**)، وإنشاء موظف، والأقسام والفروع والمسميات، ومعلومات الشركة وتعديلها، والإعلانات وإنشاؤها، والمهمات وإنشاؤها، وسياسة الحضور، وسياسة الإجازات، وسياسة العمل، والعطلات الرسمية، واسترداد الإجازة، والتظبيطات المرنة، وأدوات الاستيراد، والهيكل، وإنهاء الخدمة، وتقرير المواقع، واعتماد مواقع العمل، وإعدادات التذكير، والأجهزة المعتمدة |
| صلاحيات المدير | مركز الصلاحيات، والأدوار وتفاصيلها، والتعيين، والاستثناءات، والتصدير، وإدارة الصلاحيات، وصلاحيات الموظف |
| المرتبات (`manager/payroll/`) | مركز المرتبات، وتشغيل المسير وتفاصيله، والملخص، والقسيمة، وتفاصيل الموظف، والإدخالات اليدوية، والمكافآت والجزاءات، وقواعد الجزاءات والمكافآت والبدلات والإجازات، والتأمينات، والضرايب، ونهاية الخدمة، ودورة المرتبات، وإعدادات المرتبات، وسياسات الشركة (تبويبات: الكل/بدلات/جزاءات/مكافآت/طبي/اجتماعي) |
| التقارير (`manager/reports/`) | مركز التقارير، والغياب، والحضور، والحضور اليومي، والتأخير، ومقارنة الفروع، والإجازات (عادي ومفصّل)، والرواتب، والأذونات، والطلبات، والشيفتات، وساعات العمل |
| الشيفتات (`manager/shifts/`) | الشيفتات، وإنشاء وتعديل، والتعيين وتفاصيله، والاستثناء، والتناوب |

**مزايا الموبايل:** تسجيل الحضور بالـ GPS، والتتبع في الخلفية للميدانيين، واختيار مكان من الخريطة، وإشعارات FCM، وبصمة الوش/الصباع، وبصمة الجهاز (UDID) لاعتماد الجهاز، وتصدير PDF وExcel، وفحص الإصدار (`check-version`).

---

## 10. الموديلات (قاعدة البيانات)

| التطبيق | الموديلات |
| --- | --- |
| core | `TimeStampedModel`, `TenantModel`, `TenantManager`, `AllObjectsManager`, `TrialSignupLead`, `AppVersion` |
| accounts | `User`, `EmployeeNotification`, `PushSubscription`, `FCMDeviceToken`, `NotificationLog`, `TrustedDevice`, `CustomRole`, `RolePermission`, `UserRole`, `UserPermissionOverride` |
| companies | `Company`, `Branch`, `Department`, `DepartmentHierarchy`, `CompanyLoginSettings`, `WorkCharter`, `CharterVersion`, `CharterAcceptance`, `CharterDigitalSignature`, `CharterNotificationLog`, `CompanyPolicy`, `NotificationPreference` |
| employees | `JobTitle`, `JobHierarchyLevel`, `DepartmentJobTitleRule`, `Employee`, `EmployeeDocument`, `EmployeeFolder`, `EmployeeMovement`, `Deduction`, `ImportLog` |
| attendance (الحضور والشيفتات) | `Shift`, `AttendanceSession`, `ShiftAssignment`, `EmployeeShift`, `ShiftChangeRequest`, `ShiftOverride`, `ShiftRotation`, `ShiftRotationSlot`, `ShiftRotationAssignment`, `Attendance`, `DailyAttendanceSummary`, `FlexDayAdjustment`, `AttendanceActionLog`, `DailyAssignment` |
| attendance (السياسات والقواعد) | `AttendancePolicy`, `AttendancePolicyAssignment`, `LateRule`, `AbsenceRule`, `OvertimeRule`, `NightShiftRule`, `WeekendWorkRule`, `LateRepeatPenalty`, `LateIncident`, `LateNotification`, `DisciplinaryRule`, `DisciplinaryAction`, `PermissionLedger` |
| attendance (الموقع والتتبع) | `LocationLog`, `LocationCheckIn`, `LocationHistory`, `RouteHistory`, `TrackingAlert`, `EmployeeWorkLocation` |
| attendance (سياسات الشركة والمرتبات) | `CompanyWorkPolicy`, `PayrollAllowance`, `PayrollDeduction`, `CompanyAllowancePolicy`, `CompanyDeductionPolicy`, `CompanyBonusPolicy`, `CompanyInsurancePolicy`, `CompanyPayrollCyclePolicy`, `PenaltyRule`, `BonusRule`, `AllowanceRule`, `LeaveRule`, `ManualPenalty`, `ManualBonus`, `ManualAllowance`, `ManualEntryApprovalSetting`, `TaxPolicy`, `EndOfServicePolicy`, `CompanyPolicy`, `PolicyAcceptance` |
| attendance (تشغيل المرتبات) | `PayrollRun`, `PayrollLine`, `PayrollBonus`, `PayrollPenalty`, `PayrollInstallment` |
| attendance (المهمات) | `Mission`, `MissionAssignment`, `MissionLocation`, `MissionAttachment`, `MissionRequest`, `MissionClient`, `MissionFeedback`, `MissionFeedbackAddendum`, `MissionFollowup` |
| leaves | `LeaveType`, `LeaveBalance`, `LeaveRequest`, `LeavePolicy`, `LeavePolicyTier`, `LeavePolicyTypeRule`, `LeaveBalanceAdjustment`, `LeaveRecallRequest`, `ManagerSubstitution` |
| requests_app | `RequestCategory`, `RequestType`, `EmployeeRequest`, `ApprovalFlow`, `ApprovalDelegation`, `PermissionPolicy`, `PermissionUsage` |
| subscriptions | `FeatureFlag`, `SubscriptionPlan`, `CompanySubscription` |
| audit | `AuditLog` |
| biometric | `BiometricDevice`, `BiometricUserMap`, `BiometricPunch` |

---

## 11. الـ API (الربط)

**الأساس:** `https://jssolutions-eg.com`. الموبايل بيستخدم JWT (`/attendance/api/mobile/jwt/...`)، والويب بيستخدم JWT/Token من خلال `lib/api/client.ts`.
القايمة الكاملة بكل رابط موجودة في `MASTER_DOCS.md` (القسم 10) و `API_DOCS.md`. المجموعات:

| المجموعة | أمثلة |
| --- | --- |
| الدخول | `api/mobile/login`, `api/mobile/logout`, `api/mobile/jwt/*`, `api/mobile/activate-account`, `api/mobile/change-password`, تفعيل الحساب، والدخول بكود الموظف، وقفل بعد محاولات |
| الأجهزة | `api/mobile/device/*` (تسجيل الجهاز، الموافقة، الرفض، الإلغاء) |
| الموظفين | إدارة الموظفين، والملف، والمستندات (إضافة/تعديل/حذف مع تذكير بالانتهاء)، والحركات، والاستيراد، والتصدير، و**تعديل كود الموظف** |
| الحضور | `api/check-in/`, `api/check-out/`, `api/mobile/attendance`, `api/mobile/history`, `api/mobile/status`, `api/mobile/geofence`, `api/mobile/geofence-ping`, تعديل الحضور، والحضور التلقائي |
| الموقع والتتبع | `api/mobile/location`, `api/track/`, `api/live-locations/`, `api/employee-route/<id>`, `api/monitor/`, `api/stealth-location/` |
| الشيفتات | `api/mobile/my-shift`, إنشاء وتعديل وتعيين واستثناء وتناوب، وكشف التداخل |
| الإجازات | `api/mobile/leave-types`, `api/mobile/leave-request`, `api/mobile/my-leaves`, `api/mobile/leave-recall`, `api/mobile/leave-substitutes` |
| الطلبات | `api/mobile/request-types`, `api/mobile/submit-request`, `api/mobile/my-requests`, الموافقة والرفض |
| الإشعارات | `api/mobile/notifications`, `api/mobile/fcm-token` |
| الإعلانات واللائحة | `api/mobile/announcements`, `api/mobile/my-pending-announcements`, `api/mobile/charter(s)` |
| المهمات والزيارات | `api/mobile/missions`, `api/mobile/field-visits`, تقرير الزيارات |
| مواقع العمل | `api/mobile/work-locations` (اقتراح، واعتماد، ورفض، وتعيين) |
| المرتبات | الحساب، والمسيرات، والاعتماد، والقسيمة، والإدخالات اليدوية، والسلف |
| السياسات | الحضور، والعمل، والبدلات، والخصومات، والمكافآت، والإجازات، والتأمين، والضرايب، ونهاية الخدمة، ودورة المرتبات |
| الصلاحيات | الأدوار، والتعيين، والاستثناءات، والتصدير، ورصيد الأذونات |
| الشركة | البيانات، والفروع، والأقسام، والمسميات، والهيكل |
| إنهاء الخدمة والجزاءات | Offboarding، Disciplinary |
| التقارير | 11 تقرير × 3 صيغ (JSON / Excel / PDF) = 33 رابط، + باقي التقارير |
| المدير والـ HR | `api/mobile/manager/*`, `api/mobile/hr/*` |
| الإصدار | `api/mobile/check-version` |
| أجهزة البصمة | `/iclock/cdata`, `/iclock/getrequest`, `/iclock/devicecmd` (بروتوكول ADMS لأجهزة ZKTeco) + `/biometric/...` |
| سجل التعديلات | `/audit/...` |
| الاشتراكات | `/subscriptions/...` (`my-plan`، والتمديد) |

---

## 12. الأنظمة الأساسية بالتفصيل

### 12.1 الحضور الذكي
- **طرق التسجيل (من سياسة العمل):** يدوي فقط · إشعار ذكي · تسجيل تلقائي.
- **قواعد الحضور حسب نوع الموظف:**
  - مكتبي برّه النطاق ← مرفوض.
  - ميداني حر ← من أي مكان.
  - ميداني محدد ← لازم يكون جوه موقع معتمد.
  - الـ GPS مقفول ← مرفوض + تنبيه للمدير.
- **خروج مؤقت / استئناف العمل** أثناء اليوم (`AttendanceSession`).
- **الانصراف التلقائي** (`auto_checkout`) لو الموظف نسي.
- **تعديل الحضور** من الـ HR بسبب إجباري، ومتسجّل في السجل.

### 12.2 اعتماد الأجهزة
1. أول جهاز ← معتمد لوحده + الحضور التلقائي شغال.
2. جهاز جديد ← مستني + إشعار للمدير/الـ HR.
3. موافقة المدير ← معتمد + الحضور التلقائي شغال.
4. رفض المدير ← مرفوض + الحضور التلقائي واقف.
5. نفس الجهاز بحساب تاني ← مرفوض + إشعار "نشاط مشبوه" للمدير.

### 12.3 الشيفتات
- الأنواع: ثابت (`fixed`)، وشيفتين في اليوم (`split_fixed`)، ومرن (`flexible`)، وبعد نص الليل (`overnight`).
- الشيفت الليلي بيتحسب على يومين، وبيمنع تسجيل حضور مكرر.
- كشف التداخل بين التعيينات، وفحص تغطية التناوب (أيام ناقصة / أيام متداخلة).
- التعيين لفرع أو قسم أو موظف من تاريخ معيّن، وشيفت افتراضي للشركة.
- إيقاف الشيفت بيحتفظ بالتاريخ.

### 12.4 الإجازات
- أنواع الإجازات وأرصدتها، وسياسات بتدرج (حسب سنين الخدمة)، والترحيل للسنة الجاية (`carry_forward_leave`).
- الرصيد بيتحسب مرة واحدة، وتعديل الإجازة بيعيد حساب الأيام والرصيد.
- **البديل:** صاحب الإجازة بيختار بديل (`ManagerSubstitution`)، وبيتلغي لوحده بعد الإجازة.
- استرداد الإجازة (`LeaveRecallRequest`).

### 12.5 الطلبات والموافقات
- أنواع طلبات مقسّمة لفئات (`seed_request_types` بيعمل الافتراضي).
- `ApprovalFlow`: مسار موافقة لكل نوع طلب، لحد 3 مستويات + تخطّي.
- `ApprovalDelegation`: تفويض أثناء الغياب.
- قرار الطلب مرة واحدة بس، ومفيش حد يوافق على طلب نفسه.
- الأذونات (`PermissionPolicy` / `PermissionUsage` / `PermissionLedger`) بحد أقصى ورصيد.

### 12.6 المرتبات
**المحرك:** `calculate_effective_payroll(emp, year, month, settings)` بيحسب لكل موظف:
- المرتب الأساسي + البدلات + الأوفر تايم + المكافآت + بدل الليل + بدل العطلة = الإجمالي.
- ناقص: خصم التأخير + الغياب + الانصراف المبكر + الإجازة بدون مرتب + نقص الساعات المرنة + التأمين + الأقساط + الجزاءات + الخصومات.
- = **صافي المرتب**، ومعاه أيام الشغل والحضور والغياب والتأخير.

**قواعد الجزاءات (`payroll_rules.py`):**
- شرايح تأخير/غياب/خروج مبكر. نوع الخصم: بالأيام، أو بالمبلغ، أو **بعدد الساعات** (جديد: سعر الساعة من شيفت الموظف × قيمة الشريحة).
- التأخير بعد آخر شريحة = آخر شريحة + الدقايق الزيادة بالسعر الافتراضي.
- الأوفر تايم: الحد الأدنى والحد اليومي بيتحسبوا لكل يوم.
- الخصومات بتتقرّب لكل يوم زي قواعد سياسة الحضور.

**الدورة:** دورة المرتبات (Cut-off) ← الإدخالات اليدوية (جزاءات/مكافآت/بدلات بموافقة) ← تشغيل المسير (مسودة) ← مراجعة ← اعتماد وإغلاق ← القسيمة للموظف.

### 12.7 المهمات والزيارات الميدانية
- المهمة: عنوان، ووصف، وأولوية، ووقت، ومكان، وعميل، وموظفين. الموظف ممكن يطلب مهمة (`MissionRequest`) والمدير يقبل أو يرفض أو يعيد التعيين.
- **الفيدباك:** بعد الزيارة الموظف بيكتب النتيجة (مهتم جداً / مهتم / عقد / متابعة) وقيمة الصفقة، ومتابعات.
- **الزيارة الميدانية:** بدء وإنهاء بالموقع والغرض، وتقرير للمدير.
- التتبع المستمر للميدانيين (`LocationLog`/`RouteHistory`) وخريطة لايف.

### 12.8 الإشعارات
الأنواع: تذكير حضور (للموظف وللمدير بالغايبين)، وتذكير اللائحة (للموظف وللمدير)، وفجوة في تغطية الشيفت، وجهاز جديد مستني موافقة، ونشاط مشبوه، وتحذير تأخير، وإشعار عام، وموافقة/رفض طلب، وموافقة/رفض إجازة، وبداية فترة شيفت مقسوم وفواتها، واقتراح موقع عمل، وتحديث حالة الجهاز، وانتهاء مستند.

### 12.9 أجهزة البصمة (ZKTeco)
- **ADMS:** الجهاز بيبعت البصمات للسيرفر لوحده على `/iclock/cdata`.
- **رفع ملف:** لو الجهاز مابيدعمش السيرفر، البصمات بتترفع من ملف.
- **أداة الشبكة المحلية** (`_deploy/biometric/zk_tool.py` + `install_sync.ps1`): بتقرا بيانات الجهاز، وتمسح أدمن ضايع، وتصدّر البصمات، وتبعت أسماء المستخدمين للسيرفر، ووضع مزامنة تلقائي للأجهزة اللي من غير Cloud Server.
- **ربط الأرقام:** رقم الموظف على الجهاز ← الموظف في البرنامج.
- **تقرير المقارنة:** بصمات الجهاز مقابل حضور البرنامج.
- ⚠️ لسه **مش بيتطبق على الحضور** (مقارنة بس).

### 12.10 اللائحة التنظيمية
إصدارات (`CharterVersion`)، وتوقيع رقمي (`CharterDigitalSignature`)، وتذكير للي ماوافقش.

### 12.11 الاشتراكات
باقات (`SubscriptionPlan`) بمزايا (`FeatureFlag`)، واشتراك كل شركة (`CompanySubscription`) وتمديده، وتسجيل الشركات التجريبية (`TrialSignupLead`)، وإيقاف الشركة لو الاشتراك خلص.

---

## 13. التقارير

25 تقرير في `/hr/reports`:

| التقرير | الرابط |
| --- | --- |
| الغياب | `absence` |
| الحضور | `attendance` |
| الحضور اليومي | `daily-attendance` |
| الحضور الشهري | `monthly-attendance` |
| التأخير | `late` |
| ساعات العمل | `work-hours` |
| الشيفتات | `shifts` |
| الإجازات (أساسي) | `leaves-basic` |
| الإجازات (مفصّل) | `leaves-enhanced` |
| الأذونات | `permissions` |
| الطلبات | `requests` |
| الرواتب | `payroll` |
| التحويل البنكي | `bank-transfer` |
| التأمينات | `insurance` |
| الضريبة | `tax` |
| السلف والقروض | `loans-advances` |
| المصروفات (Reimbursements) | `reimbursements` |
| مكافأة نهاية الخدمة | `eos` |
| انتهاء العقود | `contracts-expiry` |
| دوران الموظفين | `turnover` |
| مقارنة الفروع | `branch-comparison` |
| أداء المهمات | `missions-performance` |
| الزيارات الميدانية | `field-visits` |
| تتبع المواقع | `location-tracking` |
| لوحة التنفيذيين | `executive-dashboard` |

كل تقرير بيتصدّر Excel و PDF (عربي بخط Amiri). التقارير بتحترم الإجازات وأيام الراحة، وبتتفلتر حسب نطاق المدير.

---

## 14. الخدمات التلقائية (Cron)

```bash
python manage.py send_reminders --type checkin         # 10:00 الصبح
python manage.py send_reminders --type checkout        # بعد الشيفت
python manage.py send_reminders --type pending         # يومياً
python manage.py send_reminders --type charter         # 9:30 الصبح
python manage.py send_reminders --type documents       # انتهاء المستندات
python manage.py send_reminders --type split_periods   # أثناء الشيفت المقسوم
python manage.py send_reminders --type shift_coverage  # 8:00 الصبح
python manage.py auto_checkout                         # انصراف تلقائي
python manage.py compute_daily_summaries               # ملخص الحضور اليومي
python manage.py notify_upcoming_shifts                # تنبيه بالشيفت الجاي
python manage.py deactivate_manager_substitutions      # إلغاء البدائل بعد الإجازة
python manage.py carry_forward_leave                   # ترحيل الإجازات (سنوي)
```

---

## 15. أوامر الإدارة (Management Commands)

| الأمر | التطبيق | بيعمل إيه |
| --- | --- | --- |
| `send_reminders`, `auto_checkout`, `compute_daily_summaries`, `notify_upcoming_shifts` | attendance | التذكيرات والحضور |
| `add_bulk_allowance` | attendance | بدل لمجموعة موظفين |
| `convert_policy_rules` | attendance | تحويل قواعد السياسات للشكل الجديد |
| `company_access` | companies | فتح/قفل وصول شركة |
| `import_employees_bulk`, `generate_employee_template` | employees | استيراد الموظفين وقالبه |
| `seed_request_types` | requests_app | أنواع الطلبات الافتراضية |
| `biometric_setup` | biometric | تجهيز أجهزة البصمة |
| `audit_setup` | audit | تجهيز سجل التعديلات |
| `carry_forward_leave`, `deactivate_manager_substitutions` | leaves | الإجازات والبدائل |

---

## 16. التنصيب والتشغيل

### تطوير محلي (الباك إند)
```bash
python -m venv venv && source venv/bin/activate      # ويندوز: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```
- الصفحات القديمة (Django): `/` و `/login/` و `/admin/` و `/dashboard/`.
- من الموبايل على نفس الشبكة: `http://<رقم الجهاز>:8000`.
- متغيرات البيئة: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` + مفتاح Firebase (`firebase-key.json` مايترفعش).

### الويب
```bash
npm install
NEXT_PUBLIC_API_BASE=https://jssolutions-eg.com npm run dev     # أو npm run build && npm start
```

### الموبايل
```bash
flutter pub get
flutter run                       # تجربة
flutter build apk --release       # أندرويد
```

### السيرفر (أول مرة) — الملفات في `_deploy/`
- `ubuntu_server_commands.md` و `deploy_checklist.md`: خطوات التنصيب.
- `gunicorn_motionhr.service`: Gunicorn بـ 3 workers على `127.0.0.1:8001`.
- `nginx_motionhr.conf`: `/static/` و `/media/` وتحويل الباقي للـ Gunicorn، وحد الرفع 30 ميجا.
- `budget_estimate.md`: تقدير التكلفة.

---

## 17. طريقة التحديث والنشر

كل ميزة جديدة ليها سكريبت نشر **بأمر واحد** في `_deploy/<الميزة>/deploy.sh`، بيتلصق في تيرمنال السيرفر:
```bash
curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/MotionHR/main/_deploy/hours_penalty/deploy.sh | sudo bash
```
السكريبت بيعمل:
1. نسخة احتياطية من الكود (الباك إند والويب) ومن القاعدة في `/var/backups/motionhr_*`.
2. ينزّل الملفات المعدّلة بس من GitHub.
3. يشغّل الاختبارات على السيرفر (على قاعدة وهمية في الذاكرة، مابيلمسش البيانات).
4. يبني الويب ويعيد تشغيل الخدمات (`motionhr` و `motionhr-web`).
5. لو أي خطوة فشلت: بيرجّع كل حاجة زي ما كانت لوحده (و`rollback.sh` للرجوع اليدوي).

السكريبتات الموجودة: `policies_hub` (مع `precheck_access.py` و `check_company.py` و `survey_rules.py` و `rollback.sh`)، و`hours_penalty`، و`employee_code`، و`biometric`.
لو المستودع خاص: مفتاح قراية من GitHub في `/root/.motionhr_github_token`.

---

## 18. الاختبارات

```bash
python manage.py test
```
- اختبارات بالمجموعات في `attendance/test_group3…16_*.py` (الصلاحيات، والأخطاء، والسيرفر، والأمان، والنطاق، والموبايل، والتطبيق، والويب، والتقارير، والمستندات).
- `attendance/test_payroll_scenarios.py`: سيناريوهات المرتبات (200/200 ناجحة في آخر تعديل).
- `accounts/test_access_guard.py`, `attendance/test_action_scope.py`, `employees/test_import_bulk.py`.
- **GitHub Actions** (`.github/workflows/api_test.yml`): مع كل رفع على `main` بيشغّل Newman على `motionhr_smoke_test.json`.
- سكريبتات فحص يدوي: `api_health_check.py`, `api_health_check_v2.py`, `full_business_test.py`, `seed_business_scenarios.py`, `SIMULATION_GUIDE.md`.

---

## 19. سجل آخر الشغل

| التاريخ | النسخة | الحاجة |
| --- | --- | --- |
| 25 أكتوبر 2026 | `eed7d8e` | نوع خصم "عدد ساعات" في شرايح التأخير والغياب والخروج المبكر |
| 24 أكتوبر | `17bcc92` / `98601fd` | كود الموظف بيتكتب بالإيد من المدير + سكريبت نشره |
| 22 أكتوبر | `5c8066c` / `16c77fc` | مركز السياسات وتصليحات محرك المرتبات، ودمج المستندات |
| 21 أكتوبر | `c428803` … `0161d31` | أجهزة البصمة ZKTeco (ADMS، ورفع ملف، وربط، ومقارنة، وأداة الشبكة، والمزامنة التلقائية) |
| 21 أكتوبر | `2be2480` | مستندات الموظف (إضافة/تعديل/حذف) وتذكير بالانتهاء للموظف والمدير والـ HR |
| 21 أكتوبر | `12b077c` | تقرير الزيارات الميدانية وسجل التعديلات |
| 20–21 أكتوبر | المجموعات 8–13 | الدخول بكود الموظف، والنطاق، وقفل بعد محاولات، والبدائل، والمهمات، والإعلانات، ودعم تطبيق 1.5، وأمان الرفع والتصدير |
| 20 أكتوبر | عدة | حظر الحسابات المعطّلة والشركات الموقوفة، والمدير يتعامل مع نطاقه بس، ومفيش موافقة على النفس |

---

## 20. ملاحظات وتحذيرات

- **الأسرار:** `firebase-key.json` و `.env` و `local_settings.py` ممنوعين من الرفع (`.gitignore`).
- المستودع فيه ملف `db.sqlite3` (3.4 ميجا) وفولدرات `backups/` و `_patches/` وسكريبتات فحص كتير في الجذر؛ محتاجين تنضيف.
- ملفات فاضية بأسماء غريبة في الجذر (`Get-Content`, `flutter`, `result.txt`) اتعملت بالغلط من أوامر PowerShell.
- `scope=team_only` في مسارات الموافقة موجود في الموديل بس مش متفعّل في التحقق.
- البصمة (ZKTeco) لسه مقارنة بس، مابتتطبقش على الحضور.
- بيانات الديمو والاختبار (الشركة التجريبية والحسابات) موجودة في `MASTER_DOCS.md` و `START_HERE_OWNER_GUIDE.md`.
- الويب والموبايل مستودعات منفصلة، وأي تعديل في الـ API لازم يتراجع أثره عليهم.
