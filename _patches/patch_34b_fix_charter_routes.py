#!/usr/bin/env python3
"""
Patch 34b: Fix Charter Routes
=============================
- يثبت views الميثاق
- يعيد كتابة companies/urls.py بشكل نظيف
- يتأكد إن الـ Sidebar بيستخدم namespace الصحيح
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def append_file(path, content):
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")


print("=" * 60)
print("  Patch 34b: Fix Charter Routes")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# 1) تأكيد وجود Views الميثاق
# ════════════════════════════════════════════════════════════
print("\n🔧 فحص companies/views.py...")

views_path = os.path.join(BASE_DIR, "companies", "views.py")
views = read_file(views_path)

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
            company=company,
            is_active=True
        ).first()

        employee = Employee.objects.filter(user=request.user).first()

        if charter and employee:
            accepted = CharterAcceptance.objects.filter(
                employee=employee,
                charter=charter
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
        company=company,
        is_active=True
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
        messages.error(request, "حدث خطأ أثناء تسجيل الموافقة")

    return redirect("dashboard")


@login_required
def charter_manage(request):
    """إدارة ميثاق العمل (للإدارة فقط)"""
    from .models import WorkCharter, CharterAcceptance
    from employees.models import Employee

    company = request.user.company
    charter = None
    acceptances = []
    total_employees = 0
    accepted_count = 0

    if company:
        charter, _ = WorkCharter.objects.get_or_create(
            company=company,
            defaults={
                "title": "ميثاق العمل",
                "introduction": "نرحب بانضمامك لفريق العمل. يرجى قراءة الميثاق والموافقة عليه.",
                "content": _default_charter_content(),
                "version": 1,
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
            company=company,
            status="active"
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

if "def charter_view" not in views:
    views += charter_views
    write_file(views_path, views)
    print("  ✅ تم إضافة Views الميثاق")
else:
    print("  ℹ️  Views الميثاق موجودة بالفعل")

# ════════════════════════════════════════════════════════════
# 2) إعادة كتابة companies/urls.py بشكل نظيف
# ════════════════════════════════════════════════════════════
print("\n🔧 إعادة كتابة companies/urls.py...")

companies_urls = """from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [

    # الشركة
    path('settings/', views.company_settings, name='settings'),

    # ميثاق العمل
    path('charter/', views.charter_view, name='charter'),
    path('charter/accept/', views.charter_accept, name='charter_accept'),
    path('charter/manage/', views.charter_manage, name='charter_manage'),

    # الفروع
    path('branches/', views.branches_list, name='branches_list'),
    path('branches/add/', views.branch_add, name='branch_add'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),

    # الإدارات
    path('departments/', views.departments_list, name='departments_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    # الشيفتات
    path('shifts/', views.shifts_list, name='shifts_list'),
    path('shifts/add/', views.shift_add, name='shift_add'),
    path('shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'),
    path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),
]
"""

urls_path = os.path.join(BASE_DIR, "companies", "urls.py")
write_file(urls_path, companies_urls)

# ════════════════════════════════════════════════════════════
# 3) تأكيد الـ Sidebar
# ════════════════════════════════════════════════════════════
print("\n🔧 فحص dashboard_base.html...")

sidebar_path = os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html")
sidebar = read_file(sidebar_path)

# تأكيد استخدام namespace
sidebar = sidebar.replace("{% url 'charter' %}", "{% url 'companies:charter' %}")
sidebar = sidebar.replace("{% url 'charter_manage' %}", "{% url 'companies:charter_manage' %}")

write_file(sidebar_path, sidebar)
print("  ✅ تم تأكيد namespace الصحيح")

print("\n" + "=" * 60)
print("  ✅ Patch 34b اكتمل!")
print("=" * 60)
print("""
جرب دلوقتي:
1) python manage.py check
2) python manage.py runserver 0.0.0.0:8000
3) افتح /dashboard/
4) employee → /companies/charter/
5) admin → /companies/charter/manage/
""")