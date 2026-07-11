"""
Patch 49b — Employee List Live Search

الهدف:
- إضافة Live Search حرف بحرف في صفحة الموظفين
- البحث في الاسم / الكود / الوظيفة / الفرع / الإدارة / التليفون / الإيميل
- إظهار النتائج فورًا بدون ضغط زر
- عدم كسر صفحة الموظفين الحالية

الملفات التي سيتم تعديلها:
- employees/views.py
- employees/urls.py
- templates/employees/list.html
"""

import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")
django.setup()


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
print("Patch 49b — Employee List Live Search")
print("=" * 60)


# ═════════════════════════════════════════════════════════════
# Step 1: تحديث employees/views.py
# ═════════════════════════════════════════════════════════════
print("\n📌 Step 1: تحديث employees/views.py")

views_path = "employees/views.py"
views_content = read_file(views_path)
if views_content is None:
    raise SystemExit("❌ ملف employees/views.py غير موجود")

# 1) إضافة JsonResponse إلى import لو مش موجود
if "from django.http import HttpResponse, JsonResponse" not in views_content:
    if "from django.http import HttpResponse" in views_content:
        views_content = views_content.replace(
            "from django.http import HttpResponse",
            "from django.http import HttpResponse, JsonResponse"
        )
    elif "from django.http import" in views_content and "JsonResponse" not in views_content:
        views_content = views_content.replace(
            "from django.http import",
            "from django.http import JsonResponse,",
            1
        )

# 2) توسيع البحث في employee_list لو snippet القديم موجود
old_search_snippet = """    # البحث
    search = request.GET.get('search', '').strip()
    if search:
        employees = employees.filter(
            Q(employee_code__icontains=search) |
            Q(first_name_ar__icontains=search) |
            Q(last_name_ar__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
"""

new_search_snippet = """    # البحث
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
"""

if old_search_snippet in views_content:
    views_content = views_content.replace(old_search_snippet, new_search_snippet)
    print("   ✅ تم توسيع البحث داخل employee_list")
else:
    print("   ℹ️ لم يتم العثور على snippet القديم — سيتم إضافة API فقط")

# 3) إضافة API search view في آخر الملف لو مش موجودة
api_view_code = '''

@login_required
@feature_required('employees_management')
def employee_search_api(request):
    """API للبحث الحي في الموظفين — Patch 49b"""
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    department_filter = request.GET.get('department', '').strip()

    employees = get_accessible_employees(request.user).select_related(
        'branch', 'department', 'job_title', 'direct_manager'
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

    employees = employees.order_by('employee_code')[:100]

    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'employee_code': emp.employee_code or '',
            'full_name_ar': getattr(emp, 'full_name_ar', '') or '',
            'job_title': (
                getattr(emp.job_title, 'name_ar', None)
                or getattr(emp.job_title, 'name_en', None)
                or '—'
            ) if emp.job_title else '—',
            'department': (
                getattr(emp.department, 'name_ar', None)
                or getattr(emp.department, 'name_en', None)
                or '—'
            ) if emp.department else '—',
            'branch': (
                getattr(emp.branch, 'name_ar', None)
                or getattr(emp.branch, 'name_en', None)
                or '—'
            ) if emp.branch else '—',
            'phone': emp.phone or '—',
            'email': emp.email or '—',
            'status': emp.get_status_display() if hasattr(emp, 'get_status_display') else (emp.status or '—'),
            'manager': (
                getattr(emp.direct_manager, 'full_name_ar', None) or '—'
            ) if emp.direct_manager else '—',
        })

    return JsonResponse({
        'success': True,
        'count': len(results),
        'results': results,
    })
'''

if "def employee_search_api(request):" not in views_content:
    views_content = views_content.rstrip() + "\n" + api_view_code + "\n"
    print("   ✅ تم إضافة employee_search_api")
else:
    print("   ℹ️ employee_search_api موجودة بالفعل")

write_file(views_path, views_content)


# ═════════════════════════════════════════════════════════════
# Step 2: تحديث employees/urls.py
# ═════════════════════════════════════════════════════════════
print("\n📌 Step 2: تحديث employees/urls.py")

urls_path = "employees/urls.py"
urls_content = read_file(urls_path)
if urls_content is None:
    raise SystemExit("❌ ملف employees/urls.py غير موجود")

search_url_line = "    path('api/search/', views.employee_search_api, name='search_api'),"

if "name='search_api'" not in urls_content:
    if "urlpatterns = [" in urls_content:
        urls_content = urls_content.replace(
            "urlpatterns = [",
            "urlpatterns = [\n" + search_url_line,
            1
        )
        print("   ✅ تم إضافة route للبحث الحي")
    else:
        print("   ⚠️ لم يتم العثور على urlpatterns بشكل متوقع")
else:
    print("   ℹ️ route البحث الحي موجود بالفعل")

write_file(urls_path, urls_content)


# ═════════════════════════════════════════════════════════════
# Step 3: استبدال templates/employees/list.html
# ═════════════════════════════════════════════════════════════
print("\n📌 Step 3: تحديث templates/employees/list.html")

employees_list_template = """{% extends 'base/dashboard_base.html' %}

{% block title %}قائمة الموظفين{% endblock %}

{% block extra_css %}
<style>
  .search-hero {
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fdff 100%);
  }

  .search-box {
    position: relative;
  }

  .search-box .form-control {
    padding-right: 44px;
    border-radius: 14px;
    height: 48px;
    font-size: 1rem;
  }

  .search-box .search-icon {
    position: absolute;
    top: 50%;
    right: 14px;
    transform: translateY(-50%);
    color: #64748b;
    z-index: 3;
  }

  .live-badge {
    border-radius: 999px;
    font-size: .78rem;
    padding: .45rem .8rem;
  }

  .search-note {
    font-size: .82rem;
    color: #64748b;
  }

  .result-pill {
    border-radius: 999px;
    font-size: .78rem;
    padding: .35rem .7rem;
  }

  .table thead th {
    white-space: nowrap;
  }

  .employee-name {
    font-weight: 700;
    color: #0f172a;
  }

  .employee-sub {
    font-size: .78rem;
    color: #64748b;
  }

  .search-loading {
    display: none;
  }

  .empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #64748b;
  }

  .empty-state i {
    font-size: 2rem;
    opacity: .35;
  }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <!-- Header -->
  <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
    <div>
      <h4 class="mb-1 fw-bold">
        <i class="bi bi-people-fill text-primary me-2"></i>قائمة الموظفين
      </h4>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0 small">
          <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">الرئيسية</a></li>
          <li class="breadcrumb-item active">الموظفون</li>
        </ol>
      </nav>
    </div>

    <div class="d-flex gap-2 flex-wrap">
      <a href="?export=excel" class="btn btn-success">
        <i class="bi bi-file-earmark-excel me-1"></i>تصدير Excel
      </a>
      <button type="button" class="btn btn-outline-secondary" disabled title="سيتم تنفيذ PDF في باتش مستقل">
        <i class="bi bi-file-earmark-pdf me-1"></i>PDF قريبًا
      </button>
    </div>
  </div>

  <!-- Live Search -->
  <div class="card border-0 shadow-sm search-hero mb-4">
    <div class="card-body p-4">
      <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
        <div>
          <h5 class="mb-1 fw-bold">
            <i class="bi bi-search text-primary me-2"></i>البحث الذكي عن الموظفين
          </h5>
          <div class="search-note">
            اكتب أي حرف من الاسم أو الكود أو الوظيفة أو الإدارة أو الفرع أو رقم الهاتف
          </div>
        </div>
        <span class="badge bg-info-subtle text-info border border-info-subtle live-badge">
          <i class="bi bi-lightning-charge-fill me-1"></i>Live Search
        </span>
      </div>

      <form method="get" id="employee-filter-form">
        <div class="row g-3">
          <div class="col-lg-7">
            <div class="search-box">
              <i class="bi bi-search search-icon"></i>
              <input
                type="text"
                class="form-control"
                id="live-search-input"
                name="search"
                value="{{ request.GET.search }}"
                placeholder="ابحث بالاسم / الكود / الوظيفة / الإدارة / الفرع / التليفون..."
                autocomplete="off">
            </div>
          </div>

          <div class="col-lg-2">
            <select class="form-select" id="branch-filter" name="branch">
              <option value="">كل الفروع</option>
              {% for branch in branches %}
                <option value="{{ branch.id }}" {% if request.GET.branch == branch.id|stringformat:'s' %}selected{% endif %}>
                  {{ branch.name_ar|default:branch.name_en }}
                </option>
              {% endfor %}
            </select>
          </div>

          <div class="col-lg-2">
            <select class="form-select" id="department-filter" name="department">
              <option value="">كل الإدارات</option>
              {% for department in departments %}
                <option value="{{ department.id }}" {% if request.GET.department == department.id|stringformat:'s' %}selected{% endif %}>
                  {{ department.name_ar|default:department.name_en }}
                </option>
              {% endfor %}
            </select>
          </div>

          <div class="col-lg-1">
            <button type="submit" class="btn btn-primary w-100">
              <i class="bi bi-funnel"></i>
            </button>
          </div>
        </div>
      </form>

      <div class="d-flex align-items-center justify-content-between mt-3 flex-wrap gap-2">
        <div class="search-note">
          النتائج تظهر تلقائيًا أثناء الكتابة بدون الضغط على زر
        </div>
        <div class="search-loading" id="search-loading">
          <span class="spinner-border spinner-border-sm text-primary me-2"></span>
          <span class="small text-muted">جارٍ البحث...</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Live Search Results -->
  <div class="card border-0 shadow-sm mb-4" id="live-results-card" style="display:none;">
    <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
      <div class="fw-bold">
        <i class="bi bi-lightning-charge text-primary me-2"></i>نتائج البحث المباشر
      </div>
      <span class="badge bg-primary result-pill" id="live-results-count">0 نتيجة</span>
    </div>
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>الموظف</th>
              <th>الكود</th>
              <th>الوظيفة</th>
              <th>الإدارة</th>
              <th>الفرع</th>
              <th>المدير المباشر</th>
              <th>التليفون</th>
              <th>الإيميل</th>
              <th>الحالة</th>
            </tr>
          </thead>
          <tbody id="live-results-body">
          </tbody>
        </table>
      </div>
      <div class="empty-state" id="live-empty-state" style="display:none;">
        <i class="bi bi-search"></i>
        <div class="mt-2">لا توجد نتائج مطابقة</div>
      </div>
    </div>
  </div>

  <!-- Server Rendered Default List -->
  <div id="default-list-wrapper">
    <div class="card border-0 shadow-sm">
      <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
        <div class="fw-bold">
          <i class="bi bi-list-ul text-primary me-2"></i>قائمة الموظفين
        </div>
        <span class="badge bg-secondary result-pill">
          {{ page_obj.paginator.count }} موظف
        </span>
      </div>

      <div class="card-body p-0">
        {% if page_obj %}
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>الموظف</th>
                <th>الكود</th>
                <th>الوظيفة</th>
                <th>الإدارة</th>
                <th>الفرع</th>
                <th>المدير المباشر</th>
                <th>التليفون</th>
                <th>الإيميل</th>
                <th>الحالة</th>
              </tr>
            </thead>
            <tbody>
              {% for emp in page_obj %}
              <tr>
                <td>
                  <div class="employee-name">{{ emp.full_name_ar }}</div>
                  <div class="employee-sub">
                    {{ emp.national_id|default:"—" }}
                  </div>
                </td>
                <td>{{ emp.employee_code }}</td>
                <td>{{ emp.job_title.name_ar|default:emp.job_title.name_en|default:"—" }}</td>
                <td>{{ emp.department.name_ar|default:emp.department.name_en|default:"—" }}</td>
                <td>{{ emp.branch.name_ar|default:emp.branch.name_en|default:"—" }}</td>
                <td>{{ emp.direct_manager.full_name_ar|default:"—" }}</td>
                <td>{{ emp.phone|default:"—" }}</td>
                <td>{{ emp.email|default:"—" }}</td>
                <td>
                  <span class="badge bg-light text-dark border">
                    {{ emp.get_status_display|default:emp.status }}
                  </span>
                </td>
              </tr>
              {% empty %}
              <tr>
                <td colspan="9">
                  <div class="empty-state">
                    <i class="bi bi-people"></i>
                    <div class="mt-2">لا يوجد موظفون</div>
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>

        {% if page_obj.has_other_pages %}
        <div class="p-3">
          <nav>
            <ul class="pagination pagination-sm justify-content-center mb-0">
              {% if page_obj.has_previous %}
              <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.previous_page_number }}&branch={{ request.GET.branch }}&department={{ request.GET.department }}&search={{ request.GET.search }}">
                  السابق
                </a>
              </li>
              {% endif %}

              <li class="page-item active">
                <span class="page-link">{{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span>
              </li>

              {% if page_obj.has_next %}
              <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.next_page_number }}&branch={{ request.GET.branch }}&department={{ request.GET.department }}&search={{ request.GET.search }}">
                  التالي
                </a>
              </li>
              {% endif %}
            </ul>
          </nav>
        </div>
        {% endif %}

        {% endif %}
      </div>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_js %}
<script>
(function() {
  const searchInput = document.getElementById('live-search-input');
  const branchFilter = document.getElementById('branch-filter');
  const departmentFilter = document.getElementById('department-filter');
  const loadingBox = document.getElementById('search-loading');

  const defaultWrapper = document.getElementById('default-list-wrapper');
  const liveCard = document.getElementById('live-results-card');
  const liveBody = document.getElementById('live-results-body');
  const liveCount = document.getElementById('live-results-count');
  const emptyState = document.getElementById('live-empty-state');

  let timer = null;

  function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function showDefaultList() {
    liveCard.style.display = 'none';
    defaultWrapper.style.display = 'block';
    emptyState.style.display = 'none';
    liveBody.innerHTML = '';
  }

  function showLoading(show) {
    loadingBox.style.display = show ? 'inline-flex' : 'none';
  }

  function renderResults(results) {
    liveBody.innerHTML = '';

    if (!results.length) {
      emptyState.style.display = 'block';
      return;
    }

    emptyState.style.display = 'none';

    let html = '';
    results.forEach(emp => {
      html += `
        <tr>
          <td>
            <div class="employee-name">${escapeHtml(emp.full_name_ar || '—')}</div>
            <div class="employee-sub">${escapeHtml(emp.phone || '—')}</div>
          </td>
          <td>${escapeHtml(emp.employee_code || '—')}</td>
          <td>${escapeHtml(emp.job_title || '—')}</td>
          <td>${escapeHtml(emp.department || '—')}</td>
          <td>${escapeHtml(emp.branch || '—')}</td>
          <td>${escapeHtml(emp.manager || '—')}</td>
          <td>${escapeHtml(emp.phone || '—')}</td>
          <td>${escapeHtml(emp.email || '—')}</td>
          <td><span class="badge bg-light text-dark border">${escapeHtml(emp.status || '—')}</span></td>
        </tr>
      `;
    });

    liveBody.innerHTML = html;
  }

  function runLiveSearch() {
    const q = (searchInput.value || '').trim();
    const branch = branchFilter.value || '';
    const department = departmentFilter.value || '';

    if (!q) {
      showDefaultList();
      showLoading(false);
      return;
    }

    defaultWrapper.style.display = 'none';
    liveCard.style.display = 'block';
    liveCount.textContent = '...';
    showLoading(true);

    const params = new URLSearchParams({
      q: q,
      branch: branch,
      department: department
    });

    fetch("{% url 'employees:search_api' %}?" + params.toString(), {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => response.json())
    .then(data => {
      const results = data.results || [];
      liveCount.textContent = `${data.count || 0} نتيجة`;
      renderResults(results);
      showLoading(false);
    })
    .catch(error => {
      liveCount.textContent = '0 نتيجة';
      liveBody.innerHTML = '';
      emptyState.style.display = 'block';
      showLoading(false);
    });
  }

  function debounceSearch() {
    clearTimeout(timer);
    timer = setTimeout(runLiveSearch, 250);
  }

  searchInput.addEventListener('input', debounceSearch);
  branchFilter.addEventListener('change', runLiveSearch);
  departmentFilter.addEventListener('change', runLiveSearch);

  // لو الصفحة مفتوحة وفيها search query بالفعل
  if ((searchInput.value || '').trim()) {
    runLiveSearch();
  }
})();
</script>
{% endblock %}
"""

write_file("templates/employees/list.html", employees_list_template)


print("\n" + "=" * 60)
print("✅ Patch 49b اكتمل")
print("=" * 60)
print("""
اللي اتعمل:
  ✅ Live Search API للموظفين
  ✅ توسيع البحث ليشمل الوظيفة / الفرع / الإدارة
  ✅ تحديث صفحة قائمة الموظفين بواجهة بحث مباشر
  ✅ النتائج تظهر حرف بحرف بدون ضغط زر

الملفات المعدلة:
  ✅ employees/views.py
  ✅ employees/urls.py
  ✅ templates/employees/list.html

شغّل:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000
""")