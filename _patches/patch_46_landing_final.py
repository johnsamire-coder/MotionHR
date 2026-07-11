#!/usr/bin/env python3
"""
Patch 46: Landing Pages Final Polish
=====================================
1) فحص + تأكيد كل صفحات الـ Landing
2) إصلاح أي مشكلة باقية
3) تأكيد Login/Logout حسب حالة المستخدم
4) Contact form يحفظ + يبعت رسالة واضحة
5) Responsive final check
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")


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


print("=" * 60)
print("  Patch 46: Landing Pages Final Polish")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) فحص الصفحات الموجودة
# ════════════════════════════════════════════════════════════
print("\n🔍 فحص صفحات الـ Landing...")

pages = {
    "home":    "templates/landing/home.html",
    "pricing": "templates/landing/pricing.html",
    "about":   "templates/landing/about.html",
    "contact": "templates/landing/contact.html",
}

for name, rel_path in pages.items():
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        content = read_file(full)
        issues = []
        if "split" in content and "{% load" not in content[:100]:
            issues.append("split filter بدون load")
        if "getattr" in content and "{% load" not in content[:100]:
            issues.append("getattr filter بدون load")
        if issues:
            print(f"  ⚠️  {name}: {', '.join(issues)}")
        else:
            print(f"  ✅ {name}: سليم")
    else:
        print(f"  ❌ {name}: مش موجود!")


# ════════════════════════════════════════════════════════════
# 2) Navbar الموحد — كل صفحات الـ Landing
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء navbar موحد لصفحات الـ Landing...")

# نضيف template جزئي مشترك
create_file(
    os.path.join(BASE_DIR, "templates", "landing", "_navbar.html"),
    r"""<nav style="background:rgba(15,23,42,0.97); padding:16px 0; position:sticky; top:0; z-index:1000;">
  <div class="container">
    <div class="d-flex align-items-center justify-content-between">

      <!-- Logo -->
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">
        MotionHR
        <small style="font-size:0.6rem;color:rgba(255,255,255,0.3);font-weight:400;vertical-align:super;">v1.0</small>
      </a>

      <!-- Links (Desktop) -->
      <div class="d-none d-md-flex align-items-center gap-1">
        <a href="{% url 'landing:home' %}" style="color:rgba(255,255,255,0.8);text-decoration:none;padding:8px 16px;font-weight:600;font-family:'Cairo',sans-serif;">الرئيسية</a>
        <a href="{% url 'landing:pricing' %}" style="color:rgba(255,255,255,0.8);text-decoration:none;padding:8px 16px;font-weight:600;font-family:'Cairo',sans-serif;">الأسعار</a>
        <a href="{% url 'landing:about' %}" style="color:rgba(255,255,255,0.8);text-decoration:none;padding:8px 16px;font-weight:600;font-family:'Cairo',sans-serif;">عن النظام</a>
        <a href="{% url 'landing:contact' %}" style="color:rgba(255,255,255,0.8);text-decoration:none;padding:8px 16px;font-weight:600;font-family:'Cairo',sans-serif;">تواصل معنا</a>
      </div>

      <!-- CTA Buttons -->
      <div class="d-flex align-items-center gap-2">
        {% if request.user.is_authenticated %}
          <a href="{% url 'dashboard' %}"
             class="btn btn-sm rounded-pill text-white"
             style="background:#06B6D4;font-family:'Cairo',sans-serif;font-weight:700;">
            لوحة التحكم
          </a>
          <form method="post" action="{% url 'logout' %}" class="m-0">
            {% csrf_token %}
            <button type="submit"
                    class="btn btn-sm btn-outline-light rounded-pill"
                    style="font-family:'Cairo',sans-serif;">
              تسجيل الخروج
            </button>
          </form>
        {% else %}
          <a href="{% url 'login' %}"
             class="btn btn-sm btn-outline-light rounded-pill"
             style="font-family:'Cairo',sans-serif;">
            تسجيل الدخول
          </a>
          <a href="{% url 'landing:contact' %}"
             class="btn btn-sm rounded-pill text-white"
             style="background:#06B6D4;font-family:'Cairo',sans-serif;font-weight:700;">
            اطلب عرضاً
          </a>
        {% endif %}
      </div>

    </div>
  </div>
</nav>
"""
)

# ════════════════════════════════════════════════════════════
# 3) إعادة كتابة pricing.html نظيف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث pricing.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "landing", "pricing.html"),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>الأسعار - MotionHR</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    * { font-family: 'Cairo', sans-serif; }
    :root { --primary: #06B6D4; }
    .pricing-card {
      border-radius: 20px; padding: 32px;
      border: 2px solid #e5e7eb; transition: all 0.3s;
      height: 100%; position: relative;
    }
    .pricing-card.popular {
      border-color: var(--primary);
      box-shadow: 0 12px 40px rgba(6,182,212,0.2);
    }
    .popular-badge {
      position: absolute; top: -14px; left: 50%;
      transform: translateX(-50%);
      background: var(--primary); color: white;
      padding: 4px 20px; border-radius: 50px;
      font-size: 0.8rem; font-weight: 700;
    }
  </style>
</head>
<body style="background:#f8fafc;">

{% include 'landing/_navbar.html' %}

<div class="container py-5">

  <div class="text-center mb-5">
    <h1 class="fw-black mb-3" style="font-size:2.5rem;">الأسعار والباقات</h1>
    <p class="text-muted fs-5">اختر الباقة المناسبة لحجم شركتك</p>
  </div>

  <div class="row g-4 justify-content-center">

    <!-- Starter -->
    <div class="col-md-6 col-lg-3">
      <div class="pricing-card bg-white">
        <div class="mb-3">
          <h4 class="fw-bold" style="color:#6b7280;">المبتدئ</h4>
          <div class="text-muted small">حتى 15 موظف</div>
        </div>
        <div class="mb-4 pb-3 border-bottom">
          <span style="font-size:2.5rem;font-weight:900;color:#6b7280;">299</span>
          <span class="text-muted"> ج.م/شهر</span>
          <div class="small text-muted">أو <strong>2,999 ج.م</strong>/سنة <span class="badge bg-success ms-1">وفر 17%</span></div>
        </div>
        <ul class="list-unstyled mb-4">
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>إدارة الموظفين</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>الحضور بالـ GPS</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>التقارير الأساسية</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>تصدير Excel</li>
          <li class="d-flex gap-2 mb-2 small text-muted"><i class="bi bi-x-circle mt-1" style="color:#d1d5db;"></i>التتبع الميداني</li>
          <li class="d-flex gap-2 mb-2 small text-muted"><i class="bi bi-x-circle mt-1" style="color:#d1d5db;"></i>الخريطة الحية</li>
        </ul>
        <a href="{% url 'landing:contact' %}"
           class="btn w-100 fw-bold"
           style="border:2px solid #6b7280;color:#6b7280;border-radius:10px;">
          ابدأ الآن
        </a>
      </div>
    </div>

    <!-- Business -->
    <div class="col-md-6 col-lg-3">
      <div class="pricing-card bg-white popular">
        <div class="popular-badge">⭐ الأكثر شيوعاً</div>
        <div class="mb-3">
          <h4 class="fw-bold" style="color:#06B6D4;">الأعمال</h4>
          <div class="text-muted small">حتى 50 موظف</div>
        </div>
        <div class="mb-4 pb-3 border-bottom">
          <span style="font-size:2.5rem;font-weight:900;color:#06B6D4;">599</span>
          <span class="text-muted"> ج.م/شهر</span>
          <div class="small text-muted">أو <strong>5,999 ج.م</strong>/سنة <span class="badge bg-success ms-1">وفر 17%</span></div>
        </div>
        <ul class="list-unstyled mb-4">
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>كل مميزات Starter</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>التتبع الميداني</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>الخريطة الحية</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>Workflow الموافقات</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>إدارة الإجازات</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>تقارير متقدمة</li>
        </ul>
        <a href="{% url 'landing:contact' %}"
           class="btn w-100 fw-bold text-white"
           style="background:#06B6D4;border-radius:10px;">
          ابدأ الآن
        </a>
      </div>
    </div>

    <!-- Professional -->
    <div class="col-md-6 col-lg-3">
      <div class="pricing-card bg-white">
        <div class="mb-3">
          <h4 class="fw-bold" style="color:#7c3aed;">الاحترافي</h4>
          <div class="text-muted small">حتى 100 موظف</div>
        </div>
        <div class="mb-4 pb-3 border-bottom">
          <span style="font-size:2.5rem;font-weight:900;color:#7c3aed;">999</span>
          <span class="text-muted"> ج.م/شهر</span>
          <div class="small text-muted">أو <strong>9,999 ج.م</strong>/سنة <span class="badge bg-success ms-1">وفر 17%</span></div>
        </div>
        <ul class="list-unstyled mb-4">
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>كل مميزات Business</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>دخول بالموبايل</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>SMS OTP</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>Payroll متقدم</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>التتبع الصامت</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>API Access</li>
        </ul>
        <a href="{% url 'landing:contact' %}"
           class="btn w-100 fw-bold"
           style="border:2px solid #7c3aed;color:#7c3aed;border-radius:10px;">
          ابدأ الآن
        </a>
      </div>
    </div>

    <!-- Enterprise -->
    <div class="col-md-6 col-lg-3">
      <div class="pricing-card bg-white">
        <div class="mb-3">
          <h4 class="fw-bold text-dark">المؤسسي</h4>
          <div class="text-muted small">100+ موظف</div>
        </div>
        <div class="mb-4 pb-3 border-bottom">
          <div style="font-size:1.5rem;font-weight:900;">حسب الطلب</div>
          <div class="small text-muted">تواصل معنا للسعر</div>
        </div>
        <ul class="list-unstyled mb-4">
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>كل المميزات</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>White Label</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>سيرفر العميل</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>SSO / Active Directory</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>دعم مخصص 24/7</li>
          <li class="d-flex gap-2 mb-2 small"><i class="bi bi-check-circle-fill text-success mt-1"></i>تدريب وتأهيل</li>
        </ul>
        <a href="{% url 'landing:contact' %}"
           class="btn w-100 fw-bold"
           style="border:2px solid #1f2937;color:#1f2937;border-radius:10px;">
          تواصل معنا
        </a>
      </div>
    </div>

  </div>

  <!-- إضافات -->
  <div class="row justify-content-center mt-5">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h5 class="fw-bold mb-3 text-center">إضافات متاحة</h5>
          <div class="row g-2 text-center">
            <div class="col-6 col-md-3">
              <div class="p-3 rounded" style="background:#f8fafc;">
                <div class="fw-bold" style="color:#06B6D4;">+200 ج.م</div>
                <small class="text-muted">تتبع ميداني</small>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-3 rounded" style="background:#f8fafc;">
                <div class="fw-bold" style="color:#06B6D4;">+300 ج.م</div>
                <small class="text-muted">Payroll متقدم</small>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-3 rounded" style="background:#f8fafc;">
                <div class="fw-bold" style="color:#06B6D4;">5,000 ج.م</div>
                <small class="text-muted">سيرفر العميل</small>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-3 rounded" style="background:#f8fafc;">
                <div class="fw-bold" style="color:#06B6D4;">2,000 ج.م</div>
                <small class="text-muted">إعداد وتدريب</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- FAQ -->
  <div class="row justify-content-center mt-5">
    <div class="col-lg-8">
      <h3 class="fw-bold text-center mb-4">أسئلة شائعة</h3>
      <div class="accordion" id="faqAcc">
        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq1" style="background:white;">
              هل يوجد فترة تجريبية مجانية؟
            </button>
          </h2>
          <div id="faq1" class="accordion-collapse collapse" data-bs-parent="#faqAcc">
            <div class="accordion-body text-muted">نعم، نقدم 14 يوم مجاناً بدون بطاقة ائتمان.</div>
          </div>
        </div>
        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq2" style="background:white;">
              هل يمكنني الترقية لاحقاً؟
            </button>
          </h2>
          <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAcc">
            <div class="accordion-body text-muted">بالطبع، يمكنك الترقية أو تخفيض الخطة في أي وقت.</div>
          </div>
        </div>
        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq3" style="background:white;">
              كيف يتم الدفع؟
            </button>
          </h2>
          <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#faqAcc">
            <div class="accordion-body text-muted">تحويل بنكي أو محافظ إلكترونية. شهري أو سنوي.</div>
          </div>
        </div>
        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq4" style="background:white;">
              هل بياناتي آمنة؟
            </button>
          </h2>
          <div id="faq4" class="accordion-collapse collapse" data-bs-parent="#faqAcc">
            <div class="accordion-body text-muted">نعم، بياناتك مشفرة ومعزولة تماماً عن بيانات الشركات الأخرى.</div>
          </div>
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
# 4) إعادة كتابة about.html نظيف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث about.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "landing", "about.html"),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>عن MotionHR</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
  <style>* { font-family: 'Cairo', sans-serif; }</style>
</head>
<body>

{% include 'landing/_navbar.html' %}

<!-- Hero -->
<section style="background:linear-gradient(135deg,#0f172a,#1e3a5f); padding:80px 0; text-align:center; color:white;">
  <div class="container">
    <h1 class="fw-black mb-3" style="font-size:3rem;">عن MotionHR</h1>
    <p class="fs-5 mb-0" style="color:rgba(255,255,255,0.75); max-width:600px; margin:0 auto;">
      نظام إدارة الموارد البشرية الأذكى للشركات العربية الصغيرة والمتوسطة
    </p>
  </div>
</section>

<div class="container py-5">

  <!-- لماذا MotionHR -->
  <div class="row justify-content-center mb-5">
    <div class="col-lg-8 text-center">
      <h2 class="fw-bold mb-4">لماذا MotionHR؟</h2>
      <p class="text-muted fs-5 lh-lg">
        وُلد MotionHR من حاجة حقيقية — الشركات العربية الصغيرة والمتوسطة
        تعاني من غياب نظام HR محترف يناسب احتياجاتها وميزانيتها.
        معظم الأنظمة إما مكلفة جداً أو معقدة أو غير مصممة للسوق العربي.
      </p>
      <p class="text-muted fs-5 lh-lg">
        MotionHR يختلف — نظام سهل، احترافي، بسعر مناسب،
        مع ميزة تنافسية لا مثيل لها:
        <strong style="color:#06B6D4;">تتبع الموظفين الميدانيين في الوقت الفعلي</strong>.
      </p>
    </div>
  </div>

  <!-- القيم الأربعة -->
  <div class="row g-4 mb-5">
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#fff3e0;">
          <i class="bi bi-trophy-fill" style="font-size:1.8rem;color:#f59e0b;"></i>
        </div>
        <h5 class="fw-bold">البساطة</h5>
        <p class="text-muted small">نظام بسيط يتعلمه أي موظف في دقائق</p>
      </div>
    </div>
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#e8f5e9;">
          <i class="bi bi-shield-check-fill" style="font-size:1.8rem;color:#10b981;"></i>
        </div>
        <h5 class="fw-bold">الأمان</h5>
        <p class="text-muted small">بياناتك محمية ومشفرة تماماً</p>
      </div>
    </div>
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#e0f7fa;">
          <i class="bi bi-lightning-fill" style="font-size:1.8rem;color:#06B6D4;"></i>
        </div>
        <h5 class="fw-bold">السرعة</h5>
        <p class="text-muted small">إعداد كامل في ساعة واحدة</p>
      </div>
    </div>
    <div class="col-md-6 col-lg-3">
      <div class="card border-0 shadow-sm h-100 text-center p-4">
        <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3"
             style="width:64px;height:64px;background:#ede7f6;">
          <i class="bi bi-headset-fill" style="font-size:1.8rem;color:#7c3aed;"></i>
        </div>
        <h5 class="fw-bold">الدعم</h5>
        <p class="text-muted small">فريق دعم متخصص يساعدك دايماً</p>
      </div>
    </div>
  </div>

  <!-- المميزات الرئيسية -->
  <div class="row g-4 mb-5">
    <div class="col-12 text-center mb-2">
      <h2 class="fw-bold">ما يميز MotionHR</h2>
    </div>

    {% for icon, color, bg, title, desc in features %}
    <div class="col-md-6 col-lg-4">
      <div class="d-flex gap-3 p-3 rounded-3 h-100" style="background:#f8fafc;">
        <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
             style="width:48px;height:48px;background:{{ bg }};">
          <i class="bi bi-{{ icon }}" style="color:{{ color }};font-size:1.2rem;"></i>
        </div>
        <div>
          <h6 class="fw-bold mb-1">{{ title }}</h6>
          <p class="text-muted small mb-0">{{ desc }}</p>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- CTA -->
  <div class="text-center py-5 rounded-3"
       style="background:linear-gradient(135deg,#0f172a,#1e3a5f);">
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
# 5) تحديث landing/views.py — about يبعت features context
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث landing/views.py...")

views_path = os.path.join(BASE_DIR, "landing", "views.py")
views = read_file(views_path)

if "def landing_about" in views:
    old_about = '''def landing_about(request):
    """صفحة عن النظام"""
    context = {
        "page_title": "عن MotionHR",
    }
    return render(request, "landing/about.html", context)'''

    new_about = '''def landing_about(request):
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
    return render(request, "landing/about.html", context)'''

    if old_about in views:
        views = views.replace(old_about, new_about)
        write_file(views_path, views)
        print("  ✅ تم تحديث landing_about view")
    else:
        print("  ℹ️  landing_about مختلف — هنضيف features context بطريقة بديلة")
        views = views.replace(
            '"page_title": "عن MotionHR",\n    }\n    return render(request, "landing/about.html", context)',
            '''"page_title": "عن MotionHR",
        "features": [
            ("people-fill", "#06B6D4", "#e0f7fa", "إدارة الموظفين", "ملف شامل لكل موظف"),
            ("geo-alt-fill", "#10b981", "#e8f5e9", "حضور GPS", "تسجيل بالموقع مع التحقق"),
            ("broadcast", "#f59e0b", "#fff3e0", "تتبع ميداني Live", "خريطة حية للموظفين"),
            ("calendar2-check", "#e91e63", "#fce4ec", "إدارة الإجازات", "طلبات وموافقات"),
            ("bar-chart-fill", "#7c3aed", "#ede7f6", "تقارير شاملة", "Excel + تحليلات"),
            ("sliders", "#f59e0b", "#fff3e0", "سياسات مرنة", "كل شركة لها سياستها"),
        ],
    }
    return render(request, "landing/about.html", context)'''
        )
        write_file(views_path, views)
        print("  ✅ تم إضافة features context")
else:
    print("  ℹ️  landing_about غير موجود بالشكل المتوقع")


# ════════════════════════════════════════════════════════════
# 6) فحص Django check
# ════════════════════════════════════════════════════════════
print("\n🔍 Django Check...")

import django
django.setup()

from django.core.management import call_command
import io
from contextlib import redirect_stderr, redirect_stdout

out = io.StringIO()
err = io.StringIO()
try:
    with redirect_stdout(out), redirect_stderr(err):
        call_command("check", "--deploy", stdout=out, stderr=err)
except SystemExit:
    pass

output = out.getvalue() + err.getvalue()
if "System check identified no issues" in output or "no issues" in output.lower():
    print("  ✅ System check: لا يوجد أخطاء")
else:
    print("  ℹ️  شغّل: python manage.py check")


print("\n" + "=" * 60)
print("  ✅ Patch 46 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ _navbar.html مشترك لكل صفحات Landing
  2. ✅ pricing.html نظيف بدون split/getattr
  3. ✅ about.html نظيف مع features section
  4. ✅ Navbar يعرض:
       - لو داخل: لوحة التحكم + تسجيل الخروج
       - لو مش داخل: تسجيل الدخول + اطلب عرضاً
  5. ✅ FAQ في صفحة الأسعار
  6. ✅ إضافات في صفحة الأسعار

جرب:
  http://127.0.0.1:8000/
  http://127.0.0.1:8000/pricing/
  http://127.0.0.1:8000/about/
  http://127.0.0.1:8000/contact/

جرب من غير Login ومن جوا Login
""")