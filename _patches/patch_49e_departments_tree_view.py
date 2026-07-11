"""
Patch 49e — Departments Tree View + Parent/Child Mapping

الهدف:
1) إضافة هيكل شجري للإدارات (إدارة أم / أقسام تابعة)
2) إعادة تصميم صفحة /companies/departments/
3) تمكين ربط أي إدارة بإدارة أم من نفس الشاشة
4) عرض الإدارات بشكل واضح ومنظم
5) هذا الباتش مستقل عن Job Hierarchy الخاص بالموظفين

الملفات التي سيتم تعديلها/إنشاؤها:
- companies/models.py
- companies/migrations/0014_department_hierarchy.py
- companies/admin.py
- companies/views.py
- templates/companies/departments_list.html
"""

import os
import shutil
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
print("Patch 49e — Departments Tree View + Parent/Child Mapping")
print("=" * 60)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
os.makedirs(backup_dir, exist_ok=True)

for rel_path, backup_name in [
    ("companies/models.py", "companies_models_before_patch_49e.py.bak"),
    ("companies/admin.py", "companies_admin_before_patch_49e.py.bak"),
    ("companies/views.py", "companies_views_before_patch_49e.py.bak"),
    ("templates/companies/departments_list.html", "companies_departments_list_before_patch_49e.html.bak"),
]:
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup created: _patches/_backups/{backup_name}")

# ────────────────────────────────────────────────────────────
# Step 1: Update companies/models.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: تحديث companies/models.py")

models_path = "companies/models.py"
models_content = read_file(models_path)
if models_content is None:
    raise SystemExit("❌ ملف companies/models.py غير موجود")

models_append = '''

# ═════════════════════════════════════════════════════════════
# Patch 49e — Department Hierarchy
# ═════════════════════════════════════════════════════════════

class DepartmentHierarchy(models.Model):
    """
    ربط بين إدارة أم وقسم/إدارة فرعية
    لا يغير Department model نفسه لتجنب كسر الشاشات القديمة
    """

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='department_hierarchies',
        verbose_name='الشركة',
    )
    parent_department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        related_name='child_links',
        verbose_name='الإدارة الأم',
    )
    child_department = models.OneToOneField(
        'companies.Department',
        on_delete=models.CASCADE,
        related_name='parent_link',
        verbose_name='الإدارة الفرعية',
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ربط هيكل إداري'
        verbose_name_plural = 'الهيكل الإداري'
        ordering = ['parent_department_id', 'child_department_id', 'id']
        unique_together = [
            ['company', 'child_department']
        ]

    def __str__(self):
        try:
            parent_name = getattr(self.parent_department, 'name_ar', None) or getattr(self.parent_department, 'name_en', None) or f"#{self.parent_department_id}"
            child_name = getattr(self.child_department, 'name_ar', None) or getattr(self.child_department, 'name_en', None) or f"#{self.child_department_id}"
            return f"{parent_name} -> {child_name}"
        except Exception:
            return f"Hierarchy #{self.pk}"
'''

if "class DepartmentHierarchy(models.Model):" not in models_content:
    models_content = models_content.rstrip() + "\n" + models_append + "\n"
    write_file(models_path, models_content)
else:
    print("ℹ️ DepartmentHierarchy موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Write migration
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء migration يدوي")

migration_code = '''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0013_alter_notificationpreference_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentHierarchy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('child_department', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='parent_link', to='companies.department', verbose_name='الإدارة الفرعية')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_hierarchies', to='companies.company', verbose_name='الشركة')),
                ('parent_department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='child_links', to='companies.department', verbose_name='الإدارة الأم')),
            ],
            options={
                'verbose_name': 'ربط هيكل إداري',
                'verbose_name_plural': 'الهيكل الإداري',
                'ordering': ['parent_department_id', 'child_department_id', 'id'],
                'unique_together': {('company', 'child_department')},
            },
        ),
    ]
'''
write_file("companies/migrations/0014_department_hierarchy.py", migration_code)

# ────────────────────────────────────────────────────────────
# Step 3: Update admin.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: تحديث companies/admin.py")

admin_path = "companies/admin.py"
admin_content = read_file(admin_path)
if admin_content is None:
    admin_content = "from django.contrib import admin\n"

if "from .models import DepartmentHierarchy" not in admin_content:
    admin_content += "\nfrom .models import DepartmentHierarchy\n"

admin_append = '''

@admin.register(DepartmentHierarchy)
class DepartmentHierarchyAdmin(admin.ModelAdmin):
    list_display = ('parent_department', 'child_department', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = (
        'parent_department__name_ar', 'parent_department__name_en',
        'child_department__name_ar', 'child_department__name_en',
    )
'''
if "@admin.register(DepartmentHierarchy)" not in admin_content:
    admin_content = admin_content.rstrip() + "\n" + admin_append + "\n"

write_file(admin_path, admin_content)

# ────────────────────────────────────────────────────────────
# Step 4: Override departments_list view by appending final version
# ────────────────────────────────────────────────────────────
print("\n📌 Step 4: تحديث companies/views.py")

views_path = "companies/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف companies/views.py غير موجود")

views_append = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49e — Departments Tree View Override
# ═════════════════════════════════════════════════════════════

def _dept_display_name(dept):
    return (
        getattr(dept, 'name_ar', None)
        or getattr(dept, 'name_en', None)
        or f"Department #{getattr(dept, 'pk', '')}"
    )


def _build_department_tree_rows(departments, hierarchy_links):
    dept_map = {d.id: d for d in departments}
    child_to_parent = {}
    children_map = {}

    for link in hierarchy_links:
        if not getattr(link, 'is_active', True):
            continue
        parent_id = getattr(link, 'parent_department_id', None)
        child_id = getattr(link, 'child_department_id', None)
        if not parent_id or not child_id:
            continue
        child_to_parent[child_id] = parent_id
        children_map.setdefault(parent_id, []).append(child_id)

    root_ids = [d.id for d in departments if d.id not in child_to_parent]
    visited = set()
    rows = []

    def walk(dept_id, depth=0):
        if dept_id in visited:
            return
        visited.add(dept_id)

        dept = dept_map.get(dept_id)
        if not dept:
            return

        child_ids = children_map.get(dept_id, [])
        rows.append({
            'id': dept.id,
            'name': _dept_display_name(dept),
            'depth': depth,
            'children_count': len(child_ids),
            'parent_id': child_to_parent.get(dept_id),
            'is_root': depth == 0,
        })

        for c_id in sorted(child_ids, key=lambda x: _dept_display_name(dept_map.get(x)).lower() if dept_map.get(x) else ''):
            walk(c_id, depth + 1)

    for root_id in sorted(root_ids, key=lambda x: _dept_display_name(dept_map.get(x)).lower() if dept_map.get(x) else ''):
        walk(root_id, 0)

    # لو فيه loops/عناصر ما اتعرضتش
    remaining_ids = [d.id for d in departments if d.id not in visited]
    for rem_id in sorted(remaining_ids, key=lambda x: _dept_display_name(dept_map.get(x)).lower() if dept_map.get(x) else ''):
        walk(rem_id, 0)

    return rows


@login_required
def departments_list(request):
    """
    Patch 49e:
    صفحة الإدارات بشكل شجري + إدارة الربط بين الإدارة الأم والأقسام التابعة
    """
    from django.contrib import messages
    from django.core.exceptions import PermissionDenied
    from .models import Department, DepartmentHierarchy

    role = getattr(request.user, 'role', '') or ''
    if role not in ['company_admin', 'hr_manager', 'manager']:
        raise PermissionDenied("ليس لديك صلاحية عرض صفحة الإدارات")

    company = getattr(request.user, 'company', None)
    if not company:
        try:
            company = request.user.employee.company
        except Exception:
            company = None

    if not company:
        messages.error(request, 'لا يمكن تحديد الشركة الحالية.')
        return redirect('dashboard')

    def _would_create_cycle(child_id, parent_id):
        """
        منع:
        A -> B -> A
        """
        if not child_id or not parent_id:
            return False

        if child_id == parent_id:
            return True

        links = DepartmentHierarchy.objects.filter(company=company, is_active=True)
        parent_map = {link.child_department_id: link.parent_department_id for link in links}

        current = parent_id
        seen = set()
        while current and current not in seen:
            if current == child_id:
                return True
            seen.add(current)
            current = parent_map.get(current)
        return False

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        # ── حفظ الربط ────────────────────────────────────────
        if action == 'save_hierarchy':
            child_department_id = (request.POST.get('child_department_id') or '').strip()
            parent_department_id = (request.POST.get('parent_department_id') or '').strip()
            is_active = bool(request.POST.get('is_active'))
            notes = (request.POST.get('notes') or '').strip()

            if not child_department_id:
                messages.error(request, 'يرجى اختيار الإدارة الفرعية المراد ربطها')
                return redirect('/companies/departments/')

            try:
                child_department = Department.objects.get(pk=child_department_id, company=company)
            except Exception:
                messages.error(request, 'الإدارة الفرعية غير موجودة')
                return redirect('/companies/departments/')

            # لو parent فاضي = تحويل الإدارة إلى جذر / بدون أم
            if not parent_department_id:
                deleted_count, _ = DepartmentHierarchy.objects.filter(
                    company=company,
                    child_department=child_department
                ).delete()

                if deleted_count:
                    messages.success(request, f'تم تحويل "{_dept_display_name(child_department)}" إلى إدارة رئيسية')
                else:
                    messages.info(request, f'"{_dept_display_name(child_department)}" بالفعل إدارة رئيسية')
                return redirect('/companies/departments/')

            try:
                parent_department = Department.objects.get(pk=parent_department_id, company=company)
            except Exception:
                messages.error(request, 'الإدارة الأم غير موجودة')
                return redirect('/companies/departments/')

            if child_department.id == parent_department.id:
                messages.error(request, 'لا يمكن ربط الإدارة بنفسها كإدارة أم')
                return redirect('/companies/departments/')

            if _would_create_cycle(child_department.id, parent_department.id):
                messages.error(request, 'هذا الربط سيُحدث حلقة غير صحيحة في الهيكل الإداري')
                return redirect('/companies/departments/')

            try:
                link, created = DepartmentHierarchy.objects.update_or_create(
                    company=company,
                    child_department=child_department,
                    defaults={
                        'parent_department': parent_department,
                        'is_active': is_active,
                        'notes': notes,
                    }
                )
                if created:
                    messages.success(request, f'تم ربط "{_dept_display_name(child_department)}" تحت "{_dept_display_name(parent_department)}"')
                else:
                    messages.success(request, f'تم تحديث ربط "{_dept_display_name(child_department)}"')
            except Exception as e:
                messages.error(request, f'تعذر حفظ الربط: {e}')

            return redirect('/companies/departments/')

        # ── حذف الربط ────────────────────────────────────────
        if action == 'delete_hierarchy':
            link_id = (request.POST.get('link_id') or '').strip()
            try:
                link = DepartmentHierarchy.objects.get(pk=link_id, company=company)
                child_name = _dept_display_name(link.child_department)
                link.delete()
                messages.success(request, f'تم فك ربط "{child_name}" وأصبحت إدارة رئيسية')
            except DepartmentHierarchy.DoesNotExist:
                messages.error(request, 'الرابط غير موجود')
            except Exception as e:
                messages.error(request, f'تعذر حذف الربط: {e}')
            return redirect('/companies/departments/')

    departments = list(
        Department.objects.filter(company=company).order_by('name_ar', 'name_en', 'id')
    )

    hierarchy_links = list(
        DepartmentHierarchy.objects.filter(company=company).select_related(
            'parent_department', 'child_department'
        ).order_by('parent_department__name_ar', 'child_department__name_ar', 'id')
    )

    tree_rows = _build_department_tree_rows(departments, hierarchy_links)

    child_ids = {link.child_department_id for link in hierarchy_links if getattr(link, 'is_active', True)}
    root_departments = [d for d in departments if d.id not in child_ids]

    context = {
        'page_title': 'الإدارات',
        'departments': departments,
        'root_departments': root_departments,
        'hierarchy_links': hierarchy_links,
        'tree_rows': tree_rows,
    }
    return render(request, 'companies/departments_list.html', context)
'''

if "Patch 49e — Departments Tree View Override" not in views_content:
    views_content = views_content.rstrip() + "\n\n" + views_append + "\n"
    write_file(views_path, views_content)
else:
    print("ℹ️ departments_list override موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 5: Rewrite template
# ────────────────────────────────────────────────────────────
print("\n📌 Step 5: تحديث templates/companies/departments_list.html")

template_path = "templates/companies/departments_list.html"
template_code = """{% extends 'base/dashboard_base.html' %}

{% block title %}الإدارات{% endblock %}

{% block extra_css %}
<style>
  .soft-card {
    border: 1px solid #e2e8f0;
    border-radius: 18px;
  }
  .soft-card .card-header {
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    border-radius: 18px 18px 0 0 !important;
  }
  .tree-row {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 12px 14px;
    background: #fff;
  }
  .tree-line {
    border-right: 3px solid #06B6D4;
  }
  .tree-badge {
    border-radius: 999px;
    font-size: .76rem;
    padding: .35rem .65rem;
  }
  .help-box {
    border: 1px solid #bae6fd;
    background: #f0f9ff;
    border-radius: 16px;
    padding: 16px;
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
        <i class="bi bi-diagram-3-fill text-primary me-2"></i>الإدارات
      </h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item active">الإدارات</li>
        </ol>
      </nav>
    </div>
  </div>

  <div class="help-box mb-4">
    <div class="fw-bold mb-2">
      <i class="bi bi-lightbulb-fill text-warning me-1"></i>فكرة الصفحة
    </div>
    <div class="small text-muted">
      من هنا تقدر تحدد <strong>الإدارة الأم</strong> وتربط تحتها الإدارات/الأقسام الفرعية،
      بحيث الهيكل الإداري يبقى واضح جدًا للشركة بدل قائمة مسطحة غير مفهومة.
    </div>
  </div>

  <div class="row g-4">

    <!-- Form -->
    <div class="col-lg-4">
      <div class="card soft-card border-0 shadow-sm">
        <div class="card-header py-3">
          <h6 class="mb-0 fw-bold">
            <i class="bi bi-link-45deg me-2 text-primary"></i>ربط إدارة بإدارة أم
          </h6>
        </div>
        <div class="card-body">
          <form method="post">
            {% csrf_token %}
            <input type="hidden" name="action" value="save_hierarchy">

            <div class="mb-3">
              <label class="form-label fw-semibold">الإدارة الفرعية <span class="text-danger">*</span></label>
              <select name="child_department_id" class="form-select" required>
                <option value="">اختر الإدارة الفرعية</option>
                {% for dept in departments %}
                  <option value="{{ dept.id }}">{{ dept.name_ar|default:dept.name_en }}</option>
                {% endfor %}
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">الإدارة الأم</label>
              <select name="parent_department_id" class="form-select">
                <option value="">بدون — إدارة رئيسية</option>
                {% for dept in departments %}
                  <option value="{{ dept.id }}">{{ dept.name_ar|default:dept.name_en }}</option>
                {% endfor %}
              </select>
              <div class="mini-note mt-1">
                لو سيبتها فاضية، القسم هيبقى إدارة رئيسية مستقلة.
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">ملاحظات</label>
              <textarea name="notes" class="form-control" rows="2" placeholder="مثال: تابع إداريًا لإدارة التشغيل"></textarea>
            </div>

            <div class="form-check mb-3">
              <input class="form-check-input" type="checkbox" name="is_active" id="hierarchyActive" checked>
              <label class="form-check-label" for="hierarchyActive">
                ربط نشط
              </label>
            </div>

            <button type="submit" class="btn btn-primary w-100">
              <i class="bi bi-save me-1"></i>حفظ الربط
            </button>
          </form>
        </div>
      </div>

      <div class="card soft-card border-0 shadow-sm mt-4">
        <div class="card-header py-3">
          <h6 class="mb-0 fw-bold">
            <i class="bi bi-stars me-2 text-primary"></i>الإدارات الرئيسية
          </h6>
        </div>
        <div class="card-body">
          {% if root_departments %}
            <div class="d-flex flex-wrap gap-2">
              {% for dept in root_departments %}
                <span class="badge bg-info-subtle text-info border border-info-subtle tree-badge">
                  {{ dept.name_ar|default:dept.name_en }}
                </span>
              {% endfor %}
            </div>
          {% else %}
            <div class="text-muted small">لا توجد إدارات رئيسية واضحة حاليًا</div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- Tree -->
    <div class="col-lg-8">
      <div class="card soft-card border-0 shadow-sm mb-4">
        <div class="card-header py-3 d-flex justify-content-between align-items-center">
          <h6 class="mb-0 fw-bold">
            <i class="bi bi-diagram-2 me-2 text-primary"></i>الهيكل الشجري للإدارات
          </h6>
          <span class="badge bg-secondary">{{ tree_rows|length }} عقدة</span>
        </div>
        <div class="card-body">
          {% if tree_rows %}
            <div class="d-flex flex-column gap-2">
              {% for row in tree_rows %}
              <div class="tree-row {% if row.depth > 0 %}tree-line{% endif %}" style="margin-right: {{ row.depth|add:0 }}rem; padding-right: calc(14px + {{ row.depth }} * 18px);">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <div>
                    <div class="fw-bold">
                      {% if row.depth == 0 %}
                        <i class="bi bi-building text-primary me-1"></i>
                      {% else %}
                        <i class="bi bi-arrow-return-left text-muted me-1"></i>
                      {% endif %}
                      {{ row.name }}
                    </div>
                    <div class="mini-note mt-1">
                      المستوى: {{ row.depth }}
                      {% if row.is_root %} | إدارة رئيسية{% endif %}
                      | عدد الإدارات التابعة المباشرة: {{ row.children_count }}
                    </div>
                  </div>
                  <div class="d-flex gap-2">
                    {% if row.is_root %}
                      <span class="badge bg-primary-subtle text-primary border border-primary-subtle tree-badge">أم</span>
                    {% else %}
                      <span class="badge bg-light text-dark border tree-badge">فرعية</span>
                    {% endif %}
                  </div>
                </div>
              </div>
              {% endfor %}
            </div>
          {% else %}
            <div class="text-center text-muted py-4">
              <i class="bi bi-diagram-3 fs-1 opacity-25"></i>
              <div class="mt-2">لا توجد إدارات لعرضها</div>
            </div>
          {% endif %}
        </div>
      </div>

      <div class="card soft-card border-0 shadow-sm">
        <div class="card-header py-3 d-flex justify-content-between align-items-center">
          <h6 class="mb-0 fw-bold">
            <i class="bi bi-list-ul me-2 text-primary"></i>روابط الهيكل الحالية
          </h6>
          <span class="badge bg-secondary">{{ hierarchy_links|length }} رابط</span>
        </div>
        <div class="card-body p-0">
          {% if hierarchy_links %}
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>الإدارة الأم</th>
                  <th>الإدارة الفرعية</th>
                  <th>الحالة</th>
                  <th>ملاحظات</th>
                  <th>إجراء</th>
                </tr>
              </thead>
              <tbody>
                {% for link in hierarchy_links %}
                <tr>
                  <td>{{ link.parent_department.name_ar|default:link.parent_department.name_en }}</td>
                  <td>{{ link.child_department.name_ar|default:link.child_department.name_en }}</td>
                  <td>
                    {% if link.is_active %}
                      <span class="badge bg-success-subtle text-success border border-success-subtle">نشط</span>
                    {% else %}
                      <span class="badge bg-secondary-subtle text-secondary">معطل</span>
                    {% endif %}
                  </td>
                  <td class="small text-muted">{{ link.notes|default:"—" }}</td>
                  <td>
                    <form method="post" onsubmit="return confirm('فك الربط؟ ستصبح الإدارة الفرعية إدارة رئيسية.');">
                      {% csrf_token %}
                      <input type="hidden" name="action" value="delete_hierarchy">
                      <input type="hidden" name="link_id" value="{{ link.id }}">
                      <button type="submit" class="btn btn-sm btn-outline-danger">
                        <i class="bi bi-unlink"></i>
                      </button>
                    </form>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center text-muted py-4">
            <i class="bi bi-link-45deg fs-1 opacity-25"></i>
            <div class="mt-2">لا توجد روابط هرمية بعد</div>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
write_file(template_path, template_code)

print("\n" + "=" * 60)
print("✅ Patch 49e اكتمل")
print("=" * 60)
print("""
الملفات المعدلة/المنشأة:
  ✅ companies/models.py
  ✅ companies/migrations/0014_department_hierarchy.py
  ✅ companies/admin.py
  ✅ companies/views.py
  ✅ templates/companies/departments_list.html

مهم:
  ✅ هذا الباتش يضيف هيكل شجري للإدارات بدون كسر Department model القديم
  ✅ الربط بين الإدارة الأم والفرعية يتم من نفس صفحة /companies/departments/
  ✅ هذا الباتش مستقل عن hierarchy الخاصة بالمسميات الوظيفية للموظفين

شغّل:
  python manage.py makemigrations --check
  python manage.py migrate
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")