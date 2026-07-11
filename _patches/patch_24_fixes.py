#!/usr/bin/env python3
"""
Patch 24: إصلاح الأخطاء من الـ Simulation
===========================================
1. إصلاح التقارير (TemplateSyntaxError - period==)
2. إصلاح subscriptions/my-plan (ImportError)
3. إصلاح subscriptions/views.py كله
4. إصلاح getattr filter في الشيفتات
5. إصلاح روابط sub-admin القديمة
"""

import os, sys, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

print("=" * 60)
print("  Patch 24: Bug Fixes from Simulation")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إصلاح التقارير - period== → period ==
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح التقارير (TemplateSyntaxError)...")

report_templates = [
    'templates/reports/attendance_report.html',
    'templates/reports/late_report.html',
    'templates/reports/leave_report.html',
    'templates/reports/field_report.html',
]

for tmpl_path in report_templates:
    full_path = os.path.join(BASE_DIR, tmpl_path)
    if not os.path.exists(full_path):
        print(f"  ⚠️  مش موجود: {tmpl_path}")
        continue

    content = read_file(full_path)
    original = content

    # إصلاح period=='value' → period == 'value'
    content = re.sub(r"period=='(\w+)'", r"period == '\1'", content)
    content = re.sub(r'period=="(\w+)"', r'period == "\1"', content)

    # إصلاح status=='value' → status == 'value'
    content = re.sub(r"status=='(\w+)'", r"status == '\1'", content)

    # إصلاح أي مقارنة ملتصقة في الـ if
    content = re.sub(r"(\w+)==('[\w]+')", r"\1 == \2", content)
    content = re.sub(r"(\w+)==(\"[\w]+\")", r'\1 == \2', content)

    if content != original:
        write_file(full_path, content)
    else:
        print(f"  ℹ️  لا يحتاج تعديل: {tmpl_path}")


# ════════════════════════════════════════════════════════════
# 2. إصلاح subscriptions/views.py - my_plan_view
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح subscriptions/views.py...")

subs_views_path = os.path.join(BASE_DIR, 'subscriptions', 'views.py')
subs_views = read_file(subs_views_path)

# استبدال الـ import القديم
old_import = "from .models import Subscription, Plan"
new_import = "from .models import CompanySubscription, SubscriptionPlan"

if old_import in subs_views:
    subs_views = subs_views.replace(old_import, new_import)
    write_file(subs_views_path, subs_views)
    print("  ✅ تم إصلاح import في subscriptions/views.py")

# إصلاح my_plan_view كامل
my_plan_view_new = '''

# ─────────────────────────────────────────────
# صفحة خطتي
# ─────────────────────────────────────────────
@login_required
def my_plan_view(request):
    """صفحة خطتي - تفاصيل الاشتراك الحالي"""
    from .models import CompanySubscription, SubscriptionPlan

    subscription    = None
    active_features = []

    if request.user.company:
        subscription = CompanySubscription.objects.filter(
            company=request.user.company,
            status__in=['active', 'trial']
        ).select_related('plan').first()

    # قائمة الميزات مع أسمائها العربية
    features_list = [
        ('employee_management',    'إدارة الموظفين'),
        ('attendance_tracking',    'تتبع الحضور'),
        ('gps_attendance',         'حضور GPS'),
        ('field_tracking',         'التتبع الميداني'),
        ('live_map',               'الخريطة الحية'),
        ('location_visits',        'تسجيل الزيارات'),
        ('reports_basic',          'التقارير الأساسية'),
        ('reports_advanced',       'التقارير المتقدمة'),
        ('excel_export',           'تصدير Excel'),
        ('pdf_export',             'تصدير PDF'),
        ('login_by_employee_code', 'دخول بالرقم الوظيفي'),
        ('login_by_phone',         'دخول بالموبايل'),
        ('leave_management',       'إدارة الإجازات'),
        ('multi_branch',           'فروع متعددة'),
        ('payroll_basic',          'مرتبات أساسي'),
    ]

    # حساب عدد الموظفين
    current_employees = 0
    if request.user.company:
        try:
            from employees.models import Employee
            current_employees = Employee.objects.filter(
                company=request.user.company,
                status='active'
            ).count()
        except Exception:
            pass

    context = {
        'subscription':      subscription,
        'active_features':   active_features,
        'features_list':     features_list,
        'current_employees': current_employees,
        'page_title':        'خطتي',
    }
    return render(request, 'subscriptions/my_plan.html', context)
'''

# نحذف الـ my_plan_view القديم ونضيف الجديد
subs_views = read_file(subs_views_path)

# نشيل الـ my_plan_view القديم لو موجود
if 'def my_plan_view' in subs_views:
    # نستخدم regex لحذف الـ function القديمة
    pattern = r'\n# ─+\n# صفحة خطتي\n# ─+\n@login_required\ndef my_plan_view\(request\):.*?(?=\n# ═|\n@login_required|\Z)'
    subs_views = re.sub(pattern, '', subs_views, flags=re.DOTALL)
    subs_views += my_plan_view_new
    write_file(subs_views_path, subs_views)
    print("  ✅ تم إصلاح my_plan_view")
else:
    subs_views += my_plan_view_new
    write_file(subs_views_path, subs_views)
    print("  ✅ تم إضافة my_plan_view")


# ════════════════════════════════════════════════════════════
# 3. إصلاح my_plan.html - إزالة الـ getattr
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح templates/subscriptions/my_plan.html...")

my_plan_template = r"""{% extends 'base/dashboard_base.html' %}

{% block title %}خطتي - MotionHR{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <!-- Header -->
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-star-fill me-2" style="color:#06B6D4;"></i>
        خطتي
      </h4>
      <p class="text-muted mb-0">تفاصيل اشتراكك الحالي</p>
    </div>
    <a href="{% url 'subscriptions:contact_sales' %}"
       class="btn text-white"
       style="background:#06B6D4;">
      <i class="bi bi-rocket me-1"></i>
      ترقية الخطة
    </a>
  </div>

  {% if subscription %}

  <!-- بطاقة الخطة -->
  <div class="row g-4 mb-4">

    <div class="col-lg-4">
      <div class="card border-0 shadow-sm h-100"
           style="border-right: 4px solid #06B6D4 !important;">
        <div class="card-body p-4">
          <div class="d-flex align-items-center mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center me-3"
                 style="width:50px;height:50px;background:#e0f7fa;">
              <i class="bi bi-patch-check-fill fs-4" style="color:#06B6D4;"></i>
            </div>
            <div>
              <h6 class="mb-0 text-muted">الخطة الحالية</h6>
              <h5 class="fw-bold mb-0">
                {% if subscription.plan.name_ar %}
                  {{ subscription.plan.name_ar }}
                {% else %}
                  {{ subscription.plan.name_en|default:"غير محدد" }}
                {% endif %}
              </h5>
            </div>
          </div>
          <span class="badge fs-6 px-3 py-2
            {% if subscription.status == 'active' %}bg-success
            {% elif subscription.status == 'trial' %}bg-warning text-dark
            {% elif subscription.status == 'expired' %}bg-danger
            {% else %}bg-secondary{% endif %}">
            {% if subscription.status == 'active' %}✅ نشط
            {% elif subscription.status == 'trial' %}🔄 تجريبي
            {% elif subscription.status == 'expired' %}❌ منتهي
            {% else %}{{ subscription.status }}{% endif %}
          </span>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <h6 class="text-muted mb-3">
            <i class="bi bi-calendar3 me-2"></i>تفاصيل الاشتراك
          </h6>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-muted">تاريخ البداية</span>
            <strong>{{ subscription.start_date|date:"d/m/Y" }}</strong>
          </div>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-muted">تاريخ الانتهاء</span>
            <strong>{{ subscription.end_date|date:"d/m/Y" }}</strong>
          </div>
          <div class="d-flex justify-content-between">
            <span class="text-muted">دورة الفوترة</span>
            <strong>
              {% if subscription.billing_cycle == 'monthly' %}شهري
              {% elif subscription.billing_cycle == 'yearly' %}سنوي
              {% else %}{{ subscription.billing_cycle }}{% endif %}
            </strong>
          </div>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <h6 class="text-muted mb-3">
            <i class="bi bi-people me-2"></i>الموظفون
          </h6>
          <div class="text-center py-2">
            <div class="display-5 fw-bold" style="color:#06B6D4;">
              {{ current_employees }}
            </div>
            <div class="text-muted">موظف نشط</div>
            <div class="mt-2 text-muted small">
              الحد الأقصى:
              <strong>{{ subscription.plan.max_employees }}</strong>
            </div>
          </div>
          {% if subscription.plan.max_employees %}
          <div class="progress mt-3" style="height:8px;">
            <div class="progress-bar bg-success"
                 style="width: {% widthratio current_employees subscription.plan.max_employees 100 %}%">
            </div>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

  </div>

  <!-- الميزات -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
      <h5 class="fw-bold mb-0">
        <i class="bi bi-grid-3x3-gap me-2" style="color:#06B6D4;"></i>
        مميزات خطتك
      </h5>
    </div>
    <div class="card-body p-4">
      <div class="row g-3">
        {% for feature_key, feature_name in features_list %}
        <div class="col-md-4 col-lg-3">
          <div class="d-flex align-items-center p-2 rounded bg-light">
            <i class="bi bi-check-circle-fill text-success me-2"></i>
            <span class="small">{{ feature_name }}</span>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  {% else %}
  <!-- مفيش اشتراك -->
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-bag-x" style="font-size:4rem; color:#06B6D4;"></i>
      <h4 class="mt-3 fw-bold">لا يوجد اشتراك نشط</h4>
      <p class="text-muted">تواصل معنا للحصول على اشتراكك</p>
      <a href="{% url 'subscriptions:contact_sales' %}"
         class="btn btn-lg text-white mt-2"
         style="background:#06B6D4;">
        <i class="bi bi-headset me-2"></i>
        تواصل مع فريق المبيعات
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'subscriptions', 'my_plan.html'),
    my_plan_template
)


# ════════════════════════════════════════════════════════════
# 4. إصلاح shift_form.html - إزالة getattr filter
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح templates/companies/shift_form.html...")

shift_form_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'companies:shifts_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">{{ page_title }}</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  اسم الشيفت <span class="text-danger">*</span>
                </label>
                <input type="text" name="name" class="form-control"
                       value="{{ shift.name|default:'' }}" required
                       placeholder="مثال: صباحي، مسائي...">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">النوع</label>
                <select name="shift_type" class="form-select">
                  <option value="fixed"
                    {% if shift.shift_type == 'fixed' %}selected
                    {% elif not shift %}selected{% endif %}>ثابت</option>
                  <option value="flexible"
                    {% if shift.shift_type == 'flexible' %}selected{% endif %}>مرن</option>
                  <option value="rotating"
                    {% if shift.shift_type == 'rotating' %}selected{% endif %}>متناوب</option>
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">وقت البداية</label>
                <input type="time" name="start_time" class="form-control"
                       value="{% if shift %}{{ shift.start_time|time:'H:i' }}{% else %}08:00{% endif %}">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">وقت النهاية</label>
                <input type="time" name="end_time" class="form-control"
                       value="{% if shift %}{{ shift.end_time|time:'H:i' }}{% else %}17:00{% endif %}">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">فترة السماح (دقيقة)</label>
                <input type="number" name="grace_period" class="form-control"
                       value="{{ shift.grace_period|default:15 }}"
                       min="0" max="60">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">وقت الاستراحة (دقيقة)</label>
                <input type="number" name="break_duration" class="form-control"
                       value="{{ shift.break_duration|default:60 }}"
                       min="0" max="180">
              </div>

              <!-- أيام العمل -->
              <div class="col-12">
                <label class="form-label fw-semibold small">أيام العمل</label>
                <div class="d-flex flex-wrap gap-3 mt-2">

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_sunday" id="work_sunday"
                           {% if shift.work_sunday %}checked{% elif not shift %}checked{% endif %}>
                    <label class="form-check-label" for="work_sunday">الأحد</label>
                  </div>

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_monday" id="work_monday"
                           {% if shift.work_monday %}checked{% elif not shift %}checked{% endif %}>
                    <label class="form-check-label" for="work_monday">الاثنين</label>
                  </div>

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_tuesday" id="work_tuesday"
                           {% if shift.work_tuesday %}checked{% elif not shift %}checked{% endif %}>
                    <label class="form-check-label" for="work_tuesday">الثلاثاء</label>
                  </div>

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_wednesday" id="work_wednesday"
                           {% if shift.work_wednesday %}checked{% elif not shift %}checked{% endif %}>
                    <label class="form-check-label" for="work_wednesday">الأربعاء</label>
                  </div>

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_thursday" id="work_thursday"
                           {% if shift.work_thursday %}checked{% elif not shift %}checked{% endif %}>
                    <label class="form-check-label" for="work_thursday">الخميس</label>
                  </div>

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_friday" id="work_friday"
                           {% if shift.work_friday %}checked{% endif %}>
                    <label class="form-check-label" for="work_friday">الجمعة</label>
                  </div>

                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="work_saturday" id="work_saturday"
                           {% if shift.work_saturday %}checked{% endif %}>
                    <label class="form-check-label" for="work_saturday">السبت</label>
                  </div>

                </div>
              </div>

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit"
                      class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة الشيفت{% else %}حفظ التغييرات{% endif %}
              </button>
              <a href="{% url 'companies:shifts_list' %}"
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
    os.path.join(BASE_DIR, 'templates', 'companies', 'shift_form.html'),
    shift_form_template
)


# ════════════════════════════════════════════════════════════
# 5. إصلاح department_form.html - خيار "إدارة رئيسية"
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح templates/companies/department_form.html...")

dept_form_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'companies:departments_list' %}"
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
                  الاسم (عربي) <span class="text-danger">*</span>
                </label>
                <input type="text" name="name_ar" class="form-control"
                       value="{{ dept.name_ar|default:'' }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الاسم (إنجليزي)</label>
                <input type="text" name="name_en" class="form-control"
                       value="{{ dept.name_en|default:'' }}" dir="ltr">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الكود</label>
                <input type="text" name="code" class="form-control"
                       value="{{ dept.code|default:'' }}" dir="ltr"
                       placeholder="مثال: HR, FIN, IT">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الإدارة الأم</label>
                <select name="parent" class="form-select">
                  <option value="">
                    ── إدارة رئيسية (بدون إدارة أم) ──
                  </option>
                  {% for d in departments %}
                  <option value="{{ d.pk }}"
                    {% if dept.parent and dept.parent.pk == d.pk %}selected{% endif %}>
                    {{ d.name_ar }}
                  </option>
                  {% endfor %}
                </select>
                <div class="form-text text-muted">
                  <i class="bi bi-info-circle me-1"></i>
                  اتركه فاضي لو هذا قسم رئيسي
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">الوصف</label>
                <textarea name="description" class="form-control" rows="3">{{ dept.description|default:'' }}</textarea>
              </div>

              {% if action == 'edit' %}
              <div class="col-12">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox"
                         name="is_active" id="isActive"
                         {% if dept.is_active %}checked{% endif %}
                         style="width:2.5rem;height:1.25rem;">
                  <label class="form-check-label fw-semibold" for="isActive">
                    الإدارة نشطة
                  </label>
                </div>
              </div>
              {% endif %}

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit"
                      class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة{% else %}حفظ{% endif %}
              </button>
              <a href="{% url 'companies:departments_list' %}"
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
    os.path.join(BASE_DIR, 'templates', 'companies', 'department_form.html'),
    dept_form_template
)


# ════════════════════════════════════════════════════════════
# 6. إصلاح روابط sub-admin القديمة في الـ templates
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح روابط sub-admin القديمة...")

import glob

template_files = glob.glob(
    os.path.join(BASE_DIR, 'templates', '**', '*.html'),
    recursive=True
)

fixed_count = 0
for tmpl_path in template_files:
    content = read_file(tmpl_path)
    original = content

    # استبدال /sub-admin/ بـ /subscriptions/
    content = content.replace('/sub-admin/', '/subscriptions/')
    content = content.replace("'sub-admin'", "'subscriptions'")
    content = content.replace('"sub-admin"', '"subscriptions"')

    # إصلاح upgrade URL
    content = content.replace(
        "{% url 'subscriptions:upgrade' %}",
        "{% url 'subscriptions:contact_sales' %}"
    )
    content = content.replace(
        "{% url 'subscriptions:upgrade_plan' %}",
        "{% url 'subscriptions:contact_sales' %}"
    )

    if content != original:
        write_file(tmpl_path, content)
        fixed_count += 1

print(f"  ✅ تم إصلاح {fixed_count} ملف")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 24 اكتمل!")
print("=" * 60)
print("""
📋 اللي اتصلح:
  1. ✅ التقارير - TemplateSyntaxError (period==)
  2. ✅ my_plan.html - صفحة خطتي جديدة
  3. ✅ subscriptions/views.py - my_plan_view
  4. ✅ shift_form.html - بدون getattr
  5. ✅ department_form.html - خيار إدارة رئيسية واضح
  6. ✅ روابط sub-admin القديمة

🚀 شغّل السيرفر وجرب:
  /reports/attendance/
  /subscriptions/my-plan/
  /companies/shifts/add/
  /companies/departments/add/
""")