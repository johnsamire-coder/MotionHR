"""
Patch 49j-Hooks v3 — Free Premium Modules in Sidebar

الهدف:
- إضافة المنتجات المجانية اللي نقدر نبنيها بدون تكلفة
- حذف أي hooks قديمة
- كل hook تحت القسم اللي يخصه

المنتجات المجانية:
1) الرواتب والأجور → تحت الموظفين
2) التوظيف (ATS) → تحت الطلبات
3) تقييم الأداء → تحت التقارير
4) إدارة التدريب → تحت الموظفين
5) إدارة الأصول → تحت الإعدادات

المنتجات المدفوعة (مش هنحطها دلوقتي):
- SMS/WhatsApp Notifications (Twilio)
- Cloud Storage (S3)
- Biometric Live Sync
"""

import os
import shutil

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
print("Patch 49j-Hooks v3 — Free Premium Modules in Sidebar")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path in [
    "subscriptions/views.py",
    "templates/base/dashboard_base.html",
    "templates/subscriptions/upsell_page.html",
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_name = rel_path.replace("/", "_").replace("\\", "_") + ".49j_v3.bak"
        shutil.copy2(full, os.path.join(backup_dir, backup_name))

print("✅ Backups created")

# ────────────────────────────────────────────────────────────
# Step 1: Update subscriptions/views.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: تحديث Upsell View بالمنتجات الجديدة")

views_path = "subscriptions/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف subscriptions/views.py غير موجود")

# نحذف الـ view القديمة ونستبدلها بالجديدة
new_upsell_view = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49j-Hooks v3 — Premium Module Upsell Pages
# ═════════════════════════════════════════════════════════════

@login_required
def feature_upsell_page(request, feature_code):
    """صفحة تسويقية للموديولات الإضافية"""

    # ═══ تعريف المنتجات ═══
    features_meta = {

        # ── 1) الرواتب ──
        'payroll': {
            'title': 'نظام الرواتب والأجور',
            'subtitle': 'Payroll Management',
            'icon': 'bi-cash-coin',
            'color': '#10b981',
            'gradient': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            'description': 'نظام آلي متكامل لحساب الرواتب بضغطة زر واحدة. يسحب بيانات الحضور والتأخيرات والخصومات تلقائياً ويحسب صافي الراتب لكل موظف.',
            'benefits': [
                {'title': 'حساب آلي للرواتب', 'desc': 'يسحب التأخيرات والغياب والخصومات من سجلات الحضور ويحسب الراتب تلقائياً بدون تدخل بشري.', 'icon': 'bi-calculator'},
                {'title': 'مسيرات الرواتب (Payslips)', 'desc': 'إصدار كشف راتب مفصّل لكل موظف بصيغة PDF جاهز للطباعة أو الإرسال بالإيميل.', 'icon': 'bi-file-earmark-pdf'},
                {'title': 'إدارة البدلات والسلف', 'desc': 'تسجيل البدلات (سكن/مواصلات/طعام) والسلف وخصمها تلقائياً من الراتب.', 'icon': 'bi-wallet2'},
                {'title': 'تصدير بنكي', 'desc': 'تصدير ملف إكسل جاهز بفورمات البنوك المصرية لتحويل الرواتب مباشرة.', 'icon': 'bi-bank'},
                {'title': 'التأمينات والضرائب', 'desc': 'حساب حصة التأمينات الاجتماعية وضريبة كسب العمل تلقائياً حسب القانون المصري.', 'icon': 'bi-shield-check'},
                {'title': 'إقفال شهري', 'desc': 'إقفال الشهر بضغطة زر وأرشفة مسير الرواتب للرجوع إليه في أي وقت.', 'icon': 'bi-lock'},
            ],
            'price_hint': 'يبدأ من 200 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول الرواتب والأجور في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 2) التوظيف ──
        'recruitment': {
            'title': 'إدارة التوظيف',
            'subtitle': 'Applicant Tracking System (ATS)',
            'icon': 'bi-person-badge',
            'color': '#8b5cf6',
            'gradient': 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            'description': 'نظّم عملية التوظيف بالكامل من لحظة نشر الوظيفة حتى توقيع العقد وتحويل المرشح إلى موظف رسمي في النظام.',
            'benefits': [
                {'title': 'نشر الوظائف', 'desc': 'أنشئ إعلانات وظائف احترافية وشاركها مع المرشحين عبر رابط مباشر.', 'icon': 'bi-megaphone'},
                {'title': 'استقبال السير الذاتية', 'desc': 'استقبل طلبات التوظيف والسير الذاتية إلكترونياً في مكان واحد منظم.', 'icon': 'bi-inbox'},
                {'title': 'جدولة المقابلات', 'desc': 'حدد مواعيد المقابلات وأرسل إشعارات للمرشحين والمديرين تلقائياً.', 'icon': 'bi-calendar-event'},
                {'title': 'تقييم المرشحين', 'desc': 'نماذج تقييم مخصصة يملأها المدير بعد كل مقابلة لاتخاذ قرار موضوعي.', 'icon': 'bi-star-half'},
                {'title': 'تحويل لموظف', 'desc': 'بضغطة زر واحدة حوّل المرشح المقبول إلى موظف رسمي في النظام بكل بياناته.', 'icon': 'bi-person-check'},
                {'title': 'تقارير التوظيف', 'desc': 'تقارير عن عدد المتقدمين ومعدل القبول ومتوسط وقت التوظيف.', 'icon': 'bi-bar-chart-line'},
            ],
            'price_hint': 'يبدأ من 150 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول التوظيف (ATS) في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 3) تقييم الأداء ──
        'performance': {
            'title': 'تقييم الأداء',
            'subtitle': 'Performance Management & KPIs',
            'icon': 'bi-graph-up-arrow',
            'color': '#f59e0b',
            'gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            'description': 'ارتقِ بأداء فريقك من خلال نظام تقييم موضوعي يعتمد على مؤشرات أداء رئيسية (KPIs) واضحة ومحددة.',
            'benefits': [
                {'title': 'تقييم دوري', 'desc': 'إعداد دورات تقييم (شهرية / ربع سنوية / سنوية) بنماذج مخصصة لكل إدارة.', 'icon': 'bi-calendar-range'},
                {'title': 'مؤشرات أداء (KPIs)', 'desc': 'تعريف مؤشرات أداء قابلة للقياس لكل وظيفة وربطها بالتقييم.', 'icon': 'bi-speedometer'},
                {'title': 'تقييم 360 درجة', 'desc': 'تقييم من المدير + الزميل + تقييم ذاتي للحصول على صورة شاملة.', 'icon': 'bi-arrow-repeat'},
                {'title': 'ربط بالمكافآت', 'desc': 'ربط نتائج التقييم بالترقيات والمكافآت والعلاوات تلقائياً.', 'icon': 'bi-trophy'},
                {'title': 'خطط تطوير', 'desc': 'إنشاء خطط تطوير فردية للموظفين بناءً على نقاط الضعف في التقييم.', 'icon': 'bi-lightbulb'},
                {'title': 'تقارير وإحصائيات', 'desc': 'رسوم بيانية توضح أداء الإدارات والفرق ومقارنات بين الفترات.', 'icon': 'bi-pie-chart'},
            ],
            'price_hint': 'يبدأ من 150 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول تقييم الأداء في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 4) إدارة التدريب ──
        'training': {
            'title': 'إدارة التدريب والتطوير',
            'subtitle': 'Training & Development',
            'icon': 'bi-mortarboard',
            'color': '#06b6d4',
            'gradient': 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
            'description': 'تابع البرامج التدريبية لموظفيك وطوّر مهاراتهم بشكل منظم ومتابع.',
            'benefits': [
                {'title': 'خطة تدريب سنوية', 'desc': 'إعداد خطة تدريب لكل إدارة تشمل الدورات المطلوبة والميزانية.', 'icon': 'bi-journal-text'},
                {'title': 'تسجيل الدورات', 'desc': 'تسجيل كل دورة تدريبية بتفاصيلها (المدرب، المكان، المدة، التكلفة).', 'icon': 'bi-bookmark-plus'},
                {'title': 'متابعة الحضور', 'desc': 'تسجيل حضور الموظفين للدورات ومتابعة نسبة الإتمام.', 'icon': 'bi-check2-square'},
                {'title': 'الشهادات', 'desc': 'رفع شهادات التدريب وربطها بملف الموظف تلقائياً.', 'icon': 'bi-award'},
                {'title': 'تقييم أثر التدريب', 'desc': 'نماذج لتقييم مدى استفادة الموظف من الدورة التدريبية.', 'icon': 'bi-clipboard-data'},
                {'title': 'تقارير التدريب', 'desc': 'تقارير عن ميزانية التدريب وعدد الساعات التدريبية لكل موظف.', 'icon': 'bi-file-earmark-bar-graph'},
            ],
            'price_hint': 'يبدأ من 100 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول إدارة التدريب في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 5) إدارة الأصول والعهد ──
        'assets': {
            'title': 'إدارة الأصول والعهد',
            'subtitle': 'Asset & Custody Management',
            'icon': 'bi-laptop',
            'color': '#64748b',
            'gradient': 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
            'description': 'تابع أصول الشركة (لابتوبات، موبايلات، سيارات، أدوات) وربطها بالموظفين المسؤولين عنها.',
            'benefits': [
                {'title': 'سجل الأصول', 'desc': 'تسجيل كل أصل بتفاصيله (نوع، رقم تسلسلي، قيمة، تاريخ شراء).', 'icon': 'bi-box-seam'},
                {'title': 'تسليم واستلام', 'desc': 'توثيق تسليم الأصول للموظفين واستلامها عند المغادرة بمحاضر رسمية.', 'icon': 'bi-arrow-left-right'},
                {'title': 'إخلاء الطرف', 'desc': 'ربط الأصول بإخلاء الطرف — الموظف ما يقدرش يخلي طرفه إلا بعد تسليم كل العهد.', 'icon': 'bi-clipboard-check'},
                {'title': 'صيانة وتتبع', 'desc': 'جدولة صيانة الأصول وتتبع حالتها (جديد / مستخدم / يحتاج صيانة / تالف).', 'icon': 'bi-tools'},
                {'title': 'تنبيهات الضمان', 'desc': 'تنبيه قبل انتهاء ضمان الأصول أو عقود الصيانة.', 'icon': 'bi-bell'},
                {'title': 'تقارير الأصول', 'desc': 'تقارير عن قيمة الأصول وتوزيعها على الإدارات والموظفين.', 'icon': 'bi-bar-chart'},
            ],
            'price_hint': 'يبدأ من 100 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول إدارة الأصول والعهد في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 6) الربط البرمجي (API) ──
        'api': {
            'title': 'الربط البرمجي',
            'subtitle': 'API & System Integration',
            'icon': 'bi-plug',
            'color': '#ef4444',
            'gradient': 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            'description': 'اربط MotionHR مع أنظمتك الحالية (ERP، برامج محاسبية، أجهزة بصمة) عبر واجهة برمجة تطبيقات (API) آمنة.',
            'benefits': [
                {'title': 'REST API كامل', 'desc': 'واجهة برمجية تدعم قراءة وكتابة بيانات الموظفين والحضور والإجازات.', 'icon': 'bi-code-slash'},
                {'title': 'ربط مع ERP', 'desc': 'تصدير القيود المحاسبية للرواتب مباشرة لبرامج (Odoo, SAP, QuickBooks).', 'icon': 'bi-diagram-3'},
                {'title': 'أجهزة البصمة', 'desc': 'استيراد بيانات الحضور من أجهزة ZKTeco وغيرها عبر ملفات أو API.', 'icon': 'bi-fingerprint'},
                {'title': 'Webhooks', 'desc': 'إشعارات لحظية لأنظمتك الخارجية عند حدوث أي حدث (تعيين، إجازة، استقالة).', 'icon': 'bi-broadcast'},
                {'title': 'SSO / Active Directory', 'desc': 'تسجيل دخول موحد مع Microsoft 365 أو Google Workspace.', 'icon': 'bi-shield-lock'},
                {'title': 'توثيق API', 'desc': 'توثيق كامل ومفصل لكل Endpoints مع أمثلة عملية.', 'icon': 'bi-book'},
            ],
            'price_hint': 'حسب متطلبات الربط',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول الربط البرمجي (API) في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },
    }

    feature = features_meta.get(feature_code)
    if not feature:
        return redirect('dashboard')

    context = {
        'feature': feature,
        'feature_code': feature_code,
        'page_title': feature['title'],
        'sales_phone': '+201000000000',
        'sales_whatsapp': '201000000000',
        'sales_email': 'sales@motionhr.com',
    }
    return render(request, 'subscriptions/upsell_page.html', context)
'''

# نحذف الـ view القديمة ونضيف الجديدة
if "Patch 49j-Hooks v3" not in views_content:
    # نحذف القديمة لو موجودة
    import re
    pattern = re.compile(
        r'# ═+\n# Patch 49j-Hooks.*?(?=\n# ═|\nclass |\Z)',
        re.DOTALL
    )
    views_content = pattern.sub('', views_content)

    # نحذف view القديمة لو موجودة بأي شكل
    old_func_pattern = re.compile(
        r'@login_required\s*\ndef feature_upsell_page\(request.*?\n(?=@login_required|\ndef |\nclass |\Z)',
        re.DOTALL
    )
    views_content = old_func_pattern.sub('', views_content)

    views_content = views_content.rstrip() + "\n" + new_upsell_view + "\n"
    write_file(views_path, views_content)
    print("   ✅ تم تحديث feature_upsell_page")
else:
    print("   ℹ️ Hooks v3 موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Rewrite Upsell Template
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إعادة كتابة صفحة التسويق")

upsell_html = r"""{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
  .upsell-hero {
    background: {{ feature.gradient }};
    border-radius: 24px;
    color: white;
    padding: 50px 40px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .upsell-hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
    animation: rotateGlow 25s linear infinite;
  }
  @keyframes rotateGlow { 100% { transform: rotate(360deg); } }

  .hero-icon {
    width: 90px; height: 90px;
    border-radius: 22px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 2.8rem;
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 15px 30px rgba(0,0,0,0.2);
  }

  .pro-badge {
    position: absolute;
    top: 20px; right: 20px;
    background: linear-gradient(45deg, #f59e0b, #fbbf24);
    color: #000;
    padding: 6px 18px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(245,158,11,0.35);
  }

  .benefit-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }

  .benefit-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 24px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  .benefit-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.06);
  }

  .benefit-icon {
    width: 48px; height: 48px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    color: white;
    margin-bottom: 14px;
  }

  .cta-section {
    background: #0f172a;
    border-radius: 20px;
    color: white;
    padding: 40px;
    text-align: center;
  }

  .cta-btn {
    padding: 14px 36px;
    border-radius: 14px;
    font-size: 1.05rem;
    font-weight: 700;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    transition: transform 0.2s;
  }
  .cta-btn:hover { transform: scale(1.03); }

  .price-hint {
    display: inline-block;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 999px;
    padding: 6px 20px;
    font-size: .88rem;
    margin-top: 16px;
  }
</style>
{% endblock %}

{% block content %}
<div class="container" style="max-width: 920px;">

  <!-- Hero -->
  <div class="upsell-hero shadow-lg mb-5">
    <div class="pro-badge"><i class="bi bi-star-fill me-1"></i>وحدة متقدمة (Pro)</div>
    <div class="hero-icon">
      <i class="bi {{ feature.icon }}"></i>
    </div>
    <h1 class="fw-bold mb-2" style="font-size:2rem;">{{ feature.title }}</h1>
    <div class="mb-3" style="font-size:.95rem; opacity:.85;">{{ feature.subtitle }}</div>
    <p class="lead mb-0" style="color: rgba(255,255,255,0.85); max-width: 600px; margin: 0 auto; font-size:1rem;">
      {{ feature.description }}
    </p>
    <div class="price-hint">{{ feature.price_hint }}</div>
  </div>

  <!-- Benefits -->
  <div class="text-center mb-4">
    <h4 class="fw-bold">المميزات التي ستحصل عليها</h4>
    <p class="text-muted">كل ما تحتاجه شركتك في مكان واحد</p>
  </div>

  <div class="benefit-grid mb-5">
    {% for benefit in feature.benefits %}
    <div class="benefit-card">
      <div class="benefit-icon" style="background: {{ feature.gradient }};">
        <i class="bi {{ benefit.icon }}"></i>
      </div>
      <h6 class="fw-bold mb-2">{{ benefit.title }}</h6>
      <p class="text-muted small mb-0">{{ benefit.desc }}</p>
    </div>
    {% endfor %}
  </div>

  <!-- CTA -->
  <div class="cta-section mb-4">
    <h4 class="fw-bold mb-2">جاهز تطوّر شركتك؟</h4>
    <p class="mb-4" style="color:#94a3b8;">تواصل معنا الآن وفعّل هذه الوحدة في دقائق</p>

    <div class="d-flex justify-content-center gap-3 flex-wrap">
      <a href="https://wa.me/{{ sales_whatsapp }}?text={{ feature.whatsapp_text|urlencode }}"
         target="_blank"
         class="cta-btn"
         style="background:#25d366; color:white;">
        <i class="bi bi-whatsapp" style="font-size:1.3rem;"></i>
        تواصل عبر واتساب
      </a>

      <a href="tel:{{ sales_phone }}"
         class="cta-btn"
         style="background:{{ feature.color }}; color:white;">
        <i class="bi bi-telephone-fill"></i>
        اتصل بنا
      </a>

      <a href="mailto:{{ sales_email }}?subject={{ feature.title|urlencode }}"
         class="cta-btn"
         style="background:#475569; color:white;">
        <i class="bi bi-envelope-fill"></i>
        أرسل إيميل
      </a>
    </div>
  </div>

  <div class="text-center mb-4">
    <a href="{% url 'dashboard' %}" class="btn btn-outline-secondary">
      <i class="bi bi-arrow-right me-1"></i>العودة للرئيسية
    </a>
  </div>

</div>
{% endblock %}
"""
write_file("templates/subscriptions/upsell_page.html", upsell_html)

# ────────────────────────────────────────────────────────────
# Step 3: Update Sidebar — Contextual Hooks
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: تحديث القائمة الجانبية")

base_path = "templates/base/dashboard_base.html"
base_content = read_file(base_path)
if base_content is None:
    raise SystemExit("❌ dashboard_base.html غير موجود")

# حذف أي hooks قديمة
for old_marker_start, old_marker_end in [
    ("<!-- 🔒 SaaS Hooks / Upsell Modules -->", "<!-- End SaaS Hooks -->"),
    ("<!-- Hook: الرواتب تحت الموظفين -->", "<!-- End Hook: الرواتب -->"),
    ("<!-- Hook: التوظيف تحت الطلبات -->", "<!-- End Hook: التوظيف -->"),
    ("<!-- Hook: تقييم الأداء تحت التقارير -->", "<!-- End Hook: تقييم الأداء -->"),
    ("<!-- Hook: الربط البرمجي تحت الإعدادات -->", "<!-- End Hook: الربط البرمجي -->"),
]:
    if old_marker_start in base_content and old_marker_end in base_content:
        start = base_content.index(old_marker_start)
        end = base_content.index(old_marker_end) + len(old_marker_end)
        base_content = base_content[:start] + base_content[end:]

# حذف أي li.nav-item قديم فيه subscriptions:upsell
import re
base_content = re.sub(
    r'<li class="nav-item">\s*<a[^>]*subscriptions:upsell[^>]*>.*?</a>\s*</li>',
    '',
    base_content,
    flags=re.DOTALL
)

# ═══ تعريف الـ Hook HTML ═══
def make_hook(feature_code, title, icon, color):
    return f"""
        <!-- Hook-v3: {title} -->
        {{% if request.user.role == 'company_admin' %}}
        <li class="nav-item">
          <a class="nav-link d-flex align-items-center gap-2 py-2" href="{{% url 'subscriptions:upsell' '{feature_code}' %}}"
             style="color:#94a3b8; font-size:.85rem; border-right: 3px solid {color}; background: rgba(0,0,0,0.02); margin: 2px 8px; border-radius: 8px;">
            <i class="bi {icon}" style="color:{color}; font-size:.9rem;"></i>
            <span>{title}</span>
            <span class="ms-auto d-flex align-items-center gap-1">
              <i class="bi bi-lock-fill" style="color:{color}; font-size:.65rem;"></i>
              <span class="badge rounded-pill" style="background:{color}; color:#fff; font-size:.55rem; padding: 2px 6px;">Pro</span>
            </span>
          </a>
        </li>
        {{% endif %}}
        <!-- End Hook-v3: {title} -->"""

payroll_hook = make_hook('payroll', 'الرواتب والأجور', 'bi-cash-coin', '#10b981')
training_hook = make_hook('training', 'إدارة التدريب', 'bi-mortarboard', '#06b6d4')
recruitment_hook = make_hook('recruitment', 'التوظيف (ATS)', 'bi-person-badge', '#8b5cf6')
performance_hook = make_hook('performance', 'تقييم الأداء', 'bi-graph-up-arrow', '#f59e0b')
assets_hook = make_hook('assets', 'الأصول والعهد', 'bi-laptop', '#64748b')
api_hook = make_hook('api', 'الربط البرمجي (API)', 'bi-plug', '#ef4444')

# ═══ حقن الـ Hooks ═══
hooks_config = [
    # (hook_html, marker_to_search_after, description)
    (payroll_hook + training_hook, "employees:", "الرواتب + التدريب تحت الموظفين"),
    (recruitment_hook, "requests_app:", "التوظيف تحت الطلبات"),
    (performance_hook, "reports:", "تقييم الأداء تحت التقارير"),
    (assets_hook + api_hook, "companies:", "الأصول + API تحت الإعدادات"),
]

for hook_html, search_marker, desc in hooks_config:
    if f"Hook-v3: " in hook_html.split("Hook-v3: ")[1].split(" -->")[0] and f"<!-- Hook-v3: {hook_html.split('Hook-v3: ')[1].split(' -->')[0]}" in base_content:
        print(f"   ℹ️ {desc} — موجود بالفعل")
        continue

    # نبحث عن آخر ظهور للـ marker
    all_positions = [m.start() for m in re.finditer(re.escape(search_marker), base_content)]
    if all_positions:
        # ناخد آخر ظهور
        last_pos = all_positions[-1]
        # نبحث عن أقرب </li> بعد الماركر
        next_li = base_content.find("</li>", last_pos)
        if next_li != -1:
            insert_point = next_li + len("</li>")
            base_content = base_content[:insert_point] + hook_html + base_content[insert_point:]
            print(f"   ✅ {desc}")
        else:
            print(f"   ⚠️ {desc} — لم أجد </li> بعد الماركر")
    else:
        print(f"   ⚠️ {desc} — لم أجد '{search_marker}' في السايدبار")

write_file(base_path, base_content)

print("\n" + "=" * 60)
print("✅ Patch 49j-Hooks v3 اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ تم حذف كل الـ hooks القديمة
  ✅ تم إضافة 6 منتجات مجانية (ما بتحتاجش فلوس) في السايدبار:

  📋 تحت الموظفين:
     🔒 الرواتب والأجور
     🔒 إدارة التدريب

  📝 تحت الطلبات:
     🔒 التوظيف (ATS)

  📊 تحت التقارير:
     🔒 تقييم الأداء

  ⚙️ تحت الإعدادات:
     🔒 الأصول والعهد
     🔒 الربط البرمجي (API)

  ✅ كل hook يظهر فقط لـ company_admin
  ✅ كل hook لما يتدوس عليه:
     - يفتح صفحة تسويقية احترافية
     - فيها المميزات بالتفصيل
     - زرار واتساب + اتصال + إيميل
     - كل زرار فيه رسالة مجهزة

  ❌ المنتجات المدفوعة (SMS/WhatsApp/Cloud/Biometric Live)
     لم تُضف — ستُضاف لاحقاً عند توفر الميزانية

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")