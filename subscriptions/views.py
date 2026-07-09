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
