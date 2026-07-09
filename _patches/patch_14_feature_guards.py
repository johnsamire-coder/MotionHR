"""
============================================================
Patch 14: Feature Guards + Client Subscription Pages
============================================================
- Countdown Bar
- Sidebar محدث (يخفي الميزات المقفلة)
- صفحة "خطتي"
- صفحة "ترقية الخطة"
- صفحة "الميزة غير متاحة"
- Feature Guards على Views
============================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
# 1. Views للعميل
# ═══════════════════════════════════════════════════════════

CLIENT_VIEWS = '''

# ═══════════════════════════════════════════════════════════
# Client-side Subscription Views
# ═══════════════════════════════════════════════════════════

@login_required
def my_subscription(request):
    """صفحة خطتي - للعميل"""
    
    subscription = None
    all_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('order')
    
    if request.user.role != 'super_admin' and request.user.company:
        subscription = CompanySubscription.objects.filter(
            company=request.user.company
        ).select_related('plan').first()
    
    context = {
        'subscription': subscription,
        'all_plans': all_plans,
    }
    
    return render(request, 'subscriptions/my_subscription.html', context)


@login_required
def upgrade_plan(request):
    """صفحة ترقية الخطة - للعميل"""
    
    subscription = None
    if request.user.company:
        subscription = CompanySubscription.objects.filter(
            company=request.user.company
        ).select_related('plan').first()
    
    all_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('order')
    
    context = {
        'subscription': subscription,
        'all_plans': all_plans,
    }
    
    return render(request, 'subscriptions/upgrade_plan.html', context)


@login_required
def feature_locked(request):
    """صفحة الميزة غير متاحة"""
    feature_key = request.GET.get('feature', '')
    
    feature = None
    if feature_key:
        try:
            feature = FeatureFlag.objects.get(key=feature_key)
        except FeatureFlag.DoesNotExist:
            pass
    
    subscription = None
    if request.user.company:
        subscription = CompanySubscription.objects.filter(
            company=request.user.company
        ).select_related('plan').first()
    
    # جلب الخطط اللي فيها الميزة دي
    plans_with_feature = []
    if feature:
        plans_with_feature = SubscriptionPlan.objects.filter(
            features=feature,
            is_active=True
        ).order_by('order')
    
    context = {
        'feature': feature,
        'subscription': subscription,
        'plans_with_feature': plans_with_feature,
    }
    
    return render(request, 'subscriptions/feature_locked.html', context)
'''


# ═══════════════════════════════════════════════════════════
# 2. URLs للعميل
# ═══════════════════════════════════════════════════════════

NEW_URLS = '''
    # Client-side URLs
    path('my-subscription/', views.my_subscription, name='my_subscription'),
    path('upgrade/', views.upgrade_plan, name='upgrade'),
    path('feature-locked/', views.feature_locked, name='feature_locked'),
]
'''


# ═══════════════════════════════════════════════════════════
# 3. صفحة "خطتي"
# ═══════════════════════════════════════════════════════════

MY_SUBSCRIPTION_TEMPLATE = '''{% extends 'base/dashboard_base.html' %}
{% load subscription_tags %}

{% block title %}خطتي{% endblock %}

{% block page_title %}خطتي 💎{% endblock %}
{% block page_subtitle %}تفاصيل اشتراكك الحالي{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للرئيسية
    </a>
</div>

{% if subscription %}

<!-- Subscription Info Card -->
<div class="card border-0 shadow-sm mb-4" 
     style="background: linear-gradient(135deg, {{ subscription.plan.color }} 0%, #06B6D4 100%);">
    <div class="card-body p-4 p-md-5 text-white">
        <div class="row align-items-center">
            <div class="col-md-8">
                <div class="mb-2">
                    <span class="badge bg-white bg-opacity-25 mb-2">
                        {% if subscription.is_trial %}
                            <i class="bi bi-star-fill"></i> تجربة مجانية
                        {% else %}
                            <i class="bi bi-award-fill"></i> {{ subscription.get_billing_cycle_display }}
                        {% endif %}
                    </span>
                </div>
                <h2 class="fw-bold mb-2">{{ subscription.plan.name_ar }}</h2>
                <p class="mb-0 opacity-75">{{ subscription.plan.description }}</p>
            </div>
            <div class="col-md-4 text-md-end mt-3 mt-md-0">
                <div class="display-4 fw-bold">{{ subscription.days_remaining }}</div>
                <div>يوم متبقي</div>
            </div>
        </div>
    </div>
</div>

<!-- Status Alert -->
{% if subscription.days_remaining <= 7 and subscription.days_remaining > 0 %}
<div class="alert alert-warning d-flex align-items-center mb-4">
    <i class="bi bi-exclamation-triangle-fill fs-4 ms-3"></i>
    <div class="flex-grow-1">
        <strong>اشتراكك ينتهي قريباً!</strong>
        متبقي {{ subscription.days_remaining }} أيام فقط. قم بالتجديد الآن لتجنب انقطاع الخدمة.
    </div>
    <a href="{% url 'subscriptions:upgrade' %}" class="btn btn-warning">جدد الآن</a>
</div>
{% elif subscription.days_remaining == 0 or subscription.is_expired %}
<div class="alert alert-danger d-flex align-items-center mb-4">
    <i class="bi bi-x-circle-fill fs-4 ms-3"></i>
    <div class="flex-grow-1">
        <strong>اشتراكك انتهى!</strong>
        قم بالتجديد للاستمرار في استخدام النظام.
    </div>
    <a href="{% url 'subscriptions:upgrade' %}" class="btn btn-light">جدد الاشتراك</a>
</div>
{% endif %}

<!-- Stats -->
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-calendar-check text-success fs-1"></i>
                <div class="small text-muted mt-2">تاريخ البداية</div>
                <div class="fw-bold">{{ subscription.start_date|date:"Y-m-d" }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-calendar-x text-danger fs-1"></i>
                <div class="small text-muted mt-2">تاريخ الانتهاء</div>
                <div class="fw-bold">{{ subscription.end_date|date:"Y-m-d" }}</div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-people-fill text-primary fs-1"></i>
                <div class="small text-muted mt-2">حد الموظفين</div>
                <div class="fw-bold">
                    {% if subscription.max_employees %}
                        {{ subscription.max_employees }}
                    {% else %}
                        غير محدود
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body">
                <i class="bi bi-shop text-info fs-1"></i>
                <div class="small text-muted mt-2">حد الفروع</div>
                <div class="fw-bold">
                    {% if subscription.plan.max_branches %}
                        {{ subscription.plan.max_branches }}
                    {% else %}
                        غير محدود
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Features -->
<div class="row g-3">
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
                <h6 class="fw-bold mb-0">
                    <i class="bi bi-check2-square text-success"></i>
                    الميزات المتاحة في خطتك ({{ subscription.plan.features.count }})
                </h6>
            </div>
            <div class="card-body">
                <div class="row g-2">
                    {% for feature in subscription.plan.features.all %}
                    <div class="col-md-6">
                        <div class="d-flex align-items-center gap-2 p-2 rounded bg-success bg-opacity-10">
                            <i class="{{ feature.icon }} text-success"></i>
                            <span class="small">{{ feature.name_ar }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-lg-4">
        <!-- Upgrade Card -->
        <div class="card border-0 shadow-sm mb-3" 
             style="background: linear-gradient(135deg, #F59E0B, #EF4444);">
            <div class="card-body p-4 text-white text-center">
                <i class="bi bi-rocket-takeoff-fill" style="font-size: 3rem;"></i>
                <h5 class="fw-bold mt-3">قم بترقية خطتك!</h5>
                <p class="opacity-75">احصل على المزيد من الميزات والقدرات</p>
                <a href="{% url 'subscriptions:upgrade' %}" class="btn btn-light">
                    <i class="bi bi-arrow-up-circle"></i>
                    عرض الخطط
                </a>
            </div>
        </div>
        
        <!-- Support -->
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-headset text-primary"></i>
                    تحتاج مساعدة؟
                </h6>
                <p class="small text-muted mb-3">
                    فريقنا جاهز للرد على استفساراتك
                </p>
                <a href="mailto:support@motionhr.com" class="btn btn-sm btn-outline-primary w-100">
                    <i class="bi bi-envelope"></i>
                    تواصل مع الدعم
                </a>
            </div>
        </div>
    </div>
</div>

{% else %}

<!-- No Subscription -->
<div class="card border-0 shadow-sm">
    <div class="card-body text-center py-5">
        <i class="bi bi-x-circle text-danger" style="font-size: 5rem;"></i>
        <h4 class="fw-bold mt-3">لا يوجد اشتراك</h4>
        <p class="text-muted">
            لم يتم تفعيل اشتراك لشركتك بعد. يرجى التواصل مع البائع.
        </p>
        <a href="mailto:sales@motionhr.com" class="btn btn-primary">
            <i class="bi bi-envelope"></i>
            تواصل مع المبيعات
        </a>
    </div>
</div>

{% endif %}

{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 4. صفحة "ترقية الخطة"
# ═══════════════════════════════════════════════════════════

UPGRADE_PLAN_TEMPLATE = '''{% extends 'base/dashboard_base.html' %}

{% block title %}ترقية الخطة{% endblock %}

{% block page_title %}ترقية الخطة 🚀{% endblock %}
{% block page_subtitle %}احصل على المزيد من الميزات{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'subscriptions:my_subscription' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع لخطتي
    </a>
</div>

{% if subscription %}
<div class="alert alert-info mb-4">
    <i class="bi bi-info-circle-fill"></i>
    خطتك الحالية: <strong>{{ subscription.plan.name_ar }}</strong>
    {% if subscription.days_remaining > 0 %}
    - متبقي {{ subscription.days_remaining }} يوم
    {% endif %}
</div>
{% endif %}

<!-- Plans Cards -->
<div class="row g-3 mb-4">
    {% for plan in all_plans %}
    {% if not plan.is_trial %}
    <div class="col-md-6 col-lg-3">
        <div class="card border-0 shadow-sm h-100 
             {% if subscription.plan.id == plan.id %}border-primary border-3{% endif %}
             {% if plan.is_featured %}shadow-lg{% endif %}"
             style="border-top: 4px solid {{ plan.color }};">
            
            {% if plan.is_featured %}
            <div style="background: {{ plan.color }}; color: white; padding: 5px; text-align: center;">
                <small><i class="bi bi-star-fill"></i> الأكثر شعبية</small>
            </div>
            {% endif %}
            
            {% if subscription.plan.id == plan.id %}
            <div style="background: #10B981; color: white; padding: 5px; text-align: center;">
                <small><i class="bi bi-check-circle-fill"></i> خطتك الحالية</small>
            </div>
            {% endif %}
            
            <div class="card-body p-4 text-center">
                <h4 class="fw-bold" style="color: {{ plan.color }};">
                    {{ plan.name_ar }}
                </h4>
                <p class="text-muted small">{{ plan.description }}</p>
                
                <div class="my-4">
                    <div class="display-5 fw-bold" style="color: {{ plan.color }};">
                        {{ plan.price_monthly|floatformat:0 }}
                    </div>
                    <small class="text-muted">ج.م / شهر</small>
                    {% if plan.price_yearly %}
                    <div class="mt-1">
                        <small class="text-success">
                            أو {{ plan.price_yearly|floatformat:0 }} ج.م/سنة
                            {% if plan.yearly_discount %}
                            (وفر {{ plan.yearly_discount }}%)
                            {% endif %}
                        </small>
                    </div>
                    {% endif %}
                </div>
                
                <div class="border-top pt-3 mb-3">
                    <div class="d-flex justify-content-around">
                        <div>
                            <div class="fw-bold">
                                {% if plan.max_employees %}{{ plan.max_employees }}{% else %}∞{% endif %}
                            </div>
                            <small class="text-muted">موظف</small>
                        </div>
                        <div>
                            <div class="fw-bold">
                                {% if plan.max_branches %}{{ plan.max_branches }}{% else %}∞{% endif %}
                            </div>
                            <small class="text-muted">فرع</small>
                        </div>
                        <div>
                            <div class="fw-bold">{{ plan.features.count }}</div>
                            <small class="text-muted">ميزة</small>
                        </div>
                    </div>
                </div>
                
                <ul class="list-unstyled small text-start" style="max-height: 200px; overflow-y: auto;">
                    {% for feature in plan.features.all|slice:":6" %}
                    <li class="mb-1">
                        <i class="bi bi-check-circle-fill text-success"></i>
                        {{ feature.name_ar }}
                    </li>
                    {% endfor %}
                    {% if plan.features.count > 6 %}
                    <li class="text-muted">
                        <i class="bi bi-three-dots"></i>
                        + {{ plan.features.count|add:"-6" }} ميزة أخرى
                    </li>
                    {% endif %}
                </ul>
                
                <div class="mt-3">
                    {% if subscription.plan.id == plan.id %}
                    <button class="btn btn-secondary w-100" disabled>
                        <i class="bi bi-check-circle"></i>
                        خطتك الحالية
                    </button>
                    {% else %}
                    <a href="mailto:sales@motionhr.com?subject=طلب%20ترقية%20للخطة%20{{ plan.name_ar }}" 
                       class="btn w-100" 
                       style="background: {{ plan.color }}; color: white;">
                        <i class="bi bi-arrow-up-circle"></i>
                        اطلب هذه الخطة
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    {% endfor %}
</div>

<!-- Contact -->
<div class="card border-0 shadow-sm">
    <div class="card-body text-center py-4">
        <h5 class="fw-bold mb-3">تحتاج خطة مخصصة؟ 🎯</h5>
        <p class="text-muted">
            للشركات الكبيرة أو الاحتياجات الخاصة، نوفر خطط مخصصة تناسب متطلباتك
        </p>
        <a href="mailto:sales@motionhr.com" class="btn btn-primary">
            <i class="bi bi-telephone"></i>
            تواصل معنا
        </a>
    </div>
</div>

{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 5. صفحة "الميزة غير متاحة"
# ═══════════════════════════════════════════════════════════

FEATURE_LOCKED_TEMPLATE = '''{% extends 'base/dashboard_base.html' %}

{% block title %}الميزة غير متاحة{% endblock %}

{% block page_title %}الميزة غير متاحة 🔒{% endblock %}
{% block page_subtitle %}هذه الميزة تتطلب ترقية الخطة{% endblock %}

{% block dashboard_content %}

<div class="mb-3">
    <a href="{% url 'dashboard' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-right"></i>
        رجوع للرئيسية
    </a>
</div>

<div class="row justify-content-center">
    <div class="col-lg-8">
        
        <div class="card border-0 shadow-sm text-center">
            <div class="card-body p-5">
                <div class="mb-4">
                    <div class="d-inline-flex align-items-center justify-content-center rounded-circle" 
                         style="width: 120px; height: 120px; background: linear-gradient(135deg, #F59E0B, #EF4444);">
                        <i class="bi bi-lock-fill text-white" style="font-size: 4rem;"></i>
                    </div>
                </div>
                
                <h3 class="fw-bold mb-3">
                    {% if feature %}
                    {{ feature.name_ar }} غير متاحة في خطتك
                    {% else %}
                    هذه الميزة غير متاحة
                    {% endif %}
                </h3>
                
                <p class="text-muted mb-4">
                    قم بترقية خطتك للاستفادة من هذه الميزة والمزيد
                </p>
                
                {% if subscription %}
                <div class="alert alert-info d-inline-block">
                    خطتك الحالية: <strong>{{ subscription.plan.name_ar }}</strong>
                </div>
                {% endif %}
                
                <div class="mt-4">
                    <a href="{% url 'subscriptions:upgrade' %}" class="btn btn-primary btn-lg">
                        <i class="bi bi-arrow-up-circle-fill"></i>
                        عرض خطط الترقية
                    </a>
                </div>
            </div>
        </div>
        
        {% if plans_with_feature %}
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-white">
                <h6 class="mb-0 fw-bold">
                    <i class="bi bi-check-circle-fill text-success"></i>
                    هذه الميزة متاحة في الخطط التالية:
                </h6>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    {% for plan in plans_with_feature %}
                    <div class="col-md-4">
                        <div class="border rounded-3 p-3 text-center" 
                             style="border-color: {{ plan.color }} !important; border-width: 2px !important;">
                            <h6 class="fw-bold" style="color: {{ plan.color }};">
                                {{ plan.name_ar }}
                            </h6>
                            <div class="my-2">
                                <span class="h4 fw-bold">{{ plan.price_monthly|floatformat:0 }}</span>
                                <small class="text-muted">ج.م/شهر</small>
                            </div>
                            <a href="{% url 'subscriptions:upgrade' %}" 
                               class="btn btn-sm w-100"
                               style="background: {{ plan.color }}; color: white;">
                                ترقية
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}
        
    </div>
</div>

{% endblock %}
'''


# ═══════════════════════════════════════════════════════════
# 6. Countdown Bar (يضاف للـ dashboard_base)
# ═══════════════════════════════════════════════════════════

COUNTDOWN_BAR_CODE = '''
<!-- Subscription Countdown Bar -->
{% if request.subscription and user.role != 'super_admin' %}
    {% if request.subscription.is_expired %}
    <div class="alert alert-danger mb-0 rounded-0 text-center py-2">
        <i class="bi bi-x-circle-fill"></i>
        <strong>اشتراكك انتهى!</strong>
        <a href="{% url 'subscriptions:upgrade' %}" class="alert-link">اضغط هنا للتجديد</a>
    </div>
    {% elif request.subscription.days_remaining <= 3 %}
    <div class="alert alert-warning mb-0 rounded-0 text-center py-2">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <strong>تنبيه:</strong> اشتراكك ينتهي خلال {{ request.subscription.days_remaining }} أيام فقط
        <a href="{% url 'subscriptions:upgrade' %}" class="alert-link">جدد الآن</a>
    </div>
    {% elif request.subscription.days_remaining <= 7 %}
    <div class="alert alert-info mb-0 rounded-0 text-center py-2">
        <i class="bi bi-info-circle-fill"></i>
        اشتراكك ينتهي خلال {{ request.subscription.days_remaining }} أيام.
        <a href="{% url 'subscriptions:upgrade' %}" class="alert-link">قم بالترقية</a>
    </div>
    {% elif request.subscription.is_trial and request.subscription.days_remaining <= 7 %}
    <div class="alert alert-info mb-0 rounded-0 text-center py-2">
        <i class="bi bi-star-fill"></i>
        <strong>تجربة مجانية:</strong> متبقي {{ request.subscription.days_remaining }} يوم
        <a href="{% url 'subscriptions:upgrade' %}" class="alert-link">اشترك الآن</a>
    </div>
    {% endif %}
{% endif %}
'''


# ═══════════════════════════════════════════════════════════
# التنفيذ
# ═══════════════════════════════════════════════════════════

def create_file(relative_path, content):
    full_path = BASE_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')


def add_client_views():
    """إضافة Views للعميل"""
    views_path = BASE_DIR / 'subscriptions' / 'views.py'
    content = views_path.read_text(encoding='utf-8')
    
    if 'def my_subscription' in content:
        return True, "Views موجودة بالفعل"
    
    with views_path.open('a', encoding='utf-8') as f:
        f.write(CLIENT_VIEWS)
    
    return True, "تم إضافة Views للعميل"


def update_urls():
    """تحديث URLs"""
    urls_path = BASE_DIR / 'subscriptions' / 'urls.py'
    content = urls_path.read_text(encoding='utf-8')
    
    if 'my_subscription' in content:
        return True, "URLs موجودة بالفعل"
    
    old = "    path('subscriptions/<int:pk>/activate/', views.activate_subscription, name='activate'),\n]"
    new = "    path('subscriptions/<int:pk>/activate/', views.activate_subscription, name='activate'),\n" + NEW_URLS
    
    if old not in content:
        return False, "لم يتم العثور على URLs"
    
    content = content.replace(old, new)
    urls_path.write_text(content, encoding='utf-8')
    return True, "تم تحديث URLs"


def add_countdown_bar():
    """إضافة Countdown Bar في dashboard_base.html"""
    base_path = BASE_DIR / 'templates' / 'base' / 'dashboard_base.html'
    content = base_path.read_text(encoding='utf-8')
    
    if 'Subscription Countdown Bar' in content:
        return True, "Countdown Bar موجود بالفعل"
    
    # نضيف قبل <header class="top-header">
    old = '<!-- Top Header -->'
    new = COUNTDOWN_BAR_CODE + '\n    <!-- Top Header -->'
    
    if old not in content:
        return False, "لم يتم العثور على المكان المناسب"
    
    content = content.replace(old, new)
    base_path.write_text(content, encoding='utf-8')
    return True, "تم إضافة Countdown Bar"


def add_my_subscription_to_sidebar():
    """إضافة رابط 'خطتي' في Sidebar"""
    sidebar_path = BASE_DIR / 'templates' / 'base' / 'dashboard_base.html'
    content = sidebar_path.read_text(encoding='utf-8')
    
    if 'my_subscription' in content:
        return True, "الرابط موجود بالفعل"
    
    # نضيف في قسم الإعدادات
    old = '<a href="/admin/" class="menu-item">'
    new = '''<a href="{% url 'subscriptions:my_subscription' %}" 
               class="menu-item {% if 'my-subscription' in request.path or 'upgrade' in request.path %}active{% endif %}">
                <i class="bi bi-award-fill"></i>
                <span>خطتي</span>
            </a>
            
            <a href="/admin/" class="menu-item">'''
    
    if old not in content:
        return False, "لم يتم العثور على قسم الإعدادات"
    
    content = content.replace(old, new)
    sidebar_path.write_text(content, encoding='utf-8')
    return True, "تم إضافة رابط خطتي"


def main():
    print("=" * 60)
    print("Patch 14: Feature Guards + Client Pages")
    print("=" * 60)
    print()
    
    # Templates
    print("Templates:")
    print("-" * 60)
    templates = [
        ('templates/subscriptions/my_subscription.html', MY_SUBSCRIPTION_TEMPLATE),
        ('templates/subscriptions/upgrade_plan.html', UPGRADE_PLAN_TEMPLATE),
        ('templates/subscriptions/feature_locked.html', FEATURE_LOCKED_TEMPLATE),
    ]
    
    for path, content in templates:
        try:
            create_file(path, content)
            print(f"  [OK] {path}")
        except Exception as e:
            print(f"  [X] {path}: {e}")
    
    print()
    print("Views + URLs:")
    print("-" * 60)
    
    tasks = [
        ('Client Views', add_client_views),
        ('URLs', update_urls),
        ('Countdown Bar', add_countdown_bar),
        ('Sidebar Link', add_my_subscription_to_sidebar),
    ]
    
    for name, func in tasks:
        try:
            success, message = func()
            icon = "[OK]" if success else "[!]"
            print(f"  {icon} {name}: {message}")
        except Exception as e:
            print(f"  [X] {name}: {e}")
    
    print()
    print("=" * 60)
    print("[SUCCESS] Done!")
    print("=" * 60)
    print()
    print("Test URLs:")
    print("  My Subscription: /sub-admin/my-subscription/")
    print("  Upgrade Plan:    /sub-admin/upgrade/")
    print("  Feature Locked:  /sub-admin/feature-locked/?feature=payroll_basic")
    print()


if __name__ == '__main__':
    main()