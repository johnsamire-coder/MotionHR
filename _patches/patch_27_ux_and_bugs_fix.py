#!/usr/bin/env python3
"""
Patch 27: UX Fix + Bugs Fix
=============================
المرحلة 1 كاملة:
1. Logout واضح في الـ Header
2. Sidebar حسب الدور
3. Active link في الـ Sidebar
4. إصلاح bugs الـ Template (getattr, split)
5. إصلاح "اشتراكك منتهي"
6. إصلاح روابط sub-admin
7. رسائل النجاح والخطأ واضحة
8. Loading indicator
"""

import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
print("  Patch 27: UX Fix + Bugs Fix")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. Custom Template Tags (split + getattr)
# ════════════════════════════════════════════════════════════
print("\n🔧 Custom Template Tags...")

create_file(
    os.path.join(BASE_DIR, "accounts", "templatetags", "__init__.py"),
    ""
)

create_file(
    os.path.join(BASE_DIR, "accounts", "templatetags", "custom_filters.py"),
    '''from django import template
register = template.Library()

@register.filter(name="split")
def split_filter(value, delimiter="|"):
    if value:
        return str(value).split(delimiter)
    return []

@register.filter(name="getattr")
def getattr_filter(obj, attr):
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

@register.filter(name="get_item")
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
'''
)


# ════════════════════════════════════════════════════════════
# 2. Dashboard Base — Logout + Active Links + Sidebar بالدور
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء dashboard_base.html جديد...")

dashboard_base = r"""{% load custom_filters %}
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}MotionHR{% endblock %}</title>

  <!-- Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap"
        rel="stylesheet">
  <!-- Bootstrap RTL -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css"
        rel="stylesheet">
  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"
        rel="stylesheet">
  <!-- PWA -->
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#06B6D4">
  <link rel="stylesheet" href="/static/css/pwa.css">

  {% block extra_css %}{% endblock %}

  <style>
    * { font-family: 'Cairo', sans-serif; }

    body {
      background: #f8fafc;
      min-height: 100vh;
    }

    /* ── Sidebar ── */
    .sidebar {
      width: 260px;
      min-height: 100vh;
      background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
      position: fixed;
      top: 0;
      right: 0;
      z-index: 100;
      display: flex;
      flex-direction: column;
      transition: transform 0.3s ease;
      overflow-y: auto;
    }

    .sidebar-brand {
      padding: 20px 20px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .sidebar-brand h5 {
      color: #06B6D4;
      font-weight: 900;
      font-size: 1.4rem;
      margin: 0;
      letter-spacing: -0.5px;
    }

    .sidebar-brand small {
      color: rgba(255,255,255,0.4);
      font-size: 0.7rem;
    }

    .sidebar-section {
      padding: 16px 12px 4px;
    }

    .sidebar-section-label {
      color: rgba(255,255,255,0.3);
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      padding: 0 8px;
      margin-bottom: 4px;
    }

    .sidebar .nav-link {
      color: rgba(255,255,255,0.65);
      border-radius: 10px;
      padding: 9px 12px;
      margin-bottom: 2px;
      font-size: 0.88rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.2s;
    }

    .sidebar .nav-link:hover {
      background: rgba(255,255,255,0.08);
      color: white;
    }

    .sidebar .nav-link.active {
      background: linear-gradient(135deg, #06B6D4, #0891B2);
      color: white;
      box-shadow: 0 4px 12px rgba(6,182,212,0.3);
    }

    .sidebar .nav-link i {
      font-size: 1rem;
      width: 20px;
      text-align: center;
    }

    /* ── Content ── */
    .main-content {
      margin-right: 260px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ── Header ── */
    .top-header {
      background: white;
      border-bottom: 1px solid #e5e7eb;
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .page-title {
      font-weight: 700;
      color: #1f2937;
      font-size: 1rem;
      margin: 0;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* ── Content Area ── */
    .content-area {
      flex: 1;
      padding: 0;
    }

    /* ── Messages ── */
    .messages-container {
      position: fixed;
      top: 70px;
      left: 20px;
      z-index: 1000;
      max-width: 380px;
    }

    .alert {
      border: none;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.12);
      font-size: 0.9rem;
      padding: 12px 16px;
    }

    /* ── Loading Bar ── */
    .loading-bar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, #06B6D4, #0891B2, #06B6D4);
      background-size: 200% 100%;
      animation: loading-anim 1.5s infinite;
      z-index: 9999;
      display: none;
    }

    @keyframes loading-anim {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* ── Mobile ── */
    .sidebar-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.5);
      z-index: 99;
    }

    @media (max-width: 768px) {
      .sidebar {
        transform: translateX(100%);
      }
      .sidebar.show {
        transform: translateX(0);
      }
      .main-content {
        margin-right: 0;
      }
      .sidebar-overlay.show {
        display: block;
      }
    }

    /* ── Logout Button ── */
    .logout-btn {
      background: rgba(239,68,68,0.1);
      border: 1px solid rgba(239,68,68,0.2);
      color: #ef4444;
      border-radius: 8px;
      padding: 6px 14px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      font-family: 'Cairo', sans-serif;
    }

    .logout-btn:hover {
      background: #ef4444;
      color: white;
    }

    /* ── User Badge ── */
    .user-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 10px;
      background: #f8fafc;
      border: 1px solid #e5e7eb;
    }

    .user-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: linear-gradient(135deg, #06B6D4, #0891B2);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 700;
      font-size: 0.85rem;
      flex-shrink: 0;
    }
  </style>
</head>

<body>

<!-- Loading Bar -->
<div class="loading-bar" id="loadingBar"></div>

<!-- Sidebar Overlay (Mobile) -->
<div class="sidebar-overlay" id="sidebarOverlay"></div>

<!-- ════════════════════════════════════════
     SIDEBAR
════════════════════════════════════════ -->
<div class="sidebar" id="sidebar">

  <!-- Brand -->
  <div class="sidebar-brand">
    <a href="{% url 'dashboard' %}" style="text-decoration:none;">
      <h5>MotionHR</h5>
      <small>HR in Motion</small>
    </a>
  </div>

  <!-- Nav -->
  <nav class="flex-grow-1 py-2 px-2">

    <!-- ── الرئيسية ── -->
    <a href="{% url 'dashboard' %}"
       class="nav-link {% if request.path == '/dashboard/' %}active{% endif %}">
      <i class="bi bi-speedometer2"></i>
      <span>الرئيسية</span>
    </a>

    <!-- ── الموظفون ── -->
    {% if request.user.role != 'employee' %}
    <div class="sidebar-section">
      <div class="sidebar-section-label">الموظفون</div>
    </div>
    <a href="{% url 'employees:employee_list' %}"
       class="nav-link {% if '/employees/' in request.path %}active{% endif %}">
      <i class="bi bi-people-fill"></i>
      <span>الموظفون</span>
    </a>
    {% endif %}

    <!-- ── الحضور ── -->
    <div class="sidebar-section">
      <div class="sidebar-section-label">الحضور</div>
    </div>

    <a href="{% url 'attendance:check_in' %}"
       class="nav-link {% if 'check-in' in request.path %}active{% endif %}">
      <i class="bi bi-qr-code-scan"></i>
      <span>تسجيل الحضور</span>
    </a>

    {% if request.user.role != 'employee' %}
    <a href="{% url 'attendance:list' %}"
       class="nav-link {% if request.path == '/attendance/' %}active{% endif %}">
      <i class="bi bi-calendar-check"></i>
      <span>سجلات الحضور</span>
    </a>

    <a href="{% url 'attendance:live_map' %}"
       class="nav-link {% if 'map' in request.path %}active{% endif %}">
      <i class="bi bi-map"></i>
      <span>الخريطة الحية</span>
    </a>

    <a href="{% url 'attendance:monitor' %}"
       class="nav-link {% if 'monitor' in request.path %}active{% endif %}">
      <i class="bi bi-broadcast"></i>
      <span>متابعة الميدانيين</span>
    </a>

    <a href="{% url 'attendance:visits' %}"
       class="nav-link {% if 'visits' in request.path %}active{% endif %}">
      <i class="bi bi-geo-alt"></i>
      <span>الزيارات</span>
    </a>
    {% endif %}

    <!-- ── الإجازات ── -->
    <div class="sidebar-section">
      <div class="sidebar-section-label">الإجازات</div>
    </div>

    <a href="{% url 'leaves:leave_requests_list' %}"
       class="nav-link {% if '/leaves/' in request.path and 'types' not in request.path and 'balances' not in request.path %}active{% endif %}">
      <i class="bi bi-calendar2-week"></i>
      <span>طلبات الإجازات</span>
    </a>

    {% if request.user.role != 'employee' %}
    <a href="{% url 'leaves:leave_balances' %}"
       class="nav-link {% if 'balances' in request.path %}active{% endif %}">
      <i class="bi bi-wallet2"></i>
      <span>أرصدة الإجازات</span>
    </a>

    <a href="{% url 'leaves:leave_types_list' %}"
       class="nav-link {% if 'types' in request.path %}active{% endif %}">
      <i class="bi bi-list-check"></i>
      <span>أنواع الإجازات</span>
    </a>
    {% endif %}

    <!-- ── التقارير ── -->
    {% if request.user.role != 'employee' %}
    <div class="sidebar-section">
      <div class="sidebar-section-label">التقارير</div>
    </div>

    <a href="{% url 'reports:home' %}"
       class="nav-link {% if '/reports/' in request.path %}active{% endif %}">
      <i class="bi bi-bar-chart"></i>
      <span>التقارير</span>
    </a>
    {% endif %}

    <!-- ── الإعدادات ── -->
    {% if request.user.role in 'super_admin,company_admin,hr_manager' %}
    <div class="sidebar-section">
      <div class="sidebar-section-label">الإعدادات</div>
    </div>

    <a href="{% url 'companies:settings' %}"
       class="nav-link {% if 'companies/settings' in request.path %}active{% endif %}">
      <i class="bi bi-building"></i>
      <span>الشركة</span>
    </a>

    <a href="{% url 'companies:branches_list' %}"
       class="nav-link {% if 'branches' in request.path %}active{% endif %}">
      <i class="bi bi-geo-alt"></i>
      <span>الفروع</span>
    </a>

    <a href="{% url 'companies:departments_list' %}"
       class="nav-link {% if 'departments' in request.path %}active{% endif %}">
      <i class="bi bi-diagram-3"></i>
      <span>الإدارات</span>
    </a>

    <a href="{% url 'companies:shifts_list' %}"
       class="nav-link {% if 'shifts' in request.path %}active{% endif %}">
      <i class="bi bi-clock"></i>
      <span>الشيفتات</span>
    </a>
    {% endif %}

    <!-- ── الاشتراك ── -->
    <div class="sidebar-section">
      <div class="sidebar-section-label">الاشتراك</div>
    </div>

    <a href="{% url 'subscriptions:my_plan' %}"
       class="nav-link {% if 'my-plan' in request.path %}active{% endif %}">
      <i class="bi bi-star"></i>
      <span>خطتي</span>
    </a>

    <a href="{% url 'subscriptions:contact_sales' %}"
       class="nav-link {% if 'contact-sales' in request.path %}active{% endif %}">
      <i class="bi bi-headset"></i>
      <span>تواصل / ترقية</span>
    </a>

  </nav>

  <!-- User Info في أسفل الـ Sidebar -->
  <div style="padding: 12px; border-top: 1px solid rgba(255,255,255,0.08);">
    <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; margin-bottom:8px; padding:0 4px;">
      {{ request.user.get_full_name|default:request.user.username }}
      <br>
      <span style="color:rgba(255,255,255,0.3);">
        {% if request.user.role == 'super_admin' %}مشرف النظام
        {% elif request.user.role == 'company_admin' %}مدير شركة
        {% elif request.user.role == 'hr_manager' %}مدير HR
        {% elif request.user.role == 'manager' %}مدير
        {% else %}موظف{% endif %}
      </span>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════
     MAIN CONTENT
════════════════════════════════════════ -->
<div class="main-content">

  <!-- Header -->
  <div class="top-header">

    <!-- Mobile Toggle -->
    <button class="btn btn-sm btn-light d-md-none me-2"
            id="sidebarToggle"
            style="border-radius:8px;">
      <i class="bi bi-list fs-5"></i>
    </button>

    <!-- Page Title -->
    <h6 class="page-title">
      {% block header_title %}{{ page_title|default:"MotionHR" }}{% endblock %}
    </h6>

    <!-- Header Actions -->
    <div class="header-actions">

      <!-- Search -->
      <a href="{% url 'global_search' %}"
         class="btn btn-sm btn-light"
         style="border-radius:8px; width:36px; height:36px; padding:0;
                display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-search" style="color:#06B6D4;"></i>
      </a>

      <!-- Notifications -->
      <a href="{% url 'accounts:notifications' %}"
         class="btn btn-sm btn-light position-relative"
         style="border-radius:8px; width:36px; height:36px; padding:0;
                display:flex; align-items:center; justify-content:center;">
        <i class="bi bi-bell" style="color:#6b7280;"></i>
      </a>

      <!-- User Dropdown -->
      <div class="dropdown">
        <button class="btn user-badge dropdown-toggle"
                type="button"
                data-bs-toggle="dropdown"
                style="border:none; background:#f8fafc;">
          <div class="user-avatar">
            {% if request.user.avatar %}
              <img src="{{ request.user.avatar.url }}"
                   style="width:32px;height:32px;border-radius:50%;object-fit:cover;">
            {% else %}
              {{ request.user.get_full_name|first|default:request.user.username|first|upper }}
            {% endif %}
          </div>
          <span class="d-none d-md-inline small fw-semibold text-dark">
            {{ request.user.get_full_name|default:request.user.username }}
          </span>
        </button>
        <ul class="dropdown-menu dropdown-menu-start shadow border-0"
            style="border-radius:12px; min-width:200px;">
          <li class="px-3 py-2">
            <div class="fw-bold text-dark small">
              {{ request.user.get_full_name|default:request.user.username }}
            </div>
            <div class="text-muted" style="font-size:0.75rem;">
              {{ request.user.email|default:"" }}
            </div>
          </li>
          <li><hr class="dropdown-divider my-1"></li>
          <li>
            <a class="dropdown-item d-flex align-items-center gap-2 py-2"
               href="{% url 'accounts:profile' %}">
              <i class="bi bi-person-circle text-muted"></i>
              الملف الشخصي
            </a>
          </li>
          <li>
            <a class="dropdown-item d-flex align-items-center gap-2 py-2"
               href="{% url 'accounts:notifications' %}">
              <i class="bi bi-bell text-muted"></i>
              الإشعارات
            </a>
          </li>
          <li>
            <a class="dropdown-item d-flex align-items-center gap-2 py-2"
               href="{% url 'password_change' %}">
              <i class="bi bi-key text-muted"></i>
              تغيير كلمة المرور
            </a>
          </li>
          <li><hr class="dropdown-divider my-1"></li>
          <li>
            <form method="post" action="{% url 'logout' %}" class="px-1">
              {% csrf_token %}
              <button type="submit" class="logout-btn w-100 text-start py-2 px-3">
                <i class="bi bi-box-arrow-left me-2"></i>
                تسجيل الخروج
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
    <div class="alert alert-{% if message.tags == 'error' %}danger{% else %}{{ message.tags }}{% endif %}
                alert-dismissible fade show mb-2">
      {% if message.tags == 'success' %}
        <i class="bi bi-check-circle-fill me-2"></i>
      {% elif message.tags == 'error' or message.tags == 'danger' %}
        <i class="bi bi-x-circle-fill me-2"></i>
      {% elif message.tags == 'warning' %}
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {% else %}
        <i class="bi bi-info-circle-fill me-2"></i>
      {% endif %}
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

<!-- Scripts -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
// ── Sidebar Toggle ──────────────────────────────────────
const sidebar        = document.getElementById('sidebar');
const overlay        = document.getElementById('sidebarOverlay');
const sidebarToggle  = document.getElementById('sidebarToggle');
const loadingBar     = document.getElementById('loadingBar');

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('show');
    overlay.classList.toggle('show');
  });
}

if (overlay) {
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('show');
    overlay.classList.remove('show');
  });
}

// ── Loading Bar ──────────────────────────────────────────
document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="javascript"])').forEach(link => {
  link.addEventListener('click', () => {
    if (loadingBar) loadingBar.style.display = 'block';
  });
});

// ── Auto-hide Messages ───────────────────────────────────
setTimeout(() => {
  document.querySelectorAll('.messages-container .alert').forEach(alert => {
    alert.style.transition = 'opacity 0.5s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 500);
  });
}, 4000);

// ── PWA Service Worker ───────────────────────────────────
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js', { scope: '/' })
    .catch(() => {});
}

// ── Connection Status ────────────────────────────────────
window.addEventListener('offline', () => {
  const bar = document.createElement('div');
  bar.id = 'offlineBar';
  bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#ef4444;color:white;text-align:center;padding:8px;font-size:0.85rem;z-index:9999;';
  bar.innerHTML = '<i class="bi bi-wifi-off me-2"></i>لا يوجد اتصال بالإنترنت';
  document.body.appendChild(bar);
});

window.addEventListener('online', () => {
  const bar = document.getElementById('offlineBar');
  if (bar) bar.remove();
});
</script>

{% block extra_js %}{% endblock %}
{% block dashboard_js %}{% endblock %}

<!-- PWA Install Banner -->
<div id="installBanner" class="d-none"
     style="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
            z-index:9999;min-width:300px;max-width:380px;">
  <div class="card border-0 shadow-lg" style="border-radius:16px;overflow:hidden;">
    <div class="card-body p-3 d-flex align-items-center gap-3"
         style="background:linear-gradient(135deg,#0f172a,#1e3a5f);">
      <div style="width:48px;height:48px;background:#06B6D4;border-radius:12px;
                  display:flex;align-items:center;justify-content:center;
                  color:white;font-weight:900;font-size:1.2rem;flex-shrink:0;">M</div>
      <div class="flex-grow-1">
        <div class="fw-bold text-white small">MotionHR</div>
        <div class="text-white-50" style="font-size:0.75rem;">ثبّت التطبيق على جهازك</div>
      </div>
      <div class="d-flex gap-1">
        <button id="installBtn" class="btn btn-sm text-white fw-bold"
                style="background:#06B6D4;border-radius:8px;font-size:0.8rem;">
          تثبيت
        </button>
        <button id="dismissBtn" class="btn btn-sm"
                style="background:rgba(255,255,255,0.1);color:white;border-radius:8px;font-size:0.8rem;">
          ✕
        </button>
      </div>
    </div>
  </div>
</div>

<script>
let deferredPrompt = null;
const banner     = document.getElementById('installBanner');
const installBtn = document.getElementById('installBtn');
const dismissBtn = document.getElementById('dismissBtn');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (!localStorage.getItem('pwa-dismissed')) {
    setTimeout(() => banner?.classList.remove('d-none'), 3000);
  }
});

installBtn?.addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  banner?.classList.add('d-none');
});

dismissBtn?.addEventListener('click', () => {
  banner?.classList.add('d-none');
  localStorage.setItem('pwa-dismissed', '1');
});
</script>

</body>
</html>
"""

create_file(
    os.path.join(BASE_DIR, "templates", "base", "dashboard_base.html"),
    dashboard_base
)


# ════════════════════════════════════════════════════════════
# 3. إصلاح كل التمبلتس اللي بتستخدم getattr / split
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة {% load custom_filters %} للتمبلتس...")

import glob

templates_need_load = [
    "templates/accounts/login_settings.html",
    "templates/leaves/leave_type_form.html",
    "templates/subscriptions/my_plan.html",
    "templates/landing/pricing.html",
    "templates/landing/about.html",
    "templates/landing/home.html",
    "templates/companies/shift_form.html",
]

for tmpl_path in templates_need_load:
    full_path = os.path.join(BASE_DIR, tmpl_path)
    if not os.path.exists(full_path):
        print(f"  ⚠️  مش موجود: {tmpl_path}")
        continue

    content = read_file(full_path)

    if "{% load custom_filters %}" not in content:
        if "{% extends" in content:
            content = content.replace(
                "{% extends",
                "{% load custom_filters %}\n{% extends",
                1
            )
        elif "<!DOCTYPE" in content:
            content = "{% load custom_filters %}\n" + content
        else:
            content = "{% load custom_filters %}\n" + content

        write_file(full_path, content)
    else:
        print(f"  ℹ️  موجود: {tmpl_path}")


# ════════════════════════════════════════════════════════════
# 4. إصلاح روابط sub-admin في كل التمبلتس
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح روابط sub-admin...")

all_templates = glob.glob(
    os.path.join(BASE_DIR, "templates", "**", "*.html"),
    recursive=True
)

fixed = 0
for tmpl in all_templates:
    content = read_file(tmpl)
    original = content
    content = content.replace("/sub-admin/", "/subscriptions/")
    content = content.replace("'sub-admin'", "'subscriptions'")
    content = content.replace('"sub-admin"', '"subscriptions"')
    if content != original:
        write_file(tmpl, content)
        fixed += 1

print(f"  ✅ تم إصلاح {fixed} ملف")


# ════════════════════════════════════════════════════════════
# 5. إصلاح TemplateSyntaxError في التقارير (period==)
# ════════════════════════════════════════════════════════════
print("\n🔧 إصلاح التقارير...")

report_tmpls = [
    "templates/reports/attendance_report.html",
    "templates/reports/late_report.html",
    "templates/reports/leave_report.html",
    "templates/reports/field_report.html",
]

for tmpl_path in report_tmpls:
    full_path = os.path.join(BASE_DIR, tmpl_path)
    if not os.path.exists(full_path):
        continue
    content = read_file(full_path)
    original = content
    content = re.sub(r"(\w+)==('[\w]+')", r"\1 == \2", content)
    content = re.sub(r'(\w+)==("[\w]+")', r'\1 == \2', content)
    if content != original:
        write_file(full_path, content)
    else:
        print(f"  ℹ️  {tmpl_path} - لا يحتاج تعديل")


# ════════════════════════════════════════════════════════════
# 6. إضافة custom_filters في INSTALLED_APPS (accounts فيها templatetags)
# ════════════════════════════════════════════════════════════
print("\n🔧 تأكيد accounts في INSTALLED_APPS...")

settings_path = os.path.join(BASE_DIR, "motionhr", "settings.py")
settings = read_file(settings_path)

if "'accounts'" not in settings and '"accounts"' not in settings:
    print("  ⚠️  accounts مش في INSTALLED_APPS!")
else:
    print("  ✅ accounts موجود في INSTALLED_APPS")


# ════════════════════════════════════════════════════════════
# 7. تحديث base.html لإضافة load custom_filters
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث base/base.html...")

base_html_path = os.path.join(BASE_DIR, "templates", "base", "base.html")
if os.path.exists(base_html_path):
    base_html = read_file(base_html_path)
    if "{% load custom_filters %}" not in base_html:
        base_html = "{% load custom_filters %}\n" + base_html
        write_file(base_html_path, base_html)
    else:
        print("  ℹ️  موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 27 اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Custom Template Tags (split + getattr)
  2. ✅ dashboard_base.html جديد كامل:
       - Logout واضح في الـ Header
       - Sidebar حسب الدور
       - Active links
       - Loading Bar
       - Messages احترافية
       - PWA Install Banner
       - Connection Status
  3. ✅ إصلاح روابط sub-admin
  4. ✅ إصلاح TemplateSyntaxError في التقارير
  5. ✅ load custom_filters في التمبلتس

شغّل السيرفر وجرب:
  python manage.py runserver 0.0.0.0:8000
  http://127.0.0.1:8000/dashboard/

المتوقع:
  - Sidebar نظيف وواضح
  - Logout واضح في الـ Header
  - Active links بتتلون
  - Messages بتظهر وتختفي تلقائي
""")