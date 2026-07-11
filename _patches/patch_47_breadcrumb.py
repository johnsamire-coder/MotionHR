#!/usr/bin/env python3
"""
Patch 47: Breadcrumb
=====================
1) Breadcrumb في dashboard_base.html
2) Context processor أو manual breadcrumbs
3) تحديث أهم الـ views بـ breadcrumbs
"""

import os
import sys

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


print("=" * 60)
print("  Patch 47: Breadcrumb")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) dashboard_base.html — إضافة Breadcrumb
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث dashboard_base.html...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

if "breadcrumbs" not in sidebar:
    breadcrumb_html = """
  <!-- Breadcrumb -->
  {% if breadcrumbs %}
  <nav aria-label="breadcrumb" style="padding:8px 20px 0;">
    <ol class="breadcrumb mb-0" style="font-size:0.82rem;">
      <li class="breadcrumb-item">
        <a href="{% url 'dashboard' %}" style="color:#06B6D4; text-decoration:none;">
          <i class="bi bi-house-fill me-1"></i>الرئيسية
        </a>
      </li>
      {% for crumb in breadcrumbs %}
        {% if crumb.url %}
        <li class="breadcrumb-item">
          <a href="{{ crumb.url }}" style="color:#06B6D4; text-decoration:none;">{{ crumb.label }}</a>
        </li>
        {% else %}
        <li class="breadcrumb-item active text-muted" aria-current="page">{{ crumb.label }}</li>
        {% endif %}
      {% endfor %}
    </ol>
  </nav>
  {% endif %}
"""
    # نضيف بعد الـ header وقبل الـ messages
    target = """  <!-- Messages -->
  {% if messages %}"""

    if target in sidebar:
        sidebar = sidebar.replace(target, breadcrumb_html + "\n" + target)
        write_file(sidebar_path, sidebar)
        print("  ✅ تم إضافة Breadcrumb")
    else:
        # طريقة بديلة: قبل content-area
        target2 = """  <div class="content-area">"""
        if target2 in sidebar:
            sidebar = sidebar.replace(target2, breadcrumb_html + "\n" + target2)
            write_file(sidebar_path, sidebar)
            print("  ✅ تم إضافة Breadcrumb (طريقة بديلة)")
        else:
            print("  ⚠️  لم أجد مكان مناسب")
else:
    print("  ℹ️  Breadcrumb موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) Context Processor — breadcrumbs تلقائي
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء context processor...")

processor_code = '''"""
breadcrumb_processor.py
Context processor يولّد breadcrumbs تلقائي حسب الـ URL
"""


def breadcrumb_processor(request):
    """
    يولد breadcrumbs تلقائيًا من الـ URL
    ولو الـ view بعت breadcrumbs في الـ context يستخدمها بدلاً منه
    """
    path = request.path_info
    breadcrumbs = []

    # خريطة المسارات
    path_map = {
        "/employees/": "الموظفون",
        "/employees/add/": "إضافة موظف",
        "/attendance/": "الحضور",
        "/attendance/check-in/": "تسجيل الحضور",
        "/attendance/map/": "الخريطة الحية",
        "/attendance/monitor/": "متابعة الميدانيين",
        "/attendance/visits/": "الزيارات",
        "/attendance/schedule/": "جدول العمل",
        "/attendance/late-notifications/": "إشعارات التأخير",
        "/attendance/stealth-manage/": "إدارة التتبع",
        "/attendance/stealth-alerts/": "تنبيهات التتبع",
        "/attendance/my-warnings/": "إنذاراتي",
        "/leaves/": "الإجازات",
        "/leaves/add/": "طلب إجازة",
        "/leaves/types/": "أنواع الإجازات",
        "/leaves/balances/": "أرصدة الإجازات",
        "/requests/": "الطلبات",
        "/requests/add/": "طلب جديد",
        "/reports/": "التقارير",
        "/reports/attendance/": "تقرير الحضور",
        "/reports/late/": "تقرير التأخيرات",
        "/reports/leaves/": "تقرير الإجازات",
        "/reports/field/": "تقرير الميدانيين",
        "/reports/employees/": "تقرير الموظفين",
        "/companies/settings/": "إعدادات الشركة",
        "/companies/branches/": "الفروع",
        "/companies/branches/add/": "إضافة فرع",
        "/companies/departments/": "الإدارات",
        "/companies/departments/add/": "إضافة إدارة",
        "/companies/shifts/": "الشيفتات",
        "/companies/shifts/add/": "إضافة شيفت",
        "/companies/charter/": "ميثاق العمل",
        "/companies/charter/manage/": "إدارة الميثاق",
        "/companies/policies/": "السياسات والقواعد",
        "/companies/approval-flows/": "مسارات الموافقة",
        "/companies/delegations/": "التفويضات",
        "/companies/delegations/add/": "إضافة تفويض",
        "/subscriptions/my-plan/": "خطتي",
        "/subscriptions/contact-sales/": "تواصل / ترقية",
        "/accounts/profile/": "الملف الشخصي",
        "/accounts/notifications/": "الإشعارات",
        "/accounts/notifications/send/": "إرسال إشعار",
        "/accounts/login-settings/": "إعدادات الدخول",
        "/employees/my-balance/": "رصيد إجازاتي",
        "/employees/my-deductions/": "خصوماتي",
        "/search/": "البحث",
        "/password-change/": "تغيير كلمة المرور",
    }

    # نبني الـ breadcrumbs من المسار
    # نبص على الـ sections
    section_map = {
        "/employees/": {"label": "الموظفون", "url": "/employees/"},
        "/attendance/": {"label": "الحضور", "url": "/attendance/"},
        "/leaves/": {"label": "الإجازات", "url": "/leaves/"},
        "/requests/": {"label": "الطلبات", "url": "/requests/"},
        "/reports/": {"label": "التقارير", "url": "/reports/"},
        "/companies/": {"label": "الشركة", "url": "/companies/settings/"},
        "/subscriptions/": {"label": "الاشتراك", "url": "/subscriptions/my-plan/"},
        "/accounts/": {"label": "حسابي", "url": "/accounts/profile/"},
    }

    # لو الصفحة هي Dashboard ذاتها
    if path == "/dashboard/":
        return {"breadcrumbs": []}

    # نبحث عن القسم
    for section_path, section_info in section_map.items():
        if path.startswith(section_path):
            # لو القسم مش هو الصفحة نفسها
            if path != section_path:
                breadcrumbs.append({
                    "label": section_info["label"],
                    "url": section_info["url"]
                })

            # لو الصفحة معروفة
            page_label = path_map.get(path)
            if page_label and page_label != section_info["label"]:
                breadcrumbs.append({
                    "label": page_label,
                    "url": None
                })
            elif page_label:
                breadcrumbs.append({
                    "label": page_label,
                    "url": None
                })
            break

    # لو مفيش match
    if not breadcrumbs:
        label = path_map.get(path)
        if label:
            breadcrumbs.append({"label": label, "url": None})

    return {"breadcrumbs": breadcrumbs}
'''

processor_path = os.path.join(BASE_DIR, "core", "breadcrumb_processor.py")
write_file(processor_path, processor_code)
print("  ✅ تم إنشاء breadcrumb_processor.py")


# ════════════════════════════════════════════════════════════
# 3) settings.py — إضافة context processor
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings.py...")

settings_path = os.path.join(BASE_DIR, "motionhr", "settings.py")
settings = read_file(settings_path)

if "breadcrumb_processor" not in settings:
    old = "'django.template.context_processors.request',"
    new = "'django.template.context_processors.request',\n                'core.breadcrumb_processor.breadcrumb_processor',"

    if old in settings:
        settings = settings.replace(old, new)
        write_file(settings_path, settings)
        print("  ✅ تم إضافة breadcrumb context processor")
    else:
        print("  ⚠️  لم أجد context_processors في settings")
        print("  هتحتاج تضيفه يدوي في TEMPLATES → OPTIONS → context_processors")
else:
    print("  ℹ️  breadcrumb_processor موجود بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 47 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Breadcrumb في dashboard_base.html
  2. ✅ Context processor تلقائي
  3. ✅ خريطة مسارات لكل الصفحات
  4. ✅ مسجل في settings.py

كيف يشتغل:
  - كل صفحة تلقائي يظهر لها breadcrumb
  - الرئيسية ← القسم ← الصفحة الحالية
  - بدون ما نعدل أي view!

جرب:
  - /employees/
  - /attendance/schedule/
  - /companies/policies/
  - /reports/attendance/
  - /requests/add/
""")