#!/usr/bin/env python3
"""
Patch 21: Landing Page
=======================
- صفحة تسويقية احترافية
- Hero Section
- Features Section
- Pricing Section
- Testimonials
- CTA Section
- Contact Form
- صفحة About
"""

import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def append_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

print("=" * 60)
print("  Patch 21: Landing Page")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إنشاء landing app
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء landing app...")

landing_dir = os.path.join(BASE_DIR, 'landing')
os.makedirs(landing_dir, exist_ok=True)

create_file(os.path.join(landing_dir, '__init__.py'), '')
create_file(os.path.join(landing_dir, 'apps.py'), '''from django.apps import AppConfig

class LandingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "landing"
    verbose_name = "الصفحة التسويقية"
''')
create_file(os.path.join(landing_dir, 'tests.py'), '')


# ════════════════════════════════════════════════════════════
# 2. landing/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء landing/views.py...")

create_file(os.path.join(landing_dir, 'views.py'), '''"""
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
    context = {
        "page_title": "عن MotionHR",
    }
    return render(request, "landing/about.html", context)


def _get_plans():
    return [
        {
            "name":        "Starter",
            "name_ar":     "المبتدئ",
            "price":       299,
            "price_year":  2999,
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
            "price":       599,
            "price_year":  5999,
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
            "price":       999,
            "price_year":  9999,
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
        {"value": "10-100",  "label": "موظف"},
        {"value": "٦",       "label": "وحدات متكاملة"},
        {"value": "GPS",     "label": "تتبع ميداني"},
        {"value": "٢٤/٧",   "label": "دعم فني"},
    ]
''')


# ════════════════════════════════════════════════════════════
# 3. landing/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء landing/urls.py...")

create_file(os.path.join(landing_dir, 'urls.py'), '''from django.urls import path
from . import views

app_name = "landing"

urlpatterns = [
    path("",         views.landing_home,    name="home"),
    path("pricing/", views.landing_pricing, name="pricing"),
    path("contact/", views.landing_contact, name="contact"),
    path("about/",   views.landing_about,   name="about"),
]
''')


# ════════════════════════════════════════════════════════════
# 4. إضافة landing في settings + urls
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings.py و urls.py...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')
settings_content = read_file(settings_path)

if "'landing'" not in settings_content:
    settings_content = settings_content.replace(
        "'reports',",
        "'reports',\n    'landing',"
    )
    write_file(settings_path, settings_content)

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

if "landing.urls" not in main_urls_content:
    main_urls_content = main_urls_content.replace(
        "    path('', home_redirect, name='home'),",
        "    path('', include('landing.urls', namespace='landing')),\n    path('app/', home_redirect, name='home'),",
    )
    write_file(main_urls_path, main_urls_content)


# ════════════════════════════════════════════════════════════
# 5. landing/home.html - الصفحة الرئيسية
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء landing/home.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'landing', 'home.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ page_title }}</title>
  <meta name="description" content="MotionHR - نظام إدارة الموارد البشرية الأذكى للشركات الصغيرة والمتوسطة في مصر والعالم العربي">

  <!-- Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">

  <!-- Bootstrap RTL -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">

  <style>
    * { font-family: 'Cairo', sans-serif; }

    :root {
      --primary: #06B6D4;
      --primary-dark: #0891B2;
      --dark: #0f172a;
    }

    /* ── Navbar ── */
    .navbar-landing {
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(10px);
      padding: 16px 0;
      position: sticky;
      top: 0;
      z-index: 1000;
    }

    .navbar-brand-text {
      font-size: 1.5rem;
      font-weight: 900;
      color: var(--primary) !important;
      letter-spacing: -1px;
    }

    .nav-link-landing {
      color: rgba(255,255,255,0.8) !important;
      font-weight: 600;
      transition: color 0.2s;
      padding: 8px 16px !important;
    }

    .nav-link-landing:hover { color: var(--primary) !important; }

    /* ── Hero ── */
    .hero {
      background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #0e7490 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      position: relative;
      overflow: hidden;
    }

    .hero::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle at 70% 50%, rgba(6,182,212,0.1) 0%, transparent 60%);
      animation: pulse-bg 4s ease-in-out infinite;
    }

    @keyframes pulse-bg {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }

    .hero-title {
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 900;
      color: white;
      line-height: 1.2;
    }

    .hero-subtitle {
      font-size: clamp(1rem, 2vw, 1.3rem);
      color: rgba(255,255,255,0.75);
      line-height: 1.7;
    }

    .hero-badge {
      display: inline-block;
      padding: 6px 16px;
      background: rgba(6,182,212,0.2);
      border: 1px solid rgba(6,182,212,0.4);
      border-radius: 50px;
      color: var(--primary);
      font-size: 0.85rem;
      font-weight: 700;
      margin-bottom: 20px;
    }

    .btn-hero-primary {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: white;
      padding: 14px 36px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 1.1rem;
      border: none;
      box-shadow: 0 8px 25px rgba(6,182,212,0.4);
      transition: all 0.3s;
      text-decoration: none;
    }

    .btn-hero-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 30px rgba(6,182,212,0.5);
      color: white;
    }

    .btn-hero-secondary {
      background: rgba(255,255,255,0.1);
      color: white;
      padding: 14px 36px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 1.1rem;
      border: 1px solid rgba(255,255,255,0.3);
      transition: all 0.3s;
      text-decoration: none;
    }

    .btn-hero-secondary:hover {
      background: rgba(255,255,255,0.2);
      color: white;
    }

    /* ── Stats ── */
    .stat-card {
      text-align: center;
      padding: 20px;
      border-radius: 16px;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.15);
      backdrop-filter: blur(10px);
    }

    .stat-value {
      font-size: 2rem;
      font-weight: 900;
      color: var(--primary);
    }

    .stat-label {
      color: rgba(255,255,255,0.7);
      font-size: 0.9rem;
    }

    /* ── Features ── */
    .section-title {
      font-size: clamp(1.5rem, 3vw, 2.2rem);
      font-weight: 900;
      color: #1f2937;
    }

    .feature-card {
      border-radius: 16px;
      padding: 28px;
      border: 1px solid #e5e7eb;
      transition: all 0.3s;
      height: 100%;
    }

    .feature-card:hover {
      border-color: var(--primary);
      box-shadow: 0 8px 30px rgba(6,182,212,0.15);
      transform: translateY(-4px);
    }

    .feature-icon {
      width: 56px;
      height: 56px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      margin-bottom: 16px;
    }

    /* ── Pricing ── */
    .pricing-card {
      border-radius: 20px;
      padding: 32px;
      border: 2px solid #e5e7eb;
      transition: all 0.3s;
      height: 100%;
      position: relative;
    }

    .pricing-card.popular {
      border-color: var(--primary);
      box-shadow: 0 12px 40px rgba(6,182,212,0.2);
    }

    .popular-badge {
      position: absolute;
      top: -14px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--primary);
      color: white;
      padding: 4px 20px;
      border-radius: 50px;
      font-size: 0.8rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .price-number {
      font-size: 2.5rem;
      font-weight: 900;
    }

    .feature-check {
      color: #10b981;
    }

    .feature-x {
      color: #d1d5db;
    }

    /* ── CTA ── */
    .cta-section {
      background: linear-gradient(135deg, var(--dark), #1e3a5f);
      padding: 80px 0;
    }

    /* ── Footer ── */
    .footer {
      background: #0f172a;
      color: rgba(255,255,255,0.6);
      padding: 40px 0 20px;
    }

    .footer a {
      color: rgba(255,255,255,0.6);
      text-decoration: none;
      transition: color 0.2s;
    }

    .footer a:hover { color: var(--primary); }

    /* ── Animations ── */
    .fade-in {
      opacity: 0;
      transform: translateY(30px);
      transition: all 0.6s ease;
    }

    .fade-in.visible {
      opacity: 1;
      transform: translateY(0);
    }

    /* ── Mockup ── */
    .mockup-container {
      position: relative;
      z-index: 1;
    }

    .mockup-screen {
      background: #1e293b;
      border-radius: 16px;
      padding: 20px;
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }

    .mockup-bar {
      height: 32px;
      background: #0f172a;
      border-radius: 8px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      padding: 0 12px;
      gap: 6px;
    }

    .mockup-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .mockup-stat {
      background: #0f172a;
      border-radius: 10px;
      padding: 14px;
      margin-bottom: 8px;
    }
  </style>
</head>

<body>

<!-- ════════════════════════════════════════
     NAVBAR
════════════════════════════════════════ -->
<nav class="navbar-landing">
  <div class="container">
    <div class="d-flex align-items-center justify-content-between">

      <!-- Logo -->
      <a href="{% url 'landing:home' %}" class="navbar-brand-text text-decoration-none">
        MotionHR
        <span style="font-size:0.6rem; color:rgba(255,255,255,0.4);
                     font-weight:400; vertical-align:super;">
          v1.0
        </span>
      </a>

      <!-- Nav Links (Desktop) -->
      <div class="d-none d-md-flex align-items-center gap-1">
        <a href="{% url 'landing:home' %}#features" class="nav-link-landing">المميزات</a>
        <a href="{% url 'landing:pricing' %}"        class="nav-link-landing">الأسعار</a>
        <a href="{% url 'landing:about' %}"          class="nav-link-landing">عن النظام</a>
        <a href="{% url 'landing:contact' %}"        class="nav-link-landing">تواصل معنا</a>
      </div>

      <!-- CTA Buttons -->
      <div class="d-flex align-items-center gap-2">
        <a href="{% url 'login' %}"
           class="btn btn-sm btn-outline-light rounded-pill px-3">
          تسجيل الدخول
        </a>
        <a href="{% url 'landing:contact' %}"
           class="btn btn-sm rounded-pill px-3 text-white"
           style="background:var(--primary); font-weight:700;">
          اطلب عرضاً
        </a>
      </div>

    </div>
  </div>
</nav>


<!-- ════════════════════════════════════════
     HERO SECTION
════════════════════════════════════════ -->
<section class="hero">
  <div class="container position-relative" style="z-index:1;">
    <div class="row align-items-center g-5">

      <!-- Text -->
      <div class="col-lg-6">
        <div class="hero-badge">
          <i class="bi bi-stars me-1"></i>
          نظام HR الأذكى للشركات العربية
        </div>
        <h1 class="hero-title mb-4">
          أدِر فريقك
          <span style="color:var(--primary);">بذكاء</span>
          <br>وتابعهم في
          <span style="color:var(--primary);">الوقت الفعلي</span>
        </h1>
        <p class="hero-subtitle mb-5">
          MotionHR نظام إدارة موارد بشرية عصري مصمم للشركات الصغيرة والمتوسطة
          في مصر والعالم العربي. تتبع حضور موظفيك بالـ GPS، وتابع الميدانيين
          على الخريطة، وأدِر الإجازات والتقارير بسهولة تامة.
        </p>
        <div class="d-flex gap-3 flex-wrap">
          <a href="{% url 'landing:contact' %}" class="btn-hero-primary">
            <i class="bi bi-rocket me-2"></i>
            ابدأ مجاناً الآن
          </a>
          <a href="#features" class="btn-hero-secondary">
            <i class="bi bi-play-circle me-2"></i>
            اعرف أكثر
          </a>
        </div>

        <!-- Trust Badges -->
        <div class="d-flex align-items-center gap-3 mt-4 flex-wrap">
          <div class="d-flex align-items-center gap-1 text-white-50 small">
            <i class="bi bi-shield-check text-success"></i>
            بيانات آمنة ومشفرة
          </div>
          <div class="d-flex align-items-center gap-1 text-white-50 small">
            <i class="bi bi-phone text-primary"></i>
            يعمل على الموبايل
          </div>
          <div class="d-flex align-items-center gap-1 text-white-50 small">
            <i class="bi bi-lightning text-warning"></i>
            إعداد خلال ساعة
          </div>
        </div>
      </div>

      <!-- Mockup -->
      <div class="col-lg-6">
        <div class="mockup-container">
          <div class="mockup-screen">

            <!-- Top Bar -->
            <div class="mockup-bar">
              <div class="mockup-dot" style="background:#ef4444;"></div>
              <div class="mockup-dot" style="background:#f59e0b;"></div>
              <div class="mockup-dot" style="background:#10b981;"></div>
              <div style="flex:1; height:16px; background:#1e293b; border-radius:4px; margin-right:8px;"></div>
            </div>

            <!-- Dashboard Preview -->
            <div class="row g-2 mb-2">
              <div class="col-6">
                <div class="mockup-stat">
                  <div style="color:#06B6D4; font-size:1.5rem; font-weight:900;">47</div>
                  <div style="color:rgba(255,255,255,0.5); font-size:0.7rem;">موظف نشط</div>
                </div>
              </div>
              <div class="col-6">
                <div class="mockup-stat">
                  <div style="color:#10b981; font-size:1.5rem; font-weight:900;">89%</div>
                  <div style="color:rgba(255,255,255,0.5); font-size:0.7rem;">نسبة الحضور</div>
                </div>
              </div>
              <div class="col-6">
                <div class="mockup-stat">
                  <div style="color:#f59e0b; font-size:1.5rem; font-weight:900;">3</div>
                  <div style="color:rgba(255,255,255,0.5); font-size:0.7rem;">إجازات معلقة</div>
                </div>
              </div>
              <div class="col-6">
                <div class="mockup-stat">
                  <div style="color:#7c3aed; font-size:1.5rem; font-weight:900;">12</div>
                  <div style="color:rgba(255,255,255,0.5); font-size:0.7rem;">ميدانيون نشطون</div>
                </div>
              </div>
            </div>

            <!-- Map Preview -->
            <div class="rounded-3 p-2 d-flex align-items-center justify-content-center"
                 style="background:#0f172a; height:100px; position:relative; overflow:hidden;">
              <div style="position:absolute; inset:0; background:
                radial-gradient(circle at 30% 50%, rgba(6,182,212,0.3) 0%, transparent 40%),
                radial-gradient(circle at 70% 30%, rgba(16,185,129,0.2) 0%, transparent 40%);">
              </div>
              <div style="position:relative; z-index:1; text-center;">
                <i class="bi bi-geo-alt-fill"
                   style="font-size:2rem; color:#06B6D4;
                          text-shadow: 0 0 20px rgba(6,182,212,0.8);"></i>
                <div style="color:rgba(255,255,255,0.7); font-size:0.7rem; margin-top:4px;">
                  خريطة الموظفين الميدانيين
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

    </div>

    <!-- Stats Row -->
    <div class="row g-3 mt-5">
      {% for stat in stats %}
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
      {% endfor %}
    </div>

  </div>
</section>


<!-- ════════════════════════════════════════
     FEATURES SECTION
════════════════════════════════════════ -->
<section id="features" class="py-6" style="padding: 80px 0; background:#f8fafc;">
  <div class="container">

    <div class="text-center mb-5 fade-in">
      <span class="badge px-3 py-2 mb-3 fs-6"
            style="background:#e0f7fa; color:#06B6D4;">
        المميزات
      </span>
      <h2 class="section-title mb-3">كل ما تحتاجه في مكان واحد</h2>
      <p class="text-muted fs-5 mx-auto" style="max-width:600px;">
        MotionHR مش بس نظام HR - هو نظام ذكي لإدارة فريقك بالكامل
        من أي مكان وفي أي وقت
      </p>
    </div>

    <div class="row g-4">
      {% for feature in features %}
      <div class="col-md-6 col-lg-4 fade-in">
        <div class="feature-card bg-white">
          <div class="feature-icon" style="background:{{ feature.bg }};">
            <i class="bi bi-{{ feature.icon }}" style="color:{{ feature.color }};"></i>
          </div>
          <h5 class="fw-bold mb-2">{{ feature.title }}</h5>
          <p class="text-muted small mb-0">{{ feature.desc }}</p>
        </div>
      </div>
      {% endfor %}
    </div>

  </div>
</section>


<!-- ════════════════════════════════════════
     GPS HIGHLIGHT SECTION
════════════════════════════════════════ -->
<section style="padding: 80px 0; background:white;">
  <div class="container">
    <div class="row align-items-center g-5">

      <div class="col-lg-6 fade-in">
        <span class="badge px-3 py-2 mb-3 fs-6"
              style="background:#e8f5e9; color:#4caf50;">
          الميزة الأهم
        </span>
        <h2 class="section-title mb-4">
          تتبع موظفيك الميدانيين
          <span style="color:#06B6D4;">في الوقت الفعلي</span>
        </h2>
        <p class="text-muted fs-5 mb-4">
          شوف فين كل موظف ميداني على الخريطة لحظة بلحظة.
          سجّل زياراتهم، تابع مساراتهم، واعرف إيه اللي بيحصل
          حتى لو إنت مش في المكتب.
        </p>
        <div class="d-flex flex-column gap-3">
          {% for point in "خريطة حية بتتحدث كل 30 ثانية|تسجيل تلقائي لكل الزيارات|مسار كامل ليوم العمل|تنبيهات فورية عند التحرك أو التوقف"|split:"|" %}
          <div class="d-flex align-items-center gap-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                 style="width:36px;height:36px;background:#e0f7fa;">
              <i class="bi bi-check-lg" style="color:#06B6D4;"></i>
            </div>
            <span>{{ point }}</span>
          </div>
          {% endfor %}
        </div>
      </div>

      <div class="col-lg-6 fade-in">
        <div class="rounded-3 p-4 text-center"
             style="background: linear-gradient(135deg, #0f172a, #1e3a5f);
                    min-height:350px; display:flex; align-items:center;
                    justify-content:center; position:relative; overflow:hidden;">

          <!-- خريطة وهمية -->
          <div style="position:absolute; inset:0; opacity:0.3;
                      background: repeating-linear-gradient(
                        0deg,
                        transparent,
                        transparent 40px,
                        rgba(255,255,255,0.05) 40px,
                        rgba(255,255,255,0.05) 41px
                      ),
                      repeating-linear-gradient(
                        90deg,
                        transparent,
                        transparent 40px,
                        rgba(255,255,255,0.05) 40px,
                        rgba(255,255,255,0.05) 41px
                      );">
          </div>

          <div style="position:relative; z-index:1;">
            <!-- نقاط الموظفين -->
            <div style="position:relative; width:280px; height:250px; margin:0 auto;">

              {% for emp in "أ|م|س|ك"|split:"|" %}
              <div style="position:absolute;
                          {% if forloop.counter == 1 %}top:20%; left:30%;
                          {% elif forloop.counter == 2 %}top:60%; left:60%;
                          {% elif forloop.counter == 3 %}top:40%; left:75%;
                          {% else %}top:70%; left:20%;{% endif %}">
                <div style="width:44px; height:44px; border-radius:50%;
                             background:#06B6D4; border:3px solid white;
                             display:flex; align-items:center; justify-content:center;
                             color:white; font-weight:900; font-size:1rem;
                             box-shadow: 0 0 0 8px rgba(6,182,212,0.2);">
                  {{ emp }}
                </div>
                <div style="position:absolute; top:-28px; left:50%; transform:translateX(-50%);
                             background:rgba(0,0,0,0.8); color:white;
                             padding:2px 8px; border-radius:4px; font-size:0.65rem;
                             white-space:nowrap;">
                  متحرك الآن
                </div>
              </div>
              {% endfor %}

              <!-- خطوط المسار -->
              <svg style="position:absolute; inset:0; width:100%; height:100%;"
                   viewBox="0 0 280 250">
                <polyline points="84,50 168,150 210,100 56,175"
                          fill="none" stroke="#06B6D4" stroke-width="2"
                          stroke-dasharray="5,5" opacity="0.5"/>
              </svg>

            </div>

            <div class="mt-3 d-flex justify-content-center gap-2">
              <span class="badge" style="background:#10b981;">4 متصل</span>
              <span class="badge" style="background:#06B6D4;">متحرك</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</section>


<!-- ════════════════════════════════════════
     PRICING SECTION
════════════════════════════════════════ -->
<section id="pricing" style="padding:80px 0; background:#f8fafc;">
  <div class="container">

    <div class="text-center mb-5 fade-in">
      <span class="badge px-3 py-2 mb-3 fs-6"
            style="background:#e0f7fa; color:#06B6D4;">
        الأسعار
      </span>
      <h2 class="section-title mb-3">اختر الخطة المناسبة لشركتك</h2>
      <p class="text-muted">بدون عقود ملزمة - يمكنك الترقية أو الإلغاء في أي وقت</p>
    </div>

    <div class="row g-4 justify-content-center">
      {% for plan in plans %}
      <div class="col-md-6 col-lg-3 fade-in">
        <div class="pricing-card bg-white {% if plan.popular %}popular{% endif %}">

          {% if plan.popular %}
          <div class="popular-badge">⭐ الأكثر شيوعاً</div>
          {% endif %}

          <div class="d-flex align-items-center gap-2 mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:40px;height:40px;background:{{ plan.color }}20;">
              <i class="bi bi-building" style="color:{{ plan.color }};"></i>
            </div>
            <div>
              <div class="fw-bold">{{ plan.name_ar }}</div>
              <small class="text-muted">{{ plan.employees }} موظف</small>
            </div>
          </div>

          <div class="mb-4">
            {% if plan.price > 0 %}
              <span class="price-number" style="color:{{ plan.color }};">
                {{ plan.price }}
              </span>
              <span class="text-muted"> ج.م/شهر</span>
              <div class="text-muted small mt-1">
                أو {{ plan.price_year }} ج.م/سنة
                <span class="badge bg-success ms-1">وفر 17%</span>
              </div>
            {% else %}
              <div class="price-number text-dark" style="font-size:1.8rem;">
                حسب الطلب
              </div>
              <div class="text-muted small">تواصل معنا للسعر</div>
            {% endif %}
          </div>

          <ul class="list-unstyled mb-4">
            {% for f in plan.features %}
            <li class="d-flex align-items-center gap-2 mb-2 small">
              <i class="bi bi-check-circle-fill feature-check flex-shrink-0"></i>
              {{ f }}
            </li>
            {% endfor %}
            {% for f in plan.missing %}
            <li class="d-flex align-items-center gap-2 mb-2 small text-muted">
              <i class="bi bi-x-circle feature-x flex-shrink-0"></i>
              {{ f }}
            </li>
            {% endfor %}
          </ul>

          <a href="{% url 'landing:contact' %}"
             class="btn w-100 fw-bold rounded-3"
             style="{% if plan.popular %}
                      background:{{ plan.color }}; color:white;
                    {% else %}
                      background:transparent; color:{{ plan.color }};
                      border: 2px solid {{ plan.color }};
                    {% endif %}">
            {% if plan.price == 0 %}تواصل معنا{% else %}ابدأ الآن{% endif %}
          </a>

        </div>
      </div>
      {% endfor %}
    </div>

    <!-- Addons -->
    <div class="row justify-content-center mt-4">
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
          <div class="card-body p-4">
            <h5 class="fw-bold mb-3 text-center">إضافات متاحة</h5>
            <div class="row g-2 text-center">
              <div class="col-6 col-md-3">
                <div class="p-2 rounded" style="background:#f8fafc;">
                  <div class="fw-bold" style="color:#06B6D4;">+200 ج.م</div>
                  <small class="text-muted">تتبع ميداني</small>
                </div>
              </div>
              <div class="col-6 col-md-3">
                <div class="p-2 rounded" style="background:#f8fafc;">
                  <div class="fw-bold" style="color:#06B6D4;">+300 ج.م</div>
                  <small class="text-muted">Payroll متقدم</small>
                </div>
              </div>
              <div class="col-6 col-md-3">
                <div class="p-2 rounded" style="background:#f8fafc;">
                  <div class="fw-bold" style="color:#06B6D4;">5,000 ج.م</div>
                  <small class="text-muted">سيرفر العميل</small>
                </div>
              </div>
              <div class="col-6 col-md-3">
                <div class="p-2 rounded" style="background:#f8fafc;">
                  <div class="fw-bold" style="color:#06B6D4;">2,000 ج.م</div>
                  <small class="text-muted">إعداد وتدريب</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</section>


<!-- ════════════════════════════════════════
     CTA SECTION
════════════════════════════════════════ -->
<section class="cta-section">
  <div class="container text-center">
    <div class="fade-in">
      <h2 class="fw-black text-white mb-3" style="font-size:2.5rem;">
        جاهز تبدأ مع MotionHR؟
      </h2>
      <p class="text-white-50 fs-5 mb-5">
        تواصل معنا اليوم واحصل على نسخة تجريبية مجانية لمدة 14 يوم
      </p>
      <div class="d-flex gap-3 justify-content-center flex-wrap">
        <a href="{% url 'landing:contact' %}"
           class="btn btn-lg fw-bold rounded-pill px-5"
           style="background:#06B6D4; color:white;
                  box-shadow:0 8px 25px rgba(6,182,212,0.4);">
          <i class="bi bi-rocket me-2"></i>
          ابدأ التجربة المجانية
        </a>
        <a href="{% url 'login' %}"
           class="btn btn-lg fw-bold rounded-pill px-5"
           style="background:rgba(255,255,255,0.1); color:white;
                  border:1px solid rgba(255,255,255,0.3);">
          <i class="bi bi-box-arrow-in-right me-2"></i>
          تسجيل الدخول
        </a>
      </div>
    </div>
  </div>
</section>


<!-- ════════════════════════════════════════
     FOOTER
════════════════════════════════════════ -->
<footer class="footer">
  <div class="container">
    <div class="row g-4 mb-4">

      <div class="col-md-4">
        <h5 class="fw-black text-white mb-3" style="color:#06B6D4 !important;">
          MotionHR
        </h5>
        <p class="small mb-3">
          نظام إدارة الموارد البشرية الأذكى للشركات الصغيرة والمتوسطة
          في مصر والعالم العربي.
        </p>
        <div class="d-flex gap-2">
          <a href="#" class="btn btn-sm"
             style="background:rgba(255,255,255,0.1); color:white; border-radius:8px;">
            <i class="bi bi-facebook"></i>
          </a>
          <a href="#" class="btn btn-sm"
             style="background:rgba(255,255,255,0.1); color:white; border-radius:8px;">
            <i class="bi bi-whatsapp"></i>
          </a>
          <a href="#" class="btn btn-sm"
             style="background:rgba(255,255,255,0.1); color:white; border-radius:8px;">
            <i class="bi bi-linkedin"></i>
          </a>
        </div>
      </div>

      <div class="col-md-2">
        <h6 class="text-white fw-bold mb-3">روابط سريعة</h6>
        <ul class="list-unstyled small">
          <li class="mb-2"><a href="{% url 'landing:home' %}">الرئيسية</a></li>
          <li class="mb-2"><a href="{% url 'landing:home' %}#features">المميزات</a></li>
          <li class="mb-2"><a href="{% url 'landing:pricing' %}">الأسعار</a></li>
          <li class="mb-2"><a href="{% url 'landing:about' %}">عن النظام</a></li>
          <li class="mb-2"><a href="{% url 'landing:contact' %}">تواصل معنا</a></li>
        </ul>
      </div>

      <div class="col-md-3">
        <h6 class="text-white fw-bold mb-3">المميزات</h6>
        <ul class="list-unstyled small">
          <li class="mb-2"><a href="#">إدارة الموظفين</a></li>
          <li class="mb-2"><a href="#">الحضور GPS</a></li>
          <li class="mb-2"><a href="#">التتبع الميداني</a></li>
          <li class="mb-2"><a href="#">إدارة الإجازات</a></li>
          <li class="mb-2"><a href="#">التقارير</a></li>
        </ul>
      </div>

      <div class="col-md-3">
        <h6 class="text-white fw-bold mb-3">تواصل معنا</h6>
        <ul class="list-unstyled small">
          <li class="mb-2">
            <i class="bi bi-telephone me-2" style="color:#06B6D4;"></i>
            01000000000
          </li>
          <li class="mb-2">
            <i class="bi bi-envelope me-2" style="color:#06B6D4;"></i>
            sales@motionhr.com
          </li>
          <li class="mb-2">
            <i class="bi bi-clock me-2" style="color:#06B6D4;"></i>
            أحد - خميس، 9ص - 5م
          </li>
        </ul>
      </div>

    </div>

    <hr style="border-color:rgba(255,255,255,0.1);">

    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
      <small>© 2025 MotionHR - جميع الحقوق محفوظة</small>
      <small>
        صُنع بـ ❤️ في مصر
      </small>
    </div>

  </div>
</footer>


<!-- Scripts -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
  // Fade in on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
</script>

</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 6. pricing.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء landing/pricing.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'landing', 'pricing.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ page_title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    * { font-family: 'Cairo', sans-serif; }
    :root { --primary: #06B6D4; }
    .navbar-landing {
      background: rgba(15,23,42,0.97);
      padding: 16px 0;
      position: sticky; top: 0; z-index: 1000;
    }
    .pricing-card {
      border-radius: 20px; padding: 32px;
      border: 2px solid #e5e7eb; transition: all 0.3s; height: 100%;
      position: relative;
    }
    .pricing-card.popular {
      border-color: var(--primary);
      box-shadow: 0 12px 40px rgba(6,182,212,0.2);
    }
    .popular-badge {
      position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
      background: var(--primary); color: white;
      padding: 4px 20px; border-radius: 50px;
      font-size: 0.8rem; font-weight: 700; white-space: nowrap;
    }
  </style>
</head>
<body style="background:#f8fafc;">

<!-- Navbar -->
<nav class="navbar-landing">
  <div class="container">
    <div class="d-flex align-items-center justify-content-between">
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">
        MotionHR
      </a>
      <div class="d-flex gap-2">
        <a href="{% url 'landing:home' %}"
           class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
        <a href="{% url 'landing:contact' %}"
           class="btn btn-sm rounded-pill text-white"
           style="background:#06B6D4;">اطلب عرضاً</a>
      </div>
    </div>
  </div>
</nav>

<div class="container py-5">

  <div class="text-center mb-5">
    <h1 class="fw-black mb-3" style="font-size:2.5rem;">الأسعار والباقات</h1>
    <p class="text-muted fs-5">اختر الباقة المناسبة لحجم شركتك</p>
  </div>

  <div class="row g-4 justify-content-center">
    {% for plan in plans %}
    <div class="col-md-6 col-lg-3">
      <div class="pricing-card bg-white {% if plan.popular %}popular{% endif %}">
        {% if plan.popular %}
        <div class="popular-badge">⭐ الأكثر شيوعاً</div>
        {% endif %}

        <div class="mb-3">
          <h4 class="fw-bold" style="color:{{ plan.color }};">{{ plan.name_ar }}</h4>
          <div class="text-muted small">{{ plan.employees }} موظف</div>
        </div>

        <div class="mb-4 pb-3 border-bottom">
          {% if plan.price > 0 %}
          <div>
            <span style="font-size:2.5rem;font-weight:900;color:{{ plan.color }};">
              {{ plan.price }}
            </span>
            <span class="text-muted"> ج.م/شهر</span>
          </div>
          <div class="small text-muted">
            أو <strong>{{ plan.price_year }} ج.م</strong>/سنة
            <span class="badge bg-success ms-1">وفر 17%</span>
          </div>
          {% else %}
          <div style="font-size:1.5rem;font-weight:900;color:#1f2937;">
            حسب الطلب
          </div>
          {% endif %}
        </div>

        <ul class="list-unstyled mb-4">
          {% for f in plan.features %}
          <li class="d-flex gap-2 mb-2 small">
            <i class="bi bi-check-circle-fill text-success flex-shrink-0 mt-1"></i>
            {{ f }}
          </li>
          {% endfor %}
          {% for f in plan.missing %}
          <li class="d-flex gap-2 mb-2 small text-muted">
            <i class="bi bi-x-circle flex-shrink-0 mt-1" style="color:#d1d5db;"></i>
            {{ f }}
          </li>
          {% endfor %}
        </ul>

        <a href="{% url 'landing:contact' %}"
           class="btn w-100 fw-bold"
           style="{% if plan.popular %}
                    background:{{ plan.color }};color:white;
                  {% else %}
                    border:2px solid {{ plan.color }};color:{{ plan.color }};
                  {% endif %}
                  border-radius:10px;">
          {% if plan.price == 0 %}تواصل معنا{% else %}ابدأ الآن{% endif %}
        </a>
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- FAQ -->
  <div class="row justify-content-center mt-5">
    <div class="col-lg-8">
      <h3 class="fw-bold text-center mb-4">أسئلة شائعة</h3>
      <div class="accordion" id="faqAccordion">

        {% for q, a in "هل يوجد فترة تجريبية مجانية?|نعم، نقدم نسخة تجريبية مجانية لمدة 14 يوم بدون الحاجة لبطاقة ائتمان.|هل يمكنني الترقية لاحقاً?|بالطبع، يمكنك الترقية أو تخفيض الخطة في أي وقت.|هل بياناتي آمنة?|نعم، بياناتك مشفرة ومحمية. يمكنك أيضاً التثبيت على سيرفرك الخاص.|كيف يتم الدفع?|الدفع شهري أو سنوي عبر تحويل بنكي أو محافظ إلكترونية."|split:"|" %}
          {% if forloop.counter|divisibleby:2 %}
          </div>
          </div>
          {% else %}
          <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
            <h2 class="accordion-header">
              <button class="accordion-button collapsed fw-semibold"
                      type="button"
                      data-bs-toggle="collapse"
                      data-bs-target="#faq{{ forloop.counter }}"
                      style="background:white;">
                {{ q }}
              </button>
            </h2>
            <div id="faq{{ forloop.counter }}"
                 class="accordion-collapse collapse"
                 data-bs-parent="#faqAccordion">
              <div class="accordion-body text-muted">
          {% endif %}
          {% if forloop.counter|divisibleby:2 %}{{ a }}{% endif %}
        {% endfor %}

      </div>
    </div>
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 7. contact.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء landing/contact.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'landing', 'contact.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ page_title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    * { font-family: 'Cairo', sans-serif; }
    .navbar-landing {
      background: rgba(15,23,42,0.97);
      padding: 16px 0; position: sticky; top: 0; z-index: 1000;
    }
    .contact-card {
      border-radius: 16px; padding: 28px;
      text-decoration: none; transition: transform 0.2s;
      display: block;
    }
    .contact-card:hover { transform: translateY(-4px); }
  </style>
</head>
<body style="background:#f8fafc;">

<!-- Navbar -->
<nav class="navbar-landing">
  <div class="container">
    <div class="d-flex align-items-center justify-content-between">
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">
        MotionHR
      </a>
      <a href="{% url 'landing:home' %}"
         class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
    </div>
  </div>
</nav>

<div class="container py-5">

  <div class="text-center mb-5">
    <h1 class="fw-black mb-3">تواصل معنا</h1>
    <p class="text-muted fs-5">فريقنا جاهز يساعدك تختار الأنسب لشركتك</p>
  </div>

  {% if messages %}
  {% for msg in messages %}
  <div class="alert alert-success border-0 shadow-sm mb-4 text-center fw-bold">
    {{ msg }}
  </div>
  {% endfor %}
  {% endif %}

  <div class="row g-5 justify-content-center">

    <!-- طرق التواصل -->
    <div class="col-lg-4">
      <h5 class="fw-bold mb-4">تواصل مباشر</h5>

      <a href="https://wa.me/{{ contact_info.whatsapp|default:'201000000000' }}"
         target="_blank"
         class="contact-card mb-3 text-decoration-none"
         style="background: linear-gradient(135deg, #25D366, #128C7E);">
        <div class="d-flex align-items-center gap-3 text-white">
          <i class="bi bi-whatsapp fs-2"></i>
          <div>
            <div class="fw-bold">واتساب</div>
            <small>{{ contact_info.phone|default:'01000000000' }}</small>
          </div>
        </div>
      </a>

      <a href="tel:{{ contact_info.phone|default:'01000000000' }}"
         class="contact-card mb-3 text-decoration-none"
         style="background: linear-gradient(135deg, #06B6D4, #0891B2);">
        <div class="d-flex align-items-center gap-3 text-white">
          <i class="bi bi-telephone-fill fs-2"></i>
          <div>
            <div class="fw-bold">اتصل بنا</div>
            <small>{{ contact_info.phone|default:'01000000000' }}</small>
          </div>
        </div>
      </a>

      <a href="mailto:{{ contact_info.email|default:'sales@motionhr.com' }}"
         class="contact-card text-decoration-none"
         style="background: linear-gradient(135deg, #6366F1, #4F46E5);">
        <div class="d-flex align-items-center gap-3 text-white">
          <i class="bi bi-envelope-fill fs-2"></i>
          <div>
            <div class="fw-bold">البريد الإلكتروني</div>
            <small>{{ contact_info.email|default:'sales@motionhr.com' }}</small>
          </div>
        </div>
      </a>

      <div class="card border-0 shadow-sm mt-3">
        <div class="card-body p-3 text-center text-muted small">
          <i class="bi bi-clock me-1"></i>
          أحد - خميس: 9 صباحاً - 5 مساءً
        </div>
      </div>
    </div>

    <!-- فورم التواصل -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h5 class="fw-bold mb-4">أرسل رسالة</h5>
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسمك <span class="text-danger">*</span></label>
                <input type="text" name="name" class="form-control" required
                       placeholder="محمد أحمد">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold small">موبايلك <span class="text-danger">*</span></label>
                <input type="tel" name="phone" class="form-control" required
                       placeholder="01000000000">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold small">البريد الإلكتروني</label>
                <input type="email" name="email" class="form-control"
                       placeholder="example@company.com" dir="ltr">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسم الشركة</label>
                <input type="text" name="company" class="form-control"
                       placeholder="شركة ABC">
              </div>
              <div class="col-12">
                <label class="form-label fw-semibold small">عدد الموظفين</label>
                <select name="employees" class="form-select">
                  <option value="">اختر</option>
                  <option value="1-15">1 - 15 موظف</option>
                  <option value="16-50">16 - 50 موظف</option>
                  <option value="51-100">51 - 100 موظف</option>
                  <option value="100+">أكثر من 100</option>
                </select>
              </div>
              <div class="col-12">
                <label class="form-label fw-semibold small">رسالتك</label>
                <textarea name="message" class="form-control" rows="4"
                          placeholder="اكتب رسالتك هنا..."></textarea>
              </div>
            </div>
            <button type="submit"
                    class="btn w-100 mt-4 fw-bold text-white"
                    style="background:#06B6D4; border-radius:10px; padding:12px;">
              <i class="bi bi-send me-2"></i>
              إرسال الرسالة
            </button>
          </form>
        </div>
      </div>
    </div>

  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 8. about.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء landing/about.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'landing', 'about.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ page_title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    * { font-family: 'Cairo', sans-serif; }
    .navbar-landing {
      background: rgba(15,23,42,0.97);
      padding: 16px 0; position: sticky; top: 0; z-index: 1000;
    }
    .hero-about {
      background: linear-gradient(135deg, #0f172a, #1e3a5f);
      padding: 80px 0;
      color: white;
      text-align: center;
    }
  </style>
</head>
<body>

<!-- Navbar -->
<nav class="navbar-landing">
  <div class="container">
    <div class="d-flex align-items-center justify-content-between">
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">
        MotionHR
      </a>
      <div class="d-flex gap-2">
        <a href="{% url 'landing:home' %}"
           class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
        <a href="{% url 'landing:contact' %}"
           class="btn btn-sm rounded-pill text-white"
           style="background:#06B6D4;">تواصل معنا</a>
      </div>
    </div>
  </div>
</nav>

<!-- Hero -->
<section class="hero-about">
  <div class="container">
    <h1 class="fw-black mb-3" style="font-size:3rem;">عن MotionHR</h1>
    <p class="fs-5 mb-0" style="color:rgba(255,255,255,0.75); max-width:600px; margin:0 auto;">
      نظام إدارة الموارد البشرية الأذكى المصمم خصيصاً
      للشركات العربية الصغيرة والمتوسطة
    </p>
  </div>
</section>

<div class="container py-5">

  <!-- القصة -->
  <div class="row justify-content-center mb-5">
    <div class="col-lg-8 text-center">
      <h2 class="fw-bold mb-4">لماذا MotionHR؟</h2>
      <p class="text-muted fs-5 lh-lg">
        وُلد MotionHR من حاجة حقيقية - الشركات العربية الصغيرة والمتوسطة
        تعاني من غياب نظام HR محترف يناسب احتياجاتها وميزانيتها.
        معظم الأنظمة الموجودة إما مكلفة جداً أو معقدة أو غير مصممة للسوق العربي.
      </p>
      <p class="text-muted fs-5 lh-lg">
        MotionHR يختلف - نظام سهل، احترافي، بسعر مناسب،
        مع ميزة تنافسية لا مثيل لها في السوق المصري:
        <strong style="color:#06B6D4;">تتبع الموظفين الميدانيين في الوقت الفعلي</strong>.
      </p>
    </div>
  </div>

  <!-- القيم -->
  <div class="row g-4 mb-5">
    {% for icon, color, bg, title, desc in "trophy|#f59e0b|#fff3e0|البساطة|نظام بسيط يتعلمه أي موظف في دقائق بدون تدريب معقد|shield-check|#10b981|#e8f5e9|الأمان|بياناتك محمية ومشفرة - يمكنك التثبيت على سيرفرك الخاص|lightning|#06B6D4|#e0f7fa|السرعة|إعداد كامل في ساعة واحدة وتشغيل فوري بدون تعقيدات|headset|#7c3aed|#ede7f6|الدعم|فريق دعم متخصص يساعدك في أي وقت"|split:"|" %}
    {% if forloop.counter|divisibleby:4 or forloop.counter == 4 %}
    {% elif forloop.counter == 1 or forloop.counter == 5 or forloop.counter == 9 or forloop.counter == 13 %}
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:{{ bg }};">
          <i class="bi bi-{{ icon }}" style="font-size:1.8rem;color:{{ color }};"></i>
        </div>
        <h5 class="fw-bold">{{ title }}</h5>
        <p class="text-muted small">{{ desc }}</p>
      </div>
    </div>
    {% endif %}
    {% endfor %}

    <!-- نضيف الـ 4 كروت يدوياً عشان template tags محدودة -->
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#fff3e0;">
          <i class="bi bi-trophy-fill" style="font-size:1.8rem;color:#f59e0b;"></i>
        </div>
        <h5 class="fw-bold">البساطة</h5>
        <p class="text-muted small">نظام بسيط يتعلمه أي موظف في دقائق بدون تدريب معقد</p>
      </div>
    </div>
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#e8f5e9;">
          <i class="bi bi-shield-check-fill" style="font-size:1.8rem;color:#10b981;"></i>
        </div>
        <h5 class="fw-bold">الأمان</h5>
        <p class="text-muted small">بياناتك محمية ومشفرة - يمكنك التثبيت على سيرفرك الخاص</p>
      </div>
    </div>
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#e0f7fa;">
          <i class="bi bi-lightning-fill" style="font-size:1.8rem;color:#06B6D4;"></i>
        </div>
        <h5 class="fw-bold">السرعة</h5>
        <p class="text-muted small">إعداد كامل في ساعة واحدة وتشغيل فوري بدون تعقيدات</p>
      </div>
    </div>
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#ede7f6;">
          <i class="bi bi-headset-fill" style="font-size:1.8rem;color:#7c3aed;"></i>
        </div>
        <h5 class="fw-bold">الدعم</h5>
        <p class="text-muted small">فريق دعم متخصص يساعدك في أي وقت</p>
      </div>
    </div>

  </div>

  <!-- CTA -->
  <div class="text-center py-5 rounded-3"
       style="background: linear-gradient(135deg, #0f172a, #1e3a5f);">
    <h3 class="fw-bold text-white mb-3">جاهز تجرب MotionHR؟</h3>
    <p class="text-white-50 mb-4">14 يوم مجاناً بدون أي التزام</p>
    <a href="{% url 'landing:contact' %}"
       class="btn btn-lg fw-bold rounded-pill px-5 text-white"
       style="background:#06B6D4;">
      ابدأ الآن
    </a>
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 9. تحديث home_redirect
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث home_redirect في urls.py...")

main_urls_content = read_file(main_urls_path)

# نعدل home_redirect عشان يروح للـ dashboard لو مسجل دخول
if 'app/' in main_urls_content:
    main_urls_content = main_urls_content.replace(
        "    path('app/', home_redirect, name='home'),",
        "    path('app/', home_redirect, name='app_home'),"
    )
    write_file(main_urls_path, main_urls_content)


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 21 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ landing app كامل
  2.  ✅ landing/views.py - 4 صفحات
  3.  ✅ landing/urls.py
  4.  ✅ home.html - الصفحة الرئيسية الكاملة
  5.  ✅ pricing.html - الأسعار مع FAQ
  6.  ✅ contact.html - فورم التواصل
  7.  ✅ about.html - عن النظام
  8.  ✅ settings.py + urls.py محدث

🔗 URLs الجديدة:
  /              ← الصفحة الرئيسية التسويقية
  /pricing/      ← الأسعار
  /contact/      ← تواصل معنا
  /about/        ← عن النظام
  /app/          ← redirect للـ dashboard

⚠️  ملاحظة:
  الصفحة الرئيسية / بقت Landing Page
  مسجل الدخول يروح للـ /dashboard/ مباشرة

🚀 تبقى:
  Patch 22: صفحات إضافية (Profile, Settings, 404)
  Patch 23: Simulation كامل + إصلاح أي أخطاء
""")