#!/usr/bin/env python3
"""
Patch 33b: Visit Guard + Visit Page UI Fix
==========================================
1) قفل صفحة الزيارة لغير الموظف الميداني
2) ربط /visits/add/ بـ guarded view
3) إصلاح UI صفحة الزيارة والخريطة
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
print("  Patch 33b: Visit Guard + UI Fix")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) attendance/views.py
# إضافة wrapper يحمي صفحة الزيارة
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/views.py...")

views_path = os.path.join(BASE_DIR, "attendance", "views.py")
views = read_file(views_path)

guard_code = '''

# ════════════════════════════════════════════════════════════
# Guarded Visit Add Page (للميداني فقط)
# ════════════════════════════════════════════════════════════
@login_required
def field_visit_add_page(request):
    """
    الموظف العادي ما يفتحش صفحة الزيارة
    الموظف الميداني فقط هو اللي يقدر يفتحها
    المديرين / HR / company admin يقدروا يفتحوها
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from employees.models import Employee

    # الموظف العادي
    if getattr(request.user, "role", "") == "employee":
        employee = Employee.objects.filter(user=request.user).first()

        if not employee:
            messages.error(request, "لم يتم ربط حسابك بأي موظف")
            return redirect("dashboard")

        if not getattr(employee, "is_field_worker", False):
            messages.warning(request, "تسجيل الزيارات الميدانية متاح للموظفين الميدانيين فقط")
            return redirect("attendance:check_in")

    # لو ميداني أو مدير/HR/صاحب شركة
    return visit_add(request)
'''

if "def field_visit_add_page" not in views:
    views += guard_code
    write_file(views_path, views)
    print("  ✅ تم إضافة field_visit_add_page")
else:
    print("  ℹ️  field_visit_add_page موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) attendance/urls.py
# ربط visits/add/ بالـ guarded view
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/urls.py...")

urls_path = os.path.join(BASE_DIR, "attendance", "urls.py")
urls = read_file(urls_path)

old_line = "path('visits/add/', views.visit_add, name='visit_add'),"
new_line = "path('visits/add/', views.field_visit_add_page, name='visit_add'),"

if old_line in urls:
    urls = urls.replace(old_line, new_line)
    write_file(urls_path, urls)
    print("  ✅ تم ربط visits/add/ بالـ guarded view")
else:
    if "field_visit_add_page" in urls:
        print("  ℹ️  الرابط محدث بالفعل")
    else:
        print("  ⚠️  لم أجد السطر المتوقع في attendance/urls.py")


# ════════════════════════════════════════════════════════════
# 3) إصلاح visit_form.html
# تبسيط UI + منع الخريطة من تكسير الصفحة
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث templates/attendance/visit_form.html...")

visit_form_path = os.path.join(BASE_DIR, "templates", "attendance", "visit_form.html")

if os.path.exists(visit_form_path):
    visit_form = read_file(visit_form_path)

    # تأكد إن extends أول سطر
    if "{% load custom_filters %}" in visit_form and "{% extends" in visit_form:
        lines = visit_form.split("\n")
        load_idx = None
        extends_idx = None
        for i, line in enumerate(lines):
            if "{% load custom_filters %}" in line and load_idx is None:
                load_idx = i
            if "{% extends" in line and extends_idx is None:
                extends_idx = i
        if load_idx is not None and extends_idx is not None and load_idx < extends_idx:
            load_line = lines.pop(load_idx)
            for i, line in enumerate(lines):
                if "{% extends" in line:
                    lines.insert(i + 1, load_line)
                    break
            visit_form = "\n".join(lines)

    css_block = """
{% block extra_css %}
<style>
  .visit-page-wrap {
    max-width: 760px;
    margin: 0 auto;
  }

  /* الخريطة ما تخرجش من مكانها */
  #map, [id="map"], [id*="map"] {
    width: 100% !important;
    max-width: 100% !important;
    min-height: 260px !important;
    border-radius: 14px !important;
    overflow: hidden !important;
  }

  .leaflet-container {
    width: 100% !important;
    max-width: 100% !important;
    min-height: 260px !important;
    border-radius: 14px !important;
  }

  .map-container, .map-section {
    position: relative !important;
    top: auto !important;
    left: auto !important;
    right: auto !important;
    overflow: hidden !important;
    border-radius: 14px !important;
    margin-top: 12px;
  }

  /* على الموبايل */
  @media (max-width: 768px) {
    #map, .leaflet-container, .map-container, .map-section {
      min-height: 220px !important;
    }
  }

  /* للموظف الميداني: نبسط العرض ونخلي الخريطة ثانوية */
  {% if request.user.role == 'employee' %}
  .visit-page-wrap .map-section,
  .visit-page-wrap .map-container {
    margin-top: 16px;
  }
  {% endif %}
</style>
{% endblock %}
"""

    if "{% block extra_css %}" not in visit_form:
        if "{% block content %}" in visit_form:
            visit_form = visit_form.replace("{% block content %}", css_block + "\n{% block content %}", 1)
        else:
            visit_form = css_block + "\n" + visit_form

    # لف المحتوى الأساسي في wrapper لو مش موجود
    if "visit-page-wrap" not in visit_form:
        if "{% block content %}" in visit_form and "{% endblock %}" in visit_form:
            visit_form = visit_form.replace(
                "{% block content %}",
                "{% block content %}\n<div class=\"container-fluid py-4\"><div class=\"visit-page-wrap\">",
                1
            )
            # آخر endblock للمحتوى
            visit_form = visit_form.replace(
                "{% endblock %}",
                "</div></div>\n{% endblock %}",
                1
            )

    # ملاحظة واضحة للموظف
    if "سيتم تحديد موقعك تلقائيًا" not in visit_form:
        note_html = """
{% if request.user.role == 'employee' %}
<div class="alert alert-info border-0 shadow-sm mb-3">
  <i class="bi bi-info-circle-fill me-2"></i>
  سيتم تحديد موقعك تلقائيًا عند تسجيل الزيارة.
</div>
{% endif %}
"""
        if "{% block content %}" in visit_form:
            visit_form = visit_form.replace("{% block content %}", "{% block content %}\n" + note_html, 1)

    write_file(visit_form_path, visit_form)
    print("  ✅ تم إصلاح visit_form.html")
else:
    print("  ⚠️  visit_form.html غير موجود")


# ════════════════════════════════════════════════════════════
# 4) ملاحظة تأكيد على زر الزيارة في check_in.html
# ════════════════════════════════════════════════════════════
print("\n🔧 تأكيد شرط زر الزيارة في check_in.html...")

checkin_path = os.path.join(BASE_DIR, "templates", "attendance", "check_in.html")
if os.path.exists(checkin_path):
    checkin = read_file(checkin_path)

    old_visit_cond = "{% if employee.is_field_worker %}"
    new_visit_cond = "{% if employee and employee.is_field_worker %}"

    if old_visit_cond in checkin:
        checkin = checkin.replace(old_visit_cond, new_visit_cond)
        write_file(checkin_path, checkin)
        print("  ✅ تم تشديد شرط ظهور زر الزيارة")
    else:
        if new_visit_cond in checkin:
            print("  ℹ️  شرط زر الزيارة مضبوط بالفعل")
        else:
            print("  ⚠️  لم أجد شرط زر الزيارة المتوقع")
else:
    print("  ⚠️  check_in.html غير موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 33b اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  1. ✅ غير الميداني ما يفتحش صفحة الزيارة
  2. ✅ /visits/add/ محمية للميداني فقط
  3. ✅ شرط ظهور زر الزيارة أصبح أدق
  4. ✅ visit_form UI والخريطة اتظبطوا

جرب دلوقتي:
  1. emp10003
     - ما يشوفش زر الزيارة
     - ولو فتح /attendance/visits/add/ يدويًا يترفض

  2. emp10004
     - يشوف زر الزيارة
     - صفحة الزيارة شكلها ثابت
""")