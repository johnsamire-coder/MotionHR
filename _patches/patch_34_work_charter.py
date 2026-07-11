#!/usr/bin/env python3
"""
Patch 34: Work Charter (ميثاق العمل)
======================================
1. Model للميثاق (واحد لكل شركة + قابل للتعديل)
2. Model لتسجيل موافقة الموظف
3. Middleware إجبار الموافقة أول دخول
4. صفحة عرض الميثاق والموافقة
5. صفحة الميثاق في ملف الموظف
6. صفحة إدارة الميثاق لصاحب الشركة
7. بنود افتراضية
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 34: Work Charter")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إضافة Models في companies/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة نماذج ميثاق العمل...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

charter_models = '''

# ════════════════════════════════════════════════════════════
# ميثاق العمل
# ════════════════════════════════════════════════════════════
class WorkCharter(models.Model):
    """ميثاق العمل — مستند واحد لكل شركة"""

    company = models.OneToOneField(
        "Company",
        on_delete=models.CASCADE,
        related_name="work_charter",
        verbose_name="الشركة"
    )
    title = models.CharField(
        max_length=200,
        default="ميثاق العمل",
        verbose_name="العنوان"
    )
    introduction = models.TextField(
        blank=True,
        verbose_name="مقدمة",
        help_text="نص تمهيدي يظهر قبل البنود"
    )
    content = models.TextField(
        verbose_name="محتوى الميثاق",
        help_text="البنود الكاملة للميثاق"
    )
    version = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="رقم الإصدار"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="مفعّل"
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name="إجباري للموظفين الجدد"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ميثاق العمل"
        verbose_name_plural = "مواثيق العمل"

    def __str__(self):
        return f"{self.title} - {self.company.name_ar} (v{self.version})"


class CharterAcceptance(models.Model):
    """تسجيل موافقة الموظف على الميثاق"""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="charter_acceptances",
        verbose_name="الموظف"
    )
    charter = models.ForeignKey(
        WorkCharter,
        on_delete=models.CASCADE,
        related_name="acceptances",
        verbose_name="الميثاق"
    )
    accepted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الموافقة"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="عنوان IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="المتصفح"
    )

    class Meta:
        verbose_name = "موافقة على الميثاق"
        verbose_name_plural = "موافقات الميثاق"
        unique_together = [["employee", "charter"]]

    def __str__(self):
        return f"{self.employee} وافق على {self.charter.title}"
'''

if "class WorkCharter" not in comp_models:
    comp_models += charter_models
    write_file(comp_models_path, comp_models)
    print("  ✅ تم إضافة WorkCharter + CharterAcceptance")
else:
    print("  ℹ️  موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2. Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

import django
django.setup()

from django.core.management import call_command
call_command("makemigrations", "companies")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 3. Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 Admin...")

admin_path = os.path.join(BASE_DIR, "companies", "admin.py")
admin_content = read_file(admin_path)

if "WorkCharter" not in admin_content:
    admin_content += '''
from .models import WorkCharter, CharterAcceptance

@admin.register(WorkCharter)
class WorkCharterAdmin(admin.ModelAdmin):
    list_display = ["company", "title", "version", "is_active", "is_mandatory"]

@admin.register(CharterAcceptance)
class CharterAcceptanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "charter", "accepted_at"]
'''
    write_file(admin_path, admin_content)


# ════════════════════════════════════════════════════════════
# 4. Views
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Views...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

charter_views = '''

# ════════════════════════════════════════════════════════════
# ميثاق العمل
# ════════════════════════════════════════════════════════════

@login_required
def charter_view(request):
    """عرض ميثاق العمل للموظف"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    company = request.user.company
    charter = None
    accepted = False
    employee = None

    if company:
        charter = WorkCharter.objects.filter(
            company=company, is_active=True
        ).first()

        employee = Employee.objects.filter(user=request.user).first()

        if charter and employee:
            accepted = CharterAcceptance.objects.filter(
                employee=employee, charter=charter
            ).exists()

    context = {
        "charter": charter,
        "accepted": accepted,
        "employee": employee,
        "page_title": "ميثاق العمل",
    }
    return render(request, "companies/charter_view.html", context)


@login_required
def charter_accept(request):
    """الموظف يوافق على الميثاق"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    if request.method != "POST":
        return redirect("companies:charter")

    company = request.user.company
    charter = WorkCharter.objects.filter(
        company=company, is_active=True
    ).first()

    employee = Employee.objects.filter(user=request.user).first()

    if charter and employee:
        CharterAcceptance.objects.get_or_create(
            employee=employee,
            charter=charter,
            defaults={
                "ip_address": request.META.get("REMOTE_ADDR", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
            }
        )
        messages.success(request, "تم تسجيل موافقتك على ميثاق العمل بنجاح")
    else:
        messages.error(request, "حدث خطأ")

    return redirect("dashboard")


@login_required
def charter_manage(request):
    """إدارة ميثاق العمل (لصاحب الشركة / HR)"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    company = request.user.company
    charter = None
    acceptances = []
    total_employees = 0
    accepted_count = 0

    if company:
        charter, created = WorkCharter.objects.get_or_create(
            company=company,
            defaults={
                "title": "ميثاق العمل",
                "content": _default_charter_content(),
                "introduction": "نرحب بانضمامك لفريق عملنا. يرجى قراءة ميثاق العمل التالي والموافقة عليه.",
                "is_active": True,
                "is_mandatory": True,
            }
        )

        if request.method == "POST":
            charter.title = request.POST.get("title", charter.title)
            charter.introduction = request.POST.get("introduction", "")
            charter.content = request.POST.get("content", charter.content)
            charter.is_active = "is_active" in request.POST
            charter.is_mandatory = "is_mandatory" in request.POST

            if "new_version" in request.POST:
                charter.version += 1

            charter.save()
            messages.success(request, "تم حفظ ميثاق العمل بنجاح")
            return redirect("companies:charter_manage")

        total_employees = Employee.objects.filter(
            company=company, status="active"
        ).count()

        acceptances = CharterAcceptance.objects.filter(
            charter=charter
        ).select_related("employee").order_by("-accepted_at")

        accepted_count = acceptances.count()

    context = {
        "charter": charter,
        "acceptances": acceptances,
        "total_employees": total_employees,
        "accepted_count": accepted_count,
        "not_accepted": total_employees - accepted_count,
        "page_title": "إدارة ميثاق العمل",
    }
    return render(request, "companies/charter_manage.html", context)


def _default_charter_content():
    return """1. الالتزام بمواعيد العمل الرسمية والحضور والانصراف في الأوقات المحددة.

2. الحفاظ على سرية بيانات الشركة والعملاء وعدم إفشائها لأي طرف خارجي.

3. احترام بيئة العمل والزملاء والتعامل بمهنية في جميع الأوقات.

4. عدم استخدام ممتلكات الشركة أو مواردها لأغراض شخصية.

5. الالتزام بسياسة الإجازات المعتمدة وتقديم الطلبات في الوقت المناسب.

6. الحفاظ على المظهر اللائق والالتزام بقواعد اللباس المعتمدة.

7. الإبلاغ الفوري عن أي مخالفات أو سلوكيات غير مقبولة.

8. الالتزام بقواعد السلامة والصحة المهنية.

9. عدم ممارسة أي عمل يتعارض مع مصالح الشركة.

10. الالتزام بالقوانين واللوائح المعمول بها في الشركة والدولة."""
'''

if "def charter_view" not in comp_views:
    comp_views += charter_views
    write_file(comp_views_path, comp_views)
    print("  ✅ تم إضافة charter views")
else:
    print("  ℹ️  charter views موجودة")


# ════════════════════════════════════════════════════════════
# 5. URLs
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/urls.py...")

urls_path = os.path.join(BASE_DIR, "companies", "urls.py")
urls = read_file(urls_path)

if "charter" not in urls:
    urls = urls.rstrip()
    if urls.endswith("]"):
        urls = urls[:-1]
        urls += "\n    # ميثاق العمل\n"
        urls += "    path('charter/', views.charter_view, name='charter'),\n"
        urls += "    path('charter/accept/', views.charter_accept, name='charter_accept'),\n"
        urls += "    path('charter/manage/', views.charter_manage, name='charter_manage'),\n"
        urls += "]\n"
        write_file(urls_path, urls)
        print("  ✅ URLs محدثة")
else:
    print("  ℹ️  URLs موجودة")


# ════════════════════════════════════════════════════════════
# 6. Template — عرض الميثاق للموظف
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء charter_view.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "companies", "charter_view.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}ميثاق العمل{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="row justify-content-center">
    <div class="col-lg-8">

      {% if charter %}

      <!-- العنوان -->
      <div class="text-center mb-4">
        <div class="rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
             style="width:70px; height:70px; background:#e0f7fa;">
          <i class="bi bi-file-earmark-text-fill" style="font-size:2rem; color:#06B6D4;"></i>
        </div>
        <h4 class="fw-bold">{{ charter.title }}</h4>
        <small class="text-muted">الإصدار {{ charter.version }}</small>
      </div>

      <!-- حالة الموافقة -->
      {% if accepted %}
      <div class="alert border-0 shadow-sm mb-4"
           style="background:#e8f5e9; border-radius:12px;">
        <div class="d-flex align-items-center gap-2">
          <i class="bi bi-check-circle-fill text-success fs-4"></i>
          <div>
            <strong class="text-success">تمت الموافقة</strong>
            <div class="text-muted small">لقد وافقت على ميثاق العمل بالفعل</div>
          </div>
        </div>
      </div>
      {% endif %}

      <!-- الميثاق -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body p-4">

          {% if charter.introduction %}
          <div class="p-3 mb-4 rounded" style="background:#f0f9ff; border-right:4px solid #06B6D4;">
            <p class="mb-0">{{ charter.introduction }}</p>
          </div>
          {% endif %}

          <div class="charter-content" style="line-height:2; font-size:1rem;">
            {{ charter.content|linebreaksbr }}
          </div>

        </div>
      </div>

      <!-- زرار الموافقة -->
      {% if not accepted and employee %}
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4 text-center">
          <p class="mb-3 fw-semibold">
            بالضغط على "أوافق" أنت تؤكد أنك قرأت ميثاق العمل وتوافق على جميع بنوده.
          </p>
          <form method="post" action="{% url 'companies:charter_accept' %}">
            {% csrf_token %}
            <div class="form-check d-flex align-items-center justify-content-center gap-2 mb-3">
              <input class="form-check-input" type="checkbox"
                     id="agreeCheck" required
                     style="width:1.3rem; height:1.3rem;">
              <label class="form-check-label fw-semibold" for="agreeCheck">
                قرأت ميثاق العمل وأوافق على جميع البنود
              </label>
            </div>
            <button type="submit" class="btn btn-lg text-white fw-bold px-5"
                    style="background:#06B6D4; border-radius:12px;">
              <i class="bi bi-check-lg me-2"></i>
              أوافق على الميثاق
            </button>
          </form>
        </div>
      </div>
      {% endif %}

      {% else %}
      <div class="card border-0 shadow-sm">
        <div class="card-body text-center py-5">
          <i class="bi bi-file-earmark-x" style="font-size:4rem; color:#d1d5db;"></i>
          <h5 class="mt-3 fw-bold text-muted">لا يوجد ميثاق عمل بعد</h5>
        </div>
      </div>
      {% endif %}

    </div>
  </div>
</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 7. Template — إدارة الميثاق
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء charter_manage.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "companies", "charter_manage.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}إدارة ميثاق العمل{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-file-earmark-text me-2" style="color:#06B6D4;"></i>
        إدارة ميثاق العمل
      </h4>
      <p class="text-muted mb-0">عدّل بنود الميثاق وتابع موافقات الموظفين</p>
    </div>
  </div>

  <div class="row g-4">

    <!-- إحصائيات -->
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm mb-3">
        <div class="card-body p-4 text-center">
          <div class="row g-2">
            <div class="col-4">
              <div class="fs-3 fw-bold" style="color:#06B6D4;">{{ total_employees }}</div>
              <small class="text-muted">إجمالي</small>
            </div>
            <div class="col-4">
              <div class="fs-3 fw-bold text-success">{{ accepted_count }}</div>
              <small class="text-muted">وافقوا</small>
            </div>
            <div class="col-4">
              <div class="fs-3 fw-bold text-danger">{{ not_accepted }}</div>
              <small class="text-muted">لم يوافقوا</small>
            </div>
          </div>
        </div>
      </div>

      <!-- قائمة الموافقات -->
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h6 class="fw-bold mb-0">الموافقات</h6>
        </div>
        <div class="card-body p-0">
          {% if acceptances %}
          <div class="table-responsive">
            <table class="table table-sm table-hover mb-0">
              <tbody>
                {% for acc in acceptances %}
                <tr>
                  <td class="px-4 py-2">
                    <div class="fw-semibold small">
                      {{ acc.employee.full_name_ar }}
                    </div>
                    <small class="text-muted">
                      {{ acc.accepted_at|date:"d/m/Y H:i" }}
                    </small>
                  </td>
                  <td class="text-end pe-4">
                    <i class="bi bi-check-circle-fill text-success"></i>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          {% else %}
          <div class="text-center py-4 text-muted small">
            لا يوجد موافقات بعد
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- تعديل الميثاق -->
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post">
            {% csrf_token %}
            <div class="row g-3">

              <div class="col-md-8">
                <label class="form-label fw-semibold small">
                  العنوان <span class="text-danger">*</span>
                </label>
                <input type="text" name="title" class="form-control"
                       value="{{ charter.title }}" required>
              </div>

              <div class="col-md-4">
                <label class="form-label fw-semibold small">الإصدار</label>
                <div class="d-flex align-items-center gap-2">
                  <input type="text" class="form-control bg-light" readonly
                         value="v{{ charter.version }}">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox"
                           name="new_version" id="newVersion">
                    <label class="form-check-label small" for="newVersion">
                      إصدار جديد
                    </label>
                  </div>
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">المقدمة</label>
                <textarea name="introduction" class="form-control" rows="2"
                          placeholder="نص تمهيدي اختياري...">{{ charter.introduction }}</textarea>
              </div>

              <div class="col-12">
                <label class="form-label fw-semibold small">
                  بنود الميثاق <span class="text-danger">*</span>
                </label>
                <textarea name="content" class="form-control" rows="14"
                          required style="line-height:1.8;">{{ charter.content }}</textarea>
                <small class="text-muted">
                  اكتب كل بند في سطر مستقل
                </small>
              </div>

              <div class="col-md-6">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox"
                         name="is_active" id="isActive"
                         {% if charter.is_active %}checked{% endif %}
                         style="width:2.5rem; height:1.25rem;">
                  <label class="form-check-label fw-semibold" for="isActive">
                    الميثاق مفعّل
                  </label>
                </div>
              </div>

              <div class="col-md-6">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox"
                         name="is_mandatory" id="isMandatory"
                         {% if charter.is_mandatory %}checked{% endif %}
                         style="width:2.5rem; height:1.25rem;">
                  <label class="form-check-label fw-semibold" for="isMandatory">
                    إجباري للموظفين الجدد
                  </label>
                </div>
              </div>

            </div>

            <div class="mt-4 pt-3 border-top">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                حفظ التغييرات
              </button>
            </div>

          </form>
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 8. Middleware — إجبار الموافقة
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Charter Middleware...")

middleware_path = os.path.join(BASE_DIR, "core", "middleware.py")
middleware = read_file(middleware_path)

charter_middleware = '''

class CharterMiddleware:
    """
    لو الميثاق إجباري والموظف ما وافقش
    يتحول لصفحة الميثاق تلقائيًا
    """

    EXEMPT_URLS = [
        '/login/',
        '/logout/',
        '/admin/',
        '/password-change/',
        '/password-reset/',
        '/companies/charter/',
        '/static/',
        '/media/',
        '/manifest.json',
        '/sw.js',
        '/offline/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role == 'employee'
            and hasattr(request.user, 'company')
            and request.user.company
            and not request.user.is_superuser
        ):
            path = request.path_info
            exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)

            if not exempt:
                try:
                    from companies.models import WorkCharter, CharterAcceptance
                    from employees.models import Employee

                    charter = WorkCharter.objects.filter(
                        company=request.user.company,
                        is_active=True,
                        is_mandatory=True,
                    ).first()

                    if charter:
                        employee = Employee.objects.filter(
                            user=request.user
                        ).first()

                        if employee:
                            accepted = CharterAcceptance.objects.filter(
                                employee=employee,
                                charter=charter,
                            ).exists()

                            if not accepted:
                                from django.shortcuts import redirect
                                return redirect('/companies/charter/')
                except Exception:
                    pass

        return self.get_response(request)
'''

if "class CharterMiddleware" not in middleware:
    middleware += charter_middleware
    write_file(middleware_path, middleware)
    print("  ✅ تم إضافة CharterMiddleware")
else:
    print("  ℹ️  CharterMiddleware موجود")

# إضافة في settings.py
settings_path = os.path.join(BASE_DIR, "motionhr", "settings.py")
settings = read_file(settings_path)

if "CharterMiddleware" not in settings:
    settings = settings.replace(
        "'accounts.middleware.ForcePasswordChangeMiddleware',",
        "'accounts.middleware.ForcePasswordChangeMiddleware',\n    'core.middleware.CharterMiddleware',"
    )
    write_file(settings_path, settings)
    print("  ✅ تم إضافة CharterMiddleware في settings")
else:
    print("  ℹ️  CharterMiddleware في settings موجود")


# ════════════════════════════════════════════════════════════
# 9. تحديث الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث الـ Sidebar...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# إضافة رابط ميثاق العمل للموظف
if "companies:charter" not in sidebar:
    old_profile = """    <!-- حسابي -->
    <div class="sidebar-label">حسابي</div>
    <a href="{% url 'accounts:profile' %}"
       class="nav-link {% if 'profile' in request.path %}active{% endif %}">
      <i class="bi bi-person-circle"></i><span>الملف الشخصي</span>
    </a>"""

    new_profile = """    <!-- حسابي -->
    <div class="sidebar-label">حسابي</div>
    <a href="{% url 'companies:charter' %}"
       class="nav-link {% if 'charter' in request.path and 'manage' not in request.path %}active{% endif %}">
      <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
    </a>
    <a href="{% url 'accounts:profile' %}"
       class="nav-link {% if 'profile' in request.path %}active{% endif %}">
      <i class="bi bi-person-circle"></i><span>الملف الشخصي</span>
    </a>"""

    if old_profile in sidebar:
        sidebar = sidebar.replace(old_profile, new_profile)

    # إضافة إدارة الميثاق لصاحب الشركة
    old_company = """    <a href="{% url 'companies:shifts_list' %}"
       class="nav-link {% if 'shifts' in request.path %}active{% endif %}">
      <i class="bi bi-clock"></i><span>الشيفتات</span>
    </a>
    {% endif %}"""

    new_company = """    <a href="{% url 'companies:shifts_list' %}"
       class="nav-link {% if 'shifts' in request.path %}active{% endif %}">
      <i class="bi bi-clock"></i><span>الشيفتات</span>
    </a>
    <a href="{% url 'companies:charter_manage' %}"
       class="nav-link {% if 'charter/manage' in request.path %}active{% endif %}">
      <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
    </a>
    {% endif %}"""

    if old_company in sidebar:
        sidebar = sidebar.replace(old_company, new_company)

    write_file(sidebar_path, sidebar)
    print("  ✅ تم إضافة ميثاق العمل في الـ Sidebar")
else:
    print("  ℹ️  ميثاق العمل موجود في الـ Sidebar")


# ════════════════════════════════════════════════════════════
# 10. Seed Data — ميثاق افتراضي
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء ميثاق افتراضي...")

from companies.models import Company, WorkCharter

company = Company.objects.first()
if company:
    charter, created = WorkCharter.objects.get_or_create(
        company=company,
        defaults={
            "title": "ميثاق العمل",
            "introduction": "نرحب بانضمامك لفريق عملنا في شركة الاختبار. يرجى قراءة ميثاق العمل التالي بعناية والموافقة عليه قبل بدء العمل.",
            "content": """1. الالتزام بمواعيد العمل الرسمية والحضور والانصراف في الأوقات المحددة.

2. الحفاظ على سرية بيانات الشركة والعملاء وعدم إفشائها لأي طرف خارجي.

3. احترام بيئة العمل والزملاء والتعامل بمهنية في جميع الأوقات.

4. عدم استخدام ممتلكات الشركة أو مواردها لأغراض شخصية.

5. الالتزام بسياسة الإجازات المعتمدة وتقديم الطلبات في الوقت المناسب.

6. الحفاظ على المظهر اللائق والالتزام بقواعد اللباس المعتمدة.

7. الإبلاغ الفوري عن أي مخالفات أو سلوكيات غير مقبولة في بيئة العمل.

8. الالتزام بقواعد السلامة والصحة المهنية المعتمدة.

9. عدم ممارسة أي عمل خارجي يتعارض مع مصالح الشركة.

10. الالتزام بالقوانين واللوائح المعمول بها في الشركة وفي الدولة.""",
            "version": 1,
            "is_active": True,
            "is_mandatory": True,
        }
    )
    if created:
        print("  ✅ تم إنشاء ميثاق افتراضي")
    else:
        print("  ℹ️  ميثاق موجود بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 34 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1.  ✅ WorkCharter Model (ميثاق لكل شركة)
  2.  ✅ CharterAcceptance Model (موافقة الموظف)
  3.  ✅ Migration
  4.  ✅ Admin
  5.  ✅ charter_view — صفحة عرض الميثاق
  6.  ✅ charter_accept — الموافقة
  7.  ✅ charter_manage — إدارة الميثاق
  8.  ✅ CharterMiddleware — إجبار الموافقة
  9.  ✅ Sidebar محدث
  10. ✅ ميثاق افتراضي ببنود

جرب:
  1. emp10003 → أول ما يدخل يتحول لصفحة الميثاق
  2. يوافق → يدخل عادي
  3. demo_admin → يشوف "إدارة ميثاق العمل"
     يقدر يعدل البنود والعنوان
  4. الموظف يشوف "ميثاق العمل" في الـ Sidebar
""")