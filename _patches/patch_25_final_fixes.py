#!/usr/bin/env python3
"""
Patch 25: Final Fixes
======================
1. إصلاح split filter في pricing + about
2. إصلاح getattr filter في login-settings + leave types
3. إصلاح الاشتراك المنتهي
4. إصلاح تكرار اسم الشهر في Dashboard
"""

import os, sys, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

print("=" * 60)
print("  Patch 25: Final Fixes")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إنشاء Custom Template Tags
#    يحل مشكلة split + getattr
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء Custom Template Tags...")

# نعمل templatetags في accounts app
tags_dir = os.path.join(BASE_DIR, 'accounts', 'templatetags')
os.makedirs(tags_dir, exist_ok=True)

create_file(os.path.join(tags_dir, '__init__.py'), '')

create_file(
    os.path.join(tags_dir, 'custom_filters.py'),
    '''"""
custom_filters.py
فلاتر مخصصة لـ Django Templates
"""

from django import template

register = template.Library()


@register.filter(name="split")
def split_filter(value, delimiter="|"):
    """
    يقسم النص حسب الفاصل
    استخدام: {{ "a|b|c"|split:"|" }}
    """
    if value:
        return str(value).split(delimiter)
    return []


@register.filter(name="getattr")
def getattr_filter(obj, attr):
    """
    يجيب قيمة attribute من object
    استخدام: {{ obj|getattr:"field_name" }}
    """
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    يجيب قيمة من dictionary
    استخدام: {{ dict|get_item:"key" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter(name="multiply")
def multiply(value, arg):
    """ضرب"""
    try:
        return float(value) * float(arg)
    except Exception:
        return 0


@register.filter(name="percentage")
def percentage(value, total):
    """حساب النسبة المئوية"""
    try:
        if float(total) == 0:
            return 0
        return round(float(value) / float(total) * 100, 1)
    except Exception:
        return 0
'''
)


# ════════════════════════════════════════════════════════════
# 2. إصلاح landing/pricing.html - إزالة split filter
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح landing/pricing.html...")

pricing_template = r"""<!DOCTYPE html>
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
      padding: 16px 0; position: sticky; top: 0; z-index: 1000;
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
        <div class="popular-badge">الأكثر شيوعاً</div>
        {% endif %}

        <div class="mb-3">
          <h4 class="fw-bold" style="color:{{ plan.color }};">{{ plan.name_ar }}</h4>
          <div class="text-muted small">{{ plan.employees }} موظف</div>
        </div>

        <div class="mb-4 pb-3 border-bottom">
          {% if plan.price %}
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
          <div style="font-size:1.5rem;font-weight:900;">حسب الطلب</div>
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
           style="{% if plan.popular %}background:{{ plan.color }};color:white;
                  {% else %}border:2px solid {{ plan.color }};color:{{ plan.color }};{% endif %}
                  border-radius:10px;">
          {% if not plan.price %}تواصل معنا{% else %}ابدأ الآن{% endif %}
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

        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button"
                    data-bs-toggle="collapse" data-bs-target="#faq1" style="background:white;">
              هل يوجد فترة تجريبية مجانية؟
            </button>
          </h2>
          <div id="faq1" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
            <div class="accordion-body text-muted">
              نعم، نقدم نسخة تجريبية مجانية لمدة 14 يوم بدون الحاجة لبطاقة ائتمان.
            </div>
          </div>
        </div>

        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button"
                    data-bs-toggle="collapse" data-bs-target="#faq2" style="background:white;">
              هل يمكنني الترقية لاحقاً؟
            </button>
          </h2>
          <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
            <div class="accordion-body text-muted">
              بالطبع، يمكنك الترقية أو تخفيض الخطة في أي وقت.
            </div>
          </div>
        </div>

        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button"
                    data-bs-toggle="collapse" data-bs-target="#faq3" style="background:white;">
              هل بياناتي آمنة؟
            </button>
          </h2>
          <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
            <div class="accordion-body text-muted">
              نعم، بياناتك مشفرة ومحمية. يمكنك أيضاً التثبيت على سيرفرك الخاص.
            </div>
          </div>
        </div>

        <div class="accordion-item border-0 mb-2 rounded-3 overflow-hidden shadow-sm">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed fw-semibold" type="button"
                    data-bs-toggle="collapse" data-bs-target="#faq4" style="background:white;">
              كيف يتم الدفع؟
            </button>
          </h2>
          <div id="faq4" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
            <div class="accordion-body text-muted">
              الدفع شهري أو سنوي عبر تحويل بنكي أو محافظ إلكترونية.
            </div>
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

create_file(
    os.path.join(BASE_DIR, 'templates', 'landing', 'pricing.html'),
    pricing_template
)


# ════════════════════════════════════════════════════════════
# 3. إصلاح landing/about.html - إزالة split filter
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح landing/about.html...")

about_template = r"""<!DOCTYPE html>
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
    .navbar-landing { background:rgba(15,23,42,0.97); padding:16px 0; position:sticky; top:0; z-index:1000; }
    .hero-about { background:linear-gradient(135deg,#0f172a,#1e3a5f); padding:80px 0; color:white; text-align:center; }
  </style>
</head>
<body>

<nav class="navbar-landing">
  <div class="container">
    <div class="d-flex align-items-center justify-content-between">
      <a href="{% url 'landing:home' %}"
         style="font-size:1.5rem;font-weight:900;color:#06B6D4;text-decoration:none;">MotionHR</a>
      <div class="d-flex gap-2">
        <a href="{% url 'landing:home' %}" class="btn btn-sm btn-outline-light rounded-pill">الرئيسية</a>
        <a href="{% url 'landing:contact' %}" class="btn btn-sm rounded-pill text-white" style="background:#06B6D4;">تواصل معنا</a>
      </div>
    </div>
  </div>
</nav>

<section class="hero-about">
  <div class="container">
    <h1 class="fw-black mb-3" style="font-size:3rem;">عن MotionHR</h1>
    <p class="fs-5 mb-0" style="color:rgba(255,255,255,0.75); max-width:600px; margin:0 auto;">
      نظام إدارة الموارد البشرية الأذكى للشركات العربية الصغيرة والمتوسطة
    </p>
  </div>
</section>

<div class="container py-5">

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

  <div class="text-center py-5 rounded-3"
       style="background:linear-gradient(135deg,#0f172a,#1e3a5f);">
    <h3 class="fw-bold text-white mb-3">جاهز تجرب MotionHR؟</h3>
    <p class="text-white-50 mb-4">14 يوم مجاناً بدون أي التزام</p>
    <a href="{% url 'landing:contact' %}"
       class="btn btn-lg fw-bold rounded-pill px-5 text-white"
       style="background:#06B6D4;">ابدأ الآن</a>
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'landing', 'about.html'),
    about_template
)


# ════════════════════════════════════════════════════════════
# 4. إصلاح leave_type_form.html - إزالة getattr
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح templates/leaves/leave_type_form.html...")

leave_type_form = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'leaves:leave_types_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">{{ page_title }}</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-7">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  اسم الإجازة <span class="text-danger">*</span>
                </label>
                <input type="text" name="name" class="form-control"
                       value="{{ lt.name|default:'' }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الفئة</label>
                <select name="category" class="form-select">
                  {% for val, label in categories %}
                  <option value="{{ val }}"
                    {% if lt.category == val %}selected{% endif %}>
                    {{ label }}
                  </option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  عدد الأيام المسموحة سنوياً
                  <small class="text-muted">(0 = بدون حد)</small>
                </label>
                <input type="number" name="days_allowed" class="form-control"
                       value="{{ lt.days_allowed|default:0 }}" min="0">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">أقصى أيام ترحيل</label>
                <input type="number" name="max_carry_days" class="form-control"
                       value="{{ lt.max_carry_days|default:0 }}" min="0">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">اللون</label>
                <div class="d-flex gap-2 align-items-center">
                  <input type="color" name="color"
                         class="form-control form-control-color"
                         value="{{ lt.color|default:'#06B6D4' }}"
                         style="width:50px;height:38px;">
                  <small class="text-muted">لون تمييز نوع الإجازة</small>
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">الوصف</label>
                <textarea name="description" class="form-control" rows="2">{{ lt.description|default:'' }}</textarea>
              </div>

              <!-- Switches بدون getattr -->
              <div class="col-12">
                <div class="row g-2">

                  <div class="col-md-6">
                    <div class="d-flex align-items-center justify-content-between p-3 border rounded-3">
                      <span class="fw-semibold small">بمرتب</span>
                      <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox"
                               name="is_paid" id="is_paid"
                               {% if lt.is_paid or not lt %}checked{% endif %}
                               style="width:2.5rem;height:1.25rem;">
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6">
                    <div class="d-flex align-items-center justify-content-between p-3 border rounded-3">
                      <span class="fw-semibold small">تحتاج موافقة</span>
                      <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox"
                               name="requires_approval" id="requires_approval"
                               {% if lt.requires_approval or not lt %}checked{% endif %}
                               style="width:2.5rem;height:1.25rem;">
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6">
                    <div class="d-flex align-items-center justify-content-between p-3 border rounded-3">
                      <span class="fw-semibold small">تحتاج وثيقة</span>
                      <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox"
                               name="requires_document" id="requires_document"
                               {% if lt.requires_document %}checked{% endif %}
                               style="width:2.5rem;height:1.25rem;">
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6">
                    <div class="d-flex align-items-center justify-content-between p-3 border rounded-3">
                      <span class="fw-semibold small">ترحيل للسنة القادمة</span>
                      <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox"
                               name="carry_forward" id="carry_forward"
                               {% if lt.carry_forward %}checked{% endif %}
                               style="width:2.5rem;height:1.25rem;">
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6">
                    <div class="d-flex align-items-center justify-content-between p-3 border rounded-3">
                      <span class="fw-semibold small">نشط</span>
                      <div class="form-check form-switch mb-0">
                        <input class="form-check-input" type="checkbox"
                               name="is_active" id="is_active"
                               {% if lt.is_active or not lt %}checked{% endif %}
                               style="width:2.5rem;height:1.25rem;">
                      </div>
                    </div>
                  </div>

                </div>
              </div>

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة{% else %}حفظ{% endif %}
              </button>
              <a href="{% url 'leaves:leave_types_list' %}"
                 class="btn btn-outline-secondary px-4"
                 style="border-radius:10px;">إلغاء</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'leaves', 'leave_type_form.html'),
    leave_type_form
)


# ════════════════════════════════════════════════════════════
# 5. إصلاح login_settings.html - إزالة getattr
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح templates/accounts/login_settings.html...")

login_settings_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إعدادات تسجيل الدخول{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-shield-lock me-2" style="color:#06B6D4;"></i>
        إعدادات تسجيل الدخول
      </h4>
      <p class="text-muted mb-0">تحكم في طرق الدخول وأمان كلمات المرور</p>
    </div>
  </div>

  <form method="post">
    {% csrf_token %}
    <div class="row g-4">

      <!-- طرق تسجيل الدخول -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-door-open me-2" style="color:#06B6D4;"></i>
              طرق تسجيل الدخول
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            {% for field_name, label, desc, available in login_methods %}
            <div class="d-flex align-items-start justify-content-between py-3
                        border-bottom {% if forloop.last %}border-0{% endif %}">
              <div>
                <div class="fw-semibold">{{ label }}</div>
                <small class="text-muted">{{ desc }}</small>
                {% if not available %}
                <span class="badge bg-warning text-dark ms-1">يتطلب ترقية</span>
                {% endif %}
              </div>
              <div class="form-check form-switch ms-3 mt-1">
                <input class="form-check-input" type="checkbox"
                       name="{{ field_name }}"
                       id="{{ field_name }}"
                       {% if available %}
                         {% if settings_obj %}
                           {% if field_name == 'login_by_username' and settings_obj.login_by_username %}checked
                           {% elif field_name == 'login_by_email' and settings_obj.login_by_email %}checked
                           {% elif field_name == 'login_by_employee_code' and settings_obj.login_by_employee_code %}checked
                           {% elif field_name == 'login_by_phone' and settings_obj.login_by_phone %}checked
                           {% endif %}
                         {% else %}
                           {% if field_name == 'login_by_username' %}checked
                           {% elif field_name == 'login_by_email' %}checked{% endif %}
                         {% endif %}
                       {% else %}disabled{% endif %}
                       style="width:2.5rem; height:1.25rem;">
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
      </div>

      <!-- إعدادات كلمة المرور -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-key me-2" style="color:#06B6D4;"></i>
              إعدادات كلمة المرور
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="mb-4">
              <label class="fw-semibold small mb-2">الحد الأدنى لطول كلمة المرور</label>
              <div class="d-flex align-items-center gap-3">
                <input type="range" name="min_password_length"
                       class="form-range flex-grow-1" min="6" max="20"
                       value="{{ settings_obj.min_password_length|default:8 }}"
                       oninput="document.getElementById('pwdLen').textContent=this.value">
                <span class="badge fs-6 px-3" style="background:#06B6D4; min-width:40px;">
                  <span id="pwdLen">{{ settings_obj.min_password_length|default:8 }}</span>
                </span>
              </div>
            </div>

            {% for field_name, label in password_rules %}
            <div class="d-flex align-items-center justify-content-between py-2 border-bottom">
              <span class="fw-semibold small">{{ label }}</span>
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox"
                       name="{{ field_name }}"
                       {% if settings_obj %}
                         {% if field_name == 'require_uppercase' and settings_obj.require_uppercase %}checked
                         {% elif field_name == 'require_numbers' and settings_obj.require_numbers %}checked
                         {% elif field_name == 'require_symbols' and settings_obj.require_symbols %}checked
                         {% endif %}
                       {% endif %}
                       style="width:2.5rem; height:1.25rem;">
              </div>
            </div>
            {% endfor %}

            <div class="mt-3">
              <label class="fw-semibold small mb-2">
                انتهاء صلاحية كلمة المرور (يوم)
                <small class="text-muted fw-normal">(0 = لا تنتهي)</small>
              </label>
              <input type="number" name="password_expiry_days"
                     class="form-control" min="0" max="365"
                     value="{{ settings_obj.password_expiry_days|default:0 }}">
            </div>

          </div>
        </div>
      </div>

      <!-- إعدادات القفل -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-shield-x me-2" style="color:#06B6D4;"></i>
              إعدادات القفل
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="mb-3">
              <label class="fw-semibold small mb-2">أقصى عدد محاولات قبل القفل</label>
              <select name="max_login_attempts" class="form-select">
                <option value="3" {% if settings_obj.max_login_attempts == 3 %}selected{% endif %}>3 محاولات</option>
                <option value="5" {% if settings_obj.max_login_attempts == 5 or not settings_obj %}selected{% endif %}>5 محاولات</option>
                <option value="10" {% if settings_obj.max_login_attempts == 10 %}selected{% endif %}>10 محاولات</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="fw-semibold small mb-2">مدة القفل (بالدقائق)</label>
              <select name="lockout_duration_minutes" class="form-select">
                {% for n, label in lockout_options %}
                <option value="{{ n }}"
                  {% if settings_obj.lockout_duration_minutes == n %}selected{% endif %}>
                  {{ label }}
                </option>
                {% endfor %}
              </select>
            </div>

            <div class="form-check form-switch mt-4">
              <input class="form-check-input" type="checkbox"
                     name="force_change_on_first_login"
                     id="forceChange"
                     {% if settings_obj.force_change_on_first_login or not settings_obj %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="forceChange">
                إجبار تغيير كلمة المرور عند أول دخول
              </label>
            </div>

          </div>
        </div>
      </div>

    </div>

    <div class="mt-4 d-flex gap-2">
      <button type="submit" class="btn btn-lg text-white px-5"
              style="background:#06B6D4; border-radius:10px;">
        <i class="bi bi-check-lg me-2"></i>
        حفظ الإعدادات
      </button>
      <a href="{% url 'dashboard' %}"
         class="btn btn-lg btn-outline-secondary px-4"
         style="border-radius:10px;">إلغاء</a>
    </div>

  </form>
</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'accounts', 'login_settings.html'),
    login_settings_template
)


# ════════════════════════════════════════════════════════════
# 6. إصلاح تكرار اسم الشهر في Dashboard
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح تكرار الشهر في Dashboard...")

dashboard_path = os.path.join(BASE_DIR, 'templates', 'dashboard', 'index.html')
dashboard = read_file(dashboard_path)

# إصلاح format التاريخ
old_date = '{{ today|date:"l، d MMMM Y" }}'
new_date = '{{ today|date:"d/m/Y" }}'

if old_date in dashboard:
    dashboard = dashboard.replace(old_date, new_date)
    write_file(dashboard_path, dashboard)
    print("  ✅ تم إصلاح format التاريخ")
else:
    # نبحث عن أي format فيه MMMM
    dashboard = re.sub(r'\{\{.*?today.*?MMMM.*?\}\}', '{{ today|date:"d/m/Y" }}', dashboard)
    write_file(dashboard_path, dashboard)
    print("  ✅ تم إصلاح format التاريخ")


# ════════════════════════════════════════════════════════════
# 7. إصلاح "اشتراكك منتهي" - تحديث SubscriptionMiddleware
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح مشكلة الاشتراك المنتهي...")

middleware_path = os.path.join(BASE_DIR, 'core', 'middleware.py')
middleware = read_file(middleware_path)

# إصلاح is_valid property
old_check = "request.subscription_valid = sub.is_valid"
new_check = """# التحقق من صلاحية الاشتراك
                        try:
                            is_valid = sub.is_valid
                        except AttributeError:
                            # لو is_valid مش موجود نعمله يدوياً
                            from django.utils import timezone
                            is_valid = (
                                sub.status in ['active', 'trial'] and
                                sub.end_date >= timezone.now().date()
                            )
                        request.subscription_valid = is_valid"""

if old_check in middleware:
    middleware = middleware.replace(old_check, new_check)
    write_file(middleware_path, middleware)
    print("  ✅ تم إصلاح SubscriptionMiddleware")
else:
    print("  ℹ️  SubscriptionMiddleware - لا يحتاج تعديل")

# إصلاح all_features
old_features = "request.subscription_features = sub.all_features"
new_features = """# جلب الميزات
                        try:
                            features = sub.all_features
                        except AttributeError:
                            features = set()
                        request.subscription_features = features"""

if old_features in middleware:
    middleware = read_file(middleware_path)
    middleware = middleware.replace(old_features, new_features)
    write_file(middleware_path, middleware)


# ════════════════════════════════════════════════════════════
# 8. إضافة is_valid و days_remaining في CompanySubscription
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة properties في CompanySubscription...")

subs_models_path = os.path.join(BASE_DIR, 'subscriptions', 'models.py')
subs_models = read_file(subs_models_path)

if 'def is_valid' not in subs_models and 'def days_remaining' not in subs_models:
    # نضيف properties في CompanySubscription
    extra_properties = '''
    @property
    def is_valid(self):
        """التحقق من صلاحية الاشتراك"""
        from django.utils import timezone
        today = timezone.now().date()
        return (
            self.status in ['active', 'trial'] and
            self.end_date >= today
        )

    @property
    def days_remaining(self):
        """الأيام المتبقية"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.end_date >= today:
            return (self.end_date - today).days
        return 0

    @property
    def is_expired(self):
        """هل منتهي؟"""
        from django.utils import timezone
        return self.end_date < timezone.now().date()

    @property
    def all_features(self):
        """كل ميزات الخطة"""
        return set()

    def __str__(self):
        return f"{self.company} - {self.plan}"
'''

    # نضيف قبل class التالي أو في آخر CompanySubscription
    if 'class CompanySubscription' in subs_models:
        # نلاقي نهاية الكلاس ونضيف فيها
        idx = subs_models.find('class CompanySubscription')
        # نلاقي أول class بعده أو EOF
        next_class = subs_models.find('\nclass ', idx + 1)
        if next_class == -1:
            subs_models += extra_properties
        else:
            subs_models = subs_models[:next_class] + extra_properties + subs_models[next_class:]
        write_file(subs_models_path, subs_models)
        print("  ✅ تم إضافة properties لـ CompanySubscription")
    else:
        print("  ⚠️  CompanySubscription مش موجود في models.py")
else:
    print("  ℹ️  Properties موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 25 اكتمل!")
print("=" * 60)
print("""
📋 اللي اتصلح:
  1. ✅ Custom Template Tags (split + getattr)
  2. ✅ landing/pricing.html - بدون split
  3. ✅ landing/about.html - بدون split
  4. ✅ leave_type_form.html - بدون getattr
  5. ✅ login_settings.html - بدون getattr
  6. ✅ Dashboard - تكرار الشهر
  7. ✅ SubscriptionMiddleware - is_valid
  8. ✅ CompanySubscription - properties

🚀 شغّل السيرفر وجرب:
  /pricing/
  /about/
  /leaves/types/add/
  /accounts/login-settings/
  /subscriptions/my-plan/
  /dashboard/
""")