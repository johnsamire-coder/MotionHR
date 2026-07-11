"""
Patch 49c Revised — Job Hierarchy Setup + Direct Manager Logic

الهدف:
1) إضافة شاشة لإدارة الهيكل الوظيفي:
   Department + Job Level + Job Title + Parent Job Title
2) direct_manager يعتمد أولاً على القواعد المعرّفة في الشاشة
3) fallback ذكي لو القواعد لم تُضبط بعد
4) تحديث فورم الموظف ليحمّل المديرين المحتملين Live حسب الإدارة + المسمى الوظيفي
5) هذا الباتش supersedes أي Patch 49c قديم لم يتم تشغيله

مهم:
- لا تشغّل أي Patch 49c قديم خاص بالمدير المباشر بعد هذا الباتش
"""

import os
import shutil
import subprocess
import sys
import re

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
print("Patch 49c Revised — Job Hierarchy Setup + Direct Manager Logic")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# Backups
# ─────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path, backup_name in [
    ("employees/models.py", "employees_models_before_patch_49c_revised.py.bak"),
    ("employees/views.py", "employees_views_before_patch_49c_revised.py.bak"),
    ("employees/urls.py", "employees_urls_before_patch_49c_revised.py.bak"),
    ("employees/admin.py", "employees_admin_before_patch_49c_revised.py.bak"),
    ("templates/employees/form.html", "employees_form_before_patch_49c_revised.html.bak"),
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup created: _patches/_backups/{backup_name}")

# ─────────────────────────────────────────────────────────────
# Step 1: Append models to employees/models.py
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 1: تحديث employees/models.py")

models_path = "employees/models.py"
models_content = read_file(models_path)
if models_content is None:
    raise SystemExit("❌ ملف employees/models.py غير موجود")

models_append = '''

# ═════════════════════════════════════════════════════════════
# Patch 49c Revised — Job Hierarchy Models
# ═════════════════════════════════════════════════════════════

class JobHierarchyLevel(models.Model):
    """
    مستوى وظيفي معرف من الشركة:
    الرقم الأقل = مستوى أعلى
    مثال:
      1 صاحب الشركة
      2 مدير عام
      3 مدير
      4 مشرف
      5 أخصائي
      6 موظف
      7 عامل
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='job_hierarchy_levels',
        verbose_name='الشركة',
    )
    name_ar = models.CharField(max_length=150, verbose_name='الاسم بالعربي')
    name_en = models.CharField(max_length=150, blank=True, verbose_name='الاسم بالإنجليزي')
    sort_order = models.PositiveIntegerField(default=1, verbose_name='الترتيب الهرمي')
    description = models.TextField(blank=True, verbose_name='الوصف')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستوى وظيفي'
        verbose_name_plural = 'المستويات الوظيفية'
        ordering = ['sort_order', 'id']
        unique_together = [
            ['company', 'sort_order'],
            ['company', 'name_ar'],
        ]

    def __str__(self):
        return f"{self.sort_order} - {self.name_ar}"


class DepartmentJobTitleRule(models.Model):
    """
    ربط:
      الإدارة + المسمى الوظيفي + المستوى + المسمى الوظيفي الأب المباشر
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='department_job_title_rules',
        verbose_name='الشركة',
    )
    department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        related_name='job_title_rules',
        verbose_name='الإدارة',
    )
    job_title = models.ForeignKey(
        'employees.JobTitle',
        on_delete=models.CASCADE,
        related_name='hierarchy_rules',
        verbose_name='المسمى الوظيفي',
    )
    level = models.ForeignKey(
        'employees.JobHierarchyLevel',
        on_delete=models.CASCADE,
        related_name='job_title_rules',
        verbose_name='المستوى الوظيفي',
    )
    parent_job_title = models.ForeignKey(
        'employees.JobTitle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_hierarchy_rules',
        verbose_name='المسمى الأعلى المباشر',
    )
    same_department_only = models.BooleanField(
        default=True,
        verbose_name='المدير من نفس الإدارة فقط',
    )
    allow_higher_parent_fallback = models.BooleanField(
        default=True,
        verbose_name='السماح ببدائل أعلى لو المسمى الأب غير موجود',
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'قاعدة ربط وظيفي'
        verbose_name_plural = 'قواعد الربط الوظيفي'
        ordering = ['department_id', 'level__sort_order', 'job_title_id', 'id']
        unique_together = [
            ['company', 'department', 'job_title']
        ]

    def __str__(self):
        parent = self.parent_job_title.name_ar if self.parent_job_title else 'بدون'
        return f"{self.department.name_ar} | {self.job_title.name_ar} -> {parent}"
'''

if "class JobHierarchyLevel(models.Model):" not in models_content:
    models_content = models_content.rstrip() + "\n" + models_append + "\n"
    write_file(models_path, models_content)
else:
    print("ℹ️ JobHierarchyLevel موجودة بالفعل - تم تجاهل الإضافة")

# ─────────────────────────────────────────────────────────────
# Step 2: Write manual migration
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء migration يدوي")

migration_code = '''from django.db import migrations, models
import django.db.models.deletion


def seed_default_job_levels(apps, schema_editor):
    Company = apps.get_model('companies', 'Company')
    JobHierarchyLevel = apps.get_model('employees', 'JobHierarchyLevel')

    defaults = [
        (1, 'صاحب الشركة', 'Company Owner'),
        (2, 'مدير عام', 'General Manager'),
        (3, 'مدير', 'Manager'),
        (4, 'مشرف', 'Supervisor'),
        (5, 'أخصائي', 'Specialist'),
        (6, 'موظف', 'Employee'),
        (7, 'عامل', 'Worker'),
    ]

    for company in Company.objects.all():
        for sort_order, name_ar, name_en in defaults:
            JobHierarchyLevel.objects.get_or_create(
                company_id=company.id,
                sort_order=sort_order,
                defaults={
                    'name_ar': name_ar,
                    'name_en': name_en,
                    'is_active': True,
                    'description': '',
                }
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0013_alter_notificationpreference_id'),
        ('employees', '0005_add_stealth_tracking_to_employee'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobHierarchyLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_ar', models.CharField(max_length=150, verbose_name='الاسم بالعربي')),
                ('name_en', models.CharField(blank=True, max_length=150, verbose_name='الاسم بالإنجليزي')),
                ('sort_order', models.PositiveIntegerField(default=1, verbose_name='الترتيب الهرمي')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_hierarchy_levels', to='companies.company', verbose_name='الشركة')),
            ],
            options={
                'verbose_name': 'مستوى وظيفي',
                'verbose_name_plural': 'المستويات الوظيفية',
                'ordering': ['sort_order', 'id'],
                'unique_together': {('company', 'sort_order'), ('company', 'name_ar')},
            },
        ),
        migrations.CreateModel(
            name='DepartmentJobTitleRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('same_department_only', models.BooleanField(default=True, verbose_name='المدير من نفس الإدارة فقط')),
                ('allow_higher_parent_fallback', models.BooleanField(default=True, verbose_name='السماح ببدائل أعلى لو المسمى الأب غير موجود')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_job_title_rules', to='companies.company', verbose_name='الشركة')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_title_rules', to='companies.department', verbose_name='الإدارة')),
                ('job_title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hierarchy_rules', to='employees.jobtitle', verbose_name='المسمى الوظيفي')),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_title_rules', to='employees.jobhierarchylevel', verbose_name='المستوى الوظيفي')),
                ('parent_job_title', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_hierarchy_rules', to='employees.jobtitle', verbose_name='المسمى الأعلى المباشر')),
            ],
            options={
                'verbose_name': 'قاعدة ربط وظيفي',
                'verbose_name_plural': 'قواعد الربط الوظيفي',
                'ordering': ['department_id', 'level__sort_order', 'job_title_id', 'id'],
                'unique_together': {('company', 'department', 'job_title')},
            },
        ),
        migrations.RunPython(seed_default_job_levels, noop_reverse),
    ]
'''
write_file("employees/migrations/0006_job_hierarchy_models.py", migration_code)

# ─────────────────────────────────────────────────────────────
# Step 3: Update admin.py
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 3: تحديث employees/admin.py")

admin_path = "employees/admin.py"
admin_content = read_file(admin_path)
if admin_content is None:
    admin_content = "from django.contrib import admin\n"

if "JobHierarchyLevel" not in admin_content:
    if "from .models import" in admin_content:
        admin_content = admin_content.replace(
            "from .models import",
            "from .models import JobHierarchyLevel, DepartmentJobTitleRule,",
            1
        )
    else:
        admin_content += "\nfrom .models import JobHierarchyLevel, DepartmentJobTitleRule\n"

admin_append = '''

@admin.register(JobHierarchyLevel)
class JobHierarchyLevelAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'company', 'sort_order', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('name_ar', 'name_en')
    ordering = ('company', 'sort_order', 'id')


@admin.register(DepartmentJobTitleRule)
class DepartmentJobTitleRuleAdmin(admin.ModelAdmin):
    list_display = ('department', 'job_title', 'level', 'parent_job_title', 'same_department_only', 'is_active')
    list_filter = ('company', 'department', 'level', 'same_department_only', 'is_active')
    search_fields = ('department__name_ar', 'job_title__name_ar', 'parent_job_title__name_ar')
'''
if "@admin.register(JobHierarchyLevel)" not in admin_content:
    admin_content = admin_content.rstrip() + "\n" + admin_append + "\n"
write_file(admin_path, admin_content)

# ─────────────────────────────────────────────────────────────
# Step 4: Rewrite employees/urls.py
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 4: إعادة كتابة employees/urls.py")

urls_code = '''from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('api/search/', views.employee_search_api, name='search_api'),
    path('api/manager-options/', views.employee_manager_options_api, name='manager_options_api'),
    path('hierarchy/', views.job_hierarchy_manage, name='hierarchy_manage'),

    path('add/', views.employee_add, name='add'),
    path('print/', views.employee_print, name='print_all'),
    path('my-balance/', views.my_balance_view, name='my_balance'),
    path('my-deductions/', views.my_deductions_view, name='my_deductions'),

    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/delete/', views.employee_delete, name='delete'),
    path('<int:pk>/print/', views.employee_print_detail, name='print_detail'),
    path('<int:pk>/credentials/', views.print_credentials_view, name='print_credentials'),
    path('<int:pk>/create-account/', views.create_account_view, name='create_account'),
    path('<int:pk>/deactivate-account/', views.deactivate_account_view, name='deactivate_account'),
    path('<int:pk>/reset-password/', views.reset_password_view, name='reset_password'),
    path('<int:pk>/', views.employee_detail, name='detail'),

    path('', views.employee_list, name='list'),
]
'''
write_file(urls_path := "employees/urls.py", urls_code)

# ─────────────────────────────────────────────────────────────
# Step 5: Rewrite employees/views.py cleanly
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 5: إعادة كتابة employees/views.py")

views_code = r'''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.crypto import get_random_string

from .models import (
    Employee, JobTitle, Deduction,
    JobHierarchyLevel, DepartmentJobTitleRule,
)
from .forms import EmployeeForm
from .exports import export_employees_excel, export_employees_pdf
from companies.models import Branch, Department
from subscriptions.helpers import feature_required
from core.permissions import (
    get_accessible_employees,
    can_user_edit_employee,
    can_user_delete_employee,
    can_user_add_employee,
    is_admin_or_hr,
)


# ═════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════

def _get_current_company(user):
    company = getattr(user, 'company', None)
    if company:
        return company
    try:
        return user.employee.company
    except Exception:
        return None


def _employee_name(employee):
    if not employee:
        return '—'
    return (
        getattr(employee, 'full_name_ar', None)
        or f"{getattr(employee, 'first_name_ar', '')} {getattr(employee, 'last_name_ar', '')}".strip()
        or getattr(employee, 'employee_code', '')
        or 'الموظف'
    )


def _status_choices():
    return getattr(Employee, 'STATUS_CHOICES', [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'موقوف'),
        ('terminated', 'منتهي الخدمة'),
    ])


def _safe_qs(model, company=None):
    qs = model.objects.all()
    if company and hasattr(model, 'company'):
        try:
            qs = qs.filter(company=company)
        except Exception:
            pass
    return qs


def _can_manage_hierarchy(user):
    role = getattr(user, 'role', '') or ''
    return role in ['company_admin', 'hr_manager'] or is_admin_or_hr(user)


# ═════════════════════════════════════════════════════════════
# Hierarchy ranking helpers
# ═════════════════════════════════════════════════════════════

def _job_title_text(job_title):
    if not job_title:
        return ''
    return f"{getattr(job_title, 'name_ar', '')} {getattr(job_title, 'name_en', '')}".strip().lower()


def _job_title_explicit_rank(job_title):
    """
    لو موديل JobTitle فيه level/rank/order فعلي نستخدمه
    الأقل = أعلى
    """
    if not job_title:
        return None
    for attr in ['level', 'rank', 'sort_order', 'hierarchy_level', 'order', 'priority']:
        if hasattr(job_title, attr):
            try:
                val = getattr(job_title, attr)
                if val is not None and str(val).strip() != '':
                    return int(val)
            except Exception:
                pass
    return None


def _job_title_rank_from_keywords(job_title):
    """
    fallback heuristic لو لم تُضبط القواعد بعد
    الأقل = أعلى
    """
    text = _job_title_text(job_title)
    if not text:
        return 6

    groups = [
        (1, ['owner', 'founder', 'chairman', 'ceo', 'president', 'مالك', 'مؤسس', 'رئيس تنفيذي', 'صاحب الشركة', 'رئيس مجلس']),
        (2, ['general manager', 'executive director', 'managing director', 'chief', 'مدير عام', 'مدير تنفيذي', 'مدير قطاع', 'رئيس قطاع']),
        (3, ['manager', 'department head', 'branch manager', 'مدير', 'رئيس قسم']),
        (4, ['supervisor', 'team lead', 'lead', 'coordinator', 'مشرف', 'قائد فريق', 'منسق']),
        (5, ['senior', 'specialist', 'officer', 'executive', 'analyst', 'accountant', 'engineer', 'consultant', 'أخصائي', 'مسؤول', 'تنفيذي', 'محاسب', 'مهندس', 'محلل', 'استشاري']),
        (6, ['employee', 'staff', 'associate', 'assistant', 'representative', 'clerk', 'technician', 'administrator', 'موظف', 'مساعد', 'مندوب', 'فني', 'إداري']),
        (7, ['worker', 'labor', 'driver', 'intern', 'trainee', 'helper', 'عامل', 'سائق', 'متدرب']),
    ]
    for rank, keywords in groups:
        for kw in keywords:
            if kw in text:
                return rank
    return 6


def _job_title_hierarchy_rank(job_title):
    explicit = _job_title_explicit_rank(job_title)
    if explicit is not None:
        return explicit
    return _job_title_rank_from_keywords(job_title)


def _user_role_rank(user):
    role = getattr(user, 'role', '') if user else ''
    mapping = {
        'company_admin': 1,
        'hr_manager': 3,
        'manager': 3,
        'employee': 6,
    }
    return mapping.get(role, 6)


def _employee_hierarchy_rank(employee):
    title_rank = _job_title_hierarchy_rank(getattr(employee, 'job_title', None))
    role_rank = _user_role_rank(getattr(employee, 'user', None))
    return min(title_rank, role_rank)


def _get_selected_job_title(form=None, instance=None):
    selected_job_title = None
    selected_job_title_id = None

    try:
        if form is not None and hasattr(form, 'data'):
            selected_job_title_id = form.data.get('job_title') or None
    except Exception:
        selected_job_title_id = None

    if selected_job_title_id:
        try:
            selected_job_title = JobTitle.objects.get(pk=selected_job_title_id)
        except Exception:
            selected_job_title = None

    if not selected_job_title and instance is not None:
        selected_job_title = getattr(instance, 'job_title', None)

    return selected_job_title


def _get_selected_department(form=None, instance=None):
    selected_department = None
    selected_department_id = None

    try:
        if form is not None and hasattr(form, 'data'):
            selected_department_id = form.data.get('department') or None
    except Exception:
        selected_department_id = None

    if selected_department_id:
        try:
            selected_department = Department.objects.get(pk=selected_department_id)
        except Exception:
            selected_department = None

    if not selected_department and instance is not None:
        selected_department = getattr(instance, 'department', None)

    return selected_department


def _get_manager_candidates_queryset(company=None, instance=None, selected_job_title=None, selected_department=None):
    """
    الأولوية:
    1) لو فيه Rule صريح للإدارة + المسمى الوظيفي → نعتمده
    2) لو لا → fallback heuristic
    """
    base_qs = _safe_qs(Employee, company).select_related('user', 'job_title', 'department')

    try:
        base_qs = base_qs.filter(status='active')
    except Exception:
        pass

    if instance and instance.pk:
        base_qs = base_qs.exclude(pk=instance.pk)

    if not selected_job_title:
        return base_qs.none()

    current_manager_id = getattr(instance, 'direct_manager_id', None) if instance else None

    # ── Rule-based selection ────────────────────────────────
    if company and selected_department:
        try:
            rule = DepartmentJobTitleRule.objects.select_related('level', 'parent_job_title').get(
                company=company,
                department=selected_department,
                job_title=selected_job_title,
                is_active=True,
            )
        except DepartmentJobTitleRule.DoesNotExist:
            rule = None

        if rule:
            scoped_qs = base_qs
            if rule.same_department_only:
                scoped_qs = scoped_qs.filter(department=selected_department)

            # parent exact title
            if rule.parent_job_title:
                exact_qs = scoped_qs.filter(job_title=rule.parent_job_title)
                if exact_qs.exists():
                    candidate_ids = list(exact_qs.values_list('id', flat=True))
                    if current_manager_id and current_manager_id not in candidate_ids:
                        candidate_ids.append(current_manager_id)
                    return base_qs.filter(id__in=candidate_ids).distinct().order_by('employee_code', 'id')

            # fallback to any higher level titles from same configured rules
            if rule.allow_higher_parent_fallback:
                higher_rules = DepartmentJobTitleRule.objects.filter(
                    company=company,
                    is_active=True,
                    level__sort_order__lt=rule.level.sort_order
                )
                if rule.same_department_only:
                    higher_rules = higher_rules.filter(department=selected_department)

                higher_title_ids = list(higher_rules.values_list('job_title_id', flat=True).distinct())
                if higher_title_ids:
                    higher_qs = scoped_qs.filter(job_title_id__in=higher_title_ids)
                    if higher_qs.exists():
                        candidate_ids = list(higher_qs.values_list('id', flat=True))
                        if current_manager_id and current_manager_id not in candidate_ids:
                            candidate_ids.append(current_manager_id)
                        return base_qs.filter(id__in=candidate_ids).distinct().order_by('employee_code', 'id')

            # لو القاعدة موجودة لكن لم نجد مرشحين
            if current_manager_id:
                return base_qs.filter(id=current_manager_id)
            return base_qs.none()

    # ── Heuristic fallback ──────────────────────────────────
    selected_rank = _job_title_hierarchy_rank(selected_job_title)
    candidate_ids = []

    for emp in base_qs:
        emp_rank = _employee_hierarchy_rank(emp)
        if emp_rank < selected_rank:
            candidate_ids.append(emp.id)

    if current_manager_id and current_manager_id not in candidate_ids:
        candidate_ids.append(current_manager_id)

    if not candidate_ids:
        return base_qs.none()

    return base_qs.filter(id__in=candidate_ids).distinct().order_by('employee_code', 'id')


def _configure_employee_form(form, company=None, instance=None):
    try:
        if 'branch' in form.fields:
            form.fields['branch'].queryset = _safe_qs(Branch, company).order_by('name_ar', 'name_en')
    except Exception:
        pass

    try:
        if 'department' in form.fields:
            form.fields['department'].queryset = _safe_qs(Department, company).order_by('name_ar', 'name_en')
    except Exception:
        pass

    try:
        if 'job_title' in form.fields:
            qs = _safe_qs(JobTitle, company)
            if hasattr(JobTitle, 'is_active'):
                try:
                    qs = qs.filter(is_active=True)
                except Exception:
                    pass
            form.fields['job_title'].queryset = qs.order_by('name_ar', 'name_en')
    except Exception:
        pass

    try:
        if 'direct_manager' in form.fields:
            selected_job_title = _get_selected_job_title(form=form, instance=instance)
            selected_department = _get_selected_department(form=form, instance=instance)

            qs = _get_manager_candidates_queryset(
                company=company,
                instance=instance,
                selected_job_title=selected_job_title,
                selected_department=selected_department,
            )
            form.fields['direct_manager'].queryset = qs

            try:
                if not selected_department and not selected_job_title:
                    form.fields['direct_manager'].empty_label = 'اختر الإدارة والمسمى الوظيفي أولًا'
                elif selected_job_title and not selected_department:
                    form.fields['direct_manager'].empty_label = 'اختر الإدارة أولًا'
                elif selected_department and not selected_job_title:
                    form.fields['direct_manager'].empty_label = 'اختر المسمى الوظيفي أولًا'
                elif qs.exists():
                    form.fields['direct_manager'].empty_label = 'اختر المدير المباشر المناسب'
                else:
                    form.fields['direct_manager'].empty_label = 'لا يوجد مدير أعلى مناسب حاليًا'
            except Exception:
                pass
    except Exception:
        pass


def _try_sync_employee_account(employee):
    try:
        from . import account_utils
    except Exception:
        return False

    candidate_names = [
        'create_or_update_employee_account',
        'ensure_employee_account',
        'sync_employee_account',
        'sync_employee_user',
        'create_employee_account',
        'provision_employee_account',
        'create_employee_user',
    ]

    for name in candidate_names:
        fn = getattr(account_utils, name, None)
        if callable(fn):
            try:
                fn(employee)
                return True
            except TypeError:
                try:
                    fn(employee=employee)
                    return True
                except Exception:
                    pass
            except Exception:
                pass
    return False


def _redirect_employee_detail_or_list(employee):
    for url_name in ['employees:detail', 'employees:list']:
        try:
            if 'detail' in url_name:
                return redirect(url_name, pk=employee.pk)
            return redirect(url_name)
        except Exception:
            continue
    return redirect('dashboard')


def _get_employee_or_404_for_user(user, pk):
    qs = get_accessible_employees(user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    )
    return get_object_or_404(qs, pk=pk)


# ═════════════════════════════════════════════════════════════
# Employee List
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_list(request):
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    )

    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(middle_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(first_name_en__icontains=search) |
            Q(last_name_en__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(job_title__name_ar__icontains=search) |
            Q(job_title__name_en__icontains=search) |
            Q(branch__name_ar__icontains=search) |
            Q(branch__name_en__icontains=search) |
            Q(department__name_ar__icontains=search) |
            Q(department__name_en__icontains=search)
        ).distinct()

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        employees = employees.filter(status=status_filter)

    branch_filter = request.GET.get('branch', '').strip()
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)

    department_filter = request.GET.get('department', '').strip()
    if department_filter:
        employees = employees.filter(department_id=department_filter)

    employees = employees.order_by('employee_code', 'id')

    export_type = request.GET.get('export', '').strip()
    if export_type == 'excel':
        return export_employees_excel(employees, user=request.user)
    elif export_type == 'pdf':
        try:
            return export_employees_pdf(employees, user=request.user)
        except Exception as e:
            messages.warning(request, f'خطأ في تصدير PDF: {e}')
            return redirect('employees:list')

    paginator = Paginator(employees, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    company = _get_current_company(request.user)
    branches = _safe_qs(Branch, company).order_by('name_ar', 'name_en')
    departments = _safe_qs(Department, company).order_by('name_ar', 'name_en')

    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'branches': branches,
        'departments': departments,
        'search': search,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'status_choices': _status_choices(),
    }
    return render(request, 'employees/list.html', context)


# ═════════════════════════════════════════════════════════════
# Live Search API
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_search_api(request):
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    department_filter = request.GET.get('department', '').strip()

    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    )

    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(middle_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(first_name_en__icontains=search) |
            Q(last_name_en__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(job_title__name_ar__icontains=search) |
            Q(job_title__name_en__icontains=search) |
            Q(branch__name_ar__icontains=search) |
            Q(branch__name_en__icontains=search) |
            Q(department__name_ar__icontains=search) |
            Q(department__name_en__icontains=search)
        ).distinct()

    if status_filter:
        employees = employees.filter(status=status_filter)
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)
    if department_filter:
        employees = employees.filter(department_id=department_filter)

    employees = employees.order_by('employee_code', 'id')[:100]

    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'employee_code': emp.employee_code or '',
            'full_name_ar': _employee_name(emp),
            'job_title': (
                getattr(emp.job_title, 'name_ar', None)
                or getattr(emp.job_title, 'name_en', None)
                or '—'
            ) if getattr(emp, 'job_title', None) else '—',
            'department': (
                getattr(emp.department, 'name_ar', None)
                or getattr(emp.department, 'name_en', None)
                or '—'
            ) if getattr(emp, 'department', None) else '—',
            'branch': (
                getattr(emp.branch, 'name_ar', None)
                or getattr(emp.branch, 'name_en', None)
                or '—'
            ) if getattr(emp, 'branch', None) else '—',
            'phone': emp.phone or '—',
            'email': emp.email or '—',
            'status': emp.get_status_display() if hasattr(emp, 'get_status_display') else (emp.status or '—'),
            'manager': _employee_name(emp.direct_manager) if getattr(emp, 'direct_manager', None) else '—',
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
        'results': results,
    })


# ═════════════════════════════════════════════════════════════
# Job Hierarchy Management
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def job_hierarchy_manage(request):
    company = _get_current_company(request.user)
    if not company:
        messages.error(request, 'لا يمكن تحديد الشركة الحالية.')
        return redirect('employees:list')

    if not _can_manage_hierarchy(request.user):
        raise PermissionDenied('ليس لديك صلاحية إدارة الهيكل الوظيفي')

    departments = Department.objects.filter(company=company).order_by('name_ar', 'name_en')
    job_titles = JobTitle.objects.filter(company=company).order_by('name_ar', 'name_en')
    levels = JobHierarchyLevel.objects.filter(company=company).order_by('sort_order', 'id')

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        # ── Add level ────────────────────────────────────────
        if action == 'add_level':
            name_ar = (request.POST.get('name_ar') or '').strip()
            name_en = (request.POST.get('name_en') or '').strip()
            sort_order = (request.POST.get('sort_order') or '').strip()
            description = (request.POST.get('description') or '').strip()
            is_active = bool(request.POST.get('is_active'))

            if not name_ar:
                messages.error(request, 'اسم المستوى بالعربي مطلوب')
                return redirect('employees:hierarchy_manage')

            try:
                sort_order = int(sort_order)
            except Exception:
                messages.error(request, 'الترتيب الهرمي يجب أن يكون رقمًا صحيحًا')
                return redirect('employees:hierarchy_manage')

            try:
                JobHierarchyLevel.objects.create(
                    company=company,
                    name_ar=name_ar,
                    name_en=name_en,
                    sort_order=sort_order,
                    description=description,
                    is_active=is_active,
                )
                messages.success(request, f'تم إضافة المستوى الوظيفي: {name_ar}')
            except Exception as e:
                messages.error(request, f'تعذر إضافة المستوى الوظيفي: {e}')
            return redirect('employees:hierarchy_manage')

        # ── Delete level ─────────────────────────────────────
        if action == 'delete_level':
            level_id = request.POST.get('level_id')
            level = get_object_or_404(JobHierarchyLevel, pk=level_id, company=company)
            if DepartmentJobTitleRule.objects.filter(company=company, level=level).exists():
                messages.error(request, 'لا يمكن حذف هذا المستوى لأنه مستخدم في قواعد الربط')
            else:
                level_name = level.name_ar
                level.delete()
                messages.success(request, f'تم حذف المستوى: {level_name}')
            return redirect('employees:hierarchy_manage')

        # ── Save rule (upsert) ───────────────────────────────
        if action == 'save_rule':
            department_id = (request.POST.get('department_id') or '').strip()
            job_title_id = (request.POST.get('job_title_id') or '').strip()
            level_id = (request.POST.get('level_id') or '').strip()
            parent_job_title_id = (request.POST.get('parent_job_title_id') or '').strip()
            same_department_only = bool(request.POST.get('same_department_only'))
            allow_higher_parent_fallback = bool(request.POST.get('allow_higher_parent_fallback'))
            is_active = bool(request.POST.get('rule_is_active'))
            notes = (request.POST.get('notes') or '').strip()

            if not department_id or not job_title_id or not level_id:
                messages.error(request, 'الإدارة + المسمى الوظيفي + المستوى الوظيفي حقول مطلوبة')
                return redirect('employees:hierarchy_manage')

            department = get_object_or_404(Department, pk=department_id, company=company)
            job_title = get_object_or_404(JobTitle, pk=job_title_id, company=company)
            level = get_object_or_404(JobHierarchyLevel, pk=level_id, company=company)

            parent_job_title = None
            if parent_job_title_id:
                parent_job_title = get_object_or_404(JobTitle, pk=parent_job_title_id, company=company)

            if parent_job_title and parent_job_title.id == job_title.id:
                messages.error(request, 'لا يمكن أن يكون المسمى الوظيفي هو نفسه المسمى الأعلى المباشر')
                return redirect('employees:hierarchy_manage')

            try:
                rule, created = DepartmentJobTitleRule.objects.update_or_create(
                    company=company,
                    department=department,
                    job_title=job_title,
                    defaults={
                        'level': level,
                        'parent_job_title': parent_job_title,
                        'same_department_only': same_department_only,
                        'allow_higher_parent_fallback': allow_higher_parent_fallback,
                        'is_active': is_active,
                        'notes': notes,
                    }
                )
                if created:
                    messages.success(request, f'تم إنشاء قاعدة ربط لـ {job_title.name_ar} داخل {department.name_ar}')
                else:
                    messages.success(request, f'تم تحديث قاعدة الربط لـ {job_title.name_ar} داخل {department.name_ar}')
            except Exception as e:
                messages.error(request, f'تعذر حفظ القاعدة: {e}')

            return redirect('employees:hierarchy_manage')

        # ── Delete rule ──────────────────────────────────────
        if action == 'delete_rule':
            rule_id = request.POST.get('rule_id')
            rule = get_object_or_404(DepartmentJobTitleRule, pk=rule_id, company=company)
            title_name = getattr(rule.job_title, 'name_ar', 'القاعدة')
            dept_name = getattr(rule.department, 'name_ar', 'الإدارة')
            rule.delete()
            messages.success(request, f'تم حذف قاعدة الربط: {title_name} / {dept_name}')
            return redirect('employees:hierarchy_manage')

    rules = DepartmentJobTitleRule.objects.filter(company=company).select_related(
        'department', 'job_title', 'level', 'parent_job_title'
    ).order_by('department__name_ar', 'level__sort_order', 'job_title__name_ar')

    return render(request, 'employees/job_hierarchy_manage.html', {
        'page_title': 'إدارة الهيكل الوظيفي',
        'departments': departments,
        'job_titles': job_titles,
        'levels': levels,
        'rules': rules,
    })


# ═════════════════════════════════════════════════════════════
# Manager Options API
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_manager_options_api(request):
    company = _get_current_company(request.user)
    if not company:
        return JsonResponse({
            'success': False,
            'count': 0,
            'results': [],
            'message': 'لا يمكن تحديد الشركة الحالية',
        })

    job_title_id = (request.GET.get('job_title_id') or '').strip()
    department_id = (request.GET.get('department_id') or '').strip()
    employee_id = (request.GET.get('employee_id') or '').strip()

    instance = None
    if employee_id:
        try:
            instance = Employee.objects.get(pk=employee_id)
        except Exception:
            instance = None

    selected_job_title = None
    if job_title_id:
        try:
            selected_job_title = JobTitle.objects.get(pk=job_title_id, company=company)
        except Exception:
            selected_job_title = None

    selected_department = None
    if department_id:
        try:
            selected_department = Department.objects.get(pk=department_id, company=company)
        except Exception:
            selected_department = None

    if not selected_job_title and not selected_department:
        return JsonResponse({
            'success': True,
            'count': 0,
            'results': [],
            'message': 'اختر الإدارة والمسمى الوظيفي أولًا',
        })

    if not selected_department:
        return JsonResponse({
            'success': True,
            'count': 0,
            'results': [],
            'message': 'اختر الإدارة أولًا',
        })

    if not selected_job_title:
        return JsonResponse({
            'success': True,
            'count': 0,
            'results': [],
            'message': 'اختر المسمى الوظيفي أولًا',
        })

    qs = _get_manager_candidates_queryset(
        company=company,
        instance=instance,
        selected_job_title=selected_job_title,
        selected_department=selected_department,
    )

    results = []
    for emp in qs[:200]:
        results.append({
            'id': emp.id,
            'name': _employee_name(emp),
            'employee_code': emp.employee_code or '',
            'job_title': (
                getattr(emp.job_title, 'name_ar', None)
                or getattr(emp.job_title, 'name_en', None)
                or '—'
            ) if getattr(emp, 'job_title', None) else '—',
            'department': (
                getattr(emp.department, 'name_ar', None)
                or getattr(emp.department, 'name_en', None)
                or '—'
            ) if getattr(emp, 'department', None) else '—',
            'rank': _employee_hierarchy_rank(emp),
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
        'results': results,
        'message': 'تم تحميل المديرين المحتملين بنجاح',
    })


# ═════════════════════════════════════════════════════════════
# Add / Edit / Delete / Detail
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_add(request):
    if not can_user_add_employee(request.user):
        raise PermissionDenied('ليس لديك صلاحية إضافة موظف')

    company = _get_current_company(request.user)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        _configure_employee_form(form, company=company)

        if form.is_valid():
            employee = form.save(commit=False)
            if company and hasattr(employee, 'company_id') and not employee.company_id:
                employee.company = company
            employee.save()
            try:
                form.save_m2m()
            except Exception:
                pass

            _try_sync_employee_account(employee)
            messages.success(request, f'تم إضافة الموظف {_employee_name(employee)} بنجاح')
            return redirect('employees:list')
        else:
            messages.error(request, 'يرجى مراجعة الحقول المطلوبة')
    else:
        form = EmployeeForm()
        _configure_employee_form(form, company=company)

    return render(request, 'employees/form.html', {
        'form': form,
        'page_title': 'إضافة موظف',
        'form_title': 'إضافة موظف جديد',
        'is_edit': False,
    })


@login_required
@feature_required('employees_management')
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not can_user_edit_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية تعديل هذا الموظف')

    company = _get_current_company(request.user)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        _configure_employee_form(form, company=company, instance=employee)

        if form.is_valid():
            employee = form.save(commit=False)
            if company and hasattr(employee, 'company_id') and not employee.company_id:
                employee.company = company
            employee.save()
            try:
                form.save_m2m()
            except Exception:
                pass

            _try_sync_employee_account(employee)
            messages.success(request, f'تم تحديث بيانات الموظف {_employee_name(employee)}')
            return redirect('employees:list')
        else:
            messages.error(request, 'يرجى مراجعة الحقول المطلوبة')
    else:
        form = EmployeeForm(instance=employee)
        _configure_employee_form(form, company=company, instance=employee)

    return render(request, 'employees/form.html', {
        'form': form,
        'employee': employee,
        'page_title': 'تعديل موظف',
        'form_title': 'تعديل بيانات الموظف',
        'is_edit': True,
    })


@login_required
@feature_required('employees_management')
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not can_user_delete_employee(request.user, employee):
        raise PermissionDenied('ليس لديك صلاحية حذف هذا الموظف')

    if request.method == 'POST':
        name = _employee_name(employee)
        employee.delete()
        messages.success(request, f'تم حذف الموظف {name}')
        return redirect('employees:list')

    return render(request, 'employees/delete_confirm.html', {
        'employee': employee,
        'page_title': 'حذف موظف',
    })


@login_required
@feature_required('employees_management')
def employee_detail(request, pk):
    employee = _get_employee_or_404_for_user(request.user, pk)

    documents = []
    deductions = []

    for rel_name in ['documents', 'employeedocument_set']:
        rel = getattr(employee, rel_name, None)
        if rel is not None:
            try:
                documents = rel.all()
                break
            except Exception:
                pass

    for rel_name in ['deductions', 'deduction_set']:
        rel = getattr(employee, rel_name, None)
        if rel is not None:
            try:
                deductions = rel.all()
                break
            except Exception:
                pass

    return render(request, 'employees/detail.html', {
        'employee': employee,
        'documents': documents,
        'deductions': deductions,
        'page_title': f'ملف الموظف - {_employee_name(employee)}',
    })


# ═════════════════════════════════════════════════════════════
# Print Views
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def employee_print_list(request):
    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager', 'user'
    ).order_by('employee_code', 'id')

    return render(request, 'employees/print_list.html', {
        'employees': employees,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'page_title': 'طباعة قائمة الموظفين',
    })


@login_required
@feature_required('employees_management')
def employee_print_detail(request, pk):
    employee = _get_employee_or_404_for_user(request.user, pk)

    return render(request, 'employees/print_detail.html', {
        'employee': employee,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'page_title': f'طباعة ملف الموظف - {_employee_name(employee)}',
    })


@login_required
@feature_required('employees_management')
def print_credentials(request, pk):
    employee = _get_employee_or_404_for_user(request.user, pk)
    username = '—'
    if getattr(employee, 'user', None):
        username = getattr(employee.user, 'username', '—') or '—'

    return render(request, 'employees/print_credentials.html', {
        'employee': employee,
        'company': _get_current_company(request.user),
        'printed_at': timezone.now(),
        'username': username,
        'page_title': f'بيانات الدخول - {_employee_name(employee)}',
    })


# ═════════════════════════════════════════════════════════════
# Account Views
# ═════════════════════════════════════════════════════════════

@login_required
@feature_required('employees_management')
def create_account_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية إنشاء حساب لهذا الموظف')

    try:
        before_user = getattr(employee, 'user', None)
        synced = _try_sync_employee_account(employee)
        employee.refresh_from_db()
        after_user = getattr(employee, 'user', None)

        if after_user:
            username = getattr(after_user, 'username', None) or '—'
            if before_user:
                messages.success(request, f'تمت مزامنة حساب الموظف {_employee_name(employee)} (اسم المستخدم: {username})')
            else:
                messages.success(request, f'تم إنشاء حساب للموظف {_employee_name(employee)} (اسم المستخدم: {username})')
        else:
            if synced:
                messages.warning(request, 'تمت محاولة إنشاء الحساب لكن لم يتم ربط مستخدم بالموظف.')
            else:
                messages.warning(request, 'لا يوجد helper صالح لإنشاء الحساب في account_utils.')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')

    return _redirect_employee_detail_or_list(employee)


@login_required
@feature_required('employees_management')
def deactivate_account_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية إدارة حساب هذا الموظف')

    user = getattr(employee, 'user', None)
    if not user:
        messages.warning(request, 'هذا الموظف لا يملك حساب مستخدم مرتبطًا به.')
        return _redirect_employee_detail_or_list(employee)

    action = request.POST.get('action', '').strip().lower() if request.method == 'POST' else ''

    try:
        if request.method == 'POST' and action == 'activate':
            user.is_active = True
            if hasattr(user, 'must_change_password'):
                try:
                    user.must_change_password = True
                except Exception:
                    pass
            user.save()
            messages.success(request, f'تمت إعادة تفعيل حساب الموظف {_employee_name(employee)}')
        else:
            user.is_active = False
            user.save()
            messages.success(request, f'تم تعطيل حساب الموظف {_employee_name(employee)}')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تحديث حالة الحساب: {e}')

    return _redirect_employee_detail_or_list(employee)


@login_required
@feature_required('employees_management')
def reset_password_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if not (can_user_edit_employee(request.user, employee) or is_admin_or_hr(request.user)):
        raise PermissionDenied('ليس لديك صلاحية إعادة تعيين كلمة مرور هذا الموظف')

    user = getattr(employee, 'user', None)
    if not user:
        messages.warning(request, 'هذا الموظف لا يملك حساب مستخدم مرتبطًا به. أنشئ الحساب أولاً.')
        return _redirect_employee_detail_or_list(employee)

    try:
        base_code = (employee.employee_code or 'EMP').replace(' ', '')
        temp_password = f"{base_code}@{get_random_string(4)}"

        user.set_password(temp_password)

        if hasattr(user, 'must_change_password'):
            try:
                user.must_change_password = True
            except Exception:
                pass

        if hasattr(user, 'is_active') and not user.is_active:
            user.is_active = True

        user.save()

        messages.success(
            request,
            f'تم إعادة تعيين كلمة المرور للموظف {_employee_name(employee)} | '
            f'اسم المستخدم: {getattr(user, "username", "—")} | '
            f'كلمة المرور المؤقتة: {temp_password}'
        )
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إعادة تعيين كلمة المرور: {e}')

    return _redirect_employee_detail_or_list(employee)


# ═════════════════════════════════════════════════════════════
# Self Service
# ═════════════════════════════════════════════════════════════

@login_required
def my_balance(request):
    try:
        employee = Employee.objects.select_related('branch', 'department', 'job_title').get(user=request.user)
    except Employee.DoesNotExist:
        messages.warning(request, 'لا يوجد ملف موظف مرتبط بهذا الحساب')
        return redirect('dashboard')

    try:
        from leaves.models import LeaveBalance
        balances = LeaveBalance.objects.filter(employee=employee).select_related('leave_type')
    except Exception:
        balances = []

    return render(request, 'employees/my_balance.html', {
        'employee': employee,
        'balances': balances,
        'page_title': 'رصيد إجازاتي',
    })


@login_required
def my_deductions(request):
    try:
        employee = Employee.objects.select_related('branch', 'department', 'job_title').get(user=request.user)
    except Employee.DoesNotExist:
        messages.warning(request, 'لا يوجد ملف موظف مرتبط بهذا الحساب')
        return redirect('dashboard')

    deductions = Deduction.objects.filter(employee=employee).order_by('-date', '-id')

    return render(request, 'employees/my_deductions.html', {
        'employee': employee,
        'deductions': deductions,
        'page_title': 'خصوماتي',
    })


# ═════════════════════════════════════════════════════════════
# Compatibility Aliases
# ═════════════════════════════════════════════════════════════

employee_print = employee_print_list
print_credentials_view = print_credentials
my_balance_view = my_balance
my_deductions_view = my_deductions

employee_create = employee_add
create_employee = employee_add
add_employee = employee_add
add = employee_add

employee_update = employee_edit
update_employee = employee_edit
edit_employee = employee_edit
edit = employee_edit

employee_remove = employee_delete
delete_employee = employee_delete
remove_employee = employee_delete
delete = employee_delete

detail = employee_detail
employee_profile = employee_detail
employee_info = employee_detail

employee_print_all = employee_print_list
employees_print = employee_print_list
employees_print_all = employee_print_list
print_all = employee_print_list
print_list = employee_print_list
print_list_view = employee_print_list

employee_detail_print = employee_print_detail
employee_profile_print = employee_print_detail
employees_print_detail = employee_print_detail
print_detail = employee_print_detail
print_detail_view = employee_print_detail

employee_print_credentials = print_credentials
employee_credentials_print = print_credentials
credentials_print = print_credentials
employee_credentials = print_credentials

create_account = create_account_view
employee_create_account = create_account_view
employee_account_create = create_account_view
create_employee_account = create_account_view

employee_deactivate_account = deactivate_account_view
employee_reset_password = reset_password_view
employee_balance = my_balance
employee_balance_view = my_balance
employee_deductions = my_deductions
employee_deductions_view = my_deductions
employee_search = employee_search_api
search_api = employee_search_api
manager_options_api = employee_manager_options_api
'''
write_file("employees/views.py", views_code)

# ─────────────────────────────────────────────────────────────
# Step 6: Write hierarchy management template
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 6: إنشاء شاشة إدارة الهيكل الوظيفي")

hierarchy_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}إدارة الهيكل الوظيفي{% endblock %}

{% block extra_css %}
<style>
  .info-box {
    border: 1px solid #bae6fd;
    background: #f0f9ff;
    border-radius: 16px;
    padding: 16px;
  }
  .soft-card {
    border: 1px solid #e2e8f0;
    border-radius: 18px;
  }
  .soft-card .card-header {
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
    border-radius: 18px 18px 0 0 !important;
  }
  .mini-note {
    color: #64748b;
    font-size: .82rem;
  }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold">
        <i class="bi bi-diagram-3-fill text-primary me-2"></i>إدارة الهيكل الوظيفي
      </h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item"><a href="{% url 'employees:list' %}">الموظفون</a></li>
          <li class="breadcrumb-item active">الهيكل الوظيفي</li>
        </ol>
      </nav>
    </div>
    <div>
      <a href="{% url 'employees:add' %}" class="btn btn-primary">
        <i class="bi bi-person-plus me-1"></i>إضافة موظف
      </a>
    </div>
  </div>

  <div class="info-box mb-4">
    <div class="fw-bold mb-2">
      <i class="bi bi-lightbulb-fill text-warning me-1"></i>كيف تستخدم الشاشة؟
    </div>
    <div class="small text-muted">
      1) أضف المستويات الوظيفية أو عدّلها حسب هيكل الشركة.<br>
      2) اربط كل <strong>إدارة</strong> مع <strong>مسمى وظيفي</strong> وحدد له <strong>مستوى</strong> و<strong>المسمى الأعلى المباشر</strong>.<br>
      3) بعد ذلك عند إضافة موظف، النظام سيقترح المدير المباشر المناسب تلقائيًا حسب هذه القواعد.
    </div>
  </div>

  <div class="row g-4">
    <!-- Add Level -->
    <div class="col-lg-4">
      <div class="card soft-card border-0 shadow-sm">
        <div class="card-header py-3">
          <h6 class="mb-0 fw-bold"><i class="bi bi-layers me-2 text-primary"></i>إضافة مستوى وظيفي</h6>
        </div>
        <div class="card-body">
          <form method="post">
            {% csrf_token %}
            <input type="hidden" name="action" value="add_level">

            <div class="mb-3">
              <label class="form-label fw-semibold">الاسم بالعربي <span class="text-danger">*</span></label>
              <input type="text" name="name_ar" class="form-control" required placeholder="مثال: مدير">
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">الاسم بالإنجليزي</label>
              <input type="text" name="name_en" class="form-control" placeholder="Manager">
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">الترتيب الهرمي <span class="text-danger">*</span></label>
              <input type="number" name="sort_order" class="form-control" required min="1" placeholder="1 = أعلى">
              <div class="mini-note mt-1">كلما كان الرقم أقل كان المستوى أعلى.</div>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">الوصف</label>
              <textarea name="description" class="form-control" rows="2"></textarea>
            </div>

            <div class="form-check mb-3">
              <input class="form-check-input" type="checkbox" name="is_active" id="levelActive" checked>
              <label class="form-check-label" for="levelActive">مستوى نشط</label>
            </div>

            <button type="submit" class="btn btn-primary w-100">
              <i class="bi bi-plus-circle me-1"></i>إضافة المستوى
            </button>
          </form>
        </div>
      </div>

      <div class="card soft-card border-0 shadow-sm mt-4">
        <div class="card-header py-3">
          <h6 class="mb-0 fw-bold"><i class="bi bi-list-ol me-2 text-primary"></i>المستويات الحالية</h6>
        </div>
        <div class="card-body p-0">
          {% if levels %}
          <div class="table-responsive">
            <table class="table align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>ترتيب</th>
                  <th>الاسم</th>
                  <th>حالة</th>
                  <th>إجراء</th>
                </tr>
              </thead>
              <tbody>
                {% for level in levels %}
                <tr>
                  <td>{{ level.sort_order }}</td>
                  <td>{{ level.name_ar }}</td>
                  <td>
                    {% if level.is_active %}
                      <span class="badge bg-success-subtle text-success border border-success-subtle">نشط</span>
                    {% else %}
                      <span class="badge bg-secondary-subtle text-secondary">غير نشط</span>
                    {% endif %}
                  </td>
                  <td>
                    <form method="post" onsubmit="return confirm('حذف المستوى؟');">
                      {% csrf_token %}
                      <input type="hidden" name="action" value="delete_level">
                      <input type="hidden" name="level_id" value="{{ level.id }}">
                      <button type="submit" class="btn btn-sm btn-outline-danger">
                        <i class="bi bi-trash"></i>
                      </button>
                    </form>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="p-4 text-center text-muted">لا توجد مستويات بعد</div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- Rules -->
    <div class="col-lg-8">
      <div class="card soft-card border-0 shadow-sm">
        <div class="card-header py-3">
          <h6 class="mb-0 fw-bold"><i class="bi bi-bezier2 me-2 text-primary"></i>ربط الإدارة بالمستوى والمسمى الوظيفي</h6>
        </div>
        <div class="card-body">
          <form method="post">
            {% csrf_token %}
            <input type="hidden" name="action" value="save_rule">

            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label fw-semibold">الإدارة <span class="text-danger">*</span></label>
                <select name="department_id" class="form-select" required>
                  <option value="">اختر الإدارة</option>
                  {% for dept in departments %}
                    <option value="{{ dept.id }}">{{ dept.name_ar|default:dept.name_en }}</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold">المسمى الوظيفي <span class="text-danger">*</span></label>
                <select name="job_title_id" class="form-select" required>
                  <option value="">اختر المسمى الوظيفي</option>
                  {% for jt in job_titles %}
                    <option value="{{ jt.id }}">{{ jt.name_ar|default:jt.name_en }}</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-4">
                <label class="form-label fw-semibold">المستوى الوظيفي <span class="text-danger">*</span></label>
                <select name="level_id" class="form-select" required>
                  <option value="">اختر المستوى</option>
                  {% for level in levels %}
                    <option value="{{ level.id }}">{{ level.sort_order }} - {{ level.name_ar }}</option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-md-8">
                <label class="form-label fw-semibold">المسمى الأعلى المباشر</label>
                <select name="parent_job_title_id" class="form-select">
                  <option value="">بدون / يعتمد على بديل أعلى</option>
                  {% for jt in job_titles %}
                    <option value="{{ jt.id }}">{{ jt.name_ar|default:jt.name_en }}</option>
                  {% endfor %}
                </select>
                <div class="mini-note mt-1">مثال: موظف → مشرف، مشرف → مدير، مدير → مدير عام</div>
              </div>

              <div class="col-md-4">
                <div class="form-check mt-4">
                  <input class="form-check-input" type="checkbox" name="same_department_only" id="sameDepartmentOnly" checked>
                  <label class="form-check-label" for="sameDepartmentOnly">
                    المدير من نفس الإدارة فقط
                  </label>
                </div>
              </div>

              <div class="col-md-4">
                <div class="form-check mt-4">
                  <input class="form-check-input" type="checkbox" name="allow_higher_parent_fallback" id="allowFallback" checked>
                  <label class="form-check-label" for="allowFallback">
                    السماح ببديل أعلى
                  </label>
                </div>
              </div>

              <div class="col-md-4">
                <div class="form-check mt-4">
                  <input class="form-check-input" type="checkbox" name="rule_is_active" id="ruleActive" checked>
                  <label class="form-check-label" for="ruleActive">
                    قاعدة نشطة
                  </label>
                </div>
              </div>

              <div class="col-md-12">
                <label class="form-label fw-semibold">ملاحظات</label>
                <textarea name="notes" class="form-control" rows="2"></textarea>
              </div>
            </div>

            <div class="d-flex justify-content-end mt-3">
              <button type="submit" class="btn btn-primary">
                <i class="bi bi-save me-1"></i>حفظ قاعدة الربط
              </button>
            </div>
          </form>
        </div>
      </div>

      <div class="card soft-card border-0 shadow-sm mt-4">
        <div class="card-header py-3 d-flex justify-content-between align-items-center">
          <h6 class="mb-0 fw-bold"><i class="bi bi-diagram-2 me-2 text-primary"></i>قواعد الربط الحالية</h6>
          <span class="badge bg-secondary">{{ rules|length }} قاعدة</span>
        </div>
        <div class="card-body p-0">
          {% if rules %}
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>الإدارة</th>
                  <th>المسمى</th>
                  <th>المستوى</th>
                  <th>المسمى الأعلى المباشر</th>
                  <th>نفس الإدارة</th>
                  <th>بديل أعلى</th>
                  <th>الحالة</th>
                  <th>إجراء</th>
                </tr>
              </thead>
              <tbody>
                {% for rule in rules %}
                <tr>
                  <td>{{ rule.department.name_ar|default:rule.department.name_en }}</td>
                  <td>{{ rule.job_title.name_ar|default:rule.job_title.name_en }}</td>
                  <td>{{ rule.level.sort_order }} - {{ rule.level.name_ar }}</td>
                  <td>{{ rule.parent_job_title.name_ar|default:rule.parent_job_title.name_en|default:"—" }}</td>
                  <td>
                    {% if rule.same_department_only %}
                      <span class="badge bg-info-subtle text-info border border-info-subtle">نعم</span>
                    {% else %}
                      <span class="badge bg-secondary-subtle text-secondary">لا</span>
                    {% endif %}
                  </td>
                  <td>
                    {% if rule.allow_higher_parent_fallback %}
                      <span class="badge bg-success-subtle text-success border border-success-subtle">مسموح</span>
                    {% else %}
                      <span class="badge bg-secondary-subtle text-secondary">غير مسموح</span>
                    {% endif %}
                  </td>
                  <td>
                    {% if rule.is_active %}
                      <span class="badge bg-success-subtle text-success border border-success-subtle">نشطة</span>
                    {% else %}
                      <span class="badge bg-secondary-subtle text-secondary">معطلة</span>
                    {% endif %}
                  </td>
                  <td>
                    <form method="post" onsubmit="return confirm('حذف قاعدة الربط؟');">
                      {% csrf_token %}
                      <input type="hidden" name="action" value="delete_rule">
                      <input type="hidden" name="rule_id" value="{{ rule.id }}">
                      <button type="submit" class="btn btn-sm btn-outline-danger">
                        <i class="bi bi-trash"></i>
                      </button>
                    </form>
                  </td>
                </tr>
                {% if rule.notes %}
                <tr class="table-light">
                  <td colspan="8" class="small text-muted">
                    <strong>ملاحظات:</strong> {{ rule.notes }}
                  </td>
                </tr>
                {% endif %}
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="p-4 text-center text-muted">
            لا توجد قواعد ربط بعد — ابدأ بتعريف أول قاعدة
          </div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>

</div>
{% endblock %}
"""
write_file("templates/employees/job_hierarchy_manage.html", hierarchy_template)

# ─────────────────────────────────────────────────────────────
# Step 7: Rewrite employee form with wizard + hierarchy-aware manager loading
# ─────────────────────────────────────────────────────────────
print("\n📌 Step 7: تحديث templates/employees/form.html")

form_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}{{ page_title|default:"إضافة موظف" }}{% endblock %}

{% block extra_css %}
<style>
  .wizard-shell { border: 1px solid #e2e8f0; border-radius: 20px; background: linear-gradient(180deg, #ffffff 0%, #f8fdff 100%); }
  .wizard-stepper { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
  .wizard-step { border: 1px solid #dbeafe; background: #fff; border-radius: 16px; padding: 14px 12px; cursor: pointer; transition: .2s ease; min-height: 88px; }
  .wizard-step:hover { border-color: #06B6D4; transform: translateY(-1px); }
  .wizard-step.active { background: #06B6D4; border-color: #06B6D4; color: white; box-shadow: 0 10px 24px rgba(6,182,212,.18); }
  .wizard-step.done { background: #ecfeff; border-color: #67e8f9; }
  .wizard-step-number { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; background: rgba(6,182,212,.12); color: #0891b2; margin-bottom: 10px; }
  .wizard-step.active .wizard-step-number { background: rgba(255,255,255,.18); color: #fff; }
  .wizard-step-title { font-weight: 800; font-size: .95rem; margin-bottom: 3px; }
  .wizard-step-note { font-size: .78rem; opacity: .85; }
  .wizard-panel { display: none; }
  .wizard-panel.active { display: block; animation: fadePanel .18s ease; }
  @keyframes fadePanel { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
  .section-card { border: 1px solid #e2e8f0; border-radius: 18px; overflow: hidden; }
  .section-head { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 14px 18px; }
  .section-head h6 { margin: 0; font-weight: 800; }
  .section-head small { color: #64748b; }
  .field-box { margin-bottom: 1rem; }
  .field-box label { display: block; margin-bottom: .45rem; font-weight: 700; color: #0f172a; }
  .field-box .required-star { color: #dc2626; margin-right: 4px; }
  .field-box .errorlist { list-style: none; padding: 0; margin: .35rem 0 0; color: #dc2626; font-size: .82rem; }
  .wizard-actions { position: sticky; bottom: 0; background: #fff; border-top: 1px solid #e2e8f0; padding: 16px 0 0; margin-top: 24px; }
  .wizard-status { border: 1px dashed #cbd5e1; background: #f8fafc; border-radius: 14px; padding: 12px 14px; }
  .wizard-status .status-title { font-weight: 800; margin-bottom: 6px; }
  .missing-list { margin: 0; padding-right: 18px; }
  .missing-list li { margin-bottom: 4px; }
  .field-invalid { border-color: #dc2626 !important; box-shadow: 0 0 0 .2rem rgba(220,38,38,.08) !important; }
  .form-check-wrap { border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; background: #fff; }
  .mini-note { color: #64748b; font-size: .8rem; }
  .hierarchy-note { border: 1px solid #bae6fd; background: #f0f9ff; border-radius: 14px; padding: 12px 14px; color: #0c4a6e; font-size: .88rem; }
  .hierarchy-note strong { color: #075985; }
  @media (max-width: 991.98px) { .wizard-stepper { grid-template-columns: 1fr; } }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold">
        <i class="bi bi-person-plus-fill text-primary me-2"></i>{{ form_title|default:"إضافة موظف جديد" }}
      </h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item"><a href="{% url 'employees:list' %}">الموظفون</a></li>
          <li class="breadcrumb-item active">{{ form_title|default:"إضافة موظف جديد" }}</li>
        </ol>
      </nav>
    </div>
    <div class="d-flex gap-2">
      <a href="{% url 'employees:hierarchy_manage' %}" class="btn btn-outline-primary">
        <i class="bi bi-diagram-3 me-1"></i>إدارة الهيكل الوظيفي
      </a>
      <a href="{% url 'employees:list' %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-right-circle me-1"></i>العودة للقائمة
      </a>
    </div>
  </div>

  {% if form.errors %}
  <div class="alert alert-danger border-0 shadow-sm">
    <div class="fw-bold mb-2">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>يوجد حقول مطلوبة أو بيانات غير صحيحة:
    </div>
    <ul class="mb-0">
      {% for field in form %}
        {% for error in field.errors %}
          <li><strong>{{ field.label }}:</strong> {{ error }}</li>
        {% endfor %}
      {% endfor %}
      {% for error in form.non_field_errors %}
        <li>{{ error }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  <div class="card border-0 shadow-sm wizard-shell">
    <div class="card-body p-4">

      <div class="wizard-stepper mb-4" id="wizard-stepper">
        <div class="wizard-step active" data-step="1">
          <div class="wizard-step-number">1</div>
          <div class="wizard-step-title">البيانات الأساسية</div>
          <div class="wizard-step-note">الاسم والهوية والبيانات الشخصية</div>
        </div>
        <div class="wizard-step" data-step="2">
          <div class="wizard-step-number">2</div>
          <div class="wizard-step-title">التواصل</div>
          <div class="wizard-step-note">الهاتف والعنوان والطوارئ</div>
        </div>
        <div class="wizard-step" data-step="3">
          <div class="wizard-step-number">3</div>
          <div class="wizard-step-title">بيانات التعيين</div>
          <div class="wizard-step-note">الإدارة والمسمى والمدير المباشر</div>
        </div>
        <div class="wizard-step" data-step="4">
          <div class="wizard-step-number">4</div>
          <div class="wizard-step-title">المالية والتأمين</div>
          <div class="wizard-step-note">الراتب والبنك والتأمين</div>
        </div>
        <div class="wizard-step" data-step="5">
          <div class="wizard-step-number">5</div>
          <div class="wizard-step-title">الحضور والتتبع</div>
          <div class="wizard-step-note">الحضور والتتبع والموظف الميداني</div>
        </div>
      </div>

      <div class="wizard-status mb-4" id="wizard-status-box">
        <div class="status-title">
          <i class="bi bi-info-circle-fill text-primary me-1"></i>
          الخطوة الحالية: <span id="current-step-title">البيانات الأساسية</span>
        </div>
        <div class="mini-note">
          لا يمكن الانتقال للخطوة التالية إلا بعد استكمال الحقول الإلزامية في الخطوة الحالية.
        </div>
        <div id="missing-fields-box" class="mt-2" style="display:none;">
          <div class="fw-bold text-danger mb-1">الحقول الناقصة:</div>
          <ul class="missing-list text-danger" id="missing-fields-list"></ul>
        </div>
      </div>

      <form method="post" enctype="multipart/form-data" id="employeeWizardForm" novalidate>
        {% csrf_token %}
        {% for hidden in form.hidden_fields %}{{ hidden }}{% endfor %}

        <!-- STEP 1 -->
        <div class="wizard-panel active" data-step-panel="1">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-person-vcard me-2 text-primary"></i>البيانات الأساسية</h6>
              <small>أدخل هوية الموظف الأساسية والبيانات الشخصية</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.employee_code %}<div class="col-md-4 field-box">{{ form.employee_code.label_tag }}{{ form.employee_code }}{{ form.employee_code.errors }}</div>{% endif %}
                {% if form.first_name_ar %}<div class="col-md-4 field-box">{{ form.first_name_ar.label_tag }}{{ form.first_name_ar }}{{ form.first_name_ar.errors }}</div>{% endif %}
                {% if form.middle_name_ar %}<div class="col-md-4 field-box">{{ form.middle_name_ar.label_tag }}{{ form.middle_name_ar }}{{ form.middle_name_ar.errors }}</div>{% endif %}
                {% if form.last_name_ar %}<div class="col-md-4 field-box">{{ form.last_name_ar.label_tag }}{{ form.last_name_ar }}{{ form.last_name_ar.errors }}</div>{% endif %}
                {% if form.first_name_en %}<div class="col-md-4 field-box">{{ form.first_name_en.label_tag }}{{ form.first_name_en }}{{ form.first_name_en.errors }}</div>{% endif %}
                {% if form.last_name_en %}<div class="col-md-4 field-box">{{ form.last_name_en.label_tag }}{{ form.last_name_en }}{{ form.last_name_en.errors }}</div>{% endif %}
                {% if form.national_id %}<div class="col-md-4 field-box">{{ form.national_id.label_tag }}{{ form.national_id }}{{ form.national_id.errors }}</div>{% endif %}
                {% if form.birth_date %}<div class="col-md-4 field-box">{{ form.birth_date.label_tag }}{{ form.birth_date }}{{ form.birth_date.errors }}</div>{% endif %}
                {% if form.gender %}<div class="col-md-4 field-box">{{ form.gender.label_tag }}{{ form.gender }}{{ form.gender.errors }}</div>{% endif %}
                {% if form.marital_status %}<div class="col-md-4 field-box">{{ form.marital_status.label_tag }}{{ form.marital_status }}{{ form.marital_status.errors }}</div>{% endif %}
                {% if form.religion %}<div class="col-md-4 field-box">{{ form.religion.label_tag }}{{ form.religion }}{{ form.religion.errors }}</div>{% endif %}
                {% if form.nationality %}<div class="col-md-4 field-box">{{ form.nationality.label_tag }}{{ form.nationality }}{{ form.nationality.errors }}</div>{% endif %}
                {% if form.photo %}<div class="col-md-6 field-box">{{ form.photo.label_tag }}{{ form.photo }}{{ form.photo.errors }}</div>{% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 2 -->
        <div class="wizard-panel" data-step-panel="2">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-telephone-forward me-2 text-primary"></i>بيانات التواصل والطوارئ</h6>
              <small>بيانات الاتصال الأساسية ووسيلة التواصل في الحالات الطارئة</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.email %}<div class="col-md-4 field-box">{{ form.email.label_tag }}{{ form.email }}{{ form.email.errors }}</div>{% endif %}
                {% if form.phone %}<div class="col-md-4 field-box">{{ form.phone.label_tag }}{{ form.phone }}{{ form.phone.errors }}</div>{% endif %}
                {% if form.phone2 %}<div class="col-md-4 field-box">{{ form.phone2.label_tag }}{{ form.phone2 }}{{ form.phone2.errors }}</div>{% endif %}
                {% if form.city %}<div class="col-md-4 field-box">{{ form.city.label_tag }}{{ form.city }}{{ form.city.errors }}</div>{% endif %}
                {% if form.address %}<div class="col-md-8 field-box">{{ form.address.label_tag }}{{ form.address }}{{ form.address.errors }}</div>{% endif %}
                {% if form.emergency_contact_name %}<div class="col-md-4 field-box">{{ form.emergency_contact_name.label_tag }}{{ form.emergency_contact_name }}{{ form.emergency_contact_name.errors }}</div>{% endif %}
                {% if form.emergency_contact_relation %}<div class="col-md-4 field-box">{{ form.emergency_contact_relation.label_tag }}{{ form.emergency_contact_relation }}{{ form.emergency_contact_relation.errors }}</div>{% endif %}
                {% if form.emergency_contact_phone %}<div class="col-md-4 field-box">{{ form.emergency_contact_phone.label_tag }}{{ form.emergency_contact_phone }}{{ form.emergency_contact_phone.errors }}</div>{% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 3 -->
        <div class="wizard-panel" data-step-panel="3">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-briefcase-fill me-2 text-primary"></i>بيانات التعيين</h6>
              <small>الإدارة والمسمى الوظيفي والمدير المباشر</small>
            </div>
            <div class="p-4">
              <div class="hierarchy-note mb-3" id="managerHierarchyNote">
                <strong>المنطق الحالي:</strong>
                اختر الإدارة + المسمى الوظيفي أولًا، وسيظهر لك فقط المديرون الأعلى المناسبون حسب القواعد المعرفة في شاشة الهيكل الوظيفي.
              </div>

              <div class="row">
                {% if form.hire_date %}<div class="col-md-4 field-box">{{ form.hire_date.label_tag }}{{ form.hire_date }}{{ form.hire_date.errors }}</div>{% endif %}
                {% if form.contract_type %}<div class="col-md-4 field-box">{{ form.contract_type.label_tag }}{{ form.contract_type }}{{ form.contract_type.errors }}</div>{% endif %}
                {% if form.contract_end_date %}<div class="col-md-4 field-box">{{ form.contract_end_date.label_tag }}{{ form.contract_end_date }}{{ form.contract_end_date.errors }}</div>{% endif %}
                {% if form.branch %}<div class="col-md-4 field-box">{{ form.branch.label_tag }}{{ form.branch }}{{ form.branch.errors }}</div>{% endif %}
                {% if form.department %}<div class="col-md-4 field-box">{{ form.department.label_tag }}{{ form.department }}{{ form.department.errors }}</div>{% endif %}
                {% if form.job_title %}<div class="col-md-4 field-box">{{ form.job_title.label_tag }}{{ form.job_title }}{{ form.job_title.errors }}</div>{% endif %}
                {% if form.direct_manager %}<div class="col-md-6 field-box">{{ form.direct_manager.label_tag }}{{ form.direct_manager }}{{ form.direct_manager.errors }}</div>{% endif %}
                {% if form.status %}<div class="col-md-3 field-box">{{ form.status.label_tag }}{{ form.status }}{{ form.status.errors }}</div>{% endif %}
                {% if form.termination_date %}<div class="col-md-3 field-box">{{ form.termination_date.label_tag }}{{ form.termination_date }}{{ form.termination_date.errors }}</div>{% endif %}
                {% if form.termination_reason %}<div class="col-md-12 field-box">{{ form.termination_reason.label_tag }}{{ form.termination_reason }}{{ form.termination_reason.errors }}</div>{% endif %}
                {% if form.notes %}<div class="col-md-12 field-box">{{ form.notes.label_tag }}{{ form.notes }}{{ form.notes.errors }}</div>{% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 4 -->
        <div class="wizard-panel" data-step-panel="4">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-cash-coin me-2 text-primary"></i>البيانات المالية والتأمين</h6>
              <small>الراتب وبيانات البنك والتأمينات</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.basic_salary %}<div class="col-md-4 field-box">{{ form.basic_salary.label_tag }}{{ form.basic_salary }}{{ form.basic_salary.errors }}</div>{% endif %}
                {% if form.bank_name %}<div class="col-md-4 field-box">{{ form.bank_name.label_tag }}{{ form.bank_name }}{{ form.bank_name.errors }}</div>{% endif %}
                {% if form.bank_account %}<div class="col-md-4 field-box">{{ form.bank_account.label_tag }}{{ form.bank_account }}{{ form.bank_account.errors }}</div>{% endif %}
                {% if form.iban %}<div class="col-md-4 field-box">{{ form.iban.label_tag }}{{ form.iban }}{{ form.iban.errors }}</div>{% endif %}
                {% if form.insurance_number %}<div class="col-md-4 field-box">{{ form.insurance_number.label_tag }}{{ form.insurance_number }}{{ form.insurance_number.errors }}</div>{% endif %}
                {% if form.insurance_date %}<div class="col-md-4 field-box">{{ form.insurance_date.label_tag }}{{ form.insurance_date }}{{ form.insurance_date.errors }}</div>{% endif %}
                {% if form.has_insurance %}
                <div class="col-md-12 field-box">
                  <label>{{ form.has_insurance.label }}</label>
                  <div class="form-check-wrap">
                    <div class="form-check">
                      {{ form.has_insurance }}
                      <label class="form-check-label ms-2" for="{{ form.has_insurance.id_for_label }}">الموظف مشترك في التأمينات</label>
                    </div>
                  </div>
                  {{ form.has_insurance.errors }}
                </div>
                {% endif %}
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 5 -->
        <div class="wizard-panel" data-step-panel="5">
          <div class="section-card">
            <div class="section-head">
              <h6><i class="bi bi-fingerprint me-2 text-primary"></i>الحضور والتتبع</h6>
              <small>إعدادات الحضور ونمط العمل والتتبع</small>
            </div>
            <div class="p-4">
              <div class="row">
                {% if form.attendance_mode %}<div class="col-md-4 field-box">{{ form.attendance_mode.label_tag }}{{ form.attendance_mode }}{{ form.attendance_mode.errors }}</div>{% endif %}
                {% if form.required_daily_hours %}<div class="col-md-4 field-box">{{ form.required_daily_hours.label_tag }}{{ form.required_daily_hours }}{{ form.required_daily_hours.errors }}</div>{% endif %}
                {% if form.stealth_tracking_enabled %}
                <div class="col-md-6 field-box">
                  <label>{{ form.stealth_tracking_enabled.label }}</label>
                  <div class="form-check-wrap">
                    <div class="form-check">
                      {{ form.stealth_tracking_enabled }}
                      <label class="form-check-label ms-2" for="{{ form.stealth_tracking_enabled.id_for_label }}">تفعيل التتبع الصامت لهذا الموظف</label>
                    </div>
                  </div>
                  {{ form.stealth_tracking_enabled.errors }}
                </div>
                {% endif %}
                {% if form.is_field_worker %}
                <div class="col-md-6 field-box">
                  <label>{{ form.is_field_worker.label }}</label>
                  <div class="form-check-wrap">
                    <div class="form-check">
                      {{ form.is_field_worker }}
                      <label class="form-check-label ms-2" for="{{ form.is_field_worker.id_for_label }}">موظف ميداني</label>
                    </div>
                  </div>
                  {{ form.is_field_worker.errors }}
                </div>
                {% endif %}
              </div>
            </div>
          </div>
        </div>

        <div class="wizard-actions">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div class="mini-note">
              <i class="bi bi-lightbulb me-1 text-warning"></i>
              النظام سيمنعك من الانتقال لو الحقول الإلزامية في الخطوة الحالية غير مكتملة.
            </div>
            <div class="d-flex gap-2">
              <button type="button" class="btn btn-outline-secondary" id="prevStepBtn">
                <i class="bi bi-arrow-right me-1"></i>السابق
              </button>
              <button type="button" class="btn btn-primary" id="nextStepBtn">
                التالي<i class="bi bi-arrow-left ms-1"></i>
              </button>
              <button type="submit" class="btn btn-success" id="submitFormBtn" style="display:none;">
                <i class="bi bi-check2-circle me-1"></i>حفظ الموظف
              </button>
            </div>
          </div>
        </div>

      </form>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_js %}
<script>
(function() {
  const form = document.getElementById('employeeWizardForm');
  const stepButtons = Array.from(document.querySelectorAll('.wizard-step'));
  const panels = Array.from(document.querySelectorAll('.wizard-panel'));
  const prevBtn = document.getElementById('prevStepBtn');
  const nextBtn = document.getElementById('nextStepBtn');
  const submitBtn = document.getElementById('submitFormBtn');
  const currentStepTitle = document.getElementById('current-step-title');
  const missingBox = document.getElementById('missing-fields-box');
  const missingList = document.getElementById('missing-fields-list');

  let currentStep = 1;

  const stepMeta = {
    1: 'البيانات الأساسية',
    2: 'التواصل',
    3: 'بيانات التعيين',
    4: 'المالية والتأمين',
    5: 'الحضور والتتبع'
  };

  function bootstrapizeFields() {
    document.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.type === 'hidden') return;
      if (el.type === 'checkbox') {
        el.classList.add('form-check-input');
        return;
      }
      if (el.tagName === 'SELECT') {
        el.classList.add('form-select');
      } else {
        el.classList.add('form-control');
      }
    });

    document.querySelectorAll('.field-box label').forEach(label => {
      const box = label.closest('.field-box');
      if (!box) return;
      const input = box.querySelector('input, select, textarea');
      if (!input) return;

      if (input.required && !label.querySelector('.required-star')) {
        const star = document.createElement('span');
        star.className = 'required-star';
        star.textContent = '*';
        label.appendChild(star);
      }
    });
  }

  function getPanel(step) {
    return document.querySelector('.wizard-panel[data-step-panel="' + step + '"]');
  }

  function getVisibleRequiredInputs(step) {
    const panel = getPanel(step);
    if (!panel) return [];
    return Array.from(panel.querySelectorAll('input, select, textarea')).filter(el => {
      if (el.disabled) return false;
      if (el.type === 'hidden') return false;
      if (!el.required) return false;
      if (el.offsetParent === null) return false;
      return true;
    });
  }

  function clearInvalid(step) {
    const panel = getPanel(step);
    if (!panel) return;
    panel.querySelectorAll('.field-invalid').forEach(el => el.classList.remove('field-invalid'));
  }

  function getLabelText(input) {
    const box = input.closest('.field-box');
    if (box) {
      const label = box.querySelector('label');
      if (label) return label.textContent.replace('*', '').trim();
    }
    return input.getAttribute('placeholder') || input.name || 'حقل مطلوب';
  }

  function validateStep(step, focusFirst=true) {
    clearInvalid(step);
    const requiredInputs = getVisibleRequiredInputs(step);
    const missing = [];
    let firstInvalid = null;

    requiredInputs.forEach(input => {
      let valid = true;

      if (input.type === 'checkbox') {
        valid = input.checked;
      } else if (input.tagName === 'SELECT') {
        valid = !!String(input.value || '').trim();
      } else {
        valid = input.checkValidity() && !!String(input.value || '').trim();
      }

      if (!valid) {
        input.classList.add('field-invalid');
        const label = getLabelText(input);
        if (!missing.includes(label)) missing.push(label);
        if (!firstInvalid) firstInvalid = input;
      }
    });

    if (missing.length) {
      missingBox.style.display = 'block';
      missingList.innerHTML = missing.map(item => '<li>' + item + '</li>').join('');
      if (focusFirst && firstInvalid) firstInvalid.focus();
      return false;
    }

    missingBox.style.display = 'none';
    missingList.innerHTML = '';
    return true;
  }

  function updateStepper() {
    stepButtons.forEach(btn => {
      const step = parseInt(btn.dataset.step, 10);
      btn.classList.remove('active', 'done');
      if (step === currentStep) btn.classList.add('active');
      else if (step < currentStep) btn.classList.add('done');
    });

    panels.forEach(panel => {
      const step = parseInt(panel.dataset.stepPanel, 10);
      panel.classList.toggle('active', step === currentStep);
    });

    currentStepTitle.textContent = stepMeta[currentStep] || 'الخطوة الحالية';
    prevBtn.style.visibility = currentStep === 1 ? 'hidden' : 'visible';
    nextBtn.style.display = currentStep === panels.length ? 'none' : 'inline-block';
    submitBtn.style.display = currentStep === panels.length ? 'inline-block' : 'none';
  }

  function goToStep(step) {
    if (step < 1 || step > panels.length) return;
    currentStep = step;
    updateStepper();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  prevBtn.addEventListener('click', function() {
    if (currentStep > 1) {
      missingBox.style.display = 'none';
      goToStep(currentStep - 1);
    }
  });

  nextBtn.addEventListener('click', function() {
    if (validateStep(currentStep)) goToStep(currentStep + 1);
  });

  stepButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      const target = parseInt(btn.dataset.step, 10);
      if (target < currentStep) {
        missingBox.style.display = 'none';
        goToStep(target);
        return;
      }
      if (target === currentStep) return;
      if (validateStep(currentStep)) goToStep(target);
    });
  });

  form.addEventListener('submit', function(e) {
    for (let step = 1; step <= panels.length; step++) {
      const ok = validateStep(step, false);
      if (!ok) {
        e.preventDefault();
        goToStep(step);
        validateStep(step, true);
        return;
      }
    }
  });

  bootstrapizeFields();
  updateStepper();
})();
</script>

<script>
(function() {
  const departmentSelect = document.querySelector('[name="department"]');
  const jobTitleSelect = document.querySelector('[name="job_title"]');
  const directManagerSelect = document.querySelector('[name="direct_manager"]');
  const noteBox = document.getElementById('managerHierarchyNote');
  const employeeId = "{{ employee.id|default:'' }}";

  if (!departmentSelect || !jobTitleSelect || !directManagerSelect) return;

  directManagerSelect.dataset.originalRequired = directManagerSelect.required ? '1' : '0';

  function setNote(html) {
    if (noteBox) noteBox.innerHTML = html;
  }

  function disableManagerSelect(placeholderText) {
    directManagerSelect.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = placeholderText || 'اختر الإدارة والمسمى الوظيفي أولًا';
    directManagerSelect.appendChild(opt);
    directManagerSelect.disabled = true;
    directManagerSelect.required = false;
    directManagerSelect.value = '';
  }

  function enableManagerSelect() {
    directManagerSelect.disabled = false;
    if (directManagerSelect.dataset.originalRequired === '1') {
      directManagerSelect.required = true;
    }
  }

  function renderManagers(items, keepValue) {
    directManagerSelect.innerHTML = '';
    const first = document.createElement('option');
    first.value = '';
    first.textContent = 'اختر المدير المباشر';
    directManagerSelect.appendChild(first);

    items.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = `${item.name} — ${item.job_title} — ${item.department}`;
      if (String(keepValue || '') === String(item.id)) {
        opt.selected = true;
      }
      directManagerSelect.appendChild(opt);
    });
  }

  function loadManagerOptions() {
    const departmentId = (departmentSelect.value || '').trim();
    const jobTitleId = (jobTitleSelect.value || '').trim();
    const keepValue = directManagerSelect.value || '';

    if (!departmentId && !jobTitleId) {
      disableManagerSelect('اختر الإدارة والمسمى الوظيفي أولًا');
      setNote('<strong>المنطق الحالي:</strong> اختر الإدارة + المسمى الوظيفي أولًا، وسيظهر لك فقط المديرون الأعلى المناسبون حسب القواعد المعرفة في شاشة الهيكل الوظيفي.');
      return;
    }

    if (!departmentId) {
      disableManagerSelect('اختر الإدارة أولًا');
      setNote('<strong>مطلوب:</strong> اختر الإدارة أولًا حتى يتم تحديد المدراء المحتملين.');
      return;
    }

    if (!jobTitleId) {
      disableManagerSelect('اختر المسمى الوظيفي أولًا');
      setNote('<strong>مطلوب:</strong> اختر المسمى الوظيفي أولًا حتى يتم تحديد المدراء المحتملين.');
      return;
    }

    setNote('<strong>جارٍ التحليل:</strong> يتم الآن تحميل المديرين الأعلى المناسبين حسب الإدارة والمسمى الوظيفي...');
    directManagerSelect.disabled = true;

    const params = new URLSearchParams({
      department_id: departmentId,
      job_title_id: jobTitleId
    });

    if (employeeId) params.append('employee_id', employeeId);

    fetch("{% url 'employees:manager_options_api' %}?" + params.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
      const items = data.results || [];

      if (!items.length) {
        disableManagerSelect('لا يوجد مدير أعلى مناسب حاليًا');
        setNote('<strong>نتيجة التحليل:</strong> لا يوجد مدير أعلى مناسب حاليًا حسب القواعد الحالية. يمكنك تعديلها من شاشة إدارة الهيكل الوظيفي.');
        return;
      }

      renderManagers(items, keepValue);
      enableManagerSelect();
      setNote(`<strong>نتيجة التحليل:</strong> تم العثور على <strong>${items.length}</strong> مدير/قائد أعلى مناسب لهذا المسمى داخل هذا السياق التنظيمي.`);
    })
    .catch(() => {
      disableManagerSelect('تعذر تحميل المديرين المحتملين');
      setNote('<strong>تعذر التحليل:</strong> حدث خطأ أثناء تحميل قائمة المديرين المحتملين.');
    });
  }

  departmentSelect.addEventListener('change', loadManagerOptions);
  jobTitleSelect.addEventListener('change', loadManagerOptions);
  window.addEventListener('load', loadManagerOptions);
})();
</script>
{% endblock %}
"""
write_file("templates/employees/form.html", form_template)

print("\n" + "=" * 60)
print("✅ Patch 49c Revised اكتمل")
print("=" * 60)
print("""
الملفات المعدلة/المنشأة:
  ✅ employees/models.py
  ✅ employees/migrations/0006_job_hierarchy_models.py
  ✅ employees/admin.py
  ✅ employees/urls.py
  ✅ employees/views.py
  ✅ templates/employees/job_hierarchy_manage.html
  ✅ templates/employees/form.html

مهم:
  ✅ هذا الباتش هو البديل المعتمد لأي Patch 49c قديم خاص بفلترة المدير المباشر
  ✅ لا تشغّل أي Patch 49c قديم بعد هذا الباتش

شغّل بالترتيب:
  python manage.py makemigrations --check
  python manage.py migrate
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")