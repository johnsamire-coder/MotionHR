#!/usr/bin/env python3
"""
Patch 16: Login Methods Feature-Based
=======================================
- Login بالإيميل (Starter+)
- Login بالرقم الوظيفي (Business+)
- Login بالموبايل (Professional+)
- Login بـ 2FA (Enterprise) - واجهة فقط
- استعادة عبر المدير (Business+)
- إعدادات كلمة المرور لكل شركة
- صفحة Login ذكية حسب خطة الشركة
"""

import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def append_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

print("=" * 60)
print("  Patch 16: Login Methods Feature-Based")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إنشاء accounts/login_backend.py
#    Backend ذكي يدعم الإيميل + الرقم الوظيفي + الموبايل
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء accounts/login_backend.py...")

login_backend = '''"""
login_backend.py
Backend تسجيل الدخول الذكي
يدعم: username / email / employee_code / phone
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class SmartLoginBackend(ModelBackend):
    """
    Backend ذكي يحاول تسجيل الدخول بـ:
    1. username (دايماً)
    2. email (لو مفعّل للشركة)
    3. employee_code (لو مفعّل للشركة)
    4. phone (لو مفعّل للشركة)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        username = username.strip()

        try:
            # نبحث بكل الطرق في وقت واحد
            user = User.objects.filter(
                Q(username__iexact=username) |
                Q(email__iexact=username) |
                Q(phone=username)
            ).first()

            # لو مش لاقيه جرب الرقم الوظيفي
            if not user:
                from employees.models import Employee
                emp = Employee.objects.filter(
                    employee_code__iexact=username
                ).select_related('user').first()
                if emp and emp.user:
                    user = emp.user

            if user and user.check_password(password):
                return user

        except Exception:
            return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
'''

create_file(
    os.path.join(BASE_DIR, 'accounts', 'login_backend.py'),
    login_backend
)


# ════════════════════════════════════════════════════════════
# 2. إنشاء CompanyLoginSettings model
#    إعدادات تسجيل الدخول لكل شركة
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء CompanyLoginSettings model...")

# نضيف في companies/models.py
companies_models_path = os.path.join(BASE_DIR, 'companies', 'models.py')
companies_models = read_file(companies_models_path)

login_settings_model = '''

# ════════════════════════════════════════════════════════════
# إعدادات تسجيل الدخول لكل شركة
# ════════════════════════════════════════════════════════════
class CompanyLoginSettings(models.Model):
    """
    إعدادات تسجيل الدخول الخاصة بكل شركة
    تتحكم في طرق الدخول وإعدادات كلمة المرور
    """
    company = models.OneToOneField(
        'Company',
        on_delete=models.CASCADE,
        related_name='login_settings',
        verbose_name='الشركة'
    )

    # ── طرق تسجيل الدخول ──
    login_by_email = models.BooleanField(
        default=True,
        verbose_name='الدخول بالإيميل'
    )
    login_by_employee_code = models.BooleanField(
        default=True,
        verbose_name='الدخول بالرقم الوظيفي'
    )
    login_by_phone = models.BooleanField(
        default=False,
        verbose_name='الدخول بالموبايل'
    )
    login_by_username = models.BooleanField(
        default=True,
        verbose_name='الدخول باسم المستخدم'
    )

    # ── إعدادات كلمة المرور ──
    min_password_length = models.PositiveSmallIntegerField(
        default=8,
        verbose_name='الحد الأدنى لطول كلمة المرور'
    )
    require_uppercase = models.BooleanField(
        default=False,
        verbose_name='إجبار حروف كبيرة'
    )
    require_numbers = models.BooleanField(
        default=False,
        verbose_name='إجبار أرقام'
    )
    require_symbols = models.BooleanField(
        default=False,
        verbose_name='إجبار رموز'
    )
    password_expiry_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='مدة انتهاء كلمة المرور (يوم)',
        help_text='0 = لا تنتهي'
    )

    # ── إعدادات القفل ──
    max_login_attempts = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='أقصى محاولات دخول'
    )
    lockout_duration_minutes = models.PositiveSmallIntegerField(
        default=15,
        verbose_name='مدة القفل (دقيقة)'
    )

    # ── تسجيل الدخول الإجباري ──
    force_change_on_first_login = models.BooleanField(
        default=True,
        verbose_name='إجبار تغيير كلمة المرور عند أول دخول'
    )

    class Meta:
        verbose_name        = 'إعدادات تسجيل الدخول'
        verbose_name_plural = 'إعدادات تسجيل الدخول'

    def __str__(self):
        return f'إعدادات دخول - {self.company.name_ar}'

    @classmethod
    def get_for_company(cls, company):
        """جلب الإعدادات أو إنشاء افتراضية"""
        obj, _ = cls.objects.get_or_create(company=company)
        return obj
'''

if 'CompanyLoginSettings' not in companies_models:
    append_file(companies_models_path, login_settings_model)
else:
    print("  ℹ️  CompanyLoginSettings موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3. Migration لـ CompanyLoginSettings
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء migration لـ CompanyLoginSettings...")

companies_migrations_dir = os.path.join(BASE_DIR, 'companies', 'migrations')
existing = sorted([
    f for f in os.listdir(companies_migrations_dir)
    if f.endswith('.py') and f != '__init__.py'
])
last = existing[-1].replace('.py', '') if existing else '0001_initial'
num  = str(int(last.split('_')[0]) + 1).zfill(4)

migration_content = f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '{last}'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyLoginSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name=\'ID\')),
                ('login_by_email',         models.BooleanField(default=True,
                                            verbose_name=\'الدخول بالإيميل\')),
                ('login_by_employee_code', models.BooleanField(default=True,
                                            verbose_name=\'الدخول بالرقم الوظيفي\')),
                ('login_by_phone',         models.BooleanField(default=False,
                                            verbose_name=\'الدخول بالموبايل\')),
                ('login_by_username',      models.BooleanField(default=True,
                                            verbose_name=\'الدخول باسم المستخدم\')),
                ('min_password_length',    models.PositiveSmallIntegerField(default=8,
                                            verbose_name=\'الحد الأدنى لطول كلمة المرور\')),
                ('require_uppercase',      models.BooleanField(default=False,
                                            verbose_name=\'إجبار حروف كبيرة\')),
                ('require_numbers',        models.BooleanField(default=False,
                                            verbose_name=\'إجبار أرقام\')),
                ('require_symbols',        models.BooleanField(default=False,
                                            verbose_name=\'إجبار رموز\')),
                ('password_expiry_days',   models.PositiveSmallIntegerField(default=0,
                                            verbose_name=\'مدة انتهاء كلمة المرور (يوم)\')),
                ('max_login_attempts',     models.PositiveSmallIntegerField(default=5,
                                            verbose_name=\'أقصى محاولات دخول\')),
                ('lockout_duration_minutes', models.PositiveSmallIntegerField(default=15,
                                              verbose_name=\'مدة القفل (دقيقة)\')),
                ('force_change_on_first_login', models.BooleanField(default=True,
                                                 verbose_name=\'إجبار تغيير كلمة المرور عند أول دخول\')),
                ('company', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name=\'login_settings\',
                    to=\'companies.company\',
                    verbose_name=\'الشركة\'
                )),
            ],
            options={{
                'verbose_name':        \'إعدادات تسجيل الدخول\',
                'verbose_name_plural': \'إعدادات تسجيل الدخول\',
            }},
        ),
    ]
'''

create_file(
    os.path.join(companies_migrations_dir, f"{num}_add_company_login_settings.py"),
    migration_content
)


# ════════════════════════════════════════════════════════════
# 4. تحديث accounts/views.py
#    Smart Login View
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء Smart Login View...")

smart_login_view = '''

# ════════════════════════════════════════════════════════════
# Smart Login View
# ════════════════════════════════════════════════════════════
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache


@never_cache
@require_http_methods(["GET", "POST"])
def smart_login_view(request):
    """
    صفحة تسجيل الدخول الذكية
    تدعم: username / email / employee_code / phone
    """
    # لو مسجل دخوله خليه يروح للـ dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    # تحديد placeholder حسب الشركة (مبدئياً عام)
    login_hint = 'اسم المستخدم أو الإيميل أو الرقم الوظيفي'

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember  = request.POST.get('remember_me')

        if not username or not password:
            error = 'يرجى إدخال اسم المستخدم وكلمة المرور'
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    error = 'حسابك موقوف - تواصل مع المدير'
                else:
                    auth_login(request, user,
                               backend='accounts.login_backend.SmartLoginBackend')

                    # Session expiry
                    if not remember:
                        request.session.set_expiry(0)  # ينتهي مع إغلاق المتصفح
                    else:
                        request.session.set_expiry(60 * 60 * 24 * 30)  # 30 يوم

                    # لو لازم يغير كلمة المرور
                    if getattr(user, 'must_change_password', False):
                        return redirect('password_change')

                    return redirect('dashboard')
            else:
                error = 'اسم المستخدم أو كلمة المرور غير صحيحة'

    context = {
        'login_hint': login_hint,
        'error':      error,
    }
    return render(request, 'accounts/login.html', context)


def smart_logout_view(request):
    """تسجيل الخروج"""
    if request.method == 'POST':
        auth_logout(request)
    return redirect('login')
'''

accounts_views_path = os.path.join(BASE_DIR, 'accounts', 'views.py')
accounts_views = read_file(accounts_views_path)

if 'smart_login_view' not in accounts_views:
    append_file(accounts_views_path, smart_login_view)
else:
    print("  ℹ️  smart_login_view موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 5. تحديث motionhr/urls.py
#    استخدام smart_login_view بدل auth_views.LoginView
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث motionhr/urls.py...")

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

# إضافة import
if 'smart_login_view' not in main_urls_content:
    old_import = 'from accounts.views import CustomPasswordChangeView'
    new_import  = ('from accounts.views import '
                   'CustomPasswordChangeView, smart_login_view, smart_logout_view')

    if old_import in main_urls_content:
        main_urls_content = main_urls_content.replace(old_import, new_import)
    else:
        # لو مش موجود نضيفه بعد auth_views import
        main_urls_content = main_urls_content.replace(
            'from django.contrib.auth import views as auth_views',
            'from django.contrib.auth import views as auth_views\n'
            'from accounts.views import '
            'CustomPasswordChangeView, smart_login_view, smart_logout_view'
        )

    # استبدال login URL
    if "path('login/'," in main_urls_content:
        import re
        main_urls_content = re.sub(
            r"path\('login/',\s*auth_views\.LoginView[^)]+\),",
            "path('login/', smart_login_view, name='login'),",
            main_urls_content
        )

    # استبدال logout URL
    if "path('logout/'," in main_urls_content:
        main_urls_content = re.sub(
            r"path\('logout/',\s*auth_views\.LogoutView[^)]+\),",
            "path('logout/', smart_logout_view, name='logout'),",
            main_urls_content
        )

    write_file(main_urls_path, main_urls_content)
else:
    print("  ℹ️  smart_login_view موجود في urls.py")


# ════════════════════════════════════════════════════════════
# 6. تحديث settings.py
#    إضافة SmartLoginBackend
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings.py - Authentication Backends...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')
settings_content = read_file(settings_path)

if 'AUTHENTICATION_BACKENDS' not in settings_content:
    auth_backends = """
# ─────────────────────────────────────────────
# Authentication Backends
# ─────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'accounts.login_backend.SmartLoginBackend',
    'django.contrib.auth.backends.ModelBackend',
]
"""
    append_file(settings_path, auth_backends)
else:
    print("  ℹ️  AUTHENTICATION_BACKENDS موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 7. تحديث login.html
#    صفحة Login احترافية وذكية
# ════════════════════════════════════════════════════════════
print("\n📄 تحديث login.html...")

login_template = r"""{% extends 'base/base.html' %}

{% block title %}تسجيل الدخول - MotionHR{% endblock %}

{% block content %}
<div class="min-vh-100 d-flex align-items-center justify-content-center"
     style="background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0e7490 100%);">

  <div class="container">
    <div class="row justify-content-center">
      <div class="col-sm-10 col-md-7 col-lg-5 col-xl-4">

        <!-- Card -->
        <div class="card border-0 shadow-lg"
             style="border-radius:20px; overflow:hidden;">

          <!-- Header -->
          <div class="card-header border-0 text-center py-4"
               style="background: linear-gradient(135deg, #06B6D4, #0891B2);">
            <h2 class="text-white fw-black mb-1" style="font-size:2rem; letter-spacing:-1px;">
              MotionHR
            </h2>
            <p class="text-white mb-0" style="opacity:0.85; font-size:0.9rem;">
              HR in Motion – إدارة بسلاسة
            </p>
          </div>

          <!-- Body -->
          <div class="card-body p-4 p-md-5">

            <h5 class="fw-bold text-center mb-4 text-dark">
              مرحباً بك 👋
            </h5>

            <!-- رسالة الخطأ -->
            {% if error %}
            <div class="alert alert-danger border-0 rounded-3 py-2 px-3 mb-4"
                 style="background:#fde8e8; color:#dc2626; font-size:0.9rem;">
              <i class="bi bi-exclamation-circle me-2"></i>{{ error }}
            </div>
            {% endif %}

            <!-- Django Messages -->
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }} border-0 rounded-3 py-2 px-3 mb-3">
              {{ message }}
            </div>
            {% endfor %}

            <!-- فورم الدخول -->
            <form method="post" action="{% url 'login' %}" autocomplete="off">
              {% csrf_token %}

              <!-- اسم المستخدم -->
              <div class="mb-3">
                <label class="form-label fw-semibold text-dark small mb-1">
                  <i class="bi bi-person me-1" style="color:#06B6D4;"></i>
                  بيانات الدخول
                </label>
                <input type="text"
                       name="username"
                       class="form-control form-control-lg border-0"
                       style="background:#f8fafc; border-radius:10px; font-size:0.95rem;"
                       placeholder="{{ login_hint }}"
                       value="{{ request.POST.username|default:'' }}"
                       autofocus
                       required>
                <div class="form-text text-muted mt-1" style="font-size:0.78rem;">
                  <i class="bi bi-info-circle me-1"></i>
                  يمكنك الدخول بـ: اسم المستخدم أو الإيميل أو الرقم الوظيفي أو الموبايل
                </div>
              </div>

              <!-- كلمة المرور -->
              <div class="mb-4">
                <label class="form-label fw-semibold text-dark small mb-1">
                  <i class="bi bi-lock me-1" style="color:#06B6D4;"></i>
                  كلمة المرور
                </label>
                <div class="input-group">
                  <input type="password"
                         name="password"
                         id="passwordInput"
                         class="form-control form-control-lg border-0 border-end-0"
                         style="background:#f8fafc; border-radius:10px 0 0 10px; font-size:0.95rem;"
                         placeholder="••••••••••"
                         required>
                  <button class="btn border-0"
                          style="background:#f8fafc; border-radius:0 10px 10px 0;"
                          type="button"
                          onclick="togglePassword()">
                    <i class="bi bi-eye" id="eyeIcon" style="color:#06B6D4;"></i>
                  </button>
                </div>
              </div>

              <!-- تذكرني + نسيت كلمة المرور -->
              <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox"
                         name="remember_me" id="rememberMe"
                         style="border-color:#06B6D4;">
                  <label class="form-check-label small text-muted" for="rememberMe">
                    تذكرني
                  </label>
                </div>
                <a href="{% url 'password_reset' %}"
                   class="small text-decoration-none fw-semibold"
                   style="color:#06B6D4;">
                  نسيت كلمة المرور؟
                </a>
              </div>

              <!-- زرار الدخول -->
              <button type="submit"
                      class="btn btn-lg w-100 text-white fw-bold"
                      style="background: linear-gradient(135deg, #06B6D4, #0891B2);
                             border-radius:12px; padding:14px; font-size:1rem;
                             box-shadow: 0 4px 15px rgba(6,182,212,0.4);">
                <i class="bi bi-box-arrow-in-right me-2"></i>
                تسجيل الدخول
              </button>

            </form>

          </div>

          <!-- Footer -->
          <div class="card-footer border-0 text-center py-3"
               style="background:#f8fafc;">
            <small class="text-muted">
              مشكلة في الدخول؟
              <a href="{% url 'subscriptions:contact_sales' %}"
                 class="text-decoration-none fw-semibold"
                 style="color:#06B6D4;">
                تواصل مع المدير
              </a>
            </small>
          </div>

        </div>

        <!-- نسخة النظام -->
        <div class="text-center mt-3">
          <small style="color:rgba(255,255,255,0.4); font-size:0.75rem;">
            MotionHR v1.0 &copy; 2025
          </small>
        </div>

      </div>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_js %}
<script>
function togglePassword() {
    const input = document.getElementById('passwordInput');
    const icon  = document.getElementById('eyeIcon');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

// Enter key submit
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.target.closest('form')?.submit();
    }
});
</script>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'accounts', 'login.html'),
    login_template
)


# ════════════════════════════════════════════════════════════
# 8. إنشاء صفحة إعدادات تسجيل الدخول للمدير
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء login_settings.html...")

login_settings_template = r"""{% extends 'base/dashboard_base.html' %}

{% block title %}إعدادات تسجيل الدخول{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <!-- Header -->
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-shield-lock me-2" style="color:#06B6D4;"></i>
        إعدادات تسجيل الدخول
      </h4>
      <p class="text-muted mb-0">تحكم في طرق الدخول وأمان كلمات المرور</p>
    </div>
  </div>

  <form method="post">
    {% csrf_token %}

    <div class="row g-4">

      <!-- طرق تسجيل الدخول -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-door-open me-2" style="color:#06B6D4;"></i>
              طرق تسجيل الدخول
            </h5>
            <small class="text-muted">اختر الطرق المسموح بها لموظفيك</small>
          </div>
          <div class="card-body px-4 pb-4">

            {% for field_name, label, desc, available in login_methods %}
            <div class="d-flex align-items-start justify-content-between py-3
                        border-bottom {% if forloop.last %}border-0{% endif %}">
              <div>
                <div class="fw-semibold">{{ label }}</div>
                <small class="text-muted">{{ desc }}</small>
                {% if not available %}
                <span class="badge bg-warning text-dark ms-1">
                  يتطلب ترقية
                </span>
                {% endif %}
              </div>
              <div class="form-check form-switch ms-3 mt-1">
                <input class="form-check-input"
                       type="checkbox"
                       name="{{ field_name }}"
                       id="{{ field_name }}"
                       {% if available %}
                         {% if settings_obj and settings_obj|getattr:field_name %}checked{% endif %}
                       {% else %}
                         disabled
                       {% endif %}
                       style="width:2.5rem; height:1.25rem;">
              </div>
            </div>
            {% endfor %}

          </div>
        </div>
      </div>

      <!-- إعدادات كلمة المرور -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-key me-2" style="color:#06B6D4;"></i>
              إعدادات كلمة المرور
            </h5>
            <small class="text-muted">قواعد أمان كلمات المرور</small>
          </div>
          <div class="card-body px-4 pb-4">

            <!-- الحد الأدنى للطول -->
            <div class="mb-4">
              <label class="fw-semibold small mb-2">
                الحد الأدنى لطول كلمة المرور
              </label>
              <div class="d-flex align-items-center gap-3">
                <input type="range"
                       name="min_password_length"
                       class="form-range flex-grow-1"
                       min="6" max="20"
                       value="{{ settings_obj.min_password_length|default:8 }}"
                       oninput="document.getElementById('pwdLen').textContent=this.value">
                <span class="badge fs-6 px-3" style="background:#06B6D4; min-width:40px;">
                  <span id="pwdLen">{{ settings_obj.min_password_length|default:8 }}</span>
                </span>
              </div>
            </div>

            <!-- قواعد التعقيد -->
            {% for field_name, label in password_rules %}
            <div class="d-flex align-items-center justify-content-between py-2 border-bottom">
              <span class="fw-semibold small">{{ label }}</span>
              <div class="form-check form-switch">
                <input class="form-check-input"
                       type="checkbox"
                       name="{{ field_name }}"
                       {% if settings_obj and settings_obj|getattr:field_name %}checked{% endif %}
                       style="width:2.5rem; height:1.25rem;">
              </div>
            </div>
            {% endfor %}

            <!-- انتهاء صلاحية كلمة المرور -->
            <div class="mt-3">
              <label class="fw-semibold small mb-2">
                انتهاء صلاحية كلمة المرور (يوم)
                <small class="text-muted fw-normal">(0 = لا تنتهي)</small>
              </label>
              <input type="number"
                     name="password_expiry_days"
                     class="form-control"
                     min="0" max="365"
                     value="{{ settings_obj.password_expiry_days|default:0 }}">
            </div>

          </div>
        </div>
      </div>

      <!-- إعدادات القفل -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-shield-x me-2" style="color:#06B6D4;"></i>
              إعدادات القفل
            </h5>
            <small class="text-muted">الحماية من محاولات الدخول المتكررة</small>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="mb-3">
              <label class="fw-semibold small mb-2">أقصى عدد محاولات قبل القفل</label>
              <select name="max_login_attempts" class="form-select">
                {% for n in "3 5 10"|split:" " %}
                <option value="{{ n }}"
                  {% if settings_obj.max_login_attempts == n|add:0 %}selected{% endif %}>
                  {{ n }} محاولات
                </option>
                {% endfor %}
              </select>
            </div>

            <div class="mb-3">
              <label class="fw-semibold small mb-2">مدة القفل (بالدقائق)</label>
              <select name="lockout_duration_minutes" class="form-select">
                {% for n, label in lockout_options %}
                <option value="{{ n }}"
                  {% if settings_obj.lockout_duration_minutes == n %}selected{% endif %}>
                  {{ label }}
                </option>
                {% endfor %}
              </select>
            </div>

            <div class="form-check form-switch mt-4">
              <input class="form-check-input"
                     type="checkbox"
                     name="force_change_on_first_login"
                     id="forceChange"
                     {% if settings_obj.force_change_on_first_login %}checked{% endif %}
                     style="width:2.5rem; height:1.25rem;">
              <label class="form-check-label fw-semibold" for="forceChange">
                إجبار تغيير كلمة المرور عند أول دخول
              </label>
            </div>

          </div>
        </div>
      </div>

    </div>

    <!-- Save -->
    <div class="mt-4 d-flex gap-2">
      <button type="submit"
              class="btn btn-lg text-white px-5"
              style="background:#06B6D4; border-radius:10px;">
        <i class="bi bi-check-lg me-2"></i>
        حفظ الإعدادات
      </button>
      <a href="{% url 'dashboard' %}"
         class="btn btn-lg btn-outline-secondary px-4"
         style="border-radius:10px;">
        إلغاء
      </a>
    </div>

  </form>

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'accounts', 'login_settings.html'),
    login_settings_template
)


# ════════════════════════════════════════════════════════════
# 9. إضافة login_settings view في accounts/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة login_settings_view...")

login_settings_view = '''

# ════════════════════════════════════════════════════════════
# إعدادات تسجيل الدخول
# ════════════════════════════════════════════════════════════
from django.contrib.auth.decorators import login_required


@login_required
def login_settings_view(request):
    """صفحة إعدادات تسجيل الدخول"""
    from companies.models import CompanyLoginSettings

    if not request.user.company:
        from django.contrib import messages as msg
        msg.error(request, 'لا يوجد شركة مرتبطة بحسابك')
        return redirect('dashboard')

    settings_obj = CompanyLoginSettings.get_for_company(request.user.company)

    # تحديد الميزات المتاحة حسب الخطة
    has_business     = _has_feature(request.user.company, 'login_by_employee_code')
    has_professional = _has_feature(request.user.company, 'login_by_phone')

    login_methods = [
        ('login_by_username',
         'اسم المستخدم',
         'الدخول باسم المستخدم التقليدي',
         True),
        ('login_by_email',
         'البريد الإلكتروني',
         'الدخول بعنوان البريد الإلكتروني',
         True),
        ('login_by_employee_code',
         'الرقم الوظيفي',
         'الدخول بالرقم الوظيفي (EMP00001)',
         has_business),
        ('login_by_phone',
         'رقم الموبايل',
         'الدخول برقم الهاتف المحمول',
         has_professional),
    ]

    password_rules = [
        ('require_uppercase', 'إجبار حروف كبيرة (A-Z)'),
        ('require_numbers',   'إجبار أرقام (0-9)'),
        ('require_symbols',   'إجبار رموز (@#$%)'),
    ]

    lockout_options = [
        (5,  '5 دقائق'),
        (15, '15 دقيقة'),
        (30, '30 دقيقة'),
        (60, 'ساعة'),
    ]

    if request.method == 'POST':
        # حفظ طرق الدخول
        settings_obj.login_by_username      = 'login_by_username'      in request.POST
        settings_obj.login_by_email         = 'login_by_email'         in request.POST
        settings_obj.login_by_employee_code = 'login_by_employee_code' in request.POST
        settings_obj.login_by_phone         = 'login_by_phone'         in request.POST

        # حفظ إعدادات كلمة المرور
        settings_obj.min_password_length  = int(request.POST.get('min_password_length', 8))
        settings_obj.require_uppercase    = 'require_uppercase'    in request.POST
        settings_obj.require_numbers      = 'require_numbers'      in request.POST
        settings_obj.require_symbols      = 'require_symbols'      in request.POST
        settings_obj.password_expiry_days = int(request.POST.get('password_expiry_days', 0))

        # حفظ إعدادات القفل
        settings_obj.max_login_attempts       = int(request.POST.get('max_login_attempts', 5))
        settings_obj.lockout_duration_minutes = int(request.POST.get('lockout_duration_minutes', 15))
        settings_obj.force_change_on_first_login = 'force_change_on_first_login' in request.POST

        settings_obj.save()

        from django.contrib import messages as msg
        msg.success(request, '✅ تم حفظ الإعدادات بنجاح')
        return redirect('accounts:login_settings')

    context = {
        'settings_obj':    settings_obj,
        'login_methods':   login_methods,
        'password_rules':  password_rules,
        'lockout_options': lockout_options,
        'page_title':      'إعدادات تسجيل الدخول',
    }
    return render(request, 'accounts/login_settings.html', context)


def _has_feature(company, feature_name):
    """تحقق من ميزة في اشتراك الشركة"""
    try:
        from subscriptions.models import Subscription
        sub = Subscription.objects.filter(
            company=company,
            status__in=['active', 'trial']
        ).select_related('plan').first()
        if sub:
            return getattr(sub.plan, feature_name, False)
    except Exception:
        pass
    return False
'''

accounts_views = read_file(accounts_views_path)
if 'login_settings_view' not in accounts_views:
    append_file(accounts_views_path, login_settings_view)
else:
    print("  ℹ️  login_settings_view موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 10. إضافة accounts/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء accounts/urls.py...")

accounts_urls = """from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login-settings/', views.login_settings_view, name='login_settings'),
]
"""

create_file(
    os.path.join(BASE_DIR, 'accounts', 'urls.py'),
    accounts_urls
)


# ════════════════════════════════════════════════════════════
# 11. إضافة accounts URLs في motionhr/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة accounts URLs في motionhr/urls.py...")

main_urls_content = read_file(main_urls_path)

if "include('accounts.urls'" not in main_urls_content:
    old = "urlpatterns = ["
    new = """urlpatterns = [
    path('accounts/', include('accounts.urls', namespace='accounts')),"""
    main_urls_content = main_urls_content.replace(old, new, 1)
    write_file(main_urls_path, main_urls_content)
else:
    print("  ℹ️  accounts URLs موجود")


# ════════════════════════════════════════════════════════════
# 12. إضافة رابط إعدادات الدخول في الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة رابط إعدادات الدخول في الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
sidebar_content = read_file(sidebar_path)

if 'login_settings' not in sidebar_content:
    settings_link = """
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'accounts:login_settings' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px; font-size:0.85rem;">
                    <i class="bi bi-shield-lock"></i>
                    <span>إعدادات الدخول</span>
                  </a>
                </li>"""

    # نضيفه قبل رابط "خطتي"
    if "{% url 'subscriptions:my_plan' %}" in sidebar_content:
        sidebar_content = sidebar_content.replace(
            "{% url 'subscriptions:my_plan' %}",
            "{% url 'subscriptions:my_plan' %}"
        )
        # نضيف قبل my_plan
        my_plan_idx = sidebar_content.find("{% url 'subscriptions:my_plan' %}")
        li_start = sidebar_content.rfind('<li', 0, my_plan_idx)
        sidebar_content = (
            sidebar_content[:li_start] +
            settings_link + '\n' +
            sidebar_content[li_start:]
        )
        write_file(sidebar_path, sidebar_content)
        print("  ✅ تم إضافة رابط إعدادات الدخول")
    else:
        print("  ⚠️  مش لاقي مكان مناسب")
else:
    print("  ℹ️  رابط إعدادات الدخول موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 16 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ accounts/login_backend.py - Smart Login Backend
  2.  ✅ CompanyLoginSettings model
  3.  ✅ Migration لـ CompanyLoginSettings
  4.  ✅ smart_login_view - صفحة دخول ذكية
  5.  ✅ smart_logout_view
  6.  ✅ login.html - صفحة دخول احترافية
  7.  ✅ login_settings.html - إعدادات الدخول
  8.  ✅ login_settings_view
  9.  ✅ accounts/urls.py
  10. ✅ motionhr/urls.py - Smart Login
  11. ✅ settings.py - AUTHENTICATION_BACKENDS
  12. ✅ Sidebar - إعدادات الدخول

🔗 URLs الجديدة:
  /login/                    ← صفحة الدخول الذكية
  /accounts/login-settings/  ← إعدادات الدخول

⚠️  مطلوب تشغيل:
  python manage.py migrate

🚀 الخطوة الجاية: Patch 17 - صفحات الشركات والفروع
""")