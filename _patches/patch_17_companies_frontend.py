#!/usr/bin/env python3
"""
Patch 17: صفحات الشركات والفروع والإدارات (Frontend)
========================================================
- إصلاح URLs نهائياً
- صفحة إعدادات الشركة
- صفحة الفروع (قائمة + إضافة + تعديل)
- صفحة الإدارات (قائمة + شجرة)
- صفحة الشيفتات (قائمة + إضافة)
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
print("  Patch 17: Companies Frontend")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إصلاح motionhr/urls.py نهائياً
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح motionhr/urls.py نهائياً...")

new_main_urls = """from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from accounts.views import (
    CustomPasswordChangeView,
    smart_login_view,
    smart_logout_view,
    dashboard,
)


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


urlpatterns = [

    # ── الرئيسية ──────────────────────────────────────────
    path('', home_redirect, name='home'),

    # ── Admin ─────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── تسجيل الدخول والخروج ──────────────────────────────
    path('login/',  smart_login_view,  name='login'),
    path('logout/', smart_logout_view, name='logout'),

    # ── استعادة كلمة المرور ───────────────────────────────
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/password-reset/done/',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/password-reset-complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # ── تغيير كلمة المرور ─────────────────────────────────
    path('password-change/',
         CustomPasswordChangeView.as_view(
             template_name='accounts/password_change.html',
             success_url='/password-change/done/',
         ),
         name='password_change'),

    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html',
         ),
         name='password_change_done'),

    # ── Dashboard ─────────────────────────────────────────
    path('dashboard/', dashboard, name='dashboard'),

    # ── Apps ──────────────────────────────────────────────
    path('accounts/',      include('accounts.urls',      namespace='accounts')),
    path('employees/',     include('employees.urls',     namespace='employees')),
    path('attendance/',    include('attendance.urls',    namespace='attendance')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    path('companies/',     include('companies.urls',     namespace='companies')),

]

# ── Media + Static (Development) ──────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,   document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,  document_root=settings.STATIC_ROOT)
"""

write_file(
    os.path.join(BASE_DIR, 'motionhr', 'urls.py'),
    new_main_urls
)


# ════════════════════════════════════════════════════════════
# 2. إنشاء companies/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء companies/urls.py...")

companies_urls = """from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [

    # ── الشركة ────────────────────────────────────────────
    path('settings/',       views.company_settings,  name='settings'),

    # ── الفروع ────────────────────────────────────────────
    path('branches/',           views.branches_list,   name='branches_list'),
    path('branches/add/',       views.branch_add,      name='branch_add'),
    path('branches/<int:pk>/edit/',   views.branch_edit,   name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),

    # ── الإدارات ──────────────────────────────────────────
    path('departments/',              views.departments_list,   name='departments_list'),
    path('departments/add/',          views.department_add,     name='department_add'),
    path('departments/<int:pk>/edit/',   views.department_edit,   name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    # ── الشيفتات ──────────────────────────────────────────
    path('shifts/',              views.shifts_list,   name='shifts_list'),
    path('shifts/add/',          views.shift_add,     name='shift_add'),
    path('shifts/<int:pk>/edit/',   views.shift_edit,   name='shift_edit'),
    path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),

]
"""

create_file(
    os.path.join(BASE_DIR, 'companies', 'urls.py'),
    companies_urls
)


# ════════════════════════════════════════════════════════════
# 3. إنشاء companies/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء companies/views.py...")

companies_views = '''"""
companies/views.py
صفحات إدارة الشركة والفروع والإدارات والشيفتات
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Company, Branch, Department
from attendance.models import Shift


# ════════════════════════════════════════════════════════════
# الشركة
# ════════════════════════════════════════════════════════════

@login_required
def company_settings(request):
    """إعدادات الشركة"""
    company = request.user.company
    if not company:
        messages.error(request, 'لا يوجد شركة مرتبطة بحسابك')
        return redirect('dashboard')

    if request.method == 'POST':
        company.name_ar           = request.POST.get('name_ar', company.name_ar)
        company.name_en           = request.POST.get('name_en', company.name_en)
        company.email             = request.POST.get('email', company.email)
        company.phone             = request.POST.get('phone', company.phone)
        company.address           = request.POST.get('address', company.address)
        company.website           = request.POST.get('website', company.website)
        company.commercial_register = request.POST.get('commercial_register', '')
        company.tax_number        = request.POST.get('tax_number', '')

        if 'logo' in request.FILES:
            company.logo = request.FILES['logo']

        company.save()
        messages.success(request, '✅ تم حفظ إعدادات الشركة بنجاح')
        return redirect('companies:settings')

    context = {
        'company':    company,
        'page_title': 'إعدادات الشركة',
    }
    return render(request, 'companies/settings.html', context)


# ════════════════════════════════════════════════════════════
# الفروع
# ════════════════════════════════════════════════════════════

@login_required
def branches_list(request):
    """قائمة الفروع"""
    company  = request.user.company
    branches = Branch.objects.filter(company=company).order_by('-is_main', 'name_ar')
    context  = {
        'branches':   branches,
        'page_title': 'الفروع',
    }
    return render(request, 'companies/branches_list.html', context)


@login_required
def branch_add(request):
    """إضافة فرع جديد"""
    company = request.user.company

    if request.method == 'POST':
        branch = Branch(company=company)
        branch.name_ar        = request.POST.get('name_ar', '')
        branch.name_en        = request.POST.get('name_en', '')
        branch.address        = request.POST.get('address', '')
        branch.phone          = request.POST.get('phone', '')
        branch.is_main        = request.POST.get('is_main') == 'on'
        branch.is_active      = True

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        if lat:
            branch.latitude  = float(lat)
        if lng:
            branch.longitude = float(lng)

        radius = request.POST.get('check_in_radius', 100)
        branch.check_in_radius = int(radius) if radius else 100

        branch.save()
        messages.success(request, f'✅ تم إضافة الفرع "{branch.name_ar}" بنجاح')
        return redirect('companies:branches_list')

    context = {
        'page_title': 'إضافة فرع جديد',
        'action':     'add',
    }
    return render(request, 'companies/branch_form.html', context)


@login_required
def branch_edit(request, pk):
    """تعديل فرع"""
    branch = get_object_or_404(Branch, pk=pk, company=request.user.company)

    if request.method == 'POST':
        branch.name_ar   = request.POST.get('name_ar', branch.name_ar)
        branch.name_en   = request.POST.get('name_en', branch.name_en)
        branch.address   = request.POST.get('address', branch.address)
        branch.phone     = request.POST.get('phone', branch.phone)
        branch.is_main   = request.POST.get('is_main') == 'on'
        branch.is_active = request.POST.get('is_active') == 'on'

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        if lat:
            branch.latitude  = float(lat)
        if lng:
            branch.longitude = float(lng)

        radius = request.POST.get('check_in_radius', 100)
        branch.check_in_radius = int(radius) if radius else 100

        branch.save()
        messages.success(request, f'✅ تم تحديث الفرع "{branch.name_ar}" بنجاح')
        return redirect('companies:branches_list')

    context = {
        'branch':     branch,
        'page_title': f'تعديل فرع: {branch.name_ar}',
        'action':     'edit',
    }
    return render(request, 'companies/branch_form.html', context)


@login_required
@require_POST
def branch_delete(request, pk):
    """حذف فرع"""
    branch = get_object_or_404(Branch, pk=pk, company=request.user.company)
    name   = branch.name_ar
    branch.delete()
    messages.success(request, f'✅ تم حذف الفرع "{name}"')
    return redirect('companies:branches_list')


# ════════════════════════════════════════════════════════════
# الإدارات
# ════════════════════════════════════════════════════════════

@login_required
def departments_list(request):
    """قائمة الإدارات"""
    company     = request.user.company
    departments = Department.objects.filter(
        company=company
    ).select_related('parent').order_by('parent__name_ar', 'name_ar')

    context = {
        'departments': departments,
        'page_title':  'الإدارات والأقسام',
    }
    return render(request, 'companies/departments_list.html', context)


@login_required
def department_add(request):
    """إضافة إدارة جديدة"""
    company     = request.user.company
    departments = Department.objects.filter(company=company, is_active=True)

    if request.method == 'POST':
        dept         = Department(company=company)
        dept.name_ar = request.POST.get('name_ar', '')
        dept.name_en = request.POST.get('name_en', '')
        dept.code    = request.POST.get('code', '')
        dept.description = request.POST.get('description', '')
        dept.is_active   = True

        parent_id = request.POST.get('parent')
        if parent_id:
            dept.parent = get_object_or_404(Department, pk=parent_id, company=company)

        dept.save()
        messages.success(request, f'✅ تم إضافة الإدارة "{dept.name_ar}" بنجاح')
        return redirect('companies:departments_list')

    context = {
        'departments': departments,
        'page_title':  'إضافة إدارة جديدة',
        'action':      'add',
    }
    return render(request, 'companies/department_form.html', context)


@login_required
def department_edit(request, pk):
    """تعديل إدارة"""
    company = request.user.company
    dept    = get_object_or_404(Department, pk=pk, company=company)
    departments = Department.objects.filter(
        company=company, is_active=True
    ).exclude(pk=pk)

    if request.method == 'POST':
        dept.name_ar     = request.POST.get('name_ar', dept.name_ar)
        dept.name_en     = request.POST.get('name_en', dept.name_en)
        dept.code        = request.POST.get('code', dept.code)
        dept.description = request.POST.get('description', dept.description)
        dept.is_active   = request.POST.get('is_active') == 'on'

        parent_id = request.POST.get('parent')
        if parent_id:
            dept.parent = get_object_or_404(Department, pk=parent_id, company=company)
        else:
            dept.parent = None

        dept.save()
        messages.success(request, f'✅ تم تحديث الإدارة "{dept.name_ar}" بنجاح')
        return redirect('companies:departments_list')

    context = {
        'dept':        dept,
        'departments': departments,
        'page_title':  f'تعديل: {dept.name_ar}',
        'action':      'edit',
    }
    return render(request, 'companies/department_form.html', context)


@login_required
@require_POST
def department_delete(request, pk):
    """حذف إدارة"""
    dept = get_object_or_404(Department, pk=pk, company=request.user.company)
    name = dept.name_ar
    dept.delete()
    messages.success(request, f'✅ تم حذف الإدارة "{name}"')
    return redirect('companies:departments_list')


# ════════════════════════════════════════════════════════════
# الشيفتات
# ════════════════════════════════════════════════════════════

@login_required
def shifts_list(request):
    """قائمة الشيفتات"""
    company = request.user.company
    shifts  = Shift.objects.filter(company=company).order_by('name')
    context = {
        'shifts':     shifts,
        'page_title': 'الشيفتات',
    }
    return render(request, 'companies/shifts_list.html', context)


@login_required
def shift_add(request):
    """إضافة شيفت جديد"""
    company = request.user.company

    if request.method == 'POST':
        shift = Shift(company=company)
        shift.name        = request.POST.get('name', '')
        shift.shift_type  = request.POST.get('shift_type', 'fixed')
        shift.start_time  = request.POST.get('start_time', '08:00')
        shift.end_time    = request.POST.get('end_time',   '17:00')
        shift.grace_period   = int(request.POST.get('grace_period', 15))
        shift.break_duration = int(request.POST.get('break_duration', 60))

        # أيام العمل
        shift.work_sunday    = 'work_sunday'    in request.POST
        shift.work_monday    = 'work_monday'    in request.POST
        shift.work_tuesday   = 'work_tuesday'   in request.POST
        shift.work_wednesday = 'work_wednesday' in request.POST
        shift.work_thursday  = 'work_thursday'  in request.POST
        shift.work_friday    = 'work_friday'    in request.POST
        shift.work_saturday  = 'work_saturday'  in request.POST

        shift.save()
        messages.success(request, f'✅ تم إضافة الشيفت "{shift.name}" بنجاح')
        return redirect('companies:shifts_list')

    context = {
        'page_title': 'إضافة شيفت جديد',
        'action':     'add',
    }
    return render(request, 'companies/shift_form.html', context)


@login_required
def shift_edit(request, pk):
    """تعديل شيفت"""
    shift = get_object_or_404(Shift, pk=pk, company=request.user.company)

    if request.method == 'POST':
        shift.name        = request.POST.get('name', shift.name)
        shift.shift_type  = request.POST.get('shift_type', shift.shift_type)
        shift.start_time  = request.POST.get('start_time', shift.start_time)
        shift.end_time    = request.POST.get('end_time',   shift.end_time)
        shift.grace_period   = int(request.POST.get('grace_period',   15))
        shift.break_duration = int(request.POST.get('break_duration', 60))

        shift.work_sunday    = 'work_sunday'    in request.POST
        shift.work_monday    = 'work_monday'    in request.POST
        shift.work_tuesday   = 'work_tuesday'   in request.POST
        shift.work_wednesday = 'work_wednesday' in request.POST
        shift.work_thursday  = 'work_thursday'  in request.POST
        shift.work_friday    = 'work_friday'    in request.POST
        shift.work_saturday  = 'work_saturday'  in request.POST

        shift.save()
        messages.success(request, f'✅ تم تحديث الشيفت "{shift.name}" بنجاح')
        return redirect('companies:shifts_list')

    context = {
        'shift':      shift,
        'page_title': f'تعديل: {shift.name}',
        'action':     'edit',
    }
    return render(request, 'companies/shift_form.html', context)


@login_required
@require_POST
def shift_delete(request, pk):
    """حذف شيفت"""
    shift = get_object_or_404(Shift, pk=pk, company=request.user.company)
    name  = shift.name
    shift.delete()
    messages.success(request, f'✅ تم حذف الشيفت "{name}"')
    return redirect('companies:shifts_list')
'''

create_file(
    os.path.join(BASE_DIR, 'companies', 'views.py'),
    companies_views
)


# ════════════════════════════════════════════════════════════
# 4. إنشاء Template: companies/settings.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/settings.html...")

settings_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إعدادات الشركة{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-building me-2" style="color:#06B6D4;"></i>
        إعدادات الشركة
      </h4>
      <p class="text-muted mb-0">بيانات ومعلومات الشركة</p>
    </div>
  </div>

  <form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    <div class="row g-4">

      <!-- البيانات الأساسية -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">البيانات الأساسية</h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسم الشركة (عربي) <span class="text-danger">*</span></label>
                <input type="text" name="name_ar" class="form-control"
                       value="{{ company.name_ar }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسم الشركة (إنجليزي)</label>
                <input type="text" name="name_en" class="form-control"
                       value="{{ company.name_en|default:'' }}" dir="ltr">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">البريد الإلكتروني</label>
                <input type="email" name="email" class="form-control"
                       value="{{ company.email|default:'' }}" dir="ltr">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">رقم الهاتف</label>
                <input type="text" name="phone" class="form-control"
                       value="{{ company.phone|default:'' }}">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">السجل التجاري</label>
                <input type="text" name="commercial_register" class="form-control"
                       value="{{ company.commercial_register|default:'' }}">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الرقم الضريبي</label>
                <input type="text" name="tax_number" class="form-control"
                       value="{{ company.tax_number|default:'' }}">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الموقع الإلكتروني</label>
                <input type="url" name="website" class="form-control"
                       value="{{ company.website|default:'' }}" dir="ltr">
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">العنوان</label>
                <textarea name="address" class="form-control" rows="2">{{ company.address|default:'' }}</textarea>
              </div>

            </div>
          </div>
        </div>
      </div>

      <!-- الشعار -->
      <div class="col-lg-4">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">شعار الشركة</h5>
          </div>
          <div class="card-body px-4 pb-4 text-center">

            <!-- عرض الشعار الحالي -->
            <div class="mb-3">
              {% if company.logo %}
                <img src="{{ company.logo.url }}"
                     class="rounded-3 shadow-sm"
                     style="max-width:150px; max-height:150px; object-fit:contain;">
              {% else %}
                <div class="rounded-3 d-flex align-items-center justify-content-center mx-auto"
                     style="width:150px;height:150px;background:#e0f7fa;">
                  <i class="bi bi-building" style="font-size:3rem;color:#06B6D4;"></i>
                </div>
              {% endif %}
            </div>

            <label class="form-label fw-semibold small">رفع شعار جديد</label>
            <input type="file" name="logo" class="form-control"
                   accept="image/*">
            <small class="text-muted d-block mt-1">PNG, JPG - حجم أقصى 2MB</small>

          </div>
        </div>

        <!-- معلومات الاشتراك -->
        <div class="card border-0 shadow-sm mt-3">
          <div class="card-body p-4">
            <h6 class="fw-bold mb-3">
              <i class="bi bi-star me-2" style="color:#06B6D4;"></i>
              معلومات الاشتراك
            </h6>
            <a href="{% url 'subscriptions:my_plan' %}"
               class="btn w-100 text-white"
               style="background:#06B6D4;">
              عرض خطتي
            </a>
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
        حفظ التغييرات
      </button>
    </div>

  </form>
</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'settings.html'),
    settings_template
)


# ════════════════════════════════════════════════════════════
# 5. إنشاء Template: companies/branches_list.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/branches_list.html...")

branches_list_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}الفروع{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-geo-alt me-2" style="color:#06B6D4;"></i>
        الفروع
      </h4>
      <p class="text-muted mb-0">إدارة فروع الشركة</p>
    </div>
    <a href="{% url 'companies:branch_add' %}"
       class="btn text-white"
       style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i>
      فرع جديد
    </a>
  </div>

  {% if branches %}
  <div class="row g-3">
    {% for branch in branches %}
    <div class="col-md-6 col-lg-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">

          <div class="d-flex align-items-start justify-content-between mb-3">
            <div class="d-flex align-items-center gap-3">
              <div class="rounded-circle d-flex align-items-center justify-content-center"
                   style="width:48px;height:48px;
                          background:{% if branch.is_main %}#e0f7fa{% else %}#f3f4f6{% endif %};">
                <i class="bi bi-{% if branch.is_main %}star-fill{% else %}geo-alt-fill{% endif %}"
                   style="color:{% if branch.is_main %}#06B6D4{% else %}#6b7280{% endif %};"></i>
              </div>
              <div>
                <h6 class="fw-bold mb-0">{{ branch.name_ar }}</h6>
                {% if branch.name_en %}
                  <small class="text-muted" dir="ltr">{{ branch.name_en }}</small>
                {% endif %}
              </div>
            </div>
            <div class="d-flex gap-1">
              {% if branch.is_main %}
                <span class="badge" style="background:#06B6D4;">رئيسي</span>
              {% endif %}
              {% if not branch.is_active %}
                <span class="badge bg-danger">موقوف</span>
              {% endif %}
            </div>
          </div>

          {% if branch.address %}
          <div class="d-flex align-items-start gap-2 mb-2">
            <i class="bi bi-pin-map text-muted mt-1" style="font-size:0.8rem;"></i>
            <small class="text-muted">{{ branch.address }}</small>
          </div>
          {% endif %}

          {% if branch.phone %}
          <div class="d-flex align-items-center gap-2 mb-2">
            <i class="bi bi-telephone text-muted" style="font-size:0.8rem;"></i>
            <small class="text-muted">{{ branch.phone }}</small>
          </div>
          {% endif %}

          {% if branch.latitude %}
          <div class="d-flex align-items-center gap-2 mb-2">
            <i class="bi bi-crosshair text-success" style="font-size:0.8rem;"></i>
            <small class="text-muted">
              GPS: {{ branch.latitude|floatformat:4 }}, {{ branch.longitude|floatformat:4 }}
              <span class="badge bg-light text-dark ms-1">نطاق {{ branch.check_in_radius }}م</span>
            </small>
          </div>
          {% endif %}

          <div class="d-flex gap-2 mt-3 pt-3 border-top">
            <a href="{% url 'companies:branch_edit' branch.pk %}"
               class="btn btn-sm btn-outline-primary flex-fill">
              <i class="bi bi-pencil me-1"></i>تعديل
            </a>
            <form method="post"
                  action="{% url 'companies:branch_delete' branch.pk %}"
                  onsubmit="return confirm('حذف الفرع {{ branch.name_ar }}؟')">
              {% csrf_token %}
              <button type="submit" class="btn btn-sm btn-outline-danger">
                <i class="bi bi-trash"></i>
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-geo-alt" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد فروع بعد</h5>
      <a href="{% url 'companies:branch_add' %}"
         class="btn mt-2 text-white"
         style="background:#06B6D4;">
        <i class="bi bi-plus me-1"></i>أضف أول فرع
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'branches_list.html'),
    branches_list_template
)


# ════════════════════════════════════════════════════════════
# 6. إنشاء Template: companies/branch_form.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/branch_form.html...")

branch_form_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'companies:branches_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <div>
      <h4 class="fw-bold mb-0">{{ page_title }}</h4>
    </div>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">

          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسم الفرع (عربي) <span class="text-danger">*</span></label>
                <input type="text" name="name_ar" class="form-control"
                       value="{{ branch.name_ar|default:'' }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسم الفرع (إنجليزي)</label>
                <input type="text" name="name_en" class="form-control"
                       value="{{ branch.name_en|default:'' }}" dir="ltr">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">رقم الهاتف</label>
                <input type="text" name="phone" class="form-control"
                       value="{{ branch.phone|default:'' }}">
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">العنوان</label>
                <input type="text" name="address" class="form-control"
                       value="{{ branch.address|default:'' }}">
              </div>

              <!-- GPS -->
              <div class="col-12">
                <label class="form-label fw-semibold small">
                  <i class="bi bi-crosshair me-1 text-success"></i>
                  موقع GPS
                </label>
                <div class="row g-2">
                  <div class="col-md-4">
                    <input type="number" name="latitude"
                           class="form-control" step="any"
                           placeholder="خط العرض"
                           id="latInput"
                           value="{{ branch.latitude|default:'' }}"
                           dir="ltr">
                  </div>
                  <div class="col-md-4">
                    <input type="number" name="longitude"
                           class="form-control" step="any"
                           placeholder="خط الطول"
                           id="lngInput"
                           value="{{ branch.longitude|default:'' }}"
                           dir="ltr">
                  </div>
                  <div class="col-md-4">
                    <button type="button"
                            class="btn w-100"
                            style="background:#06B6D4;color:white;"
                            onclick="getMyLocation()">
                      <i class="bi bi-crosshair me-1"></i>
                      موقعي الحالي
                    </button>
                  </div>
                </div>
              </div>

              <!-- نطاق الـ Check-in -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  نطاق تسجيل الحضور (متر)
                </label>
                <div class="d-flex align-items-center gap-3">
                  <input type="range" name="check_in_radius"
                         class="form-range flex-grow-1"
                         min="50" max="1000" step="50"
                         value="{{ branch.check_in_radius|default:100 }}"
                         oninput="document.getElementById('radiusVal').textContent=this.value">
                  <span class="badge fs-6 px-3" style="background:#06B6D4; min-width:55px;">
                    <span id="radiusVal">{{ branch.check_in_radius|default:100 }}</span>م
                  </span>
                </div>
                <small class="text-muted">الحد الأدنى: 50م | الحد الأقصى: 1000م</small>
              </div>

              <!-- الفرع الرئيسي -->
              <div class="col-md-6 d-flex align-items-center">
                <div class="form-check form-switch mt-3">
                  <input class="form-check-input" type="checkbox"
                         name="is_main" id="isMain"
                         {% if branch.is_main %}checked{% endif %}
                         style="width:2.5rem;height:1.25rem;">
                  <label class="form-check-label fw-semibold" for="isMain">
                    الفرع الرئيسي للشركة
                  </label>
                </div>
              </div>

              {% if action == 'edit' %}
              <div class="col-12">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox"
                         name="is_active" id="isActive"
                         {% if branch.is_active %}checked{% endif %}
                         style="width:2.5rem;height:1.25rem;">
                  <label class="form-check-label fw-semibold" for="isActive">
                    الفرع نشط
                  </label>
                </div>
              </div>
              {% endif %}

            </div>

            <!-- أزرار -->
            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit"
                      class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة الفرع{% else %}حفظ التغييرات{% endif %}
              </button>
              <a href="{% url 'companies:branches_list' %}"
                 class="btn btn-outline-secondary px-4"
                 style="border-radius:10px;">
                إلغاء
              </a>
            </div>

          </form>
        </div>
      </div>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_js %}
<script>
function getMyLocation() {
    if (!navigator.geolocation) {
        alert('المتصفح لا يدعم تحديد الموقع');
        return;
    }
    navigator.geolocation.getCurrentPosition(
        function(pos) {
            document.getElementById('latInput').value = pos.coords.latitude.toFixed(6);
            document.getElementById('lngInput').value = pos.coords.longitude.toFixed(6);
        },
        function(err) {
            alert('تعذر تحديد الموقع: ' + err.message);
        }
    );
}
</script>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'branch_form.html'),
    branch_form_template
)


# ════════════════════════════════════════════════════════════
# 7. إنشاء Template: companies/departments_list.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/departments_list.html...")

departments_list_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}الإدارات والأقسام{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-diagram-3 me-2" style="color:#06B6D4;"></i>
        الإدارات والأقسام
      </h4>
      <p class="text-muted mb-0">الهيكل التنظيمي للشركة</p>
    </div>
    <a href="{% url 'companies:department_add' %}"
       class="btn text-white"
       style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i>
      إدارة جديدة
    </a>
  </div>

  {% if departments %}
  <div class="card border-0 shadow-sm">
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead style="background:#f8fafc;">
            <tr>
              <th class="px-4 py-3">الإدارة / القسم</th>
              <th>الإدارة الأم</th>
              <th>الكود</th>
              <th>الحالة</th>
              <th class="text-center">إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {% for dept in departments %}
            <tr>
              <td class="px-4">
                <div class="d-flex align-items-center gap-2">
                  {% if dept.parent %}
                    <span style="color:#d1d5db;">└─</span>
                  {% endif %}
                  <div class="rounded-circle d-flex align-items-center justify-content-center"
                       style="width:36px;height:36px;background:#e0f7fa;flex-shrink:0;">
                    <i class="bi bi-{% if dept.parent %}folder2{% else %}diagram-3{% endif %}"
                       style="color:#06B6D4;"></i>
                  </div>
                  <div>
                    <div class="fw-semibold">{{ dept.name_ar }}</div>
                    {% if dept.name_en %}
                      <small class="text-muted" dir="ltr">{{ dept.name_en }}</small>
                    {% endif %}
                  </div>
                </div>
              </td>
              <td>
                {% if dept.parent %}
                  <span class="badge bg-light text-dark">{{ dept.parent.name_ar }}</span>
                {% else %}
                  <span class="text-muted small">—</span>
                {% endif %}
              </td>
              <td>
                {% if dept.code %}
                  <code class="bg-light px-2 py-1 rounded">{{ dept.code }}</code>
                {% else %}
                  <span class="text-muted">—</span>
                {% endif %}
              </td>
              <td>
                {% if dept.is_active %}
                  <span class="badge bg-success">نشط</span>
                {% else %}
                  <span class="badge bg-danger">موقوف</span>
                {% endif %}
              </td>
              <td class="text-center">
                <a href="{% url 'companies:department_edit' dept.pk %}"
                   class="btn btn-sm btn-outline-primary me-1">
                  <i class="bi bi-pencil"></i>
                </a>
                <form method="post"
                      action="{% url 'companies:department_delete' dept.pk %}"
                      class="d-inline"
                      onsubmit="return confirm('حذف {{ dept.name_ar }}؟')">
                  {% csrf_token %}
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
    </div>
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-diagram-3" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد إدارات بعد</h5>
      <a href="{% url 'companies:department_add' %}"
         class="btn mt-2 text-white"
         style="background:#06B6D4;">
        <i class="bi bi-plus me-1"></i>أضف أول إدارة
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'departments_list.html'),
    departments_list_template
)


# ════════════════════════════════════════════════════════════
# 8. إنشاء Template: companies/department_form.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/department_form.html...")

department_form_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'companies:departments_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">{{ page_title }}</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-7">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الاسم (عربي) <span class="text-danger">*</span></label>
                <input type="text" name="name_ar" class="form-control"
                       value="{{ dept.name_ar|default:'' }}" required>
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الاسم (إنجليزي)</label>
                <input type="text" name="name_en" class="form-control"
                       value="{{ dept.name_en|default:'' }}" dir="ltr">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الكود</label>
                <input type="text" name="code" class="form-control"
                       value="{{ dept.code|default:'' }}" dir="ltr"
                       placeholder="مثال: HR, FIN, IT">
              </div>

              <div class="col-md-6">
                <label class="form-label fw-semibold small">الإدارة الأم</label>
                <select name="parent" class="form-select">
                  <option value="">— لا يوجد (إدارة رئيسية) —</option>
                  {% for d in departments %}
                  <option value="{{ d.pk }}"
                    {% if dept.parent.pk == d.pk %}selected{% endif %}>
                    {{ d.name_ar }}
                  </option>
                  {% endfor %}
                </select>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">الوصف</label>
                <textarea name="description" class="form-control" rows="3">{{ dept.description|default:'' }}</textarea>
              </div>

              {% if action == 'edit' %}
              <div class="col-12">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox"
                         name="is_active" id="isActive"
                         {% if dept.is_active %}checked{% endif %}
                         style="width:2.5rem;height:1.25rem;">
                  <label class="form-check-label fw-semibold" for="isActive">
                    الإدارة نشطة
                  </label>
                </div>
              </div>
              {% endif %}

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit"
                      class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة{% else %}حفظ{% endif %}
              </button>
              <a href="{% url 'companies:departments_list' %}"
                 class="btn btn-outline-secondary px-4"
                 style="border-radius:10px;">إلغاء</a>
            </div>

          </form>
        </div>
      </div>
    </div>
  </div>

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'department_form.html'),
    department_form_template
)


# ════════════════════════════════════════════════════════════
# 9. إنشاء Template: companies/shifts_list.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/shifts_list.html...")

shifts_list_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}الشيفتات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-clock me-2" style="color:#06B6D4;"></i>
        الشيفتات
      </h4>
      <p class="text-muted mb-0">جداول العمل المتاحة</p>
    </div>
    <a href="{% url 'companies:shift_add' %}"
       class="btn text-white"
       style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i>
      شيفت جديد
    </a>
  </div>

  {% if shifts %}
  <div class="row g-3">
    {% for shift in shifts %}
    <div class="col-md-6 col-lg-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">

          <div class="d-flex align-items-center gap-3 mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center"
                 style="width:48px;height:48px;background:#e0f7fa;">
              <i class="bi bi-clock-fill" style="color:#06B6D4; font-size:1.2rem;"></i>
            </div>
            <div>
              <h6 class="fw-bold mb-0">{{ shift.name }}</h6>
              <small class="text-muted">
                {% if shift.shift_type == 'fixed' %}ثابت
                {% elif shift.shift_type == 'flexible' %}مرن
                {% else %}متناوب{% endif %}
              </small>
            </div>
          </div>

          <!-- أوقات العمل -->
          <div class="d-flex justify-content-between align-items-center mb-3 p-2 rounded"
               style="background:#f8fafc;">
            <div class="text-center">
              <div class="fw-bold" style="color:#06B6D4;">{{ shift.start_time|time:"H:i" }}</div>
              <small class="text-muted">بداية</small>
            </div>
            <i class="bi bi-arrow-left text-muted"></i>
            <div class="text-center">
              <div class="fw-bold text-dark">{{ shift.work_hours }}س</div>
              <small class="text-muted">ساعات</small>
            </div>
            <i class="bi bi-arrow-left text-muted"></i>
            <div class="text-center">
              <div class="fw-bold" style="color:#06B6D4;">{{ shift.end_time|time:"H:i" }}</div>
              <small class="text-muted">نهاية</small>
            </div>
          </div>

          <!-- أيام العمل -->
          <div class="d-flex gap-1 flex-wrap mb-3">
            {% if shift.work_sunday %}
              <span class="badge bg-light text-dark border">أحد</span>
            {% endif %}
            {% if shift.work_monday %}
              <span class="badge bg-light text-dark border">اثن</span>
            {% endif %}
            {% if shift.work_tuesday %}
              <span class="badge bg-light text-dark border">ثلا</span>
            {% endif %}
            {% if shift.work_wednesday %}
              <span class="badge bg-light text-dark border">أرب</span>
            {% endif %}
            {% if shift.work_thursday %}
              <span class="badge bg-light text-dark border">خمي</span>
            {% endif %}
            {% if shift.work_friday %}
              <span class="badge bg-warning text-dark border">جمع</span>
            {% endif %}
            {% if shift.work_saturday %}
              <span class="badge bg-warning text-dark border">سبت</span>
            {% endif %}
          </div>

          <div class="d-flex gap-1 text-muted small mb-3">
            <span>سماح: {{ shift.grace_period }} دقيقة</span>
            <span>|</span>
            <span>استراحة: {{ shift.break_duration }} دقيقة</span>
          </div>

          <div class="d-flex gap-2 pt-3 border-top">
            <a href="{% url 'companies:shift_edit' shift.pk %}"
               class="btn btn-sm btn-outline-primary flex-fill">
              <i class="bi bi-pencil me-1"></i>تعديل
            </a>
            <form method="post"
                  action="{% url 'companies:shift_delete' shift.pk %}"
                  onsubmit="return confirm('حذف الشيفت؟')">
              {% csrf_token %}
              <button type="submit" class="btn btn-sm btn-outline-danger">
                <i class="bi bi-trash"></i>
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-clock" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد شيفتات بعد</h5>
      <a href="{% url 'companies:shift_add' %}"
         class="btn mt-2 text-white"
         style="background:#06B6D4;">
        <i class="bi bi-plus me-1"></i>أضف أول شيفت
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'shifts_list.html'),
    shifts_list_template
)


# ════════════════════════════════════════════════════════════
# 10. إنشاء Template: companies/shift_form.html
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء templates/companies/shift_form.html...")

shift_form_template = r"""{% extends 'base/dashboard_base.html' %}
{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'companies:shifts_list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">{{ page_title }}</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <!-- اسم الشيفت -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">اسم الشيفت <span class="text-danger">*</span></label>
                <input type="text" name="name" class="form-control"
                       value="{{ shift.name|default:'' }}" required
                       placeholder="مثال: صباحي، مسائي...">
              </div>

              <!-- نوع الشيفت -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">النوع</label>
                <select name="shift_type" class="form-select">
                  <option value="fixed"
                    {% if shift.shift_type == 'fixed' or not shift %}selected{% endif %}>
                    ثابت
                  </option>
                  <option value="flexible"
                    {% if shift.shift_type == 'flexible' %}selected{% endif %}>
                    مرن
                  </option>
                  <option value="rotating"
                    {% if shift.shift_type == 'rotating' %}selected{% endif %}>
                    متناوب
                  </option>
                </select>
              </div>

              <!-- وقت البداية -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">وقت البداية</label>
                <input type="time" name="start_time" class="form-control"
                       value="{{ shift.start_time|time:'H:i'|default:'08:00' }}">
              </div>

              <!-- وقت النهاية -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">وقت النهاية</label>
                <input type="time" name="end_time" class="form-control"
                       value="{{ shift.end_time|time:'H:i'|default:'17:00' }}">
              </div>

              <!-- فترة السماح -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  فترة السماح (دقيقة)
                  <small class="text-muted fw-normal">— تأخير مسموح به</small>
                </label>
                <input type="number" name="grace_period" class="form-control"
                       value="{{ shift.grace_period|default:15 }}"
                       min="0" max="60">
              </div>

              <!-- وقت الاستراحة -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  وقت الاستراحة (دقيقة)
                </label>
                <input type="number" name="break_duration" class="form-control"
                       value="{{ shift.break_duration|default:60 }}"
                       min="0" max="180">
              </div>

              <!-- أيام العمل -->
              <div class="col-12">
                <label class="form-label fw-semibold small">أيام العمل</label>
                <div class="d-flex flex-wrap gap-2">

                  {% for day_field, day_label, day_color in days %}
                  <div class="form-check" style="min-width:80px;">
                    <input class="form-check-input day-check" type="checkbox"
                           name="{{ day_field }}" id="{{ day_field }}"
                           {% if shift and shift|getattr:day_field %}checked{% endif %}
                           {% if not shift and day_label not in 'الجمعة,السبت' %}checked{% endif %}>
                    <label class="form-check-label" for="{{ day_field }}">
                      {{ day_label }}
                    </label>
                  </div>
                  {% endfor %}

                </div>
                <small class="text-muted">اختر أيام العمل في هذا الشيفت</small>
              </div>

            </div>

            <div class="d-flex gap-2 mt-4 pt-3 border-top">
              <button type="submit"
                      class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                {% if action == 'add' %}إضافة الشيفت{% else %}حفظ التغييرات{% endif %}
              </button>
              <a href="{% url 'companies:shifts_list' %}"
                 class="btn btn-outline-secondary px-4"
                 style="border-radius:10px;">إلغاء</a>
            </div>

          </form>
        </div>
      </div>
    </div>
  </div>

</div>
{% endblock %}
"""

create_file(
    os.path.join(BASE_DIR, 'templates', 'companies', 'shift_form.html'),
    shift_form_template
)


# ════════════════════════════════════════════════════════════
# 11. إضافة context لـ shift_form view (أيام العمل)
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث shift_add و shift_edit context...")

companies_views_path = os.path.join(BASE_DIR, 'companies', 'views.py')
views_content = read_file(companies_views_path)

days_context = """
WORK_DAYS = [
    ('work_sunday',    'الأحد',    'primary'),
    ('work_monday',    'الاثنين',  'primary'),
    ('work_tuesday',   'الثلاثاء', 'primary'),
    ('work_wednesday', 'الأربعاء', 'primary'),
    ('work_thursday',  'الخميس',  'primary'),
    ('work_friday',    'الجمعة',   'warning'),
    ('work_saturday',  'السبت',    'warning'),
]
"""

if 'WORK_DAYS' not in views_content:
    views_content = days_context + '\n' + views_content
    # تحديث context في shift_add
    views_content = views_content.replace(
        "    context = {\n        'page_title': 'إضافة شيفت جديد',\n        'action':     'add',\n    }\n    return render(request, 'companies/shift_form.html', context)",
        "    context = {\n        'page_title': 'إضافة شيفت جديد',\n        'action':     'add',\n        'days':       WORK_DAYS,\n    }\n    return render(request, 'companies/shift_form.html', context)"
    )
    # تحديث context في shift_edit
    views_content = views_content.replace(
        "    context = {\n        'shift':      shift,\n        'page_title': f'تعديل: {shift.name}',\n        'action':     'edit',\n    }\n    return render(request, 'companies/shift_form.html', context)",
        "    context = {\n        'shift':      shift,\n        'page_title': f'تعديل: {shift.name}',\n        'action':     'edit',\n        'days':       WORK_DAYS,\n    }\n    return render(request, 'companies/shift_form.html', context)"
    )
    write_file(companies_views_path, views_content)
else:
    print("  ℹ️  WORK_DAYS موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 12. تحديث الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
sidebar_content = read_file(sidebar_path)

if 'companies:settings' not in sidebar_content:
    company_links = """
                <!-- ══ الشركة ══ -->
                <li class="nav-item mt-3">
                  <div class="px-3 mb-1">
                    <small style="color:rgba(255,255,255,0.35);
                                  font-size:0.7rem;
                                  letter-spacing:1px;
                                  text-transform:uppercase;">
                      إعدادات الشركة
                    </small>
                  </div>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'companies:settings' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-building"></i>
                    <span>الشركة</span>
                  </a>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'companies:branches_list' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-geo-alt"></i>
                    <span>الفروع</span>
                  </a>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'companies:departments_list' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-diagram-3"></i>
                    <span>الإدارات</span>
                  </a>
                </li>
                <li class="nav-item">
                  <a class="nav-link d-flex align-items-center gap-2 py-2 px-3"
                     href="{% url 'companies:shifts_list' %}"
                     style="color:rgba(255,255,255,0.7); border-radius:8px;">
                    <i class="bi bi-clock"></i>
                    <span>الشيفتات</span>
                  </a>
                </li>"""

    # نضيف قبل إعدادات الدخول
    if 'accounts:login_settings' in sidebar_content:
        login_settings_idx = sidebar_content.find("{% url 'accounts:login_settings' %}")
        li_start = sidebar_content.rfind('<li', 0, login_settings_idx)
        sidebar_content = (
            sidebar_content[:li_start] +
            company_links + '\n' +
            sidebar_content[li_start:]
        )
        write_file(sidebar_path, sidebar_content)
        print("  ✅ تم إضافة روابط الشركة في الـ Sidebar")
    else:
        print("  ⚠️  مش لاقي مكان مناسب")
else:
    print("  ℹ️  روابط الشركة موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 17 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ motionhr/urls.py - نظيف ونهائي
  2.  ✅ companies/urls.py
  3.  ✅ companies/views.py
  4.  ✅ settings.html - إعدادات الشركة
  5.  ✅ branches_list.html - قائمة الفروع
  6.  ✅ branch_form.html - إضافة/تعديل فرع + GPS
  7.  ✅ departments_list.html - قائمة الإدارات
  8.  ✅ department_form.html - إضافة/تعديل إدارة
  9.  ✅ shifts_list.html - قائمة الشيفتات
  10. ✅ shift_form.html - إضافة/تعديل شيفت
  11. ✅ Sidebar - روابط الشركة

🔗 URLs الجديدة:
  /companies/settings/          ← إعدادات الشركة
  /companies/branches/          ← الفروع
  /companies/departments/       ← الإدارات
  /companies/shifts/            ← الشيفتات

🚀 الخطوة الجاية: Patch 18 - نظام الإجازات
""")