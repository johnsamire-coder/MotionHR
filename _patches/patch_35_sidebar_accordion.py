#!/usr/bin/env python3
"""
Patch 35: Sidebar Accordion
=============================
كل قسم في الـ Sidebar بيفتح ويقفل لما تدوس عليه
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 35: Sidebar Accordion")
print("=" * 60)

sidebar_html = """{% load custom_filters %}
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

    /* ── Sidebar ── */
    .sidebar {
      width:250px; min-height:100vh;
      background:linear-gradient(180deg,#0f172a,#1e293b);
      position:fixed; top:0; right:0; z-index:100;
      display:flex; flex-direction:column;
      overflow-y:auto; transition:transform 0.3s;
    }
    .sidebar::-webkit-scrollbar { width:4px; }
    .sidebar::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:4px; }

    .sidebar-brand { padding:16px; border-bottom:1px solid rgba(255,255,255,0.08); }
    .sidebar-brand a { text-decoration:none; }
    .sidebar-brand h5 { color:#06B6D4; font-weight:900; font-size:1.3rem; margin:0; }
    .sidebar-brand small { color:rgba(255,255,255,0.3); font-size:0.7rem; }

    /* ── Accordion Section ── */
    .sidebar-section-btn {
      display:flex; align-items:center; justify-content:space-between;
      width:100%; padding:10px 16px; border:none; background:none;
      color:rgba(255,255,255,0.4); font-size:0.72rem; font-weight:700;
      letter-spacing:1px; text-transform:uppercase;
      cursor:pointer; transition:all 0.2s;
      font-family:'Cairo',sans-serif;
    }
    .sidebar-section-btn:hover { color:rgba(255,255,255,0.6); }
    .sidebar-section-btn i {
      transition:transform 0.3s;
      font-size:0.65rem;
    }
    .sidebar-section-btn.collapsed i { transform:rotate(-90deg); }
    .sidebar-section-btn:not(.collapsed) i { transform:rotate(0deg); }

    .sidebar-section-items {
      overflow:hidden; transition:max-height 0.35s ease;
    }

    .sidebar .nav-link {
      color:rgba(255,255,255,0.65); border-radius:8px;
      padding:8px 12px; margin:1px 8px;
      font-size:0.85rem; font-weight:600;
      display:flex; align-items:center; gap:10px;
      transition:all 0.2s;
    }
    .sidebar .nav-link:hover { background:rgba(255,255,255,0.08); color:white; }
    .sidebar .nav-link.active {
      background:linear-gradient(135deg,#06B6D4,#0891B2);
      color:white; box-shadow:0 4px 12px rgba(6,182,212,0.3);
    }
    .sidebar .nav-link i { font-size:0.95rem; width:18px; text-align:center; }

    /* ── Main ── */
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
      background:none; border:none; width:100%;
      color:rgba(255,255,255,0.65); border-radius:8px;
      padding:8px 12px; margin:1px 8px;
      font-family:'Cairo',sans-serif; font-size:0.85rem;
      font-weight:600; cursor:pointer;
      display:flex; align-items:center; gap:10px;
      transition:all 0.2s; text-align:right;
    }
    .logout-form-btn:hover { background:rgba(239,68,68,0.15); color:#ef4444; }
  </style>
</head>
<body>

<div class="loading-bar" id="loadingBar"></div>
<div class="sidebar-overlay" id="sidebarOverlay"></div>

<!-- ══════ SIDEBAR ══════ -->
<div class="sidebar" id="sidebar">

  <div class="sidebar-brand">
    <a href="{% url 'dashboard' %}">
      <h5>MotionHR</h5>
      <small>HR in Motion</small>
    </a>
  </div>

  <nav class="flex-grow-1 py-2">

    <!-- الرئيسية (بدون accordion) -->
    <a href="{% url 'dashboard' %}"
       class="nav-link {% if request.path == '/dashboard/' %}active{% endif %}">
      <i class="bi bi-speedometer2"></i><span>الرئيسية</span>
    </a>

    <!-- ═══ الموظفون ═══ -->
    {% if request.user.role != 'employee' %}
    <button class="sidebar-section-btn {% if '/employees/' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secEmployees', this)">
      الموظفون <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secEmployees"
         style="{% if '/employees/' not in request.path %}max-height:0;{% else %}max-height:200px;{% endif %}">
      <a href="{% url 'employees:employee_list' %}"
         class="nav-link {% if '/employees/' in request.path and 'add' not in request.path %}active{% endif %}">
        <i class="bi bi-people-fill"></i><span>قائمة الموظفين</span>
      </a>
      <a href="{% url 'employees:employee_add' %}"
         class="nav-link {% if '/employees/add' in request.path %}active{% endif %}">
        <i class="bi bi-person-plus"></i><span>إضافة موظف</span>
      </a>
    </div>
    {% endif %}

    <!-- ═══ الحضور ═══ -->
    <button class="sidebar-section-btn {% if '/attendance/' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secAttendance', this)">
      الحضور <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secAttendance"
         style="{% if '/attendance/' not in request.path %}max-height:0;{% else %}max-height:300px;{% endif %}">

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
    </div>

    <!-- ═══ الطلبات ═══ -->
    <button class="sidebar-section-btn {% if '/requests/' not in request.path and '/leaves/' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secRequests', this)">
      الطلبات <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secRequests"
         style="{% if '/requests/' not in request.path and '/leaves/' not in request.path %}max-height:0;{% else %}max-height:300px;{% endif %}">
      <a href="{% url 'requests_app:list' %}"
         class="nav-link {% if '/requests/' in request.path and 'add' not in request.path %}active{% endif %}">
        <i class="bi bi-inbox"></i><span>طلباتي</span>
      </a>
      <a href="{% url 'requests_app:add' %}"
         class="nav-link {% if '/requests/add' in request.path %}active{% endif %}">
        <i class="bi bi-plus-circle"></i><span>طلب جديد</span>
      </a>
      {% if request.user.role != 'employee' %}
      <a href="{% url 'leaves:leave_requests_list' %}"
         class="nav-link {% if '/leaves/' in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
        <i class="bi bi-calendar2-week"></i><span>طلبات الإجازات</span>
      </a>
      <a href="{% url 'leaves:leave_balances' %}"
         class="nav-link {% if 'balances' in request.path %}active{% endif %}">
        <i class="bi bi-wallet2"></i><span>أرصدة الإجازات</span>
      </a>
      <a href="{% url 'leaves:leave_types_list' %}"
         class="nav-link {% if 'types' in request.path %}active{% endif %}">
        <i class="bi bi-list-check"></i><span>أنواع الإجازات</span>
      </a>
      {% endif %}
    </div>

    <!-- ═══ التقارير ═══ -->
    {% if request.user.role != 'employee' %}
    <button class="sidebar-section-btn {% if '/reports/' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secReports', this)">
      التقارير <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secReports"
         style="{% if '/reports/' not in request.path %}max-height:0;{% else %}max-height:300px;{% endif %}">
      <a href="{% url 'reports:home' %}"
         class="nav-link {% if request.path == '/reports/' %}active{% endif %}">
        <i class="bi bi-bar-chart"></i><span>كل التقارير</span>
      </a>
      <a href="{% url 'reports:attendance' %}"
         class="nav-link {% if 'reports/attendance' in request.path %}active{% endif %}">
        <i class="bi bi-calendar-check"></i><span>تقرير الحضور</span>
      </a>
      <a href="{% url 'reports:late' %}"
         class="nav-link {% if 'reports/late' in request.path %}active{% endif %}">
        <i class="bi bi-clock-history"></i><span>تقرير التأخيرات</span>
      </a>
      <a href="{% url 'reports:leaves' %}"
         class="nav-link {% if 'reports/leaves' in request.path %}active{% endif %}">
        <i class="bi bi-calendar2-week"></i><span>تقرير الإجازات</span>
      </a>
      <a href="{% url 'reports:employees' %}"
         class="nav-link {% if 'reports/employees' in request.path %}active{% endif %}">
        <i class="bi bi-people"></i><span>تقرير الموظفين</span>
      </a>
    </div>
    {% endif %}

    <!-- ═══ الشركة ═══ -->
    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <button class="sidebar-section-btn {% if '/companies/' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secCompany', this)">
      الشركة <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secCompany"
         style="{% if '/companies/' not in request.path %}max-height:0;{% else %}max-height:400px;{% endif %}">
      <a href="{% url 'companies:settings' %}"
         class="nav-link {% if 'companies/settings' in request.path %}active{% endif %}">
        <i class="bi bi-building"></i><span>إعدادات الشركة</span>
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
      <a href="{% url 'companies:charter_manage' %}"
         class="nav-link {% if 'charter/manage' in request.path %}active{% endif %}">
        <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
      </a>
    </div>
    {% endif %}

    <!-- ═══ حسابي المالي ═══ -->
    {% if request.current_employee or request.user.role == 'employee' %}
    <button class="sidebar-section-btn {% if 'my-balance' not in request.path and 'my-deductions' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secFinance', this)">
      حسابي المالي <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secFinance"
         style="{% if 'my-balance' not in request.path and 'my-deductions' not in request.path %}max-height:0;{% else %}max-height:200px;{% endif %}">
      <a href="{% url 'employees:my_balance' %}"
         class="nav-link {% if 'my-balance' in request.path %}active{% endif %}">
        <i class="bi bi-wallet2"></i><span>رصيد إجازاتي</span>
      </a>
      <a href="{% url 'employees:my_deductions' %}"
         class="nav-link {% if 'my-deductions' in request.path %}active{% endif %}">
        <i class="bi bi-receipt-cutoff"></i><span>خصوماتي</span>
      </a>
    </div>
    {% endif %}

    <!-- ═══ حسابي ═══ -->
    <button class="sidebar-section-btn {% if 'profile' not in request.path and 'password' not in request.path and 'charter' not in request.path or 'manage' in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secAccount', this)">
      حسابي <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secAccount"
         style="{% if 'profile' not in request.path and 'password' not in request.path %}max-height:0;{% else %}max-height:250px;{% endif %}">
      <a href="{% url 'companies:charter' %}"
         class="nav-link {% if 'charter' in request.path and 'manage' not in request.path %}active{% endif %}">
        <i class="bi bi-file-earmark-text"></i><span>ميثاق العمل</span>
      </a>
      <a href="{% url 'accounts:profile' %}"
         class="nav-link {% if 'profile' in request.path %}active{% endif %}">
        <i class="bi bi-person-circle"></i><span>الملف الشخصي</span>
      </a>
      <a href="{% url 'password_change' %}"
         class="nav-link {% if 'password-change' in request.path %}active{% endif %}">
        <i class="bi bi-key"></i><span>تغيير كلمة المرور</span>
      </a>
    </div>

    <!-- ═══ الاشتراك ═══ -->
    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <button class="sidebar-section-btn {% if 'my-plan' not in request.path and 'contact-sales' not in request.path %}collapsed{% endif %}"
            onclick="toggleSection('secSubs', this)">
      الاشتراك <i class="bi bi-chevron-down"></i>
    </button>
    <div class="sidebar-section-items" id="secSubs"
         style="{% if 'my-plan' not in request.path and 'contact-sales' not in request.path %}max-height:0;{% else %}max-height:200px;{% endif %}">
      <a href="{% url 'subscriptions:my_plan' %}"
         class="nav-link {% if 'my-plan' in request.path %}active{% endif %}">
        <i class="bi bi-star"></i><span>خطتي</span>
      </a>
      <a href="{% url 'subscriptions:contact_sales' %}"
         class="nav-link {% if 'contact-sales' in request.path %}active{% endif %}">
        <i class="bi bi-headset"></i><span>تواصل / ترقية</span>
      </a>
    </div>
    {% endif %}

    <!-- Logout -->
    <div style="padding:8px 0;">
      <form method="post" action="{% url 'logout' %}" style="margin:1px 8px;">
        {% csrf_token %}
        <button type="submit" class="logout-form-btn">
          <i class="bi bi-box-arrow-left" style="width:18px;text-align:center;"></i>
          <span>تسجيل الخروج</span>
        </button>
      </form>
    </div>

  </nav>

  <!-- User Info -->
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

<!-- ══════ MAIN ══════ -->
<div class="main-content">

  <div class="top-header">
    <div class="d-flex align-items-center gap-2">
      <button class="btn btn-sm btn-light d-md-none" id="sidebarToggle" style="border-radius:8px;">
        <i class="bi bi-list fs-5"></i>
      </button>
      <h6 style="margin:0;font-weight:700;color:#1f2937;font-size:0.95rem;">
        {% block header_title %}{{ page_title|default:"MotionHR" }}{% endblock %}
      </h6>
    </div>

    <div class="d-flex align-items-center gap-2">
      <a href="{% url 'global_search' %}"
         class="btn btn-sm btn-light" style="border-radius:8px;width:34px;height:34px;padding:0;display:flex;align-items:center;justify-content:center;">
        <i class="bi bi-search" style="color:#06B6D4;"></i>
      </a>

      <div class="dropdown">
        <button class="btn btn-sm btn-light dropdown-toggle d-flex align-items-center gap-2"
                type="button" data-bs-toggle="dropdown" style="border-radius:8px;">
          <div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#06B6D4,#0891B2);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:0.8rem;">
            {{ request.user.get_full_name|first|default:request.user.username|first|upper }}
          </div>
          <span class="d-none d-md-inline" style="font-size:0.85rem;font-weight:600;">
            {{ request.user.get_full_name|default:request.user.username }}
          </span>
        </button>
        <ul class="dropdown-menu dropdown-menu-start shadow border-0" style="border-radius:12px;min-width:190px;">
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

  {% if messages %}
  <div class="messages-container">
    {% for message in messages %}
    <div class="alert alert-{% if message.tags == 'error' %}danger{% else %}{{ message.tags }}{% endif %} alert-dismissible fade show mb-2"
         style="border:none;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);font-size:0.88rem;">
      {{ message }}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="content-area">
    {% block content %}{% endblock %}
    {% block dashboard_content %}{% endblock %}
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
// ── Sidebar Toggle (Mobile) ──
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

// ── Accordion Toggle ──
function toggleSection(id, btn) {
  const el = document.getElementById(id);
  if (!el) return;

  const isOpen = el.style.maxHeight && el.style.maxHeight !== '0px';

  if (isOpen) {
    el.style.maxHeight = '0px';
    btn.classList.add('collapsed');
  } else {
    el.style.maxHeight = el.scrollHeight + 'px';
    btn.classList.remove('collapsed');
  }
}

// ── Loading Bar ──
const loadingBar = document.getElementById('loadingBar');
document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])').forEach(link => {
  link.addEventListener('click', () => {
    if (loadingBar) loadingBar.style.display = 'block';
  });
});

// ── Auto-hide Messages ──
setTimeout(() => {
  document.querySelectorAll('.messages-container .alert').forEach(el => {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.5s';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);

// ── PWA ──
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
}
</script>

{% block extra_js %}{% endblock %}
{% block dashboard_js %}{% endblock %}

</body>
</html>"""

create_file(
    os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html"),
    sidebar_html
)

print("\n" + "=" * 60)
print("  ✅ Patch 35 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ Sidebar بالـ Accordion
  ✅ كل قسم بيفتح ويقفل
  ✅ القسم اللي فيه الصفحة الحالية يفتح تلقائي
  ✅ باقي الأقسام مقفولة
  ✅ أنيميشن سلسة
  ✅ حسب الدور (employee / manager / admin)

جرب بأي يوزر وشوف الـ Sidebar الجديد!
""")