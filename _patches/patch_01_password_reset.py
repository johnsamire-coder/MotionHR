"""
============================================================
Patch 01: Password Reset + Change Password
============================================================
هذا السكريبت ينشئ كل الملفات المطلوبة لنظام استعادة وتغيير كلمة المرور

للتشغيل:
    python _patches/patch_01_password_reset.py

============================================================
"""

import os
import sys
from pathlib import Path

# جذر المشروع
BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# الملفات اللي هننشئها
# ═══════════════════════════════════════════════════════════

FILES = {
    # ────────────────────────────────────────
    # 1. صفحة نسيت كلمة المرور
    # ────────────────────────────────────────
    'templates/accounts/password_reset.html': '''{% extends 'base/base.html' %}

{% block title %}استعادة كلمة المرور{% endblock %}

{% block content %}
<div class="min-vh-100 d-flex align-items-center justify-content-center py-5" 
     style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%);">
    
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5 col-xl-4">
                
                <div class="text-center mb-4">
                    <div class="d-inline-flex align-items-center justify-content-center bg-white rounded-circle mb-3" 
                         style="width: 80px; height: 80px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
                        <i class="bi bi-key-fill" style="font-size: 2.5rem; color: #06B6D4;"></i>
                    </div>
                    <h2 class="text-white fw-bold mb-1">استعادة كلمة المرور</h2>
                    <p class="text-white-50">أدخل بريدك الإلكتروني</p>
                </div>
                
                <div class="card shadow-lg border-0">
                    <div class="card-body p-4 p-md-5">
                        
                        <p class="text-muted mb-4">
                            سنرسل لك رابط لإعادة تعيين كلمة المرور
                        </p>
                        
                        <form method="post">
                            {% csrf_token %}
                            
                            <div class="mb-3">
                                <label for="id_email" class="form-label fw-semibold">
                                    <i class="bi bi-envelope"></i> البريد الإلكتروني
                                </label>
                                <input type="email" 
                                       name="email"
                                       id="id_email"
                                       class="form-control form-control-lg" 
                                       placeholder="example@email.com"
                                       required 
                                       autofocus>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-lg w-100 fw-semibold">
                                <i class="bi bi-send ms-1"></i>
                                إرسال الرابط
                            </button>
                            
                            <div class="text-center mt-3">
                                <a href="{% url 'login' %}" class="text-decoration-none small">
                                    <i class="bi bi-arrow-right"></i>
                                    الرجوع لتسجيل الدخول
                                </a>
                            </div>
                        </form>
                        
                    </div>
                </div>
                
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',

    # ────────────────────────────────────────
    # 2. صفحة "تم الإرسال"
    # ────────────────────────────────────────
    'templates/accounts/password_reset_done.html': '''{% extends 'base/base.html' %}

{% block title %}تم الإرسال{% endblock %}

{% block content %}
<div class="min-vh-100 d-flex align-items-center justify-content-center py-5" 
     style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%);">
    
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                
                <div class="card shadow-lg border-0">
                    <div class="card-body p-5 text-center">
                        
                        <div class="mb-4">
                            <div class="d-inline-flex align-items-center justify-content-center rounded-circle mb-3" 
                                 style="width: 100px; height: 100px; background: rgba(16, 185, 129, 0.1);">
                                <i class="bi bi-check-circle-fill text-success" style="font-size: 4rem;"></i>
                            </div>
                        </div>
                        
                        <h3 class="fw-bold mb-3">تم الإرسال بنجاح ✅</h3>
                        
                        <p class="text-muted mb-4">
                            تم إرسال رابط استعادة كلمة المرور إلى بريدك الإلكتروني.
                            <br>
                            من فضلك افتح بريدك واضغط على الرابط.
                        </p>
                        
                        <div class="alert alert-info small">
                            <i class="bi bi-info-circle"></i>
                            لم يصلك البريد؟ تأكد من مجلد الـ Spam
                        </div>
                        
                        <a href="{% url 'login' %}" class="btn btn-primary">
                            <i class="bi bi-arrow-right"></i>
                            العودة لتسجيل الدخول
                        </a>
                        
                    </div>
                </div>
                
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',

    # ────────────────────────────────────────
    # 3. صفحة كلمة مرور جديدة
    # ────────────────────────────────────────
    'templates/accounts/password_reset_confirm.html': '''{% extends 'base/base.html' %}

{% block title %}كلمة مرور جديدة{% endblock %}

{% block content %}
<div class="min-vh-100 d-flex align-items-center justify-content-center py-5" 
     style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%);">
    
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                
                <div class="text-center mb-4">
                    <div class="d-inline-flex align-items-center justify-content-center bg-white rounded-circle mb-3" 
                         style="width: 80px; height: 80px;">
                        <i class="bi bi-shield-lock-fill" style="font-size: 2.5rem; color: #06B6D4;"></i>
                    </div>
                    <h2 class="text-white fw-bold">كلمة مرور جديدة</h2>
                </div>
                
                <div class="card shadow-lg border-0">
                    <div class="card-body p-4 p-md-5">
                        
                        {% if validlink %}
                        
                        <form method="post">
                            {% csrf_token %}
                            
                            {% if form.errors %}
                            <div class="alert alert-danger">
                                {% for field, errors in form.errors.items %}
                                    {% for error in errors %}
                                    <div>{{ error }}</div>
                                    {% endfor %}
                                {% endfor %}
                            </div>
                            {% endif %}
                            
                            <div class="mb-3">
                                <label class="form-label fw-semibold">
                                    <i class="bi bi-lock"></i> كلمة المرور الجديدة
                                </label>
                                <input type="password" 
                                       name="new_password1"
                                       class="form-control form-control-lg" 
                                       required 
                                       autofocus>
                                <small class="text-muted">8 أحرف على الأقل</small>
                            </div>
                            
                            <div class="mb-4">
                                <label class="form-label fw-semibold">
                                    <i class="bi bi-lock-fill"></i> تأكيد كلمة المرور
                                </label>
                                <input type="password" 
                                       name="new_password2"
                                       class="form-control form-control-lg" 
                                       required>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-lg w-100">
                                <i class="bi bi-check-circle"></i>
                                تغيير كلمة المرور
                            </button>
                        </form>
                        
                        {% else %}
                        
                        <div class="text-center">
                            <div class="mb-3">
                                <i class="bi bi-x-circle-fill text-danger" style="font-size: 4rem;"></i>
                            </div>
                            <h5 class="fw-bold">الرابط غير صالح</h5>
                            <p class="text-muted">
                                الرابط منتهي الصلاحية أو تم استخدامه من قبل
                            </p>
                            <a href="{% url 'password_reset' %}" class="btn btn-primary">
                                طلب رابط جديد
                            </a>
                        </div>
                        
                        {% endif %}
                        
                    </div>
                </div>
                
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',

    # ────────────────────────────────────────
    # 4. صفحة تم بنجاح
    # ────────────────────────────────────────
    'templates/accounts/password_reset_complete.html': '''{% extends 'base/base.html' %}

{% block title %}تم بنجاح{% endblock %}

{% block content %}
<div class="min-vh-100 d-flex align-items-center justify-content-center py-5" 
     style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%);">
    
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                
                <div class="card shadow-lg border-0">
                    <div class="card-body p-5 text-center">
                        
                        <div class="mb-4">
                            <div class="d-inline-flex align-items-center justify-content-center rounded-circle" 
                                 style="width: 100px; height: 100px; background: rgba(16, 185, 129, 0.1);">
                                <i class="bi bi-shield-check text-success" style="font-size: 4rem;"></i>
                            </div>
                        </div>
                        
                        <h3 class="fw-bold mb-3">🎉 تم تغيير كلمة المرور</h3>
                        
                        <p class="text-muted mb-4">
                            تم تغيير كلمة المرور بنجاح.
                            <br>
                            يمكنك الآن تسجيل الدخول بكلمة المرور الجديدة.
                        </p>
                        
                        <a href="{% url 'login' %}" class="btn btn-primary btn-lg">
                            <i class="bi bi-box-arrow-in-right"></i>
                            تسجيل الدخول
                        </a>
                        
                    </div>
                </div>
                
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',

    # ────────────────────────────────────────
    # 5. قالب البريد الإلكتروني
    # ────────────────────────────────────────
    'templates/accounts/password_reset_email.html': '''{% autoescape off %}
مرحباً {{ user.get_full_name|default:user.username }}،

تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك في MotionHR.

اضغط على الرابط التالي لإعادة تعيين كلمة المرور:

{{ protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}

الرابط صالح لمدة 24 ساعة فقط.

إذا لم تطلب هذا، يمكنك تجاهل هذا البريد.

---
فريق MotionHR
إدارة الموارد البشرية بسلاسة
{% endautoescape %}
''',

    # ────────────────────────────────────────
    # 6. عنوان البريد
    # ────────────────────────────────────────
    'templates/accounts/password_reset_subject.txt': '''استعادة كلمة المرور - MotionHR
''',

    # ────────────────────────────────────────
    # 7. صفحة تغيير كلمة المرور (للمسجل)
    # ────────────────────────────────────────
    'templates/accounts/password_change.html': '''{% extends 'base/dashboard_base.html' %}

{% block title %}تغيير كلمة المرور{% endblock %}

{% block page_title %}تغيير كلمة المرور 🔐{% endblock %}
{% block page_subtitle %}قم بتحديث كلمة المرور بشكل دوري للأمان{% endblock %}

{% block dashboard_content %}

<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        
        <div class="card border-0 shadow-sm">
            <div class="card-body p-4 p-md-5">
                
                <div class="text-center mb-4">
                    <div class="d-inline-flex align-items-center justify-content-center rounded-circle mb-3" 
                         style="width: 80px; height: 80px; background: rgba(6, 182, 212, 0.1);">
                        <i class="bi bi-shield-lock-fill text-primary" style="font-size: 2.5rem;"></i>
                    </div>
                    <h4 class="fw-bold">تغيير كلمة المرور</h4>
                </div>
                
                <form method="post">
                    {% csrf_token %}
                    
                    {% if form.errors %}
                    <div class="alert alert-danger">
                        {% for field, errors in form.errors.items %}
                            {% for error in errors %}
                            <div><i class="bi bi-exclamation-triangle"></i> {{ error }}</div>
                            {% endfor %}
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    <div class="mb-3">
                        <label class="form-label fw-semibold">
                            <i class="bi bi-lock"></i> كلمة المرور الحالية
                        </label>
                        <input type="password" 
                               name="old_password"
                               class="form-control form-control-lg" 
                               required 
                               autofocus>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label fw-semibold">
                            <i class="bi bi-key"></i> كلمة المرور الجديدة
                        </label>
                        <input type="password" 
                               name="new_password1"
                               class="form-control form-control-lg" 
                               required>
                        <small class="text-muted">
                            <i class="bi bi-info-circle"></i>
                            8 أحرف على الأقل، تحتوي على حروف وأرقام
                        </small>
                    </div>
                    
                    <div class="mb-4">
                        <label class="form-label fw-semibold">
                            <i class="bi bi-key-fill"></i> تأكيد كلمة المرور
                        </label>
                        <input type="password" 
                               name="new_password2"
                               class="form-control form-control-lg" 
                               required>
                    </div>
                    
                    <div class="d-flex gap-2">
                        <a href="{% url 'dashboard' %}" class="btn btn-outline-secondary">
                            <i class="bi bi-x-circle"></i>
                            إلغاء
                        </a>
                        <button type="submit" class="btn btn-primary flex-grow-1">
                            <i class="bi bi-check-circle"></i>
                            تغيير كلمة المرور
                        </button>
                    </div>
                </form>
                
            </div>
        </div>
        
    </div>
</div>

{% endblock %}
''',

    # ────────────────────────────────────────
    # 8. صفحة "تم بنجاح" بعد تغيير كلمة المرور
    # ────────────────────────────────────────
    'templates/accounts/password_change_done.html': '''{% extends 'base/dashboard_base.html' %}

{% block title %}تم بنجاح{% endblock %}

{% block page_title %}تم تغيير كلمة المرور{% endblock %}

{% block dashboard_content %}

<div class="row justify-content-center">
    <div class="col-md-6">
        
        <div class="card border-0 shadow-sm">
            <div class="card-body p-5 text-center">
                
                <div class="mb-4">
                    <div class="d-inline-flex align-items-center justify-content-center rounded-circle" 
                         style="width: 100px; height: 100px; background: rgba(16, 185, 129, 0.1);">
                        <i class="bi bi-shield-check text-success" style="font-size: 4rem;"></i>
                    </div>
                </div>
                
                <h3 class="fw-bold mb-3">🎉 تم بنجاح</h3>
                
                <p class="text-muted mb-4">
                    تم تغيير كلمة المرور بنجاح.
                    <br>
                    استخدم كلمة المرور الجديدة في المرة القادمة.
                </p>
                
                <a href="{% url 'dashboard' %}" class="btn btn-primary">
                    <i class="bi bi-arrow-right"></i>
                    العودة للرئيسية
                </a>
                
            </div>
        </div>
        
    </div>
</div>

{% endblock %}
''',
}


# ═══════════════════════════════════════════════════════════
# التعديلات على ملفات موجودة
# ═══════════════════════════════════════════════════════════

def update_urls():
    """تحديث motionhr/urls.py"""
    urls_path = BASE_DIR / 'motionhr' / 'urls.py'
    
    if not urls_path.exists():
        return False, "ملف urls.py مش موجود"
    
    content = urls_path.read_text(encoding='utf-8')
    
    # نتأكد إن التعديل مش موجود قبل كده
    if 'password_reset' in content:
        return True, "التعديل موجود بالفعل"
    
    # نجيب السطر ونضيف بعده
    old_line = "path('logout/', auth_views.LogoutView.as_view(), name='logout'),"
    new_addition = '''path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/password-reset-complete/'
    ), name='password_reset_confirm'),
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Change Password
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/password-change/done/'
    ), name='password_change'),
    
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),'''
    
    if old_line not in content:
        return False, "لم يتم العثور على السطر المطلوب في urls.py"
    
    new_content = content.replace(old_line, new_addition)
    urls_path.write_text(new_content, encoding='utf-8')
    
    return True, "تم تحديث urls.py"


def update_settings():
    """تحديث motionhr/settings.py لإضافة إعدادات Email"""
    settings_path = BASE_DIR / 'motionhr' / 'settings.py'
    
    if not settings_path.exists():
        return False, "ملف settings.py مش موجود"
    
    content = settings_path.read_text(encoding='utf-8')
    
    if 'EMAIL_BACKEND' in content:
        return True, "إعدادات Email موجودة بالفعل"
    
    email_settings = '''

# Email Settings (للتطوير - يطبع في التيرمنال)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'MotionHR <noreply@motionhr.com>'
'''
    
    with settings_path.open('a', encoding='utf-8') as f:
        f.write(email_settings)
    
    return True, "تم تحديث settings.py"


def update_login_page():
    """تحديث رابط نسيت كلمة المرور في صفحة Login"""
    login_path = BASE_DIR / 'templates' / 'accounts' / 'login.html'
    
    if not login_path.exists():
        return False, "ملف login.html مش موجود"
    
    content = login_path.read_text(encoding='utf-8')
    
    old = '<a href="#" class="text-decoration-none small text-primary">\n                                    نسيت كلمة المرور؟\n                                </a>'
    new = '<a href="{% url \'password_reset\' %}" class="text-decoration-none small text-primary">\n                                    نسيت كلمة المرور؟\n                                </a>'
    
    if '{% url \'password_reset\' %}' in content:
        return True, "التعديل موجود بالفعل في login.html"
    
    if old not in content:
        # جرب بشكل تاني (مسافات مختلفة)
        old_alt = '<a href="#" class="text-decoration-none small text-primary">'
        new_alt = '<a href="{% url \'password_reset\' %}" class="text-decoration-none small text-primary">'
        
        if old_alt in content:
            content = content.replace(old_alt, new_alt, 1)
            login_path.write_text(content, encoding='utf-8')
            return True, "تم تحديث login.html"
        
        return False, "لم يتم العثور على رابط نسيت كلمة المرور"
    
    new_content = content.replace(old, new)
    login_path.write_text(new_content, encoding='utf-8')
    
    return True, "تم تحديث login.html"


def update_dashboard_base():
    """إضافة تغيير كلمة المرور في User Dropdown"""
    dashboard_path = BASE_DIR / 'templates' / 'base' / 'dashboard_base.html'
    
    if not dashboard_path.exists():
        return False, "ملف dashboard_base.html مش موجود"
    
    content = dashboard_path.read_text(encoding='utf-8')
    
    if 'password_change' in content:
        return True, "التعديل موجود بالفعل في dashboard_base.html"
    
    old = '''<li>
                            <a class="dropdown-item" href="#">
                                <i class="bi bi-gear ms-2"></i> الإعدادات
                            </a>
                        </li>'''
    
    new = '''<li>
                            <a class="dropdown-item" href="{% url 'password_change' %}">
                                <i class="bi bi-shield-lock ms-2"></i> تغيير كلمة المرور
                            </a>
                        </li>
                        <li>
                            <a class="dropdown-item" href="#">
                                <i class="bi bi-gear ms-2"></i> الإعدادات
                            </a>
                        </li>'''
    
    if old not in content:
        return False, "لم يتم العثور على قائمة الإعدادات في dashboard_base.html"
    
    new_content = content.replace(old, new)
    dashboard_path.write_text(new_content, encoding='utf-8')
    
    return True, "تم تحديث dashboard_base.html"


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def create_file(relative_path, content):
    """إنشاء ملف مع إنشاء المجلدات لو مش موجودة"""
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')
    return True


def main():
    print("=" * 60)
    print("🚀 Patch 01: Password Reset + Change Password")
    print("=" * 60)
    print()
    
    # إنشاء الملفات
    print("📁 إنشاء الملفات...")
    print("-" * 60)
    
    created_count = 0
    for file_path, content in FILES.items():
        try:
            create_file(file_path, content)
            print(f"  ✅ {file_path}")
            created_count += 1
        except Exception as e:
            print(f"  ❌ {file_path}")
            print(f"     خطأ: {e}")
    
    print()
    print(f"📊 تم إنشاء {created_count}/{len(FILES)} ملف")
    print()
    
    # تحديث الملفات
    print("🔧 تحديث الملفات الموجودة...")
    print("-" * 60)
    
    updates = [
        ('urls.py', update_urls),
        ('settings.py', update_settings),
        ('login.html', update_login_page),
        ('dashboard_base.html', update_dashboard_base),
    ]
    
    for name, func in updates:
        try:
            success, message = func()
            icon = "✅" if success else "⚠️"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  ❌ {name}: خطأ - {e}")
    
    print()
    print("=" * 60)
    print("✨ تم الانتهاء!")
    print("=" * 60)
    print()
    print("الخطوات التالية:")
    print("  1. شغل السيرفر: python manage.py runserver 0.0.0.0:8000")
    print("  2. اختبر Logout ثم اضغط 'نسيت كلمة المرور'")
    print("  3. اختبر تغيير كلمة المرور من قائمة المستخدم")
    print()


if __name__ == '__main__':
    main()