#!/usr/bin/env python3
"""
Patch 29b: Quick Fixes
"""

import os
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 29b: Quick Fixes")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. إصلاح load قبل extends في كل التمبلتس
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح load قبل extends...")

all_templates = glob.glob(
    os.path.join(BASE_DIR, "templates", "**", "*.html"),
    recursive=True
)

fixed = 0
for tmpl in all_templates:
    content = read_file(tmpl)
    if "{% load custom_filters %}" not in content:
        continue
    if "{% extends" not in content:
        continue

    lines = content.split("\n")
    load_idx = None
    extends_idx = None

    for i, line in enumerate(lines):
        if "{% load custom_filters %}" in line and load_idx is None:
            load_idx = i
        if "{% extends" in line and extends_idx is None:
            extends_idx = i

    if load_idx is None or extends_idx is None:
        continue

    # load لازم يكون بعد extends مباشرة
    if load_idx < extends_idx:
        load_line = lines.pop(load_idx)
        # extends بقى في مكان جديد
        new_extends_idx = None
        for i, line in enumerate(lines):
            if "{% extends" in line:
                new_extends_idx = i
                break
        if new_extends_idx is not None:
            lines.insert(new_extends_idx + 1, load_line)
        new_content = "\n".join(lines)
        if new_content != content:
            write_file(tmpl, new_content)
            fixed += 1

print(f"  ✅ تم إصلاح {fixed} ملف")


# ════════════════════════════════════════════════════════════
# 2. إنشاء dashboard_base.html نهائي نظيف
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث dashboard_base.html...")

dashboard_base = """{% load custom_filters %}
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}MotionHR{% endblock %}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#06B6D4">
  {% block extra_css %}{% endblock %}
  <style>
    * { font-family: 'Cairo', sans-serif; }
    body { background:#f8fafc; min-height:100vh; }

    .sidebar {
      width:250px; min-height:100vh;
      background:linear-gradient(180deg,#0f172a,#1e293b);
      position:fixed; top:0; right:0; z-index:100;
      display:flex; flex-direction:column;
      overflow-y:auto; transition:transform 0.3s;
    }
    .sidebar-brand { padding:16px; border-bottom:1px solid rgba(255,255,255,0.08); }
    .sidebar-brand a { text-decoration:none; }
    .sidebar-brand h5 { color:#06B6D4; font-weight:900; font-size:1.3rem; margin:0; }
    .sidebar-brand small { color:rgba(255,255,255,0.3); font-size:0.7rem; }

    .sidebar-label {
      color:rgba(255,255,255,0.3); font-size:0.65rem;
      font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
      padding:12px 16px 4px;
    }

    .sidebar .nav-link {
      color:rgba(255,255,255,0.65); border-radius:8px;
      padding:8px 12px; margin:1px 8px;
      font-size:0.87rem; font-weight:600;
      display:flex; align-items:center; gap:10px;
      transition:all 0.2s;
    }
    .sidebar .nav-link:hover { background:rgba(255,255,255,0.08); color:white; }
    .sidebar .nav-link.active {
      background:linear-gradient(135deg,#06B6D4,#0891B2);
      color:white; box-shadow:0 4px 12px rgba(6,182,212,0.3);
    }
    .sidebar .nav-link i { font-size:1rem; width:18px; text-align:center; }

    .main-content { margin-right:250px; min-height:100vh; display:flex; flex-direction:column; }

    .top-header {
      background:white; border-bottom:1px solid #e5e7eb;
      padding:10px 20px; display:flex; align-items:center;
      justify-content:space-between; position:sticky; top:0; z-index:50;
      box-shadow:0 1px 3px rgba(0,0,0,0.05);
    }

    .messages-container {
      position:fixed; top:65px; left:20px;
      z-index:1000; max-width:350px;
    }

    .loading-bar {
      position:fixed; top:0; left:0; right:0; height:3px;
      background:linear-gradient(90deg,#06B6D4,#0891B2,#06B6D4);
      background-size:200% 100%;
      animation:loading 1.5s infinite; z-index:9999; display:none;
    }
    @keyframes loading { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

    .sidebar-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:99; }

    @media(max-width:768px){
      .sidebar { transform:translateX(100%); }
      .sidebar.show { transform:translateX(0); }
      .main-content { margin-right:0; }
      .sidebar-overlay.show { display:block; }
    }

    .logout-form-btn {
      background:none; border:none; padding:0;
      color:inherit; width:100%; text-align:right;
      font-family:'Cairo',sans-serif; font-size:0.87rem;
      font-weight:600; cursor:pointer;
      display:flex; align-items:center; gap:10px;
      color:rgba(255,255,255,0.65); border-radius:8px;
      padding:8px 12px; margin:1px 8px;
      transition:all 0.2s;
    }
    .logout-form-btn:hover { background:rgba(239,68,68,0.15); color:#ef4444; }
  </style>
</head>
<body>

<div class="loading-bar" id="loadingBar"></div>
<div class="sidebar-overlay" id="sidebarOverlay"></div>

<!-- SIDEBAR -->
<div class="sidebar" id="sidebar">

  <div class="sidebar-brand">
    <a href="{% url 'dashboard' %}">
      <h5>MotionHR</h5>
      <small>HR in Motion</small>
    </a>
  </div>

  <nav class="flex-grow-1 py-2">

    <!-- الرئيسية -->
    <a href="{% url 'dashboard' %}"
       class="nav-link {% if request.path == '/dashboard/' %}active{% endif %}">
      <i class="bi bi-speedometer2"></i><span>الرئيسية</span>
    </a>

    <!-- الموظفون - للإدارة فقط -->
    {% if request.user.role != 'employee' %}
    <div class="sidebar-label">الموظفون</div>
    <a href="{% url 'employees:employee_list' %}"
       class="nav-link {% if '/employees/' in request.path %}active{% endif %}">
      <i class="bi bi-people-fill"></i><span>الموظفون</span>
    </a>
    {% endif %}

    <!-- الحضور -->
    <div class="sidebar-label">الحضور</div>

    {% if request.current_employee %}
    <a href="{% url 'attendance:check_in' %}"
       class="nav-link {% if 'check-in' in request.path %}active{% endif %}">
      <i class="bi bi-qr-code-scan"></i><span>تسجيل الحضور</span>
    </a>
    {% endif %}

    {% if request.user.role != 'employee' %}
    <a href="{% url 'attendance:list' %}"
       class="nav-link {% if request.path == '/attendance/' %}active{% endif %}">
      <i class="bi bi-calendar-check"></i><span>سجلات الحضور</span>
    </a>
    <a href="{% url 'attendance:live_map' %}"
       class="nav-link {% if 'map' in request.path %}active{% endif %}">
      <i class="bi bi-map"></i><span>الخريطة الحية</span>
    </a>
    <a href="{% url 'attendance:monitor' %}"
       class="nav-link {% if 'monitor' in request.path %}active{% endif %}">
      <i class="bi bi-broadcast"></i><span>متابعة الميدانيين</span>
    </a>
    <a href="{% url 'attendance:visits' %}"
       class="nav-link {% if 'visits' in request.path %}active{% endif %}">
      <i class="bi bi-geo-alt"></i><span>الزيارات</span>
    </a>
    {% endif %}

    <!-- الإجازات -->
    <div class="sidebar-label">الإجازات</div>
    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'add' not in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i><span>طلبات الإجازات</span>
    </a>
    <a href="{% url 'leaves:leave_request_add' %}"
       class="nav-link {% if '/leaves/add' in request.path %}active{% endif %}">
      <i class="bi bi-calendar-plus"></i><span>طلب إجازة جديد</span>
    </a>
    {% if request.user.role != 'employee' %}
    <a href="{% url 'leaves:leave_balances' %}"
       class="nav-link {% if 'balances' in request.path %}active{% endif %}">
      <i class="bi bi-wallet2"></i><span>أرصدة الإجازات</span>
    </a>
    <a href="{% url 'leaves:leave_types_list' %}"
       class="nav-link {% if 'types' in request.path %}active{% endif %}">
      <i class="bi bi-list-check"></i><span>أنواع الإجازات</span>
    </a>
    {% endif %}

    <!-- التقارير - للإدارة فقط -->
    {% if request.user.role != 'employee' %}
    <div class="sidebar-label">التقارير</div>
    <a href="{% url 'reports:home' %}"
       class="nav-link {% if '/reports/' in request.path %}active{% endif %}">
      <i class="bi bi-bar-chart"></i><span>التقارير</span>
    </a>
    {% endif %}

    <!-- إعدادات الشركة - للإدارة فقط -->
    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <div class="sidebar-label">الشركة</div>
    <a href="{% url 'companies:settings' %}"
       class="nav-link {% if 'companies/settings' in request.path %}active{% endif %}">
      <i class="bi bi-building"></i><span>الشركة</span>
    </a>
    <a href="{% url 'companies:branches_list' %}"
       class="nav-link {% if 'branches' in request.path %}active{% endif %}">
      <i class="bi bi-geo-alt"></i><span>الفروع</span>
    </a>
    <a href="{% url 'companies:departments_list' %}"
       class="nav-link {% if 'departments' in request.path %}active{% endif %}">
      <i class="bi bi-diagram-3"></i><span>الإدارات</span>
    </a>
    <a href="{% url 'companies:shifts_list' %}"
       class="nav-link {% if 'shifts' in request.path %}active{% endif %}">
      <i class="bi bi-clock"></i><span>الشيفتات</span>
    </a>
    {% endif %}

    <!-- حسابي -->
    <div class="sidebar-label">حسابي</div>
    <a href="{% url 'accounts:profile' %}"
       class="nav-link {% if 'profile' in request.path %}active{% endif %}">
      <i class="bi bi-person-circle"></i><span>الملف الشخصي</span>
    </a>
    <a href="{% url 'password_change' %}"
       class="nav-link {% if 'password-change' in request.path %}active{% endif %}">
      <i class="bi bi-key"></i><span>تغيير كلمة المرور</span>
    </a>

    <!-- الاشتراك - للإدارة فقط -->
    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <div class="sidebar-label">الاشتراك</div>
    <a href="{% url 'subscriptions:my_plan' %}"
       class="nav-link {% if 'my-plan' in request.path %}active{% endif %}">
      <i class="bi bi-star"></i><span>خطتي</span>
    </a>
    <a href="{% url 'subscriptions:contact_sales' %}"
       class="nav-link {% if 'contact-sales' in request.path %}active{% endif %}">
      <i class="bi bi-headset"></i><span>تواصل / ترقية</span>
    </a>
    {% endif %}

    <!-- Logout -->
    <div class="sidebar-label">الحساب</div>
    <form method="post" action="{% url 'logout' %}" style="margin:1px 8px;">
      {% csrf_token %}
      <button type="submit" class="logout-form-btn">
        <i class="bi bi-box-arrow-left" style="width:18px;text-align:center;"></i>
        <span>تسجيل الخروج</span>
      </button>
    </form>

  </nav>

  <!-- معلومات المستخدم -->
  <div style="padding:12px 16px; border-top:1px solid rgba(255,255,255,0.08);">
    <div style="color:rgba(255,255,255,0.5); font-size:0.75rem;">
      {{ request.user.get_full_name|default:request.user.username }}
    </div>
    <div style="color:rgba(255,255,255,0.3); font-size:0.7rem;">
      {% if request.user.role == 'super_admin' %}مشرف النظام
      {% elif request.user.role == 'company_admin' %}مدير شركة
      {% elif request.user.role == 'hr_manager' %}مدير HR
      {% elif request.user.role == 'manager' %}مدير
      {% else %}موظف{% endif %}
    </div>
  </div>

</div>

<!-- MAIN CONTENT -->
<div class="main-content">

  <!-- Header -->
  <div class="top-header">
    <div class="d-flex align-items-center gap-2">
      <button class="btn btn-sm btn-light d-md-none" id="sidebarToggle" style="border-radius:8px;">
        <i class="bi bi-list fs-5"></i>
      </button>
      <h6 style="margin:0; font-weight:700; color:#1f2937; font-size:0.95rem;">
        {% block header_title %}{{ page_title|default:"MotionHR" }}{% endblock %}
      </h6>
    </div>

    <div class="d-flex align-items-center gap-2">
      <!-- Search -->
      <a href="{% url 'global_search' %}"
         class="btn btn-sm btn-light" style="border-radius:8px; width:34px; height:34px; padding:0; display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-search" style="color:#06B6D4;"></i>
      </a>

      <!-- User Dropdown -->
      <div class="dropdown">
        <button class="btn btn-sm btn-light dropdown-toggle d-flex align-items-center gap-2"
                type="button" data-bs-toggle="dropdown"
                style="border-radius:8px;">
          <div style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,#06B6D4,#0891B2); display:flex; align-items:center; justify-content:center; color:white; font-weight:700; font-size:0.8rem;">
            {{ request.user.get_full_name|first|default:request.user.username|first|upper }}
          </div>
          <span class="d-none d-md-inline" style="font-size:0.85rem; font-weight:600;">
            {{ request.user.get_full_name|default:request.user.username }}
          </span>
        </button>
        <ul class="dropdown-menu dropdown-menu-start shadow border-0" style="border-radius:12px; min-width:190px;">
          <li>
            <a class="dropdown-item py-2" href="{% url 'accounts:profile' %}">
              <i class="bi bi-person-circle me-2 text-muted"></i>الملف الشخصي
            </a>
          </li>
          <li>
            <a class="dropdown-item py-2" href="{% url 'password_change' %}">
              <i class="bi bi-key me-2 text-muted"></i>تغيير كلمة المرور
            </a>
          </li>
          <li><hr class="dropdown-divider my-1"></li>
          <li>
            <form method="post" action="{% url 'logout' %}">
              {% csrf_token %}
              <button type="submit" class="dropdown-item py-2 text-danger">
                <i class="bi bi-box-arrow-left me-2"></i>تسجيل الخروج
              </button>
            </form>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Messages -->
  {% if messages %}
  <div class="messages-container">
    {% for message in messages %}
    <div class="alert alert-{% if message.tags == 'error' %}danger{% else %}{{ message.tags }}{% endif %} alert-dismissible fade show mb-2"
         style="border:none; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.1); font-size:0.88rem;">
      {{ message }}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Content -->
  <div class="content-area">
    {% block content %}{% endblock %}
    {% block dashboard_content %}{% endblock %}
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
  // Sidebar Toggle
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    sidebar.classList.toggle('show');
    overlay.classList.toggle('show');
  });
  overlay?.addEventListener('click', () => {
    sidebar.classList.remove('show');
    overlay.classList.remove('show');
  });

  // Loading Bar
  const loadingBar = document.getElementById('loadingBar');
  document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])').forEach(link => {
    link.addEventListener('click', () => {
      if (loadingBar) loadingBar.style.display = 'block';
    });
  });

  // Auto-hide Messages
  setTimeout(() => {
    document.querySelectorAll('.messages-container .alert').forEach(el => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.5s';
      setTimeout(() => el.remove(), 500);
    });
  }, 4000);

  // PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
  }
</script>

{% block extra_js %}{% endblock %}
{% block dashboard_js %}{% endblock %}

</body>
</html>"""

write_file(
    os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html"),
    dashboard_base
)

print("\n" + "=" * 60)
print("  ✅ Patch 29b اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  1. ✅ load قبل extends في كل التمبلتس
  2. ✅ dashboard_base.html نظيف كامل
  3. ✅ Logout في الـ Sidebar والـ Header
  4. ✅ خطتي/تواصل للإدارة فقط
  5. ✅ تسجيل الحضور للموظفين المربوطين فقط
  6. ✅ طلب إجازة جديد في الـ Sidebar
  7. ✅ الملف الشخصي في الـ Sidebar
  8. ✅ Sidebar نظيف حسب الدور

جرب:
  1. demo_admin  - لازم يشوف كل حاجة ما عدا تسجيل الحضور
  2. emp10001    - لازم يشوف الحضور + الإجازات + ملفه بس
  3. /subscriptions/my-plan/ - لازم تشتغل بدون خطأ
""")