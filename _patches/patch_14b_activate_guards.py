"""
============================================================
Patch 14b: تفعيل Feature Guards على Sidebar والـ Views
============================================================
- إخفاء الروابط المقفلة من Sidebar
- Feature Guards على كل View مهم
- Redirect تلقائي للصفحة "الميزة غير متاحة"
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# Sidebar محدث مع Feature Guards
# ═══════════════════════════════════════════════════════════

NEW_SIDEBAR = '''<!-- Sidebar -->
<aside class="sidebar" id="sidebar">
    
    <!-- Logo -->
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">
            <i class="bi bi-people-fill"></i>
        </div>
        <div class="sidebar-logo-text">
            <h5>MotionHR</h5>
            <small>إدارة الموارد البشرية</small>
        </div>
    </div>
    
    <!-- Menu -->
    <div class="sidebar-menu">
        
        <div class="menu-section">
            <div class="menu-title">الرئيسية</div>
            
            <a href="{% url 'dashboard' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
                <i class="bi bi-grid-1x2-fill"></i>
                <span>لوحة التحكم</span>
            </a>
        </div>
        
        <div class="menu-section">
            <div class="menu-title">الموارد البشرية</div>
            
            {% has_feature 'employees_management' as can_employees %}
            {% if can_employees %}
            <a href="{% url 'employees:list' %}" 
               class="menu-item {% if 'employees' in request.resolver_match.namespace %}active{% endif %}">
                <i class="bi bi-people-fill"></i>
                <span>الموظفون</span>
            </a>
            {% endif %}
            
            {% has_feature 'companies_management' as can_companies %}
            {% if can_companies %}
            <a href="#" class="menu-item">
                <i class="bi bi-building"></i>
                <span>الشركات والفروع</span>
            </a>
            {% endif %}
            
            {% has_feature 'departments_management' as can_depts %}
            {% if can_depts %}
            <a href="#" class="menu-item">
                <i class="bi bi-diagram-3"></i>
                <span>الإدارات</span>
            </a>
            {% endif %}
        </div>
        
        {% has_feature 'attendance_gps' as can_attendance %}
        {% has_feature 'attendance_records' as can_records %}
        {% has_feature 'continuous_tracking' as can_tracking %}
        {% has_feature 'live_map' as can_map %}
        {% has_feature 'location_visits' as can_visits %}
        {% has_feature 'shifts_management' as can_shifts %}
        
        {% if can_attendance or can_records or can_tracking or can_map or can_visits or can_shifts %}
        <div class="menu-section">
            <div class="menu-title">الحضور والتتبع</div>
            
            {% if can_records %}
            <a href="{% url 'attendance:list' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'list' and 'attendance' in request.path %}active{% endif %}">
                <i class="bi bi-clock-history"></i>
                <span>سجلات الحضور</span>
            </a>
            {% endif %}
            
            {% if can_attendance %}
            <a href="{% url 'attendance:check_in' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'check_in' %}active{% endif %}">
                <i class="bi bi-fingerprint"></i>
                <span>تسجيل حضور</span>
            </a>
            {% endif %}
            
            {% if can_tracking %}
            <a href="{% url 'attendance:tracking' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'tracking' %}active{% endif %}">
                <i class="bi bi-broadcast"></i>
                <span>التتبع المستمر</span>
            </a>
            
            <a href="{% url 'attendance:monitor' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'monitor' %}active{% endif %}">
                <i class="bi bi-people-fill"></i>
                <span>متابعة الميدانيين</span>
                <span class="menu-badge">HR</span>
            </a>
            {% endif %}
            
            {% if can_map %}
            <a href="{% url 'attendance:live_map' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'live_map' %}active{% endif %}">
                <i class="bi bi-geo-alt-fill"></i>
                <span>خريطة التتبع</span>
                <span class="menu-badge">Live</span>
            </a>
            {% endif %}
            
            {% if can_visits %}
            <a href="{% url 'attendance:visits' %}" 
               class="menu-item {% if request.resolver_match.url_name == 'visits' %}active{% endif %}">
                <i class="bi bi-pin-map-fill"></i>
                <span>الزيارات</span>
            </a>
            {% endif %}
            
            {% if can_shifts %}
            <a href="#" class="menu-item">
                <i class="bi bi-calendar-week"></i>
                <span>الشيفتات</span>
            </a>
            {% endif %}
        </div>
        {% endif %}
        
        {% has_feature 'leaves_management' as can_leaves %}
        {% if can_leaves %}
        <div class="menu-section">
            <div class="menu-title">الطلبات</div>
            
            <a href="#" class="menu-item">
                <i class="bi bi-calendar-check"></i>
                <span>الإجازات</span>
            </a>
            
            <a href="#" class="menu-item">
                <i class="bi bi-file-earmark-text"></i>
                <span>الطلبات</span>
            </a>
        </div>
        {% endif %}
        
        {% has_feature 'payroll_basic' as can_payroll %}
        {% if can_payroll %}
        <div class="menu-section">
            <div class="menu-title">المرتبات</div>
            
            <a href="#" class="menu-item">
                <i class="bi bi-cash-stack"></i>
                <span>المرتبات</span>
            </a>
        </div>
        {% endif %}
        
        {% has_feature 'basic_reports' as can_reports %}
        {% if can_reports %}
        <div class="menu-section">
            <div class="menu-title">التقارير</div>
            
            <a href="#" class="menu-item">
                <i class="bi bi-graph-up"></i>
                <span>التقارير</span>
            </a>
        </div>
        {% endif %}
        
        {% if user.role == 'super_admin' %}
        <div class="menu-section">
            <div class="menu-title">إدارة النظام</div>
            
            <a href="{% url 'subscriptions:admin_dashboard' %}" 
               class="menu-item {% if 'sub-admin' in request.path and 'my-subscription' not in request.path and 'upgrade' not in request.path %}active{% endif %}">
                <i class="bi bi-briefcase-fill"></i>
                <span>إدارة الاشتراكات</span>
                <span class="menu-badge">Admin</span>
            </a>
        </div>
        {% endif %}
        
        <div class="menu-section">
            <div class="menu-title">الإعدادات</div>
            
            {% if user.role != 'super_admin' %}
            <a href="{% url 'subscriptions:my_subscription' %}" 
               class="menu-item {% if 'my-subscription' in request.path or 'upgrade' in request.path %}active{% endif %}">
                <i class="bi bi-award-fill"></i>
                <span>خطتي</span>
            </a>
            {% endif %}
            
            <a href="/admin/" class="menu-item">
                <i class="bi bi-gear-fill"></i>
                <span>لوحة الإدارة</span>
            </a>
        </div>
        
    </div>
</aside>'''


# ═══════════════════════════════════════════════════════════
# تحديث dashboard_base.html
# ═══════════════════════════════════════════════════════════

def update_sidebar():
    """تحديث Sidebar بالكامل مع Feature Guards"""
    path = BASE_DIR / 'templates' / 'base' / 'dashboard_base.html'
    
    if not path.exists():
        return False, "الملف مش موجود"
    
    content = path.read_text(encoding='utf-8')
    
    # نتأكد إن load subscription_tags موجود
    if '{% load subscription_tags %}' not in content:
        # نضيفه بعد {% extends 'base/base.html' %}
        old_extends = "{% extends 'base/base.html' %}"
        new_extends = "{% extends 'base/base.html' %}\n{% load subscription_tags %}"
        
        if old_extends in content:
            content = content.replace(old_extends, new_extends)
    
    # نستبدل الـ Sidebar بالكامل
    # ندور على بداية <aside class="sidebar" ونهاية </aside>
    start_marker = '<!-- Sidebar -->'
    end_marker = '</aside>'
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        # مفيش تعليق، ندور على <aside
        start_marker = '<aside class="sidebar"'
        start_idx = content.find(start_marker)
    
    if start_idx == -1:
        return False, "لم يتم العثور على Sidebar"
    
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        return False, "لم يتم العثور على نهاية Sidebar"
    
    end_idx += len(end_marker)
    
    # نستبدل
    new_content = content[:start_idx] + NEW_SIDEBAR + content[end_idx:]
    
    path.write_text(new_content, encoding='utf-8')
    return True, "تم تحديث Sidebar مع Feature Guards"


# ═══════════════════════════════════════════════════════════
# Feature Guards على Attendance Views
# ═══════════════════════════════════════════════════════════

def add_guards_to_attendance():
    """إضافة feature_required decorators على attendance views"""
    path = BASE_DIR / 'attendance' / 'views.py'
    
    if not path.exists():
        return False, "ملف views.py مش موجود"
    
    content = path.read_text(encoding='utf-8')
    
    if 'from subscriptions.helpers import feature_required' in content:
        return True, "Guards موجودة بالفعل"
    
    # نضيف import
    old_imports = "from .models import Shift, EmployeeShift, Attendance, LocationLog, LocationCheckIn"
    new_imports = """from subscriptions.helpers import feature_required
from .models import Shift, EmployeeShift, Attendance, LocationLog, LocationCheckIn"""
    
    if old_imports in content:
        content = content.replace(old_imports, new_imports)
    
    # نضيف decorators على الـ views
    replacements = [
        (
            '@login_required\ndef attendance_list(request):',
            '@login_required\n@feature_required(\'attendance_records\')\ndef attendance_list(request):'
        ),
        (
            '@login_required\ndef check_in_page(request):',
            '@login_required\n@feature_required(\'attendance_gps\')\ndef check_in_page(request):'
        ),
        (
            '@login_required\ndef tracking_page(request):',
            '@login_required\n@feature_required(\'continuous_tracking\')\ndef tracking_page(request):'
        ),
        (
            '@login_required\ndef field_employees_monitor(request):',
            '@login_required\n@feature_required(\'continuous_tracking\')\ndef field_employees_monitor(request):'
        ),
        (
            '@login_required\ndef live_map(request):',
            '@login_required\n@feature_required(\'live_map\')\ndef live_map(request):'
        ),
        (
            '@login_required\ndef visits_list(request):',
            '@login_required\n@feature_required(\'location_visits\')\ndef visits_list(request):'
        ),
        (
            '@login_required\ndef visit_add(request):',
            '@login_required\n@feature_required(\'location_visits\')\ndef visit_add(request):'
        ),
    ]
    
    changed = 0
    for old, new in replacements:
        if old in content and '@feature_required' not in content[content.find(old)-100:content.find(old)]:
            content = content.replace(old, new, 1)
            changed += 1
    
    path.write_text(content, encoding='utf-8')
    return True, f"تم إضافة Guards على {changed} views"


# ═══════════════════════════════════════════════════════════
# Feature Guards على Employees Views
# ═══════════════════════════════════════════════════════════

def add_guards_to_employees():
    """إضافة feature_required على employees views"""
    path = BASE_DIR / 'employees' / 'views.py'
    
    if not path.exists():
        return False, "ملف views.py مش موجود"
    
    content = path.read_text(encoding='utf-8')
    
    if 'from subscriptions.helpers import feature_required' in content:
        return True, "Guards موجودة بالفعل"
    
    # نضيف import
    old_imports = "from core.permissions import ("
    new_imports = "from subscriptions.helpers import feature_required\nfrom core.permissions import ("
    
    if old_imports in content:
        content = content.replace(old_imports, new_imports)
    
    # نضيف decorator على employee_list فقط
    replacements = [
        (
            '@login_required\ndef employee_list(request):',
            '@login_required\n@feature_required(\'employees_management\')\ndef employee_list(request):'
        ),
    ]
    
    changed = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new, 1)
            changed += 1
    
    path.write_text(content, encoding='utf-8')
    return True, f"تم إضافة Guards على {changed} views"


# ═══════════════════════════════════════════════════════════
# تحديث helpers للتوجيه لصفحة feature_locked
# ═══════════════════════════════════════════════════════════

def update_helpers():
    """تحديث helpers للتوجيه لصفحة feature_locked مع feature key"""
    path = BASE_DIR / 'subscriptions' / 'helpers.py'
    
    if not path.exists():
        return False, "ملف helpers.py مش موجود"
    
    content = path.read_text(encoding='utf-8')
    
    if "reverse('subscriptions:feature_locked')" in content:
        return True, "التعديل موجود بالفعل"
    
    # نستبدل feature_required
    old_func = '''def feature_required(feature_key):
    """
    Decorator للـ Views
    يتحقق إن الميزة متاحة في اشتراك الشركة
    
    مثال:
        @feature_required('continuous_tracking')
        def tracking_page(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Super Admin دايماً يوصل
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            
            # التحقق من الاشتراك
            if not getattr(request, 'subscription_valid', False):
                messages.warning(request, 'اشتراكك منتهي. يرجى التجديد للوصول لهذه الميزة')
                return redirect('subscription_upgrade')
            
            # التحقق من الميزة
            if feature_key not in getattr(request, 'subscription_features', set()):
                messages.info(
                    request,
                    f'هذه الميزة غير متاحة في خطتك الحالية. قم بترقية الخطة للاستفادة منها'
                )
                return redirect('subscription_upgrade')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator'''
    
    new_func = '''def feature_required(feature_key):
    """
    Decorator للـ Views
    يتحقق إن الميزة متاحة في اشتراك الشركة
    
    مثال:
        @feature_required('continuous_tracking')
        def tracking_page(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Super Admin دايماً يوصل
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            
            # التحقق من الاشتراك
            if not getattr(request, 'subscription_valid', False):
                messages.warning(request, 'اشتراكك منتهي. يرجى التجديد للوصول لهذه الميزة')
                return redirect(f'/sub-admin/upgrade/')
            
            # التحقق من الميزة
            if feature_key not in getattr(request, 'subscription_features', set()):
                return redirect(f'/sub-admin/feature-locked/?feature={feature_key}')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator'''
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        path.write_text(content, encoding='utf-8')
        return True, "تم تحديث helpers"
    
    return False, "لم يتم العثور على الـ function"


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Patch 14b: Activate Feature Guards")
    print("=" * 60)
    print()
    
    tasks = [
        ('تحديث Sidebar مع Feature Guards', update_sidebar),
        ('تحديث Helpers', update_helpers),
        ('Guards على Attendance', add_guards_to_attendance),
        ('Guards على Employees', add_guards_to_employees),
    ]
    
    for name, func in tasks:
        try:
            success, message = func()
            icon = "[OK]" if success else "[X]"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  [X] {name}: {e}")
    
    print()
    print("=" * 60)
    print("[SUCCESS] Feature Guards activated!")
    print("=" * 60)
    print()
    print("Now:")
    print("  1. Super Admin sees EVERYTHING")
    print("  2. Company Admin sees only features in their plan")
    print("  3. Sidebar hides locked features")
    print("  4. Trying locked features -> feature_locked page")
    print()
    print("Test with a company that has 'Starter' plan:")
    print("  - No continuous tracking")
    print("  - No live map")
    print("  - No visits")
    print()


if __name__ == '__main__':
    main()