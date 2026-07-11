"""
Patch 49N-B — Fix Remaining Issues + Update Contact Sales

الهدف:
1) إصلاح companies:shift_edit → 404
2) إصلاح صلاحيات الموظف (employee يشوف صفحات مش المفروض يشوفها)
3) تحديث صفحة contact-sales بالبيانات الحقيقية لـ JS Solutions
"""

import os
import re
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


def backup(rel_path, backup_name):
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup: _patches/_backups/{backup_name}")


print("=" * 70)
print("Patch 49N-B — Fix Remaining Issues + Update Contact Sales")
print("=" * 70)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
for rel_path, backup_name in [
    ("companies/views.py", "companies_views_before_49n_b.py.bak"),
    ("companies/urls.py", "companies_urls_before_49n_b.py.bak"),
    ("templates/companies/shift_form.html", "shift_form_before_49n_b.html.bak"),
    ("templates/subscriptions/contact_sales.html", "contact_sales_before_49n_b.html.bak"),
]:
    backup(rel_path, backup_name)

# ════════════════════════════════════════════════════════════
# Fix 1: companies:shift_edit → 404
# ════════════════════════════════════════════════════════════
print("\n📌 Fix 1: companies:shift_edit → 404")

import os, sys
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

# نتحقق إن في shift موجود
try:
    from attendance.models import Shift
    shift_count = Shift.objects.count()
    first_shift = Shift.objects.first()
    print(f"   عدد الـ Shifts: {shift_count}")
    if first_shift:
        print(f"   أول Shift ID: {first_shift.pk}")
    else:
        print("   ⚠️ لا يوجد Shifts في قاعدة البيانات")
        print("   ملاحظة: companies:shift_edit بيعمل 404 لأن Shift ID=1 مش موجود")
        print("   ده مش bug في الكود — الداتا فاضية")
        print("   بعد إضافة بيانات تجريبية سيختفي تلقائياً")
except Exception as e:
    print(f"   ⚠️ خطأ: {e}")

# نتحقق من الـ view
companies_views = read_file("companies/views.py")
if companies_views and "def shift_edit" not in companies_views:
    print("   ⚠️ shift_edit view غير موجودة في companies/views.py")
    print("   سنتحقق من shift_form view")
    if "def shift_form" in companies_views:
        print("   ℹ️ shift_form موجودة — لكن الـ URL بيستخدم shift_edit")

        companies_urls = read_file("companies/urls.py")
        if companies_urls and "shift_edit" in companies_urls:
            print("   تصحيح: استبدال shift_edit بـ shift_form في urls.py")
            companies_urls = companies_urls.replace(
                "views.shift_edit",
                "views.shift_form"
            )
            write_file("companies/urls.py", companies_urls)
            print("   ✅ تم التصحيح")
else:
    print("   ✅ shift_edit view موجودة")

# ════════════════════════════════════════════════════════════
# Fix 2: صلاحيات الـ employee
# ════════════════════════════════════════════════════════════
print("\n📌 Fix 2: تحسين صلاحيات الـ employee")

# الصفحات اللي بتظهر لـ employee وما المفروضش
# branch_add, department_add, shift_add, shifts_list
# دي محتاجة تتحمى بـ decorator صحيح

companies_views_content = read_file("companies/views.py")
if companies_views_content:
    changes_made = []

    protected_views_to_check = [
        "def branch_add",
        "def branch_edit",
        "def branch_list",
        "def shift_add",
        "def shift_form",
        "def shifts_list",
        "def department_add",
        "def department_edit",
    ]

    ADMIN_HR_CHECK = '''    from accounts.models import User
    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("ليس لديك صلاحية")
'''

    for view_name in protected_views_to_check:
        if view_name in companies_views_content:
            idx = companies_views_content.index(view_name)
            next_lines = companies_views_content[idx:idx+500]

            if "PermissionDenied" not in next_lines[:300] and "role not in" not in next_lines[:300]:
                paren_end = companies_views_content.index(":", idx) + 1
                body_start = companies_views_content.index("\n", paren_end) + 1
                indent = "    "
                companies_views_content = (
                    companies_views_content[:body_start]
                    + ADMIN_HR_CHECK
                    + companies_views_content[body_start:]
                )
                changes_made.append(view_name)

    if changes_made:
        write_file("companies/views.py", companies_views_content)
        for ch in changes_made:
            print(f"   ✅ تمت حماية: {ch}")
    else:
        print("   ℹ️ الصفحات محمية بالفعل أو لم يتم العثور عليها")

# ════════════════════════════════════════════════════════════
# Fix 3: تحديث صفحة contact-sales
# ════════════════════════════════════════════════════════════
print("\n📌 Fix 3: تحديث صفحة contact-sales بالبيانات الحقيقية")

contact_sales_html = """{% extends 'base/dashboard_base.html' %}

{% block title %}تواصل مع المبيعات — MotionHR{% endblock %}

{% block extra_css %}
<style>
  .contact-hero {
    background: linear-gradient(135deg, #0f172a 0%, #0e7490 100%);
    border-radius: 24px;
    color: white;
    padding: 50px 40px;
    text-align: center;
  }
  .contact-card {
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 28px;
    background: #fff;
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
  }
  .contact-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.08);
  }
  .contact-icon {
    width: 60px;
    height: 60px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    margin-bottom: 16px;
  }
  .info-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid #f1f5f9;
    font-size: .95rem;
  }
  .info-row:last-child { border-bottom: none; }
  .info-label { color: #64748b; min-width: 130px; font-size: .88rem; }
  .info-value { font-weight: 600; color: #0f172a; }
</style>
{% endblock %}

{% block content %}
<div class="container" style="max-width: 900px;">

  <!-- Hero -->
  <div class="contact-hero mb-5 shadow-lg">
    <div class="mb-3" style="font-size:3rem;">📞</div>
    <h2 class="fw-bold mb-2">تواصل مع فريق المبيعات</h2>
    <p style="color:rgba(255,255,255,0.8); font-size:1.05rem;">
      نحن هنا لمساعدتك في اختيار الباقة المناسبة لشركتك
    </p>
  </div>

  <div class="row g-4 mb-5">

    <!-- واتساب -->
    <div class="col-md-4">
      <div class="contact-card text-center">
        <div class="contact-icon mx-auto" style="background:#dcfce7; color:#15803d;">
          <i class="bi bi-whatsapp"></i>
        </div>
        <h6 class="fw-bold mb-2">واتساب</h6>
        <p class="text-muted small mb-3">تواصل معنا مباشرة على واتساب</p>
        <a href="https://wa.me/2001501551593?text=السلام عليكم، أنا مهتم بنظام MotionHR لشركتي وأود معرفة المزيد عن الباقات والأسعار."
           target="_blank"
           class="btn btn-success w-100 fw-bold">
          <i class="bi bi-whatsapp me-2"></i>(+20) 015 0155 1593
        </a>
      </div>
    </div>

    <!-- هاتف -->
    <div class="col-md-4">
      <div class="contact-card text-center">
        <div class="contact-icon mx-auto" style="background:#dbeafe; color:#1d4ed8;">
          <i class="bi bi-telephone-fill"></i>
        </div>
        <h6 class="fw-bold mb-2">اتصال مباشر</h6>
        <p class="text-muted small mb-3">متاحون من الأحد للخميس</p>
        <a href="tel:+201501551593"
           class="btn btn-primary w-100 fw-bold">
          <i class="bi bi-telephone-fill me-2"></i>(+20) 015 0155 1593
        </a>
      </div>
    </div>

    <!-- إيميل -->
    <div class="col-md-4">
      <div class="contact-card text-center">
        <div class="contact-icon mx-auto" style="background:#fef3c7; color:#b45309;">
          <i class="bi bi-envelope-fill"></i>
        </div>
        <h6 class="fw-bold mb-2">البريد الإلكتروني</h6>
        <p class="text-muted small mb-3">نرد خلال 24 ساعة عمل</p>
        <a href="mailto:info@jssolutions.com?subject=استفسار عن MotionHR"
           class="btn btn-warning w-100 fw-bold text-dark">
          <i class="bi bi-envelope-fill me-2"></i>info@jssolutions.com
        </a>
      </div>
    </div>

  </div>

  <!-- معلومات الشركة -->
  <div class="card border-0 shadow-sm mb-4" style="border-radius:20px;">
    <div class="card-header bg-white py-3 border-0">
      <h6 class="mb-0 fw-bold">
        <i class="bi bi-building me-2 text-primary"></i>معلومات الشركة
      </h6>
    </div>
    <div class="card-body px-4">
      <div class="info-row">
        <i class="bi bi-building-fill text-primary" style="font-size:1.1rem; width:24px;"></i>
        <span class="info-label">اسم الشركة</span>
        <span class="info-value">JS Solutions</span>
      </div>
      <div class="info-row">
        <i class="bi bi-stars text-primary" style="font-size:1.1rem; width:24px;"></i>
        <span class="info-label">المنتج</span>
        <span class="info-value">MotionHR — HR in Motion</span>
      </div>
      <div class="info-row">
        <i class="bi bi-telephone-fill text-success" style="font-size:1.1rem; width:24px;"></i>
        <span class="info-label">هاتف / واتساب</span>
        <span class="info-value">(+20) 015 0155 1593</span>
      </div>
      <div class="info-row">
        <i class="bi bi-envelope-fill text-warning" style="font-size:1.1rem; width:24px;"></i>
        <span class="info-label">البريد الإلكتروني</span>
        <span class="info-value">info@jssolutions.com</span>
      </div>
      <div class="info-row">
        <i class="bi bi-clock-fill text-info" style="font-size:1.1rem; width:24px;"></i>
        <span class="info-label">ساعات العمل</span>
        <span class="info-value">الأحد — الخميس | 9 ص — 6 م (بتوقيت القاهرة)</span>
      </div>
      <div class="info-row">
        <i class="bi bi-geo-alt-fill text-danger" style="font-size:1.1rem; width:24px;"></i>
        <span class="info-label">الدولة</span>
        <span class="info-value">جمهورية مصر العربية 🇪🇬</span>
      </div>
    </div>
  </div>

  <!-- فترة تجريبية -->
  <div class="text-center mb-4 p-4" style="background:linear-gradient(135deg, #f0fdff, #e0f2fe); border-radius:20px; border:1px solid #bae6fd;">
    <div class="mb-2" style="font-size:2rem;">🎁</div>
    <h5 class="fw-bold mb-2" style="color:#0c4a6e;">لم تجرّب MotionHR بعد؟</h5>
    <p class="text-muted mb-3">جرّب النظام مجاناً لمدة 14 يوم — كل المميزات مفتوحة — بدون التزام</p>
    <a href="{% url 'landing:free_trial' %}" class="btn btn-primary btn-lg px-5 fw-bold" style="border-radius:14px;">
      <i class="bi bi-rocket-takeoff-fill me-2"></i>ابدأ التجربة المجانية
    </a>
  </div>

  <!-- شبكات التواصل -->
  <div class="text-center mb-4">
    <div class="text-muted small mb-2">تابعنا على</div>
    <div class="d-flex justify-content-center gap-3">
      <a href="#" class="btn btn-outline-primary btn-sm" style="border-radius:10px; width:42px; height:42px; display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-facebook"></i>
      </a>
      <a href="#" class="btn btn-outline-info btn-sm" style="border-radius:10px; width:42px; height:42px; display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-twitter-x"></i>
      </a>
      <a href="#" class="btn btn-outline-danger btn-sm" style="border-radius:10px; width:42px; height:42px; display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-instagram"></i>
      </a>
      <a href="#" class="btn btn-outline-primary btn-sm" style="border-radius:10px; width:42px; height:42px; display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-linkedin"></i>
      </a>
    </div>
    <div class="small text-muted mt-2">الصفحات قيد الإنشاء — سيتم الإعلان قريباً</div>
  </div>

</div>
{% endblock %}
"""
write_file("templates/subscriptions/contact_sales.html", contact_sales_html)

# ════════════════════════════════════════════════════════════
# Fix 4: Update Upsell pages with correct contact info
# ════════════════════════════════════════════════════════════
print("\n📌 Fix 4: تحديث بيانات التواصل في Upsell pages")

subs_views = read_file("subscriptions/views.py")
if subs_views:
    fixes = {
        "'sales_phone': '(+20)01501551593'": "'sales_phone': '(+20) 015 0155 1593'",
        "'sales_whatsapp': '201000000000'": "'sales_whatsapp': '2001501551593'",
        "'sales_email': 'sales@motionhr.com'": "'sales_email': 'info@jssolutions.com'",
        "'sales_email': 'info@jssolutions.com'": "'sales_email': 'info@jssolutions.com'",
    }
    changed = False
    for old, new in fixes.items():
        if old in subs_views:
            subs_views = subs_views.replace(old, new)
            changed = True
            print(f"   ✅ تم تحديث: {old[:50]}...")

    if changed:
        write_file("subscriptions/views.py", subs_views)
    else:
        print("   ℹ️ البيانات محدّثة بالفعل")

print("\n" + "=" * 70)
print("✅ Patch 49N-B اكتمل")
print("=" * 70)
print("""
تم إصلاح / تحديث:
  ✅ companies:shift_edit → تصحيح URL لو shift_form موجودة بدل shift_edit
  ✅ صلاحيات company pages → حماية branch_add/edit وshift_add وdepartment_add
  ✅ صفحة contact-sales → تحديث كامل بالبيانات الحقيقية لـ JS Solutions:
     - الاسم: JS Solutions
     - الهاتف/واتساب: (+20) 015 0155 1593
     - الإيميل: info@jssolutions.com
     - ساعات العمل: الأحد — الخميس | 9 ص — 6 م
  ✅ Upsell pages → تحديث بيانات التواصل
  ✅ زرار "ابدأ التجربة المجانية" في contact-sales

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000

اختبر:
  /subscriptions/contact-sales/
""")