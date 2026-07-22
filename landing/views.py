"""
landing/views.py
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings


def landing_home(request):
    """الصفحة الرئيسية التسويقية"""
    # لو مسجل دخوله يروح للـ Dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")

    context = {
        "page_title": "MotionHR - إدارة الموارد البشرية",
        "plans": _get_plans(),
        "features": _get_features(),
        "stats": _get_stats(),
    }
    return render(request, "landing/home.html", context)


def landing_pricing(request):
    """صفحة الأسعار"""
    context = {
        "page_title": "الأسعار - MotionHR",
        "plans": _get_plans(),
    }
    return render(request, "landing/pricing.html", context)


def landing_contact(request):
    """صفحة التواصل"""
    contact_info = getattr(settings, "MOTIONHR_SALES_CONTACT", {})

    if request.method == "POST":
        name    = request.POST.get("name", "")
        email   = request.POST.get("email", "")
        phone   = request.POST.get("phone", "")
        company = request.POST.get("company", "")
        message = request.POST.get("message", "")
        employees = request.POST.get("employees", "")

        # هنا ممكن تضيف إرسال إيميل أو حفظ في DB
        # حالياً نطبعها في الـ Console
        print(f"""
=== طلب تواصل جديد ===
الاسم: {name}
الإيميل: {email}
الموبايل: {phone}
الشركة: {company}
الموظفون: {employees}
الرسالة: {message}
======================
        """)

        messages.success(
            request,
            "✅ تم استقبال رسالتك بنجاح! سيتواصل معك فريقنا خلال 24 ساعة."
        )
        return redirect("landing:contact")

    context = {
        "page_title":   "تواصل معنا - MotionHR",
        "contact_info": contact_info,
    }
    return render(request, "landing/contact.html", context)


def landing_about(request):
    """صفحة عن النظام"""
    features = [
        ("people-fill", "#06B6D4", "#e0f7fa", "إدارة الموظفين", "ملف شامل لكل موظف مع كل بياناته"),
        ("geo-alt-fill", "#10b981", "#e8f5e9", "حضور GPS", "تسجيل الحضور بالموقع مع التحقق من النطاق"),
        ("broadcast", "#f59e0b", "#fff3e0", "تتبع ميداني Live", "تابع موظفيك على الخريطة في الوقت الفعلي"),
        ("calendar2-check", "#e91e63", "#fce4ec", "إدارة الإجازات", "طلبات وموافقات وأرصدة تلقائية"),
        ("bar-chart-fill", "#7c3aed", "#ede7f6", "تقارير وتحليلات", "تقارير شاملة مع تصدير Excel"),
        ("phone-fill", "#0891B2", "#e0f2fe", "تطبيق موبايل", "PWA يعمل على كل الأجهزة بدون تحميل"),
        ("sliders", "#f59e0b", "#fff3e0", "سياسات مرنة", "كل شركة تحدد سياساتها الخاصة"),
        ("diagram-2", "#7c3aed", "#ede7f6", "Workflow ذكي", "مسارات موافقة مخصصة لكل شركة"),
        ("eye-slash-fill", "#ef4444", "#fde8e8", "تتبع صامت", "مراقبة الأداء أثناء ساعات العمل"),
    ]
    context = {
        "page_title": "عن MotionHR",
        "features": features,
    }
    return render(request, "landing/about.html", context)


def _get_plans():
    return [
        {
            "name":        "Starter",
            "name_ar":     "المبتدئ",
            "price":       490,
            "price_year":  4900,
            "employees":   "حتى 15",
            "color":       "#6b7280",
            "popular":     False,
            "features": [
                "إدارة الموظفين",
                "الحضور بالـ GPS",
                "التقارير الأساسية",
                "تصدير Excel",
                "دعم فني",
            ],
            "missing": [
                "التتبع الميداني",
                "الخريطة الحية",
                "الإشعارات SMS",
            ],
        },
        {
            "name":        "Business",
            "name_ar":     "الأعمال",
            "price":       690,
            "price_year":  6900,
            "employees":   "حتى 50",
            "color":       "#06B6D4",
            "popular":     True,
            "features": [
                "كل مميزات Starter",
                "التتبع الميداني",
                "الخريطة الحية",
                "زيارات الموظفين",
                "دخول بالرقم الوظيفي",
                "تقارير متقدمة",
                "إدارة الإجازات",
            ],
            "missing": [
                "إشعارات SMS",
                "2FA",
            ],
        },
        {
            "name":        "Professional",
            "name_ar":     "الاحترافي",
            "price":       890,
            "price_year":  8900,
            "employees":   "حتى 100",
            "color":       "#7c3aed",
            "popular":     False,
            "features": [
                "كل مميزات Business",
                "دخول بالموبايل",
                "إشعارات SMS",
                "Payroll متقدم",
                "مصادقة ثنائية",
                "API Access",
                "تدريب مجاني",
            ],
            "missing": [],
        },
        {
            "name":        "Enterprise",
            "name_ar":     "المؤسسي",
            "price":       0,
            "price_year":  0,
            "employees":   "100+",
            "color":       "#1f2937",
            "popular":     False,
            "features": [
                "كل المميزات",
                "White Label",
                "سيرفر العميل",
                "SSO / Active Directory",
                "دعم مخصص 24/7",
                "تدريب وتأهيل",
                "تخصيص كامل",
            ],
            "missing": [],
        },
    ]


def _get_features():
    return [
        {
            "icon":  "people-fill",
            "color": "#06B6D4",
            "bg":    "#e0f7fa",
            "title": "إدارة الموظفين",
            "desc":  "ملف شامل لكل موظف: بيانات شخصية، عقود، مستندات، تاريخ وظيفي كامل",
        },
        {
            "icon":  "geo-alt-fill",
            "color": "#4caf50",
            "bg":    "#e8f5e9",
            "title": "حضور GPS",
            "desc":  "تسجيل الحضور بالموقع الجغرافي مع التحقق من نطاق الفرع (Geofencing)",
        },
        {
            "icon":  "broadcast",
            "color": "#f59e0b",
            "bg":    "#fff3e0",
            "title": "تتبع ميداني Live",
            "desc":  "تابع موظفيك الميدانيين على الخريطة في الوقت الفعلي مع سجل المسار",
        },
        {
            "icon":  "calendar2-check",
            "color": "#e91e63",
            "bg":    "#fce4ec",
            "title": "إدارة الإجازات",
            "desc":  "نظام إجازات متكامل: طلبات، موافقات، أرصدة، وتقارير تفصيلية",
        },
        {
            "icon":  "bar-chart-fill",
            "color": "#7c3aed",
            "bg":    "#ede7f6",
            "title": "تقارير وتحليلات",
            "desc":  "تقارير حضور، تأخيرات، إجازات، وميدانيين مع تصدير Excel فوري",
        },
        {
            "icon":  "phone-fill",
            "color": "#0891B2",
            "bg":    "#e0f2fe",
            "title": "تطبيق موبايل",
            "desc":  "يعمل على كل الأجهزة بدون تحميل - Progressive Web App جاهز للتثبيت",
        },
    ]


def _get_stats():
    return [
        {"value": "\u221e",  "label": "بدون حد للموظفين"},
        {"value": "٦",       "label": "وحدات متكاملة"},
        {"value": "GPS",     "label": "تتبع ميداني"},
        {"value": "٢٤/٧",   "label": "دعم فني"},
    ]


# ═════════════════════════════════════════════════════════════
# Patch 49M — Auto Trial Activation
# ═════════════════════════════════════════════════════════════

def free_trial_register(request):
    """صفحة تسجيل تجربة مجانية مع إنشاء تلقائي للحساب"""
    from core.models import TrialSignupLead
    from companies.models import Company
    from accounts.models import User
    from subscriptions.models import SubscriptionPlan, CompanySubscription
    from django.utils.crypto import get_random_string
    from datetime import date, timedelta
    from django.contrib import messages

    TRIAL_DAYS = 14

    if request.method == 'POST':
        company_name = (request.POST.get('company_name') or '').strip()
        contact_name = (request.POST.get('contact_name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        whatsapp = (request.POST.get('whatsapp') or '').strip()
        email = (request.POST.get('email') or '').strip()
        employees_count = (request.POST.get('employees_count') or '10').strip()
        city = (request.POST.get('city') or '').strip()
        industry = (request.POST.get('industry') or '').strip()
        notes = (request.POST.get('notes') or '').strip()

        # Validation
        errors = []
        if not company_name:
            errors.append('يرجى إدخال اسم الشركة')
        if not contact_name:
            errors.append('يرجى إدخال اسم المسؤول')
        if not phone:
            errors.append('يرجى إدخال رقم الموبايل')
        if not whatsapp:
            errors.append('يرجى إدخال رقم الواتساب')
        if not email:
            errors.append('يرجى إدخال البريد الإلكتروني')

        # Check duplicate email
        if email and User.objects.filter(email=email).exists():
            errors.append('هذا البريد الإلكتروني مسجل بالفعل')

        try:
            employees_count = int(employees_count)
            if employees_count < 1:
                employees_count = 1
        except Exception:
            employees_count = 10

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'landing/free_trial_register.html', {
                'page_title': 'ابدأ تجربتك المجانية',
                'trial_days': TRIAL_DAYS,
            })

        try:
            # ── 1) إنشاء الشركة ──
            company = Company.objects.create(
                name_ar=company_name,
                name_en=company_name,
            )

            # ── 2) إنشاء المستخدم ──
            # username من اسم الشركة
            base_username = email.split('@')[0].lower()
            base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
            if not base_username:
                base_username = 'admin'

            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            password = f"Trial@{get_random_string(6)}"

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=contact_name.split()[0] if contact_name else '',
                last_name=' '.join(contact_name.split()[1:]) if len(contact_name.split()) > 1 else '',
            )

            # Set role and company
            if hasattr(user, 'role'):
                user.role = 'company_admin'
            if hasattr(user, 'company'):
                user.company = company
            if hasattr(user, 'must_change_password'):
                user.must_change_password = True

            user.save()

            # ── 3) إنشاء اشتراك Trial ──
            today = date.today()
            trial_end = today + timedelta(days=TRIAL_DAYS)

            # ابحث عن أي plan موجود أو أنشئ واحد
            plan = SubscriptionPlan.objects.first()
            if not plan:
                plan = SubscriptionPlan.objects.create(
                    name_ar='تجربة مجانية',
                    name_en='Trial',
                    tier='trial',
                    price_monthly=0,
                    price_yearly=0,
                    max_employees=50,
                    is_active=True,
                )

            try:
                CompanySubscription.objects.create(
                    company=company,
                    plan=plan,
                    start_date=today,
                    end_date=trial_end,
                    status='trial',
                    billing_cycle='trial',
                    is_trial=True,
                    trial_end_date=trial_end,
                )
            except Exception as e:
                print(f'Subscription error: {e}')
                pass

            # ── 4) حفظ بيانات الطلب ──
            lead = TrialSignupLead.objects.create(
                company_name=company_name,
                contact_name=contact_name,
                phone=phone,
                whatsapp=whatsapp,
                email=email,
                employees_count=employees_count,
                city=city,
                industry=industry,
                notes=notes,
                source='free_trial_auto',
                status='activated',
                trial_start_date=today,
                trial_end_date=trial_end,
                created_company=company,
                created_user=user,
                generated_username=username,
                generated_password=password,
            )

            # ── Store in session for success page ──
            request.session['trial_data'] = {
                'company_name': company_name,
                'contact_name': contact_name,
                'username': username,
                'password': password,
                'email': email,
                'trial_start': str(today),
                'trial_end': str(trial_end),
                'trial_days': TRIAL_DAYS,
            }

            return redirect('landing:free_trial_success')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')
            return render(request, 'landing/free_trial_register.html', {
                'page_title': 'ابدأ تجربتك المجانية',
                'trial_days': TRIAL_DAYS,
            })

    context = {
        'page_title': 'ابدأ تجربتك المجانية',
        'trial_days': TRIAL_DAYS,
        'sales_phone': '(+20)01501551593',
        'sales_whatsapp': '2001501551593',
    }
    return render(request, 'landing/free_trial_register.html', context)


def free_trial_success(request):
    """صفحة نجاح التسجيل — تعرض بيانات الدخول"""
    trial_data = request.session.pop('trial_data', None)

    if not trial_data:
        return redirect('landing:free_trial')

    context = {
        'page_title': 'تم إنشاء حسابك بنجاح',
        'trial_data': trial_data,
        'sales_phone': '(+20)01501551593',
        'sales_whatsapp': '2001501551593',
    }
    return render(request, 'landing/free_trial_success.html', context)


# ═════════════════════════════════════════════════════════════
# Patch 50b — JS Solutions Corporate Landing
# ═════════════════════════════════════════════════════════════

def js_solutions_home(request):
    """الصفحة الرئيسية لـ JS Solutions — Corporate Landing"""
    context = {
        'page_title': 'JS Solutions — نطوّر حلول ذكية للشركات',
    }
    return render(request, 'landing/js_solutions.html', context)

def coming_soon(request):
    """صفحة قريباً - لتحميل التطبيق أو أي ميزة قادمة"""
    context = {
        'page_title': 'قريباً',
    }
    return render(request, 'landing/coming_soon.html', context)

def smart_home(request):
    """يفتح صفحة مختلفة حسب الدومين"""
    host = request.get_host().lower()
    if host.startswith('motion.'):
        return landing_home(request)
    return js_solutions_home(request)
