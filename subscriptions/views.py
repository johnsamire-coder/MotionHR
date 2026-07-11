"""
Subscription Admin Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from datetime import timedelta, date

from .models import SubscriptionPlan, CompanySubscription, FeatureFlag
from companies.models import Company


def is_super_admin(user):
    """التحقق من إن المستخدم Super Admin"""
    return user.is_authenticated and user.role == 'super_admin'


@login_required
@user_passes_test(is_super_admin)
def admin_dashboard(request):
    """Dashboard إدارة الاشتراكات"""
    
    today = timezone.now().date()
    
    # الإحصائيات
    total_companies = Company.objects.count()
    total_subscriptions = CompanySubscription.objects.count()
    active_subs = CompanySubscription.objects.filter(status='active').count()
    trial_subs = CompanySubscription.objects.filter(status='trial').count()
    expired_subs = CompanySubscription.objects.filter(end_date__lt=today).count()
    
    # قربوا على الانتهاء (خلال 7 أيام)
    expiring_soon = CompanySubscription.objects.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=7)
    ).order_by('end_date')
    
    # الإيرادات
    total_revenue = CompanySubscription.objects.aggregate(
        total=Sum('price_paid')
    )['total'] or 0
    
    # MRR - Monthly Recurring Revenue
    active_monthly = CompanySubscription.objects.filter(
        status='active',
        billing_cycle='monthly'
    ).aggregate(total=Sum('price_paid'))['total'] or 0
    
    active_yearly = CompanySubscription.objects.filter(
        status='active',
        billing_cycle='yearly'
    ).aggregate(total=Sum('price_paid'))['total'] or 0
    
    mrr = active_monthly + (active_yearly / 12)
    arr = mrr * 12
    
    # توزيع الخطط
    plans_distribution = SubscriptionPlan.objects.annotate(
        subs_count=Count('subscriptions', filter=Q(subscriptions__status='active'))
    ).values('name_ar', 'subs_count', 'color')
    
    # آخر الاشتراكات
    recent_subscriptions = CompanySubscription.objects.select_related(
        'company', 'plan'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_companies': total_companies,
        'total_subscriptions': total_subscriptions,
        'active_subs': active_subs,
        'trial_subs': trial_subs,
        'expired_subs': expired_subs,
        'expiring_soon': expiring_soon,
        'total_revenue': total_revenue,
        'mrr': round(mrr, 2),
        'arr': round(arr, 2),
        'plans_distribution': list(plans_distribution),
        'recent_subscriptions': recent_subscriptions,
    }
    
    return render(request, 'subscriptions/admin_dashboard.html', context)


@login_required
@user_passes_test(is_super_admin)
def plans_list(request):
    """قائمة الخطط"""
    plans = SubscriptionPlan.objects.filter(is_active=True).prefetch_related('features').order_by('order')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'subscriptions/plans_list.html', context)


@login_required
@user_passes_test(is_super_admin)
def subscriptions_list(request):
    """قائمة الاشتراكات"""
    subscriptions = CompanySubscription.objects.select_related(
        'company', 'plan'
    ).order_by('-created_at')
    
    # الفلترة
    status_filter = request.GET.get('status', '')
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    
    plan_filter = request.GET.get('plan', '')
    if plan_filter:
        subscriptions = subscriptions.filter(plan_id=plan_filter)
    
    search = request.GET.get('search', '').strip()
    if search:
        subscriptions = subscriptions.filter(
            Q(company__name_ar__icontains=search) |
            Q(company__name_en__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'subscriptions': page_obj.object_list,
        'total_count': paginator.count,
        'plans': SubscriptionPlan.objects.filter(is_active=True),
        'status_filter': status_filter,
        'plan_filter': plan_filter,
        'search': search,
        'status_choices': CompanySubscription.STATUS_CHOICES,
    }
    
    return render(request, 'subscriptions/subscriptions_list.html', context)


@login_required
@user_passes_test(is_super_admin)
def subscription_detail(request, pk):
    """تفاصيل الاشتراك"""
    subscription = get_object_or_404(CompanySubscription, pk=pk)
    
    context = {
        'subscription': subscription,
        'all_plans': SubscriptionPlan.objects.filter(is_active=True).exclude(id=subscription.plan.id),
    }
    
    return render(request, 'subscriptions/subscription_detail.html', context)


@login_required
@user_passes_test(is_super_admin)
def create_subscription(request):
    """إضافة اشتراك جديد (Wizard)"""
    
    if request.method == 'POST':
        try:
            # جلب البيانات
            company_id = request.POST.get('company_id')
            new_company_name_ar = request.POST.get('new_company_name_ar', '').strip()
            new_company_name_en = request.POST.get('new_company_name_en', '').strip()
            new_company_email = request.POST.get('new_company_email', '').strip()
            new_company_phone = request.POST.get('new_company_phone', '').strip()
            
            plan_id = request.POST.get('plan_id')
            billing_cycle = request.POST.get('billing_cycle', 'monthly')
            start_date_str = request.POST.get('start_date')
            duration_days = int(request.POST.get('duration_days', 30))
            price_paid = float(request.POST.get('price_paid', 0))
            discount = float(request.POST.get('discount', 0))
            notes = request.POST.get('notes', '')
            is_trial = request.POST.get('is_trial') == 'on'
            
            # التحقق
            if not plan_id:
                messages.error(request, 'يرجى اختيار خطة')
                return redirect('subscriptions:create')
            
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # إنشاء أو جلب الشركة
            if company_id:
                company = Company.objects.get(id=company_id)
            elif new_company_name_ar:
                company = Company.objects.create(
                    name_ar=new_company_name_ar,
                    name_en=new_company_name_en or None,
                    email=new_company_email or None,
                    phone=new_company_phone or None,
                    is_active=True,
                )
            else:
                messages.error(request, 'يرجى اختيار شركة أو إدخال بيانات شركة جديدة')
                return redirect('subscriptions:create')
            
            # التحقق من عدم وجود اشتراك سابق
            existing = CompanySubscription.objects.filter(company=company).first()
            if existing:
                messages.warning(request, f'الشركة {company.name_ar} لديها اشتراك بالفعل. يمكنك تعديله من صفحة التفاصيل.')
                return redirect('subscriptions:detail', pk=existing.pk)
            
            # التواريخ
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = start_date + timedelta(days=duration_days)
            
            # إنشاء الاشتراك
            subscription = CompanySubscription.objects.create(
                company=company,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                status='trial' if is_trial else 'active',
                billing_cycle=billing_cycle,
                is_trial=is_trial,
                trial_end_date=end_date if is_trial else None,
                price_paid=price_paid,
                discount=discount,
                notes=notes,
                activated_at=timezone.now(),
            )
            
            messages.success(
                request,
                f'✅ تم إنشاء اشتراك للشركة {company.name_ar} بخطة {plan.name_ar}'
            )
            return redirect('subscriptions:detail', pk=subscription.pk)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
    
    context = {
        'plans': SubscriptionPlan.objects.filter(is_active=True).order_by('order'),
        'companies_without_sub': Company.objects.filter(subscription__isnull=True),
        'today': date.today(),
    }
    
    return render(request, 'subscriptions/create_subscription.html', context)


@login_required
@user_passes_test(is_super_admin)
def upgrade_subscription(request, pk):
    """ترقية/تخفيض الاشتراك"""
    subscription = get_object_or_404(CompanySubscription, pk=pk)
    
    if request.method == 'POST':
        new_plan_id = request.POST.get('new_plan_id')
        try:
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
            old_plan_name = subscription.plan.name_ar
            subscription.plan = new_plan
            subscription.save()
            
            messages.success(
                request,
                f'✅ تم تغيير الخطة من {old_plan_name} إلى {new_plan.name_ar}'
            )
            return redirect('subscriptions:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
    
    return redirect('subscriptions:detail', pk=pk)


@login_required
@user_passes_test(is_super_admin)
def extend_subscription(request, pk):
    """تمديد الاشتراك"""
    subscription = get_object_or_404(CompanySubscription, pk=pk)
    
    if request.method == 'POST':
        try:
            days = int(request.POST.get('days', 30))
            price = float(request.POST.get('price', 0))
            
            subscription.end_date = subscription.end_date + timedelta(days=days)
            subscription.status = 'active'
            subscription.price_paid = subscription.price_paid + price
            subscription.save()
            
            messages.success(
                request,
                f'✅ تم تمديد الاشتراك لـ {days} يوم إضافي'
            )
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
    
    return redirect('subscriptions:detail', pk=pk)


@login_required
@user_passes_test(is_super_admin)
def cancel_subscription(request, pk):
    """إلغاء الاشتراك"""
    subscription = get_object_or_404(CompanySubscription, pk=pk)
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.save()
        
        messages.success(request, '✅ تم إلغاء الاشتراك')
    
    return redirect('subscriptions:detail', pk=pk)


@login_required
@user_passes_test(is_super_admin)
def activate_subscription(request, pk):
    """تفعيل اشتراك"""
    subscription = get_object_or_404(CompanySubscription, pk=pk)
    
    if request.method == 'POST':
        subscription.status = 'active'
        subscription.is_trial = False
        subscription.save()
        
        messages.success(request, '✅ تم تفعيل الاشتراك')
    
    return redirect('subscriptions:detail', pk=pk)


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


# ─────────────────────────────────────────────
# صفحة التواصل / البيع
# ─────────────────────────────────────────────
from django.conf import settings as django_settings

def contact_sales_view(request):
    """صفحة التواصل مع فريق المبيعات"""
    contact_info = getattr(django_settings, 'MOTIONHR_SALES_CONTACT', {})
    context = {
        'contact_phone':   contact_info.get('phone',     '01000000000'),
        'contact_email':   contact_info.get('email',     'sales@motionhr.com'),
        'whatsapp_number': contact_info.get('whatsapp',  '201000000000'),
        'page_title': 'تواصل معنا',
    }
    return render(request, 'subscriptions/contact_sales.html', context)



# ─────────────────────────────────────────────
# صفحة خطتي
# ─────────────────────────────────────────────
@login_required
def my_plan_view(request):
    """صفحة خطتي - تفاصيل الاشتراك الحالي"""
    from .models import CompanySubscription, SubscriptionPlan

    subscription    = None
    active_features = []

    if request.user.company:
        subscription = CompanySubscription.objects.filter(
            company=request.user.company,
            status__in=['active', 'trial']
        ).select_related('plan').first()

    # قائمة الميزات مع أسمائها العربية
    features_list = [
        ('employee_management',    'إدارة الموظفين'),
        ('attendance_tracking',    'تتبع الحضور'),
        ('gps_attendance',         'حضور GPS'),
        ('field_tracking',         'التتبع الميداني'),
        ('live_map',               'الخريطة الحية'),
        ('location_visits',        'تسجيل الزيارات'),
        ('reports_basic',          'التقارير الأساسية'),
        ('reports_advanced',       'التقارير المتقدمة'),
        ('excel_export',           'تصدير Excel'),
        ('pdf_export',             'تصدير PDF'),
        ('login_by_employee_code', 'دخول بالرقم الوظيفي'),
        ('login_by_phone',         'دخول بالموبايل'),
        ('leave_management',       'إدارة الإجازات'),
        ('multi_branch',           'فروع متعددة'),
        ('payroll_basic',          'مرتبات أساسي'),
    ]

    # حساب عدد الموظفين
    current_employees = 0
    if request.user.company:
        try:
            from employees.models import Employee
            current_employees = Employee.objects.filter(
                company=request.user.company,
                status='active'
            ).count()
        except Exception:
            pass

    context = {
        'subscription':      subscription,
        'active_features':   active_features,
        'features_list':     features_list,
        'current_employees': current_employees,
        'page_title':        'خطتي',
    }
    return render(request, 'subscriptions/my_plan.html', context)


# ═════════════════════════════════════════════════════════════
# Patch 49j-Hooks v3 — Premium Module Upsell Pages
# ═════════════════════════════════════════════════════════════

@login_required
def feature_upsell_page(request, feature_code):
    """صفحة تسويقية للموديولات الإضافية"""

    # ═══ تعريف المنتجات ═══
    features_meta = {

        # ── 1) الرواتب ──
        'payroll': {
            'title': 'نظام الرواتب والأجور',
            'subtitle': 'Payroll Management',
            'icon': 'bi-cash-coin',
            'color': '#10b981',
            'gradient': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            'description': 'نظام آلي متكامل لحساب الرواتب بضغطة زر واحدة. يسحب بيانات الحضور والتأخيرات والخصومات تلقائياً ويحسب صافي الراتب لكل موظف.',
            'benefits': [
                {'title': 'حساب آلي للرواتب', 'desc': 'يسحب التأخيرات والغياب والخصومات من سجلات الحضور ويحسب الراتب تلقائياً بدون تدخل بشري.', 'icon': 'bi-calculator'},
                {'title': 'مسيرات الرواتب (Payslips)', 'desc': 'إصدار كشف راتب مفصّل لكل موظف بصيغة PDF جاهز للطباعة أو الإرسال بالإيميل.', 'icon': 'bi-file-earmark-pdf'},
                {'title': 'إدارة البدلات والسلف', 'desc': 'تسجيل البدلات (سكن/مواصلات/طعام) والسلف وخصمها تلقائياً من الراتب.', 'icon': 'bi-wallet2'},
                {'title': 'تصدير بنكي', 'desc': 'تصدير ملف إكسل جاهز بفورمات البنوك المصرية لتحويل الرواتب مباشرة.', 'icon': 'bi-bank'},
                {'title': 'التأمينات والضرائب', 'desc': 'حساب حصة التأمينات الاجتماعية وضريبة كسب العمل تلقائياً حسب القانون المصري.', 'icon': 'bi-shield-check'},
                {'title': 'إقفال شهري', 'desc': 'إقفال الشهر بضغطة زر وأرشفة مسير الرواتب للرجوع إليه في أي وقت.', 'icon': 'bi-lock'},
            ],
            'price_hint': 'يبدأ من 200 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول الرواتب والأجور في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 2) التوظيف ──
        'recruitment': {
            'title': 'إدارة التوظيف',
            'subtitle': 'Applicant Tracking System (ATS)',
            'icon': 'bi-person-badge',
            'color': '#8b5cf6',
            'gradient': 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            'description': 'نظّم عملية التوظيف بالكامل من لحظة نشر الوظيفة حتى توقيع العقد وتحويل المرشح إلى موظف رسمي في النظام.',
            'benefits': [
                {'title': 'نشر الوظائف', 'desc': 'أنشئ إعلانات وظائف احترافية وشاركها مع المرشحين عبر رابط مباشر.', 'icon': 'bi-megaphone'},
                {'title': 'استقبال السير الذاتية', 'desc': 'استقبل طلبات التوظيف والسير الذاتية إلكترونياً في مكان واحد منظم.', 'icon': 'bi-inbox'},
                {'title': 'جدولة المقابلات', 'desc': 'حدد مواعيد المقابلات وأرسل إشعارات للمرشحين والمديرين تلقائياً.', 'icon': 'bi-calendar-event'},
                {'title': 'تقييم المرشحين', 'desc': 'نماذج تقييم مخصصة يملأها المدير بعد كل مقابلة لاتخاذ قرار موضوعي.', 'icon': 'bi-star-half'},
                {'title': 'تحويل لموظف', 'desc': 'بضغطة زر واحدة حوّل المرشح المقبول إلى موظف رسمي في النظام بكل بياناته.', 'icon': 'bi-person-check'},
                {'title': 'تقارير التوظيف', 'desc': 'تقارير عن عدد المتقدمين ومعدل القبول ومتوسط وقت التوظيف.', 'icon': 'bi-bar-chart-line'},
            ],
            'price_hint': 'يبدأ من 150 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول التوظيف (ATS) في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 3) تقييم الأداء ──
        'performance': {
            'title': 'تقييم الأداء',
            'subtitle': 'Performance Management & KPIs',
            'icon': 'bi-graph-up-arrow',
            'color': '#f59e0b',
            'gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            'description': 'ارتقِ بأداء فريقك من خلال نظام تقييم موضوعي يعتمد على مؤشرات أداء رئيسية (KPIs) واضحة ومحددة.',
            'benefits': [
                {'title': 'تقييم دوري', 'desc': 'إعداد دورات تقييم (شهرية / ربع سنوية / سنوية) بنماذج مخصصة لكل إدارة.', 'icon': 'bi-calendar-range'},
                {'title': 'مؤشرات أداء (KPIs)', 'desc': 'تعريف مؤشرات أداء قابلة للقياس لكل وظيفة وربطها بالتقييم.', 'icon': 'bi-speedometer'},
                {'title': 'تقييم 360 درجة', 'desc': 'تقييم من المدير + الزميل + تقييم ذاتي للحصول على صورة شاملة.', 'icon': 'bi-arrow-repeat'},
                {'title': 'ربط بالمكافآت', 'desc': 'ربط نتائج التقييم بالترقيات والمكافآت والعلاوات تلقائياً.', 'icon': 'bi-trophy'},
                {'title': 'خطط تطوير', 'desc': 'إنشاء خطط تطوير فردية للموظفين بناءً على نقاط الضعف في التقييم.', 'icon': 'bi-lightbulb'},
                {'title': 'تقارير وإحصائيات', 'desc': 'رسوم بيانية توضح أداء الإدارات والفرق ومقارنات بين الفترات.', 'icon': 'bi-pie-chart'},
            ],
            'price_hint': 'يبدأ من 150 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول تقييم الأداء في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 4) إدارة التدريب ──
        'training': {
            'title': 'إدارة التدريب والتطوير',
            'subtitle': 'Training & Development',
            'icon': 'bi-mortarboard',
            'color': '#06b6d4',
            'gradient': 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
            'description': 'تابع البرامج التدريبية لموظفيك وطوّر مهاراتهم بشكل منظم ومتابع.',
            'benefits': [
                {'title': 'خطة تدريب سنوية', 'desc': 'إعداد خطة تدريب لكل إدارة تشمل الدورات المطلوبة والميزانية.', 'icon': 'bi-journal-text'},
                {'title': 'تسجيل الدورات', 'desc': 'تسجيل كل دورة تدريبية بتفاصيلها (المدرب، المكان، المدة، التكلفة).', 'icon': 'bi-bookmark-plus'},
                {'title': 'متابعة الحضور', 'desc': 'تسجيل حضور الموظفين للدورات ومتابعة نسبة الإتمام.', 'icon': 'bi-check2-square'},
                {'title': 'الشهادات', 'desc': 'رفع شهادات التدريب وربطها بملف الموظف تلقائياً.', 'icon': 'bi-award'},
                {'title': 'تقييم أثر التدريب', 'desc': 'نماذج لتقييم مدى استفادة الموظف من الدورة التدريبية.', 'icon': 'bi-clipboard-data'},
                {'title': 'تقارير التدريب', 'desc': 'تقارير عن ميزانية التدريب وعدد الساعات التدريبية لكل موظف.', 'icon': 'bi-file-earmark-bar-graph'},
            ],
            'price_hint': 'يبدأ من 100 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول إدارة التدريب في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 5) إدارة الأصول والعهد ──
        'assets': {
            'title': 'إدارة الأصول والعهد',
            'subtitle': 'Asset & Custody Management',
            'icon': 'bi-laptop',
            'color': '#64748b',
            'gradient': 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
            'description': 'تابع أصول الشركة (لابتوبات، موبايلات، سيارات، أدوات) وربطها بالموظفين المسؤولين عنها.',
            'benefits': [
                {'title': 'سجل الأصول', 'desc': 'تسجيل كل أصل بتفاصيله (نوع، رقم تسلسلي، قيمة، تاريخ شراء).', 'icon': 'bi-box-seam'},
                {'title': 'تسليم واستلام', 'desc': 'توثيق تسليم الأصول للموظفين واستلامها عند المغادرة بمحاضر رسمية.', 'icon': 'bi-arrow-left-right'},
                {'title': 'إخلاء الطرف', 'desc': 'ربط الأصول بإخلاء الطرف — الموظف ما يقدرش يخلي طرفه إلا بعد تسليم كل العهد.', 'icon': 'bi-clipboard-check'},
                {'title': 'صيانة وتتبع', 'desc': 'جدولة صيانة الأصول وتتبع حالتها (جديد / مستخدم / يحتاج صيانة / تالف).', 'icon': 'bi-tools'},
                {'title': 'تنبيهات الضمان', 'desc': 'تنبيه قبل انتهاء ضمان الأصول أو عقود الصيانة.', 'icon': 'bi-bell'},
                {'title': 'تقارير الأصول', 'desc': 'تقارير عن قيمة الأصول وتوزيعها على الإدارات والموظفين.', 'icon': 'bi-bar-chart'},
            ],
            'price_hint': 'يبدأ من 100 ج.م / شهر',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول إدارة الأصول والعهد في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },

        # ── 6) الربط البرمجي (API) ──
        'api': {
            'title': 'الربط البرمجي',
            'subtitle': 'API & System Integration',
            'icon': 'bi-plug',
            'color': '#ef4444',
            'gradient': 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            'description': 'اربط MotionHR مع أنظمتك الحالية (ERP، برامج محاسبية، أجهزة بصمة) عبر واجهة برمجة تطبيقات (API) آمنة.',
            'benefits': [
                {'title': 'REST API كامل', 'desc': 'واجهة برمجية تدعم قراءة وكتابة بيانات الموظفين والحضور والإجازات.', 'icon': 'bi-code-slash'},
                {'title': 'ربط مع ERP', 'desc': 'تصدير القيود المحاسبية للرواتب مباشرة لبرامج (Odoo, SAP, QuickBooks).', 'icon': 'bi-diagram-3'},
                {'title': 'أجهزة البصمة', 'desc': 'استيراد بيانات الحضور من أجهزة ZKTeco وغيرها عبر ملفات أو API.', 'icon': 'bi-fingerprint'},
                {'title': 'Webhooks', 'desc': 'إشعارات لحظية لأنظمتك الخارجية عند حدوث أي حدث (تعيين، إجازة، استقالة).', 'icon': 'bi-broadcast'},
                {'title': 'SSO / Active Directory', 'desc': 'تسجيل دخول موحد مع Microsoft 365 أو Google Workspace.', 'icon': 'bi-shield-lock'},
                {'title': 'توثيق API', 'desc': 'توثيق كامل ومفصل لكل Endpoints مع أمثلة عملية.', 'icon': 'bi-book'},
            ],
            'price_hint': 'حسب متطلبات الربط',
            'whatsapp_text': 'السلام عليكم، أنا مهتم بتفعيل موديول الربط البرمجي (API) في نظام MotionHR لشركتي. أرجو التواصل معي لمعرفة التفاصيل والتكلفة.',
        },
    }

    feature = features_meta.get(feature_code)
    if not feature:
        return redirect('dashboard')

    context = {
        'feature': feature,
        'feature_code': feature_code,
        'page_title': feature['title'],
        'sales_phone': '(+20) 015 0155 1593',
        'sales_whatsapp': '2001501551593',
        'sales_email': 'info@jssolutions.com',
    }
    return render(request, 'subscriptions/upsell_page.html', context)


# ═════════════════════════════════════════════════════════════
# Patch 49N-A — Safe Admin Dashboard Override
# ═════════════════════════════════════════════════════════════

@login_required
def admin_dashboard(request):
    from decimal import Decimal
    from datetime import date
    from companies.models import Company
    from .models import CompanySubscription, SubscriptionPlan

    today = date.today()

    subscriptions = CompanySubscription.objects.select_related('company', 'plan').order_by('-id')
    plans = SubscriptionPlan.objects.all().order_by('id')
    companies_count = Company.objects.count()

    def _is_active(sub):
        status = str(getattr(sub, 'status', '') or '').lower()
        if status in ['cancelled', 'expired', 'inactive']:
            return False

        if hasattr(sub, 'is_active'):
            try:
                if sub.is_active is False:
                    return False
            except Exception:
                pass

        end_date = getattr(sub, 'end_date', None)
        if end_date and end_date < today:
            return False

        return True

    active_subscriptions = [s for s in subscriptions if _is_active(s)]
    expired_subscriptions = [s for s in subscriptions if not _is_active(s)]

    total_revenue = Decimal('0.00')
    for s in active_subscriptions:
        price = None
        if getattr(s, 'plan', None) and hasattr(s.plan, 'price'):
            price = s.plan.price
        elif hasattr(s, 'price'):
            price = s.price
        else:
            price = Decimal('0.00')

        try:
            total_revenue += Decimal(str(price))
        except Exception:
            pass

    monthly_revenue = total_revenue

    context = {
        'page_title': 'لوحة الاشتراكات',
        'subscriptions': subscriptions[:10],
        'recent_subscriptions': subscriptions[:10],
        'plans': plans,
        'companies_count': companies_count,
        'active_count': len(active_subscriptions),
        'expired_count': len(expired_subscriptions),
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
    }
    return render(request, 'subscriptions/admin_dashboard.html', context)

