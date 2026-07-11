"""
Patch 49i — Employee Document Management System

الهدف:
1) نظام إدارة ملفات/مستندات الموظف
2) أنواع مستندات ثابتة + مستندات حرة
3) رفع ملفات + تسمية + تصنيف
4) عرض كل ملفات الموظف في مكان واحد
5) ربط المستندات بأحداث (تعيين/إجازة/ترقية/إنذار/...)

الأنواع الثابتة:
- بطاقة الهوية / الرقم القومي
- عقد التعيين
- شهادة المؤهل
- شهادة الخبرة
- صورة شخصية
- شهادة ميلاد
- فيش وتشبيه
- تقرير طبي
- عقد تجديد
- خطاب ترقية
- إنذار
- استقالة
- إخلاء طرف

+ نوع "أخرى" يكتب فيه HR الاسم يدوي
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
print("Patch 49i — Employee Document Management System")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path in [
    "employees/views.py",
    "employees/urls.py",
    "employees/models.py",
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_name = rel_path.replace("/", "_").replace("\\", "_") + ".49i.bak"
        shutil.copy2(full, os.path.join(backup_dir, backup_name))

print("✅ Backups created")

# ────────────────────────────────────────────────────────────
# Step 1: Update employees/models.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: تحديث employees/models.py")

models_path = "employees/models.py"
models_content = read_file(models_path)
if models_content is None:
    raise SystemExit("❌ ملف employees/models.py غير موجود")

doc_model_append = '''

# ═════════════════════════════════════════════════════════════
# Patch 49i — Employee Document Management
# ═════════════════════════════════════════════════════════════

class EmployeeFolder(models.Model):
    """
    ملف/مستند في فولدر الموظف
    يدعم أنواع ثابتة + أنواع حرة
    """

    DOCUMENT_CATEGORIES = [
        ('id_card', 'بطاقة الهوية / الرقم القومي'),
        ('employment_contract', 'عقد التعيين'),
        ('contract_renewal', 'عقد تجديد'),
        ('contract_amendment', 'ملحق عقد / تعديل'),
        ('qualification', 'شهادة المؤهل الدراسي'),
        ('experience_cert', 'شهادة الخبرة'),
        ('personal_photo', 'صورة شخصية'),
        ('birth_cert', 'شهادة الميلاد'),
        ('criminal_record', 'فيش وتشبيه'),
        ('medical_report', 'تقرير طبي'),
        ('medical_insurance', 'بطاقة التأمين الصحي'),
        ('social_insurance', 'مستند التأمينات الاجتماعية'),
        ('promotion_letter', 'خطاب ترقية'),
        ('transfer_letter', 'خطاب نقل'),
        ('salary_adjustment', 'خطاب تعديل راتب'),
        ('warning_letter', 'إنذار'),
        ('disciplinary', 'إجراء تأديبي'),
        ('resignation', 'استقالة'),
        ('termination', 'إنهاء خدمة'),
        ('clearance', 'إخلاء طرف'),
        ('leave_request', 'طلب إجازة مرفق'),
        ('marriage_cert', 'عقد زواج'),
        ('military_cert', 'شهادة الخدمة العسكرية / الإعفاء'),
        ('driving_license', 'رخصة قيادة'),
        ('passport', 'جواز سفر'),
        ('training_cert', 'شهادة تدريب'),
        ('performance_review', 'تقييم أداء'),
        ('other', 'أخرى'),
    ]

    RELATED_EVENTS = [
        ('hiring', 'التعيين'),
        ('contract_renewal', 'تجديد العقد'),
        ('promotion', 'ترقية'),
        ('transfer', 'نقل'),
        ('salary_change', 'تعديل راتب'),
        ('leave', 'إجازة'),
        ('medical', 'حالة طبية'),
        ('warning', 'إنذار / تأديب'),
        ('resignation', 'استقالة'),
        ('termination', 'إنهاء خدمة'),
        ('training', 'تدريب'),
        ('personal', 'شخصي'),
        ('other', 'أخرى'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='employee_folder_docs',
        verbose_name='الشركة',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='folder_documents',
        verbose_name='الموظف',
    )

    # التصنيف
    category = models.CharField(
        max_length=30,
        choices=DOCUMENT_CATEGORIES,
        default='other',
        verbose_name='تصنيف المستند',
    )
    custom_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='اسم المستند (لو أخرى أو اسم مخصص)',
        help_text='يمكن ترك هذا الحقل فارغًا لو اخترت تصنيف ثابت',
    )

    # الحدث المرتبط
    related_event = models.CharField(
        max_length=30,
        choices=RELATED_EVENTS,
        blank=True,
        verbose_name='الحدث المرتبط',
    )
    event_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ الحدث',
    )
    event_notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات الحدث',
    )

    # الملف
    file = models.FileField(
        upload_to='employee_folders/%Y/%m/',
        verbose_name='الملف',
    )
    file_size_kb = models.PositiveIntegerField(
        default=0,
        verbose_name='حجم الملف (KB)',
    )

    # معلومات إضافية
    issue_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ الإصدار',
    )
    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ الانتهاء',
    )
    is_confidential = models.BooleanField(
        default=False,
        verbose_name='سري',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات',
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='رفع بواسطة',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستند في ملف الموظف'
        verbose_name_plural = 'مستندات ملفات الموظفين'
        ordering = ['-created_at']

    def __str__(self):
        display_name = self.custom_name or self.get_category_display()
        emp_name = getattr(self.employee, 'full_name_ar', '') or f"#{self.employee_id}"
        return f"{emp_name} — {display_name}"

    @property
    def display_name(self):
        if self.custom_name:
            return self.custom_name
        return self.get_category_display()

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.file_size_kb = self.file.size // 1024
            except Exception:
                pass
        super().save(*args, **kwargs)
'''

if "class EmployeeFolder(models.Model):" not in models_content:
    models_content = models_content.rstrip() + "\n" + doc_model_append + "\n"
    write_file(models_path, models_content)
else:
    print("ℹ️ EmployeeFolder موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Migration
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء migration")

migration_code = '''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0015_charter_digital_signature'),
        ('employees', '0006_job_hierarchy_models'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('id_card', 'بطاقة الهوية / الرقم القومي'), ('employment_contract', 'عقد التعيين'), ('contract_renewal', 'عقد تجديد'), ('contract_amendment', 'ملحق عقد / تعديل'), ('qualification', 'شهادة المؤهل الدراسي'), ('experience_cert', 'شهادة الخبرة'), ('personal_photo', 'صورة شخصية'), ('birth_cert', 'شهادة الميلاد'), ('criminal_record', 'فيش وتشبيه'), ('medical_report', 'تقرير طبي'), ('medical_insurance', 'بطاقة التأمين الصحي'), ('social_insurance', 'مستند التأمينات الاجتماعية'), ('promotion_letter', 'خطاب ترقية'), ('transfer_letter', 'خطاب نقل'), ('salary_adjustment', 'خطاب تعديل راتب'), ('warning_letter', 'إنذار'), ('disciplinary', 'إجراء تأديبي'), ('resignation', 'استقالة'), ('termination', 'إنهاء خدمة'), ('clearance', 'إخلاء طرف'), ('leave_request', 'طلب إجازة مرفق'), ('marriage_cert', 'عقد زواج'), ('military_cert', 'شهادة الخدمة العسكرية / الإعفاء'), ('driving_license', 'رخصة قيادة'), ('passport', 'جواز سفر'), ('training_cert', 'شهادة تدريب'), ('performance_review', 'تقييم أداء'), ('other', 'أخرى')], default='other', max_length=30, verbose_name='تصنيف المستند')),
                ('custom_name', models.CharField(blank=True, help_text='يمكن ترك هذا الحقل فارغًا لو اخترت تصنيف ثابت', max_length=200, verbose_name='اسم المستند (لو أخرى أو اسم مخصص)')),
                ('related_event', models.CharField(blank=True, choices=[('hiring', 'التعيين'), ('contract_renewal', 'تجديد العقد'), ('promotion', 'ترقية'), ('transfer', 'نقل'), ('salary_change', 'تعديل راتب'), ('leave', 'إجازة'), ('medical', 'حالة طبية'), ('warning', 'إنذار / تأديب'), ('resignation', 'استقالة'), ('termination', 'إنهاء خدمة'), ('training', 'تدريب'), ('personal', 'شخصي'), ('other', 'أخرى')], max_length=30, verbose_name='الحدث المرتبط')),
                ('event_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الحدث')),
                ('event_notes', models.TextField(blank=True, verbose_name='ملاحظات الحدث')),
                ('file', models.FileField(upload_to='employee_folders/%Y/%m/', verbose_name='الملف')),
                ('file_size_kb', models.PositiveIntegerField(default=0, verbose_name='حجم الملف (KB)')),
                ('issue_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الإصدار')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الانتهاء')),
                ('is_confidential', models.BooleanField(default=False, verbose_name='سري')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_folder_docs', to='companies.company', verbose_name='الشركة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folder_documents', to='employees.employee', verbose_name='الموظف')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user', verbose_name='رفع بواسطة')),
            ],
            options={
                'verbose_name': 'مستند في ملف الموظف',
                'verbose_name_plural': 'مستندات ملفات الموظفين',
                'ordering': ['-created_at'],
            },
        ),
    ]
'''
write_file("employees/migrations/0007_employee_folder.py", migration_code)

# ────────────────────────────────────────────────────────────
# Step 3: Add views
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إضافة views")

views_path = "employees/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف employees/views.py غير موجود")

folder_views = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49i — Employee Folder / Document Management
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_folder(request, pk):
    """عرض كل مستندات الموظف"""
    from .models import EmployeeFolder

    employee = _get_employee_or_404_for_user(request.user, pk)
    company = _get_current_company(request.user)

    documents = EmployeeFolder.objects.filter(
        employee=employee
    ).order_by('-created_at')

    # تصنيف حسب الكاتيجوري
    categories = {}
    for doc in documents:
        cat_name = doc.get_category_display()
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(doc)

    context = {
        'employee': employee,
        'documents': documents,
        'categories': categories,
        'total_docs': documents.count(),
        'page_title': f'ملف مستندات — {_employee_name(employee)}',
    }
    return render(request, 'employees/employee_folder.html', context)


@login_required
@feature_required('employees_management')
def employee_folder_upload(request, pk):
    """رفع مستند جديد لملف الموظف"""
    from .models import EmployeeFolder

    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية رفع مستندات لهذا الموظف')

    company = _get_current_company(request.user)

    if request.method == 'POST':
        category = (request.POST.get('category') or 'other').strip()
        custom_name = (request.POST.get('custom_name') or '').strip()
        related_event = (request.POST.get('related_event') or '').strip()
        event_date = request.POST.get('event_date') or None
        event_notes = (request.POST.get('event_notes') or '').strip()
        issue_date = request.POST.get('issue_date') or None
        expiry_date = request.POST.get('expiry_date') or None
        is_confidential = bool(request.POST.get('is_confidential'))
        notes = (request.POST.get('notes') or '').strip()
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            messages.error(request, 'يرجى اختيار ملف للرفع')
            return redirect('employees:folder', pk=employee.pk)

        # لو الكاتيجوري = other ولازم يكون فيه اسم مخصص
        if category == 'other' and not custom_name:
            custom_name = uploaded_file.name

        try:
            from datetime import date as dt_date
            if event_date:
                event_date = dt_date.fromisoformat(event_date)
            if issue_date:
                issue_date = dt_date.fromisoformat(issue_date)
            if expiry_date:
                expiry_date = dt_date.fromisoformat(expiry_date)
        except Exception:
            event_date = None
            issue_date = None
            expiry_date = None

        try:
            doc = EmployeeFolder(
                company=company,
                employee=employee,
                category=category,
                custom_name=custom_name,
                related_event=related_event,
                event_date=event_date,
                event_notes=event_notes,
                file=uploaded_file,
                issue_date=issue_date,
                expiry_date=expiry_date,
                is_confidential=is_confidential,
                notes=notes,
                uploaded_by=request.user,
            )
            doc.save()
            messages.success(request, f'تم رفع المستند: {doc.display_name}')
        except Exception as e:
            messages.error(request, f'تعذر رفع المستند: {e}')

        return redirect('employees:folder', pk=employee.pk)

    # GET
    category_choices = EmployeeFolder.DOCUMENT_CATEGORIES
    event_choices = EmployeeFolder.RELATED_EVENTS

    context = {
        'employee': employee,
        'category_choices': category_choices,
        'event_choices': event_choices,
        'page_title': f'رفع مستند — {_employee_name(employee)}',
    }
    return render(request, 'employees/employee_folder_upload.html', context)


@login_required
@feature_required('employees_management')
def employee_folder_delete(request, pk, doc_id):
    """حذف مستند"""
    from .models import EmployeeFolder

    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية حذف مستندات هذا الموظف')

    doc = get_object_or_404(EmployeeFolder, pk=doc_id, employee=employee)

    if request.method == 'POST':
        doc_name = doc.display_name
        doc.delete()
        messages.success(request, f'تم حذف المستند: {doc_name}')

    return redirect('employees:folder', pk=employee.pk)
'''

if "def employee_folder(request, pk):" not in views_content:
    marker = "# ═════════════════════════════════════════════════════════════\n# Compatibility Aliases"
    if marker in views_content:
        views_content = views_content.replace(marker, folder_views + "\n\n" + marker)
    else:
        views_content = views_content.rstrip() + "\n" + folder_views + "\n"

    # aliases
    views_content = views_content.rstrip() + "\nfolder = employee_folder\nfolder_upload = employee_folder_upload\nfolder_delete = employee_folder_delete\n"
    write_file(views_path, views_content)
else:
    print("ℹ️ employee_folder views موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Step 4: Update URLs
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: تحديث employees/urls.py")

urls_path = "employees/urls.py"
urls_content = read_file(urls_path)
if urls_content is None:
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

folder_urls = [
    "    path('<int:pk>/folder/', views.employee_folder, name='folder'),",
    "    path('<int:pk>/folder/upload/', views.employee_folder_upload, name='folder_upload'),",
    "    path('<int:pk>/folder/<int:doc_id>/delete/', views.employee_folder_delete, name='folder_delete'),",
]

for url_line in folder_urls:
    url_name = url_line.split("name='")[1].split("'")[0]
    if f"name='{url_name}'" not in urls_content:
        if "urlpatterns = [" in urls_content:
            urls_content = urls_content.replace(
                "urlpatterns = [",
                "urlpatterns = [\n" + url_line,
                1
            )
            print(f"   ✅ route: {url_name}")

write_file(urls_path, urls_content)

# ────────────────────────────────────────────────────────────
# Step 5: Create templates
# ────────────────────────────────────────────────────────────
print("\n📌 Step 5: إنشاء templates")

# employee_folder.html
folder_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
  .doc-card { border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; transition: .2s; }
  .doc-card:hover { border-color: #06B6D4; background: #f0fdff; }
  .cat-section { margin-bottom: 2rem; }
  .cat-header { font-weight: 800; color: #0c4a6e; border-bottom: 2px solid #06B6D4; padding-bottom: 8px; margin-bottom: 12px; }
  .confidential-badge { background: #fecdd3; color: #9f1239; border-radius: 999px; padding: 2px 10px; font-size: .75rem; }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold"><i class="bi bi-folder2-open text-primary me-2"></i>{{ page_title }}</h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item"><a href="{% url 'employees:list' %}">الموظفون</a></li>
          <li class="breadcrumb-item"><a href="{% url 'employees:detail' employee.pk %}">{{ employee.full_name_ar }}</a></li>
          <li class="breadcrumb-item active">ملف المستندات</li>
        </ol>
      </nav>
    </div>
    <div class="d-flex gap-2">
      <a href="{% url 'employees:folder_upload' employee.pk %}" class="btn btn-primary">
        <i class="bi bi-cloud-upload me-1"></i>رفع مستند جديد
      </a>
      <a href="{% url 'employees:detail' employee.pk %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-right-circle me-1"></i>ملف الموظف
      </a>
    </div>
  </div>

  <!-- إحصائيات -->
  <div class="row g-3 mb-4">
    <div class="col-md-3">
      <div class="card border-0 shadow-sm text-center py-3" style="border-radius:16px;">
        <div class="fs-2 fw-bold text-primary">{{ total_docs }}</div>
        <div class="text-muted small">إجمالي المستندات</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="card border-0 shadow-sm text-center py-3" style="border-radius:16px;">
        <div class="fs-2 fw-bold text-info">{{ categories|length }}</div>
        <div class="text-muted small">تصنيفات مختلفة</div>
      </div>
    </div>
  </div>

  {% if categories %}
    {% for cat_name, docs in categories.items %}
    <div class="cat-section">
      <div class="cat-header">
        <i class="bi bi-folder me-2"></i>{{ cat_name }}
        <span class="badge bg-secondary ms-2">{{ docs|length }}</span>
      </div>

      <div class="row g-3">
        {% for doc in docs %}
        <div class="col-md-6 col-lg-4">
          <div class="doc-card">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <div>
                <div class="fw-bold small">{{ doc.display_name }}</div>
                {% if doc.related_event %}
                <div class="text-muted" style="font-size:.78rem;">
                  <i class="bi bi-link-45deg me-1"></i>{{ doc.get_related_event_display }}
                  {% if doc.event_date %} — {{ doc.event_date|date:"Y/m/d" }}{% endif %}
                </div>
                {% endif %}
              </div>
              {% if doc.is_confidential %}
              <span class="confidential-badge"><i class="bi bi-lock-fill me-1"></i>سري</span>
              {% endif %}
            </div>

            <div class="d-flex justify-content-between align-items-center">
              <div class="small text-muted">
                {{ doc.created_at|date:"Y/m/d" }}
                {% if doc.file_size_kb %} | {{ doc.file_size_kb }} KB{% endif %}
              </div>
              <div class="d-flex gap-1">
                <a href="{{ doc.file.url }}" class="btn btn-sm btn-outline-primary" target="_blank" title="عرض">
                  <i class="bi bi-eye"></i>
                </a>
                <a href="{{ doc.file.url }}" class="btn btn-sm btn-outline-success" download title="تحميل">
                  <i class="bi bi-download"></i>
                </a>
                <form method="post" action="{% url 'employees:folder_delete' employee.pk doc.id %}"
                      onsubmit="return confirm('حذف المستند؟');" class="d-inline">
                  {% csrf_token %}
                  <button type="submit" class="btn btn-sm btn-outline-danger" title="حذف">
                    <i class="bi bi-trash"></i>
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  {% else %}
  <div class="text-center py-5 text-muted">
    <i class="bi bi-folder2-open fs-1 opacity-25"></i>
    <div class="mt-2">لا توجد مستندات في ملف هذا الموظف بعد</div>
    <a href="{% url 'employees:folder_upload' employee.pk %}" class="btn btn-primary mt-3">
      <i class="bi bi-cloud-upload me-1"></i>رفع أول مستند
    </a>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
write_file("templates/employees/employee_folder.html", folder_template)

# employee_folder_upload.html
upload_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
  .upload-card { border: 1px solid #e2e8f0; border-radius: 20px; background: linear-gradient(180deg, #fff 0%, #f8fdff 100%); }
  .custom-name-box { display: none; }
  .custom-name-box.visible { display: block; }
</style>
{% endblock %}

{% block content %}
<div class="container" style="max-width: 800px;">

  <nav aria-label="breadcrumb" class="mb-3">
    <ol class="breadcrumb small">
      <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
      <li class="breadcrumb-item"><a href="{% url 'employees:list' %}">الموظفون</a></li>
      <li class="breadcrumb-item"><a href="{% url 'employees:detail' employee.pk %}">{{ employee.full_name_ar }}</a></li>
      <li class="breadcrumb-item"><a href="{% url 'employees:folder' employee.pk %}">ملف المستندات</a></li>
      <li class="breadcrumb-item active">رفع مستند</li>
    </ol>
  </nav>

  <div class="card upload-card border-0 shadow-sm">
    <div class="card-body p-4">
      <h5 class="fw-bold mb-4">
        <i class="bi bi-cloud-upload text-primary me-2"></i>رفع مستند جديد لـ {{ employee.full_name_ar }}
      </h5>

      <form method="post" enctype="multipart/form-data">
        {% csrf_token %}

        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label fw-semibold">تصنيف المستند <span class="text-danger">*</span></label>
            <select name="category" class="form-select" id="docCategory" required>
              {% for val, label in category_choices %}
              <option value="{{ val }}">{{ label }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="col-md-6 custom-name-box" id="customNameBox">
            <label class="form-label fw-semibold">اسم المستند المخصص</label>
            <input type="text" name="custom_name" class="form-control" placeholder="مثال: تقرير طبي — مستشفى السلام">
          </div>

          <div class="col-md-12">
            <label class="form-label fw-semibold">الملف <span class="text-danger">*</span></label>
            <input type="file" name="file" class="form-control" required>
            <div class="form-text">PDF / صورة / Word — الحد الأقصى 10 MB</div>
          </div>

          <div class="col-md-6">
            <label class="form-label fw-semibold">الحدث المرتبط</label>
            <select name="related_event" class="form-select">
              <option value="">بدون حدث محدد</option>
              {% for val, label in event_choices %}
              <option value="{{ val }}">{{ label }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="col-md-6">
            <label class="form-label fw-semibold">تاريخ الحدث</label>
            <input type="date" name="event_date" class="form-control">
          </div>

          <div class="col-md-12">
            <label class="form-label fw-semibold">ملاحظات الحدث</label>
            <textarea name="event_notes" class="form-control" rows="2" placeholder="مثال: تقرير طبي بسبب إصابة عمل"></textarea>
          </div>

          <div class="col-md-4">
            <label class="form-label fw-semibold">تاريخ الإصدار</label>
            <input type="date" name="issue_date" class="form-control">
          </div>

          <div class="col-md-4">
            <label class="form-label fw-semibold">تاريخ الانتهاء</label>
            <input type="date" name="expiry_date" class="form-control">
          </div>

          <div class="col-md-4">
            <div class="form-check mt-4">
              <input class="form-check-input" type="checkbox" name="is_confidential" id="isConfidential">
              <label class="form-check-label" for="isConfidential">مستند سري</label>
            </div>
          </div>

          <div class="col-md-12">
            <label class="form-label fw-semibold">ملاحظات إضافية</label>
            <textarea name="notes" class="form-control" rows="2"></textarea>
          </div>
        </div>

        <div class="d-flex justify-content-end gap-2 mt-4">
          <a href="{% url 'employees:folder' employee.pk %}" class="btn btn-outline-secondary">إلغاء</a>
          <button type="submit" class="btn btn-primary">
            <i class="bi bi-cloud-upload me-1"></i>رفع المستند
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
(function() {
  const categorySelect = document.getElementById('docCategory');
  const customNameBox = document.getElementById('customNameBox');

  function toggleCustomName() {
    const val = (categorySelect.value || '').trim();
    if (val === 'other') {
      customNameBox.classList.add('visible');
    } else {
      customNameBox.classList.remove('visible');
    }
  }

  categorySelect.addEventListener('change', toggleCustomName);
  toggleCustomName();
})();
</script>
{% endblock %}
"""
write_file("templates/employees/employee_folder_upload.html", upload_template)

# ────────────────────────────────────────────────────────────
# Step 6: Add folder link to employee detail page
# ────────────────────────────────────────────────────────────
print("\n📌 Step 6: إضافة رابط المستندات في صفحة الموظف")

detail_path = "templates/employees/detail.html"
detail_content = read_file(detail_path)

if detail_content and "folder" not in detail_content:
    folder_link = '''
      <a href="{% url 'employees:folder' employee.pk %}" class="btn btn-outline-info btn-sm">
        <i class="bi bi-folder2-open me-1"></i>ملف المستندات
      </a>
'''
    # نبحث عن مكان مناسب — غالبًا بعد أزرار أخرى
    if "employee.pk" in detail_content:
        # نضيفه بعد أول </div> بعد أزرار
        detail_content = detail_content.replace(
            "ملف الموظف",
            "ملف الموظف" + folder_link,
            1
        )
        write_file(detail_path, detail_content)
        print("   ✅ تم إضافة رابط المستندات")
    else:
        print("   ⚠️ لم أتمكن من حقن الرابط — تحتاج إضافة يدوية")
else:
    if detail_content is None:
        print("   ⚠️ ملف detail.html غير موجود")
    else:
        print("   ℹ️ رابط folder موجود بالفعل")

print("\n" + "=" * 60)
print("✅ Patch 49i اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ Model جديد: EmployeeFolder
     - 27 تصنيف مستند ثابت + أخرى
     - 13 حدث مرتبط
     - ملف + حجم + تاريخ إصدار + تاريخ انتهاء
     - سري / غير سري
     - مرفوع بواسطة
  ✅ Migration: employees/migrations/0007_employee_folder.py
  ✅ Views:
     - employee_folder — عرض كل المستندات مصنفة
     - employee_folder_upload — رفع مستند جديد
     - employee_folder_delete — حذف مستند
  ✅ URLs:
     - /employees/<pk>/folder/
     - /employees/<pk>/folder/upload/
     - /employees/<pk>/folder/<doc_id>/delete/
  ✅ Templates:
     - employee_folder.html
     - employee_folder_upload.html
  ✅ رابط المستندات في صفحة تفاصيل الموظف

شغّل:
  python manage.py makemigrations --check
  python manage.py migrate
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")