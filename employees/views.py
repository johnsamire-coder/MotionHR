from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Employee, JobTitle
from companies.models import Branch, Department


@login_required
def employee_list(request):
    """قائمة الموظفين"""
    
    # جلب كل الموظفين (الـ TenantManager هيفلتر حسب الشركة أوتوماتيك)
    employees = Employee.objects.all().select_related(
        'branch', 'department', 'job_title'
    )
    
    # البحث
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
    
    # الفلترة
    status_filter = request.GET.get('status', '')
    if status_filter:
        employees = employees.filter(status=status_filter)
    
    branch_filter = request.GET.get('branch', '')
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)
    
    department_filter = request.GET.get('department', '')
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    # Pagination
    paginator = Paginator(employees, 20)  # 20 موظف في الصفحة
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # البيانات المساعدة للفلترة
    branches = Branch.objects.all()
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'total_count': paginator.count,
        'search': search,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'branches': branches,
        'departments': departments,
        'status_choices': Employee.STATUS_CHOICES,
    }
    
    return render(request, 'employees/list.html', context)


@login_required
def employee_add(request):
    """إضافة موظف جديد"""
    messages.info(request, 'صفحة الإضافة قيد التطوير - استخدم لوحة الإدارة مؤقتاً')
    return redirect('/admin/employees/employee/add/')


@login_required
def employee_detail(request, pk):
    """تفاصيل الموظف"""
    employee = get_object_or_404(Employee, pk=pk)
    
    context = {
        'employee': employee,
    }
    
    return render(request, 'employees/detail.html', context)


@login_required
def employee_edit(request, pk):
    """تعديل الموظف"""
    messages.info(request, 'صفحة التعديل قيد التطوير - استخدم لوحة الإدارة مؤقتاً')
    return redirect(f'/admin/employees/employee/{pk}/change/')


@login_required
def employee_delete(request, pk):
    """حذف الموظف"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        name = employee.full_name_ar
        employee.delete()
        messages.success(request, f'تم حذف الموظف {name} بنجاح')
        return redirect('employees:list')
    
    return render(request, 'employees/delete_confirm.html', {'employee': employee})