"""
Views لإدارة إشعارات الشركة
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator

from .company_announcements import CompanyAnnouncement, CompanyAnnouncementRead


def can_manage_announcements(user):
    """هل المستخدم يقدر يدير الإشعارات؟"""
    if user.is_superuser:
        return True
    role = getattr(user, 'role', None)
    return role in ('company_admin', 'hr_manager', 'manager')


@login_required
def announcements_list(request):
    """قائمة الإشعارات - كل الشركات: للأدمن / موظف: بس اللي جالها"""
    user = request.user
    company = getattr(user, 'company', None)
    
    if not company:
        messages.warning(request, "لا توجد شركة مرتبطة بحسابك")
        return redirect('/')

    # لو المستخدم مدير - يشوف كل إشعارات الشركة
    if can_manage_announcements(user):
        announcements = CompanyAnnouncement.objects.filter(
            company=company
        ).order_by('-publish_at')
        is_manager_view = True
    else:
        # موظف عادي - يشوف الإشعارات اللي جاله
        employee = getattr(user, 'employee_profile', None)
        if not employee:
            employee = user.employees.first() if hasattr(user, 'employees') else None
        
        if employee:
            # هات كل الإشعارات النشطة للشركة
            all_announcements = CompanyAnnouncement.objects.filter(
                company=company,
                publish_at__lte=timezone.now(),
            ).order_by('-publish_at')
            
            # فلتر - يشوف بس اللي هو مستهدف فيها
            announcement_ids = []
            for ann in all_announcements:
                if employee in ann.get_target_employees():
                    announcement_ids.append(ann.id)
            
            announcements = CompanyAnnouncement.objects.filter(
                id__in=announcement_ids
            ).order_by('-publish_at')
        else:
            announcements = CompanyAnnouncement.objects.none()
        
        is_manager_view = False

    # Pagination
    paginator = Paginator(announcements, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'announcements': page_obj,
        'is_manager_view': is_manager_view,
        'can_create': can_manage_announcements(user),
    }
    return render(request, 'announcements/list.html', context)


@login_required
def announcement_create(request):
    """إنشاء إشعار جديد"""
    user = request.user
    if not can_manage_announcements(user):
        messages.error(request, "ليس لديك صلاحية لإنشاء إشعارات")
        return redirect('announcements:list')

    company = user.company
    if not company:
        messages.error(request, "لا توجد شركة مرتبطة")
        return redirect('/')

    if request.method == 'POST':
        try:
            ann = CompanyAnnouncement.objects.create(
                company=company,
                title=request.POST.get('title'),
                message=request.POST.get('message'),
                announcement_type=request.POST.get('announcement_type', 'general'),
                priority=request.POST.get('priority', 'medium'),
                target_type=request.POST.get('target_type', 'all'),
                target_job_titles=request.POST.get('target_job_titles', ''),
                excluded_job_titles=request.POST.get('excluded_job_titles', ''),
                send_push=request.POST.get('send_push') == 'on',
                created_by=user,
            )

            # M2M fields
            target_emp_ids = request.POST.getlist('target_employees')
            if target_emp_ids:
                ann.target_employees.set(target_emp_ids)

            target_dept_ids = request.POST.getlist('target_departments')
            if target_dept_ids:
                ann.target_departments.set(target_dept_ids)

            target_branch_ids = request.POST.getlist('target_branches')
            if target_branch_ids:
                ann.target_branches.set(target_branch_ids)

            excluded_emp_ids = request.POST.getlist('excluded_employees')
            if excluded_emp_ids:
                ann.excluded_employees.set(excluded_emp_ids)

            excluded_dept_ids = request.POST.getlist('excluded_departments')
            if excluded_dept_ids:
                ann.excluded_departments.set(excluded_dept_ids)

            # ابعت الإشعارات
            targets = ann.get_target_employees()
            
            from accounts.models import EmployeeNotification
            severity = 'warning' if ann.priority in ('high', 'urgent') else 'info'
            
            for emp in targets:
                EmployeeNotification.objects.create(
                    employee=emp,
                    title=ann.title,
                    message=ann.message,
                    notification_type='general_notice',
                    severity=severity,
                )
            
            ann.total_sent = targets.count()
            ann.save(update_fields=['total_sent'])

            messages.success(request, f"✅ تم إرسال الإشعار لـ {targets.count()} موظف")
            return redirect('announcements:list')
        
        except Exception as e:
            messages.error(request, f"حدث خطأ: {e}")

    # GET: عرض النموذج
    from employees.models import Employee
    from companies.models import Department, Branch
    
    context = {
        'employees': Employee.objects.filter(company=company),
        'departments': Department.objects.filter(company=company) if hasattr(Department, 'company') else Department.objects.all(),
        'branches': Branch.objects.filter(company=company) if hasattr(Branch, 'company') else Branch.objects.all(),
        'type_choices': CompanyAnnouncement.TYPE_CHOICES,
        'priority_choices': CompanyAnnouncement.PRIORITY_CHOICES,
        'target_choices': CompanyAnnouncement.TARGET_CHOICES,
    }
    return render(request, 'announcements/create.html', context)


@login_required
def announcement_detail(request, pk):
    """تفاصيل إشعار"""
    user = request.user
    company = user.company
    ann = get_object_or_404(CompanyAnnouncement, pk=pk, company=company)

    # سجّل قراءة
    employee = getattr(user, 'employee_profile', None) or (user.employees.first() if hasattr(user, 'employees') else None)
    if employee:
        CompanyAnnouncementRead.objects.get_or_create(
            employee=employee,
            announcement=ann,
        )
        ann.total_read = ann.reads.count()
        ann.save(update_fields=['total_read'])

    context = {
        'announcement': ann,
        'targets': ann.get_target_employees() if can_manage_announcements(user) else None,
        'can_manage': can_manage_announcements(user),
    }
    return render(request, 'announcements/detail.html', context)


@login_required
def announcement_delete(request, pk):
    """حذف إشعار"""
    user = request.user
    if not can_manage_announcements(user):
        messages.error(request, "ليس لديك صلاحية")
        return redirect('announcements:list')

    ann = get_object_or_404(CompanyAnnouncement, pk=pk, company=user.company)
    ann.delete()
    messages.success(request, "تم حذف الإشعار")
    return redirect('announcements:list')
