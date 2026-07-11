#!/usr/bin/env python3
"""
Patch 31b: Requests System Templates
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 31b: Requests Templates")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. قائمة الطلبات
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء list.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "requests_app", "list.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}الطلبات{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h4 class="fw-bold mb-1">
        <i class="bi bi-inbox me-2" style="color:#06B6D4;"></i>
        الطلبات
      </h4>
      <p class="text-muted mb-0">كل طلباتك في مكان واحد</p>
    </div>
    <a href="{% url 'requests_app:add' %}"
       class="btn text-white fw-bold"
       style="background:#06B6D4; border-radius:10px;">
      <i class="bi bi-plus-lg me-1"></i>
      طلب جديد
    </a>
  </div>

  <!-- فلترة -->
  <div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-3">
      <form method="get" class="d-flex gap-3 flex-wrap align-items-center">
        <select name="status" class="form-select"
                style="max-width:200px;" onchange="this.form.submit()">
          <option value="">كل الحالات</option>
          <option value="pending"
            {% if status_filter == 'pending' %}selected{% endif %}>
            قيد الانتظار
          </option>
          <option value="approved"
            {% if status_filter == 'approved' %}selected{% endif %}>
            موافق عليه
          </option>
          <option value="rejected"
            {% if status_filter == 'rejected' %}selected{% endif %}>
            مرفوض
          </option>
          <option value="cancelled"
            {% if status_filter == 'cancelled' %}selected{% endif %}>
            ملغي
          </option>
        </select>
        <a href="{% url 'requests_app:list' %}"
           class="btn btn-light btn-sm">إعادة تعيين</a>
      </form>
    </div>
  </div>

  {% if requests %}
  <div class="card border-0 shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead style="background:#f8fafc;">
          <tr>
            <th class="px-4 py-3">الموضوع</th>
            <th>النوع</th>
            <th>الموظف</th>
            <th>تاريخ الطلب</th>
            <th>الأولوية</th>
            <th>الحالة</th>
            <th class="text-center">إجراءات</th>
          </tr>
        </thead>
        <tbody>
          {% for req in requests %}
          <tr>
            <td class="px-4">
              <div class="fw-semibold">{{ req.subject }}</div>
              <small class="text-muted">
                {{ req.request_type.category.name }}
              </small>
            </td>
            <td>
              <span class="badge bg-light text-dark border">
                {{ req.request_type.name }}
              </span>
            </td>
            <td class="text-muted small">
              {{ req.employee.full_name_ar }}
            </td>
            <td class="text-muted small">
              {{ req.created_at|date:"d/m/Y" }}
            </td>
            <td>
              {% if req.priority == 'urgent' %}
                <span class="badge bg-danger">عاجل</span>
              {% else %}
                <span class="badge bg-secondary">عادي</span>
              {% endif %}
            </td>
            <td>
              <span class="badge bg-{{ req.status_color }}">
                <i class="bi bi-{{ req.status_icon }} me-1"></i>
                {{ req.get_status_display }}
              </span>
            </td>
            <td class="text-center">
              <a href="{% url 'requests_app:detail' req.pk %}"
                 class="btn btn-sm btn-outline-primary">
                <i class="bi bi-eye"></i>
              </a>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  {% else %}
  <div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
      <i class="bi bi-inbox" style="font-size:4rem; color:#d1d5db;"></i>
      <h5 class="mt-3 fw-bold text-muted">لا يوجد طلبات</h5>
      <a href="{% url 'requests_app:add' %}"
         class="btn mt-2 text-white"
         style="background:#06B6D4;">
        <i class="bi bi-plus me-1"></i>أضف طلبك الأول
      </a>
    </div>
  </div>
  {% endif %}

</div>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 2. إضافة طلب جديد
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء add.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "requests_app", "add.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}طلب جديد{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'requests_app:list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">طلب جديد</h4>
  </div>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form method="post" enctype="multipart/form-data" id="requestForm">
            {% csrf_token %}
            <div class="row g-3">

              <!-- الموظف -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">
                  الموظف <span class="text-danger">*</span>
                </label>
                {% if request.user.role == 'employee' and request.current_employee %}
                  <input type="hidden" name="employee"
                         value="{{ request.current_employee.pk }}">
                  <input type="text" class="form-control bg-light" readonly
                         value="{{ request.current_employee.full_name_ar }}">
                {% else %}
                  <select name="employee" class="form-select" required>
                    <option value="">اختر الموظف</option>
                    {% for emp in employees %}
                    <option value="{{ emp.pk }}">
                      {{ emp.full_name_ar }} ({{ emp.employee_code }})
                    </option>
                    {% endfor %}
                  </select>
                {% endif %}
              </div>

              <!-- الأولوية -->
              <div class="col-md-6">
                <label class="form-label fw-semibold small">الأولوية</label>
                <select name="priority" class="form-select">
                  <option value="normal">عادي</option>
                  <option value="urgent">عاجل</option>
                </select>
              </div>

              <!-- نوع الطلب -->
              <div class="col-12">
                <label class="form-label fw-semibold small">
                  نوع الطلب <span class="text-danger">*</span>
                </label>

                <!-- الفئات -->
                <div class="row g-2 mb-3" id="categoriesSection">
                  {% for cat in categories %}
                  <div class="col-6 col-md-3">
                    <div class="card border-2 category-card text-center p-2"
                         style="cursor:pointer; border-color:#e5e7eb; border-radius:10px;"
                         data-cat="{{ cat.pk }}">
                      <i class="bi {{ cat.icon }} fs-4 mb-1"
                         style="color:{{ cat.color }};"></i>
                      <div style="font-size:0.78rem; font-weight:600; color:#374151;">
                        {{ cat.name }}
                      </div>
                    </div>
                  </div>
                  {% endfor %}
                </div>

                <!-- أنواع الطلب حسب الفئة -->
                <div id="typesSection" class="d-none">
                  <select name="request_type" id="requestTypeSelect"
                          class="form-select" required>
                    <option value="">اختر نوع الطلب</option>
                    {% for rt in request_types %}
                    <option value="{{ rt.pk }}"
                            data-cat="{{ rt.category.pk }}"
                            data-dates="{{ rt.requires_date_range|yesno:'true,false' }}"
                            data-amount="{{ rt.requires_amount|yesno:'true,false' }}"
                            data-doc="{{ rt.requires_document|yesno:'true,false' }}"
                            class="type-option d-none">
                      {{ rt.name }}
                    </option>
                    {% endfor %}
                  </select>
                </div>
              </div>

              <!-- الموضوع -->
              <div class="col-12" id="subjectSection" style="display:none;">
                <label class="form-label fw-semibold small">
                  الموضوع <span class="text-danger">*</span>
                </label>
                <input type="text" name="subject" class="form-control"
                       placeholder="اكتب موضوع الطلب بإيجاز">
              </div>

              <!-- تواريخ (اختياري) -->
              <div class="col-md-6 d-none" id="startDateSection">
                <label class="form-label fw-semibold small">من تاريخ</label>
                <input type="date" name="start_date" class="form-control">
              </div>

              <div class="col-md-6 d-none" id="endDateSection">
                <label class="form-label fw-semibold small">إلى تاريخ</label>
                <input type="date" name="end_date" class="form-control">
              </div>

              <!-- مبلغ (اختياري) -->
              <div class="col-md-6 d-none" id="amountSection">
                <label class="form-label fw-semibold small">المبلغ (جنيه)</label>
                <input type="number" name="amount" class="form-control"
                       min="0" step="0.01" placeholder="0.00">
              </div>

              <!-- التفاصيل -->
              <div class="col-12" id="detailsSection" style="display:none;">
                <label class="form-label fw-semibold small">
                  التفاصيل <span class="text-danger">*</span>
                </label>
                <textarea name="details" class="form-control" rows="4"
                          placeholder="اشرح طلبك بالتفصيل..."></textarea>
              </div>

              <!-- مرفق (اختياري) -->
              <div class="col-12 d-none" id="documentSection">
                <label class="form-label fw-semibold small">
                  مرفق
                  <small class="text-muted fw-normal">(إن وجد)</small>
                </label>
                <input type="file" name="document" class="form-control">
              </div>

            </div>

            <!-- أزرار -->
            <div class="d-flex gap-2 mt-4 pt-3 border-top" id="submitSection"
                 style="display:none !important;">
              <button type="submit" class="btn text-white px-4"
                      style="background:#06B6D4; border-radius:10px;">
                <i class="bi bi-send me-1"></i>
                تقديم الطلب
              </button>
              <a href="{% url 'requests_app:list' %}"
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

{% block extra_js %}
<script>
document.querySelectorAll('.category-card').forEach(card => {
  card.addEventListener('click', function() {
    const catId = this.dataset.cat;

    // تلوين الكارت المختار
    document.querySelectorAll('.category-card').forEach(c => {
      c.style.borderColor = '#e5e7eb';
      c.style.background = 'white';
    });
    this.style.borderColor = '#06B6D4';
    this.style.background = '#e0f7fa';

    // إظهار الأنواع
    const typesSection = document.getElementById('typesSection');
    const select = document.getElementById('requestTypeSelect');

    typesSection.classList.remove('d-none');

    // إظهار options الفئة المختارة
    document.querySelectorAll('.type-option').forEach(opt => {
      if (opt.dataset.cat === catId) {
        opt.classList.remove('d-none');
      } else {
        opt.classList.add('d-none');
        opt.selected = false;
      }
    });

    select.value = '';
    hideExtraFields();
  });
});

document.getElementById('requestTypeSelect').addEventListener('change', function() {
  const selected = this.options[this.selectedIndex];
  if (!selected.value) {
    hideExtraFields();
    return;
  }

  const needsDates  = selected.dataset.dates  === 'true';
  const needsAmount = selected.dataset.amount  === 'true';
  const needsDoc    = selected.dataset.doc     === 'true';

  // إظهار الحقول
  document.getElementById('subjectSection').style.display = 'block';
  document.getElementById('detailsSection').style.display = 'block';
  document.getElementById('submitSection').style.removeProperty('display');

  toggleSection('startDateSection', needsDates);
  toggleSection('endDateSection', needsDates);
  toggleSection('amountSection', needsAmount);
  toggleSection('documentSection', needsDoc);

  // subject placeholder ذكي
  document.querySelector('[name="subject"]').placeholder =
    'طلب ' + selected.text.trim();
});

function toggleSection(id, show) {
  const el = document.getElementById(id);
  if (show) {
    el.classList.remove('d-none');
  } else {
    el.classList.add('d-none');
  }
}

function hideExtraFields() {
  document.getElementById('subjectSection').style.display = 'none';
  document.getElementById('detailsSection').style.display = 'none';
  document.getElementById('submitSection').style.display = 'none';
  ['startDateSection', 'endDateSection', 'amountSection', 'documentSection'].forEach(id => {
    document.getElementById(id).classList.add('d-none');
  });
}
</script>
{% endblock %}
"""
)


# ════════════════════════════════════════════════════════════
# 3. تفاصيل الطلب
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء detail.html...")

create_file(
    os.path.join(BASE_DIR, "templates", "requests_app", "detail.html"),
    r"""{% extends 'base/dashboard_base.html' %}
{% load custom_filters %}
{% block title %}تفاصيل الطلب{% endblock %}

{% block content %}
<div class="container-fluid py-4">

  <div class="d-flex align-items-center mb-4">
    <a href="{% url 'requests_app:list' %}"
       class="btn btn-outline-secondary btn-sm me-3">
      <i class="bi bi-arrow-right"></i>
    </a>
    <h4 class="fw-bold mb-0">تفاصيل الطلب</h4>
    <span class="badge bg-{{ req.status_color }} ms-3 fs-6 px-3">
      <i class="bi bi-{{ req.status_icon }} me-1"></i>
      {{ req.get_status_display }}
    </span>
    {% if req.priority == 'urgent' %}
    <span class="badge bg-danger ms-2">عاجل</span>
    {% endif %}
  </div>

  <div class="row g-4">

    <!-- تفاصيل الطلب -->
    <div class="col-lg-8">
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
          <h5 class="fw-bold mb-0">{{ req.subject }}</h5>
          <small class="text-muted">
            {{ req.request_type.category.name }} ←
            {{ req.request_type.name }}
          </small>
        </div>
        <div class="card-body px-4 pb-4">
          <div class="row g-3 mb-4">

            <div class="col-md-6">
              <label class="text-muted small">الموظف</label>
              <div class="fw-bold">{{ req.employee.full_name_ar }}</div>
              <small class="text-muted">{{ req.employee.employee_code }}</small>
            </div>

            <div class="col-md-6">
              <label class="text-muted small">تاريخ الطلب</label>
              <div class="fw-bold">{{ req.created_at|date:"d/m/Y H:i" }}</div>
            </div>

            {% if req.start_date %}
            <div class="col-md-6">
              <label class="text-muted small">من تاريخ</label>
              <div class="fw-bold">{{ req.start_date|date:"d/m/Y" }}</div>
            </div>
            <div class="col-md-6">
              <label class="text-muted small">إلى تاريخ</label>
              <div class="fw-bold">{{ req.end_date|date:"d/m/Y"|default:"—" }}</div>
            </div>
            {% endif %}

            {% if req.amount %}
            <div class="col-md-6">
              <label class="text-muted small">المبلغ</label>
              <div class="fw-bold fs-5" style="color:#06B6D4;">
                {{ req.amount }} ج.م
              </div>
            </div>
            {% endif %}

          </div>

          <label class="text-muted small">التفاصيل</label>
          <div class="p-3 rounded mb-3" style="background:#f8fafc;">
            {{ req.details }}
          </div>

          {% if req.document %}
          <a href="{{ req.document.url }}" target="_blank"
             class="btn btn-sm btn-outline-primary">
            <i class="bi bi-file-earmark me-1"></i>
            عرض المرفق
          </a>
          {% endif %}
        </div>
      </div>

      <!-- تفاصيل المراجعة -->
      {% if req.reviewed_by %}
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h6 class="fw-bold mb-3">تفاصيل المراجعة</h6>
          <div class="d-flex align-items-center gap-3 mb-2">
            <i class="bi bi-person-check fs-4" style="color:#06B6D4;"></i>
            <div>
              <div class="fw-semibold">
                {{ req.reviewed_by.get_full_name|default:req.reviewed_by.username }}
              </div>
              <small class="text-muted">
                {{ req.reviewed_at|date:"d/m/Y H:i" }}
              </small>
            </div>
          </div>
          {% if req.review_notes %}
          <div class="p-3 rounded" style="background:#f8fafc;">
            {{ req.review_notes }}
          </div>
          {% endif %}
        </div>
      </div>
      {% endif %}
    </div>

    <!-- الإجراءات -->
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <h6 class="fw-bold mb-3">الإجراءات</h6>

          {% if req.status == 'pending' %}

          {% if request.user.role != 'employee' %}
          <!-- موافقة -->
          <form method="post"
                action="{% url 'requests_app:approve' req.pk %}"
                class="mb-2">
            {% csrf_token %}
            <textarea name="notes" class="form-control form-control-sm mb-2"
                      placeholder="ملاحظات الموافقة" rows="2"></textarea>
            <button type="submit" class="btn btn-success w-100 fw-bold"
                    onclick="return confirm('الموافقة على الطلب؟')">
              <i class="bi bi-check-lg me-1"></i>موافقة
            </button>
          </form>

          <!-- رفض -->
          <form method="post"
                action="{% url 'requests_app:reject' req.pk %}"
                class="mb-2">
            {% csrf_token %}
            <textarea name="notes" class="form-control form-control-sm mb-2"
                      placeholder="سبب الرفض" rows="2"></textarea>
            <button type="submit" class="btn btn-danger w-100 fw-bold"
                    onclick="return confirm('رفض الطلب؟')">
              <i class="bi bi-x-lg me-1"></i>رفض
            </button>
          </form>
          {% endif %}

          <!-- إلغاء (للموظف أو الإدارة) -->
          <form method="post"
                action="{% url 'requests_app:cancel' req.pk %}">
            {% csrf_token %}
            <button type="submit"
                    class="btn btn-outline-secondary w-100"
                    onclick="return confirm('إلغاء الطلب؟')">
              <i class="bi bi-slash-circle me-1"></i>إلغاء الطلب
            </button>
          </form>

          {% else %}
          <div class="text-center text-muted py-3">
            <i class="bi bi-check-all fs-3"></i>
            <p class="mb-0 mt-1 small">تم اتخاذ الإجراء</p>
          </div>
          {% endif %}

          <hr>
          <a href="{% url 'requests_app:list' %}"
             class="btn btn-light w-100">
            <i class="bi bi-arrow-right me-1"></i>
            رجوع للقائمة
          </a>
        </div>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""
)


print("\n" + "=" * 60)
print("  ✅ Patch 31b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ list.html - قائمة الطلبات
  2. ✅ add.html - فورم ذكي بالفئات والأنواع
  3. ✅ detail.html - تفاصيل + موافقة/رفض

جرب دلوقتي:
  http://127.0.0.1:8000/requests/add/

المتوقع:
  - تشوف 4 فئات (كروت)
  - تضغط على فئة تظهر الأنواع
  - تختار نوع تظهر الحقول المناسبة
  - تقدم الطلب
""")