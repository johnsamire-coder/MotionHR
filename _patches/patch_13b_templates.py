"""
============================================================
Patch 13b: Subscription Admin Templates
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. Admin Dashboard Template
# ═══════════════════════════════════════════════════════════

ADMIN_DASHBOARD = '''{% extends 'base/dashboard_base.html' %}

{% block title %}إدارة الاشتراكات{% endblock %}

{% block page_title %}إدارة الاشتراكات 💼{% endblock %}
{% block page_subtitle %}لوحة تحكم المبيعات والعملاء{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للرئيسية
    </a>
</div>

<!-- Quick Actions -->
<div class="card border-0 shadow-sm mb-4" 
     style="background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);">
    <div class="card-body p-4 text-white">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h3 class="fw-bold mb-2">مركز التحكم بالاشتراكات 🎯</h3>
                <p class="mb-0 opacity-75">
                    إدارة العملاء والخطط والفواتير من مكان واحد
                </p>
            </div>
            <div class="col-md-4 text-md-end mt-3 mt-md-0">
                <a href="{% url 'subscriptions:create' %}" class="btn btn-light btn-lg">
                    <i class="bi bi-plus-circle-fill"></i>
                    عميل جديد
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Stats -->
<div class="row g-3 mb-4">
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">إجمالي العملاء</p>
                        <h3 class="fw-bold mb-0">{{ total_companies }}</h3>
                        <small class="text-muted">
                            <i class="bi bi-building"></i>
                            {{ total_subscriptions }} اشتراك
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(6, 182, 212, 0.1);">
                        <i class="bi bi-people-fill text-primary fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">اشتراكات نشطة</p>
                        <h3 class="fw-bold mb-0 text-success">{{ active_subs }}</h3>
                        <small class="text-warning">
                            {{ trial_subs }} تجربة
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(16, 185, 129, 0.1);">
                        <i class="bi bi-check-circle-fill text-success fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">MRR</p>
                        <h3 class="fw-bold mb-0 text-info">{{ mrr }}</h3>
                        <small class="text-muted">
                            جنيه شهرياً
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(59, 130, 246, 0.1);">
                        <i class="bi bi-graph-up-arrow text-info fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <p class="text-muted mb-1 small">ARR</p>
                        <h3 class="fw-bold mb-0 text-warning">{{ arr }}</h3>
                        <small class="text-muted">
                            جنيه سنوياً
                        </small>
                    </div>
                    <div class="rounded-3 p-3" style="background: rgba(245, 158, 11, 0.1);">
                        <i class="bi bi-cash-stack text-warning fs-4"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Quick Links -->
<div class="row g-3 mb-4">
    <div class="col-md-6 col-lg-3">
        <a href="{% url 'subscriptions:subscriptions_list' %}" class="text-decoration-none">
            <div class="card border-0 shadow-sm h-100 hover-lift">
                <div class="card-body text-center py-4">
                    <i class="bi bi-list-ul text-primary" style="font-size: 3rem;"></i>
                    <h6 class="fw-bold mt-3 text-dark">كل الاشتراكات</h6>
                </div>
            </div>
        </a>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <a href="{% url 'subscriptions:plans_list' %}" class="text-decoration-none">
            <div class="card border-0 shadow-sm h-100 hover-lift">
                <div class="card-body text-center py-4">
                    <i class="bi bi-award-fill text-info" style="font-size: 3rem;"></i>
                    <h6 class="fw-bold mt-3 text-dark">الخطط</h6>
                </div>
            </div>
        </a>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <a href="{% url 'subscriptions:create' %}" class="text-decoration-none">
            <div class="card border-0 shadow-sm h-100 hover-lift">
                <div class="card-body text-center py-4">
                    <i class="bi bi-plus-circle-fill text-success" style="font-size: 3rem;"></i>
                    <h6 class="fw-bold mt-3 text-dark">إضافة عميل</h6>
                </div>
            </div>
        </a>
    </div>
    
    <div class="col-md-6 col-lg-3">
        <a href="/admin/subscriptions/" class="text-decoration-none">
            <div class="card border-0 shadow-sm h-100 hover-lift">
                <div class="card-body text-center py-4">
                    <i class="bi bi-gear-fill text-secondary" style="font-size: 3rem;"></i>
                    <h6 class="fw-bold mt-3 text-dark">إعدادات متقدمة</h6>
                </div>
            </div>
        </a>
    </div>
</div>

<div class="row g-3">
    <!-- Expiring Soon -->
    <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white">
                <h6 class="fw-bold mb-0">
                    <i class="bi bi-alarm text-warning"></i>
                    قربوا على الانتهاء (7 أيام)
                </h6>
            </div>
            <div class="card-body p-0">
                {% if expiring_soon %}
                <div class="list-group list-group-flush">
                    {% for sub in expiring_soon %}
                    <a href="{% url 'subscriptions:detail' sub.pk %}" 
                       class="list-group-item list-group-item-action">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fw-semibold">{{ sub.company.name_ar }}</div>
                                <small class="text-muted">{{ sub.plan.name_ar }}</small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-warning">
                                    {{ sub.days_remaining }} يوم متبقي
                                </span>
                                <small class="d-block text-muted mt-1">
                                    {{ sub.end_date|date:"Y-m-d" }}
                                </small>
                            </div>
                        </div>
                    </a>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-check-circle text-success" style="font-size: 3rem;"></i>
                    <p class="text-muted mt-2">لا توجد اشتراكات قربت على الانتهاء</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Recent Subscriptions -->
    <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white">
                <h6 class="fw-bold mb-0">
                    <i class="bi bi-clock-history text-primary"></i>
                    آخر الاشتراكات
                </h6>
            </div>
            <div class="card-body p-0">
                {% if recent_subscriptions %}
                <div class="list-group list-group-flush">
                    {% for sub in recent_subscriptions %}
                    <a href="{% url 'subscriptions:detail' sub.pk %}" 
                       class="list-group-item list-group-item-action">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fw-semibold">{{ sub.company.name_ar }}</div>
                                <small class="text-muted">
                                    {{ sub.plan.name_ar }} - {{ sub.get_billing_cycle_display }}
                                </small>
                            </div>
                            <div class="text-end">
                                {% if sub.status == 'active' %}
                                    <span class="badge bg-success">نشط</span>
                                {% elif sub.status == 'trial' %}
                                    <span class="badge bg-info">تجربة</span>
                                {% elif sub.status == 'expired' %}
                                    <span class="badge bg-danger">منتهي</span>
                                {% else %}
                                    <span class="badge bg-secondary">{{ sub.get_status_display }}</span>
                                {% endif %}
                                <small class="d-block text-muted mt-1">
                                    {{ sub.created_at|date:"Y-m-d" }}
                                </small>
                            </div>
                        </div>
                    </a>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
                    <p class="text-muted mt-2">لا يوجد اشتراكات بعد</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block dashboard_css %}
<style>
    .hover-lift {
        transition: all 0.2s;
        cursor: pointer;
    }
    .hover-lift:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
    }
</style>
{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 2. Plans List Template
# ═══════════════════════════════════════════════════════════

PLANS_LIST = '''{% extends 'base/dashboard_base.html' %}

{% block title %}خطط الاشتراك{% endblock %}

{% block page_title %}خطط الاشتراك 💎{% endblock %}
{% block page_subtitle %}الخطط المتاحة للعملاء{% endblock %}

{% block dashboard_content %}

<div class="mb-3 d-flex gap-2 flex-wrap">
    <a href="{% url 'subscriptions:admin_dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع
    </a>
    <a href="/admin/subscriptions/subscriptionplan/" class="btn btn-sm btn-outline-primary">
        <i class="bi bi-pencil"></i>
        تعديل الخطط
    </a>
    <a href="/admin/subscriptions/subscriptionplan/add/" class="btn btn-sm btn-success">
        <i class="bi bi-plus"></i>
        خطة جديدة
    </a>
</div>

<div class="row g-3">
    {% for plan in plans %}
    <div class="col-md-6 col-lg-4">
        <div class="card border-0 shadow-sm h-100 {% if plan.is_featured %}border-primary{% endif %}" 
             style="border-top: 4px solid {{ plan.color }};">
            
            {% if plan.is_featured %}
            <div class="text-center" style="background: {{ plan.color }}; color: white; padding: 5px;">
                <small><i class="bi bi-star-fill"></i> الأكثر شعبية</small>
            </div>
            {% endif %}
            
            <div class="card-body p-4">
                <!-- Header -->
                <div class="text-center mb-3">
                    <h4 class="fw-bold" style="color: {{ plan.color }};">
                        {{ plan.name_ar }}
                    </h4>
                    {% if plan.is_trial %}
                    <span class="badge bg-warning">تجربة {{ plan.trial_days }} يوم</span>
                    {% endif %}
                    <p class="text-muted small mt-2">{{ plan.description }}</p>
                </div>
                
                <!-- Price -->
                <div class="text-center mb-3">
                    {% if plan.price_monthly %}
                    <div class="display-6 fw-bold" style="color: {{ plan.color }};">
                        {{ plan.price_monthly|floatformat:0 }}
                        <small class="fs-6 text-muted">ج.م/شهر</small>
                    </div>
                    {% if plan.price_yearly %}
                    <small class="text-success">
                        أو {{ plan.price_yearly|floatformat:0 }} ج.م/سنة
                        {% if plan.yearly_discount %}
                        (وفر {{ plan.yearly_discount }}%)
                        {% endif %}
                    </small>
                    {% endif %}
                    {% else %}
                    <div class="display-6 fw-bold text-success">مجاناً</div>
                    {% endif %}
                </div>
                
                <!-- Limits -->
                <div class="border-top border-bottom py-3 mb-3">
                    <div class="row text-center">
                        <div class="col-4">
                            <i class="bi bi-people text-muted"></i>
                            <div class="fw-bold">
                                {% if plan.max_employees %}{{ plan.max_employees }}{% else %}∞{% endif %}
                            </div>
                            <small class="text-muted">موظف</small>
                        </div>
                        <div class="col-4 border-start border-end">
                            <i class="bi bi-shop text-muted"></i>
                            <div class="fw-bold">
                                {% if plan.max_branches %}{{ plan.max_branches }}{% else %}∞{% endif %}
                            </div>
                            <small class="text-muted">فرع</small>
                        </div>
                        <div class="col-4">
                            <i class="bi bi-diagram-3 text-muted"></i>
                            <div class="fw-bold">
                                {% if plan.max_departments %}{{ plan.max_departments }}{% else %}∞{% endif %}
                            </div>
                            <small class="text-muted">إدارة</small>
                        </div>
                    </div>
                </div>
                
                <!-- Features -->
                <div class="mb-3" style="max-height: 200px; overflow-y: auto;">
                    <h6 class="fw-bold small mb-2">الميزات ({{ plan.features.count }}):</h6>
                    <ul class="list-unstyled small">
                        {% for feature in plan.features.all|slice:":8" %}
                        <li class="mb-1">
                            <i class="bi bi-check-circle-fill text-success"></i>
                            {{ feature.name_ar }}
                        </li>
                        {% endfor %}
                        {% if plan.features.count > 8 %}
                        <li class="text-muted">
                            <i class="bi bi-three-dots"></i>
                            و {{ plan.features.count|add:"-8" }} ميزة أخرى
                        </li>
                        {% endif %}
                    </ul>
                </div>
                
                <!-- Actions -->
                <div class="d-flex gap-2">
                    <a href="/admin/subscriptions/subscriptionplan/{{ plan.id }}/change/" 
                       class="btn btn-sm btn-outline-primary flex-grow-1">
                        <i class="bi bi-pencil"></i>
                        تعديل
                    </a>
                    <a href="{% url 'subscriptions:create' %}?plan={{ plan.id }}" 
                       class="btn btn-sm btn-primary flex-grow-1"
                       style="background: {{ plan.color }}; border-color: {{ plan.color }};">
                        <i class="bi bi-plus-circle"></i>
                        عميل جديد
                    </a>
                </div>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-12">
        <div class="card border-0 shadow-sm">
            <div class="card-body text-center py-5">
                <i class="bi bi-inbox text-muted" style="font-size: 4rem;"></i>
                <h5 class="mt-3 fw-bold">لا توجد خطط</h5>
                <a href="/admin/subscriptions/subscriptionplan/add/" class="btn btn-primary">
                    <i class="bi bi-plus-circle"></i>
                    إضافة خطة
                </a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 3. Subscriptions List
# ═══════════════════════════════════════════════════════════

SUBSCRIPTIONS_LIST = '''{% extends 'base/dashboard_base.html' %}

{% block title %}اشتراكات العملاء{% endblock %}

{% block page_title %}اشتراكات العملاء 📋{% endblock %}
{% block page_subtitle %}كل الشركات المشتركة في النظام{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'subscriptions:admin_dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع
    </a>
</div>

<!-- Header -->
<div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
        <div class="row g-3 align-items-center">
            <div class="col-md-5">
                <form method="get" class="d-flex gap-2">
                    <input type="text" name="search" class="form-control" 
                           placeholder="بحث باسم الشركة..." value="{{ search }}">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-search"></i>
                    </button>
                </form>
            </div>
            <div class="col-md-4">
                <div class="d-flex align-items-center gap-2 p-2 rounded-3" 
                     style="background: rgba(6, 182, 212, 0.1);">
                    <i class="bi bi-list-ol text-primary fs-4"></i>
                    <div>
                        <small class="text-muted">إجمالي</small>
                        <div class="fw-bold text-primary">{{ total_count }} اشتراك</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 text-md-end">
                <a href="{% url 'subscriptions:create' %}" class="btn btn-success">
                    <i class="bi bi-plus-circle"></i>
                    اشتراك جديد
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Filters -->
<div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
        <form method="get" class="row g-3">
            {% if search %}<input type="hidden" name="search" value="{{ search }}">{% endif %}
            
            <div class="col-md-4">
                <label class="form-label small fw-semibold">الحالة</label>
                <select name="status" class="form-select" onchange="this.form.submit()">
                    <option value="">كل الحالات</option>
                    {% for value, label in status_choices %}
                    <option value="{{ value }}" {% if status_filter == value %}selected{% endif %}>
                        {{ label }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="col-md-4">
                <label class="form-label small fw-semibold">الخطة</label>
                <select name="plan" class="form-select" onchange="this.form.submit()">
                    <option value="">كل الخطط</option>
                    {% for plan in plans %}
                    <option value="{{ plan.id }}" {% if plan_filter == plan.id|stringformat:"s" %}selected{% endif %}>
                        {{ plan.name_ar }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            
            {% if search or status_filter or plan_filter %}
            <div class="col-md-4 d-flex align-items-end">
                <a href="{% url 'subscriptions:subscriptions_list' %}" class="btn btn-sm btn-outline-danger">
                    <i class="bi bi-x-circle"></i>
                    مسح الفلاتر
                </a>
            </div>
            {% endif %}
        </form>
    </div>
</div>

<!-- Table -->
<div class="card border-0 shadow-sm">
    <div class="card-body p-0">
        {% if subscriptions %}
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="ps-4">الشركة</th>
                        <th>الخطة</th>
                        <th>الحالة</th>
                        <th>نوع الفوترة</th>
                        <th>البداية</th>
                        <th>الانتهاء</th>
                        <th>متبقي</th>
                        <th>السعر</th>
                        <th class="pe-4">الإجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for sub in subscriptions %}
                    <tr>
                        <td class="ps-4">
                            <div class="fw-semibold">{{ sub.company.name_ar }}</div>
                            <small class="text-muted">{{ sub.company.email|default:"-" }}</small>
                        </td>
                        <td>
                            <span class="badge" style="background: {{ sub.plan.color }};">
                                {{ sub.plan.name_ar }}
                            </span>
                        </td>
                        <td>
                            {% if sub.status == 'active' %}
                                <span class="badge bg-success">نشط</span>
                            {% elif sub.status == 'trial' %}
                                <span class="badge bg-info">تجربة</span>
                            {% elif sub.status == 'expired' %}
                                <span class="badge bg-danger">منتهي</span>
                            {% elif sub.status == 'cancelled' %}
                                <span class="badge bg-secondary">ملغي</span>
                            {% elif sub.status == 'grace_period' %}
                                <span class="badge bg-warning">فترة سماح</span>
                            {% else %}
                                <span class="badge bg-secondary">{{ sub.get_status_display }}</span>
                            {% endif %}
                        </td>
                        <td><small>{{ sub.get_billing_cycle_display }}</small></td>
                        <td><small>{{ sub.start_date|date:"Y-m-d" }}</small></td>
                        <td><small>{{ sub.end_date|date:"Y-m-d" }}</small></td>
                        <td>
                            {% if sub.days_remaining > 7 %}
                                <span class="text-success">{{ sub.days_remaining }} يوم</span>
                            {% elif sub.days_remaining > 0 %}
                                <span class="text-warning fw-bold">{{ sub.days_remaining }} يوم</span>
                            {% else %}
                                <span class="text-danger">منتهي</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="fw-bold text-success">{{ sub.price_paid|floatformat:0 }}</span>
                            <small class="text-muted">ج.م</small>
                        </td>
                        <td class="pe-4">
                            <a href="{% url 'subscriptions:detail' sub.pk %}" 
                               class="btn btn-sm btn-primary">
                                <i class="bi bi-eye"></i>
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="text-center py-5">
            <i class="bi bi-inbox text-muted" style="font-size: 4rem;"></i>
            <h5 class="mt-3 fw-bold">لا توجد اشتراكات</h5>
            <a href="{% url 'subscriptions:create' %}" class="btn btn-primary mt-2">
                <i class="bi bi-plus-circle"></i>
                إضافة اشتراك جديد
            </a>
        </div>
        {% endif %}
    </div>
</div>

{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 4. Create Subscription
# ═══════════════════════════════════════════════════════════

CREATE_SUBSCRIPTION = '''{% extends 'base/dashboard_base.html' %}

{% block title %}إضافة اشتراك{% endblock %}

{% block page_title %}إضافة اشتراك جديد ➕{% endblock %}
{% block page_subtitle %}إضافة عميل جديد للنظام{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'subscriptions:admin_dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع
    </a>
</div>

<form method="post" id="subscriptionForm">
    {% csrf_token %}
    
    <div class="row">
        <div class="col-lg-8">
            
            <!-- الشركة -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-white">
                    <h6 class="mb-0 fw-bold">
                        <i class="bi bi-building text-primary"></i>
                        بيانات الشركة
                    </h6>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <div class="btn-group w-100" role="group">
                            <input type="radio" class="btn-check" name="company_type" id="existing" value="existing" checked>
                            <label class="btn btn-outline-primary" for="existing">شركة موجودة</label>
                            
                            <input type="radio" class="btn-check" name="company_type" id="new" value="new">
                            <label class="btn btn-outline-primary" for="new">شركة جديدة</label>
                        </div>
                    </div>
                    
                    <!-- شركة موجودة -->
                    <div id="existingCompanySection">
                        <label class="form-label fw-semibold">اختر الشركة</label>
                        <select name="company_id" class="form-select">
                            <option value="">-- اختر شركة --</option>
                            {% for company in companies_without_sub %}
                            <option value="{{ company.id }}">{{ company.name_ar }}</option>
                            {% endfor %}
                        </select>
                        <small class="text-muted">
                            {% if not companies_without_sub %}
                            لا توجد شركات بدون اشتراك حالياً
                            {% endif %}
                        </small>
                    </div>
                    
                    <!-- شركة جديدة -->
                    <div id="newCompanySection" style="display: none;">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">
                                    اسم الشركة (عربي) <span class="text-danger">*</span>
                                </label>
                                <input type="text" name="new_company_name_ar" class="form-control">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">اسم الشركة (إنجليزي)</label>
                                <input type="text" name="new_company_name_en" class="form-control">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">البريد الإلكتروني</label>
                                <input type="email" name="new_company_email" class="form-control">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">رقم الهاتف</label>
                                <input type="text" name="new_company_phone" class="form-control">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- الخطة -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-white">
                    <h6 class="mb-0 fw-bold">
                        <i class="bi bi-award-fill text-primary"></i>
                        اختر الخطة
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        {% for plan in plans %}
                        <div class="col-md-6 col-lg-4">
                            <label class="w-100">
                                <input type="radio" name="plan_id" value="{{ plan.id }}" 
                                       class="btn-check" required
                                       data-price-monthly="{{ plan.price_monthly }}"
                                       data-price-yearly="{{ plan.price_yearly }}"
                                       data-is-trial="{{ plan.is_trial|yesno:'true,false' }}"
                                       data-trial-days="{{ plan.trial_days }}">
                                <div class="card border-2 h-100 plan-card" 
                                     style="cursor: pointer; border-color: {{ plan.color }} !important;">
                                    <div class="card-body text-center p-3">
                                        <h6 class="fw-bold" style="color: {{ plan.color }};">
                                            {{ plan.name_ar }}
                                        </h6>
                                        {% if plan.is_trial %}
                                        <span class="badge bg-warning">تجربة {{ plan.trial_days }} يوم</span>
                                        {% else %}
                                        <div class="my-2">
                                            <strong>{{ plan.price_monthly|floatformat:0 }}</strong>
                                            <small class="text-muted">ج.م/شهر</small>
                                        </div>
                                        <small class="text-muted d-block">
                                            {% if plan.max_employees %}
                                            {{ plan.max_employees }} موظف
                                            {% else %}
                                            غير محدود
                                            {% endif %}
                                        </small>
                                        {% endif %}
                                    </div>
                                </div>
                            </label>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- تفاصيل الاشتراك -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-white">
                    <h6 class="mb-0 fw-bold">
                        <i class="bi bi-calendar-check text-primary"></i>
                        تفاصيل الاشتراك
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">نوع الفوترة</label>
                            <select name="billing_cycle" class="form-select" id="billingCycle">
                                <option value="trial">تجربة</option>
                                <option value="monthly" selected>شهري</option>
                                <option value="quarterly">ربع سنوي</option>
                                <option value="semi_annual">نصف سنوي</option>
                                <option value="yearly">سنوي</option>
                                <option value="custom">مخصص</option>
                            </select>
                        </div>
                        
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">تاريخ البداية</label>
                            <input type="date" name="start_date" class="form-control" 
                                   value="{{ today|date:'Y-m-d' }}">
                        </div>
                        
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">
                                المدة (بالأيام) <span class="text-danger">*</span>
                            </label>
                            <input type="number" name="duration_days" class="form-control" 
                                   id="durationDays" value="30" required>
                            <small class="text-muted">
                                14 = تجربة | 30 = شهر | 90 = 3 شهور | 365 = سنة
                            </small>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="form-check mt-4 pt-2">
                                <input type="checkbox" name="is_trial" id="isTrial" 
                                       class="form-check-input">
                                <label for="isTrial" class="form-check-label fw-semibold">
                                    اشتراك تجريبي
                                </label>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">السعر المدفوع</label>
                            <div class="input-group">
                                <input type="number" name="price_paid" class="form-control" 
                                       id="pricePaid" step="0.01" value="0">
                                <span class="input-group-text">ج.م</span>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">الخصم</label>
                            <div class="input-group">
                                <input type="number" name="discount" class="form-control" 
                                       step="0.01" value="0">
                                <span class="input-group-text">ج.م</span>
                            </div>
                        </div>
                        
                        <div class="col-12">
                            <label class="form-label fw-semibold">ملاحظات</label>
                            <textarea name="notes" class="form-control" rows="3"
                                      placeholder="أي ملاحظات خاصة بهذا الاشتراك..."></textarea>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>
        
        <!-- Summary -->
        <div class="col-lg-4">
            <div class="card border-0 shadow-sm sticky-top" style="top: 20px;">
                <div class="card-header bg-white">
                    <h6 class="mb-0 fw-bold">
                        <i class="bi bi-clipboard-check text-primary"></i>
                        ملخص الاشتراك
                    </h6>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <small class="text-muted d-block">الخطة المختارة</small>
                        <div class="fw-bold" id="summaryPlan">لم يتم الاختيار</div>
                    </div>
                    
                    <div class="mb-3">
                        <small class="text-muted d-block">نوع الفوترة</small>
                        <div class="fw-bold" id="summaryBilling">شهري</div>
                    </div>
                    
                    <div class="mb-3">
                        <small class="text-muted d-block">المدة</small>
                        <div class="fw-bold" id="summaryDuration">30 يوم</div>
                    </div>
                    
                    <hr>
                    
                    <div class="d-flex justify-content-between">
                        <span>السعر الأساسي:</span>
                        <span class="fw-bold" id="summaryPrice">0 ج.م</span>
                    </div>
                    
                    <hr>
                    
                    <button type="submit" class="btn btn-success btn-lg w-100">
                        <i class="bi bi-check-circle-fill"></i>
                        إنشاء الاشتراك
                    </button>
                </div>
            </div>
        </div>
        
    </div>
</form>

{% endblock %}

{% block dashboard_css %}
<style>
    .plan-card {
        transition: all 0.2s;
        opacity: 0.6;
    }
    .btn-check:checked + .plan-card {
        opacity: 1;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .plan-card:hover {
        opacity: 1;
    }
</style>
{% endblock %}

{% block dashboard_js %}
<script>
    // Toggle company sections
    document.querySelectorAll('input[name="company_type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            document.getElementById('existingCompanySection').style.display = 
                this.value === 'existing' ? 'block' : 'none';
            document.getElementById('newCompanySection').style.display = 
                this.value === 'new' ? 'block' : 'none';
        });
    });
    
    // Update summary
    function updateSummary() {
        const selectedPlan = document.querySelector('input[name="plan_id"]:checked');
        const billing = document.getElementById('billingCycle').value;
        const duration = document.getElementById('durationDays').value;
        
        if (selectedPlan) {
            const priceMonthly = parseFloat(selectedPlan.dataset.priceMonthly);
            const priceYearly = parseFloat(selectedPlan.dataset.priceYearly);
            const planCard = selectedPlan.nextElementSibling;
            const planName = planCard.querySelector('h6').textContent.trim();
            
            document.getElementById('summaryPlan').textContent = planName;
            
            // احسب السعر حسب المدة
            let price = 0;
            const days = parseInt(duration);
            
            if (billing === 'yearly' && priceYearly) {
                price = priceYearly;
            } else {
                price = (priceMonthly / 30) * days;
            }
            
            document.getElementById('summaryPrice').textContent = price.toFixed(0) + ' ج.م';
            document.getElementById('pricePaid').value = price.toFixed(2);
        }
        
        // Billing cycle name
        const billingNames = {
            'trial': 'تجربة',
            'monthly': 'شهري',
            'quarterly': 'ربع سنوي',
            'semi_annual': 'نصف سنوي',
            'yearly': 'سنوي',
            'custom': 'مخصص',
        };
        document.getElementById('summaryBilling').textContent = billingNames[billing] || billing;
        
        // Duration
        document.getElementById('summaryDuration').textContent = duration + ' يوم';
    }
    
    // Auto-set duration based on billing cycle
    document.getElementById('billingCycle').addEventListener('change', function() {
        const days = {
            'trial': 14,
            'monthly': 30,
            'quarterly': 90,
            'semi_annual': 180,
            'yearly': 365,
        };
        if (days[this.value]) {
            document.getElementById('durationDays').value = days[this.value];
        }
        updateSummary();
    });
    
    document.getElementById('durationDays').addEventListener('input', updateSummary);
    document.querySelectorAll('input[name="plan_id"]').forEach(r => {
        r.addEventListener('change', function() {
            // لو Trial خلي is_trial checked
            if (this.dataset.isTrial === 'true') {
                document.getElementById('isTrial').checked = true;
                document.getElementById('billingCycle').value = 'trial';
                document.getElementById('durationDays').value = this.dataset.trialDays;
            }
            updateSummary();
        });
    });
</script>
{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 5. Subscription Detail
# ═══════════════════════════════════════════════════════════

SUBSCRIPTION_DETAIL = '''{% extends 'base/dashboard_base.html' %}

{% block title %}{{ subscription.company.name_ar }}{% endblock %}

{% block page_title %}تفاصيل الاشتراك{% endblock %}
{% block page_subtitle %}{{ subscription.company.name_ar }}{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'subscriptions:subscriptions_list' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للقائمة
    </a>
</div>

<!-- Header -->
<div class="card border-0 shadow-sm mb-4" 
     style="background: linear-gradient(135deg, {{ subscription.plan.color }} 0%, #06B6D4 100%);">
    <div class="card-body p-4 text-white">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h3 class="fw-bold mb-2">{{ subscription.company.name_ar }}</h3>
                <p class="mb-0 opacity-75">
                    <i class="bi bi-award"></i>
                    {{ subscription.plan.name_ar }} - {{ subscription.get_billing_cycle_display }}
                </p>
            </div>
            <div class="col-md-4 text-md-end mt-3 mt-md-0">
                {% if subscription.status == 'active' %}
                    <span class="badge bg-success fs-6">نشط</span>
                {% elif subscription.status == 'trial' %}
                    <span class="badge bg-info fs-6">تجربة</span>
                {% elif subscription.status == 'expired' %}
                    <span class="badge bg-danger fs-6">منتهي</span>
                {% else %}
                    <span class="badge bg-secondary fs-6">{{ subscription.get_status_display }}</span>
                {% endif %}
                
                <div class="mt-2">
                    {% if subscription.days_remaining > 0 %}
                    <strong>{{ subscription.days_remaining }}</strong> يوم متبقي
                    {% else %}
                    <strong>منتهي</strong>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Stats -->
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-calendar-check text-primary fs-1"></i>
                <div class="small text-muted">تاريخ البداية</div>
                <div class="fw-bold">{{ subscription.start_date|date:"Y-m-d" }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-calendar-x text-danger fs-1"></i>
                <div class="small text-muted">تاريخ الانتهاء</div>
                <div class="fw-bold">{{ subscription.end_date|date:"Y-m-d" }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-cash-stack text-success fs-1"></i>
                <div class="small text-muted">المبلغ المدفوع</div>
                <div class="fw-bold">{{ subscription.price_paid|floatformat:0 }} ج.م</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-people-fill text-info fs-1"></i>
                <div class="small text-muted">حد الموظفين</div>
                <div class="fw-bold">
                    {% if subscription.max_employees %}{{ subscription.max_employees }}{% else %}غير محدود{% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row g-3">
    <!-- Actions -->
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-lightning-fill text-warning"></i>
                    إجراءات
                </h6>
            </div>
            <div class="card-body">
                <!-- ترقية -->
                <form method="post" action="{% url 'subscriptions:upgrade' subscription.pk %}" class="mb-3">
                    {% csrf_token %}
                    <label class="form-label small fw-semibold">ترقية/تخفيض الخطة</label>
                    <div class="d-flex gap-2">
                        <select name="new_plan_id" class="form-select form-select-sm" required>
                            <option value="">اختر خطة</option>
                            {% for plan in all_plans %}
                            <option value="{{ plan.id }}">{{ plan.name_ar }}</option>
                            {% endfor %}
                        </select>
                        <button type="submit" class="btn btn-sm btn-primary">تغيير</button>
                    </div>
                </form>
                
                <!-- تمديد -->
                <form method="post" action="{% url 'subscriptions:extend' subscription.pk %}" class="mb-3">
                    {% csrf_token %}
                    <label class="form-label small fw-semibold">تمديد الاشتراك</label>
                    <div class="row g-2">
                        <div class="col-6">
                            <input type="number" name="days" class="form-control form-control-sm" placeholder="أيام" value="30" required>
                        </div>
                        <div class="col-6">
                            <input type="number" name="price" class="form-control form-control-sm" placeholder="سعر" step="0.01">
                        </div>
                        <div class="col-12">
                            <button type="submit" class="btn btn-sm btn-success w-100">
                                <i class="bi bi-arrow-clockwise"></i> تمديد
                            </button>
                        </div>
                    </div>
                </form>
                
                <!-- تفعيل / إلغاء -->
                <hr>
                {% if subscription.status == 'trial' or subscription.status == 'suspended' %}
                <form method="post" action="{% url 'subscriptions:activate' subscription.pk %}" class="mb-2">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-sm btn-success w-100">
                        <i class="bi bi-check-circle"></i>
                        تفعيل الاشتراك
                    </button>
                </form>
                {% endif %}
                
                {% if subscription.status != 'cancelled' %}
                <form method="post" action="{% url 'subscriptions:cancel' subscription.pk %}"
                      onsubmit="return confirm('هل أنت متأكد من إلغاء الاشتراك؟');">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-sm btn-outline-danger w-100">
                        <i class="bi bi-x-circle"></i>
                        إلغاء الاشتراك
                    </button>
                </form>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Features -->
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-check2-square text-success"></i>
                    الميزات المتاحة ({{ subscription.plan.features.count }})
                </h6>
            </div>
            <div class="card-body">
                <div class="row g-2">
                    {% for feature in subscription.plan.features.all %}
                    <div class="col-md-6">
                        <div class="d-flex align-items-center gap-2 p-2 rounded">
                            <i class="{{ feature.icon }} text-success"></i>
                            <span class="small">{{ feature.name_ar }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                {% if subscription.extra_features.all %}
                <hr>
                <h6 class="fw-bold small mb-2">ميزات إضافية:</h6>
                <div class="row g-2">
                    {% for feature in subscription.extra_features.all %}
                    <div class="col-md-6">
                        <div class="d-flex align-items-center gap-2 p-2 rounded bg-warning bg-opacity-10">
                            <i class="{{ feature.icon }} text-warning"></i>
                            <span class="small">{{ feature.name_ar }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>
        
        {% if subscription.notes %}
        <div class="card border-0 shadow-sm mt-3">
            <div class="card-header bg-white">
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-sticky text-warning"></i>
                    الملاحظات
                </h6>
            </div>
            <div class="card-body">
                <p class="mb-0">{{ subscription.notes|linebreaks }}</p>
            </div>
        </div>
        {% endif %}
    </div>
</div>

{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def create_file(relative_path, content):
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')


def add_sidebar_link():
    """إضافة رابط الاشتراكات في Sidebar"""
    sidebar_path = BASE_DIR / 'templates' / 'base' / 'dashboard_base.html'
    content = sidebar_path.read_text(encoding='utf-8')
    
    if 'sub-admin' in content or 'subscriptions:admin_dashboard' in content:
        return True, "الرابط موجود بالفعل"
    
    # نضيف قسم جديد للـ Super Admin قبل الإعدادات
    old = '<div class="menu-section">\n            <div class="menu-title">الإعدادات</div>'
    
    new = '''<div class="menu-section">
            <div class="menu-title">إدارة النظام</div>
            
            {% if user.role == 'super_admin' %}
            <a href="{% url 'subscriptions:admin_dashboard' %}" 
               class="menu-item {% if 'sub-admin' in request.path %}active{% endif %}">
                <i class="bi bi-briefcase-fill"></i>
                <span>إدارة الاشتراكات</span>
                <span class="menu-badge">Admin</span>
            </a>
            {% endif %}
        </div>
        
        <div class="menu-section">
            <div class="menu-title">الإعدادات</div>'''
    
    if old not in content:
        return False, "لم يتم العثور على قسم الإعدادات"
    
    content = content.replace(old, new)
    sidebar_path.write_text(content, encoding='utf-8')
    return True, "تم إضافة رابط الاشتراكات في Sidebar"


def main():
    print("=" * 60)
    print("Patch 13b: Subscription Admin Templates")
    print("=" * 60)
    print()
    
    templates = [
        ('templates/subscriptions/admin_dashboard.html', ADMIN_DASHBOARD),
        ('templates/subscriptions/plans_list.html', PLANS_LIST),
        ('templates/subscriptions/subscriptions_list.html', SUBSCRIPTIONS_LIST),
        ('templates/subscriptions/create_subscription.html', CREATE_SUBSCRIPTION),
        ('templates/subscriptions/subscription_detail.html', SUBSCRIPTION_DETAIL),
    ]
    
    print("Templates:")
    print("-" * 60)
    for path, content in templates:
        try:
            create_file(path, content)
            print(f"  [OK] {path}")
        except Exception as e:
            print(f"  [X] {path}: {e}")
    
    print()
    print("Sidebar:")
    print("-" * 60)
    try:
        success, message = add_sidebar_link()
        icon = "[OK]" if success else "[!]"
        print(f"  {icon} {message}")
    except Exception as e:
        print(f"  [X] {e}")
    
    print()
    print("=" * 60)
    print("[SUCCESS] All templates created!")
    print("=" * 60)
    print()
    print("Test URLs:")
    print("  Dashboard:      /sub-admin/")
    print("  Plans:          /sub-admin/plans/")
    print("  Subscriptions:  /sub-admin/subscriptions/")
    print("  Create New:     /sub-admin/subscriptions/create/")
    print()


if __name__ == '__main__':
    main()