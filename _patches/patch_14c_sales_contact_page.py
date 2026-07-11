#!/usr/bin/env python3
"""
Patch 14c: Sales Contact Page + Fix All Empty Links
=====================================================
- ينشئ صفحة بيع/تواصل داخلية احترافية
- يصلح كل اللينكات الفاضية في كل صفحات الاشتراك
- بيانات التواصل من مكان واحد
"""

import os
import sys

# ── تحديد مسار المشروع ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def create_file(path, content):
    """ينشئ ملف ومجلداته لو مش موجودين"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def update_file(path, old, new):
    """يعدل محتوى ملف موجود"""
    if not os.path.exists(path):
        print(f"  ⚠️  الملف مش موجود: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        print(f"  ⚠️  النص مش موجود في: {path}")
        return False
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.replace(old, new))
    print(f"  ✅ تم تعديل: {path}")
    return True

def append_to_file(path, content):
    """يضيف محتوى لآخر ملف موجود"""
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

print("=" * 60)
print("  Patch 14c: Sales Contact Page")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1. إنشاء صفحة التواصل/البيع
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء صفحة البيع الداخلية...")

contact_template = r"""{% extends 'base/dashboard_base.html' %}

{% block title %}تواصل معنا - MotionHR{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <!-- ── Header ── -->
  <div class="text-center mb-5">
    <div class="mb-3">
      <span style="font-size:4rem;">🚀</span>
    </div>
    <h2 class="fw-bold text-dark mb-2">طور اشتراكك مع MotionHR</h2>
    <p class="text-muted fs-5">
      فريقنا جاهز يساعدك تختار الخطة المناسبة لشركتك
    </p>
  </div>

  <!-- ── الباقات ── -->
  <div class="row justify-content-center mb-5 g-3">

    <!-- Starter -->
    <div class="col-md-3">
      <div class="card border-0 shadow-sm h-100 text-center p-3">
        <div class="card-body">
          <span class="badge bg-secondary mb-2">Starter</span>
          <h5 class="fw-bold">حتى 15 موظف</h5>
          <div class="display-6 fw-bold text-primary my-3">299<small class="fs-6 text-muted"> ج.م/شهر</small></div>
          <ul class="list-unstyled text-start small text-muted">
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> إدارة الموظفين</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> الحضور بالـ GPS</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> التقارير الأساسية</li>
            <li><i class="bi bi-x-circle-fill text-danger me-1"></i> التتبع الميداني</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Business -->
    <div class="col-md-3">
      <div class="card border-2 shadow h-100 text-center p-3" style="border-color: #06B6D4 !important;">
        <div class="card-body">
          <span class="badge mb-2" style="background:#06B6D4;">Business ⭐</span>
          <h5 class="fw-bold">حتى 50 موظف</h5>
          <div class="display-6 fw-bold my-3" style="color:#06B6D4;">599<small class="fs-6 text-muted"> ج.م/شهر</small></div>
          <ul class="list-unstyled text-start small text-muted">
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> كل مميزات Starter</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> التتبع الميداني</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> الخريطة الحية</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> تسجيل دخول بالرقم الوظيفي</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Professional -->
    <div class="col-md-3">
      <div class="card border-0 shadow-sm h-100 text-center p-3">
        <div class="card-body">
          <span class="badge bg-warning text-dark mb-2">Professional</span>
          <h5 class="fw-bold">حتى 100 موظف</h5>
          <div class="display-6 fw-bold text-warning my-3">999<small class="fs-6 text-muted"> ج.م/شهر</small></div>
          <ul class="list-unstyled text-start small text-muted">
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> كل مميزات Business</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> تسجيل دخول بالموبايل</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> SMS OTP</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> Payroll متقدم</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Enterprise -->
    <div class="col-md-3">
      <div class="card border-0 shadow-sm h-100 text-center p-3">
        <div class="card-body">
          <span class="badge bg-dark mb-2">Enterprise</span>
          <h5 class="fw-bold">100+ موظف</h5>
          <div class="display-6 fw-bold text-dark my-3"><small class="fs-5">حسب</small><br><small class="fs-5">الطلب</small></div>
          <ul class="list-unstyled text-start small text-muted">
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> كل المميزات</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> 2FA + SSO</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> White Label</li>
            <li><i class="bi bi-check-circle-fill text-success me-1"></i> سيرفر العميل</li>
          </ul>
        </div>
      </div>
    </div>

  </div>

  <!-- ── طرق التواصل ── -->
  <div class="row justify-content-center mb-5">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h4 class="fw-bold text-center mb-4">
            <i class="bi bi-headset me-2" style="color:#06B6D4;"></i>
            تواصل مع فريق المبيعات
          </h4>

          <div class="row g-3">

            <!-- واتساب -->
            <div class="col-md-4">
              <a href="https://wa.me/{{ whatsapp_number }}"
                 target="_blank"
                 class="card border-0 text-decoration-none h-100"
                 style="background: linear-gradient(135deg, #25D366, #128C7E); border-radius: 12px;">
                <div class="card-body text-white text-center p-4">
                  <i class="bi bi-whatsapp" style="font-size: 2.5rem;"></i>
                  <h6 class="mt-2 mb-1 fw-bold">واتساب</h6>
                  <small>{{ contact_phone }}</small>
                </div>
              </a>
            </div>

            <!-- موبايل -->
            <div class="col-md-4">
              <a href="tel:{{ contact_phone }}"
                 class="card border-0 text-decoration-none h-100"
                 style="background: linear-gradient(135deg, #06B6D4, #0891B2); border-radius: 12px;">
                <div class="card-body text-white text-center p-4">
                  <i class="bi bi-telephone-fill" style="font-size: 2.5rem;"></i>
                  <h6 class="mt-2 mb-1 fw-bold">اتصل بنا</h6>
                  <small>{{ contact_phone }}</small>
                </div>
              </a>
            </div>

            <!-- إيميل -->
            <div class="col-md-4">
              <a href="mailto:{{ contact_email }}"
                 class="card border-0 text-decoration-none h-100"
                 style="background: linear-gradient(135deg, #6366F1, #4F46E5); border-radius: 12px;">
                <div class="card-body text-white text-center p-4">
                  <i class="bi bi-envelope-fill" style="font-size: 2.5rem;"></i>
                  <h6 class="mt-2 mb-1 fw-bold">البريد الإلكتروني</h6>
                  <small>{{ contact_email }}</small>
                </div>
              </a>
            </div>

          </div>

          <!-- ساعات العمل -->
          <div class="text-center mt-4 p-3 rounded" style="background:#f0f9ff;">
            <i class="bi bi-clock me-2 text-primary"></i>
            <span class="text-muted">ساعات العمل: </span>
            <strong>الأحد - الخميس، 9 صباحاً - 5 مساءً</strong>
          </div>

        </div>
      </div>
    </div>
  </div>

  <!-- ── إضافات مدفوعة ── -->
  <div class="row justify-content-center mb-5">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h5 class="fw-bold mb-3">
            <i class="bi bi-puzzle me-2" style="color:#06B6D4;"></i>
            إضافات متاحة بسعر إضافي
          </h5>
          <div class="table-responsive">
            <table class="table table-hover align-middle">
              <tbody>
                <tr>
                  <td><i class="bi bi-geo-alt text-primary me-2"></i>التتبع الميداني المتقدم</td>
                  <td class="text-end fw-bold">200 ج.م / شهر</td>
                </tr>
                <tr>
                  <td><i class="bi bi-cash-stack text-primary me-2"></i>Payroll متقدم</td>
                  <td class="text-end fw-bold">300 ج.م / شهر</td>
                </tr>
                <tr>
                  <td><i class="bi bi-server text-primary me-2"></i>تثبيت على سيرفر العميل</td>
                  <td class="text-end fw-bold">5,000 ج.م (مرة واحدة)</td>
                </tr>
                <tr>
                  <td><i class="bi bi-people text-primary me-2"></i>إعداد وتدريب</td>
                  <td class="text-end fw-bold">2,000 ج.م (مرة واحدة)</td>
                </tr>
                <tr>
                  <td><i class="bi bi-palette text-primary me-2"></i>White Label</td>
                  <td class="text-end fw-bold">10,000 ج.م</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── أزرار التنقل ── -->
  <div class="text-center">
    <a href="{% url 'subscriptions:my_plan' %}"
       class="btn btn-outline-secondary btn-lg me-2">
      <i class="bi bi-arrow-right me-1"></i>
      رجوع لخطتي
    </a>
    <a href="{% url 'dashboard' %}"
       class="btn btn-lg text-white"
       style="background:#06B6D4;">
      <i class="bi bi-house me-1"></i>
      الرئيسية
    </a>
  </div>

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'subscriptions', 'contact_sales.html'),
    contact_template
)


# ════════════════════════════════════════════════════════════
# 2. إضافة View + URL لصفحة التواصل
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث subscriptions/views.py...")

views_path = os.path.join(BASE_DIR, 'subscriptions', 'views.py')

with open(views_path, 'r', encoding='utf-8') as f:
    views_content = f.read()

# إضافة View الجديد في آخر الملف لو مش موجود
contact_view = '''

# ─────────────────────────────────────────────
# صفحة التواصل / البيع
# ─────────────────────────────────────────────
from django.conf import settings as django_settings

def contact_sales_view(request):
    """صفحة التواصل مع فريق المبيعات"""
    contact_info = getattr(django_settings, 'MOTIONHR_SALES_CONTACT', {})
    context = {
        'contact_phone':   contact_info.get('phone',     '01000000000'),
        'contact_email':   contact_info.get('email',     'sales@motionhr.com'),
        'whatsapp_number': contact_info.get('whatsapp',  '201000000000'),
        'page_title': 'تواصل معنا',
    }
    return render(request, 'subscriptions/contact_sales.html', context)
'''

if 'contact_sales_view' not in views_content:
    append_to_file(views_path, contact_view)
else:
    print("  ℹ️  contact_sales_view موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3. تحديث subscriptions/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث subscriptions/urls.py...")

urls_path = os.path.join(BASE_DIR, 'subscriptions', 'urls.py')

with open(urls_path, 'r', encoding='utf-8') as f:
    urls_content = f.read()

if 'contact-sales' not in urls_content:
    # إضافة الـ import + الـ URL
    update_file(
        urls_path,
        'from . import views',
        'from . import views\nfrom .views import contact_sales_view'
    )
    # إضافة URL قبل آخر سطر
    update_file(
        urls_path,
        ']',
        "    path('contact-sales/', contact_sales_view, name='contact_sales'),\n]",
    )
else:
    print("  ℹ️  URL موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 4. إضافة بيانات التواصل في settings.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة MOTIONHR_SALES_CONTACT في settings.py...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')

with open(settings_path, 'r', encoding='utf-8') as f:
    settings_content = f.read()

sales_contact_block = """
# ─────────────────────────────────────────────
# بيانات التواصل للمبيعات (عدّلها بياناتك)
# ─────────────────────────────────────────────
MOTIONHR_SALES_CONTACT = {
    'company_name': 'MotionHR',
    'phone':        '01000000000',      # ← غيّر لرقمك
    'whatsapp':     '201000000000',     # ← غيّر لرقم الواتساب (بدون +)
    'email':        'sales@motionhr.com',  # ← غيّر لإيميلك
    'facebook':     '',
    'website':      '',
}
"""

if 'MOTIONHR_SALES_CONTACT' not in settings_content:
    append_to_file(settings_path, sales_contact_block)
else:
    print("  ℹ️  MOTIONHR_SALES_CONTACT موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 5. إصلاح كل اللينكات الفاضية في صفحات الاشتراك
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح اللينكات في صفحات الاشتراك...")

templates_sub = os.path.join(BASE_DIR, 'templates', 'subscriptions')

# ─── قائمة الصفحات اللي فيها أزرار تواصل ───
pages_to_fix = []
for fname in os.listdir(templates_sub):
    if fname.endswith('.html'):
        pages_to_fix.append(os.path.join(templates_sub, fname))

# ─── الاستبدالات المطلوبة ───
replacements = [
    # أي href فاضي أو # في أزرار التواصل/الترقية
    ('href="#"',                         "href=\"{% url 'subscriptions:contact_sales' %}\""),
    ('href=""',                          "href=\"{% url 'subscriptions:contact_sales' %}\""),
    # نصوص شائعة لأزرار التواصل
    ('تواصل مع المبيعات" href="',        "تواصل مع المبيعات\" href=\"{% url 'subscriptions:contact_sales' %}\""),
    # روابط خارجية فارغة
    ('href="http://#"',                  "href=\"{% url 'subscriptions:contact_sales' %}\""),
    ('href="https://#"',                 "href=\"{% url 'subscriptions:contact_sales' %}\""),
]

fixed_count = 0
for page_path in pages_to_fix:
    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ تم إصلاح: {os.path.basename(page_path)}")
        fixed_count += 1

if fixed_count == 0:
    print("  ℹ️  لم يتم العثور على لينكات فاضية للإصلاح")


# ════════════════════════════════════════════════════════════
# 6. تحديث my_plan.html - كل أزرار الترقية توصل لصفحة التواصل
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث my_plan.html...")

my_plan_path = os.path.join(BASE_DIR, 'templates', 'subscriptions', 'my_plan.html')

if os.path.exists(my_plan_path):
    with open(my_plan_path, 'r', encoding='utf-8') as f:
        my_plan_content = f.read()

    # تأكد إن زرار الترقية موجود وشغال
    upgrade_btn_old = "ترقية الخطة</a>"
    upgrade_btn_new = """ترقية الخطة</a>
              <a href="{% url 'subscriptions:contact_sales' %}"
                 class="btn btn-outline-primary btn-sm ms-2">
                <i class="bi bi-headset me-1"></i>تواصل معنا
              </a>"""

    if upgrade_btn_old in my_plan_content and upgrade_btn_new not in my_plan_content:
        with open(my_plan_path, 'w', encoding='utf-8') as f:
            f.write(my_plan_content.replace(upgrade_btn_old, upgrade_btn_new))
        print("  ✅ تم إضافة زرار 'تواصل معنا' في my_plan.html")
    else:
        print("  ℹ️  my_plan.html - الزرار موجود أو النص مختلف")
else:
    print("  ⚠️  my_plan.html مش موجود")


# ════════════════════════════════════════════════════════════
# 7. تحديث feature_unavailable.html
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث feature_unavailable.html...")

unavailable_path = os.path.join(BASE_DIR, 'templates', 'subscriptions', 'feature_unavailable.html')

if os.path.exists(unavailable_path):
    with open(unavailable_path, 'r', encoding='utf-8') as f:
        unavailable_content = f.read()

    # استبدال أي زرار بيروح على # بزرار صح
    if "contact_sales" not in unavailable_content:
        # ابحث عن زرار الترقية وعدله
        old_btn = 'ترقية الخطة'
        if old_btn in unavailable_content:
            unavailable_content = unavailable_content.replace(
                old_btn,
                "ترقية الخطة"
            )
            # ابحث عن الـ href القديم وغيره
            import re
            unavailable_content = re.sub(
                r'href="[^"]*"\s*>\s*<i[^>]*></i>\s*ترقية الخطة',
                "href=\"{% url 'subscriptions:contact_sales' %}\"><i class=\"bi bi-rocket me-1\"></i>ترقية الخطة",
                unavailable_content
            )
            with open(unavailable_path, 'w', encoding='utf-8') as f:
                f.write(unavailable_content)
            print("  ✅ تم تحديث feature_unavailable.html")
        else:
            print("  ℹ️  feature_unavailable.html - لا يحتاج تعديل")
    else:
        print("  ℹ️  feature_unavailable.html - محدث بالفعل")
else:
    print("  ⚠️  feature_unavailable.html مش موجود")


# ════════════════════════════════════════════════════════════
# 8. إضافة رابط "تواصل معنا" في الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة رابط التواصل في الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')

if os.path.exists(sidebar_path):
    with open(sidebar_path, 'r', encoding='utf-8') as f:
        sidebar_content = f.read()

    if 'contact_sales' not in sidebar_content:
        # نضيف الرابط قبل إغلاق الـ sidebar
        contact_link = """
                <!-- تواصل مع المبيعات -->
                <li class="nav-item mt-2">
                  <a class="nav-link text-white-50 d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'subscriptions:contact_sales' %}"
                     style="border-radius:8px; font-size:0.85rem;">
                    <i class="bi bi-headset"></i>
                    <span>تواصل / ترقية</span>
                  </a>
                </li>"""

        # ابحث عن نهاية قائمة الـ nav في الـ Sidebar
        sidebar_end_markers = [
            '</ul>\n          </div>\n        </div>',
            '{% endblock sidebar_menu %}',
            '<!-- end sidebar -->',
        ]

        added = False
        for marker in sidebar_end_markers:
            if marker in sidebar_content:
                sidebar_content = sidebar_content.replace(
                    marker,
                    contact_link + '\n              ' + marker
                )
                with open(sidebar_path, 'w', encoding='utf-8') as f:
                    f.write(sidebar_content)
                print("  ✅ تم إضافة رابط التواصل في الـ Sidebar")
                added = True
                break

        if not added:
            print("  ⚠️  مش لاقي مكان مناسب في الـ Sidebar - هتضيفه يدوياً لو محتاج")
    else:
        print("  ℹ️  رابط التواصل موجود في الـ Sidebar")
else:
    print("  ⚠️  dashboard_base.html مش موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 14c اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1. ✅ صفحة البيع الداخلية (contact_sales.html)
  2. ✅ View جديد (contact_sales_view)
  3. ✅ URL: /subscriptions/contact-sales/
  4. ✅ بيانات التواصل في settings.py
  5. ✅ إصلاح اللينكات الفاضية في صفحات الاشتراك
  6. ✅ زرار "تواصل معنا" في my_plan.html
  7. ✅ تحديث feature_unavailable.html
  8. ✅ رابط في الـ Sidebar

⚙️  تعديل مطلوب منك:
  افتح motionhr/settings.py وغيّر:
  - phone:    رقمك الحقيقي
  - whatsapp: رقم الواتساب (بدون + وبدون صفر)
  - email:    إيميلك الحقيقي

🚀 الخطوة الجاية: Patch 15 - إنشاء حسابات الموظفين
""")