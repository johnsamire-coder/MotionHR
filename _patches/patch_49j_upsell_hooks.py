"""
Patch 49j-Hooks — SaaS Upsell Hooks

الهدف:
1) إضافة "وحدات إضافية (Add-ons)" في القائمة الجانبية.
2) عرض (الرواتب، التوظيف، تقييم الأداء) وعليها علامة قفل 🔒.
3) عند الضغط عليها، تفتح صفحة تسويقية جذابة (Upsell Page).
4) زرار "تواصل مع المبيعات" يفتح الواتساب برسالة مجهزة أو يوجه للاتصال.

الملفات المعدلة:
- subscriptions/urls.py
- subscriptions/views.py
- templates/subscriptions/upsell_page.html (جديد)
- templates/base/dashboard_base.html
"""

import os
import shutil
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")

print("=" * 60)
print("Patch 49j-Hooks — SaaS Upsell Hooks")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path in [
    "subscriptions/views.py",
    "subscriptions/urls.py",
    "templates/base/dashboard_base.html",
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_name = rel_path.replace("/", "_").replace("\\", "_") + ".49j_hooks.bak"
        shutil.copy2(full, os.path.join(backup_dir, backup_name))

# ────────────────────────────────────────────────────────────
# Step 1: Update subscriptions/views.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: إضافة Upsell View")

views_path = "subscriptions/views.py"
views_content = read_file(views_path)

upsell_view = r'''
@login_required
def feature_upsell_page(request, feature_code):
    """صفحة تسويقية للموديولات الإضافية (Hooks)"""
    
    # محتوى تسويقي لكل موديول
    features_meta = {
        'payroll': {
            'title': 'نظام الرواتب والأجور (Payroll)',
            'icon': 'bi-cash-coin',
            'color': '#10b981',
            'description': 'نظام آلي متكامل لحساب الرواتب بضغطة زر بناءً على سجلات الحضور، التأخيرات، والخصومات.',
            'benefits': [
                'حساب آلي للتأخيرات والغياب بدون تدخل بشري.',
                'إصدار مسيرات الرواتب (Payslips) للموظفين.',
                'إدارة السلف، البدلات، والمكافآت.',
                'ربط مباشر مع البنوك لتصدير ملفات التحويل.',
            ],
            'whatsapp_text': 'أهلاً، مهتم بإضافة موديول (الرواتب والأجور) لنظام شركتي لمعرفة التكلفة.'
        },
        'recruitment': {
            'title': 'إدارة التوظيف (ATS)',
            'icon': 'bi-person-badge',
            'color': '#8b5cf6',
            'description': 'نظم عملية التوظيف بالكامل، من نشر الوظيفة حتى تعيين الموظف وتوقيع العقد.',
            'benefits': [
                'استقبال السير الذاتية وفرزها تلقائياً.',
                'جدولة المقابلات وإرسال إشعارات للمرشحين.',
                'تقييم المرشحين من مديري الإدارات.',
                'تحويل المرشح إلى موظف بضغطة زر.',
            ],
            'whatsapp_text': 'أهلاً، مهتم بإضافة موديول (التوظيف) لنظام شركتي لمعرفة التكلفة.'
        },
        'performance': {
            'title': 'تقييم الأداء (Performance)',
            'icon': 'bi-graph-up-arrow',
            'color': '#f59e0b',
            'description': 'ارتقِ بأداء فريقك عبر نظام تقييم موضوعي ومؤشرات أداء رئيسية (KPIs).',
            'benefits': [
                'تقييم دوري (شهري/ربع سنوي/سنوي).',
                'نماذج تقييم مخصصة لكل إدارة.',
                'تقييم 360 درجة (مدير، زميل، تقييم ذاتي).',
                'ربط التقييم بالمكافآت والترقيات.',
            ],
            'whatsapp_text': 'أهلاً، مهتم بإضافة موديول (تقييم الأداء) لنظام شركتي لمعرفة التكلفة.'
        },
        'api': {
            'title': 'الربط البرمجي (API & ERP)',
            'icon': 'bi-plug',
            'color': '#ef4444',
            'description': 'اربط MotionHR مع أنظمتك الحالية (ERP، أجهزة البصمة، البرامج المحاسبية).',
            'benefits': [
                'مزامنة البيانات في الوقت الفعلي.',
                'ربط مع أجهزة ZKTeco وغيرها.',
                'تصدير القيود المحاسبية لبرامج (Odoo, Zoho, إلخ).',
                'Webhooks مخصصة.',
            ],
            'whatsapp_text': 'أهلاً، مهتم بإضافة موديول (الربط البرمجي) لنظام شركتي لمعرفة التكلفة.'
        }
    }

    feature = features_meta.get(feature_code)
    if not feature:
        return redirect('dashboard')

    context = {
        'feature': feature,
        'page_title': f"ترقية النظام — {feature['title']}",
        # حط رقم المبيعات الخاص بيك هنا
        'sales_whatsapp': '201000000000' 
    }
    return render(request, 'subscriptions/upsell_page.html', context)
'''

if "def feature_upsell_page(" not in views_content:
    views_content += "\n" + upsell_view
    write_file(views_path, views_content)
else:
    print("ℹ️ feature_upsell_page موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Update subscriptions/urls.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إضافة URL الـ Upsell")

urls_path = "subscriptions/urls.py"
urls_content = read_file(urls_path)

if "name='upsell'" not in urls_content:
    upsell_url = "    path('upgrade/module/<str:feature_code>/', views.feature_upsell_page, name='upsell'),\n"
    urls_content = urls_content.replace("urlpatterns = [", "urlpatterns = [\n" + upsell_url)
    write_file(urls_path, urls_content)
else:
    print("ℹ️ Upsell URL موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 3: Create Upsell Template
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إنشاء صفحة التسويق (Upsell Page)")

upsell_html = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
  .upsell-hero {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 24px;
    color: white;
    padding: 60px 40px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .upsell-hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 50%);
    animation: rotate 20s linear infinite;
  }
  @keyframes rotate { 100% { transform: rotate(360deg); } }
  
  .upsell-icon-wrapper {
    width: 80px; height: 80px;
    border-radius: 20px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 2.5rem;
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.2);
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  }

  .benefit-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    height: 100%;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  .benefit-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    border-color: {{ feature.color }};
  }
  
  .pro-badge {
    position: absolute;
    top: 20px; right: 20px;
    background: linear-gradient(45deg, #f59e0b, #fbbf24);
    color: #fff;
    padding: 5px 15px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(245,158,11,0.3);
  }
</style>
{% endblock %}

{% block content %}
<div class="container" style="max-width: 900px;">

  <div class="upsell-hero shadow-lg mb-5">
    <div class="pro-badge"><i class="bi bi-star-fill me-1"></i>وحدة متقدمة (Pro)</div>
    <div class="upsell-icon-wrapper" style="color: {{ feature.color }};">
      <i class="bi {{ feature.icon }}"></i>
    </div>
    <h1 class="fw-bold mb-3">{{ feature.title }}</h1>
    <p class="lead mb-4" style="color: #cbd5e1; max-width: 600px; margin: 0 auto;">
      {{ feature.description }}
    </p>
    
    <div class="d-flex justify-content-center gap-3 mt-4">
      <a href="https://wa.me/{{ sales_whatsapp }}?text={{ feature.whatsapp_text|urlencode }}" 
         target="_blank"
         class="btn btn-lg fw-bold" 
         style="background: {{ feature.color }}; color: white; border-radius: 12px; padding: 12px 30px;">
        <i class="bi bi-whatsapp me-2"></i>تواصل مع المبيعات للتفعيل
      </a>
      <a href="{% url 'dashboard' %}" class="btn btn-outline-light btn-lg" style="border-radius: 12px;">
        العودة للرئيسية
      </a>
    </div>
  </div>

  <div class="text-center mb-4">
    <h4 class="fw-bold">لماذا تحتاج هذه الوحدة في شركتك؟</h4>
    <p class="text-muted">ميزات صممت لتسريع نمو شركتك وتقليل الأخطاء البشرية.</p>
  </div>

  <div class="row g-4 mb-5">
    {% for benefit in feature.benefits %}
    <div class="col-md-6">
      <div class="benefit-card d-flex align-items-start gap-3">
        <div class="fs-3" style="color: {{ feature.color }};"><i class="bi bi-check-circle-fill"></i></div>
        <div>
          <h6 class="fw-bold mb-1">ميزة أساسية</h6>
          <p class="text-muted small mb-0">{{ benefit }}</p>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>

</div>
{% endblock %}
"""
write_file("templates/subscriptions/upsell_page.html", upsell_html)

# ────────────────────────────────────────────────────────────
# Step 4: Inject into Sidebar (dashboard_base.html)
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: إضافة الموديولات المغلقة للقائمة الجانبية")

base_path = "templates/base/dashboard_base.html"
base_content = read_file(base_path)

upsell_sidebar_html = """
        <!-- 🔒 SaaS Hooks / Upsell Modules -->
        {% if request.user.role == 'company_admin' %}
        <li class="nav-item mt-3 mb-1">
          <div class="text-muted small fw-bold px-3 text-uppercase" style="letter-spacing: 1px; font-size: 0.7rem;">
            وحدات إضافية (Add-ons) <i class="bi bi-stars text-warning"></i>
          </div>
        </li>
        <li class="nav-item">
          <a class="nav-link text-secondary" href="{% url 'subscriptions:upsell' 'payroll' %}" style="background: rgba(0,0,0,0.02);">
            <i class="bi bi-cash-coin me-2"></i>الرواتب والأجور
            <i class="bi bi-lock-fill ms-auto text-warning" style="font-size: 0.8rem;"></i>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link text-secondary" href="{% url 'subscriptions:upsell' 'recruitment' %}" style="background: rgba(0,0,0,0.02);">
            <i class="bi bi-person-badge me-2"></i>التوظيف (ATS)
            <i class="bi bi-lock-fill ms-auto text-warning" style="font-size: 0.8rem;"></i>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link text-secondary" href="{% url 'subscriptions:upsell' 'performance' %}" style="background: rgba(0,0,0,0.02);">
            <i class="bi bi-graph-up-arrow me-2"></i>تقييم الأداء
            <i class="bi bi-lock-fill ms-auto text-warning" style="font-size: 0.8rem;"></i>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link text-secondary" href="{% url 'subscriptions:upsell' 'api' %}" style="background: rgba(0,0,0,0.02);">
            <i class="bi bi-plug me-2"></i>الربط البرمجي (API)
            <i class="bi bi-lock-fill ms-auto text-warning" style="font-size: 0.8rem;"></i>
          </a>
        </li>
        {% endif %}
        <!-- End SaaS Hooks -->
"""

# نبحث عن مكان الإعدادات في السايدبار عشان نحط القائمة فوقها
if "<!-- 🔒 SaaS Hooks / Upsell Modules -->" not in base_content:
    if "<!-- Settings -->" in base_content:
        base_content = base_content.replace("<!-- Settings -->", upsell_sidebar_html + "\n        <!-- Settings -->")
        write_file(base_path, base_content)
        print("✅ تم حقن الـ Hooks في القائمة الجانبية")
    else:
        print("⚠️ لم أتمكن من العثور على مكان مناسب في السايدبار. ستحتاج إضافتها يدوياً.")
else:
    print("ℹ️ الـ Hooks موجودة بالفعل في السايدبار")

print("\n" + "=" * 60)
print("✅ Patch 49j-Hooks اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
1) تم إضافة أقسام (الرواتب، التوظيف، تقييم الأداء، الـ API) في القائمة الجانبية.
2) الأقسام دي تظهر للـ company_admin فقط وجنبها علامة قفل 🔒.
3) لما يضغط عليها تفتح شاشة Landing رائعة (Upsell) بتشرح فوائد الموديول.
4) الشاشة فيها زرار بياخده على الواتس آب مباشرة برسالة مجهزة للتواصل معاك.

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")