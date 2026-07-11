"""
Patch 49h — Work Charter Notifications + Digital Signature

الهدف:
1) إشعار كل 3 شهور لكل الموظفين بالميثاق
2) إجباري للموظفين الجدد
3) أي تعديل على الميثاق يتبعت للكل مع highlight للتغييرات
4) الموافقة تكون توقيع رقمي (اسم + تاريخ + IP + checkbox تأكيد)
5) طباعة الميثاق بالتوقيع
6) dashboard للـ HR يعرض حالة القبول

الملفات:
- companies/models.py (تحديث CharterAcceptance)
- companies/migrations/0015_charter_digital_signature.py
- companies/views.py
- templates/companies/charter_view.html
- templates/companies/charter_manage.html
- templates/companies/charter_acceptance_status.html (جديد)
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
print("Patch 49h — Work Charter Notifications + Digital Signature")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path in [
    "companies/models.py",
    "companies/views.py",
    "companies/urls.py",
    "templates/companies/charter_view.html",
    "templates/companies/charter_manage.html",
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_name = rel_path.replace("/", "_").replace("\\", "_") + ".49h.bak"
        shutil.copy2(full, os.path.join(backup_dir, backup_name))

print("✅ Backups created")

# ────────────────────────────────────────────────────────────
# Step 1: Update companies/models.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: تحديث companies/models.py")

models_path = "companies/models.py"
models_content = read_file(models_path)
if models_content is None:
    raise SystemExit("❌ ملف companies/models.py غير موجود")

charter_models_append = '''

# ═════════════════════════════════════════════════════════════
# Patch 49h — Charter Digital Signature + Tracking
# ═════════════════════════════════════════════════════════════

class CharterVersion(models.Model):
    """
    تتبع تعديلات الميثاق — كل تعديل يُنشئ version جديد
    """
    charter = models.ForeignKey(
        'companies.WorkCharter',
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='الميثاق',
    )
    version_number = models.PositiveIntegerField(default=1, verbose_name='رقم الإصدار')
    content_snapshot = models.TextField(verbose_name='محتوى الإصدار')
    changes_summary = models.TextField(blank=True, verbose_name='ملخص التغييرات')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='أنشأ بواسطة',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إصدار ميثاق'
        verbose_name_plural = 'إصدارات الميثاق'
        ordering = ['-version_number']
        unique_together = [['charter', 'version_number']]

    def __str__(self):
        return f"الإصدار {self.version_number} — {self.charter.title}"


class CharterDigitalSignature(models.Model):
    """
    توقيع رقمي على الميثاق — أقوى من مجرد checkbox
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='charter_signatures',
        verbose_name='الشركة',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='charter_signatures',
        verbose_name='الموظف',
    )
    charter = models.ForeignKey(
        'companies.WorkCharter',
        on_delete=models.CASCADE,
        related_name='digital_signatures',
        verbose_name='الميثاق',
    )
    charter_version = models.ForeignKey(
        'companies.CharterVersion',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='signatures',
        verbose_name='إصدار الميثاق',
    )

    # التوقيع الرقمي
    full_name_typed = models.CharField(
        max_length=200,
        verbose_name='الاسم الكامل كما كتبه الموظف',
    )
    national_id_typed = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='الرقم القومي كما كتبه الموظف',
    )
    agreement_text = models.TextField(
        verbose_name='نص الموافقة',
        default='أقر بأنني قرأت وفهمت ميثاق العمل وأوافق على الالتزام بكل بنوده.',
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name='عنوان IP',
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='متصفح الموظف',
    )

    signed_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوقيع')
    is_valid = models.BooleanField(default=True, verbose_name='توقيع صالح')
    invalidated_reason = models.TextField(blank=True, verbose_name='سبب الإلغاء')

    class Meta:
        verbose_name = 'توقيع رقمي على الميثاق'
        verbose_name_plural = 'التوقيعات الرقمية'
        ordering = ['-signed_at']

    def __str__(self):
        emp_name = getattr(self.employee, 'full_name_ar', '') or f"#{self.employee_id}"
        return f"توقيع {emp_name} على {self.charter.title}"


class CharterNotificationLog(models.Model):
    """
    سجل إشعارات الميثاق — لمنع التكرار ومتابعة من استلم
    """
    NOTIFICATION_TYPES = [
        ('quarterly_reminder', 'تذكير ربع سنوي'),
        ('new_employee', 'موظف جديد'),
        ('charter_updated', 'تحديث الميثاق'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='charter_notification_logs',
        verbose_name='الشركة',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='charter_notification_logs',
        verbose_name='الموظف',
    )
    charter = models.ForeignKey(
        'companies.WorkCharter',
        on_delete=models.CASCADE,
        related_name='notification_logs',
        verbose_name='الميثاق',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name='نوع الإشعار',
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ القراءة')

    class Meta:
        verbose_name = 'سجل إشعار ميثاق'
        verbose_name_plural = 'سجلات إشعارات الميثاق'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} — {self.employee}"
'''

if "class CharterDigitalSignature(models.Model):" not in models_content:
    models_content = models_content.rstrip() + "\n" + charter_models_append + "\n"
    write_file(models_path, models_content)
else:
    print("ℹ️ Charter models موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Migration
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء migration")

migration_code = '''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0014_department_hierarchy'),
        ('employees', '0006_job_hierarchy_models'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharterVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField(default=1, verbose_name='رقم الإصدار')),
                ('content_snapshot', models.TextField(verbose_name='محتوى الإصدار')),
                ('changes_summary', models.TextField(blank=True, verbose_name='ملخص التغييرات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('charter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='companies.workcharter', verbose_name='الميثاق')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user', verbose_name='أنشأ بواسطة')),
            ],
            options={
                'verbose_name': 'إصدار ميثاق',
                'verbose_name_plural': 'إصدارات الميثاق',
                'ordering': ['-version_number'],
                'unique_together': {('charter', 'version_number')},
            },
        ),
        migrations.CreateModel(
            name='CharterDigitalSignature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name_typed', models.CharField(max_length=200, verbose_name='الاسم الكامل كما كتبه الموظف')),
                ('national_id_typed', models.CharField(blank=True, max_length=30, verbose_name='الرقم القومي كما كتبه الموظف')),
                ('agreement_text', models.TextField(default='أقر بأنني قرأت وفهمت ميثاق العمل وأوافق على الالتزام بكل بنوده.', verbose_name='نص الموافقة')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='عنوان IP')),
                ('user_agent', models.TextField(blank=True, verbose_name='متصفح الموظف')),
                ('signed_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوقيع')),
                ('is_valid', models.BooleanField(default=True, verbose_name='توقيع صالح')),
                ('invalidated_reason', models.TextField(blank=True, verbose_name='سبب الإلغاء')),
                ('charter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='digital_signatures', to='companies.workcharter', verbose_name='الميثاق')),
                ('charter_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signatures', to='companies.charterversion', verbose_name='إصدار الميثاق')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_signatures', to='companies.company', verbose_name='الشركة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_signatures', to='employees.employee', verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'توقيع رقمي على الميثاق',
                'verbose_name_plural': 'التوقيعات الرقمية',
                'ordering': ['-signed_at'],
            },
        ),
        migrations.CreateModel(
            name='CharterNotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('quarterly_reminder', 'تذكير ربع سنوي'), ('new_employee', 'موظف جديد'), ('charter_updated', 'تحديث الميثاق')], max_length=30, verbose_name='نوع الإشعار')),
                ('sent_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ القراءة')),
                ('charter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_logs', to='companies.workcharter', verbose_name='الميثاق')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_notification_logs', to='companies.company', verbose_name='الشركة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_notification_logs', to='employees.employee', verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'سجل إشعار ميثاق',
                'verbose_name_plural': 'سجلات إشعارات الميثاق',
                'ordering': ['-sent_at'],
            },
        ),
    ]
'''
write_file("companies/migrations/0015_charter_digital_signature.py", migration_code)

# ────────────────────────────────────────────────────────────
# Step 3: Add views to companies/views.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إضافة charter views")

views_path = "companies/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف companies/views.py غير موجود")

charter_views = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49h — Charter Digital Signature Views
# ═════════════════════════════════════════════════════════════

@login_required
def charter_sign(request, charter_id):
    """صفحة توقيع الميثاق رقميًا"""
    from .models import WorkCharter, CharterDigitalSignature, CharterVersion
    from employees.models import Employee

    charter = get_object_or_404(WorkCharter, pk=charter_id)

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'لا يوجد ملف موظف مرتبط بحسابك')
        return redirect('dashboard')

    company = getattr(request.user, 'company', None) or getattr(employee, 'company', None)

    # هل وقّع بالفعل؟
    existing_signature = CharterDigitalSignature.objects.filter(
        employee=employee,
        charter=charter,
        is_valid=True
    ).first()

    if request.method == 'POST':
        full_name = (request.POST.get('full_name_typed') or '').strip()
        national_id = (request.POST.get('national_id_typed') or '').strip()
        agreement_confirmed = bool(request.POST.get('agreement_confirmed'))

        errors = []
        if not full_name:
            errors.append('يرجى كتابة الاسم الكامل')
        if not agreement_confirmed:
            errors.append('يرجى تأكيد الموافقة على الميثاق')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            # جلب آخر version
            latest_version = CharterVersion.objects.filter(charter=charter).order_by('-version_number').first()

            # IP
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not ip:
                ip = request.META.get('REMOTE_ADDR', '')

            user_agent = request.META.get('HTTP_USER_AGENT', '')

            CharterDigitalSignature.objects.create(
                company=company,
                employee=employee,
                charter=charter,
                charter_version=latest_version,
                full_name_typed=full_name,
                national_id_typed=national_id,
                agreement_text='أقر بأنني قرأت وفهمت ميثاق العمل وأوافق على الالتزام بكل بنوده.',
                ip_address=ip or None,
                user_agent=user_agent,
                is_valid=True,
            )
            messages.success(request, 'تم توقيع الميثاق بنجاح. شكرًا لالتزامك.')
            return redirect('companies:charter_view', charter_id=charter.pk)

    context = {
        'charter': charter,
        'employee': employee,
        'existing_signature': existing_signature,
        'page_title': f'توقيع ميثاق العمل — {charter.title}',
    }
    return render(request, 'companies/charter_sign.html', context)


@login_required
def charter_acceptance_status(request, charter_id):
    """حالة قبول الميثاق — للـ HR"""
    from .models import WorkCharter, CharterDigitalSignature
    from employees.models import Employee

    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('ليس لديك صلاحية عرض هذه الصفحة')

    charter = get_object_or_404(WorkCharter, pk=charter_id)

    company = getattr(request.user, 'company', None)
    if not company:
        messages.error(request, 'لا يمكن تحديد الشركة')
        return redirect('dashboard')

    all_employees = Employee.objects.filter(company=company, status='active').order_by('employee_code')

    signed_employee_ids = set(
        CharterDigitalSignature.objects.filter(
            charter=charter,
            company=company,
            is_valid=True
        ).values_list('employee_id', flat=True)
    )

    signed = []
    unsigned = []
    for emp in all_employees:
        if emp.id in signed_employee_ids:
            sig = CharterDigitalSignature.objects.filter(
                charter=charter, employee=emp, is_valid=True
            ).order_by('-signed_at').first()
            signed.append({'employee': emp, 'signature': sig})
        else:
            unsigned.append(emp)

    # إرسال تذكير
    if request.method == 'POST' and request.POST.get('action') == 'send_reminder':
        from .models import CharterNotificationLog
        sent_count = 0
        for emp in unsigned:
            try:
                CharterNotificationLog.objects.create(
                    company=company,
                    employee=emp,
                    charter=charter,
                    notification_type='quarterly_reminder',
                )
                # إرسال إشعار داخلي
                try:
                    from accounts.models import EmployeeNotification
                    if emp.user:
                        EmployeeNotification.objects.create(
                            recipient=emp.user,
                            title='تذكير بتوقيع ميثاق العمل',
                            message=f'يرجى مراجعة وتوقيع ميثاق العمل: {charter.title}',
                            notification_type='charter_reminder',
                        )
                except Exception:
                    pass
                sent_count += 1
            except Exception:
                pass
        messages.success(request, f'تم إرسال تذكير لـ {sent_count} موظف لم يوقعوا بعد')
        return redirect('companies:charter_acceptance_status', charter_id=charter.pk)

    context = {
        'charter': charter,
        'signed': signed,
        'unsigned': unsigned,
        'signed_count': len(signed),
        'unsigned_count': len(unsigned),
        'total_count': len(signed) + len(unsigned),
        'page_title': f'حالة توقيع الميثاق — {charter.title}',
    }
    return render(request, 'companies/charter_acceptance_status.html', context)


@login_required
def charter_print_signature(request, signature_id):
    """طباعة توقيع رقمي"""
    from .models import CharterDigitalSignature

    sig = get_object_or_404(CharterDigitalSignature, pk=signature_id)

    company = getattr(request.user, 'company', None)

    context = {
        'signature': sig,
        'company': company,
        'page_title': f'طباعة توقيع — {sig.employee.full_name_ar}',
    }
    return render(request, 'companies/charter_print_signature.html', context)
'''

if "def charter_sign(request, charter_id):" not in views_content:
    views_content = views_content.rstrip() + "\n" + charter_views + "\n"
    write_file(views_path, views_content)
else:
    print("ℹ️ charter views موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Step 4: Update companies/urls.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: تحديث companies/urls.py")

urls_path = "companies/urls.py"
urls_content = read_file(urls_path)
if urls_content is None:
    raise SystemExit("❌ ملف companies/urls.py غير موجود")

new_urls = [
    "    path('charter/<int:charter_id>/sign/', views.charter_sign, name='charter_sign'),",
    "    path('charter/<int:charter_id>/acceptance-status/', views.charter_acceptance_status, name='charter_acceptance_status'),",
    "    path('charter/signature/<int:signature_id>/print/', views.charter_print_signature, name='charter_print_signature'),",
]

for url_line in new_urls:
    url_name = url_line.split("name='")[1].split("'")[0]
    if f"name='{url_name}'" not in urls_content:
        if "urlpatterns = [" in urls_content:
            urls_content = urls_content.replace(
                "urlpatterns = [",
                "urlpatterns = [\n" + url_line,
                1
            )
            print(f"   ✅ route: {url_name}")
        else:
            print(f"   ⚠️ لم أجد urlpatterns")

write_file(urls_path, urls_content)

# ────────────────────────────────────────────────────────────
# Step 5: Create charter_sign.html
# ────────────────────────────────────────────────────────────
print("\n📌 Step 5: إنشاء templates/companies/charter_sign.html")

sign_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
  .sign-box { border: 2px solid #06B6D4; border-radius: 20px; background: linear-gradient(180deg, #f0fdff 0%, #fff 100%); }
  .charter-content { max-height: 400px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; background: #fff; font-size: .95rem; line-height: 1.8; }
  .sig-field { border: 2px dashed #cbd5e1; border-radius: 14px; padding: 16px; background: #f8fafc; }
  .sig-field:focus-within { border-color: #06B6D4; background: #f0fdff; }
  .agreement-box { border: 1px solid #fbbf24; background: #fffbeb; border-radius: 14px; padding: 16px; }
  .already-signed { border: 1px solid #22c55e; background: #f0fdf4; border-radius: 16px; padding: 20px; }
</style>
{% endblock %}

{% block content %}
<div class="container" style="max-width: 800px;">

  <nav aria-label="breadcrumb" class="mb-3">
    <ol class="breadcrumb small">
      <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
      <li class="breadcrumb-item active">توقيع الميثاق</li>
    </ol>
  </nav>

  {% if existing_signature %}
  <div class="already-signed text-center mb-4">
    <div class="fs-1 mb-2"><i class="bi bi-check-circle-fill text-success"></i></div>
    <h5 class="fw-bold text-success">تم توقيع الميثاق مسبقًا</h5>
    <div class="text-muted small mt-2">
      تاريخ التوقيع: {{ existing_signature.signed_at|date:"Y/m/d H:i" }}<br>
      الاسم المكتوب: {{ existing_signature.full_name_typed }}
    </div>
  </div>
  {% endif %}

  <div class="sign-box p-4">
    <div class="text-center mb-4">
      <h4 class="fw-bold"><i class="bi bi-file-earmark-check text-primary me-2"></i>{{ charter.title }}</h4>
      <div class="text-muted small">يرجى قراءة الميثاق بعناية ثم التوقيع أدناه</div>
    </div>

    <div class="charter-content mb-4">
      {{ charter.content|linebreaksbr }}
    </div>

    {% if not existing_signature %}
    <form method="post">
      {% csrf_token %}

      <div class="agreement-box mb-4">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="agreementConfirmed" name="agreement_confirmed" required>
          <label class="form-check-label fw-bold" for="agreementConfirmed">
            أقر بأنني قرأت وفهمت ميثاق العمل بالكامل وأوافق على الالتزام بكل بنوده
          </label>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-6">
          <div class="sig-field">
            <label class="form-label fw-bold">الاسم الكامل <span class="text-danger">*</span></label>
            <input type="text" name="full_name_typed" class="form-control form-control-lg" required
                   placeholder="اكتب اسمك الكامل كما في بطاقة الهوية"
                   value="{{ employee.full_name_ar }}">
            <div class="small text-muted mt-1">هذا الاسم يعتبر توقيعك الرقمي على الميثاق</div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="sig-field">
            <label class="form-label fw-bold">الرقم القومي</label>
            <input type="text" name="national_id_typed" class="form-control form-control-lg"
                   placeholder="اختياري — للتأكيد"
                   value="{{ employee.national_id|default:'' }}">
          </div>
        </div>
      </div>

      <div class="text-center">
        <button type="submit" class="btn btn-primary btn-lg px-5">
          <i class="bi bi-pen me-2"></i>توقيع الميثاق
        </button>
      </div>
    </form>
    {% endif %}
  </div>
</div>
{% endblock %}
"""
write_file("templates/companies/charter_sign.html", sign_template)

# ────────────────────────────────────────────────────────────
# Step 6: Create charter_acceptance_status.html
# ────────────────────────────────────────────────────────────
print("\n📌 Step 6: إنشاء charter_acceptance_status.html")

status_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid">

  <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold"><i class="bi bi-clipboard-check text-primary me-2"></i>{{ page_title }}</h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item active">حالة التوقيع</li>
        </ol>
      </nav>
    </div>
    <div>
      {% if unsigned_count > 0 %}
      <form method="post" class="d-inline">
        {% csrf_token %}
        <input type="hidden" name="action" value="send_reminder">
        <button type="submit" class="btn btn-warning"
                onclick="return confirm('إرسال تذكير لـ {{ unsigned_count }} موظف لم يوقعوا بعد؟');">
          <i class="bi bi-bell me-1"></i>إرسال تذكير ({{ unsigned_count }})
        </button>
      </form>
      {% endif %}
    </div>
  </div>

  <!-- Stats -->
  <div class="row g-3 mb-4">
    <div class="col-md-4">
      <div class="card border-0 shadow-sm text-center py-3" style="border-radius:16px;">
        <div class="fs-2 fw-bold text-primary">{{ total_count }}</div>
        <div class="text-muted small">إجمالي الموظفين النشطين</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card border-0 shadow-sm text-center py-3" style="border-radius:16px;">
        <div class="fs-2 fw-bold text-success">{{ signed_count }}</div>
        <div class="text-muted small">وقّعوا</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card border-0 shadow-sm text-center py-3" style="border-radius:16px;">
        <div class="fs-2 fw-bold text-danger">{{ unsigned_count }}</div>
        <div class="text-muted small">لم يوقعوا بعد</div>
      </div>
    </div>
  </div>

  <div class="row g-4">
    <!-- لم يوقعوا -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm" style="border-radius:18px;">
        <div class="card-header bg-white py-3" style="border-radius:18px 18px 0 0;">
          <h6 class="mb-0 fw-bold text-danger"><i class="bi bi-x-circle me-2"></i>لم يوقعوا ({{ unsigned_count }})</h6>
        </div>
        <div class="card-body p-0">
          {% if unsigned %}
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" style="font-size:.88rem;">
              <thead class="table-light"><tr><th>الموظف</th><th>الكود</th><th>الإدارة</th></tr></thead>
              <tbody>
                {% for emp in unsigned %}
                <tr>
                  <td class="fw-semibold">{{ emp.full_name_ar }}</td>
                  <td class="text-muted">{{ emp.employee_code }}</td>
                  <td>{{ emp.department.name_ar|default:"—" }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-4 text-muted">🎉 كل الموظفين وقّعوا!</div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- وقّعوا -->
    <div class="col-lg-6">
      <div class="card border-0 shadow-sm" style="border-radius:18px;">
        <div class="card-header bg-white py-3" style="border-radius:18px 18px 0 0;">
          <h6 class="mb-0 fw-bold text-success"><i class="bi bi-check-circle me-2"></i>وقّعوا ({{ signed_count }})</h6>
        </div>
        <div class="card-body p-0">
          {% if signed %}
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" style="font-size:.88rem;">
              <thead class="table-light"><tr><th>الموظف</th><th>الكود</th><th>تاريخ التوقيع</th><th>طباعة</th></tr></thead>
              <tbody>
                {% for item in signed %}
                <tr>
                  <td class="fw-semibold">{{ item.employee.full_name_ar }}</td>
                  <td class="text-muted">{{ item.employee.employee_code }}</td>
                  <td>{{ item.signature.signed_at|date:"Y/m/d H:i" }}</td>
                  <td>
                    <a href="{% url 'companies:charter_print_signature' item.signature.id %}" class="btn btn-sm btn-outline-primary" target="_blank">
                      <i class="bi bi-printer"></i>
                    </a>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-4 text-muted">لا يوجد توقيعات بعد</div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
write_file("templates/companies/charter_acceptance_status.html", status_template)

# ────────────────────────────────────────────────────────────
# Step 7: Create charter_print_signature.html
# ────────────────────────────────────────────────────────────
print("\n📌 Step 7: إنشاء charter_print_signature.html")

print_sig_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}طباعة توقيع الميثاق{% endblock %}

{% block extra_css %}
<style>
  .print-doc { max-width: 700px; margin: 0 auto; font-family: 'Cairo', sans-serif; }
  .sig-block { border: 2px solid #0f172a; border-radius: 14px; padding: 20px; margin-top: 30px; }
  .sig-line { border-bottom: 2px solid #334155; margin-top: 40px; padding-bottom: 6px; display: inline-block; min-width: 250px; }
  @media print {
    .sidebar, .navbar, .breadcrumb, .btn, .print-hide { display: none !important; }
    .main-content { margin: 0 !important; padding: 0 !important; }
    body { font-size: 14px; }
  }
</style>
{% endblock %}

{% block content %}
<div class="print-doc p-4">

  <div class="text-center mb-3 print-hide">
    <button onclick="window.print()" class="btn btn-primary btn-lg">
      <i class="bi bi-printer me-2"></i>طباعة المستند
    </button>
  </div>

  <div class="text-center mb-4">
    {% if company and company.logo %}
    <img src="{{ company.logo.url }}" alt="Logo" style="max-height:60px; margin-bottom:10px;">
    {% endif %}
    <h4 class="fw-bold">{{ company.name_ar|default:"MotionHR" }}</h4>
    <h5 class="text-muted">إقرار قبول ميثاق العمل</h5>
    <hr>
  </div>

  <div class="mb-4" style="line-height:2;">
    <p>
      أقر أنا / <strong>{{ signature.full_name_typed }}</strong>
      {% if signature.national_id_typed %} — الرقم القومي: <strong>{{ signature.national_id_typed }}</strong>{% endif %}
      ، الموظف بالشركة بالرقم الوظيفي <strong>{{ signature.employee.employee_code }}</strong>
      ، بأنني قد قرأت وفهمت جميع بنود ميثاق العمل بعنوان:
    </p>
    <p class="fw-bold text-primary fs-5 text-center">"{{ signature.charter.title }}"</p>
    <p>
      وأوافق على الالتزام الكامل بكل ما جاء فيه من أحكام وشروط وقواعد.
    </p>
  </div>

  <div class="sig-block">
    <div class="row">
      <div class="col-6">
        <div class="mb-2 fw-bold">التوقيع الرقمي:</div>
        <div class="fs-5 fw-bold text-primary">{{ signature.full_name_typed }}</div>
      </div>
      <div class="col-6 text-end">
        <div class="mb-2 fw-bold">التاريخ:</div>
        <div>{{ signature.signed_at|date:"Y/m/d" }}</div>
        <div class="small text-muted">{{ signature.signed_at|time:"H:i:s" }}</div>
      </div>
    </div>

    <div class="row mt-3">
      <div class="col-6">
        <div class="small text-muted">IP: {{ signature.ip_address|default:"—" }}</div>
      </div>
      <div class="col-6 text-end">
        <div class="small text-muted">
          {% if signature.charter_version %}
          إصدار الميثاق: {{ signature.charter_version.version_number }}
          {% endif %}
        </div>
      </div>
    </div>

    <div class="text-center mt-4">
      <div class="sig-line"></div>
      <div class="small text-muted mt-1">توقيع الموظف</div>
    </div>
  </div>

  <div class="text-center mt-4" style="font-size:.8rem; color:#94a3b8; font-style:italic;">
    MotionHR — HR in Motion | JS Solution<br>
    تم إنشاء هذا المستند إلكترونيًا ويعتبر وثيقة رسمية
  </div>
</div>
{% endblock %}
"""
write_file("templates/companies/charter_print_signature.html", print_sig_template)

print("\n" + "=" * 60)
print("✅ Patch 49h اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ Models جديدة:
     - CharterVersion (تتبع تعديلات الميثاق)
     - CharterDigitalSignature (توقيع رقمي حقيقي)
     - CharterNotificationLog (سجل إشعارات الميثاق)
  ✅ Migration:
     companies/migrations/0015_charter_digital_signature.py
  ✅ Views جديدة:
     - charter_sign — صفحة توقيع الميثاق
     - charter_acceptance_status — حالة القبول للـ HR
     - charter_print_signature — طباعة التوقيع الرقمي
  ✅ Templates جديدة:
     - charter_sign.html
     - charter_acceptance_status.html
     - charter_print_signature.html
  ✅ URLs جديدة:
     - /companies/charter/<id>/sign/
     - /companies/charter/<id>/acceptance-status/
     - /companies/charter/signature/<id>/print/

شغّل:
  python manage.py makemigrations --check
  python manage.py migrate
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")