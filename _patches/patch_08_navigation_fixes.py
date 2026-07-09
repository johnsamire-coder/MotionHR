"""
============================================================
Patch 08: إصلاحات التنقل
============================================================
- إضافة زرار "رجوع للـ Dashboard" في كل الصفحات
- إصلاح روابط Quick Actions
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# إصلاح روابط الـ Dashboard
# ═══════════════════════════════════════════════════════════

def fix_dashboard_links():
    """إصلاح روابط Quick Actions في الـ Dashboard"""
    template_path = BASE_DIR / 'templates' / 'dashboard' / 'index.html'
    
    if not template_path.exists():
        return False, "ملف dashboard/index.html مش موجود"
    
    content = template_path.read_text(encoding='utf-8')
    
    # نتأكد من الروابط الصحيحة
    replacements = [
        ('href="/employees/add/"', 'href="{% url \'employees:add\' %}"'),
        ('href="/attendance/check-in/"', 'href="{% url \'attendance:check_in\' %}"'),
        ('href="/attendance/monitor/"', 'href="{% url \'attendance:monitor\' %}"'),
        ('href="/attendance/live-map/"', 'href="{% url \'attendance:live_map\' %}"'),
        ('href="/attendance/"', 'href="{% url \'attendance:list\' %}"'),
        ('href="/employees/"', 'href="{% url \'employees:list\' %}"'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    template_path.write_text(content, encoding='utf-8')
    return True, "تم إصلاح روابط الـ Dashboard"


# ═══════════════════════════════════════════════════════════
# إضافة زرار الرجوع في صفحة تسجيل الحضور
# ═══════════════════════════════════════════════════════════

def add_back_button_checkin():
    """إضافة زرار رجوع في صفحة تسجيل الحضور"""
    template_path = BASE_DIR / 'templates' / 'attendance' / 'check_in.html'
    
    if not template_path.exists():
        return False, "ملف check_in.html مش موجود"
    
    content = template_path.read_text(encoding='utf-8')
    
    if 'رجوع للرئيسية' in content:
        return True, "زرار الرجوع موجود بالفعل"
    
    # نضيف زرار الرجوع في بداية المحتوى
    old = '{% block dashboard_content %}\n\n<div class="row justify-content-center">'
    new = '''{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للرئيسية
    </a>
</div>

<div class="row justify-content-center">'''
    
    if old not in content:
        return False, "لم يتم العثور على النقطة المناسبة"
    
    content = content.replace(old, new)
    template_path.write_text(content, encoding='utf-8')
    
    return True, "تم إضافة زرار الرجوع"


# ═══════════════════════════════════════════════════════════
# إضافة زرار الرجوع في فورم الموظف
# ═══════════════════════════════════════════════════════════

def fix_employee_form_back_button():
    """إصلاح زرار الرجوع في فورم الموظف ليرجع للـ Dashboard"""
    template_path = BASE_DIR / 'templates' / 'employees' / 'form.html'
    
    if not template_path.exists():
        return False, "ملف form.html مش موجود"
    
    content = template_path.read_text(encoding='utf-8')
    
    # نغير زرار الرجوع ليعطي خيارين
    old = '''<div class="mb-3">
    <a href="{% if is_edit %}{% url 'employees:detail' employee.pk %}{% else %}{% url 'employees:list' %}{% endif %}" 
       class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع
    </a>
</div>'''
    
    new = '''<div class="mb-3 d-flex gap-2 flex-wrap">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-primary">
        <i class="bi bi-house-fill"></i>
        الرئيسية
    </a>
    <a href="{% url 'employees:list' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-people-fill"></i>
        قائمة الموظفين
    </a>
    {% if is_edit %}
    <a href="{% url 'employees:detail' employee.pk %}" class="btn btn-sm btn-outline-info">
        <i class="bi bi-eye-fill"></i>
        عرض الموظف
    </a>
    {% endif %}
</div>'''
    
    if old not in content:
        return False, "لم يتم العثور على زرار الرجوع"
    
    content = content.replace(old, new)
    template_path.write_text(content, encoding='utf-8')
    
    return True, "تم إصلاح زرار الرجوع في الفورم"


# ═══════════════════════════════════════════════════════════
# إضافة زرار الرجوع في صفحة تفاصيل الموظف
# ═══════════════════════════════════════════════════════════

def fix_employee_detail_back():
    """إضافة زرار الرئيسية في صفحة تفاصيل الموظف"""
    template_path = BASE_DIR / 'templates' / 'employees' / 'detail.html'
    
    if not template_path.exists():
        return False, "ملف detail.html مش موجود"
    
    content = template_path.read_text(encoding='utf-8')
    
    if 'الرئيسية' in content and 'dashboard' in content:
        return True, "الأزرار موجودة بالفعل"
    
    old = '''<div class="mb-3">
    <a href="{% url 'employees:list' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        الرجوع للقائمة
    </a>
</div>'''
    
    new = '''<div class="mb-3 d-flex gap-2 flex-wrap">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-primary">
        <i class="bi bi-house-fill"></i>
        الرئيسية
    </a>
    <a href="{% url 'employees:list' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-people-fill"></i>
        قائمة الموظفين
    </a>
</div>'''
    
    if old not in content:
        return False, "لم يتم العثور على زرار الرجوع"
    
    content = content.replace(old, new)
    template_path.write_text(content, encoding='utf-8')
    
    return True, "تم إصلاح صفحة تفاصيل الموظف"


# ═══════════════════════════════════════════════════════════
# إضافة زرار رجوع للصفحات التانية
# ═══════════════════════════════════════════════════════════

def add_back_button_to_page(template_relative_path, page_name):
    """إضافة زرار رجوع لأي صفحة"""
    template_path = BASE_DIR / template_relative_path
    
    if not template_path.exists():
        return False, f"ملف {page_name} مش موجود"
    
    content = template_path.read_text(encoding='utf-8')
    
    if 'الرئيسية' in content and 'dashboard' in content:
        return True, f"الزرار موجود في {page_name}"
    
    # نضيف بعد {% block dashboard_content %}
    old = '{% block dashboard_content %}\n'
    new = '''{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للرئيسية
    </a>
</div>
'''
    
    if old not in content:
        return False, f"لم يتم العثور على المكان في {page_name}"
    
    # نضيف مرة واحدة فقط في أول ظهور
    content = content.replace(old, new, 1)
    template_path.write_text(content, encoding='utf-8')
    
    return True, f"تم إضافة زرار الرجوع في {page_name}"


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🔧 Patch 08: إصلاحات التنقل")
    print("=" * 60)
    print()
    
    tasks = [
        ('Dashboard Links', fix_dashboard_links),
        ('صفحة تسجيل الحضور', add_back_button_checkin),
        ('فورم إضافة/تعديل موظف', fix_employee_form_back_button),
        ('صفحة تفاصيل الموظف', fix_employee_detail_back),
    ]
    
    for name, func in tasks:
        try:
            success, message = func()
            icon = "✅" if success else "⚠️"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    # الصفحات التانية
    print()
    print("📄 إضافة زرار الرجوع للصفحات الأخرى...")
    print("-" * 60)
    
    pages = [
        ('templates/attendance/list.html', 'سجلات الحضور'),
        ('templates/attendance/visits.html', 'الزيارات'),
        ('templates/attendance/tracking.html', 'التتبع المستمر'),
        ('templates/attendance/monitor.html', 'متابعة الميدانيين'),
        ('templates/attendance/live_map.html', 'الخريطة الحية'),
    ]
    
    for path, name in pages:
        try:
            success, message = add_back_button_to_page(path, name)
            icon = "✅" if success else "⚠️"
            print(f"  {icon} {message}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()