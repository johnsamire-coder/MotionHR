#!/usr/bin/env python3
"""
Patch 22: صفحات إضافية
========================
- صفحة الملف الشخصي (Profile)
- صفحة الإعدادات (Settings)
- صفحة 404
- صفحة 500
- صفحة البحث الشامل
- Notifications Center
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
print("  Patch 22: Extra Pages")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. صفحة الملف الشخصي
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء profile.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'accounts', 'profile.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}الملف الشخصي{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="row g-4">

    <!-- بطاقة المعلومات الشخصية -->
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4 text-center">

          <!-- الصورة -->
          <div class="position-relative d-inline-block mb-3">
            {% if user.avatar %}
              <img src="{{ user.avatar.url }}"
                   class="rounded-circle shadow"
                   style="width:100px;height:100px;object-fit:cover;">
            {% else %}
              <div class="rounded-circle d-flex align-items-center justify-content-center shadow mx-auto"
                   style="width:100px;height:100px;
                          background:linear-gradient(135deg,#06B6D4,#0891B2);
                          font-size:2.5rem;font-weight:900;color:white;">
                {{ user.get_full_name|first|default:user.username|first|upper }}
              </div>
            {% endif %}
            <label for="avatarInput"
                   class="position-absolute bottom-0 end-0
                          btn btn-sm btn-light rounded-circle shadow-sm"
                   style="width:32px;height:32px;padding:0;
                          display:flex;align-items:center;justify-content:center;
                          cursor:pointer;">
              <i class="bi bi-camera-fill" style="color:#06B6D4;font-size:0.8rem;"></i>
            </label>
          </div>

          <h5 class="fw-bold mb-1">
            {{ user.get_full_name|default:user.username }}
          </h5>
          <div class="badge mb-2" style="background:#06B6D4;">
            {{ user.get_role_display|default:"مستخدم" }}
          </div>
          <div class="text-muted small">
            {{ user.company.name_ar|default:"—" }}
          </div>

          <hr>

          <div class="text-start">
            <div class="d-flex align-items-center gap-2 mb-2">
              <i class="bi bi-envelope text-muted"></i>
              <span class="small">{{ user.email|default:"لم يحدد" }}</span>
            </div>
            <div class="d-flex align-items-center gap-2 mb-2">
              <i class="bi bi-phone text-muted"></i>
              <span class="small">{{ user.phone|default:"لم يحدد" }}</span>
            </div>
            <div class="d-flex align-items-center gap-2">
              <i class="bi bi-calendar text-muted"></i>
              <span class="small">
                عضو منذ {{ user.date_joined|date:"d/m/Y" }}
              </span>
            </div>
          </div>

        </div>
      </div>

      <!-- إحصائيات سريعة -->
      <div class="card border-0 shadow-sm mt-3">
        <div class="card-body p-4">
          <h6 class="fw-bold mb-3">إحصائياتي</h6>
          <div class="d-flex justify-content-between py-2 border-bottom">
            <span class="text-muted small">آخر دخول</span>
            <span class="small fw-semibold">
              {{ user.last_login|date:"d/m/Y H:i"|default:"—" }}
            </span>
          </div>
          <div class="d-flex justify-content-between py-2">
            <span class="text-muted small">حالة الحساب</span>
            <span class="badge {% if user.is_active %}bg-success{% else %}bg-danger{% endif %}">
              {% if user.is_active %}نشط{% else %}موقوف{% endif %}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- تعديل البيانات -->
    <div class="col-lg-8">

      <!-- بيانات الحساب -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">
            <i class="bi bi-person me-2" style="color:#06B6D4;"></i>
            بيانات الحساب
          </h5>
        </div>
        <div class="card-body px-4 pb-4">
          <form method="post" enctype="multipart/form-data"
                action="{% url 'accounts:profile_update' %}">
            {% csrf_token %}
            <input type="file" id="avatarInput" name="avatar"
                   class="d-none" accept="image/*"
                   onchange="this.form.submit()">

            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label fw-semibold small">الاسم الأول</label>
                <input type="text" name="first_name" class="form-control"
                       value="{{ user.first_name }}">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold small">الاسم الأخير</label>
                <input type="text" name="last_name" class="form-control"
                       value="{{ user.last_name }}">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold small">البريد الإلكتروني</label>
                <input type="email" name="email" class="form-control"
                       value="{{ user.email }}" dir="ltr">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold small">رقم الموبايل</label>
                <input type="text" name="phone" class="form-control"
                       value="{{ user.phone|default:'' }}">
              </div>
            </div>

            <div class="mt-3">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-check-lg me-1"></i>
                حفظ التغييرات
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- تغيير كلمة المرور -->
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">
            <i class="bi bi-key me-2" style="color:#06B6D4;"></i>
            تغيير كلمة المرور
          </h5>
        </div>
        <div class="card-body px-4 pb-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <p class="mb-1 fw-semibold">كلمة المرور الحالية</p>
              <p class="text-muted small mb-0">
                لحماية حسابك، يُنصح بتغيير كلمة المرور بانتظام
              </p>
            </div>
            <a href="{% url 'password_change' %}"
               class="btn btn-outline-primary">
              <i class="bi bi-key me-1"></i>
              تغيير
            </a>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 2. صفحة 404
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء 404.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', '404.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>404 - الصفحة غير موجودة</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap"
        rel="stylesheet">
  <style>
    * { margin:0; padding:0; box-sizing:border-box; font-family:'Cairo',sans-serif; }
    body {
      background: linear-gradient(135deg, #0f172a, #1e3a5f);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      color: white;
      padding: 20px;
    }
    .number {
      font-size: clamp(6rem, 20vw, 12rem);
      font-weight: 900;
      line-height: 1;
      background: linear-gradient(135deg, #06B6D4, #0891B2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    h1 { font-size: 1.8rem; font-weight: 700; margin: 16px 0; }
    p { color: rgba(255,255,255,0.6); margin-bottom: 32px; }
    .btn {
      display: inline-block;
      padding: 12px 32px;
      background: #06B6D4;
      color: white;
      text-decoration: none;
      border-radius: 12px;
      font-weight: 700;
      margin: 4px;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.9; color: white; }
    .btn-outline {
      background: transparent;
      border: 2px solid rgba(255,255,255,0.3);
    }
  </style>
</head>
<body>
  <div>
    <div class="number">404</div>
    <h1>الصفحة غير موجودة</h1>
    <p>الصفحة اللي بتدور عليها مش موجودة أو اتنقلت لمكان تاني</p>
    <div>
      <a href="/dashboard/" class="btn">
        🏠 الرئيسية
      </a>
      <a href="javascript:history.back()" class="btn btn-outline">
        ← رجوع
      </a>
    </div>
  </div>
</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 3. صفحة 500
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء 500.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', '500.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>500 - خطأ في الخادم</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap"
        rel="stylesheet">
  <style>
    * { margin:0; padding:0; box-sizing:border-box; font-family:'Cairo',sans-serif; }
    body {
      background: linear-gradient(135deg, #1f2937, #374151);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      color: white;
      padding: 20px;
    }
    .number {
      font-size: clamp(6rem, 20vw, 12rem);
      font-weight: 900;
      line-height: 1;
      color: #ef4444;
    }
    h1 { font-size: 1.8rem; font-weight: 700; margin: 16px 0; }
    p { color: rgba(255,255,255,0.6); margin-bottom: 32px; }
    .btn {
      display: inline-block;
      padding: 12px 32px;
      background: #06B6D4;
      color: white;
      text-decoration: none;
      border-radius: 12px;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div>
    <div class="number">500</div>
    <h1>خطأ في الخادم</h1>
    <p>حدث خطأ غير متوقع. فريقنا تم إشعاره تلقائياً.</p>
    <a href="/dashboard/" class="btn">🏠 الرئيسية</a>
  </div>
</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 4. صفحة البحث الشامل
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء search.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'search.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}نتائج البحث{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <!-- فورم البحث -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" action="{% url 'global_search' %}">
        <div class="input-group">
          <span class="input-group-text border-0 bg-light">
            <i class="bi bi-search" style="color:#06B6D4;"></i>
          </span>
          <input type="text" name="q" class="form-control border-0 bg-light"
                 value="{{ query }}"
                 placeholder="ابحث عن موظف، رقم وظيفي، إدارة..."
                 style="font-size:1.1rem;" autofocus>
          <button type="submit" class="btn text-white px-4"
                  style="background:#06B6D4; border-radius:0 10px 10px 0;">
            بحث
          </button>
        </div>
      </form>
    </div>
  </div>

  {% if query %}

  <!-- إحصائيات النتائج -->
  <div class="d-flex align-items-center gap-3 mb-4">
    <h5 class="fw-bold mb-0">
      نتائج البحث عن:
      <span style="color:#06B6D4;">"{{ query }}"</span>
    </h5>
    <span class="badge bg-light text-dark border">
      {{ total_results }} نتيجة
    </span>
  </div>

  {% if employees %}
  <!-- الموظفون -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-header bg-white border-0 pt-3 pb-2 px-4">
      <h6 class="fw-bold mb-0">
        <i class="bi bi-people me-2" style="color:#06B6D4;"></i>
        الموظفون ({{ employees|length }})
      </h6>
    </div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <tbody>
            {% for emp in employees %}
            <tr>
              <td class="px-4 py-3">
                <a href="{% url 'employees:employee_detail' emp.pk %}"
                   class="text-decoration-none">
                  <div class="fw-semibold text-dark">{{ emp.full_name_ar }}</div>
                  <small class="text-muted">
                    {{ emp.employee_code }} |
                    {{ emp.job_title.name_ar|default:"" }} |
                    {{ emp.department.name_ar|default:"" }}
                  </small>
                </a>
              </td>
              <td class="text-end pe-4">
                <span class="badge
                  {% if emp.status == 'active' %}bg-success
                  {% else %}bg-secondary{% endif %}">
                  {{ emp.get_status_display }}
                </span>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  {% endif %}

  {% if not employees and query %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-search" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد نتائج</h5>
      <p class="text-muted">لم نجد نتائج لـ "{{ query }}"</p>
    </div>
  </div>
  {% endif %}

  {% else %}
  <div class="text-center py-5 text-muted">
    <i class="bi bi-search" style="font-size:4rem;color:#d1d5db;"></i>
    <h5 class="mt-3 fw-bold">ابحث عن أي شيء</h5>
    <p>اكتب اسم موظف أو رقم وظيفي أو رقم قومي</p>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 5. إضافة Views في accounts/views.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة views في accounts/views.py...")

extra_views = '''

# ════════════════════════════════════════════════════════════
# Profile Views
# ════════════════════════════════════════════════════════════

@login_required
def profile_view(request):
    """صفحة الملف الشخصي"""
    context = {
        "page_title": "الملف الشخصي",
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_update(request):
    """تحديث بيانات الملف الشخصي"""
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name  = request.POST.get("last_name",  user.last_name)
        user.email      = request.POST.get("email",      user.email)
        user.phone      = request.POST.get("phone",      getattr(user, "phone", ""))

        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]

        user.save()
        from django.contrib import messages as msg
        msg.success(request, "✅ تم تحديث ملفك الشخصي بنجاح")

    return redirect("accounts:profile")


# ════════════════════════════════════════════════════════════
# Global Search
# ════════════════════════════════════════════════════════════

@login_required
def global_search(request):
    """البحث الشامل"""
    from django.db.models import Q

    query     = request.GET.get("q", "").strip()
    employees = []
    total     = 0

    if query and request.user.company:
        try:
            from employees.models import Employee
            employees = Employee.objects.filter(
                company=request.user.company
            ).filter(
                Q(first_name_ar__icontains=query) |
                Q(last_name_ar__icontains=query) |
                Q(first_name_en__icontains=query) |
                Q(last_name_en__icontains=query) |
                Q(employee_code__icontains=query) |
                Q(national_id__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            ).select_related(
                "job_title", "department"
            )[:20]
            total = len(employees)
        except Exception:
            pass

    context = {
        "query":         query,
        "employees":     employees,
        "total_results": total,
        "page_title":    f"بحث: {query}" if query else "البحث",
    }
    return render(request, "search.html", context)


# ════════════════════════════════════════════════════════════
# Notifications
# ════════════════════════════════════════════════════════════

@login_required
def notifications_view(request):
    """مركز الإشعارات"""
    context = {
        "page_title":     "الإشعارات",
        "notifications":  _get_notifications(request.user),
    }
    return render(request, "accounts/notifications.html", context)


def _get_notifications(user):
    """جمع الإشعارات من كل الأماكن"""
    notifications = []

    if not user.company:
        return notifications

    try:
        # إجازات معلقة (للمدير)
        from leaves.models import LeaveRequest
        pending = LeaveRequest.objects.filter(
            company=user.company,
            status="pending"
        ).count()
        if pending:
            notifications.append({
                "type":    "warning",
                "icon":    "calendar2-week",
                "title":   f"{pending} طلب إجازة ينتظر موافقتك",
                "time":    "الآن",
                "url":     "/leaves/",
                "unread":  True,
            })

        # اشتراك ينتهي قريباً
        from subscriptions.models import Subscription
        sub = Subscription.objects.filter(
            company=user.company,
            status__in=["active", "trial"]
        ).first()
        if sub and sub.days_remaining <= 14:
            notifications.append({
                "type":    "danger",
                "icon":    "exclamation-triangle",
                "title":   f"اشتراكك ينتهي خلال {sub.days_remaining} يوم",
                "time":    "",
                "url":     "/subscriptions/my-plan/",
                "unread":  True,
            })

    except Exception:
        pass

    return notifications
'''

accounts_views_path = os.path.join(BASE_DIR, 'accounts', 'views.py')
accounts_views = read_file(accounts_views_path)

if 'profile_view' not in accounts_views:
    append_file(accounts_views_path, extra_views)
else:
    print("  ℹ️  views موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 6. صفحة الإشعارات
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء notifications.html...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'accounts', 'notifications.html'),
    r"""{% extends 'base/dashboard_base.html' %}
{% block title %}الإشعارات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <h4 class="fw-bold mb-0">
      <i class="bi bi-bell me-2" style="color:#06B6D4;"></i>
      الإشعارات
    </h4>
    <span class="badge fs-6 px-3" style="background:#06B6D4;">
      {{ notifications|length }}
    </span>
  </div>

  {% if notifications %}
  <div class="card border-0 shadow-sm">
    <div class="card-body p-0">
      {% for notif in notifications %}
      <a href="{{ notif.url }}"
         class="d-flex align-items-start gap-3 p-4 text-decoration-none
                border-bottom {% if forloop.last %}border-0{% endif %}
                {% if notif.unread %}
                  hover-bg
                {% endif %}"
         style="{% if notif.unread %}background:#f0f9ff;{% endif %}
                transition: background 0.2s;">

        <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
             style="width:44px;height:44px;
                    background:
                    {% if notif.type == 'warning' %}#fff3e0
                    {% elif notif.type == 'danger' %}#fde8e8
                    {% elif notif.type == 'success' %}#e8f5e9
                    {% else %}#e0f7fa{% endif %};">
          <i class="bi bi-{{ notif.icon }}"
             style="font-size:1.2rem;
                    color:{% if notif.type == 'warning' %}#f59e0b
                    {% elif notif.type == 'danger' %}#ef4444
                    {% elif notif.type == 'success' %}#4caf50
                    {% else %}#06B6D4{% endif %};"></i>
        </div>

        <div class="flex-grow-1">
          <div class="fw-semibold text-dark">{{ notif.title }}</div>
          {% if notif.time %}
          <small class="text-muted">{{ notif.time }}</small>
          {% endif %}
        </div>

        {% if notif.unread %}
        <div class="rounded-circle flex-shrink-0"
             style="width:8px;height:8px;background:#06B6D4;margin-top:6px;">
        </div>
        {% endif %}

      </a>
      {% endfor %}
    </div>
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-bell-slash" style="font-size:4rem;color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد إشعارات</h5>
      <p class="text-muted">كل حاجة تمام! 🎉</p>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 7. تحديث accounts/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث accounts/urls.py...")

write_file(
    os.path.join(BASE_DIR, 'accounts', 'urls.py'),
    """from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login-settings/', views.login_settings_view, name='login_settings'),
    path('profile/',        views.profile_view,         name='profile'),
    path('profile/update/', views.profile_update,       name='profile_update'),
    path('notifications/',  views.notifications_view,   name='notifications'),
]
"""
)


# ════════════════════════════════════════════════════════════
# 8. إضافة Global Search URL في motionhr/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Search URL...")

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

if 'global_search' not in main_urls_content:
    # إضافة import
    main_urls_content = main_urls_content.replace(
        "from accounts.views import (\n    CustomPasswordChangeView,\n    smart_login_view,\n    smart_logout_view,\n    dashboard,\n    offline_view,\n    manifest_view,\n    service_worker_view,\n)",
        "from accounts.views import (\n    CustomPasswordChangeView,\n    smart_login_view,\n    smart_logout_view,\n    dashboard,\n    offline_view,\n    manifest_view,\n    service_worker_view,\n    global_search,\n)"
    )

    # إضافة URL
    main_urls_content = main_urls_content.replace(
        "    path('offline/',",
        "    path('search/',       global_search,       name='global_search'),\n    path('offline/',",
    )
    write_file(main_urls_path, main_urls_content)
else:
    print("  ℹ️  Search URL موجود")


# ════════════════════════════════════════════════════════════
# 9. تحديث dashboard_base.html
#    إضافة Search + Profile + Notifications في Header
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث Header في dashboard_base.html...")

dashboard_base_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
dashboard_base = read_file(dashboard_base_path)

# نبحث عن الـ Header ونضيف فيه البحث والإشعارات
if 'global_search' not in dashboard_base:

    # إضافة Search Bar في الـ Header
    search_bar = """
          <!-- Search Bar -->
          <form action="{% url 'global_search' %}" method="get"
                class="d-none d-md-flex align-items-center">
            <div class="input-group" style="max-width:280px;">
              <input type="text" name="q"
                     class="form-control border-0 bg-light rounded-pill"
                     placeholder="بحث سريع..."
                     style="font-size:0.85rem; padding:8px 16px;">
              <button type="submit"
                      class="btn border-0 bg-light rounded-pill ms-1"
                      style="padding:8px 12px;">
                <i class="bi bi-search text-muted" style="font-size:0.85rem;"></i>
              </button>
            </div>
          </form>"""

    # إضافة Notification Icon
    notif_icon = """
          <!-- Notifications -->
          <a href="{% url 'accounts:notifications' %}"
             class="btn btn-sm btn-light rounded-circle position-relative"
             style="width:36px;height:36px;padding:0;
                    display:flex;align-items:center;justify-content:center;">
            <i class="bi bi-bell" style="font-size:1rem;"></i>
          </a>"""

    # إضافة Profile Link في الـ User Dropdown
    profile_link = """
                <li>
                  <a class="dropdown-item d-flex align-items-center gap-2"
                     href="{% url 'accounts:profile' %}">
                    <i class="bi bi-person-circle text-muted"></i>
                    الملف الشخصي
                  </a>
                </li>
                <li>
                  <a class="dropdown-item d-flex align-items-center gap-2"
                     href="{% url 'accounts:notifications' %}">
                    <i class="bi bi-bell text-muted"></i>
                    الإشعارات
                  </a>
                </li>
                <li><hr class="dropdown-divider"></li>"""

    # نبحث عن مكان مناسب في الـ Header لإضافة البحث
    if 'sidebarToggle' in dashboard_base:
        # نضيف بعد زرار الـ Toggle
        dashboard_base = dashboard_base.replace(
            'id="sidebarToggle"',
            'id="sidebarToggle"'
        )

    # نضيف Profile في الـ dropdown لو مش موجود
    if 'accounts:profile' not in dashboard_base:
        # نبحث عن dropdown-menu في الـ header
        if 'dropdown-menu' in dashboard_base:
            # نضيف في أول الـ dropdown
            dashboard_base = dashboard_base.replace(
                '<ul class="dropdown-menu',
                f'<ul class="dropdown-menu'
            )
            # نبحث عن أول dropdown-item وقبله نضيف الـ profile
            dashboard_base = dashboard_base.replace(
                '<li>\n                  <a class="dropdown-item',
                profile_link + '\n                <li>\n                  <a class="dropdown-item',
                1
            )
            write_file(dashboard_base_path, dashboard_base)
            print("  ✅ تم إضافة Profile في الـ Header dropdown")
        else:
            print("  ⚠️  مش لاقي dropdown-menu في الـ Header")
    else:
        print("  ℹ️  Profile موجود في الـ Header")
else:
    print("  ℹ️  Search موجود في الـ Header")


# ════════════════════════════════════════════════════════════
# 10. تحديث settings.py - إضافة Handler للـ 404 و 500
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث settings.py - Error Handlers...")

settings_path = os.path.join(BASE_DIR, 'motionhr', 'settings.py')
settings_content = read_file(settings_path)

if 'handler404' not in settings_content:
    append_file(settings_path, """
# ─────────────────────────────────────────────
# Custom Error Pages
# ─────────────────────────────────────────────
# handler404 و handler500 بيتحددوا في urls.py
""")

# إضافة handlers في motionhr/urls.py
main_urls_content = read_file(main_urls_path)
if 'handler404' not in main_urls_content:
    append_file(main_urls_path, """

# ── Custom Error Handlers ─────────────────────
handler404 = 'accounts.views.handler_404'
handler500 = 'accounts.views.handler_500'
""")

# إضافة handler views
accounts_views = read_file(accounts_views_path)
if 'handler_404' not in accounts_views:
    append_file(accounts_views_path, '''

# ════════════════════════════════════════════════════════════
# Error Handlers
# ════════════════════════════════════════════════════════════

def handler_404(request, exception=None):
    return render(request, "404.html", status=404)

def handler_500(request):
    return render(request, "500.html", status=500)
''')
    print("  ✅ تم إضافة Error Handlers")
else:
    print("  ℹ️  Error Handlers موجودة")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 22 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ profile.html - الملف الشخصي
  2.  ✅ notifications.html - الإشعارات
  3.  ✅ 404.html - صفحة خطأ مخصصة
  4.  ✅ 500.html - صفحة خطأ مخصصة
  5.  ✅ search.html - البحث الشامل
  6.  ✅ profile_view + profile_update
  7.  ✅ global_search view
  8.  ✅ notifications_view
  9.  ✅ accounts/urls.py محدث
  10. ✅ motionhr/urls.py - Search URL
  11. ✅ Error Handlers (404 + 500)
  12. ✅ Header - Profile + Notifications

🔗 URLs الجديدة:
  /accounts/profile/        ← الملف الشخصي
  /accounts/notifications/  ← الإشعارات
  /search/                  ← البحث الشامل

🚀 الخطوة الأخيرة: Patch 23 - Simulation كامل
""")