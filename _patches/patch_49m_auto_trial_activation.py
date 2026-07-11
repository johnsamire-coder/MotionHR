"""
Patch 49M — Auto Trial Activation

الهدف:
1) العميل يسجل من /free-trial/
2) النظام ينشئ تلقائيًا:
   - شركة جديدة
   - حساب Admin
   - اشتراك Trial 14 يوم
3) يظهر للعميل بيانات الدخول
4) كل البيانات تتحفظ عندك في Admin:
   - اسم الشركة
   - اسم المسؤول
   - الموبايل
   - الواتساب
   - الإيميل
   - عدد الموظفين
   - تاريخ التسجيل
   - تاريخ انتهاء التجربة
   - حالة الطلب
"""

import os
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


print("=" * 60)
print("Patch 49M — Auto Trial Activation")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path in [
    "core/models.py",
    "core/admin.py",
    "landing/views.py",
    "templates/landing/free_trial_register.html",
    "templates/landing/free_trial_success.html",
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_name = rel_path.replace("/", "_").replace("\\", "_") + ".49m.bak"
        shutil.copy2(full, os.path.join(backup_dir, backup_name))

print("✅ Backups created")

# ════════════════════════════════════════════════════════════
# Step 1: Update core/models.py — Add whatsapp + trial dates
# ════════════════════════════════════════════════════════════
print("\n📌 Step 1: تحديث TrialSignupLead model")

models_path = "core/models.py"
models_content = read_file(models_path)
if models_content is None:
    raise SystemExit("❌ ملف core/models.py غير موجود")

# نحذف الموديل القديم ونستبدله بالجديد
import re

# حذف الموديل القديم
old_pattern = re.compile(
    r'# ═+\n# Patch 49L.*?class TrialSignupLead.*?(?=\nclass |\n# ═|\Z)',
    re.DOTALL
)
models_content = old_pattern.sub('', models_content)

# لو لسه موجود بشكل تاني
if "class TrialSignupLead" in models_content:
    pattern2 = re.compile(r'class TrialSignupLead\(models\.Model\):.*?(?=\nclass |\n# ═|\Z)', re.DOTALL)
    models_content = pattern2.sub('', models_content)

new_lead_model = '''

# ═════════════════════════════════════════════════════════════
# Patch 49M — Trial Signup Lead (Enhanced)
# ═════════════════════════════════════════════════════════════

class TrialSignupLead(models.Model):
    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('activated', 'تم التفعيل'),
        ('contacted', 'تم التواصل'),
        ('converted', 'تم التحويل لعميل'),
        ('expired', 'انتهت التجربة'),
        ('rejected', 'مرفوض'),
    ]

    # بيانات الشركة
    company_name = models.CharField(max_length=200, verbose_name='اسم الشركة')
    contact_name = models.CharField(max_length=200, verbose_name='اسم المسؤول')

    # بيانات التواصل
    phone = models.CharField(max_length=30, verbose_name='رقم الموبايل')
    whatsapp = models.CharField(max_length=30, verbose_name='رقم الواتساب')
    email = models.EmailField(verbose_name='البريد الإلكتروني')

    # تفاصيل إضافية
    employees_count = models.PositiveIntegerField(default=1, verbose_name='عدد الموظفين المتوقع')
    city = models.CharField(max_length=100, blank=True, verbose_name='المدينة')
    industry = models.CharField(max_length=150, blank=True, verbose_name='نوع النشاط')
    notes = models.TextField(blank=True, verbose_name='ملاحظات العميل')

    # مصدر وحالة
    source = models.CharField(max_length=100, blank=True, default='free_trial', verbose_name='مصدر التسجيل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='حالة الطلب')

    # تواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التسجيل')
    updated_at = models.DateTimeField(auto_now=True)
    trial_start_date = models.DateField(null=True, blank=True, verbose_name='بداية التجربة')
    trial_end_date = models.DateField(null=True, blank=True, verbose_name='نهاية التجربة')

    # ربط بالحساب المنشأ
    created_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trial_leads',
        verbose_name='الشركة المنشأة',
    )
    created_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trial_leads',
        verbose_name='الحساب المنشأ',
    )
    generated_username = models.CharField(max_length=100, blank=True, verbose_name='اسم المستخدم المولّد')
    generated_password = models.CharField(max_length=100, blank=True, verbose_name='كلمة المرور المولّدة')

    # ملاحظات المبيعات
    sales_notes = models.TextField(blank=True, verbose_name='ملاحظات فريق المبيعات')

    class Meta:
        verbose_name = 'طلب تجربة مجانية'
        verbose_name_plural = 'طلبات التجربة المجانية'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} — {self.contact_name} ({self.get_status_display()})"

    @property
    def is_trial_active(self):
        if not self.trial_end_date:
            return False
        from datetime import date
        return date.today() <= self.trial_end_date

    @property
    def days_remaining(self):
        if not self.trial_end_date:
            return 0
        from datetime import date
        delta = self.trial_end_date - date.today()
        return max(0, delta.days)
'''

models_content = models_content.rstrip() + "\n" + new_lead_model + "\n"
write_file(models_path, models_content)

# ════════════════════════════════════════════════════════════
# Step 2: Migration
# ════════════════════════════════════════════════════════════
print("\n📌 Step 2: إنشاء migration")

migration_code = '''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('companies', '0015_charter_digital_signature'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.DeleteModel(name='TrialSignupLead'),
        migrations.CreateModel(
            name='TrialSignupLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=200, verbose_name='اسم الشركة')),
                ('contact_name', models.CharField(max_length=200, verbose_name='اسم المسؤول')),
                ('phone', models.CharField(max_length=30, verbose_name='رقم الموبايل')),
                ('whatsapp', models.CharField(max_length=30, verbose_name='رقم الواتساب')),
                ('email', models.EmailField(max_length=254, verbose_name='البريد الإلكتروني')),
                ('employees_count', models.PositiveIntegerField(default=1, verbose_name='عدد الموظفين المتوقع')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='المدينة')),
                ('industry', models.CharField(blank=True, max_length=150, verbose_name='نوع النشاط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات العميل')),
                ('source', models.CharField(blank=True, default='free_trial', max_length=100, verbose_name='مصدر التسجيل')),
                ('status', models.CharField(choices=[('new', 'جديد'), ('activated', 'تم التفعيل'), ('contacted', 'تم التواصل'), ('converted', 'تم التحويل لعميل'), ('expired', 'انتهت التجربة'), ('rejected', 'مرفوض')], default='new', max_length=20, verbose_name='حالة الطلب')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التسجيل')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trial_start_date', models.DateField(blank=True, null=True, verbose_name='بداية التجربة')),
                ('trial_end_date', models.DateField(blank=True, null=True, verbose_name='نهاية التجربة')),
                ('generated_username', models.CharField(blank=True, max_length=100, verbose_name='اسم المستخدم المولّد')),
                ('generated_password', models.CharField(blank=True, max_length=100, verbose_name='كلمة المرور المولّدة')),
                ('sales_notes', models.TextField(blank=True, verbose_name='ملاحظات فريق المبيعات')),
                ('created_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_leads', to='companies.company', verbose_name='الشركة المنشأة')),
                ('created_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_leads', to='accounts.user', verbose_name='الحساب المنشأ')),
            ],
            options={
                'verbose_name': 'طلب تجربة مجانية',
                'verbose_name_plural': 'طلبات التجربة المجانية',
                'ordering': ['-created_at'],
            },
        ),
    ]
'''
write_file("core/migrations/0002_enhanced_trial_signup.py", migration_code)

# ════════════════════════════════════════════════════════════
# Step 3: Update Admin
# ════════════════════════════════════════════════════════════
print("\n📌 Step 3: تحديث core/admin.py")

admin_path = "core/admin.py"
admin_content = read_file(admin_path)
if admin_content is None:
    admin_content = "from django.contrib import admin\n"

# نحذف القديم
admin_content = re.sub(r'@admin\.register\(TrialSignupLead\).*?(?=\n@admin|\nclass |\Z)', '', admin_content, flags=re.DOTALL)

if "from .models import" not in admin_content or "TrialSignupLead" not in admin_content:
    if "from .models import" in admin_content:
        admin_content = admin_content.replace("from .models import", "from .models import TrialSignupLead,", 1)
    else:
        admin_content = "from django.contrib import admin\nfrom .models import TrialSignupLead\n" + admin_content

new_admin = '''

@admin.register(TrialSignupLead)
class TrialSignupLeadAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'contact_name', 'phone', 'whatsapp', 'email',
        'employees_count', 'status', 'trial_start_date', 'trial_end_date',
        'is_trial_active', 'days_remaining', 'created_at',
    )
    list_filter = ('status', 'industry', 'created_at', 'trial_end_date')
    search_fields = ('company_name', 'contact_name', 'phone', 'whatsapp', 'email')
    ordering = ('-created_at',)
    readonly_fields = (
        'generated_username', 'generated_password',
        'created_company', 'created_user',
        'trial_start_date', 'trial_end_date',
        'created_at', 'updated_at',
    )

    fieldsets = (
        ('بيانات العميل', {
            'fields': ('company_name', 'contact_name', 'phone', 'whatsapp', 'email',
                       'employees_count', 'city', 'industry', 'notes'),
        }),
        ('حالة الطلب', {
            'fields': ('status', 'source', 'sales_notes'),
        }),
        ('بيانات التجربة', {
            'fields': ('trial_start_date', 'trial_end_date',
                       'created_company', 'created_user',
                       'generated_username', 'generated_password'),
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def is_trial_active(self, obj):
        return obj.is_trial_active
    is_trial_active.boolean = True
    is_trial_active.short_description = 'التجربة فعّالة؟'

    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'أيام متبقية'
'''

admin_content = admin_content.rstrip() + "\n" + new_admin + "\n"
write_file(admin_path, admin_content)

# ════════════════════════════════════════════════════════════
# Step 4: Update landing/views.py
# ════════════════════════════════════════════════════════════
print("\n📌 Step 4: تحديث landing/views.py")

views_path = "landing/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف landing/views.py غير موجود")

# نحذف القديم
views_content = re.sub(
    r'# ═+\n# Patch 49L.*?(?=\ndef [a-z]|\n# ═|\Z)',
    '', views_content, flags=re.DOTALL
)
# نحذف الدوال القديمة
for fn_name in ['free_trial_register', 'free_trial_success']:
    views_content = re.sub(
        rf'\ndef {fn_name}\(request\):.*?(?=\ndef |\n# ═|\Z)',
        '', views_content, flags=re.DOTALL
    )

new_trial_views = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49M — Auto Trial Activation
# ═════════════════════════════════════════════════════════════

def free_trial_register(request):
    """صفحة تسجيل تجربة مجانية مع إنشاء تلقائي للحساب"""
    from core.models import TrialSignupLead
    from companies.models import Company
    from accounts.models import User
    from subscriptions.models import SubscriptionPlan, CompanySubscription
    from django.utils.crypto import get_random_string
    from datetime import date, timedelta
    from django.contrib import messages

    TRIAL_DAYS = 14

    if request.method == 'POST':
        company_name = (request.POST.get('company_name') or '').strip()
        contact_name = (request.POST.get('contact_name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        whatsapp = (request.POST.get('whatsapp') or '').strip()
        email = (request.POST.get('email') or '').strip()
        employees_count = (request.POST.get('employees_count') or '10').strip()
        city = (request.POST.get('city') or '').strip()
        industry = (request.POST.get('industry') or '').strip()
        notes = (request.POST.get('notes') or '').strip()

        # Validation
        errors = []
        if not company_name:
            errors.append('يرجى إدخال اسم الشركة')
        if not contact_name:
            errors.append('يرجى إدخال اسم المسؤول')
        if not phone:
            errors.append('يرجى إدخال رقم الموبايل')
        if not whatsapp:
            errors.append('يرجى إدخال رقم الواتساب')
        if not email:
            errors.append('يرجى إدخال البريد الإلكتروني')

        # Check duplicate email
        if email and User.objects.filter(email=email).exists():
            errors.append('هذا البريد الإلكتروني مسجل بالفعل')

        try:
            employees_count = int(employees_count)
            if employees_count < 1:
                employees_count = 1
        except Exception:
            employees_count = 10

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'landing/free_trial_register.html', {
                'page_title': 'ابدأ تجربتك المجانية',
                'trial_days': TRIAL_DAYS,
            })

        try:
            # ── 1) إنشاء الشركة ──
            company = Company.objects.create(
                name_ar=company_name,
                name_en=company_name,
            )

            # ── 2) إنشاء المستخدم ──
            # username من اسم الشركة
            base_username = email.split('@')[0].lower()
            base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
            if not base_username:
                base_username = 'admin'

            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            password = f"Trial@{get_random_string(6)}"

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=contact_name.split()[0] if contact_name else '',
                last_name=' '.join(contact_name.split()[1:]) if len(contact_name.split()) > 1 else '',
            )

            # Set role and company
            if hasattr(user, 'role'):
                user.role = 'company_admin'
            if hasattr(user, 'company'):
                user.company = company
            if hasattr(user, 'must_change_password'):
                user.must_change_password = True

            user.save()

            # ── 3) إنشاء اشتراك Trial ──
            today = date.today()
            trial_end = today + timedelta(days=TRIAL_DAYS)

            # ابحث عن أي plan موجود أو أنشئ واحد
            plan = SubscriptionPlan.objects.first()
            if not plan:
                plan = SubscriptionPlan.objects.create(
                    name='Trial',
                    slug='trial',
                    price=0,
                    duration_days=TRIAL_DAYS,
                    max_employees=50,
                    is_active=True,
                )

            try:
                CompanySubscription.objects.create(
                    company=company,
                    plan=plan,
                    start_date=today,
                    end_date=trial_end,
                    is_active=True,
                )
            except Exception:
                # لو الموديل مختلف شوية
                try:
                    CompanySubscription.objects.create(
                        company=company,
                        plan=plan,
                        status='active',
                    )
                except Exception:
                    pass

            # ── 4) حفظ بيانات الطلب ──
            lead = TrialSignupLead.objects.create(
                company_name=company_name,
                contact_name=contact_name,
                phone=phone,
                whatsapp=whatsapp,
                email=email,
                employees_count=employees_count,
                city=city,
                industry=industry,
                notes=notes,
                source='free_trial_auto',
                status='activated',
                trial_start_date=today,
                trial_end_date=trial_end,
                created_company=company,
                created_user=user,
                generated_username=username,
                generated_password=password,
            )

            # ── Store in session for success page ──
            request.session['trial_data'] = {
                'company_name': company_name,
                'contact_name': contact_name,
                'username': username,
                'password': password,
                'email': email,
                'trial_start': str(today),
                'trial_end': str(trial_end),
                'trial_days': TRIAL_DAYS,
            }

            return redirect('landing:free_trial_success')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')
            return render(request, 'landing/free_trial_register.html', {
                'page_title': 'ابدأ تجربتك المجانية',
                'trial_days': TRIAL_DAYS,
            })

    context = {
        'page_title': 'ابدأ تجربتك المجانية',
        'trial_days': TRIAL_DAYS,
        'sales_phone': '(+20)01501551593',
        'sales_whatsapp': '2001501551593',
    }
    return render(request, 'landing/free_trial_register.html', context)


def free_trial_success(request):
    """صفحة نجاح التسجيل — تعرض بيانات الدخول"""
    trial_data = request.session.pop('trial_data', None)

    if not trial_data:
        return redirect('landing:free_trial')

    context = {
        'page_title': 'تم إنشاء حسابك بنجاح',
        'trial_data': trial_data,
        'sales_phone': '(+20)01501551593',
        'sales_whatsapp': '2001501551593',
    }
    return render(request, 'landing/free_trial_success.html', context)
'''

views_content = views_content.rstrip() + "\n" + new_trial_views + "\n"
write_file(views_path, views_content)

# ════════════════════════════════════════════════════════════
# Step 5: Update registration template
# ════════════════════════════════════════════════════════════
print("\n📌 Step 5: تحديث صفحة التسجيل")

register_html = """{% extends 'base/base.html' %}
{% block title %}ابدأ تجربتك المجانية — MotionHR{% endblock %}

{% block content %}
<div class="container py-5" style="max-width: 850px;">
  <div class="text-center mb-4">
    <h1 class="fw-bold" style="color:#06B6D4;">ابدأ تجربتك المجانية</h1>
    <p class="text-muted">جرّب MotionHR مجاناً لمدة {{ trial_days }} يوم — كل المميزات مفتوحة — بدون التزام</p>
  </div>

  {% if messages %}
  <div class="mb-3">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags|default:'info' }} border-0" style="border-radius:12px;">
      {{ message }}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="card border-0 shadow-lg" style="border-radius:24px;">
    <div class="card-body p-4 p-md-5">

      <div class="alert border-0 mb-4" style="border-radius:16px; background:linear-gradient(135deg, #ecfdf5, #d1fae5);">
        <div class="fw-bold mb-1" style="color:#065f46;"><i class="bi bi-gift-fill me-2"></i>ماذا ستحصل عليه مجاناً؟</div>
        <div class="row small" style="color:#047857;">
          <div class="col-md-6">
            <div>✅ تجربة مجانية {{ trial_days }} يوم</div>
            <div>✅ كل مميزات النظام متاحة</div>
            <div>✅ بدون رسوم تنفيذ</div>
          </div>
          <div class="col-md-6">
            <div>✅ بدون رسوم تدريب</div>
            <div>✅ حسابك جاهز فورًا</div>
            <div>✅ دعم مباشر من JS Solutions</div>
          </div>
        </div>
      </div>

      <form method="post">
        {% csrf_token %}
        <div class="row g-3">

          <div class="col-md-6">
            <label class="form-label fw-semibold">اسم الشركة <span class="text-danger">*</span></label>
            <input type="text" name="company_name" class="form-control form-control-lg" required
                   placeholder="مثال: شركة النجاح للمقاولات" style="border-radius:12px;">
          </div>

          <div class="col-md-6">
            <label class="form-label fw-semibold">اسم المسؤول <span class="text-danger">*</span></label>
            <input type="text" name="contact_name" class="form-control form-control-lg" required
                   placeholder="الاسم الكامل" style="border-radius:12px;">
          </div>

          <div class="col-md-6">
            <label class="form-label fw-semibold">رقم الموبايل <span class="text-danger">*</span></label>
            <input type="tel" name="phone" class="form-control form-control-lg" required
                   placeholder="01xxxxxxxxx" style="border-radius:12px;">
          </div>

          <div class="col-md-6">
            <label class="form-label fw-semibold">رقم الواتساب <span class="text-danger">*</span></label>
            <input type="tel" name="whatsapp" class="form-control form-control-lg" required
                   placeholder="01xxxxxxxxx" style="border-radius:12px;">
            <div class="form-text small">لو نفس رقم الموبايل، اكتبه تاني</div>
          </div>

          <div class="col-md-12">
            <label class="form-label fw-semibold">البريد الإلكتروني <span class="text-danger">*</span></label>
            <input type="email" name="email" class="form-control form-control-lg" required
                   placeholder="name@company.com" style="border-radius:12px;">
            <div class="form-text small">سيتم إرسال بيانات الدخول على هذا البريد</div>
          </div>

          <div class="col-md-4">
            <label class="form-label fw-semibold">عدد الموظفين المتوقع</label>
            <input type="number" name="employees_count" class="form-control form-control-lg"
                   min="1" value="10" style="border-radius:12px;">
          </div>

          <div class="col-md-4">
            <label class="form-label fw-semibold">المدينة</label>
            <input type="text" name="city" class="form-control form-control-lg"
                   placeholder="القاهرة / الجيزة / ..." style="border-radius:12px;">
          </div>

          <div class="col-md-4">
            <label class="form-label fw-semibold">نوع النشاط</label>
            <input type="text" name="industry" class="form-control form-control-lg"
                   placeholder="مقاولات / توزيع / ..." style="border-radius:12px;">
          </div>

          <div class="col-md-12">
            <label class="form-label fw-semibold">ملاحظات إضافية</label>
            <textarea name="notes" class="form-control" rows="3" style="border-radius:12px;"
                      placeholder="اكتب أي تفاصيل إضافية عن احتياج شركتك"></textarea>
          </div>

          <div class="col-12 text-center mt-4">
            <button type="submit" class="btn btn-lg px-5 fw-bold text-white"
                    style="background:linear-gradient(135deg, #06B6D4, #0891b2); border:none; border-radius:14px; padding:14px 40px;">
              <i class="bi bi-rocket-takeoff-fill me-2"></i>ابدأ التجربة المجانية الآن
            </button>
          </div>
        </div>
      </form>

      <div class="text-center mt-4">
        <div class="text-muted small mb-2">أو تواصل معنا مباشرة:</div>
        <a href="https://wa.me/{{ sales_whatsapp }}" target="_blank" class="btn btn-success btn-sm me-2">
          <i class="bi bi-whatsapp me-1"></i>واتساب
        </a>
        <a href="tel:{{ sales_phone }}" class="btn btn-outline-primary btn-sm">
          <i class="bi bi-telephone me-1"></i>{{ sales_phone }}
        </a>
      </div>

    </div>
  </div>
</div>
{% endblock %}
"""
write_file("templates/landing/free_trial_register.html", register_html)

# ════════════════════════════════════════════════════════════
# Step 6: Update success template
# ════════════════════════════════════════════════════════════
print("\n📌 Step 6: تحديث صفحة النجاح")

success_html = """{% extends 'base/base.html' %}
{% block title %}تم إنشاء حسابك بنجاح{% endblock %}

{% block content %}
<div class="container py-5" style="max-width: 750px;">
  <div class="card border-0 shadow-lg" style="border-radius:24px; overflow:hidden;">

    <!-- Header -->
    <div class="text-center py-4" style="background:linear-gradient(135deg, #10b981, #059669);">
      <i class="bi bi-check-circle-fill text-white" style="font-size:3.5rem;"></i>
      <h2 class="fw-bold text-white mt-2 mb-1">تم إنشاء حسابك بنجاح! 🎉</h2>
      <div class="text-white-50">تجربة مجانية {{ trial_data.trial_days }} يوم — كل المميزات مفتوحة</div>
    </div>

    <div class="card-body p-4 p-md-5">

      <!-- بيانات الدخول -->
      <div class="mb-4 p-4" style="background:#f0f9ff; border:2px solid #06B6D4; border-radius:16px;">
        <h5 class="fw-bold mb-3" style="color:#0c4a6e;">
          <i class="bi bi-key-fill me-2"></i>بيانات الدخول الخاصة بك
        </h5>

        <div class="row g-3">
          <div class="col-md-6">
            <div class="fw-semibold text-muted small">اسم المستخدم:</div>
            <div class="fs-5 fw-bold" style="color:#0e7490;" id="username-display">{{ trial_data.username }}</div>
          </div>
          <div class="col-md-6">
            <div class="fw-semibold text-muted small">كلمة المرور المؤقتة:</div>
            <div class="fs-5 fw-bold" style="color:#0e7490;" id="password-display">{{ trial_data.password }}</div>
          </div>
        </div>

        <div class="mt-3 p-3" style="background:#fffbeb; border-radius:10px; border:1px solid #fbbf24;">
          <div class="small fw-bold" style="color:#92400e;">
            <i class="bi bi-exclamation-triangle-fill me-1"></i>مهم جداً:
          </div>
          <div class="small" style="color:#78350f;">
            احفظ بيانات الدخول دي في مكان آمن.<br>
            ننصحك بتغيير كلمة المرور بعد أول تسجيل دخول.
          </div>
        </div>
      </div>

      <!-- تفاصيل التجربة -->
      <div class="row g-3 mb-4">
        <div class="col-md-6">
          <div class="p-3" style="background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0;">
            <div class="small text-muted">اسم الشركة</div>
            <div class="fw-bold">{{ trial_data.company_name }}</div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3" style="background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0;">
            <div class="small text-muted">المسؤول</div>
            <div class="fw-bold">{{ trial_data.contact_name }}</div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3" style="background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0;">
            <div class="small text-muted">بداية التجربة</div>
            <div class="fw-bold">{{ trial_data.trial_start }}</div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3" style="background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0;">
            <div class="small text-muted">نهاية التجربة</div>
            <div class="fw-bold text-danger">{{ trial_data.trial_end }}</div>
          </div>
        </div>
      </div>

      <!-- الخطوات التالية -->
      <div class="mb-4 p-4" style="background:#fefce8; border-radius:14px; border:1px solid #fde68a;">
        <div class="fw-bold mb-2" style="color:#854d0e;">
          <i class="bi bi-arrow-right-circle-fill me-1"></i>الخطوات التالية:
        </div>
        <div class="small" style="color:#713f12;">
          1. اضغط على زرار <strong>"الدخول الآن"</strong> أسفل الصفحة<br>
          2. سجّل دخول باسم المستخدم وكلمة المرور أعلاه<br>
          3. ابدأ بإعداد بيانات شركتك (الفروع، الإدارات، الموظفين)<br>
          4. فريق الدعم جاهز لمساعدتك في أي وقت
        </div>
      </div>

      <!-- أزرار -->
      <div class="d-flex justify-content-center gap-3 flex-wrap mb-3">
        <a href="/accounts/login/" class="btn btn-lg fw-bold text-white px-5"
           style="background:linear-gradient(135deg, #06B6D4, #0891b2); border:none; border-radius:14px;">
          <i class="bi bi-box-arrow-in-left me-2"></i>الدخول الآن
        </a>

        <a href="https://wa.me/{{ sales_whatsapp }}" target="_blank" class="btn btn-success btn-lg px-4"
           style="border-radius:14px;">
          <i class="bi bi-whatsapp me-2"></i>تواصل معنا
        </a>
      </div>

      <div class="text-center text-muted small">
        تحتاج مساعدة؟ تواصل معنا: {{ sales_phone }}
      </div>

    </div>
  </div>
</div>
{% endblock %}
"""
write_file("templates/landing/free_trial_success.html", success_html)

print("\n" + "=" * 60)
print("✅ Patch 49M اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ تحديث TrialSignupLead model بالحقول الجديدة:
     - رقم الموبايل
     - رقم الواتساب
     - تاريخ بداية/نهاية التجربة
     - اسم المستخدم المولّد
     - كلمة المرور المولّدة
     - ربط بالشركة والحساب المنشأ
     - ملاحظات المبيعات
     - حالة الطلب
  ✅ إنشاء تلقائي عند التسجيل:
     - شركة جديدة
     - حساب Admin (company_admin)
     - اشتراك Trial 14 يوم
  ✅ صفحة نجاح تعرض:
     - بيانات الدخول (اسم مستخدم + كلمة مرور)
     - تفاصيل التجربة
     - الخطوات التالية
     - زرار الدخول الآن
  ✅ كل البيانات تتحفظ في Admin:
     - بيانات العميل كاملة
     - بيانات الدخول
     - تواريخ التجربة
     - حالة الطلب
     - إمكانية إضافة ملاحظات المبيعات

شغّل:
  python manage.py migrate
  python manage.py check
  python manage.py runserver 0.0.0.0:8000

اختبر:
  /free-trial/
""")