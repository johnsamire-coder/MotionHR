#!/usr/bin/env python3
"""
Patch 15: Employee User Accounts
==================================
- Checkbox "إنشاء حساب" عند إضافة موظف
- Auto-generate username من employee_code
- Auto-generate password آمنة
- إيميل ترحيبي لو فيه إيميل
- طباعة بيانات الدخول لو مفيش إيميل
- إعادة تعيين كلمة المرور من المدير
- إجبار تغيير الباسورد أول دخول
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
print("  Patch 15: Employee User Accounts")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. تحديث accounts/models.py
#    إضافة حقل must_change_password
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/models.py...")

accounts_models_path = os.path.join(BASE_DIR, 'accounts', 'models.py')
accounts_models = read_file(accounts_models_path)

if 'must_change_password' not in accounts_models:
    # نضيف الحقل بعد avatar
    old = "    class Meta:"
    new = """    must_change_password = models.BooleanField(
        default=False,
        verbose_name='يجب تغيير كلمة المرور'
    )

    class Meta:"""
    accounts_models = accounts_models.replace(old, new, 1)
    write_file(accounts_models_path, accounts_models)
else:
    print("  ℹ️  must_change_password موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2. إنشاء Migration لحقل must_change_password
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء migration للحقل الجديد...")

# هنعمل migration يدوي
migrations_dir = os.path.join(BASE_DIR, 'accounts', 'migrations')
existing_migrations = sorted([
    f for f in os.listdir(migrations_dir)
    if f.endswith('.py') and f != '__init__.py'
])

last_migration = existing_migrations[-1].replace('.py', '') if existing_migrations else '0001_initial'
migration_number = str(int(last_migration.split('_')[0]) + 1).zfill(4)
new_migration_name = f"{migration_number}_add_must_change_password"

migration_content = f"""from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '{last_migration}'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='must_change_password',
            field=models.BooleanField(default=False, verbose_name='يجب تغيير كلمة المرور'),
        ),
    ]
"""

create_file(
    os.path.join(migrations_dir, f"{new_migration_name}.py"),
    migration_content
)


# ════════════════════════════════════════════════════════════
# 3. إنشاء employees/account_utils.py
#    أدوات إنشاء وإدارة حسابات الموظفين
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء employees/account_utils.py...")

account_utils = '''"""
account_utils.py
أدوات إنشاء وإدارة حسابات الموظفين
"""

import random
import string
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

User = get_user_model()


def generate_password(length=10):
    """
    توليد كلمة سر آمنة
    - حروف كبيرة + صغيرة + أرقام + رموز
    """
    chars = (
        string.ascii_uppercase +   # A-Z
        string.ascii_lowercase +   # a-z
        string.digits +            # 0-9
        "@#$%"                     # رموز بسيطة
    )
    # نضمن وجود كل نوع
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("@#$%"),
    ]
    # باقي الطول عشوائي
    password += random.choices(chars, k=length - 4)
    random.shuffle(password)
    return "".join(password)


def generate_username(employee):
    """
    توليد username من employee_code
    مثال: EMP00001
    """
    return employee.employee_code.lower()


def create_employee_account(employee, created_by=None, send_email=True):
    """
    إنشاء حساب مستخدم للموظف

    Returns:
        dict: {
            'success': bool,
            'user': User or None,
            'password': str,
            'message': str,
            'email_sent': bool,
        }
    """
    result = {
        'success':    False,
        'user':       None,
        'password':   '',
        'message':    '',
        'email_sent': False,
    }

    # تحقق لو عنده حساب بالفعل
    if employee.user:
        result['message'] = 'الموظف عنده حساب بالفعل'
        return result

    try:
        username = generate_username(employee)
        password = generate_password()

        # تحقق إن الـ username مش مكرر
        if User.objects.filter(username=username).exists():
            username = f"{username}_{employee.pk}"

        # إنشاء الـ User
        user = User.objects.create_user(
            username=username,
            password=password,
            email=employee.email or '',
            first_name=employee.first_name_ar or '',
            last_name=employee.last_name_ar or '',
            phone=employee.phone or '',
            role='employee',
            company=employee.company,
            must_change_password=True,  # إجباري تغيير أول دخول
        )

        # ربط الـ User بالموظف
        employee.user = user
        employee.save(update_fields=['user'])

        result['success']  = True
        result['user']     = user
        result['password'] = password
        result['message']  = 'تم إنشاء الحساب بنجاح'

        # إرسال إيميل لو فيه إيميل
        if send_email and employee.email:
            try:
                _send_welcome_email(employee, user, password)
                result['email_sent'] = True
            except Exception as e:
                result['email_sent'] = False
                result['message'] += f' (فشل إرسال الإيميل: {e})'

    except Exception as e:
        result['message'] = f'خطأ في إنشاء الحساب: {e}'

    return result


def reset_employee_password(employee, reset_by=None):
    """
    إعادة تعيين كلمة مرور الموظف من المدير

    Returns:
        dict: {
            'success': bool,
            'password': str,
            'message': str,
            'email_sent': bool,
        }
    """
    result = {
        'success':    False,
        'password':   '',
        'message':    '',
        'email_sent': False,
    }

    if not employee.user:
        result['message'] = 'الموظف مالوش حساب'
        return result

    try:
        new_password = generate_password()
        employee.user.set_password(new_password)
        employee.user.must_change_password = True  # إجباري تغيير
        employee.user.save()

        result['success']  = True
        result['password'] = new_password
        result['message']  = 'تم إعادة تعيين كلمة المرور بنجاح'

        # إرسال إيميل لو فيه إيميل
        if employee.email:
            try:
                _send_password_reset_email(employee, new_password)
                result['email_sent'] = True
            except Exception as e:
                result['email_sent'] = False

    except Exception as e:
        result['message'] = f'خطأ: {e}'

    return result


def _send_welcome_email(employee, user, password):
    """إرسال إيميل ترحيبي للموظف الجديد"""
    subject = f'مرحباً بك في {employee.company.name_ar} - بيانات دخولك'
    
    login_url = getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/login/'
    
    message = f"""
مرحباً {employee.full_name_ar}،

تم إنشاء حسابك في نظام MotionHR لإدارة الموارد البشرية.

بيانات تسجيل الدخول:
━━━━━━━━━━━━━━━━━━━━
اسم المستخدم: {user.username}
كلمة المرور:  {password}
رابط الدخول:  {login_url}
━━━━━━━━━━━━━━━━━━━━

⚠️ ملاحظة مهمة:
يرجى تغيير كلمة المرور فور تسجيل دخولك الأول.

لا تشارك بيانات دخولك مع أي شخص.

مع تحيات،
فريق {employee.company.name_ar}
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[employee.email],
        fail_silently=False,
    )


def _send_password_reset_email(employee, new_password):
    """إرسال إيميل إعادة تعيين كلمة المرور"""
    subject = f'إعادة تعيين كلمة المرور - {employee.company.name_ar}'
    
    login_url = getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/login/'
    
    message = f"""
مرحباً {employee.full_name_ar}،

تم إعادة تعيين كلمة مرور حسابك.

بيانات تسجيل الدخول الجديدة:
━━━━━━━━━━━━━━━━━━━━
اسم المستخدم: {employee.user.username}
كلمة المرور:  {new_password}
رابط الدخول:  {login_url}
━━━━━━━━━━━━━━━━━━━━

⚠️ يرجى تغيير كلمة المرور فور تسجيل دخولك.

مع تحيات،
فريق {employee.company.name_ar}
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[employee.email],
        fail_silently=False,
    )
'''

create_file(
    os.path.join(BASE_DIR, 'employees', 'account_utils.py'),
    account_utils
)


# ════════════════════════════════════════════════════════════
# 4. تحديث employees/views.py
#    إضافة views للحسابات
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employees/views.py...")

views_path = os.path.join(BASE_DIR, 'employees', 'views.py')
views_content = read_file(views_path)

employee_account_views = '''

# ════════════════════════════════════════════════════════════
# إدارة حسابات الموظفين
# ════════════════════════════════════════════════════════════

from .account_utils import create_employee_account, reset_employee_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


@login_required
@require_POST
def create_account_view(request, pk):
    """
    إنشاء حساب للموظف
    POST /employees/<pk>/create-account/
    """
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)

    send_email = request.POST.get('send_email', 'true') == 'true'
    result = create_employee_account(
        employee=employee,
        created_by=request.user,
        send_email=send_email,
    )

    if result['success']:
        messages.success(
            request,
            f'✅ تم إنشاء الحساب بنجاح - اسم المستخدم: {result["user"].username}'
        )
        # لو مفيش إيميل - نحوله لصفحة طباعة البيانات
        if not employee.email or not result['email_sent']:
            return redirect(
                reverse('employees:print_credentials', args=[pk])
                + f'?pwd={result["password"]}'
            )
    else:
        messages.error(request, f'❌ {result["message"]}')

    return redirect('employees:employee_detail', pk=pk)


@login_required
@require_POST
def reset_password_view(request, pk):
    """
    إعادة تعيين كلمة مرور الموظف
    POST /employees/<pk>/reset-password/
    """
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)

    result = reset_employee_password(
        employee=employee,
        reset_by=request.user,
    )

    if result['success']:
        messages.success(request, '✅ تم إعادة تعيين كلمة المرور بنجاح')
        # لو مفيش إيميل - نحوله لصفحة طباعة البيانات
        if not employee.email or not result['email_sent']:
            return redirect(
                reverse('employees:print_credentials', args=[pk])
                + f'?pwd={result["password"]}&reset=1'
            )
    else:
        messages.error(request, f'❌ {result["message"]}')

    return redirect('employees:employee_detail', pk=pk)


@login_required
def print_credentials_view(request, pk):
    """
    صفحة طباعة بيانات الدخول
    GET /employees/<pk>/print-credentials/
    """
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)

    # كلمة السر بتيجي من الـ URL مؤقتاً (بس في session أحسن)
    password = request.GET.get('pwd', '••••••••••')
    is_reset  = request.GET.get('reset', '0') == '1'

    context = {
        'employee':   employee,
        'username':   employee.user.username if employee.user else '',
        'password':   password,
        'is_reset':   is_reset,
        'page_title': 'بيانات تسجيل الدخول',
    }
    return render(request, 'employees/print_credentials.html', context)


@login_required
def deactivate_account_view(request, pk):
    """
    تعطيل حساب الموظف
    POST /employees/<pk>/deactivate-account/
    """
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)

    if request.method == 'POST':
        if employee.user:
            employee.user.is_active = False
            employee.user.save()
            messages.success(request, '✅ تم تعطيل الحساب')
        else:
            messages.warning(request, 'الموظف مالوش حساب')

    return redirect('employees:employee_detail', pk=pk)


@login_required
def activate_account_view(request, pk):
    """
    تفعيل حساب الموظف
    POST /employees/<pk>/activate-account/
    """
    employee = get_object_or_404(Employee, pk=pk, company=request.user.company)

    if request.method == 'POST':
        if employee.user:
            employee.user.is_active = True
            employee.user.save()
            messages.success(request, '✅ تم تفعيل الحساب')
        else:
            messages.warning(request, 'الموظف مالوش حساب')

    return redirect('employees:employee_detail', pk=pk)
'''

if 'create_account_view' not in views_content:
    # نضيف imports مطلوبة لو مش موجودة
    if 'from django.urls import reverse' not in views_content:
        views_content = views_content.replace(
            'from django.shortcuts import',
            'from django.urls import reverse\nfrom django.shortcuts import'
        )
        write_file(views_path, views_content)

    append_file(views_path, employee_account_views)
else:
    print("  ℹ️  account views موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 5. تحديث employees/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employees/urls.py...")

urls_path = os.path.join(BASE_DIR, 'employees', 'urls.py')
urls_content = read_file(urls_path)

new_urls_to_add = [
    ("create-account",    "create_account_view",    "create_account"),
    ("reset-password",    "reset_password_view",     "reset_password"),
    ("print-credentials", "print_credentials_view",  "print_credentials"),
    ("deactivate",        "deactivate_account_view", "deactivate_account"),
    ("activate",          "activate_account_view",   "activate_account"),
]

for url_path, view_name, url_name in new_urls_to_add:
    url_line = f"    path('<int:pk>/{url_path}/', views.{view_name}, name='{url_name}'),"
    if url_name not in urls_content:
        # أضف قبل آخر ]
        urls_content = urls_content.rstrip()
        if urls_content.endswith(']'):
            urls_content = urls_content[:-1] + f"\n{url_line}\n]"
        write_file(urls_path, urls_content)
        urls_content = read_file(urls_path)  # نقرأ التحديث
        print(f"  ✅ تم إضافة URL: {url_name}")
    else:
        print(f"  ℹ️  URL موجود: {url_name}")


# ════════════════════════════════════════════════════════════
# 6. إنشاء صفحة طباعة بيانات الدخول
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء print_credentials.html...")

print_credentials_template = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>بيانات تسجيل الدخول - {{ employee.full_name_ar }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Cairo', sans-serif;
      background: #f5f5f5;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 40px;
      max-width: 500px;
      width: 100%;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      border-top: 6px solid #06B6D4;
    }
    .logo {
      text-align: center;
      margin-bottom: 24px;
    }
    .logo h1 {
      font-size: 2rem;
      font-weight: 900;
      color: #06B6D4;
    }
    .logo p {
      color: #666;
      font-size: 0.9rem;
    }
    .divider {
      border: none;
      border-top: 2px dashed #e5e7eb;
      margin: 20px 0;
    }
    .employee-name {
      text-align: center;
      margin-bottom: 24px;
    }
    .employee-name h2 {
      font-size: 1.4rem;
      font-weight: 700;
      color: #1f2937;
    }
    .employee-name span {
      color: #6b7280;
      font-size: 0.9rem;
    }
    .credentials-box {
      background: #f0f9ff;
      border: 2px solid #06B6D4;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .credentials-box h3 {
      color: #0e7490;
      font-size: 1rem;
      margin-bottom: 16px;
      text-align: center;
    }
    .cred-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #e0f2fe;
    }
    .cred-row:last-child { border-bottom: none; }
    .cred-label {
      color: #6b7280;
      font-size: 0.9rem;
    }
    .cred-value {
      font-weight: 700;
      color: #1f2937;
      font-size: 1rem;
      letter-spacing: 1px;
      direction: ltr;
    }
    .warning-box {
      background: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 20px;
      font-size: 0.85rem;
      color: #856404;
    }
    .warning-box strong { display: block; margin-bottom: 4px; }
    .login-url {
      text-align: center;
      background: #f9fafb;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 24px;
      font-size: 0.85rem;
      color: #374151;
      direction: ltr;
    }
    .signature-area {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 30px;
    }
    .sig-box {
      text-align: center;
      padding: 16px;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
    }
    .sig-box p { font-size: 0.85rem; color: #6b7280; margin-bottom: 30px; }
    .sig-line {
      border-top: 1px solid #374151;
      padding-top: 6px;
      font-size: 0.8rem;
      color: #374151;
      font-weight: 600;
    }
    .print-btn {
      display: block;
      width: 100%;
      padding: 12px;
      background: #06B6D4;
      color: white;
      border: none;
      border-radius: 8px;
      font-family: 'Cairo', sans-serif;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      margin-bottom: 10px;
      text-align: center;
    }
    .back-btn {
      display: block;
      width: 100%;
      padding: 10px;
      background: transparent;
      color: #6b7280;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      font-family: 'Cairo', sans-serif;
      font-size: 0.9rem;
      cursor: pointer;
      text-align: center;
      text-decoration: none;
    }
    @media print {
      body { background: white; padding: 0; }
      .card { box-shadow: none; border-radius: 0; }
      .print-btn, .back-btn { display: none; }
    }
  </style>
</head>
<body>

<div class="card">

  <!-- Logo -->
  <div class="logo">
    <h1>MotionHR</h1>
    <p>{{ employee.company.name_ar }}</p>
  </div>

  <hr class="divider">

  <!-- اسم الموظف -->
  <div class="employee-name">
    <h2>{{ employee.full_name_ar }}</h2>
    <span>{{ employee.employee_code }} | {{ employee.job_title.name_ar|default:"" }}</span>
  </div>

  <!-- بيانات الدخول -->
  <div class="credentials-box">
    <h3>🔐 بيانات تسجيل الدخول</h3>

    <div class="cred-row">
      <span class="cred-label">اسم المستخدم</span>
      <span class="cred-value">{{ username }}</span>
    </div>

    <div class="cred-row">
      <span class="cred-label">كلمة المرور</span>
      <span class="cred-value">{{ password }}</span>
    </div>

  </div>

  <!-- رابط الدخول -->
  <div class="login-url">
    🔗 رابط الدخول: <strong>http://your-domain.com/login/</strong>
  </div>

  <!-- تحذير -->
  <div class="warning-box">
    <strong>⚠️ ملاحظة مهمة:</strong>
    {% if is_reset %}
      تم إعادة تعيين كلمة المرور. يرجى تغييرها فور تسجيل الدخول.
    {% else %}
      هذه كلمة مرور مؤقتة. يجب تغييرها فور تسجيل الدخول الأول.
    {% endif %}
    <br>لا تشارك هذه البيانات مع أي شخص.
  </div>

  <!-- التوقيعات -->
  <div class="signature-area">
    <div class="sig-box">
      <p>توقيع مسؤول HR</p>
      <div class="sig-line">الاسم والتوقيع</div>
    </div>
    <div class="sig-box">
      <p>توقيع الموظف (استلمت)</p>
      <div class="sig-line">الاسم والتوقيع</div>
    </div>
  </div>

  <hr class="divider">

  <!-- أزرار -->
  <button class="print-btn" onclick="window.print()">
    🖨️ طباعة
  </button>
  <a href="{% url 'employees:employee_detail' employee.pk %}" class="back-btn">
    ← رجوع لملف الموظف
  </a>

</div>

</body>
</html>
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'employees', 'print_credentials.html'),
    print_credentials_template
)


# ════════════════════════════════════════════════════════════
# 7. تحديث employees/detail.html
#    إضافة تبويب "الحساب" وأزرار إدارة الحساب
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employee detail.html...")

detail_path = os.path.join(BASE_DIR, 'templates', 'employees', 'detail.html')

if os.path.exists(detail_path):
    detail_content = read_file(detail_path)

    # إضافة تبويب الحساب لو مش موجود
    if 'tab-account' not in detail_content:

        # إضافة تبويب في القائمة
        account_tab_btn = """
              <li class="nav-item" role="presentation">
                <button class="nav-link d-flex align-items-center gap-2"
                        id="account-tab"
                        data-bs-toggle="tab"
                        data-bs-target="#tab-account"
                        type="button" role="tab">
                  <i class="bi bi-person-badge"></i>
                  <span>الحساب</span>
                </button>
              </li>"""

        # نضيف التبويب في نهاية قائمة التبويبات
        # نبحث عن آخر </li> في منطقة التبويبات
        if 'nav-tabs' in detail_content or 'nav-link' in detail_content:
            # نضيف قبل إغلاق قائمة التبويبات
            tab_list_end = '</ul>'
            first_occurrence = detail_content.find(tab_list_end)
            if first_occurrence != -1:
                detail_content = (
                    detail_content[:first_occurrence] +
                    account_tab_btn + '\n            ' +
                    detail_content[first_occurrence:]
                )

        # محتوى تبويب الحساب
        account_tab_content = """
              <!-- ══ تبويب الحساب ══ -->
              <div class="tab-pane fade" id="tab-account" role="tabpanel">
                <div class="row justify-content-center">
                  <div class="col-lg-8">

                    {% if employee.user %}
                    <!-- الحساب موجود -->
                    <div class="card border-0 shadow-sm mb-4">
                      <div class="card-body p-4">

                        <div class="d-flex align-items-center mb-4">
                          <div class="rounded-circle d-flex align-items-center justify-content-center me-3"
                               style="width:56px;height:56px;background:#e0f7fa;">
                            <i class="bi bi-person-check-fill fs-3" style="color:#06B6D4;"></i>
                          </div>
                          <div>
                            <h5 class="fw-bold mb-0">الحساب نشط</h5>
                            <span class="badge {% if employee.user.is_active %}bg-success{% else %}bg-danger{% endif %}">
                              {% if employee.user.is_active %}✅ مفعّل{% else %}❌ موقوف{% endif %}
                            </span>
                          </div>
                        </div>

                        <!-- بيانات الحساب -->
                        <div class="row g-3 mb-4">
                          <div class="col-md-6">
                            <label class="text-muted small">اسم المستخدم</label>
                            <div class="fw-bold font-monospace">{{ employee.user.username }}</div>
                          </div>
                          <div class="col-md-6">
                            <label class="text-muted small">الدور</label>
                            <div class="fw-bold">{{ employee.user.get_role_display }}</div>
                          </div>
                          <div class="col-md-6">
                            <label class="text-muted small">آخر دخول</label>
                            <div class="fw-bold">
                              {{ employee.user.last_login|date:"d/m/Y H:i"|default:"لم يدخل بعد" }}
                            </div>
                          </div>
                          <div class="col-md-6">
                            <label class="text-muted small">تغيير كلمة المرور مطلوب</label>
                            <div class="fw-bold">
                              {% if employee.user.must_change_password %}
                                <span class="text-warning">⚠️ نعم</span>
                              {% else %}
                                <span class="text-success">✅ لا</span>
                              {% endif %}
                            </div>
                          </div>
                        </div>

                        <!-- أزرار الإجراءات -->
                        <div class="d-flex flex-wrap gap-2">

                          <!-- إعادة تعيين كلمة المرور -->
                          <form method="post"
                                action="{% url 'employees:reset_password' employee.pk %}"
                                onsubmit="return confirm('إعادة تعيين كلمة المرور؟')">
                            {% csrf_token %}
                            <button type="submit" class="btn btn-warning btn-sm">
                              <i class="bi bi-key me-1"></i>
                              إعادة تعيين كلمة المرور
                            </button>
                          </form>

                          <!-- تعطيل / تفعيل -->
                          {% if employee.user.is_active %}
                          <form method="post"
                                action="{% url 'employees:deactivate_account' employee.pk %}"
                                onsubmit="return confirm('تعطيل الحساب؟')">
                            {% csrf_token %}
                            <button type="submit" class="btn btn-danger btn-sm">
                              <i class="bi bi-slash-circle me-1"></i>
                              تعطيل الحساب
                            </button>
                          </form>
                          {% else %}
                          <form method="post"
                                action="{% url 'employees:activate_account' employee.pk %}"
                                onsubmit="return confirm('تفعيل الحساب؟')">
                            {% csrf_token %}
                            <button type="submit" class="btn btn-success btn-sm">
                              <i class="bi bi-check-circle me-1"></i>
                              تفعيل الحساب
                            </button>
                          </form>
                          {% endif %}

                          <!-- طباعة بيانات الدخول -->
                          <a href="{% url 'employees:print_credentials' employee.pk %}"
                             class="btn btn-outline-secondary btn-sm" target="_blank">
                            <i class="bi bi-printer me-1"></i>
                            طباعة بيانات الدخول
                          </a>

                        </div>
                      </div>
                    </div>

                    {% else %}
                    <!-- مفيش حساب -->
                    <div class="card border-0 shadow-sm">
                      <div class="card-body text-center py-5">
                        <i class="bi bi-person-x" style="font-size:4rem;color:#d1d5db;"></i>
                        <h5 class="mt-3 fw-bold text-muted">لا يوجد حساب لهذا الموظف</h5>
                        <p class="text-muted">أنشئ حساب للموظف للسماح له بتسجيل الدخول للنظام</p>

                        <!-- فورم إنشاء حساب -->
                        <form method="post"
                              action="{% url 'employees:create_account' employee.pk %}">
                          {% csrf_token %}
                          <div class="d-flex align-items-center justify-content-center gap-3 mt-3">
                            <div class="form-check">
                              <input class="form-check-input" type="checkbox"
                                     name="send_email" id="sendEmail"
                                     value="true"
                                     {% if employee.email %}checked{% endif %}
                                     {% if not employee.email %}disabled{% endif %}>
                              <label class="form-check-label" for="sendEmail">
                                إرسال بيانات الدخول بالإيميل
                                {% if not employee.email %}
                                  <small class="text-danger">(لا يوجد إيميل)</small>
                                {% endif %}
                              </label>
                            </div>
                          </div>
                          <button type="submit" class="btn btn-lg mt-3 text-white"
                                  style="background:#06B6D4;"
                                  onclick="return confirm('إنشاء حساب للموظف؟')">
                            <i class="bi bi-person-plus me-2"></i>
                            إنشاء حساب
                          </button>
                        </form>

                      </div>
                    </div>
                    {% endif %}

                  </div>
                </div>
              </div>"""

        # نضيف محتوى التبويب قبل إغلاق div الـ tab-content
        tab_content_end = '</div>\n        </div>'  # نهاية الـ tab-content
        if 'tab-content' in detail_content:
            # نلاقي آخر إغلاق للـ tab-content
            last_tab_content = detail_content.rfind('</div>\n        </div>')
            if last_tab_content != -1:
                detail_content = (
                    detail_content[:last_tab_content] +
                    account_tab_content +
                    '\n' +
                    detail_content[last_tab_content:]
                )

        write_file(detail_path, detail_content)
        print("  ✅ تم إضافة تبويب الحساب في detail.html")
    else:
        print("  ℹ️  تبويب الحساب موجود بالفعل")
else:
    print("  ⚠️  detail.html مش موجود!")


# ════════════════════════════════════════════════════════════
# 8. Middleware لإجبار تغيير كلمة المرور
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء middleware تغيير كلمة المرور...")

middleware_path = os.path.join(BASE_DIR, 'accounts', 'middleware.py')

force_change_middleware = '''"""
middleware.py - accounts
إجبار تغيير كلمة المرور عند أول دخول
"""

from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    لو المستخدم must_change_password = True
    يتحول أوتوماتيك لصفحة تغيير كلمة المرور
    """

    # الصفحات المسموح بها بدون تغيير
    EXEMPT_URLS = [
        '/password-change/',
        '/password-change/done/',
        '/logout/',
        '/login/',
        '/admin/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and hasattr(request.user, 'must_change_password')
            and request.user.must_change_password
            and not request.user.is_superuser
        ):
            # تحقق إن المسار مش معفي
            path = request.path_info
            exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)

            if not exempt:
                return redirect('/password-change/')

        return self.get_response(request)
'''

create_file(middleware_path, force_change_middleware)


# ════════════════════════════════════════════════════════════
# 9. تحديث password_change view
#    يعمل must_change_password = False بعد التغيير
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/views.py...")

accounts_views_path = os.path.join(BASE_DIR, 'accounts', 'views.py')
accounts_views = read_file(accounts_views_path)

password_change_signal = '''

# ─────────────────────────────────────────────
# بعد تغيير كلمة المرور - نلغي الإجبار
# ─────────────────────────────────────────────
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy


class CustomPasswordChangeView(PasswordChangeView):
    """
    Override لـ PasswordChangeView
    يعمل must_change_password = False بعد التغيير
    """
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        # إلغاء إجبار التغيير
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=['must_change_password'])
        return response
'''

if 'CustomPasswordChangeView' not in accounts_views:
    append_file(accounts_views_path, password_change_signal)
else:
    print("  ℹ️  CustomPasswordChangeView موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 10. تحديث motionhr/settings.py
#     إضافة ForcePasswordChangeMiddleware
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings.py - إضافة Middleware...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')
settings_content = read_file(settings_path)

if 'ForcePasswordChangeMiddleware' not in settings_content:
    old = "    'core.middleware.TenantMiddleware',"
    new = """    'core.middleware.TenantMiddleware',
    'accounts.middleware.ForcePasswordChangeMiddleware',"""
    settings_content = settings_content.replace(old, new)
    write_file(settings_path, settings_content)
else:
    print("  ℹ️  Middleware موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 11. تحديث motionhr/urls.py
#     استخدام CustomPasswordChangeView
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث motionhr/urls.py...")

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

if 'CustomPasswordChangeView' not in main_urls_content:
    old = "from django.contrib.auth import views as auth_views"
    new = """from django.contrib.auth import views as auth_views
from accounts.views import CustomPasswordChangeView"""

    if old in main_urls_content:
        main_urls_content = main_urls_content.replace(old, new)

        # استبدال PasswordChangeView القديم بالجديد
        main_urls_content = main_urls_content.replace(
            "auth_views.PasswordChangeView",
            "CustomPasswordChangeView"
        )
        write_file(main_urls_path, main_urls_content)
    else:
        print("  ⚠️  مش لاقي auth_views import - تحقق يدوياً")
else:
    print("  ℹ️  CustomPasswordChangeView موجود في urls.py")


# ════════════════════════════════════════════════════════════
# 12. تحديث password_change.html
#     إضافة رسالة لو must_change_password
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث password_change.html...")

pwd_change_path = os.path.join(
    BASE_DIR, 'templates', 'accounts', 'password_change.html'
)

if os.path.exists(pwd_change_path):
    pwd_content = read_file(pwd_change_path)

    if 'must_change_password' not in pwd_content:
        # نضيف تنبيه في أول الصفحة
        force_change_alert = """
{% if user.must_change_password %}
<div class="alert alert-warning border-0 shadow-sm mb-4">
  <div class="d-flex align-items-center">
    <i class="bi bi-exclamation-triangle-fill text-warning fs-4 me-3"></i>
    <div>
      <strong>تغيير كلمة المرور مطلوب</strong>
      <p class="mb-0 small">يجب تغيير كلمة المرور المؤقتة قبل الاستمرار في استخدام النظام.</p>
    </div>
  </div>
</div>
{% endif %}
"""
        # نضيف بعد {% block content %} أو في أول الفورم
        if '{% block content %}' in pwd_content:
            pwd_content = pwd_content.replace(
                '{% block content %}',
                '{% block content %}\n' + force_change_alert
            )
        elif '<form' in pwd_content:
            pwd_content = pwd_content.replace(
                '<form',
                force_change_alert + '\n<form',
                1
            )

        write_file(pwd_change_path, pwd_content)
        print("  ✅ تم إضافة تنبيه تغيير كلمة المرور")
    else:
        print("  ℹ️  التنبيه موجود بالفعل")
else:
    print("  ⚠️  password_change.html مش موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 15 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ accounts/models.py - حقل must_change_password
  2.  ✅ Migration جديد للحقل
  3.  ✅ employees/account_utils.py - أدوات الحسابات
  4.  ✅ employees/views.py - views إدارة الحسابات
  5.  ✅ employees/urls.py - URLs جديدة
  6.  ✅ print_credentials.html - طباعة بيانات الدخول
  7.  ✅ detail.html - تبويب الحساب
  8.  ✅ accounts/middleware.py - إجبار تغيير كلمة المرور
  9.  ✅ accounts/views.py - CustomPasswordChangeView
  10. ✅ settings.py - إضافة Middleware
  11. ✅ motionhr/urls.py - CustomPasswordChangeView
  12. ✅ password_change.html - تنبيه التغيير

🔗 URLs الجديدة:
  /employees/<pk>/create-account/    ← إنشاء حساب
  /employees/<pk>/reset-password/    ← إعادة تعيين كلمة المرور
  /employees/<pk>/print-credentials/ ← طباعة بيانات الدخول
  /employees/<pk>/deactivate/        ← تعطيل الحساب
  /employees/<pk>/activate/          ← تفعيل الحساب

⚠️  مطلوب تشغيل:
  python manage.py migrate

🚀 الخطوة الجاية: Patch 16 - Login Methods Feature-Based
""")